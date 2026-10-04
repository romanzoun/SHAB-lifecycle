from pathlib import Path

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import extract_persons, extract_text_extras, map_hr_xml, parse_publication_xml
from shab_analyzer.parser255 import extract_parser255_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('0f32259e', 'fr.text.contribution_clauses_removed.v1', 1),
    ('1de32317', 'de.text.definitive_moratorium_extended.v1', 1),
    ('28d88be5', 'fr.text.audit_waiver_declaration_date_corrected.v1', 1),
    ('4a79579e', 'fr.persons.two_administrators_origin_changed.v1', 2),
    ('738567e6', 'de.persons.board_origin_residence_corrected.v1', 1),
    ('79446eaf', 'fr.persons.partial_share_transfer_new_manager_president.v1', 2),
    ('7d4bce93', 'fr.persons.administrator_liquidator_residence.v1', 1),
    ('8b87652a', 'fr.persons.unequal_nominal_share_transfer_president.v1', 2),
    ('902c4f2a', 'fr.persons.board_replacement_president_collective.v1', 3),
    ('c45192f3', 'fr.text.statutes_date_supplement_typo.v1', 1),
    ('cca0021b', 'de.persons.manager_shareholder_replaced_by_company.v1', 2),
    ('ec02efc9', 'fr.text.branch_removal_notice_reference.v1', 1),
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
    result = parse_publication_xml(path(prefix))
    assert PARSER_VERSION >= 255
    assert result.status == 'FULLY_PARSED'
    assert result.leftover_text == ''
    events = selected(prefix)
    assert len(events) == count
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in events)
    if any(e.signing for e in events):
        assert not any(e.rule_id == 'fr.persons.group_signing.v1' for e in result.events)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unrecognized_suffix_preserved(prefix, rule, count):
    leftover, context, source = residual(prefix)
    changed = leftover + '. UNRECOGNIZED_SUFFIX'
    assert extract_parser255_leftovers(changed, *context, source_text=source) == ([], changed)


def test_payloads():
    audit = selected('28d88be5')[0].payload
    assert audit['declaration_date'] == '2019-12-17'
    assert audit['previous_published_date'] == '17 décembre 201'
    assert audit['ordinary_audit'] is False and audit['limited_audit_waived'] is True
    assert selected('c45192f3')[0].payload['date'] == '2019-12-09'
    assert selected('1de32317')[0].payload['extension_months'] == 3
    board = selected('738567e6')[0]
    assert board.payload['origin'] == 'Basadingen-Schlattingen'
    assert board.payload['previous_origin'] == 'Zürich'
    assert board.payload['place'] == 'Bern'
    assert board.payload['previous_place'] == 'Basadingen-Schlattingen'
    assert all(e.payload['origin'] == 'Bernex' for e in selected('4a79579e'))
    seller, buyer = selected('79446eaf')
    assert seller.payload['shares_before'] == 20
    assert seller.payload['shares_count'] == seller.payload['shares_transferred'] == buyer.payload['shares_received'] == 10
    assert buyer.signing == 'Einzelunterschrift' and seller.signing is None
    seller, buyer = selected('8b87652a')
    assert seller.payload['shares_nominal'] == "1'000"
    assert buyer.payload['shares_nominal'] == "19'000"
    assert 'shares_before' not in seller.payload
    manager, company = selected('cca0021b')
    assert manager.role == 'Geschäftsführer'
    assert manager.payload['action'] == 'shareholder_role_removed'
    assert company.person_key == 'uid:CHE-430.963.023'
    assert company.payload['shares_count'] == 20 and company.signing is None
    liquidator = selected('7d4bce93')[0]
    assert liquidator.role == 'administrateur liquidateur'
    assert liquidator.payload['place'] == 'Crassier' and liquidator.signing == 'Einzelunterschrift'
    removed, president, member = selected('902c4f2a')
    assert removed.payload['signing_revoked'] is True and removed.signing is None
    assert president.role == 'administrateur président'
    assert president.signing == member.signing == 'Kollektivunterschrift zu zweien'
    notice = selected('ec02efc9')[0].payload
    assert notice['notice_date'] == '2019-12-30' and notice['notice_ref'] == '1004795245'
    assert any(e.rule_id == 'fr.text.branch_removed.v1' for e in parse_publication_xml(path('ec02efc9')).events)


@pytest.mark.parametrize('prefix', ['ec02efc9'])
def test_source_evidence_required(prefix):
    leftover, context, _ = residual(prefix)
    assert extract_parser255_leftovers(leftover, *context) == ([], leftover)


@pytest.mark.parametrize('old,new', [('cède 10 de ses 20', 'cède 11 de ses 20'),
                                     ('reste titulaire de 10', 'reste titulaire de 11'),
                                     ("reste titulaire de 10 parts de CHF 1'000", "reste titulaire de 10 parts de CHF 2'000")])
def test_inconsistent_transfer_preserved(old, new):
    leftover, context, source = residual('79446eaf')
    assert old in leftover
    changed = leftover.replace(old, new)
    assert extract_parser255_leftovers(changed, *context, source_text=source) == ([], changed)
