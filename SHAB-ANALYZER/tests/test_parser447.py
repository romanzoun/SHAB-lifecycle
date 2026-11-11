import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser447 import extract_parser447_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '05cb3fd8db0940d0763c3d080d2740126c10d4caa68e7723b5bdf1cc10c584b1', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '384c2df3999d3936131f04916e6a38ac876aa6594f1c11fa88657884af3e1b8d', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a341287297ba96e1938916b070b26a6384cd05b7aad34facefaf830c80dd6cf8', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'adc3f8645900cbacefc195071c7d8d97ae1e40690dbec670445c5488fa6f0b92', 'e42a35d6f3a59f799d41a23ae74b5f63a84562185ef4a73dc30f767c410df4b1', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
COUNTS = [0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0]
NEW_CASES = [i for i, count in enumerate(COUNTS) if count]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser447_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser447_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert PARSER_VERSION == 528
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
        if not name.startswith('extract_parser') or name == 'extract_parser447_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name


@pytest.mark.parametrize('index', [0, 2, 3, 4, 5, 6, 7, 8, 11])
def test_existing_results_unchanged(index):
    result, old, (args, kwargs) = captured(index)
    assert extract(*args, **kwargs) == ([], args[0])
    assert result == old


@pytest.mark.parametrize('index,event_type,expected', [
    (1, 'officer_changed', {'action': 'appointed', 'place': "L'Isle"}),
    (9, 'officer_changed', {'action': 'appointment_extended', 'duration_months': 3, 'until_date': '2021-06-30', 'decision_date': '2021-03-29', 'previous_date': '2020-09-30'}),
    (10, 'publication_corrected', {'scope': 'officer_nationality', 'action': 'corrected', 'to': 'britischer Staatsangehöriger', 'from': 'Grossbritannischerstaatsangeöriger'}),
])
def test_evidenced_semantics(index, event_type, expected):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    assert rest == '' and events[0].event_type == event_type
    assert events[0].payload.items() >= expected.items()
    if index == 1:
        assert events[0].role == 'administrateur' and events[0].signing is None
    if index == 9:
        assert events[0].role == 'Sachwalter' and events[0].signing == 'Einzelunterschrift'


@pytest.mark.parametrize('role, module, pattern', [
    ('gérant', 'parser106', '_FR_MANAGER_APPOINTED_WITH_DOMICILE'),
    ('liquidateur', 'parser93', '_FR_LIQUIDATOR_APPOINTED_AFTER_MOVE'),
])
def test_legacy_appointments_deferred_even_in_isolation(role, module, pattern):
    import importlib
    legacy = importlib.import_module('shab_analyzer.' + module)
    _, _, (args, kwargs) = captured(1)
    text = args[0].replace('administrateur', role)
    assert getattr(legacy, pattern).fullmatch(text)
    assert extract(text, *args[1:], **kwargs) == ([], text)
    events, rest = getattr(legacy, 'extract_' + module + '_leftovers')(text, *args[1:])
    assert len(events) == 1 and rest == ''
    assert events[0].role == role

def test_legacy_nationality_correction_deferred():
    from shab_analyzer.parser222 import _DE_NATIONALITY_CORRECTED, extract_parser222_leftovers
    text = 'Im SHAB Nr. 12 vom 29.03.2021 publizierten TR-Eintrag 2337 wurde irrtümlich [bisher: britisch] publiziert. Korrekt ist [bisher: schweizerisch]'
    args = ('de', 'p', '', None, None, None)
    assert _DE_NATIONALITY_CORRECTED.fullmatch(text)
    assert extract(text, *args) == ([], text)
    events, rest = extract_parser222_leftovers(text, *args)
    assert rest == '' and len(events) == 1
    assert events[0].payload['from'] == 'britisch'
    assert events[0].payload['to'] == 'schweizerisch'


def test_extension_rejects_changed_previous_signing():
    _, _, (args, kwargs) = captured(9)
    text = args[0].replace('als Sachwalter mit Einzelunterschrift eingesetzt', 'als Sachwalter ohne Zeichnungsberechtigung eingesetzt')
    assert extract(text, *args[1:], **kwargs) == ([], text)
