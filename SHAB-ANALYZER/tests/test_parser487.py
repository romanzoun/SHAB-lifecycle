import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser487 import extract_parser487_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3c29d78b364aad990e2a5c34d846688088a5adf909328bf1cbf30e5f5edf9fe9', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '89ce6ac882c9cb489e7a27c564c70bcef445693584cf7ac4413b34ed9d8cc7cf', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser487_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser487_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert PARSER_VERSION == 525
    _, _, (args, kwargs) = captured(3)
    events, rest = extract(*args, **kwargs)
    assert rest == '' and len(events) == 1
    event = events[0]
    assert event.event_type == 'status_changed'
    assert event.payload == {
        'kind': 'repudiated_estate_liquidation_ordered', 'procedure': 'bankruptcy_office',
        'decision_date': '2021-04-22',
        'authority': "Président du Tribunal d'arrondissement de Lausanne, à Lausanne",
        'scope': 'owner_estate',
    }
    assert Event(**vars(event)) == event
    sparse, _ = extract(*args[:4], None, None, None)
    assert sparse[0].payload == event.payload
    assert sparse[0].org_uid is None and sparse[0].plz is None and sparse[0].canton is None
    assert extract(*args) == (events, rest)
    legacy = Event('legacy', '', 'status_changed', 'legacy', payload={
        'kind': 'repudiated_estate_liquidation_ordered', 'procedure': 'bankruptcy_office',
        'decision_date': '2021-04-22', 'authority': 'Tribunal', 'scope': 'owner_estate',
    })
    assert Event(**vars(legacy)) == legacy


def test_no_old_rule_owns_input():
    import shab_analyzer.parse as parser
    from shab_analyzer.text_extras import extract_text_extras
    _, _, (args, kwargs) = captured(3)
    assert extract_text_extras(*args, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser487_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
        assert old(*args, **options) == ([], args[0]), name


def test_unsupported_input():
    _, _, (args, kwargs) = captured(3)
    for text in ('', args[0] + '. UNKNOWN', args[0].replace('22.04.2021', '31.02.2021'),
                 args[0].replace('succession répudiée', 'succession'),
                 args[0].replace("l'Office des faillites", "un tiers")):
        assert extract(text, *args[1:], **kwargs) == ([], text)
    for language in ('de', 'it', None):
        assert extract(args[0], language, *args[2:], **kwargs) == ([], args[0])


def test_legacy_boundary():
    from shab_analyzer.parser130 import _FR_REPUDIATED_ESTATE_BANKRUPTCY, extract_parser130_leftovers
    _, _, (args, _) = captured(3)
    text = ("Par décision du 22.04.2021 prononcée par le Tribunal, "
            "la succession répudiée du titulaire sera liquidée selon les règles de la faillite")
    assert _FR_REPUDIATED_ESTATE_BANKRUPTCY.search(text)
    assert extract_parser130_leftovers(text, *args[1:])[0]
    assert extract(text, *args[1:]) == ([], text)


def test_legacy_pipeline_unchanged():
    import shab_analyzer.parse as parser
    from shab_analyzer.parser130 import _FR_REPUDIATED_ESTATE_BANKRUPTCY
    from xml.etree import ElementTree
    _, _, (args, _) = captured(3)
    root = ElementTree.parse(FIXTURES / (DIGESTS[3] + '.xml'))
    for element in root.iter():
        if element.tag == 'publicationText':
            element.text = element.text.replace(args[0] + '.',
                "Par décision du 22.04.2021 prononcée par le Tribunal, la succession répudiée du titulaire sera liquidée selon les règles de la faillite.")
            assert _FR_REPUDIATED_ESTATE_BANKRUPTCY.search(element.text.split('). ')[-1])
    # Use only a local fixture and an ephemeral file, never the sample source directory.
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'legacy.xml'
        root.write(path, encoding='utf-8')
        result = parse_publication_xml(path)
        with patch.object(parser, 'extract_parser487_leftovers', lambda text, *a, **kw: ([], text)):
            assert result == parse_publication_xml(path)


def test_text_extras_boundary():
    from shab_analyzer.text_extras import _FR_REPUDIATED_ESTATE_LIQUIDATION
    text = ("Le président du Tribunal d'arrondissement de Lausanne a ordonné "
            "la liquidation de la succession répudiée du titulaire de cette entreprise "
            "individuelle par l'Office des faillites le 22.04.2021")
    assert _FR_REPUDIATED_ESTATE_LIQUIDATION.search(text)
    assert extract(text, 'fr', 'legacy', '', None, None, None) == ([], text)


@pytest.mark.parametrize('stem', [
    '184ab540-5de7-4995-b11a-b071b09fe339',
    'ed2116a6-005d-4a50-83e2-d4e025a54f11',
    '067ccd6e-4ac1-46ad-af56-5bf03828c4c9',
])
def test_existing_estate_fixtures_unchanged(stem):
    import shab_analyzer.parse as parser
    path = FIXTURES / (stem + '.xml')
    result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser487_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(path)
