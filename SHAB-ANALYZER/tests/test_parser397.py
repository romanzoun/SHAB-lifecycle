import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser397 import extract_parser397_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = ['28d975f9e40d57a29cd0e6bc255228bfa31f7cad73f556b717923c5013e98ed2', '357caeafdaa94596286f365d154d71bd7f6052f8d5e5e7d88995b196dd9c951c', '5af880e026474a3ce47e07b0f213f4357f9823728fb71dda8f9c94154ac321b8', '6535c970b6ee76142872fc71c4663afb900c15d82419658339bc2ef8c6f99db7', '67ae1de93c829cc2779974f18567881ba26540bef8fe41977ea1f043590b0909', '681482eedafaef769969fa2bf7655adf9f634321476855a22069858c385dbba7', '7020f7e7d90a8992fb56e82916f61d2660b41ee16090204ab08b5c2302edc1c4', '70dc01bf20f9f203235206c40e14a68dca04329fceb7c905920a8f838b932353', '7f0c7acfeed1ae3f9ff49a7630910d298010970b1241f5a6a6e9255805d25e1d', '983c8c46cac0aaf15f5a14b3fd3dcfa39bae5be05c8c0999554a5e3e7d5bc3a8', 'c95a86ae2b88bfd6ce00f09d6f7c44cb454b2aead4210d8ac1eb512ef39b8939', 'ea3591dc16456363da170cb415f96fabd501154c24ba9d9a9e75d3589edeb7b6']
CONTEXT_REQUIRED = set()
COUNTS = {'357caeaf': 2, '67ae1de9': 3}


@lru_cache(None)
def captured(digest):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser397_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser397_leftovers', capture):
        result = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert len(calls) == 1
    return result, calls[0]

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_complete_and_unchanged_legacy_payloads(digest):
    import shab_analyzer.parse as parser
    result, (args, kwargs) = captured(digest)
    added, rest = extract_parser397_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 424
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS.get(digest[:8], 1) and not rest
    with patch.object(parser, 'extract_parser397_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_unknown_suffix_and_language_preserve_input(digest):
    _, (args, kwargs) = captured(digest)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser397_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser397_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_missing_optional_source_and_invalid_dates(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser397_leftovers(*args)
    if digest[:8] in CONTEXT_REQUIRED:
        assert not events and rest == args[0]
    else:
        assert len(events) == COUNTS.get(digest[:8], 1) and not rest
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser397_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_old_event_without_new_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event




@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_event_semantics(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser397_leftovers(*args, **kwargs)
    assert not rest
    if digest.startswith(('28d9', '357c', '67ae', '6814', '7020')):
        assert all(e.event_type == 'officer_changed' and e.person_key for e in events)
        assert all(e.signing == ('Kollektivunterschrift zu zweien' if digest.startswith('28d9') else 'Einzelunterschrift') for e in events)
    if digest.startswith('357c'):
        assert events[0].payload['origin2'] == 'Bourg-en-Lavaux'
        assert all(e.role is None for e in events)
    if digest.startswith('6814'):
        assert events[0].payload['previous_role'] == 'directeur'
        assert events[0].payload['place'] == 'Genève'
    if digest.startswith(('5af8', '70dc')):
        assert events[0].event_type == 'status_changed'
        assert events[0].payload['until_date'] in ('05.05.2021', '10.02.2021')
    if digest.startswith('6535'):
        assert [events[0].payload[k] for k in ('count', 'previous_d', 'previous_e', 'previous_f')] == ['30', '10', '20', '70']
    if digest.startswith('7f0c'):
        assert events[0].payload['absorbed_uid_raw'] == 'CHE-455-944.792'
        assert events[0].payload['capital_increase'] is False
    if digest.startswith('983c'):
        assert events[0].payload['loan_claim'] == "97'675'870.00"
        assert 'liabilities' not in events[0].payload
    if digest.startswith('c95a'):
        assert events[0].event_type == 'address_changed' and events[0].payload['removed'] is True
    if digest.startswith('ea35'):
        assert events[0].event_type == 'seat_changed' and events[0].payload['place'] == 'Villars-sur-Glâne'


def test_legacy_signing_clauses_keep_ownership():
    from shab_analyzer.parser146 import extract_parser146_leftovers
    from shab_analyzer.parser252 import extract_parser252_leftovers
    cases = [
        (extract_parser146_leftovers, 'Exemple Anne, désormais seule administratrice, signe maintenant individuellement'),
        (extract_parser252_leftovers, 'Exemple Anne, désormais à Lausanne, signe maintenant individuellement'),
    ]
    for old_parser, text in cases:
        args = text, 'fr', 'p', '', None, None, None
        events, rest = old_parser(*args)
        assert events and not rest
        assert extract_parser397_leftovers(*args) == ([], text)


@pytest.mark.parametrize('digest', [
    '1855c3abe279580b8806de34447fdc1f75832e8ebc2773afe15f19d7b9459311',
    '2bfe63c21628baa119c054da99ab2f48e32db8af946cc9b50f59376bc86bf64b',
    '77f41871b77981f2c97e4cf39bd4a74f4ea769e78b4443229fba31bc789de90f',
    'bfe02dbcec18d02da123c1d47a524bd09ed601a8eef5e27d46cd9f26cecc6422',
])
def test_existing_fixture_results_unchanged(digest):
    import shab_analyzer.parse as parser
    path = FIXTURES / (digest + '.xml')
    result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser397_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(path)


def test_related_legacy_variants_keep_ownership():
    from shab_analyzer.parser366 import extract_parser366_leftovers
    from shab_analyzer.parser370 import extract_parser370_leftovers
    from shab_analyzer.parser382 import extract_parser382_leftovers
    from shab_analyzer.parser394 import extract_parser394_leftovers
    cases = [
        (extract_parser366_leftovers, 'Mit Entscheid vom 09.12.2020 hat das Bezirksgericht Beispiel eine provisorische Nachlassstundung um zwei auf insgesamt vier Monate bis zum 10.02.2021 verlängert', 'de'),
        (extract_parser370_leftovers, "Liquidateurs: l'associé gérant Exemple Jean et la directrice Exemple Anne, lesquels continuent à signer individuellement", 'fr'),
        (extract_parser382_leftovers, 'Exemple Jean et Exemple Anne, qui est maintenant de Lausanne, signent désormais individuellement', 'fr'),
        (extract_parser394_leftovers, 'Signature collective à deux a été conférée à Exemple Anne', 'fr'),
    ]
    for predecessor, text, language in cases:
        args = text, language, 'p', '', None, None, None
        events, rest = predecessor(*args)
        assert events and not rest
        assert extract_parser397_leftovers(*args) == ([], text)
