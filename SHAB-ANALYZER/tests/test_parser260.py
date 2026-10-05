from pathlib import Path
import hashlib

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import extract_persons, extract_text_extras, map_hr_xml, parse_publication_xml
from shab_analyzer.parser260 import extract_parser260_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('02c30048', 'fr.persons.share_transfer_remaining_and_new_associate.v1', 2),
    ('111a8176', 'de.text.founders_declaration_audit_opt_out.v1', 1),
    ('1bf9b73e', 'fr.text.bankruptcy_execution_suspended_name_restored.v1', 1),
    ('51bf65c9', 'fr.text.authorized_capital_expired_clause_deleted.v1', 1),
    ('52703058', 'fr.persons.share_transfer_three_managers_typo.v1', 4),
    ('9c9cd475', 'de.persons.owner_residence_changed.v1', 1),
    ('b8dfca27', 'it.persons.president_and_manager_residence_changed.v1', 2),
    ('bc0f2ee2', 'de.text.reinstated_for_liquidation_after_deletion.v1', 1),
    ('ca25bc34', 'fr.text.sole_proprietor_asset_transfer.v1', 1),
    ('ce4e8a00', 'de.text.sole_proprietor_bankruptcy_closed_deleted.v1', 1),
    ('da297315', 'fr.persons.director_to_sole_administrator.v1', 1),
    ('dafb36bb', 'de.text.additional_address_abbreviated_place.v1', 1),
]


def path(prefix):
    paths = list(FIXTURES.glob(prefix + '*.xml'))
    assert len(paths) == 1
    return paths[0]


def selected(prefix):
    rule = next(rule for stem, rule, _ in CASES if stem == prefix)
    return [e for e in parse_publication_xml(path(prefix)).events if e.rule_id == rule]


def residual(prefix):
    p = path(prefix)
    meta, xml_events, text = map_hr_xml(p)
    context = (meta.get('language'), meta.get('publication_id') or p.stem,
               meta.get('published_at') or '', meta.get('org_uid'), meta.get('plz'), meta.get('canton'))
    persons, leftover = extract_persons(text, *context)
    _, leftover = extract_text_extras(leftover, *context, {e.event_type for e in xml_events + persons})
    return leftover, context, text


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION >= 260
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    events = selected(prefix)
    assert len(events) == count
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in events)
    assert not any(e.rule_id == 'fr.persons.group_signing.v1' for e in result.events)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    leftover, context, text = residual(prefix)
    changed = leftover + '. UNRECOGNIZED_SUFFIX'
    assert extract_parser260_leftovers(changed, *context, source_text=text) == ([], changed)


@pytest.mark.parametrize('prefix,old,new', [
    ('02c30048', 'cession de 60', 'cession de 61'),
    ('02c30048', 'cession de 60', 'cession de 0'),
    ('02c30048', 'pour 60 parts de CHF 100', 'pour 60 parts de CHF 200'),
    ('52703058', 'cède 18', 'cède 17'),
    ('52703058', 'par 6 parts', 'par 5 parts'),
    ('52703058', 'de ses 20', 'de ses 21'),
    ('52703058', 'titulaire de 2', 'titulaire de 3'),
    ('52703058', "titulaire de 2 parts de CHF 1'000", "titulaire de 2 parts de CHF 2'000"),
    ('52703058', 'chacun titulaire de 6', 'chacun titulaire de 7'),
    ('51bf65c9', "[biffé: Augmentation autorisée du capital fondée sur la décision d'autorisation du 07.12.2018]", "[biffé: Augmentation autorisée du capital fondée sur la décision d'autorisation du 08.12.2018]"),
])
def test_inconsistent_facts_preserved(prefix, old, new):
    leftover, context, text = residual(prefix)
    assert old in leftover
    changed = leftover.replace(old, new, 1)
    assert extract_parser260_leftovers(changed, *context, source_text=text) == ([], changed)


@pytest.mark.parametrize('prefix,old', [
    ('02c30048', 'sans signature sociale'),
    ('52703058', 'signature individuelle'),
    ('9c9cd475', 'Einzelunterschrift'),
    ('b8dfca27', 'firma individuale'),
    ('da297315', 'signer individuellement'),
])
def test_unknown_signing_preserved(prefix, old):
    leftover, context, text = residual(prefix)
    assert old in leftover
    changed = leftover.replace(old, 'UNRECOGNIZED_SIGNING')
    assert extract_parser260_leftovers(changed, *context, source_text=text) == ([], changed)


