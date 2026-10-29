import hashlib
import importlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser409 import extract_parser409_leftovers, _LEGACY

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed supplied SHA-256 identifiers, independent of the disposable sample source.
SUPPLIED_SHA256 = [
    '0c54f22cc69d60714294cad1ef0409249671bc45f901a6e77d01697cb5a1f06b',
    '1015b07bf6649cc809aa1e69acecf3dd4e7351d93e9f5938f6bc9c8a8a911bba',
    '3d28fe98e46091dcc844fef19803151d96de13ac0a61aecd9eaba781ac42a931',
    '590e38bb1731ae4bab5f96a65b9fff9c10d94c38a1df0a6d42aa18af2bc3f86d',
    '6570f3413b33fefeda2900d89946d15c7ff2190b044016e876921e1f98a00169',
    '7f744a651f776d079156ad23a5a0fcc5c09efa9caf79c3fea7b8fe36924ef3b5',
    '81898f8e044418a728654b67278fe43cd0b8c24a6d5828b61e4038ce4319ffc5',
    '8cc42673ce67a235675b3af19bd9a22e2c9231f420018762e751c7c269610e32',
    'adca06e5e92ca53c02af24958fda3206c08e0fc06e407d197239e86b3eb31e59',
    'afc479fdbde000a06b2c5a5eefdc33d2737196a7751c5cda75e80262040ca149',
    'e8d88812af5c226ec90698436a227b89be7883e4493fde64bb8b4ee605a177c8',
    'fb580431f0c98051a8b45ead4186d37e54b22822635848cce431a0d5f6292b98',
]
COUNTS = [1, 1, 1, 1, 3, 1, 1, 2, 1, 0, 2, 1]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser409_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser409_leftovers', capture):
        result = parse_publication_xml(FIXTURES / (SUPPLIED_SHA256[index] + '.xml'))
    assert len(calls) == 1
    return result, calls[0]


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('index', range(12))
def test_complete_and_unchanged_legacy_payloads(index):
    import shab_analyzer.parse as parser
    result, (args, kwargs) = captured(index)
    added, rest = extract_parser409_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 433
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS[index] and not rest
    with patch.object(parser, 'extract_parser409_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (SUPPLIED_SHA256[index] + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('index', range(12))
def test_unknown_suffix_language_and_invalid_dates(index):
    _, (args, kwargs) = captured(index)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser409_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser409_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser409_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index', range(12))
def test_missing_optional_metadata_and_source(index):
    _, (args, kwargs) = captured(index)
    events, rest = extract_parser409_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == COUNTS[index] and not rest
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    events, rest = extract_parser409_leftovers(*args)
    if index in (7, 9, 10, 11):
        assert (events, rest) == ([], args[0])
    else:
        assert len(events) == COUNTS[index] and not rest


def test_old_event_without_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event


EXPECTED = [
    ('capital_changed', {'statutes_date': '15.01.2021', 'clause_date': '26.10.2020'}),
    ('ownership_changed', {'before': '99', 'remaining': '40', 'count': '59', 'buyer_count': '160'}),
    ('officer_changed', {'corrected': True, 'given_names': 'Manuele'}),
    ('officer_changed', {'corrected': True, 'previous_place': 'Kollum', 'previous_country': 'NL'}),
    ('officer_changed', {'name': 'Corbaz Claude'}),
    ('assets_transferred', {'agreement_date': '15.10 2020', 'assets': "13'190'000.00"}),
    ('capital_changed', {'reduced_capital': "4'600'000.00", 'destroyed_count': "80'000", 'issued_count': "80'000"}),
    ('officer_changed', {'name': 'Da Cunha Sylvie', 'origin': 'France'}),
    ('status_changed', {'bankrupt': True, 'effective_date': '05.01.2021', 'time': '08:00'}),
    None,
    ('officer_changed', {'origin1': 'Lausanne', 'place': 'Lutry'}),
    ('officer_changed', {'signing_restriction': 'avec le/la président(e)'}),
]


@pytest.mark.parametrize('index', range(12))
def test_payload_semantics(index):
    _, (args, kwargs) = captured(index)
    events, rest = extract_parser409_leftovers(*args, **kwargs)
    assert not rest
    if index == 9:
        assert not events
        return
    kind, fields = EXPECTED[index]
    assert events[0].event_type == kind
    for key, value in fields.items():
        assert events[0].payload[key] == value
    if index == 2:
        assert events[0].role == 'Direktor' and events[0].signing == 'Einzelunterschrift'
    if index == 3:
        assert events[0].role is None and events[0].signing is None
    if index == 4:
        assert [e.role for e in events[:2]] == ['Stellvertretender Direktor'] * 2
        assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in events)
        module = importlib.import_module('shab_analyzer.parser140')
        old, _ = module.extract_parser140_leftovers(args[0].partition('. ')[2], *args[1:])
        assert events[2:] == old
    if index in (7, 10):
        assert all(e.role == 'Liquidator' and e.signing == 'Einzelunterschrift' for e in events)
    if index == 10:
        assert events[1].payload['place'] is None
    if index == 11:
        assert events[0].role == 'Mitglied des Stiftungsrates'
        assert events[0].signing == 'Kollektivunterschrift zu zweien'


