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
from shab_analyzer.parser562 import extract_parser562_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = [
    '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e',
    '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3',
    '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527',
    '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad',
    '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7',
    '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f',
    '201cc0549b80d96b877ba20395f2b2e45b40c5f1b6e5dcb7a80eaaf4def1bad2',
    '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315',
    'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5',
    'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176',
    'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37',
    'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed',
]
TARGET = "201cc0549b80d96b877ba20395f2b2e45b40c5f1b6e5dcb7a80eaaf4def1bad2"
ARGS = ('fr', 'fixture', '', None, None, None)


@lru_cache(maxsize=1)
def source_text():
    return next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text


@lru_cache(maxsize=1)
def target_text():
    calls = []
    with patch.object(parser, 'extract_parser562_leftovers',
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
    with patch.object(parser, 'extract_parser562_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser562_leftovers', lambda text, *a, **kw: ([], text)):
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



def test_payload_and_missing_optional_attributes():
    events, rest = extract(target_text(), *ARGS, source_text=source_text())
    assert rest == '' and len(events) == 1
    event = events[0]
    assert event.payload == {'name': 'Jacot Jean-Marc', 'place': None,
                             'action': 'signing_changed', 'powers_modified': True}
    assert event.role == 'Präsident des Verwaltungsrates'
    assert event.event_type == 'officer_changed'
    assert event.signing == 'Einzelunterschrift' and event.person_key
    assert Event(**vars(event)) == event
    old = Event('fixture', '', 'officer_changed', 'legacy', payload={'name': 'legacy'})
    assert Event(**vars(old)) == old
    assert 'powers_modified' not in old.payload
    assert PARSER_VERSION >= 562


def test_no_existing_rule_owns_target():
    from shab_analyzer.text_extras import extract_text_extras
    text = target_text()
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser562_leftovers':
            continue
        options = {'source_text': source_text()} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('language', ['de', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


@pytest.mark.parametrize('before,after', [
    ('pouvoirs', 'droits'), ('Jacot Jean-Marc', 'Autre Personne'),
    ('modifiés', 'radiés'),
])
def test_unknown_formulation(before, after):
    text = target_text().replace(before, after)
    assert extract(text, *ARGS, source_text=source_text()) == ([], text)


def test_source_required():
    text = target_text()
    assert extract(text, *ARGS) == ([], text)
    for before, after in [('individuellement', 'collectivement à deux'),
                          ('secrétaire', 'vice-président'),
                          ('nommé président', 'nommé secrétaire')]:
        assert extract(text, *ARGS, source_text=source_text().replace(before, after)) == ([], text)


def test_unknown_suffix():
    text = target_text() + '. UNKNOWN'
    assert extract(text, *ARGS, source_text=source_text()) == ([], text)


def test_legacy_boundary():
    from shab_analyzer.parser562 import _LEGACY
    text = source_text()[source_text().index('Administration:'):]
    assert any(p.search(text) for p in _LEGACY)
    assert parser.extract_parser57_leftovers(text, *ARGS)[0]
    assert extract(text, *ARGS, source_text=source_text()) == ([], text)


def test_context():
    events, _ = extract(target_text(), 'fr', 'pub', '2021', 'uid', '1208', 'GE',
                        source_text=source_text())
    assert len(events) == 1
    assert all((e.publication_id, e.published_at, e.org_uid, e.plz, e.canton) ==
               ('pub', '2021', 'uid', '1208', 'GE') for e in events)


@pytest.mark.parametrize('comma', ['', ','])
def test_legacy_pipeline_boundary(tmp_path, comma):
    text = source_text()[source_text().index('Administration:'):].split(';')[0]
    text = text.replace('président, et', 'président' + comma + ' et')
    owner = parser.extract_parser57_leftovers if comma else parser.extract_parser58_leftovers
    assert owner(text, *ARGS)[0]
    assert extract(text, *ARGS, source_text=text) == ([], text)
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    node = next(tree.iter('publicationText'))
    node.text = node.text[:node.text.index('Administration:')] + text + '.'
    path = tmp_path / 'legacy.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser562_leftovers', lambda text, *a, **kw: ([], text)):
        assert parser.parse_publication_xml(path) == result
