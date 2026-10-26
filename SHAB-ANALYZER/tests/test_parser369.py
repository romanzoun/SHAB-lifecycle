import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser369 import extract_parser369_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('2be1217c', 'de.text.branch_register_references_updated.v1', 1), ('3d0fb8bb', 'fr.text.sole_associate_not_manager_corrected.v1', 1), ('40bc6a34', 'de.text.bearer_to_registered_shares_statutes_changed.v1', 1), ('44f68acf', 'fr.text.two_associate_managers_share_transfer_typo.v1', 1), ('4d5b0b09', 'fr.text.definitive_composition_moratorium_extended.v1', 1), ('4ea787ef', 'de.text.covid_moratorium_granted_three_months.v1', 1), ('50807e75', 'fr.text.officer_origin_corrected_notice_reference.v1', 1), ('8733db9b', 'fr.text.two_foundation_members_unsigned.v1', 2), ('9965ad1d', 'fr.text.associate_manager_name_corrected.v1', 1), ('c4c22b5b', 'fr.text.four_officers_restricted_joint_signing.v1', 4), ('e45d8173', 'fr.text.associate_appointed_presiding_manager.v1', 1), ('ecc918bf', 'de.text.expired_authorized_capital_replaced.v1', 1)]
SUPPLIED_SHA256 = {'2be1217c': '2be1217ca08eec7cd45da39cd3e19b3d37c95a4e8c9a1d7cb3ae9af47a3afcc4', '3d0fb8bb': '3d0fb8bb928782801068639585dd600ae7c4588fd952eaf92b974461a14809fe', '40bc6a34': '40bc6a34b09b03458ce2b6a098f15f3becd7fc960d56345d59072291cc57ae32', '44f68acf': '44f68acf6f696961fd520e1aa241f6dfda87186c4b099a48a6bda5dcd656ea95', '4d5b0b09': '4d5b0b09ebecdaa1a024e2a3660e85d8f87d12a10c5fbe79f8e72d258919eb05', '4ea787ef': '4ea787ef45134ac5bfb0482d7ffa2f7f1e74ff3cefd3f12ad9c2dd862b8fb895', '50807e75': '50807e75e73f859e2014a522a16e0dd86489eb63cd028dce2c3c5ad0e1d5e9fe', '8733db9b': '8733db9b62986ee85ba3763f7c2c82adc0e4c5735b94ef4623b49b6042ec8934', '9965ad1d': '9965ad1d1812d3aa74e2d433fa11583b5d1e9af19bae5355221ae67e6e57ef67', 'c4c22b5b': 'c4c22b5b26e7864fdd2f04d5b6250fd5ea605c6f23744a1cb5c8dd854bfe6da4', 'e45d8173': 'e45d81731595e6c39f903e9a4885520cb0d53f60f55fa6713b16de85912baba2', 'ecc918bf': 'ecc918bf83d637762feef71b9bb98dd17a39c49f089c2c9c954313de76252222'}

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
        return extract_parser369_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser369_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser369_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 406
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser369_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser369_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser369_leftovers(args[0], 'en', *args[2:], **kwargs)
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
    for date in set(re.findall(r'\d{2}[-.]\d{2}[-.]\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser369_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser369_leftovers(*args)
    assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e




@pytest.mark.parametrize('prefix', ['1e36a4a8', '3a9d3e4d', '3daf9912', '6b0c71ca', '8cffc69b', '9f121617', 'a37a4549', 'a9e3033c', 'b804d142', 'cbf9efa0', 'f1ce305c', 'f3113a65'])
def test_parser368_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser369_leftovers', lambda text, *args, **kwargs: ([], text)):
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
    events, leftover = extract_parser369_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]


@pytest.mark.parametrize('text', ['', 'Unsupported clause', '   '])
def test_empty_and_unknown_residuals(text):
    assert extract_parser369_leftovers(text, 'fr', 'fixture', '', None, None, None) == ([], text.strip())



def test_payload_semantics():
    branches = selected('2be1217c')[0].payload
    assert branches['uid2'] == 'CHE-257.887.224'
    assert branches['uid3'] == 'CHE-339.821.311'
    assert branches['previous_register1'] == 'CH-350.9.001.028-9'
    associate = selected('3d0fb8bb')[0]
    assert associate.role == 'Gesellschafter' and associate.signing is None
    assert associate.payload['sole_associate'] is True
    assert associate.payload['excluded_role'] == 'Geschäftsführer'
    capital = selected('40bc6a34')[0].payload
    assert (capital['capital'], capital['count'], capital['nominal']) == ("200'000", "2'000", '100')
    assert capital['fully_paid'] is True and capital['currency'] == 'CHF'
    assert capital['security_kind'] == 'Namenaktien' and capital['previous_security_kind'] == 'Inhaberaktien'
    transfer = selected('44f68acf')[0].payload
    assert (transfer['transferred'], transfer['previous_count'], transfer['remaining_count'], transfer['recipient_count']) == ('5', '95', '90', '20')
    assert transfer['nominal'] == '100' and transfer['currency'] == 'CHF'
    extension = selected('4d5b0b09')[0].payload
    assert (extension['decision_date'], extension['end_date']) == ('26.10.2020', '16.12.2020')
    moratorium = selected('4ea787ef')[0].payload
    assert (moratorium['decision_date'], moratorium['end_date'], moratorium['duration_months']) == ('08.10.2020', '08.01.2021', '3')
    origin = selected('50807e75')[0]
    assert (origin.payload['origin'], origin.payload['previous_origin']) == ('France', 'Genève')
    assert origin.role is None and origin.signing is None
    foundation = selected('8733db9b')
    assert [e.payload['place'] for e in foundation] == ['La Chaux-de-Fonds', 'Biel/Bienne']
    assert all(e.role == 'Mitglied des Stiftungsrates' and e.signing == 'ohne Zeichnungsberechtigung' for e in foundation)
    corrected = selected('9965ad1d')[0]
    assert corrected.payload['name'].endswith('Joaquin') and corrected.payload['previous_given_name'] == 'Joaquim'
    assert corrected.role == 'Gesellschafter und Geschäftsführer' and corrected.signing is None
    officers = selected('c4c22b5b')
    assert [e.role for e in officers] == ['Vizedirektor', None, None, None]
    assert [e.payload['place'] for e in officers] == ['Mont-sur-Lausanne', 'Ecublens (VD)', 'Rolle', 'Lausanne']
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in officers)
    assert all(e.payload['signing_restriction'].startswith('pas entre eux ni avec ') for e in officers)
    assert all(len(e.payload['excluded_signers'].split(', ')) == 7 for e in officers)
    president = selected('e45d8173')[0]
    assert president.role == 'Präsident der Geschäftsführung' and president.signing is None
    authorization = selected('ecc918bf')[0].payload
    assert (authorization['previous_authorization_date'], authorization['decision_date']) == ('24.09.2018', '22.09.2020')


