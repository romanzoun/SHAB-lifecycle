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
from shab_analyzer.parser406 import extract_parser406_leftovers, _LEGACY

FIXTURES = Path(__file__).parent / 'fixtures'
# Supplied SHA-256 identifiers; deliberately independent of the sample directory.
SUPPLIED_SHA256 = [
    '44e94aea3c0b2c9c8ea78768d304973a66c7d5435a33d3cf7c1ab6ce374fb4fb',
    '86d82a806dc46c9412d7ca5b87c455248dab2f540ae748ddde08833364c60855',
    'a229f0da90ec6b035849a687dd9f89595e39b71e8aa99b930ec311ae7df049fa',
    'b7587f8484323d203ddbc21ad45a4aadf0073d64909c1c842c2cb4cc7f265506',
    'c1eaa10297bcb036fc1a85d6806562d3a428778420178f7707d9b1475b7d0d19',
    'c3136cb2a1ea35ba14492bfb13b7919609bdcbd4d6af2ada60f1541bacc6fffb',
    'd6e9d4eee1efb2dbfd29316c043ca3291bab3ab9ba0aa1cd4866c9bed3c1a77d',
    'e298f6fecca6ae6741e8823c73cb6aaf0d50b46eabe1c4891864927557a6f4d9',
    'eeb50e3900c2cec2570c1950052da7c597cf173b5ea13b3c343b369973841d76',
    'ef68e80d4f36b84bd5fc7111d45171c341b238733197f6ea9e83d217886eb726',
    'f5059597c95f9395535d565988afd5ac507e59ba419e436d9ba34da22ddd0561',
    'f5415425ecdcfe8cd530085e8f8de3d2ab2e81a673b8ea70bb53c79db780b9c0',
]
COUNTS = [1, 1, 3, 1, 6, 1, 2, 1, 1, 1, 2, 1]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser406_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser406_leftovers', capture):
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
    added, rest = extract_parser406_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 438
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == COUNTS[index] and not rest
    with patch.object(parser, 'extract_parser406_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (SUPPLIED_SHA256[index] + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('index', range(12))
def test_unknown_suffix_language_and_invalid_dates(index):
    _, (args, kwargs) = captured(index)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser406_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser406_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser406_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index', range(12))
def test_missing_optional_metadata_and_source(index):
    _, (args, kwargs) = captured(index)
    events, rest = extract_parser406_leftovers(*args[:4], None, None, None, **kwargs)
    assert events and not rest
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    events, rest = extract_parser406_leftovers(*args)
    if index == 4:
        assert not events and rest == args[0]
    else:
        assert events and not rest


def test_old_event_without_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event


EXPECTED = [
    ('ownership_changed', {'transferred': '70', 'before': '140', 'received': '140', 'remaining': '70', 'currency': 'CHF'}),
    ('officer_changed', {'origin': 'Belmont-Broye', 'place': 'Vevey'}),
    ('status_changed', {'decision_date': '22.12.2020', 'dissolved': True}),
    ('assets_transferred', {'assets': "53'230'169.00", 'count': "53'443", 'nav': '996.00', 'cash_adjustment': '941.00'}),
    ('ownership_changed', {'transferred': '1', 'nominal': "1'000", 'currency': 'CHF'}),
    ('address_changed', {'office': 'Okay Reisen', 'postal_code': '5001', 'removed': True}),
    ('officer_changed', {'name': 'Harwood Ann Marie', 'previous_name': 'Harwood Anne-Marie', 'origin': 'Ecublens (FR)', 'corrected': True}),
    ('capital_changed', {'decision_date': '08.01.2021', 'kind': 'authorized_capital'}),
    ('status_changed', {'day': '10', 'month': 'novembre', 'year': '2020', 'dissolved': True}),
    ('publication_corrected', {'uid': 'CHE-108.376.159', 'previous_registry_id': 'CH-320.3.042.689-0', 'corrected': True}),
    ('organization_changed', {'duration': 'vier', 'provisional': True, 'representative': 'Edward Salib'}),
    ('status_changed', {'confirmation_date': '27.05.2020', 'liquidation_completed': True, 'before_blocking_year': True}),
]


@pytest.mark.parametrize('index', range(12))
def test_payload_semantics(index):
    _, (args, kwargs) = captured(index)
    events, rest = extract_parser406_leftovers(*args, **kwargs)
    kind, fields = EXPECTED[index]
    assert not rest and events[0].event_type == kind
    for key, value in fields.items():
        assert events[0].payload[key] == value
    if index == 1:
        assert events[0].signing == 'Kollektivunterschrift zu zweien'
        assert events[0].role is None
    if index == 2:
        assert [e.event_type for e in events] == ['status_changed', 'company_name_changed', 'officer_changed']
        assert events[2].role == 'vorsitzender Geschäftsführer, Liquidator'
        assert events[2].signing == 'Einzelunterschrift'
        assert events[2].payload['origin'] == 'Gibloux'
    if index == 4:
        assert [e.event_type for e in events] == ['ownership_changed'] * 3 + ['officer_changed'] * 3
        assert [e.payload['buyer'] for e in events[:3]] == ['Hakimi Abdul Qader', 'Mohammadi Asadullah', 'Ozbak Nasser']
        assert [e.signing for e in events[3:]] == ['Einzelunterschrift'] * 3
        assert [e.role for e in events[3:]] == ['gérant'] * 3
    if index == 6:
        assert events[1].payload['name'] == 'Harwood Neil'
        assert events[1].payload['origin'] == 'Ecublens (FR)'
        assert 'previous_name' not in events[1].payload
        assert 'corrected' not in events[1].payload
    if index == 10:
        assert events[1].role == 'provisorische Sachwalterin'
        assert events[1].payload['administrator_uid'] == 'CHE-114.819.900'


def test_required_source_is_bound_to_names_and_signing():
    _, (args, kwargs) = captured(4)
    for source in ('Unrelated.', kwargs['source_text'].replace('Hakimi', 'Other'), kwargs['source_text'].replace('signature individuelle', 'signature collective à deux')):
        assert extract_parser406_leftovers(*args, source_text=source) == ([], args[0])


@pytest.mark.parametrize('before,after', [('reste titulaire de 70', 'reste titulaire de 71'), ('désormais titulaire de 140', 'désormais titulaire de 69')])
def test_inconsistent_share_counts_rejected(before, after):
    _, (args, kwargs) = captured(0)
    text = args[0].replace(before, after)
    assert text != args[0]
    assert extract_parser406_leftovers(text, *args[1:], **kwargs) == ([], text)


def test_invalid_written_date_rejected():
    _, (args, kwargs) = captured(8)
    text = args[0].replace('10 novembre', '31 novembre')
    assert extract_parser406_leftovers(text, *args[1:], **kwargs) == ([], text)


@pytest.mark.parametrize('version,text,lang', [
    (52, "Selon décision de son assemblée générale du 10.11.2020, l'association a prononcé sa dissolution", 'fr'),
    (78, "L'associé-gérant Exemple Anna cède 70 de ses 140 parts de CHF 100 à l'associé-gérant Exemple SA (CHE-123.456.789), désormais titulaire de 140 parts de CHF 100. L'associé-gérant Exemple Anna reste titulaire de 70 parts de CHF 100", 'fr'),
    (100, 'Neu eingetragene Person: Exemple Anna, von Bern, in Bern, Direktorin, Einzelunterschrift', 'fr'),
    (101, 'Neu eingetragene Person: Exemple Anna, von Bern, in Bern, Direktorin, ohne Unterschrift', 'fr'),
    (113, '[Die folgenden weiteren Adressen werden gelöscht:] [gestrichen: Weitere Geschäftsstelle: Beispiel, Hauptstrasse 1, 3000 Bern]', 'de'),
    (132, "L'associée Exemple SA (CHE-123.456.789) cède 70 de ses 140 parts de CHF 100 à l'associée Autre SA (CHE-987.654.321), désormais titulaire de 140 parts de CHF 100; Exemple SA reste titulaire de 70 parts de CHF 100", 'fr'),
    (243, "L'associé-gérant et président Exemple Anna, dont le prénom exact est Anne, désormais d'Ecublens (FR), est nommé liquidateur avec signature individuelle", 'fr'),
    (162, 'Die Gesellschaft hat mit Beschluss vom 08.01.2021 eine Änderung des genehmigten Kapitals gemäss näherer Umschreibung in den Statuten beschlossen', 'de'),
    (227, 'Die Bestätigung des zugelassenen Revisionsexperten vom 27.05.2020 zur Löschung vor Ablauf des Sperrjahres liegt vor. [Die Löschung der Gesellschaft erfolgt, sobald die Zustimmung der Steuerverwaltung vorliegt.]', 'de'),
])
def test_legacy_rules_keep_ownership_in_isolation(version, text, lang):
    module = importlib.import_module(f'shab_analyzer.parser{version}')
    args = text, lang, 'p', '', None, None, None
    events, rest = getattr(module, f'extract_parser{version}_leftovers')(*args)
    assert events and not rest.strip()
    assert any(p.fullmatch(text) for p in _LEGACY)
    assert extract_parser406_leftovers(*args) == ([], text)


@pytest.mark.parametrize('digest', [
    '170d1fdcf75ad0b85a1dac7780aca904bf9867ba721d333f1a44135cf4a1e718',
    '37446ffb091b102be04b1038668e17a5f0de8565673ec9f030838ac548cc2165',
    '431e03a016e712dad603655da2b3cf2e4f041840ed4d06434587cdd65b423ea6',
    '50162f87197ac07a5ec295bd051f5ca9318e51b32610f4d98d09a828de05aa9d',
    '61b076ca46797a6e9376866e0f79d84d9a9a5aee978f6242f55703d31503cf22',
    '675157f6f3b783a7a8c70603d85bcaacf6c6ea284fe1493a2a27660ad6de4b6f',
    '8ba8ab567d89a51dbfeb2b78050cee5db08e9485bbe74e7c099957485237986e',
    'a1c86f5d82ddffa90e6cccb790de5bd21143adfc528c2a05921b50e52e400b53',
    'ab4cb588c1df695ca9c6f470afd12d9beb528c300bf5cdcaaaa12ad178180680',
    'af9ed54ad9ce008acfdb463121e45b9409043c3fe94a527480c83d07b81bc5fa',
    'e7978facbdfe7b039da376f714ed2410b58ad572a16d7bdb07f0bc906a1775cb',
    'f74bf5c6a409a0c17a5f1e489fea312d9942c675358d8e7ace78b0480ca4357a',
])
def test_previous_release_fixtures_unchanged(digest):
    import shab_analyzer.parse as parser
    path = FIXTURES / (digest + '.xml')
    result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser406_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(path)
