import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser319 import extract_parser319_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('0614c924', 'it.text.common_shareholder_merger_subordinated_claims.v1', 1),
    ('0a9fc6a5', 'fr.text.person_residence_corrected.v1', 1),
    ('1753a224', 'fr.text.branch_name_head_office_bankruptcy.v1', 1),
    ('53121502', 'de.text.subsidiary_merger_deficit_malformed_uid.v1', 1),
    ('6f64368f', 'it.text.two_subsidiary_mergers.v1', 2),
    ('7c912f61', 'fr.text.foundation_members_excluded_joint_signing.v1', 3),
    ('8e9fcbd8', 'fr.text.liquidation_address_replaced.v1', 1),
    ('94cd9231', 'fr.text.share_transfer_manager_chair_appointed.v1', 3),
    ('b84ffbb8', 'fr.text.sole_director_signing_corrected.v1', 1),
    ('c1275018', 'it.text.board_member_general_director_corrected.v1', 1),
    ('ee894c5a', 'de.text.authorized_capital_replaced.v1', 1),
    ('fae01ec9', 'it.text.two_asset_transfers_without_consideration.v1', 2),
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
        return extract_parser319_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser319_leftovers', capture):
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
    assert PARSER_VERSION == 319
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
    events, leftover = extract_parser319_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser319_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]



@pytest.mark.parametrize('prefix', ['0614c924', '0a9fc6a5', '53121502', '6f64368f', 'b84ffbb8', 'ee894c5a', 'fae01ec9'])
def test_invalid_dates_preserved(prefix):
    _, (args, kwargs) = captured(prefix)
    dates = set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0]))
    assert dates
    for date in dates:
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser319_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed


@pytest.mark.parametrize('prefix', ['7c912f61', '8e9fcbd8', '94cd9231'])
def test_source_evidence_required(prefix):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser319_leftovers(*args, source_text='')
    assert not events and leftover == args[0]


@pytest.mark.parametrize('prefix,old,new', [
    ('7c912f61', 'ni entre elles', 'entre elles'),
    ('94cd9231', 'signature individuelle', 'signature collective à deux'),
    ('94cd9231', 'cède 10', 'cède 11'),
    ('b84ffbb8', 'signe individuellement', 'signe collectivement'),
    ('c1275018', 'direttore generale', 'presidente'),
    ('fae01ec9', 'Controprestazione: nessuna', 'Controprestazione: CHF 1.00'),
])
def test_unsupported_terms_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    events, leftover = extract_parser319_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


def test_payloads_and_roles():
    assert selected('0614c924')[0].payload['claims_subordinated'] is True
    assert selected('0a9fc6a5')[0].payload['place'] != selected('0a9fc6a5')[0].payload['previous_place']
    assert selected('1753a224')[0].event_type == 'status_changed'
    assert selected('53121502')[0].payload['uid_malformed'] is True
    assert selected('53121502')[0].payload['absorbed_uid_raw'].startswith('CHE- CHE-')
    assert [e.payload['claims_subordinated'] for e in selected('6f64368f')] == [False, True]
    foundation = selected('7c912f61')
    assert len({e.person_key for e in foundation}) == 3
    assert all(e.signing == 'Kollektivunterschrift zu zweien' and e.payload['signing_between_appointees'] is False and len(e.payload['signing_excluded_with']) == 3 for e in foundation)
    address = selected('8e9fcbd8')[0].payload
    assert address['address'] != address['previous_address']
    transfer = selected('94cd9231')
    assert [e.event_type for e in transfer] == ['ownership_changed', 'officer_changed', 'officer_changed']
    assert transfer[1].signing is None and transfer[2].signing == 'Einzelunterschrift'
    assert selected('b84ffbb8')[0].signing == 'Einzelunterschrift'
    assert selected('c1275018')[0].role == 'Mitglied des Verwaltungsrates und Generaldirektor'
    assert selected('ee894c5a')[0].payload['previous_authorization_removed'] is True
    assets = selected('fae01ec9')
    assert [e.payload['uid_malformed'] for e in assets] == [False, True]
    assert assets[1].payload['recipient_uid_raw'].endswith('?')
    assert all(e.payload['consideration_none'] is True for e in assets)
