import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser538 import extract_parser538_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '4eb4bf7e2d93de94b9e5e70b35b17ed92bbd6ce51b1b6b265f25e5474edc4d7d', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = "4eb4bf7e2d93de94b9e5e70b35b17ed92bbd6ce51b1b6b265f25e5474edc4d7d"
ARGS = ('fr', 'fixture', '', None, None, None)


@lru_cache(maxsize=1)
def source_text():
    return next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text


@lru_cache(maxsize=1)
def target_text():
    calls = []
    with patch.object(parser, 'extract_parser538_leftovers',
                      lambda text, *a, **kw: (calls.append(text) or [], text)):
        parser.parse_publication_xml(FIXTURES / (TARGET + '.xml'))
    return calls[0]


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', DIGESTS)
def test_pipeline_preserves_existing_results(digest):
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (digest + '.xml')
    with patch.object(parser, 'extract_parser538_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser538_leftovers', lambda text, *a, **kw: ([], text)):
        old = parser.parse_publication_xml(path)
    assert len(calls) == 1
    added, rest = extract(*calls[0][0], **calls[0][1])
    remaining = list(result.events)
    for event in old.events + added:
        remaining.remove(event)
    if digest == TARGET:
        assert len(added) == 1
        assert rest.strip(' .').endswith(result.leftover_text)
        assert old.events
    else:
        assert added == []
        assert result == old


def test_payload_and_missing_optional_attributes():
    events, rest = extract(target_text(), *ARGS)
    assert rest == '' and len(events) == 1
    event = events[0]
    assert event.event_type == 'capital_changed'
    assert event.payload == dict(kind='share_structure', action='corrected', currency='CHF',
        shares_count=125100, share_nominal='1', share_kind='actions nominatives',
        previous_shares_count=125000, previous_share_nominal='1', entry='6384',
        entry_date='2021-03-30', notice_date='2021-04-06', notice_ref='0/1005141453')
    assert event.signing is None
    assert (event.org_uid, event.plz, event.canton) == (None, None, None)
    assert Event(**vars(event)) == event
    legacy = Event(publication_id='old', published_at='', event_type='capital_changed',
                   rule_id='old', payload={'kind': 'share_structure', 'action': 'corrected'})
    assert Event(**vars(legacy)) == legacy
    assert PARSER_VERSION >= 538
    assert extract(target_text(), *ARGS, source_text=source_text()) == (events, rest)


@pytest.mark.parametrize('before,after', [
    ("125'100", '0'), ('CHF 1', 'CHF 0'), ('30.03.2021', '31.02.2021'),
    ('06.04.2021', '99.04.2021'), ('actions nominatives', 'actions au porteur'),
])
def test_unsupported_unchanged(before, after):
    text = target_text().replace(before, after)
    assert extract(text, *ARGS) == ([], text)


@pytest.mark.parametrize('language', ['de', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


def test_unknown():
    for text in ('', 'UNKNOWN', target_text() + ' UNKNOWN'):
        assert extract(text, *ARGS) == ([], text)


def test_no_old_rule_owns_target():
    text = target_text()
    from shab_analyzer.text_extras import extract_text_extras
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser538_leftovers':
            continue
        options = {'source_text': source_text()} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('version,digest', [
    (116, 'e06f5076-699b-4945-b5c2-8bdb1989f2f1'),
    (162, '103bc43c-8d9b-4803-a71c-77c849a0e5d5'),
    (202, '60e9ec7a-fb1c-4f6d-a7c1-a6da15085ea9'),
])

def test_legacy_boundary(version, digest):
    # Capture the historical rule input; assert only relative pipeline behavior.
    calls = []
    name = 'extract_parser' + str(version) + '_leftovers'
    old = getattr(parser, name)
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return old(*args, **kwargs)
    path = FIXTURES / (digest + '.xml')
    with patch.object(parser, name, capture):
        result = parser.parse_publication_xml(path)
    args, kwargs = calls[0]
    assert old(*args, **kwargs)[0]
    assert extract(*args, **kwargs) == ([], args[0])
    with patch.object(parser, 'extract_parser538_leftovers', lambda text, *a, **kw: ([], text)):
        assert parser.parse_publication_xml(path) == result


def test_context_is_preserved():
    events, _ = extract(target_text(), 'fr', 'pub', '2021', 'uid', '1000', 'VD')
    assert len(events) == 1
    for event in events:
        assert (event.publication_id, event.published_at, event.org_uid, event.plz, event.canton) == (
            'pub', '2021', 'uid', '1000', 'VD')


def test_complete_clause_retains_same_correction_payload():
    # The pipeline already emits the transfer-restriction event before this rule.
    raw = source_text().split('Rectificatif:', 1)[1]
    raw = 'Rectificatif:' + raw
    assert extract(raw, *ARGS) == extract(target_text(), *ARGS)
