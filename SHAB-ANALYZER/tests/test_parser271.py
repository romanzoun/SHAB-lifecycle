import hashlib
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser271 import extract_parser271_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('0fe62197', 'fr.text.definitive_moratorium_extended_long_dates.v1', 1),
    ('261b2aad', 'fr.persons.partial_share_transfer_new_unsigned_associate.v1', 2),
    ('3c18ec41', 'fr.persons.board_president_unsigned_secretary.v1', 2),
    ('47237c0f', 'fr.persons.delegate_general_director_continued_signing.v1', 2),
    ('8e7672e0', 'fr.text.auditor_uid_supplemented.v1', 1),
    ('93da3726', 'fr.persons.three_board_members_replaced_unsigned.v1', 6),
    ('96fb0343', 'fr.persons.board_president_changed_two_members.v1', 4),
    ('9d1e69bd', 'fr.persons.board_president_changed_two_members.v1', 4),
    ('aa9cd230', 'fr.persons.partial_share_transfer_existing_manager.v1', 2),
    ('c0a6eeda', 'fr.persons.corporate_liquidator_appointed.v1', 1),
    ('facf2dc1', 'fr.text.asset_takeover_clause_abrogated.v1', 1),
    ('ff5505fd', 'fr.persons.collective_signing_umlaut_typo.v1', 1),
]


def path(prefix):
    paths = list(FIXTURES.glob(prefix + '*.xml'))
    assert len(paths) == 1
    return paths[0]


def selected(prefix):
    rule = next(rule for stem, rule, _ in CASES if stem == prefix)
    return [e for e in parse_publication_xml(path(prefix)).events if e.rule_id == rule]


def invocation(prefix):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser271_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser271_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION >= 271
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
    assert extract_parser271_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['8e7672e0', 'facf2dc1', '0fe62197'])
def test_invalid_date_preserved(prefix):
    args, kwargs = invocation(prefix)
    def mutate(text):
        return re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', text).replace('18 février 2019', '31 février 2019')
    changed = mutate(args[0])
    assert changed != args[0]
    assert extract_parser271_leftovers(changed, *args[1:], source_text=mutate(kwargs['source_text'])) == ([], changed)


@pytest.mark.parametrize('prefix', ['96fb0343', '9d1e69bd'])
def test_source_signing_required(prefix):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(' avec signature collective à deux', '')
    assert extract_parser271_leftovers(changed, *args[1:]) == ([], changed)
    assert len(extract_parser271_leftovers(changed, *args[1:], **kwargs)[0]) == 4
    source = kwargs['source_text'].replace('avec signature collective à deux', 'sans signature')
    assert extract_parser271_leftovers(changed, *args[1:], source_text=source) == ([], changed)
    assert extract_parser271_leftovers(changed, *args[1:], source_text=kwargs['source_text'] + ' UNKNOWN_SUFFIX') == ([], changed)


@pytest.mark.parametrize('prefix,old,new', [
    ('261b2aad', '180 parts', '181 parts'),
    ('aa9cd230', '46 parts', '45 parts'),
    ('261b2aad', 'titulaire de 20 parts', 'titulaire de 21 parts'),
    ('3c18ec41', "n'exerce pas", 'exerce'),
    ('93da3726', "n'exercent pas", 'exercent'),
    ('47237c0f', 'continuent', 'cessent'),
    ('0fe62197', 'définitif', 'provisoire'),
    ('facf2dc1', 'est abrogée', 'est maintenue'),
])
def test_unsupported_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser271_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    moratorium = selected('0fe62197')[0].payload
    assert moratorium['decision_date'] == '18 février 2019'
    assert moratorium['until_date'] == '30 novembre 2020' and moratorium['definitive']
    giver, receiver = selected('261b2aad')
    assert giver.payload['shares'] == 180 and giver.payload['transferred_shares'] == 20
    assert receiver.payload['shares'] == 20 and receiver.payload['without_signature'] and receiver.signing is None
    giver, receiver = selected('aa9cd230')
    assert giver.payload['shares'] == 46 and receiver.payload['shares'] == 94
    assert receiver.role == 'associée-gérante présidente'
    president, secretary = selected('3c18ec41')
    assert president.signing == 'Einzelunterschrift'
    assert secretary.role == 'secrétaire' and secretary.payload['without_signature'] and secretary.signing is None
    delegate, director = selected('47237c0f')
    assert delegate.role == 'administrateur président, délégué' and director.role == 'directrice générale'
    assert all(e.payload['signing_continued'] for e in (delegate, director))
    auditor = selected('8e7672e0')[0]
    assert auditor.event_type == 'auditor_changed' and auditor.payload['uid'] == 'CHE-107.558.249'
    replacements = selected('93da3726')
    assert all(e.event_type == 'officer_removed' for e in replacements[:3])
    assert all(e.payload['without_signature'] and e.signing is None for e in replacements[3:])
    for prefix in ('96fb0343', '9d1e69bd'):
        events = selected(prefix)
        assert events[0].role == 'président' and events[1].payload['previous_role'] == 'président'
        assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in events)
        assert events[3].payload['origin'] == events[3].payload['place']
    liquidator = selected('c0a6eeda')[0]
    assert liquidator.role == 'liquidatrice' and liquidator.payload['uid'] == 'CHE-107.034.555'
    assert liquidator.signing is None
    assets = selected('facf2dc1')[0].payload
    assert assets['action'] == 'asset_takeover_clause_deleted' and assets['price'] == "9'722'250.00"
    assert assets['foundation_date'] == assets['contract_date'] == '11.04.2006'
    assert selected('ff5505fd')[0].signing == 'Kollektivunterschrift zu zweien'
