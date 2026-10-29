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
from shab_analyzer.parser386 import extract_parser386_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = ['0f56541799e91125dc466f8e31d6c69fbc9976009d7cba1f0d99825a37baf228', '53c59b45d91f965dc0236fc50560b480ef94d846b766c92e6270e457be8ef5f0', '62fa9996ae2c03a2ad43e1719129444c59df0ee521e6e0dde23d9494badf20c9', '6a93e5bc0b1f950c1d4507b19780383e9e83b32e29347e7668ce4f330cd71295', '7f7934b89658f041f480251f17dc08c06cd83fbe71da0739a5cf9cd3c5851376', '964fedef327c54546d21019dc6cefbd8e353f876a0f1536121f0ef8565ee60ab', 'a184b91f6fcda80c52e998c39f25537594931b4280a8feb2064466f4ba8cb398', 'bdeb4a55a9d8d704c5296a5ab1314dfd2b751bb180eaacee529871da697c65a2', 'c2973e0014fe14b2405c1e45a58c7b9e6dd797cce9c1ffe767ae385c093020ef', 'c61482e9cbb29b9c97c525df2ebe1a921c931f689833023183850c634ba9cc67', 'ca02775732524c3d7a9f59f3dac9b6f951dfa0226d51b68ba5baa8c37387d705', 'e0282eba4f3fb375f6fe99397fb180722cae4b8412c614dc62db18bf0160efea']
CONTEXT_REQUIRED = {"53c59b45", "7f7934b8"}
COUNTS = {"53c59b45": 4, "6a93e5bc": 3}

@lru_cache(None)
def captured(digest):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser386_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser386_leftovers', capture):
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
    added, rest = extract_parser386_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 433
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS.get(digest[:8], 1) and not rest
    with patch.object(parser, 'extract_parser386_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_unknown_suffix_and_language_preserve_input(digest):
    _, (args, kwargs) = captured(digest)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser386_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser386_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_missing_optional_source_and_invalid_dates(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser386_leftovers(*args)
    if digest[:8] in CONTEXT_REQUIRED:
        assert not events and rest == args[0]
    else:
        assert len(events) == COUNTS.get(digest[:8], 1) and not rest
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser386_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_old_event_without_new_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event


EXPECTED = [
    ('organization_changed', 'combination_merger_two_transferors', {'count': "5'000", 'nominal': '500.00'}),
    ('officer_changed', 'four_associate_manager_liquidators', {}),
    ('organization_changed', 'conditional_capital_expired_clause_replaced', {'introduced_date': '20.05.2015', 'decision_date': '18.12.2020'}),
    ('organization_changed', 'share_split_transfer_new_associate', {'count': '200', 'transferred': '100', 'nominal': '100'}),
    ('publication_corrected', 'statutes_date_deleted_correction', {'statutes_date': '04.05.2020', 'previous_date': '25.04.2020'}),
    ('status_changed', 'reinstatement_liquidation_article164', {'deletion_date': '24.07.2019', 'decision_date': '21.12.2020'}),
    ('organization_changed', 'asset_transfer_assets_only_cash', {'assets': "234'490'000.00", 'consideration': "234'490'000.00"}),
    ('publication_corrected', 'administrator_female_name_corrected_notice', {'entry': '19370', 'notice_ref': '0/1005031638'}),
    ('status_changed', 'bankruptcy_suspended_single_judge_order', {'decision_date': '26.11.2020'}),
    ('status_changed', 'branch_head_office_dissolved_name_uid', {'head_office_uid': 'CHE-100.742.237', 'dissolved_at_head_office': True}),
    ('officer_changed', 'officer_plural_header_individual_signing', {'previous_signing': 'Kollektivunterschrift zu zweien'}),
    ('status_changed', 'bankruptcy_opened_presidency_dot_time', {'time': '08.15', 'effective_date': '16.12.2020'}),
]

@pytest.mark.parametrize('digest,expected', list(zip(SUPPLIED_SHA256, EXPECTED)))
def test_explicit_meaning(digest, expected):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser386_leftovers(*args, **kwargs)
    kind, action, values = expected
    assert not rest
    assert events[0].event_type == kind
    assert events[0].rule_id == args[1] + '.text.' + action + '.v1'
    for key, value in values.items():
        assert events[0].payload[key] == value
    if digest.startswith('53c5'):
        assert all(e.role == 'associé-gérant liquidateur' and e.signing == 'Kollektivunterschrift zu zweien' and e.person_key for e in events)
    if digest.startswith('6a93'):
        assert [e.role for e in events[1:]] == ['gérant président', 'gérante']
        assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in events[1:])
    if digest.startswith('ca02'):
        assert events[0].signing == 'Einzelunterschrift' and events[0].role is None

@pytest.mark.parametrize('index', [1, 4])
def test_unrelated_optional_source(index):
    _, (args, _) = captured(SUPPLIED_SHA256[index])
    assert extract_parser386_leftovers(*args, source_text='Unrelated.') == ([], args[0])

@pytest.mark.parametrize('index,old,new', [(3, '200 parts sociales', '201 parts sociales'), (11, '08.15', '25.15')])
def test_invalid_values(index, old, new):
    _, (args, kwargs) = captured(SUPPLIED_SHA256[index])
    text = args[0].replace(old, new)
    assert text != args[0]
    assert extract_parser386_leftovers(text, *args[1:], **kwargs) == ([], text)

@pytest.mark.parametrize('version', [282, 344, 348, 385])
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
        assert extract_parser386_leftovers(*args, **kwargs) == ([], args[0])


@pytest.mark.parametrize('module_name,pattern_name,text,language', [
    ('parser107', '_DE_CONDITIONAL_CAPITAL_CLAUSE_REPEALED_EXPIRED_RIGHTS', 'Aufhebung der Statutenbestimmung über die mit Gewährungsbeschluss vom 20.05.2015 eingeführte bedingte Kapitalerhöhung infolge Erlöschens der Wandelrechte.', 'de'),
    ('parser137', '_FR_SOCIAL_SHARE_SPLIT_FOR_MANAGER', "Division de la part sociale de CHF 20000 de l'associé-gérant Exemple Anne en 200 parts de CHF 100.", 'fr'),
    ('parser120', '_FR_DIRECTOR_NAME_CORRECTED', "Rectificatif: l'inscription n° 123 du 20.11.2020 (FOSC du 25.11.2020, p. 0/123) est rectifiée en ce sens que le nom exact de la directrice est Exemple Anne (et non Exemple Anna comme publié).", 'fr'),
])
def test_existing_patterns_are_reused_for_ownership(module_name, pattern_name, text, language):
    import importlib
    module = importlib.import_module('shab_analyzer.' + module_name)
    assert getattr(module, pattern_name).fullmatch(text)
    assert getattr(module, 'extract_' + module_name + '_leftovers')(text, language, 'p', '', None, None, None)[0]
    assert extract_parser386_leftovers(text, language, 'p', '', None, None, None) == ([], text)
