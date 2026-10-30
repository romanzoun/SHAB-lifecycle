import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser428 import extract_parser428_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['01ce10600e4510de4756c18a2ac716f3ba2110ff4d5e887ffd080940f193637d', '09ac4f2a3b60080782652c42366642c7f1b1a7afd8902dd3d491b1a82c109c28', '0e683b678ecff402b7fc92ad341891389776d07e2ec66fe5e92ff46454482402', '3db790bc814de5d600e46fbad2bfd18d61ea4495b19b48139a3d5c58a301f402', '5828addebc3fb7a46637c708b17061c4f4948434e829ba0472dc5f2a0e3223dd', '78300015649456bba958f0a56fee7ad0bf05945f679583f4cc16873a44123555', 'a1b87b0d5879170f015ac55678474d1032cfa7766322516b3236673f248b3db4', 'a239fbad2025f1152c774750119ccdd5b844fa2c10f0d03685791e985ede7f4b', 'c5680ada44e6ecf1272c2b7dafee78d94c103d74cbacf89e419c6bf16caa91a7', 'ccc92b9160e58bc3297db40f736c0728b3b4e02d1ab00258d7b0f3461383bcd4', 'e16b4069c37f905a6d01560c187774914156fc97a1a06e63046dbd330106eed4', 'f93df3e971722a7a24fa9d65d58004a2f084b5815fb572e5e67dfdc443135b7f']
COUNTS = [1, 1, 1, 2, 2, 3, 1, 2, 1, 1, 1, 1]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser428_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser428_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert PARSER_VERSION == 442
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
    if index in (9, 10):
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
        if not name.startswith('extract_parser') or name == 'extract_parser428_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name


@pytest.mark.parametrize('index', [9, 10])
def test_source_required(index):
    _, _, (args, _) = captured(index)
    assert extract(*args, source_text='Unrelated source.') == ([], args[0])


@pytest.mark.parametrize('index', range(12))
def test_payload_semantics(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    p = events[0].payload
    assert rest == ''
    expected = ['status_changed', 'ownership_changed', 'ownership_changed',
                'officer_changed', 'ownership_changed', 'ownership_changed',
                'status_changed', 'ownership_changed', 'status_changed',
                'organization_changed', 'capital_changed', 'assets_transferred']
    assert events[0].event_type == expected[index]
    if index == 0:
        assert p['provisional'] is True and p['until_date'] == '11.04.2021'
    if index in (1, 4, 5):
        assert int(p['before']) == int(p['count']) + int(p['remaining'])
    if index == 2:
        assert p['buyer_signing'] == 'ohne Zeichnungsberechtigung'
        assert (p['count'], p['remaining'], p['nominal']) == ('8', '12', "1'000")
    if index == 3:
        assert [e.role for e in events] == ['vice-président', 'président']
        assert all(e.signing == 'Einzelunterschrift' for e in events)
    if index == 4:
        assert events[1].role == 'associée-gérante présidente'
        assert events[1].signing is None
    if index == 5:
        assert [e.role for e in events[1:]] == ['président', 'gérant']
        assert all(e.signing is None for e in events[1:])
    if index == 6:
        assert p['months'] == 'drei' and p['effective_date'] == '01.03.2021'
        assert 'provisional' not in p
    if index == 7:
        assert int(p['removed_count']) + int(p['before']) == int(p['count'])
        assert events[1].signing == 'Einzelunterschrift'
    if index == 8:
        assert p['dissolution_revoked'] is True and p['decision_month'] == 'Juli'
    if index == 9:
        assert p['historical'] is True
        assert 'name' not in p
    if index == 10:
        assert p['corrected'] is True
        assert p['reserve_type'] == 'autres réserves issues du capital (agio)'
        assert p['share_restriction'] == 'liées selon statuts'
    if index == 11:
        assert p['no_liabilities'] is True
        assert p['assets'] == p['consideration'] == "631'834.00"


def test_legacy_pattern_ownership():
    from shab_analyzer.parser213 import extract_parser213_leftovers
    text = ('Mit Entscheid vom 08.03.2021 hat der Einzelrichter die gewährte '
            'provisorische Nachlassstundung um drei Monate bis zum 11.04.2021 verlängert')
    events, rest = extract_parser213_leftovers(text, 'de', 'p', '', None, None, None)
    assert events and rest == ''
    padded = '  ' + text + '  '
    assert extract(padded, 'de', 'p', '', None, None, None) == ([], padded)

@pytest.mark.parametrize('version,text,language', [
    (379, 'Mit Entscheid vom 01.01.2021 hat der Einzelrichter am Kantonsgericht die provisorische Nachlassstundung bis 01.03.2021 verlängert', 'de'),
    (105, 'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vermögensübertragungsvertrag vom 15.10.2020 Aktiven von CHF 100 auf die Beispiel AG, in Bern (CHE-123.456.789). Gegenleistung: CHF 100', 'de'),
    (324, 'Administration: Test Anna, maintenant originaire de Lausanne, nommée présidente et Test Paul, de Lausanne, à Genève, lesquels signent individuellement', 'fr'),
])
def test_related_old_rules_keep_ownership(version, text, language):
    import importlib
    old = getattr(importlib.import_module(f'shab_analyzer.parser{version}'), f'extract_parser{version}_leftovers')
    args = text, language, 'p', '', None, None, None
    events, rest = old(*args)
    assert events and rest == ''
    assert extract(*args) == ([], text)


def test_invalid_written_date():
    _, _, (args, kwargs) = captured(8)
    changed = args[0].replace('02. Juli', '32. Juli')
    assert extract(changed, *args[1:], **kwargs) == ([], changed)


def test_correction_source_must_match_share_amount():
    _, _, (args, kwargs) = captured(10)
    source = kwargs['source_text'].replace("il est remis à l'apporteur 5'100", "il est remis à l'apporteur 5'101")
    assert extract(*args, source_text=source) == ([], args[0])


def test_historical_source_must_contain_same_officer():
    _, _, (args, kwargs) = captured(9)
    source = kwargs['source_text'].replace('Fischer, Klaus', 'Beispiel, Anna')
    assert extract(*args, source_text=source) == ([], args[0])
