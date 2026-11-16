import hashlib
import inspect
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser570 import extract_parser570_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['83eb9d5710ceb237aea65e1a221fc246708ee1f4215ba90f57fddb3020c711e9', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = '83eb9d5710ceb237aea65e1a221fc246708ee1f4215ba90f57fddb3020c711e9'
ARGS = ('de', 'fixture', '', None, None, None)


def source_text():
    return next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text


def target_text():
    return 'Diese im Sinne ' + source_text().split('Diese im Sinne ', 1)[1].split(' [nicht:', 1)[0]


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
    with patch.object(parser, 'extract_parser570_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser570_leftovers', lambda text, *a, **kw: ([], text)):
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


def test_payload_and_optional_metadata():
    events, rest = extract(target_text(), 'de', 'pub', '2021', 'uid', '4104', 'BL')
    assert rest == '' and len(events) == 1
    event = events[0]
    assert event.event_type == 'status_changed'
    assert event.rule_id == 'de.text.court_decision_official_deletion_reinstated.v1'
    assert event.payload == {
        'action': 'reinstatement', 'legal_basis': 'Art. 159 Abs. 5 HRegV',
        'authority': 'Gerichtspräsidenten des Zivilkreisgerichts Basel-Landschaft West',
        'deletion_date': '2021-01-28', 'decision_date': '2021-03-08',
    }
    assert (event.publication_id, event.published_at, event.org_uid,
            event.plz, event.canton) == ('pub', '2021', 'uid', '4104', 'BL')
    assert Event(**vars(event)) == event
    sparse = extract(target_text(), *ARGS)[0][0]
    assert sparse.payload == event.payload
    assert (sparse.org_uid, sparse.plz, sparse.canton) == (None, None, None)
    for legacy in (Event('pub', '', 'status_changed', 'legacy'),
                   Event('pub', '', 'status_changed', 'legacy', payload={'action': 'reinstatement'})):
        assert Event(**vars(legacy)) == legacy
        assert 'authority' not in legacy.payload
    assert PARSER_VERSION >= 570


def test_no_existing_rule_owns_new_clause():
    from shab_analyzer.text_extras import extract_text_extras
    text = target_text().removesuffix('.')
    assert extract_text_extras(text, *ARGS, set()) == ([], text)
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser570_leftovers':
            continue
        options = {'source_text': source_text()} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('change', [
    lambda t: '', lambda t: t + ' UNKNOWN_SUFFIX.',
    lambda t: 'Unbekannt. ' + t,
    lambda t: t.replace('eingetragen', 'gelöscht'),
    lambda t: t.replace('aufgrund des Entscheids', 'aufgrund des Urteils'),
    lambda t: t.replace('28.01.2021', '32.01.2021'),
    lambda t: t.replace('08.03.2021', '31.02.2021'),
])
def test_unsupported_input_unchanged(change):
    text = change(target_text())
    assert extract(text, *ARGS) == ([], text)


@pytest.mark.parametrize('language', ['fr', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


def test_whitespace_and_optional_period():
    expected = extract(target_text(), *ARGS)
    assert extract('  ' + target_text() + '  ', *ARGS) == expected
    assert extract(target_text().removesuffix('.'), *ARGS) == expected


@pytest.mark.parametrize('number,prefix', [(342, 'fb6010b5'), (376, '5cd02639')])
def test_legacy_rule_boundary(number, prefix):
    path, = FIXTURES.glob(prefix + '*.xml')
    old_rule = getattr(parser, f'extract_parser{number}_leftovers')
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return old_rule(*args, **kwargs)
    with patch.object(parser, f'extract_parser{number}_leftovers', capture):
        result = parser.parse_publication_xml(path)
    args, kwargs = calls[0]
    assert old_rule(*args, **kwargs)[0]
    assert extract(*args) == ([], args[0])
    with patch.object(parser, 'extract_parser570_leftovers', lambda text, *a: ([], text)):
        old = parser.parse_publication_xml(path)
    assert result == old
