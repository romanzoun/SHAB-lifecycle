import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser390 import extract_parser390_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = ['0dbf7ff5b7843c3a132760c1f76382a4f20624c30126f6b6e83ff3405890334b', '172dd5b4cb3b98680ddee27edd60400fffc66fc207ef60f6a7e42eaa629e0050', '1f98d3c1134ce8504e8b4ca29bd9d70a5a29856bebc8c84003fc11ecf14d909f', '3e8f8579ab94803d0fc9cf63cacd2cdd0115a82d7aff4632960e869fe36160a7', '483b226c9400bd50376d1f961a31ebc5db05094fe6750f6007607e9b31b5ddfb', '4875f046d3c14dd473b9851efd3a7af5247bf3b5880e5849f3cb0c0d51fc44ce', '71846bdab591402fd4eaa338fbffc6a675eef0699199e5c3f1ba92f3d0df539e', '80705f311b187d7fb3adcd842e9b8a25b0e166d3a82daad64dbd7435628eefe1', 'bb30e426fea9fc50813d105d37112dfee11ce935d230d83ee99857adf0e60227', 'be61aa85eae6dcc05ecadb835103ed931e64e7bb6e38f7f1a5f90772b098266c', 'da0ca53e034e8c893e24231c064f5493e392039acb35a9116ba5bb96e2313c48', 'ea7a81467727421b29aae50312b5906a76e1fc73f3804e20d7cc446ff747fcb1']
CONTEXT_REQUIRED = set()
COUNTS = {"80705f31": 3}

@lru_cache(None)
def captured(digest):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser390_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser390_leftovers', capture):
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
    added, rest = extract_parser390_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 424
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS.get(digest[:8], 1) and not rest
    with patch.object(parser, 'extract_parser390_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_unknown_suffix_and_language_preserve_input(digest):
    _, (args, kwargs) = captured(digest)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser390_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser390_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_missing_optional_source_and_invalid_dates(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser390_leftovers(*args)
    if digest[:8] in CONTEXT_REQUIRED:
        assert not events and rest == args[0]
    else:
        assert len(events) == COUNTS.get(digest[:8], 1) and not rest
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser390_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_old_event_without_new_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event



@pytest.mark.parametrize('module_name,pattern_name,text,language', [
    ('parser138', '_FR_PROXY_REVOKED_APPOINTED_MANAGEMENT_MEMBER', 'Exemple Anne, dont la procuration est éteinte, est nommé membre de la direction et engage désormais la société par sa signature collective à deux', 'fr'),
    ('parser152', '_DE_COMPOSITION_MORATORIUM_LIFTED', 'Mit Verfügung vom 01.01.2020 der Behörde wurde die Nachlassstundung aufgehoben', 'de'),
])
def test_legacy_patterns_retain_ownership(module_name, pattern_name, text, language):
    import importlib
    from shab_analyzer.parser390 import _LEGACY
    module = importlib.import_module('shab_analyzer.' + module_name)
    pattern = getattr(module, pattern_name)
    assert pattern in _LEGACY and pattern.fullmatch(text)
    assert getattr(module, 'extract_' + module_name + '_leftovers')(text, language, 'p', '', None, None, None)[0]
    assert extract_parser390_leftovers(text, language, 'p', '', None, None, None) == ([], text)

EXPECTED_ACTIONS = [
    'proxy_revoked_management_new_origin',
    'auditor_appointed_waiver_repealed_typo',
    'three_associates_transfer_remaining_holdings',
    'authorized_capital_clause_replaced',
    'auditor_uid_missing_hyphen',
    'composition_moratorium_lifted_previous_order',
    'ancillary_obligations_preference_rights_statutes',
    'share_transfer_manager_president_former_director',
    'authorized_capital_clause_removed_residual',
    'head_office_bankruptcy_opened_timed',
    'manager_individual_signing_corrected_notice',
    'head_office_other_address_deleted',
]

@pytest.mark.parametrize('digest,action', list(zip(SUPPLIED_SHA256, EXPECTED_ACTIONS)))
def test_explicit_meaning(digest, action):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser390_leftovers(*args, **kwargs)
    assert not rest and events[0].payload['action'] == action
    assert events[0].rule_id == args[1] + '.text.' + action + '.v1'
    payload = events[0].payload
    if digest.startswith('0dbf'):
        assert events[0].role == 'membre de la direction'
        assert events[0].signing == 'Kollektivunterschrift zu zweien'
        assert payload['procuration_revoked'] is True
    if digest.startswith('172d'):
        assert payload['waiver_repealed'] is True
    if digest.startswith('1f98'):
        assert (payload['count'], payload['buyer_count'], payload['remaining1'], payload['remaining23']) == ('10', '30', '58', '56')
    if digest.startswith(('3e8f', 'bb30')):
        assert events[0].event_type == 'capital_changed'
    if digest.startswith('483b'):
        assert payload['uid'] == 'CHE-470.549.227'
    if digest.startswith('4875'):
        assert events[0].event_type == 'status_changed' and payload['months'] == '6'
    if digest.startswith('8070'):
        assert payload['remaining'] == '9' and payload['count'] == '11'
        assert [e.role for e in events[1:]] == ['associé-gérant et président', 'associé-gérant']
        assert all(e.signing is None for e in events[1:])
    if digest.startswith('be61'):
        assert events[0].event_type == 'status_changed'
        assert payload['scope'] == 'head_office' and payload['time'] == '09.00'
    if digest.startswith('da0c'):
        assert events[0].signing == 'Einzelunterschrift'
        assert payload['previous_signing'] == 'Kollektivunterschrift zu zweien'
    if digest.startswith('ea7a'):
        assert payload['scope'] == 'head_office' and payload['postal_code'] == '6922'
