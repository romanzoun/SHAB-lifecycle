import hashlib
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser519 import extract_parser519_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']

TARGET = DIGESTS[0]
ARGS = ('fr', 'fixture', '', None, None, None)


def source_sentence():
    text = next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text
    return 'Division des ' + text.split('Division des ', 1)[1].split('. Statuts', 1)[0]


def target_text():
    return source_sentence()


def canonical():
    return target_text().replace(', liées selon statuts', '').replace(
        'actions de CHF 0.10. Capital', 'actions de CHF 0.10, nominatives. Capital')


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', DIGESTS)
def test_pipeline_preserves_old_results(digest):
    path = FIXTURES / (digest + '.xml')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser519_leftovers', lambda text, *a, **kw: ([], text)):
        old = parser.parse_publication_xml(path)
    remaining = list(result.events)
    for event in old.events:
        remaining.remove(event)
    if digest == TARGET:
        added, rest = extract(old.leftover_text, old.language, old.publication_id,
                              old.published_at, old.org_uid, old.plz, old.canton,
                              source_text=next(ET.parse(path).iter('publicationText')).text)
        assert len(added) == 1
        assert all(event in result.events for event in added)
        assert rest.endswith(result.leftover_text)
    else:
        assert result == old


def test_no_old_split_rule_owns_input():
    from shab_analyzer.text_extras import extract_text_extras
    text = target_text().rstrip(' .')
    assert extract_text_extras(text, *ARGS, set())[0] == []
    from shab_analyzer.parser519 import (
        _FR_SHARE_SPLIT, _FR_COMPLEMENTED_SHARE_SPLIT,
        _FR_REGISTERED_SHARE_SPLIT_FULLY_PAID,
        _FR_REGISTERED_SHARE_SPLIT_WITHOUT_SOURCE_KIND,
        _FR_NOMINATIVE_SHARE_SPLIT, _FR_NOMINATIVE_SHARE_SPLIT_UNRESTRICTED,
    )
    for pattern in (
        _FR_SHARE_SPLIT, _FR_COMPLEMENTED_SHARE_SPLIT,
        _FR_REGISTERED_SHARE_SPLIT_FULLY_PAID,
        _FR_REGISTERED_SHARE_SPLIT_WITHOUT_SOURCE_KIND,
        _FR_NOMINATIVE_SHARE_SPLIT, _FR_NOMINATIVE_SHARE_SPLIT_UNRESTRICTED,
    ):
        assert pattern.search(text) is None


@pytest.mark.parametrize('language', ['de', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:], source_text=source_sentence()) == ([], text)




def test_payload_and_missing_optional_attributes():
    from shab_analyzer.parser58 import extract_parser58_leftovers
    events, rest = extract(target_text(), *ARGS)
    old, _ = extract_parser58_leftovers(canonical(), *ARGS)
    assert len(events) == len(old) == 1 and rest == ''
    event = events[0]
    assert event.event_type == old[0].event_type == 'capital_changed'
    assert event.payload == {**old[0].payload, 'transfer_restricted': True}
    assert event.payload['split_from'] == {'count': 1000, 'nominal': '100'}
    assert event.payload['split_to'] == {'count': 1000000, 'nominal': '0.10'}
    assert event.payload['capital_total'] == "100'000"
    assert event.payload['paid'] == "50'000"
    assert event.payload['paid_in_full'] is False
    assert event.org_uid is event.plz is event.canton is None
    assert Event(**vars(event)) == event
    assert 'transfer_restricted' not in old[0].payload
    assert Event(**vars(old[0])) == old[0]
    assert PARSER_VERSION == 550


@pytest.mark.parametrize('before,after', [
    ("50'000", "100'001"), ("50'000", "-1"),
    ("1'000'000", "999'999"), ('0.10', '0.11'),
    ('0.10', '0'), ('0.10', '0..10'),
    ('liées selon statuts', 'non liées selon statuts'),
])
def test_invalid_values_and_unattested_wording(before, after):
    text = target_text().replace(before, after)
    assert extract(text, *ARGS) == ([], text)


def test_existing_rule_boundary(tmp_path):
    from shab_analyzer.parser58 import _FR_SHARE_SPLIT
    text = canonical()
    assert _FR_SHARE_SPLIT.search(text)
    assert extract(text, *ARGS) == ([], text)
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    next(tree.iter('publicationText')).text = text
    path = tmp_path / 'boundary.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser519_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parser.parse_publication_xml(path)


def test_context():
    events, rest = extract(target_text(), 'fr', 'pub', '2021', 'uid', '1000', 'VD')
    assert rest == '' and len(events) == 1
    assert (events[0].publication_id, events[0].published_at, events[0].org_uid,
            events[0].plz, events[0].canton) == ('pub', '2021', 'uid', '1000', 'VD')
