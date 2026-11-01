import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser450 import extract_parser450_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '29cc8734d4ae166763bc2457d4070f133ef1e125d5350107ddb16cc5a6110e6e', '2f2bb4070bd41652570a458c57335017ab31fd75dc60fb65cf1a4f787a5fad60', '34f63ee25c543752c2bfe72f4e5599af78c2afe96dec8ba36a840e8dbac355a8', '384c2df3999d3936131f04916e6a38ac876aa6594f1c11fa88657884af3e1b8d', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a341287297ba96e1938916b070b26a6384cd05b7aad34facefaf830c80dd6cf8', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
COUNTS = [0, 0, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0]
NEW_CASES = [i for i, count in enumerate(COUNTS) if count]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser450_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser450_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert PARSER_VERSION == 454
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
        if not name.startswith('extract_parser') or name == 'extract_parser450_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name


@pytest.mark.parametrize('index', [0, 1, 5, 6, 7, 8, 9, 10, 11])
def test_existing_results_unchanged(index):
    result, old, (args, kwargs) = captured(index)
    assert extract(*args, **kwargs) == ([], args[0])
    assert result == old



@pytest.mark.parametrize('index', NEW_CASES)
def test_evidenced_semantics(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    assert rest == ''
    if index == 2:
        assert [e.event_type for e in events] == ['status_changed', 'officer_changed']
        assert events[0].payload.items() >= {
            'kind': 'composition_moratorium_granted', 'action': 'granted',
            'moratorium_type': 'provisional', 'decision_date': '2021-03-29',
            'until_date': '2021-05-28', 'authority': 'Kantonsgericht Nidwalden',
            'commissioner_uid': 'CHE-106.826.571',
            'leader1': 'Alain Bachmann', 'leader2': 'RA Jürg Hadorn',
        }.items()
        assert events[1].role == 'provisorische Sachwalterin'
        assert events[1].payload['action'] == 'appointed'
        assert events[1].payload['place'] == 'Luzern'
        assert events[1].signing is None
    elif index == 3:
        assert events[0].event_type == 'ownership_changed'
        assert events[0].payload == {
            'seller': 'Pahud Jean-Yves', 'buyer': 'Vuissoz Eric', 'count': '1',
            'before': '20', 'remaining': '19', 'nominal': "1'000",
            'action': 'partial_transfer', 'currency': 'CHF',
        }
    else:
        assert events[0].event_type == 'publication_corrected'
        assert events[0].payload == {
            'authority': 'Tribunal de première instance', 'decision_date': '2021-02-10',
            'cancelled_entry': '5523', 'cancelled_entry_date': '2020-03-17',
            'confirmed_entry': '6802', 'confirmed_entry_date': '2020-04-22',
            'kind': 'registration_cancelled', 'action': 'registration_cancelled_and_confirmed',
        }


def test_inconsistent_share_count_preserves_input():
    _, _, (args, kwargs) = captured(3)
    text = args[0].replace('19 parts', '18 parts')
    assert extract(text, *args[1:], **kwargs) == ([], text)


def test_existing_manager_plural_variant_keeps_ownership():
    from shab_analyzer.parser387 import extract_parser387_leftovers
    from shab_analyzer.parser238 import _FR_SIMPLE_ASSOCIATE_SHARE_TRANSFER, extract_parser238_leftovers
    _, _, (args, kwargs) = captured(3)
    text = args[0].replace('nouvel associé, avec 1 part', 'nouvel associé avec 1 parts')
    assert extract(text, *args[1:], **kwargs) == ([], text)
    events, rest = extract_parser387_leftovers(text, *args[1:], **kwargs)
    assert len(events) == 1 and rest == ''
    assert events[0].rule_id == 'fr.text.share_transfer_to_existing_manager_remaining.v1'
    text = text.replace('. Pahud', '; Pahud')
    assert _FR_SIMPLE_ASSOCIATE_SHARE_TRANSFER.fullmatch(text)
    assert extract(text, *args[1:], **kwargs) == ([], text)
    events, rest = extract_parser238_leftovers(text, *args[1:])
    assert len(events) > 0 and rest == ''


def test_definitive_moratorium_history_remains_owned():
    from shab_analyzer.parser191 import (
        _DE_DEFINITIVE_MORATORIUM_WITH_COMMISSIONER_HISTORY,
        extract_parser191_leftovers,
    )
    _, _, (args, kwargs) = captured(2)
    previous = args[0].replace('provisorische Sachwalterin', 'provisiorische Sachwalterin')
    current = args[0].replace(
        'die provisorische Nachlassstundung bis zum 28.05.2021',
        'eine definitive Nachlassstundung von sechs Monaten',
    ).replace('provisorische Sachwalterin', 'Sachwalterin')
    text = current + '. [bisher: ' + previous + '.]'
    assert _DE_DEFINITIVE_MORATORIUM_WITH_COMMISSIONER_HISTORY.fullmatch(text)
    assert extract(text, *args[1:], **kwargs) == ([], text)
    events, rest = extract_parser191_leftovers(text, *args[1:])
    assert events and rest == ''
    assert events[0].rule_id == 'de.text.definitive_moratorium_with_commissioner_history.v1'
