import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser376 import extract_parser376_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('35b36db6', 'de.text.foreign_officer_erroneous_mutation_corrected.v1', 1), ('3fc4bb9d', 'de.text.duplicate_auditor_departure_revoked.v1', 1), ('4da7e6fc', 'de.text.judgment_liquidation_registration_reinstated.v1', 1), ('593161c7', 'fr.text.statutes_date_typo_notice_corrected.v1', 1), ('5cd02639', 'de.text.single_judge_summary_bankruptcy_reinstated.v1', 1), ('6615228f', 'fr.text.president_and_female_director_residence_changed.v1', 2), ('6c3ba07a', 'de.text.board_declaration_audit_waived.v1', 1), ('831a034a', 'fr.text.german_liquidation_french_publication_two_officers.v1', 4), ('952b2ff7', 'fr.text.authorized_capital_replaced_two_detail_notices.v1', 1), ('a0b2838e', 'de.text.three_additional_addresses_two_previous.v1', 1), ('a2a1c0b2', 'de.text.mixed_shares_liquidation_municipality_merger.v1', 2), ('edd61936', 'fr.text.person_exact_name_corrected.v1', 1)]
SUPPLIED_SHA256 = {'35b36db6': '35b36db65b2f336b27e0a5e4d4095fc7f5816f8290a729d0bb45875a674b37bd', '3fc4bb9d': '3fc4bb9de6e36ecfa892ad0dcf8bee65afda2cb92afb8077e6ee1a47589b788f', '4da7e6fc': '4da7e6fc017687d6ef37530ca20701236ccc6d313b65e77b1b80db69964f41e4', '593161c7': '593161c78d6983580360de8c0a70e29354e6c1580453e68a332605c50476a67b', '5cd02639': '5cd02639c79a636be051955aab215b53cf55bbf291256ee416676d952fbfdc9d', '6615228f': '6615228f1f7d7ef8eed39c5a9e13f9254af0c05409bc86dacb21d5c9fbe933c4', '6c3ba07a': '6c3ba07ad016899a6e0ebf38e64d5dcae3972b4b06dde4302ecffb8cd32e6fef', '831a034a': '831a034a0426bfea6ff2c3df2c442023a6e2f2626ce05f0c22b230d890296bc3', '952b2ff7': '952b2ff750d3e4f29f8760016a67e6ed8988b42d3de480949a039035cf5fece7', 'a0b2838e': 'a0b2838ec13717c66393e27270f3aa093ef5e54568584de670555f9d9903e653', 'a2a1c0b2': 'a2a1c0b2cea78bbe2bf72a3c726492e91701ca42c6e2670b51302300f4cf60d8', 'edd61936': 'edd619364e4ba82d12c9e1e534ea7321bd00e65fda15fdc329d2e2ca6cfebcb7'}

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
        return extract_parser376_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser376_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser376_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 424
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser376_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser376_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser376_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser376_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser376_leftovers(*args)
    assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e



