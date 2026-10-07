import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser288 import extract_parser288_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('1022c850', 'fr.persons.director_name_spelling_corrected.v1', 1), ('1910bfec', 'fr.text.statutes_date_corrected_colon.v1', 1), ('1fefe056', 'it.text.branch_added_uid_space.v1', 1), ('2430c5ec', 'fr.persons.origin_corrected_notice_typos.v1', 1), ('3c2973b9', 'fr.persons.two_new_managers_collective_signing.v1', 2), ('5fa91b71', 'fr.text.capital_reset_claim_offset.v1', 1), ('6aebeee7', 'fr.persons.share_transfer_two_recipients.v1', 4), ('7907dc58', 'fr.persons.board_president_two_individual_signatures.v1', 2), ('c91e5080', 'de.text.cross_border_merger_sole_shareholder.v1', 1), ('eb0b0201', 'fr.persons.name_corrected_exacte_typo.v1', 1), ('f2eea01d', 'fr.persons.committee_member_no_social_signature.v1', 1), ('f717e1dc', 'fr.persons.managers_liquidators_continue_collective_signing.v1', 2)]


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
        return extract_parser288_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser288_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 308
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
    assert extract_parser288_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser288_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('1022c850', '20.02.2020', '31.02.2020'),
    ('1910bfec', '19.02.2019', '31.02.2019'),
    ('2430c5ec', '08.08.2016', '32.08.2016'),
    ('1fefe056', '497.052.474', '497.052'),
    ('5fa91b71', "850'000 actions", "849'000 actions"),
    ('5fa91b71', "200'000 actions", "199'000 actions"),
    ('5fa91b71', "2'000'000", '0'),
    ('6aebeee7', 'cède 40', 'cède 41'),
    ('6aebeee7', 'titulaire de 15', 'titulaire de 14'),
    ('6aebeee7', 'titulaire de 75', 'titulaire de 19'),
    ('c91e5080', '14.02.2020', '31.02.2020'),
    ('c91e5080', "201'846'869.00", '0'),
])
def test_invalid_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new, 1)
    assert changed != args[0]
    assert extract_parser288_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_manager_signing_requires_same_clause():
    args, kwargs = invocation('3c2973b9')
    events, residue = extract_parser288_leftovers(*args, **kwargs)
    assert residue == '' and all(e.signing == 'Kollektivunterschrift zu zweien' for e in events)
    changed = args[0].removesuffix(', avec signature collective à deux')
    assert changed != args[0]
    assert extract_parser288_leftovers(changed, *args[1:], **kwargs)[1] == ''
    for source in ('', changed + '. Autre personne, avec signature collective à deux.'):
        assert extract_parser288_leftovers(changed, *args[1:], source_text=source) == ([], changed)


def test_payloads():
    director = selected('1022c850')[0]
    assert director.role == 'directeur' and director.payload['correction']
    assert director.payload['name'] == 'Da Riva Rocco' and director.payload['previous_name'] == 'Dariva Rocco'
    statutes = selected('1910bfec')[0].payload
    assert statutes['statutes_date'] == '19.02.2019' and statutes['previous_statutes_date'] == '19.02.2020'
    assert selected('1fefe056')[0].payload['branch_uid'] == 'CHE-497.052.474'
    origin = selected('2430c5ec')[0].payload
    assert origin['origin'] == 'Schwarzenburg' and origin['previous_origin'] == 'Shwarzenburg'
    managers = selected('3c2973b9')
    assert [e.payload['place'] for e in managers] == ['Choulex', 'Troinex']
    assert managers[1].payload['name'] == 'Humaraut ép. Zaksak Hélène'
    capital = selected('5fa91b71')[0].payload
    assert capital['capital'] == "8'500'000" and capital['offset'] == "2'000'000"
    transfer = selected('6aebeee7')
    assert [e.payload['shares'] for e in transfer[1:]] == [15, 75, 70]
    assert transfer[3].payload['registration'] == 'ATU45381901'
    assert all(e.signing is None for e in transfer)
    board = selected('7907dc58')
    assert board[0].role == 'administrateur président' and board[0].payload['place'] is None
    assert board[1].payload['country'] == 'FRA' and all(e.signing == 'Einzelunterschrift' for e in board)
    merger = selected('c91e5080')[0].payload
    assert merger['cross_border'] and not merger['capital_increase'] and not merger['shares_allocated']
    assert merger['registration'] == '419234' and merger['liabilities'] == '0.00'
    assert merger['transferor'] == 'Sonoco International (BVI) Inc.'
    assert merger['place'] == 'Road Town (Tortola (Britische Jungferninseln))'
    corrected = selected('eb0b0201')[0]
    assert corrected.payload['previous_name'] == 'Soria Fernando (fils)' and corrected.role is None
    committee = selected('f2eea01d')[0]
    assert committee.role == 'membre du comité' and committee.signing == 'ohne Zeichnungsberechtigung'
    liquidators = selected('f717e1dc')
    assert liquidators[0].payload['place'] == 'Vernier' and liquidators[1].payload['place'] is None
    assert all(e.role == 'gérant liquidateur' and e.signing == 'Kollektivunterschrift zu zweien' for e in liquidators)
