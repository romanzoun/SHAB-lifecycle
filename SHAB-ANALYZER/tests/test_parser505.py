import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser505 import extract_parser505_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', '4cb9ff705ffeb9cde3bd7105f25ee2558339561f0df92acc84139a31e1f8bdbe', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = '4cb9ff705ffeb9cde3bd7105f25ee2558339561f0df92acc84139a31e1f8bdbe'
ARGS = ('fr', 'fixture', '', None, None, None)


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', DIGESTS)
def test_pipeline_preserves_existing_events(digest):
    path = FIXTURES / (digest + '.xml')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser505_leftovers', lambda text, *a, **kw: ([], text)):
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
    else:
        assert result == old


def target_text():
    import xml.etree.ElementTree as ET
    source = next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text
    return source[source.index("L'inscription no"):].rstrip('.')


def test_payload_and_optional_attributes():
    event, = extract(target_text(), *ARGS)[0]
    assert event.event_type == 'officer_changed'
    assert event.role == 'sous-directrice adjointe'
    assert event.signing is None
    assert event.payload == {
        'name': 'Allende Tenore Katerina', 'place': None,
        'action': 'entry_supplemented', 'entry': '5894', 'entry_date': '2021-03-18',
    }
    assert (event.org_uid, event.plz, event.canton) == (None, None, None)
    assert Event(**vars(event)) == event
    legacy = Event('legacy', '', 'officer_changed', 'legacy', payload={'name': 'Example'})
    assert Event(**vars(legacy)) == legacy
    assert 'entry_date' not in legacy.payload
    assert PARSER_VERSION == 521


def test_no_old_rule_owns_input():
    import inspect
    from shab_analyzer.text_extras import extract_text_extras
    text = target_text()
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser505_leftovers':
            continue
        options = {'source_text': text} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('language', ['de', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


def test_optional_source_and_metadata():
    text = target_text()
    minimal = extract(text, *ARGS)
    assert extract(text, *ARGS, source_text=text) == minimal
    events, rest = extract(text, 'fr', 'fixture', '', 'CHE-123.456.789', '1200', 'GE')
    assert rest == ''
    assert events[0].payload == minimal[0][0].payload
    assert (events[0].org_uid, events[0].plz, events[0].canton) == ('CHE-123.456.789', '1200', 'GE')


def test_unsupported_unchanged():
    text = target_text()
    for candidate in ('', text + ' Autre.', text.replace('18.03.2021', '31.02.2021'),
                      text.replace('sous-directrice adjointe', 'directrice'),
                      text.replace('Allende Tenore Katerina', '')):
        assert extract(candidate, *ARGS) == ([], candidate)


@pytest.mark.parametrize('kind', ['vice', 'directors'])
def test_legacy_boundary(kind, tmp_path):
    import xml.etree.ElementTree as ET
    from shab_analyzer.parser186 import _FR_ENTRY_SUPPLEMENTED_BOARD_VICE_PRESIDENT
    from shab_analyzer.parser236 import _FR_ENTRY_SUPPLEMENTED_TWO_DIRECTORS
    prefix = "L'inscription 5894 du 18.03.2021 est complétée en ce sens que "
    if kind == 'vice':
        text = prefix + 'Allende Tenore Katerina est vice-présidente du conseil'
        assert _FR_ENTRY_SUPPLEMENTED_BOARD_VICE_PRESIDENT.fullmatch(text)
    else:
        text = prefix + 'Allende Tenore Katerina et Exemple Jean sont directeurs'
        assert _FR_ENTRY_SUPPLEMENTED_TWO_DIRECTORS.fullmatch(text)
    assert extract(text, *ARGS) == ([], text)
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    element = next(tree.iter('publicationText'))
    element.text = element.text.replace(target_text(), text)
    path = tmp_path / 'legacy.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser505_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parser.parse_publication_xml(path)
