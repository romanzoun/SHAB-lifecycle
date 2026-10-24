import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser323 import extract_parser323_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('3d76a503', 'fr.text.branch_label_added.v1', 1),
    ('4f3a409a', 'fr.text.assets_transfer_registered_shares.v1', 1),
    ('58990a3b', 'fr.text.civil_status_name_changed.v1', 1),
    ('73692624', 'de.text.bankruptcy_order_revoked_on_appeal.v1', 1),
    ('89c913dc', 'fr.text.administrator_signing_revoked.v1', 1),
    ('8feb80c9', 'de.text.official_deletion_pending_tax_consent.v1', 1),
    ('a0ccab8a', 'fr.text.associate_manager_share_transfer.v1', 1),
    ('c0c6347c', 'fr.text.composition_moratorium_extended.v1', 1),
    ('c3c690fd', 'fr.text.registered_share_split.v1', 1),
    ('c8c10bfe', 'fr.text.individual_signing_changed_to_procuration.v1', 1),
    ('cf486186', 'fr.text.headquarters_uid_and_registration_clauses_changed.v1', 1),
    ('e648f846', 'fr.text.person_domicile_entry_completed.v1', 1),
]


def path(prefix):
    paths = list(FIXTURES.glob(prefix + '*.xml'))
    assert len(paths) == 1
    return paths[0]


@lru_cache(None)
def captured(prefix):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser323_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser323_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    result, _ = captured(prefix)
    rule = next(rule for stem, rule, _ in CASES if stem == prefix)
    return [e for e in result.events if e.rule_id == rule]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 393
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    with patch.object(parser, 'extract_parser323_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert [e for e in result.events if e.rule_id != rule] == baseline.events
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser323_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser323_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]


@pytest.mark.parametrize('prefix', ['1cf200d1', 'c9cb541c', 'e3c5c5cd', '94b72118-d3cb-46f4-8cf3-8d526586b9f2'])
def test_previous_fixtures_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    with patch.object(parser, 'extract_parser323_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert parse_publication_xml(fixture) == baseline
    # Existing payloads can still construct events without any new attributes.
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_invalid_dates_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    dates = set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0]))
    for date in dates:
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser323_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed


def test_payload_semantics_and_missing_optional_attributes():
    assert selected('3d76a503')[0].payload['branch_uid'].startswith('CHE-')
    assert selected('4f3a409a')[0].payload['fully_paid'] is True
    renamed = selected('58990a3b')[0]
    assert renamed.person_key and renamed.payload['name'] != renamed.payload['previous_name']
    assert renamed.signing is None and renamed.role is None
    assert selected('73692624')[0].payload['bankruptcy_revoked'] is True
    assert selected('89c913dc')[0].signing == 'ohne Zeichnungsberechtigung'
    assert selected('89c913dc')[0].role == 'Verwaltungsrat'
    assert selected('8feb80c9')[0].payload['deletion_pending'] is True
    assert selected('a0ccab8a')[0].payload['remaining_shares'] == '100'
    assert selected('a0ccab8a')[0].event_type == 'ownership_changed'
    assert selected('c0c6347c')[0].payload['months'] == '6'
    assert selected('c3c690fd')[0].payload['restricted_transfer'] is True
    assert selected('c3c690fd')[0].event_type == 'capital_changed'
    assert selected('c8c10bfe')[0].signing == 'Einzelprokura'
    assert selected('cf486186')[0].payload['registration_clause_removed'] is True
    domicile = selected('e648f846')[0]
    assert domicile.payload['place'] and domicile.role is None and domicile.signing is None
    for prefix, _, _ in CASES:
        for old in selected(prefix):
            assert Event(**vars(old)) == old


@pytest.mark.parametrize('prefix', ['3d76a503', '4f3a409a', '58990a3b', 'c3c690fd'])
def test_fragment_requires_supporting_source(prefix):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser323_leftovers(*args)
    assert not events and leftover == args[0]
    events, leftover = extract_parser323_leftovers(*args, source_text='unsupported')
    assert not events and leftover == args[0]


@pytest.mark.parametrize('prefix,old,new', [
    ('c3c690fd', "110'000", "110'001"),
    ('a0ccab8a', 'pour 100 parts', 'pour 101 parts'),
    ('89c913dc', "n'exerce plus", 'exerce'),
    ('cf486186', '[biffé]', '[inchangé]'),
    ('c0c6347c', '29 mai 2020', '32 mai 2020'),
    ('c0c6347c', '18 novembre 2020', '31 novembre 2020'),
])
def test_inconsistent_or_unsupported_terms_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    events, leftover = extract_parser323_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix', ['308db91d', '36fceb37', '4f6fc83d', '5ceafc07',
    '624c412f', '6a2ac180', '828d5d8a', '82bb3513', '9e29ee21', 'b299fa9e',
    'b522080a', 'd6e20ba9'])
def test_parser322_results_unchanged(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser323_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
