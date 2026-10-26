import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser385 import extract_parser385_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = ['0a0ed6a9cdc235dd12cc1f4ce95b4ad4f20ed0d82c956ca24b0982380430d4f8', '1e50a38334f3d7c4e4c164d4f6457bac35641b5ab6fbc0ae67fe80c6dbae51cf', '2596f72beab1579c4883e96c1d7a4e797a2034cd9713560c8f8dba7cd21b7503', '3350c59c7d3e2bcd7c6bad54bc9b9a1322a5b47d124b9b76461e2e57b834e7b6', '58ff2a7ae283f15a30348162d98fcbde9f0c5e5f5d22db661ed6ae154ee1c6b5', '75652d1dd8504a6c6ce94309bfeab3bdd512a6ce849b7cbd997329de4b603bb8', '7d0169584845bd9eb914ca7ce7d60b0a777e691474188311b1bbc127a3fd05d5', '83797a18e4029fc4c6bba6a700a8836252e2798ea2c878ba5889673b45ed6f02', 'a8227b2eafe805c18c0a5f712ff1d484c8bd09c7ec30cd8441153d6c0c6b5497', 'b3a8b465269842dcc8eea947129899c791ce6d72643cdcd8024763c9e6902a43', 'c45aa613c0ea0199ca397d518d44d417ff5e2d2d4307f73bc7e160f8a4d8207b', 'f50efef2ab7200a43b3771051c7c5f050a57931f799752e7680cc4737ae69587']
CONTEXT_REQUIRED = {'0a0ed6a9', '1e50a383', 'b3a8b465'}

COUNTS = {'83797a18': 2, 'b3a8b465': 4, 'c45aa613': 2}

