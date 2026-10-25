import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser392 import extract_parser392_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = ['026181325a4f6f8ffd2f5bf9f54599f13f3ea990713636c05d80518856882bf0', '33650a043602b179acf12df15bba791cee9d62efbcdb60bce7e8b16515360562', '33ac3ba1b7f58b52fc57ffe183e1ac3376f596e0f79cec1e9135c8b236181b3d', '3771466ee5933606a755c6f2cc46e0db4e57c6e5ec2310df2314c4f18660f149', '4f922c227d5806729ebcf55ba5b097bf1010d2028cbce9cea59264cc22875d6e', '53db90beb1e6917f776ce78a51daae9487f84d70faf4bd1a578ad6e459ae122f', '8d01ed42329d6bffe7146dad3da8d0c7aa623b55b39d90e27288230a3419be57', 'a0eabcc98f96c94a80f5494126cbd276f794660cd1c0588958af18ae5161e98a', 'c84cacba3fe8d6ff002f7e7675506f3e6b4e1056a1a46f6d732b4fe7a6670e25', 'e661240c6f0ca0ce8d035e0d5defc9e40aec8b2856f8adee85f145c4270dad88', 'e88d29d2c8704b3083dbed48d08d80f63709f158ef246d692a7b9d681894346b', 'ef5a5505c8c54b41906039cc6ac176fb92bfa44a2d071990ebcad0c20b8dfada']
CONTEXT_REQUIRED = {'33650a04', 'ef5a5505'}
COUNTS = {'02618132': 3, '33650a04': 3, '33ac3ba1': 2, '3771466e': 2, '53db90be': 4, 'e88d29d2': 3, 'ef5a5505': 3}


@lru_cache(None)
def captured(digest):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser392_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser392_leftovers', capture):
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
    added, rest = extract_parser392_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 396
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS.get(digest[:8], 1) and not rest
    with patch.object(parser, 'extract_parser392_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_unknown_suffix_and_language_preserve_input(digest):
    _, (args, kwargs) = captured(digest)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser392_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser392_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_missing_optional_source_and_invalid_dates(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser392_leftovers(*args)
    if digest[:8] in CONTEXT_REQUIRED:
        assert not events and rest == args[0]
    else:
        assert len(events) == COUNTS.get(digest[:8], 1) and not rest
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser392_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_old_event_without_new_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event


EXPECTED_ACTIONS = [
    'president_share_transfer_new_manager_distinct_origin',
    'three_managers_liquidators_excluded_pair',
    'two_french_directors_separate_residences',
    'two_managers_single_share_transfer_unsigned_manager',
    'provisional_moratorium_extended_without_zum',
    'corporate_associate_renamed_moved_german_notice',
    'manager_share_transfer_existing_manager_plural_typo',
    'asset_transfer_registered_shares_credit_amount',
    'head_office_fully_paid_quota_capital',
    'cooperative_certificates_cancelled_credited_reserves',
    'three_administrators_us_residences_individual',
    'share_transfer_two_managers_assosies_typo',
]


@pytest.mark.parametrize('digest,action', list(zip(SUPPLIED_SHA256, EXPECTED_ACTIONS)))
def test_explicit_meaning(digest, action):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser392_leftovers(*args, **kwargs)
    assert not rest and events[0].payload['action'] == action
    assert events[0].rule_id == args[1] + '.text.' + action + '.v1'
    p = events[0].payload
    if digest.startswith('0261'):
        assert (p['remaining'], p['count'], p['nominal']) == ('100', '100', '100')
        assert (p['origin'], p['place']) == ('Choulex', 'Collonge-Bellerive')
        assert [e.role for e in events[1:]] == ['président', 'associé-gérant']
        assert all(e.signing is None for e in events[1:])
        assert events[1].payload['place'] is None
        assert events[2].payload['place'] == 'Collonge-Bellerive'
    elif digest.startswith('3365'):
        assert [e.role for e in events] == ['gérant et président, liquidateur', 'gérant, liquidateur', 'gérant et secrétaire, liquidateur']
        assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in events)
        assert all(e.payload['excluded_signing_pair'] == [p['name1'], p['name3']] for e in events)
    elif digest.startswith('33ac'):
        assert [e.payload['place'] for e in events] == ['Lausanne', 'Montperreux']
        assert all(e.role == 'directeur' and e.signing == 'Kollektivunterschrift zu zweien' for e in events)
        assert p['country_code'] == 'F'
    elif digest.startswith('3771'):
        assert (p['count'], p['buyer_count'], p['remaining']) == ('1', '2', '99')
        assert events[1].role == 'associée-gérante' and events[1].signing == 'ohne Zeichnungsberechtigung'
    elif digest.startswith('4f92'):
        assert events[0].event_type == 'status_changed'
        assert (p['decision_date'], p['duration'], p['until']) == ('11.11.2020', 'zwei', '18.01.2021')
    elif digest.startswith('53db'):
        assert (p['company_uid'], p['count'], p['nominal']) == ('CHE-106.014.113', '30', "1'000")
        assert p['previous_company'] != p['company']
        assert events[1].role == 'Geschäftsführer' and events[1].payload['place'] == 'Gibloux'
        assert events[1].signing == 'Einzelunterschrift'
        assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in events[2:])
    elif digest.startswith('8d01'):
        assert (p['count'], p['previous'], p['buyer_count'], p['remaining']) == ('40', '160', '80', '120')
    elif digest.startswith('a0ea'):
        assert (p['assets'], p['liabilities'], p['count'], p['nominal'], p['credit']) == ("8'744'554.00", "6'251'256.00", "1'400'000", '1.00', "351'298.00")
        assert p['recipient_uid'] == 'CHE-434.832.621'
    elif digest.startswith('c84c'):
        assert events[0].event_type == 'capital_changed'
        assert (p['head_office'], p['country'], p['capital'], p['currency'], p['scope'], p['fully_paid']) == ('Seregno', 'IT', "150'000.00", 'EUR', 'head_office', True)
    elif digest.startswith('e661'):
        assert events[0].event_type == 'capital_changed'
        assert (p['previous_nominal'], p['decision_date'], p['deed_date'], p['credited_to_reserves']) == ('100', '02.09.2020', '03.12.2020', True)
    elif digest.startswith('e88d'):
        assert [e.payload['place'] for e in events] == ['Acton, MA, USA', 'Houston, TX, USA', None]
        assert [e.role for e in events] == ['administrateur président', 'administrateur', 'administrateur']
        assert all(e.signing == 'Einzelunterschrift' for e in events)
        assert 'origin' not in events[2].payload
    elif digest.startswith('ef5a'):
        assert (p['remaining'], p['count'], p['nominal'], p['origin']) == ('10', '10', "1'000", 'Kosovo')
        assert [e.role for e in events[1:]] == ['associé-gérant et président', 'associé-gérant']
        assert all(e.signing == 'Einzelunterschrift' for e in events[1:])


