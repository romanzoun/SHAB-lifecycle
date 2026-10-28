import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser402 import extract_parser402_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = ['0bc9a2d58820df25d73b1947a88998124046b9c53c0e62d1a1b274c6033d7de6', '2c73a44f852c946cd6e3174d3fb61969b5e158ce731c5c62cb6796667a400f8f', '34276855631a7c39c7ee9658948cca11db984743928a8b9b08cc26a9f2666cb3', '3f5259fee1470685dc3fc69a21f486cb68fea4f41dd0f85648f18e7d6c4f2928', '4a3206f75385aa86ca148ef9cb80a923970ad201f7fd6f93c6db2bfa72daceac', '58e31dac092944fd6ae57d4661522b25a09a30601649f10e148448646e23bf65', '76d5af9bde188716624084e94074c9decab5a09f1c0c812c4bf3a7185ee18f2b', '76fb9687ed17cb2c943dfe1cd880de0dea01be3f241e955dc5f4ec2efa1c133e', '8c4f5b9a1cbb82afd7ef1d72117a58ff202453cde0b63d70b71888d4c4088d0a', 'b444b55ec84ba78b979427dca9ff1109c15dec8fe53390564e1c6055ea4ac8d3', 'ca9144c8eedb4914da6e7fe5beb76f024d77cef17ef4cde93bbfed9981714719', 'e8668fedead4042250fb3a6840ee71ba54ea675a98ab33ef403aa171364522f7']
CONTEXT_REQUIRED = {'76d5af9b', '76fb9687', '8c4f5b9a', '3f5259fe', '34276855'}
COUNTS = [1, 1, 1, 4, 1, 7, 1, 2, 2, 1, 1, 2]


