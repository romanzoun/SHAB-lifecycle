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
from shab_analyzer.parser542 import extract_parser542_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['2cef80fdadfde8aba62aea2c225629751aa80562fdec77ac0ca05b3393a3eaeb', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = DIGESTS[0]
ARGS = ('it', 'fixture', '', None, None, None)


@lru_cache(maxsize=1)
def source_text():
    return next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text


@lru_cache(maxsize=1)
def target_text():
    calls = []
    with patch.object(parser, 'extract_parser542_leftovers',
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
    with patch.object(parser, 'extract_parser542_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser542_leftovers', lambda text, *a, **kw: ([], text)):
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


def test_payload_and_legacy_schema():
    events, rest = extract(target_text(), *ARGS)
    assert len(events) == 1 and rest == ''
    event = events[0]
    assert event.event_type == 'capital_changed'
    assert event.payload == {
        'kind': 'conditional_capital_clause_modified', 'action': 'modified',
        'decision_date': '2021-04-19', 'original_decision_date': '2018-06-22',
        'details_in_statutes': True, 'nominal_amount_changed': True,
        'previous_entry_removed': True,
    }
    legacy = Event('legacy', '', 'capital_changed', 'legacy', payload={
        'kind': 'conditional_capital_clause_modified', 'action': 'modified',
        'decision_date': '2021-04-19', 'original_decision_date': '2018-06-22',
    })
    assert Event(**vars(legacy)) == legacy
    assert not legacy.payload.get('nominal_amount_changed', False)
    assert Event(**vars(event)) == event
    assert event.org_uid is None and event.signing is None
    assert PARSER_VERSION >= 542


@pytest.mark.parametrize('before,after', [
    ('nominale', 'autorizzato'), ('19.04.2021', '31.02.2021'),
    ('22.06.2018', '31.06.2018'), ('radiati:', 'attuale:'),
])
def test_unsupported(before, after):
    text = target_text().replace(before, after)
    assert text != target_text()
    assert extract(text, *ARGS) == ([], text)


@pytest.mark.parametrize('language', ['de', 'fr', None])
def test_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


def test_unknown():
    for text in ('', 'UNKNOWN', target_text().rstrip('.') + '. UNKNOWN'):
        assert extract(text, *ARGS) == ([], text)


def test_no_old_rule_owns_target():
    from shab_analyzer.text_extras import extract_text_extras
    text = target_text()
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser542_leftovers':
            continue
        options = {'source_text': source_text()} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('azionario', ['', ' azionario'])
def test_legacy_boundary(tmp_path, azionario):
    from shab_analyzer.parser74 import extract_parser74_leftovers
    text = ("L'assemblea generale ha introdotto una disposizione statutaria relativa "
            "all'aumento condizionale del capitale" + azionario +
            " mediante decisione del 19.04.2021. Per i dettagli vedi statuti.")
    assert extract_parser74_leftovers(text, *ARGS)[0]
    assert extract(text, *ARGS) == ([], text)
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    node = next(tree.iter('publicationText'))
    node.text = node.text.replace(target_text(), text)
    path = tmp_path / 'legacy.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser542_leftovers', lambda text, *a, **kw: ([], text)):
        assert parser.parse_publication_xml(path) == result


def test_legacy_introduction_payload_without_optional_attributes():
    from shab_analyzer.parser74 import extract_parser74_leftovers
    text = target_text().split('] ', 1)[1].split(' [radiati:', 1)[0]
    events, rest = extract_parser74_leftovers(text, *ARGS)
    assert rest == '' and len(events) == 1
    assert events[0].payload == {
        'kind': 'conditional_capital_clause', 'action': 'introduced',
        'decision_date': '2021-04-19', 'details_in_statutes': True,
    }
    assert Event(**vars(events[0])) == events[0]


def test_context():
    events, _ = extract(target_text(), 'it', 'pub', '2021', 'uid', '1000', 'TI')
    assert len(events) == 1
    e = events[0]
    assert (e.publication_id, e.published_at, e.org_uid, e.plz, e.canton) == ('pub', '2021', 'uid', '1000', 'TI')


def test_authorized_and_conditional_legacy_boundary():
    from shab_analyzer.parser304 import extract_parser304_leftovers
    path, = FIXTURES.glob('6e903ec0*.xml')
    calls = []
    def capture(text, *args, **kwargs):
        calls.append(text)
        return extract_parser304_leftovers(text, *args, **kwargs)
    with patch.object(parser, 'extract_parser304_leftovers', capture):
        result = parser.parse_publication_xml(path)
    assert len(calls) == 1
    assert extract(calls[0], *ARGS) == ([], calls[0])
    with patch.object(parser, 'extract_parser542_leftovers', lambda text, *a, **kw: ([], text)):
        assert parser.parse_publication_xml(path) == result
