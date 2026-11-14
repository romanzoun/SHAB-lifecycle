import hashlib
import inspect
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser526 import extract_parser526_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', '47735c677cbbc7dbe7ef4d2fb8be9b5ee6601a593b6e894dfa4b0fafb91d6c8e', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = "47735c677cbbc7dbe7ef4d2fb8be9b5ee6601a593b6e894dfa4b0fafb91d6c8e"
ARGS = ("fr", "fixture", "", None, None, None)


def target_text():
    source = next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text
    return source[source.index('Nouveaux faits qualifiés:'):source.index(' Nouvelles communications')].rstrip('.')

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
    with patch.object(parser, 'extract_parser526_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser526_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert event.event_type == 'statutes_changed'
    assert event.payload['action'] == 'removed'
    assert event.payload['kind'] == 'contribution_in_kind_and_asset_acquisition'
    assert event.payload['previous_contribution'].startswith('Selon convention des ')
    assert event.payload['previous_acquisition'].startswith('Reprise de biens envisagée: ')
    assert event.org_uid is event.plz is event.canton is None
    assert Event(**vars(event)) == event
    legacy = Event('old', '', 'statutes_changed', 'legacy', payload={'action': 'removed'})
    assert Event(**vars(legacy)) == legacy
    assert 'previous_contribution' not in legacy.payload
    assert 'previous_acquisition' not in legacy.payload
    assert extract(target_text(), *ARGS, source_text=target_text()) == (events, rest)
    assert PARSER_VERSION == 551


def test_no_existing_rule_owns_input():
    text = target_text()
    from shab_analyzer.text_extras import extract_text_extras
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser526_leftovers':
            continue
        options = {'source_text': text} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('text,number', [
    ("La clause relative à la reprise de biens envisagée est abrogée conformément à l'art. 628 al. 4 CO", 57),
    ("Radiation de la mention relative aux apports en nature et à la reprise de biens envisagée à la constitution de la société. Radiation du mode de communication aux actionnaires", 303),
])
def test_legacy_boundary(text, number, tmp_path):
    old = getattr(parser, f'extract_parser{number}_leftovers')
    events, _ = old(text, *ARGS)
    assert events
    assert extract(text, *ARGS) == ([], text)
    assert old(extract(text, *ARGS)[1], *ARGS)[0] == events
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    next(tree.iter('publicationText')).text = text
    path = tmp_path / 'boundary.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser526_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parser.parse_publication_xml(path)


@pytest.mark.parametrize('before,after', [
    ('Abrogation', 'Modification'), ('biffé:', 'non:'),
    ('Reprise de biens envisagée:', 'Reprise de biens:'),
    ('Selon convention des', 'Selon contrat du'),
    ('Nouveaux faits qualifiés:', 'Faits qualifiés:'),
])
def test_invalid_or_unattested_input(before, after):
    text = target_text().replace(before, after)
    assert extract(text, *ARGS) == ([], text)


@pytest.mark.parametrize('language', ['de', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


def test_unknown_remainder_and_context():
    text = target_text() + ' UNKNOWN'
    assert extract(text, *ARGS) == ([], text)
    events, _ = extract(target_text(), 'fr', 'pub', '2021', 'uid', '1000', 'ZH')
    assert len(events) == 1
    e = events[0]
    assert (e.publication_id, e.published_at, e.org_uid, e.plz, e.canton) == (
        'pub', '2021', 'uid', '1000', 'ZH')



def test_legacy_pattern_inside_deleted_clause_is_left_untouched():
    from shab_analyzer.parser57 import _FR_CONTRIBUTION_RULES_REMOVED_VARIANT
    from shab_analyzer.text_extras import _FR_CONTRIBUTION_RULES_REMOVED
    clauses = [
        "La clause relative à la reprise de biens envisagée est abrogée conformément à l'art. 628 al. 4 CO",
        "La clause statutaire relative à l'apport en nature à la constitution est supprimée conformément à l'art. 628 al. 4 CO",
    ]
    for pattern, clause in zip((_FR_CONTRIBUTION_RULES_REMOVED_VARIANT, _FR_CONTRIBUTION_RULES_REMOVED), clauses):
        assert pattern.search(clause)
        text = target_text().replace('Selon convention des ', 'Selon convention des ' + clause + ' ')
        assert extract(text, *ARGS) == ([], text)
