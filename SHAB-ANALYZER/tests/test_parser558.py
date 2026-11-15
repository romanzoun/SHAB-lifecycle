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
from shab_analyzer.parser558 import extract_parser558_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', '0023736f9c4d08a7e9a85247d4b8128cbc381119f178c552cef023a242e5fd81', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = "0023736f9c4d08a7e9a85247d4b8128cbc381119f178c552cef023a242e5fd81"
ARGS = ('fr', 'fixture', '', None, None, None)


@lru_cache(maxsize=1)
def source_text():
    return next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text


@lru_cache(maxsize=1)
def target_text():
    calls = []
    with patch.object(parser, 'extract_parser558_leftovers',
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
    with patch.object(parser, 'extract_parser558_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser558_leftovers', lambda text, *a, **kw: ([], text)):
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
    for event, name in zip(events, ['Calzolari Jérôme', 'Tudorica ép. Martin Andreea']):
        assert event.event_type == 'signing_authority_changed'
        assert event.signing == 'Kollektivunterschrift zu zweien'
        assert event.role is None
        assert event.payload == {
            'name': name, 'place': None, 'action': 'signing_replaced',
            'previous_signing': 'procuration', 'previous_signing_revoked': True}
        assert Event(**vars(event)) == event
        assert event.org_uid is event.plz is event.canton is None
    legacy = Event('fixture', '', 'signing_authority_changed', 'legacy', payload={'name': 'Example'})
    assert Event(**vars(legacy)) == legacy
    assert 'previous_signing_revoked' not in legacy.payload
    assert PARSER_VERSION >= 558


def test_no_existing_rule_owns_target():
    from shab_analyzer.text_extras import extract_text_extras
    text = target_text()
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser558_leftovers':
            continue
        options = {'source_text': source_text()} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('language', ['de', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


@pytest.mark.parametrize('before,after', [
    ('collective à deux', 'individuelle'),
    ('leur procuration est radiée', 'leur procuration subsiste'),
    (', leur', '; leur'),
    ('Calzolari Jérôme', 'Tudorica ép. Martin Andreea'),
    (' et Tudorica', ', Exemple Anne et Tudorica'),
    (' et Tudorica', ' et Exemple Anne et Tudorica'),
    ('radiée', 'radiée. UNKNOWN'),
])
def test_unsupported(before, after):
    text = target_text().replace(before, after)
    assert text != target_text()
    assert extract(text, *ARGS) == ([], text)


def test_context():
    events, _ = extract(target_text(), 'fr', 'pub', '2021', 'uid', '1200', 'GE')
    assert len(events) == 2
    assert all((e.publication_id, e.published_at, e.org_uid, e.plz, e.canton) ==
               ('pub', '2021', 'uid', '1200', 'GE') for e in events)


@pytest.mark.parametrize('number,prefix', [(73, None), (283, 'ac9bc7be'), (284, None)])
def test_legacy_boundary(number, prefix):
    old = getattr(parser, f'extract_parser{number}_leftovers')
    if prefix is None:
        if number == 73:
            text = ('Signature individuelle a été conférée à Exemple Anne; sa procuration est radiée. '
                    'Signature collective à deux a été conférée à Exemple Jean et Exemple Marc; '
                    'leur procuration est radiée')
        else:
            text = ('Signature collective à deux a été conférée à Exemple Jean et Exemple Marc, '
                    'nommés directeurs; leur procuration est radiée')
        assert old(text, *ARGS)[0]
        assert extract(text, *ARGS) == ([], text)
        tree = ET.parse(FIXTURES / (TARGET + '.xml'))
        # Use a publication with its original metadata and a controlled legacy clause.
        next(tree.iter('publicationText')).text = text
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'boundary.xml'
            tree.write(path, encoding='utf-8')
            result = parser.parse_publication_xml(path)
            with patch.object(parser, 'extract_parser558_leftovers', lambda text, *a, **kw: ([], text)):
                assert parser.parse_publication_xml(path) == result
    else:
        calls = []
        def capture(*args, **kwargs):
            calls.append((args, kwargs))
            return old(*args, **kwargs)
        path = next(FIXTURES.glob(prefix + '*.xml'))
        with patch.object(parser, f'extract_parser{number}_leftovers', capture):
            result = parser.parse_publication_xml(path)
        args, kwargs = calls[0]
        assert old(*args, **kwargs)[0]
        assert extract(*args, **kwargs) == ([], args[0])
        with patch.object(parser, 'extract_parser558_leftovers', lambda text, *a, **kw: ([], text)):
            assert parser.parse_publication_xml(path) == result
