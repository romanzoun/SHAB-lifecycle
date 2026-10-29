import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser418 import extract_parser418_leftovers as extract, _LEGACY

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['15f879c2718b0b23e9986e59b0b3dd1cdd7e36b46e03c7eeff53d6d70a171338', '27af891aed4c8415c05e277ac8ac220f776777ba707045f665045000f941560f', '28d7ab742d7d70075dd67fb250920eec1782afc20b415485c26fa36026125436', '557770ac256a93d7ea1d54b5cd785490af11da42b952516ae880e62719f65b28', '65f600e608a8b84d83fb73dadea6ed65780849fa60bf223bb8ebf19bdef6dd43', '6ce48c3d5d41827494748af6fb828a036013ca795f43e941b999ff6e7dc2c64b', '7d514518803c5c44d0cdf376f63693ece1ec40b2e10644cebc8ee306961b7341', '854e8c2dad075a330206c251c4915074518739ddc4b6b907145662eb098cc2a7', 'a7f96eb503d9ea2d6509d8c3f333363eeab3e66b23cafe8d3e58b4aba2e4b181', 'b8ec657b0c0a83c5aea6501b53daefdd87c30e74d601698dad393b0902ada9c3', 'd8d61f6368f0e97befbcdbbd199384763150fafc89adac5b2fe52e3cb5d11004', 'f55875f771c6afae2cf8164a0e2bbe62721b1b2830da162133ffb0e20d52b5ee']
COUNTS = [2, 1, 2, 1, 1, 2, 1, 1, 1, 1, 1, 1]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser418_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser418_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(path)
    assert len(calls) == 1
    return result, old, calls[0]


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('index', range(12))
def test_complete_and_unchanged_old_payloads(index):
    result, old, (args, kwargs) = captured(index)
    added, rest = extract(*args, **kwargs)
    assert PARSER_VERSION == 426
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    assert len(added) == COUNTS[index] and rest == ''
    assert old.leftover_text == args[0]
    assert result.events == old.events + added
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('index', range(12))
def test_unknown_suffix_language_and_invalid_dates(index):
    _, _, (args, kwargs) = captured(index)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract(changed, *args[1:], **kwargs) == ([], changed)
    assert extract(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index', range(12))
def test_missing_optional_metadata_and_source(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args[:4], None, None, None, **kwargs)
    assert len(events) == COUNTS[index] and rest == ''
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    events, rest = extract(*args)
    if index in (2, 3):
        assert (events, rest) == ([], args[0])
    else:
        assert len(events) == COUNTS[index] and rest == ''



EXPECTED = [
 ('ownership_changed', {'count': '100', 'before': '200', 'remaining': '100'}),
 ('ownership_changed', {'count': '10', 'remaining': '50', 'buyer_total': '50'}),
 ('officer_changed', {'origin1': 'St. Antoni', 'origin2': 'Ependes (FR)'}),
 ('organization_changed', {'branch_address': 'Bahnhofstrasse 30', 'historical_annotation': True}),
 ('officer_changed', {'place': 'Genève', 'procuration_revoked': True}),
 ('officer_changed', {'entry': '1119', 'corrected': True}),
 ('officer_changed', {'name': 'Ayoun Grégory David'}),
 ('capital_changed', {'claim': "2'800'000.00", 'count': "35'000", 'nominal': '0.10'}),
 ('status_changed', {'duration': 'six mois', 'end_date': '20.08.2021'}),
 ('ownership_changed', {'count': '5', 'before': '7', 'remaining': '2', 'buyer_total': '16'}),
 ('ownership_changed', {'count1': '19', 'count2': '1', 'buyer_total': '20', 'buyer_uid': 'CHE-262.208.326'}),
 ('capital_changed', {'capital': "8'900", 'issued_count': "26'500", 'fully_paid': True, 'transfer_restricted': True}),
]


@pytest.mark.parametrize('index', range(12))
def test_semantics(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    kind, fields = EXPECTED[index]
    assert rest == '' and events[0].event_type == kind
    for key, value in fields.items():
        assert events[0].payload[key] == value
    if index in (2, 5):
        assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in events)
        assert len({e.person_key for e in events}) == 2
    if index in (0, 6):
        assert events[-1].signing == 'ohne Zeichnungsberechtigung'
    if index == 4:
        assert events[0].signing == 'Einzelunterschrift' and events[0].role is None
    if index in (2, 3):
        assert extract(*args, source_text='unrelated') == ([], args[0])


LEGACY_TEXTS = [
 ('de', 'Bei der ordentlichen Kapitalerhöhung vom 07.12.2020 wird eine Forderung in der Höhe von CHF 2800000.00 verrechnet, wofür 35000 Namenaktien zu CHF 0.10 ausgegeben werden.'),
 ('fr', 'Test Anna, de Lausanne, à Genève, et Test Bea, de et à Lausanne, sont membres du comité.'),
 ('fr', 'Signature individuelle a été conférée à Test Anna, nommé directeur; sa procuration est radiée.'),
 ('fr', "L'associé gérant Test Anna, jusqu'ici ayant une signature individuelle, n'exerce plus la signature sociale."),
 ('fr', "L'inscription 1119 du 15.01.2021 (FOSC du 20.01.2021) est rectifiée en ce sens que Test Anna signe collectivement à deux (et non individuellement)."),
 ('fr', 'Test Anna cède 100 de ses 200 parts de CHF 100 à Test Bea, de Lausanne, à Paris (France), nouvelle associée sans signature, avec 100 parts de CHF 100; Test Anna reste titulaire de 100 parts de CHF 100.'),
]


@pytest.mark.parametrize('pattern,case', list(zip(_LEGACY, LEGACY_TEXTS)))
def test_old_rule_boundaries_without_active_old_rules(pattern, case):
    lang, text = case
    assert pattern.fullmatch(text)
    assert extract(text, lang, 'p', '', None, None, None, source_text=text) == ([], text)


def test_parser313_boundary_for_full_clause_and_residual():
    from shab_analyzer.parser313 import extract_parser313_leftovers
    residual = 'Test Anna, de Lausanne, à Genève, et Test Bea, de Ependes (FR), à Lausanne, sont membres du comité'
    source = residual + ' avec signature collective à deux'
    old, rest = extract_parser313_leftovers(source, 'fr', 'p', '', None, None, None)
    assert len(old) == 2 and rest == ''
    for text in (residual, source):
        assert extract(text, 'fr', 'p', '', None, None, None, source_text=source) == ([], text)


def test_old_event_without_optional_attributes():
    event = Event('p', '', 'officer_changed', 'legacy.rule', payload={'name': 'Test Anna'})
    assert Event(**vars(event)) == event
    assert event.payload == {'name': 'Test Anna'}
    assert event.role is None and event.signing is None


@pytest.mark.parametrize('index,before,after', [
 (0, 'de ses 200 parts', 'de ses 201 parts'),
 (9, 'de leurs 7 parts', 'de leurs 8 parts'),
 (10, 'titulaire de 20 parts', 'titulaire de 21 parts'),
 (11, "26'500 bons", "26'501 bons"),
])
def test_inconsistent_totals(index, before, after):
    _, _, (args, kwargs) = captured(index)
    text = args[0].replace(before, after)
    assert text != args[0]
    assert extract(text, *args[1:], **kwargs) == ([], text)
