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
from shab_analyzer.parser408 import extract_parser408_leftovers, _LEGACY

FIXTURES = Path(__file__).parent / 'fixtures'
# Supplied SHA-256 identifiers; deliberately independent of the sample directory.
SUPPLIED_SHA256 = ['029874c544b7139eac5b7ca4121ab0d6673f7ca100c80fe923e57d921fc00b9d', '0963015faf5c515c36bfb83e5338216ef2e98d68d389573406c59773c53fd0e5', '229384dbfdc115d4511c5a8a919434194ba9120a901ca159c7c94dbbd12a58a5', '3c63f8fce943ab7a73ca214cff3635cd2ef58e1f3a2a13d071fdc4a0358c925d', '6f2212a50e06e856da4d07b9a64bf750e5f5ece1e7f59437541ae79346322e0d', '8a059a7805b839391676c4a7c01b9a501e3ba8dd8eda831d79ec67f44f8660a2', '91dd3d9d8479b65c71e5f50b75d0bbabd73c28fce4b531458ad34a53ca4098bc', 'b503a1ab0f260ad9e5833c8d61e06188ab8d130e6d1a2825bc5540a21bcc84c9', 'bfcb4b77337b27bff1d555670b097f49805f95b638e6840b054fbe787f343799', 'c116d1c5a5c8368bc34a9ecb82dc594de9b41fafd4eac566fc29ceb9acd7d9dc', 'c1698184a56fbd7644c941ec1bc310dbe0d06eb634164edfcc0d8fed35dd8c5f', 'e0ad3f5c11307ec199f5b214a7b7e7d505017859961f3a36935e3a116ec78d17']
COUNTS = [1, 1, 1, 1, 2, 1, 4, 1, 2, 2, 2, 2]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser408_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser408_leftovers', capture):
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
    added, rest = extract_parser408_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 409
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS[index] and not rest
    with patch.object(parser, 'extract_parser408_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (SUPPLIED_SHA256[index] + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('index', range(12))
def test_unknown_suffix_language_and_invalid_dates(index):
    _, (args, kwargs) = captured(index)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser408_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser408_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser408_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index', range(12))
def test_missing_optional_metadata_and_source(index):
    _, (args, kwargs) = captured(index)
    events, rest = extract_parser408_leftovers(*args[:4], None, None, None, **kwargs)
    assert events and not rest
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    events, rest = extract_parser408_leftovers(*args)
    assert events and not rest


def test_old_event_without_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event


EXPECTED = [
    ('address_changed', {'removed': True, 'postal_code': '4424'}),
    ('assets_transferred', {'agreement_date': '18.12.2020', 'consideration': "21'100'000"}),
    ('ownership_changed', {'count': '80', 'buyer_count': '160'}),
    ('officer_changed', {'signing_restriction': 'avec le président'}),
    ('ownership_changed', {'remaining': '20', 'count': '180'}),
    ('assets_transferred', {'credit': "5'067'100.00"}),
    ('officer_changed', {'name': 'Mehta Raman'}),
    ('assets_transferred', {'consideration_none': True, 'approval_date': '27 octobre 2020'}),
    ('officer_changed', {'removed': True}),
    ('officer_changed', {'signing_restriction': 'avec le président ou le vice-président'}),
    ('status_changed', {'dissolved': True, 'decision_date': '15.01.2021'}),
    ('ownership_changed', {'intermediary_uid': 'CHE-365.510.420', 'count': '8'}),
]

@pytest.mark.parametrize('index', range(12))
def test_payload_semantics(index):
    _, (args, kwargs) = captured(index)
    events, rest = extract_parser408_leftovers(*args, **kwargs)
    kind, fields = EXPECTED[index]
    assert not rest and events[0].event_type == kind
    for key, value in fields.items():
        assert events[0].payload[key] == value
    if index == 3:
        assert events[0].role is None
        assert events[0].signing == 'Kollektivunterschrift zu zweien'
    if index == 6:
        assert [e.signing for e in events] == ['Einzelunterschrift'] * 4
        assert [e.role for e in events] == ['Präsident des Verwaltungsrates', 'Mitglied des Verwaltungsrates', 'Vizepräsidentin des Verwaltungsrates', 'Mitglied des Verwaltungsrates']
    if index in (4, 10, 11):
        assert events[1].event_type == 'officer_changed'
    if index == 8:
        assert events[0].payload['place'] is None
        assert events[1].payload['place'] == 'Estavayer'
        assert events[1].signing == 'Kollektivunterschrift zu zweien'
    if index == 9:
        assert len(events) == 2
        assert all(e.payload['signing_restriction'] == fields['signing_restriction'] for e in events)

@pytest.mark.parametrize('version,text,lang', [
    (71, '[bisher: Die Gesellschaft führt an folgender Adresse ihr Geschäftsdomizil: Beispielweg 1, 3000 Bern.]', 'de'),
    (63, 'Gelöschte Person: Beispiel Anna, Geschäftsführerin, Einzelunterschrift. Eingetragene Person geändert: Beispiel Beat, Geschäftsführer, Einzelunterschrift, neu Liquidator, Einzelunterschrift. Neu eingetragene Person: Beispiel Claire, von und in Bern, Geschäftsführerin, Kollektivunterschrift zu zweien', 'de'),
])
def test_legacy_ownership_in_isolation(version, text, lang):
    module = importlib.import_module(f'shab_analyzer.parser{version}')
    args = text, lang, 'p', '', None, None, None
    events, rest = getattr(module, f'extract_parser{version}_leftovers')(*args)
    assert events and not rest.strip(' .')
    assert any(pattern.fullmatch(text) for pattern in _LEGACY)
    assert extract_parser408_leftovers(*args) == ([], text)

@pytest.mark.parametrize('text', ['', 'Unknown clause'])
def test_unknown_is_unchanged(text):
    assert extract_parser408_leftovers(text, 'fr', 'p', '', None, None, None) == ([], text)

@pytest.mark.parametrize("digest", ['140ffe37804ff86cbbaeb56f29488753b9d3198d3fa59e4a2a3b4b539e804b84', '1528b1c22e1093eea7afb07f846dfedc197c946766b9a62bd228ddd945ba961c', '42674d07f40a98e415186ca9c30472955a4cd6f42595949d566950018f5ed4ca', '570d9032becf179512b5dd093022aae5f248f189141240a7ca25848fe479683a', '586cdbd5f2c7da857a70d83d36fdd62c1e3cf3c175331111ae3951fa057d7144', '95f825819798cd61e20c147a0ac28167198db2ac7dcf8ced668a84ad84dd72e9', '981e2aaf5c4416c9f71522fc910a671167a6cf9b8641c0708833f164d6d71fe1', 'd3ed19a98636feca4a637984a682ca256fcf6ee44279b30fc16f4b7ed45f1771', 'e58e103650d6ed79d4195d6bc4fc59dc8a951406f73e7f0e09ee02bbdc6d1581', 'e66d7b792f437bb21c5da0c6d0c8625acaf9a46c4ba9d127a35788f9feb2c56f', 'f6dd543bd498136642d37ca0d8875de8ac88700da3c1b3eccb48b7994a42ea4b', 'ff48162f585e7945604ab15682ce375aa7fb129fc18f7effbac1f363d49b13f1'])
def test_previous_release_unchanged(digest):
    import shab_analyzer.parse as parser
    path = FIXTURES / (digest + '.xml')
    result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser408_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(path)

@pytest.mark.parametrize('version,text', [
    (162, 'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom 07.01.2021 und Bilanz per 31.12.2020 Teilaktiven von CHF 100 und Teilpassiven (Fremdkapital) von CHF 20 auf die Beispiel AG (CHE-123.456.789), in Bern. Gegenleistung: 1 Namenaktien zu CHF 10 und Gutschrift einer Forderung von CHF 70'),
    (165, 'Die Gesellschaft wird gemäss Beschluss der Gesellschafterversammlung vom 15.01.2021 aufgelöst. Die Liquidation wird unter der Firma: Beispiel GmbH in Liquidation durchgeführt. Eingetragene Person geändert: Beispiel Beat, Gesellschafter, 20 Stammanteile zu CHF 100, Geschäftsführer, Einzelunterschrift, neu Gesellschafter, 20 Stammanteile zu CHF 100, Geschäftsführer, Liquidator, Einzelunterschrift. Liquidationsadresse: Beispielweg 1, 3000 Bern'),
])
def test_related_complete_legacy_clauses_pass_through(version, text):
    module = importlib.import_module(f'shab_analyzer.parser{version}')
    args = text, 'de', 'p', '', None, None, None
    events, rest = getattr(module, f'extract_parser{version}_leftovers')(*args)
    assert events and not rest.strip(' .')
    assert any(pattern.fullmatch(text) for pattern in _LEGACY)
    assert extract_parser408_leftovers(*args) == ([], text)

@pytest.mark.parametrize('index', [2, 4, 11])
def test_inconsistent_nominal_is_not_consumed(index):
    _, (args, kwargs) = captured(index)
    changed = re.sub(r'CHF [\d\x27.]+$', 'CHF 999', args[0])
    assert changed != args[0]
    assert extract_parser408_leftovers(changed, *args[1:], **kwargs) == ([], changed)

@pytest.mark.parametrize('previous,replacement', [('6, 22 et 24', '31, 22 et 24'), ('27 octobre', '32 octobre')])
def test_invalid_written_date_is_not_consumed(previous, replacement):
    _, (args, kwargs) = captured(7)
    changed = args[0].replace(previous, replacement)
    assert changed != args[0]
    assert extract_parser408_leftovers(changed, *args[1:], **kwargs) == ([], changed)
