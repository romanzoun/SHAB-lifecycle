import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser481 import extract_parser481_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '419f45ae520fe9cbf917b5efe9810f15761ce176b566a710d0beba46838c71a2', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '89ce6ac882c9cb489e7a27c564c70bcef445693584cf7ac4413b34ed9d8cc7cf', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser481_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser481_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(path)
    assert len(calls) == 1
    return result, old, calls[0]


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('index', range(12))
def test_pipeline_preserves_existing_events(index):
    result, old, (args, kwargs) = captured(index)
    added, rest = extract(*args, **kwargs)
    if index == 4:
        assert len(added) == 2
        later = list(result.events)
        for event in old.events + added:
            later.remove(event)
        own = {event.rule_id for event in added}
        assert all(event.rule_id not in own for event in later)
        assert rest.strip(' .').endswith(result.leftover_text)
    else:
        assert (added, rest) == ([], args[0])
        assert result == old


def test_payload_and_optional_metadata():
    assert PARSER_VERSION == 533
    _, _, (args, kwargs) = captured(4)
    events, rest = extract(*args, **kwargs)
    assert rest == '' and len(events) == 2
    assert [e.payload for e in events] == [
        {'name': 'Carneiro Rolim Esmeraldo Daniel', 'place': 'Lausanne',
         'action': 'two_new_committee_members_du_de', 'origin': 'Brésil'},
        {'name': 'Soto Emeline', 'place': 'Lausanne',
         'action': 'two_new_committee_members_du_de', 'origin': 'France'},
    ]
    for event in events:
        assert event.event_type == 'officer_changed'
        assert event.role == 'Mitglied des Vorstandes'
        assert event.signing == 'Kollektivunterschrift zu zweien'
        assert Event(**vars(event)) == event
    sparse, _ = extract(*args[:4], None, None, None, **kwargs)
    assert [e.payload for e in sparse] == [e.payload for e in events]
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in sparse)
    assert extract(*args) == ([], args[0])
    legacy = Event('legacy', '', 'officer_changed', 'legacy',
                   payload={'name': 'Example Person', 'place': None})
    assert Event(**vars(legacy)) == legacy
    assert 'origin' not in legacy.payload


def test_no_old_rule_owns_input():
    import shab_analyzer.parse as parser
    from shab_analyzer.text_extras import extract_text_extras
    _, _, (args, kwargs) = captured(4)
    assert extract_text_extras(*args, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser481_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
        assert old(*args, **options) == ([], args[0]), name


def test_unsupported_input():
    _, _, (args, kwargs) = captured(4)
    for text in ('', args[0] + '. UNKNOWN', args[0].replace('du Brésil', 'du'),
                 args[0].replace('à Lausanne', 'à')):
        assert extract(text, *args[1:], **kwargs) == ([], text)
    for language in ('de', 'it', None):
        assert extract(args[0], language, *args[2:], **kwargs) == ([], args[0])
    for source in ('', kwargs['source_text'].replace('collective à deux', 'individuelle'),
                   kwargs['source_text'].replace('Soto Emeline', 'Example Person')):
        assert extract(*args, source_text=source) == ([], args[0])


@pytest.mark.parametrize('name', [
    '492f86e8c9f21974a90722fd7fd1898304c335fdd062b86e09c77defd9758721.xml',
    'f5d91211934c81ced28582d1d0712becdbb5c62cc1c2c4b9185fa35a6d630b33.xml',
    '99dc1f14-86d0-4b3a-a17b-4922f9dc0136.xml',
    '93878dff-a998-430f-add1-26d3bb34784a.xml',
])
def test_old_fixtures_relative(name):
    import shab_analyzer.parse as parser
    path = FIXTURES / name
    result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser481_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(path)


def test_legacy_foreign_places_boundary():
    from shab_analyzer.parser372 import extract_parser372_leftovers as old
    pair = ('Example Anne, du Brésil, à Londres (Royaume-Uni), et '
            'Example Paul, de France, à Paris (France)')
    text = 'Nouveaux membres du comité : ' + pair
    source = 'Nouveaux membres du comité avec signature collective à deux: ' + pair + '.'
    args = ('fr', 'fixture', '', None, None, None)
    expected = old(text, *args, source_text=source)
    assert expected[0]
    assert extract(text, *args, source_text=source) == ([], text)
    assert old(extract(text, *args, source_text=source)[1], *args, source_text=source) == expected
