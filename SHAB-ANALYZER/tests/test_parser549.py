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
from shab_analyzer.parser549 import extract_parser549_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'b1ed70a8ea2c479b4ef19cd5722a0ef7f043b41dddc14a6bc4f7f7147344f98d', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = "b1ed70a8ea2c479b4ef19cd5722a0ef7f043b41dddc14a6bc4f7f7147344f98d"
ARGS = ('de', 'fixture', '', None, None, None)


@lru_cache(maxsize=1)
def source_text():
    return next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text


@lru_cache(maxsize=1)
def target_text():
    calls = []
    with patch.object(parser, 'extract_parser549_leftovers',
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
    with patch.object(parser, 'extract_parser549_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser549_leftovers', lambda text, *a, **kw: ([], text)):
        old = parser.parse_publication_xml(path)
    assert len(calls) == 1
    added, rest = extract(*calls[0][0], **calls[0][1])
    remaining = list(result.events)
    for event in old.events + added:
        remaining.remove(event)
    if digest == TARGET:
        assert len(added) == 2
        assert rest.strip(' .').endswith(result.leftover_text)
    else:
        assert added == []
        assert result == old



def test_payload_and_optional_fields():
    events, rest = extract(target_text(), *ARGS, source_text=source_text())
    assert rest == '' and len(events) == 2
    assert events[0].event_type == 'branch_changed'
    assert events[0].payload == {'action': 'added', 'place': 'Aadorf', 'branch_uid': 'CHE-149.594.630'}
    assert events[1].event_type == 'organization_changed'
    assert events[1].payload == {'action': 'branch_uid_registration_requirements_adjustment',
        'place': 'Illnau-Effretikon', 'previous_registry_id': 'CH-020.9.002.915-2', 'branch_uid': 'CHE-343.915.033'}
    assert all(Event(**vars(e)) == e for e in events)
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert extract(target_text(), *ARGS) == ([], target_text())
    legacy = Event('fixture', '', 'branch_changed', 'legacy', payload={'action': 'added'})
    assert Event(**vars(legacy)) == legacy
    assert 'previous_registry_id' not in legacy.payload
    assert PARSER_VERSION >= 549


def test_no_old_rule_owns_target():
    from shab_analyzer.text_extras import extract_text_extras
    text = target_text()
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser549_leftovers':
            continue
        options = {'source_text': source_text()} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('language', ['fr', 'it', None])
def test_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:], source_text=source_text()) == ([], text)


@pytest.mark.parametrize('change', [lambda t: t + '. UNKNOWN', lambda t: '',
    lambda t: t.replace('Illnau-Effretikon', 'Unknown', 1),
    lambda t: t.replace('CH-020.9.002.915-2', 'CHE-020.002.915')])
def test_unsupported(change):
    text = change(target_text())
    assert extract(text, *ARGS, source_text=source_text()) == ([], text)


def test_legacy_boundary(tmp_path):
    from shab_analyzer.text_extras import _DE_BRANCH_ADDED, extract_text_extras
    text = _DE_BRANCH_ADDED.search(source_text())[0]
    assert extract_text_extras(text, *ARGS, set())[0]
    assert extract(text, *ARGS, source_text=source_text()) == ([], text)
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    next(tree.iter('publicationText')).text = text
    path = tmp_path / 'boundary.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser549_leftovers', lambda text, *a, **kw: ([], text)):
        assert parser.parse_publication_xml(path) == result


def test_legacy_uid_note_boundary(tmp_path):
    from shab_analyzer.parser388 import extract_parser388_leftovers
    text = target_text().replace(' Aadorf (CHE-149.594.630).', '').replace(
        'der Zweigniederlassung in', 'der ZN').replace(
        'Eintragungsvorschriften', 'Eintragungspraxis')
    assert extract_parser388_leftovers(text, *ARGS)[0]
    assert extract(text, *ARGS, source_text=source_text()) == ([], text)
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    next(tree.iter('publicationText')).text = text
    path = tmp_path / 'uid-boundary.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser549_leftovers', lambda text, *a, **kw: ([], text)):
        assert parser.parse_publication_xml(path) == result
