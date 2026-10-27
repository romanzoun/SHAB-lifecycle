import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser401 import extract_parser401_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = ['02d7977bbec20dce451199b1cf222bc63306a7b7be0c5b42412a7c044ceafbdb', '135d03928fdb4ea0a73e9743c760906b3ca7a00f0380174a7d8b27dd5baa3731', '27a39157d4b0d98c0c3970da7dbe365a424291905c7131dfcfb254baf21cc219', '64739f4eeb7e70af6fc4d430f20b3672b6afaa178c0abf2abd69f107903795f4', '6bfad0abcdd6c4016bc02cde3bbeabed94dc908075e3ba32b1906f4292d5db64', '7d56c60097f7958fe7c4c7db0d7e12de97ed69e281be3cfaa74fdcd537475ef3', '810efd84827a881454a1871f5d4f15a8b238994c8d644d941f607a3da72ffccb', '9886d6385f561b38f5a9c3a4c8908d3ca23b34f33459e25c0ed33c76b2085306', '9ed2eece4567044963cf3bf41c96a3212b75904b67683cb557f7b3c9f3830d8a', 'a283cf2e50cac76126228abc082bbbc69366b1b04cd951e18ff2a7be6c7168f6', 'a6711b629eb396c64d2243bfb10db532b454ec57efda0506539bfecb7a8a498f', 'd8ea152645a5555e59d8b96094b2cf943afe275aa10ec567322a7fcff1993189']
CONTEXT_REQUIRED = {'02d7977b', '27a39157', '6bfad0ab', '9ed2eece'}
COUNTS = [1, 1, 1, 1, 2, 2, 5, 3, 4, 2, 2, 1]
EXPECTED = [('officer_changed', 'male_liquidator_origin_changed', {'origin': 'Belmont-sur-Lausanne'}), ('seat_changed', 'branch_seat_after_municipality_merger', {'branch_uid': 'CHE-289.928.703', 'previous_place': 'Corcelles-Cormondrèche', 'place': 'Neuchâtel'}), ('officer_changed', 'foundation_member_joint_president_or_vice', {'signing_restriction': 'avec le président ou le vice-président'}), ('company_name_changed', 'company_name_supplement_corrected', {'entry': '273', 'company_name': 'NEUSTRAG AG Bauunternehmung'}), ('ownership_changed', 'corporate_associate_transfer_new_president', {'count': '180', 'remaining': '20', 'country': 'PRT'}), ('statutes_changed', None, {'date': '2021-01-05', 'previous_date': '2020-01-05'}), ('officer_changed', 'german_management_members_french_xml', {'known_as': 'Christoph'}), ('officer_changed', 'two_signatories_board_or_named_partner', {'partner': 'Thierry Gabriel Junod'}), ('officer_changed', 'manager_presidency_and_appointments_individual', {'name1': 'Newton Christopher'}), ('organization_changed', 'foundation_board_suspension_lifted', {'decision_date': '16.12.2020', 'appointment_date': '30.09.2020'}), ('officer_changed', 'president_residence_and_director_manager', {'country': 'France'}), ('branch_changed', 'branch_registry_id_replaced_by_uid', {'previous_registry_id': 'CH-621-9007033-1', 'branch_uid': 'CHE-439.624.188'})]

