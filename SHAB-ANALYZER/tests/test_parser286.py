import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser286 import extract_parser286_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('1ac8d51e', 'fr.persons.board_president_changed.v1', 2), ('1f0d1df6', 'fr.persons.associate_appointed_manager.v1', 1), ('35caecaa', 'fr.persons.associate_manager_name_notice_corrected.v1', 1), ('41b84f7d', 'fr.text.limited_partner_contribution_reduced.v1', 1), ('66bd8235', 'fr.text.associate_communications_registered_address.v1', 1), ('6f0d9577', 'de.text.provisional_moratorium_lifted_restructuring.v1', 1), ('77b0fbf6', 'it.text.liquidation_complete_tax_consent_pending_typo.v1', 1), ('7cf4210f', 'fr.text.three_cooperative_share_nominals.v1', 1), ('8fa61e97', 'fr.text.partnership_erroneous_deletion_reinstated.v1', 1), ('9e394495', 'fr.persons.single_share_transferred_foreign_residences.v1', 3), ('acf3f011', 'fr.text.statutes_adoption_date_corrected.v1', 1), ('f32d16ec', 'fr.persons.partial_share_transfer_new_manager.v1', 3)]


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
        return extract_parser286_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser286_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 288
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
    assert extract_parser286_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser286_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('35caecaa', '27.02.2020', '31.02.2020'),
    ('41b84f7d', "50'000", '500'),
    ('41b84f7d', "1'000", '0'),
    ('6f0d9577', '24.10.2019', '31.02.2019'),
    ('6f0d9577', '28. Oktober', '32. Oktober'),
    ('7cf4210f', '500', '0'),
    ('8fa61e97', '19.12.2013', '31.02.2013'),
    ('9e394495', "10'000", '0'),
    ('acf3f011', '13.02.2020', '31.02.2020'),
    ('f32d16ec', '100 de ses', '201 de ses'),
    ('f32d16ec', 'CHF 100', 'CHF 0'),
])
def test_invalid_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new, 1)
    assert changed != args[0]
    assert extract_parser286_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['1f0d1df6', '66bd8235', '9e394495', 'f32d16ec'])
def test_source_evidence_required(prefix):
    args, kwargs = invocation(prefix)
    kwargs['source_text'] = ''
    assert extract_parser286_leftovers(*args, **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix', ['1f0d1df6', '9e394495', 'f32d16ec'])
def test_unrelated_signing_is_insufficient(prefix):
    args, kwargs = invocation(prefix)
    changed = args[0].removesuffix(' avec signature individuelle')
    kwargs['source_text'] = changed + '. Autre personne avec signature individuelle.'
    assert extract_parser286_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    board = selected('1ac8d51e')
    assert [e.role for e in board] == ['administratrice présidente', 'administrateur']
    assert all(e.signing == 'Einzelunterschrift' for e in board)
    assert board[1].payload['previous_role'] == 'président'
    manager = selected('1f0d1df6')[0]
    assert manager.role == 'associée-gérante' and manager.signing == 'Einzelunterschrift'
    corrected = selected('35caecaa')[0]
    assert corrected.payload['name'] == 'Pitton Alain'
    assert corrected.payload['previous_name'] == 'Pitton Michel'
    assert corrected.signing is None and corrected.payload['correction']
    contribution = selected('41b84f7d')[0].payload
    assert contribution['associate_uid'] == 'CHE-484.191.362'
    assert contribution['previous_amount'] == "50'000" and contribution['amount'] == "1'000"
    assert selected('66bd8235')[0].payload['address_source'] == 'registre des parts sociales'
    moratorium = selected('6f0d9577')[0].payload
    assert moratorium['decision_date'] == '24.10.2019'
    assert moratorium['previous_decision_date'] == '28.06.2019'
    assert moratorium['previous_until_date'] == '28.10.2019'
    assert moratorium['previous_duration_months'] == 4
    liquidation = selected('77b0fbf6')[0].payload
    assert liquidation['action'] == 'liquidation_completed' and liquidation['deletion_pending']
    assert selected('7cf4210f')[0].payload['share_nominals'] == ['500', "1'000", "1'500"]
    assert selected('8fa61e97')[0].payload['action'] == 'reinstatement'
    transfer = selected('9e394495')
    assert transfer[0].payload['shares'] == 1
    assert transfer[1].payload['country'] == 'ITA' and transfer[1].signing is None
    assert transfer[2].payload['country'] == 'PER' and transfer[2].signing == 'Einzelunterschrift'
    statutes = selected('acf3f011')[0].payload
    assert statutes['adoption_date'] == '13.02.2020' and statutes['previous_adoption_date'] == '13.12.2020'
    partial = selected('f32d16ec')
    assert [e.payload['shares'] for e in partial] == [100, 100, 100]
    assert partial[1].payload['previous_shares'] == 200 and partial[1].signing is None
    assert partial[2].role == 'associé-gérant' and partial[2].signing == 'Einzelunterschrift'


@pytest.mark.parametrize('prefix', ['1f0d1df6', '9e394495', 'f32d16ec'])
def test_signing_restored_only_from_source(prefix):
    args, kwargs = invocation(prefix)
    changed = args[0].removesuffix(' avec signature individuelle')
    events, residue = extract_parser286_leftovers(changed, *args[1:], **kwargs)
    assert residue == '' and any(e.signing == 'Einzelunterschrift' for e in events)
