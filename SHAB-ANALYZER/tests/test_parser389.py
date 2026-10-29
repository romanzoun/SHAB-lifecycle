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
from shab_analyzer.parser389 import extract_parser389_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = ['05bd5fafc64a970ca6eee3f70749d8eac384adec2c5042a8fd14e77080502040', '27012ef9e36a8b55c2917041b53e1b0161fe1851a2340f0e2a616eb7f41d17e2', '44188be85d938afa5c48c0224040ee60ec954da0e19eced84c805bfa667309e7', '5897f52c99d9f6f81f5ceeb40b5924a428d0ffa1f25e3ce752de24dd761391b6', '691966c66a14bc1532709f45ecb3b0f22a6b219ac6e8728fc120aa5be362a5f6', '7f9e6e9d8665e940b73c797925566b7bfac2f125b67b7b846ab24ac36d56fb21', 'a3e19a9555f1de0d6d76043079d562e431bb75dc91fa7c7e8d0894753877da3a', 'a9bdb53fca752099ebb73955da3e62dcf5625396982669de11965e74f372df3d', 'ddc815d7dde4c94929bfd81736373879855b1d5b63548fd4a7baacaf854e046b', 'eb8622175f8cc824d775d1f93ea34a49562859a11d1f8effe1ce658472b17b42', 'f38cb179cce49a55a9bcf91d2a9f2d75567fecd772f2a9fcf747d956c3ae8dd1', 'fb2f3a4274bb31f83a307f8707646b4c16bece9408c55f42009afe86a3ceb940']
CONTEXT_REQUIRED = {'05bd5faf', 'a9bdb53f'}
COUNTS = {'27012ef9': 2, '44188be8': 2, '691966c6': 4, 'a3e19a95': 2, 'eb862217': 3, 'f38cb179': 2}

@lru_cache(None)
def captured(digest):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser389_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser389_leftovers', capture):
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
    added, rest = extract_parser389_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 429
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS.get(digest[:8], 1) and not rest
    with patch.object(parser, 'extract_parser389_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_unknown_suffix_and_language_preserve_input(digest):
    _, (args, kwargs) = captured(digest)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser389_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser389_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_missing_optional_source_and_invalid_dates(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser389_leftovers(*args)
    if digest[:8] in CONTEXT_REQUIRED:
        assert not events and rest == args[0]
    else:
        assert len(events) == COUNTS.get(digest[:8], 1) and not rest
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser389_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_old_event_without_new_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event


@pytest.mark.parametrize('version', [355, 361, 374, 377, 380])
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
        assert extract_parser389_leftovers(*args, **kwargs) == ([], args[0])




EXPECTED_ACTIONS = [
    'foundation_member_gendered_signing_restriction',
    'administrator_liquidator_now_individual_signing',
    'two_proxies_shared_origin',
    'company_dissolved_abbreviated_translated_names',
    'registered_shares_liquidation_preference_and_board',
    'share_transfer_equal_remaining_holdings',
    'administrator_liquidator_last_powers_changed',
    'registered_shares_now_transfer_restricted',
    'capital_reduction_zero_simultaneous_restoration',
    'foundation_council_roles_continued_signing',
    'two_branch_limited_collective_signatories',
    'director_appointed_administrator_president',
]

@pytest.mark.parametrize('digest,action', list(zip(SUPPLIED_SHA256, EXPECTED_ACTIONS)))
def test_explicit_meaning(digest, action):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser389_leftovers(*args, **kwargs)
    assert not rest and events[0].payload['action'] == action
    assert events[0].rule_id == args[1] + '.text.' + action + '.v1'
    if digest.startswith('6919'):
        assert events[0].event_type == 'capital_changed'
        assert events[0].payload['preferred'] == '326'
        assert events[0].payload['ordinary'] == '674'
        assert [e.signing for e in events[1:]] == ['Einzelunterschrift', 'Kollektivunterschrift zu zweien', 'Kollektivunterschrift zu zweien']
    if digest.startswith('4418'):
        assert all(e.signing == 'Kollektivprokura zu zweien' for e in events)
    if digest.startswith('a3e1'):
        assert all(e.payload['liquidator'] for e in events)
        assert [e.payload['powers_changed'] for e in events] == [False, True]
    if digest.startswith('05bd'):
        assert events[0].payload['signing_restriction'] == 'avec le/la président(e) ou le/la vice-président(e)'
    if digest.startswith('f38c'):
        assert all(e.payload['signing_restriction'] == 'limitée à la succursale' for e in events)
    if digest.startswith('ddc8'):
        assert events[0].event_type == 'capital_changed' and events[0].payload['reduced'] == '0.00'

@pytest.mark.parametrize('digest', [SUPPLIED_SHA256[0], SUPPLIED_SHA256[7]])
def test_missing_source_evidence_preserves_input(digest):
    _, (args, kwargs) = captured(digest)
    assert extract_parser389_leftovers(*args, source_text='Unrelated source.') == ([], args[0])

@pytest.mark.parametrize('module_name,pattern_name,text,language', [
    ('parser152', '_FR_FOUNDATION_MEMBER_WITH_PRESIDENT_OR_VICE_PRESIDENT', 'Nouveau membre du conseil de fondation avec le/la président(e) ou le/la vice-président(e): Exemple Anne, de Lausanne, à Genève', 'fr'),
    ('parser199', '_DE_CAPITAL_REDUCTION_AND_RESTORATION', "Bei der Kapitalherabsetzung vom 01.01.2020 wird das Aktienkapital von CHF 200'000.00 durch Vernichtung von 200 Namenaktien zu CHF 1'000.00 um CHF 200'000.00 auf CHF 0.00 herabgesetzt. Gleichzeitig wird das Aktienkapital um CHF 200'000.00 auf CHF 200'000.00 durch Ausgabe von 200 Namenaktien zu CHF 1'000.00 ordentlich erhöht", 'de'),
])
def test_existing_patterns_are_reused(module_name, pattern_name, text, language):
    import importlib
    from shab_analyzer.parser389 import _LEGACY
    module = importlib.import_module('shab_analyzer.' + module_name)
    pattern = getattr(module, pattern_name)
    assert pattern in _LEGACY and pattern.fullmatch(text)
    assert getattr(module, 'extract_' + module_name + '_leftovers')(text, language, 'p', '', None, None, None)[0]
    assert extract_parser389_leftovers(text, language, 'p', '', None, None, None) == ([], text)
