import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser396 import extract_parser396_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = ['4447caf778d0b076d035fb3ba48d3decf435ee6a10044e2e81b3e2fb952fe4a5', '533a44f3e962ba468fe1f01a4014231e1ac3d7dbcda39cc1ea938175a1e25798', '8053f7ffd3af83861eb62586283910afbc7c1a7b09acd5f256e2f7bbadcb32cf', 'a3e6c401aa8830c3d0d7cb3fda789ec54d9e41e90c34f2c931164350334997a1', 'a9fef2a76e7b718b93278bfaa46a01cdf34eeca89c3dc3e682226122e8ad4e03', 'aa57e4e8d4d9539748a658dac7c512fc329db91a8e7e4065c212237848a453b3', 'bf44261a200b2883aef7aa27047c9b94bd456bdcd382cfb061236f4e992456fb', 'c4d1c5de37c0ebbe5213076f3b7e0021c5ad39f76de0e793dde7eed808c9b2c8', 'c8da37d7139abde98e40c23b8ec9e1a812477023a19b4707ba321b6e58e53a2d', 'e30a4d1d11ea7fa7b0476a2c5cbae57d881fa24dd60e7be7ff0386b05d2e51b5', 'ed78f2279f8709d4fe24750718d3aae662377ce66a43cbb62cef5fb47c31d861', 'fad0e45368b9802887079b34583c7c34df18cc1ec5075caac7dab33aa3d5903e']
CONTEXT_REQUIRED = set()
COUNTS = {"8053f7ff": 3, "ed78f227": 2, "fad0e453": 4}


@lru_cache(None)
def captured(digest):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser396_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser396_leftovers', capture):
        result = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert len(calls) == 1
    return result, calls[0]

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_complete_and_unchanged_legacy_payloads(digest):
    import shab_analyzer.parse as parser
    result, (args, kwargs) = captured(digest)
    added, rest = extract_parser396_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 414
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS.get(digest[:8], 1) and not rest
    with patch.object(parser, 'extract_parser396_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_unknown_suffix_and_language_preserve_input(digest):
    _, (args, kwargs) = captured(digest)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser396_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser396_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_missing_optional_source_and_invalid_dates(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser396_leftovers(*args)
    if digest[:8] in CONTEXT_REQUIRED:
        assert not events and rest == args[0]
    else:
        assert len(events) == COUNTS.get(digest[:8], 1) and not rest
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser396_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_old_event_without_new_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event



EXPECTED_ACTIONS = [
    'sole_proprietor_asset_transfer_net_assets_claim',
    'bankruptcy_appeal_rejected_pronouncement_confirmed',
    'three_foundation_members_shared_origin',
    'share_transfer_new_associate_manager_president',
    'publication_facts_unchanged_typo',
    'limited_partnership_amount_previous_currency_typo',
    'former_administrator_individual_proxy',
    'collective_signatory_comma_in_name',
    'provisional_moratorium_separate_commissioner_decision',
    'statutes_non_public_changes_double_typo',
    'two_liquidators_shared_new_residence',
    'four_foundation_members_liquidators_typo',
]

@pytest.mark.parametrize('digest,action', list(zip(SUPPLIED_SHA256, EXPECTED_ACTIONS)))
def test_explicit_meaning(digest, action):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser396_leftovers(*args, **kwargs)
    assert not rest and all(e.payload['action'] == action for e in events)
    p = events[0].payload
    if digest.startswith('4447'):
        assert p['currency'] == 'CHF' and p['consideration'] == p['net_assets']
        assert p['agreement_date'] == '11.11.2020'
    elif digest.startswith('533a'):
        assert events[0].event_type == 'status_changed'
        assert p['effective_time'] == '16h15' and p['effective_date'] == '1er décembre 2020'
    elif digest.startswith('8053'):
        assert [e.payload['origin'] for e in events] == ['Belgique', 'Belgique', 'Bex']
        assert all(e.signing is None for e in events)
    elif digest.startswith('a3e6'):
        assert (p['count'], p['previous'], p['remaining']) == ('10', '20', '10')
    elif digest.startswith('a9fe'):
        assert p['publication_facts_changed'] is False
    elif digest.startswith('aa57'):
        assert p['previous_currency_raw'] == 'CHE' and 'currency' not in p
        assert p['amount'] == "471'683" and p['previous_amount'] == "361'905"
    elif digest.startswith('bf44'):
        assert p['previous_role'] == 'administrateur'
        assert events[0].role is None and events[0].signing == 'Einzelprokura'
    elif digest.startswith('c4d1'):
        assert ', ' in p['name'] and events[0].signing == 'Kollektivunterschrift zu zweien'
    elif digest.startswith('c8da'):
        assert events[0].event_type == 'status_changed'
        assert p['until_date'] == '17.03.2021' and p['appointment_date'] == '27.11.2020'
    elif digest.startswith('e30a'):
        assert p['statutes_date'] == '28.10.2020'
    else:
        assert all('liquidateur' in e.role and e.signing is None for e in events)


def test_predecessor_patterns_keep_ownership():
    from shab_analyzer.parser144 import extract_parser144_leftovers
    from shab_analyzer.parser207 import extract_parser207_leftovers
    from shab_analyzer.parser140 import extract_parser140_leftovers
    cases = [
        (extract_parser144_leftovers, "Kommanditsumme neu: 200 [bisher: CHF 100]", 'de'),
        (extract_parser207_leftovers, "Kommanditsumme neu: CHE 200 [bisher: CHF 100]", 'de'),
        (extract_parser140_leftovers, 'Exemple Anne et Exemple Jean sont nommés liquidateurs', 'fr'),
    ]
    for predecessor, text, lang in cases:
        args = text, lang, 'p', '', None, None, None
        old, rest = predecessor(*args)
        assert old and not rest
        assert extract_parser396_leftovers(*args) == ([], text)


def test_ordinary_signatory_remains_owned_by_old_rule():
    from shab_analyzer.parser394 import extract_parser394_leftovers
    text = 'Signature collective à deux a été conférée à Exemple Anne'
    args = text, 'fr', 'p', '', None, None, None
    old, rest = extract_parser394_leftovers(*args)
    assert old and not rest
    assert extract_parser396_leftovers(*args) == ([], text)


def test_invalid_share_count_preserves_input():
    _, (args, kwargs) = captured(SUPPLIED_SHA256[3])
    text = args[0].replace('cède 10', 'cède 11')
    assert extract_parser396_leftovers(text, *args[1:], **kwargs) == ([], text)


def test_invalid_french_date_and_time_preserve_input():
    _, (args, kwargs) = captured(SUPPLIED_SHA256[1])
    for old, new in [('1er décembre', '32 décembre'), ('16h15', '24h15')]:
        text = args[0].replace(old, new)
        assert extract_parser396_leftovers(text, *args[1:], **kwargs) == ([], text)

@pytest.mark.parametrize('digest', [
    '1855c3abe279580b8806de34447fdc1f75832e8ebc2773afe15f19d7b9459311',
    '2bfe63c21628baa119c054da99ab2f48e32db8af946cc9b50f59376bc86bf64b',
    '77f41871b77981f2c97e4cf39bd4a74f4ea769e78b4443229fba31bc789de90f',
    'bfe02dbcec18d02da123c1d47a524bd09ed601a8eef5e27d46cd9f26cecc6422',
])
def test_existing_fixture_results_without_new_attributes_unchanged(digest):
    import shab_analyzer.parse as parser
    path = FIXTURES / (digest + '.xml')
    result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser396_leftovers', lambda text, *a, **kw: ([], text)):
        previous = parse_publication_xml(path)
    assert result == previous
