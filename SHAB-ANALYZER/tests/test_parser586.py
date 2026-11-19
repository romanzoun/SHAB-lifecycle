import hashlib
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser369 import extract_parser369_leftovers
from shab_analyzer.parser586 import extract_parser586_leftovers as extract

DIGEST = '988004abd3fbc37a31fc9c1910fd96b424fd3fddd49aa24a3c189c77f5b8fca7'
FIXTURE = Path(__file__).parent / 'fixtures' / (DIGEST + '.xml')
ARGS = ('de', 'fixture', '', None, None, None)


def test_fixture_integrity():
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == DIGEST
    assert PARSER_VERSION == 588


def test_pipeline_and_compatibility():
    calls = []
    def capture(*args):
        calls.append(args)
        return extract(*args)
    with patch.object(parser, 'extract_parser586_leftovers', capture):
        result = parser.parse_publication_xml(FIXTURE)
    with patch.object(parser, 'extract_parser586_leftovers', lambda text, *args: ([], text)):
        old = parser.parse_publication_xml(FIXTURE)
    added, rest = extract(*calls[0])
    remaining = list(result.events)
    for event in old.events + added:
        remaining.remove(event)
    assert rest.endswith(result.leftover_text)
    assert len(added) == 1
    event = added[0]
    assert event.event_type == 'organization_changed'
    assert event.payload == {'action': 'bearer_to_registered_shares_statutes_changed',
        'capital': "75'000", 'count': '75', 'nominal': "1'000", 'previous_count': '75',
        'previous_nominal': "1'000", 'statutes_date': '26.04.2021', 'currency': 'CHF',
        'fully_paid': True, 'security_kind': 'Namenaktien', 'previous_security_kind': 'Inhaberaktien',
        'transfer_restricted': True, 'communication': 'Brief, E-Mail oder Telefax'}
    legacy = Event('old', '', 'organization_changed', 'old', payload={'action': 'bearer_to_registered_shares_statutes_changed'})
    assert Event(**vars(legacy)) == legacy
    assert 'transfer_restricted' not in legacy.payload and 'communication' not in legacy.payload
    text = calls[0][0]
    for changed in (text + ' unbekannt', text.replace('26.04.2021', '31.02.2021'), text.replace('Inhaberaktien', 'Namenaktien')):
        assert extract(changed, *ARGS) == ([], changed)
    assert extract(text, 'fr', *ARGS[1:]) == ([], text)


def test_old_rule_boundary(tmp_path):
    text = "Aktienkapital neu: CHF 75'000, vollständig liberiert, eingeteilt in 75 Namenaktien zu CHF 1'000 (Bisher: 75 Inhaberaktien zu CHF 1'000). Statuten geändert am 26.04.2021"
    assert extract_parser369_leftovers(text, *ARGS)[0]
    assert extract(text, *ARGS) == ([], text)
    tree = ET.parse(FIXTURE)
    next(tree.iter('publicationText')).text = text
    path = tmp_path / 'boundary.xml'
    tree.write(path, encoding='utf-8')
    with patch.object(parser, 'extract_parser586_leftovers', lambda value, *args: ([], value)):
        old = parser.parse_publication_xml(path)
    assert parser.parse_publication_xml(path) == old
