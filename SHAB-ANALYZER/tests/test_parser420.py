import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser420 import extract_parser420_leftovers as extract, _LEGACY

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['2cdc7e745413658dd63f65db0fe0dacaf278d14e8088c9d8e24e9429a2b9d773', '3aaf442691ee91968739ac79da0380a58c4ad16774db687c67d0c27579f2c5b6', '4ff9baf8fbf09540374da6dabcfd4e2f61892f94c8c8660e6cfa447a08445433', '619dc916b3cf747005dfb0b2a98821b71dd6acb3f9eb5e0591e521167507f871', '708007cfc3ceee03c9a9035dcb4b233c9ea10dfa90f0ddb90e8668beeacec10b', 'ab997c09b7da337b5bd4408b64bb048f3857ab4a9cbe8bfa9b81714324f2b95d', 'b8a72e0a9ab75fced2f6cdb7f97d8426d5a6e02553f16489915ccff200afd498', 'c01b6634a564db01a7bdf15bfce651e05571c886c2e6d599b5f93d46e0d0a8ab', 'c72be4d2a8b86a6b1384d6f48e15eb1866dacd7bd89e5b2a0ee8f9e4c6ce4fdd', 'd6c91269c614c68f716616bf34e053f6f062e9e167ba852eb8b1af29334fe0ca', 'e4006fc64d13984b0860ed5c017aa751676a247bd85e00b01e4308cc0ecf856a', 'f2558831188f3294b2ed3cb9f42b38974c2d52629769cae97f1bf419c8ce92da']
COUNTS = [1, 1, 1, 2, 1, 2, 1, 1, 1, 1, 1, 1]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser420_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser420_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert PARSER_VERSION == 441
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


EXPECTED = [
 ('organization_changed', {'historical_annotation': True, 'count1': '100', 'count2': '100', 'previous_name1': 'Bachmann, Martin Fabian', 'previous_name2': 'Mohsen, Mona Omar Mahmoud', 'entry_date': '12.02.2021'}),
 ('officer_changed', {'corrected': True, 'signing_partner_role': 'administrateur', 'name': 'Ruffieux Hervé Louis Charles', 'previous_name': 'Ruffieux Alain Louis Charles'}),
 ('status_changed', {'legal_basis': 'Art. 935 OR i.V.m. Art. 164 HRegV'}),
 ('officer_changed', {'country': 'FRA', 'origin': 'Genève'}),
 ('officer_changed', {'signing_restriction': 'not_with'}),
 ('ownership_changed', {'count': '1', 'before': '200', 'remaining': '199', 'buyer': 'Alves da Cunha dos Santos Sandra Isabel', 'origin': 'Portugal'}),
 ('ownership_changed', {'count': '2', 'remaining': '8', 'total1': '6', 'total2': '6'}),
 ('organization_changed', {'legal_basis': 'Art. 152 HRegV'}),
 ('organization_changed', {'branch_uid': 'CHE-331.639.582'}),
 ('officer_changed', {'procuration_removed': True, 'signing_partner_roles': ['administrateur', 'directeur']}),
 ('organization_changed', {'previous_place': 'Morgins', 'previous_municipality': 'Troistorrents'}),
 ('officer_changed', {'corrected': True, 'previous_name': 'Kyd Laurence Olivier', 'name': 'Kyd Laurent Olivier'}),
]


@pytest.mark.parametrize('index', range(12))
def test_semantics(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    kind, fields = EXPECTED[index]
    assert rest == '' and events[0].event_type == kind
    for key, value in fields.items():
        assert events[0].payload[key] == value
    if index in (1, 4, 9):
        assert events[0].signing == 'Kollektivunterschrift zu zweien'
    if index == 3:
        assert all(e.signing == 'ohne Zeichnungsberechtigung' for e in events)
        assert events[1].payload['origin'] == events[1].payload['place'] == 'Genève'
        assert events[1].payload['country'] is None
    if index == 4:
        assert len(events[0].payload['excluded_partners']) == 5
        assert extract(*args, source_text='unrelated') == ([], args[0])
    if index == 5:
        assert events[1].role == 'associée'
        assert events[1].signing == 'ohne Zeichnungsberechtigung'
    if index == 7:
        assert events[0].signing is None
        assert 'place' not in events[0].payload
    if index == 11:
        assert events[0].signing is None
        assert events[0].role == 'membre du conseil'


def test_old_event_without_optional_attributes():
    event = Event('p', '', 'officer_changed', 'legacy.rule', payload={'name': 'Test Anna'})
    assert Event(**vars(event)) == event
    assert event.payload == {'name': 'Test Anna'}
    assert event.role is None and event.signing is None


def test_inconsistent_partial_transfer():
    _, _, (args, kwargs) = captured(5)
    text = args[0].replace('de ses 200 parts', 'de ses 199 parts')
    assert text != args[0]
    assert extract(text, *args[1:], **kwargs) == ([], text)


def test_old_rule_boundary_without_active_old_rule():
    text = 'Nouvelle succursale: Testville (CHE-123.456.789) [précédemment: Ancienville (CH-123.4.567.890-1)]'
    assert _LEGACY[0].fullmatch(text)
    assert extract(text, 'fr', 'p', '', None, None, None, source_text=text) == ([], text)


@pytest.mark.parametrize('module,text', [
    ('parser277', 'Test Anna, associé-gérant, cède 1 de ses 20 parts de CHF 100 à Test Bea, de France, à Lausanne, nouvelle associée avec 1 parts de CHF 100, sans signature. Test Anna reste titulaire de 19 parts de CHF 100'),
    ('parser262', "La succursale d'Orpund est radiée (FOSC du 17.02.2021, Id 1005103063)"),
    ('parser266', 'Signature collective à deux, sauf avec Test Anna, a été conférée à Test Bea, nommée sous-directrice; sa procuration est radiée'),
    ('parser366', 'Succursale: Testville (CHE-123.456.789) [précédemment: Ancienville (Commune)]'),
])
def test_related_inline_rule_boundaries(module, text):
    from importlib import import_module
    old_extract = getattr(import_module('shab_analyzer.' + module), 'extract_' + module + '_leftovers')
    events, rest = old_extract(text, 'fr', 'p', '', None, None, None)
    assert events and rest == ''
    assert extract(text, 'fr', 'p', '', None, None, None, source_text=text) == ([], text)


@pytest.mark.parametrize('suffix', ['', '.'])
@pytest.mark.parametrize('legacy_id', ['CH-123.4.567.890-1', 'CH-123-1'])
def test_legacy_identifier_retains_original_whitespace(suffix, legacy_id):
    text = f'  Nouvelle succursale: Testville (CHE-123.456.789) [précédemment: Ancienville ({legacy_id})]' + suffix + '  '
    assert _LEGACY[0].fullmatch(text.strip())
    assert extract(text, 'fr', 'p', '', None, None, None) == ([], text)


def test_missing_source_signing_is_not_inferred():
    _, _, (args, kwargs) = captured(4)
    source = kwargs['source_text'].replace('avec signature collective à deux', 'avec signature individuelle')
    assert source != kwargs['source_text']
    assert extract(*args, source_text=source) == ([], args[0])
