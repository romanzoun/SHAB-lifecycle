import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser367 import extract_parser367_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('15fca0c1', 'fr.text.registered_share_composition_supplemented.v1', 1), ('1b6eb4b8', 'de.text.covid_moratorium_revoked_with_previous_grant.v1', 1), ('2d4d020d', 'fr.text.two_managers_joint_signing_with_manager_typo.v1', 2), ('37e0ff28', 'de.text.covid_moratorium_appeals_suspensive_effect.v1', 1), ('6098826f', 'fr.text.manager_origin_corrected.v1', 1), ('6ab95148', 'fr.text.three_associates_share_split.v1', 1), ('77b6aefd', 'de.text.branch_commercial_registry.v1', 1), ('831e0472', 'fr.text.president_share_transfer_new_associate_manager.v1', 1), ('97aa9560', 'de.text.ancillary_obligations_erroneous_entry_corrected.v1', 1), ('a00f3e3d', 'fr.text.registered_share_transfer_restriction_since_incorporation.v1', 1), ('e34d012c', 'fr.text.associate_manager_appointed_liquidator.v1', 1), ('f9481940', 'fr.text.board_president_individual_signing_corrected.v1', 1)]
SUPPLIED_SHA256 = {'15fca0c1': '15fca0c1df706e2b64d5bd924bb7cb41a3b11f31cf6a357af65051719855c010', '1b6eb4b8': '1b6eb4b8d9c96665ccbe1db5120edde655d8f46f85e990951955d4c686f5adb1', '2d4d020d': '2d4d020d0d2974308398303b3f53d41f6bd01194a60a7a619bd0cfea9b919173', '37e0ff28': '37e0ff28b70aa0ea27bd9e8f844a06d9970b3b22008806ca208154286ab2b6b4', '6098826f': '6098826f234f93d6f6ae6b9f5d7c419a855c7a287ea13bfaa7e5a42c947ec32d', '6ab95148': '6ab95148f46032757414926f503fd947b8ec05ea5f8ed50431e821953e438053', '77b6aefd': '77b6aefd1208b71021ad51d226906aa86f62c6eae12583fe234623587b5641d8', '831e0472': '831e0472782cfe31386f6dae8d357fa3303991035659fa6b3f319b11d761d0dc', '97aa9560': '97aa9560ca6ebbf3dea93961eb953008b2f5d51f9a0921d8074a638d63108f8c', 'a00f3e3d': 'a00f3e3d2a3537169627e591ae446080e2c190e58fc35ec0701b16e59de8d038', 'e34d012c': 'e34d012c7ffa900ff1533751920965291e0dc108032ee521e5c4ae5275b0347d', 'f9481940': 'f94819405adaf9cbbd4f9639d1af484d263137bde7df8d113208a5176cfe284f'}

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
        return extract_parser367_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser367_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser367_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 438
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser367_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser367_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser367_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser367_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser367_leftovers(*args)
    if prefix in ('77b6aefd', '97aa9560', 'a00f3e3d'):
        assert not events and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e




@pytest.mark.parametrize('prefix', ['0f557064', '142f9a8f', '6d1e330a', '96d7cc45', 'c01f17c4', 'c3985f64', 'c6f8c01d', 'dd44c6e6', 'e9aaec59', 'f43ad476', 'f6ee5e6f', 'fdeba080'])
def test_parser366_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser367_leftovers', lambda text, *args, **kwargs: ([], text)):
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
    events, leftover = extract_parser367_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]


@pytest.mark.parametrize('text', ['', 'Unsupported clause', '   '])
def test_empty_and_unknown_residuals(text):
    assert extract_parser367_leftovers(text, 'fr', 'fixture', '', None, None, None) == ([], text.strip())



def test_payload_semantics():
    shares = selected('15fca0c1')[0].payload
    assert (shares['entry'], shares['count'], shares['nominal']) == ('2333', '100', "1'000")
    revoked = selected('1b6eb4b8')[0].payload
    assert (revoked['effective_date'], revoked['time'], revoked['previous_until_date']) == ('05.10.2020', '10.00', '08.10.2020')
    managers = selected('2d4d020d')
    assert [e.payload['place'] for e in managers] == ['Saint-Cergue', 'Lausanne']
    assert all(e.role == 'Geschäftsführer' and e.signing == 'Kollektivunterschrift zu zweien' and e.payload['signing_restriction'] == 'avec un gérant' for e in managers)
    appeal = selected('37e0ff28')[0].payload
    # Preserve the dates printed in the notice, including the different years.
    assert (appeal['revocation_date'], appeal['extension_date'], appeal['decision_date']) == ('05.10.2010', '05.10.2010', '05.10.2020')
    origin = selected('6098826f')[0]
    assert (origin.payload['origin'], origin.payload['previous_origin'], origin.role, origin.signing) == ('Riaz', 'France', 'Geschäftsführer', 'Kollektivunterschrift zu zweien')
    split = selected('6ab95148')[0].payload
    assert (split['previous_count'], split['previous_nominal'], split['count'], split['nominal'], split['count_each']) == ('3', "8'000", '240', '100', '80')
    branch = selected('77b6aefd')[0].payload
    assert (branch['registry'], branch['branch_place'], branch['branch_uid']) == ('Zürich', 'Schlieren', 'CHE-414.553.879')
    transfer = selected('831e0472')[0].payload
    assert (transfer['retained_count'], transfer['transferred_count'], transfer['recipient_count'], transfer['nominal']) == ('100', '100', '100', '100')
    assert transfer['name'] != transfer['recipient']
    assert transfer['place'] is None and transfer['recipient_place'] == 'Lancy'
    assert selected('97aa9560')[0].payload['action'] == 'ancillary_obligations_erroneous_entry_corrected'
    restriction = selected('a00f3e3d')[0].payload
    assert (restriction['capital'], restriction['count'], restriction['nominal'], restriction['transfer_restriction']) == ("100'000", '100', "1'000", 'liées selon statuts')
    liquidator = selected('e34d012c')[0]
    assert liquidator.role == 'Liquidatorin' and liquidator.payload['place'] == 'Coppet'
    corrected = selected('f9481940')[0]
    assert corrected.role == 'Präsident des Verwaltungsrates' and corrected.signing == 'Einzelunterschrift'
    assert corrected.payload['previous_signing'] == 'Kollektivunterschrift zu zweien'


@pytest.mark.parametrize('prefix', ['77b6aefd', '97aa9560', 'a00f3e3d'])
def test_missing_or_unrelated_source_context_preserved(prefix):
    _, (args, kwargs) = captured(prefix)
    for source in ('', 'Unrelated context'):
        assert extract_parser367_leftovers(*args, source_text=source) == ([], args[0])


@pytest.mark.parametrize('prefix', ['1b6eb4b8', '37e0ff28'])
@pytest.mark.parametrize('time', ['24.00', '10.60'])
def test_invalid_revocation_time_preserved(prefix, time):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace('10.00', time)
    assert extract_parser367_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['6ab95148', '831e0472'])
def test_inconsistent_nominal_preserved(prefix):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].rsplit('CHF 100', 1)
    changed = 'CHF 200'.join(changed)
    assert extract_parser367_leftovers(changed, *args[1:], **kwargs) == ([], changed)
