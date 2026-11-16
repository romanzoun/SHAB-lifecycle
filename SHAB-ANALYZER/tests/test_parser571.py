import hashlib
import inspect
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser571 import extract_parser571_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['0f6cc00a74f0fc535512aed82c7023f2cc6a69b60d0c62a92abce0fd52efee6a', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = '0f6cc00a74f0fc535512aed82c7023f2cc6a69b60d0c62a92abce0fd52efee6a'
ARGS = ('fr', 'fixture', '', None, None, None)


def source_text():
    return next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text


def target_text():
    return 'Liquidateurs: ' + source_text().split('Liquidateurs: ', 1)[1]


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
    with patch.object(parser, 'extract_parser571_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser571_leftovers', lambda text, *a, **kw: ([], text)):
        old = parser.parse_publication_xml(path)
    assert len(calls) == 1
    added, rest = extract(*calls[0][0], **calls[0][1])
    remaining = list(result.events)
    for event in old.events + added:
        remaining.remove(event)
    if digest == TARGET:
        assert len(added) == 3
        assert rest.strip(' .').endswith(result.leftover_text)
    else:
        assert added == []
        assert result == old


def test_payload_and_optional_metadata():
    events, rest = extract(target_text(), 'fr', 'pub', '2021', 'uid', '4104', 'BL')
    assert rest == '' and len(events) == 3
    assert {e.rule_id for e in events} == {'fr.persons.board_president_secretary_liquidators_restrictions_lifted.v1'}
    assert [e.event_type for e in events] == ['officer_changed', 'officer_changed', 'organization_changed']
    assert [e.role for e in events[:2]] == ["président du conseil d'administration liquidateur", "secrétaire du conseil d'administration liquidateur"]
    assert [e.signing for e in events[:2]] == ['Kollektivunterschrift zu zweien'] * 2
    assert [e.payload for e in events] == [
        {'name': 'Rossetti Terenzio', 'place': None},
        {'name': 'Faivre-Rampant Stéphane', 'place': None},
        {'action': 'share_transfer_restrictions_lifted'},
    ]
    sparse = extract(target_text(), *ARGS)[0]
    for event, minimal in zip(events, sparse):
        assert Event(**vars(event)) == event
        assert minimal.payload == event.payload
        assert (event.publication_id, event.published_at, event.org_uid, event.plz, event.canton) == ('pub', '2021', 'uid', '4104', 'BL')
        assert (minimal.org_uid, minimal.plz, minimal.canton) == (None, None, None)
    for legacy in (Event('pub', '', 'officer_changed', 'legacy'),
                   Event('pub', '', 'organization_changed', 'legacy', payload={'action': 'share_transfer_restrictions_lifted'})):
        assert Event(**vars(legacy)) == legacy
    assert PARSER_VERSION >= 571


def test_no_existing_rule_owns_new_clause():
    from shab_analyzer.text_extras import extract_text_extras
    text = target_text().removesuffix('.')
    assert extract_text_extras(text, *ARGS, set()) == ([], text)
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser571_leftovers':
            continue
        options = {'source_text': source_text()} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('change', [
    lambda t: '', lambda t: t + ' UNKNOWN_SUFFIX.',
    lambda t: 'Inconnu. ' + t,
    lambda t: t.replace('secrétaire', 'trésorier'),
    lambda t: t.replace('collectivement à deux', 'individuellement'),
    lambda t: t.replace('sont levées', 'ne sont pas levées'),
    lambda t: t.replace('Faivre-Rampant Stéphane', 'Rossetti Terenzio'),
])
def test_unsupported_input_unchanged(change):
    text = change(target_text())
    assert extract(text, *ARGS) == ([], text)


@pytest.mark.parametrize('language', ['de', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


def test_whitespace_and_optional_period():
    expected = extract(target_text(), *ARGS)
    assert extract('  ' + target_text() + '  ', *ARGS) == expected
    assert extract(target_text().removesuffix('.'), *ARGS) == expected


@pytest.mark.parametrize('number', [171, 291, 329])
def test_legacy_rule_boundary(number):
    # Remove only the new secretary qualification for the two-member old rule.
    text = target_text().replace(', secrétaire', '')
    if number == 171:
        text = text.replace('liées à la', 'à la')
    elif number == 329:
        text = text.replace(', et Faivre', ', Faivre').replace(
            ", membres du conseil", ", et Martin Paul, tous membres du conseil")
    old_rule = getattr(parser, f'extract_parser{number}_leftovers')
    assert old_rule(text, *ARGS)[0]
    assert extract(text, *ARGS) == ([], text)
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as directory:
        tree = ET.parse(FIXTURES / (TARGET + '.xml'))
        next(tree.iter('publicationText')).text = text
        path = Path(directory) / 'boundary.xml'
        tree.write(path, encoding='utf-8')
        with patch.object(parser, 'extract_parser571_leftovers', lambda text, *a: ([], text)):
            expected = parser.parse_publication_xml(path)
        assert parser.parse_publication_xml(path) == expected
