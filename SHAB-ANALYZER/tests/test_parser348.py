import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser348 import extract_parser348_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('26ca1aa6', 'fr.text.continued_collective_signing_named_partners.v1', 6), ('2f33710a', 'fr.text.board_president_signing_corrected.v1', 2), ('434b77f3', 'fr.text.limited_partner_contribution_changed.v1', 3), ('459e4a0a', 'fr.text.authorized_capital_clause_deleted_conditional_clause_amended.v1', 1), ('5830f519', 'de.text.organization_uid_corrected.v1', 1), ('8a791e50', 'de.text.limited_audit_waived_by_declaration.v1', 1), ('8e6b1453', 'fr.text.foundation_members_with_president_or_vice_president.v1', 2), ('9e9d9a28', 'de.text.bankruptcy_closed_registration_retained_for_assigned_claims.v1', 1), ('a966266d', 'de.text.bankruptcy_discontinued_insufficient_assets.v1', 1), ('df2deff6', 'fr.text.board_president_and_member_individual_signing.v1', 2), ('e2ed9941', 'fr.text.proprietor_bankruptcy_judgment_annulled.v1', 1), ('f5442777', 'fr.text.conditional_capital_clause_amended.v1', 3)]
SUPPLIED_SHA256 = {'26ca1aa6': '26ca1aa65cd1c997466c934a24a7d91073e8cf08d26226ce34351eae97a46a44', '2f33710a': '2f33710add8262025c3abe4d706c1297fab33ae279e5b5166e3c5db14a9023f8', '434b77f3': '434b77f345a5e949d6f6c81658e6e6f11887d3e5a2c46ba4c74ffb8896246518', '459e4a0a': '459e4a0a7c009c281803d3876b0fc3fc8234b945f6c760943aa4f872933d6847', '5830f519': '5830f519bffbebeeac7a497368fea70797a4fe44a47c14931b1e468403587039', '8a791e50': '8a791e509b89e4a2d4d546e966b81627cb85fd29eb1fb16f954dc28a2bf4c702', '8e6b1453': '8e6b14536be92f292c1e32193a13d372055b374f139c0c25273dd62a417264b0', '9e9d9a28': '9e9d9a2819b50debfad26ce8f7b9151bb92d72f4ca0c503ff63683ee3e003c7f', 'a966266d': 'a966266d357b17f7a5ef48db525467898262632772f9bf22a4a2d198601ff719', 'df2deff6': 'df2deff67e77c10079252caf184b93f36f5a923788daa99050099728bcab46e4', 'e2ed9941': 'e2ed99419624ff3956c10c15336542aa740cd4fbfe9809c0edd6cfc77730b1da', 'f5442777': 'f544277767fe65fe3ea5848dd64d6e21f8326dfe650e6ac5b72dc8917ba1c89b'}

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
        return extract_parser348_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser348_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser348_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 359
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser348_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser348_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser348_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser348_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser348_leftovers(*args)
    assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e