@lru_cache(None)
def captured(digest):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser402_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser402_leftovers', capture):
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
    added, rest = extract_parser402_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 416
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS[SUPPLIED_SHA256.index(digest)] and not rest
    with patch.object(parser, 'extract_parser402_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_unknown_suffix_language_and_invalid_dates(digest):
    _, (args, kwargs) = captured(digest)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser402_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser402_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser402_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_missing_optional_metadata_and_source(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser402_leftovers(*args[:4], None, None, None, **kwargs)
    assert events and not rest
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    events, rest = extract_parser402_leftovers(*args)
    if digest[:8] in CONTEXT_REQUIRED:
        assert not events and rest == args[0]
    else:
        assert events and not rest


def test_old_event_without_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event



EXPECTED = [
 ('statutes_changed', {'date': '2020-12-21', 'previous_date': '2021-01-21'}),
 ('assets_transferred', {'assets': "34'251'756.00", 'net_assets': '1.00', 'consideration': 'aucune'}),
 ('organization_changed', {'omitted_field': 'Weitere Adresse', 'entry': "1'623"}),
 ('officer_changed', {'previous_role': 'président, délégué', 'signing_restriction': "avec le président du conseil d'administration"}),
 ('officer_changed', {'previous_role': 'administrateur'}),
 ('officer_removed', {'name': 'Eichholzer Nieuwoudt Claudia'}),
 ('officer_changed', {'origin': 'Genève', 'place': 'Genève'}),
 ('officer_changed', {'name': 'Sevaz Cédric Samuel', 'place': None, 'origin': None, 'country': None}),
 ('ownership_changed', {'count': '67', 'remaining': '133', 'country': 'FRA'}),
 ('officer_changed', {'previous_signing': 'Einzelunterschrift', 'previous_place': 'Oberkirch', 'corrected': True}),
 ('assets_transferred', {'count': '80', 'value': "80'000.00", 'consideration': 'keine'}),
 ('ownership_changed', {'count': '54', 'remaining': '108'}),
]

@pytest.mark.parametrize('digest,expected', list(zip(SUPPLIED_SHA256, EXPECTED)))
def test_explicit_payload_meaning(digest, expected):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser402_leftovers(*args, **kwargs)
    kind, fields = expected
    assert not rest and events[0].event_type == kind
    assert {key: events[0].payload[key] for key in fields} == fields


def test_roles_signing_and_residences():
    def events(index):
        _, (args, kwargs) = captured(SUPPLIED_SHA256[index])
        return extract_parser402_leftovers(*args, **kwargs)[0]
    board = events(3)
    assert [e.signing for e in board] == ['Kollektivunterschrift zu zweien'] * 2 + ['Einzelunterschrift'] * 2
    assert [e.payload['place'] for e in board] == [None, None, 'Versoix', 'Grand-Saconnex']
    assert all(e.role == 'administrateur' for e in board[:2])
    assert board[2].role == "président du conseil d'administration"
    director = events(4)[0]
    assert director.role == 'directeur' and director.signing == 'Kollektivunterschrift zu zweien'
    foundation = events(5)
    assert [e.event_type for e in foundation] == ['officer_removed'] * 4 + ['officer_changed'] * 3
    assert all(e.signing == 'ohne Zeichnungsberechtigung' for e in foundation)
    assert [e.payload['place'] for e in foundation[4:]] == ['Zurich', 'Genève', 'Wettingen']
    assert events(6)[0].role == 'Liquidator' and events(6)[0].signing == 'Einzelunterschrift'
    assert all(e.role == 'directeur' and e.signing == 'Einzelunterschrift' for e in events(7))
    assert events(7)[1].payload['place'] == 'Annecy'
    for index in (8, 11):
        assert events(index)[1].role == 'associé' and events(index)[1].signing == 'Einzelunterschrift'


@pytest.mark.parametrize('index', [2, 3, 6, 7, 8])
def test_source_evidence_required(index):
    _, (args, kwargs) = captured(SUPPLIED_SHA256[index])
    assert extract_parser402_leftovers(*args, source_text='Unrelated.') == ([], args[0])


def test_legacy_rule_ownership_and_date_payload():
    from shab_analyzer import parser192
    text = 'Das korrekte Statutendatum ist der 21.12.2020 und nicht der 21.01.2021'
    args = text, 'de', 'p', '', None, None, None
    old, rest = parser192.extract_parser192_leftovers(*args)
    assert old and not rest.strip()
    assert extract_parser402_leftovers(*args) == ([], text)
    variant = text.replace('ist der', 'lautet:').replace('und nicht der', 'nicht')
    assert extract_parser402_leftovers(variant, *args[1:]) == (old, rest)


@pytest.mark.parametrize('stem', ['7be44b47', '095f22f3', '21ebc82b', '0a10e470', '0ef3066f'])
def test_existing_fixture_unchanged(stem):
    import shab_analyzer.parse as parser
    paths = list(FIXTURES.glob(stem + '*.xml'))
    assert len(paths) == 1
    result = parse_publication_xml(paths[0])
    with patch.object(parser, 'extract_parser402_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(paths[0])

@pytest.mark.parametrize('version,text,language,source', [
    (356, 'Nouveau liquidateur : Exemple Anne, de Lausanne, à Genève', 'fr', 'Nouveau liquidateur avec signature individuelle: Exemple Anne, de Lausanne, à Genève.'),
    (384, "Exemple Anne détient désormais 2 parts de CHF 100 par suite de cession d'une part de CHF 100 à Exemple Marc, d'Italie, à Genève, nouvel associé pour une part de CHF 100", 'fr', ''),
    (400, 'Exemple Anne détient désormais 2 parts de CHF 100 par suite de cession de 1 parts de CHF 100 à Exemple Marc qui détient désormais 3 parts de CHF 100', 'fr', ''),
    (380, 'Mit dem im SHAB Nr. 8 vom 13.01.2021 publizierten TR-Nr. 1435 vom 08.01.2021 wurde der bisherige Text unvollständig publiziert. Korrekt wäre: Beispiel, Anna, von Bern, in Luzern, Präsident des Verwaltungsrates, mit Einzelunterschrift [bisher: in Oberkirch, Mitglied des Verwaltungsrates, mit Einzelunterschrift]', 'de', ''),
])
def test_legacy_variants_in_isolation(version, text, language, source):
    import importlib
    module = importlib.import_module(f'shab_analyzer.parser{version}')
    if version == 384:
        source = text + ' avec signature collective à deux.'
    args = text, language, 'p', '', None, None, None
    events, rest = getattr(module, f'extract_parser{version}_leftovers')(*args, source_text=source)
    assert events and not rest.strip()
    assert extract_parser402_leftovers(*args, source_text=source) == ([], text)

@pytest.mark.parametrize('index', [3, 6, 7, 8])
def test_signing_evidence_must_match(index):
    _, (args, kwargs) = captured(SUPPLIED_SHA256[index])
    changed = kwargs['source_text'].replace('signature individuelle', 'signature collective à deux')
    assert extract_parser402_leftovers(*args, source_text=changed) == ([], args[0])


def test_omission_reference_invalid_date():
    _, (args, kwargs) = captured(SUPPLIED_SHA256[2])
    changed = kwargs['source_text'].replace('14.01.2021', '31.02.2021')
    assert extract_parser402_leftovers(*args, source_text=changed) == ([], args[0])
