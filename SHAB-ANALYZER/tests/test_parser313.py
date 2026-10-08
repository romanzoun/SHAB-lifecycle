import hashlib
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser313 import extract_parser313_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('2ce0c448', 'fr.text.council_president_vice_president_swap.v1', 2),
    ('2faf5dab', 'fr.text.two_committee_members_distinct_places.v1', 2),
    ('34642774', 'de.text.covid19_deferral_granted.v1', 1),
    ('461aa959', 'fr.text.associate_managers_presidency_changed.v1', 2),
    ('4f6155b8', 'fr.text.two_administrators_foreign_place.v1', 2),
    ('6be6373c', 'fr.text.two_manager_liquidators_signing_typo.v1', 2),
    ('9e355e93', 'fr.text.associate_holdings_corrected_manager_added.v1', 2),
    ('c7795b29', 'de.text.authorized_conditional_capital_resolutions_replaced.v1', 1),
    ('cfab680a', 'de.text.expired_authorized_capital_replaced.v1', 1),
    ('d2e6241d', 'de.text.undisclosed_intent_unregistered_business_acquired.v1', 1),
    ('db967c02', 'fr.text.three_associates_managers_signing_typo.v1', 3),
    ('f4ead531', 'it.text.two_mergers_subordination_own_shares.v1', 2),
]


def path(prefix):
    paths = list(FIXTURES.glob(prefix + '*.xml'))
    assert len(paths) == 1
    return paths[0]


def invocation(prefix):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser313_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser313_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 319
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    events = [e for e in result.events if e.rule_id == rule]
    assert len(events) == count
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in events)
    if any(e.signing for e in events):
        assert not any(e.rule_id == 'fr.persons.group_signing.v1' for e in result.events)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser313_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser313_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix', ['34642774', '9e355e93', 'c7795b29', 'cfab680a', 'd2e6241d', 'f4ead531'])
def test_invalid_dates_preserved(prefix):
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', args[0])
    assert changed != args[0]
    assert extract_parser313_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,old,new', [
    ('2ce0c448', 'vice-président', 'secrétaire'),
    ('2faf5dab', 'collective à deux', 'individuelle'),
    ('34642774', 'bewilligt', 'abgewiesen'),
    ('461aa959', 'présidente', 'secrétaire'),
    ('4f6155b8', 'individuelle', 'collective à deux'),
    ('6be6373c', 'Liquidateurs', 'Administrateurs'),
    ('9e355e93', 'détient', 'cède'),
    ('c7795b29', 'angepasst', 'aufgehoben'),
    ('cfab680a', 'Fristablauf', 'Widerruf'),
    ('d2e6241d', 'übernommen', 'veräussert'),
    ('db967c02', 'gérants', 'liquidateurs'),
    ('f4ead531', 'senza aumento', 'con aumento'),
])
def test_unsupported_terms_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser313_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_business_source_context_required():
    args, kwargs = invocation('d2e6241d')
    for source in ('', kwargs['source_text'].replace('nicht im Handelsregister', 'im Handelsregister')):
        assert extract_parser313_leftovers(*args, source_text=source) == ([], args[0])


def test_payloads_and_roles():
    def selected(prefix):
        rule = next(rule for stem, rule, _ in CASES if stem == prefix)
        return [e for e in parse_publication_xml(path(prefix)).events if e.rule_id == rule]
    council = selected('2ce0c448')
    assert council[1].role == 'Mitglied des Stiftungsrates, Vizepräsident'
    assert council[0].role == 'Mitglied des Stiftungsrates, Präsident'
    assert all(e.signing == 'Einzelunterschrift' for e in council)
    committee = selected('2faf5dab')
    assert len({e.person_key for e in committee}) == 2
    assert len({e.payload['place'] for e in committee}) == 2
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in committee)
    assert all('Liquidator' in e.role and e.signing == 'Einzelunterschrift' for e in selected('6be6373c'))
    correction = selected('9e355e93')
    assert len({e.person_key for e in correction}) == 2
    assert correction[0].payload['count1'] != correction[0].payload['previous_count']
    assert all(e.signing is None for e in correction)
    business = selected('d2e6241d')[0].payload
    assert business['registered'] is False and business['intent_disclosed_at_formation'] is False
    assert len({e.person_key for e in selected('db967c02')}) == 3
    mergers = selected('f4ead531')
    assert len({e.payload['absorbed_uid'] for e in mergers}) == 2
    assert all(e.event_type == 'company_merged' and e.payload['capital_increase'] is False and e.payload['claims_subordinated'] is True for e in mergers)


def test_foundation_source_context_required():
    args, kwargs = invocation('2ce0c448')
    for source in ('', kwargs['source_text'].replace('Fondation ', 'Société ', 1)):
        assert extract_parser313_leftovers(*args, source_text=source) == ([], args[0])
