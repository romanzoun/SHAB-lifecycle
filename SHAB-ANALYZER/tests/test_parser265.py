import hashlib
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser265 import extract_parser265_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('200045e0', 'de.text.liquidation_address_care_of.v1', 1),
    ('23a7b351', 'fr.persons.vice_president_residence_changed.v1', 1),
    ('2d984b57', 'de.persons.management_restored_sections.v1', 4),
    ('392f4330', 'de.text.unpublished_statutes_changed.v1', 1),
    ('51c945c0', 'fr.persons.share_transfer_equal_holdings.v1', 2),
    ('66b2c659', 'fr.persons.liquidators_restricted_collective_signing.v1', 7),
    ('83fd3f93', 'fr.persons.collective_signatory_name_corrected.v1', 1),
    ('84502bcf', 'de.text.association_assets_transferred.v1', 1),
    ('924732b5', 'it.persons.associate_corrected_manager_added.v1', 2),
    ('a663dbff', 'fr.persons.associate_manager_given_name_corrected.v1', 1),
    ('a986adf2', 'it.text.audit_opt_out_date_corrected.v1', 1),
    ('c5006a29', 'de.text.conditional_capital_clause_deletion_corrected.v1', 1),
]


def path(prefix):
    matches = list(FIXTURES.glob(prefix + '*.xml'))
    assert len(matches) == 1
    return matches[0]


def selected(prefix):
    rule = next(rule for stem, rule, _ in CASES if stem == prefix)
    return [e for e in parse_publication_xml(path(prefix)).events if e.rule_id == rule]


def invocation(prefix):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser265_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser265_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 265
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    events = selected(prefix)
    assert len(events) == count
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in events)
    assert not any(e.rule_id == 'fr.persons.group_signing.v1' for e in result.events)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser265_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['66b2c659', '924732b5', 'a986adf2', 'c5006a29'])
def test_consumed_facts_require_source(prefix):
    args, kwargs = invocation(prefix)
    assert extract_parser265_leftovers(*args) == ([], args[0])
    kwargs['source_text'] += ' UNKNOWN'
    assert extract_parser265_leftovers(*args, **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix', ['392f4330', '83fd3f93', '84502bcf', 'a663dbff', 'a986adf2', 'c5006a29'])
def test_invalid_date_preserved(prefix):
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', args[0])
    assert extract_parser265_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,old,new', [
    ('66b2c659', 'avec signature collective à deux.', 'avec signature individuelle.'),
    ('924732b5', 'socio e gerente', 'socio'),
    ('a986adf2', '20.07.2018', '21.07.2018'),
    ('c5006a29', '02.05.2017', '03.05.2017'),
])
def test_source_disagreement_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    assert old in kwargs['source_text']
    kwargs['source_text'] = kwargs['source_text'].replace(old, new)
    assert extract_parser265_leftovers(*args, **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('51c945c0', 'a cédé 4', 'a cédé 0'),
    ('51c945c0', "10 parts de CHF 1'000", "10 parts de CHF 2'000"),
    ('2d984b57', 'mit 160 Stammanteilen', 'mit 0 Stammanteilen'),
    ('2d984b57', 'Geschäftsführer', 'UNKNOWN_ROLE'),
    ('924732b5', 'con 5 quote', 'con 0 quote'),
])
def test_inconsistent_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    kwargs['source_text'] = kwargs['source_text'].replace(old, new)
    assert changed != args[0]
    assert extract_parser265_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    assert selected('200045e0')[0].payload['postal_code'] == '3074'
    assert selected('23a7b351')[0].signing == 'Kollektivunterschrift zu zweien'
    persons = selected('2d984b57')
    assert [e.event_type for e in persons] == ['officer_removed'] + ['officer_changed'] * 3
    assert [e.payload.get('shares_count') for e in persons] == [40, 160, 40, None]
    assert persons[1].payload['previous'] == 'Gesellschafter, ohne Zeichnungsberechtigung'
    assert selected('392f4330')[0].payload['date'] == '2020-01-08'
    seller, buyer = selected('51c945c0')
    assert seller.payload['transferred_count'] == buyer.payload['transferred_count'] == 4
    assert seller.payload['shares_count'] == buyer.payload['shares_count'] == 10
    liquidators = selected('66b2c659')
    assert all(e.person_key and e.signing == 'Kollektivunterschrift zu zweien' for e in liquidators)
    assert all('signing_restriction' not in e.payload for e in liquidators[:5])
    assert liquidators[5].payload['excluded_partner'] == liquidators[6].payload['name']
    assert liquidators[6].payload['excluded_partner'] == liquidators[5].payload['name']
    assert selected('83fd3f93')[0].payload['previous_name'] != selected('83fd3f93')[0].payload['name']
    transfer = selected('84502bcf')[0].payload
    assert transfer['assets'] == "2'773'028.99" and transfer['liabilities'] == "1'878'950.50"
    assert transfer['recipient_uid'] == 'CHE-110.073.403' and transfer['consideration'] == 'none'
    corrected, manager = selected('924732b5')
    assert corrected.signing == 'ohne Zeichnungsberechtigung' and corrected.payload['shares_count'] == 5
    assert manager.signing == 'Kollektivunterschrift zu zweien'
    assert selected('a663dbff')[0].payload['previous_given'] == 'Bruno'
    audit = selected('a986adf2')[0].payload
    assert audit['date'] == '20.07.2018' and audit['previous_date'] == '20.07.2048'
    assert not any(e.rule_id == 'it.text.audit_waiver.v1' for e in parse_publication_xml(path('a986adf2')).events)
    capital = selected('c5006a29')[0].payload
    assert capital['date'] == '02.05.2017' and capital['previous_date'] == '22.01.2020'


@pytest.mark.parametrize('prefix,old', [('a986adf2', '20.07.2048'), ('c5006a29', '22.01.2020')])
def test_invalid_previous_date_preserved(prefix, old):
    args, kwargs = invocation(prefix)
    kwargs['source_text'] = kwargs['source_text'].replace(old, '31.02.2020')
    assert extract_parser265_leftovers(*args, **kwargs) == ([], args[0])
