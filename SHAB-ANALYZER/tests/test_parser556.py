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
from shab_analyzer.parser556 import extract_parser556_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', '659606f8874135a9158cd2575ce7f3f79fef35c05c88fef61d5a8b2062e821cc', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = "659606f8874135a9158cd2575ce7f3f79fef35c05c88fef61d5a8b2062e821cc"
ARGS = ('fr', 'fixture', '', None, None, None)


@lru_cache(maxsize=1)
def source_text():
    return next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text


@lru_cache(maxsize=1)
def target_text():
    calls = []
    with patch.object(parser, 'extract_parser556_leftovers',
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
    with patch.object(parser, 'extract_parser556_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser556_leftovers', lambda text, *a, **kw: ([], text)):
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
        'Beguin Nicolas', 'Martin Arnaud', 'Richa Alexandre Xavier', 'Clerc Gregory']
    assert [e.payload['shares_count'] for e in events] == [225] * 4
    assert [e.payload['shares_transferred'] for e in events[:3]] == [75] * 3
    assert events[3].payload == {
        'name': 'Clerc Gregory', 'place': 'Genève', 'share_nominal': '100',
        'currency': 'CHF', 'shares_count': 225, 'action': 'shares_received',
        'shares_received': 225, 'new_associate': True, 'origin': 'Genève'}
    assert [e.role for e in events] == ['associé'] * 3 + ['associé-gérant']
    assert [e.signing for e in events] == [None] * 3 + ['Einzelunterschrift']
    assert all('country' not in e.payload for e in events)
    for event in events:
        assert event.event_type == 'officer_changed'
        assert event.org_uid is event.plz is event.canton is None
        assert Event(**vars(event)) == event
    legacy = Event('fixture', '', 'officer_changed', 'legacy', payload={'name': 'Example'})
    assert Event(**vars(legacy)) == legacy
    assert 'shares_received' not in legacy.payload
    assert PARSER_VERSION >= 556


def test_source_evidence_required():
    text = target_text()
    for source in ('', source_text().replace('Clerc Gregory', 'Example Anne'),
                   source_text().replace('signature individuelle', 'signature collective à deux')):
        assert extract(text, *ARGS, source_text=source) == ([], text)


def test_no_old_rule_owns_target():
    from shab_analyzer.text_extras import extract_text_extras
    text = target_text()
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser556_leftovers':
            continue
        options = {'source_text': source_text()} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('language', ['de', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


@pytest.mark.parametrize('change', [lambda t: '', lambda t: t + '. UNKNOWN',
    lambda t: t.replace('respectivement cédé', 'cédé'),
    lambda t: t.replace('cédé 75', 'cédé 0'),
    lambda t: t.replace('Clerc Gregory sont', 'Example Anne sont'),
    lambda t: t.replace('CHF 100 chacun', 'CHF 200 chacun')])
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
    with patch.object(parser, 'extract_parser556_leftovers', lambda text, *a, **kw: ([], text)):
        assert parser.parse_publication_xml(path) == result


@pytest.mark.parametrize('number,digest', [
    (117, '0f51c396-4826-4703-be6e-9e1722939bcf'),
    (224, '722662c5-24e3-4087-abb8-d654cbc36f04'),
    (527, 'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176'),
    (555, '90c8ab47ab4c5ab352f6b1065bf03413569429906e5f11f75220f0ecfa2ad305'),
])
def test_legacy_three_sellers_and_two_buyers_boundary(number, digest):
    old = getattr(parser, f'extract_parser{number}_leftovers')
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return old(*args, **kwargs)
    path = FIXTURES / (digest + '.xml')
    with patch.object(parser, f'extract_parser{number}_leftovers', capture):
        result = parser.parse_publication_xml(path)
    args, kwargs = calls[0]
    assert old(*args, **kwargs)[0]
    assert extract(*args, **kwargs) == ([], args[0])
    with patch.object(parser, 'extract_parser556_leftovers', lambda text, *a, **kw: ([], text)):
        assert parser.parse_publication_xml(path) == result


def test_context_and_independent_reported_amounts():
    text = target_text().replace('cédé 75', 'cédé 50')
    source = source_text().replace('cédé 75', 'cédé 50')
    events, rest = extract(text, 'fr', 'pub', '2021', 'uid', '1200', 'GE', source_text=source)
    assert len(events) == 4 and rest == ''
    assert [e.payload['shares_count'] for e in events] == [225] * 4
    assert events[3].payload['shares_received'] == 150
    assert all((e.publication_id, e.published_at, e.org_uid, e.plz, e.canton) ==
               ('pub', '2021', 'uid', '1200', 'GE') for e in events)
