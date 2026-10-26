import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser332 import extract_parser332_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('20f4e032', 'de.text.official_deletion_objected.v1', 1),
    ('38b520f1', 'fr.text.ordinary_registered_capital_increase.v1', 1),
    ('433558ba', 'fr.text.contribution_in_kind_clause_repealed.v1', 1),
    ('4d97f0a8', 'de.text.previous_manager_text_corrected.v1', 1),
    ('4e13c196', 'de.text.covid19_stay_granted.v1', 1),
    ('732e61bf', 'fr.text.board_members_restricted_signing.v1', 2),
    ('92ab8218', 'de.text.branch_register_entry_removed.v1', 1),
    ('a7271172', 'fr.text.foundation_dissolution_authority.v1', 5),
    ('ae9ac4da', 'fr.text.share_transfer_existing_holders.v1', 1),
    ('bb279338', 'de.text.foundation_asset_transfer_no_consideration.v1', 1),
    ('da10e733', 'fr.text.board_vice_presidency_changed.v1', 2),
    ('fa099435', 'fr.text.procuration_name_corrected.v1', 1),
]


def path(prefix):
    paths = list(FIXTURES.glob(prefix + '*.xml'))
    assert len(paths) == 1
    return paths[0]


@lru_cache(None)
def captured(prefix):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser332_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser332_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser332_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 406
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser332_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser332_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser332_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]



