import hashlib
import re
from pathlib import Path
from unittest.mock import patch

import pytest

import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser80 import extract_parser80_leftovers, _DE_CONDITIONAL_PARTICIPATION_CAPITAL
from shab_analyzer.parser499 import extract_parser499_leftovers
from shab_analyzer.parser500 import extract_parser500_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '4c3c15589a9ef978eab8474cd573c22e0283bc4a811ba6faa48191d4dbed92f1', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('index', range(12))
def test_pipeline_preserves_existing_events(index):
    path = FIXTURES / (DIGESTS[index] + '.xml')
    calls = []
    def capture(*args, **kwargs):
        value = extract_parser499_leftovers(*args, **kwargs)
        calls.append((args, value))
        return value
    with patch.object(parser, 'extract_parser499_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, '_DE_CONDITIONAL_PARTICIPATION_CAPITAL', re.compile(r'(?!)')):
        old = parser.parse_publication_xml(path)
    assert len(calls) == 1
    args, (previous_added, text) = calls[0]
    assert extract(text, *args[1:]) == ([], text)
    if index == 4:
        added, rest = extract_parser80_leftovers(text, *args[1:])
        assert len(added) == 1
        assert added[0].rule_id == 'de.text.conditional_participation_capital.v1'
        assert added[0].payload == {
            'kind': 'conditional_participation_capital', 'action': 'increase_authorized',
            'decision_date': '2021-04-07', 'details_in_statutes': True,
        }
        remaining = list(result.events)
        for event in old.events + added:
            remaining.remove(event)
        assert all(event.rule_id != added[0].rule_id for event in remaining)
        assert rest.endswith(result.leftover_text)
        assert previous_added and all(event in result.events for event in previous_added)
    else:
        assert result == old


def test_legacy_owner_and_missing_optional_metadata():
    assert PARSER_VERSION == 506
    text = ('Die Gesellschaft hat mit Beschluss vom 07.04.2021 eine bedingte Erhöhung '
            'des Partizipationskapitals gemäss näherer Umschreibung in den Statuten beschlossen')
    args = ('de', 'fixture', '', None, None, None)
    assert _DE_CONDITIONAL_PARTICIPATION_CAPITAL.fullmatch(text)
    assert extract(text, *args) == ([], text)
    events, rest = extract_parser80_leftovers(text, *args)
    assert len(events) == 1
    event = events[0]
    assert (event.org_uid, event.plz, event.canton) == (None, None, None)
    assert Event(**vars(event)) == event
    legacy = Event('legacy', '', 'capital_changed', 'legacy', payload={})
    assert Event(**vars(legacy)) == legacy
    assert 'decision_date' not in legacy.payload


@pytest.mark.parametrize('number', [270, 399, 498, 499])
def test_legacy_boundary(number):
    # Exercise the fixtures referenced by the original tests without changing them.
    source = (Path(__file__).parent / f'test_parser{number}.py').read_text()
    names = re.findall(r"[A-Za-z0-9_-]+\.xml", source)
    paths = {FIXTURES / name for name in names if (FIXTURES / name).is_file()}
    for digest in re.findall(r"['\"]([a-f0-9]{64})['\"]", source):
        path = FIXTURES / (digest + '.xml')
        if path.is_file():
            paths.add(path)
    assert paths
    for path in paths:
        result = parser.parse_publication_xml(path)
        with patch.object(parser, 'extract_parser500_leftovers', lambda text, *a, **kw: ([], text)):
            assert result == parser.parse_publication_xml(path)


def test_original_parser80_fixture_boundary():
    path = FIXTURES / '5772d372-72a7-4a08-8e48-a07a24723080.xml'
    from xml.etree import ElementTree as ET
    text = ET.parse(path).findtext('.//publicationText') or ''
    assert text
    assert extract(text, 'de', 'boundary', '', None, None, None) == ([], text)
    result = parser.parse_publication_xml(path)
    with patch.object(parser, '_DE_CONDITIONAL_PARTICIPATION_CAPITAL', re.compile(r'(?!)')):
        assert result == parser.parse_publication_xml(path)
