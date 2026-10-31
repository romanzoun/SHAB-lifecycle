import hashlib
import importlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser411 import extract_parser411_leftovers, _LEGACY

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = [
    '0f1a0f7d6f5c1498c5f89cdeb6019132d2b9954b47895d0a2bb8b85e000948e5',
    '21acce6e233786d06491460aba5ce13b3173224fbade2f7b2098f806b1ba55d9',
    '522b3720fef2dd51fa94894759fe1096c2a0308390046d831ba69f4b3749df9d',
    '53e794ba036cc8760f8c12f9974afdb0657e512f6552c936e98fad49f23aebfc',
    '6343098da7ed117f85f47d8ffb7e5a7abb726f5f3bcd9442ea3e627094c9c0df',
    '7323eb3d2aaf569299fbae395b4b3af9d2fcfef01054e6985bf75a4c3ef0cc54',
    '7db3a3c2a3bc25b4023a4168434a88af7da3b1a1e1c8f93707cf46d0b36509c9',
    '8289483a52bd32004dab6d628b8630d59381680c5d911bef261a61c7c01c82fc',
    '9ecd6b3adfdc3a1f28de16225437d1e60bb66cdbac44a7cd5eb706e3e90f7c54',
    'c89321e6d776449a06ceeacac7199344d2f495b7b06a72ec72323b68f56aebe8',
    'cbf09bc66035f9bb4e6c7f6e2584312763e9274d6f6660f135a9d2b4a910fb5a',
    'eb3211eaf8cf24634e27cb0d1817d60ecd275c53eda6f9a5567a374173333985',
]
COUNTS = [2, 2, 1, 1, 4, 1, 1, 1, 4, 5, 2, 4]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser411_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser411_leftovers', capture):
        result = parse_publication_xml(FIXTURES / (SUPPLIED_SHA256[index] + '.xml'))
    assert len(calls) == 1
    return result, calls[0]


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('index', range(12))
def test_complete_and_unchanged_legacy_payloads(index):
    import shab_analyzer.parse as parser
    result, (args, kwargs) = captured(index)
    added, rest = extract_parser411_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 443
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS[index] and not rest
    with patch.object(parser, 'extract_parser411_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (SUPPLIED_SHA256[index] + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('index', range(12))
def test_unknown_suffix_language_and_invalid_dates(index):
    _, (args, kwargs) = captured(index)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser411_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser411_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser411_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index', range(12))
def test_missing_optional_metadata_and_source(index):
    _, (args, kwargs) = captured(index)
    events, rest = extract_parser411_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == COUNTS[index] and not rest
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)


def test_old_event_without_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event

EXPECTED = [
    ('officer_changed', {'name1': 'Bieri Jean-Yves'}),
    ('officer_changed', {'excluded3': 'Duperret Julien'}),
    ('organization_changed', {'foundation_date': '25.05.1999'}),
    ('capital_changed', {'clause_date': '1er juillet 2013', 'decision_date': '14 janvier 2021'}),
    ('officer_changed', {'country2': 'FRA'}),
    ('seat_changed', {'to': 'Klosters', 'reason': 'municipality_name_change', 'official_change': False, 'person_details_adapted': True}),
    ('ownership_changed', {'count': '20', 'before': '100', 'remaining': '80', 'buyer_count': '65'}),
    ('capital_changed', {'capital': "3'425'000'000.00", 'previous_capital': "3'000'000'000.00"}),
    ('ownership_changed', {'count1': '40', 'count2': '40'}),
    ('officer_removed', {'powers_revoked': True}),
    ('status_changed', {'decision_date': '03.02.2021', 'dissolved': True}),
    ('ownership_changed', {'removed_count': '36', 'previous_count2': '56', 'count2': '78', 'count3': '14'}),
]


@pytest.mark.parametrize('index', range(12))
def test_payload_semantics(index):
    _, (args, kwargs) = captured(index)
    events, rest = extract_parser411_leftovers(*args, **kwargs)
    assert not rest
    kind, fields = EXPECTED[index]
    assert events[0].event_type == kind
    for key, value in fields.items():
        assert events[0].payload[key] == value
    if index == 0:
        assert [e.role for e in events] == ['Präsident des Verwaltungsrates', 'Mitglied des Verwaltungsrates']
        assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in events)
    if index == 1:
        assert all(e.role is None and e.signing == 'Kollektivunterschrift zu zweien' for e in events)
        for i, event in enumerate(events):
            assert event.payload['excluded_signing_partners'] == [events[1-i].payload['name']] + [event.payload[f'excluded{j}'] for j in (1, 2, 3)]
    if index == 4:
        assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in events)
        assert events[0].role == 'Mitglied des Verwaltungsrates'
        assert events[1].role == 'Präsident des Verwaltungsrates'
        assert [e.payload['name'] for e in events] == [events[0].payload[k] for k in ('previous_president', 'name1', 'name2', 'name3')]
    if index == 8:
        assert all(e.signing == 'Einzelunterschrift' for e in events[1:])
        assert [e.payload['name'] for e in events[1:]] == [events[0].payload[k] for k in ('seller', 'buyer1', 'buyer2')]
    if index == 9:
        assert [e.payload['name'] for e in events[:3]] == ['Hentsch Carl Robert', 'Pattey Edouard R.', 'Tripod-Fatio Elisabeth']
        assert all(e.event_type == 'officer_removed' and e.signing is None for e in events[:3])
        assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in events[3:])
    if index == 10:
        assert events[0].payload['liquidation_name'].endswith(' in Liquidation')
        assert events[1].payload['corrected'] is True
        assert events[1].payload['name'] != events[1].payload['previous_name']
        assert events[1].role == 'Gesellschafter, Geschäftsführer, Liquidator'
        assert events[1].signing == 'Einzelunterschrift'
    if index == 11:
        assert events[1].payload['place'] == 'Neuenegg'
        assert events[2].signing == 'Kollektivunterschrift zu zweien'
        assert events[3].signing == 'ohne Unterschrift' and events[3].role == 'Gesellschafter'


