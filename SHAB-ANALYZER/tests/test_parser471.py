import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser471 import extract_parser471_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '89ce6ac882c9cb489e7a27c564c70bcef445693584cf7ac4413b34ed9d8cc7cf', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'e1763e067158f0b15031b25c0eca39349327325113e6b0be8af200f011246857', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser471_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser471_leftovers', lambda text, *a, **kw: ([], text)):
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
    if index == 10:
        assert len(added) == 1
        assert result.events == old.events + added
        assert result.leftover_text == rest.strip(' .')
    else:
        assert (added, rest) == ([], args[0])
        assert result == old


def test_payload_and_missing_optional_metadata():
    assert PARSER_VERSION == 482
    _, _, (args, kwargs) = captured(10)
    events, rest = extract(*args, **kwargs)
    event, = events
    assert rest == ''
    assert event.event_type == 'organization_changed'
    assert event.rule_id == 'de.text.purpose_register_error_corrected.v1'
    assert event.payload == {
        'action': 'purpose_register_error_corrected', 'entry': '2359',
        'entry_date': '15.03.2021', 'register_place': 'Luzern',
        'correction_entry': '2513', 'correction_date': '18.03.2021'}
    assert Event(**vars(event)) == event
    sparse, _ = extract(*args[:4], None, None, None, **kwargs)
    assert sparse[0].payload == event.payload
    assert sparse[0].org_uid is None and sparse[0].plz is None and sparse[0].canton is None
    legacy = Event(publication_id='legacy', published_at='', event_type='organization_changed',
                   rule_id='legacy', payload={'action': 'legacy'})
    assert Event(**vars(legacy)) == legacy


def test_no_old_rule_consumes_new_residue():
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(10)
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser471_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
        events, rest = old(*args, **options)
        assert not events and rest == args[0], name


def test_unsupported_input_unchanged():
    _, _, (args, kwargs) = captured(10)
    for text in ('', args[0] + ' UNKNOWN', '[' + args[0] + ']',
                 args[0].replace('15.03.2021', '31.02.2021'),
                 args[0].replace('18.03.2021', '31.02.2021'),
                 args[0].replace('Handelsregisters Luzern', 'Handelsregisters Bern'),
                 args[0].replace('berichtigt', 'bestätigt')):
        assert extract(text, *args[1:], **kwargs) == ([], text)
    assert extract(args[0], 'fr', *args[2:], **kwargs) == ([], args[0])
    assert extract(*args) == extract(*args, **kwargs)


@pytest.mark.parametrize('number,prefix', [(306, 'a6c94c7d'), (393, '2a794bcc'),
                                           (444, '568ac0c8'), (444, '703670ac'),
                                           (444, '9dc333c9')])
def test_old_rules_keep_ownership(number, prefix):
    import shab_analyzer.parse as parser
    old = getattr(parser, f'extract_parser{number}_leftovers')
    path, = FIXTURES.glob(prefix + '*.xml')
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return old(*args, **kwargs)
    with patch.object(parser, f'extract_parser{number}_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser471_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(path)
    assert any(old(*args, **kwargs)[0] for args, kwargs in calls)
    for args, kwargs in calls:
        assert extract(*args, **kwargs) == ([], args[0])
