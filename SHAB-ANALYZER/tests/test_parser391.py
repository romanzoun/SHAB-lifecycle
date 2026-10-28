import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser391 import extract_parser391_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = ['033d86eb432e17a24483de93565a656b58c52e16b806efb8b02dc8371f54d28b', '21005e713da43172a802e9664e98d118d0aed09f57c6842663eb97d1c05592ff', '2933235242f53718d7507a45733a3c1fcecbb07f0bc853799b198121ded6b51a', '510f0cf6f55068dead640ed36b1af49c5c25830626aff6d3772e8e441d2beca2', '5ccceacef21c4e158490d060ca912aca21f000014520d051e039468a2ff82e95', 'a014f74ac3784abdc9fd5f94ce92e1738cbfa428f55070d0f1d16fc209803a3e', 'b38613605644454d4490842e906a029d721bf625699dffb3a52e0e7b759f45e2', 'bf46357687bce1d0578d014f0ebdc049f256def5cceacf9bd99d904226df9db1', 'cb5bf3fc8d49f29cdcf8784c250051cf600f2cfebd88114298682019eaf69f50', 'e2ebda3291861665205eaf1e84d93e28d2c3b35836ada76247037b6c03daaf62', 'e58347b87675085fd344c21624300048fe69cf77fd4c34b7fd80f7a52854047f', 'ea4324d032f6a932b95ef41320ca82700b98106ce4ce52f28fb533689a3c054a']
CONTEXT_REQUIRED = set()
COUNTS = {"e58347b8": 4}

@lru_cache(None)
def captured(digest):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser391_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser391_leftovers', capture):
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
    added, rest = extract_parser391_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 418
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS.get(digest[:8], 1) and not rest
    with patch.object(parser, 'extract_parser391_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_unknown_suffix_and_language_preserve_input(digest):
    _, (args, kwargs) = captured(digest)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser391_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser391_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_missing_optional_source_and_invalid_dates(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser391_leftovers(*args)
    if digest[:8] in CONTEXT_REQUIRED:
        assert not events and rest == args[0]
    else:
        assert len(events) == COUNTS.get(digest[:8], 1) and not rest
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser391_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_old_event_without_new_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event



EXPECTED_ACTIONS = [
    'cooperative_dissolved_general_meeting',
    'bankruptcy_execution_suspended_appeal_withdrawn',
    'organization_statement_removed_no_longer_required',
    'asset_transfer_no_consideration',
    'conditional_participation_capital_statutes_corrected',
    'asset_transfer_registered_shares_no_consideration',
    'female_managers_share_transfer_existing_president',
    'asset_transfer_assets_only_no_inventory',
    'single_person_powers_revoked_elision',
    'manager_share_transfer_to_existing_director',
    'four_company_merger_same_owner',
    'associate_residence_corrected_notice',
]

@pytest.mark.parametrize('digest,action', list(zip(SUPPLIED_SHA256, EXPECTED_ACTIONS)))
def test_explicit_meaning(digest, action):
    result, (args, kwargs) = captured(digest)
    events, rest = extract_parser391_leftovers(*args, **kwargs)
    assert not rest and events
    assert all(e.payload['action'] == action for e in events)
    assert all(e.rule_id == args[1] + '.text.' + action + '.v1' for e in events)
    p = events[0].payload
    if digest.startswith('033d'):
        assert events[0].event_type == 'status_changed' and p['decision_date'] == '07.09.2020'
    elif digest.startswith('2100'):
        assert events[0].event_type == 'status_changed' and p['appeal_withdrawn'] is True
        assert (p['suspension_date'], p['bankruptcy_date'], p['closure_date']) == ('26.10.2020', '05.10.2020', '07.12.2020')
    elif digest.startswith('510f'):
        assert (p['assets'], p['liabilities'], p['net_assets'], p['consideration']) == ("1'016'675.58", '0', "1'016'675.58", 'aucune')
    elif digest.startswith('5ccc'):
        assert events[0].event_type == 'capital_changed' and p['notice_date'] == '13-07-2020'
    elif digest.startswith('a014'):
        assert (p['count'], p['nominal'], p['company_uid'], p['recipient_uid']) == ('400', '500.00', 'CHE-107.881.911', 'CHE-446.879.960')
    elif digest.startswith('b386'):
        assert (p['remaining'], p['count'], p['buyer_count']) == ('5', '70', '195')
    elif digest.startswith('bf46'):
        assert p['assets'] == p['consideration'] == "100'000.00" and 'liabilities' not in p
    elif digest.startswith('cb5b'):
        assert p['powers_revoked'] is True and events[0].role is None and events[0].signing is None
    elif digest.startswith('e2eb'):
        assert (p['count'], p['previous'], p['remaining']) == ('25', '200', '175')
    elif digest.startswith('e583'):
        assert len(events) == 4
        assert [e.payload['transferor_uid'] for e in events] == ['CHE-102.226.627', 'CHE-109.053.339', 'CHE-105.634.655', 'CHE-114.570.072']
        assert [e.payload['capital_social'] for e in events] == [' et du capital social', None, None, None]
    elif digest.startswith('ea43'):
        assert events[0].role == 'associé' and events[0].signing == 'Kollektivunterschrift zu zweien'
        assert (p['place'], p['previous_place']) == ('Billens-Hennens', 'Henniez')


def test_legacy_female_transfer_retains_ownership():
    from shab_analyzer import parser155
    from shab_analyzer.parser391 import _LEGACY
    text = "L'associée-gérante Exemple Anne détient désormais 5 parts de CHF 100 par suite de cession de 70 parts de CHF 100 à Exemple Eve, de Berne, à Paris, FRA, nouvelle associée-gérante pour 70 parts de CHF 100"
    pattern = parser155._FR_FEMALE_MANAGER_TRANSFER_NEW_FEMALE_MANAGER
    assert pattern in _LEGACY and pattern.fullmatch(text)
    assert parser155.extract_parser155_leftovers(text, 'fr', 'p', '', None, None, None)[0]
    assert extract_parser391_leftovers(text, 'fr', 'p', '', None, None, None) == ([], text)


def test_two_person_revocation_retains_ownership():
    from shab_analyzer.parser300 import extract_parser300_leftovers
    text = "Les pouvoirs d'Exemple Anne et Exemple Eve sont radiés"
    assert len(extract_parser300_leftovers(text, 'fr', 'p', '', None, None, None)[0]) == 2
    assert extract_parser391_leftovers(text, 'fr', 'p', '', None, None, None) == ([], text)


def test_invalid_dash_date_preserves_input():
    _, (args, kwargs) = captured(SUPPLIED_SHA256[4])
    changed = args[0].replace('13-07-2020', '31-02-2020')
    assert extract_parser391_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_merger_is_atomic_and_requires_supported_component_count():
    _, (args, kwargs) = captured(SUPPLIED_SHA256[10])
    for changed in (args[0].replace('04.12.2020', '31.02.2020', 1),
                    args[0].rsplit('. Reprise des actifs et passifs de ', 1)[0]):
        assert extract_parser391_leftovers(changed, *args[1:], **kwargs) == ([], changed)
