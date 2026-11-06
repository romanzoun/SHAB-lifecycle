import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser474 import extract_parser474_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '89ce6ac882c9cb489e7a27c564c70bcef445693584cf7ac4413b34ed9d8cc7cf', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed', 'ff3901eaf7aec7d121254ffb60a30e24f5f63e716b6d4371a1143bcf57862762']


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser474_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser474_leftovers', lambda text, *a, **kw: ([], text)):
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
    if index == 11:
        assert len(added) == 1
        assert result.events == old.events + added
        assert result.leftover_text == rest.strip(' .')
    else:
        assert (added, rest) == ([], args[0])
        assert result == old


def test_payload_and_missing_optional_metadata():
    assert PARSER_VERSION == 497
    _, _, (args, kwargs) = captured(11)
    events, rest = extract(*args, **kwargs)
    assert rest == '' and len(events) == 1
    event = events[0]
    assert event.event_type == 'capital_changed'
    assert event.rule_id == 'fr.text.listed_participation_bearer_shares_permitted.v1'
    assert event.payload == {'action': 'bearer_shares_permitted', 'reason': 'listed_securities',
                             'retain_permitted': True, 'issue_permitted': True}
    assert Event(**vars(event)) == event
    sparse, _ = extract(*args[:4], None, None, None)
    assert sparse[0].payload == event.payload
    assert sparse[0].org_uid is None and sparse[0].plz is None and sparse[0].canton is None
    assert extract(*args) == (events, rest)
    legacy = Event('legacy', '', 'capital_changed', 'legacy',
                   payload={'action': 'bearer_shares_permitted', 'reason': 'listed_securities'})
    assert Event(**vars(legacy)) == legacy
    assert 'retain_permitted' not in legacy.payload and 'issue_permitted' not in legacy.payload


def test_no_old_extractor_already_owns_new_input():
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(11)
    from shab_analyzer.text_extras import extract_text_extras
    assert extract_text_extras(*args, set()) == ([], args[0])
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser474_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
        assert old(*args, **options) == ([], args[0]), name


def test_unsupported_input_unchanged():
    _, _, (args, kwargs) = captured(11)
    for text in ('', args[0] + ' UNKNOWN', '[' + args[0] + ']',
                 args[0].replace('cotés en bourse', 'non cotés en bourse'),
                 args[0].replace('au porteur', 'nominatives'),
                 args[0].replace('conserver et à émettre', 'conserver')):
        assert extract(text, *args[1:], **kwargs) == ([], text)
    for language in ('de', 'it', 'en', None):
        assert extract(args[0], language, *args[2:], **kwargs) == ([], args[0])


@pytest.mark.parametrize('text', [
    'La société est autorisée à avoir des actions au porteur car elles sont toutes cotées en bourse (art. 622 al. 1bis CO)',
    'Toutes les actions au porteur de la société étant émises sous forme de titres intermédiés au sens de la loi fédérale sur les titres intermédiés, elle est autorisée à en avoir',
])
def test_legacy_permission_ownership(text):
    from shab_analyzer.parser50 import _FR_INTERMEDIATED_BEARER_SHARES, extract_parser50_leftovers
    from shab_analyzer.parser451 import extract_parser451_leftovers
    context = ('fr', 'test', '', None, None, None)
    assert extract(text, *context) == ([], text)
    old = extract_parser50_leftovers if _FR_INTERMEDIATED_BEARER_SHARES.search(text) else extract_parser451_leftovers
    events, rest = old(text, *context)
    assert events
    assert (events, rest) == old(extract(text, *context)[1], *context)


def test_legacy_pipeline_relative():
    import shab_analyzer.parse as parser
    path = FIXTURES / 'c81d0d637c7813d98a7ed5bd5421c596782029f3c6b8816f6bba3a87e766c2e2.xml'
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    with patch.object(parser, 'extract_parser474_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser474_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(path)
    assert calls
    for args, kwargs in calls:
        assert extract(*args, **kwargs) == ([], args[0])


def test_legacy_listed_participation_pattern_ownership():
    from shab_analyzer.text_extras import _FR_BEARER_SHARES_AUTHORIZED, extract_text_extras
    _, _, (args, kwargs) = captured(11)
    text = args[0].replace('conserver et à émettre', 'avoir')
    assert _FR_BEARER_SHARES_AUTHORIZED.fullmatch(text)
    assert extract(text, *args[1:], **kwargs) == ([], text)
    old = extract_text_extras(text, *args[1:], set())
    assert old[0]
    assert extract_text_extras(extract(text, *args[1:])[1], *args[1:], set()) == old
