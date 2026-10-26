import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser365 import extract_parser365_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('2071d8fd', 'fr.text.share_transfer_manager_presidency.v1', 1), ('2d9f73ab', 'fr.text.german_officers_french_notice.v1', 8), ('3ab22b96', 'de.text.profit_participation_certificate_rights.v1', 1), ('6b8c6bb0', 'fr.text.reinstatement_bankruptcy_reopened_summary.v1', 1), ('6feea7e6', 'it.text.corrected_manager_details_two_shares.v1', 2), ('8013a442', 'fr.text.auditor_company_name_corrected.v1', 1), ('85478caa', 'de.text.reinstatement_assigned_claims_after_bankruptcy.v1', 1), ('9464161a', 'de.text.covid19_moratorium_extended.v1', 1), ('96e729af', 'fr.text.board_president_and_joint_member.v1', 2), ('acf42ef9', 'de.text.asset_transfer_business_unit_share_consideration.v1', 1), ('bbcc07d5', 'fr.text.share_transfer_manager_presidency.v1', 1), ('e87c2499', 'fr.text.manager_appointed_same_origin_place.v1', 1)]
SUPPLIED_SHA256 = {'2071d8fd': '2071d8fd090302f14533895ebbf8a64aea3c84e6d6145abacb6b591344723889', '2d9f73ab': '2d9f73ab4e11aa9d748524a83a3cdb67714eca88b6bebf0e3d79cd8888198fc5', '3ab22b96': '3ab22b96d9d6b29aa0ba9d4051a005c9a8977cb9957da66af0657bd71e8451b0', '6b8c6bb0': '6b8c6bb037b1ee8259bc0ffa96702500f6979c46eafb25c5d424ef55bc69c002', '6feea7e6': '6feea7e6ebb787fa6ff615a7fd90bf1ff78f28cf1c8583c46342eff20a4e5ab5', '8013a442': '8013a44271b103a6366c025696aaa54300f5b77ab09f1773295568be3d58978c', '85478caa': '85478caa8ccb5b4a87e5670b9ec0355fb27c3fd8410697933f08d43f41993875', '9464161a': '9464161a940daf8d82f0a7226fcb8299f4b121759dec0e2ce68ba5525735a42b', '96e729af': '96e729af8b4c0d11f3af45c49832cdda304efff92c2ac9f18a5a5021a23e8a92', 'acf42ef9': 'acf42ef9a9e6c9bdaeaa49687c9ef91db97446007ee412ca04175aa7901346e3', 'bbcc07d5': 'bbcc07d5da23272d5cfbebf52fe231c7747482cd230b28d9bb6d12bdef81e70c', 'e87c2499': 'e87c2499c38b658ad50cddb7a85e474bd516c7b737ba4365ac08ba522717f4de'}

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
        return extract_parser365_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser365_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser365_leftovers(*args, **kwargs)[0]


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
    with patch.object(parser, 'extract_parser365_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser365_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser365_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser365_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser365_leftovers(*args)
    if prefix in ('96e729af', 'e87c2499'):
        assert not events and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e




@pytest.mark.parametrize('prefix', ['07493c0d', '0d40dd29', '1a32f6d9', '1c52462f', '269a35c0', '42b4a508', '6d154b6d', '710ae056', '79b5d750', 'd238096b', 'f0c9ed26', 'fa87e1f2'])
def test_parser364_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser365_leftovers', lambda text, *args, **kwargs: ([], text)):
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
    events, leftover = extract_parser365_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]


@pytest.mark.parametrize('text', ['', 'Unsupported clause', '   '])
def test_empty_and_unknown_residuals(text):
    assert extract_parser365_leftovers(text, 'fr', 'fixture', '', None, None, None) == ([], text.strip())




def test_payload_semantics():
    transfer = selected('2071d8fd')[0].payload
    assert (transfer['remaining'], transfer['transferred'], transfer['nominal']) == ('11', '9', "1'000")
    assert selected('bbcc07d5')[0].payload['recipient_role'] == 'nouvel associé-gérant et président'
    officers = selected('2d9f73ab')
    assert officers[0].payload['change'] == 'removed'
    assert all(e.payload['change'] == 'appointed' for e in officers[1:])
    assert officers[1].role == 'Mitglied des Verwaltungsrates'
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in officers)
    assert selected('3ab22b96')[0].payload['liquidation_proceeds_participation'] is True
    assert selected('6b8c6bb0')[0].payload['suspension_revoked'] is True
    corrected = selected('6feea7e6')
    assert [e.signing for e in corrected] == ['Einzelunterschrift'] * 2
    assert corrected[0].payload['nominal1'] == "19'000.00"
    auditor = selected('8013a442')[0].payload
    assert (auditor['name'], auditor['previous_name']) == ('KPMG SA', 'KMPG SA')
    assert selected('85478caa')[0].payload['legal_basis'] == 'Art. 260 SchKG'
    assert selected('9464161a')[0].payload['until_date'] == '19.01.2021'
    assert [e.signing for e in selected('96e729af')] == ['Einzelunterschrift', 'Kollektivunterschrift zu zweien']
    assets = selected('acf42ef9')[0].payload
    assert (assets['assets'], assets['liabilities'], assets['count'], assets['nominal']) == ("8'118'187.00", "118'187.00", "39'927", '1.00')
    assert selected('e87c2499')[0].signing == 'Kollektivunterschrift zu zweien'


@pytest.mark.parametrize('prefix', ['2071d8fd', 'bbcc07d5'])
def test_inconsistent_transfer_preserved(prefix):
    _, (args, kwargs) = captured(prefix)
    changed = re.sub(r'pour \d+ parts', 'pour 999 parts', args[0])
    assert changed != args[0]
    assert extract_parser365_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['96e729af', 'e87c2499'])
def test_missing_or_conflicting_source_signing_preserved(prefix):
    _, (args, kwargs) = captured(prefix)
    for source in ('', kwargs['source_text'].replace('signature collective à deux', 'signature individuelle')):
        assert extract_parser365_leftovers(*args, source_text=source) == ([], args[0])
