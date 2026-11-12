import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser468 import extract_parser468_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '89ce6ac882c9cb489e7a27c564c70bcef445693584cf7ac4413b34ed9d8cc7cf', '8bb4f070db8be493d9d8774f0782f67efdbe36f44d408ddc67ebbdfbfb37152a', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'b5af3f0e6abf37341fde72077b4d3e04d6b5ec4345945a94a9e5a42269f775e9', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser468_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser468_leftovers', lambda text, *a, **kw: ([], text)):
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
    if index == 10:
        assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
        assert len(added) == 1 and rest == ''
        assert result.events == old.events + added
    else:
        assert (added, rest) == ([], args[0])
        assert result == old


def test_payload_and_missing_optional_metadata():
    assert PARSER_VERSION == 534
    _, _, (args, kwargs) = captured(10)
    events, rest = extract(*args, **kwargs)
    assert rest == '' and len(events) == 1
    event = events[0]
    assert event.event_type == 'organization_changed'
    assert event.rule_id == 'de.text.company_assets_two_contract_dates_no_consideration.v1'
    assert event.payload == {
        'action': 'company_assets_two_contract_dates_no_consideration',
        'agreement_date1': '13.02.2021', 'agreement_date2': '15.02.2021',
        'assets': "75'900.00", 'recipient': 'SWISSMOLE IMMO AG',
        'place': 'Schöftland', 'recipient_uid': 'CHE-426.449.214',
        'currency': 'CHF', 'consideration': 'keine',
    }
    assert 'liabilities' not in event.payload
    assert event.person_key is None and event.role is None and event.signing is None
    assert Event(**vars(event)) == event
    sparse, rest = extract(*args[:4], None, None, None)
    assert rest == '' and sparse[0].payload == event.payload
    assert sparse[0].org_uid is None and sparse[0].plz is None and sparse[0].canton is None
    legacy = Event(publication_id='legacy', published_at='', event_type='organization_changed',
                   rule_id='legacy', payload={'action': 'contribution_in_kind'})
    assert Event(**vars(legacy)) == legacy


def test_unsupported_input_unchanged():
    _, _, (args, kwargs) = captured(10)
    for text in ('', args[0] + ' UNKNOWN',
                 args[0].replace('13.02.2021', '31.02.2021'),
                 args[0].replace('15.02.2021', '31.02.2021'),
                 args[0].replace("75'900.00", '0'),
                 args[0].replace('an die', 'auf die'),
                 args[0].replace('Die Gesellschaft', 'Der Verein'),
                 args[0].replace('Gegenleistung: keine', 'Gegenleistung: CHF 100')):
        assert extract(text, *args[1:], **kwargs) == ([], text)
    assert extract(args[0], 'fr', *args[2:]) == ([], args[0])


def test_no_old_rule_consumes_new_formulation():
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(10)
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser468_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
        events, rest = old(*args, **options)
        assert not events and rest == args[0], name




@pytest.mark.parametrize('module,prefix', [('381', '0359dca5'), ('387', '4eb7c6d9')])
def test_old_transfer_rules_keep_ownership(module, prefix):
    import shab_analyzer.parse as parser
    paths = list(FIXTURES.glob(prefix + '*.xml'))
    assert len(paths) == 1
    name = 'extract_parser' + module + '_leftovers'
    old_extract = getattr(parser, name)
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return old_extract(*args, **kwargs)
    with patch.object(parser, name, capture):
        result = parse_publication_xml(paths[0])
    with patch.object(parser, 'extract_parser468_leftovers', lambda text, *a, **kw: ([], text)):
        baseline = parse_publication_xml(paths[0])
    assert result == baseline
    (args, kwargs), = calls
    assert old_extract(*args, **kwargs)[0]
    assert extract(*args, **kwargs) == ([], args[0])
