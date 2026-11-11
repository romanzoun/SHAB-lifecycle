import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser512 import extract_parser512_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'd3589ae77ed739810d33b724de5fa82a18b4396ce1d1882c8a88b4d397d9d326', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = 'd3589ae77ed739810d33b724de5fa82a18b4396ce1d1882c8a88b4d397d9d326'
ARGS = ('fr', 'fixture', '', None, None, None)


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', DIGESTS)
def test_pipeline_preserves_existing_events(digest):
    path = FIXTURES / (digest + '.xml')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser512_leftovers', lambda text, *a, **kw: ([], text)):
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
    return 'Rectificatif:' + source.split('Rectificatif:', 1)[1]


def test_payload_and_legacy_schema():
    event = extract(target_text(), *ARGS)[0][0]
    assert event.event_type == 'address_changed'
    assert event.payload == {
        'kind': 'other_address', 'action': 'publication_corrected',
        'to': 'Avenue de la Rosiaz 14, Vithus Epicerie, 1009 Pully',
        'from': 'Avenue de la Rosiaz 4, Vithus Epicerie, 1009 Pully',
        'entry': '7362', 'entry_date': '2021-04-15',
        'notice_date': '2021-04-20', 'notice_ref': '0/1005154296',
    }
    assert event.org_uid is event.plz is event.canton is None
    assert Event(**vars(event)) == event
    legacy = Event('legacy', '', 'address_changed', 'legacy', payload={'kind': 'other_address'})
    assert Event(**vars(legacy)) == legacy
    assert 'notice_ref' not in legacy.payload
    assert PARSER_VERSION == 529


def test_no_old_rule_owns_input():
    import inspect
    from shab_analyzer.text_extras import extract_text_extras
    source = target_text()
    text = source.removesuffix('.')
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser512_leftovers':
            continue
        options = {'source_text': source} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('colon', [True, False])
def test_legacy_boundary(tmp_path, colon):
    import xml.etree.ElementTree as ET
    from shab_analyzer.parser191 import extract_parser191_leftovers
    from shab_analyzer.parser126 import extract_parser126_leftovers
    text = target_text().replace('inscription no ', 'inscription n° ').replace(
        '2021 p.', '2021, p.').replace('la nouvelle autre adresse', "l'autre adresse")
    old = extract_parser191_leftovers
    if not colon:
        text = text.replace('adresse est:', 'adresse est').replace(', comme publié', ' comme publié')
        old = extract_parser126_leftovers
    assert old(text, *ARGS)[0]
    assert extract(text, *ARGS) == ([], text)
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    element = next(tree.iter('publicationText'))
    element.text = element.text.replace(target_text(), text)
    path = tmp_path / 'legacy.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser512_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parser.parse_publication_xml(path)


@pytest.mark.parametrize('old,new', [
    ('15.04.2021', '31.02.2021'), ('20.04.2021', '32.04.2021'),
    ('la nouvelle autre adresse', 'le siège'), ('comme publié', 'inconnu'),
])
def test_unsupported_variants(old, new):
    text = target_text().replace(old, new)
    assert extract(text, *ARGS) == ([], text)


@pytest.mark.parametrize('language', ['de', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


def test_unmatched_and_context():
    for text in ('', target_text() + ' Suite.', target_text().split(' (et non')[0]):
        assert extract(text, *ARGS) == ([], text)
    events, rest = extract(target_text(), 'fr', 'pub', '2021-04-22', 'CHE-000.000.000', '1009', 'VD')
    assert len(events) == 1 and rest == ''
    event = events[0]
    assert (event.publication_id, event.published_at, event.org_uid, event.plz, event.canton) == (
        'pub', '2021-04-22', 'CHE-000.000.000', '1009', 'VD')
