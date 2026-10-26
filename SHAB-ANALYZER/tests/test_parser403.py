import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser403 import extract_parser403_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = ['0a28fd6a64c964d81193840dcce06b5b5a1a337ef3799ac99f967f69f9eb6142', '15c0ec464a8756ac47ef79f7dd45b3fff448e1154f0cb70ce3fb02264ea887f3', '1d60fa4227e81f127893bd888b51d98216983c608bc8e8eb24fded804e17307b', '2a9e28ead12d20c6e24e25bde716e09349c0b674e2256af9410dbb0b56935ff4', '5876b6698a1acd76e170bc4982ddbcea212ed9677341a18a32a3f9440923c23f', '5c31e3e5034bff02e35fbac27fc7ccbe6aa0e62b69d29cee32c2087776d33e19', '7be93a148378b852a2473aa3c6d3e684b8a0f307784360f13ad8044e429b3618', '886bfc77e32f6ebab10870bc96f3531a77f5c17343349fa225d9512890b47682', '8be68ecc1a2c4e1408218db80c856e780ca42ee4954764ec7e5a4a0fcdd95666', '8c7dae67ee8566df706d78bad5ce79247694e1d429d48c72fdf30a67a146c7da', '8dac124a4037c164ce39110c4eede54821823a52afaaa5d8cbc86093d4bd3ded', 'e589ced72c52b84577865b1f5b1d535e4b5468ee50613d24b261b3c0fa5b7ace']
CONTEXT_REQUIRED = {'15c0ec46', '5c31e3e5', '7be93a14', '886bfc77'}
COUNTS = [1, 2, 1, 2, 1, 4, 1, 2, 1, 1, 1, 1]


