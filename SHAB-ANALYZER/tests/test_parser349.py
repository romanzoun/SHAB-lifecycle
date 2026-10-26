import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser349 import extract_parser349_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('0bd210d8', 'fr.text.board_members_departed_signatures_revoked.v1', 2), ('20e004f9', 'fr.text.branch_seat_transferred.v1', 1), ('3ce9b632', 'de.text.endowment_capital_created_or_increased.v1', 1), ('56179eca', 'de.text.incorporation_contribution_acquisition_details.v1', 1), ('9f7e3aa9', 'fr.text.shares_transferred_new_associate_manager.v1', 3), ('c2d438fb', 'fr.text.associates_collective_signing.v1', 2), ('d10f9522', 'fr.text.board_co_presidents_continued_signing.v1', 2), ('da81d9fb', 'de.text.liquidation_not_completed_correction.v1', 1), ('e3ed525f', 'fr.text.general_director_and_deputy_appointed.v1', 2), ('e6fa8515', 'de.text.branch_entries_updated.v1', 1), ('ea435444', 'it.text.covid_moratorium_granted.v1', 1), ('f9a68ce8', 'fr.text.signature_revoked_individual_procuration_granted.v1', 1)]
SUPPLIED_SHA256 = {'0bd210d8': '0bd210d8e827bbd34d3edfc43164f2a3a28eecebbda74cb8444d531ebfc217da', '20e004f9': '20e004f9f499f27fc32765763d966f603b5cefe475805998bc12f6521c30ada9', '3ce9b632': '3ce9b63252ec94ff29649d7b7d789df6dbb0f59fa5b276fd20f712ccf029614b', '56179eca': '56179ecaa01f79ee67a121b68bcf438c29a5f9229a896c814947a1c6f5a6218e', '9f7e3aa9': '9f7e3aa9ad939f278e3d5e8af760ee399e73433105e5d65cec917e557eceb173', 'c2d438fb': 'c2d438fba4cce05df99323644b9eb0e376ff178bb8d5dfc5dc2ecd05d796bd63', 'd10f9522': 'd10f9522212146230a749d1e24fe38b1f2f6355239ce9e2399a0f5bc01becaec', 'da81d9fb': 'da81d9fb9004a01de4a4e1276e8e83c7055228dc1991b2718bf5fd26bf809438', 'e3ed525f': 'e3ed525f5842f44a713caa3594bf6d80b6ac1f4053d77410765741514bb0a593', 'e6fa8515': 'e6fa851515d2193921168a05e363e72cbad9e941eefd9b6af1f6d022476ec109', 'ea435444': 'ea43544403cd5d57666b70bc65d5274a8ba8105dbc2857eb73f2a3b3b15f7b3d', 'f9a68ce8': 'f9a68ce8584f11a8356584a223c3727d2c84986b859596b3652cec65329ba432'}

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
        return extract_parser349_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser349_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser349_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 400
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser349_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser349_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser349_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser349_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser349_leftovers(*args)
    if prefix == '56179eca':
        assert not events and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e


@pytest.mark.parametrize('prefix', ['bcf422aa', '2ee7eb0d', 'c5fa5c4d', 'f2300fb5', '360fedd4', '0ab39892', 'c9b3ebd6', 'a1e7ae61', '6fa3fe10', 'c9637524', 'a60779f4', 'fa9ce006'])
def test_previous_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser349_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old






@pytest.mark.parametrize("prefix", ['26ca1aa6', '2f33710a', '434b77f3', '459e4a0a', '5830f519', '8a791e50', '8e6b1453', '9e9d9a28', 'a966266d', 'df2deff6', 'e2ed9941', 'f5442777'])
def test_parser348_results_unchanged(prefix):
    test_previous_results_unchanged_without_optional_attributes(prefix)


def test_payload_values_and_person_semantics():
    assert selected('20e004f9')[0].payload['uid'] == 'CHE-152.037.330'
    assert selected('3ce9b632')[0].payload['amount'] == "27'603'000.00"
    contribution = selected('56179eca')[0].payload
    assert contribution['count'] == '140' and contribution['credit'] == '661.42'
    transfer = selected('9f7e3aa9')
    assert transfer[0].payload['count'] == '99'
    assert transfer[0].payload['remaining_count'] == '101'
    assert transfer[1].signing is None
    assert transfer[2].signing == 'Einzelunterschrift'
    assert [e.signing for e in selected('0bd210d8')] == ['gelöscht'] * 2
    assert len({e.person_key for e in selected('0bd210d8')}) == 2
    assert [e.role for e in selected('d10f9522')] == ['Co-Präsident'] * 2
    assert [e.signing for e in selected('c2d438fb')] == ['Kollektivunterschrift zu zweien'] * 2
    assert selected('f9a68ce8')[0].signing == 'Einzelprokura'
    assert selected('ea435444')[0].payload['months'] == '3'
    assert selected('da81d9fb')[0].payload['action'] == 'liquidation_not_completed_correction'
    assert [e.role for e in selected('e3ed525f')] == ['Generaldirektor', 'Stellvertretender Generaldirektor']
    assert selected('e6fa8515')[0].payload['uid3'] == 'CHE-343.368.740'


def test_unbalanced_contribution_preserved():
    _, (args, kwargs) = captured('56179eca')
    text = args[0].replace('140 Stammanteile', '200 Stammanteile')
    assert extract_parser349_leftovers(text, *args[1:], **kwargs) == ([], text)
