import hashlib
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.models import Event
from shab_analyzer.parser91 import extract_parser91_leftovers
from shab_analyzer.parser580 import extract_parser580_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = [
    '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e',
    '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3',
    '44435c19f6ac21bbdb3abf1645af87418d5925d87df5cecb9ac3d736cc82a45d',
    '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527',
    '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad',
    '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7',
    '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f',
    '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315',
    'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5',
    'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176',
    'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37',
    'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed',
]
TARGET = DIGESTS[2]
ARGS = ('fr', 'fixture', '', None, None, None)


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', DIGESTS)
def test_existing_pipeline_results(digest):
    path = FIXTURES / (digest + '.xml')
    calls = []
    def capture(*args):
        calls.append(args)
        return extract(*args)
    with patch.object(parser, 'extract_parser580_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser580_leftovers', lambda text, *a: ([], text)):
        old = parser.parse_publication_xml(path)
    added, rest = extract(*calls[0])
    remaining = list(result.events)
    for event in old.events + added:
        remaining.remove(event)
    if digest == TARGET:
        assert len(added) == 3
        assert rest.strip(' .').endswith(result.leftover_text)
    else:
        assert result == old


def target_text():
    calls = []
    with patch.object(parser, 'extract_parser580_leftovers', lambda text, *a: (calls.append(text) or [], text)):
        parser.parse_publication_xml(FIXTURES / (TARGET + '.xml'))
    return calls[0]


def test_payload_and_legacy_metadata():
    events, rest = extract(target_text(), *ARGS)
    assert rest == '' and len(events) == 3
    seller, first, second = events
    assert all(e.event_type == 'officer_changed' for e in events)
    assert (seller.payload['shares_before'], seller.payload['shares_transferred'], seller.payload['shares_count']) == (19, 8, 11)
    assert first.payload['shares_received'] == second.payload['shares_received'] == 4
    assert first.signing is None and second.signing == 'Einzelunterschrift'
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    legacy = Event('old', '', 'officer_changed', 'old', payload={'name': 'Example'})
    assert Event(**vars(legacy)) == legacy
    assert 'shares_received' not in legacy.payload


@pytest.mark.parametrize('change', [lambda s: s.replace('cède 8', 'cède 9'),
    lambda s: s.replace('reste titulaire de 11', 'reste titulaire de 12'),
    lambda s: s.replace('signature individuelle', 'signature collective'),
    lambda s: s + ' autre'])
def test_unsupported(change):
    text = change(target_text())
    assert extract(text, *ARGS) == ([], text)


def test_old_rule_boundary(tmp_path):
    text = ('Alpha Jean cède 8 de ses 19 parts de CHF 1000, par 4 parts de CHF 1000 '
            'à Beta Paul, de Genève, à Genève, et par 4 parts de CHF 1000 à Gamma Luc, '
            'de Nyon, à Nyon, nouveaux associés-gérants; Alpha Jean, qui reste titulaire '
            'de 11 parts de CHF 1000, est nommé président.')
    assert extract_parser91_leftovers(text, *ARGS)[0]
    assert extract(text, *ARGS) == ([], text)
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    next(tree.iter('publicationText')).text = text
    path = tmp_path / 'boundary.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser580_leftovers', lambda text, *a: ([], text)):
        assert result == parser.parse_publication_xml(path)
