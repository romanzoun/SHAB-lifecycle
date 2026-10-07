import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser281 import extract_parser281_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('0d13608a', 'fr.persons.two_new_associates_origins.v1', 2),
    ('111ad8d8', 'fr.text.share_split_authorized_capital.v1', 1),
    ('1aff83f4', 'fr.text.foundation_purpose_change_reserved.v1', 1),
    ('2651da06', 'fr.persons.five_board_members_signing_retained.v1', 5),
    ('4385b208', 'de.text.conditional_capital_common_preferred.v1', 1),
    ('465c7fde', 'fr.persons.foundation_board_unrestricted_collective.v1', 8),
    ('5fa6c5e1', 'de.persons.dissolution_manager_liquidator.v1', 2),
    ('92d2287d', 'fr.persons.board_mixed_signing.v1', 6),
    ('a7798640', 'fr.text.other_address_corrected.v1', 1),
    ('d5ba3154', 'de.text.bankruptcy_appeal_suspensive_effect.v1', 1),
    ('e9099c89', 'fr.persons.transfer_two_unsigned_associates.v1', 3),
    ('fcb93da7', 'fr.text.bankruptcy_revoked_owner_reinstated.v1', 1),
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
        return extract_parser281_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser281_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 302
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
    assert extract_parser281_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser281_leftovers(args[0], 'it', *args[2:], **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('111ad8d8', '31 janvier 2020', '31 février 2020'),
    ('111ad8d8', 'CHF 0.01', 'CHF 0.02'),
    ('111ad8d8', "100'000'000", '0'),
    ('4385b208', '25.02.2020', '31.02.2020'),
    ('4385b208', '06.05.2019', '31.04.2019'),
    ('5fa6c5e1', '16.03.2020', '31.02.2020'),
    ('5fa6c5e1', '10 Stammanteile', '0 Stammanteile'),
    ('a7798640', '20.02.2020', '31.02.2020'),
    ('d5ba3154', '17.03.2020', '31.02.2020'),
    ('e9099c89', 'titulaire de 11', 'titulaire de 12'),
    ('e9099c89', 'cède 9', 'cède 8'),
    ('e9099c89', "CHF 1'000", 'CHF 0'),
    ('fcb93da7', '13 mars 2020', '31 février 2020'),
    ('92d2287d', 'ou collective à deux de Leclercq', 'ou collective à deux de Inconnu'),
])
def test_invalid_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new, 1)
    assert changed != args[0]
    assert extract_parser281_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    assert [e.payload['origin'] for e in selected('0d13608a')] == ['Genève', 'Zurich']
    capital = selected('111ad8d8')[0].payload
    assert capital['previous_count'] == "10'000'000"
    assert capital['count'] == "100'000'000"
    assert capital['transfer_restricted']
    assert capital['decision_date'] == '31 janvier 2020'
    assert selected('1aff83f4')[0].payload['article'] == '86a CC'
    assert selected('2651da06')[0].role.startswith('directrice,')
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in selected('2651da06'))
    conditional = selected('4385b208')[0].payload
    assert conditional['previous_date'] == '06.05.2019'
    assert conditional['preferred_date'] == '25.02.2020'
    foundation = selected('465c7fde')
    assert foundation[0].role == 'vice-président du conseil de fondation'
    assert all(e.payload['signing_restriction_removed'] for e in foundation)
    dissolution, liquidator = selected('5fa6c5e1')
    assert dissolution.payload['action'] == 'dissolution'
    assert liquidator.role == 'Gesellschafter, Geschäftsführer, Liquidator'
    assert liquidator.payload['shares'] == 10
    assert liquidator.signing == 'Einzelunterschrift'
    board = selected('92d2287d')
    assert [e.signing for e in board] == ['Kollektivunterschrift zu zweien', 'Einzelunterschrift', 'Einzelunterschrift', 'Kollektivunterschrift zu zweien', 'Kollektivunterschrift zu zweien', 'ohne Zeichnungsberechtigung']
    assert board[1].payload['previous_role'] == 'président'
    assert board[3].role == "secrétaire du conseil d'administration"
    assert board[5].payload['country'] == 'F'
    address = selected('a7798640')[0].payload
    assert address['address'] == 'rue du Puits-Godet 10a'
    assert address['previous_address'] == 'rue du Puits-Godet 8A'
    assert address['postal_code'] == '2000'
    assert selected('d5ba3154')[0].payload['action'] == 'bankruptcy_appeal_suspensive_effect'
    transfer = selected('e9099c89')
    assert [e.payload['shares'] for e in transfer] == [11, 4, 5]
    assert transfer[0].signing is None
    assert all(e.signing == 'ohne Zeichnungsberechtigung' for e in transfer[1:])
    assert selected('fcb93da7')[0].payload['decision_date'] == '13 mars 2020'
    assert selected('fcb93da7')[0].payload['action'] == 'bankruptcy_revoked_owner_reinstated'
