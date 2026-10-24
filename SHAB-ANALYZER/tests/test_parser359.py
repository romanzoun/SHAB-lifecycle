import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser359 import extract_parser359_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('0ff8b861', 'fr.text.foundation_secretary_restricted_collective_signing.v1', 1), ('195e4e8b', 'fr.text.cantonal_court_bankruptcy_judgment_annulled.v1', 1), ('2a96a47b', 'it.text.liquidation_address_replaced.v1', 1), ('48bf8c0f', 'fr.text.corporate_associate_shares_transferred_to_manager.v1', 1), ('618c7acd', 'fr.text.registered_seat_retained_correction.v1', 1), ('824b7855', 'fr.text.associate_changed_by_restructuring.v1', 1), ('9458794a', 'fr.text.share_transfer_collective_managers.v1', 3), ('9ca87f86', 'fr.text.board_president_keeps_individual_signing.v1', 3), ('a05c6e34', 'fr.text.secretary_outside_foundation_board_corrected.v1', 1), ('b2ad6bc5', 'fr.text.share_transfer_new_presiding_manager.v1', 2), ('d55489e4', 'fr.text.share_transfer_new_associate_individual_signing.v1', 2), ('eef5e104', 'fr.text.director_role_retained_correction.v1', 1)]
SUPPLIED_SHA256 = {'0ff8b861': '0ff8b8611addb54922d2cf5476b23c5f06c70d99c126207d638c81369a140774', '195e4e8b': '195e4e8bdede32073c2e4f326a4039aa4d0d9ce73fdbf4ca290d4442a7e94725', '2a96a47b': '2a96a47b8ec22f5e129d1481574f54d1577bc88c226908a24809607fa358bb25', '48bf8c0f': '48bf8c0f3ceb027900bd621b3c4aaecf4012e04a387778bff643e7a1c68f610a', '618c7acd': '618c7acd2e18cc29bb98a60bf8ae33b65eb5d19f91e397d99235a70299746d43', '824b7855': '824b7855cc9ea84970357d4f8b37cadc6352e809671faa1f33cdc963910ca49a', '9458794a': '9458794a3d62d16d9a3cb344f6b8bc17ea93ff2216960354c80134b6abbd91b5', '9ca87f86': '9ca87f860753fffe127654583e08d30aae087435142d920109b174f8487cd8c8', 'a05c6e34': 'a05c6e348df63fbc67263d46377e6c3300ea92099f66c8d0dfbe076366055ade', 'b2ad6bc5': 'b2ad6bc573236bf14f925406996adaba79d04e7dbfbb3e5f914c439e2aae050f', 'd55489e4': 'd55489e4c5c22521d473d0e8e89623241ae012ddd30295c549feb4ee37616894', 'eef5e104': 'eef5e104f3266a6fdc3643fc00799d1ac61e9ae70f134aad5a4250cae3ba948a'}

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
        return extract_parser359_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser359_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser359_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 390
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser359_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser359_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser359_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser359_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser359_leftovers(*args)
    if prefix in ('0ff8b861', '9458794a', 'b2ad6bc5'):
        assert events == [] and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e




@pytest.mark.parametrize('prefix', ['10429a7f', '207be062', '2af8e79d', '34111f7d', '57ae60b9', '61ed7353', '71e8766b', '9284c4f4', 'b35cc72c', 'b628a3d8', 'e77d4351', 'f8a90c87'])
def test_parser358_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser359_leftovers', lambda text, *args, **kwargs: ([], text)):
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
    events, leftover = extract_parser359_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]



def test_payload_semantics():
    assert selected('0ff8b861')[0].signing == 'Kollektivunterschrift zu zweien'
    assert selected('0ff8b861')[0].payload['signing_restriction'] == 'avec le président ou les vices-présidents'
    assert selected('2a96a47b')[0].payload['address'] != selected('2a96a47b')[0].payload['previous_address']
    assert selected('48bf8c0f')[0].payload['transferred'] == '180'
    assert selected('9458794a')[1].signing == 'Kollektivunterschrift zu zweien'
    assert selected('9458794a')[2].role == 'Vorsitzender der Geschäftsführung'
    assert [e.signing for e in selected('9ca87f86')] == ['Einzelunterschrift', 'Kollektivunterschrift zu zweien', 'Kollektivunterschrift zu zweien']
    assert len({e.person_key for e in selected('9ca87f86')}) == 3
    assert selected('a05c6e34')[0].payload['previous_role'] == 'Mitglied des Stiftungsrates'
    assert selected('b2ad6bc5')[1].signing == 'Einzelunterschrift'
    assert selected('d55489e4')[1].role == 'Gesellschafter'
    assert selected('eef5e104')[0].signing is None


@pytest.mark.parametrize('prefix', ['0ff8b861', '9458794a', 'b2ad6bc5'])
def test_truncated_clauses_require_original_context(prefix):
    _, (args, kwargs) = captured(prefix)
    assert extract_parser359_leftovers(*args, source_text='unrelated') == ([], args[0])
    changed = kwargs['source_text'].replace('avec signature individuelle', 'sans signature').replace('avec signature collective à deux', 'sans signature')
    assert extract_parser359_leftovers(*args, source_text=changed) == ([], args[0])


@pytest.mark.parametrize('text', ['', 'Unsupported clause', '   '])
def test_empty_and_unknown_residuals(text):
    assert extract_parser359_leftovers(text, 'fr', 'fixture', '', None, None, None) == ([], text.strip())
