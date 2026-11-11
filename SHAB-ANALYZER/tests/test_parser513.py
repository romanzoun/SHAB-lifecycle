import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser513 import extract_parser513_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', '7502b7fe098ea49ffc3caf556a9db6e388b802150133e0c301765a0c6dfd8885', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = '7502b7fe098ea49ffc3caf556a9db6e388b802150133e0c301765a0c6dfd8885'
ARGS = ('fr', 'fixture', '', None, None, None)


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', DIGESTS)
def test_pipeline_preserves_existing_events(digest):
    path = FIXTURES / (digest + '.xml')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser513_leftovers', lambda text, *a, **kw: ([], text)):
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
    from shab_analyzer.parser55 import _FR_STANDALONE_GROUP_SIGNING
    return _FR_STANDALONE_GROUP_SIGNING.sub('', "L'inscription" + source.split("L'inscription", 1)[1])


def test_payload_and_legacy_schema():
    from shab_analyzer.keys import person_key
    event = extract(target_text(), *ARGS)[0][0]
    assert event.event_type == 'officer_changed'
    assert event.role == "membre du conseil d'administration"
    assert event.signing is None
    assert event.person_key == person_key(name='Hopwood Tara')
    assert event.payload == {
        'name': 'Hopwood Tara', 'place': None, 'action': 'deletion_reversed',
        'remains_registered': True, 'entry': '5757', 'entry_date': '2021-03-16',
    }
    assert event.org_uid is event.plz is event.canton is None
    assert Event(**vars(event)) == event
    legacy = Event('legacy', '', 'officer_changed', 'legacy', payload={'name': 'Example'})
    assert Event(**vars(legacy)) == legacy
    assert 'remains_registered' not in legacy.payload
    assert legacy.signing is None
    assert PARSER_VERSION == 527


def test_no_old_rule_owns_input():
    import inspect
    from shab_analyzer.text_extras import extract_text_extras
    source = target_text()
    text = source.removesuffix('.')
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser513_leftovers':
            continue
        options = {'source_text': source} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


def test_legacy_boundary(tmp_path):
    import xml.etree.ElementTree as ET
    from shab_analyzer.parser117 import extract_parser117_leftovers
    text = ("L'inscription no 5757 du 16.03.2021 est rectifiée en ce sens que "
            "Hopwood Tara n'est pas radiée; demeure inscrite en qualité de "
            "membre du conseil d'administration.")
    assert extract_parser117_leftovers(text, *ARGS)[0]
    assert extract(text, *ARGS) == ([], text)
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    element = next(tree.iter('publicationText'))
    element.text = element.text.split("L'inscription", 1)[0] + text
    path = tmp_path / 'legacy.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser513_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parser.parse_publication_xml(path)


@pytest.mark.parametrize('old,new', [
    ('16.03.2021', '31.02.2021'), ('elle n\'est donc pas radiée', 'elle est radiée'),
    (' ; elle', ' avec signature individuelle; elle'),
    ("membre du conseil d'administration", 'gérante'),
])
def test_unsupported_variants(old, new):
    text = target_text().replace(old, new)
    assert extract(text, *ARGS) == ([], text)


@pytest.mark.parametrize('language', ['de', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


def test_unmatched_and_context():
    for text in ('', target_text() + ' Suite.', target_text().split(';')[0]):
        assert extract(text, *ARGS) == ([], text)
    events, rest = extract(target_text(), 'fr', 'pub', '2021-04-22', 'CHE-000.000.000', '1009', 'VD')
    assert len(events) == 1 and rest == ''
    event = events[0]
    assert (event.publication_id, event.published_at, event.org_uid, event.plz, event.canton) == (
        'pub', '2021-04-22', 'CHE-000.000.000', '1009', 'VD')

def test_original_director_correction_fixture_preserved():
    path = FIXTURES / '0c3d0b74-5467-4053-b5c6-ac2a3405a886.xml'
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser513_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parser.parse_publication_xml(path)


def test_existing_signing_rule_keeps_ownership():
    from shab_analyzer.parser55 import _FR_STANDALONE_GROUP_SIGNING, extract_parser55_leftovers
    text = target_text().replace(' ; elle', ' avec signature collective à deux; elle')
    assert _FR_STANDALONE_GROUP_SIGNING.search(text)
    assert extract_parser55_leftovers(text, *ARGS)[0]
    assert extract(text, *ARGS) == ([], text)
