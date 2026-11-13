import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser502 import extract_parser502_leftovers as extract
from shab_analyzer.parser223 import _FR_MANAGER_SHARE_TRANSFER

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'c4b6609d4cfaf56002d0cf7d4926367f2bf77447578af29917d0c43327b69968', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = 'c4b6609d4cfaf56002d0cf7d4926367f2bf77447578af29917d0c43327b69968'
ARGS = ('fr', 'fixture', '', None, None, None)
TEXT = ('Alpha Paul cède 60 des 200 parts de CHF 100 à Beta Jean, de France, '
        'à Paris (France), nouvel associé-gérant avec 60 parts de CHF 100. '
        'Alpha Paul reste titulaire de 140 parts de CHF 100')


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', DIGESTS)
def test_pipeline_preserves_existing_events(digest):
    path = FIXTURES / (digest + '.xml')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser502_leftovers', lambda text, *a, **kw: ([], text)):
        old = parser.parse_publication_xml(path)
    remaining = list(result.events)
    for event in old.events:
        remaining.remove(event)
    if digest == TARGET:
        added, rest = extract(old.leftover_text, old.language, old.publication_id,
                              old.published_at, old.org_uid, old.plz, old.canton)
        assert len(added) == 2
        assert all(e in result.events for e in added)
        assert rest.endswith(result.leftover_text)
        assert any(e.event_type == 'signing_authority_changed' for e in old.events)
    else:
        assert result == old


def test_payload_and_absent_optional_attributes():
    events, rest = extract(TEXT, *ARGS)
    assert rest == ''
    ownership, officer = events
    assert ownership.event_type == 'ownership_changed'
    assert ownership.payload == dict(seller='Alpha Paul', buyer='Beta Jean', count='60',
                                    before='200', remaining='140', nominal='100',
                                    origin='France', place='Paris (France)',
                                    action='partial_transfer', currency='CHF')
    assert officer.event_type == 'officer_changed'
    assert officer.role == 'associé-gérant'
    assert officer.signing is None
    assert officer.payload == dict(name='Beta Jean', place='Paris (France)',
                                  origin='France', action='appointed')
    for event in events:
        assert (event.org_uid, event.plz, event.canton) == (None, None, None)
        assert Event(**vars(event)) == event
    legacy = Event('legacy', '', 'ownership_changed', 'legacy', payload={'action': 'partial_transfer'})
    assert Event(**vars(legacy)) == legacy
    assert 'origin' not in legacy.payload
    assert PARSER_VERSION == 546


@pytest.mark.parametrize('text,language', [
    (TEXT, 'de'), (TEXT + ' Autre reste', 'fr'),
    (TEXT.replace('140 parts', '141 parts'), 'fr'),
    (TEXT.replace('60 des', '0 des').replace('avec 60', 'avec 0'), 'fr'),
    (TEXT.replace('avec 60', 'avec 61'), 'fr'),
    (TEXT.replace('CHF 100.', 'CHF 101.'), 'fr'),
    (TEXT.replace('200 parts', '60 parts').replace('140 parts', '0 parts'), 'fr'),
])
def test_unsupported_unchanged(text, language):
    assert extract(text, language, *ARGS[1:]) == ([], text)


def test_legacy_pattern_boundary():
    text = ("L'associé-gérant Alpha Paul cède 60 de ses 200 parts de CHF 100 à "
            'Beta Jean, de France, à Paris, nouvel associé. '
            'Alpha Paul reste titulaire de 140 parts de CHF 100')
    assert _FR_MANAGER_SHARE_TRANSFER.fullmatch(text)
    assert extract(text, *ARGS) == ([], text)


@pytest.mark.parametrize('number', [417, 448, 501])
def test_relative_legacy_pipeline_boundary(number):
    import re
    source = (Path(__file__).parent / f'test_parser{number}.py').read_text()
    names = re.findall(r'[A-Za-z0-9_-]+\.xml', source)
    names += [d + '.xml' for d in re.findall(r"['\"]([a-f0-9]{64})['\"]", source)]
    paths = {FIXTURES / n for n in names if (FIXTURES / n).is_file()}
    assert paths
    for path in paths:
        result = parser.parse_publication_xml(path)
        with patch.object(parser, 'extract_parser502_leftovers', lambda text, *a, **kw: ([], text)):
            assert result == parser.parse_publication_xml(path)