@pytest.mark.parametrize('version,text,language', [
    (105, 'Nouveau membre du conseil de fondation avec le président: Exemple Anne, de Berne, à Lausanne', 'fr'),
    (105, 'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vermögensübertragungsvertrag vom 15.10.2020 Aktiven von CHF 100 auf die Beispiel AG, in Bern (CHE-123.456.789). Gegenleistung: CHF 100', 'de'),
    (140, 'Exemple Anne et Exemple Beat sont nommés liquidateurs', 'fr'),
    (140, 'Signature collective à deux a été conférée à Exemple Anne, nommé sous-directeur; sa procuration est radiée', 'fr'),
    (107, 'Die Generalversammlung hat mit Beschluss vom 15.01.2021 die Statutenbestimmung über die bedingte Kapitalerhöhung vom 26.10.2020 geändert. [bisher: Die Generalversammlung hat mit Beschluss vom 26.10.2020 die Statutenbestimmung über die bedingte Kapitalerhöhung vom 01.01.2020 geändert.]', 'de'),
    (252, 'Die Generalversammlung hat mit Beschluss vom 15.01.2021 die Statutenbestimmung über die bedingte Kapitalerhöhung vom 26.10.2020 geändert. [gestrichen: Die Generalversammlung hat mit Beschluss vom 26.10.2020 die Statutenbestimmung über die bedingte Kapitalerhöhung vom 01.01.2020 geändert.]', 'de'),
    (194, 'Bei der letzten Publikation wurde der bisherige Wohnort nicht als Bishereintrag aufgeführt: Beispiel, Beat, von Bern, in Bern, Gesellschafter und Geschäftsführer, mit Einzelunterschrift, mit 20 Stammanteilen zu je CHF 100 [bisher: in Zürich, Gesellschafter und Geschäftsführer, mit Einzelunterschrift, mit 20 Stammanteilen zu je CHF 100]', 'de'),
])
def test_legacy_ownership_in_isolation(version, text, language):
    module = importlib.import_module(f'shab_analyzer.parser{version}')
    args = text, language, 'p', '', None, None, None
    events, rest = getattr(module, f'extract_parser{version}_leftovers')(*args)
    assert events and not rest.strip(' .')
    assert any(pattern.fullmatch(text) for pattern in _LEGACY)
    assert extract_parser409_leftovers(*args) == ([], text)


@pytest.mark.parametrize('text', ['', 'Unknown clause', 'toutes deux'])
def test_unknown_is_unchanged(text):
    assert extract_parser409_leftovers(text, 'fr', 'p', '', None, None, None) == ([], text)


@pytest.mark.parametrize('index', [7, 9, 10, 11])
def test_unrelated_source_does_not_supply_signing_or_context(index):
    _, (args, _) = captured(index)
    assert extract_parser409_leftovers(*args, source_text='Unrelated signature individuelle.') == ([], args[0])


def test_invalid_irregular_date():
    _, (args, kwargs) = captured(5)
    changed = args[0].replace('15.10 2020', '31.02 2020')
    assert extract_parser409_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('old,new', [('40 parts', '41 parts'), ('160 parts de CHF 100', '160 parts de CHF 999')])
def test_inconsistent_transfer_is_unchanged(old, new):
    _, (args, kwargs) = captured(1)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser409_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index', range(12))
def test_previous_release_unchanged(index):
    import shab_analyzer.parse as parser
    from tests.test_parser408 import SUPPLIED_SHA256 as PREVIOUS
    path = FIXTURES / (PREVIOUS[index] + '.xml')
    result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser409_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(path)
