import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser493 import extract_parser493_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'c50c64167183d4486e793324615a7102a0098ad55c1c6ff2bb3f49ac3df72bba', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser493_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser493_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert PARSER_VERSION == 516
    _, _, (args, kwargs) = captured(10)
    events, rest = extract(*args, **kwargs)
    assert len(events) == 1 and rest == ''
    event = events[0]
    assert event.event_type == 'statutes_changed'
    assert event.rule_id == 'fr.text.contribution_clause_repealed_art628.v1'
    assert event.payload == {
        'kind': 'contribution_in_kind', 'action': 'removed',
        'legal_basis': '628, al. 4, CO',
        'previous': "La société se propose d'acquérir de Damien Berclaz, d'Adolphe, à Montana, la parcelle art. 8215, No 11, Montagnette, place 1'380 m2 pour le prix en bloc de CHF 25'000.--, montant payé par remise à l'apporteur de 25 actions au porteur de CHF 1'000.-- chacune, entièrement libérées",
    }
    assert Event(**vars(event)) == event
    sparse, _ = extract(*args[:4], None, None, None)
    assert sparse[0].payload == event.payload
    assert (sparse[0].org_uid, sparse[0].plz, sparse[0].canton) == (None, None, None)
    assert extract(*args) == (events, rest)
    legacy = Event('legacy', '', 'statutes_changed', 'legacy', payload={
        'kind': 'contribution_in_kind', 'action': 'removed', 'previous': 'Legacy',
    })
    assert Event(**vars(legacy)) == legacy
    assert 'legal_basis' not in legacy.payload


def test_no_old_rule_owns_input():
    import shab_analyzer.parse as parser
    from shab_analyzer.text_extras import extract_text_extras
    _, _, (args, kwargs) = captured(10)
    assert extract_text_extras(*args, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser493_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
        assert old(*args, **options) == ([], args[0]), name


@pytest.mark.parametrize('transform', [
    lambda t: '', lambda t: t + ' UNKNOWN',
    lambda t: t.replace('Abrogation', 'Modification'),
    lambda t: t.replace('al. 4', 'al. 3'),
    lambda t: t.replace('apports en nature', 'reprises de biens'),
    lambda t: t.replace("se propose d'acquérir", 'reprend'),
    lambda t: t.replace(']', ''),
])
def test_unsupported_input(transform):
    _, _, (args, kwargs) = captured(10)
    text = transform(args[0])
    assert extract(text, *args[1:], **kwargs) == ([], text)


@pytest.mark.parametrize('language', ['it', 'de', None])
def test_other_languages(language):
    _, _, (args, kwargs) = captured(10)
    assert extract(args[0], language, *args[2:], **kwargs) == ([], args[0])


@pytest.mark.parametrize('module,pattern_name,text', [
    ('parser66', '_FR_QUALIFIED_FACT_REMOVED', "Nouveaux faits qualifiés: [La disposition statutaire sur les apports en nature et la reprise de biens lors de la fondation du 01.01.2000 est abrogée] [biffé: Apport en nature: ancien apport]"),
    ('parser113', '_FR_REMOVED_QUALIFIED_FACT', "Nouveaux faits qualifiés: [biffé: Apport en nature: ancien apport]"),
    ('parser170', '_FR_CONTRIBUTION_AND_ASSET_ACQUISITION_CLAUSE_REPEALED', "Nouveaux faits qualifiés: [Abrogation de la clause d'apport en nature et de reprise de biens] [biffé: apport en nature: selon convention du 01.01.2000 et inventaire, sont apportés pour CHF 100.- des biens; apport accepté pour ce prix et payé par remise à l'apporteur de 1 actions imputées sur le capital]"),
])
def test_legacy_boundary(module, pattern_name, text):
    import importlib
    import shab_analyzer.parse as parser
    old = importlib.import_module('shab_analyzer.' + module)
    assert getattr(old, pattern_name).fullmatch(text)
    args = (text, 'fr', 'fixture', '', None, None, None)
    assert getattr(old, 'extract_' + module + '_leftovers')(*args)[0]
    assert extract(*args) == ([], text)
    path = FIXTURES / (DIGESTS[10] + '.xml')
    from tempfile import TemporaryDirectory
    import xml.etree.ElementTree as ET
    with TemporaryDirectory() as directory:
        tree = ET.parse(path)
        tree.find('.//publicationText').text = text
        local = Path(directory) / 'boundary.xml'
        tree.write(local, encoding='utf-8')
        result = parse_publication_xml(local)
        with patch.object(parser, 'extract_parser493_leftovers', lambda text, *a, **kw: ([], text)):
            assert result == parse_publication_xml(local)


def test_text_extras_boundary(tmp_path):
    import xml.etree.ElementTree as ET
    import shab_analyzer.parse as parser
    from shab_analyzer.text_extras import _FR_CONTRIBUTION_RULES_REMOVED, extract_text_extras
    text = "La clause statutaire relative à l'apport en nature à la constitution est abrogée conformément à l'art. 628, al. 4, CO."
    assert _FR_CONTRIBUTION_RULES_REMOVED.fullmatch(text)
    args = (text, 'fr', 'fixture', '', None, None, None)
    assert extract_text_extras(*args, set())[0]
    assert extract(*args) == ([], text)
    tree = ET.parse(FIXTURES / (DIGESTS[10] + '.xml'))
    tree.find('.//publicationText').text = text
    local = tmp_path / 'boundary.xml'
    tree.write(local, encoding='utf-8')
    result = parse_publication_xml(local)
    with patch.object(parser, 'extract_parser493_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(local)
