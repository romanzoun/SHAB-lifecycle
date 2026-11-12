import hashlib
import inspect
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser524 import extract_parser524_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '35f65058a687606abaaf26cced5adc6a5e5033652f3f8b62274167fd6c4fa422', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = "35f65058a687606abaaf26cced5adc6a5e5033652f3f8b62274167fd6c4fa422"
ARGS = ("de", "fixture", "", None, None, None)


def target_text():
    source = next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text
    return source.split('). ', 1)[1].rstrip('.')

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
    with patch.object(parser, 'extract_parser524_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser524_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert event.event_type == 'publication_corrected'
    assert event.payload == {
        'kind': 'statutes_date', 'action': 'erroneous_entry_noted',
        'entry': '22269', 'entry_date': '2015-06-24', 'erroneous_date': '2015-06-09',
    }
    assert event.role is event.signing is None
    assert event.org_uid is event.plz is event.canton is None
    assert Event(**vars(event)) == event
    assert PARSER_VERSION == 535


def test_no_existing_rule_owns_input():
    text = target_text()
    from shab_analyzer.text_extras import extract_text_extras
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser524_leftovers':
            continue
        options = {'source_text': text} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('text', [
    '[Das Statutendatum vom 09.06.2015 wurde irrtümlich eingetragen.]',
    'Als Statutendatum wurde irrtümlich 09.06.2015 anstelle von 10.06.2015 eingetragen',
    'Mit TR-Eintrag Nr. 22269 vom 24.06.2015 wurde irrtümlich nur das Statutendatum vom 09.06.2015 erfasst',
])
def test_legacy_boundary_and_missing_optional_attributes(text, tmp_path):
    from shab_analyzer.parser90 import extract_parser90_leftovers
    from shab_analyzer.parser161 import extract_parser161_leftovers
    from shab_analyzer.parser346 import extract_parser346_leftovers
    assert extract(text, *ARGS) == ([], text)
    legacy = []
    for old in (extract_parser90_leftovers, extract_parser161_leftovers, extract_parser346_leftovers):
        legacy.extend(old(text, *ARGS)[0])
    assert len(legacy) == 1
    assert 'entry_date' not in legacy[0].payload or 'erroneous_date' not in legacy[0].payload
    assert Event(**vars(legacy[0])) == legacy[0]
    if text.startswith('['):
        assert legacy[0].payload == {
            'kind': 'statutes_date', 'action': 'erroneous_entry_noted',
            'erroneous_date': '2015-06-09',
        }
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    next(tree.iter('publicationText')).text = text
    path = tmp_path / 'boundary.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser524_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parser.parse_publication_xml(path)


@pytest.mark.parametrize('before,after', [
    ('24.06.2015', '31.02.2015'), ('09.06.2015', '31.06.2015'),
    ('22269', ''), ('irrtümlich', 'korrekt'), ('eingetragen', 'gelöscht'),
    ('Statutendatum', 'Kapital'),
])
def test_invalid_or_unattested_input(before, after):
    text = target_text().replace(before, after)
    assert extract(text, *ARGS) == ([], text)


@pytest.mark.parametrize('language', ['fr', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


def test_unknown_remainder_and_context():
    text = target_text() + ' UNKNOWN'
    assert extract(text, *ARGS) == ([], text)
    events, _ = extract(target_text(), 'de', 'pub', '2021', 'uid', '1000', 'ZH')
    assert len(events) == 1
    e = events[0]
    assert (e.publication_id, e.published_at, e.org_uid, e.plz, e.canton) == (
        'pub', '2021', 'uid', '1000', 'ZH')

