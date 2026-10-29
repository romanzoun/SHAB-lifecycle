import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser421 import extract_parser421_leftovers as extract, _LEGACY

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['08f0a654d82d76865c76c874575320b75b2a43ecc5cdb4c46db76b1bc6ced2ae', '11f619c03c6e7e06a2f80e9a67a38f2a0386872f0883222324d4aca60e0be27f', '155b329a0b96e1baaa98ffa4995699210a2a5dd626da2aea3c6c11d99b5bf6ee', '22fdccf5bdbb32ee965e1015f73e14bbb9481ef3f76ed93f8385907fc5021ced', '3b75e469218994d27addc411462fb570db3fc5a05561481710b9846f42e12e5d', '48df8570ed7f5a45c16e09ce6a32206910fd1d266f20baf3df62f93c4e423b13', '4c64a002d3aca3348ac4e8943aadac7cda795da75da607ec4aa7283da41d9903', '63fb7de00291c1a0fd86d8618df928e5404423f1c319b3bddef58ac482ce8fd1', '792ec833f4d2dabe824d24c6b4a217e05471f223db3edee3da57f17763d25c2d', '9509dd4b989dfe2adb2932abbfc12fd99daec4c176d0a54f7f429dc1bd9e8eeb', 'f857a1171085ba4b516b7029b00285de83ed46c88c31fc2c1f093ec96c9ae1f9', 'fb185d2254c6ac79d8331c3b143eea5b55cab2077b8aece7aa2c11e2beb44cf5']
COUNTS = [1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser421_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser421_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert PARSER_VERSION == 431
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
    if index == 9:
        assert (events, rest) == ([], args[0])
    else:
        assert len(events) == COUNTS[index] and rest == ''



def test_old_event_without_optional_attributes():
    event = Event('p', '', 'officer_changed', 'legacy.rule', payload={'name': 'Test Anna'})
    assert Event(**vars(event)) == event
    assert event.payload == {'name': 'Test Anna'}
    assert event.role is None and event.signing is None


@pytest.mark.parametrize('pattern_index,text', [
    (0, 'Nouveau membre du conseil de fondation sans signature: Test Anna, de Genève, à Lausanne'),
    (1, 'Nouveau membre du conseil de fondation sans signature: Test Anna, de et à Genève'),
    (2, 'Test Anna engage désormais la société par sa signature collective à deux'),
])
def test_old_rule_boundary_without_active_old_rule(pattern_index, text):
    assert _LEGACY[pattern_index].fullmatch(text)
    assert extract(text, 'fr', 'p', '', None, None, None) == ([], text)


def test_source_required_for_removed_signing_clause():
    _, _, (args, kwargs) = captured(9)
    source = kwargs['source_text'].replace('avec signature collective à deux', 'avec signature individuelle')
    assert source != kwargs['source_text']
    assert extract(*args, source_text=source) == ([], args[0])

EXPECTED = [
    ('organization_changed', {'branch_uid': 'CHE-376.401.611', 'previous_place': 'Peseux', 'place': 'Neuchâtel'}),
    ('organization_changed', {'branch_uid1': 'CHE-137.397.028', 'branch_uid2': 'CHE-472.502.461'}),
    ('officer_changed', {'mentioned_roles': ['associé indéfiniment responsable', 'administrateur'], 'powers_revoked': True}),
    ('organization_changed', {'audit_waiver_removed': True, 'auditor_uid': 'CHE-112.162.532'}),
    ('capital_changed', {'decision_date': '17.02.2021'}),
    ('status_changed', {'duration': 'sechs', 'end_date': '28.08.2021', 'court': 'Bezirksgericht Horgen'}),
    ('officer_changed', {'country': 'GBR', 'origin': 'Grande-Bretagne', 'place': 'Londres'}),
    ('officer_changed', {'origin': 'Val-de-Ruz', 'place': 'Chenit'}),
    ('officer_changed', {'additional_role': 'délégué', 'previous_role': 'vice-président'}),
    ('officer_changed', {'additional_role': 'secrétaire', 'origin': 'Genève'}),
    ('officer_changed', {'corrected': True, 'name': 'Arnod-Prin Samuel Yannick', 'entry': '1061'}),
    ('officer_changed', {'name': 'Preti Etienne'}),
]


@pytest.mark.parametrize('index', range(12))
def test_semantics(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    kind, fields = EXPECTED[index]
    assert rest == '' and events[0].event_type == kind
    for key, value in fields.items():
        assert events[0].payload[key] == value
    if index in (6, 11):
        assert events[0].signing == 'Einzelunterschrift'
    elif index in (8, 9):
        assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in events)
    elif index == 2:
        assert events[0].signing == 'ohne Unterschrift'
        assert events[0].role is None
        assert 'roles_removed' not in events[0].payload
    elif index == 7:
        assert events[0].role == 'membre du conseil de fondation'
        assert events[0].signing == 'ohne Zeichnungsberechtigung'
    else:
        assert events[0].signing is None
    if index == 8:
        assert events[0].role == 'président'
        assert events[1].role == 'administrateur'
        assert events[1].payload['previous_role'] == 'président'
    if index == 9:
        assert events[0].role == 'gérante'
    if index == 10:
        assert events[0].role == 'associé et gérant'


@pytest.mark.parametrize('module,text,lang', [
    ('parser267', "Nouveau membre du conseil de fondation sans signature: Test Anna, d'Yverdon, au Chenit", 'fr'),
    ('parser401', 'Par suite de fusion de communes, le siège de la succursale (CHE-123.456.789) à Ancienville devient Nouveauville', 'fr'),
    ('parser414', "Test Anna n'est associé indéfiniment responsable; ses pouvoirs sont radiés", 'fr'),
    ('parser315', "Radiation de la mention relative à la renonciation à l'organe de révision. Rrgane de révision: Test SA (CHE-123.456.789), à Lausanne", 'fr'),
    ('parser131', 'Mit Verfügung vom 11.02.2021 hat das Bezirksgericht Horgen die gewährte definitive Nachlassstundung um sechs Monate bis zum 28.08.2021 verlängert', 'de'),
])
def test_related_old_rules_keep_unchanged_rest(module, text, lang):
    from importlib import import_module
    old_extract = getattr(import_module('shab_analyzer.' + module), 'extract_' + module + '_leftovers')
    events, rest = old_extract(text, lang, 'p', '', None, None, None)
    assert events and rest == ''
    padded = '  ' + text + '  '
    assert extract(padded, lang, 'p', '', None, None, None, source_text=text) == ([], padded)


def test_source_with_additional_signing_restriction_is_not_consumed():
    _, _, (args, kwargs) = captured(9)
    source = kwargs['source_text'].rstrip('.') + ', avec le président.'
    assert extract(*args, source_text=source) == ([], args[0])
