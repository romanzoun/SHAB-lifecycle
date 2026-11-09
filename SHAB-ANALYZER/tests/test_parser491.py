import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser491 import extract_parser491_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'd8c4eda2f1ded3b940a9da1fde17dfdf14b1a5c1f3ee8386228377b771c674ec', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser491_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser491_leftovers', lambda text, *a, **kw: ([], text)):
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
    if index == 10:
        assert len(added) == 1
        assert result.events == old.events + added
        assert result.leftover_text == rest.strip(' .')
    else:
        assert (added, rest) == ([], args[0])
        assert result == old


def test_payload_and_optional_metadata():
    assert PARSER_VERSION == 510
    _, _, (args, kwargs) = captured(10)
    events, rest = extract(*args, **kwargs)
    assert len(events) == 1 and rest == ''
    event = events[0]
    assert event.event_type == 'officer_changed'
    assert event.role == 'associée' and event.signing is None
    assert event.payload == {
        'name': 'Up to you Holding Sàrl', 'place': 'Villars-sur-Glâne',
        'uid': 'CHE-261.649.136', 'previous_name': 'L31 Holding SARL',
        'previous_uid': 'CHE-463.150.185', 'previous_place': 'Oron',
        'entry': '5815', 'entry_date': '2021-03-24', 'notice_date': '2021-03-29',
        'notice_ref': '0/1005136371', 'count': 21, 'nominal': "1'000",
        'currency': 'CHF', 'action': 'associate_corrected', 'correction': True,
        'source_wording': 'rectitiée',
    }
    assert Event(**vars(event)) == event
    sparse, _ = extract(*args[:4], None, None, None)
    assert sparse[0].payload == event.payload
    assert (sparse[0].org_uid, sparse[0].plz, sparse[0].canton) == (None, None, None)
    assert extract(*args) == (events, rest)
    legacy = Event('legacy', '', 'officer_changed', 'legacy', payload={'name': 'Legacy', 'place': None})
    assert Event(**vars(legacy)) == legacy
    assert 'source_wording' not in legacy.payload


def test_no_old_rule_owns_input():
    import shab_analyzer.parse as parser
    from shab_analyzer.text_extras import extract_text_extras
    _, _, (args, kwargs) = captured(10)
    assert extract_text_extras(*args, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser491_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
        assert old(*args, **options) == ([], args[0]), name


@pytest.mark.parametrize('transform', [
    lambda t: '', lambda t: t + ' UNKNOWN',
    lambda t: t.replace('CHF', 'EUR'),
    lambda t: t.replace('rectitiée', 'rectifiée'),
    lambda t: t.replace('24.03.2021', '32.03.2021'),
    lambda t: t.replace('29.03.2021', '29.02.2021'),
    lambda t: t.replace('CHE-261', 'CHE-26'),
    lambda t: t.replace('comme publié', 'publié'),
])
def test_unsupported_input(transform):
    _, _, (args, kwargs) = captured(10)
    text = transform(args[0])
    assert extract(text, *args[1:], **kwargs) == ([], text)


@pytest.mark.parametrize('language', ['it', 'de', None])
def test_other_languages(language):
    _, _, (args, kwargs) = captured(10)
    assert extract(args[0], language, *args[2:], **kwargs) == ([], args[0])


def test_legacy_boundary():
    import shab_analyzer.parse as parser
    from shab_analyzer.parser120 import (
        _FR_ASSOCIATE_ORGANIZATION_NAME_AND_SEAT_CORRECTED as pattern,
        extract_parser120_leftovers as old_extract,
    )
    path = FIXTURES / '4646a51a-0f14-448f-b97e-7174bc3fc31b.xml'
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return old_extract(*args, **kwargs)
    with patch.object(parser, 'extract_parser120_leftovers', capture):
        result = parse_publication_xml(path)
    args, kwargs = calls[0]
    assert pattern.fullmatch(args[0])
    assert old_extract(*args, **kwargs)[0]
    assert extract(*args) == ([], args[0])
    with patch.object(parser, 'extract_parser491_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(path)