def test_abbreviated_address_requires_source_and_replaces_partial_event():
    leftover, context, text = residual('dafb36bb')
    assert extract_parser260_leftovers(leftover, *context) == ([], leftover)
    assert extract_parser260_leftovers(leftover, *context, source_text=text + ' UNKNOWN') == ([], leftover)
    result = parse_publication_xml(path('dafb36bb'))
    assert not any(e.rule_id == 'de.text.additional_address.v1' for e in result.events)
    assert selected('dafb36bb')[0].payload == {'action': 'added', 'address': 'Längmoos 1A', 'postal_code': '3636', 'place': 'Forst b. Längenbühl'}


def test_payloads():
    seller, buyer = selected('02c30048')
    assert seller.payload['shares_count'] == 140 and seller.payload['shares_transferred'] == 60
    assert seller.signing is None and 'shares_before' not in seller.payload
    assert buyer.payload['shares_count'] == 60 and buyer.payload['country'] == 'F'
    assert buyer.payload['origin'] == 'France' and buyer.signing == 'ohne Unterschrift'
    audit = selected('111a8176')[0]
    assert audit.event_type == 'auditor_changed' and audit.payload['declaration_date'] == '2016-11-10'
    assert audit.payload['ordinary_audit_required'] is False and audit.payload['limited_audit_waived'] is True
    suspended = selected('1bf9b73e')[0]
    assert suspended.payload['date'] == '2019-12-30' and suspended.payload['judgment_date'] == '2019-12-09'
    assert suspended.payload['court'] == 'Tribunal cantonal' and suspended.payload['restored_name'] == 'Thiébaud & Co SA'
    capital = selected('51bf65c9')[0]
    assert capital.payload['authorization_date'] == '2018-12-07' and capital.payload['statutes_date'] == '2020-01-14'
    rules = [e.rule_id for e in parse_publication_xml(path('51bf65c9')).events]
    assert 'fr.text.capital_clause_expired.v1' not in rules
    assert 'fr.text.authorized_capital_clause.v2' in rules and 'fr.text.conditional_capital_clause.v1' in rules
    seller, *buyers = selected('52703058')
    assert seller.payload['shares_before'] == 20 and seller.payload['shares_count'] == 2
    assert seller.role == 'président' and seller.signing is None
    assert sum(b.payload['shares_received'] for b in buyers) == seller.payload['shares_transferred'] == 18
    assert all(b.role == 'associé-gérant' and b.signing == 'Einzelunterschrift' and b.payload['origin'] == 'Portugal' for b in buyers)
    assert [b.payload['place'] for b in buyers] == ['Renens (VD)', 'Lausanne', 'Préverenges']
    owner = selected('9c9cd475')[0]
    assert owner.role == 'Inhaber' and owner.signing == 'Einzelunterschrift' and owner.payload['place'] == 'Köniz'
    president, manager = selected('b8dfca27')
    assert president.role == 'presidente' and manager.role == 'gerente'
    assert president.signing == manager.signing == 'Einzelunterschrift'
    assert manager.payload['place'] == 'Monaco (MC)' and manager.payload['previous_place'] == 'Besazio (Mendrisio)'
    reinstated = selected('bc0f2ee2')[0]
    assert reinstated.payload['deleted'] is False and reinstated.payload['purpose'] == 'liquidation'
    assert reinstated.payload['deletion_date'] == '2019-05-01' and reinstated.payload['decision_date'] == '2019-12-16'
    transfer = selected('ca25bc34')[0]
    assert transfer.payload['date'] == '2019-12-18' and transfer.payload['uid'] == 'CHE-116.025.779'
    assert transfer.payload['assets'] == "248'770.77" and transfer.payload['liabilities'] == "214'468.24"
    assert transfer.payload['consideration'] == "34'302.53" and transfer.payload['recipient'] == "Pierrot Ayer, L'Authentique Sàrl"
    closed = selected('ce4e8a00')[0]
    assert closed.payload['court'] == 'Bezirksgerichts Horgen' and closed.payload['date'] == '2020-01-09'
    assert closed.payload['deleted'] is True
    director = selected('da297315')[0]
    assert director.role == 'administrateur unique' and director.signing == 'Einzelunterschrift'
    assert director.payload['previous_role'] == 'directeur'
