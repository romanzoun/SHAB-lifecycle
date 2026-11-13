import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser511 import extract_parser511_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'e47fbcea4377f867e0ef2d1c7ec84653d6152cfdf7e9c7d20e989de25d8c89ad', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = 'e47fbcea4377f867e0ef2d1c7ec84653d6152cfdf7e9c7d20e989de25d8c89ad'
ARGS = ('de', 'fixture', '', None, None, None)


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', DIGESTS)
def test_pipeline_preserves_existing_events(digest):
    path = FIXTURES / (digest + '.xml')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser511_leftovers', lambda text, *a, **kw: ([], text)):
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
        assert len(added) == 2
        assert all(e in result.events for e in added)
        assert rest.endswith(result.leftover_text)
    else:
        assert result == old


def target_text():
    import xml.etree.ElementTree as ET
    source = next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text
    return 'Bemerkungen zum Hauptsitz neu:' + source.split('Bemerkungen zum Hauptsitz neu:', 1)[1]


def test_payload_and_missing_optional_attributes():
    grant, extension = extract(target_text(), *ARGS)[0]
    assert grant.event_type == extension.event_type == 'status_changed'
    assert grant.payload == {
        'scope': 'head_office', 'moratorium_type': 'provisional',
        'authority': 'Zivilkreisgericht Basel-Landschaft Ost',
        'kind': 'composition_moratorium_granted', 'decision_date': '2020-12-15',
        'until': '2021-02-15', 'commissioner': 'Martin Niederberger',
        'commissioner_status': 'provisional', 'commissioner_company': 'BDO AG',
        'commissioner_company_uid': 'CHE-105.952.747',
        'commissioner_address': 'Schiffbaustrasse 2',
        'commissioner_postal_code': '8005', 'commissioner_place': 'Zürich',
    }
    assert extension.payload == {
        'scope': 'head_office', 'moratorium_type': 'provisional',
        'authority': 'Zivilkreisgericht Basel-Landschaft Ost',
        'kind': 'composition_moratorium_extended', 'decision_date': '2021-02-09',
        'until': '2021-05-14', 'publication_order_date': '2021-03-30',
    }
    for event in (grant, extension):
        assert event.role is event.signing is None
        assert (event.org_uid, event.plz, event.canton) == (None, None, None)
        assert Event(**vars(event)) == event
    legacy = Event('legacy', '', 'status_changed', 'legacy', payload={
        'kind': 'composition_moratorium_extended', 'until': '2021-05-14'})
    assert Event(**vars(legacy)) == legacy
    assert 'publication_order_date' not in legacy.payload
    assert PARSER_VERSION == 547


def test_no_old_rule_owns_input():
    import inspect
    from shab_analyzer.text_extras import extract_text_extras
    source = target_text()
    text = source.removesuffix('.')
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser511_leftovers':
            continue
        options = {'source_text': source} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


def test_legacy_boundary(tmp_path):
    import xml.etree.ElementTree as ET
    from shab_analyzer.parser63 import extract_parser63_leftovers
    text = ('Das Bezirksgericht Beispiel hat der Gesellschaft mit Entscheid vom '
            '15.12.2020 die provisorische Nachlassstundung für die Dauer von zwei Monaten '
            'bewilligt und als provisorischen Sachwalter Max Muster eingesetzt. '
            'Mit Entscheid vom 09.02.2021 ist der Gesellschaft die provisorische '
            'Nachlassstundung bis zum 14.05.2021 verlängert worden')
    assert extract_parser63_leftovers(text, *ARGS)[0]
    assert extract(text, *ARGS) == ([], text)
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    element = next(tree.iter('publicationText'))
    element.text = element.text.replace(target_text(), text)
    path = tmp_path / 'legacy.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser511_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parser.parse_publication_xml(path)


@pytest.mark.parametrize('language', ['fr', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


@pytest.mark.parametrize('old,new', [
    ('15.12.2020', '31.02.2020'), ('09.02.2021', '32.02.2021'),
    ('30.03.2021', '30.13.2021'), ('14.05.2021', '14.00.2021'),
    ('provisorische Nachlassstundung', 'definitive Nachlassstundung'),
    ('die Publikation der', 'die Aufhebung der'),
    ('p.A.', 'bei'),
])
def test_unsupported_variants(old, new):
    text = target_text().replace(old, new)
    assert extract(text, *ARGS) == ([], text)


def test_unsupported_unchanged():
    for text in ('', target_text() + ' Weiterer Text.', target_text().split(' Mit Verfügung vom 30.')[0]):
        assert extract(text, *ARGS) == ([], text)


def test_context_is_preserved():
    events, rest = extract(target_text(), 'de', 'publication', '2021-04-01',
                           'CHE-000.000.000', '4000', 'BS')
    assert len(events) == 2 and rest == ''
    for event in events:
        assert (event.publication_id, event.published_at, event.org_uid,
                event.plz, event.canton) == (
                    'publication', '2021-04-01', 'CHE-000.000.000', '4000', 'BS')
