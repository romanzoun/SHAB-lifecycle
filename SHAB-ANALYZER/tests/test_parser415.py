import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser415 import extract_parser415_leftovers as extract, _LEGACY

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['1af69a9849c342e96807f821d75ad1ed403ccc81fa55152edc8ee34d7925b4f3', '2cfde85a9d2b6539551393d2384737263d062629993144c940d022908e36dfc3', '2d2e60562eb4fc5214d20d4116f16f7c62055fb8f5b06087b1e4490578c07f1c', '38904c96e22333c7a40ab03fa76a25e967792f0227e20015f819a9a2aa1b7ce4', '539376d397ec28420981b55c59bd41694ea6d66a600098fc42c586d8b4c0a9fe', '6f3b1cbef33fe3e7ae58c71d56d37a85dbec463a3a63e16b9a8b97e2ef74ccae', '7655980fc9885078f3503817dde2dfc8393dae60473ba0e4127835aa3b070005', '82c21941d872c2bdc7e54a8122885adad471c943a3425194a3d9cfe305890fdc', '9cd3862a04eafb2217ff10cf825e7a8200b7df09887235b69a0c01238858551d', 'ba618558816ffa391fe15d09b04917e3c0b431ad2a3d98f067cc14b7de9e472d', 'e3cb8216715c342351e974d9f6acf695503361a3adf3e56105b462bd16a4cebd', 'e8043613d26fb26503b5e69f05c4e5b6281364feed0205556839958425b543d7']
COUNTS = [1, 2, 1, 2, 1, 1, 1, 1, 3, 1, 2, 1]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser415_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser415_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert PARSER_VERSION == 428
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
    if index == 9:
        assert events == [] and rest == args[0]
    else:
        assert len(events) == COUNTS[index] and rest == ''


EXPECTED = [
    ('officer_changed', {'role': 'sous-directrice', 'previous_role': 'directrice', 'corrected': True}),
    ('officer_changed', {'place1': 'Genève', 'origin2': 'Grand-Saconnex'}),
    ('capital_changed', {'capital': "242'127.25", 'count': "4'842'545", 'nominal': '0.05', 'amended_date': '30 décembre 2020'}),
    ('ownership_changed', {'transferred1': '3', 'transferred2': '15', 'transferred3': '12', 'buyer_count': '30'}),
    ('status_changed', {'effective_date': '12.02.2021', 'effective_time': '12h00'}),
    ('organization_changed', {'previous_registry_id': 'CH-020.3.020.876-5', 'corrected': True}),
    ('capital_changed', {'count': '20'}),
    ('capital_changed', {'clause_count': 2, 'decision_date': '11.12.2020'}),
    ('officer_changed', {'name': 'Nicole Marc André', 'previous_name': 'Nicole Marc-André'}),
    ('capital_changed', {'founding_date': '18.06.2020', 'decision_date': '11.02.2021', 'historical_annotation': True}),
    ('capital_changed', {'previous_date': '15.05.2020', 'decision_date': '28.01.2021', 'initial_date': '25.05.2018'}),
    ('officer_changed', {'origin': 'Broc', 'previous_origin': 'Crésuz', 'corrected': True}),
]


@pytest.mark.parametrize('index', range(12))
def test_semantics(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    kind, fields = EXPECTED[index]
    assert rest == '' and events[0].event_type == kind
    for key, value in fields.items():
        assert events[0].payload[key] == value
    if index == 1:
        assert all(e.role == 'gérant' and e.signing == 'Kollektivunterschrift zu zweien' for e in events)
    if index == 2:
        assert 'fully_paid' not in events[0].payload
    if index == 3:
        assert events[1].signing == 'ohne Unterschrift'
    if index == 8:
        assert all(e.role == 'liquidateur' and e.signing is None for e in events)
        assert events[2].payload['origin'] == 'Chavannes-de-Bogis'
    if index == 10:
        from shab_analyzer.parser144 import extract_parser144_leftovers
        expected, remainder = extract_parser144_leftovers(events[0].payload['legacy_clause'], *args[1:])
        assert remainder.strip(' .') == '' and events[1:] == expected


LEGACY_TEXTS = [
    "L'inscription n° 3290 du 29.10.2020 est rectifiée en ce sens que Test Jean est sous-directeur (et non pas directeur).",
    "L'assemblée générale a introduit deux clauses statutaires relatives à des augmentations conditionnelles du capital-actions par décision du 11.12.2020; pour les détails, voir les statuts.",
    "Augmentation conditionnelle du capital-participation fondée sur la décision relative à l'octroi de droits du 27.06.2014. Nouveau capital-participation: CHF 100, entièrement libéré, divisé en 100 bons nominatifs de CHF 1. Le conseil d'administration a modifié une clause statutaire relative à une augmentation conditionnelle du capital-participation (selon décision relative à l'octroi de droits de l'assemblée générale du 27.06.2014), par décision du 15.01.2021, pour le détail cf. statuts.",
    'Die Generalversammlung hat mit Beschluss vom 28.01.2021 eine zusätzliche bedingte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten eingeführt.',
]


@pytest.mark.parametrize('pattern,text', list(zip(_LEGACY, LEGACY_TEXTS)))
def test_old_rule_boundaries_without_active_old_rules(pattern, text):
    assert pattern.fullmatch(text)
    assert extract(text, 'de' if text.startswith('Die ') else 'fr', 'p', '', None, None, None, source_text=text) == ([], text)


def test_old_event_without_optional_attributes():
    event = Event('p', '', 'officer_changed', 'legacy.rule', payload={'name': 'Test Anna'})
    assert Event(**vars(event)) == event
    assert event.payload == {'name': 'Test Anna'}
    assert event.role is None and event.signing is None


@pytest.mark.parametrize('index,old,new', [(2, "242'127.25", "242'127.26"), (3, 'pour 30 parts', 'pour 31 parts')])
def test_inconsistent_capital_or_transfer_totals(index, old, new):
    _, _, (args, kwargs) = captured(index)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract(changed, *args[1:], **kwargs) == ([], changed)


def test_history_requires_current_source_clause():
    _, _, (args, _) = captured(9)
    assert extract(*args, source_text='unrelated') == ([], args[0])
