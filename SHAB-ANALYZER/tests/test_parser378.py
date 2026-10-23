import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser378 import extract_parser378_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('20c220ba', 'fr.text.shares_transferred_new_manager_president.v1', 2), ('29e9c2fb', 'fr.text.notice_person_domicile_corrected.v1', 1), ('2a5ace3a', 'fr.text.single_share_transferred_manager_retained.v1', 3), ('35776284', 'de.text.company_reinstated_bankruptcy_suspension_revoked.v1', 1), ('60e868c5', 'de.text.assets_transferred_for_fund_units_cash_adjustment.v1', 1), ('68f2073f', 'fr.text.president_shares_transferred_new_manager.v1', 2), ('94a55344', 'fr.text.new_administrator_au_domicile.v1', 1), ('9b4aa462', 'fr.text.individual_company_partial_shares_transferred.v1', 2), ('9b57c7fb', 'de.text.company_dissolved_female_manager_liquidator.v1', 2), ('af1046d9', 'de.text.share_sale_prohibition_order_updated.v1', 1), ('b88e27e1', 'fr.text.notice_board_membership_retained.v1', 1), ('e67d2534', 'de.text.company_translations_corrected_nested_parentheses.v1', 1)]
SUPPLIED_SHA256 = {'20c220ba': '20c220ba1fd4309f77bfb2406d1765ba03da774a0c73431f03fec1856eb7ce6a', '29e9c2fb': '29e9c2fb40b063d73650c096034cddb14d8d65d1702c0ff91b2e60e215fe1b48', '2a5ace3a': '2a5ace3a4f6cbd48d46750f7360b70274ccb8aae05d00ee71030948231ef1522', '35776284': '3577628473cc60428f66557a821c752b2653ff3d3a9bd7f43cc9b389987e4dbf', '60e868c5': '60e868c57b52029dca9e3298fa30c782a02ec3e99e1350046c87810d39fc6a5b', '68f2073f': '68f2073f8c6c1070c1379496f86a4bb46deb44ef4e455eef0fe189a190a7ac16', '94a55344': '94a55344ec4ebdcbdf49587a1eee05434da9f778289577b5f6ce3adca2c8bdac', '9b4aa462': '9b4aa462a4f3fe203fd9e64dd70f1427bb21bc823b2f16e2738136dcb7a113f1', '9b57c7fb': '9b57c7fbcea46f65308bc4268e46c3ea7b86aa1930ade3f672466a2844f152c9', 'af1046d9': 'af1046d950ca271ad97aef4102fd9835b26240f8470df192a99a34b48751ce83', 'b88e27e1': 'b88e27e1a8168ac2cabeb663ad47c495f675de4959ff4438fc0ce2fd569ee512', 'e67d2534': 'e67d2534724c444079b28f54533d50c5a1b90e43b32401bc6401a3727ba048e5'}

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
        return extract_parser378_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser378_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser378_leftovers(*args, **kwargs)[0]


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
    with patch.object(parser, 'extract_parser378_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser378_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser378_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser378_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser378_leftovers(*args)
    if prefix == 'e67d2534':
        assert not events and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e



@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_optional_metadata_absent(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser378_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old


@pytest.mark.parametrize('version', [268, 285, 350, 352, 376, 377])
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
        assert extract_parser378_leftovers(*args, **kwargs) == ([], args[0])
        with patch.object(parser, 'extract_parser378_leftovers', lambda text, *a, **kw: ([], text)):
            assert parse_publication_xml(fixtures[0]) == actual
        with patch.object(parser, name, lambda text, *a, **kw: ([], text)):
            disabled = parse_publication_xml(fixtures[0])
        assert not any(e.rule_id in {case[1] for case in CASES} for e in disabled.events)
        checked += 1
    assert checked



def test_payload_semantics():
    a, b = selected('20c220ba')
    assert a.payload['count'] == '100' and b.role == 'associée-gérante et présidente'
    assert b.signing is None
    a = selected('29e9c2fb')[0]
    assert a.payload['place'] == 'Evian-les-Bains' and a.payload['previous_place'] == 'Evina-les-Bains'
    a, b, c = selected('2a5ace3a')
    assert a.payload['nominal'] == "20'000"
    assert b.role == 'gérant' and b.signing == 'Einzelunterschrift'
    assert c.role == 'associé-gérant' and c.signing is None
    a = selected('35776284')[0]
    assert a.event_type == 'status_changed' and a.payload['bankruptcy_reopened'] is True
    p = selected('60e868c5')[0].payload
    assert (p['assets'], p['count'], p['nav'], p['cash_adjustment']) == ("887'145'444.00", "887'145", "1'000.00", '444.00')
    assert selected('68f2073f')[1].role == 'associé-gérant'
    assert selected('94a55344')[0].role == 'administratrice'
    p = selected('9b4aa462')[0].payload
    assert (p['transferred1'], p['transferred2'], p['received'], p['remaining1'], p['remaining2']) == ('4', '2', '6', '6', '8')
    a, b = selected('9b57c7fb')
    assert a.event_type == 'status_changed' and a.payload['liquidation'] is True
    assert b.role == 'Gesellschafterin, Geschäftsführerin, Liquidatorin' and b.signing == 'Einzelunterschrift'
    p = selected('af1046d9')[0].payload
    assert (p['decision_date'], p['previous_decision_date']) == ('13.10.2020', '04.03.2020')
    assert selected('b88e27e1')[0].role == "membre du conseil d'administration"
    p = selected('e67d2534')[0].payload
    assert p['translation_fr'] == 'Aardglobe (Suisse) SA'
    assert p['translation_en'] == 'Aardglobe (Switzerland) Ltd'


def test_existing_administrator_pattern_keeps_ownership():
    from shab_analyzer.parser109 import _FR_NEW_ADMINISTRATOR, extract_parser109_leftovers
    text = 'Nouvelle administratrice : Exemple Anne, de France, à Lausanne'
    args = (text, 'fr', 'fixture', '', None, None, None)
    assert _FR_NEW_ADMINISTRATOR.fullmatch(text)
    assert extract_parser109_leftovers(*args)[0]
    assert extract_parser378_leftovers(*args) == ([], text)
    padded = '  ' + text + '  '
    assert extract_parser378_leftovers(padded, *args[1:]) == ([], padded)


def test_translation_fragment_requires_matching_complete_source():
    _, (args, kwargs) = captured('e67d2534')
    assert extract_parser378_leftovers(*args) == ([], args[0])
    assert extract_parser378_leftovers(*args, source_text='unrelated') == ([], args[0])
    altered = (args[0] + ' unexpected', *args[1:])
    assert extract_parser378_leftovers(*altered, **kwargs) == ([], altered[0])
