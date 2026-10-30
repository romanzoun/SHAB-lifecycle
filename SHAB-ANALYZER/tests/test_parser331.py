import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser331 import extract_parser331_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('0629cb21', 'fr.text.board_presidency_changed.v1', 4),
    ('08c613ba', 'fr.text.share_transfer_manager_president.v1', 3),
    ('267dd215', 'it.text.merger_common_shareholders_coverage.v1', 1),
    ('50985666', 'fr.text.administrator_signing_corrected.v1', 1),
    ('5dad8aa2', 'de.text.asset_transfer_eur.v1', 1),
    ('87ac66e7', 'de.text.cross_border_merger_subordination.v1', 1),
    ('a9eb2fc1', 'fr.text.administrators_not_directors_corrected.v1', 2),
    ('c2b60397', 'fr.text.person_residence_corrected.v1', 1),
    ('ddedd79d', 'de.text.asset_transfer_without_liabilities.v1', 1),
    ('f632cfcf', 'de.text.additional_conditional_capital.v1', 1),
    ('f698c58d', 'fr.text.collective_procuration_with_administrator.v1', 4),
    ('f7ee7573', 'fr.text.two_managers_share_transfer_remaining.v1', 2),
]


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
        return extract_parser331_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser331_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser331_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 435
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser331_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser331_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser331_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]



