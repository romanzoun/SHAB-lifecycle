import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser302 import extract_parser302_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('01e1d44a', 'de.text.authorized_conditional_capital_amended.v1', 1),
    ('14bd74ae', 'de.text.liquidation_address_corrected.v1', 1),
    ('16ff316f', 'de.text.business_assets_transferred_shares_claim.v1', 1),
    ('284bc68e', 'de.text.conditional_capital_repeated_amendment.v1', 1),
    ('61a83808', 'fr.text.merger_corporate_associate_transfer.v1', 1),
    ('84107e35', 'de.text.covid_moratorium_three_months.v1', 1),
    ('ac480cce', 'fr.persons.foundation_member_name_corrected.v1', 1),
    ('b9c1375f', 'de.text.bankruptcy_appeal_provisional_suspension.v1', 1),
    ('cc84f3e2', 'fr.text.proprietor_bankruptcy_annulled.v1', 1),
    ('dc1059db', 'fr.text.registered_shares_consolidated.v1', 1),
    ('e99ac573', 'fr.text.share_classes_capital_provisions_amended.v1', 1),
    ('fcba462c', 'fr.persons.administrators_mixed_signing.v1', 3),
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
        return extract_parser302_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser302_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 303
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
    assert extract_parser302_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser302_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])



@pytest.mark.parametrize('prefix', ['01e1d44a', '16ff316f', '284bc68e', '84107e35', 'ac480cce', 'b9c1375f', 'cc84f3e2'])
def test_invalid_dates_preserved(prefix):
    import re
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', args[0], count=1)
    assert changed != args[0]
    assert extract_parser302_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('old,new', [('19 mai', '32 mai'), ('30 mars', '32 mars'), ('24 avril', '31 avril'), ('17 mars', '32 mars')])
def test_invalid_written_dates_preserved(old, new):
    args, kwargs = invocation('e99ac573')
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser302_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('old,new', [('collective à deux', 'inconnue'), ('individuelle', 'inconnue'), ('ou Fankhauser Stéphane', 'ou Deagostini Olivier Laurent')])
def test_unsupported_signing_preserved(old, new):
    args, kwargs = invocation('fcba462c')
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser302_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    assert selected('01e1d44a')[0].payload['conditional_date'] == '20.04.2018'
    address = selected('14bd74ae')[0].payload
    assert '18' in address['address'] and '16' in address['previous_address']
    transfer = selected('16ff316f')[0].payload
    assert transfer['assets'] == "790'758.48" and transfer['liabilities'] == "334'638.85"
    assert transfer['share_count'] == '100' and transfer['claim'] == "356'119.63"
    assert selected('284bc68e')[0].payload['introduction_date'] == '07.05.2014'
    associate = selected('61a83808')[0].payload
    assert associate['count'] == '200' and associate['previous_uid'] != associate['uid']
    assert selected('84107e35')[0].payload['deadline_date'] == '20.08.2020'
    corrected = selected('ac480cce')[0]
    assert corrected.role == 'membre du conseil de fondation'
    assert corrected.payload['name'] != corrected.payload['previous_name']
    assert selected('b9c1375f')[0].payload['opening_time'] == '11.00'
    assert selected('cc84f3e2')[0].payload['opening_date'] == '13.01.2020'
    consolidation = selected('dc1059db')[0].payload
    assert consolidation['previous_count'] == "150'000'000" and consolidation['count'] == "1'500"
    classes = selected('e99ac573')[0].payload
    assert classes['capital'] == "4'267'000" and classes['c_count'] == "8'075'006"
    assert classes['authorization_written'] == '19 mai 2016'
    officers = selected('fcba462c')
    assert [e.signing for e in officers] == ['Kollektivunterschrift zu zweien', 'Einzelunterschrift', 'Kollektivunterschrift zu zweien']
    assert len({e.person_key for e in officers}) == 3
    assert officers[0].payload['previous_role'] == 'directeur'
    assert officers[2].payload['origin'] == officers[2].payload['place'] == 'Molondin'
