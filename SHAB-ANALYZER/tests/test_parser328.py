import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser328 import extract_parser328_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('03dcc069', 'fr.text.head_office_capital_recorded.v1', 1), ('315da231', 'de.text.partnership_dissolved_business_continued.v1', 1), ('353d9e29', 'fr.text.surname_spelling_corrected.v1', 1), ('693c452c', 'de.text.bankruptcy_revoked_previous_registration_restored.v1', 1), ('7c27565a', 'fr.text.dissolution_and_liquidators_appointed.v1', 4), ('8889623a', 'fr.text.board_presidency_exchanged.v1', 4), ('a5f4be23', 'fr.text.board_president_appointed_signing_retained.v1', 2), ('bbf607eb', 'de.text.authorized_capital_provision_changed.v1', 1), ('c332722f', 'fr.text.english_company_name_added.v1', 1), ('ce010fcd', 'fr.text.definitive_composition_stay_extended.v1', 1), ('cfbe1db2', 'fr.text.authorized_clause_removed_conditional_clause_introduced.v1', 1), ('f0fd9d83', 'fr.text.conditional_capital_clause_changed.v1', 1)]


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
        return extract_parser328_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser328_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser328_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 344
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser328_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser328_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser328_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]


@pytest.mark.parametrize('prefix', ['1cf200d1', 'c9cb541c', 'e3c5c5cd', '94b72118-d3cb-46f4-8cf3-8d526586b9f2'])
def test_previous_fixtures_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    with patch.object(parser, 'extract_parser328_leftovers', lambda text, *args, **kwargs: ([], text)):
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
        events, leftover = extract_parser328_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed


@pytest.mark.parametrize('prefix', ['05b6666b', '1968c08c', '2aa4d2fe', '2f31cf20', '300f1168', '3d9d0ae9', '400516fb', '5776a534', '7a7462ca', '7dcc63be', 'b44f8220', 'd4f4a25c'])
def test_parser326_results_unchanged(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser328_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_optional_source_not_required_and_events_roundtrip(prefix, rule, count):
    _, (args, _) = captured(prefix)
    events, leftover = extract_parser328_leftovers(*args)
    if prefix in {'03dcc069', '7c27565a', '8889623a'}:
        assert not events and leftover == args[0]
        return
    assert not leftover and len(events) == count
    for event in events:
        assert Event(**vars(event)) == event



def test_payload_semantics():
    capital = selected('03dcc069')[0]
    assert capital.event_type == 'capital_changed'
    assert capital.payload['capital'] == "4'000'000.00"
    assert capital.payload['currency'] == 'USD'
    assert capital.payload['scope'] == 'head_office'
    continued = selected('315da231')[0]
    assert continued.payload['dissolved'] is True
    assert continued.payload['business_continued'] is True
    corrected = selected('353d9e29')[0]
    assert corrected.event_type == 'publication_corrected'
    assert corrected.person_key is None and corrected.signing is None
    assert corrected.payload['corrected'] is True
    assert selected('693c452c')[0].payload['bankruptcy_revoked'] is True
    dissolution, *liquidators = selected('7c27565a')
    assert dissolution.payload['dissolved'] is True
    assert len(liquidators) == 3
    assert all(e.role == 'Liquidator' and e.signing == 'Einzelunterschrift' for e in liquidators)
    board = selected('8889623a')
    assert [e.role for e in board] == ['Verwaltungsratspräsident', 'Vizepräsident', 'Verwaltungsrat', 'Verwaltungsrat']
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in board)
    assert board[0].payload['previous_role'] == 'vice-président'
    assert board[1].payload['previous_role'] == 'président'
    president, director = selected('a5f4be23')
    assert president.role == 'Verwaltungsratspräsident'
    assert director.role == 'Verwaltungsrat, Generaldirektor'
    assert director.payload['previous_role'] == 'président'
    assert selected('bbf607eb')[0].event_type == 'capital_changed'
    name = selected('c332722f')[0]
    assert name.event_type == 'organization_changed'
    assert name.payload['english_name'].endswith('Lancy/Geneva branch')
    stay = selected('ce010fcd')[0]
    assert stay.payload['definitive_stay'] is True
    assert stay.payload['end_date'] == '14.09.2020'
    clauses = selected('cfbe1db2')[0]
    assert clauses.payload['authorized_clause_removed'] is True
    assert clauses.payload['conditional_clause_introduced'] is True
    assert selected('f0fd9d83')[0].payload['decision_date'] == '23.06.2020'


@pytest.mark.parametrize('prefix', ['518fef8d', '5404cc5f', '54125ed4', '6d18ed72', '6d50c77a', '7a6515f3', '930507a1', 'a16a5540', 'a564e09d', 'b384c365', 'cf527290', 'ecba5198'])
def test_parser327_results_unchanged(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser328_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline


@pytest.mark.parametrize('prefix', ['03dcc069', '7c27565a', '8889623a'])
def test_missing_or_inconsistent_source_preserved(prefix):
    _, (args, kwargs) = captured(prefix)
    for source in ['', kwargs['source_text'] + ' UNKNOWN_SUFFIX']:
        events, leftover = extract_parser328_leftovers(*args, source_text=source)
        assert not events and leftover == args[0]


@pytest.mark.parametrize('prefix,old,new', [
    ('315da231', 'aufgelöst', 'nicht aufgelöst'),
    ('353d9e29', 'est rectifiée', 'est confirmée'),
    ('693c452c', 'widerrufen', 'bestätigt'),
    ('7c27565a', 'sont nommés liquidateurs', 'ne sont plus liquidateurs'),
    ('8889623a', 'nommé président', 'nommé directeur'),
    ('a5f4be23', 'collectivement à deux', 'individuellement'),
    ('bbf607eb', 'genehmigte Kapital', 'bedingte Kapital'),
    ('c332722f', 'version anglaise', 'version allemande'),
    ('ce010fcd', 'définitif', 'provisoire'),
    ('cfbe1db2', 'Suppression', 'Introduction'),
    ('f0fd9d83', 'a été modifiée', 'a été supprimée'),
])
def test_unsupported_meanings_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    events, leftover = extract_parser328_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed
