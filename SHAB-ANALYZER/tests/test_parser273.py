import hashlib
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser273 import extract_parser273_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('481cc99b', 'fr.text.share_split_preferred_voting_rights.v1', 1),
    ('588d4240', 'fr.persons.director_promotion_continued_signing.v1', 1),
    ('66be260f', 'fr.persons.administrator_vice_president_continued_signing.v1', 1),
    ('78cdc581', 'fr.persons.share_transfer_equal_holdings.v1', 2),
    ('7f3c011c', 'de.text.branch_transfer_by_split.v1', 1),
    ('7fd5115d', 'fr.persons.share_transfer_two_new_associates.v1', 3),
    ('87c6c688', 'fr.text.conditional_participation_capital_increase.v1', 1),
    ('8a40d78f', 'fr.persons.three_signers_director_relocation.v1', 3),
    ('ae4238ec', 'fr.persons.three_collective_signers_exclusion.v1', 3),
    ('da1c1a8a', 'fr.persons.two_limited_partner_contributions_reduced.v1', 2),
    ('dbb6b63f', 'fr.persons.manager_share_transfer_signing_changed.v1', 2),
    ('dc7a5c74', 'fr.persons.board_president_new_collective_member.v1', 2),
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
        return extract_parser273_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser273_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 274
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
    assert extract_parser273_leftovers(changed, *args[1:], **kwargs) == ([], changed)



@pytest.mark.parametrize('prefix,old,new', [
    ('481cc99b', "400'000 actions", "400'001 actions"),
    ('87c6c688', "35'500 bons", "35'501 bons"),
    ('87c6c688', '16.06.2016', '31.02.2016'),
    ('7fd5115d', 'cession de 134', 'cession de 135'),
    ('78cdc581', 'cession de 40', 'cession de 0'),
    ('dbb6b63f', '120 parts', '121 parts'),
    ('da1c1a8a', "5'000'000", "500'000"),
    ('ae4238ec', 'pas entre eux', 'entre eux'),
    ('66be260f', 'collectivement à deux', 'individuellement'),
    ('7f3c011c', '112 HRegV', '113 HRegV'),
])
def test_unsupported_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new, 1)
    assert changed != args[0]
    assert extract_parser273_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    split = selected('481cc99b')[0]
    assert split.payload['preferred_voting_rights'] and split.payload['restricted_by_statutes']
    assert selected('87c6c688')[0].payload['conditional']
    director = selected('588d4240')[0]
    assert director.role == 'directeur' and director.payload['previous_role'] == 'sous-directeur'
    assert director.signing == 'Kollektivunterschrift zu zweien'
    assert selected('66be260f')[0].payload['signing_continued']
    assert [e.payload['shares'] for e in selected('78cdc581')] == [100, 100]
    assert selected('7f3c011c')[0].payload['reason'] == 'Spaltung'
    seller, president, unsigned = selected('7fd5115d')
    assert [e.payload['shares'] for e in (seller, president, unsigned)] == [66, 67, 67]
    assert president.signing == 'Einzelunterschrift'
    assert unsigned.signing is None and unsigned.payload['without_signature']
    relocated, director, signer = selected('8a40d78f')
    assert relocated.payload['place'] and director.role == 'directeur général'
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in (relocated, director, signer))
    assert all(e.payload['not_with_each_other'] for e in selected('ae4238ec'))
    assert all(e.role == 'associé commanditaire' for e in selected('da1c1a8a'))
    seller, buyer = selected('dbb6b63f')
    assert seller.payload['shares'] == 80 and buyer.payload['shares'] == 120
    assert seller.signing == 'Kollektivunterschrift zu zweien' and buyer.signing == 'Einzelunterschrift'
    president, member = selected('dc7a5c74')
    assert president.role == 'administrateur président' and president.signing == 'Einzelunterschrift'
    assert member.role == 'administrateur' and member.signing == 'Kollektivunterschrift zu zweien'
