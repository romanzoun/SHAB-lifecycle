import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser398 import extract_parser398_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = ['095f22f3056945a747f711a9f5fc9d0a927fb11e7336f954fbb681b6c410c326', '21ebc82baf4b8865717c30be08c23429b3ae50a53790f54b6d6b4f146d367350', '2e5457050fddeb5e49941c9cd0e5628bfe12b7495f1db60b53936871afd1bfd4', '4c785ec7c65fb6c5fe8bdd71bccaae1a62f264a2dd6492353a147ce58ef358de', '51337db2809017a0dc4cec22a5dd06aca6465b22499a54b4d1eff70dd47da8fa', '6876f60ee96bb27a488d19ab395c43183e0e1367179ec0fb1e7dd765fbc48c32', '6ba3e924bf8ba34a3bd8588012e6184df538d3cbff6b0dfdf109f62eaced569a', '90765c04730c829e7242802dfbfe7b682c8a2f1aa8d7e894738ed96f26a7c5bc', '96c3b4308b3e56e911f7c88d08a56643df7e61b0e23c00ae8d5f2c5a76e75caf', 'a64b0478030cd089b2b8bb9377ceee4da5651e22d502245d29935ca71881d227', 'c6d27d6b2e90040210b361ddbcaddb68577cec87f3f4e9f3595ec864ba0cb2d4', 'efb6ff5df85ba7ef7ab941c85fa249c75bc6320ae34480222cdbaa41cb002431']
CONTEXT_REQUIRED = {'095f22f3', '51337db2', '6876f60e', '96c3b430'}
COUNTS = {'90765c04': 3}


