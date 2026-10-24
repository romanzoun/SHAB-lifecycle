import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser329 import extract_parser329_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('09f90c1f', 'fr.text.single_share_transfer_unsigned_associate.v1', 2),
    ('28528abc', 'fr.text.share_transfer_collective_managers.v1', 3),
    ('3e71da53', 'de.text.liquidator_departed_powers_revoked.v1', 2),
    ('762ea6e8', 'fr.text.bankruptcy_appeal_rejected_effective.v1', 1),
    ('7f11be01', 'fr.text.registered_share_count_corrected.v1', 1),
    ('950a0991', 'fr.text.board_members_become_liquidators.v1', 4),
    ('9c5c898c', 'fr.text.share_transfer_new_collective_associate.v1', 2),
    ('bb4542dd', 'fr.text.two_managers_sign_individually.v1', 2),
    ('d518eb02', 'fr.text.share_transfer_four_existing_associates.v1', 1),
    ('f63aa392', 'de.text.company_reinstated_summary_bankruptcy_reopened.v1', 1),
    ('f663e109', 'fr.text.joint_procuration_excluding_each_other.v1', 2),
    ('f8fc2919', 'de.text.association_asset_transfer_cash_consideration.v1', 1),
]


def path(prefix):
    paths = list(FIXTURES.glob(prefix + '*.xml'))
    assert len(paths) == 1
    return paths[0]


@lru_cache(None)
def captured(prefix):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser329_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser329_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser329_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 386
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser329_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser329_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser329_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]



