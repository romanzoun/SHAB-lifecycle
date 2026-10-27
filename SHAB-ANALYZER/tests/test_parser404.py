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
from shab_analyzer.parser404 import extract_parser404_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = ['00f789c46d9a1a3eb33fcaa11a087654c12438a9e495dc0e095cf925feffbcf0', '34da5c62c671d920d67792cf77670a02645824bf23ebc59df4ef21188b3d2211', '5aa4aef107654f5c7ecc1df22440035c23766be473a3b8424439881ce5868b2d', '8dd9d9372f143cd802138bf69aef2a4bf5370527026e4f8043f222ee4d58ed71', '9d7fa560fd489a218f8c5d1490c0ba2cd6153d9576fe8a65dd18ce75ab369ddb', 'a68e0c57bc1ce1ea7693b9a830ea63c50ab28f00c67db6141b66bb159a710f38', 'b573d009c56257ce9b9ae1e76b48c87750cb4094c1dbf3f61673268d480519b8', 'bd00ea9a58e78b62ff1a89c4e9940a906cf6f9d7c6a53af85297b3a54024cdd9', 'c00fe3f41cd0e252067ed217993bdeaaacb635ad7304e57cf154544a360e8778', 'eb0b4502e77562ad258ab46ae0be12131fc9d538ded0b2907546e694b6aeeca8', 'ee2146ff9a0c12f13a0fe12ed4d6660e3e438428e302820cfec7aeaa622b8ac3', 'fa1f487d21c340f4477cc362a157e6ef1af241f031b0c7356c2403442b3efaad']
COUNTS = [2, 1, 1, 2, 1, 2, 1, 1, 1, 2, 3, 2]
CONTEXT_REQUIRED = {8, 9, 10}


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser404_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser404_leftovers', capture):
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
    added, rest = extract_parser404_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 414
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS[index] and not rest
    with patch.object(parser, 'extract_parser404_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (SUPPLIED_SHA256[index] + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('index', range(12))
def test_unknown_suffix_language_and_invalid_dates(index):
    _, (args, kwargs) = captured(index)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser404_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser404_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser404_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index', range(12))
def test_missing_optional_metadata_and_source(index):
    _, (args, kwargs) = captured(index)
    events, rest = extract_parser404_leftovers(*args[:4], None, None, None, **kwargs)
    assert events and not rest
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    events, rest = extract_parser404_leftovers(*args)
    if index in CONTEXT_REQUIRED:
        assert not events and rest == args[0]
    else:
        assert events and not rest


def test_old_event_without_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event


EXPECTED = [
    ('officer_removed', {'name': 'Winz Heinz'}),
    ('organization_changed', {'decision_date': '29.12.2020', 'time': '15.22', 'dissolved': True}),
    ('capital_changed', {'setoff': "70'000.00", 'count': '18', 'nominal': '100.00', 'currency': 'CHF'}),
    ('organization_changed', {'decision_date': '14.01.2021', 'until_date': '12.06.2021', 'provisional': False, 'months': 6}),
    ('organization_changed', {'revocation_date': '06.11.2019', 'bankruptcy_entry_removed': True}),
    ('officer_changed', {'place': "Saint-Cyr-au-Mont-d'Or (France)"}),
    ('officer_changed', {'name': "d'Andlau de Cléron d'Haussonville Simon", 'signing_continued': True}),
    ('organization_changed', {'previous_place': 'Uetendorf', 'place': 'Langenthal', 'branch_uid': 'CHE-163.017.509', 'notice_date': '13.01.2021', 'notice_id': '1005072358'}),
    ('officer_removed', {'name': 'Binggeli Kurt', 'signing_restriction': 'mit einem Verwaltungsratsmitglied'}),
    ('ownership_changed', {'transferred': '10', 'previous': '50', 'remaining': '40', 'received': '40'}),
    ('ownership_changed', {'remaining': '15', 'transferred': '7', 'nominal': "1'000"}),
    ('officer_changed', {'name': 'Hubert Dietrich Nathalie Anne Hélène', 'signing_continued': True}),
]


def added(index):
    _, (args, kwargs) = captured(index)
    return extract_parser404_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('index', range(12))
def test_explicit_payload_meaning(index):
    events = added(index)
    kind, fields = EXPECTED[index]
    assert events[0].event_type == kind
    assert {key: events[0].payload[key] for key in fields} == fields


def test_people_roles_and_signing():
    assert [e.role for e in added(0)] == ['Verwaltungsratsmitglied'] * 2
    assert all(e.signing == 'Einzelunterschrift' for e in added(0))
    assert added(0)[1].payload['nationality'] == 'deutscher Staatsangehöriger'
    assert added(3)[1].role == 'commissaire au sursis' and added(3)[1].signing is None
    assert added(5)[0].role == 'président' and added(5)[0].signing is None
    assert added(5)[1].role == 'administrateur' and added(5)[1].signing == 'Einzelunterschrift'
    assert added(6)[0].role == 'trésorier' and added(6)[0].signing == 'Kollektivunterschrift zu zweien'
    assert added(8)[0].signing == 'Kollektivprokura zu zweien'
    assert added(9)[1].role == 'associé-gérant' and added(9)[1].signing == 'Kollektivunterschrift zu zweien'
    assert [e.role for e in added(10)[1:]] == ['associé, gérant président', 'associée, gérante']
    assert all(e.signing == 'Einzelunterschrift' for e in added(10)[1:])
    assert [e.role for e in added(11)] == ['administratrice, présidente', 'administratrice']
    assert added(11)[1].payload['previous_role'] == 'présidente'


@pytest.mark.parametrize('index', [8, 9, 10])
def test_required_source_evidence(index):
    _, (args, kwargs) = captured(index)
    assert extract_parser404_leftovers(*args, source_text='Unrelated.') == ([], args[0])
    source = kwargs['source_text'].replace('signature individuelle', 'signature collective à deux').replace('signature collective à deux', 'signature collective à trois').replace('mit einem Verwaltungsratsmitglied', 'mit einem Direktor')
    assert extract_parser404_leftovers(*args, source_text=source) == ([], args[0])


@pytest.mark.parametrize('before,after', [('cèdent chacun 10', 'cèdent chacun 9'), ('titulaire de 40', 'titulaire de 39')])
def test_inconsistent_share_totals_rejected(before, after):
    _, (args, kwargs) = captured(9)
    text = args[0].replace(before, after)
    source = kwargs['source_text'].replace(before, after)
    assert text != args[0]
    assert extract_parser404_leftovers(text, *args[1:], source_text=source) == ([], text)


def test_invalid_french_dates():
    _, (args, kwargs) = captured(3)
    for before, after in [('14 janvier', '32 janvier'), ('12 juin', '31 juin'), ('juin 2021', 'juin 2020')]:
        text = args[0].replace(before, after)
        assert extract_parser404_leftovers(text, *args[1:], **kwargs) == ([], text)


@pytest.mark.parametrize('version,text,language', [
    (157, 'Gelöschte Person: Exemple Anne, Verwaltungsratsmitglied, Einzelunterschrift. Neu eingetragene Person: Exemple Anna, französische Staatsangehörige, in Baar, Verwaltungsratsmitglied, Einzelunterschrift', 'fr'),
    (149, 'Gelöschte Person: Exemple Anne, Verwaltungsratsmitglied, Einzelunterschrift. Neu eingetragene Person: Exemple Anna, von Bern, in Baar, Verwaltungsratsmitglied, Einzelunterschrift', 'fr'),
    (207, "Par prononcé rendu le 14 janvier 2021, le président du Tribunal de Lausanne a accordé à la société un sursis concordataire provisoire jusqu'au 12 juin 2021. Exemple Anne, de Lausanne, à Lausanne, est inscrit en qualité de commissaire au sursis", 'fr'),
    (213, 'Gelöschte Person: Exemple Anne, Verwaltungsratsmitglied, Einzelunterschrift', 'fr'),
    (298, 'La succursale à Uetendorf (CHE-163.017.509) a transféré son siège à Langenthal', 'fr'),
    (297, "Par suite de cession de 7 parts de CHF 100, Exemple Anne est maintenant associé pour 15 parts de CHF 100, et Exemple Anna, de Bern, à Lausanne, est nouvelle associée pour 7 parts de CHF 100. Gérants: les associés Exemple Anne, nommé président, et Exemple Anna, tous deux", 'fr'),
])
def test_legacy_ownership_in_isolation(version, text, language):
    module = importlib.import_module(f'shab_analyzer.parser{version}')
    if version == 297:
        text += ' avec signature individuelle'
    args = text, language, 'p', '', None, None, None
    kwargs = {'source_text': text + '.'} if version == 297 else {}
    events, rest = getattr(module, f'extract_parser{version}_leftovers')(*args, **kwargs)
    assert events and not rest.strip()
    assert extract_parser404_leftovers(*args, **kwargs) == ([], text)


@pytest.mark.parametrize('stem', ['0a28fd6a', '15c0ec46', '1d60fa42', '5876b669', 'e589ced7'])
def test_existing_fixtures_unchanged(stem):
    import shab_analyzer.parse as parser
    paths = list(FIXTURES.glob(stem + '*.xml'))
    assert len(paths) == 1
    result = parse_publication_xml(paths[0])
    with patch.object(parser, 'extract_parser404_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(paths[0])


@pytest.mark.parametrize('index', [1, 4])
def test_invalid_times(index):
    _, (args, kwargs) = captured(index)
    text = re.sub(r'\d{2}\.\d{2} Uhr', '25.61 Uhr', args[0])
    assert text != args[0]
    assert extract_parser404_leftovers(text, *args[1:], **kwargs) == ([], text)


@pytest.mark.parametrize('index', [8, 9, 10])
def test_source_person_must_match(index):
    _, (args, kwargs) = captured(index)
    source = kwargs['source_text'].replace('Binggeli Kurt', 'Exemple Anne').replace('Prost Arthur', 'Exemple Anne').replace('Zouaïmia Isabelle', 'Exemple Anne')
    assert source != kwargs['source_text']
    if index == 8:
        # The residual restriction has no identity: it refers to the person
        # in the source, rather than inventing an identity from the fragment.
        events, rest = extract_parser404_leftovers(*args, source_text=source)
        assert not rest and events[0].payload['name'] == 'Exemple Anne'
    else:
        assert extract_parser404_leftovers(*args, source_text=source) == ([], args[0])
