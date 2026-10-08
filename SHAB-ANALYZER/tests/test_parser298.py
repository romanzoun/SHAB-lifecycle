import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser298 import extract_parser298_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('0625e0e7', 'fr.text.asset_transfer_shares_claim.v1', 1), ('151379ad', 'de.text.definitive_moratorium_extended_typo.v1', 1), ('15a2955f', 'fr.text.asset_transfer_shares_premium.v1', 1), ('1aa6e93f', 'fr.text.foundation_additional_address_completed.v1', 1), ('2009f823', 'fr.text.bankruptcy_appeal_rejected_effective.v1', 1), ('30c32145', 'fr.text.sole_proprietor_moratorium_extended.v1', 1), ('5d48a8da', 'de.text.supporting_documents_changed.v1', 1), ('8c99ab1a', 'de.text.moratorium_administrator_fr_xml.v1', 2), ('acd3989d', 'fr.text.branch_seat_transferred.v1', 1), ('af085b6a', 'fr.persons.collective_signing_partners_changed.v1', 2), ('da25bbb7', 'fr.persons.two_foreign_foundation_board_members.v1', 2), ('ff196f0f', 'fr.persons.branch_duplicate_registration_removed_typo.v1', 1)]


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
        return extract_parser298_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser298_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 310
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
    assert extract_parser298_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser298_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix', ['0625e0e7', '151379ad', '15a2955f', '1aa6e93f', '2009f823', '30c32145', '8c99ab1a'])
def test_invalid_dates_preserved(prefix):
    import re
    args, kwargs = invocation(prefix)
    changed = re.sub(r"\d{2}\.\d{2}\.\d{4}|\d{1,2} (?:janvier|avril|juillet) \d{4}", '31.02.2020', args[0], count=1)
    assert changed != args[0]
    assert extract_parser298_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_source_signing_required():
    args, kwargs = invocation('da25bbb7')
    assert extract_parser298_leftovers(*args, source_text='') == ([], args[0])
    changed = kwargs['source_text'].replace('signature collective à deux', 'signature individuelle')
    assert extract_parser298_leftovers(*args, source_text=changed) == ([], args[0])


def test_payloads():
    claim = selected('0625e0e7')[0].payload
    assert claim['count'] == '20' and claim['claim'] == "35'143.35"
    assert claim['recipient_uid'] == 'CHE-269.408.493'
    premium = selected('15a2955f')[0].payload
    assert premium['count'] == "1'002" and premium['premium'] == "2'218'745.60"
    assert selected('151379ad')[0].payload['months'] == '6'
    address = selected('1aa6e93f')[0].payload
    assert address['postal_code'] == '1213' and address['place'] == 'Petit-Lancy'
    bankruptcy = selected('2009f823')[0].payload
    assert bankruptcy['hour'] == '16' and bankruptcy['minute'] == '15'
    assert selected('30c32145')[0].payload['months'] == 3
    assert selected('5d48a8da')[0].payload['action'] == 'supporting_documents_changed'
    moratorium, administrator = selected('8c99ab1a')
    assert moratorium.payload['months'] == 6
    assert administrator.role == 'Sachwalterin' and administrator.payload['place'] == 'Bern'
    assert administrator.payload['administrator_uid'] == 'CHE-105.892.105'
    assert selected('acd3989d')[0].payload['place'] == 'Sierre'
    signers = selected('af085b6a')
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in signers)
    assert all(e.payload['signing_partners'] == ['Giroud Luc', 'Risse Louis'] for e in signers)
    members = selected('da25bbb7')
    assert [e.payload['country'] for e in members] == ['FRA', 'ITA']
    assert all(e.role == 'membre du conseil de fondation' and e.signing == 'Kollektivunterschrift zu zweien' for e in members)
    removed = selected('ff196f0f')[0]
    assert removed.event_type == 'officer_removed' and removed.payload['main_place'] == 'Moutier'
