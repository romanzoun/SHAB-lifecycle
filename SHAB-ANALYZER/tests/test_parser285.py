import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser285 import extract_parser285_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('0336731b', 'fr.persons.president_signing_corrected.v1', 1), ('42fbd63c', 'fr.text.two_branch_identifiers.v1', 2), ('6889065f', 'fr.persons.associate_manager_name_corrected.v1', 1), ('7ef9996b', 'fr.text.dissolution_resolution_date_corrected.v1', 1), ('a6de7107', 'de.text.court_reinstatement_for_liquidation.v1', 1), ('b3c9452f', 'fr.persons.administrator_signing_corrected.v1', 1), ('d878e90f', 'fr.persons.director_to_collective_procuration.v1', 1), ('e1da2826', 'fr.persons.two_procurations_with_administrator.v1', 2), ('e7ec08b6', 'fr.persons.two_single_shares_transferred.v1', 3), ('f8221d17', 'fr.text.share_split_restrictions_removed.v1', 1), ('f907a735', 'fr.persons.two_managers_transfer_new_manager.v1', 3), ('ff59cae4', 'de.text.court_share_sale_prohibited.v1', 1)]


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
        return extract_parser285_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser285_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 290
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
    assert extract_parser285_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser285_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('0336731b', '13.03.2020', '31.02.2020'),
    ('6889065f', '26.02.2020', '31.02.2020'),
    ('7ef9996b', '20 novembre', '31 novembre'),
    ('a6de7107', '21.02.2020', '31.02.2020'),
    ('b3c9452f', '21.02.2020', '31.02.2020'),
    ('e7ec08b6', "5'000", '0'),
    ('f8221d17', "100'000", "101'000"),
    ('f907a735', '66 parts', '65 parts'),
    ('f907a735', '67 parts', '68 parts'),
    ('ff59cae4', '04.03.2020', '31.02.2020'),
])
def test_invalid_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new, 1)
    assert changed != args[0]
    assert extract_parser285_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['7ef9996b', 'f8221d17', 'f907a735'])
def test_source_evidence_required(prefix):
    args, kwargs = invocation(prefix)
    kwargs['source_text'] = ''
    assert extract_parser285_leftovers(*args, **kwargs) == ([], args[0])


def test_payloads():
    president = selected('0336731b')[0]
    assert president.role == 'administrateur président' and president.signing == 'Einzelunterschrift'
    assert president.payload['correction']
    branches = selected('42fbd63c')
    assert [e.payload['branch_uid'] for e in branches] == ['CHE-241.704.938', 'CHE-230.378.645']
    assert all(e.payload['place'] == e.payload['previous_place'] for e in branches)
    name = selected('6889065f')[0]
    assert name.payload['name'] == 'Da Silva Couto Paulo'
    assert name.payload['previous_name'] == 'Da Silva Cuoto Paulo' and name.signing is None
    resolution = selected('7ef9996b')[0].payload
    assert resolution['resolution_date'] == '20.11.2019'
    assert resolution['previous_resolution_date'] == '20.12.2019'
    reinstatement = selected('a6de7107')[0].payload
    assert reinstatement['action'] == 'reinstatement' and reinstatement['decision_date'] == '21.02.2020'
    assert reinstatement['deletion_date'] == '15.05.2019'
    administrator = selected('b3c9452f')[0]
    assert administrator.signing == 'Kollektivunterschrift zu zweien'
    assert administrator.payload['previous_signing'] == 'Einzelunterschrift'
    procuration = selected('d878e90f')[0]
    assert procuration.signing == 'Kollektivprokura zu zweien'
    assert procuration.role is None and procuration.payload['previous_role'] == 'directeur'
    assert all(e.signing == 'Kollektivprokura zu zweien' and e.payload['signing_restriction'] == 'avec un administrateur' for e in selected('e1da2826'))
    transfers = selected('e7ec08b6')
    assert [e.payload['share_nominal'] for e in transfers[:2]] == ["5'000", "15'000"]
    assert transfers[2].role == 'associé-gérant' and transfers[2].payload['sole_manager']
    capital = selected('f8221d17')[0].payload
    assert capital['count'] == "1'000" and capital['nominal'] == '100'
    assert capital['previous_count'] == '100' and capital['previous_nominal'] == "1'000"
    assert capital['previous_restricted_by_statutes'] and not capital['restricted_by_statutes']
    managers = selected('f907a735')
    assert [e.payload['shares'] for e in managers] == [67, 67, 66]
    assert all(e.signing is None for e in managers[:2])
    assert managers[2].signing == 'Einzelunterschrift'
    assert managers[2].payload['origin'] == managers[2].payload['place'] == 'Genève'
    prohibition = selected('ff59cae4')[0].payload
    assert prohibition['action'] == 'share_sale_prohibited' and 'name' not in prohibition
