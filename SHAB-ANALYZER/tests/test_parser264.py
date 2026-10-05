from pathlib import Path
import hashlib
import re
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser264 import extract_parser264_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('1f895e05', 'fr.text.bankruptcy_appeal_suspensive_effect.v1', 1),
    ('27138a76', 'de.text.second_statutes_date_means_changed.v1', 2),
    ('4a4d496d', 'de.text.head_office_bankruptcy_opened.v1', 1),
    ('5a4f213e', 'fr.text.preferred_share_rights_supplemented.v1', 1),
    ('72c387ce', 'fr.persons.executive_committee_individual_signing.v1', 2),
    ('81500494', 'de.text.branch_uid_replaced_and_branch_added.v1', 2),
    ('c1cf4702', 'de.text.erroneous_statutes_date_deleted.v1', 1),
    ('c4a9add5', 'de.text.two_business_offices_deleted.v1', 2),
    ('c55e203e', 'de.text.cooperative_share_nominal_changed.v1', 1),
    ('cb3fe68a', 'fr.text.authorized_capital_decision_date_corrected.v1', 1),
    ('d03f87cd', 'fr.persons.one_share_transfer_two_managers.v1', 2),
    ('e975b0e4', 'de.text.cooperative_dissolved_bankruptcy.v1', 1),
]


def path(prefix):
    paths = list(FIXTURES.glob(prefix + '*.xml'))
    assert len(paths) == 1
    return paths[0]


def selected(prefix):
    rule = next(rule for stem, rule, _ in CASES if stem == prefix)
    return [e for e in parse_publication_xml(path(prefix)).events if e.rule_id == rule]


def invocation(prefix):
    import shab_analyzer.parse as parser
    captured = []
    def capture(*args, **kwargs):
        result = extract_parser264_leftovers(*args, **kwargs)
        if result[0]:
            captured.append((args, kwargs))
        return result
    with patch.object(parser, 'extract_parser264_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(captured) == 1
    return captured[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION >= 264
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    events = selected(prefix)
    assert len(events) == count
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in events)
    assert not any(e.rule_id == 'fr.persons.group_signing.v1' for e in result.events)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser264_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['27138a76', '81500494', 'c55e203e', 'd03f87cd'])
def test_source_required(prefix):
    args, kwargs = invocation(prefix)
    assert extract_parser264_leftovers(*args) == ([], args[0])
    kwargs['source_text'] += ' UNKNOWN'
    assert extract_parser264_leftovers(*args, **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix', ['1f895e05', '27138a76', '4a4d496d', '5a4f213e', 'c1cf4702', 'cb3fe68a', 'e975b0e4'])
def test_invalid_dates_preserved(prefix):
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', args[0])
    kwargs['source_text'] = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', kwargs['source_text'])
    assert extract_parser264_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,old,new', [
    ('81500494', 'Spreitenbach (CH-', 'UNKNOWN (CH-'),
    ('c55e203e', 'CHF 100.--', 'CHF 101.--'),
    ('d03f87cd', 'avec signature individuelle', 'UNKNOWN_SIGNING'),
])
def test_source_must_agree(prefix, old, new):
    args, kwargs = invocation(prefix)
    assert old in kwargs['source_text']
    kwargs['source_text'] = kwargs['source_text'].replace(old, new)
    assert extract_parser264_leftovers(*args, **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix', ['4a4d496d', 'e975b0e4'])
def test_invalid_time_preserved(prefix):
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2} Uhr', '25.61 Uhr', args[0])
    assert extract_parser264_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads_and_superseded_events():
    assert selected('1f895e05')[0].payload['action'] == 'suspensive_effect_granted'
    statutes, means = selected('27138a76')
    assert statutes.payload['date'] == '2020-01-17'
    assert len(means.payload['means']) == 4
    assert selected('4a4d496d')[0].payload['scope'] == 'head_office'
    shares = selected('5a4f213e')[0].payload
    assert shares['shares_count'] == 3000000 and shares['nominal'] == '10'
    assert shares['rights'] == ['vote', 'dividend', 'liquidation_proceeds']
    assert all(e.signing == 'Einzelunterschrift' and e.person_key for e in selected('72c387ce'))
    updated, added = selected('81500494')
    assert updated.payload['previous_uid'].startswith('CH-')
    assert updated.payload['branch_uid'] == 'CHE-136.450.217'
    assert added.payload['action'] == 'added'
    assert selected('c1cf4702')[0].payload['action'] == 'deleted'
    assert [e.payload['postal_code'] for e in selected('c4a9add5')] == ['8105', '8105']
    share = selected('c55e203e')[0].payload
    assert share['nominal'] == '500.00' and share['previous_nominal'] == '100.--'
    correction = selected('cb3fe68a')[0].payload
    assert correction['decision_date'] == '2019-12-27'
    assert correction['previous_decision_date'] == '2019-12-10'
    seller, buyer = selected('d03f87cd')
    assert seller.payload['shares_transferred'] == buyer.payload['shares_received'] == 1
    assert seller.payload['shares_count'] == buyer.payload['shares_count'] == 10
    assert seller.signing == buyer.signing == 'Einzelunterschrift'
    assert seller.role == 'associé-gérant président'
    assert selected('e975b0e4')[0].payload['time'] == '08.30'
    for prefix, obsolete in [('81500494', 'de.text.branch_added.v1'), ('c55e203e', 'de.text.cooperative_share_certificate.v1')]:
        assert not any(e.rule_id == obsolete for e in parse_publication_xml(path(prefix)).events)


def test_inconsistent_share_nominal_preserved():
    args, kwargs = invocation('d03f87cd')
    changed = args[0].replace("cession de une part de CHF 1'000", "cession de une part de CHF 2'000")
    kwargs['source_text'] = kwargs['source_text'].replace(args[0], changed)
    assert extract_parser264_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('old,new', [
    ('27 décembre', '32 décembre'),
    ('10 décembre', '0 décembre'),
])
def test_invalid_written_dates_preserved(old, new):
    args, kwargs = invocation('cb3fe68a')
    changed = args[0].replace(old, new)
    assert extract_parser264_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('old,new', [
    ('associé pour 10', 'associé pour 0'),
    ('président', 'UNKNOWN_ROLE'),
    ('Gérants: les associés Daviaud', 'Gérants: les associés UNKNOWN'),
])
def test_share_transfer_inconsistent_facts_preserved(old, new):
    args, kwargs = invocation('d03f87cd')
    changed = args[0].replace(old, new)
    kwargs['source_text'] = kwargs['source_text'].replace(old, new)
    assert extract_parser264_leftovers(changed, *args[1:], **kwargs) == ([], changed)