@pytest.mark.parametrize('prefix', [
    '082387c3',
    '0decdc6f',
    '3e890c4b',
    '4ffff852',
    '815e8cba',
    '85bfaa5e',
    'c3346b0d',
    'c5336706',
    'd0ea0ee1',
    'd6c330d8',
    'fe01b812',
    'fe9ab06f',
    '2987f13e', '3285d09c', '63269358', '77d5163e', '976e168b', '9dab1a36', 'aedb98df', 'b80ba80f', 'c4186931', 'd431ce77', 'e54bf477', 'e76aae5c',
    '05170f05',
    '0534e4d1',
    '17abb90d',
    '1aca3e0c',
    '44a3c09b',
    '6f482002',
    '90fdb042',
    '9971fec7',
    'afa64fa2',
    'b0cc538a',
    'cad77ea9',
    'cb42b642',
    '09959877',
    '2889606f',
    '57b618c1',
    '679b9142',
    '7a44efd2',
    '915ad298',
    '953589b6',
    'a8b7b261',
    'adc2b7d9',
    'b5ac2015',
    'd582e010',
    'd7503e33',
    '02b01d21', '05f754ae', '28d8a9ab', '344fd637', '3fd951f1', '53049963', '74e2d459', '947e1202', 'a1b75c8f', 'ac7a80ad', 'b89de1db', 'f06a7e6a',
    '03f3a7e2', '14bd8e0e', '1b239b69', '2520e8be', '2df613fd', '2e2ec72c',
    '335bc269', '9713ae8a', 'aac76783', 'c238098a', 'cd084f70', 'dfcb36ee',
    '31628a88',
    '39ec36b8',
    '43a6bf54',
    '5b720f18',
    '6ac3eab0',
    '8ea39615',
    'aa9d9002',
    'aae43f2b',
    'c1edd5aa',
    'd8ea7c8b',
    'd92a31fa',
    'f13ce517',
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
    with patch.object(parser, 'extract_parser348_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old






@pytest.mark.parametrize('prefix', ['0de4e39b', '24d6f7bc', '46fa377a', '5d459649', '667caef8', '6ca57cbb', '7bb4c54f', '81b03e8e', '8d29c898', 'abdc2a7a', 'da8606cf', 'f5d91211', '1aa85cf4', '1f8ffa74', '311d3bbf', '5632f244', '7b1eb120', '8241c2ba', 'ab405e2d', 'afe72629', 'ba5f5ddf', 'df57ab86', 'f5cf3c65', 'fb6010b5'])
def test_recent_results_unchanged(prefix):
    test_previous_results_unchanged_without_optional_attributes(prefix)


@pytest.mark.parametrize('prefix', ['12199924','495ee781','4b25a973','5227277b','9457810b','9ddc431e','b671b751','c1ab87b2','d16ef08d','d794d81f','dcabd534','fbaa4000'])
def test_parser344_results_unchanged(prefix):
    test_previous_results_unchanged_without_optional_attributes(prefix)


@pytest.mark.parametrize('prefix', ['0c03925b','26bec0b9','34ba9e7e','366516ce','54fa9aa4','9681fa18','9b049f70','9c313ec4','b34e5263','e01c7759','e5e4bce9','ea0cfdb0'])
def test_parser345_results_unchanged(prefix):
    test_previous_results_unchanged_without_optional_attributes(prefix)

@pytest.mark.parametrize('prefix', ['0d5bd40b', '2dfa90cc', '32a8036e', '57340b0a', '74f19e4f', 'a321ccaf', 'ab18dfa5', 'bd7486d8', 'c1d41c77', 'c419f896', 'd3251a39', 'e87e3685'])
def test_parser346_results_unchanged(prefix):
    test_previous_results_unchanged_without_optional_attributes(prefix)


@pytest.mark.parametrize("prefix", ['bcf422aa', '2ee7eb0d', 'c5fa5c4d', 'f2300fb5', '360fedd4', '0ab39892', 'c9b3ebd6', 'a1e7ae61', '6fa3fe10', 'c9637524', 'a60779f4', 'fa9ce006'])
def test_parser347_results_unchanged(prefix):
    test_previous_results_unchanged_without_optional_attributes(prefix)


@pytest.mark.parametrize('prefix,expected', [
    ('5830f519', {'uid': 'CHE-371.789.696', 'previous_uid': '486.813.909', 'entry_date': '25.06.2020'}),
    ('8a791e50', {'declaration_date': '23.07.2014'}),
    ('a966266d', {'decision_date': '18.08.2020', 'court_place': 'Brugg'}),
    ('e2ed9941', {'decision_date': '04.08.2020', 'bankruptcy_date': '13.07.2020'}),
    ('459e4a0a', {'decision_date': '17.07.2020', 'authorization_date': '14.06.2019', 'conditional_authorization_date': '14.06.2019'}),
    ('f5442777', {'decision_date': '18.08.2020', 'authorization_date': '24.04.2017'}),
])
def test_payload_values(prefix, expected):
    assert selected(prefix)[0].payload.items() >= expected.items()


def test_contributions_and_identity():
    events = selected('434b77f3')
    assert [e.payload['amount'] for e in events] == ["3'385'000", "3'100'000", "33'600'000"]
    assert [e.payload['previous_amount'] for e in events] == ["3'400'000", "2'125'000", "33'625'000"]
    assert [e.payload['uid'] for e in events] == ['CHE-216.606.563', 'CHE-328.635.856', 'CHE-104.139.689']


def test_roles_and_signing_restrictions():
    events = selected('26ca1aa6')
    assert len({e.person_key for e in events}) == 6
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in events)
    assert events[0].payload['authorized_partners'] == ['Marty David', 'Luyet Stany', 'Brinon Jérôme']
    foundation = selected('8e6b1453')
    assert all(e.role == 'Mitglied des Stiftungsrates' and e.signing is None for e in foundation)
    assert all(e.payload['signing_partner_roles'] == ['président', 'vice-président'] for e in foundation)
    assert [e.signing for e in selected('df2deff6')] == ['Einzelunterschrift'] * 2
    corrected = selected('2f33710a')
    assert corrected[0].signing == 'Einzelunterschrift'
    assert corrected[1].payload['name'] == 'Petit Florian Jean-Marc'
    assert corrected[1].payload['given_names'] == 'Florian Jean-Marc'
    assert corrected[1].payload['previous_given_names'] == 'Floran Jean-Marc'
    assert [e.role for e in selected('f5442777')[1:]] == ['Präsident', 'Vizepräsident']


def test_contradictory_contribution_preserved():
    _, (args, kwargs) = captured('434b77f3')
    text = args[0].replace("3'385'000", "3'500'000")
    assert extract_parser348_leftovers(text, *args[1:], **kwargs) == ([], text)
