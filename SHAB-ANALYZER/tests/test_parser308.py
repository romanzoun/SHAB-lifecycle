import hashlib
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser308 import extract_parser308_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('2e69c652', 'fr.text.head_office_uid_replaced.v1', 1), ('31eecbab', 'de.text.head_office_bankruptcy_opened.v1', 1), ('4a33cb8d', 'fr.text.two_procurations_except_between_them.v1', 2), ('5fefcc9b', 'fr.text.bankruptcy_execution_suspended_name_restored.v1', 1), ('686b01fb', 'fr.text.two_liquidators_domiciles_changed.v1', 2), ('8728987f', 'de.text.dissolution_liquidator_transferability_deleted.v1', 2), ('9530550e', 'de.text.capital_fully_paid_after_failed_asset_transfer.v1', 1), ('9becffac', 'it.text.foundation_organization_entry_deleted.v1', 1), ('bd80c735', 'de.text.definitive_moratorium_extension_granted.v1', 1), ('ddfe94f3', 'fr.text.foundation_board_membership_denied_signing_corrected.v1', 1), ('e7d54890', 'it.text.association_dissolved_by_law_organization_deleted.v1', 1), ('f416c61d', 'de.text.authorized_capital_expired_clause_deleted.v1', 1)]


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
        return extract_parser308_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser308_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 311
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
    assert extract_parser308_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser308_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])




@pytest.mark.parametrize('prefix', ['31eecbab', '5fefcc9b', '8728987f', '9530550e', 'bd80c735', 'ddfe94f3', 'f416c61d'])
def test_invalid_dates_preserved(prefix):
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', args[0], count=1)
    kwargs['source_text'] = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', kwargs['source_text'], count=1)
    assert changed != args[0]
    assert extract_parser308_leftovers(changed, *args[1:], **kwargs) == ([], changed)

@pytest.mark.parametrize('prefix', ['686b01fb', '8728987f'])
def test_source_required(prefix):
    args, kwargs = invocation(prefix)
    kwargs['source_text'] = ''
    assert extract_parser308_leftovers(*args, **kwargs) == ([], args[0])

@pytest.mark.parametrize('prefix,old,new', [
    ('686b01fb', 'signature individuelle', 'signature collective à deux'),
    ('8728987f', 'Liquidator', 'Geschäftsführer'),
])
def test_source_mismatch(prefix, old, new):
    args, kwargs = invocation(prefix)
    assert old in kwargs['source_text']
    kwargs['source_text'] = kwargs['source_text'].replace(old, new)
    assert extract_parser308_leftovers(*args, **kwargs) == ([], args[0])

@pytest.mark.parametrize('prefix,old,new', [
    ('4a33cb8d', 'sauf entre eux', 'sans restriction'),
    ('9530550e', 'vollständig liberiert', 'teilweise liberiert'),
    ('bd80c735', 'definitiven', 'provisorischen'),
    ('ddfe94f3', "n'est en réalité pas membre", 'est membre'),
    ('9becffac', '95 cpv. 1 lett. h', '96 cpv. 1 lett. h'),
    ('e7d54890', '77 CC', '78 CC'),
    ('f416c61d', 'Zeitablauf', 'Widerruf'),
])
def test_unsupported_terms_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser308_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    assert selected('2e69c652')[0].payload['uid'] == 'CHE-105.999.625'
    assert selected('31eecbab')[0].payload['time'] == '15.22'
    procurations = selected('4a33cb8d')
    assert len({e.person_key for e in procurations}) == 2
    assert all(e.signing == 'Kollektivprokura zu zweien' and e.payload['signing_restriction'] == 'sauf entre eux' for e in procurations)
    assert selected('5fefcc9b')[0].payload['company_name'] == 'L.B.L. Espace FC Porto Sàrl'
    assert all(e.role == 'liquidateur' and e.signing == 'Einzelunterschrift' for e in selected('686b01fb'))
    dissolution = selected('8728987f')
    assert dissolution[0].payload['company_name'] == 'BERKON A.G.'
    assert dissolution[1].role == 'Verwaltungsratsmitglied, Liquidator'
    assert selected('9530550e')[0].payload['contract_date'] == '26.06.2019'
    assert selected('9becffac')[0].payload['article'] == '95 cpv. 1 lett. h ORC'
    assert selected('bd80c735')[0].payload['months'] == '6'
    signatory = selected('ddfe94f3')[0]
    assert signatory.role is None and signatory.signing == 'Kollektivunterschrift zu zweien'
    assert selected('e7d54890')[0].payload['dissolution_article'] == '77 CC'
    assert selected('f416c61d')[0].payload['authorization_date'] == '22.05.2015'

@pytest.mark.parametrize('invalid_time', ['24.00', '15.60'])
def test_invalid_time_preserved(invalid_time):
    args, kwargs = invocation('31eecbab')
    changed = args[0].replace('15.22', invalid_time)
    assert extract_parser308_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_repeated_authorization_date_must_agree():
    args, kwargs = invocation('f416c61d')
    changed = args[0].replace('22.05.2015', '23.05.2015', 1)
    assert extract_parser308_leftovers(changed, *args[1:], **kwargs) == ([], changed)
