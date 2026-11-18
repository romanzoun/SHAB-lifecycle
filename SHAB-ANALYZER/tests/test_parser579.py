import hashlib
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.models import Event
from shab_analyzer.parser181 import extract_parser181_leftovers
from shab_analyzer.parser579 import extract_parser579_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = [
    '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e',
    '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3',
    '3072d1efd40242275d6dc6dbbe09179df430cd26479ed2122e52be2655a2180a',
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
ARGS = ('de', 'fixture', '', None, None, None)


@pytest.mark.parametrize('digest', DIGESTS)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', DIGESTS)
def test_preserves_existing_results(digest):
    path = FIXTURES / (digest + '.xml')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser579_leftovers', lambda text, *a: ([], text)):
        old = parser.parse_publication_xml(path)
    remaining = list(result.events)
    for event in old.events:
        remaining.remove(event)
    if digest == TARGET:
        added, rest = extract(old.leftover_text, old.language, old.publication_id,
                              old.published_at, old.org_uid, old.plz, old.canton)
        assert len(added) == 1
        assert all(event in result.events for event in added)
        assert rest.endswith(result.leftover_text)
    else:
        assert result == old


def test_duration_event_and_legacy_metadata():
    events, rest = extract('Dauer der Gesellschaft neu: maximal Ende 2024.', *ARGS)
    assert not rest and len(events) == 1
    event = events[0]
    assert event.event_type == 'organization_changed'
    assert event.payload == {'kind': 'company_duration', 'action': 'changed',
                             'until_year': 2024, 'maximum_end_of_year': True}
    assert (event.org_uid, event.plz, event.canton) == (None, None, None)
    assert Event(**vars(event)) == event
    legacy = Event('old', '', 'organization_changed', 'old', payload={
        'kind': 'company_duration', 'action': 'changed', 'until_year': 2035,
        'extension_unlimited': True, 'maximum_extension_years': 3,
        'maximum_extension_years_raw': 'drei'})
    assert Event(**vars(legacy)) == legacy


def test_old_duration_boundary(tmp_path):
    text = 'Dauer der Gesellschaft neu: Bis 2035 mit unbeschränkter Verlängerungsmöglichkeit um jeweils höchstens drei Jahre.'
    assert extract_parser181_leftovers(text, *ARGS)[0]
    assert extract(text, *ARGS) == ([], text)
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    next(tree.iter('publicationText')).text = text
    path = tmp_path / 'boundary.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser579_leftovers', lambda text, *a: ([], text)):
        assert result == parser.parse_publication_xml(path)


@pytest.mark.parametrize('text,language', [
    ('Dauer der Gesellschaft neu: Ende 2024', 'de'),
    ('Dauer der Gesellschaft neu: maximal Ende 2024 mit Verlängerung', 'de'),
    ('Dauer der Gesellschaft neu: maximal Ende 2024', 'fr'),
])
def test_unsupported(text, language):
    assert extract(text, language, *ARGS[1:]) == ([], text)
