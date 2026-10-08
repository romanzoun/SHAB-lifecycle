import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser295 import extract_parser295_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('32ccf76e', 'de.text.new_branches_uid_spacing.v1', 7),
    ('4136c2c2', 'fr.persons.two_share_buyers_collective_managers.v1', 4),
    ('46bf60ad', 'de.text.foundation_business_asset_transfer.v1', 1),
    ('49a82aff', 'fr.persons.board_individual_signing_heading_typo.v1', 3),
    ('4f9df2b8', 'de.text.definitive_moratorium_replaces_four_months.v1', 1),
    ('56e5a368', 'de.text.previous_paid_capital_communications.v1', 1),
    ('85fbe68a', 'fr.text.transfer_balance_corrected.v1', 1),
    ('9531961a', 'it.persons.departure_restricted_signing_de_xml.v1', 2),
    ('a80750e0', 'fr.persons.share_transfer_new_manager_president.v1', 2),
    ('e4c8f29e', 'it.text.merger_wholly_owned_transferor.v1', 1),
    ('e5b1a4a6', 'fr.text.foundation_dissolved_liquidator.v1', 2),
    ('ec584ea5', 'fr.persons.share_transfer_female_manager_president.v1', 2),
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
        return extract_parser295_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser295_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 316
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
    assert extract_parser295_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser295_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('46bf60ad', '08.04.2020', '31.04.2020'),
    ('46bf60ad', "6'200'000.00", "6'200'001.00"),
    ('85fbe68a', "456'541", "456'542"),
    ('85fbe68a', '12.12.2019', '32.12.2019'),
    ('4f9df2b8', '23.03.2020', '31.02.2020'),
    ('4f9df2b8', '03.10.2020', '03.10.2019'),
    ('e4c8f29e', '31.12.2019', '31.12.2029'),
    ('e4c8f29e', '07.04.2020', '31.04.2020'),
    ('a80750e0', "1'000 parts", "1'001 parts"),
    ('ec584ea5', '200 parts', '201 parts'),
    ('4136c2c2', '18 parts', '19 parts'),
    ('4136c2c2', 'par 3 parts', 'par 4 parts'),
    ('e5b1a4a6', '24 février', '30 février'),
])
def test_invalid_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser295_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['32ccf76e', 'a80750e0', 'ec584ea5', 'e5b1a4a6'])
def test_context_requires_source_evidence(prefix):
    args, kwargs = invocation(prefix)
    for source in ['', kwargs['source_text'].replace('individuelle', 'collective à deux').replace('Zweigniederlassung neu:', 'Zweigniederlassung gelöscht:')]:
        assert extract_parser295_leftovers(*args, source_text=source) == ([], args[0])


def test_payloads():
    branches = selected('32ccf76e')
    assert branches[4].payload['uid'] == 'CHE-402. 696.489'
    assert branches[4].payload['uid_normalized'] == 'CHE-402.696.489'
    transfer = selected('46bf60ad')[0]
    assert transfer.payload['action'] == 'asset_transfer'
    assert transfer.payload['consideration'] == "6'200'000.00"
    balance = selected('85fbe68a')[0]
    assert balance.payload['net_assets'] == "456'541"
    moratorium = selected('4f9df2b8')[0]
    assert moratorium.payload['months'] == 6
    assert moratorium.payload['previous_months'] == 4
    assert moratorium.payload['court'] == 'Kreisgerichts St. Gallen'
    merger = selected('e4c8f29e')[0]
    assert merger.payload['capital_increase'] is False
    assert merger.payload['shares_allocated'] is False
    previous = selected('56e5a368')[0]
    assert previous.payload['paid_capital'] == "30'000"
    assert previous.payload['previous_method'] == 'brieflich'
    board = selected('49a82aff')
    assert [e.role for e in board] == ['présidente', 'vice-président', 'secrétaire']
    assert all(e.signing == 'Einzelunterschrift' for e in board)
    assert board[0].payload['origin'] == 'France'
    assert board[2].payload['place'] is None
    restricted = selected('9531961a')
    assert restricted[0].event_type == 'officer_removed'
    assert restricted[0].signing is None
    assert restricted[1].payload['signing_restriction'] == 'con il presidente'
    assert restricted[1].signing == 'Kollektivunterschrift zu zweien'
    assert [e.payload['shares'] for e in selected('a80750e0')] == [500, 500]
    assert selected('a80750e0')[1].role == 'associé-gérant président'
    assert selected('a80750e0')[1].signing == 'Einzelunterschrift'
    assert [e.payload['shares'] for e in selected('ec584ea5')] == [100, 100]
    assert selected('ec584ea5')[1].role == 'associée gérante présidente'
    assert selected('ec584ea5')[1].signing == 'Einzelunterschrift'
    buyers = selected('4136c2c2')
    assert [e.payload.get('shares') for e in buyers] == [12, None, 3, 3]
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in buyers[:2])
    assert all(e.signing == 'ohne Zeichnungsberechtigung' for e in buyers[2:])
    dissolved = selected('e5b1a4a6')
    assert dissolved[0].payload['decision_date'] == '24.02.2020'
    assert dissolved[1].role == 'liquidateur'
    assert dissolved[1].signing == 'Einzelunterschrift'
