import ast
import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser388 import extract_parser388_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = ['0008d9420652f027cee92d185714c82902a43005026198a55fbe7ad574ffbfe4', '081707cf1cab2488e3ed2064b451ae920fa007d1da732c1812993367e4ef8e54', '34df0e20acc8aef9e307d8e0f2fb313e7521699020114f25b6aa4f19b512dcd2', '52147dfaa243975e4ccecde62e7acfff3f79ffad547fce3e40348806307497c9', '6cde624189932ee4422914624f00fdba926a3e86f6504cc4ce9be9c894c3c3a4', '74987ce227639f00231a9cefcc7b1e3d1ed9c3bd49a2cb0cf2e3ad4ca01f80f1', 'c68efb042e4914b65bc9f482e9bceb0674a99ee14fead9e2a8bc6b91098f487d', 'cf2a34c87fa72dbb4194de899d53c0bf797cf817f967e9b63dafd78bfec9631a', 'da14c567c164fa92f538120b54ae9ab49c2dbc8237ac29cf90e3ac4be3c6eeae', 'dad8e35c9fef2f5d4125cfef9e92521bff6250dbf818dc4bc5166e1953e46052', 'ebfc9296ba9351e07d2193ff586f7319277e325188e4748ee30d9c285162efdb', 'fdddc18262c982cd9191258ed4988a48064b1deea0bc5d3c3458601da4e2d6a3']
CONTEXT_REQUIRED = set()
COUNTS = {'081707cf': 3, '6cde6241': 4, 'cf2a34c8': 2, 'da14c567': 3, 'ebfc9296': 3}

