import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser426 import extract_parser426_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['00e1a39143c7c9cd5d080640aa1b480fe3096dc8855bb60bf3bf7d96d2d4fa28', '3105b0ce45bd667b6c17df8913f6fc050bcb88fcaee2f00e504371fd0e74f812', '3da4fdac2a1ec647dcf20806688dbc0eec5d823c74635ed6dd89d20951b7dbbd', '598f557ef9abf6079f83c25c12e9ac9da5fb69a120e397bca67f39b1b71a8349', '5e41290f9e33885413f80e5b0b6edbda1bfe190f48f03797c6df98109c922d90', '7000885fad3bb0ee15619ab127096ce907fd5be6feea774a3c9a47390315c68a', '7ba3d15f53f0a040667703e9a14111b657568b6e5b5809a2161af50bfe161447', '87c6a0775b0de38412ad8195b8a198515be95fd6b3f3ca9907e1d890a11f9261', '8ae801add92f0ec42b4129f9869e417a4b7037b279421419f70d3cec233b889d', 'a11850289d9ca8a8a653ddbfbafe90d159bb871269fe67b7fe7094e4254e5552', 'caa01aca8e610286bb326454032b9c88feae6594c0db061afb48b33278e2a27f', 'ecbc160402b226e63be655cb5e887cd214ee2559299e2dd087910eb901d24472']
COUNTS = [1, 1, 1, 1, 3, 1, 1, 1, 2, 1, 1, 1]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser426_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser426_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert PARSER_VERSION == 430
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
    if index == 4:
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
        if not name.startswith('extract_parser') or name == 'extract_parser426_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name


EXPECTED = [
    ('address_changed', 'additional_address_supplemented_notice'),
    ('organization_changed', 'three_branch_mentions_removed_plural'),
    ('capital_changed', 'conditional_capital_clause_introduced_decision_first'),
    ('status_changed', 'female_owner_bankruptcy_appeal_suspended_order'),
    ('ownership_changed', 'share_transfer_new_female_manager_seller_president'),
    ('capital_changed', 'bearer_participation_certificates_intermediated_authorized'),
    ('ownership_changed', 'associate_share_count_corrected_notice'),
    ('address_changed', 'branch_location_changed_short_published_uid'),
    ('officer_changed', 'director_appointed_president_pair_continued_signing'),
    ('status_changed', 'bankruptcy_appeal_declared_inadmissible'),
    ('officer_changed', 'director_identity_corrected_collective_signing'),
    ('status_changed', 'erroneous_deletion_reinstated_for_liquidation_corrected_notice'),
]


@pytest.mark.parametrize('index', range(12))
def test_semantics(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    assert rest == ''
    assert (events[0].event_type, events[0].payload['action']) == EXPECTED[index]
    p = events[0].payload
    if index == 0:
        assert p['postal_code'] == '3423' and p['supplemented'] is True
    if index == 1:
        assert p['mention_removed'] is True
        assert [p['place'+str(i)] for i in (1, 2, 3)] == ['Corsier-sur-Vevey', 'Nyon', 'Yverdon-les-Bains']
    if index == 2:
        assert p['introduced'] is True and p['decision_date'] == '23.03.2021'
    if index == 3:
        assert p['suspensive_effect'] is True and p['bankruptcy_entry_removed'] is True
        assert p['time'] == '09.00'
    if index == 4:
        assert (p['count'], p['before'], p['remaining'], p['nominal']) == ('99', '200', '101', '100')
        assert events[1].role == 'gérante' and events[1].signing == 'Einzelunterschrift'
        assert events[2].role == 'président' and events[2].signing is None
        assert extract(*args, source_text='Unrelated source.') == ([], args[0])
    if index == 5:
        assert p['intermediated'] is True
    if index == 6:
        assert (p['count'], p['previous_count'], p['nominal']) == ('230', '200', '100')
        assert p['corrected'] is True
    if index == 7:
        assert p['branch_uid'] == 'CHE-287.702.24'
        assert p['previous_uid'] == 'CHE-287.702.246'
    if index == 8:
        assert events[0].role == 'président' and p['previous_role'] == 'directeur'
        assert events[1].payload['place'] == 'Dardagny'
        assert all(e.signing == 'Einzelunterschrift' for e in events)
    if index == 9:
        assert p['appeal_inadmissible'] is True and p['bankruptcy_date'] == '05.01.2021'
    if index == 10:
        assert events[0].role == 'direttore' and events[0].signing == 'Kollektivunterschrift zu zweien'
        assert p['corrected'] is True
    if index == 11:
        assert p['reinstated'] is True and p['in_liquidation'] is True and p['corrected'] is True


@pytest.mark.parametrize('text,language,version', [
    ('Neue zusätzliche Adresse: Testweg 1, 8000 Zürich', 'de', 153),
    ('Persona iscritta corretta: Test, Anna, da Lugano, in Lugano, membro, con firma individuale', 'it', 317),
    ('Die Gesellschaft hat sämtliche Inhaberpartizipationsscheine als Bucheffekten im Sinne des Bucheffektengesetzes ausgestaltet und ist daher befugt, Inhaberpartizipationsscheine zu halten', 'de', 363),
    ("Radiation de la mention de l'existence d'une succursale à Lausanne", 'fr', 137),
])
def test_old_rule_ownership(text, language, version):
    import importlib
    old = getattr(importlib.import_module(f'shab_analyzer.parser{version}'), f'extract_parser{version}_leftovers')
    events, rest = old(text, language, 'p', '', None, None, None)
    assert events and rest == ''
    padded = '  ' + text + '  '
    assert extract(padded, language, 'p', '', None, None, None) == ([], padded)
