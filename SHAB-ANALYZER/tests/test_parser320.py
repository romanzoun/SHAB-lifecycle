import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser320 import extract_parser320_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('1cf200d1', 'de.text.two_association_mergers.v1', 2),
    ('2724b165', 'fr.text.two_branch_mentions_removed.v1', 1),
    ('64a0d327', 'it.text.subsidiary_merger_free_equity.v1', 1),
    ('82b97abe', 'it.text.asset_transfer_without_consideration.v1', 1),
    ('8a7f1266', 'fr.text.branch_erroneous_deletion_reinstated.v1', 1),
    ('9780d1da', 'fr.text.uid_corrected.v1', 1),
    ('a0f07f7d', 'fr.text.asset_transfer_cash_consideration.v1', 1),
    ('b9894488', 'fr.text.share_transfer_new_associate_joint_signing.v1', 2),
    ('c9cb541c', 'fr.text.branch_registration_notice.v1', 1),
    ('d19188d5', 'fr.text.manager_full_name_corrected.v1', 1),
    ('d9afd8a8', 'fr.text.new_statutes_date.v1', 1),
    ('e3c5c5cd', 'fr.text.board_chair_and_former_chair_joint_signing.v1', 2),
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
        return extract_parser320_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser320_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    result, _ = captured(prefix)
    rule = next(rule for stem, rule, _ in CASES if stem == prefix)
    return [e for e in result.events if e.rule_id == rule]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 412
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    events = selected(prefix)
    assert len(events) == count
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in events)
    if any(e.signing for e in events):
        assert not any(e.rule_id == 'fr.persons.group_signing.v1' for e in result.events)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser320_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser320_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]



@pytest.mark.parametrize('prefix', ['1cf200d1', '64a0d327', '82b97abe', '8a7f1266', '9780d1da', 'a0f07f7d', 'c9cb541c', 'd9afd8a8'])
def test_invalid_dates_preserved(prefix):
    _, (args, kwargs) = captured(prefix)
    dates = set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0]))
    assert dates
    for date in dates:
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser320_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed


@pytest.mark.parametrize('prefix,old,new', [
    ('1cf200d1', 'werden zu Mitgliedern', 'werden nicht zu Mitgliedern'),
    ('64a0d327', 'senza aumento del capitale', 'con aumento del capitale'),
    ('82b97abe', 'Controprestazione: nessuna', 'Controprestazione: CHF 1.00'),
    ('b9894488', 'cession de 20', 'cession de 21'),
    ('b9894488', 'Signature collective à deux', 'Signature individuelle'),
    ('e3c5c5cd', 'continuent de signer collectivement à deux', 'continuent de signer individuellement'),
])
def test_unsupported_terms_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    events, leftover = extract_parser320_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


def test_payloads_and_roles():
    mergers = selected('1cf200d1')
    assert len({e.payload['absorbed_uid'] for e in mergers}) == 2
    assert all(e.payload['members_transferred'] for e in mergers)
    branches = selected('2724b165')[0]
    assert branches.payload['mention_removed'] is True
    assert branches.payload['branch_uid1'] != branches.payload['branch_uid2']
    merger = selected('64a0d327')[0].payload
    assert merger['free_equity_confirmed'] is True
    assert merger['capital_increase'] is False and merger['share_allocation'] is False
    assert selected('82b97abe')[0].payload['consideration_none'] is True
    assert selected('8a7f1266')[0].event_type == 'status_changed'
    assert selected('8a7f1266')[0].payload['reinstated'] is True
    corrected = selected('9780d1da')[0]
    assert corrected.payload['corrected_uid'] == corrected.org_uid
    assert selected('a0f07f7d')[0].payload['consideration'] == "586'000.00"
    transfer = selected('b9894488')
    assert [e.event_type for e in transfer] == ['ownership_changed', 'officer_changed']
    assert transfer[1].role == 'Gesellschafter' and transfer[1].signing == 'Kollektivunterschrift zu zweien'
    assert transfer[0].payload['transferred'] == transfer[0].payload['buyer_count']
    assert selected('c9cb541c')[0].payload['branch_uid'] != selected('c9cb541c')[0].org_uid
    branch = selected('c9cb541c')[0]
    assert branch.event_type == 'branch_changed'
    assert branch.payload['action'] == 'registered'
    assert set(branch.payload) == {
        'action', 'branch_uid', 'place', 'register_canton',
        'source_notice_date', 'source_notice_id',
    }
    from datetime import date
    date.fromisoformat(branch.payload['source_notice_date'])
    name = selected('d19188d5')[0]
    assert name.role == 'Geschäftsführerin' and name.signing is None
    assert name.payload['name'] != name.payload['previous_name']
    assert selected('d9afd8a8')[0].payload['statutes_date'] == '28.05.2020'
    board = selected('e3c5c5cd')
    assert [e.role for e in board] == ['Präsident des Verwaltungsrates', 'Mitglied des Verwaltungsrates']
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in board)
    assert len({e.person_key for e in board}) == 2


def test_two_mergers_fail_atomically():
    _, (args, kwargs) = captured('1cf200d1')
    changed = args[0].rsplit('werden zu Mitgliedern', 1)
    changed = 'werden nicht zu Mitgliedern'.join(changed)
    events, leftover = extract_parser320_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('stem,rule', [
    ('94b72118-d3cb-46f4-8cf3-8d526586b9f2', 'fr.text.branch_registered.v1'),
    ('d4a02679-04a7-4fe1-ae17-ae0a98da7cd1', 'fr.text.branch_registered_at.v1'),
])
def test_existing_branch_events_keep_their_rule_and_payload(stem, rule):
    import shab_analyzer.parse as parser
    fixture = path(stem)
    with patch.object(parser, 'extract_parser320_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    result = parse_publication_xml(fixture)
    assert result.status == baseline.status
    assert result.leftover_text == baseline.leftover_text
    previous = [event for event in baseline.events if event.rule_id == rule]
    current = [event for event in result.events if event.rule_id == rule]
    assert len(previous) == len(current) == 1
    assert current == previous
    assert current[0].event_type == 'branch_changed'
    assert not any(event.rule_id == 'fr.text.branch_registration_notice.v1' for event in result.events)
