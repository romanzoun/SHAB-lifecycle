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
from shab_analyzer.parser540 import extract_parser540_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02a5c24a5135642ea2cb6bc0d205a8179af2127e9976aa96e924957682a3fe04', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = DIGESTS[0]
ARGS = ('de', 'fixture', '', None, None, None)


@lru_cache(maxsize=1)
def source_text():
    return next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text


@lru_cache(maxsize=1)
def target_text():
    calls = []
    with patch.object(parser, 'extract_parser540_leftovers',
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
    with patch.object(parser, 'extract_parser540_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser540_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert len(events) == 1 and rest == ''
    event = events[0]
    assert event.event_type == 'assets_transferred'
    assert event.payload == {
        'source_kind': 'gesellschaft', 'agreement_date': '2021-04-09',
        'inventory_date': '2021-03-31', 'assets': "5'857'516.00",
        'liabilities': "4'539'968.00", 'liabilities_kind': 'third_party_capital',
        'currency': 'CHF', 'recipient': 'Kimberly-Clark Switzerland GmbH',
        'recipient_place': 'Solothurn', 'recipient_canton': None,
        'recipient_uid': 'CHE-290.491.446', 'consideration': "1'317'548.00",
        'consideration_kind': 'held_share_nominal_increase',
        'nominal_before': "20'000.00", 'nominal_increase': "1'317'548.00",
        'nominal_after': "1'337'548.00",
    }
    assert event.org_uid is None and event.signing is None
    assert Event(**vars(event)) == event
    legacy = Event(publication_id='old', published_at='', event_type='assets_transferred',
                   rule_id='old', payload={'consideration': '100'})
    assert Event(**vars(legacy)) == legacy
    assert 'nominal_before' not in legacy.payload
    assert PARSER_VERSION >= 540
    assert extract(target_text(), *ARGS, source_text=source_text()) == (events, rest)


@pytest.mark.parametrize('before,after', [
    ('herauf', 'herab'), ("5'857'516.00", '1.2.3'), ("1'337'548.00", "1'337'549.00"),
    ('09.04.2021', '31.02.2021'), ('gehaltenen Stammanteils', 'verkauften Stammanteils'),
])
def test_unsupported_unchanged(before, after):
    text = target_text().replace(before, after)
    assert extract(text, *ARGS) == ([], text)


@pytest.mark.parametrize('language', ['it', 'fr', None])
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
        if not name.startswith('extract_parser') or name == 'extract_parser540_leftovers':
            continue
        options = {'source_text': source_text()} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


def test_legacy_boundary(tmp_path):
    from shab_analyzer.parser155 import extract_parser155_leftovers
    text = target_text().split('Als Gegenleistung setzt die ', 1)[0] + 'Gegenleistung: CHF 100'
    assert extract_parser155_leftovers(text, *ARGS)[0]
    assert extract(text, *ARGS) == ([], text)
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    node = next(tree.iter('publicationText'))
    node.text = node.text.split('Als Gegenleistung setzt die ', 1)[0] + 'Gegenleistung: CHF 100.'
    path = tmp_path / 'legacy.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser540_leftovers', lambda text, *a, **kw: ([], text)):
        assert parser.parse_publication_xml(path) == result


def test_context_is_preserved():
    events, _ = extract(target_text(), 'de', 'pub', '2021', 'uid', '1000', 'TI')
    assert len(events) == 1
    event = events[0]
    assert (event.publication_id, event.published_at, event.org_uid, event.plz, event.canton) == (
        'pub', '2021', 'uid', '1000', 'TI')

