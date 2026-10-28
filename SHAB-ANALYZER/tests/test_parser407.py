import hashlib
import importlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser407 import extract_parser407_leftovers, _LEGACY

FIXTURES = Path(__file__).parent / 'fixtures'
# Supplied SHA-256 identifiers; deliberately independent of the sample directory.
SUPPLIED_SHA256 = [
    '140ffe37804ff86cbbaeb56f29488753b9d3198d3fa59e4a2a3b4b539e804b84',
    '1528b1c22e1093eea7afb07f846dfedc197c946766b9a62bd228ddd945ba961c',
    '42674d07f40a98e415186ca9c30472955a4cd6f42595949d566950018f5ed4ca',
    '570d9032becf179512b5dd093022aae5f248f189141240a7ca25848fe479683a',
    '586cdbd5f2c7da857a70d83d36fdd62c1e3cf3c175331111ae3951fa057d7144',
    '95f825819798cd61e20c147a0ac28167198db2ac7dcf8ced668a84ad84dd72e9',
    '981e2aaf5c4416c9f71522fc910a671167a6cf9b8641c0708833f164d6d71fe1',
    'd3ed19a98636feca4a637984a682ca256fcf6ee44279b30fc16f4b7ed45f1771',
    'e58e103650d6ed79d4195d6bc4fc59dc8a951406f73e7f0e09ee02bbdc6d1581',
    'e66d7b792f437bb21c5da0c6d0c8625acaf9a46c4ba9d127a35788f9feb2c56f',
    'f6dd543bd498136642d37ca0d8875de8ac88700da3c1b3eccb48b7994a42ea4b',
    'ff48162f585e7945604ab15682ce375aa7fb129fc18f7effbac1f363d49b13f1',
]
COUNTS = [3, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser407_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser407_leftovers', capture):
        result = parse_publication_xml(FIXTURES / (SUPPLIED_SHA256[index] + '.xml'))
    assert len(calls) == 1
    return result, calls[0]


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('index', range(12))
def test_complete_and_unchanged_legacy_payloads(index):
    import shab_analyzer.parse as parser
    result, (args, kwargs) = captured(index)
    added, rest = extract_parser407_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 417
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS[index] and not rest
    with patch.object(parser, 'extract_parser407_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (SUPPLIED_SHA256[index] + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('index', range(12))
def test_unknown_suffix_language_and_invalid_dates(index):
    _, (args, kwargs) = captured(index)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser407_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser407_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser407_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index', range(12))
def test_missing_optional_metadata_and_source(index):
    _, (args, kwargs) = captured(index)
    events, rest = extract_parser407_leftovers(*args[:4], None, None, None, **kwargs)
    assert events and not rest
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    events, rest = extract_parser407_leftovers(*args)
    assert events and not rest


def test_old_event_without_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event


EXPECTED = [
    ('officer_changed', {'name': 'Granziero Gilles'}),
    ('publication_corrected', {'previous_name': 'Chavaz Jean', 'given_names': 'Jean Charles', 'corrected': True}),
    ('company_name_changed', {'german_name': 'PRO-PART AG in Liquidation'}),
    ('status_changed', {'deleted': True}),
    ('officer_changed', {'name': 'von Fliedner Saskia Catherine', 'origin': 'Beringen', 'place': 'Belmont-sur-Lausanne', 'corrected': True}),
    ('status_changed', {'deleted': True, 'official': True}),
    ('publication_corrected', {'date': '14.12.2020', 'previous_date': '14.12.2021', 'kind': 'statutes_date'}),
    ('organization_changed', {'extension': 'vier', 'end_date': '26.05.2021', 'definitive': True, 'extended': True}),
    ('capital_changed', {'voting_count': "200'000", 'previous_count': "5'000", 'count': "10'000", 'nominal': '10'}),
    ('company_merged', {'assets': "1'900'522'092", 'liabilities': '967', 'absorbed_uid': 'CHE-399.847.136', 'capital_increase': False, 'shares_allocated': False}),
    ('status_changed', {'decision_date': '31.12.2020', 'appeal_date': '24.12.2020', 'bankruptcy_date': '10.12.2020', 'suspensive_effect': True}),
    ('branch_changed', {'place': 'Plaffeien', 'notice_date': '29.12.2020', 'notice_id': '1005061141', 'removed': True}),
]


@pytest.mark.parametrize('index', range(12))
def test_payload_semantics(index):
    _, (args, kwargs) = captured(index)
    events, rest = extract_parser407_leftovers(*args, **kwargs)
    kind, fields = EXPECTED[index]
    assert not rest and events[0].event_type == kind
    for key, value in fields.items():
        assert events[0].payload[key] == value
    if index == 0:
        assert [e.signing for e in events] == ['Kollektivunterschrift zu zweien'] * 3
        assert [e.role for e in events] == ['Präsident des Verwaltungsrates', 'Mitglied des Verwaltungsrates', 'Mitglied des Verwaltungsrates']
        assert [e.payload['place'] for e in events] == [None, 'Genthod', 'Tannay']
    if index == 1:
        assert 'name' not in events[0].payload
    if index == 2:
        assert events[1].event_type == 'capital_changed'
        assert events[1].payload['transfer_restricted'] is False
        assert events[0].payload['italian_name'] == 'PRO-PART SA in liquidazione'
        assert events[0].payload['english_name'] == 'PRO-PART Ltd in liquidation'
        assert events[0].payload['translations'] == {'de': 'PRO-PART AG in Liquidation', 'it': 'PRO-PART SA in liquidazione', 'en': 'PRO-PART Ltd in liquidation'}
    if index == 5:
        assert 'activity_ceased' not in events[0].payload
        assert 'no_opposition' not in events[0].payload
    if index == 9:
        assert '(TE Connectivity Finance Alpha I LLC)' in events[0].payload['absorbed_name']


def test_inconsistent_split_is_not_consumed():
    _, (args, kwargs) = captured(8)
    changed = args[0].replace("10'000", "10'001")
    assert changed != args[0]
    assert extract_parser407_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('version,text,lang', [
    (50, 'Administration: Exemple Anne, nommé président, et Exemple Jean, de Berne, à Lausanne, lesquels signent collectivement à deux', 'fr'),
    (50, "Aucune opposition motivée n'ayant été présentée, la société est radiée d'office, conformément à l'art. 159, al. 5, let. a aORC", 'fr'),
    (131, 'Mit Verfügung vom 21.01.2021 hat das Bezirksgericht Bern die gewährte definitive Nachlassstundung um vier Monate bis zum 26.05.2021 verlängert', 'de'),
    (360, 'Mit Urteil vom 21.01.2021 hat die Einzelrichterin im summarischen Verfahren des Bezirksgerichts Bern die gewährte definitive Nachlassstundung um drei Monate bis 26.05.2021 verlängert', 'de'),
    (377, 'Mit Entscheid vom 31.12.2020 hat das Kantonsgericht Bern dem Rekurs vom 24.12.2020 gegen das Konkurseröffnungsurteil vom 10.12.2020 die aufschiebende Wirkung erteilt (Art. 159 Abs. 2 HRegV)', 'de'),
])
def test_legacy_rules_keep_ownership_in_isolation(version, text, lang):
    module = importlib.import_module(f'shab_analyzer.parser{version}')
    args = text, lang, 'p', '', None, None, None
    events, rest = getattr(module, f'extract_parser{version}_leftovers')(*args)
    assert events and not rest.strip(' .')
    if version in (50, 131):
        assert any(pattern.fullmatch(text) for pattern in _LEGACY)
    assert extract_parser407_leftovers(*args) == ([], text)


@pytest.mark.parametrize('text', ['', 'Unknown clause'])
def test_unknown_and_empty_are_unchanged(text):
    assert extract_parser407_leftovers(text, 'fr', 'p', '', None, None, None) == ([], text)


@pytest.mark.parametrize('digest', ['44e94aea3c0b2c9c8ea78768d304973a66c7d5435a33d3cf7c1ab6ce374fb4fb', '86d82a806dc46c9412d7ca5b87c455248dab2f540ae748ddde08833364c60855', 'a229f0da90ec6b035849a687dd9f89595e39b71e8aa99b930ec311ae7df049fa', 'b7587f8484323d203ddbc21ad45a4aadf0073d64909c1c842c2cb4cc7f265506', 'c1eaa10297bcb036fc1a85d6806562d3a428778420178f7707d9b1475b7d0d19', 'c3136cb2a1ea35ba14492bfb13b7919609bdcbd4d6af2ada60f1541bacc6fffb', 'd6e9d4eee1efb2dbfd29316c043ca3291bab3ab9ba0aa1cd4866c9bed3c1a77d', 'e298f6fecca6ae6741e8823c73cb6aaf0d50b46eabe1c4891864927557a6f4d9', 'eeb50e3900c2cec2570c1950052da7c597cf173b5ea13b3c343b369973841d76', 'ef68e80d4f36b84bd5fc7111d45171c341b238733197f6ea9e83d217886eb726', 'f5059597c95f9395535d565988afd5ac507e59ba419e436d9ba34da22ddd0561', 'f5415425ecdcfe8cd530085e8f8de3d2ab2e81a673b8ea70bb53c79db780b9c0'])
def test_previous_release_fixtures_unchanged(digest):
    import shab_analyzer.parse as parser
    path = FIXTURES / (digest + '.xml')
    result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser407_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(path)
