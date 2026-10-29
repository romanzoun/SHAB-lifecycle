import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser431 import extract_parser431_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['062ef26ef7b7792baf301bb423367409b6bc126cdf89f94e769fe35394ff4c98', '26e8f32a217a928c5590fc08a9ee3aa1fa636ed317f9f7f126b2e667cf08a1aa', '2ef49bef343bd717b761514fc4cd6450bb8ac359eca49a34712fee90957df49d', '377699085a770aed7f1cc98b9c25e64b9bcf31bc4c6826242d2d788a6f194140', '384c2df3999d3936131f04916e6a38ac876aa6594f1c11fa88657884af3e1b8d', '38b7cbf6f482e428b75ad92bb5830669c4265fb94f84339752e3641e5edbecde', '5a105e0098fb163679d2709be1fc7c93334961f6484e81f415199ce471db653d', '6b676f5b6f330055a09eeacb4e17aaa17b93dbbebba638c23e8449366caa222d', 'd0acb8fe743c16edddde552f8d1931a88504aee2004f577483f09861b7aea934', 'd8ee53a7643d9c7a694cef1665565bda23d1ebb383638e5c12ca5204b3e6acea', 'dec8e7f101da9285864f9a7c04f122a1bcb54deadb5b349d83892bae4b63143f', 'f9867736a70a775f74c8166b259e3be9e400cffe4fe3a83abfdae257956f77a0']
COUNTS = [2, 1, 1, 2, 0, 2, 1, 1, 1, 2, 1, 1]
NEW_CASES = [i for i, count in enumerate(COUNTS) if count]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser431_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser431_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(path)
    assert len(calls) == 1
    return result, old, calls[0]


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('index', NEW_CASES)
def test_complete_and_unchanged_old_payloads(index):
    result, old, (args, kwargs) = captured(index)
    added, rest = extract(*args, **kwargs)
    assert PARSER_VERSION == 431
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    assert len(added) == COUNTS[index] and rest == ''
    assert old.leftover_text == args[0]
    assert result.events == old.events + added
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('index', NEW_CASES)
def test_unknown_suffix_language_and_invalid_dates(index):
    _, _, (args, kwargs) = captured(index)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract(changed, *args[1:], **kwargs) == ([], changed)
    assert extract(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index', NEW_CASES)
def test_missing_optional_metadata_and_source(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args[:4], None, None, None, **kwargs)
    assert len(events) == COUNTS[index] and rest == ''
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    events, rest = extract(*args)
    assert len(events) == COUNTS[index] and rest == ''


def test_old_event_without_optional_attributes():
    event = Event('p', '', 'officer_changed', 'legacy.rule', payload={'name': 'Test Anna'})
    assert Event(**vars(event)) == event
    assert event.payload == {'name': 'Test Anna'}
    assert event.role is None and event.signing is None


@pytest.mark.parametrize('index', NEW_CASES)
def test_no_overlap_with_old_rules_even_in_isolation(index):
    # Exercise every historical extractor on the complete clause in isolation.
    import inspect
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(index)
    for name, old_extract in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser431_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name


def test_existing_board_formulation_is_left_to_historical_rules():
    from shab_analyzer.parser55 import extract_parser55_leftovers
    from shab_analyzer.parser165 import _FR_BOARD_MEMBERS
    result, old, (args, kwargs) = captured(4)
    assert _FR_BOARD_MEMBERS.fullmatch(args[0])
    historical_events, historical_rest = extract_parser55_leftovers(*args)
    assert historical_events and historical_rest != args[0]
    assert extract(*args, **kwargs) == ([], args[0])
    assert result == old
    assert result.status == 'PARTIALLY_PARSED'
    assert result.leftover_text == args[0]


@pytest.mark.parametrize('version,text,language', [
    (165, "Test Anne, président, et Test Paul, secrétaire, membres du conseil d'administration, signent désormais individuellement", 'fr'),
    (132, "Administration: Test Anne, nommée présidente, et Test Paul, de Genève, à Lausanne. Signature individuelle de la présidente ou collective à deux de l'autre membre du conseil d'administration", 'fr'),
    (200, "Test Anne, dont la procuration est éteinte, signe maintenant collectivement à deux", 'fr'),
    (58, "Mediante decisione della Pretura, Locarno, del 15.07.2019, la fondazione è stata soppressa. La cancellazione non può tuttavia essere effettuata mancando il consenso delle autorità fiscali federali e cantonali", 'it'),
    (300, "Das Zivilgericht hat mit Entscheid vom 11.02.2021 die Wiedereintragung der am 12.04.2013 gelöschten Gesellschaft in das Handelsregister angeordnet, Test Anna, von Basel, in Basel, als Liquidator eingesetzt und folgende Adresse als Liquidationsdomizil bestimmt: c/o Beispiel AG, Strasse 1, 4051 Basel", 'de'),
    (402, "Test Anne détient désormais 89 parts de CHF 100 par suite de cession de 6 parts de CHF 100 à Test Paul, de Genève, à Paris, FRA, nouvel associé pour 6 parts de CHF 100", 'fr'),
])
def test_related_old_rules_retain_payloads_and_input(version, text, language):
    import importlib
    old_extract = getattr(importlib.import_module(f'shab_analyzer.parser{version}'), f'extract_parser{version}_leftovers')
    args = text, language, 'p', '', None, None, None
    options = {'source_text': text + ' avec signature individuelle.'} if version == 402 else {}
    expected = old_extract(*args, **options)
    assert expected[0] and expected[1] == ''
    padded = '  ' + text + '  '
    assert extract(padded, *args[1:], **options) == ([], padded)
    assert old_extract(*args, **options) == expected


@pytest.mark.parametrize('index,kind,action', [
    (0, 'organization_changed', 'reinstatement_liquidator_liquidation_address'),
    (1, 'officer_changed', 'foundation_member_now_collective_signing'),
    (2, 'status_changed', 'bankruptcy_closed_by_decision'),
    (3, 'ownership_changed', 'share_transfer_new_associate_manager'),
    (5, 'officer_changed', 'board_members_and_directors_individual_signing'),
    (6, 'organization_changed', 'public_pension_institution_statutes_legal_basis_organization'),
    (7, 'organization_changed', 'two_liquidation_name_translations'),
    (8, 'status_changed', 'foundation_suppressed_tax_consent_pending'),
    (9, 'officer_changed', 'president_secretary_asymmetric_signing'),
    (10, 'officer_changed', 'domicile_abroad_without_comma'),
    (11, 'ownership_changed', 'associate_transfer_foreign_unsigned_buyer'),
])
def test_evidenced_semantics(index, kind, action):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    assert rest == ''
    assert events[0].event_type == kind
    assert events[0].rule_id == f'{args[1]}.text.{action}.v1'
    assert events[0].payload['action'] == action
    p = events[0].payload
    if index == 0:
        assert p['reinstated'] is True
        assert events[1].role == 'Liquidator' and events[1].signing is None
    elif index == 1:
        assert events[0].role == 'membre du conseil de fondation'
        assert events[0].signing == 'Kollektivunterschrift zu zweien'
    elif index == 2:
        assert p['bankruptcy_closed'] is True and p['decision_date'] == '09.03.2021'
    elif index == 3:
        assert (p['remaining'], p['count'], p['nominal']) == ('67', '33', '200')
        assert events[1].role == 'associé-gérant' and events[1].signing is None
    elif index == 5:
        assert all(e.signing == 'Einzelunterschrift' and 'directeur' in e.role for e in events)
        assert 'président' in events[0].role and 'secrétaire' in events[1].role
    elif index == 6:
        assert (p['members'], p['insured_representatives'], p['employer_representatives']) == ('10', '5', '5')
        assert 'RL 174.100' in p['legal_basis'] and p['previous_organization'] == 'organo supremo di 10 membri'
        assert p['capital_note'] and p['previous_capital'] and p['statutes_regulation']
    elif index == 7:
        assert p['german_name'].endswith('in Liquidation') and p['english_name'].endswith('in liquidation')
    elif index == 8:
        assert p['suppressed'] is True and p['deletion_pending'] is True
    elif index == 9:
        assert [(e.role, e.signing) for e in events] == [('présidente', 'Einzelunterschrift'), ('secrétaire', 'Kollektivunterschrift zu zweien')]
    elif index == 10:
        assert p['country'] == 'PRT' and p['place'] == 'Lisbonne'
        assert events[0].role is None and events[0].signing is None
    elif index == 11:
        assert (p['remaining'], p['count'], p['nominal']) == ('89', '6', '100')
        assert p['buyer_signing'] == 'ohne Zeichnungsberechtigung' and p['country'] == 'USA'
