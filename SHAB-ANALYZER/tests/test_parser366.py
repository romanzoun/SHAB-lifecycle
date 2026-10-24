import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser366 import extract_parser366_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('0f557064', 'de.text.bankruptcy_petition_dismissed_on_appeal.v1', 1), ('142f9a8f', 'de.text.audit_waiver_erroneous_deletion_corrected.v1', 1), ('6d1e330a', 'fr.text.asset_transfer_proprietor_cash_consideration.v1', 1), ('96d7cc45', 'de.text.provisional_moratorium_extended_total_duration.v1', 1), ('c01f17c4', 'fr.text.branch_uid_and_previous_place.v1', 1), ('c3985f64', 'fr.text.board_president_vice_president_exchanged.v1', 2), ('c6f8c01d', 'fr.text.individual_signing_powers_amended.v1', 1), ('dd44c6e6', 'fr.text.associate_manager_share_count_corrected.v1', 1), ('e9aaec59', 'fr.text.head_office_company_name_corrected.v1', 1), ('f43ad476', 'de.text.asset_transfer_cash_consideration_no_space.v1', 1), ('f6ee5e6f', 'de.text.branch_with_canton_removed.v1', 1), ('fdeba080', 'fr.text.two_board_members_joint_signing_typo.v1', 2)]
SUPPLIED_SHA256 = {'0f557064': '0f5570643afdc275359b7d04489f8c9d3bd55bd360b3d83ee7ece203f9308e97', '142f9a8f': '142f9a8f8172b30bc27e75cf0b56953c5e2418bec012cc623fc7be0b50a09dd6', '6d1e330a': '6d1e330aeb41658d172a31a0f6effe285774d06ebd8c3b463ef048b4aede6c91', '96d7cc45': '96d7cc45b4eed625b534e9421e5c1263c110e60b2415809aa77395e849e02eab', 'c01f17c4': 'c01f17c4b51cba4432988591e9270deee41cf2db63fac92a476bbea31fd209b4', 'c3985f64': 'c3985f64fc4c6983b6810ccc767b89e2e6f35ab4dfb094920b797f2e967a6a0a', 'c6f8c01d': 'c6f8c01dadb85f47437b6934d02f44f84b48ce97b0f9224e55e5906609d888cf', 'dd44c6e6': 'dd44c6e63612f39e2965b3d86764cdc4e72ddd1592beb4f4197b011ec616ffc3', 'e9aaec59': 'e9aaec591d6ba22d553c6436e1991195725a340af2816b1b398aad4c0c9f79fe', 'f43ad476': 'f43ad476ab3779cd6c73d60aceb9799087e59e4e8aa75ce585cee35b301b5977', 'f6ee5e6f': 'f6ee5e6fa201ce3c45c869d98de2c514e7d6400d6dd4cb218da7a875708fd218', 'fdeba080': 'fdeba0808e4999b8845fe3999cb49f75f72d8955b5939f9ec5e6fb5bbccb6c2e'}

def path(prefix):
    paths = list(FIXTURES.glob(prefix + '*.xml'))
    assert len(paths) == 1
    return paths[0]


@lru_cache(None)
def captured(prefix):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser366_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser366_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser366_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 392
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser366_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser366_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser366_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_bytes_match_supplied_samples(prefix, rule, count):
    supplied_sha256 = SUPPLIED_SHA256
    fixture = path(prefix)
    assert fixture.stem == supplied_sha256[prefix]
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == supplied_sha256[prefix]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_dates_and_optional_source(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser366_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser366_leftovers(*args)
    if prefix in ('0f557064', '142f9a8f', 'f6ee5e6f'):
        assert not events and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e




@pytest.mark.parametrize('prefix', ['2071d8fd', '2d9f73ab', '3ab22b96', '6b8c6bb0', '6feea7e6', '8013a442', '85478caa', '9464161a', '96e729af', 'acf42ef9', 'bbcc07d5', 'e87c2499'])
def test_parser365_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser366_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for event in baseline.events:
        assert Event(**vars(event)) == event


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_optional_metadata_absent(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser366_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]


@pytest.mark.parametrize('text', ['', 'Unsupported clause', '   '])
def test_empty_and_unknown_residuals(text):
    assert extract_parser366_leftovers(text, 'fr', 'fixture', '', None, None, None) == ([], text.strip())




def test_payload_semantics():
    assert selected('142f9a8f')[0].payload['declaration_date'] == '18.05.2018'
    transfer = selected('6d1e330a')[0].payload
    assert (transfer['assets'], transfer['consideration'], transfer['agreement_day']) == ("120'000", "120'000", '7')
    moratorium = selected('96d7cc45')[0].payload
    assert (moratorium['until_date'], moratorium['extension_months_word'], moratorium['total_months_word']) == ('10.12.2020', 'zwei', 'vier')
    assert selected('c01f17c4')[0].payload['branch_uid'] == 'CHE-287.218.163'
    officers = selected('c3985f64')
    assert [e.role for e in officers] == ['Präsident des Verwaltungsrates', 'Vizepräsident des Verwaltungsrates']
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in officers)
    assert selected('c6f8c01d')[0].signing == 'Einzelunterschrift'
    shares = selected('dd44c6e6')[0].payload
    assert (shares['count'], shares['previous_count'], shares['nominal']) == ('140', '240', '100')
    corrected = selected('e9aaec59')[0].payload
    assert corrected['name'] != corrected['previous_name']
    assets = selected('f43ad476')[0].payload
    assert (assets['assets'], assets['consideration']) == ("440'941'000.00", "440'941'000.00")
    assert selected('f6ee5e6f')[0].payload['branch_uid'] == 'CHE-146.839.597'
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in selected('fdeba080'))


@pytest.mark.parametrize('prefix', ['0f557064', '142f9a8f', 'f6ee5e6f'])
def test_missing_source_context_preserved(prefix):
    _, (args, kwargs) = captured(prefix)
    for source in ('', 'Unrelated context'):
        assert extract_parser366_leftovers(*args, source_text=source) == ([], args[0])


def test_invalid_spelled_contract_date_preserved():
    _, (args, kwargs) = captured('6d1e330a')
    changed = args[0].replace('7 octobre', '32 octobre')
    assert extract_parser366_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_inconsistent_corrected_share_nominal_preserved():
    _, (args, kwargs) = captured('dd44c6e6')
    changed = args[0].replace('240 parts de CHF 100', '240 parts de CHF 200')
    assert extract_parser366_leftovers(changed, *args[1:], **kwargs) == ([], changed)
