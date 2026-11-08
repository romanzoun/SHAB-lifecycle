import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser469 import extract_parser469_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '89ce6ac882c9cb489e7a27c564c70bcef445693584cf7ac4413b34ed9d8cc7cf', '8bb4f070db8be493d9d8774f0782f67efdbe36f44d408ddc67ebbdfbfb37152a', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser469_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser469_leftovers', lambda text, *a, **kw: ([], text)):
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
    if index == 9:
        assert len(added) == 1
        assert result.events == old.events + added
        assert result.leftover_text == rest.strip(' .')
        assert rest and args[0].startswith(rest)
    else:
        assert (added, rest) == ([], args[0])
        assert result == old


def test_payload_and_missing_optional_metadata():
    assert PARSER_VERSION == 503
    _, _, (args, kwargs) = captured(9)
    events, _ = extract(*args, **kwargs)
    event, = events
    assert event.event_type == 'organization_changed'
    assert event.rule_id == 'fr.text.contribution_in_kind_disposition_repealed.v1'
    assert event.payload == {'action': 'contribution_in_kind_clause_repealed',
                             'legal_basis': 'article 628 al. 4 CO'}
    assert Event(**vars(event)) == event
    sparse, _ = extract(*args[:4], None, None, None)
    assert sparse[0].payload == event.payload
    assert sparse[0].org_uid is None and sparse[0].plz is None and sparse[0].canton is None
    assert sparse[0].person_key is None and sparse[0].role is None and sparse[0].signing is None
    legacy = Event(publication_id='legacy', published_at='', event_type='organization_changed',
                   rule_id='legacy', payload={'action': 'contribution_in_kind_clause_repealed'})
    assert Event(**vars(legacy)) == legacy


def test_no_old_rule_consumes_new_sentence():
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(9)
    sentence = args[0][args[0].index('La disposition statutaire'):]
    for text in (args[0], sentence):
        for name, old in vars(parser).items():
            if not name.startswith('extract_parser') or name == 'extract_parser469_leftovers':
                continue
            options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
            events, rest = old(text, *args[1:], **options)
            assert not events and rest == text, name


def test_unsupported_input_unchanged():
    _, _, (args, kwargs) = captured(9)
    sentence = args[0][args[0].index('La disposition statutaire'):]
    for text in ('', sentence + ' UNKNOWN', '[' + sentence + ']',
                 sentence.replace('apport en nature', 'reprise de biens'),
                 sentence.replace('628', '634'),
                 sentence.replace('est abrogée', 'sera abrogée'),
                 sentence.replace('La disposition', 'La clause'),
                 sentence.replace("l'article", "l'art.")):
        assert extract(text, *args[1:], **kwargs) == ([], text)
    assert extract(sentence, 'de', *args[2:]) == ([], sentence)
    events, rest = extract(sentence, *args[1:])
    assert len(events) == 1 and rest == ''


def test_old_rule_keeps_ownership():
    import shab_analyzer.parse as parser
    path, = FIXTURES.glob('433558ba*.xml')
    calls = []
    old_extract = parser.extract_parser332_leftovers
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return old_extract(*args, **kwargs)
    with patch.object(parser, 'extract_parser332_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser469_leftovers', lambda text, *a, **kw: ([], text)):
        baseline = parse_publication_xml(path)
    assert result == baseline
    (args, kwargs), = calls
    assert old_extract(*args, **kwargs)[0]
    assert extract(*args, **kwargs) == ([], args[0])
