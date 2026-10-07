import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser280 import extract_parser280_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('025536a0', 'fr.persons.president_name_corrected_notice.v1', 1), ('1e3ba70d', 'fr.persons.president_supplement_notice.v1', 1), ('4686c91a', 'fr.persons.commandite_reduced.v1', 1), ('51266548', 'de.text.authorized_capital_clause_removed.v1', 1), ('54a71c3b', 'fr.persons.transfer_manager_president.v1', 2), ('904db5fc', 'fr.persons.new_commanditaire_collective.v1', 1), ('92a6871b', 'fr.text.asset_transfer_third_party_liabilities.v1', 1), ('964c4c93', 'fr.persons.two_transfers_three_managers.v1', 3), ('b3715b85', 'fr.persons.board_name_corrected_unmatched_parenthesis.v1', 1), ('d41a5966', 'fr.persons.given_name_residence_changed.v1', 1), ('d5c020d3', 'fr.persons.manager_associate_supplement.v1', 1), ('ea1f5fb5', 'de.text.branch_headquarters_bankruptcy_request_rejected.v1', 1)]


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
        return extract_parser280_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser280_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 308
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
    assert extract_parser280_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser280_leftovers(args[0], 'de' if args[1] == 'it' else 'it', *args[2:], **kwargs) == ([], args[0])



@pytest.mark.parametrize('prefix,old,new', [
 ('025536a0', '15.10.2019', '31.02.2019'),
 ('1e3ba70d', '31.01.2020', '31.02.2020'),
 ('51266548', '25.04.2014', '31.04.2014'),
 ('92a6871b', '05.03.2020', '31.02.2020'),
 ('b3715b85', '12.02.2020', '31.02.2020'),
 ('d5c020d3', '10.03.2020', '31.02.2020'),
 ('ea1f5fb5', '14.01.2020', '31.02.2020'),
 ('4686c91a', "2'000'000", "8'000'000"),
 ('54a71c3b', 'titulaire de 10 parts', 'titulaire de 11 parts'),
 ('904db5fc', "30'000", '0'),
 ('964c4c93', 'avec 70 parts', 'avec 71 parts'),
 ('d5c020d3', '100 parts', '0 parts'),
])
def test_invalid_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new, 1)
    assert changed != args[0]
    assert extract_parser280_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    assert selected('025536a0')[0].payload['name'] == 'Kalinina Nadezda'
    assert selected('025536a0')[0].payload['correction']
    assert selected('1e3ba70d')[0].role == 'administratrice présidente'
    assert selected('1e3ba70d')[0].payload['supplement']
    assert selected('4686c91a')[0].payload['associate_uid'] == 'CHE-239.753.548'
    assert selected('4686c91a')[0].payload['amount'] == "2'000'000"
    assert selected('51266548')[0].payload['action'] == 'authorized_capital_clause_removed'
    assert [e.payload['shares'] for e in selected('54a71c3b')] == [10, 10]
    assert selected('54a71c3b')[0].signing == 'Einzelunterschrift'
    assert selected('54a71c3b')[1].signing == 'Einzelunterschrift'
    assert selected('904db5fc')[0].signing == 'Kollektivunterschrift zu zweien'
    assert selected('904db5fc')[0].payload['country'] == 'E'
    assert selected('92a6871b')[0].payload['consideration'] == "291'173"
    assert selected('92a6871b')[0].payload['liabilities'] == "344'182.30"
    assert [e.payload['shares'] for e in selected('964c4c93')] == [70, 70, 70]
    assert all(e.signing == 'Einzelunterschrift' for e in selected('964c4c93'))
    assert selected('b3715b85')[0].payload['name'] == 'Dionis Toé Henri Roger Jean Malo'
    assert selected('d41a5966')[0].payload['name'] == 'Guan Zhijie'
    assert selected('d41a5966')[0].payload['place'] == 'Veyrier'
    assert selected('d5c020d3')[0].payload['shares'] == 100
    assert selected('ea1f5fb5')[0].payload['action'] == 'headquarters_bankruptcy_request_rejected'
