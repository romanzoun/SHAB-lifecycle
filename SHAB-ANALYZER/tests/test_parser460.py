import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser460 import extract_parser460_leftovers as extract
from shab_analyzer.parser302 import extract_parser302_leftovers
from shab_analyzer.parser96 import extract_parser96_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = '''02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11
1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e
2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3
31bc228c95a083db1a4f10db79c75cd34ab0f92b45004c2eb04de53cc4a8079d
3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232
7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad
88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7
8bb4f070db8be493d9d8774f0782f67efdbe36f44d408ddc67ebbdfbfb37152a
8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f
a341287297ba96e1938916b070b26a6384cd05b7aad34facefaf830c80dd6cf8
a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5
f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed'''.split()


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser460_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser460_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(path)
    assert len(calls) == 1
    return result, old, calls[0]


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('index', range(12))
def test_pipeline_preserves_existing_events(index):
    result, old, (args, kwargs) = captured(index)
    added, rest = extract(*args, **kwargs)
    if index == 9:
        assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
        assert len(added) == 1 and rest == ''
        assert result.events == old.events + added
    else:
        assert (added, rest) == ([], args[0])
        assert result == old


def test_payload_and_missing_optional_attributes():
    assert PARSER_VERSION == 529
    _, _, (args, kwargs) = captured(9)
    events, rest = extract(*args, **kwargs)
    assert rest == ''
    assert len(events) == 1
    assert events[0].event_type == 'organization_changed'
    assert events[0].rule_id == 'fr.text.formerly_privileged_shares_consolidated.v1'
    assert events[0].payload == {
        'action': 'registered_shares_consolidated',
        'previous_count': "2'000", 'previous_nominal': '90',
        'new_count': "1'800", 'new_nominal': '100', 'capital': "492'600",
        'count': "4'926", 'nominal': '100', 'previous_voting_privileged': True,
    }
    optional, rest = extract(*args[:4], None, None, None, **kwargs)
    assert rest == ''
    for event, original in zip(optional, events):
        assert event.payload == original.payload
        assert event.org_uid is None and event.plz is None and event.canton is None
        assert Event(**vars(event)) == event
    legacy = Event('p', '', 'organization_changed', 'fr.text.registered_shares_consolidated.v1',
                   payload={'action': 'registered_shares_consolidated', 'previous_count': "2'000"})
    assert 'previous_voting_privileged' not in legacy.payload
    assert Event(**vars(legacy)) == legacy


def test_boundaries_and_unknown_input():
    _, _, (args, kwargs) = captured(9)
    for text in (args[0] + '; UNKNOWN', args[0].replace('90,', '91,'),
                 args[0].replace("4'926", "4'925"),
                 args[0].replace('entièrement libéré', 'partiellement libéré'),
                 args[0].replace("jusqu'ici privilégiées", 'privilégiées')):
        assert extract(text, *args[1:], **kwargs) == ([], text)
    assert extract(args[0], 'de', *args[2:]) == ([], args[0])
    assert extract(*args) == ([], args[0])  # stripped restriction requires source evidence
    text = args[0].replace('nominatives, .', 'nominatives, liées selon statuts.')
    assert extract(text, *args[1:])[0][0].payload == extract(*args, **kwargs)[0][0].payload


@pytest.mark.parametrize('stem,extractor', [
    ('dc1059db', extract_parser302_leftovers),
    ('89563831-2b91-48ca-b516-b16fdecfa657', extract_parser96_leftovers),
])
def test_old_rule_owns_consolidation_even_in_isolation(stem, extractor):
    import shab_analyzer.parse as parser
    path, = FIXTURES.glob(stem + '*.xml')
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return [], args[0]
    with patch.object(parser, extractor.__name__, capture):
        parse_publication_xml(path)
    args, kwargs = calls[0]
    assert extractor(*args, **kwargs)[0]
    assert extract(*args, **kwargs) == ([], args[0])
    result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser460_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(path)
    assert result == old


def test_no_old_extractor_consumes_new_consolidation():
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(9)
    for name, old_extract in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser460_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert not any(event.payload.get('action') == 'registered_shares_consolidated'
                       or event.payload.get('kind') == 'share_consolidation'
                       for event in events), name
        assert rest.strip(' ,.;'), name
