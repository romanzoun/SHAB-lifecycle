import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser439 import extract_parser439_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2d68d8d7150bc8023cd91808fd77af861dbf4425693db1546ec50be8ce0c9d2e', '2daf07732ae22a88b523bfc595ae746bbe9f9e472133ff49e13c51a768126bf8', '384c2df3999d3936131f04916e6a38ac876aa6594f1c11fa88657884af3e1b8d', '4d1600937e561662ad037b01d03d861d77356610bad166a62711cc9ffe9016ba', '53e53fa1687c899ebcf5adc3784ceddf5cf2f2c71d990bfbc2d808c33be255c2', '64c9f8928dbb73a8aafec7d91ce6eb54a981f2214a16cca38251fd35d9ed5a42', '8e6fee5f6e37386e43584611043715e010dccc38b7f5c87cd413caa582186275', 'a341287297ba96e1938916b070b26a6384cd05b7aad34facefaf830c80dd6cf8', 'b0c5f3934752af42245cc9d590830fe064adca28d89c9c2e42daa86de9b1427e', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
COUNTS = [0, 0, 5, 2, 0, 1, 8, 3, 1, 0, 4, 0]
NEW_CASES = [i for i, count in enumerate(COUNTS) if count]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser439_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser439_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(path)
    assert len(calls) == 1
    return result, old, calls[0]


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('index', NEW_CASES)
def test_complete_and_unchanged_old_payloads(index):
    result, old, (args, kwargs) = captured(index)
    added, rest = extract(*args, **kwargs)
    assert PARSER_VERSION == 439
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    assert len(added) == COUNTS[index] and rest == ''
    assert old.leftover_text == args[0]
    assert result.events == old.events + added
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('index', NEW_CASES)
def test_unknown_suffix_language_and_invalid_dates(index):
    _, _, (args, kwargs) = captured(index)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract(changed, *args[1:], **kwargs) == ([], changed)
    assert extract(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index', NEW_CASES)
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


@pytest.mark.parametrize('index', NEW_CASES)
def test_no_overlap_with_old_rules_even_in_isolation(index):
    # Exercise every historical extractor on the complete clause in isolation.
    import inspect
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(index)
    for name, old_extract in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser439_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name


@pytest.mark.parametrize('index,owner', [(0, 60), (1, 55), (4, 55), (9, 60), (11, 55)])
def test_existing_formulations_retain_historical_ownership(index, owner):
    import importlib
    result, old, (args, kwargs) = captured(index)
    old_extract = getattr(importlib.import_module(f'shab_analyzer.parser{owner}'), f'extract_parser{owner}_leftovers')
    expected = old_extract(*args)
    assert expected[0] or expected[1] != args[0]
    assert extract(*args, **kwargs) == ([], args[0])
    assert result == old
    assert result.status == 'PARTIALLY_PARSED'
    assert old_extract(*args) == expected




@pytest.mark.parametrize('index,event_type,action,expected', [
    (2, 'officer_changed', 'continued_signing_named_partners', {'name': 'Brabeck-Letmathe Andres', 'signing_partners': ['Clivaz Boris', 'Rossellat Michel', 'Panchaud Lionel']}),
    (3, 'officer_changed', 'removed', {'name': 'Abegglen Rosa Maria'}),
    (5, 'status_changed', 'bankruptcy_appeal_rejected_truncated_effective_year', {'effective_date_raw': '26.02.201', 'decision_date': '26.02.2021', 'judgment_date': '01.12.2020', 'bankruptcy_confirmed': True}),
    (6, 'officer_changed', 'proxy_powers_changed', {'name': 'Grunder Thalia', 'signing_restriction': 'sans autre restriction'}),
    (7, 'officer_changed', 'board_members_president_foreign_residence', {'name': 'Tattini Vincent', 'origin': 'Locle', 'place': 'Genève'}),
    (8, 'organization_changed', 'supporting_documents_supplement', {}),
    (10, 'status_changed', 'association_dissolved_three_committee_liquidators', {'decision_date': '30.06.2020', 'dissolved': True}),
])
def test_evidenced_semantics(index, event_type, action, expected):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    assert rest == '' and events[0].event_type == event_type
    assert events[0].payload['action'] == action
    for key, value in expected.items():
        assert events[0].payload[key] == value
    if index == 2:
        assert all(e.signing == 'Kollektivprokura zu zweien' for e in events[1:])
    if index == 3:
        assert events[1].payload['share_count'] == '200'
        assert events[1].role == 'Gesellschafter, Geschäftsführer'
        assert events[1].signing == 'Einzelunterschrift'
    if index == 5:
        assert 'effective_date' not in events[0].payload
    if index == 6:
        assert events[1].payload['country'] == 'FRA'
        assert events[1].payload['place'] == 'Léaz'
        assert all(e.signing == 'Kollektivprokura zu zweien' for e in events)
        assert all(e.payload['signing_restriction'] == 'sauf entre eux' for e in events[3:])
        assert events[4].payload['origin'] == 'France'
        assert events[7].payload['country'] == 'FRA'
    if index == 7:
        assert events[0].role == 'président'
        assert events[1].payload['country'] == 'FRA'
        assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in events)
    if index == 10:
        assert [e.payload['committee_role'] for e in events[1:]] == ['président', 'secrétaire', 'trésorière']
        assert all(e.role == 'Liquidator' and e.signing == 'Kollektivunterschrift zu zweien' for e in events[1:])


def test_board_signing_requires_adjacent_source_evidence():
    _, _, (args, _) = captured(7)
    events, rest = extract(*args)
    assert rest == '' and all(e.signing is None for e in events)
    events, rest = extract(*args, source_text='Autre personne avec signature collective à deux.')
    assert rest == '' and all(e.signing is None for e in events)


@pytest.mark.parametrize('owner,text', [
    (168, "L'association est dissoute par décision de l'assemblée générale du 30.06.2020. Liquidateurs: les membres du comité Exemple Anne et Exemple Paul, lesquels continuent à signer individuellement"),
    (226, "L'association est dissoute par décision de l'assemblée générale du 30.06.2020. Liquidateurs: les membres du comité Exemple Anne et Exemple Paul, lesquels continuent à signer collectivement à deux"),
])
def test_historical_liquidator_patterns_retain_ownership(owner, text):
    import importlib
    old_extract = getattr(importlib.import_module(f'shab_analyzer.parser{owner}'), f'extract_parser{owner}_leftovers')
    args = (text, 'fr', 'p', '', None, None, None)
    events, rest = old_extract(*args)
    assert events and not rest
    assert extract(*args) == ([], text)
