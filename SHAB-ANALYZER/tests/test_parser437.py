import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser437 import extract_parser437_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '384c2df3999d3936131f04916e6a38ac876aa6594f1c11fa88657884af3e1b8d', '40739069f6c5a5a5ab412ba49d508b03698f47571555bff6abad5cff78c5969a', '4a8476a47d5f4fdfa028d50205e3a25222809b711ced14dde7e9fb8cc9c0f76c', '7b3923da87759335ccc74b8db6b97e6d6d6a66c33a0b6eb5faba04c84d465fd9', 'a341287297ba96e1938916b070b26a6384cd05b7aad34facefaf830c80dd6cf8', 'c2847660e7db008fe3bbbd74c675fb6a6ad9b9c1343aae2a0861c0910b1d4159', 'c8c2c081500b0b4e210a8a63877df5af45ac5aaf186938a67b43611ba6454c28', 'da5cf49f4489b8ef3a3a07b058ba8121f4db76bf1523f03a24b3c5ffad3fca85', 'e3403980c0f92f88a722f37aa2379aeba466760f232a5cbe38f256f583b43105', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
COUNTS = [0, 0, 0, 1, 2, 2, 0, 1, 1, 1, 1, 0]
NEW_CASES = [i for i, count in enumerate(COUNTS) if count]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser437_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser437_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(path)
    assert len(calls) == 1
    return result, old, calls[0]


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('index', NEW_CASES)
def test_complete_and_unchanged_old_payloads(index):
    result, old, (args, kwargs) = captured(index)
    added, rest = extract(*args, **kwargs)
    assert PARSER_VERSION == 443
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    assert len(added) == COUNTS[index] and rest == ''
    assert old.leftover_text == args[0]
    assert result.events == old.events + added
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('index', NEW_CASES)
def test_unknown_suffix_language_and_invalid_dates(index):
    _, _, (args, kwargs) = captured(index)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract(changed, *args[1:], **kwargs) == ([], changed)
    assert extract(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index', NEW_CASES)
def test_missing_optional_metadata_and_source(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args[:4], None, None, None, **kwargs)
    assert len(events) == COUNTS[index] and rest == ''
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    events, rest = extract(*args)
    assert len(events) == COUNTS[index] and rest == ''


def test_old_event_without_optional_attributes():
    event = Event('p', '', 'officer_changed', 'legacy.rule', payload={'name': 'Test Anna'})
    assert Event(**vars(event)) == event
    assert event.payload == {'name': 'Test Anna'}
    assert event.role is None and event.signing is None


@pytest.mark.parametrize('index', NEW_CASES)
def test_no_overlap_with_old_rules_even_in_isolation(index):
    # Exercise every historical extractor on the complete clause in isolation.
    import inspect
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(index)
    for name, old_extract in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser437_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name


@pytest.mark.parametrize('index,owner', [(0, 60), (1, 55), (2, 55), (6, 60), (11, 55)])
def test_existing_formulations_retain_historical_ownership(index, owner):
    import importlib
    result, old, (args, kwargs) = captured(index)
    old_extract = getattr(importlib.import_module(f'shab_analyzer.parser{owner}'), f'extract_parser{owner}_leftovers')
    expected = old_extract(*args)
    assert expected[0] or expected[1] != args[0]
    assert extract(*args, **kwargs) == ([], args[0])
    assert result == old
    assert result.status == 'PARTIALLY_PARSED'
    assert old_extract(*args) == expected


@pytest.mark.parametrize('index,kind,action,expected', [
    (3, 'status_changed', 'summary_bankruptcy_proceedings_ordered_article231', {'bankruptcy_procedure': 'summarisch', 'legal_basis': 'Art. 231 SchKG', 'decision_date': '17.02.2021'}),
    (4, 'ownership_changed', 'two_transferors_person_and_company_new_manager', {'count1': '10', 'count2': '30', 'buyer_count': '40', 'remaining1': '40', 'remaining2': '120', 'seller_uid2': 'CHE-428.099.591'}),
    (5, 'ownership_changed', 'partial_transfer_new_unsigned_female_associate_de_origin', {'count': '60', 'previous_count': '200', 'remaining': '140'}),
    (7, 'organization_changed', 'company_name_changed_two_translations', {'name': 'Med-Innova SA', 'german_name': 'Med-Innova AG', 'english_name': 'Med-Innova Ltd'}),
    (8, 'audit_requirement_changed', 'opting_out_erroneous_bracket_corrected', {'limited_audit_waived': False, 'kind': 'limited_audit_waiver'}),
    (9, 'officer_changed', 'liquidator_appointed_name_with_initial', {'name': 'Grass Hans W.'}),
    (10, 'status_changed', 'sole_proprietorship_erroneous_deletion_request_reinstated', {'reinstated': True, 'erroneous_deletion_request': True, 'entry': '140', 'entry_date': '04.01.2021'}),
])
def test_evidenced_semantics(index, kind, action, expected):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    assert rest == ''
    assert events[0].event_type == kind
    assert events[0].rule_id == f'{args[1]}.text.{action}.v1'
    for key, value in expected.items():
        assert events[0].payload[key] == value
    if index in (4, 5):
        assert events[1].role == ('associé-gérant' if index == 4 else 'associée')
        assert events[1].signing == (None if index == 4 else 'ohne Zeichnungsberechtigung')
        assert events[1].payload['name'] == events[0].payload['buyer']
        assert events[1].payload['place'] == events[0].payload['place']
    if index == 9:
        assert events[0].role == 'Liquidator' and events[0].signing is None


@pytest.mark.parametrize('index,before,after', [(4, 'avec 40 parts', 'avec 41 parts'), (5, 'de 140 parts', 'de 141 parts'), (5, 'CHF 100', 'CHF 0')])
def test_transfer_rejects_inconsistent_or_zero_amounts(index, before, after):
    _, _, (args, kwargs) = captured(index)
    changed = args[0].replace(before, after)
    assert changed != args[0]
    assert extract(changed, *args[1:], **kwargs) == ([], changed)


def test_old_audit_waiver_formulation_keeps_its_rule_and_payload():
    from shab_analyzer.parser211 import extract_parser211_leftovers
    text = '[Der Verzicht auf eine eingeschränkte Revision wurde fälschlicherweise eingetragen.]'
    args = (text, 'de', 'p', '', None, None, None)
    events, rest = extract_parser211_leftovers(*args)
    assert rest == '' and len(events) == 1
    assert events[0].rule_id == 'de.text.audit_waiver_erroneous_bracket.v1'
    assert events[0].payload == {'kind': 'limited_audit_waiver', 'action': 'erroneous_entry_corrected', 'limited_audit_waived': False}
    assert extract(*args) == ([], text)
