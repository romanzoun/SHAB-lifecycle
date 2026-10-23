import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser344 import extract_parser344_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('12199924', 'de.text.authorized_capital_clause_expired.v1', 2), ('495ee781', 'fr.text.statutes_amended_multiple_dates.v1', 1), ('4b25a973', 'de.text.registered_person_signing_changed.v1', 1), ('5227277b', 'fr.text.planned_property_acquisition_completed.v1', 1), ('9457810b', 'fr.text.board_president_residence_corrected.v1', 1), ('9ddc431e', 'fr.text.associate_appointed_without_signing.v1', 1), ('b671b751', 'fr.text.manager_signing_changed.v1', 3), ('c1ab87b2', 'fr.text.board_member_signing_changed.v1', 5), ('d16ef08d', 'fr.text.committee_member_signing_corrected.v1', 2), ('d794d81f', 'de.text.bankruptcy_reopened_dissolved_company.v1', 1), ('dcabd534', 'it.text.branch_suppressed_deletion_pending_tax_consent.v1', 1), ('fbaa4000', 'de.text.founding_statutes_date_corrected.v1', 1)]
SUPPLIED_SHA256 = {'12199924': '121999242571099286b6c8d318c2cd6b54c4d13363d17562dd2f414eec2204bf', '495ee781': '495ee7810fe9c6770305e5239b514a4a56b51da15c01969fbc320fe5f0eb3ac0', '4b25a973': '4b25a973558c542bd3f31f605d4c58ab315b38c31311e73a9266cb683fe76845', '5227277b': '5227277b30a20d723210413e5c76debfb5663c2007043b2a1301b0b95ade3a4e', '9457810b': '9457810b002f0c0a1eace97420becb7d09c2023f283d15c7205afff8469a8037', '9ddc431e': '9ddc431ee6b127efb257bc9cc7411c181a5b657cadedf8ec55882fb0e3eeeae1', 'b671b751': 'b671b751d8768d76e831c3ba3c47734aca6b8938ccfd3feead24094d90875080', 'c1ab87b2': 'c1ab87b2e00feaed48e95956143282910aa70cc73d482565172e62d0e0219661', 'd16ef08d': 'd16ef08d0927ca3f4ee1bbb53984b91ab536c9ec920756eb5ac64599856c21ab', 'd794d81f': 'd794d81f89c692077222bc356bd7706ed91d1e9c0717e4f4e1f1fdeaf9ab07ce', 'dcabd534': 'dcabd534327e54cd56b078dc9a1d128a80071b1c0e43d57091cf53590477110e', 'fbaa4000': 'fbaa400080f9536affc59cbed2a3f0c448526b4622e39facd623a4839d9a2bca'}

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
        return extract_parser344_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser344_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser344_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 374
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser344_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser344_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser344_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser344_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser344_leftovers(*args)
    if prefix == '12199924':
        assert events == [] and leftover == args[0]
    else:
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
    with patch.object(parser, 'extract_parser344_leftovers', lambda text, *args, **kwargs: ([], text)):
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

@pytest.mark.parametrize('prefix,expected', [
    ('12199924', {'statutes_date': '13.08.2020'}),
    ('495ee781', {'statutes_dates': ['18.06.2020', '31.07.2020']}),
    ('4b25a973', {'previous_signing': 'Kollektivunterschrift zu zweien'}),
    ('5227277b', {'parcel': '10564', 'municipality': 'Plan-les-Ouates', 'agreement_date': '23.07.2020', 'price': "4'421'000", 'currency': 'CHF'}),
    ('9457810b', {'entry': '3964', 'entry_date': '26.08.2013', 'notice_date': '29.08.2013', 'notice_id': '1050329', 'place': 'Vully-les-Lacs', 'previous_place': 'Les Cullayes VD'}),
    ('9ddc431e', {'origin': 'France', 'place': 'Carouge (GE)'}),
    ('d16ef08d', {'entry': '2079', 'entry_date': '08.07.2020'}),
    ('d794d81f', {'decision_date': '29.07.2020', 'effective_date': '29.07.2020', 'effective_time': '13:00'}),
    ('dcabd534', {'head_office': 'Belize City', 'country': 'BZ', 'deletion_completed': False}),
    ('fbaa4000', {'statutes_date': '27.06.2013', 'previous_statutes_date': '27.07.2013'}),
])
def test_payload_values(prefix, expected):
    assert selected(prefix)[0].payload.items() >= expected.items()


def test_roles_signing_and_event_types():
    assert all(e.event_type == 'capital_changed' for e in selected('12199924'))
    assert selected('5227277b')[0].event_type == 'ownership_changed'
    assert selected('4b25a973')[0].role is None
    assert selected('4b25a973')[0].signing == 'Einzelunterschrift'
    president = selected('9457810b')[0]
    assert president.role == 'Präsident' and president.signing == 'Kollektivunterschrift zu zweien'
    associate = selected('9ddc431e')[0]
    assert associate.role == 'Gesellschafter' and associate.signing == 'ohne Zeichnungsberechtigung'
    managers = selected('b671b751')
    assert [e.payload['name'] for e in managers] == ['Spörri Jonathan', 'Galand Julien', 'Leclerc Jeremy-François']
    assert [e.signing for e in managers] == ['Kollektivunterschrift zu zweien', 'Einzelunterschrift', 'Einzelunterschrift']
    assert all(e.role == 'Geschäftsführer' for e in managers)
    assert managers[1].payload['place'] == 'Saint-Jorioz' and managers[1].payload['country2'] == 'FRA'
    assert managers[2].payload['additional_role'] == 'Präsident'
    board = selected('c1ab87b2')
    assert [e.payload['name'] for e in board] == ['Villar José', 'Bourrit Blaise', 'Gris Alain', 'Benagiano Giuseppe', 'Langer Glas Ana Maria']
    assert all(e.role == 'Verwaltungsrat' and e.signing == 'Kollektivunterschrift zu zweien' for e in board)
    committee = selected('d16ef08d')
    assert [e.payload['name'] for e in committee] == ['Galeuchet Margrit', 'Delley Maria Cristina']
    assert all(e.role == 'Vorstand' and e.signing == 'Kollektivunterschrift zu zweien' for e in committee)
    assert committee[1].payload['additional_role'] == 'Kassierin'


def test_duplicate_statutes_date_requires_matching_source():
    _, (args, kwargs) = captured('12199924')
    assert extract_parser344_leftovers(*args, source_text='unrelated source') == ([], args[0])


def test_invalid_french_dates_and_time_are_preserved():
    for prefix, old, new in [('495ee781', '18 juin', '32 juin'), ('495ee781', '31 juillet', '32 juillet'), ('d794d81f', '13:00', '25:00')]:
        _, (args, kwargs) = captured(prefix)
        text = args[0].replace(old, new)
        assert extract_parser344_leftovers(text, *args[1:], **kwargs) == ([], text)
