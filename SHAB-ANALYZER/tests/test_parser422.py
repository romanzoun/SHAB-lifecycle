import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser422 import extract_parser422_leftovers as extract, _LEGACY

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['3e23ad3050879ab05bd613e232da97b3502af1cff3162fdae9f19dbd2fdf0c1c', '5a2c59710ddd170f740a955b21138d6bedaa40a017a31afc436573b6532fe865', '878cd720128f16ff07a7080143b9c5c1132a87ceb5121066d54d9269c34f3dd2', '8da8704e3685c2da7888375ac6b228a780462a656ef2d918d407db696de36d17', '9484fd18a967006df3dbd204f9e6c95103a76c7b7fdfce167964879d6a86621e', 'ad3112c2e035dd530be7962b6d548da96d9c40c96db6ef69c7a8f5e9aa45ca2c', 'be2a52d471fc0e2a03a6ba58d58ece069e8a5508dd72b208a33b7c5bb3ea0128', 'be81e6e08783b3deea04aa7444e3a47c8b52ef2faa70a46d7e73a4e36742104c', 'dd09e117d4a7f483089e5eb17da3310624066842069324ff020e537def4d2d29', 'e57942776161dc3fdbf7100627b2c8a901332a6f4847077a6c6b446f34d51c6b', 'ed6cdec8ffd2755edbb565ce6734c699a4f326461d46775891c8e137472e6391', 'f6517c8e403ac8ce109122926e2d1e0a9466016657fd5de75a683f22b63e7d0f']
COUNTS = [5, 1, 3, 2, 1, 3, 1, 1, 1, 2, 1, 3]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser422_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser422_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(path)
    assert len(calls) == 1
    return result, old, calls[0]


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('index', range(12))
def test_complete_and_unchanged_old_payloads(index):
    result, old, (args, kwargs) = captured(index)
    added, rest = extract(*args, **kwargs)
    assert PARSER_VERSION == 431
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    assert len(added) == COUNTS[index] and rest == ''
    assert old.leftover_text == args[0]
    assert result.events == old.events + added
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('index', range(12))
def test_unknown_suffix_language_and_invalid_dates(index):
    _, _, (args, kwargs) = captured(index)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract(changed, *args[1:], **kwargs) == ([], changed)
    assert extract(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index', range(12))
def test_missing_optional_metadata_and_source(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args[:4], None, None, None, **kwargs)
    assert len(events) == COUNTS[index] and rest == ''
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    events, rest = extract(*args)
    assert len(events) == COUNTS[index] and rest == ''



def test_old_event_without_optional_attributes():
    event = Event('p', '', 'officer_changed', 'legacy.rule', payload={'name': 'Test Anna'})
    assert Event(**vars(event)) == event
    assert event.payload == {'name': 'Test Anna'}
    assert event.role is None and event.signing is None



EXPECTED = [
    ('organization_changed', {'german_name': 'Codex D. GmbH in Liquidation'}),
    ('organization_changed', {'previous_head_office_id': 'CH-350.4.003.515-7'}),
    ('status_changed', {'decision_date': '24.07.2020'}),
    ('officer_changed', {'previous_role': 'associé'}),
    ('officer_changed', {'corrected': True, 'previous_name': "N'Dri Mianwlein Yolanda Denelle"}),
    ('ownership_changed', {'count': '6', 'before': '20', 'origin': 'Chili'}),
    ('officer_changed', {'corrected': True, 'previous_name': 'Rotschild Guy'}),
    ('status_changed', {'reinstated': True}),
    ('capital_changed', {'previous_amendment_date': '23.04.2015'}),
    ('officer_changed', {'country': 'ITA'}),
    ('status_changed', {'dissolved': True, 'suspended_for_lack_of_assets': True, 'suspension_date': '01.02.2021'}),
    ('ownership_changed', {'count': '5', 'remaining': '15', 'origin': 'Cameroun'}),
]


@pytest.mark.parametrize('index', range(12))
def test_semantics(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    kind, fields = EXPECTED[index]
    assert events[0].event_type == kind and rest == ''
    for key, value in fields.items():
        assert events[0].payload[key] == value
    if index == 0:
        assert all(e.role == 'liquidateur' and e.signing is None for e in events[1:])
    if index == 2:
        assert all(e.role == 'liquidatrice' and e.signing == 'Kollektivunterschrift zu zweien' for e in events[1:])
    if index == 3:
        assert all(e.role == 'liquidateur' and e.signing == 'Einzelunterschrift' for e in events)
    if index in (5, 11):
        assert events[1].role == 'président'
        assert events[2].role == ('associé-gérant' if index == 5 else 'associée-gérante')
        assert all(e.signing is None for e in events)
    if index == 6:
        assert events[0].signing == 'Einzelunterschrift'
    if index == 9:
        assert [e.role for e in events] == ['secrétaire', 'président']
        assert all(e.signing == 'Einzelunterschrift' for e in events)


@pytest.mark.parametrize('text,lang', [
    ("Selon décision de l'Autorité cantonale de surveillance des fondations et des institutions de prévoyance du 24.07.2020, la fondation est dissoute. Liquidateurs: les membres du conseil Test Anna et Test Paul, lesquels continuent à signer collectivement à deux", 'fr'),
    ('[Anpassung des Sitzes infolge Namensänderung der Gemeinde]', 'de'),
    ('Test Anna, Test Paul, Test Jean et Test Marc sont nommés liquidateurs', 'fr'),
    ("L'inscription no 3125 du 09.02.2021 est rectifiée en ce sens qu'un membre du conseil se nomme Test Anna (et non pas Test Anne)", 'fr'),
])
def test_related_old_rules_unchanged_rest(text, lang):
    padded = '  ' + text + '  '
    assert extract(padded, lang, 'p', '', None, None, None, source_text=text) == ([], padded)


@pytest.mark.parametrize('index', range(12))
def test_no_overlap_with_old_rules_even_in_isolation(index):
    # Exercise every historical extractor on the complete clause in isolation.
    import inspect
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(index)
    for name, old_extract in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser422_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name


@pytest.mark.parametrize('pattern_index,text,lang', [
    (0, "Selon décision de l'Autorité de surveillance du 24.07.2020, la fondation est dissoute. Liquidateurs: les membres du conseil Test Anna et Test Paul, lesquels continuent à signer individuellement", 'fr'),
    (1, 'Die Generalversammlung hat mit Beschluss vom 02.05.2019 die Statutenbestimmung über die bedingte Kapitalerhöhung vom 22.04.2010 geändert. [bisher: Die Generalversammlung hat mit Beschluss vom 23.04.2015 die Statutenbestimmung über die bedingte Kapitalerhöhung vom 22.04.2010 geändert.]', 'de'),
])
def test_imported_legacy_patterns_keep_original_input(pattern_index, text, lang):
    assert _LEGACY[pattern_index].fullmatch(text)
    padded = '  ' + text + '  '
    assert extract(padded, lang, 'p', '', None, None, None) == ([], padded)
