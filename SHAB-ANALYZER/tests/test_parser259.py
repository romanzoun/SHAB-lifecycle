from pathlib import Path

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import extract_persons, extract_text_extras, map_hr_xml, parse_publication_xml
from shab_analyzer.parser259 import extract_parser259_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('1c419cfe', 'fr.text.seat_renamed_municipal_merger.v1', 1),
    ('21a2f188', 'fr.persons.partial_share_transfer_new_associate_without_signing.v1', 2),
    ('2eb202c6', 'fr.persons.auditor_replaced_branch.v1', 2),
    ('6cc20041', 'de.persons.director_residence_corrected.v1', 1),
    ('6e6e2eab', 'fr.persons.partial_share_transfer_existing_company.v1', 2),
    ('7855732f', 'fr.persons.board_president_residence_and_member_signing.v1', 2),
    ('7aad1723', 'de.text.complete_and_other_address.v1', 2),
    ('874e4169', 'it.text.association_deletion_pending_tax_consent.v1', 1),
    ('8b597fce', 'fr.persons.partial_share_transfer_director_manager.v1', 2),
    ('d7e541bf', 'fr.persons.manager_appointment_notice_supplement.v1', 1),
    ('ddc1ff3f', 'fr.persons.board_president_vice_president_signing_typo.v1', 2),
    ('f88a6052', 'de.persons.additional_nationality_notice_supplement.v1', 1),
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
    assert PARSER_VERSION >= 259
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    events = selected(prefix)
    assert len(events) == count
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in events)
    assert not any(e.rule_id == 'fr.persons.group_signing.v1' for e in result.events)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    leftover, context, text = residual(prefix)
    changed = leftover + '. UNRECOGNIZED_SUFFIX'
    assert extract_parser259_leftovers(changed, *context, source_text=text) == ([], changed)


@pytest.mark.parametrize('prefix,old,new', [
    ('21a2f188', 'cède 100', 'cède 101'),
    ('21a2f188', 'de 100 parts', 'de 99 parts'),
    ('21a2f188', 'de 100 parts de CHF 100', 'de 100 parts de CHF 200'),
    ('6e6e2eab', 'cède 7', 'cède 8'),
    ('6e6e2eab', 'de 9 parts', 'de 6 parts'),
    ('6e6e2eab', "de 9 parts de CHF 1'000", "de 9 parts de CHF 2'000"),
    ('8b597fce', 'avec 98 parts', 'avec 99 parts'),
    ('8b597fce', 'de 102 parts', 'de 103 parts'),
])
def test_inconsistent_shares_preserved(prefix, old, new):
    leftover, context, text = residual(prefix)
    assert old in leftover
    changed = leftover.replace(old, new, 1)
    assert extract_parser259_leftovers(changed, *context, source_text=text) == ([], changed)


@pytest.mark.parametrize('prefix', ['d7e541bf', '8b597fce'])
def test_removed_signing_requires_source_evidence(prefix):
    leftover, context, _ = residual(prefix)
    assert extract_parser259_leftovers(leftover, *context) == ([], leftover)


@pytest.mark.parametrize('prefix,old', [
    ('21a2f188', 'sans signature'),
    ('6cc20041', 'Kollektivunterschrift zu zweien'),
    ('7855732f', 'signent individuellement'),
    ('8b597fce', 'signer collectivement à deux'),
    ('ddc1ff3f', 'signent individuellement'),
])
def test_unknown_signing_preserved(prefix, old):
    leftover, context, text = residual(prefix)
    assert old in leftover
    changed = leftover.replace(old, 'UNRECOGNIZED_SIGNING')
    assert extract_parser259_leftovers(changed, *context, source_text=text) == ([], changed)


def test_supplement_unknown_source_signing_preserved():
    leftover, context, text = residual('d7e541bf')
    changed_source = text.replace('signature individuelle', 'UNRECOGNIZED_SIGNING')
    assert extract_parser259_leftovers(leftover, *context, source_text=changed_source) == ([], leftover)