@lru_cache(None)
def captured(digest):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser398_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser398_leftovers', capture):
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
    added, rest = extract_parser398_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 416
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS.get(digest[:8], 1) and not rest
    with patch.object(parser, 'extract_parser398_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_unknown_suffix_and_language_preserve_input(digest):
    _, (args, kwargs) = captured(digest)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser398_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser398_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_missing_optional_source_and_invalid_dates(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser398_leftovers(*args)
    if digest[:8] in CONTEXT_REQUIRED:
        assert not events and rest == args[0]
    else:
        assert len(events) == COUNTS.get(digest[:8], 1) and not rest
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser398_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_old_event_without_new_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event


EXPECTED = {
    '095f22f3': ('organization_changed', 'shareholder_communications_post_and_email_residual', {'methods': ['brieflich', 'E-Mail'], 'recipients': 'Aktionäre bzw. Nutzniesser'}),
    '21ebc82b': ('status_changed', 'bankruptcy_suspended_single_court_decision', {'decision_date': '29.12.2020', 'court': 'zuständigen Einzelgerichts'}),
    '2e545705': ('officer_changed', 'individual_signing_corrected_notice_page', {'entry': '621', 'entry_date': '11.01.2021', 'notice_date': '14.01.2021', 'notice_ref': '0/1005074116', 'previous_signing': 'Kollektivunterschrift zu zweien'}),
    '4c785ec7': ('seat_changed', 'branch_seat_municipality_changed', {'previous_place': 'Bagnes', 'place': 'Val de Bagnes', 'branch_uid': 'CHE-338.949.983'}),
    '51337db2': ('ownership_changed', 'two_managers_partial_transfer_new_joint_manager', {'transferred': '10', 'previous': '100', 'received': '20', 'remaining': '90', 'nominal': '100', 'place': 'Ecublens (VD)'}),
    '6876f60e': ('statutes_changed', 'statutes_non_public_plural_typo_residual', {'statutes_date': '24.10.2020'}),
    '6ba3e924': ('capital_changed', 'share_split_published_comma_nominal', {'previous_count': "9'090", 'count': "90'900", 'nominal': '1.10', 'capital_nominal_raw': '1, 10', 'capital_count': "99'990", 'capital': "109'989"}),
    '90765c04': ('officer_removed', 'chair_manager_removed_title_corrected_appointed', {'removed_name': 'Hohorst Sven Michael'}),
    '96c3b430': ('capital_changed', 'registered_share_split_retained_transfer_restrictions', {'previous_count': '50', 'count': '500', 'previous_nominal': "1'000", 'nominal': '100'}),
    'a64b0478': ('officer_changed', 'branch_deputy_director_contine_typo', {'signing_scope': 'affaires de la succursale'}),
    'c6d27d6b': ('officer_changed', 'italian_associate_manager_name_corrected', {'name': 'Ballerio, Francesco', 'count': '20', 'nominal': "1'000.00", 'place': 'Castagnola (Lugano)'}),
    'efb6ff5d': ('status_changed', 'provisional_moratorium_extended_until_am', {'decision_date': '23.12.2020', 'until_date': '20.01.2021', 'court': 'Einzelgericht des Bezirksgerichts Horgen'}),
}


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_explicit_event_meaning(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser398_leftovers(*args, **kwargs)
    kind, action, values = EXPECTED[digest[:8]]
    assert not rest and events[0].event_type == kind
    assert events[0].rule_id == f'{args[1]}.text.{action}.v1'
    assert events[0].payload['action'] == action
    assert {key: events[0].payload[key] for key in values} == values
    if digest.startswith(('2e545705', 'c6d27d6b')):
        assert events[0].person_key and events[0].signing == 'Einzelunterschrift'
    if digest.startswith('a64b0478'):
        assert events[0].role == 'sous-directeur de la succursale'
        assert events[0].signing == 'Kollektivunterschrift zu zweien'
    if digest.startswith('90765c04'):
        assert [e.event_type for e in events] == ['officer_removed', 'officer_changed', 'officer_changed']
        assert events[1].payload['previous_name'] == 'Stoll Karsten Rüdiger'
        assert events[1].payload['name'] == 'Dr. Stoll Karsten Rüdiger'
        assert events[1].signing is None and events[1].role is None
        assert events[0].payload['place'] is None
        assert events[1].payload['place'] is None
        assert events[2].payload['place'] == 'Mögglingen'
        assert events[2].payload['name'] == 'Dr. Lang Heiner Robert Friedrich'
        assert events[2].role == 'vorsitzender Geschäftsführer'
        assert events[2].signing == 'Kollektivunterschrift zu zweien'


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_missing_optional_organization_metadata(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser398_leftovers(*args[:4], None, None, None, **kwargs)
    assert not rest and len(events) == COUNTS.get(digest[:8], 1)
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)


@pytest.mark.parametrize('prefix', sorted(CONTEXT_REQUIRED))
def test_context_must_agree_and_be_present(prefix):
    digest = next(d for d in SUPPLIED_SHA256 if d.startswith(prefix))
    _, (args, kwargs) = captured(digest)
    assert extract_parser398_leftovers(*args, source_text='Unrelated.') == ([], args[0])
    # A matching source must not authorize a different residual payload.
    if prefix != '6876f60e':
        token = {'095f22f3': 'Nutzniessers', '51337db2': '10', '96c3b430': '500'}[prefix]
        replacement = {'095f22f3': 'UNKNOWN', '51337db2': '11', '96c3b430': '501'}[prefix]
        changed = args[0].replace(token, replacement)
        assert changed != args[0]
        assert extract_parser398_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('version,text,language', [
    (119, 'Division des 1000 actions de CHF 100 en 100000 actions de CHF 1. Capital-actions: CHF 100000, entièrement libéré, divisé en 100000 actions de CHF 1, nominatives', 'fr'),
    (149, "Les 100 actions nominatives de CHF 1000, formant l'entier du capital-actions, sont transformées en 1000 actions nominatives de CHF 100", 'fr'),
    (379, 'Mit Entscheid vom 01.01.2021 hat der Einzelrichter am Kantonsgericht die provisorische Nachlassstundung bis 01.03.2021 verlängert', 'de'),
    (386, 'Das Konkursverfahren ist mit Verfügung des Einzelrichters des Bezirksgerichts Beispiel vom 01.01.2021 mangels Aktiven eingestellt worden', 'de'),
    (319, "L'inscription No 123 du 01.01.2021 est rectifiée en ce sens que l'administrateur unique Exemple Anne signe individuellement (et non pas collectivement à deux)", 'fr'),
])
def test_legacy_rules_retain_ownership_in_isolation(version, text, language):
    import importlib
    module = importlib.import_module(f'shab_analyzer.parser{version}')
    old = getattr(module, f'extract_parser{version}_leftovers')
    args = text, language, 'p', '', None, None, None
    events, rest = old(*args)
    assert events and not rest
    assert extract_parser398_leftovers(*args) == ([], text)


@pytest.mark.parametrize('stem', [
    '37a3ffc9-0f3b-47b3-bacd-1b40d851d8c0',
    '1855c3abe279580b8806de34447fdc1f75832e8ebc2773afe15f19d7b9459311',
    '2bfe63c21628baa119c054da99ab2f48e32db8af946cc9b50f59376bc86bf64b',
])
def test_existing_fixture_results_unchanged(stem):
    import shab_analyzer.parse as parser
    path = FIXTURES / (stem + '.xml')
    result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser398_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(path)


@pytest.mark.parametrize('prefix', sorted(CONTEXT_REQUIRED))
def test_source_contradictions_are_rejected(prefix):
    digest = next(d for d in SUPPLIED_SHA256 if d.startswith(prefix))
    _, (args, kwargs) = captured(digest)
    old, new = {
        '095f22f3': ('brieflich', 'UNKNOWN'),
        '51337db2': ('signature collective à deux', 'signature individuelle'),
        '6876f60e': ('24.10.2020', '31.02.2020'),
        '96c3b430': ('500 actions', '501 actions'),
    }[prefix]
    source = kwargs['source_text'].replace(old, new)
    assert source != kwargs['source_text']
    assert extract_parser398_leftovers(*args, source_text=source) == ([], args[0])
