import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser384 import extract_parser384_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = ['179839687e4441ed05bc6429f3cc46d2f5771906de371f6ab5ecc10a59ae5b00', '4e5a03d0daaef49324c2a1d04ade18947c3e54764405674618d2262a3103a41d', '5fbcf7a4eef5cbd0042faf5101f772077c123ff333241fed4633a516d8e1f2ab', '6272916844912374d3f3c0631d8f0ba7d4cc065f2edf22e508f8e070eb45fee5', '683e006dafc36a83360de0ffc81d02cf39b29616d8285d1860bd0f4ad2837587', '98e29e5c439a11d70877e97df2f366a9f6850962596b3dd7cd4e5fae90a8b50c', 'be8fd586d975a5905c80590db6d943fc6172b37958ff89b805cc2dce40c55069', 'dcb1c709e3bde2437b8587dd5c0c7363ddcbcb25e12a4fc83e30137b66522767', 'e71f3cebab9b191ea4f5a5acec34268359eab01ca7b0ab0f0c3e34586d7c817e', 'e9806dbbbccf7c08ab238d1fcdd2286908d581f9959bade44ec13c6d3c993ac8', 'ee29e5cfed68a7aa14dd420dc15e98fb3bc9cf3ed7f24d57b0891dae1652a472', 'ee534d6d1b360b76cbbf6b66491c9d75bf8460c8d58a155d8f360a6f889d7457']
CONTEXT_REQUIRED = {'62729168'}

@lru_cache(None)
def captured(digest):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser384_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser384_leftovers', capture):
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
    added, rest = extract_parser384_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 408
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == (2 if digest[:8] in {'683e006d', 'ee29e5cf'} else 1) and not rest
    with patch.object(parser, 'extract_parser384_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_unknown_suffix_and_language_preserve_input(digest):
    _, (args, kwargs) = captured(digest)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser384_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser384_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_missing_optional_source_and_invalid_dates(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser384_leftovers(*args)
    if digest[:8] in CONTEXT_REQUIRED:
        assert not events and rest == args[0]
    else:
        assert len(events) == (2 if digest[:8] in {'683e006d', 'ee29e5cf'} else 1) and not rest
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser384_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_old_event_without_new_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event


EXPECTED = [
    ('officer_changed', 'associate_manager_president_domicile_corrected', {'count': '10', 'corrected': True}),
    ('publication_corrected', 'corporate_associate_domicile_corrected', {'registry_id': '124016', 'previous_country': 'USA'}),
    ('organization_changed', 'audit_waiver_dell_declaration', {'declaration_date': '11.05.2020', 'limited_audit_waived': True}),
    ('organization_changed', 'single_share_transfer_new_collective_associate', {'remaining': '19', 'transferred_count': '1', 'buyer_signing': 'Kollektivunterschrift zu zweien'}),
    ('officer_changed', 'directresses_appointed_proxies_revoked', {'proxy_revoked': True}),
    ('organization_changed', 'private_sale_manager_shareholding_transferred', {'transferred': '100', 'total': '200', 'seller_remains_manager': True}),
    ('status_changed', 'definitive_moratorium_extended_company_decision', {'end_date': '18.05.2021', 'months': 'sechs'}),
    ('organization_changed', 'foundation_asset_transfer_recipient_uid_before_place', {'assets': "1'851'515.00", 'consideration': 'keine'}),
    ('status_changed', 'company_reinstated_liquidator_facts_retained', {'liquidator_facts_retained': True}),
    ('officer_changed', 'board_member_previous_domicile_supplemented', {'previous_place': 'Freienbach', 'corrected': True}),
    ('officer_changed', 'administratrices_appointed_signing_retained', {}),
    ('organization_changed', 'additional_addresses_deleted_mixed_labels', {'unlabelled': 'Bälliz 35, 3600 Thun'}),
]

@pytest.mark.parametrize('digest,expected', list(zip(SUPPLIED_SHA256, EXPECTED)))
def test_explicit_meaning(digest, expected):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser384_leftovers(*args, **kwargs)
    kind, action, payload = expected
    for event in events:
        assert event.event_type == kind
        assert event.rule_id == args[1] + '.text.' + action + '.v1'
        for key, value in payload.items():
            assert event.payload[key] == value
    if digest.startswith('683e'):
        assert [e.role for e in events] == ['directrice', 'directrice']
        assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in events)
    if digest.startswith('ee29'):
        assert [e.role for e in events] == ['administratrice présidente', 'administratrice']
        assert all(e.signing == 'Einzelunterschrift' for e in events)
    if digest.startswith('ee53'):
        assert len(events[0].payload['addresses']) == 7


@pytest.mark.parametrize('text,lang,pattern', [
    ("Alpha Anne et Beta Bob sont nommés directeurs avec signature individuelle; leur procuration est radiée.", 'fr', '_FR_TWO_APPOINTED_DIRECTORS_PROXY_REVOKED'),
    ("Alpha Anne détient désormais 19 parts de CHF 100 par suite de cession d'une part de CHF 100 à Beta Bob, d'Afghanistan, à Thônex, AFG, nouvel associé pour une part de CHF 100, sans signature sociale.", 'fr', '_FR_ONE_SHARE_TRANSFER_UNSIGNED_BUYER'),
    ('[gestrichen: Weitere Adresse: Beispielweg 1, 8000 Zürich.].', 'de', '_DE_REMOVED_ADDITIONAL_ADDRESSES'),
])
def test_legacy_ownership_in_isolation(text, lang, pattern):
    import shab_analyzer.parser384 as new
    assert getattr(new, pattern).fullmatch(text)
    assert extract_parser384_leftovers(text, lang, 'p', '', None, None, None, source_text=text) == ([], text)


def test_optional_context_cannot_be_replaced():
    digest = SUPPLIED_SHA256[3]
    _, (args, _) = captured(digest)
    assert extract_parser384_leftovers(*args, source_text='Unrelated.') == ([], args[0])


def test_invalid_hyphenated_date_preserves_input():
    _, (args, kwargs) = captured(SUPPLIED_SHA256[1])
    changed = args[0].replace('22-10-2020', '31-02-2020')
    assert extract_parser384_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_impossible_private_sale_count_preserves_input():
    _, (args, kwargs) = captured(SUPPLIED_SHA256[5])
    changed = args[0].replace('Les 100 parts', 'Les 201 parts')
    assert extract_parser384_leftovers(changed, *args[1:], **kwargs) == ([], changed)
