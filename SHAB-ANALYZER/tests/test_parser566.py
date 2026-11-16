import hashlib
import inspect
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser566 import extract_parser566_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['16b7386a065ee3d76bedaea9b0391bd3801a76d69c293452ece950d5b6c0a954', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = '16b7386a065ee3d76bedaea9b0391bd3801a76d69c293452ece950d5b6c0a954'
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
    with patch.object(parser, 'extract_parser566_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser566_leftovers', lambda text, *a, **kw: ([], text)):
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


def test_payload_and_optional_metadata():
    events, rest = extract(target_text(), 'fr', 'pub', '2021', 'uid', '1200', 'GE')
    assert rest == '' and len(events) == 2
    for event, name in zip(events, ('Dubouloz Eric', 'Bernard ép. Bany Valérie')):
        assert event.event_type == 'officer_changed'
        assert event.payload == {
            'name': name, 'place': 'Péron', 'country': 'FRA',
            'action': 'domicile_changed', 'domicile_changed': True,
        }
        assert (event.publication_id, event.published_at, event.org_uid,
                event.plz, event.canton) == ('pub', '2021', 'uid', '1200', 'GE')
        assert event.role is None and event.signing is None
        assert Event(**vars(event)) == event
    minimal = Event('pub', '', 'officer_changed', 'legacy')
    assert Event(**vars(minimal)) == minimal and minimal.payload == {}
    legacy = Event('pub', '', 'officer_changed', 'legacy',
                   payload={'name': 'Legacy', 'place': 'Genève'})
    assert Event(**vars(legacy)) == legacy
    missing = extract(target_text(), *ARGS)[0]
    for actual, expected in zip(missing, events):
        assert actual.org_uid is None and actual.plz is None and actual.canton is None
        assert actual.payload == expected.payload
    assert PARSER_VERSION >= 566


def test_no_existing_rule_owns_new_clause():
    from shab_analyzer.text_extras import extract_text_extras
    text = target_text().removesuffix('.')
    assert extract_text_extras(text, *ARGS, set()) == ([], text)
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser566_leftovers':
            continue
        options = {'source_text': source_text()} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('change', [
    lambda t: '', lambda t: t + ' UNKNOWN_SUFFIX.',
    lambda t: 'Unbekannt. ' + t,
    lambda t: t.replace('FRA', 'FRANCE'),
    lambda t: t.replace('FRA', 'fra'),
    lambda t: t.replace(' et ', ' et Personne Trois et '),
    lambda t: t.replace('sont maintenant domiciliés', 'ne sont plus domiciliés'),
])
def test_unsupported_input_unchanged(change):
    text = change(target_text())
    assert extract(text, *ARGS) == ([], text)


@pytest.mark.parametrize('language', ['de', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


def test_whitespace_and_optional_period():
    expected = extract(target_text(), *ARGS)
    assert extract('  ' + target_text() + '  ', *ARGS) == expected
    assert extract(target_text().removesuffix('.'), *ARGS) == expected


@pytest.mark.parametrize('prefix', [
    'd41564dc-fe8c-4994-82c6-ff6a3f0cd54f',
    'f80f2302-a57e-483a-b26f-92070fa24ef1', '74a65497',
])
def test_legacy_pipeline_boundary(prefix):
    paths = list(FIXTURES.glob(prefix + '*.xml'))
    assert len(paths) == 1
    calls = []
    def capture(*args, **kwargs):
        calls.append(args)
        return extract(*args, **kwargs)
    with patch.object(parser, 'extract_parser566_leftovers', capture):
        result = parser.parse_publication_xml(paths[0])
    with patch.object(parser, 'extract_parser566_leftovers', lambda text, *a: ([], text)):
        assert parser.parse_publication_xml(paths[0]) == result
    assert len(calls) == 1
    assert extract(*calls[0]) == ([], calls[0][0])


@pytest.mark.parametrize('number,text', [
    (148, 'Alpha Jean et Beta Marie sont maintenant domiciliés à Péron, FRA.'),
    (231, 'Alpha Jean et Beta ép. Gamma Marie sont maintenant domiciliés à Péron, F.'),
    (284, 'Alpha Jean et Beta ép. Gamma Marie sont maintenant domiciliés à Péron.'),
])
def test_old_rule_ownership_in_isolation(number, text):
    old = getattr(parser, f'extract_parser{number}_leftovers')
    options = {'source_text': text} if 'source_text' in inspect.signature(old).parameters else {}
    assert old(text, *ARGS, **options)[0]
    assert extract(text, *ARGS) == ([], text)
