import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser289 import extract_parser289_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('03ebd82b', 'fr.persons.associate_manager_liquidator_origin.v1', 1), ('1e60224b', 'de.text.definitive_moratorium_extended_previous.v1', 1), ('33f91a14', 'fr.persons.board_roles_collective_unrestricted.v1', 4), ('57e57a5f', 'de.text.liquidation_address_previous.v1', 1), ('64501755', 'fr.persons.board_president_secretary_distinct_signing.v1', 2), ('8ee46a93', 'fr.persons.board_roles_collective_residence.v1', 3), ('a3ad3d84', 'fr.persons.share_transfer_new_associate_no_signing.v1', 3), ('c21ddc50', 'fr.text.bankruptcy_appeal_suspensive_effect.v1', 1), ('d0915140', 'fr.persons.board_delegate_two_individual_signatures.v1', 2), ('ddc784fb', 'de.text.contribution_acquisition_balance_corrected.v1', 1), ('e030bd27', 'fr.persons.manager_share_transfer_remaining.v1', 3), ('fa900a5c', 'fr.persons.share_transfer_new_manager_president.v1', 3)]


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
        return extract_parser289_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser289_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 289
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
    assert extract_parser289_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser289_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])



@pytest.mark.parametrize('prefix,old,new', [
    ('1e60224b', '17.03.2020', '31.02.2020'),
    ('1e60224b', '21.07.2020', '21.07.2019'),
    ('c21ddc50', '25.02.2020', '31.02.2020'),
    ('c21ddc50', '25.02.2020', '11.02.2020'),
    ('ddc784fb', '30.09.2019', '31.09.2019'),
    ('ddc784fb', "338'271.85", "338'271.84"),
    ('a3ad3d84', 'cédé 40', 'cédé 201'),
    ('a3ad3d84', 'CHF 100', 'CHF 0'),
    ('e030bd27', 'titulaire de 150', 'titulaire de 149'),
    ('fa900a5c', 'détient 10', 'détient 11'),
])
def test_invalid_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new, 1)
    assert changed != args[0]
    assert extract_parser289_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['03ebd82b', 'd0915140', 'fa900a5c'])
def test_signing_requires_same_source_clause(prefix):
    args, kwargs = invocation(prefix)
    clause = args[0].removesuffix(' avec signature individuelle')
    assert clause != args[0]
    for source in ('', clause + '. Autre personne avec signature individuelle.'):
        assert extract_parser289_leftovers(clause, *args[1:], source_text=source) == ([], clause)
    events, residue = extract_parser289_leftovers(clause, *args[1:], **kwargs)
    assert not residue and any(e.signing == 'Einzelunterschrift' for e in events)


def test_contribution_requires_source_context():
    args, kwargs = invocation('ddc784fb')
    assert extract_parser289_leftovers(*args, source_text='') == ([], args[0])
    source = kwargs['source_text'].replace('[nicht: Sacheinlage/Sachübernahme:', '[bisher:')
    assert extract_parser289_leftovers(*args, source_text=source) == ([], args[0])


def test_payloads():
    liquidator = selected('03ebd82b')[0]
    assert liquidator.role == 'associée-gérante liquidatrice'
    assert liquidator.payload['origin'] == 'Val-de-Ruz' and liquidator.signing == 'Einzelunterschrift'
    moratorium = selected('1e60224b')[0].payload
    assert moratorium['extension_months'] == 4 and moratorium['until_date'] == '21.07.2020'
    board = selected('33f91a14')
    assert [e.role for e in board] == ['présidente', 'vice-président', None, None]
    assert board[-1].payload['restriction_removed']
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in board)
    address = selected('57e57a5f')[0].payload
    assert 'Signalstrasse 28' in address['address'] and 'Eisbahnstrasse 41' in address['previous_address']
    officers = selected('64501755')
    assert [e.signing for e in officers] == ['Einzelunterschrift', 'Kollektivunterschrift zu zweien']
    assert officers[1].role == 'administrateur secrétaire' and officers[1].payload['origin'] == 'Onex'
    board = selected('8ee46a93')
    assert board[2].payload['place'] == 'Lancy' and board[2].role is None
    transfer = selected('a3ad3d84')
    assert [e.payload['shares'] for e in transfer[1:]] == [160, 40]
    assert transfer[2].payload['country'] == 'F' and transfer[2].signing == 'ohne Zeichnungsberechtigung'
    appeal = selected('c21ddc50')[0].payload
    assert appeal['bankruptcy_date'] == '12.02.2020' and appeal['decision_date'] == '25.02.2020'
    board = selected('d0915140')
    assert [e.role for e in board] == ['administrateur délégué', 'administrateur']
    assert [e.payload['place'] for e in board] == ['Ornex', 'Saint-Malo']
    assert all(e.signing == 'Einzelunterschrift' for e in board)
    contribution = selected('ddc784fb')[0].payload
    assert contribution['correction'] and contribution['balance_date'] == '30.09.2019'
    assert contribution['shares'] == '100' and contribution['claim'] == "338'271.85"
    transfer = selected('e030bd27')
    assert [e.payload['shares'] for e in transfer[1:]] == [150, 30]
    assert transfer[1].signing is None and transfer[2].payload['origin'] == 'Etagnières'
    transfer = selected('fa900a5c')
    assert [e.payload['shares'] for e in transfer[1:]] == [10, 10]
    assert transfer[1].signing is None
    assert transfer[2].role == 'associé-gérant président' and transfer[2].signing == 'Einzelunterschrift'


def test_address_with_sentence_separator_remains_for_existing_parser():
    args, kwargs = invocation('57e57a5f')
    changed = args[0].replace(' [bisher:', '. [bisher:', 1)
    assert changed != args[0]
    assert extract_parser289_leftovers(changed, *args[1:], **kwargs) == ([], changed)