@lru_cache(None)
def captured(digest):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser403_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser403_leftovers', capture):
        result = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert len(calls) == 1
    return result, calls[0]


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_complete_and_unchanged_legacy_payloads(digest):
    import shab_analyzer.parse as parser
    result, (args, kwargs) = captured(digest)
    added, rest = extract_parser403_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 403
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS[SUPPLIED_SHA256.index(digest)] and not rest
    with patch.object(parser, 'extract_parser403_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_unknown_suffix_language_and_invalid_dates(digest):
    _, (args, kwargs) = captured(digest)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser403_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser403_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser403_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_missing_optional_metadata_and_source(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser403_leftovers(*args[:4], None, None, None, **kwargs)
    assert events and not rest
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    events, rest = extract_parser403_leftovers(*args)
    if digest[:8] in CONTEXT_REQUIRED:
        assert not events and rest == args[0]
    else:
        assert events and not rest


def test_old_event_without_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event

EXPECTED = [
    ('organization_changed', {'deleted': True}),
    ('officer_changed', {'origin': 'Inde', 'country': 'CHN', 'place': 'Beijing'}),
    ('organization_changed', {'suspensive_effect': True, 'bankruptcy_entry_removed': True, 'effective_time': '09.00'}),
    ('officer_changed', {'place': 'Carouge GE', 'signing_continued': True, 'president': True}),
    ('officer_changed', {'action': 'name_corrected', 'entry_date': '2020-12-15', 'previous_name': 'Ripoli épouse Rouffiange Nathalie', 'name': 'Ripoll épouse Rouffiange Nathalie'}),
    ('ownership_changed', {'transferred': '16', 'previous': '24', 'remaining': '8', 'count1': '8', 'count2': '8'}),
    ('ownership_changed', {'previous_nominal': "20'000", 'count': '20', 'nominal': "1'000"}),
    ('capital_changed', {'transfer_restricted': False, 'preferred_right': 'produit de liquidation', 'count1': "266'443", 'count2': "151'343"}),
    ('organization_changed', {'suspensive_effect': True, 'bankruptcy_date': '04.01.2021', 'appeal_date': '11.01.2021'}),
    ('assets_transferred', {'assets': "380'925'024.16", 'count': "450'602", 'nav': '996.00', 'cash_adjustment': '304.00', 'effective_date': '1. Januar 2021'}),
    ('publication_corrected', {'kind': 'deed_date', 'date': '2020-12-16'}),
    ('officer_changed', {'origin': 'Fehraltorf', 'previous_origin': 'Ferhaltorf', 'corrected': True}),
]


def added(index):
    _, (args, kwargs) = captured(SUPPLIED_SHA256[index])
    return extract_parser403_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('index', range(12))
def test_explicit_payload_meaning(index):
    events = added(index)
    kind, fields = EXPECTED[index]
    assert events[0].event_type == kind
    assert {key: events[0].payload[key] for key in fields} == fields


def test_people_roles_signing_and_missing_residences():
    board = added(1)
    assert [e.role for e in board] == ["président du conseil d'administration", "membre du conseil d'administration"]
    assert all(e.signing == 'Einzelunterschrift' for e in board)
    assert board[1].payload['origin'] == 'Chine'
    liquidators = added(3)
    assert all(e.role == 'Liquidator' and e.signing == 'Einzelunterschrift' for e in liquidators)
    assert liquidators[1].payload['place'] is None
    buyers = added(5)
    assert buyers[1].role == 'associée-gérante présidente'
    assert buyers[1].payload['place'] is None
    assert buyers[2].role == 'associée-gérante' and buyers[2].payload['place'] == 'Bonvillars'
    assert buyers[3].payload['place'] == 'Nods' and buyers[3].signing is None
    liquidator = added(7)[1]
    assert liquidator.role == 'Liquidator' and liquidator.signing == 'Einzelunterschrift'
    assert liquidator.payload['procuration_extinguished'] is True


@pytest.mark.parametrize('index', [1, 5, 6, 7])
def test_required_source_evidence(index):
    _, (args, _) = captured(SUPPLIED_SHA256[index])
    assert extract_parser403_leftovers(*args, source_text='Unrelated.') == ([], args[0])


@pytest.mark.parametrize('index', [1, 5, 7])
def test_signing_evidence_must_match(index):
    _, (args, kwargs) = captured(SUPPLIED_SHA256[index])
    source = kwargs['source_text'].replace('signature individuelle', 'signature collective à deux')
    assert extract_parser403_leftovers(*args, source_text=source) == ([], args[0])


@pytest.mark.parametrize('index,before,after', [(5, 'cède 16', 'cède 15'), (5, 'titulaire de 8', 'titulaire de 9'), (6, 'en 20 parts', 'en 19 parts')])
def test_inconsistent_share_totals_rejected(index, before, after):
    _, (args, kwargs) = captured(SUPPLIED_SHA256[index])
    text = args[0].replace(before, after)
    source = kwargs['source_text'].replace(before, after)
    assert text != args[0]
    assert extract_parser403_leftovers(text, *args[1:], source_text=source) == ([], text)


@pytest.mark.parametrize('version,text,language', [
    (129, "L'inscription no 123 du 15.12.2020 est rectifiée en ce sens que le nom exact de Exemple Anne est Exemple Anna", 'fr'),
    (143, 'Urkundendatum: 16.12.2020', 'de'),
    (205, "Division de la part de CHF 20'000 de l'associé-gérant Exemple Anne, formant le capital de même montant, en 20 parts de CHF 1'000", 'fr'),
    (208, 'Das Urkundendatum datiert vom 16.12.2020 [nicht vom 15.12.2020]', 'de'),
    (274, "Par arrêt du 12.01.2021, le Tribunal cantonal de Fribourg a accordé l'effet suspensif au recours interjeté le 11.01.2021 contre la décision du 04.01.2021", 'fr'),
    (397, 'Liquidateurs: les associés gérants Exemple Anne, président, Exemple Marc et Exemple Luc, lesquels continuent à signer individuellement', 'fr'),
])
def test_legacy_ownership_in_isolation(version, text, language):
    import importlib
    module = importlib.import_module(f'shab_analyzer.parser{version}')
    args = text, language, 'p', '', None, None, None
    events, rest = getattr(module, f'extract_parser{version}_leftovers')(*args)
    assert events and not rest.strip()
    assert extract_parser403_leftovers(*args) == ([], text)


def test_name_variant_preserves_legacy_payload():
    from shab_analyzer.parser129 import extract_parser129_leftovers
    _, (args, kwargs) = captured(SUPPLIED_SHA256[4])
    canonical = args[0].replace("L'inscription ", "L'inscription no ", 1)
    assert extract_parser403_leftovers(*args, **kwargs) == extract_parser129_leftovers(canonical, *args[1:])


@pytest.mark.parametrize('stem', ['60e868c5', '28d975f9', '0bc9a2d5', '7be44b47', '095f22f3'])
def test_existing_fixtures_unchanged(stem):
    import shab_analyzer.parse as parser
    paths = list(FIXTURES.glob(stem + '*.xml'))
    assert len(paths) == 1
    result = parse_publication_xml(paths[0])
    with patch.object(parser, 'extract_parser403_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(paths[0])
