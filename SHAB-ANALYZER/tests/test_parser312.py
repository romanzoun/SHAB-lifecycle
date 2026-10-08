import hashlib
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser312 import extract_parser312_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('257ae106', 'fr.text.two_signatories_shared_origin_place.v1', 2),
    ('277e5406', 'fr.text.audit_waiver_removal_entry_completed.v1', 1),
    ('4702d798', 'fr.text.associate_share_split_two_nominals.v1', 1),
    ('a60092b1', 'de.text.demerger_assets_membership_continuity.v1', 1),
    ('afad8b33', 'it.text.asset_transfer_adjustable_consideration.v1', 1),
    ('c7534163', 'de.text.audit_waiver_removal_omitted.v1', 1),
    ('cfb0416d', 'fr.text.branch_register_entry_notice.v1', 1),
    ('d3eb4a72', 'fr.text.committee_secretary_collective_signing.v1', 1),
    ('d7b1aed9', 'de.text.reportable_facts_unchanged.v1', 1),
    ('e19b72f5', 'de.text.authorized_capital_change_expired.v1', 1),
    ('eafc571f', 'de.text.two_association_mergers_existing_members.v1', 2),
    ('f2070f0c', 'fr.text.branch_english_translation_corrected.v1', 1),
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
        return extract_parser312_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser312_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 318
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
    assert extract_parser312_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser312_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix', ['277e5406', 'a60092b1', 'afad8b33', 'cfb0416d', 'e19b72f5', 'eafc571f', 'f2070f0c'])
def test_invalid_dates_preserved(prefix):
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', args[0])
    assert changed != args[0]
    assert extract_parser312_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,old,new', [
    ('257ae106', 'collective à deux', 'individuelle'),
    ('277e5406', 'radiation', 'maintien'),
    ('4702d798', "28'000", "29'000"),
    ('a60092b1', 'weder eine Kapitalerhöhung', 'eine Kapitalerhöhung'),
    ('afad8b33', 'diminuire', 'aumentare'),
    ('c7534163', 'vergessen', 'vorgenommen'),
    ('cfb0416d', 'Inscription', 'Radiation'),
    ('d3eb4a72', 'secrétaire', 'président'),
    ('d7b1aed9', 'keine Änderung', 'eine Änderung'),
    ('e19b72f5', 'Ablaufs', 'Verlängerung'),
    ('eafc571f', 'bereits', 'nicht'),
    ('f2070f0c', 'traduction anglaise', 'traduction italienne'),
])
def test_unsupported_terms_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser312_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads_and_roles():
    def selected(prefix):
        rule = next(rule for stem, rule, _ in CASES if stem == prefix)
        return [e for e in parse_publication_xml(path(prefix)).events if e.rule_id == rule]
    people = selected('257ae106')
    assert len({e.person_key for e in people}) == 2
    assert all(e.signing == 'Kollektivunterschrift zu zweien' and e.payload['place'] for e in people)
    assert selected('d3eb4a72')[0].role == 'Mitglied des Vorstandes, Sekretär'
    assert selected('afad8b33')[0].payload['consideration_may_decrease'] is True
    assert selected('d7b1aed9')[0].payload['reportable_facts_changed'] is False
    mergers = selected('eafc571f')
    assert len({e.payload['absorbed_uid'] for e in mergers}) == 2
    assert all(e.event_type == 'company_merged' and e.payload['capital_increase'] is False and e.payload['share_allocation'] is False for e in mergers)
    correction = selected('f2070f0c')[0].payload
    assert correction['corrected_translation'] != correction['previous_translation']
