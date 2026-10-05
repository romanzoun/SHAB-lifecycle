from pathlib import Path
import hashlib

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser261 import extract_parser261_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('1cd46abe', 'de.text.statutes_date_corrected.v1', 1),
    ('2fda69b1', 'fr.persons.four_foundation_members.v1', 4),
    ('30a7c546', 'de.text.business_unit_asset_transfer.v1', 1),
    ('3c5164b6', 'de.text.bankruptcy_closed_business_continued.v1', 1),
    ('66ff9224', 'it.text.other_office_deleted.v1', 1),
    ('777ebb70', 'fr.persons.share_transfer_existing_associates.v1', 2),
    ('7ee214b8', 'fr.persons.three_administrators_president.v1', 3),
    ('80ab4095', 'de.persons.director_replaced.v1', 2),
    ('9a258426', 'it.persons.president_name_corrected.v1', 1),
    ('d8b4ec31', 'fr.persons.administrator_president_liquidator.v1', 1),
    ('dd991906', 'fr.persons.corporate_associate_renamed_two_managers.v1', 3),
    ('e66356e3', 'de.text.branches_deleted_added_corrected.v1', 3),
]


def path(prefix):
    paths = list(FIXTURES.glob(prefix + '*.xml'))
    assert len(paths) == 1
    return paths[0]


def selected(prefix):
    rule = next(rule for stem, rule, _ in CASES if stem == prefix)
    return [e for e in parse_publication_xml(path(prefix)).events if e.rule_id == rule]


def invocation(prefix):
    # Capture the successful pipeline call, including legacy preprocessing.
    from unittest.mock import patch
    import shab_analyzer.parse as parser
    captured = []

    def capture(*args, **kwargs):
        result = extract_parser261_leftovers(*args, **kwargs)
        if result[0]:
            captured.append((args, kwargs))
        return result

    with patch.object(parser, 'extract_parser261_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(captured) == 1
    return captured[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 261
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    events = selected(prefix)
    assert len(events) == count
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in events)
    assert not any(e.rule_id == 'fr.persons.group_signing.v1' for e in result.events)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    changed = args[0] + '. UNRECOGNIZED_SUFFIX'
    assert extract_parser261_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['2fda69b1', '7ee214b8', '9a258426', 'd8b4ec31', 'dd991906', 'e66356e3'])
def test_stripped_facts_require_matching_source(prefix):
    args, kwargs = invocation(prefix)
    assert extract_parser261_leftovers(*args) == ([], args[0])
    kwargs['source_text'] += ' UNKNOWN'
    assert extract_parser261_leftovers(*args, **kwargs) == ([], args[0])


@pytest.mark.parametrize('old,new', [('cession de 3', 'cession de 0'), ('cession de 3', 'cession de 5'), ('71 parts de CHF 200', '71 parts de CHF 201')])
def test_inconsistent_share_transfer_preserved(old, new):
    args, kwargs = invocation('777ebb70')
    assert old in args[0]
    changed = args[0].replace(old, new)
    assert extract_parser261_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['2fda69b1', '7ee214b8', 'd8b4ec31', 'dd991906'])
def test_unknown_source_signing_preserved(prefix):
    args, kwargs = invocation(prefix)
    source = kwargs['source_text']
    signing = 'signature collective à deux' if prefix == '2fda69b1' else 'signature individuelle'
    assert signing in source
    kwargs['source_text'] = source.replace(signing, 'UNKNOWN_SIGNING')
    assert extract_parser261_leftovers(*args, **kwargs) == ([], args[0])


def test_payloads():
    assert selected('1cd46abe')[0].payload['date'] == '2019-06-14'
    assert selected('1cd46abe')[0].payload['previous_date'] == '2019-05-14'
    members = selected('2fda69b1')
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in members)
    assert members[-1].payload['place'] == "L'Isle"
    transfer = selected('30a7c546')[0]
    assert transfer.payload['unit'] == 'Schwimmbadtechnik'
    assert transfer.payload['assets'] == transfer.payload['consideration'] == "250'000.00"
    assert transfer.payload['liabilities'] == '0.00'
    assert transfer.payload['date'] == '2019-12-24'
    assert selected('3c5164b6')[0].payload['business_continues'] is True
    assert selected('66ff9224')[0].payload['action'] == 'removed'
    seller, buyer = selected('777ebb70')
    assert seller.payload['shares_count'] == 71 and seller.payload['shares_transferred'] == 3
    assert buyer.payload['shares_count'] == 4 and buyer.payload['shares_received'] == 3
    assert seller.signing is buyer.signing is None
    admins = selected('7ee214b8')
    assert admins[0].role == 'présidente' and all(e.signing == 'Einzelunterschrift' for e in admins)
    removed, appointed = selected('80ab4095')
    assert removed.payload['action'] == 'removed' and appointed.payload['action'] == 'appointed'
    assert appointed.payload['place'] == 'Risseck'
    corrected = selected('9a258426')[0]
    assert corrected.payload['previous_name'] == 'Mondani-Moranzoni-Moranzoni, Daniela'
    liquidator = selected('d8b4ec31')[0]
    assert liquidator.payload['name'] == 'Banck Helio Steven Geert'
    assert liquidator.role == 'liquidateur' and liquidator.signing == 'Einzelunterschrift'
    company, *managers = selected('dd991906')
    assert company.payload['previous_name'] == 'LASER TEAM ENTREPRISE'
    assert company.payload['place'] == 'Margencel' and company.signing is None
    assert all(e.role == 'gérante' and e.signing == 'Einzelunterschrift' for e in managers)
    branches = selected('e66356e3')
    assert [e.payload['action'] for e in branches] == ['removed', 'added', 'place_corrected']
    assert branches[-1].payload['place'] == 'Ecublens (VD)'
    assert not any(e.rule_id == 'de.text.branch_added.v1' for e in parse_publication_xml(path('e66356e3')).events)


def test_invalid_corrected_date_preserved():
    args, kwargs = invocation('1cd46abe')
    changed = args[0].replace('14.6.2019', '31.2.2019')
    assert extract_parser261_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_branch_correction_requires_same_uid():
    args, kwargs = invocation('e66356e3')
    old = '[gestrichen: Ecublens (CHE-213.891.433)]'
    new = '[gestrichen: Ecublens (CHE-213.891.434)]'
    assert old in args[0]
    changed = args[0].replace(old, new)
    kwargs['source_text'] = kwargs['source_text'].replace(old, new)
    assert extract_parser261_leftovers(changed, *args[1:], **kwargs) == ([], changed)
