import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser325 import extract_parser325_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('1050ea87', 'de.text.asset_transfer_receivable_and_reserves.v1', 1),
    ('29468950', 'fr.text.authorized_and_conditional_capital_clauses_changed.v1', 1),
    ('3de5399d', 'fr.text.collective_signing_restrictions_removed.v1', 1),
    ('549044ac', 'fr.text.administrator_name_corrected.v1', 1),
    ('7556b9c3', 'fr.text.administrator_residence_corrected.v1', 1),
    ('a2650bb7', 'fr.text.historical_asset_acquisition_clause_removed.v1', 1),
    ('a57155ab', 'fr.text.sole_manager_surname_corrected.v1', 1),
    ('b6bdaf31', 'fr.text.unregistrable_secretary_title_removed.v1', 1),
    ('c19ecd6c', 'de.text.formation_contribution_corrected.v1', 1),
    ('d6930320', 'fr.text.merger_wholly_owned_subsidiary_no_allocation.v1', 1),
    ('e06ec036', 'fr.text.two_persons_collective_signing.v1', 2),
    ('fa463b6d', 'de.text.dissolution_resolution_reference_added.v1', 1),
]


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
        return extract_parser325_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser325_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    result, _ = captured(prefix)
    rule = next(rule for stem, rule, _ in CASES if stem == prefix)
    return [e for e in result.events if e.rule_id == rule]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 429
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    with patch.object(parser, 'extract_parser325_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert [e for e in result.events if e.rule_id != rule] == baseline.events
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser325_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser325_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]


@pytest.mark.parametrize('prefix', ['1cf200d1', 'c9cb541c', 'e3c5c5cd', '94b72118-d3cb-46f4-8cf3-8d526586b9f2'])
def test_previous_fixtures_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    with patch.object(parser, 'extract_parser325_leftovers', lambda text, *args, **kwargs: ([], text)):
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
        events, leftover = extract_parser325_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed



@pytest.mark.parametrize('prefix', ['071d1e57', '0f24b50f', '21eda001', '238c92b1', '37d2f837', '42e77773',
    '4853703f', '6899b65f', '6aceb735', 'a6efd04c', 'bc92c8c0', 'f43edc77'])
def test_parser324_results_unchanged(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser325_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline




def test_fragment_requires_corrected_source_clause():
    _, (args, kwargs) = captured('c19ecd6c')
    for source in ['', 'unsupported', kwargs['source_text'].replace('Qualifizierte Tatbestände neu:', 'Qualifizierte Tatbestände bisher:'), kwargs['source_text'].replace('[nicht:', '[gestrichen:')]:
        events, leftover = extract_parser325_leftovers(*args, source_text=source)
        assert not events and leftover == args[0]


@pytest.mark.parametrize('prefix,old,new', [
    ('3de5399d', 'sans autre restriction', 'avec autre restriction'),
    ('a2650bb7', '628, al. 4, CO', '628, al. 3, CO'),
    ('b6bdaf31', 'non soumis à inscription', 'soumis à inscription'),
    ('d6930320', 'sämtliche Stammanteile', 'einige Stammanteile'),
    ('e06ec036', 'collective à deux', 'individuelle'),
    ('fa463b6d', 'Auflösungsbeschluss', 'Kapitalerhöhungsbeschluss'),
])
def test_unsupported_meanings_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    events, leftover = extract_parser325_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


def test_payload_semantics_and_absent_optional_person_attributes():
    transfer = selected('1050ea87')[0]
    assert transfer.event_type == 'ownership_changed'
    assert transfer.payload['reserves'] == "50'000.00"
    assert transfer.payload['consideration'] == "309'386.90"
    clauses = selected('29468950')[0]
    assert clauses.event_type == 'organization_changed'
    assert clauses.payload['authorized_clause_replaced'] is True
    assert clauses.payload['conditional_clause_changed'] is True
    signing = selected('3de5399d')[0]
    assert signing.signing == 'Kollektivunterschrift zu zweien'
    assert signing.payload['other_restrictions_removed'] is True
    assert signing.role is None and signing.payload['place'] is None
    assert selected('549044ac')[0].payload['previous_name'] != selected('549044ac')[0].payload['name']
    assert selected('7556b9c3')[0].payload['place'] == 'Chêne-Bourg'
    historical = selected('a2650bb7')[0]
    assert historical.event_type == 'organization_changed'
    assert historical.payload['previous_clause_removed'] is True
    surname = selected('a57155ab')[0]
    assert surname.person_key is None and 'name' not in surname.payload
    assert surname.payload['surname'] == 'Alhaj Kaddour'
    title = selected('b6bdaf31')[0]
    assert title.event_type == 'officer_changed'
    assert title.role is None and title.signing is None
    assert title.payload['removed_title'] == 'secrétaire générale'
    assert selected('c19ecd6c')[0].payload['corrected'] is True
    merger = selected('d6930320')[0]
    assert merger.event_type == 'company_merged'
    assert merger.payload['capital_increase'] is False and merger.payload['share_allocation'] is False
    assert all(e.signing == 'Kollektivunterschrift zu zweien' and e.role is None for e in selected('e06ec036'))
    supplement = selected('fa463b6d')[0]
    assert supplement.event_type == 'organization_changed'
    assert supplement.payload['supplementary_entry'] is True
    assert 'dissolved' not in supplement.payload
    for prefix, _, _ in CASES:
        for e in selected(prefix):
            assert Event(**vars(e)) == e


@pytest.mark.parametrize('prefix,rule,count', [case for case in CASES if case[0] != 'c19ecd6c'])
def test_complete_clauses_work_without_optional_source_text(prefix, rule, count):
    _, (args, _) = captured(prefix)
    events, leftover = extract_parser325_leftovers(*args)
    assert not leftover and len(events) == count
