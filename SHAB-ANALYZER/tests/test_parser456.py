import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch
import pytest
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser456 import extract_parser456_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed supplied SHA-256 filenames, verified when copying; no job directory needed.
DIGESTS = '''02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11
1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e
31bc228c95a083db1a4f10db79c75cd34ab0f92b45004c2eb04de53cc4a8079d
3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232
7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad
88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7
8bb4f070db8be493d9d8774f0782f67efdbe36f44d408ddc67ebbdfbfb37152a
8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f
a341287297ba96e1938916b070b26a6384cd05b7aad34facefaf830c80dd6cf8
a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5
f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed
f2a7b604634c8136c38995519179b5000a4071e23ca9e40e1b449c61bad98d26'''.split()

@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser456_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser456_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(path)
    assert len(calls) == 1
    return result, old, calls[0]

@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest

@pytest.mark.parametrize('index', range(12))
def test_pipeline_and_payload_preservation(index):
    result, old, (args, kwargs) = captured(index)
    added, rest = extract(*args, **kwargs)
    if index == 11:
        assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
        assert len(added) == 4 and rest == ''
        assert result.events == old.events + added
    else:
        assert extract(*args, **kwargs) == ([], args[0])
        assert result == old

def test_exact_events_and_version():
    assert PARSER_VERSION == 485
    _, _, (args, kwargs) = captured(11)
    events, rest = extract(*args, **kwargs)
    assert rest == ''
    assert [e.event_type for e in events] == ['officer_changed', 'signing_authority_changed'] * 2
    assert [e.role for e in events] == ['président'] * 2 + ['administrateur'] * 2
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in events)
    assert [e.payload for e in events] == [
        {'name': 'Dalloz Philippe', 'place': None},
        {'name': 'Dalloz Philippe', 'place': None},
        {'name': 'Donzé Damien Adrien', 'place': 'Les Breuleux', 'heimat': 'Les Breuleux'},
        {'name': 'Donzé Damien Adrien', 'place': 'Les Breuleux', 'heimat': 'Les Breuleux'},
    ]
    assert all(Event(**vars(e)) == e for e in events)

def test_missing_optional_fields():
    _, _, (args, kwargs) = captured(11)
    baseline, _ = extract(*args, **kwargs)
    events, rest = extract(*args[:4], None, None, None)
    assert rest == '' and len(events) == 4
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in baseline]
    event = Event('p', '', 'officer_changed', 'legacy.rule', payload={'name': 'Test Anna'})
    assert Event(**vars(event)) == event
    assert event.payload == {'name': 'Test Anna'}
    assert event.role is None and event.signing is None

def test_unknown_input():
    _, _, (args, kwargs) = captured(11)
    for text in (args[0] + '; UNKNOWN', args[0].replace('collectivement à deux', 'individuellement'),
                 args[0].replace('Adrien,', 'Adrien et Autre,', 1)):
        assert extract(text, *args[1:], **kwargs) == ([], text)
    assert extract(args[0], 'de', *args[2:], **kwargs) == ([], args[0])

def test_no_historical_owner_in_isolation():
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(11)
    for name, old_extract in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser456_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name

def test_legacy_deferred_and_pipeline_equal(tmp_path):
    from shab_analyzer.parser50 import _FR_ADMINISTRATION_PAIR
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(11)
    text = args[0].replace('de et à Les Breuleux', 'de Les Breuleux, à Les Breuleux')
    assert _FR_ADMINISTRATION_PAIR.search(text)
    assert extract(text, *args[1:], **kwargs) == ([], text)
    data = (FIXTURES / (DIGESTS[11] + '.xml')).read_text()
    path = tmp_path / 'legacy.xml'
    path.write_text(data.replace('de et à Les Breuleux', 'de Les Breuleux, à Les Breuleux'))
    result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser456_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(path)
    assert result == old
