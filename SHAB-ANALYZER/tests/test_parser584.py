import hashlib
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser239 import extract_parser239_leftovers
from shab_analyzer.parser385 import extract_parser385_leftovers
from shab_analyzer.parser584 import extract_parser584_leftovers as extract

DIGEST = 'e4cc7b93d6f5a6ca3e463b9bf2d64cf4d027b8473e1f1f7b9756d42850b088d8'
FIXTURE = Path(__file__).parent / 'fixtures' / (DIGEST + '.xml')
ARGS = ('fr', 'fixture', '', None, None, None)


def test_fixture_integrity():
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == DIGEST
    assert PARSER_VERSION == 587


def test_pipeline_and_payload():
    calls = []
    def capture(*args):
        calls.append(args)
        return extract(*args)
    with patch.object(parser, 'extract_parser584_leftovers', capture):
        result = parser.parse_publication_xml(FIXTURE)
    with patch.object(parser, 'extract_parser584_leftovers', lambda text, *args: ([], text)):
        old = parser.parse_publication_xml(FIXTURE)
    added, rest = extract(*calls[0])
    remaining = list(result.events)
    for event in old.events + added:
        remaining.remove(event)
    assert rest.endswith(result.leftover_text)
    assert len(added) == 1
    event = added[0]
    assert event.event_type == 'signing_authority_changed'
    assert event.role == 'fondé de procuration'
    assert event.signing == 'Kollektivprokura zu zweien'
    assert event.payload['action'] == 'signing_restriction_changed'
    assert event.payload['signing_restriction'] == 'avec le président'
    assert event.payload['signing_continues'] is True
    legacy = Event('old', '', 'signing_authority_changed', 'old', payload={'name': 'Example'})
    assert Event(**vars(legacy)) == legacy
    assert 'signing_restriction' not in legacy.payload
    text = calls[0][0]
    for changed in (text + ' autre', text.replace('président', 'directeur'), text.replace('procuration', 'signature')):
        assert extract(changed, *ARGS) == ([], changed)
    assert extract(text, 'de', *ARGS[1:]) == ([], text)


def test_old_rules_boundary(tmp_path):
    texts = [
        ('Exemple Jean continue de signer par procuration, mais désormais individuellement', extract_parser385_leftovers),
        ('Les procurations de Exemple Jean et de Exemple Paul sont radiées. Exemple Luc et Exemple Marc continuent de signer par procuration collectivement à deux, mais désormais sauf entre eux. Exemple Anne, maintenant domicilié à Lausanne, continue de signer par procuration collectivement à deux, mais désormais sans autre restriction', extract_parser239_leftovers),
    ]
    for index, (text, old_extractor) in enumerate(texts):
        assert old_extractor(text, *ARGS)[0]
        assert extract(text, *ARGS) == ([], text)
        tree = ET.parse(FIXTURE)
        next(tree.iter('publicationText')).text = text
        path = tmp_path / f'boundary{index}.xml'
        tree.write(path, encoding='utf-8')
        with patch.object(parser, 'extract_parser584_leftovers', lambda value, *args: ([], value)):
            old = parser.parse_publication_xml(path)
        assert parser.parse_publication_xml(path) == old