def test_payloads():
    seat = selected('1c419cfe')[0]
    assert seat.event_type == 'seat_changed'
    assert seat.payload['seat'] == 'Villaz' and seat.payload['effective_date'] == '2020-01-01'
    assert seat.payload['municipalities'] == ['La Folliaz', 'Villaz-Saint-Pierre']
    seller, buyer = selected('21a2f188')
    assert seller.payload['shares_before'] == 200
    assert seller.payload['shares_transferred'] == seller.payload['shares_count'] == buyer.payload['shares_count'] == 100
    assert seller.payload['place'] == buyer.payload['place'] == 'Chavannes-près-Renens'
    assert seller.signing is None and buyer.signing == 'ohne Unterschrift'
    assert buyer.payload['origin'] == 'Brésil'
    old, new = selected('2eb202c6')
    assert old.event_type == new.event_type == 'auditor_changed'
    assert old.payload['action'] == 'departed' and new.payload['action'] == 'appointed'
    assert old.person_key == 'uid:CHE-106.397.400' and new.person_key == 'uid:CHE-396.702.286'
    assert new.payload['name'] == "GF Audit SA, succursale d'Yverdon les Bains"
    director = selected('6cc20041')[0]
    assert director.role == 'Direktor' and director.signing == 'Kollektivunterschrift zu zweien'
    assert director.payload['place'] == 'Rissegg' and director.payload['previous_place'] == 'Risseck'
    assert director.payload['entry_date'] == '2020-01-14' and director.payload['notice_date'] == '2020-01-17'
    seller, buyer = selected('6e6e2eab')
    assert seller.payload['shares_before'] == 18 and seller.payload['shares_count'] == 11
    assert buyer.payload['shares_received'] == 7 and buyer.payload['shares_count'] == 9 and buyer.payload['shares_before'] == 2
    assert buyer.person_key == 'uid:CHE-223.835.092'
    assert seller.signing is buyer.signing is None
    a, b = selected('7855732f')
    assert a.role == 'président' and a.payload['place'] == 'Dubaï' and a.payload['country'] == 'ARE'
    assert b.role == 'administrateur' and b.payload['place'] == 'Thônex' and b.payload['origin'] == 'Lausanne'
    assert a.signing == b.signing == 'Einzelunterschrift'
    full, other = selected('7aad1723')
    assert full.event_type == other.event_type == 'address_changed'
    assert full.payload == {'kind': 'complete_address', 'address': 'Beaulieu 11', 'postal_code': '3280', 'place': 'Murten'}
    assert other.payload == {'kind': 'other_address', 'action': 'new', 'address': 'Chemin du Village 20', 'postal_code': '3280', 'place': 'Meyriez'}
    pending = selected('874e4169')[0]
    assert pending.event_type == 'status_changed' and pending.payload['deleted'] is False
    assert pending.payload['action'] == 'pending' and pending.payload['legal_basis'] == '155 ORC'
    seller, buyer = selected('8b597fce')
    assert seller.role == 'gérant président' and seller.signing == 'Einzelunterschrift'
    assert buyer.role == 'associé-gérant' and buyer.signing == 'Kollektivunterschrift zu zweien'
    assert seller.payload['shares_count'] == 102 and buyer.payload['shares_count'] == 98
    assert buyer.payload['previous_role'] == 'directeur'
    manager = selected('d7e541bf')[0]
    assert manager.role == 'gérante' and manager.signing == 'Einzelunterschrift'
    assert manager.payload['entry'] == '295' and manager.payload['entry_date'] == '2020-01-06'
    assert manager.payload['origin'] == 'Rüdlingen' and manager.payload['place'] == 'Onex'
    a, b = selected('ddc1ff3f')
    assert a.role == 'président' and b.role == 'vice-président'
    assert a.signing == b.signing == 'Einzelunterschrift'
    assert b.payload['origin'] == 'Italie' and b.payload['place'] == 'Valsamoggia' and b.payload['country'] == 'I'
    nationality = selected('f88a6052')[0]
    assert nationality.payload['name'] == 'Neri-Carazzetti, Alexandra'
    assert nationality.payload['nationality'] == 'italienische'
    assert nationality.payload['entry'] == '49820' and nationality.payload['entry_date'] == '2019-12-19'
    assert nationality.role is nationality.signing is None


def test_supplement_after_legacy_signing_removal():
    leftover, context, text = residual('d7e541bf')
    changed = leftover.replace(' avec signature individuelle', '')
    events, rest = extract_parser259_leftovers(changed, *context, source_text=text)
    assert rest == '' and len(events) == 1
    assert events[0].signing == 'Einzelunterschrift'
    assert extract_parser259_leftovers(changed, *context) == ([], changed)
