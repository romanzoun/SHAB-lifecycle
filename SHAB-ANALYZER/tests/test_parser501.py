import hashlib
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser501 import extract_parser501_leftovers as extract
from shab_analyzer.parser143 import _DE_BRANCH_SEAT_CHANGED_WITHOUT_IDENTIFIER
from shab_analyzer.parser119 import _DE_BRANCH_ADDED_MALFORMED_SPACED_UID

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '87c853f123087ca7c358d76a2ec1d707c8b4aecf83b49687f0c1df430dc493fe', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = '87c853f123087ca7c358d76a2ec1d707c8b4aecf83b49687f0c1df430dc493fe'
ARGS = ('de', 'fixture', '', None, None, None)


def target_source():
    return ET.parse(FIXTURES / (TARGET + '.xml')).findtext('.//publicationText')


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', DIGESTS)
def test_pipeline_preserves_existing_payloads(digest):
    path = FIXTURES / (digest + '.xml')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser501_leftovers', lambda text, *a, **kw: ([], text)):
        old = parser.parse_publication_xml(path)
    remaining = list(result.events)
    for event in old.events:
        remaining.remove(event)
    if digest == TARGET:
        added, rest = extract(
            old.leftover_text, old.language, old.publication_id, old.published_at,
            old.org_uid, old.plz, old.canton, source_text=target_source())
        assert len(added) == 1
        assert all(event in result.events for event in added)
        assert added[0].event_type == 'branch_changed'
        assert rest.endswith(result.leftover_text)
        assert any(e.rule_id == 'de.text.branch_added.v1' for e in old.events)
    else:
        assert result == old


def test_annotation_payload_and_missing_optional_metadata():
    text = '[bisher: Mogelsberg] [amtliche Gemeindeumbenennung]'
    events, rest = extract(text, *ARGS, source_text=target_source())
    assert rest == ''
    assert len(events) == 1
    event = events[0]
    assert event.payload == {
        'action': 'municipality_renamed', 'previous_place': 'Mogelsberg',
        'place': 'Neckertal', 'branch_uid': 'CHE-389.008.884', 'official_change': True,
    }
    assert (event.org_uid, event.plz, event.canton) == (None, None, None)
    assert Event(**vars(event)) == event
    legacy = Event('legacy', '', 'branch_changed', 'de.text.branch_added.v1',
                   payload={'action': 'added', 'place': 'Neckertal', 'branch_uid': 'CHE-389.008.884'})
    assert Event(**vars(legacy)) == legacy
    assert 'official_change' not in legacy.payload
    assert 'previous_place' not in legacy.payload
    assert PARSER_VERSION == 534


@pytest.mark.parametrize('text', [
    'Zweigniederlassung neu: Neckertal [bisher: Mogelsberg]',
    'Zweigniederlassung neu: Neckertal (CHE-389.008.884)',
])
def test_legacy_owned_formulations_are_unchanged(text):
    assert any(pattern.fullmatch(text) for pattern in (
        _DE_BRANCH_SEAT_CHANGED_WITHOUT_IDENTIFIER, _DE_BRANCH_ADDED_MALFORMED_SPACED_UID))
    assert extract(text, *ARGS, source_text=text) == ([], text)


@pytest.mark.parametrize('language,source,suffix', [
    ('fr', None, ''), ('de', '', ''),
    ('de', None, ' Fremder Rest'),
    ('de', 'Zweigniederlassung neu: Neckertal (CHE-389.008.884) [bisher: Anderer Ort] [amtliche Gemeindeumbenennung].', ''),
])
def test_unproven_annotations_unchanged(language, source, suffix):
    text = '[bisher: Mogelsberg] [amtliche Gemeindeumbenennung]' + suffix
    assert extract(text, language, *ARGS[1:], source_text=target_source() if source is None else source) == ([], text)


def test_complete_clause_stays_with_historical_owner():
    text = target_source().split('Zweigniederlassung neu: ')[1]
    text = 'Zweigniederlassung neu: ' + text
    assert extract(text, *ARGS, source_text=target_source()) == ([], text)


@pytest.mark.parametrize('number', [417, 425, 500])
def test_relative_legacy_pipeline_boundary(number):
    import re
    source = (Path(__file__).parent / f'test_parser{number}.py').read_text()
    names = re.findall(r"[A-Za-z0-9_-]+\.xml", source)
    names += [digest + '.xml' for digest in re.findall(r"['\"]([a-f0-9]{64})['\"]", source)]
    paths = {FIXTURES / name for name in names if (FIXTURES / name).is_file()}
    assert paths
    for path in paths:
        result = parser.parse_publication_xml(path)
        with patch.object(parser, 'extract_parser501_leftovers', lambda text, *a, **kw: ([], text)):
            assert result == parser.parse_publication_xml(path)
