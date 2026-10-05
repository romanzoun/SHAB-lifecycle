import hashlib
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser270 import extract_parser270_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('709c2072', 'fr.persons.liquidator_shared_relocation.v1', 2),
    ('9b041988', 'de.text.authorized_conditional_participation_capital.v1', 1),
    ('a971ce29', 'fr.persons.committee_president_treasurer_changed.v1', 2),
    ('b6965d8d', 'de.text.void_statutes_audit_restored.v1', 1),
    ('bf2da2c6', 'de.persons.board_member_name_place_changed.v1', 1),
    ('c90a6f05', 'fr.persons.name_origin_corrected_typo.v1', 1),
    ('e0010e29', 'de.text.organization_entry_deleted_regulations.v1', 1),
    ('e4090fe1', 'fr.persons.registered_name_rectified.v1', 1),
    ('efdd6dd9', 'fr.persons.registered_name_rectified.v1', 1),
    ('f392226a', 'fr.text.intended_asset_takeover_clause_deleted.v1', 1),
    ('f45125c9', 'fr.persons.two_committee_members_unsigned.v1', 2),
    ('f4c315ee', 'fr.persons.director_appointed_administrator.v1', 1),
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
        return extract_parser270_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser270_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 271
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
    assert extract_parser270_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['9b041988', 'b6965d8d', 'e4090fe1', 'efdd6dd9'])
def test_invalid_date_preserved(prefix):
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', args[0])
    kwargs['source_text'] = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', kwargs['source_text'])
    assert extract_parser270_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,old,new', [
    ('709c2072', 'signature individuelle', 'signature collective à deux'),
    ('b6965d8d', 'nichtig sind', 'gültig sind'),
    ('f4c315ee', 'il continue', 'il cesse'),
])
def test_source_required_and_validated(prefix, old, new):
    args, kwargs = invocation(prefix)
    assert extract_parser270_leftovers(*args) == ([], args[0])
    changed = kwargs['source_text'].replace(old, new)
    assert changed != kwargs['source_text']
    assert extract_parser270_leftovers(*args, source_text=changed) == ([], args[0])
    assert extract_parser270_leftovers(*args, source_text=kwargs['source_text'] + ' UNKNOWN_SUFFIX') == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('9b041988', 'bedingte Erhöhung', 'unbedingte Erhöhung'),
    ('a971ce29', 'nommé trésorier', 'nommé secrétaire'),
    ('f45125c9', "n'exercent pas", 'exercent'),
    ('f392226a', '628 al. 4', '628 al. 3'),
    ('e0010e29', 'geänderter Eintragungsvorschriften', 'einer Fusion'),
])
def test_unsupported_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser270_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads_and_superseded_events():
    liquidator, associate = selected('709c2072')
    assert liquidator.payload['name'] == 'Bochud Michel'
    assert liquidator.role == 'associé-gérant, liquidateur'
    assert liquidator.payload['place'] == associate.payload['place'] == 'Lugano'
    assert liquidator.signing == associate.signing == 'Einzelunterschrift'
    assert not any(e.payload.get('name') == 'lequel' for e in parse_publication_xml(path('709c2072')).events)
    capital = selected('9b041988')[0].payload
    assert capital['decision_date'] == '05.02.2020' and capital['previous_date'] == '20.03.2019'
    assert capital['authorized_increase_amended'] and capital['conditional_increase']
    president, treasurer = selected('a971ce29')
    assert president.role == 'président du comité' and treasurer.role == 'trésorier du comité'
    assert treasurer.payload['previous_role'] == 'président'
    restored = selected('b6965d8d')[0].payload
    assert restored['audit_waiver_revoked'] and restored['statutes_restored']
    assert restored['decision_date'] == '07.09.2017' and restored['entry'] == "4'892"
    assert not any(e.rule_id == 'de.text.statutes.v1' for e in parse_publication_xml(path('b6965d8d')).events)
    board = selected('bf2da2c6')[0]
    assert board.payload['previous_name'] == 'Moser Patricia' and board.payload['name'] == 'Spring Patricia'
    assert board.payload['place'] == 'Plaffeien' and board.signing == 'Einzelunterschrift'
    origin = selected('c90a6f05')[0]
    assert origin.payload['origin'] == 'Bussigny' and origin.signing is None
    for prefix in ['e4090fe1', 'efdd6dd9']:
        e = selected(prefix)[0]
        assert e.payload['name'] != e.payload['previous_name'] and e.signing is None
    assert selected('e0010e29')[0].payload['action'] == 'organization_entry_deleted'
    assert selected('f392226a')[0].payload['legal_basis'] == 'article 628 al. 4 CO'
    assert all(e.signing is None and e.payload['without_signature'] for e in selected('f45125c9'))
    director = selected('f4c315ee')[0]
    assert director.role == 'administrateur' and director.payload['previous_role'] == 'directeur'
    assert director.signing == 'Kollektivunterschrift zu zweien'


def test_existing_name_correction_with_de_keeps_historical_rule():
    result = parse_publication_xml(FIXTURES / '3b55ab7c-1f3f-44d7-b249-5d37cb8f0bc1.xml')
    assert result.status == 'FULLY_PARSED'
    events = [e for e in result.events if e.rule_id == 'fr.persons.name_corrected_with_reference.v1']
    assert len(events) == 1 and events[0].payload['name'] == 'Hughes Alan Thomas'
    assert not any(e.rule_id == 'fr.persons.registered_name_rectified.v1' for e in result.events)
