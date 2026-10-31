import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser430 import extract_parser430_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['02953207a6c28c9d18a936d113d84c1ecfda9398624d6d14d68dad41a13e8bf2', '17e45571812f0e16893ec8cd4e30c411010c1dc528a16758d54157050b3d670d', '24b60ea8dbb192b8e6d14c06ac870df02093a8f3630fe05445b445856e23d42e', '32f52df1bd5874b04e31c5de3c2e03c1cf896f85b3d9a7eeb7f8372dce13614c', '59bf7a7a2589d68b6ed452528006e6251c2fd7f5f8b097f3c923a421236021b7', '6a28da6a2f13d760894c20a9070e9b36503a57686b50e1014b11ae6bdb13997e', '7518770c7d1289608c5e6e030bbf9230a1795dde074ec2b47a835bcb4b2178c0', '8578b6be95a090af79df1d6e1c795649f23a897b6f4567acc253adc7897a3b5a', 'a9f078edd5657e4f5e4699e0e369ff1b2ebf1e3d37f7cfa2cb208c990788f4b4', 'd8311e240f9934b35f729bece4cf67adec86a190a15115dec47a22bcc448e07a', 'da6ed9ecfda62fc7fb343251394ef84b4817926a1df656d63865344e6de9bf90', 'db95d6afe4ddb5dd949e6984808b9b031e8bfdaa46464a79c20e12a662de3d96']
COUNTS = [1] * 12


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser430_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser430_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(path)
    assert len(calls) == 1
    return result, old, calls[0]


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('index', range(12))
def test_complete_and_unchanged_old_payloads(index):
    result, old, (args, kwargs) = captured(index)
    added, rest = extract(*args, **kwargs)
    assert PARSER_VERSION == 445
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    assert len(added) == COUNTS[index] and rest == ''
    assert old.leftover_text == args[0]
    assert result.events == old.events + added
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('index', range(12))
def test_unknown_suffix_language_and_invalid_dates(index):
    _, _, (args, kwargs) = captured(index)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract(changed, *args[1:], **kwargs) == ([], changed)
    assert extract(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index', range(12))
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


@pytest.mark.parametrize('index', range(12))
def test_no_overlap_with_old_rules_even_in_isolation(index):
    # Exercise every historical extractor on the complete clause in isolation.
    import inspect
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(index)
    for name, old_extract in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser430_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name



@pytest.mark.parametrize('index,kind,action', [
    (0, 'status_changed', 'definitive_moratorium_extended_numeric_dates'),
    (1, 'officer_changed', 'director_continues_signing_unrestricted'),
    (2, 'status_changed', 'provisional_moratorium_lifted_restructuring'),
    (3, 'assets_transferred', 'asset_transfer_usd_cash_consideration'),
    (4, 'ownership_changed', 'share_transfer_new_associate_without_origin'),
    (5, 'address_changed', 'additional_address_plural_typo'),
    (6, 'organization_changed', 'erroneous_audit_waiver_deleted'),
    (7, 'ownership_changed', 'two_associates_transfer_respective_shares'),
    (8, 'status_changed', 'definitive_moratorium_replaces_provisional_duration'),
    (9, 'organization_changed', 'publication_organ_full_french_name'),
    (10, 'organization_changed', 'original_statutes_date_corrected_brackets'),
    (11, 'officer_changed', 'committee_secretary_with_president_or_deputy'),
])
def test_evidenced_payload_semantics(index, kind, action):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    assert rest == '' and len(events) == 1
    e = events[0]
    assert e.event_type == kind
    assert e.rule_id == f'{args[1]}.text.{action}.v1'
    assert e.payload['action'] == action
    p = e.payload
    if index == 0:
        assert p['extended'] is True and p['until_date'] == '01.09.2021'
    elif index == 1:
        assert e.role == 'directeur' and e.signing == 'Kollektivunterschrift zu zweien'
        assert p['signing_restriction'] == 'sans autre restriction'
    elif index == 2:
        assert p['lifted'] is True and p['reason'] == 'Sanierung'
    elif index == 3:
        assert p['currency'] == 'USD'
        assert (p['assets'], p['liabilities'], p['consideration']) == ("4'841'665.71", '0.00', "4'841'665.71")
    elif index == 4:
        assert (p['before'], p['count'], p['remaining']) == ('500', '300', '200')
        assert 'buyer_signing' not in p and e.signing is None
    elif index == 5:
        assert p['postal_code'] == '2000' and p['place'] == 'Neuchâtel'
    elif index == 6:
        assert p['corrected'] is True and p['audit_waiver_deleted'] is True
        assert p['auditor_registered'] is True
    elif index == 7:
        assert (p['each'], p['before'], p['buyer_count'], p['remaining']) == ('10', '100', '20', '90')
        assert p['buyer_signing'] == 'ohne Zeichnungsberechtigung'
    elif index == 8:
        assert p['definitive'] is True and p['months'] == '6' and p['previous_months'] == '3'
    elif index == 9:
        assert p['publication_organ'] == 'Feuille officielle suisse du commerce'
    elif index == 10:
        assert p['corrected'] is True
        assert (p['statutes_date'], p['previous_statutes_date']) == ('14.06.2010', '14.06.2000')
    elif index == 11:
        assert e.role == 'secrétaire' and e.signing is None
        assert p['signing_restriction'] == 'avec la présidente ou la vice-présidente'


@pytest.mark.parametrize('version,text,language', [
    (355, "Par prononcé rendu le 3 septembre 2020, le président du Tribunal de Lausanne a accordé à la société une prolongation du sursis concordataire définitif jusqu'au 1er mars 2021", 'fr'),
    (413, 'Exemple Anne cède 20 de ses 100 parts de CHF 100 à Exemple Marc, du Canada, à Genève, nouvel associé avec 20 parts de CHF 100, sans signature. Exemple Anne reste titulaire de 80 parts de CHF 100', 'fr'),
    (89, 'Nouveau membre du comité: Exemple Anne, de Genève, à Lausanne', 'fr'),
    (57, 'Mit Entscheid des Kreisgerichts Wil vom 09.03.2021 wurde eine definitive Nachlassstundung für die Dauer von 6 Monaten bis zum 09.09.2021 gewährt. [bisher: Mit Entscheid des Kreisgerichts Wil vom 15.12.2020 wurde eine provisorische Nachlassstundung für die Dauer von 3 Monaten bis zum 15.03.2021 gewährt.]', 'de'),
])
def test_related_old_rules_keep_ownership(version, text, language):
    import importlib
    old = getattr(importlib.import_module(f'shab_analyzer.parser{version}'), f'extract_parser{version}_leftovers')
    args = text, language, 'p', '', None, None, None
    expected = old(*args)
    assert expected[0] and expected[1] == ''
    padded = '  ' + text + '  '
    assert extract(padded, *args[1:]) == ([], padded)
    assert old(*args) == expected


def test_chf_asset_transfer_keeps_old_owner():
    import inspect
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(3)
    text = args[0].replace('USD', 'CHF')
    assert extract(text, *args[1:], **kwargs) == ([], text)
    owners = []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser430_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
        events, _ = old(text, *args[1:], **options)
        owners.extend(events)
    assert owners and all(e.event_type == 'assets_transferred' for e in owners)


def test_legacy_event_with_empty_payload_still_loads():
    event = Event('p', '', 'organization_changed', 'legacy.rule')
    assert event.payload == {}
    assert Event(**vars(event)) == event
    assert event.org_uid is None and event.role is None and event.signing is None
