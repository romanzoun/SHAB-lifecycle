import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser290 import extract_parser290_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('38012f3e', 'fr.text.branch_seat_transfer_same_uid.v1', 1),
    ('547756bd', 'fr.persons.two_administrators_individual_signing.v1', 2),
    ('74ec3c41', 'fr.persons.three_administrators_collective_signing.v1', 3),
    ('829646a8', 'fr.text.foundation_dissolution_board_liquidators.v1', 3),
    ('841177fb', 'it.text.asset_transfer_no_consideration.v1', 1),
    ('8e49f7ff', 'de.text.demerger_two_recipients.v1', 1),
    ('94f08edd', 'fr.text.definitive_moratorium_extended_written_dates.v1', 1),
    ('b681b74d', 'fr.persons.manager_share_transfer_secretary_president.v1', 3),
    ('bdd79a71', 'de.text.cooperative_share_nominal_changed.v1', 1),
    ('c552e703', 'fr.persons.foundation_three_members_shared_residence.v1', 3),
    ('d213647a', 'fr.persons.board_secretary_signing_reassigned.v1', 2),
    ('fd6d3bf6', 'fr.persons.reciprocal_restricted_signing_procuration.v1', 5),
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
        return extract_parser290_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser290_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 315
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
    assert extract_parser290_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser290_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])



@pytest.mark.parametrize('prefix,old,new', [
    ('829646a8', '11.02.2020', '31.02.2020'),
    ('841177fb', '26.02.2020', '31.02.2020'),
    ('8e49f7ff', '05.12.2019', '32.12.2019'),
    ('94f08edd', '12 mars 2020', '32 mars 2020'),
    ('94f08edd', '28 août 2020', '28 août 2019'),
    ('b681b74d', 'désormais 1 part', 'désormais 2 part'),
    ('bdd79a71', '100.00', '0.00'),
    ('38012f3e', 'Vionnaz (CHE-253.327.311)', 'Vionnaz (CHE-253.327.312)'),
])
def test_invalid_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new, 1)
    assert changed != args[0]
    assert extract_parser290_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['74ec3c41', 'c552e703'])
def test_signing_requires_source_clause(prefix):
    args, kwargs = invocation(prefix)
    clause = args[0].removesuffix(' avec signature collective à deux').replace('fondation avec signature collective à deux:', 'fondation :')
    assert extract_parser290_leftovers(clause, *args[1:], source_text='') == ([], clause)
    events, residue = extract_parser290_leftovers(clause, *args[1:], **kwargs)
    assert not residue and all(e.signing == 'Kollektivunterschrift zu zweien' for e in events)


def test_payloads():
    branch = selected('38012f3e')[0].payload
    assert branch['previous_place'] == 'Saint-Gingolph' and branch['place'] == 'Vionnaz'
    assert branch['uid'] == 'CHE-253.327.311'
    assert all(e.role == 'administrateur' and e.signing == 'Einzelunterschrift' for e in selected('547756bd'))
    assert len(selected('74ec3c41')) == 3
    dissolution = selected('829646a8')
    assert dissolution[0].payload['decision_date'] == '11.02.2020'
    assert all(e.role == 'membre du conseil liquidateur' for e in dissolution[1:])
    transfer = selected('841177fb')[0].payload
    assert transfer['assets'] == "4'352'835'572.00" and transfer['liabilities'] == '0.00'
    assert transfer['consideration'] == 'nessuna'
    split = selected('8e49f7ff')[0].payload
    assert split['uid1'] == 'CHE-413.606.220' and split['uid2'] == 'CHE-412.726.933'
    moratorium = selected('94f08edd')[0].payload
    assert moratorium['decision_date'] == '12.03.2020' and moratorium['until_date'] == '28.08.2020'
    shares = selected('b681b74d')
    assert [e.payload['shares'] for e in shares[1:]] == [1, 19]
    assert [e.role for e in shares[1:]] == ['associé gérant secrétaire', 'associé gérant président']
    assert all(e.signing is None for e in shares[1:])
    assert selected('bdd79a71')[0].payload['nominal'] == '100.00'
    members = selected('c552e703')
    assert [e.payload['place'] for e in members] == ['Cugy (VD)', 'Lausanne', 'Lausanne']
    assert [e.payload['origin'] for e in members] == ['Valbirse', 'Lieu', 'Oberthal']
    board = selected('d213647a')
    assert board[0].role == 'membre du conseil secrétaire'
    assert board[1].signing == 'ohne Zeichnungsberechtigung' and board[1].payload['previous_role'] == 'secrétaire'
    officers = selected('fd6d3bf6')
    assert [e.signing for e in officers] == ['Kollektivunterschrift zu zweien'] * 2 + ['Kollektivprokura zu zweien'] * 3
    assert officers[3].payload['origin'] == 'St. Antoni'
    for e in officers[:2]:
        assert e.payload['signing_partners'] == [p.payload['name'] for p in officers[2:]]
    for e in officers[2:]:
        assert e.payload['signing_partners'] == [p.payload['name'] for p in officers[:2]]
    assert all(e.payload['within_group_allowed'] for e in officers)


@pytest.mark.parametrize('prefix', ['0fe62197', '65509d11'])
def test_existing_moratorium_and_sole_proprietor_rules_keep_priority(prefix):
    args, kwargs = invocation(prefix)
    assert args[0]
    assert extract_parser290_leftovers(*args, **kwargs) == ([], args[0])
