import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser489 import extract_parser489_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '89ce6ac882c9cb489e7a27c564c70bcef445693584cf7ac4413b34ed9d8cc7cf', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser489_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser489_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(path)
    assert len(calls) == 1
    return result, old, calls[0]


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('index', range(12))
def test_pipeline_preserves_existing_events(index):
    result, old, (args, kwargs) = captured(index)
    added, rest = extract(*args, **kwargs)
    if index == 8:
        assert len(added) == 1
        assert result.events == old.events + added
        assert result.leftover_text == rest.strip(' .')
    else:
        assert (added, rest) == ([], args[0])
        assert result == old


def test_payload_and_optional_metadata():
    assert PARSER_VERSION == 495
    _, _, (args, kwargs) = captured(8)
    events, rest = extract(*args, **kwargs)
    assert rest == '' and len(events) == 1
    event = events[0]
    assert event.event_type == 'assets_transferred'
    assert event.payload == {
        'date': '2020-11-11', 'amendment_date': '2021-04-12',
        'recipient': 'Les Charmoises immobilier SA', 'recipient_uid': 'CHE-102.894.059',
        'assets': "677'277.11", 'liabilities': "25'000", 'net_assets': "652'277.11",
        'consideration_amount': "652'277.11", 'currency': 'CHF',
        'consideration': "une créance de CHF 652'277.11", 'consideration_kind': 'claim',
        'amendment_reason': 'non_transferable_assets_under_ldfr',
    }
    assert Event(**vars(event)) == event
    sparse, _ = extract(*args[:4], None, None, None)
    assert sparse[0].payload == event.payload
    assert sparse[0].org_uid is None and sparse[0].plz is None and sparse[0].canton is None
    assert extract(*args) == (events, rest)
    legacy = Event('legacy', '', 'assets_transferred', 'legacy', payload={'date': '2021-03-31', 'currency': 'CHF'})
    assert Event(**vars(legacy)) == legacy
    assert 'amendment_reason' not in legacy.payload
    assert 'amendment_date' not in legacy.payload


def test_no_old_rule_owns_input():
    import shab_analyzer.parse as parser
    from shab_analyzer.text_extras import extract_text_extras
    _, _, (args, kwargs) = captured(8)
    assert extract_text_extras(*args, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser489_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
        assert old(*args, **options) == ([], args[0]), name


def test_unsupported_input():
    _, _, (args, kwargs) = captured(8)
    for text in ('', args[0] + '. UNKNOWN', args[0].replace('12.04.2021', '31.02.2021'),
                 args[0].replace('selon la LDFR', ''),
                 args[0].replace("réduite à CHF 677'277.11", "réduite à CHF 1")):
        assert extract(text, *args[1:], **kwargs) == ([], text)
    for language in ('de', 'it', None):
        assert extract(args[0], language, *args[2:], **kwargs) == ([], args[0])


def test_legacy_boundary(tmp_path):
    import shab_analyzer.parse as parser
    from shab_analyzer.parser93 import _FR_ASSET_TRANSFER_UID_BEFORE_PLACE, extract_parser93_leftovers
    from xml.etree import ElementTree
    _, _, (args, _) = captured(8)
    text = ("Transfert de patrimoine: selon contrat du 31.03.2021, la société a transféré "
            "des actifs pour CHF 700'000 et des passifs envers les tiers pour CHF 70'966, "
            "à la société Immobilière Helvetia-Environnement Holding SA (CHE-200.248.883) "
            "à Carouge (GE). Contre-prestation: CHF 629'034")
    assert _FR_ASSET_TRANSFER_UID_BEFORE_PLACE.search(text)
    assert extract_parser93_leftovers(text, *args[1:])[0]
    assert extract(text, *args[1:]) == ([], text)
    root = ElementTree.parse(FIXTURES / (DIGESTS[8] + '.xml'))
    for element in root.iter('publicationText'):
        assert args[0] in element.text
        element.text = element.text.replace(args[0], text)
    path = tmp_path / 'legacy.xml'
    root.write(path, encoding='utf-8')
    result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser489_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(path)


@pytest.mark.parametrize('filename', [
    '565e704568202bfa49b1e13d1d1fff11307afd77f7d1f5333c493e9344552772.xml',
    '3eb1cd084990cb2e21d03cd016ba1c1368310ff727fb98dea9521dd0d65ae578.xml',
])
def test_related_legacy_fixtures_are_unchanged(filename):
    import shab_analyzer.parse as parser
    from xml.etree import ElementTree
    path = FIXTURES / filename
    for element in ElementTree.parse(path).iter('publicationText'):
        text = element.text
        assert extract(text, 'fr', 'legacy', '', None, None, None) == ([], text)
    result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser489_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(path)
