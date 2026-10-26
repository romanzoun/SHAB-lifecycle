import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser357 import extract_parser357_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('2d38b3dd', 'de.text.association_dissolved_by_court_bankruptcy_liquidation.v1', 1), ('35ba392a', 'fr.text.cooperative_share_nominal_range_corrected.v1', 1), ('3742e62d', 'it.text.merger_transferor_equity_attestation.v1', 1), ('44edd172', 'fr.text.subdirector_appointed_procuration_terminated.v1', 4), ('503b2dc1', 'fr.text.authorized_capital_statutory_clause_introduced.v1', 1), ('556a7958', 'fr.text.shares_transferred_new_associate_without_signing.v1', 2), ('5973af25', 'de.text.branch_added_spaced_uid.v1', 1), ('5beb21e3', 'fr.text.proprietor_name_corrected.v1', 1), ('6b8defcc', 'fr.text.council_member_without_signing.v1', 1), ('78243389', 'fr.text.corporate_associate_holding_changed.v1', 1), ('a291836b', 'fr.text.collective_signing_restriction_removed.v1', 2), ('ef7f47a2', 'fr.text.director_becomes_board_member_keeps_individual_signing.v1', 1)]
SUPPLIED_SHA256 = {'2d38b3dd': '2d38b3dd80798265d52329ef4e3520ef55625f99e5cb6d366dcaa6e1e482e4f4', '35ba392a': '35ba392a442ea0bb33b349785e80878965470477ae193f900eaf0382aced8532', '3742e62d': '3742e62d31c8ed2f1273058ff854d12db352f6146f635fb58ac7803f6a92933b', '44edd172': '44edd1726144af9615779331efc4d4d3bff3bff84d1c07474bea1248c8e05a42', '503b2dc1': '503b2dc19a504aef0aa2441e3b51346ec50d7f6b649ad4c8fc7c8802a599553e', '556a7958': '556a7958bbd10cfb4bd34d54d50494fb0cc004c2ce155592409fb47a37402f2e', '5973af25': '5973af25a2961fe66771902a1e1e5a196cb3141b3c8147c02aeb0788f0f9661e', '5beb21e3': '5beb21e36b756d1dc083ea319834aa403cded67ab4af64b25614008d1c2e3483', '6b8defcc': '6b8defcc048a6f8c82d9edd4c752620c218ecd06b1d5632c0e58cc251441fc12', '78243389': '78243389f8dcf31002bca5bf00801602453ec5e502f9d13e857a44a6878a4276', 'a291836b': 'a291836bd183222708b14b7e2fd21eeeb04b355bea50445b2fd647fa85346c9d', 'ef7f47a2': 'ef7f47a298b661c9126c69f1075cf04ab415debd0ceb964f40ce739e0f238f57'}

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
        return extract_parser357_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser357_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser357_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 399
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser357_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser357_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser357_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser357_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser357_leftovers(*args)
    if prefix in ('6b8defcc',):
        assert events == [] and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e




@pytest.mark.parametrize('prefix', ['803e00f4', 'c1a93404', '7fd4abe3', '8029e9e8', '94e042ba', '98e2725d', 'cc156f75', '737a2075', '9dd4882c', '2fc056e7', 'bb4d94f4', '41c0312e'])
def test_parser356_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser357_leftovers', lambda text, *args, **kwargs: ([], text)):
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
    events, leftover = extract_parser357_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]



def test_payload_semantics():
    merger = selected('3742e62d')[0].payload
    assert merger['equity_holder'] == 'transferor'
    assert merger['capital_increased'] is False and merger['shares_allocated'] is False
    officers = selected('44edd172')
    assert len({e.person_key for e in officers}) == 4
    assert all(e.role == 'Vizedirektor' and e.signing == 'Kollektivunterschrift zu zweien' for e in officers)
    assert all(e.payload['procuration_terminated'] is True for e in officers)
    assert all(e.payload['signing_restriction'] == "limitée à l'établissement principal" for e in officers)
    assert selected('556a7958')[1].signing == 'ohne Zeichnungsberechtigung'
    assert selected('6b8defcc')[0].role == 'Mitglied des Stiftungsrats'
    assert selected('ef7f47a2')[0].signing == 'Einzelunterschrift'
    assert selected('ef7f47a2')[0].payload['previous_role'] == 'directeur'


def test_council_role_requires_source():
    _, (args, kwargs) = captured('6b8defcc')
    assert extract_parser357_leftovers(*args, source_text='unrelated') == ([], args[0])
    changed = kwargs['source_text'].replace('sans signature', 'avec signature individuelle')
    assert extract_parser357_leftovers(*args, source_text=changed) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('556a7958', 'nouvel associé pour 6', 'nouvel associé pour 7'),
    ('3742e62d', 'la società trasferente dispone', 'la società assuntrice dispone'),
    ('44edd172', "limitée à l'établissement principal", 'sans restriction'),
])
def test_changed_facts_are_not_consumed(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser357_leftovers(changed, *args[1:], **kwargs) == ([], changed)
