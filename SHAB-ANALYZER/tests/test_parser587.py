import hashlib
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser85 import extract_parser85_leftovers
from shab_analyzer.parser377 import extract_parser377_leftovers
from shab_analyzer.parser587 import extract_parser587_leftovers as extract

DIGEST = '78262c593192d1c07faa94b6c736ac3e0d92f8e31a2252c463cbdf30b5323e18'
FIXTURE = Path(__file__).parent / 'fixtures' / (DIGEST + '.xml')
ARGS = ('fr', 'fixture', '', None, None, None)


def test_fixture_integrity():
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == DIGEST
    assert PARSER_VERSION == 590


def test_pipeline_and_optional_metadata():
    calls = []
    def capture(*args):
        calls.append(args)
        return extract(*args)
    with patch.object(parser, 'extract_parser587_leftovers', capture):
        result = parser.parse_publication_xml(FIXTURE)
    with patch.object(parser, 'extract_parser587_leftovers', lambda text, *args: ([], text)):
        old = parser.parse_publication_xml(FIXTURE)
    added, rest = extract(*calls[0])
    remaining = list(result.events)
    for event in old.events + added:
        remaining.remove(event)
    assert rest.endswith(result.leftover_text)
    assert len(added) == 1
    event = added[0]
    assert event.event_type == 'officer_changed'
    assert event.role == 'directrice' and event.signing is None
    assert event.payload == {'name': 'Yan Yiju', 'place': 'Rougemont', 'action': 'appointed'}
    events, _ = extract(calls[0][0], *ARGS)
    assert events[0].org_uid is None and events[0].plz is None and events[0].canton is None
    legacy = Event('old', '', 'officer_changed', 'old', payload={'name': 'Exemple'})
    assert Event(**vars(legacy)) == legacy
    assert 'action' not in legacy.payload and 'place' not in legacy.payload
    for changed in (calls[0][0] + ' inconnu', calls[0][0].replace('directrice', 'directeur')):
        assert extract(changed, *ARGS) == ([], changed)
    assert extract(calls[0][0], 'de', *ARGS[1:]) == ([], calls[0][0])


@pytest.mark.parametrize('text,old_extract', [
    ('Exemple Anne, maintenant à Lausanne, est nommée liquidatrice', extract_parser85_leftovers),
    ('Exemple Jean, maintenant à Lausanne, est nommé administrateur', extract_parser377_leftovers),
])
def test_old_rule_boundary(text, old_extract, tmp_path):
    assert old_extract(text, *ARGS)[0]
    assert extract(text, *ARGS) == ([], text)
    tree = ET.parse(FIXTURE)
    next(tree.iter('publicationText')).text = text
    path = tmp_path / 'boundary.xml'
    tree.write(path, encoding='utf-8')
    with patch.object(parser, 'extract_parser587_leftovers', lambda value, *args: ([], value)):
        old = parser.parse_publication_xml(path)
    assert parser.parse_publication_xml(path) == old