@lru_cache(None)
def captured(digest):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser388_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser388_leftovers', capture):
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
    added, rest = extract_parser388_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 400
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS.get(digest[:8], 1) and not rest
    with patch.object(parser, 'extract_parser388_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_unknown_suffix_and_language_preserve_input(digest):
    _, (args, kwargs) = captured(digest)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser388_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser388_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_missing_optional_source_and_invalid_dates(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser388_leftovers(*args)
    if digest[:8] in CONTEXT_REQUIRED:
        assert not events and rest == args[0]
    else:
        assert len(events) == COUNTS.get(digest[:8], 1) and not rest
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser388_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_old_event_without_new_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event


@pytest.mark.parametrize('version', [265, 324, 347, 374, 387])
def test_legacy_rule_inputs_remain_owned_in_isolation(version):
    import importlib
    import shab_analyzer.parse as parser
    old = getattr(importlib.import_module(f'shab_analyzer.parser{version}'), f'extract_parser{version}_leftovers')
    calls = []
    def capture(*args, **kwargs):
        events, rest = old(*args, **kwargs)
        if events:
            calls.append((args, kwargs))
        return events, rest
    # Reuse the old rule's fixture corpus, without executing any operational code.
    test_source = (Path(__file__).parent / f'test_parser{version}.py').read_text()
    assignments = {
        node.targets[0].id: ast.literal_eval(node.value)
        for node in ast.parse(test_source).body
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id in {'CASES', 'SUPPLIED_SHA256'}
    }
    prefixes = [case[0] for case in assignments['CASES']] if 'CASES' in assignments else assignments['SUPPLIED_SHA256']
    paths = sorted({path for prefix in prefixes for path in FIXTURES.glob(prefix + '*.xml')})
    assert paths
    with patch.object(parser, f'extract_parser{version}_leftovers', capture):
        for path in paths:
            parse_publication_xml(path)
    assert calls
    for args, kwargs in calls:
        assert extract_parser388_leftovers(*args, **kwargs) == ([], args[0])




EXPECTED = [
    ('organization_changed', 'auditor_name_and_seat_changed', {'uid': 'CHE-109.316.964'}),
    ('organization_changed', 'share_transfer_proxy_revoked_manager_elected', {'before': '18', 'count': '1', 'remaining': '17', 'buyer_count': '2'}),
    ('publication_corrected', 'collective_signing_exclusions_corrected', {'entry': '19257'}),
    ('officer_removed', 'auditor_removed_legacy_registry_id', {'registry_id': 'CH-035-9019917-2'}),
    ('officer_removed', 'committee_unsigned_member_removed', {}),
    ('organization_changed', 'foundation_transfer_cash_and_investment_claims', {'cash': "8'000'000.00", 'claims': "339'690.973", 'claim_value': '111.0555', 'dilution_protection': "75'449.10"}),
    ('officer_changed', 'person_name_and_residence_changed', {}),
    ('officer_changed', 'administrator_president_individual_signing', {}),
    ('organization_changed', 'share_transfer_foreign_residences', {'remaining': '180', 'count': '20', 'country': 'FRA'}),
    ('organization_changed', 'branch_uid_registration_practice_adjustment', {'previous_registry_id': 'CH-320.9.074.096-4'}),
    ('status_changed', 'foundation_dissolved_supervisory_authority', {'decision_date': '05.10.2020'}),
    ('publication_corrected', 'council_president_person_corrected', {'country': 'MC'}),
]

@pytest.mark.parametrize('digest,expected', list(zip(SUPPLIED_SHA256, EXPECTED)))
def test_explicit_meaning(digest, expected):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser388_leftovers(*args, **kwargs)
    kind, action, values = expected
    assert not rest and events[0].event_type == kind
    assert events[0].rule_id == args[1] + '.text.' + action + '.v1'
    assert all(events[0].payload[key] == value for key, value in values.items())
    if digest.startswith('0817'):
        assert events[1].event_type == 'officer_removed'
        assert events[2].role == 'gérant' and events[2].signing is None
    if digest.startswith('6cde'):
        assert all(e.signing == 'ohne Zeichnungsberechtigung' for e in events)
    if digest.startswith('cf2a'):
        assert [e.role for e in events] == ['président', 'directeur']
        assert all(e.signing == 'Einzelunterschrift' for e in events)
    if digest.startswith('ebfc'):
        assert all(e.payload['liquidator'] and e.signing == 'Einzelunterschrift' for e in events[1:])


@pytest.mark.parametrize('module_name,pattern_name,text,language', [
    ('parser191', '_FR_FOUNDATION_DISSOLVED_TWO_LIQUIDATORS', 'La fondation est dissoute par décision de son autorité de surveillance du 01.01.2020. Liquidateurs: Exemple Jean, président, et Exemple Anne, vice-présidente, membres du conseil de fondation, lesquels continuent de signer collectivement à deux', 'fr'),
    ('parser121', '_FR_AUDITOR_RENAMED', "L'organe de révision Ancien SA (CHE-123.456.789) a modifié sa raison sociale en Nouveau SA (CHE-123.456.789)", 'fr'),
    ('parser253', '_IT_CORRECT_PERSON_WITHOUT_SHARES', 'Nome corretto: Esempio, Mario, da Lugano, in Lugano, presidente, con firma individuale', 'it'),
])
def test_existing_patterns_are_reused(module_name, pattern_name, text, language):
    import importlib
    from shab_analyzer.parser388 import _LEGACY
    module = importlib.import_module('shab_analyzer.' + module_name)
    pattern = getattr(module, pattern_name)
    assert pattern in _LEGACY and pattern.fullmatch(text)
    assert getattr(module, 'extract_' + module_name + '_leftovers')(text, language, 'p', '', None, None, None)[0]
    assert extract_parser388_leftovers(text, language, 'p', '', None, None, None) == ([], text)


def test_inconsistent_share_counts_preserve_input():
    _, (args, kwargs) = captured(SUPPLIED_SHA256[1])
    changed = args[0].replace('17 parts', '18 parts')
    assert changed != args[0]
    assert extract_parser388_leftovers(changed, *args[1:], **kwargs) == ([], changed)
