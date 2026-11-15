import hashlib
import inspect
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser563 import extract_parser563_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = [
    '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e',
    '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3',
    '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527',
    '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad',
    '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7',
    '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f',
    'e5619a2eccf8790bc1ba93ae8a6c90f4164cbfc460859cb13776a47c86da8d55',
    '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315',
    'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5',
    'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176',
    'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37',
    'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed',
]
TARGET = "e5619a2eccf8790bc1ba93ae8a6c90f4164cbfc460859cb13776a47c86da8d55"
ARGS = ('fr', 'fixture', '', None, None, None)


def source_text():
    return next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text


def target_text():
    return source_text().split('). ', 1)[1]


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
    with patch.object(parser, 'extract_parser563_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser563_leftovers', lambda text, *a, **kw: ([], text)):
        old = parser.parse_publication_xml(path)
    assert len(calls) == 1
    added, rest = extract(*calls[0][0], **calls[0][1])
    remaining = list(result.events)
    for event in old.events + added:
        remaining.remove(event)
    if digest == TARGET:
        assert len(added) == 1
        assert rest.strip(' .').endswith(result.leftover_text)
    else:
        assert added == []
        assert result == old



def test_payload_context_and_legacy_event():
    events, rest = extract(target_text(), 'fr', 'pub', '2021', 'uid', '1200', 'VD')
    assert len(events) == 1
    event = events[0]
    assert event.event_type == 'seat_changed'
    assert event.rule_id == 'fr.text.seat_now.v1'
    assert event.payload == {'to': 'Crans (VD)'}
    assert (event.publication_id, event.published_at, event.org_uid, event.plz,
            event.canton) == ('pub', '2021', 'uid', '1200', 'VD')
    assert Event(**vars(event)) == event
    old = Event('pub', '', 'seat_changed', 'legacy', payload={'to': 'Crans (VD)'})
    assert Event(**vars(old)) == old
    minimal = Event('pub', '', 'seat_changed', 'legacy')
    assert Event(**vars(minimal)) == minimal
    assert minimal.payload == {}
    assert rest == target_text().split('. ', 1)[1]
    assert PARSER_VERSION >= 563


def test_no_existing_rule_owns_new_clause():
    from shab_analyzer.text_extras import extract_text_extras
    text = target_text().split('. ', 1)[0]
    assert extract_text_extras(text, *ARGS, set()) == ([], text)
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser563_leftovers':
            continue
        options = {'source_text': source_text()} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('language', ['de', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


@pytest.mark.parametrize('text', [
    '', ' Le siège est maintenant . ',
    'Le siège est désormais Crans (VD).',
    'Le siège est maintenant Crans (VD), selon les statuts.',
    'Le siège est maintenant Crans (VD) inconnu.',
    'Le siège est maintenant Crans (VD).UNKNOWN',
    'Autre texte. Le siège est maintenant Crans (VD).',
])
def test_unsupported_input_unchanged(text):
    assert extract(text, *ARGS) == ([], text)


def test_prefix_leaves_unknown_suffix_intact():
    clause = target_text().split('. ', 1)[0] + '.'
    for text in (clause, '  ' + clause + '  '):
        events, rest = extract(text, *ARGS)
        assert len(events) == 1 and rest == ''
    events, rest = extract(clause + ' UNKNOWN_SUFFIX.', *ARGS)
    assert len(events) == 1 and rest == 'UNKNOWN_SUFFIX.'


@pytest.mark.parametrize('fixture,owner', [
    ('0519a2b9-3b35-487b-9e94-ef49bef0f5a6', 'extras'),
    ('ea3591dc16456363da170cb415f96fabd501154c24ba9d9a9e75d3589edeb7b6', '397'),
])
def test_legacy_boundary(fixture, owner):
    from shab_analyzer.text_extras import _FR_SEAT_BECAME, extract_text_extras
    path = FIXTURES / (fixture + '.xml')
    source = next(ET.parse(path).iter('publicationText')).text
    if owner == 'extras':
        clause = _FR_SEAT_BECAME.search(source)[0]
        assert extract_text_extras(clause, *ARGS, set())[0]
    else:
        clause = source.split('). ', 1)[1].split('. ', 1)[0] + '.'
        assert parser.extract_parser397_leftovers(clause, *ARGS)[0]
    assert extract(clause, *ARGS) == ([], clause)
    assert extract(source, *ARGS) == ([], source)
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser563_leftovers', lambda text, *a, **kw: ([], text)):
        assert parser.parse_publication_xml(path) == result
