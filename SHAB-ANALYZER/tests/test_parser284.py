import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser284 import extract_parser284_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('13c68069', 'fr.persons.new_associate_individual.v1', 1), ('3f54cab5', 'de.text.additional_address_removed.v1', 1), ('5192d8e7', 'fr.persons.two_individual_procurations_shared_origin.v1', 2), ('5fc5b424', 'de.text.dissolution_corrected_name_liquidator.v1', 2), ('74a65497', 'fr.persons.two_domiciles_changed.v1', 2), ('77e45fb3', 'fr.persons.manager_president_two_new_managers.v1', 3), ('a570ef7a', 'fr.persons.transfer_managers_director_individual.v1', 3), ('b2312a06', 'fr.text.establishment_mention_removed.v1', 1), ('c944d63e', 'fr.persons.delegate_given_name_corrected.v1', 1), ('e8efb92e', 'fr.text.registered_shares_restricted.v1', 1), ('eca283df', 'fr.persons.two_directors_procurations_revoked.v1', 2), ('fc5aa990', 'de.persons.associate_exit_two_holdings.v1', 3)]


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
        return extract_parser284_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser284_leftovers', capture):
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
    assert extract_parser284_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser284_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('5fc5b424', '03.02.2020', '31.02.2020'),
    ('c944d63e', '31.01.2020', '31.02.2020'),
    ('e8efb92e', "100'000", "101'000"),
    ('e8efb92e', "1'000", '0'),
    ('a570ef7a', "1'000", '0'),
    ('fc5aa990', '100.00', '0.00'),
    ('eca283df', 'leur procuration est radiée', 'leur procuration subsiste'),
])
def test_invalid_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new, 1)
    assert changed != args[0]
    assert extract_parser284_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['a570ef7a', 'e8efb92e'])
def test_source_evidence_required(prefix):
    args, kwargs = invocation(prefix)
    kwargs['source_text'] = ''
    assert extract_parser284_leftovers(*args, **kwargs) == ([], args[0])


def test_payloads():
    associate = selected('13c68069')[0]
    assert associate.role == 'associé' and associate.signing == 'Einzelunterschrift'
    assert associate.payload['origin'] == 'Wohlen (AG)'
    address = selected('3f54cab5')[0].payload
    assert address['postal_code'] == '9430' and address['action'] == 'additional_address_removed'
    procurations = selected('5192d8e7')
    assert all(e.signing == 'Einzelprokura' and e.payload['origin'] == 'Royaume-Uni' for e in procurations)
    dissolution, liquidator = selected('5fc5b424')
    assert dissolution.payload['resolution_date'] == '03.02.2020'
    assert liquidator.payload['name'] == 'Piller Rosa Isabella'
    assert liquidator.payload['previous_name'] == 'Piller-Piller Isabelle'
    assert liquidator.role == 'Verwaltungsratsmitglied, Vizepräsidentin, Liquidatorin'
    assert all(e.payload['place'] == 'Chéserex' and e.signing is None for e in selected('74a65497'))
    managers = selected('77e45fb3')
    assert managers[0].role == 'gérant président' and managers[0].payload['place'] is None
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in managers)
    transfer = selected('a570ef7a')
    assert [e.role for e in transfer] == ['associée-gérante présidente', 'associé-gérant', 'directrice']
    assert [e.payload['shares'] for e in transfer[:2]] == [10, 10]
    assert transfer[0].payload['country'] == 'ESP'
    assert all(e.signing == 'Einzelunterschrift' for e in transfer)
    assert selected('b2312a06')[0].payload['action'] == 'establishment_mention_removed'
    corrected = selected('c944d63e')[0]
    assert corrected.payload['correction'] and corrected.payload['name'] == 'Iunius Florian Ray'
    capital = selected('e8efb92e')[0].payload
    assert capital['capital'] == "100'000" and capital['restricted_by_statutes'] and capital['fully_paid']
    assert all(e.role == 'directeur' and e.payload['procuration_revoked'] for e in selected('eca283df'))
    associates = selected('fc5aa990')
    assert [e.event_type for e in associates] == ['officer_removed', 'officer_changed', 'officer_changed']
    assert [e.payload['shares'] for e in associates] == [101, 100, 100]
    assert associates[1].payload['previous_shares'] == 99
    assert all(e.signing == 'ohne Zeichnungsberechtigung' for e in associates)
