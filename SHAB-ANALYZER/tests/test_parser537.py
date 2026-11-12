import hashlib
import inspect
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser537 import extract_parser537_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed', 'f4579d40a3e6fdfd756e6ae9e214e1d63ee078048913a16bb252fdd4b99d890b']
TARGET = 'f4579d40a3e6fdfd756e6ae9e214e1d63ee078048913a16bb252fdd4b99d890b'
ARGS = ('fr', 'fixture', '', None, None, None)


def source_text():
    return next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text


def target_text():
    calls = []
    with patch.object(parser, 'extract_parser537_leftovers',
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
    with patch.object(parser, 'extract_parser537_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser537_leftovers', lambda text, *a, **kw: ([], text)):
        old = parser.parse_publication_xml(path)
    assert len(calls) == 1
    added, rest = extract(*calls[0][0], **calls[0][1])
    remaining = list(result.events)
    for event in old.events + added:
        remaining.remove(event)
    if digest == TARGET:
        assert len(added) == 3
        assert rest.strip(' .').endswith(result.leftover_text)
        assert any(e.rule_id == 'fr.persons.group_signing.v1' for e in old.events)
    else:
        assert added == []
        assert result == old


def test_payload_and_missing_optional_attributes():
    events, rest = extract(target_text(), *ARGS)
    assert rest == '' and len(events) == 3
    ownership, buyer, seller = events
    assert ownership.event_type == 'ownership_changed'
    assert ownership.payload == dict(seller='Sadiku Agim', buyer='Sadiku Corina',
        count='10', before='200', remaining='190', nominal='100', origin='Roumanie',
        place='Denges', currency='CHF', action='share_transfer_manager_secretary')
    assert buyer.payload == dict(name='Sadiku Corina', place='Denges', origin='Roumanie', action='appointed')
    assert seller.payload == dict(name='Sadiku Agim', place=None, action='appointed')
    assert (buyer.role, seller.role) == ('gérante secrétaire', 'président')
    for event in events:
        assert event.signing is None
        assert (event.org_uid, event.plz, event.canton) == (None, None, None)
        assert Event(**vars(event)) == event
    legacy = Event(publication_id='old', published_at='', event_type='ownership_changed',
                   rule_id='old', payload={'action': 'transfer'})
    assert Event(**vars(legacy)) == legacy
    assert PARSER_VERSION >= 537
    assert extract(target_text(), *ARGS, source_text=source_text()) == (events, rest)


@pytest.mark.parametrize('before,after', [
    ('190', '191'), ('10 de ses', '0 de ses'), ('CHF 100', 'CHF 0'),
    ('gérante secrétaire', 'gérante'), ('Sadiku Corina', ''),
])
def test_unsupported_unchanged(before, after):
    text = target_text().replace(before, after)
    assert extract(text, *ARGS) == ([], text)


@pytest.mark.parametrize('language', ['de', 'it', None])
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
        if not name.startswith('extract_parser') or name == 'extract_parser537_leftovers':
            continue
        options = {'source_text': source_text()} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('version,digest', [
    (422, 'f6517c8e403ac8ce109122926e2d1e0a9466016657fd5de75a683f22b63e7d0f'),
    (426, '5e41290f9e33885413f80e5b0b6edbda1bfe190f48f03797c6df98109c922d90'),
])
def test_legacy_boundary(version, digest):
    # Capture the historical rule input; assert only relative pipeline behavior.
    calls = []
    name = 'extract_parser' + str(version) + '_leftovers'
    old = getattr(parser, name)
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return old(*args, **kwargs)
    path = FIXTURES / (digest + '.xml')
    with patch.object(parser, name, capture):
        result = parser.parse_publication_xml(path)
    args, kwargs = calls[0]
    assert old(*args, **kwargs)[0]
    assert extract(*args, **kwargs) == ([], args[0])
    with patch.object(parser, 'extract_parser537_leftovers', lambda text, *a, **kw: ([], text)):
        assert parser.parse_publication_xml(path) == result


def test_context_is_preserved():
    events, _ = extract(target_text(), 'fr', 'pub', '2021', 'uid', '1000', 'VD')
    assert len(events) == 3
    for event in events:
        assert (event.publication_id, event.published_at, event.org_uid, event.plz, event.canton) == (
            'pub', '2021', 'uid', '1000', 'VD')
