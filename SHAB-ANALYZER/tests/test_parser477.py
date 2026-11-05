import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser477 import extract_parser477_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '89ce6ac882c9cb489e7a27c564c70bcef445693584cf7ac4413b34ed9d8cc7cf', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'dcf068e2c8a91adb25e8663e831a119dbae0d3d4f437736862d0309be1eeb047', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser477_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser477_leftovers', lambda text, *a, **kw: ([], text)):
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
    else:
        assert (added, rest) == ([], args[0])
        assert result == old


def test_payload_and_missing_optional_metadata():
    assert PARSER_VERSION == 484
    _, _, (args, kwargs) = captured(9)
    events, rest = extract(*args, **kwargs)
    assert rest == '' and len(events) == 1
    event = events[0]
    assert event.event_type == 'company_merged'
    assert event.rule_id == 'it.text.merger_all_social_quotas_no_capital_increase.v1'
    assert event.payload == {
        'absorbed_name': 'La STANDA - Grandi Magazzini Sagl', 'absorbed_place': 'Lugano',
        'absorbed_uid': 'CHE-106.842.021', 'agreement_date': '2021-04-06',
        'balance_date': '2021-03-31', 'assets': "273'301.92", 'liabilities': "14'709.04",
        'currency': 'CHF', 'ownership_interests': 'quote sociali',
        'all_interests_held_by_acquirer': True, 'capital_increase': False, 'shares_allocated': False,
    }
    assert Event(**vars(event)) == event
    sparse, _ = extract(*args[:4], None, None, None)
    assert sparse[0].payload == event.payload
    assert sparse[0].org_uid is None and sparse[0].plz is None and sparse[0].canton is None
    assert extract(*args) == (events, rest)
    legacy = Event('legacy', '', 'company_merged', 'legacy', payload={})
    assert Event(**vars(legacy)) == legacy
    assert 'ownership_interests' not in legacy.payload


def test_no_old_extractor_already_owns_new_input():
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(9)
    from shab_analyzer.text_extras import extract_text_extras
    # Generic cleanup removes a prefix without emitting a merger event.
    assert extract_text_extras(*args, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser477_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
        assert old(*args, **options) == ([], args[0]), name


def test_unsupported_input_unchanged():
    _, _, (args, kwargs) = captured(9)
    for text in ('', args[0] + ' UNKNOWN', '[' + args[0] + ']',
                 args[0].replace('quote sociali', 'azioni'),
                 args[0].replace('06.04.2021', '31.02.2021')):
        assert extract(text, *args[1:], **kwargs) == ([], text)
    for language in ('de', 'fr', 'en', None):
        assert extract(args[0], language, *args[2:], **kwargs) == ([], args[0])


def test_legacy_ownership():
    from shab_analyzer.parser236 import extract_parser236_leftovers as old
    _, _, (args, kwargs) = captured(9)
    text = args[0].replace('senza aumento del capitale', 'senza aumento di capitale')
    expected = old(text, *args[1:])
    assert expected[0]
    assert extract(text, *args[1:], **kwargs) == ([], text)
    assert old(extract(text, *args[1:], **kwargs)[1], *args[1:]) == expected


def test_legacy_pipeline_relative():
    import shab_analyzer.parse as parser
    path = FIXTURES / '65e8e020-4eb4-4639-b18b-916bcf97e8f3.xml'
    result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser477_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(path)
