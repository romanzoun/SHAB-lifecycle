import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser300 import extract_parser300_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('012f950a', 'de.text.reinstatement_liquidator_domicile.v1', 2),
    ('022b72c4', 'fr.persons.associate_managers_transfer.v1', 3),
    ('10b8ae4d', 'fr.persons.two_powers_removed.v1', 2),
    ('17a23e25', 'fr.text.contribution_contract_date_corrected.v1', 1),
    ('25a88385', 'fr.text.definitive_moratorium_extended_six_months.v1', 1),
    ('414b17d0', 'de.persons.liquidator_previous_residence_corrected.v1', 1),
    ('50e72e55', 'de.text.capital_provisions_changed_deleted.v1', 1),
    ('73b5193b', 'de.text.business_division_transfer_no_consideration.v1', 1),
    ('9fb28ec7', 'fr.persons.associate_share_nominal_corrected.v1', 1),
    ('b6ab5f17', 'it.text.vehicle_contribution_claim.v1', 1),
    ('d9e3bc22', 'fr.text.two_corporate_associates_share_transfer.v1', 1),
    ('ff841740', 'fr.text.head_office_uid_changed.v1', 1),
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
        return extract_parser300_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser300_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 300
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
    assert extract_parser300_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser300_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])




@pytest.mark.parametrize('prefix', ['012f950a', '17a23e25', '50e72e55', '73b5193b', '9fb28ec7', 'b6ab5f17'])
def test_invalid_dates_preserved(prefix):
    import re
    args, kwargs = invocation(prefix)
    changed = re.sub(r"\d{2}\.\d{2}\.\d{4}", '31.02.2020', args[0], count=1)
    assert changed != args[0]
    assert extract_parser300_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_invalid_written_date_preserved():
    args, kwargs = invocation('25a88385')
    changed = args[0].replace('17 avril', '31 avril')
    assert extract_parser300_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['022b72c4', '414b17d0'])
def test_unknown_signing_preserved(prefix):
    args, kwargs = invocation(prefix)
    changed = args[0].replace('signature individuelle', 'signature inconnue').replace('Einzelunterschrift', 'Unbekannte Unterschrift')
    assert changed != args[0]
    assert extract_parser300_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_inconsistent_transfer_preserved():
    args, kwargs = invocation('d9e3bc22')
    changed = args[0].replace('avec 20 parts', 'avec 21 parts')
    assert extract_parser300_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    reinstatement, liquidator = selected('012f950a')
    assert reinstatement.payload['decision_date'] == '13.03.2020'
    assert liquidator.role == 'Liquidator' and liquidator.payload['place'] == 'Zürich'
    transfer = selected('022b72c4')
    assert [e.signing for e in transfer] == ['ohne Unterschrift', 'ohne Unterschrift', 'Einzelunterschrift']
    assert transfer[-1].payload['count'] == '20'
    assert all(e.payload['action'] == 'powers_removed' for e in selected('10b8ae4d'))
    contract = selected('17a23e25')[0].payload
    assert contract['contract_date'] == '16.10.2019' and contract['previous_date'] == '16.10.2016'
    moratorium = selected('25a88385')[0].payload
    assert moratorium['months'] == 6 and moratorium['deadline_date'] == '04.10.2020'
    assert selected('414b17d0')[0].payload['previous_place'] == 'Kloten'
    capital = selected('50e72e55')[0].payload
    assert capital['authorized_decision_date'] == capital['conditional_decision_date'] == '22.04.2020'
    assert capital['deleted2_introduction_date'] == '26.04.2010'
    assets = selected('73b5193b')[0].payload
    assert assets['assets'] == "39'494.45" and assets['liabilities'] == "16'431.04"
    assert assets['consideration'] == 'keine'
    shares = selected('9fb28ec7')[0].payload
    assert shares['nominal'] == '100' and shares['previous_nominal'] == '500'
    assert selected('b6ab5f17')[0].payload['claim'] == "4'000.00"
    corporate = selected('d9e3bc22')[0].payload
    assert corporate['previous_count'] == '10' and corporate['count'] == '20'
    assert selected('ff841740')[0].payload['head_office_uid'] == 'CHE-107.468.468'


def test_inconsistent_associate_transfer_preserved():
    args, kwargs = invocation('022b72c4')
    changed = args[0].replace('pour 20 parts', 'pour 21 parts')
    assert extract_parser300_leftovers(changed, *args[1:], **kwargs) == ([], changed)
