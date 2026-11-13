import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser490 import extract_parser490_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'c168522337af391de5b24362690932f1c08366b90fff3b05d487cf4775c56ed1', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser490_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser490_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert PARSER_VERSION == 543
    _, _, (args, kwargs) = captured(10)
    events, rest = extract(*args, **kwargs)
    assert len(events) == 1 and rest == ''
    event = events[0]
    assert event.event_type == 'statutes_changed'
    assert event.payload == {
        'kind': 'asset_acquisition_intention_clause', 'action': 'currency_corrected',
        'asset': '2 prototipi di diffusori e 1 prototipo di satellite realizzati per la diffusione aerea di probiotici',
        'currency': 'EUR', 'price': "55'000.00", 'previous_incorrect_currency': 'CHF',
    }
    assert Event(**vars(event)) == event
    sparse, _ = extract(*args[:4], None, None, None)
    assert sparse[0].payload == event.payload
    assert (sparse[0].org_uid, sparse[0].plz, sparse[0].canton) == (None, None, None)
    assert extract(*args) == (events, rest)
    legacy = Event('legacy', '', 'statutes_changed', 'legacy', payload={
        'kind': 'asset_acquisition_intention_clause', 'action': 'price_corrected',
        'currency': 'EUR', 'price': "3'900'000.00",
    })
    assert Event(**vars(legacy)) == legacy
    assert 'previous_incorrect_currency' not in legacy.payload


def test_no_old_rule_owns_input():
    import shab_analyzer.parse as parser
    from shab_analyzer.text_extras import extract_text_extras
    _, _, (args, kwargs) = captured(10)
    assert extract_text_extras(*args, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser490_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
        assert old(*args, **options) == ([], args[0]), name


@pytest.mark.parametrize('transform', [
    lambda t: '', lambda t: t + ' UNKNOWN',
    lambda t: t.replace('EUR', 'CHF'), lambda t: t.replace('EUR', 'USD'),
    lambda t: t.replace('CHF', 'EUR'),
    lambda t: t.replace("CHF 55'000.00", "CHF 56'000.00"),
    lambda t: t.replace('[no:', '[non:'),
    lambda t: t.replace('acquistare 2', 'acquistare 3', 1),
])
def test_unsupported_input(transform):
    _, _, (args, kwargs) = captured(10)
    text = transform(args[0])
    assert extract(text, *args[1:], **kwargs) == ([], text)


@pytest.mark.parametrize('language', ['fr', 'de', None])
def test_other_languages(language):
    _, _, (args, kwargs) = captured(10)
    assert extract(args[0], language, *args[2:], **kwargs) == ([], args[0])


def test_legacy_boundary():
    import shab_analyzer.parse as parser
    from shab_analyzer.parser171 import _IT_ASSET_ACQUISITION_PRICE_CORRECTED, extract_parser171_leftovers
    from xml.etree import ElementTree
    path = FIXTURES / 'd7731c7d-da5c-47ae-abfa-f96288bca09b.xml'
    text = next(ElementTree.parse(path).iter('publicationText')).text
    # Capture the exact residue delivered to the old rule by the real pipeline.
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser171_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser171_leftovers', capture):
        result = parse_publication_xml(path)
    args, kwargs = calls[0]
    assert _IT_ASSET_ACQUISITION_PRICE_CORRECTED.fullmatch(args[0])
    assert extract_parser171_leftovers(*args, **kwargs)[0]
    assert extract(*args) == ([], args[0])
    assert extract(text, 'it', 'legacy', '', None, None, None) == ([], text)
    with patch.object(parser, 'extract_parser490_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(path)
