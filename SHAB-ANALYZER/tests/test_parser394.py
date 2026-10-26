import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser394 import extract_parser394_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = ['08f2941f199bdc9f953c5d8013cd965785f2c1e74049c19916b633d33f0ae304', '0e8f6934bc91f77656dbd69a9d438a8ca4afea63879fff2ea871298f0c51e1dd', '12fb895924d6a60e8d2879e40e0b5d28745d80bd78fa849e8e06bf878d74773b', '19cf82a99cbd5e409ebe561e6b2a691956c9ead33a1cbe5af3c8706f8dfed761', '298655445f89c687f5043a99e4ee4faa3afcb6a0f37d842994ed066dbcb736f1', '400722817820cfbfe3b7981d31ab7fb7965bd1660d3a4e25fda4897f3d634229', '51f9e993f056efeaca174cd52bc5f1c6aacd1fc988dfc99a00190a52eea59af9', '5805a9769e51bd22633f7491c303e284c75a8b29c46d447c874f94480c526ee4', '626d55c544b7f95dc457c0ddc2ea0a1cfe6aab180ce674064dee15bf515e5cb8', 'eb4f1b504f91dbc51ecc6cd814165edba3946ab025f1ffdab33ca5f906d7f078', 'f6b0512ad0119f835825739fdf0e3eb4252e5121e1aa7d41eed45d225af74263', 'fdeddc027979eed585c7f0d7e9daefd739e5bc0fb3ddd5a86d600f490d05aac2']
CONTEXT_REQUIRED = {"19cf82a9", "51f9e993", "fdeddc02"}
COUNTS = {"19cf82a9": 4, "51f9e993": 3, "eb4f1b50": 5}


@lru_cache(None)
def captured(digest):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser394_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser394_leftovers', capture):
        result = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert len(calls) == 1
    return result, calls[0]

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_complete_and_unchanged_legacy_payloads(digest):
    import shab_analyzer.parse as parser
    result, (args, kwargs) = captured(digest)
    added, rest = extract_parser394_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 403
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS.get(digest[:8], 1) and not rest
    with patch.object(parser, 'extract_parser394_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_unknown_suffix_and_language_preserve_input(digest):
    _, (args, kwargs) = captured(digest)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser394_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser394_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_missing_optional_source_and_invalid_dates(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser394_leftovers(*args)
    if digest[:8] in CONTEXT_REQUIRED:
        assert not events and rest == args[0]
    else:
        assert len(events) == COUNTS.get(digest[:8], 1) and not rest
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser394_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_old_event_without_new_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event



EXPECTED_ACTIONS = [
    'administrator_appointed_individual_without_comma',
    'statutes_copy_filed_complement_notice',
    'collective_signatory_without_residence',
    'three_administrators_collective_liquidators',
    'bankruptcy_opened_president_then_company_name',
    'foundation_organization_inner_period',
    'president_and_two_managers_share_transfers',
    'provisional_reinstatement_interim_measures',
    'reinstatement_erroneous_requisition',
    'foundation_vice_president_appointed_unsigned_members',
    'two_associate_holdings_corrected_after_transfers',
    'female_associate_manager_collective_signing',
]


@pytest.mark.parametrize('digest,action', list(zip(SUPPLIED_SHA256, EXPECTED_ACTIONS)))
def test_explicit_meaning(digest, action):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser394_leftovers(*args, **kwargs)
    assert not rest and events[0].payload['action'] == action
    p = events[0].payload
    prefix = digest[:8]
    if prefix == '08f2941f':
        assert events[0].role == 'administrateur' and events[0].signing == 'Einzelunterschrift'
    elif prefix == '0e8f6934':
        assert (p['entry'], p['entry_date'], p['notice_date'], p['notice_ref']) == ('14602', '09.08.2018', '14.08.2018', '0/4414557')
    elif prefix == '12fb8959':
        assert events[0].signing == 'Kollektivunterschrift zu zweien' and events[0].role is None
    elif prefix == '19cf82a9':
        assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in events[:3])
        assert events[3].event_type == 'capital_changed' and events[3].payload['transfer_restricted'] is False
        assert (p['count'], p['nominal']) == ("952'000", '1')
    elif prefix == '29865544':
        assert events[0].event_type == 'status_changed'
        assert (p['decision_date'], p['effective_date'], p['time']) == ('10.12.2020', '10.12.2020', '08.15')
    elif prefix == '40072281':
        assert (p['minimum'], p['maximum'], p['auditor']) == ('3', '5', 'Kontrollstelle')
    elif prefix == '51f9e993':
        assert (p['count1'], p['previous1'], p['count2'], p['previous2'], p['received2'], p['remaining']) == ('4', '8', '2', '6', '4', '4')
        assert all(e.role == 'associé-gérant' and e.signing == 'Kollektivunterschrift zu zweien' for e in events[1:])
    elif prefix == '5805a976':
        assert events[0].event_type == 'status_changed' and p['provisional'] is True
        assert (p['decision_day'], p['decision_year']) == ('16', '2020')
    elif prefix == '626d55c5':
        assert events[0].event_type == 'status_changed' and p['correction'] is True
        assert (p['notice'], p['notice_date'], p['notice_ref']) == ('86', '05.05.2020', '1004883482')
    elif prefix == 'eb4f1b50':
        assert events[0].role == 'vice-présidente' and events[0].signing is None
        assert all(e.role == 'membre du conseil de fondation' and e.signing == 'ohne Zeichnungsberechtigung' for e in events[1:])
        assert events[2].payload['origin'] == events[2].payload['place']
    elif prefix == 'f6b0512a':
        assert (p['count1'], p['previous1'], p['count2'], p['previous2'], p['nominal']) == ('25', '5', '5', '10', '100')
        assert p['correction'] is True
    elif prefix == 'fdeddc02':
        assert events[0].role == 'associée-gérante' and events[0].signing == 'Kollektivunterschrift zu zweien'


def test_individual_manager_remains_owned_by_parser286():
    from shab_analyzer.parser286 import extract_parser286_leftovers
    text = "L'associée Exemple Anne est nommée gérante"
    source = text + ' avec signature individuelle.'
    args = (text, 'fr', 'p', '', None, None, None)
    old, rest = extract_parser286_leftovers(*args, source_text=source)
    assert not rest and old[0].signing == 'Einzelunterschrift'
    assert extract_parser394_leftovers(*args, source_text=source) == ([], text)
    assert extract_parser394_leftovers(*args) == ([], text)


def test_legacy_foundation_pattern_retains_ownership():
    from shab_analyzer import parser164
    from shab_analyzer.parser394 import _LEGACY
    text = 'Organisation neu: [Organisation: Stiftungsrat von 3 bis 5 Mitgliedern und Kontrollstelle]'
    assert parser164._DE_FOUNDATION_ORGANIZATION in _LEGACY
    assert parser164._DE_FOUNDATION_ORGANIZATION.fullmatch(text)
    args = (text, 'de', 'p', '', None, None, None)
    assert parser164.extract_parser164_leftovers(*args)[0]
    assert extract_parser394_leftovers(*args) == ([], text)


@pytest.mark.parametrize('digest', [d for d in SUPPLIED_SHA256 if d[:8] in CONTEXT_REQUIRED])
def test_source_signing_must_agree(digest):
    _, (args, kwargs) = captured(digest)
    changed = kwargs['source_text'].replace('avec signature collective à deux', 'avec signature individuelle')
    assert extract_parser394_leftovers(*args, source_text=changed) == ([], args[0])


def test_invalid_word_date_and_time():
    for digest, old, new in [(SUPPLIED_SHA256[7], '16 décembre', '32 décembre'),
                             (SUPPLIED_SHA256[4], '08.15 Uhr', '25.99 Uhr')]:
        _, (args, kwargs) = captured(digest)
        changed = args[0].replace(old, new)
        assert changed != args[0]
        assert extract_parser394_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('number,prefix', [(286, '1f0d1df6'), (316, None), (317, None),
                                          (335, '1b239b69'), (336, 'ed8453e2'),
                                          (339, '0534e4d1'), (353, '0e514673'),
                                          (383, None), (389, None)])
def test_predecessor_residuals_are_returned_unchanged(number, prefix):
    import importlib.util
    spec = importlib.util.spec_from_file_location(f'boundary_parser{number}', Path(__file__).with_name(f'test_parser{number}.py'))
    previous = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(previous)
    cases = [prefix] if prefix else (previous.SUPPLIED_SHA256 if number >= 383 else [c[0] for c in previous.CASES])
    for case in cases:
        if number == 286:
            args, kwargs = previous.invocation(case)
        else:
            _, (args, kwargs) = previous.captured(case)
        assert extract_parser394_leftovers(*args, **kwargs) == ([], args[0])


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_missing_optional_organization_metadata(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser394_leftovers(*args[:4], None, None, None, **kwargs)
    assert not rest and len(events) == COUNTS.get(digest[:8], 1)
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
