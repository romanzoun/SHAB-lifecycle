import hashlib
import importlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser405 import extract_parser405_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = ['170d1fdcf75ad0b85a1dac7780aca904bf9867ba721d333f1a44135cf4a1e718', '37446ffb091b102be04b1038668e17a5f0de8565673ec9f030838ac548cc2165', '431e03a016e712dad603655da2b3cf2e4f041840ed4d06434587cdd65b423ea6', '50162f87197ac07a5ec295bd051f5ca9318e51b32610f4d98d09a828de05aa9d', '61b076ca46797a6e9376866e0f79d84d9a9a5aee978f6242f55703d31503cf22', '675157f6f3b783a7a8c70603d85bcaacf6c6ea284fe1493a2a27660ad6de4b6f', '8ba8ab567d89a51dbfeb2b78050cee5db08e9485bbe74e7c099957485237986e', 'a1c86f5d82ddffa90e6cccb790de5bd21143adfc528c2a05921b50e52e400b53', 'ab4cb588c1df695ca9c6f470afd12d9beb528c300bf5cdcaaaa12ad178180680', 'af9ed54ad9ce008acfdb463121e45b9409043c3fe94a527480c83d07b81bc5fa', 'e7978facbdfe7b039da376f714ed2410b58ad572a16d7bdb07f0bc906a1775cb', 'f74bf5c6a409a0c17a5f1e489fea312d9942c675358d8e7ace78b0480ca4357a']
COUNTS = [1, 1, 1, 1, 1, 1, 1, 3, 1, 1, 1, 3]
CONTEXT_REQUIRED = {2, 3}


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser405_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser405_leftovers', capture):
        result = parse_publication_xml(FIXTURES / (SUPPLIED_SHA256[index] + '.xml'))
    assert len(calls) == 1
    return result, calls[0]


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('index', range(12))
def test_complete_and_unchanged_legacy_payloads(index):
    import shab_analyzer.parse as parser
    result, (args, kwargs) = captured(index)
    added, rest = extract_parser405_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 405
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS[index] and not rest
    with patch.object(parser, 'extract_parser405_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (SUPPLIED_SHA256[index] + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('index', range(12))
def test_unknown_suffix_language_and_invalid_dates(index):
    _, (args, kwargs) = captured(index)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser405_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser405_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser405_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index', range(12))
def test_missing_optional_metadata_and_source(index):
    _, (args, kwargs) = captured(index)
    events, rest = extract_parser405_leftovers(*args[:4], None, None, None, **kwargs)
    assert events and not rest
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    events, rest = extract_parser405_leftovers(*args)
    if index in CONTEXT_REQUIRED:
        assert not events and rest == args[0]
    else:
        assert events and not rest


def test_old_event_without_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event



EXPECTED = [
    ('officer_changed', {'role_marker': 'commissario', 'until_date': '31.12.2022'}),
    ('officer_changed', {'role_continued': True, 'corrected': True}),
    ('statutes_changed', {'maximum_price': "118'000.00", 'intended': True, 'currency': 'CHF'}),
    ('company_name_changed', {'english_name': 'Calibo Apex Ltd in liquidation'}),
    ('organization_changed', {'foundation_date': '28.10.1997', 'clause_removed': True}),
    ('officer_changed', {'supplemented': True}),
    ('ownership_changed', {'transferred': '140', 'received': '200', 'nominal': '100'}),
    ('officer_changed', {'name': 'Proctor Simon John'}),
    ('officer_changed', {'place': 'Lyon', 'country': 'F', 'corrected': True}),
    ('organization_changed', {'legal_basis': 'art. 159, al. 1 let.b ORC', 'suspensive_effect': True}),
    ('publication_corrected', {'kind': 'conditional_capital_clause', 'previous_date': '17.07.2020'}),
    ('officer_changed', {'limited_to_main_establishment': False, 'corrected': True}),
]

@pytest.mark.parametrize('index', range(12))
def test_payload_semantics(index):
    _, (args, kwargs) = captured(index)
    events, rest = extract_parser405_leftovers(*args, **kwargs)
    kind, fields = EXPECTED[index]
    assert events[0].event_type == kind
    for key, value in fields.items():
        assert (events[0].role if key == 'role_marker' else events[0].payload[key]) == value
    if index == 5:
        assert events[0].signing == 'Einzelunterschrift'
    if index == 7:
        assert [e.role for e in events] == ['administrateur président', 'administratrice vice-présidente', 'secrétaire hors conseil']
        assert [e.signing for e in events] == ['Einzelunterschrift', 'Einzelunterschrift', 'ohne Unterschrift']
    if index == 11:
        assert [e.signing for e in events] == ['Kollektivunterschrift zu zweien'] * 2 + ['Kollektivprokura zu zweien']

@pytest.mark.parametrize('index', [2, 3])
def test_source_required_and_matching(index):
    _, (args, kwargs) = captured(index)
    assert extract_parser405_leftovers(*args, source_text='Unrelated.') == ([], args[0])
    source = kwargs['source_text'].replace('118', '119').replace('Calibo', 'Other')
    assert extract_parser405_leftovers(*args, source_text=source) == ([], args[0])

@pytest.mark.parametrize('version,text', [
    (186, "Par arrêt du 21.01.2021, le Tribunal cantonal de Fribourg a accordé l'effet suspensif au recours interjeté le 20.01.2021 contre la décision du 04.01.2021 (art. 159, al. 2 ORC)"),
    (177, "Par arrêt du 21.01.2021, le Tribunal cantonal de Fribourg a accordé l'effet suspensif au recours interjeté le 20.01.2021 contre la décision de faillite prononcée le 04.01.2021"),
])
def test_legacy_ownership_in_isolation(version, text):
    module = importlib.import_module(f'shab_analyzer.parser{version}')
    args = text, 'fr', 'p', '', None, None, None
    events, rest = getattr(module, f'extract_parser{version}_leftovers')(*args)
    assert events and not rest.strip()
    assert extract_parser405_leftovers(*args) == ([], text)

@pytest.mark.parametrize('stem', ['00f789c4', '34da5c62', '5aa4aef1', '8dd9d937', '9d7fa560', 'a68e0c57', 'b573d009', 'bd00ea9a', 'c00fe3f4', 'eb0b4502', 'ee2146ff', 'fa1f487d'])
def test_existing_fixtures_unchanged(stem):
    import shab_analyzer.parse as parser
    paths = list(FIXTURES.glob(stem + '*.xml'))
    assert len(paths) == 1
    result = parse_publication_xml(paths[0])
    with patch.object(parser, 'extract_parser405_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(paths[0])

@pytest.mark.parametrize('index,before,after', [(0, '31.12.2022', '31.12.2019'), (6, 'désormais 200', 'désormais 139')])
def test_inconsistent_extension_or_share_total_rejected(index, before, after):
    _, (args, kwargs) = captured(index)
    text = args[0].replace(before, after)
    assert text != args[0]
    assert extract_parser405_leftovers(text, *args[1:], **kwargs) == ([], text)

@pytest.mark.parametrize('text,language,version', [
    ('Con decisione del 02.11.2018, la Pretura del Distretto di Mendrisio-Sud ha prorogato la nomina del commissario Exemple Anna fino al 31.12.2020', 'it', 100),
    ("L'inscription n° 434 du 13.01.2021 est rectifiée en ce sens que Exemple Anna reste directeur général", 'fr', 197),
])
def test_related_legacy_formulations_remain_owned(text, language, version):
    module = importlib.import_module(f'shab_analyzer.parser{version}')
    args = text, language, 'p', '', None, None, None
    events, rest = getattr(module, f'extract_parser{version}_leftovers')(*args)
    assert events and not rest.strip()
    assert extract_parser405_leftovers(*args) == ([], text)
