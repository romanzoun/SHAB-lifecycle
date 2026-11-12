import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser539 import extract_parser539_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = [
    '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e',
    '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3',
    '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527',
    '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad',
    '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7',
    '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f',
    '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315',
    '9f51ae5cce6293debc17335f8a54f50905af580c995d468b0ca457be6d152de6',
    'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5',
    'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176',
    'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37',
    'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed',
]
TARGET = "9f51ae5cce6293debc17335f8a54f50905af580c995d468b0ca457be6d152de6"
ARGS = ('it', 'fixture', '', None, None, None)


@lru_cache(maxsize=1)
def source_text():
    return next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text


@lru_cache(maxsize=1)
def target_text():
    calls = []
    with patch.object(parser, 'extract_parser539_leftovers',
                      lambda text, *a, **kw: (calls.append(text) or [], text)):
        parser.parse_publication_xml(FIXTURES / (TARGET + '.xml'))
    return calls[0]


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', DIGESTS)
def test_pipeline_preserves_existing_results(digest):
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (digest + '.xml')
    with patch.object(parser, 'extract_parser539_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser539_leftovers', lambda text, *a, **kw: ([], text)):
        old = parser.parse_publication_xml(path)
    assert len(calls) == 1
    added, rest = extract(*calls[0][0], **calls[0][1])
    remaining = list(result.events)
    for event in old.events + added:
        remaining.remove(event)
    if digest == TARGET:
        assert len(added) == 1
        assert rest.strip(' .').endswith(result.leftover_text)
        assert old.events
    else:
        assert added == []
        assert result == old


def test_payload_and_missing_optional_attributes():
    events, rest = extract(target_text(), *ARGS)
    assert rest == '' and len(events) == 1
    event = events[0]
    assert event.event_type == 'company_name_changed'
    assert event.payload == {'action': 'translations_removed', 'registry_updated': True}
    assert event.rule_id == 'it.text.ditta_translations_removed.v1'
    assert event.signing is None
    assert (event.org_uid, event.plz, event.canton) == (None, None, None)
    assert Event(**vars(event)) == event
    legacy = Event(publication_id='old', published_at='', event_type='company_name_changed',
                   rule_id='old', payload={'action': 'translations_removed'})
    assert Event(**vars(legacy)) == legacy
    assert PARSER_VERSION >= 539
    assert extract(target_text(), *ARGS, source_text=source_text()) == (events, rest)
    from shab_analyzer.parser110 import extract_parser110_leftovers
    normalized = target_text().replace('Traduzioni della ditta:',
                                      'Nuove traduzioni della ragione sociale:')
    old_events, old_rest = extract_parser110_leftovers(normalized, *ARGS)
    assert old_rest == rest
    old_events[0].rule_id = event.rule_id
    assert old_events == events


@pytest.mark.parametrize('before,after', [
    ('saranno', 'non saranno'), ('radiate', 'iscritte'),
    ('Registro di commercio', 'altro registro'), (']', ''),
])
def test_unsupported_unchanged(before, after):
    text = target_text().replace(before, after)
    assert extract(text, *ARGS) == ([], text)


@pytest.mark.parametrize('language', ['de', 'fr', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


def test_unknown():
    for text in ('', 'UNKNOWN', target_text() + ' UNKNOWN'):
        assert extract(text, *ARGS) == ([], text)


def test_no_old_rule_owns_target():
    text = target_text()
    from shab_analyzer.text_extras import extract_text_extras
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser539_leftovers':
            continue
        options = {'source_text': source_text()} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('version,prefix', [
    (110, '8e1f21d6-7342-4c3d-93e1-8c2ed335c5b7'), (333, '9765f439'),
])
def test_legacy_boundary(version, prefix):
    calls = []
    name = 'extract_parser' + str(version) + '_leftovers'
    old = getattr(parser, name)
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return old(*args, **kwargs)
    paths = list(FIXTURES.glob(prefix + '*.xml'))
    assert len(paths) == 1
    with patch.object(parser, name, capture):
        result = parser.parse_publication_xml(paths[0])
    args, kwargs = calls[0]
    assert old(*args, **kwargs)[0]
    assert extract(*args, **kwargs) == ([], args[0])
    with patch.object(parser, 'extract_parser539_leftovers', lambda text, *a, **kw: ([], text)):
        assert parser.parse_publication_xml(paths[0]) == result


def test_context_is_preserved():
    events, _ = extract(target_text(), 'it', 'pub', '2021', 'uid', '1000', 'TI')
    assert len(events) == 1
    event = events[0]
    assert (event.publication_id, event.published_at, event.org_uid, event.plz, event.canton) == (
        'pub', '2021', 'uid', '1000', 'TI')

