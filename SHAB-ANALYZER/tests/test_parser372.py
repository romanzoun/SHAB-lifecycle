import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser372 import extract_parser372_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('01af6481', 'de.text.liquidation_address_changed_with_previous.v1', 1), ('165b7d48', 'fr.text.three_foundation_members_shared_place.v1', 3), ('31970459', 'fr.text.presiding_manager_share_transfer_new_joint_manager.v1', 3), ('492f86e8', 'fr.text.two_new_committee_members_foreign_places.v1', 2), ('70c07974', 'fr.text.female_associate_joint_signing_married_name.v1', 1), ('78b516a5', 'de.text.statutes_date_corrected_without_richtig.v1', 1), ('84fd21eb', 'de.text.head_office_identifier_non_publishable_statutes.v1', 1), ('8b7bb042', 'fr.text.associate_manager_residence_supplemented.v1', 1), ('add76c1b', 'fr.text.registered_share_split_dividend_preference.v1', 1), ('e35ee63e', 'fr.text.company_address_corrected_exact_notice.v1', 1), ('e8fa09f6', 'fr.text.two_sellers_two_recipients_share_balances.v1', 1), ('f12bfe3c', 'fr.text.named_branch_registered_notice_comma.v1', 1)]
SUPPLIED_SHA256 = {'01af6481': '01af64811dfe4fba3b0b85880052c64b02ddfb0c26ad4297b63214b24d119d8e', '165b7d48': '165b7d488de71cda7344c5fd1e7ea38385e37db91412acf7b9532e82df1df466', '31970459': '319704590d6ebd3472a85a177ca38d3cea1a89bc74c8bd7aeb4a62207b27d133', '492f86e8': '492f86e8c9f21974a90722fd7fd1898304c335fdd062b86e09c77defd9758721', '70c07974': '70c079741e8c7ac01ad5a2e1d84158249ace819e4614f8c93518a8b3ac07639b', '78b516a5': '78b516a58a9fc9d6197d95f5857c0746ee5d5898b271b6380750ae30e38dfc0b', '84fd21eb': '84fd21eb547f2f8391c7bf8548f12c7eef92f2c888f805927d9d94f0cf5d760d', '8b7bb042': '8b7bb04227402f03668a0e34f6b6ebaceff3c51dad9cbe3df0b392876be43582', 'add76c1b': 'add76c1bf29e90b92c369697eb0b10f373455d52070e3b6d537ecf536556273f', 'e35ee63e': 'e35ee63e5667be46e9ce771b22ee12ee319eab5e9902f2be8a43a9ac5e4ae1c1', 'e8fa09f6': 'e8fa09f603d459304d92e17dc5793da2088e73a1c1ca49a7c2da3e724ff15036', 'f12bfe3c': 'f12bfe3cb25d2bcb241e35f0218746b1c3bd896fafcf35f9c5ff6e175fa17784'}

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
        return extract_parser372_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser372_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser372_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 443
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser372_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser372_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser372_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_bytes_match_supplied_samples(prefix, rule, count):
    supplied_sha256 = SUPPLIED_SHA256
    fixture = path(prefix)
    assert fixture.stem == supplied_sha256[prefix]
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == supplied_sha256[prefix]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_dates_and_optional_source(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    for date in set(re.findall(r'\d{2}[-.]\d{2}[-.]\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser372_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser372_leftovers(*args)
    if prefix in ('165b7d48', '31970459', '492f86e8', 'add76c1b'):
        assert not events and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e





@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_optional_metadata_absent(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser372_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]


@pytest.mark.parametrize('prefix', ['165b7d48', '31970459', '492f86e8', 'add76c1b'])
def test_fragment_requires_matching_source_and_valid_source_dates(prefix):
    _, (args, kwargs) = captured(prefix)
    assert extract_parser372_leftovers(*args, source_text='Unrelated source') == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', kwargs['source_text'])):
        if date in selected(prefix)[0].payload.values():
            assert extract_parser372_leftovers(*args, source_text=kwargs['source_text'].replace(date, '31.02.2020')) == ([], args[0])


def test_payload_semantics():
    address = selected('01af6481')[0].payload
    assert (address['postal_code'], address['locality']) == ('6821', 'Rovio')
    assert '6815 Melide' in address['previous_address']
    foundation = selected('165b7d48')
    assert [e.payload['place'] for e in foundation] == ['Neuchâtel', 'Neuchâtel', 'Saint-Blaise']
    assert all(e.role == 'Mitglied des Stiftungsrates' and e.signing == 'Kollektivunterschrift zu zweien' for e in foundation)
    transfer = selected('31970459')
    assert (transfer[0].payload['transferred'], transfer[0].payload['before'], transfer[0].payload['remaining']) == ('8', '20', '12')
    assert transfer[1].role == 'Präsident der Geschäftsführung'
    assert transfer[1].signing is None
    assert transfer[2].signing == 'Kollektivunterschrift zu zweien'
    committee = selected('492f86e8')
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in committee)
    assert [e.payload['country1'] for e in committee] == ['Royaume-Uni'] * 2
    assert selected('70c07974')[0].payload['name'] == 'Le Maignan de Kerangat ép. Comerro Anaïs'
    assert selected('70c07974')[0].signing == 'Kollektivunterschrift zu zweien'
    assert selected('78b516a5')[0].payload['statutes_date'] == '18.05.2019'
    assert selected('78b516a5')[0].payload['incorrect_statutes_date'] == '18.05.2020'
    assert selected('84fd21eb')[0].payload['head_office_id'] == 'HRB 142124 B'
    assert selected('8b7bb042')[0].payload['place'] == 'Fribourg'
    capital = selected('add76c1b')[0]
    assert capital.event_type == 'capital_changed'
    assert capital.payload['capital'] == "111'410"
    assert capital.payload['statutes_date'] == '25.09.2020'
    assert capital.payload['fully_paid'] is True and capital.payload['transfer_restricted'] is True
    assert capital.payload['share_classes'] == [
        {'count': "2'228'200", 'nominal': '0.01', 'kind': 'registered', 'dividend_preferred': False},
        {'count': "8'912'800", 'nominal': '0.01', 'kind': 'registered', 'dividend_preferred': True},
    ]
    corrected = selected('e35ee63e')[0].payload
    assert 'Pt. Maraîches 132' in corrected['address'] and 'Pet. Maîches 132' in corrected['previous_address']
    balances = selected('e8fa09f6')[0].payload
    assert [balances[key] for key in ('count1', 'count2', 'count3', 'remaining1', 'remaining2', 'total1', 'total2')] == ['25', '4', '13', '80', '15', '36', '78']
    assert selected('f12bfe3c')[0].payload['branch_uid'] == 'CHE-161.365.483'
    assert selected('f12bfe3c')[0].payload['place'] == 'Payerne'


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old


@pytest.mark.parametrize('text', ['', 'Unsupported clause', '   '])
def test_unknown_residuals(text):
    assert extract_parser372_leftovers(text, 'fr', 'fixture', '', None, None, None) == ([], text.strip())


@pytest.mark.parametrize('prefix', ['0b2d3eb7', '1007be5f', '3131ea15', '4848676d', '5c313c51', '7858766f', '965fa26d', 'a5b7a664', 'c686757b', 'dd72c018', 'e0b4d8c6', 'e14df61f'])
def test_parser371_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser372_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for event in baseline.events:
        assert Event(**vars(event)) == event


@pytest.mark.parametrize('prefix', ['01af6481', 'f12bfe3c'])
def test_old_patterns_keep_rule_ownership_even_in_isolation(prefix):
    from shab_analyzer.parser132 import _DE_LIQUIDATION_ADDRESS, extract_parser132_leftovers
    from shab_analyzer.parser159 import _FR_BRANCH_REGISTERED_AT, extract_parser159_leftovers
    _, (args, kwargs) = captured(prefix)
    if prefix == '01af6481':
        # The older pattern also accepts a history without internal dots.
        text = args[0].replace('Avv. ', '').replace('G. ', '').replace('Melide.]', 'Melide]')
        pattern, old = _DE_LIQUIDATION_ADDRESS, extract_parser132_leftovers
    else:
        text = args[0].replace('), au registre', ') au registre')
        pattern, old = _FR_BRANCH_REGISTERED_AT, extract_parser159_leftovers
    assert pattern.fullmatch(text)
    assert old(text, *args[1:])[0]
    assert extract_parser372_leftovers(text, *args[1:], **kwargs) == ([], text)


@pytest.mark.parametrize('prefix,replacements', [
    ('31970459', [('8 de ses 20', '9 de ses 20')]),
    ('add76c1b', [("111'410", "111'411")]),
])
def test_inconsistent_share_amounts_rejected(prefix, replacements):
    _, (args, kwargs) = captured(prefix)
    text, source = args[0], kwargs['source_text']
    for before, after in replacements:
        text, source = text.replace(before, after), source.replace(before, after)
    assert extract_parser372_leftovers(text, *args[1:], source_text=source) == ([], text)


@pytest.mark.parametrize('version,prefix', [
    (283, '3b7614d1'),
    (319, '94cd9231'),
    (319, '7c912f61'),
    (371, 'e0b4d8c6'),
    (371, '7858766f'),
])
def test_existing_rule_inputs_rejected_with_earlier_rule_disabled(version, prefix):
    import shab_analyzer.parse as parser
    name = f'extract_parser{version}_leftovers'
    original = getattr(parser, name)
    calls = []

    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return original(*args, **kwargs)

    fixture = path(prefix)
    with patch.object(parser, name, capture):
        actual = parse_publication_xml(fixture)
    assert len(calls) == 1
    args, kwargs = calls[0]
    assert original(*args, **kwargs)[0]
    # Simulate the residual seen by parser372 when the owning rule is disabled.
    assert extract_parser372_leftovers(*args, **kwargs) == ([], args[0])
    with patch.object(parser, 'extract_parser372_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert actual == baseline