def test_legacy_moratorium_retains_ownership():
    from shab_analyzer import parser213
    from shab_analyzer.parser392 import _LEGACY
    text = 'Mit Entscheid vom 11.11.2020 hat das Nachlassgericht die gewährte provisorische Nachlassstundung um zwei Monate bis zum 18.01.2021 verlängert'
    assert parser213._DE_PROVISIONAL_MORATORIUM_EXTENDED_MONTHS in _LEGACY
    assert parser213._DE_PROVISIONAL_MORATORIUM_EXTENDED_MONTHS.fullmatch(text)
    assert parser213.extract_parser213_leftovers(text, 'de', 'p', '', None, None, None)[0]
    assert extract_parser392_leftovers(text, 'de', 'p', '', None, None, None) == ([], text)


@pytest.mark.parametrize('module_number,text', [
    (331, 'Exemple Anne, maintenant président, détient désormais 100 parts de CHF 100 par suite de cession de 100 parts de CHF 100 à Exemple Eve, de et à Berne, nouvel associé-gérant pour 100 parts de CHF 100'),
    (387, 'Exemple Anne, maintenant président, détient désormais 100 parts de CHF 100 par suite de cession de 100 parts de CHF 100 à Exemple Eve, de Berne, à Paris, FRA, nouvel associé-gérant pour 100 parts de CHF 100'),
])
def test_existing_transfer_variants_retain_ownership(module_number, text):
    import importlib
    module = importlib.import_module(f'shab_analyzer.parser{module_number}')
    extractor = getattr(module, f'extract_parser{module_number}_leftovers')
    assert extractor(text, 'fr', 'p', '', None, None, None)[0]
    assert extract_parser392_leftovers(text, 'fr', 'p', '', None, None, None) == ([], text)


@pytest.mark.parametrize('digest', [SUPPLIED_SHA256[1], SUPPLIED_SHA256[-1]])
def test_signing_requires_matching_original_context(digest):
    _, (args, kwargs) = captured(digest)
    changed_source = kwargs['source_text'].replace('avec signature collective à deux', 'sans signature').replace('avec signature individuelle', 'sans signature')
    assert extract_parser392_leftovers(*args, source_text=changed_source) == ([], args[0])
