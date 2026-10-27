import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser382 import extract_parser382_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('0492851b', 'fr.text.pair_individual_signing_second_origin_changed.v1', 2), ('52b8aa3d', 'fr.text.board_presidency_pair_continued_joint_signing.v1', 2), ('61df964d', 'de.text.bankruptcy_closed_registration_retained_assigned_claims.v1', 1), ('6df68272', 'de.text.erroneous_deletion_reinstated_in_liquidation.v1', 1), ('76acd1d3', 'de.text.publication_organ_notice_supplement.v1', 1), ('8453c027', 'it.text.common_shareholder_merger_subordinated_claims_raw_balance.v1', 1), ('9d6b8caf', 'fr.text.new_associates_mixed_restricted_signing.v1', 2), ('9f8952fe', 'fr.text.association_judicial_dissolution_bankruptcy_liquidation.v1', 1), ('a4bb65b5', 'it.text.wholly_owned_merger_without_capital_increase.v1', 1), ('c905e7be', 'de.text.auditor_name_changed_same_uid.v1', 1), ('ece53437', 'fr.text.erroneous_bankruptcy_paid_before_judgment_corrected.v1', 1), ('eedae8e0', 'de.text.conversion_capital_increase_deficit_eliminated.v1', 2)]
SUPPLIED_SHA256 = {'0492851b': '0492851b5f13d686a8f10bcfad0cb28328ffef1e65969009f6bd5c21ae8dab88', '52b8aa3d': '52b8aa3db0cd0bf126cd689eeb02e0ac0510e69e758c75cbc7521e721bba32a4', '61df964d': '61df964dab22abc0de49cb052656d9930a90b8339a862af450536655e16b31ca', '6df68272': '6df68272ef26204f3e0d8699a24966e58fb3f7aec7f998724cf8b6ea876faeb8', '76acd1d3': '76acd1d30c9864d1143c6533ad2a3d71aa0dd440affd76f59a27be2472e4762a', '8453c027': '8453c0277a6581116a9ef4fd16822f4a24fc2d4101243ee8c0d4865f8eb23c9c', '9d6b8caf': '9d6b8cafa858b4b8e27e686fdc48424401baf987262961cbba92f6313f2f03a6', '9f8952fe': '9f8952fe9becc0b22d92a1d268c2f85ddab0fb40b8f87fd77034851631886354', 'a4bb65b5': 'a4bb65b56f65abafd298468a1aa16006f402c51cb15029b0dde286144852061f', 'c905e7be': 'c905e7be1d9a89e23c578e5c16852e32a400c030ba377cf73430d6c298249a6e', 'ece53437': 'ece534370c8e7c21171701b3f36fa0c02c49e76d53f3b55a2e2f11223ed6389f', 'eedae8e0': 'eedae8e06aad8a845fd41cbfea85b58297d82365ef9509fe995fc2dfbb504608'}
CONTEXT_REQUIRED = {'9d6b8caf'}

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
        return extract_parser382_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser382_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser382_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 414
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser382_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser382_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser382_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        if prefix == '8453c027' and date == '31.09.2020':
            continue  # This attested malformed date is preserved, never corrected.
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser382_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser382_leftovers(*args)
    if prefix in CONTEXT_REQUIRED:
        assert not events and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e



