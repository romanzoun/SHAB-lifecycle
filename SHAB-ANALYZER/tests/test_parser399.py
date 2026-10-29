import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser399 import extract_parser399_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = [
    '09e5b2390ef1d7b2ca8bd6b4e2a790f86fa7e9f0b6cfe4c372cd3dd62cc756af',
    '0eda1c86fd145824e93bcc4cd881fd9c86ed8576f697f324f94c4b33acdc73ad',
    '218953cc4baf14686d95d15c5716e335adfa8410ae204d71c4b22dc99f23c4ec',
    '2aef42c705246eecadd2fdeafd997be105ae8b05c5fdb438c9d9ae67c2a28331',
    '40b83e676cae1d43fbd2b255499023a8dc4d6109252dda890857f6b718d52e30',
    '52a77ee0a8a87dc09f4cef91f4b21666d4bb9bb081dda1662e32a667069ed880',
    '70e4eeb7b901b6cbbd945d7e9ee44fecb2b38bba3d948dc331a64091a3fd49a2',
    '86d461eea9b5f2589131acab7865a558d5c76f8b5c2608e9789ab19466402cc8',
    '9a86a3add07fc1abb763707c0564e542a5cdba7e93ddf597098e384021a43afd',
    'bd094c11e4baefbc19c5a1dfe8811577f6fefb9fb51cb168c601e1c933b5f51f',
    'c73c115412d0fb5119c3c3a85fdae2d84850a6fc31032daf6f211ffee82262d2',
    'fd48a3e3ce98ee7d0e4c70ec3b4d6509c4f9c71377a71708a48dbcf14fad330f',
]
CONTEXT_REQUIRED = {'0eda1c86', 'fd48a3e3'}
EXPECTED = [
    ('ownership_changed', 'corporate_associate_corrected_notice', {'count': '200', 'nominal': '100', 'associate_uid': 'CHE-356.024.698'}),
    ('officer_changed', 'italian_member_nationality_gender_corrected', {'origin': 'cittadino italiano', 'previous_origin': 'cittadina italiana'}),
    ('capital_changed', 'conditional_participation_increase_and_capital_amended', {'decision_date': '19.01.2021', 'previous_date': '12.11.2020'}),
    ('officer_changed', 'associate_manager_becomes_unsigned_associate', {'count': '100', 'nominal': '100', 'previous_signing': 'Einzelunterschrift'}),
    ('capital_changed', 'share_capital_subsequently_fully_paid', {'capital': "100'000", 'additional_paid': "50'000", 'fully_paid': True}),
    ('statutes_changed', 'conditional_capital_clause_removed_conversion_or_option_rights', {}),
    ('capital_changed', 'conditional_participation_capital_increased_clause_amended', {'previous_capital': "2'322", 'capital': "20'349", 'increase': "18'027", 'issued': "18'027", 'count': "20'349", 'nominal': '1'}),
    ('officer_changed', 'domicile_state_country_corrected_notice', {'place': 'Beverly Hills', 'region': 'CA', 'country': 'USA', 'previous_country': 'GBR'}),
    ('status_changed', 'definitive_moratorium_two_commissioners_written_dates', {'decision_date': '5 janvier 2021', 'until_date': '15 juillet 2021', 'months_word': 'six'}),
    ('statutes_changed', 'statutes_date_corrected_notice_page', {'statutes_date': '12.06.2020', 'previous_statutes_date': '11.06.2020'}),
    ('officer_changed', 'female_director_joint_signing_comma_proxy_revoked', {'previous_signing_revoked': True}),
    ('status_changed', 'association_dissolved_general_meeting_liquidation', {'decision_date': '8 septembre 2020'}),
]