@lru_cache(None)
def captured(digest):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser401_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser401_leftovers', capture):
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
    added, rest = extract_parser401_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 411
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS[SUPPLIED_SHA256.index(digest)] and not rest
    with patch.object(parser, 'extract_parser401_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('digest,expected', list(zip(SUPPLIED_SHA256, EXPECTED)))
def test_explicit_meaning(digest, expected):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser401_leftovers(*args, **kwargs)
    kind, action, fields = expected
    assert not rest and events[0].event_type == kind
    if action is not None:
        assert events[0].rule_id == f'{args[1]}.text.{action}.v1'
        assert events[0].payload['action'] == action
    else:
        assert events[0].rule_id == 'de.text.statutes_date_corrected_comma.v1'
        assert events[1].event_type == 'capital_changed'
        assert events[1].payload['claim'] == "2'080'280.00"
        assert events[1].payload['issued_shares'] == [{'count': 1978712, 'nominal': '1.00', 'currency': 'CHF', 'kind': 'Namenaktien'}]
    assert {key: events[0].payload[key] for key in fields} == fields
@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_unknown_suffix_language_and_invalid_dates(digest):
    _, (args, kwargs) = captured(digest)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser401_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser401_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser401_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_missing_optional_metadata_and_source(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser401_leftovers(*args[:4], None, None, None, **kwargs)
    assert events and not rest
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    events, rest = extract_parser401_leftovers(*args)
    if digest[:8] in CONTEXT_REQUIRED:
        assert not events and rest == args[0]
    else:
        assert events and not rest


def test_old_event_without_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event


@pytest.mark.parametrize('index', [0, 2, 4, 8])
def test_source_evidence_required_and_consistent(index):
    _, (args, kwargs) = captured(SUPPLIED_SHA256[index])
    assert extract_parser401_leftovers(*args, source_text='Unrelated.') == ([], args[0])
    assert extract_parser401_leftovers(*args, source_text=kwargs['source_text'].replace('signature', 'UNKNOWN')) == ([], args[0])


def test_person_roles_signing_and_residences():
    def events(index):
        _, (args, kwargs) = captured(SUPPLIED_SHA256[index])
        return extract_parser401_leftovers(*args, **kwargs)[0]
    liquidator = events(0)[0]
    assert liquidator.role == 'liquidateur' and liquidator.signing == 'Einzelunterschrift'
    assert liquidator.payload['place'] is None
    officers = events(6)
    assert [e.payload['known_as'] for e in officers] == ['Christoph', None, 'Céline', 'Jenny', None]
    assert all(e.role == 'Mitglied der Geschäftsleitung' and e.signing == 'Kollektivunterschrift zu zweien' for e in officers)
    assert officers[2].payload['nationality'] == 'französische Staatsangehörige'
    signers = events(7)
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in signers)
    assert signers[2].payload['restriction_removed'] is True
    assert 'signing_restriction' not in signers[2].payload
    managers = events(8)
    assert [e.role for e in managers] == ['gérant président', 'gérant', 'gérant', 'gérant']
    assert all(e.signing == 'Einzelunterschrift' for e in managers)
    assert [e.payload['place'] for e in managers] == [None, None, 'Bassins', 'Genève']
    president, director = events(10)
    assert president.payload['place'] == "Saint-Cyr-au-Mont-d'Or"
    assert director.payload['place'] is None and director.role == 'directeur, gérant'
    assert director.payload['country'] is None
    assert president.signing is None and director.signing is None


@pytest.mark.parametrize('version,text,language,source', [
    (204, "Bei der ordentlichen Kapitalerhöhung vom 05.01.2021 werden Forderungen in der Höhe von CHF 100.00 verrechnet, wofür 100 Namenaktien zu CHF 1.00 ausgegeben werden", 'de', ''),
    (103, 'Die Statuten datieren vom 05.01.2021, nicht vom 05.01.2020', 'de', ''),
    (161, 'Nouveau membre du conseil de fondation avec le président ou le vice-président: Exemple Anne, de et à Lausanne', 'fr', ''),
    (297, 'Exemple Anne, maintenant de Lausanne, est nommée liquidatrice avec signature individuelle', 'fr', 'Exemple Anne, maintenant de Lausanne, est nommée liquidatrice avec signature individuelle.'),
    (398, "Le siège de la succursale de Lausanne, dont le no d'identification des entreprises est (CHE-123.456.789), devient Genève", 'fr', ''),
    (62, 'Neu eingetragene Personen: Exemple Anne, von Bern, in Bern, Mitglied der Geschäftsleitung, Kollektivunterschrift zu zweien', 'fr', ''),
    (93, "L'identification de la succursale à Lausanne, est maintenant (CHE-123.456.789). et à Genève (CHE-987.654.321)", 'fr', ''),
])
def test_legacy_rule_ownership_in_isolation(version, text, language, source):
    import importlib
    import inspect
    module = importlib.import_module(f'shab_analyzer.parser{version}')
    old = getattr(module, f'extract_parser{version}_leftovers')
    args = text, language, 'p', '', None, None, None
    kwargs = {'source_text': source} if 'source_text' in inspect.signature(old).parameters else {}
    events, rest = old(*args, **kwargs)
    assert events and not rest.strip()
    assert extract_parser401_leftovers(*args, source_text=source) == ([], text)


def test_statutes_prefix_payload_delegated_unchanged():
    from shab_analyzer.parser103 import extract_parser103_leftovers
    _, (args, kwargs) = captured(SUPPLIED_SHA256[5])
    prefix = args[0].partition('. Bei der ordentlichen Kapitalerhöhung')[0]
    expected, rest = extract_parser103_leftovers(prefix, *args[1:])
    events, remaining = extract_parser401_leftovers(*args, **kwargs)
    assert not rest and not remaining
    assert events[:1] == expected
    from shab_analyzer.parser204 import extract_parser204_leftovers
    capital = 'Bei der ordentlichen Kapitalerhöhung' + args[0].partition('. Bei der ordentlichen Kapitalerhöhung')[2]
    issued, rest = extract_parser204_leftovers(capital[:-1], *args[1:])
    assert not rest.strip() and events[1:] == issued


@pytest.mark.parametrize('stem', [
    '7be44b47', '095f22f3', '21ebc82b', '0a10e470', '0ef3066f',
])
def test_existing_fixture_unchanged(stem):
    import shab_analyzer.parse as parser
    paths = list(FIXTURES.glob(stem + '*.xml'))
    assert len(paths) == 1
    result = parse_publication_xml(paths[0])
    with patch.object(parser, 'extract_parser401_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(paths[0])