@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_optional_metadata_absent(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser382_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old



@pytest.mark.parametrize('version', [266, 295, 319, 320, 328, 345, 347, 374, 381])
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
        assert extract_parser382_leftovers(*args, **kwargs) == ([], args[0])
        with patch.object(parser, 'extract_parser382_leftovers', lambda text, *a, **kw: ([], text)):
            assert parse_publication_xml(fixtures[0]) == actual
        with patch.object(parser, name, lambda text, *a, **kw: ([], text)):
            disabled = parse_publication_xml(fixtures[0])
        assert not any(e.rule_id in {case[1] for case in CASES} for e in disabled.events)
        checked += 1
        break  # One owned fixture per version; additional legacy regressions run separately.
    assert checked




def test_payload_semantics():
    a, b = selected('0492851b')
    assert a.signing == b.signing == 'Einzelunterschrift'
    assert b.payload['origin2'] == 'Bex'
    a, b = selected('52b8aa3d')
    assert a.role == "membre du conseil d'administration, président"
    assert b.role == "membre du conseil d'administration"
    assert a.signing == b.signing == 'Kollektivunterschrift zu zweien'
    retained = selected('61df964d')[0]
    assert retained.event_type == 'status_changed'
    assert retained.payload['registration_retained'] is True
    assert retained.payload['organs_authority_restored'] is False
    assert retained.payload['decision_date'] == '20.11.2020'
    assert selected('6df68272')[0].payload['in_liquidation'] is True
    assert selected('6df68272')[0].payload['reinstated'] is True
    assert selected('76acd1d3')[0].event_type == 'publication_corrected'
    assert selected('76acd1d3')[0].payload['entry'] == '8399'
    merger = selected('8453c027')[0]
    assert merger.payload['balance_date'] == '31.09.2020'
    assert merger.payload['balance_date_valid'] is False
    assert merger.payload['claims_subordinated'] is True
    assert merger.payload['assets'] == "164'708.00"
    for prefix in ('8453c027', 'a4bb65b5'):
        assert selected(prefix)[0].payload['capital_increase'] is False
        assert selected(prefix)[0].payload['share_allocation'] is False
    a, b = selected('9d6b8caf')
    assert a.signing == 'Einzelunterschrift' and a.role == 'associé'
    assert b.signing == 'Kollektivunterschrift zu zweien' and b.role == 'associée'
    assert b.payload['signing_restriction'] == 'avec Mathey-Doret di Doret Marc ou Nunez Stéphanie ou Pirkl Peter ou Bron Jacques-Alain'
    assert 'signing_restriction' not in a.payload
    dissolved = selected('9f8952fe')[0]
    assert dissolved.event_type == 'status_changed'
    assert dissolved.payload['decision_date'] == '16.10.2020'
    auditor = selected('c905e7be')[0]
    assert auditor.event_type == 'auditor_changed'
    assert auditor.payload['uid'] == 'CHE-101.335.923'
    assert auditor.payload['name'] == 'CORE Revision AG'
    correction = selected('ece53437')[0]
    assert correction.event_type == 'publication_corrected'
    assert correction.payload['debt_paid_before_bankruptcy'] is True
    assert correction.payload['entry'] == '15865'
    conversion, offset = selected('eedae8e0')
    assert conversion.event_type == 'organization_changed'
    assert conversion.payload['capital'] == "110'100.00"
    assert conversion.payload['shares'] == "11'010'000"
    assert conversion.payload['deficit_eliminated'] is True
    assert offset.event_type == 'capital_changed'
    assert offset.payload['offset'] == "199'999.21"
    assert offset.payload['offset_shares'] == "413'820"


def test_signing_context_must_match_exact_person_and_phrase():
    _, (args, kwargs) = captured('9d6b8caf')
    source = kwargs['source_text']
    for changed in ('', 'unrelated', source.replace('signature individuelle', 'signature collective à trois'), source.replace('Bron Jacques-Alain', 'Autre Exemple')):
        assert extract_parser382_leftovers(*args, source_text=changed) == ([], args[0])


def test_reused_legacy_pattern_keeps_exact_residue():
    from shab_analyzer.parser67 import _FR_ADMINISTRATORS_SIGN_INDIVIDUALLY
    text = 'Exemple Anne et Exemple Paul, administrateurs, signent désormais individuellement.'
    assert _FR_ADMINISTRATORS_SIGN_INDIVIDUALLY.fullmatch(text)
    assert extract_parser382_leftovers(text, 'fr', 'fixture', '', None, None, None) == ([], text)


def test_auditor_uid_change_is_not_a_rename():
    _, (args, kwargs) = captured('c905e7be')
    changed = args[0].rsplit('CHE-101.335.923', 1)
    changed = 'CHE-999.999.999'.join(changed)
    assert extract_parser382_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('version,stem', [
    (67, '5f1f0196-7817-4694-a157-960d69a9f64c'),
    (222, '4119a85b-5880-41df-9c42-410d7162475f'),
    (246, '4cb0bdb6-9d33-4be7-bb30-399a77c0f521'),
    (250, 'ac53ec64-f007-447a-921f-3239d448fd20'),
])
def test_older_fixture_ownership_with_disabled_legacy_rule(version, stem):
    import shab_analyzer.parse as parser
    name = f'extract_parser{version}_leftovers'
    original = getattr(parser, name)
    calls = []

    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return original(*args, **kwargs)

    fixture = FIXTURES / (stem + '.xml')
    with patch.object(parser, name, capture):
        actual = parse_publication_xml(fixture)
    assert calls
    for old_args, old_kwargs in calls:
        assert extract_parser382_leftovers(*old_args, **old_kwargs) == ([], old_args[0])
    args, kwargs = calls[0]
    assert original(*args, **kwargs)[0]
    assert extract_parser382_leftovers(*args, **kwargs) == ([], args[0])
    with patch.object(parser, 'extract_parser382_leftovers', lambda text, *a, **kw: ([], text)):
        assert parse_publication_xml(fixture) == actual
    with patch.object(parser, name, lambda text, *a, **kw: ([], text)):
        disabled = parse_publication_xml(fixture)
    assert not any(e.rule_id in {case[1] for case in CASES} for e in disabled.events)
