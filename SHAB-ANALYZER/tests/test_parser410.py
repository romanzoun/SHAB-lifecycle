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
from shab_analyzer.parser410 import extract_parser410_leftovers, _LEGACY

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = [
    '18109032bc4600aa75f0e23000b740445a735bf3de6923b593b98f4812a1024b',
    '2418aaec45d906ad312b814574acac48ee6831e3f0b91c09d21404870ea4015b',
    '4422446cae16b3ca96414079d4cf694a00d81c265a8e6c6928b3990c46f5c22e',
    '49ed4e9db8e2ca2194493ea43a6891142a9c2967e1454e437b7a4bc67c56e661',
    '59d2da83f9ff47aa5b6aabe8fa806687a6935e39c898fef904388dfe6186192c',
    '5bc2cf3ec540b26b41f05c7be567864de8c88397a3f3837cb6ea76bf6028f313',
    '5feccada51860f4dd3d2ec5dc3f91b477d8df0f7faada6e9910a564cd0b1c413',
    'a2c3a76dfdc5b7321c348210bea8b1092ad7551711b7e13290c2cc9d752a0b23',
    'aa1388274e5d40757f7de7cbf7cfa4d81f66ec276dd70b70e4269cf61476c77a',
    'ab6432fbe58926e00973b011c64fdf7e4a18024eb65304b905c394e22908abf6',
    'd869e3f06e47bf59ecf45b90d6b967379e6bd267924c75d0c3f16a771aa37e72',
    'e7a493534d7193c7d6b49dfdbc481ade85ed52e6177a8ece516731c4570dfbb2',
]
COUNTS = [1, 2, 1, 1, 3, 2, 2, 3, 1, 1, 1, 1]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser410_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser410_leftovers', capture):
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
    added, rest = extract_parser410_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 440
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS[index] and not rest
    with patch.object(parser, 'extract_parser410_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (SUPPLIED_SHA256[index] + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('index', range(12))
def test_unknown_suffix_language_and_invalid_dates(index):
    _, (args, kwargs) = captured(index)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser410_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser410_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser410_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index', range(12))
def test_missing_optional_metadata_and_source(index):
    _, (args, kwargs) = captured(index)
    events, rest = extract_parser410_leftovers(*args[:4], None, None, None)
    assert len(events) == COUNTS[index] and not rest
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)


def test_old_event_without_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event


EXPECTED = [
    ('organization_changed', {'entry': '864', 'corrected': True}),
    ('capital_changed', {'authorization_date': '29.12.2020', 'clause_date': '31.08.2020'}),
    ('organization_changed', {'previous_notice': '249', 'correct_notice': '252', 'corrected': True}),
    ('officer_changed', {'previous_place': 'Regensdorf', 'count': '200', 'previous_count': '100'}),
    None,
    ('ownership_changed', {'remaining': '70', 'count': '70', 'country': 'FRA'}),
    ('officer_changed', {'origin1': 'Bémont (JU)', 'origin2': 'Neuchâtel'}),
    ('officer_changed', {'origin1': 'Equateur', 'origin2': 'Saint-Barthélemy (VD)'}),
    ('ownership_changed', {'registry_id': 'LL08659', 'place': 'Labuan', 'country': 'Malaisie'}),
    ('capital_changed', {'authorization_date': '28.06.2018', 'decision_date': '17.12.2020'}),
    ('ownership_changed', {'count1': '18', 'remaining1': '72', 'count2': '4', 'remaining2': '68'}),
    ('ownership_changed', {'count': '130', 'before': '150', 'remaining': '20', 'buyer5_id': '00123426'}),
]


