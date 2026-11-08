import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser449 import extract_parser449_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '11b3dfcb473f275f433a80f49df8efb0d57b6f849bd78be5f0586cef3c1d7328', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '384c2df3999d3936131f04916e6a38ac876aa6594f1c11fa88657884af3e1b8d', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '63a5d362a897040f331d006585840ee42c8d91331493c7ebb64375bd4e6e38f7', '860404c32a3e177b32cbaec25903816d86c50a8410af2b59157b5b83ccfd2fc7', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a341287297ba96e1938916b070b26a6384cd05b7aad34facefaf830c80dd6cf8', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
COUNTS = [0, 3, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0]
NEW_CASES = [i for i, count in enumerate(COUNTS) if count]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser449_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser449_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert PARSER_VERSION == 507
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
    baseline, _ = extract(*args, **kwargs)
    assert [e.payload for e in events] == [e.payload for e in baseline]
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
        if not name.startswith('extract_parser') or name == 'extract_parser449_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name


@pytest.mark.parametrize('index', [0, 2, 3, 4, 7, 8, 9, 10, 11])
def test_existing_results_unchanged(index):
    result, old, (args, kwargs) = captured(index)
    assert extract(*args, **kwargs) == ([], args[0])
    assert result == old



@pytest.mark.parametrize('index', NEW_CASES)
def test_evidenced_semantics(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    assert rest == ''
    if index == 1:
        assert [e.role for e in events] == ['président', 'secrétaire', 'trésorier']
        assert all(e.event_type == 'officer_changed' and e.signing is None and e.payload['action'] == 'appointed' for e in events)
    elif index == 5:
        assert events[0].event_type == 'audit_requirement_changed'
        assert events[0].payload == {'kind': 'limited_audit_waiver', 'action': 'declared', 'declaration_date': '2021-04-12', 'limited_audit_waived': True}
    else:
        assert events[0].event_type == 'officer_changed'
        assert events[0].payload['place'] == 'Cugy (VD)'
        assert events[0].payload.items() >= {'action': 'domicile_corrected', 'previous_place': 'Morges', 'entry_date': '2021-04-08', 'notice_date': '2021-04-13', 'notice_ref': '0/1005148289'}.items()
        assert events[0].role is None and events[0].signing is None


def test_legacy_audit_deferred_using_original_pattern():
    from shab_analyzer.parser224 import _FR_LIMITED_AUDIT_WAIVED, extract_parser224_leftovers
    _, _, (args, kwargs) = captured(5)
    text = args[0].replace('Seon', 'Selon')
    assert _FR_LIMITED_AUDIT_WAIVED.fullmatch(text)
    assert extract(text, *args[1:], **kwargs) == ([], text)
    events, rest = extract_parser224_leftovers(text, *args[1:])
    assert len(events) == 1 and rest == ''
    assert events[0].rule_id == 'fr.text.limited_audit_waived.v1'


def test_legacy_domicile_deferred_using_original_pattern():
    from shab_analyzer.parser142 import _FR_DOMICILE_CORRECTED_NOTICE_PARENTHETICAL, extract_parser142_leftovers
    from shab_analyzer.parser122 import _FR_ADMIN_DOMICILE_CORRECTION_NOTICE, extract_parser122_leftovers
    _, _, (args, kwargs) = captured(6)
    for text, pattern, old_extract in (
        (args[0].replace('Cugy (VD)', 'Cugy'), _FR_DOMICILE_CORRECTED_NOTICE_PARENTHETICAL, extract_parser142_leftovers),
        (args[0].replace('que Pasquali', "que l'administrateur Pasquali"), _FR_ADMIN_DOMICILE_CORRECTION_NOTICE, extract_parser122_leftovers),
    ):
        assert pattern.fullmatch(text)
        assert extract(text, *args[1:], **kwargs) == ([], text)
        events, rest = old_extract(text, *args[1:])
        assert len(events) == 1 and rest == ''
