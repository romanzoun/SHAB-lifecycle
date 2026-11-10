import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser503 import extract_parser503_leftovers as extract
from shab_analyzer.text_extras import _FR_CAPITAL_CLAUSE_INTRODUCED

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', '10ac1f78aed13fb99ab358b825b3ff9947d4377005e320b18021172c313dc261', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = '10ac1f78aed13fb99ab358b825b3ff9947d4377005e320b18021172c313dc261'
ARGS = ('fr', 'fixture', '', None, None, None)
CLAUSE = ("L'assemblée générale a introduit une clause statutaire relative à une "
          'augmentation conditionnelle du capital par décision du 22.03.2021. '
          'Pour les détails, voir les statuts.')
OLD = CLAUSE.replace('conditionnelle', 'autorisée')
SOURCE = CLAUSE + ' [non: ' + OLD.rstrip('.') + '].'


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', DIGESTS)
def test_pipeline_preserves_existing_events(digest):
    path = FIXTURES / (digest + '.xml')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser503_leftovers', lambda text, *a, **kw: ([], text)):
        old = parser.parse_publication_xml(path)
    remaining = list(result.events)
    for event in old.events:
        remaining.remove(event)
    if digest == TARGET:
        import xml.etree.ElementTree as ET
        source = next(e.text for e in ET.parse(path).iter() if e.tag == 'publicationText')
        added, rest = extract(old.leftover_text, old.language, old.publication_id,
                              old.published_at, old.org_uid, old.plz, old.canton,
                              source_text=source)
        assert len(added) == 1
        assert all(e in result.events for e in added)
        assert rest.endswith(result.leftover_text)
        assert any(e.rule_id == 'fr.text.conditional_capital_clause.v1' for e in old.events)
        assert any(e.rule_id == 'fr.text.authorized_capital_clause.v2' for e in old.events)
    else:
        assert result == old


def test_payload_and_absent_optional_attributes():
    events, rest = extract('[non: ]', *ARGS, source_text=SOURCE)
    assert rest == ''
    event, = events
    assert event.event_type == 'capital_changed'
    assert event.payload == dict(kind='conditional_capital_clause', action='corrected',
                                 previous_kind='authorized_capital_clause',
                                 decision_date='2021-03-22')
    assert (event.org_uid, event.plz, event.canton) == (None, None, None)
    assert Event(**vars(event)) == event
    legacy = Event('legacy', '', 'capital_changed', 'legacy',
                   payload={'kind': 'conditional_capital_clause', 'action': 'introduced'})
    assert Event(**vars(legacy)) == legacy
    assert 'previous_kind' not in legacy.payload
    assert PARSER_VERSION == 515


@pytest.mark.parametrize('text,language,source', [
    ('[non: ]', 'de', SOURCE), ('[non: ]', 'fr', ''),
    ('[non: autre]', 'fr', SOURCE), ('Autre [non: ]', 'fr', SOURCE),
    ('[non: ]', 'fr', SOURCE + ' Autre'),
    ('[non: ]', 'fr', SOURCE.replace('22.03.2021', '31.02.2021')),
    ('[non: ]', 'fr', SOURCE.replace('22.03.2021', '23.03.2021', 1)),
    ('[non: ]', 'fr', SOURCE.replace('autorisée', 'conditionnelle')),
    ('[non: ]', 'fr', SOURCE.replace('conditionnelle', 'autorisée')),
    ('[non: ]', 'fr', SOURCE.replace(' [non:', ' Autre. [non:')),
])
def test_unsupported_unchanged(text, language, source):
    assert extract(text, language, *ARGS[1:], source_text=source) == ([], text)


@pytest.mark.parametrize('text', [CLAUSE, OLD, SOURCE])
def test_legacy_clause_boundary(text):
    assert _FR_CAPITAL_CLAUSE_INTRODUCED.search(text)
    assert extract(text, *ARGS, source_text=SOURCE) == ([], text)


@pytest.mark.parametrize('stem', [
    '3be47d53-3400-40ae-b56a-723ec79ff5a5',
    '9fecdc99-d014-4589-9d12-58f379fd1af0',
    'aed7da04-1bcd-45bd-b8ec-b557edbb0ff7',
])
def test_relative_legacy_pipeline_boundary(stem):
    path = FIXTURES / (stem + '.xml')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser503_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parser.parse_publication_xml(path)
