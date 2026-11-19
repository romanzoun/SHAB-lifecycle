import hashlib
import inspect
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser81 import extract_parser81_leftovers
from shab_analyzer.parser589 import extract_parser589_leftovers as extract

DIGEST = '4b7ff87d1a5582afc7783520bae35128aa174fb68066205e9790eeaba6d24b59'
FIXTURE = Path(__file__).parent / 'fixtures' / (DIGEST + '.xml')
ARGS = ('fr', 'fixture', '', None, None, None)


def test_fixture_integrity():
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == DIGEST
    assert PARSER_VERSION == 589


def test_fixture_pipeline_and_legacy_event():
    calls = []
    def capture(*args):
        calls.append(args)
        return extract(*args)
    with patch.object(parser, 'extract_parser589_leftovers', capture):
        result = parser.parse_publication_xml(FIXTURE)
    with patch.object(parser, 'extract_parser589_leftovers', lambda text, *args: ([], text)):
        old = parser.parse_publication_xml(FIXTURE)
    added, rest = extract(*calls[0])
    remaining = list(result.events)
    for event in old.events + added:
        remaining.remove(event)
    assert rest.endswith(result.leftover_text)
    assert len(added) == 2
    seller, buyer = added
    assert seller.event_type == buyer.event_type == 'officer_changed'
    assert seller.payload['shares_transferred'] == buyer.payload['shares_received'] == 1
    assert seller.payload['shares_count'] == 69
    assert buyer.payload['shares_count'] == 1
    assert seller.payload['shares_nominal'] == buyer.payload['shares_nominal'] == "1'000"
    assert buyer.payload['new_associate'] is True
    assert seller.signing is buyer.signing is None
    legacy = Event('old', '', 'officer_changed', 'old', payload={'name': 'Exemple'})
    assert Event(**vars(legacy)) == legacy
    assert 'new_associate' not in legacy.payload
    for text in (calls[0][0] + ' inconnu', calls[0][0].replace('1 part', '2 parts'),
                 calls[0][0].replace('69 parts', '0 parts')):
        assert extract(text, *ARGS) == ([], text)
    assert extract(calls[0][0], 'de', *ARGS[1:]) == ([], calls[0][0])


def test_legacy_boundary(tmp_path):
    text = ("Exemple Anne a cédé 3 parts de CHF 100 au nouvel associé Exemple Jean, "
            "de Genève, à Genève. Associés-gérants: Exemple Anne, nommée présidente, "
            "et Exemple Jean, pour 3 parts de CHF 100 chacun, tous deux")
    assert extract_parser81_leftovers(text, *ARGS)[0]
    assert extract(text, *ARGS) == ([], text)
    tree = ET.parse(FIXTURE)
    next(tree.iter('publicationText')).text = text
    path = tmp_path / 'boundary.xml'
    tree.write(path, encoding='utf-8')
    with patch.object(parser, 'extract_parser589_leftovers', lambda value, *args: ([], value)):
        old = parser.parse_publication_xml(path)
    assert parser.parse_publication_xml(path) == old


def test_attested_form_is_not_owned_by_old_extractors():
    text = ("Exemple Anne a cédé 1 part de CHF 100 au nouvel associé Exemple Jean, "
            "de Genève, à Genève. Exemple Anne est maintenant associé pour 5 parts de CHF 100")
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser589_leftovers':
            continue
        options = {'source_text': text} if 'source_text' in inspect.signature(old).parameters else {}
        events, _ = old(text, *ARGS, **options)
        assert not events, name
