import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser334 import extract_parser334_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('31628a88', 'de.text.ceo_origin_changed.v1', 1),
 ('39ec36b8', 'fr.text.share_holdings_after_transfer.v1', 1),
 ('43a6bf54', 'fr.text.german_foundation_officers.v1', 6),
 ('5b720f18', 'de.text.notarized_asset_transfer_no_consideration.v1', 1),
 ('6ac3eab0', 'de.text.further_conditional_capital_increase.v1', 1),
 ('8ea39615', 'de.text.statute_date_recorded.v1', 1),
 ('aa9d9002', 'fr.text.director_role_reinstated_correction.v1', 1),
 ('aae43f2b', 'fr.text.board_member_name_changed.v1', 1),
 ('c1edd5aa', 'fr.text.authorized_capital_clause_replaced.v1', 1),
 ('d8ea7c8b', 'fr.text.registered_share_transfer_restriction_removed.v1', 1),
 ('d92a31fa', 'fr.text.all_registered_shares_transfer_restriction_removed.v1', 2),
 ('f13ce517', 'it.text.collective_procuration_corrected.v1', 1)]


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
        return extract_parser334_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser334_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser334_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 433
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser334_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser334_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser334_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]



@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_bytes_match_supplied_samples(prefix, rule, count):
    supplied_sha256 = {'31628a88': '31628a88ee12b54eacb9ecabf104b5ff47cdd0a95c9efd6e87b9deb3fde8e1a5',
     '39ec36b8': '39ec36b8e10456122620ceca55183d1c7f0e9c510f492af440928ad282257ab9',
     '43a6bf54': '43a6bf548ea229c290ebd138243289118329569e9566149ed28b7fcddd8d177b',
     '5b720f18': '5b720f1866185b151d0c18a7b20ade378c83dfc6a1c713163d18e4c09e2ba309',
     '6ac3eab0': '6ac3eab092feb7d1e9f6e6f7f9a700e525bf9bf7fcf53fae304fa38757cadb60',
     '8ea39615': '8ea396150f6b5dcb007ada4f0267dc3d641ef62c5aa7a4b97d8ec47708faf178',
     'aa9d9002': 'aa9d9002587231d8a542a458d9a6dd2f48294aae1b166d3fe9e801ba0470684a',
     'aae43f2b': 'aae43f2b2aaceb0e2a41891a45fdf0be942aa70ebf6bbb6f04fc90dd6f591a17',
     'c1edd5aa': 'c1edd5aa8db02b124c39e80920d3f67040b6a2b0e8e415130536fdf689cdceff',
     'd8ea7c8b': 'd8ea7c8be35e2e2043656c5a6633c3fb0f7f4d4afe349dbdf66a9618370a23ad',
     'd92a31fa': 'd92a31fa055b408f8879dcd9874deff330f039d9bcea67afb282b400087ace46',
     'f13ce517': 'f13ce5178a4e6fa18ba41ff1f2a0ffb68163552d3be7c7acee5548fca95325fa'}
    fixture = path(prefix)
    assert fixture.stem == supplied_sha256[prefix]
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == supplied_sha256[prefix]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_dates_and_optional_source(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser334_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser334_leftovers(*args)
    assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e


@pytest.mark.parametrize('prefix', [
    '9765f439',
    '3d59d275',
    'aed2920b',
    'd91cf46b',
    '1d268a23',
    '9291f6ad',
    '81f3bc9e',
    '3450837a',
    '129135ad',
    '5378918f',
    '01927b94',
    '5f87b480',
    '0629cb21', '08c613ba', '267dd215', '50985666', '5dad8aa2', '87ac66e7',
    'a9eb2fc1', 'c2b60397', 'ddedd79d', 'f632cfcf', 'f698c58d', 'f7ee7573',
    '09f90c1f', '28528abc', '3e71da53', '762ea6e8', '7f11be01', '950a0991',
    '9c5c898c', 'bb4542dd', 'd518eb02', 'f63aa392', 'f663e109', 'f8fc2919',
    '03dcc069', '315da231', '353d9e29', '693c452c', '7c27565a', '8889623a',
    'a5f4be23', 'bbf607eb', 'c332722f', 'ce010fcd', 'cfbe1db2', 'f0fd9d83',
    '518fef8d', '5404cc5f', '54125ed4', '6d18ed72', '6d50c77a', '7a6515f3',
    '930507a1', 'a16a5540', 'a564e09d', 'b384c365', 'cf527290', 'ecba5198',
    '05a6f15b', '076b6cc6', '0f17b349', '3774d2b6', '54b4ab1b', '58504ce5',
    '68ffaf6b', '87d4b8af', '950a846d', 'a51340d6', 'bb7c8a65', 'f970cd7e',
    '20f4e032', '38b520f1', '433558ba', '4d97f0a8', '4e13c196', '732e61bf', '92ab8218', 'a7271172', 'ae9ac4da', 'bb279338', 'da10e733', 'fa099435',
    '1cf200d1', 'c9cb541c', 'e3c5c5cd', '94b72118-d3cb-46f4-8cf3-8d526586b9f2',
])
def test_previous_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser334_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old


def test_payload_semantics():
    assert selected('31628a88')[0].payload['origin'] == 'Apples'
    assert selected('31628a88')[0].signing == 'Kollektivunterschrift zu zweien'
    shares = selected('39ec36b8')[0]
    assert shares.event_type == 'ownership_changed'
    assert shares.payload['transferred_count'] == '98'
    assert shares.payload['count1'] == '99' and shares.payload['count2'] == '1'
    officers = selected('43a6bf54')
    assert officers[0].event_type == 'officer_removed'
    assert officers[2].payload['known_as'] == 'Serge'
    assert officers[2].payload['place'] == 'St. Gallen'
    assert officers[2].role == 'Mitglied des Stiftungsrates, Aktuar'
    assert officers[2].payload['origin'] == 'Glarus'
    assert officers[2].payload['previous'].startswith('Leuzinger, Dr. Serge,')
    assert officers[3].role == 'Mitglied des Stiftungsrates, Kassier'
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in officers[1:4])
    assert all(e.signing == 'ohne Zeichnungsberechtigung' for e in [officers[0], *officers[4:]])
    asset = selected('5b720f18')[0]
    assert asset.payload['no_consideration'] is True
    assert asset.payload['assets'] == "545'816.70" and asset.payload['liabilities'] == '0.00'
    assert asset.payload['properties'] == 'GB Freienbach Nr. 1699 und Nr. 1725'
    assert selected('6ac3eab0')[0].event_type == 'capital_changed'
    assert selected('8ea39615')[0].payload['statute_date'] == '26.11.2019'
    assert selected('aa9d9002')[0].role == 'Verwaltungsrat und Direktor'
    renamed = selected('aae43f2b')[0]
    assert renamed.payload['previous_name'] == 'Müller-Boschung Ruth'
    assert renamed.payload['name'] == 'Neuhaus Ruth'
    assert renamed.signing == 'Kollektivunterschrift'
    assert selected('c1edd5aa')[0].payload['previous_authorization'] == '28 juin 2018'
    capital = selected('d8ea7c8b')[0]
    assert capital.payload['count'] == "30'966" and capital.payload['capital'] == "3'096'600"
    assert capital.payload['fully_paid'] is True
    restriction, liquidator = selected('d92a31fa')
    assert restriction.event_type == 'capital_changed'
    assert liquidator.role == 'Verwaltungsrat und Liquidator' and liquidator.signing is None
    assert liquidator.payload['place'] == 'Goumoëns'
    assert selected('f13ce517')[0].signing == 'Kollektivprokura zu zweien'


def test_invalid_french_date_preserved():
    _, (args, kwargs) = captured('c1edd5aa')
    changed = args[0].replace('25 juin 2020', '31 juin 2020')
    events, leftover = extract_parser334_leftovers(changed, *args[1:], **kwargs)
    assert events == [] and leftover == changed


@pytest.mark.parametrize('old,new', [
    ('Mitglied des Stiftungsrates, Aktuar', 'Unbekannte Funktion'),
    ('ohne Zeichnungsberechtigung', 'unbekannte Zeichnung'),
])
def test_incomplete_foundation_section_preserved(old, new):
    _, (args, kwargs) = captured('43a6bf54')
    changed = args[0].replace(old, new, 1)
    events, leftover = extract_parser334_leftovers(changed, *args[1:], **kwargs)
    assert events == [] and leftover == changed