@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_bytes_match_supplied_samples(prefix, rule, count):
    supplied_sha256 = {
        '0629cb21': '0629cb21531aabe22ee0ce5c19656985d32b1f8b525f55e7b715ed09158d701b',
        '08c613ba': '08c613ba58fbcbf133e5b9148db8790be54b7b1b97f176a6aebfc745a69fad71',
        '267dd215': '267dd215ce0a536fc00accf16c07a5776325c2ebfbdabb78b98a834669de1a31',
        '50985666': '50985666b411f98988d76ade0e78fde878d8b17d61cbdaf6ab4eb114a40ab48c',
        '5dad8aa2': '5dad8aa249983e2351a62f7e7d34e648b90ad162842d9f8c72b227420f56a964',
        '87ac66e7': '87ac66e79045aae4af8fe9c01a556e69079cf2611d6e8cabaa7640b08ac353e1',
        'a9eb2fc1': 'a9eb2fc116b1233a3300ae030c1bf83753cb3b6544909bd61aedb4a4ac4bc97a',
        'c2b60397': 'c2b6039729c7964d6c903bc01242f986401244a7e8cf07d63382313b52a0e6cf',
        'ddedd79d': 'ddedd79dcc79774a3dcff1e939cd0613201f589c2cc1a1bf4914e46281193b0d',
        'f632cfcf': 'f632cfcfa6cf00f3595d1b1e02709444ca3d477aff26b6d050ab6d79288736a9',
        'f698c58d': 'f698c58db0e8bf82eb90211e478e3ef33c8b17e906a833d157a32ea002d16d97',
        'f7ee7573': 'f7ee7573ebf315840229ed861f604ef6b04f99a7c2a7b9f4d8285b88a1581526',
    }
    fixture = path(prefix)
    assert fixture.stem == supplied_sha256[prefix]
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == supplied_sha256[prefix]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_dates_and_optional_source(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser331_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser331_leftovers(*args)
    assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e


@pytest.mark.parametrize('prefix', [
    '09f90c1f', '28528abc', '3e71da53', '762ea6e8', '7f11be01', '950a0991',
    '9c5c898c', 'bb4542dd', 'd518eb02', 'f63aa392', 'f663e109', 'f8fc2919',
    '03dcc069', '315da231', '353d9e29', '693c452c', '7c27565a', '8889623a',
    'a5f4be23', 'bbf607eb', 'c332722f', 'ce010fcd', 'cfbe1db2', 'f0fd9d83',
    '518fef8d', '5404cc5f', '54125ed4', '6d18ed72', '6d50c77a', '7a6515f3',
    '930507a1', 'a16a5540', 'a564e09d', 'b384c365', 'cf527290', 'ecba5198',
    '05a6f15b', '076b6cc6', '0f17b349', '3774d2b6', '54b4ab1b', '58504ce5',
    '68ffaf6b', '87d4b8af', '950a846d', 'a51340d6', 'bb7c8a65', 'f970cd7e',
    '1cf200d1', 'c9cb541c', 'e3c5c5cd', '94b72118-d3cb-46f4-8cf3-8d526586b9f2',
])
def test_previous_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser331_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old




def test_payload_semantics():
    board = selected('0629cb21')
    assert [e.role for e in board] == ['Verwaltungsrat, Präsident', 'Verwaltungsrat, Vizepräsident', 'Verwaltungsrat', 'Verwaltungsrat']
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in board)
    assert board[2].payload['previous_role'] == 'Vizepräsident'
    assert board[3].payload['previous_role'] == 'Präsident'
    transfer, president, manager = selected('08c613ba')
    assert transfer.event_type == 'ownership_changed'
    assert transfer.payload['transferred'] == transfer.payload['buyer_count'] == '100'
    assert president.role == 'Gesellschafter, Geschäftsführer, Präsident'
    assert manager.signing is None  # Existing generic signing event is retained.
    merger = selected('267dd215')[0]
    assert merger.event_type == 'company_merged'
    assert merger.payload['free_equity_coverage_confirmed'] is True
    assert merger.payload['capital_increase'] is False and merger.payload['share_allocation'] is False
    corrected = selected('50985666')[0]
    assert corrected.event_type == 'signing_authority_changed'
    assert corrected.signing == 'Kollektivunterschrift zu zweien'
    assert corrected.payload['previous_signing'] == 'Einzelunterschrift'
    assert corrected.payload['corrected'] is True
    eur = selected('5dad8aa2')[0]
    assert eur.event_type == 'ownership_changed' and eur.payload['currency'] == 'EUR'
    assert eur.payload['assets'] == "104'184'000"
    cross = selected('87ac66e7')[0]
    assert cross.event_type == 'company_merged' and cross.payload['country'] == 'LI'
    assert cross.payload['subordination_confirmed'] is True
    assert all(e.role == 'Verwaltungsrat' and e.payload['excluded_role'] == 'Direktor' and e.signing is None for e in selected('a9eb2fc1'))
    residence = selected('c2b60397')[0]
    assert residence.payload['place'] == 'Neuilly-sur-Seine' and residence.payload['country'] == 'FRA'
    assert residence.role is None and residence.signing is None
    asset = selected('ddedd79d')[0]
    assert asset.event_type == 'ownership_changed' and asset.payload['no_liabilities'] is True
    capital = selected('f632cfcf')[0]
    assert capital.event_type == 'capital_changed' and capital.payload['conditional'] is True
    assert all(e.signing == 'Kollektivprokura zu zweien' and e.payload['signing_restriction'] == 'avec un administateur' for e in selected('f698c58d'))
    transfer, manager = selected('f7ee7573')
    assert transfer.payload['before'] == '100' and transfer.payload['remaining'] == '80'
    assert transfer.payload['buyer_count'] == '40' and manager.role == 'Gesellschafter, Geschäftsführer'


@pytest.mark.parametrize('prefix,key,value', [('08c613ba', 'buyer_count', '101'), ('f7ee7573', 'remaining', '81'), ('f7ee7573', 'buyer_count', '41')])
def test_inconsistent_share_counts_remain_unparsed(prefix, key, value):
    _, (args, kwargs) = captured(prefix)
    old = selected(prefix)[0].payload[key]
    if key == 'remaining':
        changed = args[0].replace('titulaire de ' + old, 'titulaire de ' + value)
    else:
        changed = args[0].replace(('pour ' if prefix == '08c613ba' else 'titulaire de ') + old, ('pour ' if prefix == '08c613ba' else 'titulaire de ') + value)
    assert changed != args[0]
    events, leftover = extract_parser331_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed
