import hashlib
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser272 import extract_parser272_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('11303ef2', 'fr.text.appeal_judgment_annulled.v1', 1),
    ('2d33bdc6', 'fr.persons.direction_role_unsigned_corrected.v1', 1),
    ('36ab2c15', 'fr.persons.manager_president_new_collective_manager.v1', 2),
    ('727a0a44', 'fr.persons.associate_share_transfer_holdings.v1', 2),
    ('8a208ad2', 'fr.text.sole_trader_bankruptcy_annulled.v1', 1),
    ('abc86ff6', 'it.persons.president_name_corrected.v1', 1),
    ('b46a65e0', 'fr.persons.branch_procuration_name_corrected.v1', 1),
    ('c6979f38', 'fr.persons.four_liquidators_collective_signing.v1', 4),
    ('db73648d', 'fr.text.registered_share_count_corrected.v1', 1),
    ('e9756f28', 'fr.persons.corporate_associate_partial_share_transfer.v1', 2),
    ('e9c17fa2', 'fr.persons.collective_procuration_exclusions.v1', 2),
    ('fc6d4aa3', 'fr.text.statutes_date_corrected.v1', 1),
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
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser272_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser272_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION >= 272
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    events = [e for e in result.events if e.rule_id == rule]
    assert len(events) == count
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in events)
    if any(e.signing for e in events):
        assert not any(e.rule_id == 'fr.persons.group_signing.v1' for e in result.events)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser272_leftovers(changed, *args[1:], **kwargs) == ([], changed)



@pytest.mark.parametrize('prefix', ['2d33bdc6', '8a208ad2', 'b46a65e0', 'db73648d', 'fc6d4aa3'])
def test_invalid_dates_preserved(prefix):
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', args[0])
    assert changed != args[0]
    assert extract_parser272_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['36ab2c15', 'c6979f38', 'abc86ff6'])
def test_source_required(prefix):
    args, kwargs = invocation(prefix)
    assert extract_parser272_leftovers(*args) == ([], args[0])
    assert extract_parser272_leftovers(*args, source_text=kwargs['source_text'] + ' UNKNOWN_SUFFIX') == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('e9756f28', '8 parts', '9 parts'),
    ('db73648d', "1'436'214 actions", "1'436'215 actions"),
    ('727a0a44', 'cédé 40', 'cédé 81'),
    ('2d33bdc6', 'sans signature', 'avec signature'),
    ('e9c17fa2', 'pas entre eux', 'entre eux'),
    ('8a208ad2', 'a annulé', 'a confirmé'),
])
def test_unsupported_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser272_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    assert selected('11303ef2')[0].payload['action'] == 'judgment_annulled'
    assert selected('8a208ad2')[0].payload['registration_restored']
    unsigned = selected('2d33bdc6')[0]
    assert unsigned.signing is None and unsigned.payload['without_signature']
    assert unsigned.role == 'membre de la direction'
    president, manager = selected('36ab2c15')
    assert president.signing == 'Einzelunterschrift' and president.payload['signing_continued']
    assert manager.signing == 'Kollektivunterschrift zu zweien'
    assert [e.payload['shares'] for e in selected('727a0a44')] == [120, 80]
    corrected = selected('abc86ff6')[0]
    assert corrected.payload['previous_name'] != corrected.payload['name']
    assert corrected.signing == 'Einzelunterschrift'
    assert selected('b46a65e0')[0].payload['limited_to_branch']
    assert all(e.role == 'liquidateur' and e.signing == 'Kollektivunterschrift zu zweien' for e in selected('c6979f38'))
    assert selected('db73648d')[0].payload['count'] == "1'436'214"
    seller, buyer = selected('e9756f28')
    assert seller.payload['shares'] == 8 and seller.payload['previous_shares'] == 12
    assert buyer.payload['shares'] == 12 and seller.payload['uid'].startswith('CHE-')
    for e in selected('e9c17fa2'):
        assert e.signing == 'Kollektivprokura zu zweien' and e.payload['not_with_each_other']
        assert len(e.payload['excluded_signers']) == 4
    assert selected('fc6d4aa3')[0].payload['statutes_date'] == '16.12.2019'
