import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser441 import extract_parser441_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '384c2df3999d3936131f04916e6a38ac876aa6594f1c11fa88657884af3e1b8d', '63714099c0cc372e87d21f0c1f7c3880f26bbf2de139bcde7838f3d71f446a6f', '7bbd56ddeab760643e500d0509b0fb8aa9de414b27e164960457417071580820', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a341287297ba96e1938916b070b26a6384cd05b7aad34facefaf830c80dd6cf8', 'c44cc9dec2738243febcf880ff9aeb67c7ecaf8b9884dad028b65246c91edbf3', 'cea1eecf4c4de42fa350ecc637f6251dad434ba1a70b4c894bf12b4d6b7de9e7', 'd5c4865c6ecf8a33ac04ba8bd26bb2872b72c301bd9164ba98089bd66661f05c', 'e15b931599f28559edd40030a90b06be634d25e70df3cadb089b53df5bfdfe46', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
COUNTS = [0, 0, 0, 1, 1, 0, 0, 1, 3, 1, 2, 0]
NEW_CASES = [i for i, count in enumerate(COUNTS) if count]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser441_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser441_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(path)
    assert len(calls) == 1
    return result, old, calls[0]


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('index', NEW_CASES)
def test_complete_and_unchanged_old_payloads(index):
    result, old, (args, kwargs) = captured(index)
    added, rest = extract(*args, **kwargs)
    assert PARSER_VERSION == 443
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    assert len(added) == COUNTS[index] and rest == ''
    assert old.leftover_text == args[0]
    assert result.events == old.events + added
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('index', NEW_CASES)
def test_unknown_suffix_language_and_invalid_dates(index):
    _, _, (args, kwargs) = captured(index)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract(changed, *args[1:], **kwargs) == ([], changed)
    assert extract(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index', NEW_CASES)
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


@pytest.mark.parametrize('index', NEW_CASES)
def test_no_overlap_with_old_rules_even_in_isolation(index):
    # Exercise every historical extractor on the complete clause in isolation.
    import inspect
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(index)
    for name, old_extract in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser441_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name


@pytest.mark.parametrize('index,owner', [(0, 60), (1, 55), (2, 55), (5, 55), (6, 60), (11, 55)])
def test_existing_formulations_retain_historical_ownership(index, owner):
    import importlib
    result, old, (args, kwargs) = captured(index)
    old_extract = getattr(importlib.import_module(f'shab_analyzer.parser{owner}'), f'extract_parser{owner}_leftovers')
    owned_args = (kwargs['source_text'], *args[1:]) if index == 5 else args
    expected = old_extract(*owned_args)
    assert expected[0] or expected[1] != owned_args[0]
    assert extract(*args, **kwargs) == ([], args[0])
    assert result == old
    assert result.status == 'PARTIALLY_PARSED'
    assert old_extract(*owned_args) == expected




@pytest.mark.parametrize('index,event_type,expected', [
    (3, 'officer_changed', {'name': 'Froidevaux Pierre Henri', 'previous_name': 'Froidevaud Pierre Henri', 'entry_date': '10.03.2021', 'notice_ref': '0/1005124238'}),
    (4, 'officer_changed', {'origin': 'Grand-Saconnex', 'place': 'Grand-Saconnex'}),
    (7, 'officer_changed', {'name': 'Quinodoz Brice'}),
    (8, 'status_changed', {'decision_date': '31.12.2020', 'dissolved': True, 'liquidation_name': 'A.P.L Antonio & Dolores LOBATO, en liquidation'}),
    (9, 'officer_changed', {'name': 'Donataccio, Matteo', 'origin': 'cittadino italiano'}),
    (10, 'officer_changed', {'name': 'Empain Anne Elisabeth Marie Juliette', 'origin': 'Yverdon-les-Bains'}),
])
def test_evidenced_semantics(index, event_type, expected):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    assert rest == '' and events[0].event_type == event_type
    for key, value in expected.items():
        assert events[0].payload[key] == value
    if index == 8:
        assert all(e.signing is None for e in events)
        assert [e.payload['name'] for e in events[1:]] == ['Lobato Maria Dolores', 'Lobato Perez Antonio']
    if index == 10:
        assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in events)
        assert events[1].payload['place'] == 'Zürich'
    if index == 9:
        assert events[0].role == 'amministratore unico'
        assert events[0].signing == 'Einzelunterschrift'


def test_historical_manager_correction_is_not_taken():
    from shab_analyzer.parser205 import extract_parser205_leftovers
    _, _, (args, kwargs) = captured(3)
    text = args[0].replace('FOSC. du', 'FOSC du').replace('2021 p.', '2021, p.').replace("l'administrateur président", 'le gérant')
    assert extract(text, *args[1:], **kwargs) == ([], text)
    events, rest = extract_parser205_leftovers(text, *args[1:])
    assert events and rest == ''
