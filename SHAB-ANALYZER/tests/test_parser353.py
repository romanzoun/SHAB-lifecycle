import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser353 import extract_parser353_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('0e514673', 'fr.text.statutes_copy_filed_supplement.v1', 1), ('34036b54', 'fr.text.foundation_members_appointed.v1', 2), ('50a1514a', 'fr.text.branch_signing_supplement.v1', 1), ('68337e64', 'fr.text.managers_liquidators_continued_signing.v1', 2), ('6ad145fa', 'fr.text.erroneous_dissolution_reinstatement_correction.v1', 1), ('7ffdba77', 'fr.text.managers_collective_signing_appointed.v1', 2), ('8d39d97c', 'fr.text.foundation_vice_president_individual_signing.v1', 6), ('ac348d22', 'de.text.previous_notice_reference_corrected.v1', 1), ('af6307eb', 'de.text.statutes_date_entry_corrected.v1', 1), ('bcf584d0', 'it.text.real_estate_assets_transferred.v1', 1), ('dc62f30b', 'de.text.liquidation_reinstatement_court_corrected.v1', 1), ('fd9bcd5e', 'fr.text.director_appointed_board_president.v1', 2)]
SUPPLIED_SHA256 = {'0e514673': '0e51467356dd921edc16e662379e392ec0c0c3fa9b4d212c97d65813bdb5770a', '34036b54': '34036b549f00416d2b8315a45dace53e13334b5451a281a1b19c78e5d599b586', '50a1514a': '50a1514a67e1b7b223e740cd36e1f357b9ffae75c97d1b4baff986ddf07568fd', '68337e64': '68337e64da468cd6f5c879e2410196e1549bfaa9a97d115f96044d0cf7473aac', '6ad145fa': '6ad145fa8fac76b7a143c464dfca328dffecf1e81d51432874589d138590def7', '7ffdba77': '7ffdba773ede98c388df7e0a84e3e8421a1849e82bafbb01987cec4ab52635da', '8d39d97c': '8d39d97c2e5ba99c4fc4d64850cbef1d07ccba474b4966247461d473007e20a9', 'ac348d22': 'ac348d22c0c07e202fdb55db34b649b9a4a3bfb82520271c10278d75abaa4e65', 'af6307eb': 'af6307ebabb82d64569b2942381592cbde8ae62a53e0b9efec40b0c8778437d7', 'bcf584d0': 'bcf584d032ae0bcd9dafe2bf135a77340a11976e67db2b79ad5dbfa02ed888ec', 'dc62f30b': 'dc62f30bbf9665292dc1e664178feca40ed88ffa54a9d4c4cb32d657e64ff67d', 'fd9bcd5e': 'fd9bcd5e3ae685b387c8e5f3eb5945aaa7e67f761a9df68b90aa1d8bc5c584b8'}

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
        return extract_parser353_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser353_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser353_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 381
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser353_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser353_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser353_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser353_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser353_leftovers(*args)
    if prefix in ('34036b54', '7ffdba77', '8d39d97c'):
        assert events == [] and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e



@pytest.mark.parametrize('prefix', ['0863601c', '127b7edf', '13345d7d', '1d2d21a9', '390c063f', '508e1ca0', '5a66d788', '5dab163c', '6f8bcc41', '7dd23e4e', '990046a6', 'edea6f5d'])
def test_previous_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser353_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old


def test_payload_semantics():
    assert selected('50a1514a')[0].role is None
    assert selected('50a1514a')[0].payload['signing_scope'] == 'affaires de la succursale'
    assert all(e.role == 'Liquidator' for e in selected('68337e64'))
    assert [e.role for e in selected('7ffdba77')] == ['Vorsitzender der Geschäftsführung', 'Geschäftsführer']
    foundation = selected('8d39d97c')
    assert foundation[0].signing == 'Einzelunterschrift'
    assert all(e.signing == 'Kollektivunterschrift zu zweien' and e.payload['signing_with'] == 'président ou vice-présidente' for e in foundation[1:])
    assert selected('ac348d22')[0].payload['correct_date'] == '22.09.2020'
    assert selected('af6307eb')[0].payload['correct_date'] == '08.07.2020'
    assert selected('bcf584d0')[0].payload['consideration'] == "1'685'000.00"
    assert selected('dc62f30b')[0].payload['court'] == 'Bezirksgerichts Baden'
    assert all(e.signing is None for e in selected('fd9bcd5e'))


@pytest.mark.parametrize('prefix', ['34036b54', '7ffdba77', '8d39d97c'])
def test_missing_or_unrelated_signing_source_preserves_residue(prefix):
    _, (args, kwargs) = captured(prefix)
    assert extract_parser353_leftovers(*args, source_text='Unrelated source') == ([], args[0])
    changed_source = kwargs['source_text'].replace('signature collective à deux', 'signature individuelle')
    assert extract_parser353_leftovers(*args, source_text=changed_source) == ([], args[0])
