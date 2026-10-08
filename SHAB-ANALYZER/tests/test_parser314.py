import hashlib
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser314 import extract_parser314_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('1055dd82', 'de.text.manager_nationality_corrected.v1', 1),
    ('29d242db', 'de.text.two_mergers_common_member_no_allocation.v1', 2),
    ('3d02cee9', 'it.text.merger_same_person_no_share_allocation.v1', 1),
    ('46941b70', 'fr.text.merger_shortfall_subordinated_claim_free_equity.v1', 1),
    ('603a1e42', 'de.text.bankruptcy_summary_proceedings_reopened.v1', 1),
    ('79620539', 'fr.text.transferred_share_nominal_corrected.v1', 1),
    ('afa7bdce', 'fr.text.authorized_capital_deleted_amount_reached.v1', 1),
    ('b0d988ff', 'it.text.merger_uid_before_place_common_shareholder.v1', 1),
    ('b2a12a74', 'fr.text.new_administrator_foreign_residence.v1', 1),
    ('ba8f4156', 'de.text.partial_assets_transferred_shares_claim.v1', 1),
    ('c4b2bfd6', 'fr.text.partial_shares_transferred_legal_entity.v1', 1),
    ('cddf0e11', 'de.text.merger_wholly_owned_no_stammanteile.v1', 1),
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
        return extract_parser314_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser314_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 317
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
    assert extract_parser314_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser314_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])



@pytest.mark.parametrize('prefix', [case[0] for case in CASES if case[0] not in ('b2a12a74', 'c4b2bfd6')])
def test_invalid_dates_preserved(prefix):
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', args[0])
    assert changed != args[0]
    assert extract_parser314_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,old,new', [
    ('1055dd82', 'Geschäftsführer', 'Liquidator'),
    ('29d242db', 'weder eine Kapitalerhöhung', 'eine Kapitalerhöhung'),
    ('3d02cee9', 'senza aumento', 'con aumento'),
    ('46941b70', 'créance postposée', 'créance ordinaire'),
    ('603a1e42', 'Wiedereröffnung', 'Einstellung'),
    ('79620539', 'cède', 'acquiert'),
    ('afa7bdce', 'atteint', 'réduit'),
    ('b0d988ff', 'senza aumento', 'con aumento'),
    ('b2a12a74', 'collective à deux', 'individuelle'),
    ('ba8f4156', '100%', '50%'),
    ('c4b2bfd6', '150 parts', '151 parts'),
    ('cddf0e11', 'sämtliche Stammanteile', 'einige Stammanteile'),
])
def test_unsupported_terms_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser314_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    def selected(prefix):
        rule = next(rule for stem, rule, _ in CASES if stem == prefix)
        return [e for e in parse_publication_xml(path(prefix)).events if e.rule_id == rule]
    assert selected('1055dd82')[0].signing == 'Einzelunterschrift'
    assert selected('b2a12a74')[0].signing == 'Kollektivunterschrift zu zweien'
    assert selected('603a1e42')[0].payload['dissolved_by_bankruptcy'] is True
    assert selected('ba8f4156')[0].payload['fully_paid'] is True
    assert selected('c4b2bfd6')[0].payload['recipient_uid'].startswith('CHE-')
    mergers = selected('29d242db')
    assert len({e.payload['absorbed_uid'] for e in mergers}) == 2
    for prefix in ('29d242db', '3d02cee9', '46941b70', 'b0d988ff', 'cddf0e11'):
        assert all(e.event_type == 'company_merged' and e.payload['capital_increase'] is False and e.payload['shares_allocated'] is False for e in selected(prefix))
    assert selected('46941b70')[0].payload['claims_subordinated'] is True
