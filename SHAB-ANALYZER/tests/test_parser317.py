import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser317 import extract_parser317_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('0b8ac923', 'fr.text.administrator_appointed_typo.v1', 1),
    ('28e19c08', 'de.text.cooperative_merger_cash_compensation.v1', 1),
    ('349c1e19', 'de.text.definitive_moratorium_administrator.v1', 1),
    ('524e71cb', 'de.text.limited_partnership_capital_increased.v1', 1),
    ('976ce6e4', 'it.text.previous_contribution_in_kind.v1', 1),
    ('a5f28871', 'it.text.registered_person_corrected.v1', 1),
    ('a71c7745', 'de.text.branch_register_updated.v1', 1),
    ('bb5977fe', 'fr.text.three_directors_signing_pair_excluded.v1', 3),
    ('c5e25f0b', 'fr.text.corporate_liquidator_appointed.v1', 2),
    ('d22b719a', 'de.text.authorized_conditional_capital_provisions_changed.v1', 1),
    ('edeba6d1', 'fr.text.two_liquidators_share_restrictions_removed.v1', 3),
    ('fea3f9ca', 'fr.text.share_class_nominal_corrected_typo.v1', 1),
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
        return extract_parser317_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser317_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    result, _ = captured(prefix)
    rule = next(rule for stem, rule, _ in CASES if stem == prefix)
    return [e for e in result.events if e.rule_id == rule]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 319
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    events = selected(prefix)
    assert len(events) == count
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in events)
    if any(e.signing for e in events):
        assert not any(e.rule_id == 'fr.persons.group_signing.v1' for e in result.events)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser317_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser317_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]



@pytest.mark.parametrize('prefix', ['28e19c08', '349c1e19', '976ce6e4', 'd22b719a', 'fea3f9ca'])
def test_invalid_dates_preserved(prefix):
    _, (args, kwargs) = captured(prefix)
    dates = set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0]))
    assert dates
    for date in dates:
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser317_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed


@pytest.mark.parametrize('prefix,old,new', [
    ('28e19c08', '700.00', '701.00'),
    ('349c1e19', 'vier Monaten', 'fünf Monaten'),
    ('524e71cb', "450'980.00", "19'000.00"),
    ('976ce6e4', '60 azioni', '61 azioni'),
    ('a5f28871', 'firma individuale', 'firma collettiva a due'),
    ('bb5977fe', 'ne signent pas entre eux', 'signent entre eux'),
    ('fea3f9ca', "CHF 100'000,", "CHF 100'001,"),
])
def test_unsupported_terms_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    events, leftover = extract_parser317_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix', ['0b8ac923', 'a71c7745', 'edeba6d1'])
def test_source_evidence_required(prefix):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser317_leftovers(*args, source_text='')
    assert not events and leftover == args[0]


def test_payloads_and_roles():
    assert selected('0b8ac923')[0].signing == 'Einzelunterschrift'
    assert selected('28e19c08')[0].event_type == 'company_merged'
    assert selected('349c1e19')[0].payload['duration_months'] == 4
    assert selected('524e71cb')[0].event_type == 'capital_changed'
    assert selected('976ce6e4')[0].payload['historical'] is True
    assert selected('a5f28871')[0].role == 'Mitglied des Verwaltungsrates'
    branch = selected('a71c7745')[0].payload
    assert branch['branch_uid'] != branch['previous_uid']
    assert branch['removed_uid'] != branch['branch_uid']
    directors = selected('bb5977fe')
    assert all(e.role == 'Direktor' and e.signing == 'Kollektivunterschrift zu zweien' for e in directors)
    assert len(directors[0].payload['excluded_signing_pair']) == 2
    assert selected('c5e25f0b')[1].role == 'Liquidatorin'
    assert selected('d22b719a')[0].event_type == 'capital_changed'
    liquidation = selected('edeba6d1')
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in liquidation[:2])
    assert liquidation[2].payload['transfer_restricted'] is False
    assert selected('fea3f9ca')[0].payload['fully_paid'] is True

@pytest.mark.parametrize('prefix', ['0b8ac923', 'edeba6d1'])
def test_source_signing_mismatch_preserved(prefix):
    _, (args, kwargs) = captured(prefix)
    source = kwargs['source_text'].replace('signature individuelle', 'signature collective à deux') if prefix == '0b8ac923' else kwargs['source_text'].replace('signature collective à deux', 'signature individuelle')
    assert source != kwargs['source_text']
    events, leftover = extract_parser317_leftovers(*args, source_text=source)
    assert not events and leftover == args[0]
