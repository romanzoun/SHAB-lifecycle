import hashlib
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser202 import extract_parser202_leftovers
from shab_analyzer.parser313 import extract_parser313_leftovers
from shab_analyzer.parser585 import extract_parser585_leftovers as extract

DIGEST = 'ee040c13b0f3bd26aa9ade467b9d21581c6dd953d484561c62e277a4fc766f2b'
FIXTURE = Path(__file__).parent / 'fixtures' / (DIGEST + '.xml')
ARGS = ('de', 'fixture', '', None, None, None)


def test_fixture_integrity():
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == DIGEST
    assert PARSER_VERSION == 585


def test_pipeline_and_payload():
    calls = []
    def capture(*args):
        calls.append(args)
        return extract(*args)
    with patch.object(parser, 'extract_parser585_leftovers', capture):
        result = parser.parse_publication_xml(FIXTURE)
    with patch.object(parser, 'extract_parser585_leftovers', lambda text, *args: ([], text)):
        old = parser.parse_publication_xml(FIXTURE)
    added, rest = extract(*calls[0])
    remaining = list(result.events)
    for event in old.events + added:
        remaining.remove(event)
    assert rest.endswith(result.leftover_text)
    assert len(added) == 1
    event = added[0]
    assert event.event_type == 'organization_changed'
    assert event.payload == {'action': 'expired_authorized_capital_replaced',
                             'authorization_date': '24.04.2018', 'resolution_date': '20.04.2021'}
    legacy = Event('old', '', 'organization_changed', 'old', payload={'action': 'example'})
    assert Event(**vars(legacy)) == legacy
    assert 'authorization_date' not in legacy.payload
    text = calls[0][0]
    for changed in (text + ' unbekannt', text.replace('Fristablauf', 'Ausschöpfung'),
                    text.replace('24.04.2018', '31.02.2018')):
        assert extract(changed, *ARGS) == ([], changed)
    assert extract(text, 'fr', *ARGS[1:]) == ([], text)


def test_old_rules_boundary(tmp_path):
    texts = [
        ('[Streichung der Statutenbestimmung über die mit Ermächtigungsbeschluss vom 24.04.2018 eingeführte genehmigte Kapitalerhöhung infolge Fristablauf.] . Die Gesellschaft hat mit Beschluss vom 20.04.2021 eine genehmigte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten beschlossen', extract_parser313_leftovers),
        ('Die Gesellschaft hat mit Beschluss vom 20.04.2021 eine genehmigte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten beschlossen', extract_parser202_leftovers),
    ]
    for index, (text, old_extractor) in enumerate(texts):
        assert old_extractor(text, *ARGS)[0]
        assert extract(text, *ARGS) == ([], text)
        tree = ET.parse(FIXTURE)
        next(tree.iter('publicationText')).text = text
        path = tmp_path / f'boundary{index}.xml'
        tree.write(path, encoding='utf-8')
        with patch.object(parser, 'extract_parser585_leftovers', lambda value, *args: ([], value)):
            old = parser.parse_publication_xml(path)
        assert parser.parse_publication_xml(path) == old