@lru_cache(None)
def captured(digest):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser399_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser399_leftovers', capture):
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
    added, rest = extract_parser399_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 425
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == (2 if digest.startswith('fd48a3e3') else 1) and not rest
    with patch.object(parser, 'extract_parser399_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('digest,expected', list(zip(SUPPLIED_SHA256, EXPECTED)))
def test_explicit_meaning(digest, expected):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser399_leftovers(*args, **kwargs)
    kind, action, fields = expected
    assert not rest and events[0].event_type == kind
    assert events[0].rule_id == f'{args[1]}.text.{action}.v1'
    assert events[0].payload['action'] == action
    assert {key: events[0].payload[key] for key in fields} == fields
    if digest.startswith('0eda1c86'):
        assert events[0].role == 'membro' and events[0].signing == 'Kollektivunterschrift zu zweien'
    if digest.startswith('2aef42c7'):
        assert events[0].role == 'Gesellschafter' and events[0].signing == 'ohne Unterschrift'
    if digest.startswith('c73c1154'):
        assert events[0].role == 'directrice' and events[0].signing == 'Kollektivunterschrift zu zweien'
    if digest.startswith('fd48a3e3'):
        assert events[1].role == 'liquidateur' and events[1].signing == 'Einzelunterschrift'
        assert events[1].payload['place'] == 'Rue'


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_unknown_suffix_language_and_invalid_dates(digest):
    _, (args, kwargs) = captured(digest)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser399_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser399_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser399_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_missing_optional_metadata_and_source(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser399_leftovers(*args[:4], None, None, None, **kwargs)
    assert events and not rest
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    events, rest = extract_parser399_leftovers(*args)
    if digest[:8] in CONTEXT_REQUIRED:
        assert not events and rest == args[0]
    else:
        assert events and not rest


def test_old_event_without_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event


@pytest.mark.parametrize('prefix', sorted(CONTEXT_REQUIRED))
def test_source_contradictions(prefix):
    digest = next(d for d in SUPPLIED_SHA256 if d.startswith(prefix))
    _, (args, kwargs) = captured(digest)
    assert extract_parser399_leftovers(*args, source_text='Unrelated.') == ([], args[0])
    old, new = ('cittadina italiana', 'cittadino italiano') if prefix == '0eda1c86' else ('signature individuelle', 'signature collective à deux')
    changed = kwargs['source_text'].replace(old, new)
    assert changed != kwargs['source_text']
    assert extract_parser399_leftovers(*args, source_text=changed) == ([], args[0])


@pytest.mark.parametrize('version,text,language', [
    (140, 'Signature collective à deux a été conférée à Exemple Anne, nommée directrice; sa procuration est radiée', 'fr'),
    (117, 'Die Gesellschaft hat mit Beschluss vom 01.01.2021 eine genehmigte Erhöhung des Partizipationskapitals gemäss näherer Umschreibung in den Statuten beschlossen. Die Gesellschaft hat mit Beschluss vom 01.01.2021 eine bedingte Erhöhung des Partizipationskapitals gemäss näherer Umschreibung in den Statuten beschlossen', 'de'),
    (245, "L'inscription no 123 du 01.01.2021 (FOSC du 02.01.2021) est complétée en ce sens que les statuts ont été modifiés le 01.01.2021", 'fr'),
    (198, "L'inscription no 123 du 01.01.2021 (publication FOSC du 02.01.2021 page 0/123) est rectifiée en ce sens que l'associé Exemple Anne est domicilié à Paris, FRA (et non à Lyon)", 'fr'),
])
def test_legacy_rule_ownership_in_isolation(version, text, language):
    import importlib
    old = getattr(importlib.import_module(f'shab_analyzer.parser{version}'), f'extract_parser{version}_leftovers')
    args = text, language, 'p', '', None, None, None
    events, rest = old(*args)
    assert events and not rest
    assert extract_parser399_leftovers(*args) == ([], text)


@pytest.mark.parametrize('stem', ['37a3ffc9-0f3b-47b3-bacd-1b40d851d8c0', '1855c3abe279580b8806de34447fdc1f75832e8ebc2773afe15f19d7b9459311', '2bfe63c21628baa119c054da99ab2f48e32db8af946cc9b50f59376bc86bf64b'])
def test_existing_fixture_unchanged(stem):
    import shab_analyzer.parse as parser
    path = FIXTURES / (stem + '.xml')
    result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser399_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(path)


@pytest.mark.parametrize('prefix', ['9a86a3ad', 'fd48a3e3'])
def test_invalid_written_dates(prefix):
    digest = next(d for d in SUPPLIED_SHA256 if d.startswith(prefix))
    _, (args, kwargs) = captured(digest)
    original = '5 janvier 2021' if prefix == '9a86a3ad' else '8 septembre 2020'
    changed = args[0].replace(original, '32 janvier 2021')
    assert changed != args[0]
    assert extract_parser399_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', sorted(CONTEXT_REQUIRED))
def test_source_must_match_residual_fields(prefix):
    digest = next(d for d in SUPPLIED_SHA256 if d.startswith(prefix))
    _, (args, kwargs) = captured(digest)
    old, new = ('Massagno', 'Lugano') if prefix == '0eda1c86' else ('Reconvilier', 'Lausanne')
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser399_leftovers(changed, *args[1:], **kwargs) == ([], changed)
