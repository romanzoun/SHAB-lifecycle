import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser413 import extract_parser413_leftovers as extract, _LEGACY

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = [
    '278194146bdcd54349f2306419ea6f301ec4f860ca960ec17792b5ea675587f6',
    '28d289ecb7640e5701f9f26851eac63e2381176b258c030e143ddc3af6eb5d91',
    '4271824d81deb54f8851cc0a61a89ed085f584a5cae7e01b3d4792831b45dd6e',
    '42f81310c42de319f7a7ce24ece333161188f422c7bb6179ce5de58156a87939',
    '5417f271194796d04f4758c9756cc508911a471089d7cc9584fa013ffc564e32',
    '62e6f1993ef4ed81405a25544aef535e76764195c2d6195e871d573f4cc4a479',
    '6a34a8a5c463c4ff538a8e4dd00a4fae6ec814415e39f59f6acf805beb5ac83e',
    '7dee72543665577ed5ef54b61921a5b669d5be3bf36b6deeb940091c32544f9b',
    '8658db7c954567528e1444e9dd3c23a763aa4498f36498170b72e4f6436cc10b',
    'ad8f598eabef635f7ec00f320055dc0f05b34310e536a005a0c22367a7872a8c',
    'f2e805a8e394d9c792a5be6702d5758cbfe01c9705e08e5dd5fc406e28b1e529',
    'fd92a97322550a76bfc9d7df4cdfd6b869de46fe16fab3fe7cb686efe903f21d',
]
COUNTS = [1, 2, 2, 1, 3, 1, 1, 1, 2, 1, 1, 1]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    with patch.object(parser, 'extract_parser413_leftovers', capture):
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
    added, rest = extract(*args, **kwargs)
    assert PARSER_VERSION == 425
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS[index] and not rest
    with patch.object(parser, 'extract_parser413_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (SUPPLIED_SHA256[index] + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('index', range(12))
def test_unknown_suffix_language_and_invalid_dates(index):
    _, (args, kwargs) = captured(index)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract(changed, *args[1:], **kwargs) == ([], changed)
    assert extract(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index', range(12))
def test_missing_optional_metadata_and_source(index):
    _, (args, kwargs) = captured(index)
    events, rest = extract(*args[:4], None, None, None, **kwargs)
    assert len(events) == COUNTS[index] and not rest
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    events, rest = extract(*args)
    if index in (0, 6, 9, 10):
        assert events == [] and rest == args[0]
    else:
        assert len(events) == COUNTS[index] and not rest


def test_old_event_without_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event


EXPECTED = [
    ('officer_changed', {'procuration_revoked': True}),
    ('officer_changed', {'name': 'Perriard Vincent'}),
    ('officer_changed', {'name': 'Schmidhauser Charles'}),
    ('officer_changed', {'corrected': True, 'previous_signing': 'Einzelunterschrift'}),
    ('officer_changed', {'signing_restrictions_removed': True}),
    ('status_changed', {'deleted': True, 'reason': 'not_required_to_register'}),
    ('capital_changed', {'count': "73'508", 'security_kind': 'bons de jouissance', 'transfer_restricted': True, 'liquidation_proceeds_right': True}),
    ('ownership_changed', {'associate_uid': 'CHE-115.846.035', 'corrected': True}),
    ('ownership_changed', {'count': '100', 'before': '200', 'remaining': '100', 'currency': 'CHF'}),
    ('capital_changed', {'capital': "100'000", 'count': "100'000", 'nominal': '1', 'previous_count': '100', 'previous_nominal': "1'000", 'transfer_restricted': True}),
    ('officer_changed', {'origin': 'Estavayer'}),
    ('organization_changed', {'correct_publication': '1005100198', 'previous_publication': '1005034270', 'corrected': True}),
]


@pytest.mark.parametrize('index', range(12))
def test_payload_semantics(index):
    _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    kind, fields = EXPECTED[index]
    assert not rest and events[0].event_type == kind
    for key, value in fields.items():
        assert events[0].payload[key] == value
    if index in (0, 1, 2, 3, 4):
        assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in events)
    if index == 10:
        assert events[0].signing is None
    if index == 8:
        assert events[1].signing == 'ohne Unterschrift'


LEGACY_TEXTS = [
    "Rectification: l'inscription n° 1067 du 01.02.2021 (FOSC du 04.02.2021, Id. 1005091814) est rectifiée comme suit: Said Adam, administratrice, signature collective à deux (et non pas signature individuelle).",
    'Gisiger Aline, directeur général et Jaeger Daniel, directeur, signent désormais collectivement à deux sans autre restriction; leurs pouvoirs sont modifiés en ce sens.',
    "Les membres du conseil de fondation Schmidhauser Charles, nommé président et Dramé Bernard, jusqu'ici président, continuent à signer collectivement à deux.",
    'Leibzig Pascal, qui est maintenant de Estavayer, est nommé liquidateur.',
]


@pytest.mark.parametrize('pattern,text', list(zip(_LEGACY, LEGACY_TEXTS)))
def test_legacy_boundaries_without_active_old_rule(pattern, text):
    assert pattern.fullmatch(text)
    assert extract(text, 'fr', 'p', '', None, None, None) == ([], text)


@pytest.mark.parametrize('index', [0, 6, 9])
def test_source_evidence_required(index):
    _, (args, kwargs) = captured(index)
    assert extract(*args, source_text='unrelated') == ([], args[0])
    changed = kwargs['source_text'].replace('collective à deux', 'individuelle').replace('liées selon statuts', 'librement transmissibles')
    assert extract(*args, source_text=changed) == ([], args[0])


@pytest.mark.parametrize('index,key,value', [(8, 'before', '201'), (9, 'capital', "100'001")])
def test_inconsistent_capital_or_holdings_rejected(index, key, value):
    _, (args, kwargs) = captured(index)
    events, _ = extract(*args, **kwargs)
    changed = args[0].replace(events[0].payload[key], value)
    source = kwargs['source_text'].replace(events[0].payload[key], value)
    assert extract(changed, *args[1:], source_text=source) == ([], changed)


def test_parser401_signing_variant_remains_legacy_owned():
    from shab_analyzer.parser401 import extract_parser401_leftovers
    text = 'Leibzig Pascal, maintenant de Estavayer, est nommé liquidateur'
    source = text + ' avec signature individuelle.'
    args = text, 'fr', 'p', '', None, None, None
    old, rest = extract_parser401_leftovers(*args, source_text=source)
    assert len(old) == 1 and not rest
    assert old[0].signing == 'Einzelunterschrift'
    assert extract(*args, source_text=source) == ([], text)
