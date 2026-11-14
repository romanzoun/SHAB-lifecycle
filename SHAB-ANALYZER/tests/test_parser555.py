import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser555 import extract_parser555_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', '90c8ab47ab4c5ab352f6b1065bf03413569429906e5f11f75220f0ecfa2ad305', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = "90c8ab47ab4c5ab352f6b1065bf03413569429906e5f11f75220f0ecfa2ad305"
ARGS = ('fr', 'fixture', '', None, None, None)


@lru_cache(maxsize=1)
def source_text():
    return next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text


@lru_cache(maxsize=1)
def target_text():
    calls = []
    with patch.object(parser, 'extract_parser555_leftovers',
                      lambda text, *a, **kw: (calls.append(text) or [], text)):
        parser.parse_publication_xml(FIXTURES / (TARGET + '.xml'))
    return calls[0]


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', DIGESTS)
def test_pipeline_preserves_existing_results(digest):
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (digest + '.xml')
    with patch.object(parser, 'extract_parser555_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser555_leftovers', lambda text, *a, **kw: ([], text)):
        old = parser.parse_publication_xml(path)
    assert len(calls) == 1
    added, rest = extract(*calls[0][0], **calls[0][1])
    remaining = list(result.events)
    for event in old.events + added:
        remaining.remove(event)
    if digest == TARGET:
        assert len(added) == 4
        assert rest.strip(' .').endswith(result.leftover_text)
    else:
        assert added == []
        assert result == old



def test_payload_and_missing_optional_attributes():
    events, rest = extract(target_text(), *ARGS, source_text=source_text())
    assert rest == '' and len(events) == 4
    assert [e.payload['name'] for e in events] == [
        'Miazza Claudine', 'Miazza Stéphane', 'Mira Florian', 'Samantha De Jesus Rodrigues']
    assert [e.payload['shares_count'] for e in events] == [60, 20, 60, 60]
    assert [e.payload['shares_transferred'] for e in events[:2]] == [40, 80]
    assert [e.payload['shares_received'] for e in events[2:]] == [60, 60]
    assert [e.role for e in events] == ['associé', 'associé', 'associé-gérant', 'associée-gérante']
    assert [e.signing for e in events] == [None, None, 'Einzelunterschrift', 'Einzelunterschrift']
    assert events[2].payload == {
        'name': 'Mira Florian', 'place': 'Thonon-les-Bains', 'share_nominal': '100',
        'currency': 'CHF', 'action': 'shares_received', 'new_associate': True,
        'shares_received': 60, 'shares_count': 60, 'origin': 'France', 'country': 'FRA'}
    assert 'country' not in events[3].payload
    for event in events:
        assert event.event_type == 'officer_changed'
        assert event.org_uid is event.plz is event.canton is None
        assert Event(**vars(event)) == event
    legacy = Event('fixture', '', 'officer_changed', 'legacy', payload={'name': 'Example'})
    assert Event(**vars(legacy)) == legacy
    assert 'shares_received' not in legacy.payload
    assert PARSER_VERSION >= 555


def test_source_evidence_required():
    text = target_text()
    for source in ('', source_text().replace('Mira Florian', 'Example Anne'),
                   source_text().replace('signature individuelle', 'signature collective à deux')):
        assert extract(text, *ARGS, source_text=source) == ([], text)


def test_no_old_rule_owns_target():
    from shab_analyzer.text_extras import extract_text_extras
    text = target_text()
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser555_leftovers':
            continue
        options = {'source_text': source_text()} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('language', ['de', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


@pytest.mark.parametrize('change', [lambda t: '', lambda t: t + '. UNKNOWN',
    lambda t: t.replace('respectivement cédé', 'cédé'),
    lambda t: t.replace('40 et 20', '0 et 20')])
def test_unsupported(change):
    text = change(target_text())
    assert extract(text, *ARGS, source_text=source_text()) == ([], text)


@pytest.mark.parametrize('text', [
    "Exemple Anne et Exemple Bob ont cédé 60 parts de CHF 100 à Exemple Charles, de France, à Genève, nouvel associé pour 60 parts de CHF 100, lequel associé est en outre nommé gérant Par conséquent, Exemple Anne et Exemple Bob sont désormais titulaires de 20 parts de CHF 100 chacun.",
    "Exemple Anne et Exemple Bob ont cédé 60 parts de CHF 100 à Exemple Charles, de France, à Genève, FRA, nouvel associé pour 60 parts de CHF 100. Signature collective à deux a été conférée à l'associé Exemple Charles. Par conséquent, Exemple Anne et Exemple Bob sont désormais titulaires de 20 parts de CHF 100 chacun.",
])
def test_legacy_boundary(text, tmp_path):
    from shab_analyzer.parser128 import extract_parser128_leftovers
    from shab_analyzer.parser249 import extract_parser249_leftovers
    assert any(old(text, *ARGS)[0] for old in (extract_parser128_leftovers, extract_parser249_leftovers))
    assert extract(text, *ARGS, source_text=text) == ([], text)
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    next(tree.iter('publicationText')).text = text
    path = tmp_path / 'boundary.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser555_leftovers', lambda text, *a, **kw: ([], text)):
        assert parser.parse_publication_xml(path) == result
