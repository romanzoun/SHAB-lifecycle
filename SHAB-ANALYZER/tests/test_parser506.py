import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser506 import extract_parser506_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'ae2b7ac94f0fad20f3804eba504dff939167fe253ee80e374f77c95d8b6f0859', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = 'ae2b7ac94f0fad20f3804eba504dff939167fe253ee80e374f77c95d8b6f0859'
ARGS = ('it', 'fixture', '', None, None, None)


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', DIGESTS)
def test_pipeline_preserves_existing_events(digest):
    path = FIXTURES / (digest + '.xml')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser506_leftovers', lambda text, *a, **kw: ([], text)):
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
    return source[source.index('[La restrizione'):source.index(' [no:')]


def test_payload_and_optional_attributes():
    event, = extract(target_text(), *ARGS)[0]
    assert event.event_type == 'capital_changed'
    assert event.payload == {'kind': 'share_transfer_restricted', 'action': 'removed',
                             'share_kind': 'azioni nominative'}
    assert event.role is None and event.signing is None
    assert (event.org_uid, event.plz, event.canton) == (None, None, None)
    assert Event(**vars(event)) == event
    legacy = Event('legacy', '', 'capital_changed', 'legacy', payload={})
    assert Event(**vars(legacy)) == legacy
    assert 'share_kind' not in legacy.payload
    assert PARSER_VERSION == 546


def test_no_old_rule_owns_input():
    import inspect
    from shab_analyzer.text_extras import extract_text_extras
    text = target_text()
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser506_leftovers':
            continue
        options = {'source_text': text} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('language', ['de', 'fr', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


def test_optional_source_and_metadata():
    text = target_text()
    minimal = extract(text, *ARGS)
    assert extract(text, *ARGS, source_text=text) == minimal
    events, rest = extract(text, 'it', 'fixture', '', 'CHE-123.456.789', '1200', 'GE')
    assert rest == ''
    assert events[0].payload == minimal[0][0].payload
    assert (events[0].org_uid, events[0].plz, events[0].canton) == ('CHE-123.456.789', '1200', 'GE')


def test_unsupported_unchanged():
    text = target_text()
    for candidate in ('', text + ' Altro.', text.replace('cancellata', 'introdotta'),
                      text.replace('azioni nominative', 'azioni al portatore')):
        assert extract(candidate, *ARGS) == ([], candidate)


@pytest.mark.parametrize('text', [
    'Nuova limitazione della trasferibilità: [La trasferibilità delle azioni nominative è limitata dallo statuto]',
    'Nuova limitazione della trasferibilità: [La limitazione della trasferibilità delle azioni nominative è cancellata.]',
    'Nuova limitazione della trasferibilità: [La limitazione alla trasferibilità delle azioni nominative è abrogata.] [radiati: La trasferibilità delle azioni nominative è limitata dallo statuto.]',
])
def test_legacy_boundary(text, tmp_path):
    import xml.etree.ElementTree as ET
    from shab_analyzer.parser506 import _LEGACY
    assert any(pattern.search(text) for pattern in _LEGACY)
    assert extract(text, *ARGS) == ([], text)
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    element = next(tree.iter('publicationText'))
    element.text = element.text.replace(target_text(), text)
    path = tmp_path / 'legacy.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser506_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parser.parse_publication_xml(path)
