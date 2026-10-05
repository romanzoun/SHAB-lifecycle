import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser276 import extract_parser276_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('35256965', 'fr.persons.manager_president_name_corrected_notice.v1', 1),
    ('38f5dbfa', 'fr.persons.board_presidency_changed_signing_continued.v1', 2),
    ('4a0eefd1', 'fr.persons.two_managers_equal_transfer_new_manager.v1', 3),
    ('6049658a', 'fr.persons.committee_vice_president_secretary_collective.v1', 2),
    ('690f27f5', 'fr.persons.two_board_liquidators_signing_continued.v1', 2),
    ('7ceafdf6', 'de.text.asset_transfer_price_adjustment_reserved.v1', 1),
    ('9ebe3118', 'fr.persons.two_associates_transfer_unsigned_new_associate.v1', 3),
    ('9fede94c', 'fr.persons.three_associate_managers_individual.v1', 3),
    ('d0adcec1', 'fr.persons.two_managers_transfer_collective_three.v1', 3),
    ('d884d0bc', 'fr.persons.associate_manager_name_corrected.v1', 1),
    ('e110dcd9', 'de.persons.associate_chair_manager_name_changed.v1', 1),
    ('fc027cb0', 'fr.text.bankruptcy_appeal_rejected_effective_time.v1', 1),
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
        return extract_parser276_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser276_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 276
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
    assert extract_parser276_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser276_leftovers(args[0], 'it', *args[2:], **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('35256965', '14.02.2001', '31.02.2001'),
    ('d884d0bc', '10.02.2020', '31.02.2020'),
    ('7ceafdf6', '06.02.2020', '31.02.2020'),
    ('fc027cb0', '29.01.2020', '31.02.2020'),
    ('fc027cb0', '10h0', '24h0'),
    ('fc027cb0', '10h0', '10h60'),
    ('4a0eefd1', 'avec 50 parts', 'avec 51 parts'),
    ('4a0eefd1', 'de 75 parts', 'de 76 parts'),
    ('d0adcec1', 'avec 67 parts', 'avec 68 parts'),
    ('d0adcec1', 'de 67 et 66', 'de 67 et 65'),
    ('9ebe3118', 'associée 2 parts', 'associée 3 parts'),
    ('9ebe3118', 'de 13 parts', 'de 12 parts'),
    ('e110dcd9', '70 Stammanteile', '0 Stammanteile'),
    ('9fede94c', 'signature individuelle', 'signature collective à deux'),
])
def test_invalid_or_unsupported_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new, 1)
    assert changed != args[0]
    assert extract_parser276_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    for prefix in ('35256965', 'd884d0bc'):
        e = selected(prefix)[0]
        assert e.payload['correction'] and e.payload['previous_name'] != e.payload['name']
    board = selected('38f5dbfa')
    assert [e.role for e in board] == ['administratrice présidente', 'administrateur']
    assert all(e.signing == 'Kollektivunterschrift zu zweien' and e.payload['signing_continued'] for e in board)
    assert board[1].payload['previous_role'] == 'président'
    committee = selected('6049658a')
    assert [e.role for e in committee] == ['membre du comité vice-présidente', 'membre du comité secrétaire']
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in committee)
    liquidators = selected('690f27f5')
    assert all(e.role == 'liquidateur' and e.signing == 'Einzelunterschrift' and e.payload['signing_continued'] for e in liquidators)
    assert [e.payload['board_role'] for e in liquidators] == ['président', 'secrétaire']
    managers = selected('9fede94c')
    assert [e.role for e in managers] == ['associé-gérant président', 'associé-gérant', 'associé-gérant']
    assert all(e.signing == 'Einzelunterschrift' for e in managers)
    changed = selected('e110dcd9')[0]
    assert changed.payload['shares'] == 70 and changed.payload['previous_name'] != changed.payload['name']
    assert changed.signing == 'Kollektivunterschrift zu zweien'
    transfer = selected('7ceafdf6')[0].payload
    assert transfer['action'] == 'asset_transfer' and transfer['price_adjustment_reserved']
    assert transfer['assets'] == "3'700'000.00" and transfer['liabilities'] == "1'300'818"
    assert transfer['consideration'] == "2'799'182" and transfer['recipient_uid'].startswith('CHE-')
    bankruptcy = selected('fc027cb0')[0].payload
    assert bankruptcy['action'] == 'bankruptcy_appeal_rejected' and bankruptcy['effective_time'] == '10:00'
    assert bankruptcy['effective_date'] == bankruptcy['decision_date']
    for prefix, shares, transferred in [('4a0eefd1', [75, 75, 50], [25, 25]), ('d0adcec1', [67, 66, 67], [33, 34]), ('9ebe3118', [13, 5, 2], [1, 1])]:
        people = selected(prefix)
        assert [e.payload['shares'] for e in people] == shares
        assert [e.payload['transferred_shares'] for e in people[:2]] == transferred
        assert people[2].payload['origin'] and people[2].payload['place']
    equal = selected('4a0eefd1')
    assert equal[0].payload['place'] == equal[1].payload['place']
    assert all(e.signing is None for e in equal[:2])
    assert equal[2].signing == 'Kollektivunterschrift zu zweien'
    assert all(e.signing == 'Kollektivunterschrift zu dreien' for e in selected('d0adcec1'))
    unsigned = selected('9ebe3118')[2]
    assert unsigned.signing is None and unsigned.payload['without_signature']
