import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser463 import extract_parser463_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = '''02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11
1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e
2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3
31bc228c95a083db1a4f10db79c75cd34ab0f92b45004c2eb04de53cc4a8079d
3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232
7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad
88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7
8bb4f070db8be493d9d8774f0782f67efdbe36f44d408ddc67ebbdfbfb37152a
8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f
a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5
f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed
89ce6ac882c9cb489e7a27c564c70bcef445693584cf7ac4413b34ed9d8cc7cf'''.split()


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser463_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser463_leftovers', lambda text, *a, **kw: ([], text)):
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
    if index == 3:
        assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
        assert len(added) == 1 and rest == ''
        assert result.events == old.events + added
    else:
        assert (added, rest) == ([], args[0])
        assert result == old


def test_payload_and_optional_metadata():
    assert PARSER_VERSION == 531
    _, _, (args, kwargs) = captured(3)
    events, rest = extract(*args, **kwargs)
    assert rest == '' and len(events) == 1
    event = events[0]
    assert event.event_type == 'status_changed'
    assert event.rule_id == 'de.text.bankruptcy_company_reinstated_former_law.v1'
    assert event.payload == {
        'kind': 'bankruptcy_company_reinstated', 'deleted_date': '2021-03-02',
        'decision_date': '2021-04-01', 'authority': 'Einzelrichters am Kantonsgericht',
        'bankruptcy_date': '2021-04-01', 'bankruptcy_time': '14:00',
        'legal_basis': 'Art. 159 aHRegV', 'dissolved_by_bankruptcy': True,
        'registry_reinstated': True, 'source_typo': 'Konkurseröffung',
    }
    optional, rest = extract(*args[:4], None, None, None)
    assert rest == '' and optional[0].payload == event.payload
    assert optional[0].org_uid is None and optional[0].plz is None and optional[0].canton is None
    assert Event(**vars(event)) == event
    assert extract(*args) == (events, '')


def test_invalid_inputs():
    _, _, (args, kwargs) = captured(3)
    for text in (args[0] + ' UNKNOWN', args[0].replace('01.04.2021', '31.02.2021'),
                 args[0].replace('1. April', '31. April'),
                 args[0].replace('14.00', '24.00')):
        assert extract(text, *args[1:], **kwargs) == ([], text)
    assert extract(args[0], 'fr', *args[2:]) == ([], args[0])


def test_no_old_rule_consumes_new_formulation():
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(3)
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser463_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
        events, rest = old(*args, **options)
        assert not events and rest == args[0], name


def test_legacy_ownership_and_payload_compatibility():
    from shab_analyzer.parser463 import _LEGACY
    from shab_analyzer.parser97 import extract_parser97_leftovers
    _, _, (args, _) = captured(3)
    base = args[0].replace('aHRegV', 'HRegV').replace('Konkurseröffung', 'Konkurseröffnung').replace('1. April 2021', '01.04.2021')
    variants = [base, base + '. [bisher: Frühere Eintragung.]',
                base.split(', 14.00')[0],
                base.replace('Datum der Konkurseröffnung', 'Das mit Entscheid vom 01.03.2021 mangels Aktiven eingestellte Verfahren wird wieder eröffnet. Datum der Konkurseröffnung'),
                base.replace('Konkurseröffnung', 'Konkuseröffnung')]
    for pattern, text in zip(_LEGACY, variants):
        assert pattern.fullmatch(text)
        assert extract(text, *args[1:]) == ([], text)
    old, rest = extract_parser97_leftovers(base, *args[1:])
    assert len(old) == 1 and rest == ''
    new, _ = extract(*args)
    expected = dict(new[0].payload, legal_basis='Art. 159 HRegV')
    expected.pop('source_typo')
    assert 'source_typo' not in old[0].payload
    assert Event(**vars(old[0])) == old[0]
    assert old[0].payload == expected


@pytest.mark.parametrize('fixture', [
    '8f8bac61-5c66-45c0-b97b-160405871bab',
    'e59a393c-855e-48e1-8072-feaf42425a13',
    'fb0f2927-d83e-4a87-bc75-b60907fcc3f4',
    '6fe6200b-7ea5-4cfa-89a2-9caa8fdb6894',
    '6aea1597-0b3f-4d44-9b68-2666d539ed63',
])
def test_legacy_pipeline_equal(fixture):
    import shab_analyzer.parse as parser
    path = FIXTURES / (fixture + '.xml')
    result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser463_leftovers', lambda text, *a, **kw: ([], text)):
        baseline = parse_publication_xml(path)
    assert result == baseline
