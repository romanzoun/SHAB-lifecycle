import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser282 import extract_parser282_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('06e60a0f', 'de.text.authorized_capital_renewed.v1', 1),
    ('1cba5e22', 'de.persons.board_president_signing_place_corrected.v1', 1),
    ('2409e29b', 'it.text.members_dissolution.v1', 1),
    ('7c8ce198', 'fr.text.capital_reduction_zero_simultaneous_increase.v1', 1),
    ('7efb981e', 'it.text.liquidation_completed_tax_consent_pending.v1', 1),
    ('826a1625', 'fr.persons.two_deputy_directors_not_together.v1', 2),
    ('8795252d', 'de.persons.board_member_name_origin_changed.v1', 1),
    ('a03fc4f1', 'de.text.share_split_fully_paid.v1', 1),
    ('b7fc4edc', 'fr.persons.director_signing_with_board_corrected.v1', 1),
    ('b9d146a0', 'fr.persons.two_board_departures_two_appointments.v1', 4),
    ('c4013245', 'fr.persons.sole_associate_manager_name_corrected.v1', 1),
    ('f68cef60', 'fr.persons.transfer_new_unsigned_associate_one_remaining.v1', 2),
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
        return extract_parser282_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser282_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 307
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
    assert extract_parser282_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser282_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('06e60a0f', '11.03.2020', '31.02.2020'),
    ('1cba5e22', '18.03.2020', '31.04.2020'),
    ('2409e29b', '28.02.2020', '31.02.2020'),
    ('7c8ce198', 'CHF 0', 'CHF 1'),
    ('7c8ce198', "3'200 actions", "3'201 actions"),
    ('a03fc4f1', 'CHF 0.01', 'CHF 0.02'),
    ('a03fc4f1', '06.03.2020', '31.02.2020'),
    ('b7fc4edc', '26.02.2020', '31.02.2020'),
    ('c4013245', '21.02.2020', '31.02.2020'),
    ('f68cef60', 'titulaire de 1', 'titulaire de 2'),
    ('f68cef60', "CHF 1'000", 'CHF 0'),
    ('826a1625', 'toutefois pas entre eux', 'sans restriction'),
])
def test_invalid_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new, 1)
    assert changed != args[0]
    assert extract_parser282_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['7c8ce198', 'b9d146a0'])
def test_removed_source_clause_required(prefix):
    args, kwargs = invocation(prefix)
    kwargs['source_text'] = ''
    assert extract_parser282_leftovers(*args, **kwargs) == ([], args[0])


def test_payloads():
    assert selected('06e60a0f')[0].payload['previous_date'] == '14.03.2018'
    president = selected('1cba5e22')[0]
    assert president.payload['place'] == 'Oberrieden'
    assert president.payload['previous_place'] == 'Zürich'
    assert president.signing == 'Kollektivunterschrift zu zweien'
    assert selected('2409e29b')[0].payload['decision_date'] == '28.02.2020'
    capital = selected('7c8ce198')[0].payload
    assert capital['reduced_capital'] == '0' and capital['transfer_restricted']
    assert selected('7efb981e')[0].payload['deletion_blocked']
    deputies = selected('826a1625')
    assert all(e.payload['signing_restriction'] == 'pas entre eux' for e in deputies)
    assert deputies[0].payload['excluded_co_signer'] == deputies[1].payload['name']
    renamed = selected('8795252d')[0]
    assert renamed.payload['origin'] == 'Neuhausen am Rheinfall'
    assert renamed.signing == 'Einzelunterschrift'
    assert selected('a03fc4f1')[0].payload['count'] == "20'000'000"
    assert selected('b7fc4edc')[0].payload['signing_restriction'] == 'avec un administrateur'
    board = selected('b9d146a0')
    assert [e.event_type for e in board] == ['officer_removed'] * 2 + ['officer_changed'] * 2
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in board[2:])
    assert selected('c4013245')[0].payload['previous_name'] == 'Hoxjah Ardijan'
    transfer = selected('f68cef60')
    assert [e.payload['shares'] for e in transfer] == [1, 19]
    assert transfer[1].signing == 'ohne Zeichnungsberechtigung'
