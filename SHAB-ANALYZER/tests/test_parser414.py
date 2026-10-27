import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser414 import extract_parser414_leftovers as extract, _LEGACY

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = [
    '00032fbcc3492ddc8dcfc62999803beca7060b4e3c110e8e21ed1e85387ff7ee',
    '23c05045efdee772ca5a70b89ed526a9523d0cda054304ec2d956c26becee1ec',
    '32c51c371b4de3b42a9a7af2e1800e53761648eca5b75a0801e8a1afaccb699d',
    '4f79e6ec5cd02c3cccd079aa1a86ce44dd3196618719ebd6c9982aea9a627e67',
    '5f24505db7cdf52602a2e6c470837a8169b8e9b4a9455df2c0c0a53e96f92dae',
    '7c5b9e8ff0f0bffd7efb5cb620a3aa24dbbf2187e2804b99b35a192acdeb01c1',
    '83b1ebf416aebc898089caf796e46d3f52ee77c0e15783436b92b8eacf5b66cf',
    'a02e4de8ff36b7528cecd8b4d1e186064e12cc992dc16d41675aa50f5d7095b1',
    'b16823b9886f341caf7e2a78e1f8ed2e5748e5adb783919e8b02038f35a1f551',
    'b854c666cce4527bf0fe9a3c58a8e8e6f71128aad45c96483b5340743ea70a8b',
    'bbc423608641016fb67a38e38ef0d43b8eee837b6f9369c6fdd5c2a9fe5054ae',
    'e60eea46c840dd23e1b51ae6903a27e29d26c9f7b0721babf0fd69bf443c3c61',
]
COUNTS = [1, 1, 1, 1, 2, 2, 1, 2, 1, 1, 1, 1]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser414_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser414_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert PARSER_VERSION == 415
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
    if index == 4:
        assert events == [] and rest == args[0]
    else:
        assert len(events) == COUNTS[index] and rest == ''


EXPECTED = [
    ('officer_changed', {'name': 'Gonzalez Osma Sandra'}),
    ('assets_transferred', {'assets': "705'731.25", 'liabilities': "249'173.15", 'consideration': "456'558.10", 'currency': 'CHF'}),
    ('branch_changed', {'place': 'Langenthal', 'branch_registry_id': 'CH-036.9051.786-6', 'mention_removed': True}),
    ('branch_changed', {'place': 'Teufen', 'branch_canton': 'AR', 'registration_date': '18.03.1975'}),
    ('officer_changed', {'previous_role': 'membro', 'corrected': True}),
    ('ownership_changed', {'transferred': '30', 'buyer_count': '120', 'remaining1': '245', 'remaining2': '70'}),
    ('capital_changed', {'decision_date': '26.01.2021', 'introduced_date': '18.04.2019'}),
    ('officer_changed', {'nationality1': 'serbischer', 'previous_nationality1': 'serbisch-montenegrinischer', 'corrected': True}),
    ('officer_changed', {'name': 'Binz Patrik Albert', 'previous_name': 'Binz Patrick Albert', 'corrected': True}),
    ('officer_changed', {'powers_revoked': True}),
    ('organization_changed', {'auditor_uid': 'CHE-105.952.747', 'previous_registry_id': 'CH-020.3.927.906-5', 'corrected': True}),
    ('officer_changed', {'previous_origin': 'Friltschen TG', 'previous_role': 'Gesellschafter', 'corrected': True}),
]


@pytest.mark.parametrize('index', range(12))
def test_payload_semantics(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    kind, fields = EXPECTED[index]
    assert rest == '' and events[0].event_type == kind
    for key, value in fields.items():
        assert events[0].payload[key] == value
    if index in (4, 7, 8, 11):
        assert all(e.signing == 'Einzelunterschrift' for e in events)
    if index == 0:
        assert events[0].signing == 'Einzelprokura'
    if index == 4:
        assert [e.role for e in events] == ['presidente', 'membro']
        assert [e.payload['previous_role'] for e in events] == ['membro', 'presidente']
        assert [e.payload['name'] for e in events] == ['Boyraz, Duran', 'Boyraz, Aylin']
    if index == 5:
        assert events[1].role == 'Gesellschafter' and events[1].signing == 'ohne Unterschrift'
    if index == 9:
        assert events[0].signing == 'ohne Unterschrift'
        assert 'removed' not in events[0].payload and 'deleted' not in events[0].payload


LEGACY_TEXTS = [
    'Die Gesellschaft hat mit Beschluss vom 26.01.2021 die mit Beschluss vom 18.04.2019 eingeführte Bestimmung betreffend genehmigter Kapitalerhöhung gemäss näherer Umschreibung in den Statuten geändert.',
    "Radiation de la mention de l'existence d'une succursale à Langenthal.",
    'Procuration individuelle a été conférée à Test Anna; sa procuration est modifiée en ce sens.',
    'Der Eintrag Nr. 905 vom 25.01.2021 (SHAB vom 28.01.2021, Id 1005085913) ist wie folgt berichtigt: Binz (und nicht Bintz) Patrik, Präsident, Einzelunterschrift.',
    'Vermögensübertragung: Die Stiftung überträgt gemäss Vertrag vom 14.10.2020 und Verfügung der Aufsichtsbehörde vom 10.12.2020 Aktiven von CHF 100 auf die Test AG, in Bern (CHE-110.350.028). Gegenleistung: keine.',
    'Die Gesellschaft hat mit Beschluss vom 26.01.2021 die mit Beschluss vom 18.04.2019 eingführte und mit Beschluss vom 18.04.2020 geänderte Bestimmung betreffend genehmigter Kapitalerhöhung gemäss näherer Umschreibung in den Statuten geändert.',
    "Test Anna n'est plus administrateur; ses pouvoirs sont radiés.",
]


@pytest.mark.parametrize('pattern,text', list(zip(_LEGACY, LEGACY_TEXTS)))
def test_old_rule_boundaries_even_without_active_old_rule(pattern, text):
    assert pattern.fullmatch(text)
    assert extract(text, 'de' if text.startswith(('Die ', 'Der ', 'Vermögens')) else 'fr', 'p', '', None, None, None, source_text=text) == ([], text)


def test_old_event_without_new_optional_attributes():
    event = Event('p', '2020-01-01', 'officer_changed', 'legacy.rule', payload={'name': 'Test Anna'})
    assert Event(**vars(event)) == event
    assert event.payload == {'name': 'Test Anna'}
    assert event.signing is None and event.role is None


def test_corrected_roles_require_matching_source():
    _, _, (args, kwargs) = captured(4)
    assert extract(*args, source_text='unrelated') == ([], args[0])
    assert extract(*args, source_text=kwargs['source_text'].replace('Duran', 'Unknown')) == ([], args[0])


def test_inconsistent_share_total_rejected():
    _, _, (args, kwargs) = captured(5)
    changed = args[0].replace('120 parts', '121 parts')
    assert extract(changed, *args[1:], **kwargs) == ([], changed)
