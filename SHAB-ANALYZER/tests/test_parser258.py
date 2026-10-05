from pathlib import Path

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import extract_persons, extract_text_extras, map_hr_xml, parse_publication_xml
from shab_analyzer.parser258 import extract_parser258_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('2d9b1fbd', 'de.text.authorized_capital_expired.v1', 1),
    ('3d104a57', 'fr.text.branch_purpose_same_as_headquarters.v1', 1),
    ('5d2b57a9', 'fr.persons.partial_share_transfer_new_manager.v1', 2),
    ('72ad0a09', 'de.text.last_notice_reference_corrected.v1', 1),
    ('90937ff3', 'fr.text.branch_deleted_legacy_registry_id.v1', 1),
    ('962f1c96', 'fr.persons.partial_share_transfer_new_associate.v1', 2),
    ('9ed4826a', 'de.text.profit_participation_certificate.v1', 1),
    ('a65e875b', 'fr.persons.corporate_undivided_share_transfer.v1', 5),
    ('cf490f30', 'fr.persons.given_names_corrected_notice_typo.v1', 1),
    ('eed612bf', 'de.text.asset_transfer_to_municipality.v1', 1),
    ('ef8163a7', 'fr.text.bankruptcy_suspensive_effect_revoked.v1', 1),
    ('f7ad2a41', 'fr.persons.board_collective_signing_excluding_each_other.v1', 4),
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
    assert PARSER_VERSION == 259
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    events = selected(prefix)
    assert len(events) == count
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in events)
    assert not any(e.rule_id in {'fr.persons.group_signing.v1', 'fr.persons.first_name_changed_direct.v1', 'de.text.authorized_capital.v1'} for e in result.events)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    leftover, context, text = residual(prefix)
    changed = leftover + '. UNRECOGNIZED_SUFFIX'
    assert extract_parser258_leftovers(changed, *context, source_text=text) == ([], changed)


@pytest.mark.parametrize('prefix,old,new', [
    ('5d2b57a9', 'cède 98', 'cède 99'),
    ('5d2b57a9', 'de 102 parts', 'de 103 parts'),
    ('962f1c96', 'avec 80 parts', 'avec 81 parts'),
    ('962f1c96', 'de 120 parts', 'de 121 parts'),
    ('962f1c96', 'avec 80 parts de CHF 100', 'avec 80 parts de CHF 200'),
    ('a65e875b', "indivise de CHF 19'000", "indivise de CHF 20'000"),
])
def test_inconsistent_shares_preserved(prefix, old, new):
    leftover, context, text = residual(prefix)
    assert old in leftover
    changed = leftover.replace(old, new, 1)
    assert extract_parser258_leftovers(changed, *context, source_text=text) == ([], changed)


@pytest.mark.parametrize('prefix', ['5d2b57a9', 'f7ad2a41'])
def test_signing_requires_source_evidence(prefix):
    leftover, context, _ = residual(prefix)
    assert extract_parser258_leftovers(leftover, *context) == ([], leftover)


@pytest.mark.parametrize('prefix,old', [('5d2b57a9', 'signature individuelle'), ('f7ad2a41', 'signature collective à deux')])
def test_unknown_signing_preserved(prefix, old):
    leftover, context, text = residual(prefix)
    changed = leftover.replace(old, 'UNRECOGNIZED_SIGNING')
    assert extract_parser258_leftovers(changed, *context, source_text=text) == ([], changed)


def test_payloads():
    capital = selected('2d9b1fbd')[0].payload
    assert capital['authorization_date'] == '2018-01-12' and capital['reason'] == 'expired'
    assert 'amount' not in capital
    assert selected('3d104a57')[0].payload['same_as_headquarters'] is True
    seller, buyer = selected('5d2b57a9')
    assert seller.role == 'gérant président' and buyer.role == 'associé-gérant'
    assert seller.signing == buyer.signing == 'Einzelunterschrift'
    assert seller.payload['shares_before'] == 200
    assert seller.payload['shares_transferred'] == buyer.payload['shares_count'] == 98
    assert seller.payload['shares_count'] == 102
    reference = selected('72ad0a09')[0].payload
    assert reference['entry_date'] == '2020-01-20'
    assert reference['previous_notice_date'] == '2018-11-30' and reference['notice_date'] == '2020-01-22'
    branch = selected('90937ff3')[0].payload
    assert branch['registry_id'] == 'CH-300-9017970-7' and 'uid' not in branch
    seller, buyer = selected('962f1c96')
    assert seller.payload['shares_count'] == 120 and buyer.payload['shares_count'] == 80
    assert seller.signing is buyer.signing is None
    assert selected('9ed4826a')[0].payload['count'] == 1
    statute, a, b, c, d = selected('a65e875b')
    assert statute.event_type == 'statutes_changed'
    assert a.payload['action'] == b.payload['action'] == 'departed_and_participation_transferred'
    assert c.payload['registry_id'] == '201830910101' and d.payload['registry_id'] == '201830910118'
    assert all(e.payload['undivided_share_nominal'] == "19'000" and 'shares_count' not in e.payload for e in (a, b, c, d))
    correction = selected('cf490f30')[0].payload
    assert correction['given_names'] == 'Silvia de Jesus' and correction['entry_date'] == '2019-11-07'
    assert correction['name'] == 'Faria Campos Machado Silva de Jesus'
    transfer = selected('eed612bf')[0].payload
    assert transfer['date'] == '2019-11-05' and transfer['liabilities'] == '0.00'
    assert transfer['assets'] == "1'688'987.00" and transfer['consideration'] == "1'134'613.00"
    bankruptcy = selected('ef8163a7')[0].payload
    assert bankruptcy['decision_date'] == bankruptcy['effective_date'] == '2020-01-21'
    assert bankruptcy['bankruptcy_date'] == '2019-11-12' and bankruptcy['effective_time'] == '12:00'
    a, b, c, d = selected('f7ad2a41')
    for first, second in ((a, b), (c, d)):
        assert first.payload['signing_excluded_with'] == second.payload['name']
        assert second.payload['signing_excluded_with'] == first.payload['name']
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in (a, b, c, d))
    assert c.role == d.role == 'administrateur' and c.payload['place'] == 'Sullens'
