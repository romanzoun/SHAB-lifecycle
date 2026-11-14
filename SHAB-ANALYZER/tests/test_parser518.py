import hashlib
import inspect
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser518 import extract_parser518_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGETS = {DIGESTS[0], DIGESTS[8]}
TARGET = DIGESTS[0]
ARGS = ('fr', 'fixture', '', None, None, None)


def source_sentence(digest=TARGET):
    text = next(ET.parse(FIXTURES / (digest + '.xml')).iter('publicationText')).text
    return "L'inscription " + text.split("L'inscription ", 1)[1].split('liées selon statuts.', 1)[0] + 'liées selon statuts.'


def target_text(digest=TARGET):
    return source_sentence(digest).replace('liées selon statuts', '')


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', DIGESTS)
def test_pipeline_preserves_old_results(digest):
    path = FIXTURES / (digest + '.xml')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser518_leftovers', lambda text, *a, **kw: ([], text)):
        old = parser.parse_publication_xml(path)
    remaining = list(result.events)
    for event in old.events:
        remaining.remove(event)
    if digest in TARGETS:
        added, rest = extract(old.leftover_text, old.language, old.publication_id,
                              old.published_at, old.org_uid, old.plz, old.canton,
                              source_text=next(ET.parse(path).iter('publicationText')).text)
        assert len(added) == 1
        assert all(event in result.events for event in added)
        assert rest.endswith(result.leftover_text)
    else:
        assert result == old


@pytest.mark.parametrize('digest', sorted(TARGETS))
def test_payload_and_missing_optional_attributes(digest):
    events, rest = extract(target_text(digest), *ARGS, source_text=source_sentence(digest))
    assert rest == '' and len(events) == 1
    event = events[0]
    assert event.event_type == 'organization_changed'
    assert event.role is event.signing is None
    expected = {'action': 'registered_share_transfer_restriction_entry_complemented',
                'transfer_restriction': 'liées selon statuts'}
    if digest == TARGET:
        expected.update(entry='4282', entry_date='28.02.2020', notice_date='04.03.2020', notice_reference='1004845047')
        assert 'count' not in event.payload and 'nominal' not in event.payload
    else:
        expected.update(entry='10514', entry_date='03.06.2019', notice_date='06.06.2019', notice_reference='0/1004646415', count="5'000", nominal='100')
    assert event.payload == expected
    assert event.org_uid is event.plz is event.canton is None
    assert Event(**vars(event)) == event
    legacy = Event('legacy', '', 'organization_changed', 'legacy', payload={'action': 'legacy'})
    assert Event(**vars(legacy)) == legacy
    assert 'transfer_restriction' not in legacy.payload
    assert PARSER_VERSION == 548


@pytest.mark.parametrize('digest', sorted(TARGETS))
def test_no_old_rule_owns_input(digest):
    from shab_analyzer.text_extras import extract_text_extras
    text = target_text(digest).rstrip(' .')
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser518_leftovers':
            continue
        options = {'source_text': source_sentence(digest)} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('language', ['de', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:], source_text=source_sentence()) == ([], text)


def test_source_required_and_dates_validated():
    text = target_text()
    assert extract(text, *ARGS) == ([], text)
    invalid = text.replace('28.02.2020', '31.02.2020')
    assert extract(invalid, *ARGS, source_text=source_sentence().replace('28.02.2020', '31.02.2020')) == ([], invalid)
    assert extract(text, *ARGS, source_text=source_sentence().replace('liées', 'non liées')) == ([], text)


def test_context_and_residual():
    events, rest = extract('Avant. ' + target_text() + ' Suite.', 'fr', 'pub', '2021', 'uid', '1000', 'VD', source_text=source_sentence())
    assert rest == 'Avant.  Suite.'
    assert len(events) == 1
    assert (events[0].publication_id, events[0].published_at, events[0].org_uid,
            events[0].plz, events[0].canton) == ('pub', '2021', 'uid', '1000', 'VD')


def test_existing_rule_boundary(tmp_path):
    from shab_analyzer.parser462 import _FR_COMPLEMENTED_SHARE_SPLIT
    text = ("L'inscription no 123 du 01.01.2021 est complétée en ce sens que les 100 actions de CHF 100 "
            "ont été divisées en 1000 actions de CHF 10. Capital-actions: CHF 10000, libéré à concurrence de CHF 10000, "
            "divisé en 1000 actions de CHF 10, nominatives")
    assert _FR_COMPLEMENTED_SHARE_SPLIT.fullmatch(text)
    assert extract(text, *ARGS, source_text=text) == ([], text)
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    next(tree.iter('publicationText')).text = text
    path = tmp_path / 'boundary.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser518_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parser.parse_publication_xml(path)
