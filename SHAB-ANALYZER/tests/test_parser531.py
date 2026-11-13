import hashlib
import inspect
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser531 import extract_parser531_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', 'd0f8f571a88570c154fb40336af5a63fa0e63ceff3b80ed7bd127d70699da714', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = 'd0f8f571a88570c154fb40336af5a63fa0e63ceff3b80ed7bd127d70699da714'
ARGS = ('fr', 'fixture', '', None, None, None)


def source_text():
    return next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text


def target_text():
    source = source_text()
    return source[source.index('Favre Anne a cédé'):].split(' avec signature')[0]


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', DIGESTS)
def test_pipeline_preserves_existing_results(digest):
    path = FIXTURES / (digest + '.xml')
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    with patch.object(parser, 'extract_parser531_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser531_leftovers', lambda text, *a, **kw: ([], text)):
        old = parser.parse_publication_xml(path)
    assert len(calls) == 1
    added, rest = extract(*calls[0][0], **calls[0][1])
    remaining = list(result.events)
    for event in old.events + added:
        remaining.remove(event)
    if digest == TARGET:
        assert len(added) == 2
        assert rest.strip(' .').endswith(result.leftover_text)
    else:
        assert added == []
        assert result == old


def test_payload_and_missing_optional_attributes():
    events, rest = extract(target_text(), *ARGS)
    assert len(events) == 2 and rest == ''
    assert [e.event_type for e in events] == ['officer_changed'] * 2
    assert [e.role for e in events] == ['associé-gérant', 'associé-gérant président']
    assert all(e.signing is None for e in events)
    assert events[0].payload == {'name': 'Favre Anne', 'place': None,
        'share_nominal': "1'000", 'currency': 'CHF', 'shares_count': 2,
        'shares_transferred': 18}
    assert events[1].payload == {'name': 'Chalabi Quentin Guy André', 'place': 'Meyrin',
        'share_nominal': "1'000", 'currency': 'CHF', 'shares_count': 18, 'heimat': 'France'}
    for event in events:
        assert Event(**vars(event)) == event
    legacy = Event('old', '', 'officer_changed', 'legacy', payload={'name': 'Example'})
    assert Event(**vars(legacy)) == legacy
    assert 'shares_transferred' not in legacy.payload
    assert PARSER_VERSION == 542


def test_no_existing_rule_owns_target():
    text = target_text().rstrip('.')
    from shab_analyzer.text_extras import extract_text_extras
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser531_leftovers':
            continue
        options = {'source_text': source_text()} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('language', ['de', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


@pytest.mark.parametrize('before,after', [
    ('nommé président', 'nommé secrétaire'), ('18 parts', '0 parts'),
    ('au nouvel associé', 'à'), ('pour 18 parts', 'pour 19 parts'),
    ('tous deux', 'tous trois'),
])
def test_unattested(before, after):
    text = target_text().replace(before, after)
    assert extract(text, *ARGS) == ([], text)


def test_context():
    events, _ = extract(target_text(), 'fr', 'pub', '2021', 'uid', '1000', 'GE')
    assert len(events) == 2
    for e in events:
        assert (e.publication_id, e.published_at, e.org_uid, e.plz, e.canton) == ('pub', '2021', 'uid', '1000', 'GE')


@pytest.mark.parametrize('number,text', [
    (74, "Alpha Anne a cédé 18 parts de CHF 100 à Beta Bea, de France, à Meyrin. Associés-gérants: Alpha Anne pour 2 parts de CHF 100, nommé président, et Beta Bea pour 18 parts de CHF 100, tous deux"),
    (110, "Alpha Anne a cédé 18 parts de CHF 100 à Beta Bea. Associés-gérants: Alpha Anne, pour 2 parts de CHF 100, nommé président, et Beta Bea pour 18 parts de CHF 100, jusqu'ici directrice, tous deux"),
])
def test_legacy_boundary(number, text, tmp_path):
    assert getattr(parser, f'extract_parser{number}_leftovers')(text, *ARGS)[0]
    assert extract(text, *ARGS, source_text=text) == ([], text)
    xml = ET.parse(FIXTURES / (TARGET + '.xml'))
    next(xml.iter('publicationText')).text = text
    path = tmp_path / 'boundary.xml'
    xml.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser531_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parser.parse_publication_xml(path)
