import hashlib
import inspect
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser535 import extract_parser535_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '53ba9622d9779393ec18a970c29aa8e973e71275cf2abc91f5481382177b1fad', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = '53ba9622d9779393ec18a970c29aa8e973e71275cf2abc91f5481382177b1fad'
ARGS = ('fr', 'fixture', '', None, None, None)


def source_text():
    return next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text


def target_text():
    source = source_text()
    return source[source.index('Réunion des'):source.index(' Communication aux')]


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', DIGESTS)
def test_pipeline_preserves_existing_results(digest):
    path = FIXTURES / (digest + '.xml')
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    with patch.object(parser, 'extract_parser535_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser535_leftovers', lambda text, *a, **kw: ([], text)):
        old = parser.parse_publication_xml(path)
    assert len(calls) == 1
    added, rest = extract(*calls[0][0], **calls[0][1])
    remaining = list(result.events)
    for event in old.events + added:
        remaining.remove(event)
    if digest == TARGET:
        assert len(added) == 1
        assert rest.strip(' .').endswith(result.leftover_text)
    else:
        assert added == []
        assert result == old


def test_payload_and_missing_optional_attributes():
    events, rest = extract(target_text(), *ARGS)
    assert rest == '' and len(events) == 1
    event = events[0]
    assert event.event_type == 'organization_changed'
    assert event.rule_id == 'fr.text.registered_shares_consolidated_two_classes.v1'
    assert event.payload == {
        'action': 'registered_shares_consolidated',
        'previous_count': "10'000'000", 'previous_nominal': '0.01',
        'ordinary_count': "875'000", 'ordinary_nominal': '0.10',
        'voting_count': "625'000", 'voting_nominal': '0.02',
        'capital': "100'000", 'paid': "100'000",
    }
    assert (event.org_uid, event.plz, event.canton) == (None, None, None)
    assert Event(**vars(event)) == event
    legacy = Event('old', '', 'organization_changed', 'fr.text.registered_shares_consolidated.v1',
                   payload={'action': 'registered_shares_consolidated', 'previous_count': '100'})
    assert 'ordinary_count' not in legacy.payload
    assert 'voting_count' not in legacy.payload
    assert Event(**vars(legacy)) == legacy
    assert PARSER_VERSION == 551


def test_context():
    events, _ = extract(target_text(), 'fr', 'pub', '2021', 'uid', '1000', 'GE')
    assert len(events) == 1
    event = events[0]
    assert (event.publication_id, event.published_at, event.org_uid, event.plz, event.canton) == (
        'pub', '2021', 'uid', '1000', 'GE')


@pytest.mark.parametrize('language', ['de', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


@pytest.mark.parametrize('before,after', [
    ("10'000'000", "10'000'001"), ("875'000", "875'001"),
    ('0.02', '0.03'), ("100'000", '0'),
    ('concurrence de CHF 100', 'concurrence de CHF 101'),
    ('privilégiées quant au droit de vote', 'au porteur'),
    ('nominatives', 'au porteur'),
])
def test_unsupported_or_inconsistent(before, after):
    text = target_text().replace(before, after)
    assert text != target_text()
    assert extract(text, *ARGS) == ([], text)


def test_unknown_suffix():
    text = target_text() + ' UNKNOWN'
    assert extract(text, *ARGS) == ([], text)


def test_no_old_rule_owns_target():
    text = target_text().rstrip('.')
    from shab_analyzer.text_extras import extract_text_extras
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser535_leftovers':
            continue
        options = {'source_text': source_text()} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('module,stem', [
    ('parser302', 'dc1059db'),
    ('parser96', '89563831-2b91-48ca-b516-b16fdecfa657'),
    ('parser460', 'a341287297ba96e1938916b070b26a6384cd05b7aad34facefaf830c80dd6cf8'),
])
def test_legacy_boundary(module, stem):
    import importlib
    old = getattr(importlib.import_module('shab_analyzer.' + module), 'extract_' + module + '_leftovers')
    fixture, = FIXTURES.glob(stem + '*.xml')
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return [], args[0]
    with patch.object(parser, old.__name__, capture):
        parser.parse_publication_xml(fixture)
    args, kwargs = calls[0]
    assert old(*args, **kwargs)[0]
    assert extract(*args, **kwargs) == ([], args[0])
    result = parser.parse_publication_xml(fixture)
    with patch.object(parser, 'extract_parser535_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parser.parse_publication_xml(fixture)
