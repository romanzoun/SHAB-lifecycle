import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser327 import extract_parser327_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('518fef8d', 'fr.text.historical_contribution_and_organization_mentions_removed.v1', 3), ('5404cc5f', 'fr.text.share_transfer_new_unsigned_associate.v1', 2), ('54125ed4', 'fr.text.share_transfer_and_managers_appointed.v1', 3), ('6d18ed72', 'de.text.foreign_restructuring_recognized_swiss_stay.v1', 1), ('6d50c77a', 'fr.text.manager_role_and_signing_changed.v1', 1), ('7a6515f3', 'fr.text.president_becomes_sole_administrator.v1', 1), ('930507a1', 'fr.text.associate_manager_roles_corrected.v1', 2), ('a16a5540', 'fr.text.council_president_appointed.v1', 3), ('a564e09d', 'de.text.previous_officer_text_corrected.v1', 1), ('b384c365', 'it.text.definitive_composition_stay_granted.v1', 1), ('cf527290', 'fr.text.managers_departed_powers_removed.v1', 4), ('ecba5198', 'it.text.registered_member_corrected_collective_three.v1', 1)]


def path(prefix):
    paths = list(FIXTURES.glob(prefix + '*.xml'))
    assert len(paths) == 1
    return paths[0]


@lru_cache(None)
def captured(prefix):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser327_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser327_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser327_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 368
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser327_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser327_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser327_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]


@pytest.mark.parametrize('prefix', ['1cf200d1', 'c9cb541c', 'e3c5c5cd', '94b72118-d3cb-46f4-8cf3-8d526586b9f2'])
def test_previous_fixtures_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    with patch.object(parser, 'extract_parser327_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert parse_publication_xml(fixture) == baseline
    # Existing payloads can still construct events without any new attributes.
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_invalid_dates_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    dates = set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0]))
    for date in dates:
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser327_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed


@pytest.mark.parametrize('prefix', ['05b6666b', '1968c08c', '2aa4d2fe', '2f31cf20', '300f1168', '3d9d0ae9', '400516fb', '5776a534', '7a7462ca', '7dcc63be', 'b44f8220', 'd4f4a25c'])
def test_parser326_results_unchanged(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser327_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_optional_source_not_required_and_events_roundtrip(prefix, rule, count):
    _, (args, _) = captured(prefix)
    events, leftover = extract_parser327_leftovers(*args)
    assert not leftover and len(events) == count
    for event in events:
        assert Event(**vars(event)) == event


def test_payload_semantics():
    removed, president, secretary = selected('518fef8d')
    assert removed.payload['historical_mentions_removed'] is True
    assert removed.event_type == 'organization_changed'
    assert president.payload['previous_role'] == 'secrétaire'
    assert secretary.payload['previous_role'] == 'président'
    assert president.signing == secretary.signing == 'Einzelunterschrift'
    transfer, associate = selected('5404cc5f')
    assert transfer.event_type == 'ownership_changed'
    assert transfer.payload['transferred'] == '1'
    assert transfer.payload['remaining'] == '199'
    assert associate.signing == 'ohne Zeichnungsberechtigung'
    transfer, manager1, manager2 = selected('54125ed4')
    assert transfer.payload['transferred'] == '10'
    assert manager1.signing == manager2.signing == 'Einzelunterschrift'
    assert manager1.role == 'Gesellschafter, Geschäftsführer, Präsident'
    stay = selected('6d18ed72')[0]
    assert stay.event_type == 'status_changed'
    assert stay.payload['foreign_proceedings_recognized'] is True
    assert stay.payload['end_date'] == '23.06.2021'
    assert stay.payload['stay_months'] == 12
    manager = selected('6d50c77a')[0]
    assert manager.role == 'Geschäftsführer' and manager.signing == 'Einzelunterschrift'
    assert manager.payload['previous_signing'] == 'Kollektivunterschrift zu zweien'
    assert selected('7a6515f3')[0].payload['sole_administrator'] is True
    assert all(e.payload['corrected'] and e.signing is None for e in selected('930507a1'))
    council = selected('a16a5540')
    assert [e.role for e in council] == ['Präsident', 'Sekretär', 'Kassier']
    assert [e.signing for e in council] == ['Einzelunterschrift', None, None]
    correction = selected('a564e09d')[0]
    assert correction.event_type == 'publication_corrected'
    assert correction.person_key is None and correction.signing is None
    assert correction.payload['previous_signing'] == 'Einzelunterschrift'
    stay = selected('b384c365')[0]
    assert stay.payload['definitive_stay'] is True
    assert stay.payload['months'] == '6' and stay.payload['previous_months'] == '4'
    departed1, departed2, vice, president = selected('cf527290')
    assert departed1.payload['powers_removed'] is departed2.payload['powers_removed'] is True
    assert vice.role == 'Geschäftsführerin, Vizepräsidentin'
    assert president.role == 'Geschäftsführer, Präsident'
    corrected = selected('ecba5198')[0]
    assert corrected.signing == 'Kollektivunterschrift zu dreien'
    assert corrected.payload['country'] == 'NL' and corrected.payload['corrected'] is True


@pytest.mark.parametrize('prefix,old,new', [
    ('518fef8d', "n'étant plus obligatoire", 'étant obligatoire'),
    ('5404cc5f', '199 parts', '198 parts'),
    ('5404cc5f', 'sans signature', 'avec signature'),
    ('54125ed4', '10 de ses 20', '21 de ses 20'),
    ('6d18ed72', 'anerkannt', 'nicht anerkannt'),
    ('6d50c77a', 'Einzelunterschrift', 'Kollektivunterschrift zu zweien'),
    ('7a6515f3', 'reste seule administratrice', 'ne reste pas administratrice'),
    ('930507a1', 'est rectifiée', 'est confirmée'),
    ('a16a5540', 'nommé président', 'nommé directeur'),
    ('a564e09d', '[bisher:', '[neu:'),
    ('b384c365', 'in via definitiva', 'in via provvisoria'),
    ('cf527290', 'ne sont plus gérants', 'sont gérants'),
    ('ecba5198', 'a tre', 'a due'),
])
def test_unsupported_meanings_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    events, leftover = extract_parser327_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed
