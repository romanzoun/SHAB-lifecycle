import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser395 import extract_parser395_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = ['1855c3abe279580b8806de34447fdc1f75832e8ebc2773afe15f19d7b9459311', '2bfe63c21628baa119c054da99ab2f48e32db8af946cc9b50f59376bc86bf64b', '3089b128fcdec63aee91c42ecc9684d4e6d742da8c9be894701fadae17fe6601', '48351917f74fa476df2b0a87ac072c134bca34b2d4de1ddfac7bc625d5bfd97c', '5adae93f84b5972e13cbd61c7fed3e5791dc265e899e90f75d10e502807c3c72', '638df0723a50c1f89fc346004251ad22fccce15b00c077eb5501ec90ffd66809', '77f41871b77981f2c97e4cf39bd4a74f4ea769e78b4443229fba31bc789de90f', 'bfe02dbcec18d02da123c1d47a524bd09ed601a8eef5e27d46cd9f26cecc6422', 'c45dd1f438fc09963f03dd0c0a20025f550d8a523e0a8f92aab77eaedb71f954', 'ca3b965bbaaeee515ce2c5333d728e9f09a66e480c174a6edbf832824f502e8c', 'e283a54c43f4be9f82f6c12f464bf03bff58f72a5a42de17f07e9ceef23e8654', 'eb3833552e095397d281c3876ef7ff37d42e44c0da3c39fd6c9a4d6b8b15693d']
CONTEXT_REQUIRED = set()
COUNTS = {"2bfe63c2": 3, "638df072": 2, "bfe02dbc": 2}


@lru_cache(None)
def captured(digest):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser395_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser395_leftovers', capture):
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
    added, rest = extract_parser395_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 444
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS.get(digest[:8], 1) and not rest
    with patch.object(parser, 'extract_parser395_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_unknown_suffix_and_language_preserve_input(digest):
    _, (args, kwargs) = captured(digest)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser395_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser395_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_missing_optional_source_and_invalid_dates(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser395_leftovers(*args)
    if digest[:8] in CONTEXT_REQUIRED:
        assert not events and rest == args[0]
    else:
        assert len(events) == COUNTS.get(digest[:8], 1) and not rest
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser395_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_old_event_without_new_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event



EXPECTED_ACTIONS = [
'spin_off_identical_shareholders_no_capital_increase',
'corporate_limited_partner_contribution_changed_present',
'female_manager_transfer_two_existing_associates',
'cantonal_appeal_civil_decision_annulled',
'female_administrator_name_and_origin_changed',
'administrator_president_appointed_before_new_member',
'asset_transfer_explicit_net_amount_no_consideration',
'two_managers_president_individual_signing',
'holder_full_name_stated',
'foundation_auditor_exemption_revoked_bracketed',
'public_institute_asset_transfer_board_resolution',
'administrator_name_corrected_journal_entry',
]

@pytest.mark.parametrize('digest,action', list(zip(SUPPLIED_SHA256, EXPECTED_ACTIONS)))
def test_explicit_meaning(digest, action):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser395_leftovers(*args, **kwargs)
    assert not rest and events[0].payload['action'] == action
    p = events[0].payload
    prefix = digest[:8]
    if prefix == '1855c3ab':
        assert p['capital_increase'] is False and p['share_allocation'] is False
        assert (p['assets'], p['liabilities']) == ("28'669'442.80", "25'469'442.80")
    elif prefix == '2bfe63c2':
        assert [e.payload['change'] for e in events] == ['portée', 'portée', 'réduite']
        assert [e.payload['amount'] for e in events] == ["3'885'000", "4'600'000", "27'600'000"]
    elif prefix == '3089b128':
        assert (p['count'], p['each'], p['remaining'], p['holding']) == ('80', '40', '70', '60')
    elif prefix == '48351917':
        assert events[0].event_type == 'status_changed'
        assert (p['decision_date'], p['previous_decision_date']) == ('16.12.2020', '28.09.2020')
    elif prefix == '5adae93f':
        assert events[0].role == 'administratrice' and p['origin'] == 'Bâle'
        assert events[0].signing is None and p['place'] is None
    elif prefix == '638df072':
        assert events[0].role == 'président' and events[0].signing is None
        assert events[1].signing == 'Kollektivunterschrift zu zweien'
        assert events[1].payload['country2'] == 'FRA'
    elif prefix == '77f41871':
        assert p['net_assets_raw'] == "2'797.015.75" and p['consideration'] == 'aucune'
    elif prefix == 'bfe02dbc':
        assert all(e.signing == 'Einzelunterschrift' for e in events)
        assert events[1].payload['origin'] == events[1].payload['place']
    elif prefix == 'c45dd1f4':
        assert events[0].role == 'titulaire' and events[0].signing is None
    elif prefix == 'ca3b965b':
        assert p['auditor_exemption'] is False
        assert (p['revocation_date'], p['exemption_date']) == ('01.10.2020', '23.01.2012')
    elif prefix == 'e283a54c':
        assert (p['inventory_date'], p['resolution_date'], p['consideration']) == ('04.09.2020', '12.11.2020', "6'542'000.00")
    elif prefix == 'eb383355':
        assert p['correction'] is True and p['entry'] == '22489'
        assert events[0].signing is None


def test_predecessor_patterns_keep_ownership():
    from shab_analyzer.parser115 import extract_parser115_leftovers
    from shab_analyzer.parser348 import extract_parser348_leftovers
    cases = [
        (extract_parser115_leftovers, 'Exemple Anne, laquelle se nomme maintenant Exemple Marie, est désormais à Lausanne'),
        (extract_parser348_leftovers, "La commandite de l'associée commanditaire Exemple SA (CHE-123.456.789) a été portée de CHF 100.- à CHF 200.-"),
    ]
    for old_parser, text in cases:
        args = (text, 'fr', 'p', '', None, None, None)
        old, rest = old_parser(*args)
        assert old and not rest
        assert extract_parser395_leftovers(*args) == ([], text)


def test_inconsistent_share_counts_preserve_input():
    _, (args, kwargs) = captured(SUPPLIED_SHA256[2])
    changed = args[0].replace('par 40 parts', 'par 41 parts')
    assert extract_parser395_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_valid_net_amount_remains_owned_by_parser391():
    from shab_analyzer.parser391 import extract_parser391_leftovers
    _, (args, kwargs) = captured(SUPPLIED_SHA256[6])
    text = args[0].replace("2'797.015.75", "2'797'015.75")
    old, rest = extract_parser391_leftovers(text, *args[1:], **kwargs)
    assert not rest and old[0].payload['action'] == 'asset_transfer_no_consideration'
    assert extract_parser395_leftovers(text, *args[1:], **kwargs) == ([], text)


def test_unsupported_net_amount_punctuation_preserved():
    _, (args, kwargs) = captured(SUPPLIED_SHA256[6])
    text = args[0].replace("2'797.015.75", '....')
    assert extract_parser395_leftovers(text, *args[1:], **kwargs) == ([], text)