@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_bytes_match_supplied_samples(prefix, rule, count):
    supplied_sha256 = {
        '20f4e032': '20f4e032f413c385758ca9732c712a827d42c64a3235dbd23b4c3fd4d27f7d98',
        '38b520f1': '38b520f12d5fc2612c0bfa886c27dbf9babbe45371d21f4f76ae313d49964663',
        '433558ba': '433558ba9095d6f35a80b9da3ab64247275db980e11726cbcd490b21ca30841d',
        '4d97f0a8': '4d97f0a8436824e027a5635ff7ee583eb0d8930f09b848b441c2ffb085807cc9',
        '4e13c196': '4e13c196632044497d8f16e278eefcc76f0fba62ed46782366356fa594d50c42',
        '732e61bf': '732e61bfc81b1ff1939d1a4888143f2fc437f160c744bc212dc4ec772e60a31f',
        '92ab8218': '92ab8218164624eb1127abeed67601f8c8d7e7ce348d63e57569e3259928cfcf',
        'a7271172': 'a7271172ae3024336ec83bd29974b5e93be6d2f5e0e4d9cfd1858acba0f1136c',
        'ae9ac4da': 'ae9ac4da19e1c2c218ee08c030ee7b663729cff55324f183044348b58d098049',
        'bb279338': 'bb279338ed2754293077eba3b71f453cd99994101c25e72d693563948d001812',
        'da10e733': 'da10e733797388f89b1b265b25024603bc94b0830cd9421d2dd856fcd2693a52',
        'fa099435': 'fa099435189179f64fa5cb3e8be7493d88bd4cc2277df03b500393d7cffbe870',
    }
    fixture = path(prefix)
    assert fixture.stem == supplied_sha256[prefix]
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == supplied_sha256[prefix]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_dates_and_optional_source(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser332_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser332_leftovers(*args)
    if prefix == '732e61bf':
        assert not events and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e


@pytest.mark.parametrize('prefix', [
    '0629cb21', '08c613ba', '267dd215', '50985666', '5dad8aa2', '87ac66e7',
    'a9eb2fc1', 'c2b60397', 'ddedd79d', 'f632cfcf', 'f698c58d', 'f7ee7573',
    '09f90c1f', '28528abc', '3e71da53', '762ea6e8', '7f11be01', '950a0991',
    '9c5c898c', 'bb4542dd', 'd518eb02', 'f63aa392', 'f663e109', 'f8fc2919',
    '03dcc069', '315da231', '353d9e29', '693c452c', '7c27565a', '8889623a',
    'a5f4be23', 'bbf607eb', 'c332722f', 'ce010fcd', 'cfbe1db2', 'f0fd9d83',
    '518fef8d', '5404cc5f', '54125ed4', '6d18ed72', '6d50c77a', '7a6515f3',
    '930507a1', 'a16a5540', 'a564e09d', 'b384c365', 'cf527290', 'ecba5198',
    '05a6f15b', '076b6cc6', '0f17b349', '3774d2b6', '54b4ab1b', '58504ce5',
    '68ffaf6b', '87d4b8af', '950a846d', 'a51340d6', 'bb7c8a65', 'f970cd7e',
    '1cf200d1', 'c9cb541c', 'e3c5c5cd', '94b72118-d3cb-46f4-8cf3-8d526586b9f2',
])
def test_previous_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser332_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old


def test_payload_semantics():
    objection = selected('20f4e032')[0]
    assert objection.event_type == 'status_changed'
    assert objection.payload['legal_basis'] == 'Art. 159 Abs. 5 lit. a HRegV'
    capital = selected('38b520f1')[0]
    assert capital.event_type == 'capital_changed'
    assert capital.payload['previous_capital'] == "110'000"
    assert capital.payload['capital'] == "145'000"
    assert capital.payload['issued'] == "35'000"
    assert capital.payload['count'] == "145'000"
    assert capital.payload['fully_paid'] is True
    assert selected('433558ba')[0].payload['legal_basis'] == 'art. 628 al. 4 CO'
    historical = selected('4d97f0a8')[0]
    assert historical.event_type == 'organization_changed'
    assert historical.payload['historical'] is True and historical.payload['corrected'] is True
    assert historical.role is None and historical.signing is None
    assert historical.payload['count'] == '10'
    stay = selected('4e13c196')[0]
    assert stay.event_type == 'status_changed' and stay.payload['duration_months'] == 3
    assert stay.payload['end_date'] == '17.10.2020'
    board = selected('732e61bf')
    assert all(e.role == 'Verwaltungsrat' and e.signing == 'Kollektivunterschrift zu zweien' for e in board)
    assert all(e.payload['authorized_partners'] == ['Frantskevych Igor', 'Petryshche Viacheslav'] for e in board)
    assert [e.payload['place'] for e in board] == ['Collex-Bossy', 'Thônex']
    assert selected('92ab8218')[0].payload['registry'] == 'Zürich'
    foundation = selected('a7271172')
    assert foundation[0].event_type == 'status_changed'
    assert all(e.role == 'Stiftungsrat' and e.signing == 'ohne Zeichnungsberechtigung' for e in foundation[1:4])
    assert foundation[4].role == 'Liquidator' and foundation[4].signing is None
    transfer = selected('ae9ac4da')[0]
    assert transfer.event_type == 'ownership_changed'
    assert transfer.payload['transferred'] == '20'
    assert transfer.payload['seller_remaining'] == '80' and transfer.payload['buyer_remaining'] == '120'
    asset = selected('bb279338')[0]
    assert asset.event_type == 'ownership_changed' and asset.payload['no_consideration'] is True
    assert asset.payload['assets'] == "4'081'360.64" and asset.payload['liabilities'] == "168'172.52"
    vice, former = selected('da10e733')
    assert vice.role == 'Vorstand, Vizepräsident' and vice.signing == 'Kollektivunterschrift zu zweien'
    assert former.role is None and former.signing == 'ohne Zeichnungsberechtigung'
    assert former.payload['previous_role'] == 'Vizepräsident'
    correction = selected('fa099435')[0]
    assert correction.role == 'Prokurist' and correction.signing is None
    assert correction.payload['name'] == 'Westermaier Tobias'
    assert correction.payload['previous_name'] == 'Westmaier Tobias' and correction.payload['corrected'] is True


def test_restricted_signing_requires_matching_explicit_source():
    _, (args, kwargs) = captured('732e61bf')
    for source in ['', kwargs['source_text'].replace('signature collective à deux', 'signature individuelle'), kwargs['source_text'].replace('Frantskevych Igor', 'Unknown Partner')]:
        events, leftover = extract_parser332_leftovers(*args, source_text=source)
        assert events == [] and leftover == args[0]


@pytest.mark.parametrize('old,new', [("35'000", "35'001"), ("110'000", "111'000")])
def test_inconsistent_capital_preserved(old, new):
    _, (args, kwargs) = captured('38b520f1')
    changed = args[0].replace(old, new)
    events, leftover = extract_parser332_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed
