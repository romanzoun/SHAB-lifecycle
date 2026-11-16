import hashlib
import inspect
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser569 import extract_parser569_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['24c5e19181f0c6fea44439050959a89935ab636a8bf09c23bac4225d77e0bb2c', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = '24c5e19181f0c6fea44439050959a89935ab636a8bf09c23bac4225d77e0bb2c'
ARGS = ('fr', 'fixture', '', None, None, None)


def source_text():
    return next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text


def target_text():
    return "L'inscription no " + source_text().split("L'inscription no ", 1)[1]


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
    with patch.object(parser, 'extract_parser569_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser569_leftovers', lambda text, *a, **kw: ([], text)):
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
    events, rest = extract(target_text(), 'fr', 'pub', '2021', 'uid', '1200', 'GE')
    assert rest == '' and len(events) == 1
    event = events[0]
    assert event.event_type == 'officer_changed'
    assert event.role == 'directeur'
    assert event.signing is None
    assert event.rule_id == 'fr.persons.director_role_supplemented_notice_reference.v1'
    assert event.payload == {
        'name': 'Deppierraz Philippe', 'place': None,
        'action': 'entry_supplemented', 'entry': '18830',
        'entry_date': '2019-10-08', 'notice_date': '2019-10-11',
        'notice_ref': '0/1004736283',
    }
    assert (event.publication_id, event.published_at, event.org_uid,
            event.plz, event.canton) == ('pub', '2021', 'uid', '1200', 'GE')
    assert Event(**vars(event)) == event
    sparse = extract(target_text(), *ARGS)[0][0]
    assert sparse.payload == event.payload
    assert (sparse.org_uid, sparse.plz, sparse.canton) == (None, None, None)
    for legacy in (Event('pub', '', 'officer_changed', 'legacy'),
                   Event('pub', '', 'officer_changed', 'legacy', payload={'name': 'Exemple'})):
        assert Event(**vars(legacy)) == legacy
        assert 'notice_ref' not in legacy.payload
    assert PARSER_VERSION >= 569


def test_no_existing_rule_owns_new_clause():
    from shab_analyzer.text_extras import extract_text_extras
    text = target_text().removesuffix('.')
    assert extract_text_extras(text, *ARGS, set()) == ([], text)
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser569_leftovers':
            continue
        options = {'source_text': source_text()} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('change', [
    lambda t: '', lambda t: t + ' UNKNOWN_SUFFIX.',
    lambda t: 'Inconnu. ' + t,
    lambda t: t.replace('est directeur', 'est président'),
    lambda t: t.replace('est complétée', 'est rectifiée'),
    lambda t: t.replace('08.10.2019', '32.10.2019'),
    lambda t: t.replace('11.10.2019', '31.02.2019'),
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


@pytest.mark.parametrize('number,text', [
    (210, "L'inscription 123 du 01.01.2020 (FOSC du 02.01.2020 p. 0/123) est complétée en ce sens que l'administrateur Exemple Jean est président du conseil d'administration."),
    (215, "L'inscription no 123 du 01.01.2020 est complétée en ce sens que l'administrateur Exemple Jean est aussi directeur."),
    (236, "L'inscription 123 du 01.01.2020 est complétée en ce sens que Exemple Jean et Exemple Anne sont directeurs."),
])
def test_legacy_rule_boundary(number, text, tmp_path):
    old_rule = getattr(parser, f'extract_parser{number}_leftovers')
    assert old_rule(text, *ARGS)[0]
    assert extract(text, *ARGS) == ([], text)
    paths = list(FIXTURES.glob(TARGET + '.xml'))
    original = source_text()
    xml = paths[0].read_text().replace(original, text)
    path = tmp_path / 'boundary.xml'
    path.write_text(xml)
    with patch.object(parser, 'extract_parser569_leftovers', lambda text, *a: ([], text)):
        old = parser.parse_publication_xml(path)
    assert parser.parse_publication_xml(path) == old
