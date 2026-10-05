import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser275 import extract_parser275_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('0f3b6dd3', 'fr.persons.board_president_secretary_member_individual.v1', 3),
    ('16bd80f7', 'de.text.foundation_legal_basis_removed.v1', 1),
    ('3c1cb083', 'fr.persons.domicile_corrected_entry.v1', 1),
    ('40b61920', 'fr.persons.board_member_name_corrected.v1', 1),
    ('42bd5d5a', 'fr.persons.new_manager_without_signature.v1', 1),
    ('80739abb', 'fr.persons.three_liquidators_collective.v1', 3),
    ('8a5ab5a6', 'fr.persons.subdirector_restricted_signature_procuration_removed.v1', 1),
    ('a3061a6b', 'fr.persons.president_two_board_members_individual.v1', 3),
    ('af6f037d', 'fr.persons.share_transfer_two_existing_one_unsigned.v1', 3),
    ('bd612f46', 'fr.text.registered_share_restriction_removed_supplement.v1', 1),
    ('c24765de', 'fr.persons.two_new_managers_individual.v1', 2),
    ('f7c532ff', 'fr.persons.manager_president_transfers_all_shares.v1', 2),
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
        return extract_parser275_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser275_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 275
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
    assert extract_parser275_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['0f3b6dd3', '80739abb', 'a3061a6b', 'bd612f46', 'c24765de'])
def test_removed_clause_requires_source_evidence(prefix):
    args, kwargs = invocation(prefix)
    kwargs['source_text'] = ''
    assert extract_parser275_leftovers(*args, **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('3c1cb083', '10.02.2020', '31.02.2020'),
    ('bd612f46', '07.02.2020', '31.02.2020'),
    ('af6f037d', 'pour 22 parts', 'pour 23 parts'),
    ('f7c532ff', 'désormais 200', 'désormais 99'),
    ('42bd5d5a', 'sans signature sociale', 'avec signature sociale'),
    ('8a5ab5a6', 'sa procuration est radiée', 'sa procuration est maintenue'),
])
def test_unsupported_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new, 1)
    assert changed != args[0]
    assert extract_parser275_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    board = selected('0f3b6dd3')
    assert [e.role for e in board] == ['président', 'secrétaire', "membre du conseil d'administration"]
    assert all(e.signing == 'Einzelunterschrift' for e in board)
    assert board[2].payload['country'] == 'RUS'
    assert selected('16bd80f7')[0].payload['action'] == 'legal_basis_removed'
    corrected = selected('3c1cb083')[0]
    assert corrected.payload['correction'] and corrected.payload['previous_place'] != corrected.payload['place']
    assert selected('40b61920')[0].payload['correction']
    manager = selected('42bd5d5a')[0]
    assert manager.role == 'gérant' and manager.signing is None and manager.payload['without_signature']
    assert all(e.role == 'liquidateur' and e.signing == 'Kollektivunterschrift zu zweien' for e in selected('80739abb'))
    director = selected('8a5ab5a6')[0]
    assert director.role == 'sous-directeur' and director.payload['procuration_removed']
    assert director.payload['signing_restriction'] == 'sauf avec un fondé de pouvoir ou un sous-directeur'
    president, *members = selected('a3061a6b')
    assert president.payload['signing_continued']
    assert all(e.signing == 'Einzelunterschrift' for e in members)
    associates = selected('af6f037d')
    assert [e.payload['shares'] for e in associates] == [95, 93, 22]
    assert associates[2].signing is None and associates[2].payload['without_signature']
    shares = selected('bd612f46')[0]
    assert shares.payload['shares'] == '100' and shares.payload['nominal'] == "1'000"
    assert shares.payload['action'] == 'share_transfer_restriction_removed'
    assert all(e.role == 'gérant' and e.signing == 'Einzelunterschrift' for e in selected('c24765de'))
    seller, buyer = selected('f7c532ff')
    assert seller.payload['shares'] == 0 and seller.payload['transferred_shares'] == 100
    assert buyer.payload['shares'] == 200


@pytest.mark.parametrize('prefix,suffix', [
    ('0f3b6dd3', ' avec signature individuelle'),
    ('80739abb', ' avec signature collective à deux'),
    ('a3061a6b', ' avec signature individuelle'),
    ('bd612f46', ' liées selon statuts'),
    ('c24765de', ' avec signature individuelle'),
])
def test_legacy_removed_suffix_still_requires_original_evidence(prefix, suffix):
    args, kwargs = invocation(prefix)
    assert args[0].endswith(suffix)
    shortened = args[0][:-len(suffix)]
    events, leftover = extract_parser275_leftovers(shortened, *args[1:], **kwargs)
    assert len(events) == next(count for stem, _, count in CASES if stem == prefix)
    assert leftover == ''
    kwargs['source_text'] = kwargs['source_text'].replace(suffix, ' UNKNOWN_CLAUSE')
    assert extract_parser275_leftovers(shortened, *args[1:], **kwargs) == ([], shortened)
