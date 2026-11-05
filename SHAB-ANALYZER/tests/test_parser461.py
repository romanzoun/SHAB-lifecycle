import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser461 import extract_parser461_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = '''02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11
1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e
2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3
31bc228c95a083db1a4f10db79c75cd34ab0f92b45004c2eb04de53cc4a8079d
3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232
52ba9d35ed7913498a52ef2c292cc4ab4b6ff9d2ce3aed9b105f04dead1f8cff
7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad
88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7
8bb4f070db8be493d9d8774f0782f67efdbe36f44d408ddc67ebbdfbfb37152a
8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f
a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5
f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed'''.split()


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser461_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser461_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(path)
    assert len(calls) == 1
    return result, old, calls[0]


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('index', range(12))
def test_pipeline_preserves_existing_events(index):
    result, old, (args, kwargs) = captured(index)
    added, rest = extract(*args, **kwargs)
    if index == 5:
        assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
        assert len(added) == 1 and rest == ''
        assert result.events == old.events + added
    else:
        assert (added, rest) == ([], args[0])
        assert result == old


def test_payload_and_optional_metadata():
    assert PARSER_VERSION == 485
    _, _, (args, kwargs) = captured(5)
    events, rest = extract(*args, **kwargs)
    assert rest == '' and len(events) == 1
    event = events[0]
    assert event.event_type == 'status_changed'
    assert event.rule_id == 'de.text.company_reinstated_credit_realization.v1'
    assert event.payload == {
        'kind': 'registration_reinstated', 'action': 'reinstated',
        'reason': 'credit_realization', 'deletion_date': '2013-07-08',
        'decision_date': '2021-02-23',
        'authority': 'Einzelrichters des Bezirksgerichts Bülach',
        'company_continues': True, 'registry_reinstated': True,
        'previous': 'Nachdem kein begründeter Einspruch gegen die Löschung erhoben wurde, wird die Gesellschaft im Sinne von Art. 159 Abs. 5 lit. a HRegV von Amtes wegen gelöscht.',
    }
    optional, rest = extract(*args[:4], None, None, None)
    assert rest == '' and optional[0].payload == event.payload
    assert optional[0].org_uid is None and optional[0].plz is None and optional[0].canton is None
    assert Event(**vars(optional[0])) == optional[0]
    legacy = Event('p', '', 'status_changed', 'legacy', payload={'kind': 'registration_reinstated', 'action': 'reinstated'})
    assert Event(**vars(legacy)) == legacy
    assert 'reason' not in legacy.payload
    assert extract(*args) == (events, '')


def test_unknown_input_and_invalid_dates():
    _, _, (args, kwargs) = captured(5)
    for text in (args[0] + ' UNKNOWN', args[0].replace('Verwertung eines Guthabens', 'Liquidation'),
                 args[0].replace('08.07.2013', '31.02.2013'),
                 args[0].replace('23.02.2021', '31.02.2021'),
                 args[0].replace('159 Abs. 5 lit. a', '155')):
        assert extract(text, *args[1:], **kwargs) == ([], text)
    assert extract(args[0], 'fr', *args[2:]) == ([], args[0])


def test_no_old_rule_consumes_new_formulation():
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(5)
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser461_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
        events, rest = old(*args, **options)
        assert not events and rest == args[0], name


@pytest.mark.parametrize('number', [260, 376])
def test_old_reinstatement_rules_keep_ownership(number):
    import shab_analyzer.parse as parser
    old_extract = getattr(parser, f'extract_parser{number}_leftovers')
    checked = 0
    for prefix in {260: ['bc0f2ee2'], 376: ['4da7e6fc']}[number]:
        path, = FIXTURES.glob(prefix + '*.xml')
        calls = []
        def capture(*args, **kwargs):
            calls.append((args, kwargs))
            return [], args[0]
        with patch.object(parser, old_extract.__name__, capture):
            parse_publication_xml(path)
        args, kwargs = calls[0]
        if 'wieder in das Handelsregister eingetragen' not in args[0]:
            continue
        assert old_extract(*args, **kwargs)[0]
        assert extract(*args, **kwargs) == ([], args[0])
        result = parse_publication_xml(path)
        with patch.object(parser, 'extract_parser461_leftovers', lambda text, *a, **kw: ([], text)):
            baseline = parse_publication_xml(path)
        assert result == baseline
        checked += 1
    assert checked
