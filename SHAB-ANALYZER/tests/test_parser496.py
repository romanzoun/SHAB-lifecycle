import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser496 import extract_parser496_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', '6dd317b3a2ab4e14ad38a927aa18751a97891afd38d5fdfa92a4c16059e8cb00', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser496_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser496_leftovers', lambda text, *a, **kw: ([], text)):
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
    if index == 10:
        assert len(added) == 1
        later = list(result.events)
        for event in old.events + added:
            later.remove(event)
        own = {event.rule_id for event in added}
        assert all(event.rule_id not in own for event in later)
        assert rest.strip(' .').endswith(result.leftover_text)
    else:
        assert (added, rest) == ([], args[0])
        assert result == old


def test_payload_and_optional_metadata():
    assert PARSER_VERSION == 516
    _, _, (args, kwargs) = captured(10)
    events, rest = extract(*args, **kwargs)
    assert rest == '' and len(events) == 1
    event = events[0]
    assert event.event_type == 'status_changed'
    assert event.rule_id == 'fr.text.cantonal_bankruptcy_suspended_numeric_date.v1'
    assert event.payload == {
        'kind': 'bankruptcy_effect_suspended', 'action': 'suspended',
        'date': '2021-04-08',
        'authority': 'Le président de la Cour des poursuites et faillites du Tribunal cantonal',
    }
    assert Event(**vars(event)) == event
    sparse, _ = extract(*args[:4], None, None, None)
    assert sparse[0].payload == event.payload
    assert (sparse[0].org_uid, sparse[0].plz, sparse[0].canton) == (None, None, None)
    legacy = Event('legacy', '', 'status_changed', 'legacy', payload={'kind': 'bankruptcy_effect_suspended'})
    assert Event(**vars(legacy)) == legacy
    assert 'authority' not in legacy.payload and 'date' not in legacy.payload


def test_no_old_rule_owns_input():
    import shab_analyzer.parse as parser
    from shab_analyzer.text_extras import extract_text_extras
    _, _, (args, kwargs) = captured(10)
    assert extract_text_extras(*args, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser496_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
        assert old(*args, **options) == ([], args[0]), name


@pytest.mark.parametrize('transform', [
    lambda t: '', lambda t: t + ' UNKNOWN',
    lambda t: t.replace('08.04.2021', '31.02.2021'),
    lambda t: t.replace('08.04.2021', '00.04.2021'),
    lambda t: t.replace('prononcé', 'révoqué'),
    lambda t: t.replace('effet suspensif', 'annulation'),
])
def test_unsupported_input(transform):
    _, _, (args, kwargs) = captured(10)
    text = transform(args[0])
    assert extract(text, *args[1:]) == ([], text)


@pytest.mark.parametrize('language', ['it', 'de', None])
def test_other_languages(language):
    _, _, (args, kwargs) = captured(10)
    assert extract(args[0], language, *args[2:]) == ([], args[0])


@pytest.mark.parametrize('module,pattern_name,text', [
    ('parser78', '_FR_CANTONAL_COURT_BANKRUPTCY_SUSPENDED',
     "La présidente de la Cour des poursuites et faillites du Tribunal cantonal a prononcé l'effet suspensif de la procédure de faillite le 8 avril 2021"),
    ('parser195', '_FR_BANKRUPTCY_PROCEEDINGS_SUSPENDED_ORDINAL_DATE',
     "Le président du Tribunal de l'arrondissement de Lausanne a prononcé l'effet suspensif de la procédure de faillite le 1er avril 2021"),
    ('parser354', None,
     "Le président de la Cour des poursuites et faillites du Tribunal cantonal a prononcé l'effet suspensif de la procédure de faillite le 8 août 2021"),
    ('parser257', None,
     "Le président de la Cour des poursuites et faillites du Tribunal cantonal a admis la requête d'effet suspensif de la procédure de faillite le 8 janvier 2021"),
])
def test_legacy_boundary(module, pattern_name, text, tmp_path):
    import importlib
    import xml.etree.ElementTree as ET
    import shab_analyzer.parse as parser
    old = importlib.import_module('shab_analyzer.' + module)
    if pattern_name:
        assert getattr(old, pattern_name).fullmatch(text)
    args = (text, 'fr', 'fixture', '', None, None, None)
    assert getattr(old, 'extract_' + module + '_leftovers')(*args)[0]
    assert extract(*args, source_text=text) == ([], text)
    tree = ET.parse(FIXTURES / (DIGESTS[10] + '.xml'))
    tree.find('.//publicationText').text = text
    local = tmp_path / 'boundary.xml'
    tree.write(local, encoding='utf-8')
    result = parse_publication_xml(local)
    with patch.object(parser, 'extract_parser496_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(local)
