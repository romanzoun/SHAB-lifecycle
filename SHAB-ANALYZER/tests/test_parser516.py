import hashlib
import inspect
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser516 import extract_parser516_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'cfe605f4e8bbc08085eb22b7dd844d01fdcf474e106f0506695ea7bf1fdad278', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = 'cfe605f4e8bbc08085eb22b7dd844d01fdcf474e106f0506695ea7bf1fdad278'
ARGS = ('de', 'fixture', '', None, None, None)


def target_text():
    text = next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text
    return 'Mit Entscheid' + text.split('Mit Entscheid', 1)[1]


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', DIGESTS)
def test_pipeline_preserves_old_results(digest):
    path = FIXTURES / (digest + '.xml')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser516_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert len(events) == 1 and rest == ''
    event = events[0]
    assert event.event_type == 'status_changed'
    assert event.payload == {
        'kind': 'composition_moratorium', 'action': 'extended', 'definitive': True,
        'decision_date': '2021-04-12', 'grant_date': '2020-12-04',
        'until_date': '2021-12-05', 'previous_until_date': '2021-05-05',
        'court': 'Zivilgericht Basel-Stadt', 'commissioner': 'lic.iur. Peter Goeggel',
        'profession': 'Advokat', 'care_of': 'NEOVIUS AG',
        'street': 'Hirschgässlein 30', 'postal_code': '4010', 'place': 'Basel',
        'commissioner_mandate_extended': True,
    }
    assert event.org_uid is event.plz is event.canton is None
    assert Event(**vars(event)) == event
    legacy = Event('legacy', '', 'status_changed', 'legacy', payload={'action': 'extended'})
    assert Event(**vars(legacy)) == legacy
    assert 'commissioner_mandate_extended' not in legacy.payload
    assert PARSER_VERSION == 524


def test_no_old_rule_owns_input():
    from shab_analyzer.text_extras import extract_text_extras
    text = target_text().rstrip('.')
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser516_leftovers':
            continue
        options = {'source_text': text} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('old,new', [
    ('12.04.2021', '31.02.2021'), ('05.12.2021', '05.12.2019'),
    ('definitive', 'provisorische'), ('als Sachwalter bis', 'bis'),
    ('Basel, eingesetzt', 'Bern, eingesetzt'),
])
def test_unsupported_variants(old, new):
    text = target_text().replace(old, new)
    assert extract(text, *ARGS) == ([], text)


@pytest.mark.parametrize('language', ['fr', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


def test_unmatched_and_context():
    for text in ('', target_text() + ' Suite.', target_text().split('[bisher:')[0]):
        assert extract(text, *ARGS) == ([], text)
    events, _ = extract(target_text(), 'de', 'pub', '2021-04-13', 'uid', '4000', 'BS')
    assert all((e.publication_id, e.published_at, e.org_uid, e.plz, e.canton) ==
               ('pub', '2021-04-13', 'uid', '4000', 'BS') for e in events)


def test_existing_grant_boundary(tmp_path):
    from shab_analyzer.parser397 import extract_parser397_leftovers
    text = target_text().split('[bisher: ', 1)[1].removesuffix(']').removesuffix('.')
    assert extract_parser397_leftovers(text, *ARGS)[0]
    assert extract(text, *ARGS) == ([], text)
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    element = next(tree.iter('publicationText'))
    element.text = element.text.split('Mit Entscheid', 1)[0] + text
    path = tmp_path / 'boundary.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser516_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parser.parse_publication_xml(path)


def test_existing_extension_boundary(tmp_path):
    from shab_analyzer.parser131 import (
        _DE_DEFINITIVE_MORATORIUM_EXTENDED, extract_parser131_leftovers,
    )
    text = ('Mit Verfügung vom 15.04.2021 hat das Gerichtspräsidium Baden '
            'die gewährte definitive Nachlassstundung um 6 Monate bis zum '
            '17.10.2021 verlängert')
    assert _DE_DEFINITIVE_MORATORIUM_EXTENDED.search(text)
    assert extract_parser131_leftovers(text, *ARGS)[0]
    assert extract(text, *ARGS) == ([], text)
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    element = next(tree.iter('publicationText'))
    element.text = element.text.split('Mit Entscheid', 1)[0] + text
    path = tmp_path / 'extension_boundary.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser516_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parser.parse_publication_xml(path)
