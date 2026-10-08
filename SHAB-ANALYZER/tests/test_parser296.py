import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser296 import extract_parser296_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('2b9c7baf', 'fr.text.share_count_capital_corrected.v1', 1), ('5443051c', 'de.text.deleted_branch_uid_spacing.v1', 1), ('67467300', 'de.persons.departure_fr_xml.v1', 1), ('7481512d', 'de.text.no_domicile_previous_no_board.v1', 1), ('9080a400', 'fr.persons.residence_changed_de_xml.v1', 1), ('94eaaeb6', 'de.persons.unproven_board_election_revoked.v1', 1), ('c83ba380', 'fr.persons.powers_revoked_typo.v1', 1), ('cda55657', 'it.text.definitive_moratorium_extended_two_months.v1', 1), ('e18ea1a8', 'it.text.contribution_partnership_corrected.v1', 1), ('e35d6cb9', 'de.text.asset_transfer_usufruct_loan.v1', 1), ('e877daaf', 'fr.text.nine_company_merger_balance_typo.v1', 2), ('fb4a531d', 'de.text.sole_proprietorship_deletion_revoked.v1', 1)]


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
        return extract_parser296_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser296_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 314
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
    assert extract_parser296_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser296_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])



@pytest.mark.parametrize('prefix', [
    '2b9c7baf', 'cda55657', 'e18ea1a8', 'e35d6cb9', 'e877daaf', 'fb4a531d',
])
def test_invalid_dates_preserved(prefix):
    args, kwargs = invocation(prefix)
    import re
    old = re.search(r"\d{2}\.\d{2}\.\d{4}", args[0])[0]
    changed = args[0].replace(old, '31.02.2020')
    assert extract_parser296_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['2b9c7baf', 'e18ea1a8', 'e877daaf'])
def test_inconsistent_balance_preserved(prefix):
    args, kwargs = invocation(prefix)
    import re
    old = re.search(r"CHF ([\d'.]+)", args[0])[1]
    changed = args[0].replace('CHF ' + old, 'CHF 1', 1)
    assert extract_parser296_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['5443051c', 'e877daaf'])
def test_source_required(prefix):
    args, kwargs = invocation(prefix)
    assert extract_parser296_leftovers(*args, source_text='') == ([], args[0])


def test_payloads():
    merger, director = selected('e877daaf')
    assert len(merger.payload['companies']) == 9
    assert merger.payload['companies'][-1]['liabilities_normalized'].endswith('.80')
    assert merger.payload['companies'][-1]['liabilities'] != merger.payload['companies'][-1]['liabilities_normalized']
    assert merger.payload['capital_increase'] is False
    assert merger.payload['shares_allocated'] is False
    assert director.role == 'administrateur'
    assert director.signing == 'Kollektivunterschrift zu zweien'
    assert selected('5443051c')[0].payload['action'] == 'branch_removed'
    assert ' ' not in selected('5443051c')[0].payload['uid_normalized']
    assert selected('67467300')[0].event_type == 'officer_removed'
    assert selected('67467300')[0].signing is None
    assert selected('9080a400')[0].payload['place']
    assert selected('94eaaeb6')[0].payload['action'] == 'election_revoked'
    assert selected('c83ba380')[0].event_type == 'officer_removed'
    assert selected('cda55657')[0].payload['months'] == 2
    assert selected('e18ea1a8')[0].payload['action'] == 'contribution_corrected'
    assert selected('e35d6cb9')[0].payload['consideration_kind'] == 'usufruct_and_loan'
    assert selected('fb4a531d')[0].payload['action'] == 'deletion_revoked'
    assert selected('7481512d')[0].payload['previous_no_board'] is True
    assert selected('2b9c7baf')[0].payload['action'] == 'capital_corrected'


def test_merger_source_signing_must_agree():
    args, kwargs = invocation('e877daaf')
    changed_source = kwargs['source_text'].replace('signature collective à deux', 'signature individuelle')
    assert extract_parser296_leftovers(*args, source_text=changed_source) == ([], args[0])


@pytest.mark.parametrize('prefix,key', [
    ('e18ea1a8', 'balance_date'), ('e877daaf', 'balance_date'),
    ('fb4a531d', 'entry_date'),
])
def test_reversed_dates_preserved(prefix, key):
    args, kwargs = invocation(prefix)
    old = selected(prefix)[0].payload[key]
    changed = args[0].replace(old, '01.01.2099')
    assert extract_parser296_leftovers(changed, *args[1:], **kwargs) == ([], changed)
