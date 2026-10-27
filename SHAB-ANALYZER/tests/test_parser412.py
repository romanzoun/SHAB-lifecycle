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
from shab_analyzer.parser412 import extract_parser412_leftovers, _LEGACY

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = ['00f528457ec768dc432f771b95524316ead863a201fcf7c2cdaf11d16fb50aa8', '038c2965d36b8b5ec999f0c9edaa49e50d948c33e86c5962c6bb587c2eee957c', '13dba31ef2db30bb28aebf0a404ec194b91c5078129fb7c49092b526d2c68ad8', '1daefa122415e73cc78d66d5311d49e8603811e5c6c06d69194d75ea50c85104', '43e83ed8c517d1b015a36608a6b001dd99355e131f0631ac5f76f8f735b2e77d', '74adbcf36fcaf3d5553747a83128d44809d6a2fa16b6cd78d55b012ee100bf3d', '9ffe1e39df3179c000e19937ceafd19fe8cad9f7219b99e64df08fa9a4f8c314', 'c8b14370dba2c131342db4b13595067d722d208cb1b833d6a14bd29caceeaf64', 'cfab92810de45313d1fdada919d14c8252ea7fb3ea5e4e7d26e723bb727a575c', 'daa049ed0214c4b7be6d340e55abd340f8437686401ab948d6bda6857021cc0f', 'dd854fea9ea7c2747df021540508b11dfcf5f0e29073db665ecee8b4803831fb', 'eeebc024d41a7ba567f2a6dde15a51f2397fddfa16b7e8e533782c7c3c84822b']
COUNTS = [1, 2, 1, 2, 2, 2, 4, 2, 1, 1, 1, 2]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser412_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser412_leftovers', capture):
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
    added, rest = extract_parser412_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 413
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS[index] and not rest
    with patch.object(parser, 'extract_parser412_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (SUPPLIED_SHA256[index] + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('index', range(12))
def test_unknown_suffix_language_and_invalid_dates(index):
    _, (args, kwargs) = captured(index)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser412_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser412_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser412_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index', range(12))
def test_missing_optional_metadata_and_source(index):
    _, (args, kwargs) = captured(index)
    events, rest = extract_parser412_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == COUNTS[index] and not rest
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)


def test_old_event_without_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event

EXPECTED = [
    ('status_changed', {'bankruptcy_suspended': True, 'bankruptcy_entry_removed': True}),
    ('organization_changed', {'correct_uid': 'CHE-455.333.973', 'previous_uid': 'CHE-322.442.537'}),
    ('organization_changed', {'translations': '(Fidigit (Suisse) SA) (Fidigit (Svizzera) SA)'}),
    ('officer_changed', {'liquidator_uid': 'CHE-343.051.817'}),
    ('ownership_changed', {'count': '20', 'previous_count': '200', 'corrected': True}),
    ('capital_changed', {'previous1': "1'500'000", 'amount1': "2'000'000", 'amount3': "500'000"}),
    ('officer_changed', {'country4': 'FRA'}),
    ('officer_changed', {'signing_restriction': 'sauf entre eux'}),
    ('capital_changed', {'count1': '400', 'count2': "1'300", 'capital': "134'000", 'voting_privileged': True}),
    ('status_changed', {'bankruptcy_suspended': True}),
    ('officer_changed', {'signing_restrictions_removed': True}),
    ('ownership_changed', {'remaining': '18', 'count': '2'}),
]


