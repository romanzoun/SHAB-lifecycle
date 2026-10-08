import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser291 import extract_parser291_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('0c78c2f3', 'fr.persons.procuration_article459_notice_completed.v1', 1),
    ('1b197fa2', 'fr.text.authorized_capital_clauses_replaced.v1', 1),
    ('2f2f799b', 'de.text.previous_auditor_register_id_corrected.v1', 1),
    ('4fc56f67', 'de.text.business_office_clause_deleted.v1', 1),
    ('62ca25aa', 'fr.persons.board_liquidators_share_restrictions_lifted.v1', 3),
    ('6bd778b5', 'de.text.merger_same_female_shareholder.v1', 1),
    ('77062cdc', 'fr.text.moratorium_extended_three_months.v1', 1),
    ('79e461e2', 'fr.persons.deputy_general_management_corrected.v1', 1),
    ('a035d0d3', 'fr.text.branch_head_office_name_uid.v1', 1),
    ('b2ed07f4', 'fr.persons.unsigned_administrator_typo.v1', 1),
    ('b95e047f', 'de.text.capital_reduction_restoration_offset_claim.v1', 1),
    ('eedd2a84', 'de.text.association_statute_dates_organization.v1', 1),
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
        return extract_parser291_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser291_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 312
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
    assert extract_parser291_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser291_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])



@pytest.mark.parametrize('prefix,old,new', [
    ('0c78c2f3', '26.03.2020', '31.02.2020'),
    ('1b197fa2', '30 mars 2020', '32 mars 2020'),
    ('2f2f799b', '23.03.2020', '31.02.2020'),
    ('6bd778b5', '09.03.2020', '31.02.2020'),
    ('6bd778b5', '31.12.2019', '31.12.2021'),
    ('77062cdc', '28 juin 2020', '28 juin 2019'),
    ('79e461e2', '24.02.2020', '31.02.2020'),
    ('b95e047f', "31'200.00", "31'201.00"),
    ('b95e047f', '100.00', '0.00'),
    ('eedd2a84', '24.10.2013', '31.02.2013'),
])
def test_invalid_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new, 1)
    assert changed != args[0]
    assert extract_parser291_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['a035d0d3', 'eedd2a84'])
def test_fragment_requires_matching_source(prefix):
    args, kwargs = invocation(prefix)
    assert extract_parser291_leftovers(*args, source_text='') == ([], args[0])
    source = kwargs['source_text'].replace('13.02.2020', '31.02.2020').replace('27.10.2011', '31.02.2011')
    assert extract_parser291_leftovers(*args, source_text=source) == ([], args[0])


def test_payloads():
    procuration = selected('0c78c2f3')[0]
    assert procuration.signing == 'Kollektivprokura zu zweien'
    assert procuration.payload['article'] == '459 al. 2 CO'
    clauses = selected('1b197fa2')[0].payload
    assert clauses['removed_clauses'] == 1 and clauses['introduced_clauses'] == 2
    assert selected('2f2f799b')[0].payload['register_id'] == 'CH-020.3.911.554-3'
    assert selected('4fc56f67')[0].payload['address'] == 'Bergstrasse 24, 8902 Urdorf'
    liquidators = selected('62ca25aa')
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in liquidators[:2])
    assert liquidators[2].payload['action'] == 'share_transfer_restrictions_lifted'
    merger = selected('6bd778b5')[0].payload
    assert merger['assets'] == "583'726.46" and merger['liabilities'] == "279'243.53"
    assert merger['capital_increase'] is False and merger['share_allocation'] is False
    assert selected('77062cdc')[0].payload['extension_months'] == 3
    deputy = selected('79e461e2')[0]
    assert deputy.role == 'membre de la direction générale adjoint' and deputy.signing is None
    assert selected('a035d0d3')[0].payload['uid'] == 'CHE-105.953.190'
    unsigned = selected('b2ed07f4')[0]
    assert unsigned.role == 'administrateur' and unsigned.signing == 'ohne Zeichnungsberechtigung'
    capital = selected('b95e047f')[0].payload
    assert capital['count'] == '312' and capital['claim'] == "31'200.00"
    organization = selected('eedd2a84')[0].payload
    assert len(organization['statute_dates']) == 8
    assert organization['board_min'] == 1 and organization['board_max'] == 9
