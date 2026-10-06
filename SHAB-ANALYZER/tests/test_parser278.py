import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser278 import extract_parser278_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('02db8c18', 'fr.persons.manager_transfer_two_associates.v1', 3),
    ('1caea565', 'fr.persons.procuration_ended_deputy_director.v1', 1),
    ('1ecb7ae2', 'de.text.document_list_supplement.v1', 1),
    ('3cf7a05e', 'fr.persons.administrator_presidency_supplement.v1', 1),
    ('3f700682', 'fr.persons.three_signers_mutual_and_named_exclusions.v1', 3),
    ('51e027ca', 'fr.persons.corporate_associate_name_corrected_rsin.v1', 1),
    ('6502a156', 'fr.text.bankruptcy_appeal_suspended_corrected.v1', 1),
    ('81ab5d31', 'fr.persons.administrators_liquidators_restrictions_removed.v1', 5),
    ('90b8cea6', 'fr.persons.president_transfer_unsigned_associate.v1', 2),
    ('9b030e32', 'it.persons.associate_name_corrected_unsigned_shares.v1', 1),
    ('ad455369', 'fr.persons.two_holders_transfer_appointed_manager.v1', 3),
    ('b2589d6f', 'fr.persons.foundation_members_replaced_unsigned.v1', 22),
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
        return extract_parser278_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser278_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 297
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
    assert extract_parser278_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser278_leftovers(args[0], 'de' if args[1] == 'it' else 'it', *args[2:], **kwargs) == ([], args[0])



@pytest.mark.parametrize('prefix', ['02db8c18', '9b030e32', '1ecb7ae2'])
def test_removed_context_required(prefix):
    args, kwargs = invocation(prefix)
    assert extract_parser278_leftovers(*args, source_text='') == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('3cf7a05e', '11.02.2020', '31.02.2020'),
    ('6502a156', '12.02.2020', '31.02.2020'),
    ('6502a156', '08h20', '24h20'),
    ('6502a156', '08h20', '08h60'),
    ('90b8cea6', 'titulaire de 8', 'titulaire de 9'),
    ('90b8cea6', '12 de ses', '21 de ses'),
    ('ad455369', 'pour 20 parts', 'pour 21 parts'),
    ('81ab5d31', 'CHF 1,', 'CHF 0,'),
    ('9b030e32', 'con 2 quote', 'con 0 quote'),
    ('1caea565', 'signature collective à deux', 'signature individuelle'),
    ('b2589d6f', 'sans signature', 'avec signature'),
])
def test_invalid_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new, 1)
    assert changed != args[0]
    assert extract_parser278_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    assert selected('1caea565')[0].payload['procuration_ended']
    assert selected('3cf7a05e')[0].role == 'administrateur président'
    assert selected('51e027ca')[0].payload['rsin'] == '860767401'
    corrected = selected('9b030e32')[0]
    assert corrected.payload['correction'] and corrected.payload['without_signature']
    assert corrected.payload['previous_name'] != corrected.payload['name']
    assert corrected.payload['shares'] == 2
    transfer = selected('02db8c18')
    assert transfer[0].payload['transferred_shares'] == 120
    assert [e.payload['received_shares'] for e in transfer[1:]] == [80, 40]
    assert transfer[2].payload['without_signature'] and transfer[1].signing is None
    assert [e.payload['shares'] for e in selected('90b8cea6')] == [8, 12]
    holders = selected('ad455369')
    assert [e.payload['shares'] for e in holders] == [90, 90, 20]
    assert holders[2].signing == 'Kollektivunterschrift zu zweien'
    liquidators = selected('81ab5d31')
    assert liquidators[0].payload['action'] == 'share_transfer_restrictions_removed'
    assert all(e.payload['signing_continued'] for e in liquidators[1:])
    signers = selected('3f700682')
    assert all(len(e.payload['signing_excluded_partners']) == 15 for e in signers)
    assert all(len(e.payload['signing_excluded_among_group']) == 2 for e in signers)
    members = selected('b2589d6f')
    assert sum(e.event_type == 'officer_removed' for e in members) == 10
    assert all(e.payload['without_signature'] for e in members[10:])
    assert members[17].payload['country'] == 'HUN'
    assert 'W.' in members[20].payload['name']
    assert selected('6502a156')[0].payload['previous_effective_time'] == '08:20'
    assert selected('1ecb7ae2')[0].payload['entry_date'] == '06.01.2020'