@pytest.mark.parametrize('index', range(12))
def test_payload_semantics(index):
    _, (args, kwargs) = captured(index)
    events, rest = extract_parser412_leftovers(*args, **kwargs)
    assert not rest
    kind, fields = EXPECTED[index]
    assert events[0].event_type == kind
    for key, value in fields.items():
        assert events[0].payload[key] == value
    if index == 3:
        assert events[0].signing is None and events[0].role == 'Liquidatorin'
        assert events[1].payload['transfer_restricted'] is False
    if index == 6:
        assert [e.role for e in events] == ['Präsidentin des Verwaltungsrates', 'Vizepräsidentin des Verwaltungsrates', 'Mitglied des Verwaltungsrates', 'Mitglied des Verwaltungsrates']
        assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in events)
    if index == 7:
        for i, event in enumerate(events):
            assert event.signing == 'Kollektivprokura zu zweien'
            assert event.payload['excluded_signing_partners'] == [events[1-i].payload['name']]
    if index == 11:
        assert events[1].role == 'Gesellschafter und Direktor'
        assert events[1].signing == 'Kollektivunterschrift zu zweien'


@pytest.mark.parametrize('index', [2, 8, 11])
def test_context_required(index):
    _, (args, _) = captured(index)
    assert extract_parser412_leftovers(*args) == ([], args[0])
    assert extract_parser412_leftovers(*args, source_text='unknown') == ([], args[0])


@pytest.mark.parametrize('before,after', [("134'000", "135'000"), ('400 actions', '401 actions'), ('CHF 10,', 'CHF 11,')])
def test_inconsistent_capital_rejected(before, after):
    _, (args, kwargs) = captured(8)
    changed = args[0].replace(before, after)
    assert changed != args[0]
    assert extract_parser412_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('version,text,language', [
    (124, 'Signature collective à deux, sauf entre eux a été conférée à Exemple Anne, de France, à Paris, FRA', 'fr'),
    (234, 'Exemple Anne, secrétaire hors conseil, et Exemple Beat continuent de signer collectivement à deux, mais désormais sans autre restriction', 'fr'),
    (252, "par Exemple Anne, d’Italie, à Lausanne, nommé liquidateur", 'fr'),
    (121, 'Das Kantonsgericht hat der Beschwerde gegen die Verfügung des Kreisgerichts vom 01.01.2020 betreffend Konkurseröffnung aufschiebende Wirkung zuerkannt. Demnach wird die Eintragung betreffend Konkurs im Handelsregister gestrichen. [bisher: Konkurs eröffnet.]', 'de'),
])
def test_legacy_ownership_in_isolation(version, text, language):
    module = importlib.import_module(f'shab_analyzer.parser{version}')
    args = text, language, 'p', '', None, None, None
    events, rest = getattr(module, f'extract_parser{version}_leftovers')(*args)
    assert events and not rest.strip(' .')
    assert any(pattern.fullmatch(text) for pattern in _LEGACY)
    assert extract_parser412_leftovers(*args) == ([], text)


@pytest.mark.parametrize('version', [256, 266, 339, 392, 397, 409, 410, 411])
def test_previous_fixture_events_unchanged(version):
    import shab_analyzer.parse as parser
    module = importlib.import_module(f'tests.test_parser{version}')
    if hasattr(module, 'SUPPLIED_SHA256'):
        hashes = module.SUPPLIED_SHA256
        digests = hashes.values() if isinstance(hashes, dict) else hashes
        fixtures = [FIXTURES / (digest + '.xml') for digest in digests]
    elif hasattr(module, 'CASES') and hasattr(module, 'path'):
        fixtures = [module.path(case[0]) for case in module.CASES]
    else:
        fixtures = [FIXTURES / name for name in re.findall(r'[\da-f-]{36,64}\.xml', Path(module.__file__).read_text())]
    assert fixtures
    for fixture in fixtures:
        current = parse_publication_xml(fixture)
        with patch.object(parser, 'extract_parser412_leftovers', lambda text, *a, **kw: ([], text)):
            previous = parse_publication_xml(fixture)
        assert current == previous


@pytest.mark.parametrize('index', range(12))
def test_missing_optional_source(index):
    _, (args, _) = captured(index)
    events, rest = extract_parser412_leftovers(*args)
    if index in (2, 8, 11):
        assert events == [] and rest == args[0]
    else:
        assert len(events) == COUNTS[index] and not rest