@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_bytes_match_supplied_samples(prefix, rule, count):
    supplied_sha256 = {
        '09f90c1f': '09f90c1ffe9342c36b034d4ae6144c2325aff4b52ad4005703fd789bcc01d3a9',
        '28528abc': '28528abc2165a90899bbb77ee29ff6d9a624ec707ecf1c2518131620d37a2ed4',
        '3e71da53': '3e71da537b8d6bb28d370a868e896c78ee0c374339b3ac0fd4510baa61e6eb8c',
        '762ea6e8': '762ea6e87c3d5b9220718ed0ba419c209cd4b5599272a103b8197f272a506ba7',
        '7f11be01': '7f11be01c0c0adbbdc7566857a65ffa38d67a18dbb837c53101e3c1e9599729e',
        '950a0991': '950a0991c364aef656464cde867aa049360fb274db8348b13f0fa58da36e8fc3',
        '9c5c898c': '9c5c898ce56a4fe0a460290fbe1b23d7c8de18648ba8593952f732adccf0a492',
        'bb4542dd': 'bb4542dd4f5a79ae0efbdbe6aaaa851fbb817eb037d95a2dcac579f18b4a543f',
        'd518eb02': 'd518eb02e93b6f6100cda037df8db041f664919afc377cc3c25652fd99332f9b',
        'f63aa392': 'f63aa392aa0a685f2a852da0fc6b7d0bf198138eec0ff788eed6edfad1c3d3a0',
        'f663e109': 'f663e10967e33b9983bfaf6b6d6b790c431185b5f798890e1cd31c9ebb35335d',
        'f8fc2919': 'f8fc29192c6c81d33582d4ad93c15f6d59f4da232337b90be72ef69b4f432a89',
    }
    fixture = path(prefix)
    assert fixture.stem == supplied_sha256[prefix]
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == supplied_sha256[prefix]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_dates_and_optional_source(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser329_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser329_leftovers(*args)
    if prefix in {'3e71da53', '9c5c898c'}:
        assert not events and leftover == args[0]
        for source in ['', kwargs['source_text'] + ' UNKNOWN_SUFFIX']:
            events, leftover = extract_parser329_leftovers(*args, source_text=source)
            assert not events and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e


@pytest.mark.parametrize('prefix', [
    '03dcc069', '315da231', '353d9e29', '693c452c', '7c27565a', '8889623a',
    'a5f4be23', 'bbf607eb', 'c332722f', 'ce010fcd', 'cfbe1db2', 'f0fd9d83',
    '518fef8d', '5404cc5f', '54125ed4', '6d18ed72', '6d50c77a', '7a6515f3',
    '930507a1', 'a16a5540', 'a564e09d', 'b384c365', 'cf527290', 'ecba5198',
    '1cf200d1', 'c9cb541c', 'e3c5c5cd', '94b72118-d3cb-46f4-8cf3-8d526586b9f2',
])
def test_previous_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser329_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old


def test_payload_semantics():
    transfer, associate = selected('09f90c1f')
    assert transfer.event_type == 'ownership_changed'
    assert transfer.payload['transferred'] == '1'
    assert transfer.payload['remaining'] == '19'
    assert associate.signing == 'ohne Zeichnungsberechtigung'
    assert associate.payload['without_signing'] is True
    transfer, president, manager = selected('28528abc')
    assert transfer.payload['transferred'] == '100' and transfer.payload['before'] == '200'
    assert president.role == 'Gesellschafterin, Geschäftsführerin, Präsidentin'
    assert manager.role == 'Gesellschafter, Geschäftsführer'
    assert president.signing == manager.signing == 'Kollektivunterschrift zu zweien'
    departed, appointed = selected('3e71da53')
    assert departed.payload['powers_removed'] is True
    assert departed.signing is None and appointed.signing == 'Einzelunterschrift'
    assert departed.payload['name'] != appointed.payload['name']
    assert departed.payload['place'] is None and appointed.payload['place'] == 'Tannay'
    assert appointed.role == departed.role == 'Liquidator'
    assert appointed.payload['name'].endswith('J.')
    bankruptcy = selected('762ea6e8')[0]
    assert bankruptcy.event_type == 'status_changed'
    assert bankruptcy.payload['bankruptcy_opened'] is True
    assert bankruptcy.payload['appeal_rejected'] is True
    assert bankruptcy.payload['effective_time'] == '12:00'
    corrected = selected('7f11be01')[0]
    assert corrected.event_type == 'capital_changed' and corrected.payload['corrected'] is True
    assert corrected.payload['count'] == "10'000'000"
    assert corrected.payload['previous_count'] == "10'000"
    assert corrected.payload['capital'] == "100'000" and corrected.payload['nominal'] == '0.01'
    *liquidators, restrictions = selected('950a0991')
    assert len(liquidators) == 3
    assert all('Liquidator' in e.role and e.signing == 'Kollektivunterschrift zu zweien' for e in liquidators)
    assert 'Verwaltungsratspräsident' in liquidators[0].role
    assert restrictions.payload['restrictions_lifted'] is True
    transfer, associate = selected('9c5c898c')
    assert transfer.payload['remaining'] == '180'
    assert transfer.payload['transferred'] == transfer.payload['buyer_count'] == '20'
    assert associate.signing == 'Kollektivunterschrift zu zweien'
    assert all(e.event_type == 'signing_authority_changed' and e.role == 'Geschäftsführer' and e.signing == 'Einzelunterschrift' for e in selected('bb4542dd'))
    transfer = selected('d518eb02')[0]
    assert transfer.payload['transferred'] == '4'
    assert transfer.payload['buyer_count'] == '3' and transfer.payload['remaining'] == '8'
    assert len({transfer.payload[f'buyer{i}'] for i in (1, 2, 3, 4)}) == 4
    reopened = selected('f63aa392')[0]
    assert reopened.event_type == 'status_changed'
    assert all(reopened.payload[k] is True for k in ['reinstated', 'bankruptcy_reopened', 'summary_proceedings'])
    assert reopened.payload['effective_time'] == '09.00'
    procurations = selected('f663e109')
    for e, other in zip(procurations, reversed(procurations)):
        assert e.signing == 'Kollektivprokura zu zweien'
        assert e.payload['excluded_signing_partner'] == other.payload['name']
        assert e.payload['signing_restriction'] == 'toutefois pas entre eux'
    assets = selected('f8fc2919')[0]
    assert assets.event_type == 'ownership_changed'
    assert assets.payload['assets'] == "75'000.00"
    assert assets.payload['liabilities'] == '0.00'
    assert assets.payload['consideration'] == "120'000.00"
    assert assets.payload['currency'] == 'CHF'


@pytest.mark.parametrize('prefix,old,new', [
    ('09f90c1f', 'sans signature sociale', 'avec signature sociale'),
    ('28528abc', 'collectivement à deux', 'individuellement'),
    ('3e71da53', "n'est plus liquidateur", 'est liquidateur'),
    ('762ea6e8', 'a rejeté', 'a admis'),
    ('7f11be01', 'est rectifiée', 'est confirmée'),
    ('950a0991', 'sont levées', 'sont maintenues'),
    ('9c5c898c', 'est désormais titulaire', "n'est plus titulaire"),
    ('bb4542dd', 'individuellement', 'collectivement à deux'),
    ('d518eb02', 'chacun titulaire', 'ensemble titulaires'),
    ('f63aa392', 'Wiedereröffnung', 'Einstellung'),
    ('f663e109', 'toutefois pas entre eux', 'y compris entre eux'),
    ('f8fc2919', 'Der Verein überträgt', 'Der Verein übernimmt'),
])
def test_unsupported_meanings_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    events, leftover = extract_parser329_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix', ['3e71da53', '9c5c898c'])
def test_source_signing_must_match(prefix):
    _, (args, kwargs) = captured(prefix)
    changed = kwargs['source_text'].replace('signature individuelle', 'signature collective à deux').replace('avec signature collective à deux', 'sans signature')
    assert changed != kwargs['source_text']
    events, leftover = extract_parser329_leftovers(*args, source_text=changed)
    assert not events and leftover == args[0]


@pytest.mark.parametrize('prefix,old,new', [
    ('28528abc', 'a cédé 100 de ses 200', 'a cédé 201 de ses 200'),
    ('9c5c898c', 'pour 20 parts', 'pour 21 parts'),
    ('762ea6e8', '12:00', '24:00'),
    ('f63aa392', '09.00 Uhr', '09.60 Uhr'),
])
def test_inconsistent_counts_and_invalid_times_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    events, leftover = extract_parser329_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed
