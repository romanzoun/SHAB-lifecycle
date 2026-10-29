import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser393 import extract_parser393_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = ['0714aa9f7bd761f1af358f24f38c2d75bce9c56ab7868d8cb90f02d8f135f5e1', '1070c6e05ac976490fd0123d3757b45bdf453b50e425b59ab58eb11218c7d27c', '12c6fe27e002a7e2944e240720ecab80d2389a5bdb4ddf4aa263bafa37e40ce0', '2a794bcc977a39417e79895218a83f45a67b40be9fef823bdb45b9aace013e30', '5728812e2f79bde00035a6a0079446aa883702bdaa7bbdaf0d837436952b716a', '7880df9e9e9f6494679e0bca7501551049fc09b9543f5703a5bca8e2969a2e7f', 'a91bb6c0694cdcf2b7e37a4680487719e2a98e087020f6c3696ace0c1fcdf2a7', 'c0a3821229c5a322a18f0497528d00129d76f4e893e5d3770414d72b971085d7', 'daa2afa98734de324010d1da6219c56469a4f1a921e6b60e0332e68ff2c3f169', 'e949e2710b379160fdbde898f911e1d053970aa6c29a67b37ac0d1404f6e6d6a', 'f379d78285bacd29c20348cb215dd528b1e21043f45b84e94c62156a4344d782', 'fa5328d4218aea5d8f1cf842a4ab6ec9f2069651668e351ba0e646fe91c47ae4']
CONTEXT_REQUIRED = set()
COUNTS = {'0714aa9f': 2, '1070c6e0': 2, '12c6fe27': 3, 'e949e271': 3, 'fa5328d4': 2}


@lru_cache(None)
def captured(digest):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser393_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser393_leftovers', capture):
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
    added, rest = extract_parser393_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 433
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS.get(digest[:8], 1) and not rest
    with patch.object(parser, 'extract_parser393_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_unknown_suffix_and_language_preserve_input(digest):
    _, (args, kwargs) = captured(digest)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser393_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser393_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_missing_optional_source_and_invalid_dates(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser393_leftovers(*args)
    if digest[:8] in CONTEXT_REQUIRED:
        assert not events and rest == args[0]
    else:
        assert len(events) == COUNTS.get(digest[:8], 1) and not rest
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser393_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_old_event_without_new_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event


EXPECTED_ACTIONS = [
    'limited_partner_contribution_increased_powers_deleted',
    'two_holders_transfer_unsigned_associate',
    'three_proxies_replaced_individual_signing_typo',
    'purpose_corrected_hyphenated_notice_date',
    'foundation_asset_transfer_addendum_authority',
    'owner_origin_municipal_merger',
    'asset_transfer_cash_consideration',
    'bankruptcy_subsequently_revoked',
    'provisional_covid_moratorium_authorized',
    'proxy_signing_exclusion_notice_completed',
    'ordinary_capital_increase_claims_corrected',
    'share_transfer_domestic_unsigned_associate',
]


@pytest.mark.parametrize('digest,action', list(zip(SUPPLIED_SHA256, EXPECTED_ACTIONS)))
def test_explicit_meaning(digest, action):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser393_leftovers(*args, **kwargs)
    assert not rest and events[0].payload['action'] == action
    p = events[0].payload
    if digest.startswith('0714'):
        assert (p['previous_amount'], p['amount']) == ("3'325'000", "3'825'000")
        assert events[1].signing == 'ohne Zeichnungsberechtigung'
    elif digest.startswith('1070'):
        assert (p['count'], p['previous'], p['received'], p['remaining']) == ('33', '100', '66', '67')
        assert events[1].role == 'associé' and events[1].signing == 'ohne Zeichnungsberechtigung'
    elif digest.startswith('12c6'):
        assert all(e.signing == 'Einzelunterschrift' and e.payload['procuration_extinguished'] for e in events)
    elif digest.startswith('2a79'):
        assert p['notice_date'] == '27-11-2020' and p['purpose'].endswith('(cf. statuts pour but complet)')
    elif digest.startswith('5728'):
        assert (p['assets'], p['liabilities'], p['no_consideration'], p['organization_entry_deleted']) == ("5'050'416.15", "3'373'638.75", True, True)
    elif digest.startswith('7880'):
        assert p['origin'] == 'Rochefort'
    elif digest.startswith('a91b'):
        assert (p['assets'], p['liabilities'], p['consideration']) == ("910'676.66", "770'516.14", "140'160.52")
    elif digest.startswith('c0a3'):
        assert events[0].event_type == 'status_changed' and p['decision_date'] == '02.12.2020'
    elif digest.startswith('daa2'):
        assert events[0].event_type == 'status_changed' and p['months'] == '3'
    elif digest.startswith('e949'):
        assert all(e.signing is None and len(e.payload['excluded_signing_group']) == 3 for e in events)
    elif digest.startswith('f379'):
        assert (p['claims'], p['previous_claims'], p['count'], p['previous_count']) == ("1'657'273.3923", "1'599'983.36936", "4'524'855", "4'368'436")
        assert events[0].event_type == 'capital_changed'
    elif digest.startswith('fa53'):
        assert (p['count'], p['previous'], p['nominal']) == ('30', '100', '200')
        assert events[1].payload['origin'] == events[1].payload['place'] == 'Provence'


def test_legacy_proxy_pattern_retains_ownership():
    from shab_analyzer import parser68
    from shab_analyzer.parser393 import _LEGACY
    text = 'Exemple Anne, Exemple Eve et Exemple Jean, dont la procuration est éteinte, engagent désormais la société par leur signature collective à deux, toutefois entre eux'
    assert parser68._FR_THREE_PROXIES_REPLACED_WITH_SIGNING in _LEGACY
    assert parser68._FR_THREE_PROXIES_REPLACED_WITH_SIGNING.fullmatch(text)
    assert parser68.extract_parser68_leftovers(text, 'fr', 'p', '', None, None, None)[0]
    assert extract_parser393_leftovers(text, 'fr', 'p', '', None, None, None) == ([], text)


@pytest.mark.parametrize('number', [289, 312, 320, 348, 392])
def test_legacy_fixtures_keep_unmodified_residuals(number):
    import importlib.util
    spec = importlib.util.spec_from_file_location(f'legacy_test_parser{number}', Path(__file__).with_name(f'test_parser{number}.py'))
    previous = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(previous)
    cases = previous.SUPPLIED_SHA256 if number == 392 else [case[0] for case in previous.CASES]
    for digest in cases:
        if number in (289, 312):
            args, kwargs = previous.invocation(digest)
        else:
            _, (args, kwargs) = previous.captured(digest)
        assert extract_parser393_leftovers(*args, **kwargs) == ([], args[0])