@pytest.mark.parametrize('index', range(12))
def test_payload_semantics(index):
    _, (args, kwargs) = captured(index)
    events, rest = extract_parser410_leftovers(*args, **kwargs)
    assert not rest
    if index == 4:
        from shab_analyzer import parser100
        prefix = args[0].partition(". L'assemblée")[0]
        old, rest = parser100.extract_parser100_leftovers(prefix, *args[1:])
        assert not rest and events[:1] == old
        assert events[1].event_type == 'capital_changed'
        assert events[1].payload['clause_date'] == '17.12.2020'
        assert events[2].role == 'Mitglied des Verwaltungsrates'
        assert events[2].signing is None
        return
    kind, fields = EXPECTED[index]
    assert events[0].event_type == kind
    for key, value in fields.items():
        assert events[0].payload[key] == value
    if index == 3:
        assert events[0].role == 'Gesellschafter und Geschäftsführer'
        assert events[0].signing == 'Einzelunterschrift'
    if index == 5:
        assert events[1].role == 'Gesellschafterin und Geschäftsführerin'
        assert events[1].signing is None
    if index in (6, 7):
        assert all(e.role == 'Prokurist' and e.signing == 'Kollektivprokura zu zweien' for e in events)
    if index == 7:
        for i, event in enumerate(events):
            assert event.payload['excluded_signing_partners'] == [e.payload['name'] for j, e in enumerate(events) if j != i]
    if index == 11:
        assert events[0].payload['recipient_counts'] == ['10', '10', '10', '10', '60', '10', '20']
        assert events[0].payload['representative'] == events[0].payload['coowner1']


@pytest.mark.parametrize('version,text,language', [
    (196, 'Die Generalversammlung hat mit Beschluss vom 29.12.2020 die Statutenbestimmung über die bedingte Kapitalerhöhung vom 31.08.2020 geändert', 'de'),
    (100, "Suppression de la clause statutaire relative à l'augmentation autorisée du capital-actions fondée sur la décision d'autorisation du 17.07.2020", 'fr'),
    (119, 'Procuration collective à deux, toutefois pas entre eux, est conférée à Exemple Anne, à Berne, et Exemple Beat, au Locle, tous deux de Genève', 'fr'),
    (206, 'Die Gesellschaft hat mit Beschluss vom 29.12.2020 eine weitere genehmigte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten beschlossen. [bisher: Die Gesellschaft hat mit Beschluss vom 31.08.2020 eine weitere genehmigte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten beschlossen.]', 'de'),
])
def test_legacy_ownership_in_isolation(version, text, language):
    module = importlib.import_module(f'shab_analyzer.parser{version}')
    args = text, language, 'p', '', None, None, None
    events, rest = getattr(module, f'extract_parser{version}_leftovers')(*args)
    assert events and not rest.strip(' .')
    assert any(pattern.fullmatch(text) for pattern in _LEGACY)
    assert extract_parser410_leftovers(*args) == ([], text)


@pytest.mark.parametrize('index,key,value', [(10, '18', '19'), (11, '130', '131'), (11, '20 parts', '21 parts')])
def test_inconsistent_transfer_totals_rejected(index, key, value):
    _, (args, kwargs) = captured(index)
    changed = args[0].replace(key, value)
    assert extract_parser410_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_existing_conditional_capital_payload_delegated():
    from shab_analyzer import parser196
    _, (args, kwargs) = captured(1)
    suffix = args[0].split('. ', 1)[1]
    old, rest = parser196.extract_parser196_leftovers(suffix, *args[1:])
    events, _ = extract_parser410_leftovers(*args, **kwargs)
    assert old and not rest
    assert events[1:] == old
    assert extract_parser410_leftovers(suffix, *args[1:], **kwargs) == ([], suffix)


@pytest.mark.parametrize('version', [293, 300, 329, 383, 387, 409])
def test_previous_fixture_events_unchanged(version):
    import shab_analyzer.parse as parser
    module = importlib.import_module(f'tests.test_parser{version}')
    fixtures = ([FIXTURES / (digest + '.xml') for digest in module.SUPPLIED_SHA256]
                if hasattr(module, 'SUPPLIED_SHA256') else [module.path(case[0]) for case in module.CASES])
    for fixture in fixtures:
        current = parse_publication_xml(fixture)
        with patch.object(parser, 'extract_parser410_leftovers', lambda text, *a, **kw: ([], text)):
            previous = parse_publication_xml(fixture)
        assert current == previous
