import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser277 import extract_parser277_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('01467ed2', 'fr.persons.manager_presidency_replaced.v1', 4),
    ('086c9191', 'fr.text.share_split_two_conditional_capital_clauses.v1', 1),
    ('48a76681', 'de.text.cooperative_asset_transfer_inventory.v1', 1),
    ('5b3252b7', 'fr.text.share_transfer_restrictions_removed_paid_capital.v1', 1),
    ('8d0f7974', 'fr.persons.foundation_presidency_changed.v1', 2),
    ('90c2a98e', 'de.text.sole_proprietor_bankruptcy_revoked.v1', 1),
    ('d170b1f2', 'fr.persons.three_holders_transfer_new_manager.v1', 4),
    ('d3117ac9', 'it.text.historical_in_kind_contributions_abrogated.v1', 1),
    ('db923ab3', 'fr.persons.manager_transfer_unsigned_associate.v1', 2),
    ('dbc3d6e6', 'fr.persons.restricted_signing_partner_corrected.v1', 2),
    ('ecd2b941', 'fr.persons.associate_appointed_manager_collective.v1', 1),
    ('f6cc7a66', 'fr.persons.associate_transfer_unsigned_abroad.v1', 2),
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
        return extract_parser277_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser277_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION >= 277
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
    assert extract_parser277_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser277_leftovers(args[0], 'de' if args[1] == 'it' else 'it', *args[2:], **kwargs) == ([], args[0])



@pytest.mark.parametrize('prefix,old,new', [
    ('086c9191', 'CHF 0.01', 'CHF 0.02'),
    ('086c9191', '31 janvier', '32 janvier'),
    ('48a76681', '15.01.2020', '31.02.2020'),
    ('90c2a98e', '05.02.2020', '31.02.2020'),
    ('90c2a98e', '10.55 Uhr', '24.55 Uhr'),
    ('90c2a98e', '10.55 Uhr', '10.60 Uhr'),
    ('db923ab3', 'avec 25 parts', 'avec 26 parts'),
    ('db923ab3', 'titulaire de 25', 'titulaire de 24'),
    ('f6cc7a66', '100 de ses', '201 de ses'),
    ('d170b1f2', 'pour 225 parts', 'pour 226 parts'),
    ('dbc3d6e6', '26.08.2019', '31.02.2019'),
    ('5b3252b7', "CHF 100'000", "CHF 100'001"),
    ('ecd2b941', 'signature collective à deux', 'signature individuelle'),
])
def test_invalid_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new, 1)
    assert changed != args[0]
    assert extract_parser277_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['5b3252b7', 'd3117ac9'])
def test_removed_context_required(prefix):
    args, kwargs = invocation(prefix)
    assert extract_parser277_leftovers(*args, source_text='') == ([], args[0])


def test_payloads():
    managers = selected('01467ed2')
    assert [e.role for e in managers] == ['gérant', 'gérant', 'gérant président', 'gérant vice-président']
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in managers)
    assert [e.payload['previous_role'] for e in managers[:2]] == ['président', 'vice-président']
    foundation = selected('8d0f7974')
    assert [e.role for e in foundation] == ['membre du conseil présidente', 'membre du conseil']
    assert all(e.payload['signing_continued'] for e in foundation)
    assert selected('ecd2b941')[0].signing == 'Kollektivunterschrift zu zweien'
    assert [e.payload['shares'] for e in selected('db923ab3')] == [25, 25]
    assert selected('db923ab3')[1].payload['without_signature']
    abroad = selected('f6cc7a66')
    assert abroad[0].payload['shares'] == 100
    assert abroad[1].payload['received_shares'] == 100 and abroad[1].payload['country'] == 'D'
    assert abroad[1].signing is None and abroad[1].payload['without_signature']
    holders = selected('d170b1f2')
    assert all(e.payload['shares'] == 225 for e in holders)
    assert all(e.role is None and e.signing is None for e in holders[:3])
    assert holders[3].role == 'associé-gérant' and holders[3].signing == 'Einzelunterschrift'
    corrected = selected('dbc3d6e6')
    assert all(e.payload['correction'] and len(e.payload['signing_partners']) == 3 for e in corrected)
    assert corrected[0].payload['partner2'] != corrected[0].payload['previous_name']
    transfer = selected('48a76681')[0].payload
    assert transfer['action'] == 'asset_transfer' and transfer['inventory_date'] == '31.12.2019'
    assert transfer['assets'] == "215'959'907.06" and transfer['consideration'] == "9'751'440.59"
    bankruptcy = selected('90c2a98e')[0].payload
    assert bankruptcy['action'] == 'bankruptcy_revoked' and bankruptcy['continued']
    assert bankruptcy['previous_effective_time'] == '10:55'
    split = selected('086c9191')[0].payload
    assert split['conditional_capital_clauses'] == 2 and split['transfer_restricted']
    assert split['count'] == "10'000'000" and split['decision_date'] == '2020-01-31'
    capital = selected('5b3252b7')[0].payload
    assert capital['fully_paid'] and capital['statutes_date'] == '29.01.2020'
    historical = selected('d3117ac9')[0].payload
    assert historical['action'] == 'in_kind_contribution_provisions_removed'
    assert historical['amount1'] == "19'000" and historical['amount2'] == "1'000"
