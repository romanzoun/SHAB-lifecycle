import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser423 import extract_parser423_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['12a6342c2f940fd1c6a77e4390a4095048cf9ef773e232f1a4874f746b0f3c1d', '26a22fa447ba3cd243f53466c6f4e68c17ab9b56d9393f379aec334b11f2dd20', '281204383ae199da436dcfca49a7047f120235c0fd85dfc22c9c5313a9c5902c', '297f7c63e4f9cef0a28b691a09bbb87ce69da9badee73547a8e9286374e6902f', '752ac8e258bfbd698609d88466d06d1b6fa4ace01ee5aaa9884f21b44d4c1b17', '7a33afda4b2e7906370a2018332740fb2389c013017404247b48554adf471cd0', '90f619f00b54d39707c80130def3cafc1fd8efe0ee970304560fe33dcc1122de', 'a9b73463c30bdf3928eb512b5a4621d2345f0c9d56991b05fe2df7f7391f0fd5', 'c73915f3fad7c91f4c2c8d69ecc0637366f5b274ed8b718065f4d9377b710211', 'd6d60dea29e5dbca149a10a454db7c01518d9d903b3251258606cade1c0de86c', 'e3711e4bf0bf81d6555422d5f67e56837d5ce2fd42844bbbc1f407c5e27506c5', 'f0d0476ecbb8de8cc216ca2a2f714952399b527999fc6d273f09348f6bb377eb']
COUNTS = [1, 1, 1, 1, 3, 2, 1, 2, 2, 3, 3, 1]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser423_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser423_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert PARSER_VERSION == 425
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



EXPECTED = [
    ('status_changed', {'continues': True, 'decision_date': '18.02.2021'}),
    ('status_changed', {'reinstated': True, 'bankruptcy_resumed': True}),
    ('organization_changed', {'country': 'ES', 'head_office_id': 'ES B41768177'}),
    ('officer_changed', {'corrected': True, 'entry': '973'}),
    ('officer_changed', {}),
    ('status_changed', {'agreement_type': 'Dividendenvergleich'}),
    ('organization_changed', {'statutes_date': '22.05.1996', 'previous_statutes_date': '24.05.1996'}),
    ('officer_changed', {}),
    ('officer_changed', {'country2': 'FRA'}),
    ('status_changed', {'reinstated': True, 'deletion_date': '02.11.2020'}),
    ('organization_changed', {}),
    ('ownership_changed', {'count': '20', 'holding': '100', 'currency': 'CHF'}),
]


@pytest.mark.parametrize('index', range(12))
def test_semantics(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    kind, fields = EXPECTED[index]
    assert events[0].event_type == kind and rest == ''
    for key, value in fields.items():
        assert events[0].payload[key] == value
    if index == 4:
        assert [e.role for e in events] == ['président', 'administrateur', 'administrateur']
        assert events[1].payload['previous_role'] == 'directeur'
    if index in (4, 8):
        assert all(e.signing == 'Einzelunterschrift' for e in events)
    if index == 7:
        assert [e.role for e in events] == ['présidente', 'administrateur']
        assert all(e.signing is None for e in events)
    if index == 9:
        assert events[1].role == 'Liquidator' and events[1].signing is None
        assert events[2].event_type == 'address_changed'
    if index == 10:
        assert all(e.role == 'liquidateur' and e.signing == 'Einzelunterschrift' for e in events[1:])


@pytest.mark.parametrize('index', range(12))
def test_no_overlap_with_old_rules_even_in_isolation(index):
    # Exercise every historical extractor on the complete clause in isolation.
    import inspect
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(index)
    for name, old_extract in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser423_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name




@pytest.mark.parametrize('text,lang,old_version', [
    ("Rectificatif: l'inscription n°973 du 14.01.2021 (FOSC du 19.01.2021, p. 0/1005077789) est rectifiée en ce sens que le nom exact de Test Anna est: Test Anne", 'fr', 360),
    ('Test Anna a cédé 20 parts de CHF 100 au nouvel associé Test Paul. Associés: Test Anna et Test Paul chacun pour 20 parts de CHF 100', 'fr', 389),
    ('Administration: Test Anna, maintenant originaire de Lausanne, nommée présidente et Test Paul, de Lausanne, à Genève, lesquels signent individuellement', 'fr', 324),
])
def test_related_old_rules_keep_original_input(text, lang, old_version):
    import importlib
    old_extract = getattr(importlib.import_module(f'shab_analyzer.parser{old_version}'), f'extract_parser{old_version}_leftovers')
    old_events, rest = old_extract(text, lang, 'p', '', None, None, None)
    assert old_events and rest == ''
    padded = '  ' + text + '  '
    assert extract(padded, lang, 'p', '', None, None, None) == ([], padded)


def test_imported_legacy_pattern_keeps_original_input():
    from shab_analyzer.parser151 import _DE_COMPOSITION_AGREEMENT_WITH_REMOVED_MORATORIUM
    text = ('Mit Entscheid des Gerichts vom 30.11.2020 wurde der ordentliche Nachlassvertrag mit Dividendenvergleich bestätigt. '
            '[gestrichen: Mit Entscheid vom 01.01.2020 hat das Gericht der Gesellschaft die definitive Nachlassstundung für die Dauer von 6 Monaten, d.h. bis und mit dem 01.07.2020, gewährt.]')
    assert _DE_COMPOSITION_AGREEMENT_WITH_REMOVED_MORATORIUM.fullmatch(text)
    padded = '  ' + text + '  '
    assert extract(padded, 'de', 'p', '', None, None, None) == ([], padded)
