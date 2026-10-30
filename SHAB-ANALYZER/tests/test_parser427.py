import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser427 import extract_parser427_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['1fb7a9b20d664c8d8d9fc0f8cad42a636dbe373178430bf2badb11c564c45064', '31f81b487b157667dcf35194d8bb4b495b7f5051963d4d62c90bc755a5b7f590', '429b3fbf594b36048de067948cf0e6a9adee534fb5137eb28858dfe69e236bea', '802cc6e6666347c869258ba6324f5c49fd0f0e6110b5e78e87a2f6178fdb4837', '96a49d1c821960711f86ed3d838aaeb4a4880c69f650edfaeb764e32b3f5fa72', 'a480fe4591b892f990e8a76b780a058cb286af73f53d63744edf9472882e1384', 'a4c9310eedbe1a3cf1f173ed93b535676f615480c2d20ca4a70540e88922c935', 'ae724175b8552a417607f41d0376a3d5601599c607948f5422f3bf0ccff1a0b7', 'd0b1b7ec5b2c59b5df24941107a6cccb3c469dd64e2b900ca8fdb9971dd09fd4', 'd5b7944202b93faf0b66cbd09b5d2dbef906cbca694b459e92e9db31ded02d27', 'ee5d2a1ac0922fc43d1110f429eb44ff4ad446843359eb4b5a091fa1980703fa', 'f56f27295599e96f2d7c3aa93346cd6bccb637176357060f0152794d0ffa3561']
COUNTS = [1, 1, 2, 1, 7, 1, 4, 1, 1, 3, 1, 1]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser427_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser427_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert PARSER_VERSION == 440
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
    if index in (1, 3):
        assert (events, rest) == ([], args[0])
    else:
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
        if not name.startswith('extract_parser') or name == 'extract_parser427_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name


EXPECTED = [
    ('capital_changed', 'authorized_capital_clause_repealed_bracketed'),
    ('ownership_changed', 'two_associates_transfer_equal_shares'),
    ('officer_changed', 'two_procurists_except_between_no_comma'),
    ('organization_changed', 'auditor_repeated_departure_notice_corrected'),
    ('officer_changed', 'seven_officers_with_shared_exclusions'),
    ('status_changed', 'bankruptcy_appeal_rejected_opening_fixed'),
    ('officer_changed', 'four_procurists_with_administrator'),
    ('capital_changed', 'authorized_participation_capital_description_changed'),
    ('organization_changed', 'organization_mention_removed_article_95'),
    ('officer_changed', 'director_promoted_restrictions_removed'),
    ('organization_changed', 'two_branch_mentions_removed_one_registry_id'),
    ('address_changed', 'branch_seat_relocated_with_historical_registry_id'),
]


@pytest.mark.parametrize('index', range(12))
def test_semantics(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    assert rest == ''
    assert (events[0].event_type, events[0].payload['action']) == EXPECTED[index]
    p = events[0].payload
    if index == 0:
        assert p['repealed'] is True and p['introduced_date'] == '22.07.2019'
    if index == 1:
        assert (p['count_per_seller'], p['buyer_count'], p['remaining'], p['nominal']) == ('25', '50', '75', '100')
    if index == 2:
        assert all(e.signing == 'Kollektivprokura zu zweien' for e in events)
        assert events[0].payload['excluded_signing_partners'] == [events[1].payload['name']]
    if index == 3:
        assert p['already_departed'] is True and p['corrected'] is True
        assert p['previous_date'] == '21.10.2020'
    if index == 4:
        assert [e.role for e in events] == ['directeur adjoint'] * 3 + ['directrice adjointe', 'sous-directeur', 'sous-directrice', 'sous-directeur']
        assert len(p['excluded_signing_partners']) == 12
        assert events[-1].payload['country7'] == 'FRA'
        assert events[1].payload['place'] == 'Genève'
    if index == 5:
        assert p['appeal_rejected'] is True and p['in_liquidation'] is True
        assert p['time'] == '12h00' and p['effective_date'] == '02.03.2021'
    if index == 6:
        assert all(e.signing == 'Kollektivprokura zu zweien' for e in events)
        assert all(e.payload['required_signing_partner_role'] == 'administrateur' for e in events)
        assert all(len(e.payload['excluded_signing_partners']) == 3 for e in events)
    if index == 7:
        assert p['introduced_date'] == '07.05.2019' and p['decision_date'] == '12.03.2021'
    if index == 8:
        assert p['article'] == '95 cpv. 1 lett. h ORC' and p['mention_removed'] is True
    if index == 9:
        assert [e.role for e in events] == ['directeur', 'directrice adjointe', 'directrice adjointe']
        assert events[0].payload['signing_restriction'] == 'sans autre restriction'
        assert events[1].payload['signing_restriction'] == 'avec un administrateur ou un directeur'
    if index == 10:
        assert p['branch_registry_id'] == 'CH-645.4097.284-2' and p['place2'] == 'Solothurn'
    if index == 11:
        assert p['previous_registry_id'] == 'CH-217-3540386-0' and p['branch_uid'] == 'CHE-262.745.104'


@pytest.mark.parametrize('text,language,version', [
    ('Aufhebung der Statutenbestimmung über die mit Gewährungsbeschluss vom 22.07.2019 eingeführte bedingte Kapitalerhöhung infolge Erlöschens der Wandelrechte', 'de', 107),
    ("Radiation de la mention de l'existence d'une succursale à Lausanne", 'fr', 137),
    ('Procuration collective à deux, sauf entre eux, a été conférée à Test Anna, de Lausanne, à Pully, et à Test Bruno, de Genève, à Genève', 'fr', 308),
    ('Procuration collective à deux, sauf entre eux a été conférée à Test Anna, de Lausanne, à Paris, FRA, et Test Bruno, de Genève, à Lyon, FRA', 'fr', 412),
])
def test_old_rule_ownership(text, language, version):
    import importlib
    old = getattr(importlib.import_module(f'shab_analyzer.parser{version}'), f'extract_parser{version}_leftovers')
    events, rest = old(text, language, 'p', '', None, None, None)
    assert events and rest == ''
    padded = '  ' + text + '  '
    assert extract(padded, language, 'p', '', None, None, None) == ([], padded)


@pytest.mark.parametrize('index', [1, 3])
def test_source_required_and_unrelated_source_rejected(index):
    _, _, (args, _) = captured(index)
    assert extract(*args, source_text='Unrelated source.') == ([], args[0])


def test_correction_context_date_must_be_valid():
    _, _, (args, kwargs) = captured(3)
    source = kwargs['source_text'].replace('21.10.2020', '31.02.2020')
    assert extract(*args, source_text=source) == ([], args[0])


def test_seven_officers_requires_complete_group():
    _, _, (args, kwargs) = captured(4)
    changed = args[0].replace(', FRA, sous-directeur', ', FRA, membre')
    assert extract(changed, *args[1:], **kwargs) == ([], changed)