@lru_cache(None)
def captured(digest):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser385_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser385_leftovers', capture):
        result = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert len(calls) == 1
    return result, calls[0]

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_complete_and_unchanged_legacy_payloads(digest):
    import shab_analyzer.parse as parser
    result, (args, kwargs) = captured(digest)
    added, rest = extract_parser385_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 405
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS.get(digest[:8], 1) and not rest
    with patch.object(parser, 'extract_parser385_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_unknown_suffix_and_language_preserve_input(digest):
    _, (args, kwargs) = captured(digest)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser385_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser385_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_missing_optional_source_and_invalid_dates(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser385_leftovers(*args)
    if digest[:8] in CONTEXT_REQUIRED:
        assert not events and rest == args[0]
    else:
        assert len(events) == COUNTS.get(digest[:8], 1) and not rest
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser385_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_old_event_without_new_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event


EXPECTED = [
    ('organization_changed', 'president_share_transfer_new_collective_manager', {'remaining': '10', 'transferred': '10', 'seller_signing': 'Kollektivunterschrift zu zweien'}),
    ('organization_changed', 'additional_address_fragment_and_office_deleted', {'additional_address': 'Via Surpunt 47, 7500 St. Moritz', 'deleted_address': '7505 Celerina/Schlarigna'}),
    ('status_changed', 'dissolution_corporate_general_partner_liquidator', {'dissolved': True, 'uid': 'CHE-113.709.597'}),
    ('status_changed', 'bankruptcy_opened_order_colon_time', {'time': '08:15', 'effective_date': '15.12.2020'}),
    ('officer_changed', 'procuration_now_individual', {}),
    ('organization_changed', 'asset_transfer_two_inventories_cash', {'inventory1_date': '21.02.2020', 'inventory2_date': '01.09.2020', 'consideration': "240'605.50"}),
    ('organization_changed', 'bearer_shares_converted_total_capital', {'count': '50', 'previous_kind': 'au porteur', 'share_kind': 'nominatives'}),
    ('officer_changed', 'administrator_president_signing_changed', {}),
    ('publication_corrected', 'corporate_associate_name_corrected_file_number', {'registry_id': '2363821', 'count': '200'}),
    ('officer_changed', 'cantonal_committee_members_signing', {}),
    ('organization_changed', 'female_proprietor_asset_transfer_claim', {}),
    ('organization_changed', 'conditional_participation_capital_short_issued_bonds', {'issued': '453', 'capital': "796'400", 'fully_paid': True}),
]

@pytest.mark.parametrize('digest,expected', list(zip(SUPPLIED_SHA256, EXPECTED)))
def test_explicit_meaning(digest, expected):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser385_leftovers(*args, **kwargs)
    kind, action, values = expected
    assert not rest
    assert events[0].event_type == kind
    assert events[0].rule_id == args[1] + '.text.' + action + '.v1'
    for key, value in values.items():
        assert events[0].payload[key] == value
    if digest.startswith('58ff'):
        assert events[0].signing == 'Einzelprokura'
    if digest.startswith('8379'):
        assert events[0].role == 'administrateur président'
        assert events[0].signing == 'Einzelunterschrift'
        assert events[1].payload['signing_revoked'] is True
        assert events[1].signing is None
    if digest.startswith('b3a8'):
        assert [e.signing for e in events] == ['Kollektivunterschrift zu zweien'] * 2 + [None, None]
        assert all(e.person_key and e.payload['place'] for e in events)
        assert [e.payload['signing_authorized'] for e in events] == [True, True, False, False]
    if digest.startswith('c45a'):
        assert [e.payload['net_assets'] for e in events] == ["706'095.11", "729'166.85"]

@pytest.mark.parametrize('index', [0, 1, 9])
def test_missing_or_unrelated_optional_context_preserves_residue(index):
    _, (args, _) = captured(SUPPLIED_SHA256[index])
    assert extract_parser385_leftovers(*args, source_text='Unrelated.') == ([], args[0])

@pytest.mark.parametrize('index,old,new', [
    (3, '08:15', '25:15'),
    (10, "706'095.11", "706'095.12"),
    (11, '453 bons', '454 bons'),
    (11, "7'964 bons", "7'965 bons"),
    (6, '1er décembre', '32 décembre'),
])
def test_unsupported_values_preserve_input(index, old, new):
    _, (args, kwargs) = captured(SUPPLIED_SHA256[index])
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser385_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_existing_office_rule_owns_its_complete_clause_in_isolation():
    from shab_analyzer.parser101 import _DE_BUSINESS_OFFICE_REMOVED
    text = '[gestrichen: Weiteres Geschäftslokal: 7505 Celerina/Schlarigna].'
    assert _DE_BUSINESS_OFFICE_REMOVED.fullmatch(text)
    assert extract_parser385_leftovers(text, 'de', 'p', '', None, None, None, source_text=text) == ([], text)


def test_existing_participation_rule_owns_full_issued_bond_wording_in_isolation():
    from shab_analyzer.parser242 import _FR_CONDITIONAL_PARTICIPATION_CAPITAL_INCREASE
    _, (args, kwargs) = captured(SUPPLIED_SHA256[11])
    text = args[0].replace('453 bons de CHF', '453 bons de participation de CHF')
    assert _FR_CONDITIONAL_PARTICIPATION_CAPITAL_INCREASE.fullmatch(text)
    assert extract_parser385_leftovers(text, *args[1:], **kwargs) == ([], text)


@pytest.mark.parametrize('version,prefix', [(273, '87c6c688'), (334, '5b720f18'), (358, None), (384, '683e006d')])
def test_legacy_variants_are_rejected_even_without_running_old_rule(version, prefix):
    # Capture the exact input of an old rule, then feed it directly to 385.
    import importlib
    import shab_analyzer.parse as parser
    if version == 358:
        from shab_analyzer.parser358 import extract_parser358_leftovers
        text = 'Alpha Anne continue de signer par procuration, collectivement à deux, mais désormais sans autre restriction'
        args = (text, 'fr', 'p', '', None, None, None)
        kwargs = {}
        assert extract_parser358_leftovers(*args)[0]
    else:
        old = getattr(importlib.import_module(f'shab_analyzer.parser{version}'), f'extract_parser{version}_leftovers')
        calls = []
        def capture(*args, **kwargs):
            calls.append((args, kwargs))
            return old(*args, **kwargs)
        with patch.object(parser, f'extract_parser{version}_leftovers', capture):
            parse_publication_xml(next(FIXTURES.glob(prefix + '*.xml')))
        (args, kwargs), = calls
        assert old(*args, **kwargs)[0]
    assert extract_parser385_leftovers(*args, **kwargs) == ([], args[0])
