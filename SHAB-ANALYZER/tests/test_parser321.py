import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser321 import extract_parser321_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('1c32869f', 'fr.text.two_unsigned_associates_share_transfer.v1', 3),
    ('2aba4a40', 'de.text.nested_name_translations_completed.v1', 1),
    ('37ad5819', 'fr.text.authorized_capital_clause_replaced.v1', 1),
    ('3e374c31', 'fr.text.two_new_managers_share_transfer.v1', 4),
    ('53cab221', 'fr.text.merger_subordination_minority_compensation.v1', 1),
    ('55f64321', 'fr.text.registered_names_correction_reference.v1', 3),
    ('56744f6b', 'fr.text.liquidation_company_name_restored.v1', 1),
    ('71d1272c', 'de.text.asset_transfer_assets_without_currency.v1', 1),
    ('76067542', 'fr.text.administrator_spelling_corrected.v1', 1),
    ('843c42c4', 'fr.text.two_directors_joint_signing_different_places.v1', 2),
    ('89f4f0de', 'fr.text.foundation_chair_change_joint_signing.v1', 2),
    ('c979609b', 'fr.text.director_alternative_signing.v1', 1),
]


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
        return extract_parser321_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser321_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    result, _ = captured(prefix)
    rule = next(rule for stem, rule, _ in CASES if stem == prefix)
    return [e for e in result.events if e.rule_id == rule]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 359
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    with patch.object(parser, 'extract_parser321_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert [e for e in result.events if e.rule_id != rule] == baseline.events
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser321_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser321_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]


@pytest.mark.parametrize('prefix', ['37ad5819', '53cab221', '55f64321', '56744f6b', '71d1272c', '76067542'])
def test_invalid_dates_preserved(prefix):
    _, (args, kwargs) = captured(prefix)
    dates = set(re.findall(r'\d{2}[.-]\d{2}[.-]\d{4}', args[0]))
    assert dates
    for date in dates:
        changed = args[0].replace(date, '31.02.2020' if '.' in date else '31-02-2020')
        events, leftover = extract_parser321_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed


@pytest.mark.parametrize('prefix,old,new', [
    ('1c32869f', 'cède 8', 'cède 9'),
    ('3e374c31', '104 parts', '105 parts'),
    ('53cab221', "3'239'410.29", "3'239'410.30"),
    ('53cab221', '98%', '100%'),
    ('843c42c4', 'collective à deux', 'individuelle'),
    ('89f4f0de', 'collectivement à deux', 'individuellement'),
    ('c979609b', 'individuelle ou collective', 'individuelle et collective'),
])
def test_unsupported_terms_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    events, leftover = extract_parser321_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix', ['2aba4a40', '3e374c31', '55f64321'])
def test_missing_optional_source_context_preserves_residual(prefix):
    _, (args, _) = captured(prefix)
    events, leftover = extract_parser321_leftovers(*args)
    assert not events and leftover == args[0]


def test_payloads_roles_and_signing():
    transfer = selected('1c32869f')
    assert transfer[0].event_type == 'ownership_changed'
    assert transfer[0].payload['remaining'] == '182'
    assert all(e.role == 'Gesellschafter' and e.signing == 'ohne Zeichnungsberechtigung' for e in transfer[1:])
    names = selected('2aba4a40')[0].payload
    assert names['french'].endswith('(ASSM)') and names['italian'].endswith('(ASSM)')
    assert names['english'].endswith('(SAMS)')
    capital = selected('37ad5819')[0]
    assert capital.event_type == 'capital_changed'
    assert capital.payload['previous_clause_removed'] is True and capital.payload['new_clause_introduced'] is True
    managers = selected('3e374c31')
    assert managers[0].payload['remaining'] == '104'
    assert managers[1].role == 'Vorsitzender der Geschäftsführung' and managers[1].signing == 'Einzelunterschrift'
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in managers[2:])
    merger = selected('53cab221')[0].payload
    assert merger['ownership_percent'] == '98' and merger['compensation_per_share'] == '0.01'
    assert merger['capital_increase'] is False and merger['share_allocation'] is False
    assert selected('55f64321')[0].payload['entry'] == '1485'
    assert all(e.signing == 'Einzelunterschrift' for e in selected('55f64321')[1:])
    assert selected('55f64321')[1].payload['shares'] == '200'
    restored = selected('56744f6b')[0]
    assert restored.event_type == 'company_name_changed' and restored.payload['liquidation'] is True
    assets = selected('71d1272c')[0]
    assert assets.event_type == 'ownership_changed' and assets.payload['consideration'] == '1.00'
    assert assets.payload['recipient_uid'] != assets.org_uid
    corrected = selected('76067542')[0]
    assert corrected.payload['name'] != corrected.payload['previous_name']
    assert corrected.signing is None and corrected.role == 'Mitglied des Verwaltungsrates'
    directors = selected('843c42c4')
    assert len({e.payload['place'] for e in directors}) == 2
    assert all(e.role == 'Direktor' and e.signing == 'Kollektivunterschrift zu zweien' for e in directors)
    board = selected('89f4f0de')
    assert [e.role for e in board] == ['Mitglied des Stiftungsrates', 'Präsident des Stiftungsrates']
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in board)
    alternative = selected('c979609b')[0]
    assert alternative.signing == 'Einzelunterschrift oder Kollektivunterschrift zu zweien'
    assert alternative.role == 'Direktor'


@pytest.mark.parametrize('prefix', ['1cf200d1', 'c9cb541c', 'e3c5c5cd', '94b72118-d3cb-46f4-8cf3-8d526586b9f2'])
def test_previous_fixtures_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    with patch.object(parser, 'extract_parser321_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert parse_publication_xml(fixture) == baseline
    # Existing payloads can still construct events without any new attributes.
    for old in baseline.events:
        assert Event(**vars(old)) == old


@pytest.mark.parametrize('prefix,rule,count', [case for case in CASES if case[0] not in {'2aba4a40', '3e374c31', '55f64321'}])
def test_optional_source_context_not_required_for_complete_clauses(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    assert extract_parser321_leftovers(*args) == extract_parser321_leftovers(*args, **kwargs)


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old
