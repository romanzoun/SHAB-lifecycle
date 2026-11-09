import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser479 import extract_parser479_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6464997c8de4d0bdf7c0d3bebe2d934a680745dc8918faf6181033dd0090b681', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '89ce6ac882c9cb489e7a27c564c70bcef445693584cf7ac4413b34ed9d8cc7cf', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser479_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser479_leftovers', lambda text, *a, **kw: ([], text)):
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
    if index == 4:
        assert len(added) == 1
        later = list(result.events)
        for event in old.events + added:
            later.remove(event)
        own = {event.rule_id for event in added}
        assert all(event.rule_id not in own for event in later)
        assert rest.strip(' .').endswith(result.leftover_text)
    else:
        assert (added, rest) == ([], args[0])
        assert result == old


def test_payload_and_optional_metadata():
    assert PARSER_VERSION == 514
    _, _, (args, kwargs) = captured(4)
    events, rest = extract(*args, **kwargs)
    assert rest == '' and len(events) == 1
    event = events[0]
    assert event.event_type == 'company_identifier_changed'
    assert event.payload == {'scope': 'organization', 'from': 'CH-550-1118035-0',
                             'to': 'CHE-113.916.682'}
    assert Event(**vars(event)) == event
    sparse, _ = extract(*args[:4], None, None, None)
    assert sparse[0].payload == event.payload
    assert sparse[0].org_uid is None and sparse[0].plz is None and sparse[0].canton is None
    assert extract(*args) == (events, rest)
    legacy = Event('legacy', '', 'company_identifier_changed', 'legacy',
                   payload={'scope': 'organization', 'from': 'CHE-123.456.789', 'to': 'CHE-987.654.321'})
    assert Event(**vars(legacy)) == legacy
    assert 'previous_registry_id' not in legacy.payload


def test_no_old_rule_owns_input():
    import shab_analyzer.parse as parser
    from shab_analyzer.text_extras import extract_text_extras
    _, _, (args, kwargs) = captured(4)
    # The generic header cleanup discards this standalone clause but emits no event.
    assert extract_text_extras(*args, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser479_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
        assert old(*args, **options) == ([], args[0]), name


def test_unsupported_input():
    _, _, (args, kwargs) = captured(4)
    for text in ('', args[0] + ' UNKNOWN', args[0].replace('CH-550-1118035-0', 'CH-invalid'),
                 args[0].replace('CHE-113.916.682', 'CHE-invalid')):
        assert extract(text, *args[1:]) == ([], text)
    for language in ('de', 'it', None):
        assert extract(args[0], language, *args[2:]) == ([], args[0])


@pytest.mark.parametrize('module,text', [
    ('parser283', "L'identification de la société au siège principal sous le numéro CH-550-1118035-0 est remplacée par le numéro d'identification des entreprises (IDE/UID) CHE-113.916.682"),
    ('parser401', "L'identification de la succursale de Lausanne sous le numéro CH-550-1118035-0 est remplacée par le numéro d'identification des entreprises (IDE/UID) CHE-113.916.682"),
    ('parser51', 'Le numéro d\'identification CH-550-1118035-0 de l\'organe de révision "Audit SA" à Lausanne est remplacé par le numéro d\'identification des entreprises (IDE/UID) CHE-113.916.682'),
])
def test_legacy_boundary(module, text):
    import importlib
    old = getattr(importlib.import_module('shab_analyzer.' + module), 'extract_' + module + '_leftovers')
    args = ('fr', 'fixture', '', None, None, None)
    expected = old(text, *args)
    assert expected[0]
    assert extract(text, *args) == ([], text)
    assert old(extract(text, *args)[1], *args) == expected

def test_existing_auditor_fixture_relative():
    import shab_analyzer.parse as parser
    path = FIXTURES / '51a94d41-4217-4543-bdfb-81e1c92484a4.xml'
    result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser479_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(path)
