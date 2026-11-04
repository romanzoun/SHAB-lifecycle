import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser464 import extract_parser464_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = '''02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11
1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e
2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3
0ff08580133afd54acaab3b5fd3ec80e60b3d67318de5285ae0f9f0798be0957
3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232
7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad
88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7
8bb4f070db8be493d9d8774f0782f67efdbe36f44d408ddc67ebbdfbfb37152a
8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f
a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5
f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed
89ce6ac882c9cb489e7a27c564c70bcef445693584cf7ac4413b34ed9d8cc7cf'''.split()


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser464_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser464_leftovers', lambda text, *a, **kw: ([], text)):
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
    if index == 3:
        assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
        assert len(added) == 2 and rest == ''
        assert result.events == old.events + added
    else:
        assert (added, rest) == ([], args[0])
        assert result == old



def test_payload_and_optional_metadata():
    assert PARSER_VERSION == 477
    _, _, (args, kwargs) = captured(3)
    events, rest = extract(*args, **kwargs)
    assert rest == '' and len(events) == 2
    for event, name, origin, place in zip(events, ['Gillard Alexia', 'Peter Clarence'],
                                         ['Suscévaz', 'Collonge-Bellerive'],
                                         ['Genève', 'Collonge-Bellerive']):
        assert event.event_type == 'officer_changed'
        assert event.rule_id == 'fr.persons.two_board_members_missing_comma.v1'
        assert event.role == "membre du conseil d'administration"
        assert event.signing == 'Kollektivunterschrift zu zweien'
        assert event.payload == {'name': name, 'place': place, 'origin': origin, 'action': 'appointed'}
        assert Event(**vars(event)) == event
    optional, rest = extract(*args[:4], None, None, None, **kwargs)
    assert rest == ''
    assert [e.payload for e in optional] == [e.payload for e in events]
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in optional)
    assert extract(*args) == ([], args[0])  # No unsupported signing inference.


def test_reject_unknown_and_missing_context():
    _, _, (args, kwargs) = captured(3)
    for text in (args[0] + ' UNKNOWN', args[0].replace('de et à', 'de'), ''):
        assert extract(text, *args[1:], **kwargs) == ([], text)
    assert extract(args[0], 'de', *args[2:], **kwargs) == ([], args[0])
    for source in ('', kwargs['source_text'].replace('collective à deux', 'individuelle')):
        assert extract(*args, source_text=source) == ([], args[0])


def test_no_old_rule_consumes_new_formulation():
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(3)
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser464_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
        events, rest = old(*args, **options)
        assert not events and rest == args[0], name


def test_legacy_ownership_and_payload_compatibility():
    from shab_analyzer.parser165 import extract_parser165_leftovers
    _, _, (args, kwargs) = captured(3)
    canonical = args[0].replace('Genève et', 'Genève, et')
    legacy, rest = extract_parser165_leftovers(canonical, *args[1:])
    assert len(legacy) == 2 and rest == ''
    assert extract(canonical, *args[1:], **kwargs) == ([], canonical)
    new, _ = extract(*args, **kwargs)
    for before, after in zip(legacy, new):
        assert before.payload == after.payload
        assert before.signing == after.signing
        assert before.role == after.role
        assert Event(**vars(before)) == before


@pytest.mark.parametrize('fixture', [
    '582d7302-d679-4d95-8a33-7cd62d18a592',
    '61a7ccc3-fec7-4297-a7ba-918755662d7f',
    '8f8bac61-5c66-45c0-b97b-160405871bab',
    'e59a393c-855e-48e1-8072-feaf42425a13',
    'fb0f2927-d83e-4a87-bc75-b60907fcc3f4',
])
def test_legacy_pipeline_equal(fixture):
    import shab_analyzer.parse as parser
    path = FIXTURES / (fixture + '.xml')
    result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser464_leftovers', lambda text, *a, **kw: ([], text)):
        baseline = parse_publication_xml(path)
    assert result == baseline