@pytest.mark.parametrize('index,key,value', [(6, '20 de', '21 de'), (11, '78 Stammanteile', '79 Stammanteile'), (3, '1er juillet', '32 juillet'), (3, '14 janvier', '31 février')])
def test_inconsistent_totals_and_dates_rejected(index, key, value):
    _, (args, kwargs) = captured(index)
    changed = args[0].replace(key, value)
    assert changed != args[0]
    assert extract_parser411_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index,suffix', [(4, ', avec signature collective à deux'), (8, ' avec signature individuelle')])
def test_signing_requires_exact_source(index, suffix):
    _, (args, kwargs) = captured(index)
    for source in ('', kwargs['source_text'].replace(suffix, ''), kwargs['source_text'].replace(suffix, ' avec signature inconnue')):
        assert extract_parser411_leftovers(*args, source_text=source) == ([], args[0])


@pytest.mark.parametrize('version,text,language', [
    (234, "Les administrateurs Exemple Anne, nommé président et Exemple Beat, jusqu'ici président, continuent à signer collectivement à deux", 'fr'),
    (150, "L'assemblée générale a modifié une clause statutaire relative à une augmentation conditionnelle du capital (selon décision du 1 juillet 2013) par décision du 14 janvier 2021. Pour les détails, voir les statuts", 'fr'),
    (159, "L'assemblée générale a modifié une clause statutaire relative à une augmentation conditionnelle du capital (selon décision du 1 juillet 2013, modifiée le 2 juillet 2014) par décision du 14 janvier 2021. Pour les détails, voir les statuts", 'fr'),
])
def test_legacy_ownership_in_isolation(version, text, language):
    module = importlib.import_module(f'shab_analyzer.parser{version}')
    args = text, language, 'p', '', None, None, None
    events, rest = getattr(module, f'extract_parser{version}_leftovers')(*args)
    assert events and not rest.strip(' .')
    assert any(pattern.fullmatch(text) for pattern in _LEGACY)
    assert extract_parser411_leftovers(*args) == ([], text)


def test_existing_municipality_rule_keeps_ownership():
    text = 'Sitz neu: Beispiel. [Anpassung des Sitzes infolge Namensänderung der Gemeinde]'
    assert any(pattern.fullmatch(text) for pattern in _LEGACY)
    assert extract_parser411_leftovers(text, 'de', 'p', '', None, None, None) == ([], text)


@pytest.mark.parametrize('version', [276, 281, 282, 299, 328, 350, 376, 405, 408, 409, 410])
def test_previous_fixture_events_unchanged(version):
    import shab_analyzer.parse as parser
    module = importlib.import_module(f'tests.test_parser{version}')
    if hasattr(module, 'SUPPLIED_SHA256'):
        hashes = module.SUPPLIED_SHA256
        digests = hashes.values() if isinstance(hashes, dict) else hashes
        fixtures = [FIXTURES / (digest + '.xml') for digest in digests]
    elif hasattr(module, 'CASES') and hasattr(module, 'path'):
        fixtures = [module.path(case[0]) for case in module.CASES]
    else:
        fixtures = [FIXTURES / name for name in re.findall(r'[\da-f-]{36,64}\.xml', Path(module.__file__).read_text())]
    assert fixtures
    for fixture in fixtures:
        current = parse_publication_xml(fixture)
        with patch.object(parser, 'extract_parser411_leftovers', lambda text, *a, **kw: ([], text)):
            previous = parse_publication_xml(fixture)
        assert current == previous


@pytest.mark.parametrize('index', range(12))
def test_missing_optional_source(index):
    _, (args, _) = captured(index)
    events, rest = extract_parser411_leftovers(*args)
    if index in (4, 8):
        assert events == [] and rest == args[0]
    else:
        assert len(events) == COUNTS[index] and not rest
