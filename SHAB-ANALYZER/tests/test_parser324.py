import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser324 import extract_parser324_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('071d1e57', 'fr.text.administration_delegates_collective_signing.v1', 5),
    ('0f24b50f', 'de.text.definitive_moratorium_extension_replaced.v1', 1),
    ('21eda001', 'de.text.historical_contribution_clauses_removed.v1', 1),
    ('238c92b1', 'fr.text.administration_president_and_member_individual_signing.v1', 2),
    ('37d2f837', 'fr.text.share_transfer_manager_and_unsigned_associate.v1', 2),
    ('42e77773', 'de.text.cooperative_court_dissolution.v1', 1),
    ('4853703f', 'fr.text.manager_share_transfer_president_appointed.v1', 3),
    ('6899b65f', 'de.text.court_administrator_order_replaced.v1', 1),
    ('6aceb735', 'fr.text.general_secretary_management_collective_signing.v1', 1),
    ('a6efd04c', 'fr.text.administration_roles_and_signing_retained.v1', 4),
    ('bc92c8c0', 'fr.text.ordinary_participation_capital_increase.v1', 1),
    ('f43edc77', 'fr.text.committee_members_without_signing.v1', 2),
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
        return extract_parser324_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser324_leftovers', capture):
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
    assert PARSER_VERSION == 420
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    with patch.object(parser, 'extract_parser324_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert [e for e in result.events if e.rule_id != rule] == baseline.events
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser324_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser324_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]


@pytest.mark.parametrize('prefix', ['1cf200d1', 'c9cb541c', 'e3c5c5cd', '94b72118-d3cb-46f4-8cf3-8d526586b9f2'])
def test_previous_fixtures_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    with patch.object(parser, 'extract_parser324_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert parse_publication_xml(fixture) == baseline
    # Existing payloads can still construct events without any new attributes.
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_invalid_dates_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    dates = set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0]))
    for date in dates:
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser324_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed



@pytest.mark.parametrize('prefix', ['3d76a503', '4f3a409a', '58990a3b', '73692624',
    '89c913dc', '8feb80c9', 'a0ccab8a', 'c0c6347c', 'c3c690fd', 'c8c10bfe',
    'cf486186', 'e648f846'])
def test_parser323_results_unchanged(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser324_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline


@pytest.mark.parametrize('prefix', ['071d1e57', '21eda001', '4853703f', 'a6efd04c'])
def test_fragments_require_source_and_signing_evidence(prefix):
    _, (args, kwargs) = captured(prefix)
    for source in ['', 'unsupported', kwargs['source_text'].replace('avec signature', 'sans signature').replace('[gestrichen:', '[unverändert:')]:
        events, leftover = extract_parser324_leftovers(*args, source_text=source)
        assert not events and leftover == args[0]


@pytest.mark.parametrize('prefix,old,new', [
    ('4853703f', 'titulaire de 12 parts', 'titulaire de 13 parts'),
    ('37d2f837', 'pour 100 parts', 'pour 101 parts'),
    ('bc92c8c0', "à savoir de CHF 3'000", "à savoir de CHF 3'001"),
    ('bc92c8c0', 'en 50 bons', 'en 51 bons'),
    ('f43edc77', 'sans signature', 'avec signature'),
    ('42e77773', '913 OR', '914 OR'),
])
def test_inconsistent_or_unsupported_terms_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    events, leftover = extract_parser324_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


def test_payload_semantics_and_missing_optional_attributes():
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in selected('071d1e57'))
    assert selected('0f24b50f')[0].payload['months'] == '2'
    historical = selected('21eda001')[0]
    assert historical.event_type == 'organization_changed'
    assert historical.payload['previous_clause_removed'] is True
    assert historical.payload['removed_clause_count'] == 7
    assert all(e.signing == 'Einzelunterschrift' for e in selected('238c92b1'))
    transfer = selected('37d2f837')
    assert transfer[0].event_type == 'ownership_changed'
    assert transfer[1].signing == 'ohne Zeichnungsberechtigung'
    assert selected('42e77773')[0].payload['liquidation_ordered'] is True
    transfer = selected('4853703f')
    assert transfer[1].signing is None and transfer[1].payload.get('place') is None
    assert transfer[2].signing == 'Einzelunterschrift'
    assert selected('6899b65f')[0].role == 'Sachwalterin'
    assert selected('6899b65f')[0].signing == 'Einzelunterschrift'
    assert selected('6aceb735')[0].payload['country'] == 'FRA'
    administration = selected('a6efd04c')
    assert administration[2].signing == 'Einzelunterschrift'
    assert administration[3].signing == 'Kollektivunterschrift zu zweien'
    capital = selected('bc92c8c0')[0]
    assert capital.event_type == 'capital_changed' and capital.payload['fully_paid'] is True
    assert all(e.signing == 'ohne Zeichnungsberechtigung' for e in selected('f43edc77'))
    for prefix, _, _ in CASES:
        for e in selected(prefix):
            assert Event(**vars(e)) == e
