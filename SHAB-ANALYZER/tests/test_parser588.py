import hashlib
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser411 import extract_parser411_leftovers
from shab_analyzer.parser588 import extract_parser588_leftovers as extract

DIGEST = 'c4a2ec80dd2fad977b4d1d12b48e4a846fd8e4326e735c147e4360e2e738366b'
FIXTURE = Path(__file__).parent / 'fixtures' / (DIGEST + '.xml')
ARGS = ('fr', 'fixture', '', None, None, None)


def test_fixture_integrity():
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == DIGEST
    assert PARSER_VERSION == 588


def test_pipeline_preserves_old_events_and_optional_metadata():
    calls = []
    def capture(*args):
        calls.append(args)
        return extract(*args)
    with patch.object(parser, 'extract_parser588_leftovers', capture):
        result = parser.parse_publication_xml(FIXTURE)
    with patch.object(parser, 'extract_parser588_leftovers', lambda text, *args: ([], text)):
        old = parser.parse_publication_xml(FIXTURE)
    added, rest = extract(*calls[0])
    remaining = list(result.events)
    for event in old.events + added:
        remaining.remove(event)
    assert rest.endswith(result.leftover_text)
    assert len(added) == 2
    first, second = added
    assert first.event_type == second.event_type == 'officer_changed'
    assert first.role == 'Präsident des Verwaltungsrates'
    assert second.role == 'Mitglied des Verwaltungsrates'
    assert first.signing == second.signing == 'Kollektivunterschrift zu zweien'
    assert first.payload == {'name': 'Berclaz Geneviève', 'place': None, 'action': 'role_changed', 'signing_continues': True}
    assert second.payload == {'name': 'Pelli Fulvio', 'place': None, 'action': 'role_changed', 'previous_role': 'président', 'signing_continues': True}
    events, _ = extract(calls[0][0], *ARGS)
    assert events[0].org_uid is events[0].plz is events[0].canton is None
    legacy = Event('old', '', 'officer_changed', 'old', payload={'name': 'Exemple'})
    assert Event(**vars(legacy)) == legacy
    assert 'action' not in legacy.payload
    for text in (calls[0][0] + ' inconnu', calls[0][0].replace('nommée présidente', 'non nommée présidente')):
        assert extract(text, *ARGS) == ([], text)
    assert extract(calls[0][0], 'de', *ARGS[1:]) == ([], calls[0][0])


def test_old_rule_boundary(tmp_path):
    text = "Les administrateurs Exemple Jean, nommé président et Exemple Pierre, jusqu'ici président, lesquels continuent à signer collectivement à deux"
    assert extract_parser411_leftovers(text, *ARGS)[0]
    assert extract(text, *ARGS) == ([], text)
    tree = ET.parse(FIXTURE)
    next(tree.iter('publicationText')).text = text
    path = tmp_path / 'boundary.xml'
    tree.write(path, encoding='utf-8')
    with patch.object(parser, 'extract_parser588_leftovers', lambda value, *args: ([], value)):
        old = parser.parse_publication_xml(path)
    assert parser.parse_publication_xml(path) == old


def test_standalone_is_not_owned_by_old_extractors():
    import inspect
    text = "Les administrateurs Exemple Anne, nommée présidente et Exemple Pierre, jusqu'ici président; lesquels continuent à signer collectivement à deux"
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser588_leftovers':
            continue
        options = {'source_text': text} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name
