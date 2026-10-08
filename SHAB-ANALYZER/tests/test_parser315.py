import hashlib
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser315 import extract_parser315_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('039edb5b', 'fr.text.partial_shares_transferred_unsigned_associate.v1', 2),
    ('1201f5b6', 'fr.text.sole_associate_name_number_changed_typo.v1', 1),
    ('1542bd49', 'de.text.erroneous_audit_waiver_deleted.v1', 1),
    ('2d4574cb', 'de.text.assets_transferred_without_liabilities.v1', 1),
    ('2eebc644', 'fr.text.partial_shares_transferred_manager_president.v1', 3),
    ('3b393b55', 'it.text.previous_audit_waiver_deleted.v1', 1),
    ('8989411d', 'fr.text.capital_reduced_increased_claim_offset.v1', 1),
    ('9e37156b', 'fr.text.board_treasurer_signing_revoked_members_added.v1', 3),
    ('a7725dea', 'fr.text.audit_waiver_deleted_auditor_typo.v1', 1),
    ('c1afc178', 'de.text.merger_common_shareholders_missing_punctuation.v1', 1),
    ('c294bc05', 'fr.text.two_administrators_individual_signing.v1', 2),
    ('dfbf2626', 'de.text.capital_nominal_zero_restored_claim_offset.v1', 1),
]


def path(prefix):
    paths = list(FIXTURES.glob(prefix + '*.xml'))
    assert len(paths) == 1
    return paths[0]


def invocation(prefix):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser315_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser315_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 319
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
    assert extract_parser315_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser315_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])



@pytest.mark.parametrize('prefix', ['2d4574cb', '3b393b55', '8989411d', 'c1afc178', 'dfbf2626'])
def test_invalid_dates_preserved(prefix):
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', args[0])
    assert changed != args[0]
    assert extract_parser315_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,old,new', [
    ('039edb5b', '160 parts', '161 parts'),
    ('2eebc644', '101 parts', '102 parts'),
    ('8989411d', "30'000'000.00", "30'000'001.00"),
    ('dfbf2626', 'CHF 0.00', 'CHF 0.50'),
    ('c1afc178', 'sämtliche Aktien', 'einige Aktien'),
    ('c294bc05', 'individuellement', 'collectivement'),
    ('9e37156b', 'collective à deux', 'individuelle'),
    ('2d4574cb', 'ohne Passiven', 'mit Passiven'),
])
def test_unsupported_terms_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser315_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads_and_signing():
    def selected(prefix):
        rule = next(rule for stem, rule, _ in CASES if stem == prefix)
        return [e for e in parse_publication_xml(path(prefix)).events if e.rule_id == rule]
    for prefix in ('1542bd49', '3b393b55', 'a7725dea'):
        assert selected(prefix)[0].payload['audit_waiver'] is False
    assert selected('2d4574cb')[0].payload['liabilities'] == '0'
    merger = selected('c1afc178')[0]
    assert merger.event_type == 'company_merged'
    assert merger.payload['capital_increase'] is False
    assert merger.payload['shares_allocated'] is False
    assert [e.signing for e in selected('2eebc644')] == [None, 'Kollektivunterschrift zu zweien', 'Einzelunterschrift']
    assert [e.signing for e in selected('9e37156b')] == ['ohne Zeichnungsberechtigung', 'Kollektivunterschrift zu zweien', 'ohne Zeichnungsberechtigung']
    assert all(e.signing == 'Einzelunterschrift' for e in selected('c294bc05'))
    for prefix in ('8989411d', 'dfbf2626'):
        assert selected(prefix)[0].payload['fully_paid'] is True
