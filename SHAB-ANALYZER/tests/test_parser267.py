import hashlib
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser267 import extract_parser267_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('04fa01a3', 'fr.persons.share_division_multiple_transfers.v1', 3),
    ('280fb6c4', 'fr.persons.partial_share_transfer_managers.v1', 3),
    ('2a1ba9df', 'de.text.previous_auditor_corrected.v1', 1),
    ('9c7d17c1', 'fr.text.share_classes_completed.v1', 1),
    ('b176c30f', 'fr.persons.administration_collective_signing_typo.v1', 2),
    ('cb8cd024', 'fr.persons.continued_signing_director_restriction.v1', 3),
    ('cc08b506', 'de.text.sole_proprietorship_reinstated.v1', 1),
    ('d345a372', 'fr.persons.joint_share_transfer_managers.v1', 3),
    ('d8a66d25', 'fr.persons.share_transfer_collective_managers.v1', 4),
    ('dc97cd34', 'fr.persons.foundation_member_unsigned.v1', 1),
    ('decaf6f8', 'fr.persons.board_mixed_signing_restrictions.v1', 5),
    ('e16e4d94', 'it.text.wholly_owned_merger_compact_currency.v1', 1),
]
SOURCE_CASES = ['04fa01a3', '9c7d17c1', 'd345a372']


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
        return extract_parser267_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser267_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 267
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    events = [e for e in result.events if e.rule_id == rule]
    assert len(events) == count
    if prefix == 'cc08b506':
        assert events[0].event_type == 'status_changed'
    if prefix == 'e16e4d94':
        assert events[0].event_type == 'company_merged'
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in events)
    assert not any(e.rule_id == 'fr.persons.group_signing.v1' for e in result.events)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser267_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', SOURCE_CASES)
def test_source_required_and_bounded(prefix):
    args, kwargs = invocation(prefix)
    assert extract_parser267_leftovers(*args) == ([], args[0])
    kwargs['source_text'] += ' UNKNOWN_SUFFIX'
    assert extract_parser267_leftovers(*args, **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix', ['04fa01a3', '2a1ba9df', '9c7d17c1', 'cc08b506', 'd8a66d25', 'e16e4d94'])
def test_invalid_date_preserved(prefix):
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', args[0])
    kwargs['source_text'] = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', kwargs['source_text'])
    assert extract_parser267_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,old,new', [
    ('04fa01a3', 'avec signature individuelle', 'avec signature collective à deux'),
    ('9c7d17c1', 'liées selon statuts', 'non liées'),
    ('d345a372', 'avec signature individuelle', 'avec signature collective à deux'),
])
def test_source_disagreement_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    assert old in kwargs['source_text']
    kwargs['source_text'] = kwargs['source_text'].replace(old, new)
    assert extract_parser267_leftovers(*args, **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('04fa01a3', '164 parts', '165 parts'),
    ('04fa01a3', "25'000", "26'000"),
    ('04fa01a3', '105 parts', '0 parts'),
    ('280fb6c4', '100 de ses', '201 de ses'),
    ('280fb6c4', '100 de ses', '0 de ses'),
    ('9c7d17c1', "200'000", "200'001"),
    ('9c7d17c1', "50'000 actions", "50'000.5 actions"),
    ('d345a372', '200 parts', '0 parts'),
    ('d8a66d25', "20'000", '0'),
    ('decaf6f8', 'ne signent pas entre eux', 'signent entre eux'),
    ('cb8cd024', 'avec un directeur ou le directeur général', 'sans restriction'),
    ('e16e4d94', 'senza aumento', 'con aumento'),
])
def test_inconsistent_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    kwargs['source_text'] = kwargs['source_text'].replace(old, new)
    assert changed != args[0]
    assert extract_parser267_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    transfer, president, manager = selected('04fa01a3')
    assert transfer.payload['remaining_count'] == '164'
    assert [t['count'] for t in transfer.payload['transfers']] == ['105', '30', '1']
    assert president.role == 'associé gérant président' and president.signing == manager.signing == 'Einzelunterschrift'
    assert manager.payload['shares_count'] == '1'
    transfer, president, new = selected('280fb6c4')
    assert transfer.payload['remaining_count'] == '100'
    assert new.role == 'associé gérant' and new.signing == 'Einzelunterschrift'
    auditor = selected('2a1ba9df')[0]
    assert auditor.payload['action'] == 'previous_auditor_corrected' and auditor.payload['previous_uid'] == 'CH-170.4.009.554-7'
    capital = selected('9c7d17c1')[0].payload
    assert capital['capital'] == "200'000" and capital['transfer_restricted'] and capital['fully_paid']
    assert [s['voting_preferred'] for s in capital['share_classes']] == [False, True, False]
    assert selected('b176c30f')[0].role == 'président'
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in selected('b176c30f'))
    assert all(e.payload['authorized_partner_roles'] == ['directeur', 'directeur général'] for e in selected('cb8cd024'))
    restored = selected('cc08b506')[0].payload
    assert restored['action'] == 'reinstated' and restored['previous_deletion_revoked']
    transfer, manager1, manager2 = selected('d345a372')
    assert transfer.payload['recipient_uid'] == 'CHE-259.882.930'
    assert manager1.payload['associate_removed'] and manager2.payload['associate_removed']
    transfer, manager, president, signer = selected('d8a66d25')
    assert transfer.payload['count'] == 1 and transfer.payload['recipient_uid'] == 'CHE-383.188.813'
    assert manager.payload['associate_removed'] and president.role == 'président'
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in [manager, president, signer])
    correction = next(e for e in parse_publication_xml(path('d8a66d25')).events if e.rule_id == 'fr.text.ancillary_obligations_corrected.v1')
    assert all(correction.payload[k] is False for k in ['ancillary_obligations', 'preference_rights', 'preemption_rights', 'purchase_option_rights'])
    assert selected('dc97cd34')[0].signing == 'ohne Zeichnungsberechtigung'
    board = selected('decaf6f8')
    assert board[0].payload['excluded_partner'] == board[1].payload['name']
    assert board[1].payload['excluded_partner'] == board[0].payload['name']
    assert [e.signing for e in board] == ['Kollektivunterschrift zu zweien'] * 3 + ['Einzelunterschrift', 'Kollektivunterschrift zu zweien']
    assert board[2].role == 'secrétaire et directeur'
    merger = selected('e16e4d94')[0].payload
    assert merger['assets'] == "161'315.50" and merger['liabilities'] == "51'884.73"
    assert merger['wholly_owned'] and merger['capital_increase'] is False and merger['share_allocation'] is False
