import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser454 import extract_parser454_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '31bc228c95a083db1a4f10db79c75cd34ab0f92b45004c2eb04de53cc4a8079d', '384c2df3999d3936131f04916e6a38ac876aa6594f1c11fa88657884af3e1b8d', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8bb4f070db8be493d9d8774f0782f67efdbe36f44d408ddc67ebbdfbfb37152a', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a341287297ba96e1938916b070b26a6384cd05b7aad34facefaf830c80dd6cf8', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
COUNTS = [0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0]
NEW_CASES = [i for i, count in enumerate(COUNTS) if count]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser454_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser454_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert PARSER_VERSION == 490
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
    assert extract(*args) == ([], args[0])


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
        if not name.startswith('extract_parser') or name == 'extract_parser454_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name


@pytest.mark.parametrize('index', [i for i, count in enumerate(COUNTS) if not count])
def test_existing_results_unchanged(index):
    result, old, (args, kwargs) = captured(index)
    assert extract(*args, **kwargs) == ([], args[0])
    assert result == old


def test_exact_pair_payload_and_signing():
    _, _, (args, kwargs) = captured(3)
    events, rest = extract(*args, **kwargs)
    assert rest == ''
    assert [e.payload for e in events] == [
        {'name': 'Mohamed Saleem Sadrudin', 'place': 'Burnaby', 'origin': 'Canada',
         'country': 'CAN', 'action': 'appointed', 'signing_authority': None},
        {'name': "O'Connor Smith", 'place': 'Chessington', 'origin': 'Grande-Bretagne',
         'country': 'GBR', 'action': 'appointed', 'signing_authority': None},
    ]
    assert all(e.role == 'administrateur' and e.event_type == 'officer_changed' for e in events)
    assert [e.signing for e in events] == ['Einzelunterschrift', 'Kollektivunterschrift zu zweien']


def test_legacy_foreign_pair_remains_owned_by_parser235():
    from shab_analyzer.parser235 import _FR_TWO_FOREIGN_BOARD_MEMBERS, extract_parser235_leftovers
    _, _, (args, kwargs) = captured(3)
    text = args[0].replace('CAN, et', 'CAN, président et')
    assert _FR_TWO_FOREIGN_BOARD_MEMBERS.fullmatch(text)
    assert extract(text, *args[1:], **kwargs) == ([], text)
    events, rest = extract_parser235_leftovers(text, *args[1:])
    assert rest == '' and len(events) == 2
    assert all(e.rule_id == 'fr.persons.two_foreign_board_members.v1' for e in events)
    assert events[0].role == 'administrateur et président'
    assert all(e.signing is None for e in events)

def test_complete_source_is_deferred_to_historical_signing_rule():
    from shab_analyzer.parser55 import extract_parser55_leftovers
    from shab_analyzer.parser454 import _FR_TWO_FOREIGN_MEMBERS_COLLECTIVE_SOURCE
    _, _, (args, kwargs) = captured(3)
    source = args[0].replace('GBR, sont', 'GBR, avec signature collective à deux, sont')
    assert extract(source, *args[1:], **kwargs) == ([], source)
    legacy, rest = extract_parser55_leftovers(source, *args[1:])
    assert len(legacy) == 1
    assert legacy[0].rule_id == 'fr.persons.group_signing.v1'
    assert legacy[0].payload == {'scope': 'previously_named_officers',
                                 'signing': 'Kollektivunterschrift zu zweien'}
    assert rest == args[0]

def test_previous_pipeline_events_are_preserved():
    import shab_analyzer.parse as parser
    from unittest.mock import Mock
    result, _, _ = captured(3)
    with patch.object(parser, '_FR_TWO_FOREIGN_MEMBERS_COLLECTIVE_LATE', Mock(fullmatch=lambda _: None)), \
         patch.object(parser, 'extract_parser454_leftovers', lambda text, *a, **kw: ([], text)):
        previous = parse_publication_xml(FIXTURES / (SUPPLIED_SHA256[3] + '.xml'))
    assert result.events[:len(previous.events)] == previous.events
    assert len(result.events) == len(previous.events) + 3
    assert result.events[-3].rule_id == 'fr.persons.group_signing.v1'
    assert previous.leftover_text


def test_source_signatures_must_match_the_evidenced_variant():
    _, _, (args, kwargs) = captured(3)
    changed = kwargs['source_text'].replace('avec signature individuelle, et',
                                           'sans signature, et')
    assert extract(*args, source_text=changed) == ([], args[0])
