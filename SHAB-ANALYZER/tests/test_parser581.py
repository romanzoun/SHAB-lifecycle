import hashlib
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.models import Event
from shab_analyzer.parser95 import extract_parser95_leftovers
from shab_analyzer.parser581 import extract_parser581_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e',
 '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3',
 '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527',
 '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad',
 '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7',
 '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f',
 '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315',
 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5',
 'b2bea761b5ecbda0de30003f3654d2e7eeb57302fd46471fc98285d05aead4e8',
 'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176',
 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37',
 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = DIGESTS[1]
ARGS = ('fr', 'fixture', '', None, None, None)

@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


def test_pipeline_and_payload():
    calls = []
    def capture(*args):
        calls.append(args)
        return extract(*args)
    path = FIXTURES / (TARGET + '.xml')
    with patch.object(parser, 'extract_parser581_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser581_leftovers', lambda text, *args: ([], text)):
        old = parser.parse_publication_xml(path)
    added, rest = extract(*calls[0])
    remaining = list(result.events)
    for event in old.events + added:
        remaining.remove(event)
    assert rest.strip(' .').endswith(result.leftover_text)
    assert len(added) == 4
    assert all(e.event_type == 'officer_changed' for e in added)
    assert (added[0].payload['shares_before'], added[0].payload['shares_transferred'], added[0].payload['shares_count']) == (200, 150, 50)
    assert [e.payload['shares_received'] for e in added[1:]] == [50, 50, 50]
    assert added[0].role == 'président'
    assert added[1].signing is None
    assert all(e.signing == 'ohne Zeichnungsberechtigung' for e in added[2:])
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in extract(calls[0][0], *ARGS)[0])
    legacy = Event('old', '', 'officer_changed', 'old', payload={'name': 'Example'})
    assert Event(**vars(legacy)) == legacy and 'shares_received' not in legacy.payload
    for changed in (calls[0][0].replace('cède 150', 'cède 151'), calls[0][0] + ' autre'):
        assert extract(changed, *ARGS) == ([], changed)
    assert extract(calls[0][0], 'de', *ARGS[1:]) == ([], calls[0][0])


def test_legacy_rule_boundary(tmp_path):
    text = ('Alpha Jean cède 50 de ses 100 parts de CHF 100 à Beta Paul, de Genève, à Nyon, '
            'nouvel associé-gérant avec 50 parts de CHF 100; Alpha Jean, qui reste titulaire '
            'de 50 parts de CHF 100, est nommé président.')
    assert extract_parser95_leftovers(text, *ARGS)[0]
    assert extract(text, *ARGS) == ([], text)
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    next(tree.iter('publicationText')).text = text
    path = tmp_path / 'boundary.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser581_leftovers', lambda text, *args: ([], text)):
        assert result == parser.parse_publication_xml(path)
