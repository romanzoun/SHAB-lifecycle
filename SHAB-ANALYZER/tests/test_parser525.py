import hashlib
import inspect
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser525 import extract_parser525_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'cc7d695e1f71e78ff2b6d966ec913d27064e5301053057c1402dca411b6b9dfd', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = "cc7d695e1f71e78ff2b6d966ec913d27064e5301053057c1402dca411b6b9dfd"
ARGS = ("fr", "fixture", "", None, None, None)


def target_text():
    source = next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text
    return source[source.index('Koch Lafont Caroline,'):].rstrip('.')

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
    with patch.object(parser, 'extract_parser525_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser525_leftovers', lambda text, *a, **kw: ([], text)):
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
    events, rest = extract(target_text(), *ARGS)
    assert len(events) == 1 and rest == ''
    event = events[0]
    assert event.event_type == 'officer_changed'
    assert event.role == 'membre de la direction'
    assert event.signing == 'Kollektivunterschrift zu zweien'
    assert event.payload == {
        'name': 'Koch Lafont Caroline', 'place': None,
        'previous_role': 'administratrice', 'signing_continued': True,
    }
    assert event.org_uid is event.plz is event.canton is None
    assert Event(**vars(event)) == event
    legacy = Event('old', '', 'officer_changed', 'legacy', payload={'name': 'Legacy'})
    assert Event(**vars(legacy)) == legacy
    assert 'previous_role' not in legacy.payload and 'signing_continued' not in legacy.payload
    assert extract(target_text(), *ARGS, source_text=target_text()) == (events, rest)
    assert PARSER_VERSION == 545


def test_no_existing_rule_owns_input():
    text = target_text()
    from shab_analyzer.text_extras import extract_text_extras
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser525_leftovers':
            continue
        options = {'source_text': text} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('text,number', [
    ("Exemple Jeanne, jusqu'ici membre secrétaire générale du conseil de fondation, maintenant directrice, continue à signer collectivement à deux", 274),
    ("Exemple Jean et Autre Pierre, jusqu'ici directeurs, maintenant membre de la direction, continuent à signer collectivement à deux", 351),
])
def test_legacy_boundary(text, number, tmp_path):
    old = getattr(parser, f'extract_parser{number}_leftovers')
    events, _ = old(text, *ARGS)
    assert events
    assert extract(text, *ARGS) == ([], text)
    assert old(extract(text, *ARGS)[1], *ARGS)[0] == events
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    next(tree.iter('publicationText')).text = text
    path = tmp_path / 'boundary.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser525_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parser.parse_publication_xml(path)


@pytest.mark.parametrize('before,after', [
    ('administratrice', 'directrice'), ('maintenant', 'anciennement'),
    ('membre de la direction', 'présidente'), ('collectivement à deux', 'individuellement'),
    ('continue à signer', 'ne signe plus'),
])
def test_invalid_or_unattested_input(before, after):
    text = target_text().replace(before, after)
    assert extract(text, *ARGS) == ([], text)


@pytest.mark.parametrize('language', ['de', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


def test_unknown_remainder_and_context():
    text = target_text() + ' UNKNOWN'
    assert extract(text, *ARGS) == ([], text)
    events, _ = extract(target_text(), 'fr', 'pub', '2021', 'uid', '1000', 'ZH')
    assert len(events) == 1
    e = events[0]
    assert (e.publication_id, e.published_at, e.org_uid, e.plz, e.canton) == (
        'pub', '2021', 'uid', '1000', 'ZH')

