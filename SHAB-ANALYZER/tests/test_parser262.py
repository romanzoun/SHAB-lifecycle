from pathlib import Path
import hashlib
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser262 import extract_parser262_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('118eb84a', 'de.text.previous_auditor_reference_corrected.v1', 1),
    ('1dc4ce21', 'de.text.additional_business_address_deleted.v1', 1),
    ('1f8e677e', 'fr.persons.administrator_shared_origin_place.v1', 1),
    ('4697268b', 'fr.text.registered_entity_seat_uid_updated.v1', 1),
    ('60f2e5bf', 'fr.persons.two_residences_corrected.v1', 2),
    ('63daf783', 'fr.persons.two_administrators_individual_signing.v1', 2),
    ('71b34de3', 'de.text.four_branches_removed.v1', 4),
    ('7e201d2b', 'de.text.bankruptcy_judge_corrected.v1', 1),
    ('8970fa77', 'fr.persons.share_transfer_manager_president.v1', 2),
    ('990b372f', 'fr.persons.exact_given_name_corrected.v1', 1),
    ('bce7aa35', 'fr.text.branch_removed_notice_reference.v1', 1),
    ('f328aa89', 'de.text.branch_duplicate_purpose_deleted.v1', 1),
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
    captured = []
    def capture(*args, **kwargs):
        result = extract_parser262_leftovers(*args, **kwargs)
        if result[0]:
            captured.append((args, kwargs))
        return result
    with patch.object(parser, 'extract_parser262_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(captured) == 1
    return captured[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION >= 262
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    events = selected(prefix)
    assert len(events) == count
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in events)
    assert not any(e.rule_id == 'fr.persons.group_signing.v1' for e in result.events)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    changed = args[0] + '. UNRECOGNIZED_SUFFIX'
    assert extract_parser262_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['1f8e677e', '7e201d2b', '8970fa77'])
def test_source_required(prefix):
    args, kwargs = invocation(prefix)
    assert extract_parser262_leftovers(*args) == ([], args[0])
    kwargs['source_text'] += ' UNKNOWN'
    assert extract_parser262_leftovers(*args, **kwargs) == ([], args[0])


@pytest.mark.parametrize('old,new', [('cède 19', 'cède 0'), ('ses 20', 'ses 21'), ("19 parts de CHF 1'000", "19 parts de CHF 2'000")])
def test_inconsistent_share_transfer_preserved(old, new):
    args, kwargs = invocation('8970fa77')
    assert old in args[0]
    changed = args[0].replace(old, new)
    kwargs['source_text'] = kwargs['source_text'].replace(old, new)
    assert extract_parser262_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,signing', [('1f8e677e', 'signature collective à deux'), ('8970fa77', 'signature individuelle')])
def test_unknown_source_signing_preserved(prefix, signing):
    args, kwargs = invocation(prefix)
    kwargs['source_text'] = kwargs['source_text'].replace(signing, 'UNKNOWN_SIGNING')
    assert extract_parser262_leftovers(*args, **kwargs) == ([], args[0])


def test_payloads():
    auditor = selected('118eb84a')[0]
    assert auditor.payload['action'] == 'previous_reference_corrected'
    assert auditor.payload['register'] == 'CH-020.3.900.127-5'
    assert auditor.payload['entry_date'] == '2020-01-09'
    assert selected('1dc4ce21')[0].payload['postal_code'] == '8302'
    admin = selected('1f8e677e')[0]
    assert admin.role == 'administrateur' and admin.signing == 'Kollektivunterschrift zu zweien'
    assert admin.payload['origin'] == admin.payload['place'] == 'Glaris Sud'
    entity = selected('4697268b')[0]
    assert entity.payload['entity_uid'] == 'CHE-107.768.746'
    assert entity.payload['place'] == 'Granges-Paccot'
    residences = selected('60f2e5bf')
    assert [e.payload['place'] for e in residences] == ['Yvorne', 'Essertes']
    assert [e.payload['previous_place'] for e in residences] == ['Essertes', 'Yvorne']
    assert all(e.signing is None for e in residences)
    admins = selected('63daf783')
    assert [e.role for e in admins] == ['président', 'administrateur']
    assert all(e.signing == 'Einzelunterschrift' for e in admins)
    branches = selected('71b34de3')
    assert [e.payload['place'] for e in branches] == ['Pfyn', 'Kemmental', 'Münsterlingen', 'Ermatingen']
    assert branches[0].payload['register'] == 'CH-440.9.026.775-5'
    assert all(e.payload['action'] == 'removed' for e in branches)
    bankruptcy = selected('7e201d2b')[0]
    assert bankruptcy.payload['judge'] == 'Nachlassrichterin'
    assert bankruptcy.payload['previous_judge'] == 'Konkursrichterin'
    assert bankruptcy.payload['effective_date'] == '2020-01-15'
    assert bankruptcy.payload['time'] == '16.30' and bankruptcy.payload['dissolved'] is True
    seller, buyer = selected('8970fa77')
    assert seller.payload['shares_count'] == 1 and seller.payload['shares_transferred'] == 19
    assert buyer.payload['shares_count'] == 19 and buyer.role == 'associé-gérant président'
    assert seller.signing == buyer.signing == 'Einzelunterschrift'
    assert selected('990b372f')[0].payload['previous_given_name'] == 'David'
    assert selected('bce7aa35')[0].payload['notice_id'] == '1004810657'
    assert selected('f328aa89')[0].payload['scope'] == 'branch'


def test_invalid_bankruptcy_date_preserved():
    args, kwargs = invocation('7e201d2b')
    changed = args[0].replace('15.01.2020', '31.02.2020')
    kwargs['source_text'] = kwargs['source_text'].replace('15.01.2020', '31.02.2020')
    assert extract_parser262_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_bankruptcy_correction_requires_same_facts():
    args, kwargs = invocation('7e201d2b')
    kwargs['source_text'] = kwargs['source_text'].replace('[nicht: Mit Urteil vom 15.01.2020', '[nicht: Mit Urteil vom 16.01.2020')
    assert extract_parser262_leftovers(*args, **kwargs) == ([], args[0])


def test_invalid_auditor_reference_date_preserved():
    args, kwargs = invocation('118eb84a')
    changed = args[0].replace('09.01.2020', '31.02.2020')
    assert extract_parser262_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_transfer_requires_same_seller_in_second_clause():
    args, kwargs = invocation('8970fa77')
    old = 'Villiers Jacques reste titulaire'
    changed = args[0].replace(old, 'Tellenne David reste titulaire')
    kwargs['source_text'] = kwargs['source_text'].replace(old, 'Tellenne David reste titulaire')
    assert extract_parser262_leftovers(changed, *args[1:], **kwargs) == ([], changed)