@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_optional_metadata_absent(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser376_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old


@pytest.mark.parametrize('version', [260, 283, 314, 322, 345, 350, 353, 375])
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
        assert extract_parser376_leftovers(*args, **kwargs) == ([], args[0])
        with patch.object(parser, 'extract_parser376_leftovers', lambda text, *a, **kw: ([], text)):
            assert parse_publication_xml(fixtures[0]) == actual
        with patch.object(parser, name, lambda text, *a, **kw: ([], text)):
            disabled = parse_publication_xml(fixtures[0])
        assert not any(e.rule_id in {case[1] for case in CASES} for e in disabled.events)
        checked += 1
    assert checked


def test_payload_semantics():
    p = selected('35b36db6')[0].payload
    assert (p['entry'], p['notice'], p['nationality']) == ('39513', '204', 'deutscher')
    p = selected('3fc4bb9d')[0].payload
    assert (p['auditor_uid'], p['entry'], p['entry_date']) == ('CHE-105.253.715', '38443', '08.10.2020')
    assert selected('4da7e6fc')[0].event_type == 'status_changed'
    assert selected('4da7e6fc')[0].payload['deletion_date'] == '04.05.2020'
    p = selected('593161c7')[0].payload
    assert (p['statutes_date'], p['previous_statutes_date']) == ('14 mai 2019', '15 mai 2019')
    assert selected('5cd02639')[0].payload['dissolved_by_bankruptcy'] is True
    president, director = selected('6615228f')
    assert (president.role, director.role) == ('président', 'administratrice')
    assert president.signing is None and director.signing is None
    assert director.payload['procuration_revoked'] is True
    audit = selected('6c3ba07a')[0]
    assert audit.event_type == 'audit_requirement_changed'
    assert audit.payload['ordinary_audit'] is False and audit.payload['limited_audit_waived'] is True
    status, address, associate, liquidator = selected('831a034a')
    assert (status.event_type, address.event_type) == ('status_changed', 'address_changed')
    assert associate.signing == 'ohne Zeichnungsberechtigung'
    assert liquidator.signing == 'Einzelunterschrift' and 'Liquidator' in liquidator.role
    p = selected('952b2ff7')[0].payload
    assert (p['authorization_date'], p['removal_date'], p['introduction_date']) == ('22 novembre 2019', '23 octobre 2020', '23 octobre 2020')
    addresses = selected('a0b2838e')[0]
    assert addresses.event_type == 'address_changed'
    assert all(key in addresses.payload for key in ('address1', 'address2', 'address3', 'previous_address1', 'previous_address2'))
    status, liquidator = selected('a2a1c0b2')
    assert status.event_type == 'status_changed'
    assert liquidator.payload['shares'] == "3 Stammanteile zu CHF 6'000, 1 Stammanteil zu CHF 2'000"
    assert liquidator.payload['place'] == 'Wünnewil-Flamatt' and liquidator.signing == 'Einzelunterschrift'
    p = selected('edd61936')[0].payload
    assert (p['previous_name'], p['name']) == ('de Bruyne Sylvain', 'De Bruyne Sylvain')


@pytest.mark.parametrize('prefix', ['593161c7', '952b2ff7'])
def test_invalid_written_dates_preserve_remainder(prefix):
    _, (args, kwargs) = captured(prefix)
    changed = re.sub(r'\d{1,2} (mai|novembre|octobre) \d{4}', '31 février 2020', args[0])
    assert changed != args[0]
    assert extract_parser376_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('version,pattern,text', [
    (69, '_DE_COMPANY_REINSTATED_FOR_LIQUIDATION', 'Die am 04.05.2020 gelöschte Gesellschaft wird auf Grund des Urteils des Einzelrichters des Bezirksgerichts Zürich vom 23.10.2020 zum Zwecke der Liquidation wieder in das Handelsregister eingetragen und besteht entsprechend den früheren Eintragungen weiter'),
    (189, '_FR_AUTHORIZED_CAPITAL_REPLACED', "L'assemblée générale a supprimé une clause statutaire relative à une augmentation autorisée du capital (selon décision du 22 novembre 2019) par décision du 23 octobre 2020. L'assemblée générale a introduit une clause statutaire relative à une augmentation autorisée du capital par décision du 23 octobre 2020. Pour les détails, voir les statuts"),
])
def test_reused_legacy_patterns_preserve_remainder(version, pattern, text):
    from importlib import import_module
    module = import_module(f'shab_analyzer.parser{version}')
    language = 'de' if version == 69 else 'fr'
    args = (text, language, 'fixture', '', None, None, None)
    assert getattr(module, pattern).fullmatch(text)
    assert getattr(module, f'extract_parser{version}_leftovers')(*args)[0]
    assert extract_parser376_leftovers(*args) == ([], text)

    padded = '  ' + text + '  '
    assert extract_parser376_leftovers(padded, *args[1:]) == ([], padded)
