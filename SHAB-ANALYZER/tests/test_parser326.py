import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser326 import extract_parser326_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('05b6666b', 'fr.text.administrator_president_appointed_liquidator.v1', 1), ('1968c08c', 'fr.text.foreign_resident_administrator_president_appointed.v1', 1), ('2aa4d2fe', 'de.text.asset_transfer_with_property_and_shares.v1', 1), ('2f31cf20', 'fr.text.audit_waiver_mention_removed.v1', 1), ('300f1168', 'de.text.organization_defect_proceedings_closed.v1', 1), ('3d9d0ae9', 'fr.text.unlimited_partner_appointed_individual_signing.v1', 1), ('400516fb', 'fr.text.sole_proprietorship_deleted_after_contribution.v1', 1), ('5776a534', 'it.text.bankruptcy_reopened_after_appeal_rejected.v1', 1), ('7a7462ca', 'fr.text.audit_waiver_mention_removed.v1', 1), ('7dcc63be', 'fr.text.asset_transfer_shares_and_receivable.v1', 1), ('b44f8220', 'de.text.erroneous_statutes_amendment_removed.v1', 1), ('d4f4a25c', 'fr.text.collective_signing_partners_changed.v1', 6)]


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
        return extract_parser326_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser326_leftovers', capture):
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
    assert PARSER_VERSION == 379
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    with patch.object(parser, 'extract_parser326_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert [e for e in result.events if e.rule_id != rule] == baseline.events
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser326_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser326_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]


@pytest.mark.parametrize('prefix', ['1cf200d1', 'c9cb541c', 'e3c5c5cd', '94b72118-d3cb-46f4-8cf3-8d526586b9f2'])
def test_previous_fixtures_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    with patch.object(parser, 'extract_parser326_leftovers', lambda text, *args, **kwargs: ([], text)):
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
        events, leftover = extract_parser326_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed




@pytest.mark.parametrize('prefix', ['1050ea87', '29468950', '3de5399d', '549044ac', '7556b9c3', 'a2650bb7', 'a57155ab', 'b6bdaf31', 'c19ecd6c', 'd6930320', 'e06ec036', 'fa463b6d'])
def test_parser325_results_unchanged(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser326_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_optional_source_not_required_and_events_roundtrip(prefix, rule, count):
    _, (args, _) = captured(prefix)
    events, leftover = extract_parser326_leftovers(*args)
    assert not leftover and len(events) == count
    for event in events:
        assert Event(**vars(event)) == event


def test_payload_semantics():
    assert selected('05b6666b')[0].signing is None
    assert selected('1968c08c')[0].payload['country'] == 'FRA'
    transfer = selected('2aa4d2fe')[0]
    assert transfer.event_type == 'ownership_changed'
    assert transfer.payload['shares'] == "250'000"
    assert transfer.payload['property_reference'] == 'GB Feusisberg Nr. D5751'
    assert selected('2f31cf20')[0].payload['waiver_mention_removed'] is True
    assert 'audit_required' not in selected('2f31cf20')[0].payload
    assert selected('300f1168')[0].payload['proceedings_closed'] is True
    assert selected('3d9d0ae9')[0].signing == 'Einzelunterschrift'
    assert selected('400516fb')[0].event_type == 'company_deleted'
    bankruptcy = selected('5776a534')[0]
    assert bankruptcy.event_type == 'status_changed'
    assert bankruptcy.payload['reopening_time'] == '09:00'
    assert bankruptcy.payload['bankruptcy_reopened'] is True
    assert selected('7dcc63be')[0].payload['agreement_date'] == '16.06.2020'
    assert selected('b44f8220')[0].payload['erroneous_entry_removed'] is True
    persons = selected('d4f4a25c')
    assert len(persons) == 6
    assert [len(e.payload['signing_partners']) for e in persons] == [1, 1, 1, 2, 2, 2]
    assert persons[3].payload['place'] == 'Chénens'
    assert all(e.role is None for e in persons)


@pytest.mark.parametrize('prefix,old,new', [
    ('05b6666b', 'liquidateur', 'directeur'),
    ('2f31cf20', 'radiation', 'confirmation'),
    ('300f1168', 'behoben', 'nicht behoben'),
    ('400516fb', 'est radiée', 'sera radiée'),
    ('5776a534', 'ha respinto', 'ha accolto'),
    ('b44f8220', 'keine Statutenänderung', 'eine Statutenänderung'),
    ('d4f4a25c', 'ou Ray', 'et Ray'),
    ('7dcc63be', '16 juin', '31 juin'),
])
def test_unsupported_meanings_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    events, leftover = extract_parser326_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed
