import hashlib
import inspect
import re
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser534 import extract_parser534_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '3232f91a0eaa2f82ab179e227156ca3fe3b7d829795d94e5d4e76faf04becd98', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = "3232f91a0eaa2f82ab179e227156ca3fe3b7d829795d94e5d4e76faf04becd98"
ARGS = ('fr', 'fixture', '', None, None, None)


def source_text():
    return next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text


def target_text():
    source = source_text()
    return source[source.index('Nouvelle associée commanditaire'):]


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
    with patch.object(parser, 'extract_parser534_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser534_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert event.event_type == 'officer_changed'
    assert event.payload == {
        'name': 'Fondation du Groupe Pictet', 'place': 'Carouge (GE)',
        'action': 'appointed', 'uid': 'CHE-242.674.582',
        'limited_partnership_contribution': "30'000'000", 'currency': 'CHF',
    }
    assert event.role == 'associée commanditaire' and event.signing is None
    assert Event(**vars(event)) == event
    legacy = Event('old', '', 'officer_changed', 'legacy', payload={'name': 'Legacy'})
    assert Event(**vars(legacy)) == legacy
    assert 'limited_partnership_contribution' not in legacy.payload
    assert PARSER_VERSION == 548


def test_no_existing_rule_owns_target():
    text = target_text().rstrip('.')
    from shab_analyzer.text_extras import extract_text_extras
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser534_leftovers':
            continue
        options = {'source_text': source_text()} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('language', ['de', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


@pytest.mark.parametrize('before,after', [
    ('commanditaire', 'gérante'), ('CHE-242.674.582', '242.674.582'),
    ("30'000'000", '0'), ('commandite de:', 'commandite de'),
])
def test_unattested(before, after):
    text = target_text().replace(before, after)
    assert extract(text, *ARGS) == ([], text)


def test_context():
    events, _ = extract(target_text(), 'fr', 'pub', '2021', 'uid', '1000', 'FR')
    assert len(events) == 1
    assert (events[0].publication_id, events[0].published_at, events[0].org_uid,
            events[0].plz, events[0].canton) == ('pub', '2021', 'uid', '1000', 'FR')


@pytest.mark.parametrize('module,pattern_name,fixture_id', [
    ('parser120', '_FR_LIMITED_PARTNER_REDUCED_AND_ORGANIZATION_ADDED', '4200e936-3c30-4c39-82ca-fd305d5fdd48'),
    ('parser134', '_FR_NEW_LIMITED_PARTNER_WITH_PROCURATION', '7650d63a-e532-4e90-86f7-1520f17e80fc'),
    ('parser251', '_FR_LIMITED_PARTNER_REDUCED_AND_ORGANIZATION_ADDED', 'c55f3d0d-39ae-450c-af20-5a8cfa5d060c'),
])
def test_legacy_boundary(module, pattern_name, fixture_id):
    import importlib
    old_module = importlib.import_module('shab_analyzer.' + module)
    pattern = getattr(old_module, pattern_name)
    # Reuse the exact old fixture clauses rather than recreating their grammar.
    matches = []
    for fixture in [FIXTURES / (fixture_id + '.xml')]:
        root = ET.parse(fixture)
        node = next(root.iter('publicationText'), None)
        if node is None or not node.text:
            continue
        text = node.text
        for offset in [0] + [m.end() for m in re.finditer(r'\.\s+', text)]:
            clause = text[offset:]
            if pattern.fullmatch(clause):
                matches.append((fixture, clause))
                break
        if matches:
            break
    assert matches, pattern_name
    fixture, text = matches[0]
    assert getattr(old_module, 'extract_' + module + '_leftovers')(text, *ARGS)[0]
    assert extract(text, *ARGS, source_text=text) == ([], text)
    result = parser.parse_publication_xml(fixture)
    with patch.object(parser, 'extract_parser534_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parser.parse_publication_xml(fixture)
