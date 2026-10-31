import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser432 import extract_parser432_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['01312b5db0ecdbcf5be78bdaf6c492b2d78e9aaed4672e325fdc0387ac6b56d1', '02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '384c2df3999d3936131f04916e6a38ac876aa6594f1c11fa88657884af3e1b8d', '5f693d80c6e5af76e0ea71274f2e69b0de19118660fd5ec933dcc86e444b4d26', '7102d71384b400afabaee70016c21fe81e17738065335be24d84c3237f245a94', '724f36c7c9cbd8ac441e3c95a8348af22bcac869d1412bc4724da7058bfbd114', 'a4842e0f979be041c40e87153f0317797765cd5f1b7d3d2f3e0edf3efddb5b19', 'b02a4bc87bb38ec348bffb73b43c7914ce59b053206e02f4994fe50e8babd427', 'c4329dd10a978ef13c4b75be0bc60f799a727458f147c54eff24976ca6dfa846', 'd8ba11732a76f8eba477bc36ec52a2955e14c3f2e20a198c38fb43c614401bf3', 'e6052a6e3f7b2e147683bcded8fd4db68c7e54b4734035d1848c0db098e99402', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
COUNTS = [1, 0, 0, 1, 1, 3, 1, 1, 1, 1, 1, 0]
NEW_CASES = [i for i, count in enumerate(COUNTS) if count]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser432_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser432_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(path)
    assert len(calls) == 1
    return result, old, calls[0]


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('index', NEW_CASES)
def test_complete_and_unchanged_old_payloads(index):
    result, old, (args, kwargs) = captured(index)
    added, rest = extract(*args, **kwargs)
    assert PARSER_VERSION == 446
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    assert len(added) == COUNTS[index] and rest == ''
    assert old.leftover_text == args[0]
    assert result.events == old.events + added
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('index', NEW_CASES)
def test_unknown_suffix_language_and_invalid_dates(index):
    _, _, (args, kwargs) = captured(index)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract(changed, *args[1:], **kwargs) == ([], changed)
    assert extract(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index', NEW_CASES)
def test_missing_optional_metadata_and_source(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args[:4], None, None, None, **kwargs)
    assert len(events) == COUNTS[index] and rest == ''
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    events, rest = extract(*args)
    assert len(events) == COUNTS[index] and rest == ''


def test_old_event_without_optional_attributes():
    event = Event('p', '', 'officer_changed', 'legacy.rule', payload={'name': 'Test Anna'})
    assert Event(**vars(event)) == event
    assert event.payload == {'name': 'Test Anna'}
    assert event.role is None and event.signing is None


@pytest.mark.parametrize('index', NEW_CASES)
def test_no_overlap_with_old_rules_even_in_isolation(index):
    # Exercise every historical extractor on the complete clause in isolation.
    import inspect
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(index)
    for name, old_extract in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser432_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name


@pytest.mark.parametrize('index,owner', [(1, 60), (2, 55), (11, 55)])
def test_existing_formulations_retain_historical_ownership(index, owner):
    import importlib
    result, old, (args, kwargs) = captured(index)
    old_extract = getattr(importlib.import_module(f'shab_analyzer.parser{owner}'), f'extract_parser{owner}_leftovers')
    expected = old_extract(*args)
    assert expected[0] or expected[1] != args[0]
    assert extract(*args, **kwargs) == ([], args[0])
    assert result == old
    assert result.status == 'PARTIALLY_PARSED'
    assert result.leftover_text == args[0]
    assert old_extract(*args) == expected


@pytest.mark.parametrize('index,kind,action', [
    (0, 'capital_changed', 'limited_partner_contribution_reduced'),
    (3, 'assets_transferred', 'foundation_asset_transfer_written_dates'),
    (4, 'capital_changed', 'conditional_capital_increase_adjusted'),
    (5, 'officer_changed', 'board_collective_signing_three'),
    (6, 'ownership_changed', 'share_transfer_resulting_holdings_typo'),
    (7, 'status_changed', 'sole_proprietor_bankruptcy_appeal_suspensive_effect'),
    (8, 'status_changed', 'head_office_bankruptcy_suspended_lack_assets'),
    (9, 'status_changed', 'erroneous_deletion_without_tax_authorization_reinstated'),
    (10, 'officer_changed', 'individual_to_collective_signing_without_commas'),
])
def test_evidenced_semantics(index, kind, action):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    assert rest == ''
    assert all(e.event_type == kind and e.payload['action'] == action for e in events)
    assert all(e.rule_id == f'{args[1]}.text.{action}.v1' for e in events)
    payload = events[0].payload
    if index == 0:
        assert (payload['previous'], payload['amount']) == ("27'600'000", "17'600'000")
        assert payload['currency'] == 'CHF'
    elif index == 3:
        assert (payload['assets'], payload['liabilities']) == ("2'380'449.40", "2'380'448.40")
        assert payload['consideration'] == 'aucune'
        assert payload['agreement_month'] == 'juin' and payload['decision_month'] == 'septembre'
    elif index == 4:
        assert payload['decision_date'] == '01.03.2021'
    elif index == 5:
        assert [e.role for e in events] == ['président', 'administrateur', 'administrateur']
        assert all(e.signing == 'Kollektivunterschrift zu dreien' for e in events)
    elif index == 6:
        assert (payload['count'], payload['remaining'], payload['nominal']) == ('120', '80', '100')
    elif index == 7:
        assert payload['suspensive_effect'] is True and payload['bankruptcy_entry_removed'] is True
        assert payload['opening_time'] == '11.45'
    elif index == 8:
        assert payload['scope'] == 'head_office' and payload['suspended'] is True
    elif index == 9:
        assert payload['reinstated'] is True
    elif index == 10:
        assert events[0].signing == 'Kollektivunterschrift zu zweien'
        assert payload['previous_signing'] == 'Einzelunterschrift'


def test_invalid_written_date_and_inconsistent_amounts():
    for index, before, after in [(3, '4 et 22 juin', '31 et 22 juin'), (0, "17'600'000", "37'600'000"), (6, '120', '0')]:
        _, _, (args, kwargs) = captured(index)
        text = args[0].replace(before, after)
        assert text != args[0]
        assert extract(text, *args[1:], **kwargs) == ([], text)
