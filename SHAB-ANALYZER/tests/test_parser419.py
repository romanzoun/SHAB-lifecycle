import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser419 import extract_parser419_leftovers as extract, _LEGACY

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['2cbdf3d5743abf684b58372884392bbe9d5dede097624f235c12d922e93fb90b', '36a8fd25c66a88b452ba6401e220abbac2aee61e85a715d159587e5ad1ea51c3', '42f12520a9e15274c4d857b38b0bcb117ae76f5eb7bcc526a6b927738425922d', '5de277bbd0ea2dc7e0dbb856cf4d6068375ef5bf416786038fe8d386f6c00d97', '619e66c86ff6dd7bac62fea403b3958fdc04bc66a414dacb6950cef818db31f8', '8baca56f6e37a4dff205eec8b8ccb2f03ba5f6e28d4ba253df2faf0b69013cd1', '930be8a9ec4c981a69c5eea9af953d388a4b2dd5358fdb2159c9d566c52655c7', 'a1714ae44303d8a74d9092e611b7e08777e86f44c93aeeaa958e2af07d524d5c', 'aab88174c47f53d16efc631e0420957fb7a77bb4816c55b821d84d2448944c6e', 'dc1ad7654fefab35291e3b415b0189b365cb12ea0cf9c225fdd4ac935e8a3d94', 'e532484ce0074b40be9f99c84447c92f52c89e9d02139d09b320af106cd39c0c', 'e8b4a146ae67d2907c10a1b5ccce9278a4eeb13aaa5318c385cfe241cf28654b']
COUNTS = [1, 7, 3, 3, 2, 4, 1, 1, 1, 2, 2, 1]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser419_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser419_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert PARSER_VERSION == 432
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
    if index in (1, 3, 9, 10):
        assert (events, rest) == ([], args[0])
    else:
        assert len(events) == COUNTS[index] and rest == ''


EXPECTED = [
 ('organization_changed', {'place': 'Klosters'}),
 ('status_changed', {'decision_date': '29.10.2020'}),
 ('officer_changed', {'previous_role': 'secrétaire', 'signing_partner_role': 'membre du comité'}),
 ('organization_changed', {'translated_name': 'Institute for Scientific Information on Coffee (ISIC) in liquidation'}),
 ('officer_changed', {'previous_role': 'directeur'}),
 ('officer_changed', {'name': 'Fazel Cyrus'}),
 ('organization_changed', {'removed_since': 'Mai 2017', 'historical_annotation': True}),
 ('status_changed', {'legal_basis': 'art. 159, al. 1 let. b ORC'}),
 ('status_changed', {'previous_deletion_reason': 'Das Einzelunternehmen wird infolge Fehlens der gesetzlichen Voraussetzungen der Eintragungspflicht auf Begehren der Inhaberin gelöscht.'}),
 ('ownership_changed', {'count': '10', 'before': '20', 'nominal': "1'000"}),
 ('officer_changed', {'country': 'MCO'}),
 ('officer_changed', {'place': 'Saint-Maurice', 'previous_place': 'Mex (VD)', 'corrected': True}),
]


@pytest.mark.parametrize('index', range(12))
def test_semantics(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    kind, fields = EXPECTED[index]
    assert rest == '' and events[0].event_type == kind
    for key, value in fields.items():
        assert events[0].payload[key] == value
    if index == 1:
        assert all(e.role == 'liquidateur' and e.signing == 'Kollektivunterschrift zu zweien' for e in events[1:])
        assert events[5].payload['signing_changed'] is True
        assert len({e.person_key for e in events[1:]}) == 6
    if index == 2:
        assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in events)
        assert events[2].role == 'membre et trésorière du comité'
    if index == 3:
        assert [e.signing for e in events[1:]] == ['Einzelunterschrift', 'ohne Zeichnungsberechtigung']
    if index == 4:
        assert [e.role for e in events] == ['président', 'vice-président']
        assert all(e.signing == 'Einzelunterschrift' for e in events)
    if index == 5:
        assert events[2].payload['place'] == 'Tallinn (Estonie)'
        assert all(e.payload['place'] is None for i, e in enumerate(events) if i != 2)
        assert all(e.signing == 'Einzelunterschrift' for e in events)
    if index == 9:
        assert events[1].role == 'associé-gérant président' and events[1].signing == 'Einzelunterschrift'
    if index == 10:
        assert [e.signing for e in events] == ['Kollektivunterschrift zu zweien', 'Einzelunterschrift']
        assert [e.payload['country'] for e in events] == ['MCO', 'FRA']
    if index in (1, 3, 9, 10):
        assert extract(*args, source_text='unrelated') == ([], args[0])


LEGACY_TEXTS = [
 ('fr', 'Le domicile exact de Test Anna est Lausanne (et non Genève).'),
 ('fr', "Selon décision de l'Autorité de surveillance du 15.01.2021, la fondation est dissoute. Liquidateurs: les membres du conseil Test Anna, Test Bea, Test Clara, Test Dora et Test Emma."),
 ('de', 'Zweigniederlassung neu: [Folgende Zweigniederlassung wurde aufgehoben:] [gestrichen: Zürich (CH-020.9.003.346-8)].'),
 ('fr', "Par arrêt du 15.02.2021, le Tribunal cantonal a accordé l'effet suspensif au recours interjeté le 08.02.2021 contre la décision du faillite du 26.01.2021 (art. 159, al. 2 ORC)."),
]


@pytest.mark.parametrize('pattern,case', list(zip(_LEGACY, LEGACY_TEXTS)))
def test_old_rule_boundaries_without_active_old_rules(pattern, case):
    lang, text = case
    assert pattern.fullmatch(text)
    assert extract(text, lang, 'p', '', None, None, None, source_text=text) == ([], text)


def test_old_event_without_optional_attributes():
    event = Event('p', '', 'officer_changed', 'legacy.rule', payload={'name': 'Test Anna'})
    assert Event(**vars(event)) == event
    assert event.payload == {'name': 'Test Anna'}
    assert event.role is None and event.signing is None


def test_inconsistent_partial_transfer():
    _, _, (args, kwargs) = captured(9)
    text = args[0].replace('de ses 20 parts', 'de ses 10 parts')
    source = kwargs['source_text'].replace('de ses 20 parts', 'de ses 10 parts')
    assert text != args[0]
    assert extract(text, *args[1:], source_text=source) == ([], text)


@pytest.mark.parametrize('module,text', [
 ('parser274', "Par arrêt du 15.02.2021, le Tribunal cantonal de Fribourg a accordé l'effet suspensif au recours interjeté le 08.02.2021 contre la décision du 26.01.2021"),
 ('parser405', "Par arrêt du 15.02.2021, le Tribunal cantonal de Fribourg a accordé l'effet suspensif au recours interjeté le 08.02.2021 contre la décision du 26.01.2021 (art. 159, al. 1 let.b ORC)"),
 ('parser417', 'Sitz neu: Teststadt. [Angaben des Sitzes infolge Namensänderung der Gemeinde]'),
 ('parser417', '[Anpassung des Sitzes infolge Namensänderung der Gemeinde]'),
])
def test_legacy_inline_rule_boundaries(module, text):
    from importlib import import_module
    lang = 'de' if module == 'parser417' else 'fr'
    old_extract = getattr(import_module('shab_analyzer.' + module), 'extract_' + module + '_leftovers')
    events, rest = old_extract(text, lang, 'p', '', None, None, None)
    assert events and rest == ''
    assert extract(text, lang, 'p', '', None, None, None, source_text=text) == ([], text)
