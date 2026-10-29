import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser400 import extract_parser400_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = ['0a10e4702feaefd288ac8d085c845e13d20dc62b9fe65da1a03204face1fe5f3', '0ef3066f6f73840b0ef8bd3ebe18357881b4d74e51dd316fcf469005820da286', '168eec3938f926ecf63ecf4003e67161ed1bc180d6dd61f7cee7e25c47462334', '31a76ea96be7bd85a0494ab7eb5af4f559e047af16163fead76d434a6524e850', '392b537c786c42924a6c105083070f9d6a6ba17556977e11ca5ce2adc20cfc8c', '48a379d1c3199499ed2298c890cf952653f186a0906ae00fe8384a0eef998623', '4fadb314a055e5252626b2f52b2742fcd16b143f2722586a8957bc1c22befaa0', '62712725a2044ace0d9e6a80b7abf7f1cad8cff80174040e1eb89160bcea6e32', '9e7a098e2ef284e575e68cb477f8827bcc89bee21db2b1069439cb65e457a986', 'ad615407afc46a702ed6bb293ae82e402bef4c7bcd927ecc6a35f8ec6014c932', 'bfd606dd6677176e6c5ac6792124fad605ccd6260d0268fed34df97508e935f1', 'e675b7b3abca7c8f2c21738c3fdc406f4a7ae27ba5f806542196da308f75132b']
CONTEXT_REQUIRED = {'48a379d1', '4fadb314', 'bfd606dd'}
EXPECTED = [('status_changed', 'reinstatement_peace_court_previous_facts_valid', {'decision_date': '16.12.2020'}), ('officer_changed', 'branch_female_director_joint_signing_granted', {'signing_scope': 'affaires de la succursale'}), ('ownership_changed', 'associate_transfer_new_female_manager_president', {'count': '100', 'previous_count': '200', 'country': 'P'}), ('status_changed', 'association_deletion_blocked_tax_consent', {'article': '155 vORC'}), ('ownership_changed', 'associate_transfer_both_resulting_holdings', {'remaining': '50', 'count': '49', 'buyer_count': '150'}), ('officer_changed', 'liquidator_commercial_name_individual', {'place': 'Lutry'}), ('officer_changed', 'italian_associate_president_name_corrected', {'previous_name': 'Bianchini, Claudia', 'count': '140', 'nominal': '100.00'}), ('ownership_changed', 'manager_president_transfer_retains_one_share', {'remaining': '1', 'count': '99', 'buyer_count': '199'}), ('assets_transferred', 'company_asset_transfer_inventory_postposed_liabilities', {'assets': "355'391.75", 'liabilities': "4'987.55", 'consideration': "350'404.20"}), ('company_name_changed', 'company_translation_supplement_note', {'supplement': True}), ('officer_changed', 'board_member_joint_president_proxy_revoked', {'previous_signing_revoked': True}), ('officer_changed', 'two_female_directors_joint_board_member_proxy_revoked', {'previous_signing_revoked': True})]

@lru_cache(None)
def captured(digest):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser400_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser400_leftovers', capture):
        result = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert len(calls) == 1
    return result, calls[0]


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_complete_and_unchanged_legacy_payloads(digest):
    import shab_analyzer.parse as parser
    result, (args, kwargs) = captured(digest)
    added, rest = extract_parser400_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 427
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == (3 if digest.startswith('168eec39') else 2 if digest.startswith('e675b7b3') else 1) and not rest
    with patch.object(parser, 'extract_parser400_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('digest,expected', list(zip(SUPPLIED_SHA256, EXPECTED)))
def test_explicit_meaning(digest, expected):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser400_leftovers(*args, **kwargs)
    kind, action, fields = expected
    assert not rest and events[0].event_type == kind
    assert events[0].rule_id == f'{args[1]}.text.{action}.v1'
    assert events[0].payload['action'] == action
    assert {key: events[0].payload[key] for key in fields} == fields
@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_unknown_suffix_language_and_invalid_dates(digest):
    _, (args, kwargs) = captured(digest)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser400_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser400_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser400_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_missing_optional_metadata_and_source(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser400_leftovers(*args[:4], None, None, None, **kwargs)
    assert events and not rest
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    events, rest = extract_parser400_leftovers(*args)
    if digest[:8] in CONTEXT_REQUIRED:
        assert not events and rest == args[0]
    else:
        assert events and not rest


def test_old_event_without_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event



@pytest.mark.parametrize('prefix', sorted(CONTEXT_REQUIRED))
def test_context_required_and_consistent(prefix):
    digest = next(d for d in SUPPLIED_SHA256 if d.startswith(prefix))
    _, (args, kwargs) = captured(digest)
    assert extract_parser400_leftovers(*args, source_text='Unrelated.') == ([], args[0])
    altered = args[0].replace('Guillemin', 'Autre').replace('Banchini', 'Autre').replace('Quesada', 'Autre')
    assert altered != args[0]
    assert extract_parser400_leftovers(altered, *args[1:], **kwargs) == ([], altered)


def test_person_specific_roles_signing_and_domicile():
    digest = SUPPLIED_SHA256[2]
    _, (args, kwargs) = captured(digest)
    events, _ = extract_parser400_leftovers(*args, **kwargs)
    assert events[1].role == 'gérant président'
    assert events[1].signing == 'Einzelunterschrift'
    assert events[1].payload['place'] is None
    assert events[2].role == 'gérante'
    assert events[2].signing == 'Kollektivunterschrift zu zweien'
    assert events[2].payload['place'] == 'Lisbonne'
    _, (args, kwargs) = captured(SUPPLIED_SHA256[-1])
    events, _ = extract_parser400_leftovers(*args, **kwargs)
    assert [e.payload['name'] for e in events] == ['Garcia Junko', 'Zen Ruffinen Kay Fong']
    assert all(e.signing == 'Kollektivunterschrift zu zweien' and e.role == 'directrice' for e in events)


@pytest.mark.parametrize('version,text,language', [
    (112, "L'associé Exemple Anne est nommé gérant président", 'fr'),
    (56, 'Persona iscritta corretta: Exemple, Anne, da Lugano, in Lugano, gerente, con firma individuale, con 10 quote da CHF 100', 'it'),
    (384, 'Exemple Anne et Exemple Marie, nommées directrices, signent désormais collectivement à deux; leur procuration est radiée', 'fr'),
])
def test_legacy_rule_ownership_in_isolation(version, text, language):
    import importlib
    module = importlib.import_module(f'shab_analyzer.parser{version}')
    args = text, language, 'p', '', None, None, None
    events, rest = getattr(module, f'extract_parser{version}_leftovers')(*args)
    assert events and not rest
    assert extract_parser400_leftovers(*args) == ([], text)


@pytest.mark.parametrize('stem', ['37a3ffc9-0f3b-47b3-bacd-1b40d851d8c0', '1855c3abe279580b8806de34447fdc1f75832e8ebc2773afe15f19d7b9459311', '2bfe63c21628baa119c054da99ab2f48e32db8af946cc9b50f59376bc86bf64b'])
def test_existing_fixture_unchanged(stem):
    import shab_analyzer.parse as parser
    path = FIXTURES / (stem + '.xml')
    result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser400_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(path)