@pytest.mark.parametrize('prefix,old,new', [
    ('44f68acf', '90 parts de CHF 100', '90 parts de CHF 200'),
    ('2be1217c', 'CH-350.9.001.027-3', 'INVALID'),
])
def test_inconsistent_references_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser369_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_parser340_name_correction_is_not_reinterpreted():
    import shab_analyzer.parse as parser
    from shab_analyzer.parser340 import extract_parser340_leftovers

    calls = []

    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser340_leftovers(*args, **kwargs)

    with patch.object(parser, 'extract_parser340_leftovers', capture):
        result = parse_publication_xml(path('e76aae5c'))
    assert len(calls) == 1
    args, kwargs = calls[0]
    assert extract_parser369_leftovers(*args, **kwargs) == ([], args[0])
    old = [event for event in result.events if event.rule_id == 'fr.text.associate_manager_name_corrected.v1']
    assert len(old) == 1 and 'previous_name' in old[0].payload
    assert 'previous_given_name' not in old[0].payload
    with patch.object(parser, 'extract_parser369_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path('e76aae5c'))
    assert result == baseline


def test_name_correction_does_not_capture_legacy_comma_variant():
    _, (args, kwargs) = captured('9965ad1d')
    changed = args[0].replace(' comme publié)', ', comme publié)')
    assert changed != args[0]
    assert extract_parser369_leftovers(changed, *args[1:], **kwargs) == ([], changed)
