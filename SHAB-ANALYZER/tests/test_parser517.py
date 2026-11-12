import hashlib
import inspect
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser517 import extract_parser517_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315'
ARGS = ('fr', 'fixture', '', None, None, None)


def target_text():
    text = next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text
    return 'Le nom de famille exact' + text.split('Le nom de famille exact', 1)[1].split('. ', 1)[0] + '.'


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', DIGESTS)
def test_pipeline_preserves_old_results(digest):
    path = FIXTURES / (digest + '.xml')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser517_leftovers', lambda text, *a, **kw: ([], text)):
        old = parser.parse_publication_xml(path)
    remaining = list(result.events)
    for event in old.events:
        remaining.remove(event)
    if digest == TARGET:
        added, rest = extract(old.leftover_text, old.language, old.publication_id,
                              old.published_at, old.org_uid, old.plz, old.canton)
        assert len(added) == 1
        assert all(event in result.events for event in added)
        assert rest.endswith(result.leftover_text)
    else:
        assert result == old


def test_payload_and_missing_optional_attributes():
    events, rest = extract(target_text(), *ARGS)
    assert rest == '' and len(events) == 1
    event = events[0]
    assert event.event_type == 'officer_changed'
    assert event.role == 'membre du conseil de fondation'
    assert event.signing is None
    assert event.payload == {'name': 'Fahrni Peter', 'place': None,
        'previous_name': 'Farhni Peter', 'corrected': True, 'action': 'family_name_corrected'}
    assert event.org_uid is event.plz is event.canton is None
    assert Event(**vars(event)) == event
    legacy = Event('legacy', '', 'officer_changed', 'legacy', payload={'name': 'Example'})
    assert Event(**vars(legacy)) == legacy
    assert 'previous_name' not in legacy.payload
    assert PARSER_VERSION == 533


def test_no_old_rule_owns_input():
    from shab_analyzer.text_extras import extract_text_extras
    text = target_text().rstrip('.')
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser517_leftovers':
            continue
        options = {'source_text': text} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('language', ['de', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


@pytest.mark.parametrize('text', ['', 'Le nom de famille exact du membre est Exemple.',
    'Le nom de famille exact du membre du conseil de fondation A est B; C.'])
def test_unsupported(text):
    assert extract(text, *ARGS) == ([], text)


def test_context_and_residual():
    events, rest = extract('Avant. ' + target_text() + ' Suite.', 'fr', 'pub', '2021', 'uid', '1000', 'VD')
    assert rest == 'Avant.  Suite.'
    assert len(events) == 1
    assert (events[0].publication_id, events[0].published_at, events[0].org_uid,
            events[0].plz, events[0].canton) == ('pub', '2021', 'uid', '1000', 'VD')


def test_existing_correction_boundary(tmp_path):
    from shab_analyzer.parser407 import extract_parser407_leftovers
    text = ("Rectificatif: l'inscription no 123 du 01.01.2021 (FOSC du 02.01.2021, "
            "p. 0/123) est rectifiée en ce sens que Ancien Pierre, dont le nom de famille "
            "exact est Nouveau Pierre, est désormais de Lausanne, toujours à Genève")
    assert extract_parser407_leftovers(text, *ARGS)[0]
    assert extract(text, *ARGS) == ([], text)
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    element = next(tree.iter('publicationText'))
    element.text = element.text.split('Le membre du conseil', 1)[0] + text
    path = tmp_path / 'boundary.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser517_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parser.parse_publication_xml(path)
