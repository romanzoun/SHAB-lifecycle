import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser375 import extract_parser375_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('0b8b7779', 'fr.text.two_associates_share_nominal_corrected.v1', 1), ('0e5f7767', 'fr.text.share_transfer_new_female_collective_manager.v1', 2), ('0ebd4d6f', 'de.text.previous_residence_system_error_corrected.v1', 1), ('1df23e2a', 'de.text.business_assets_liabilities_split_transferred.v1', 1), ('2142c705', 'it.text.associate_given_name_corrected_unsigned.v1', 1), ('5081a50d', 'fr.text.cooperative_publication_personal_member_communications.v1', 1), ('7bafb585', 'it.text.wholly_owned_merger_without_quota_allocation.v1', 1), ('a04b615d', 'fr.text.corporate_associate_swiss_seat_changed.v1', 1), ('b8fb191a', 'de.text.asset_transfer_duplicated_currency.v1', 1), ('bc2ed02a', 'de.text.conditional_increase_authorized_capital_adjusted.v1', 1), ('e40305db', 'fr.text.two_liquidators_individual_signing.v1', 2), ('ed29e8f8', 'de.text.previously_introduced_authorized_capital_changed.v1', 1)]
SUPPLIED_SHA256 = {'0b8b7779': '0b8b7779b4fa0ecc701250d37f0d7919fc591787dd50cc00eb65d65161024ea9', '0e5f7767': '0e5f7767216ff2afd5a694f73788ec70909e38eed3b421516e44ccfc3f192ebb', '0ebd4d6f': '0ebd4d6fb51cab94d8aba4decf2c2c2e09d8b3ba65207f2377a0157e44da0f30', '1df23e2a': '1df23e2a9564028626ba99e31de485c1153448245752de6a5682f248bc7643f5', '2142c705': '2142c7054e4c649bcb5676ef0be3188ecd42511cb87c310381bedc543246ffc8', '5081a50d': '5081a50dc6d0e5c92c01785c24f72af337d82597db8267bf37754231d6e443fd', '7bafb585': '7bafb58574c414ce5e0aabb7f89ca722aad8dffc930deacec902a114ab809f3c', 'a04b615d': 'a04b615dbc2b2de50a5c873d27746125d4270d58970da77122b876780a5cbb23', 'b8fb191a': 'b8fb191aa9ba65001f8b0a33d1a384a432525a47370767ff78a3b229ac325414', 'bc2ed02a': 'bc2ed02af2152e83f21bf89d53eba35c3b4a314ed5398d7a3ceba006f197c5fe', 'e40305db': 'e40305dbfec660f4666b99905383565754638c77e6aa87fefda2a6464b771d14', 'ed29e8f8': 'ed29e8f84799da73639d86d6a90c0ea8d9971850ed55e5632c6381cc978b2ceb'}

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
        return extract_parser375_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser375_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser375_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 444
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser375_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser375_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser375_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser375_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser375_leftovers(*args)
    if prefix in ('0e5f7767', '2142c705', 'bc2ed02a'):
        assert not events and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e





@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_optional_metadata_absent(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser375_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old




@pytest.mark.parametrize('prefix', ['0e5f7767', '2142c705', 'bc2ed02a'])
def test_source_required(prefix):
    _, (args, kwargs) = captured(prefix)
    assert extract_parser375_leftovers(*args, source_text='Unrelated.') == ([], args[0])
    assert extract_parser375_leftovers(*args, source_text=kwargs['source_text']+' UNKNOWN.') == ([], args[0])


def test_payload_semantics():
    p = selected('0b8b7779')[0].payload
    assert (p['count1'], p['count2'], p['nominal'], p['previous_nominal']) == ('12', '8', "1'000", '100')
    transfer, manager = selected('0e5f7767')
    assert (transfer.payload['before'], transfer.payload['transferred'], transfer.payload['remaining']) == ('130', '5', '125')
    assert manager.signing == 'Kollektivunterschrift zu zweien'
    corrected = selected('2142c705')[0]
    assert corrected.payload['given'] != corrected.payload['previous_given']
    assert corrected.signing == 'ohne Zeichnungsberechtigung'
    merger = selected('7bafb585')[0]
    assert merger.event_type == 'company_merged'
    assert merger.payload['wholly_owned'] is True and merger.payload['share_allocation'] is False
    assert selected('1df23e2a')[0].event_type == 'assets_transferred'
    assert selected('b8fb191a')[0].event_type == 'assets_transferred'
    assert selected('b8fb191a')[0].payload['assets'] == "46'167'000.00"
    p = selected('bc2ed02a')[0].payload
    assert (p['statutes_date'], p['conditional_date'], p['authorized_date']) == ('10.11.2020', '03.11.2020', '19.10.2020')
    assert all(e.role == 'Liquidator' and e.signing == 'Einzelunterschrift' for e in selected('e40305db'))


@pytest.mark.parametrize('version', [278, 295, 301, 338, 363, 374])
def test_earlier_rules_keep_ownership_when_disabled(version):
    import shab_analyzer.parse as parser
    source = (Path(__file__).parent / f'test_parser{version}.py').read_text()
    prefixes = set(re.findall(r"['\"]([0-9a-f]{8})(?:[0-9a-f]{56})?['\"]", source))
    name = f'extract_parser{version}_leftovers'
    original = getattr(parser, name)
    checked = 0
    for prefix in sorted(prefixes):
        fixtures = list(FIXTURES.glob(prefix + '*.xml'))
        if len(fixtures) != 1:
            continue
        calls = []
        def capture(*args, **kwargs):
            calls.append((args, kwargs))
            return original(*args, **kwargs)
        with patch.object(parser, name, capture):
            actual = parse_publication_xml(fixtures[0])
        if not calls or not original(*calls[0][0], **calls[0][1])[0]:
            continue
        args, kwargs = calls[0]
        assert extract_parser375_leftovers(*args, **kwargs) == ([], args[0])
        with patch.object(parser, 'extract_parser375_leftovers', lambda text, *a, **kw: ([], text)):
            assert parse_publication_xml(fixtures[0]) == actual
        with patch.object(parser, name, lambda text, *a, **kw: ([], text)):
            disabled = parse_publication_xml(fixtures[0])
        assert not any(e.rule_id in {case[1] for case in CASES} for e in disabled.events)
        checked += 1
    assert checked

@pytest.mark.parametrize('version,filename', [
    (145, '79688b8e-f754-41b8-b9dc-9a2cd16a6efd.xml'),
    (174, '0c6eadb5-d6cf-49d1-a9f7-70a2fdf5b1e0.xml'),
])
def test_reused_legacy_patterns_preserve_complete_remainder(version, filename):
    import shab_analyzer.parse as parser
    original = getattr(parser, f'extract_parser{version}_leftovers')
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return original(*args, **kwargs)
    with patch.object(parser, f'extract_parser{version}_leftovers', capture):
        parse_publication_xml(FIXTURES / filename)
    args, kwargs = calls[0]
    assert original(*args, **kwargs)[0]
    assert extract_parser375_leftovers(*args, **kwargs) == ([], args[0])
