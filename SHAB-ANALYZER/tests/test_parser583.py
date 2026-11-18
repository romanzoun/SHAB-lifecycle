import hashlib
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import shab_analyzer.parse as parser
from shab_analyzer.models import Event
from shab_analyzer.parser377 import extract_parser377_leftovers
from shab_analyzer.parser583 import extract_parser583_leftovers as extract

FIXTURE = Path(__file__).parent / 'fixtures' / 'b2bea761b5ecbda0de30003f3654d2e7eeb57302fd46471fc98285d05aead4e8.xml'
ARGS = ('fr', 'fixture', '', None, None, None)


def test_fixture_integrity():
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == 'b2bea761b5ecbda0de30003f3654d2e7eeb57302fd46471fc98285d05aead4e8'


def test_pipeline_and_payload():
    calls = []
    def capture(*args):
        calls.append(args)
        return extract(*args)
    with patch.object(parser, 'extract_parser583_leftovers', capture):
        result = parser.parse_publication_xml(FIXTURE)
    with patch.object(parser, 'extract_parser583_leftovers', lambda text, *args: ([], text)):
        old = parser.parse_publication_xml(FIXTURE)
    added, rest = extract(*calls[0])
    remaining = list(result.events)
    for event in old.events + added:
        remaining.remove(event)
    assert rest.endswith(result.leftover_text)
    assert len(added) == 1
    event = added[0]
    assert event.event_type == 'officer_changed'
    assert event.role == 'directeur'
    assert event.signing == 'Kollektivunterschrift zu zweien'
    assert event.payload['signing_restriction'] == 'avec un administrateur'
    assert event.payload['procuration_revoked'] is True
    assert event.payload['action'] == 'appointed'
    assert extract(calls[0][0], *ARGS)[0][0].org_uid is None
    legacy = Event('old', '', 'officer_changed', 'old', payload={'name': 'Example'})
    assert Event(**vars(legacy)) == legacy
    assert 'procuration_revoked' not in legacy.payload
    for text in (calls[0][0].replace('radiée', 'maintenue'), calls[0][0] + ' autre'):
        assert extract(text, *ARGS) == ([], text)
    assert extract(calls[0][0], 'de', *ARGS[1:]) == ([], calls[0][0])


def test_legacy_director_boundary(tmp_path):
    text = 'Exemple Jean, nommé directeur, signe désormais collectivement à deux, sans autre restriction; sa procuration est radiée'
    assert extract_parser377_leftovers(text, *ARGS)[0]
    assert extract(text, *ARGS) == ([], text)
    tree = ET.parse(FIXTURE)
    next(tree.iter('publicationText')).text = text
    path = tmp_path / 'boundary.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser583_leftovers', lambda text, *args: ([], text)):
        assert result == parser.parse_publication_xml(path)
