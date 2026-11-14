import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser498 import extract_parser498_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '4c3c15589a9ef978eab8474cd573c22e0283bc4a811ba6faa48191d4dbed92f1', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser498_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser498_leftovers', lambda text, *a, **kw: ([], text)):
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
    if index == 4:
        assert len(added) == 1
        later = list(result.events)
        for event in old.events + added:
            later.remove(event)
        assert all(event.rule_id != added[0].rule_id for event in later)
        assert rest.strip(' .').endswith(result.leftover_text)
    else:
        assert (added, rest) == ([], args[0])
        assert result == old


def test_payload_and_optional_metadata():
    assert PARSER_VERSION == 549
    _, _, (args, kwargs) = captured(4)
    events, rest = extract(*args, **kwargs)
    assert len(events) == 1
    event = events[0]
    assert event.event_type == 'organization_changed'
    assert event.rule_id == 'de.text.authorized_participation_capital_expired_fristablauf.v1'
    assert event.payload == {'action': 'authorized_capital_expired', 'decision_date': '04.12.2018'}
    assert rest and args[0].endswith(rest)
    assert Event(**vars(event)) == event
    sparse, _ = extract(*args[:4], None, None, None)
    assert sparse[0].payload == event.payload
    assert (sparse[0].org_uid, sparse[0].plz, sparse[0].canton) == (None, None, None)
    legacy = Event('legacy', '', 'organization_changed', 'legacy', payload={})
    assert Event(**vars(legacy)) == legacy
    assert 'decision_date' not in legacy.payload


def test_no_old_rule_owns_input():
    import shab_analyzer.parse as parser
    from shab_analyzer.text_extras import extract_text_extras
    _, _, (args, kwargs) = captured(4)
    clause = args[0].split(']. ', 1)[0] + ']'
    for text in (args[0], clause):
        invocation = (text, *args[1:])
        assert extract_text_extras(*invocation, set())[0] == []
        for name, old in vars(parser).items():
            if not name.startswith('extract_parser') or name == 'extract_parser498_leftovers':
                continue
            options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
            assert old(*invocation, **options) == ([], text), name



@pytest.mark.parametrize('transform', [
    lambda t: '', lambda t: 'UNKNOWN ' + t,
    lambda t: t.replace('04.12.2018', '31.02.2018'),
    lambda t: t.replace('04.12.2018', '05.12.2018', 1),
    lambda t: t.replace('genehmigte Erhöhung', 'bedingte Erhöhung'),
    lambda t: t.replace('Fristablaufs', 'Zeitablaufs'),
])
def test_unsupported_input(transform):
    _, _, (args, kwargs) = captured(4)
    text = transform(args[0])
    assert extract(text, *args[1:]) == ([], text)


@pytest.mark.parametrize('language', ['fr', 'it', None])
def test_other_languages(language):
    _, _, (args, kwargs) = captured(4)
    assert extract(args[0], language, *args[2:]) == ([], args[0])


def test_suffix_preserved_and_standalone():
    _, _, (args, _) = captured(4)
    clause = args[0].split(']. ', 1)[0] + ']'
    for ending in ('', '.'):
        events, rest = extract(clause + ending, *args[1:])
        assert len(events) == 1 and rest == ''
    events, rest = extract(clause + '. UNKNOWN', *args[1:])
    assert len(events) == 1 and rest == 'UNKNOWN'


def test_legacy_boundary(tmp_path):
    import xml.etree.ElementTree as ET
    import shab_analyzer.parse as parser
    from shab_analyzer.parser297 import extract_parser297_leftovers
    _, _, (args, _) = captured(4)
    text = args[0].split(']. ', 1)[0] + ']'
    text = text.replace('Fristablaufs', 'Zeitablaufs')
    assert extract_parser297_leftovers(text, *args[1:])[0]
    assert extract(text, *args[1:], source_text=text) == ([], text)
    tree = ET.parse(FIXTURES / (DIGESTS[4] + '.xml'))
    tree.find('.//publicationText').text = text
    local = tmp_path / 'boundary.xml'
    tree.write(local, encoding='utf-8')
    result = parse_publication_xml(local)
    with patch.object(parser, 'extract_parser498_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(local)
