import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser318 import extract_parser318_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('13cba43b', 'fr.text.two_managers_liquidators_residence_changed.v1', 2),
    ('19ee85a8', 'de.text.sole_trader_bankruptcy_appeal_suspended.v1', 1),
    ('366f2dbf', 'de.text.asset_transfer_inventory_assets_only.v1', 1),
    ('4e021a1b', 'fr.text.audit_exemption_statement_removed.v1', 1),
    ('58ad8621', 'de.text.business_unit_asset_transfer.v1', 1),
    ('7090c3ff', 'de.text.branch_transferred_new_head_office.v1', 1),
    ('72598b49', 'fr.text.foundation_member_restricted_signing.v1', 1),
    ('840ffa44', 'de.text.demerger_assets_new_company.v1', 1),
    ('911c0054', 'fr.text.person_origin_residence_corrected.v1', 1),
    ('c83e6d28', 'fr.text.audit_waiver_deletion_entry_completed.v1', 1),
    ('dd857292', 'fr.text.three_board_members_restricted_signing.v1', 3),
    ('ffa96470', 'it.text.management_chair_replaced_german_metadata.v1', 2),
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
        return extract_parser318_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser318_leftovers', capture):
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
    assert PARSER_VERSION == 318
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
    events, leftover = extract_parser318_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser318_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]



@pytest.mark.parametrize('prefix', ['19ee85a8', '366f2dbf', '58ad8621', '7090c3ff', '840ffa44', '911c0054', 'c83e6d28'])
def test_invalid_dates_preserved(prefix):
    _, (args, kwargs) = captured(prefix)
    dates = set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0]))
    assert dates
    for date in dates:
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser318_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed


@pytest.mark.parametrize('prefix,old,new', [
    ('13cba43b', 'signer individuellement', 'signer collectivement'),
    ('19ee85a8', '14.00 Uhr', '25.00 Uhr'),
    ('72598b49', 'le président ou les vices-présidents', 'tous les membres'),
    ('dd857292', 'le président ou le secrétaire', 'tous les membres'),
    ('ffa96470', 'firma individuale', 'firma collettiva a due'),
    ('911c0054', '11-08-2015', '31-02-2015'),
])
def test_unsupported_terms_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    events, leftover = extract_parser318_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


def test_branch_source_evidence_required():
    _, (args, kwargs) = captured('7090c3ff')
    for source in ('', kwargs['source_text'].replace('Art. 112 Abs. 2', 'Art. 113 Abs. 2')):
        events, leftover = extract_parser318_leftovers(*args, source_text=source)
        assert not events and leftover == args[0]


def test_payloads_and_roles():
    liquidators = selected('13cba43b')
    assert all(e.role == 'Liquidator' and e.signing == 'Einzelunterschrift' for e in liquidators)
    assert liquidators[0].payload['country1'] == 'FRA'
    suspension = selected('19ee85a8')[0]
    assert suspension.event_type == 'status_changed'
    assert suspension.payload['suspensive_effect'] is True
    assert suspension.payload['bankruptcy_entry_removed'] is True
    assert selected('366f2dbf')[0].payload['assets'] == '3.00'
    assert selected('4e021a1b')[0].payload['audit_exemption_statement_removed'] is True
    assert selected('58ad8621')[0].payload['business_unit']
    branch = selected('7090c3ff')[0].payload
    assert branch['previous_uid'] != branch['recipient_uid']
    foundation = selected('72598b49')[0]
    assert foundation.role == 'Mitglied des Stiftungsrates'
    assert foundation.payload['signing_restriction'] == 'avec le président ou les vices-présidents'
    assert selected('840ffa44')[0].payload['recipient_uid']
    correction = selected('911c0054')[0]
    assert correction.payload['origin'] != correction.payload['previous_origin']
    assert correction.payload['place'] != correction.payload['previous_place']
    assert correction.role is None and correction.signing is None
    assert selected('c83e6d28')[0].payload['audit_waiver_statement_removed'] is True
    assert all(e.payload['signing_restriction'] == 'avec le président ou le secrétaire' for e in selected('dd857292'))
    chairs = selected('ffa96470')
    assert [e.event_type for e in chairs] == ['officer_removed', 'officer_changed']
    assert [e.payload['action'] for e in chairs] == ['removed', 'appointed']
    assert all(e.role == 'Vorsitzender der Geschäftsführung' and e.signing == 'Einzelunterschrift' for e in chairs)
