import hashlib
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import shab_analyzer.parse as parser
from shab_analyzer.models import Event
from shab_analyzer.parser129 import extract_parser129_leftovers
from shab_analyzer.parser582 import extract_parser582_leftovers as extract

FIXTURE = Path(__file__).parent / 'fixtures' / '24e26edea1fe3c98669964dd91a0d0e0e43aeae141ee2ed1c7881370d7650a0c.xml'
DIGEST = '24e26edea1fe3c98669964dd91a0d0e0e43aeae141ee2ed1c7881370d7650a0c'
ARGS = ('fr', 'fixture', '', None, None, None)


def test_fixture_integrity():
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == DIGEST


def test_pipeline_and_payload():
    calls = []
    def capture(*args):
        calls.append(args)
        return extract(*args)
    with patch.object(parser, 'extract_parser582_leftovers', capture):
        result = parser.parse_publication_xml(FIXTURE)
    with patch.object(parser, 'extract_parser582_leftovers', lambda text, *args: ([], text)):
        old = parser.parse_publication_xml(FIXTURE)
    added, rest = extract(*calls[0])
    remaining = list(result.events)
    for event in old.events + added:
        remaining.remove(event)
    assert rest.endswith(result.leftover_text)
    assert len(added) == 1
    event = added[0]
    assert event.event_type == 'officer_changed'
    assert event.role == 'associé commanditaire'
    assert event.signing == 'ohne Zeichnungsberechtigung'
    assert event.payload['limited_partnership_contribution'] == "1'000"
    assert event.payload['currency'] == 'CHF'
    assert event.payload['action'] == 'appointed'
    optional = extract(calls[0][0], *ARGS)[0][0]
    assert optional.org_uid is None and optional.plz is None and optional.canton is None
    legacy = Event('old', '', 'officer_changed', 'old', payload={'name': 'Example'})
    assert Event(**vars(legacy)) == legacy
    assert 'limited_partnership_contribution' not in legacy.payload
    for text in (calls[0][0].replace("1'000", '0'), calls[0][0] + ' autre'):
        assert extract(text, *ARGS) == ([], text)
    assert extract(calls[0][0], 'de', *ARGS[1:]) == ([], calls[0][0])


def test_legacy_proxy_boundary(tmp_path):
    text = ("Nouvel associé commanditaire: Exemple Jean, de Genève, à Nyon, FR, "
            "avec une commandite de CHF 1'000, lequel signe par procuration collective à deux")
    assert extract_parser129_leftovers(text, *ARGS)[0]
    assert extract(text, *ARGS) == ([], text)
    tree = ET.parse(FIXTURE)
    next(tree.iter('publicationText')).text = text
    path = tmp_path / 'boundary.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser582_leftovers', lambda text, *args: ([], text)):
        assert result == parser.parse_publication_xml(path)
