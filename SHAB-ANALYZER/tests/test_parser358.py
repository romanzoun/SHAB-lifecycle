import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser358 import extract_parser358_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('10429a7f', 'fr.text.committee_members_individual_signing.v1', 2), ('207be062', 'fr.text.participation_capital_created_by_claim_offset.v1', 1), ('2af8e79d', 'fr.text.collective_procuration_restriction_removed.v1', 1), ('34111f7d', 'de.text.board_member_becomes_manager_keeps_collective_signing.v1', 1), ('57ae60b9', 'fr.text.director_same_origin_and_residence.v1', 1), ('61ed7353', 'de.text.supervisory_statutes_date_corrected.v1', 1), ('71e8766b', 'de.text.intended_asset_acquisition_deleted_detail.v1', 1), ('9284c4f4', 'fr.text.shares_transferred_with_remaining_holdings.v1', 1), ('b35cc72c', 'fr.text.person_origin_residence_entry_completed.v1', 1), ('b628a3d8', 'fr.text.demerger_common_owner_no_capital_increase.v1', 1), ('e77d4351', 'fr.text.share_transfer_and_managers_appointed.v1', 3), ('f8a90c87', 'de.text.asset_transfer_claim_consideration.v1', 1)]
SUPPLIED_SHA256 = {'10429a7f': '10429a7fa9630126247f58125d73285214f1fe494d03a23135bba62ea1c125ac', '207be062': '207be0624e230e063c9887ec0063111cd482f8f0a433af16637aafbeb8376c54', '2af8e79d': '2af8e79dbea1f30d703203bd95134b5fe8eabb05f8df85425bc72fc04bad92bf', '34111f7d': '34111f7df1558ffcd6a65227ad3595f49a6d24458dc0f392bc0351b06e879dfb', '57ae60b9': '57ae60b9781cc2b046b10fef92f5e8d2632d34807e3930d906a1cf5362641c68', '61ed7353': '61ed7353832122cd09811f8cc48f58925594a340a2c9514156f726023bf73b9f', '71e8766b': '71e8766b89c46bcdf1ffc0ec8af086f13c3205cd1808dd47120917f1b6a1b368', '9284c4f4': '9284c4f42fd4be17f1917c7204f715c67d3d6f9204ba0312a441247d7aa9034b', 'b35cc72c': 'b35cc72c599cec0786e00f0b32fc30b8cb03d574a85e2e41bc79e2b9d88d8eb7', 'b628a3d8': 'b628a3d80629532182530bd7c4ca27eeebb8b6cac22c10a50c1c1ed461bf37d1', 'e77d4351': 'e77d43517c68f1f49a28b3417816594395fddb7b7b4a0cbd3501cb1ec1876140', 'f8a90c87': 'f8a90c8702e6ecbe72f57332b92ab80e09512256b0b732331c7aae6a2fe1da19'}

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
        return extract_parser358_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser358_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser358_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 382
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser358_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser358_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser358_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser358_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser358_leftovers(*args)
    if prefix in ('10429a7f', '71e8766b', 'e77d4351'):
        assert events == [] and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e




@pytest.mark.parametrize('prefix', ['2d38b3dd', '35ba392a', '3742e62d', '44edd172', '503b2dc1', '556a7958', '5973af25', '5beb21e3', '6b8defcc', '78243389', 'a291836b', 'ef7f47a2'])
def test_parser357_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser358_leftovers', lambda text, *args, **kwargs: ([], text)):
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
    events, leftover = extract_parser358_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]



def test_payload_semantics():
    assert all(e.signing == 'Einzelunterschrift' for e in selected('10429a7f'))
    assert len({e.person_key for e in selected('10429a7f')}) == 2
    assert selected('2af8e79d')[0].signing == 'Kollektivprokura zu zweien'
    assert selected('34111f7d')[0].role == 'Geschäftsführer'
    assert selected('57ae60b9')[0].signing == 'Kollektivunterschrift zu zweien'
    assert selected('71e8766b')[0].payload['deleted'] is True
    assert selected('b628a3d8')[0].payload['capital_increased'] is False
    assert selected('b628a3d8')[0].payload['shares_allocated'] is False
    assert selected('f8a90c87')[0].payload['consideration_kind'] == 'claim'


@pytest.mark.parametrize('prefix', ['10429a7f', '71e8766b', 'e77d4351'])
def test_truncated_clauses_require_original_context(prefix):
    _, (args, kwargs) = captured(prefix)
    assert extract_parser358_leftovers(*args, source_text='unrelated') == ([], args[0])
    changed = kwargs['source_text'].replace('avec signature individuelle', 'sans signature').replace('[gestrichen:', '[neu:')
    assert extract_parser358_leftovers(*args, source_text=changed) == ([], args[0])
