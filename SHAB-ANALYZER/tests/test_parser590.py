import hashlib
import inspect
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser590 import extract_parser590_leftovers as extract

DIGEST = '9addf40cfea0a41de08da63270e6de7af4c3bb41c9d6831363e9e686525cac40'
FIXTURE = Path(__file__).parent / 'fixtures' / (DIGEST + '.xml')
ARGS = ('fr', 'fixture', '', None, None, None)
TEXT = ('La société est autorisée à avoir des bons de participation au porteur car '
        'ils sont tous émis sous forme de titres intermédiés au sens de la loi fédérale '
        'sur les titres intermédiés')


def test_fixture_integrity():
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == DIGEST
    assert PARSER_VERSION == 590


def test_fixture_pipeline():
    calls = []
    def capture(*args):
        calls.append(args)
        return extract(*args)
    with patch.object(parser, 'extract_parser590_leftovers', capture):
        result = parser.parse_publication_xml(FIXTURE)
    with patch.object(parser, 'extract_parser590_leftovers', lambda text, *args: ([], text)):
        old = parser.parse_publication_xml(FIXTURE)
    added, rest = extract(*calls[0])
    remaining = list(result.events)
    for event in old.events + added:
        remaining.remove(event)
    assert rest.endswith(result.leftover_text)
    assert len(added) == 1
    assert added[0].event_type == 'capital_changed'
    assert added[0].payload == {'action': 'bearer_participation_certificates_intermediated_authorized', 'intermediated': True}
    legacy = Event('old', '', 'capital_changed', 'old', payload={'action': 'old'})
    assert Event(**vars(legacy)) == legacy
    assert 'intermediated' not in legacy.payload


def test_boundaries_and_old_extractors():
    for text in (TEXT + ' inconnu', TEXT.replace('au porteur', 'nominatifs'), '[' + TEXT + ']'):
        assert extract(text, *ARGS) == ([], text)
    assert extract(TEXT, 'de', *ARGS[1:]) == ([], TEXT)
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser590_leftovers':
            continue
        options = {'source_text': TEXT} if 'source_text' in inspect.signature(old).parameters else {}
        assert not old(TEXT, *ARGS, **options)[0], name


def test_legacy_ownership(tmp_path):
    texts = [
        'Toutes les actions au porteur de la société étant émises sous forme de titres intermédiés au sens de la loi fédérale sur les titres intermédiés, elle est autorisée à en avoir',
        'La société est autorisée à avoir des actions au porteur car elles sont toutes émises sous forme de titres intermédiés au sens de la loi fédérale sur les titres intermédiés',
    ]
    for text in texts:
        assert extract(text, *ARGS) == ([], text)
        tree = ET.parse(FIXTURE)
        next(tree.iter('publicationText')).text = text
        path = tmp_path / 'boundary.xml'
        tree.write(path, encoding='utf-8')
        with patch.object(parser, 'extract_parser590_leftovers', lambda value, *args: ([], value)):
            old = parser.parse_publication_xml(path)
        assert parser.parse_publication_xml(path) == old
