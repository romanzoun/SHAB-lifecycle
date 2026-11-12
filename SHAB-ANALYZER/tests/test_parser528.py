import hashlib
import inspect
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser528 import extract_parser528_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = "9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315"
ARGS = ("fr", "fixture", "", None, None, None)


def target_text():
    source = next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text
    return source[source.index('Nouveaux membres du conseil de fondation sans signature:'):].rstrip('.')

@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', DIGESTS)
def test_pipeline_preserves_existing_results(digest):
    path = FIXTURES / (digest + '.xml')
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    with patch.object(parser, 'extract_parser528_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser528_leftovers', lambda text, *a, **kw: ([], text)):
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


def test_payload_and_missing_optional_attributes():
    events, rest = extract(target_text(), *ARGS)
    assert rest == '' and len(events) == 2
    assert [e.payload['name'] for e in events] == ['da Veiga Djaló Sarah', 'Gnoni Sara']
    for e in events:
        assert e.event_type == 'officer_changed'
        assert e.role == 'membre du conseil de fondation'
        assert e.signing == 'ohne Zeichnungsberechtigung'
        assert e.payload == {'name': e.payload['name'], 'place': 'Lausanne',
                             'heimat': 'Lausanne', 'action': 'appointed',
                             'without_signature': True}
        assert Event(**vars(e)) == e
    legacy = Event('old', '', 'officer_changed', 'legacy', payload={'name': 'Example'})
    assert Event(**vars(legacy)) == legacy
    assert 'without_signature' not in legacy.payload
    assert PARSER_VERSION == 536


def test_no_existing_rule_owns_input():
    text = target_text()
    from shab_analyzer.text_extras import extract_text_extras
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser528_leftovers':
            continue
        options = {'source_text': text} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('language', ['de', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


@pytest.mark.parametrize('before,after', [
    ('toutes deux', 'tous deux'), ('sans signature', 'avec signature individuelle'),
    ('de et à', 'à'),
])
def test_unattested_variants(before, after):
    text = target_text().replace(before, after)
    assert extract(text, *ARGS) == ([], text)


def test_context_and_rest():
    events, rest = extract('UNKNOWN. ' + target_text() + '. OTHER',
                           'fr', 'pub', '2021', 'uid', '1000', 'GE')
    assert rest == 'UNKNOWN.  OTHER'
    assert len(events) == 2
    assert all((e.publication_id, e.published_at, e.org_uid, e.plz, e.canton) ==
               ('pub', '2021', 'uid', '1000', 'GE') for e in events)


@pytest.mark.parametrize('number,text', [
    (83, 'Nouveaux membres du conseil de fondation sans signature: Alpha Anne, de Genève, à Lausanne, et Beta Bea, de Nyon, à Lausanne.'),
    (128, 'Nouveaux membres du conseil de fondation sans signature: Alpha Anne, de Genève, et Beta Bea, de Nyon, tous deux à Lausanne.'),
    (216, 'Nouveaux membres du conseil de fondation sans signature: Alpha Anne, de et à Lausanne, et Beta Bea, de Nyon, à Lausanne.'),
])
def test_legacy_boundary(number, text, tmp_path):
    assert getattr(parser, f'extract_parser{number}_leftovers')(text, *ARGS)[0]
    assert extract(text, *ARGS) == ([], text)
    xml = ET.parse(FIXTURES / (TARGET + '.xml'))
    next(xml.iter('publicationText')).text = text
    path = tmp_path / 'boundary.xml'
    xml.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser528_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parser.parse_publication_xml(path)
