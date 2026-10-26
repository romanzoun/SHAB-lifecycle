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
from shab_analyzer.parser387 import extract_parser387_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = ['4eb7c6d917e568a63da760088c6f0a6f4444aed868e561083fa3feffb6868aa2', '5754e5154f7e78e45bd8ac97a94b32e217dbd4ef54adfda961470d5a99fe0cc6', '6c20fb1305cdf18e8c60ef0f520d9ee4be75385352945ae4d5a982a835860269', '77993182cb76c89368d67dc56d9cae1df36afeef347c968f83142db4a92a9a16', '7cea67702caf9cfd254a06bb7116f588c4f78042d1dfeb13aa74ef59e3ce2228', 'a7e98d731f88d4cb14d7cad138046770cfdead45afc35e042dc90b1bc9e7fb46', 'b9893cc1043954b371345d098aeeead472588481155f98e38909fe6800472559', 'bc87881e89559e9617db736de4f6da1a14f131c27d1259fcf08340607ba2d503', 'cc03f715a1d4fd4007cc54cd72bcc62ff8ab7ea2b09abc1e9b5f2a0743645e73', 'cc924b0033af123c8ffbf0860b0809e50bbf1192f8b283d3b46ec40d0772fd51', 'd819add364d5c2a9198972f871d9d058aba08fc162f684d3ca18c4a03601224c', 'f65eb45ccde99f67f2b083291a663ba380d94f556be5f83d6b597e2d3fc16ec7']
CONTEXT_REQUIRED = {"4eb7c6d9", "f65eb45c"}
COUNTS = {"b9893cc1": 2, "cc924b00": 3}

@lru_cache(None)
def captured(digest):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser387_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser387_leftovers', capture):
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
    added, rest = extract_parser387_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 400
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS.get(digest[:8], 1) and not rest
    with patch.object(parser, 'extract_parser387_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_unknown_suffix_and_language_preserve_input(digest):
    _, (args, kwargs) = captured(digest)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser387_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser387_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_missing_optional_source_and_invalid_dates(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser387_leftovers(*args)
    if digest[:8] in CONTEXT_REQUIRED:
        assert not events and rest == args[0]
    else:
        assert len(events) == COUNTS.get(digest[:8], 1) and not rest
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser387_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_old_event_without_new_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event


EXPECTED = [
    ('organization_changed', 'association_transfer_two_contract_dates', {'liabilities': "189'317.07", 'recipient_uid': 'CHE-102.470.653'}),
    ('organization_changed', 'head_office_share_capital_paid_up', {'capital': "2'000'000.--", 'previous_paid_up': "1'000'000.--"}),
    ('organization_changed', 'successive_manager_corporate_share_transfers', {'first_count': '2', 'second_count': '6', 'seller_remaining': '12', 'manager_remaining': '2'}),
    ('organization_changed', 'merger_missing_open_parenthesis_split_decimal', {'net_integer': "214'850", 'net_cents': '30', 'transferor_uid': 'CHE-100.374.004'}),
    ('organization_changed', 'foundation_assets_only_cash_transfer', {'assets': "96'969'487.00", 'consideration': "96'969'487.00"}),
    ('organization_changed', 'authorized_conditional_capital_clauses_expired', {}),
    ('officer_changed', 'committee_secretary_collective_signing', {}),
    ('officer_changed', 'collective_signing_four_exclusions_typo', {'signing_exclusions': ['Imhof Daniel', 'Brunner Tobias', 'Heerah Ashwina', 'Okula Konrad']}),
    ('status_changed', 'bankruptcy_reopened_cantonal_appeal_rejected', {'court_canton': 'St. Gallen', 'time': '18.00'}),
    ('organization_changed', 'president_share_transfer_foreign_manager', {'remaining': '10', 'count': '10', 'country': 'FRA'}),
    ('organization_changed', 'share_transfer_to_existing_manager_remaining', {'previous_count': '20', 'count': '2', 'remaining': '18'}),
    ('publication_corrected', 'dissolution_decision_date_corrected_fragment', {'decision_date': '19.11.2020', 'previous_decision_date': '29.11.2020'}),
]

@pytest.mark.parametrize('digest,expected', list(zip(SUPPLIED_SHA256, EXPECTED)))
def test_explicit_meaning(digest, expected):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser387_leftovers(*args, **kwargs)
    kind, action, values = expected
    assert not rest
    assert events[0].event_type == kind
    assert events[0].rule_id == args[1] + '.text.' + action + '.v1'
    assert all(events[0].payload[key] == value for key, value in values.items())
    if digest.startswith('b989'):
        assert [e.role for e in events] == ['membre du bureau et secrétaire', 'membre du comité']
        assert [e.signing for e in events] == ['Kollektivunterschrift zu zweien', 'ohne Zeichnungsberechtigung']
    if digest.startswith('cc924'):
        assert [e.role for e in events[1:]] == ['président', 'associé-gérant']
        assert all(e.signing is None for e in events[1:])

@pytest.mark.parametrize('index', [0, 11])
def test_unrelated_source_preserves_fragment(index):
    _, (args, _) = captured(SUPPLIED_SHA256[index])
    assert extract_parser387_leftovers(*args, source_text='Unrelated.') == ([], args[0])

@pytest.mark.parametrize('index,old,new', [(3, "214'850, 30", "214'850, 31"), (8, '18.00', '25.00'), (10, '18 parts', '19 parts')])
def test_inconsistent_amounts_counts_and_time(index, old, new):
    _, (args, kwargs) = captured(SUPPLIED_SHA256[index])
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser387_leftovers(changed, *args[1:], **kwargs) == ([], changed)
@pytest.mark.parametrize('version', [265, 293, 331, 342, 344, 373, 384, 385, 386])
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
        assert extract_parser387_leftovers(*args, **kwargs) == ([], args[0])



@pytest.mark.parametrize('module_name,pattern_name,text,language', [
    ('parser248', '_DE_HEAD_OFFICE_SHARE_CAPITAL_AND_PAID_CHANGED', 'Kapital Hauptsitz neu: CHF 2000; Liberierung: CHF 2000 [bisher: Kapital Hauptsitz: Aktienkapital: CHF 1000. Liberierung: CHF 1000]', 'de'),
    ('parser181', '_DE_FOUNDATION_ASSET_TRANSFER_WITH_APPROVAL', 'Vermögensübertragung: Die Stiftung überträgt gemäss Vertrag vom 01.01.2020 und Verfügung der Aufsichtsbehörde vom 02.01.2020 Aktiven von CHF 200 und Fremdkapital von CHF 100 auf die Beispielstiftung (CHE-123.456.789), in Bern. Gegenleistung: keine.', 'de'),
])
def test_existing_patterns_are_reused(module_name, pattern_name, text, language):
    import importlib
    from shab_analyzer.parser387 import _LEGACY
    module = importlib.import_module('shab_analyzer.' + module_name)
    pattern = getattr(module, pattern_name)
    assert pattern in _LEGACY and pattern.fullmatch(text)
    assert getattr(module, 'extract_' + module_name + '_leftovers')(text, language, 'p', '', None, None, None)[0]
    assert extract_parser387_leftovers(text, language, 'p', '', None, None, None) == ([], text)
