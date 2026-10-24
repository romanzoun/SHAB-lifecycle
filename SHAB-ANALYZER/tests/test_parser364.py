import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser364 import extract_parser364_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('07493c0d', 'fr.text.five_direction_council_members_unsigned.v1', 5), ('0d40dd29', 'fr.text.manager_share_transfer_new_associate_remaining.v1', 1), ('1a32f6d9', 'it.text.demerger_with_capital_reduction.v1', 1), ('1c52462f', 'de.text.board_previous_details_corrected.v1', 2), ('269a35c0', 'fr.text.director_elected_board_member_joint_signing.v1', 1), ('42b4a508', 'de.text.authorized_capital_amendment_history.v1', 1), ('6d154b6d', 'fr.text.registered_share_nominal_corrected_notice.v1', 1), ('710ae056', 'fr.text.associate_manager_nominal_corrected_malformed_notice.v1', 1), ('79b5d750', 'fr.text.foundation_vice_president_appointed.v1', 2), ('d238096b', 'fr.text.liquidation_domicile_with_care_of.v1', 1), ('f0c9ed26', 'de.text.contribution_acquisition_clause_deletion_date_corrected.v1', 1), ('fa87e1f2', 'it.text.commissioner_powers_extended.v1', 1)]
SUPPLIED_SHA256 = {'07493c0d': '07493c0d183e5514d0e41f74521da4b985d250411dbdd584b58d04d8414f640d', '0d40dd29': '0d40dd2945d6b5109e58a99266e106594a40dbbc77ff0d6a16f1c0b696bf2c1d', '1a32f6d9': '1a32f6d9a2a8d39e8c711b6ba45ba041541577c14bedbf2699442b1f516d65b9', '1c52462f': '1c52462f831ed659b3946e6bb993b980e91fa57e7b098a38cfe46b2ce26b5f20', '269a35c0': '269a35c0c7bf7e2b708c2bf18065b4c2b929563d16430fdab2fb4cb9d1108b03', '42b4a508': '42b4a508590630f0392887868896db621da70f92056cbabcc8fb472e5e986c06', '6d154b6d': '6d154b6d42fef1dc3f219578f4686370cda23c1749a159f54391fe36cbf52372', '710ae056': '710ae056e31bc091d92de1926fbcff83e255ed72b30a0301bf946c361223a876', '79b5d750': '79b5d7501bff192c3ccdebf5a834e56c6eaf51501af375cfe3f481b14736aca2', 'd238096b': 'd238096b0702803a9d869cc12515257f3978b6d9f939ffb2dc4fca5ecc376175', 'f0c9ed26': 'f0c9ed2643162362c0477708236110df7060bba3608e364902cf13e5d01a27da', 'fa87e1f2': 'fa87e1f201aa191009305286fb7e51794d1e6dc26bfbb23d039d58e41acaf9f1'}

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
        return extract_parser364_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser364_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser364_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 385
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser364_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser364_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser364_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_bytes_match_supplied_samples(prefix, rule, count):
    supplied_sha256 = SUPPLIED_SHA256
    fixture = path(prefix)
    assert fixture.stem == supplied_sha256[prefix]
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == supplied_sha256[prefix]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_dates_and_optional_source(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser364_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser364_leftovers(*args)
    assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e




@pytest.mark.parametrize('prefix', ['14296b04', '1c871906', '3293f488', '462a9256', '4e63c138', '66475661', '740111db', '7ba42f80', '9974f6b7', 'da5fb894', 'dea8e644', 'f223fea7'])
def test_parser363_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser364_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for event in baseline.events:
        assert Event(**vars(event)) == event


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_optional_metadata_absent(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser364_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]


@pytest.mark.parametrize('text', ['', 'Unsupported clause', '   '])
def test_empty_and_unknown_residuals(text):
    assert extract_parser364_leftovers(text, 'fr', 'fixture', '', None, None, None) == ([], text.strip())




def test_payload_semantics():
    assert [e.signing for e in selected('07493c0d')] == ['ohne Zeichnungsberechtigung'] * 5
    transfer = selected('0d40dd29')[0].payload
    assert (transfer['transferred'], transfer['remaining'], transfer['nominal']) == ('5', '15', "1'000")
    assert selected('1a32f6d9')[0].payload['reduction'] == "1'000'000.00"
    board = selected('1c52462f')
    assert [e.role for e in board] == ['Präsident des Verwaltungsrates', 'Mitglied des Verwaltungsrates']
    assert all(e.signing == 'Einzelunterschrift' for e in board)
    assert all('Liquidator' in e.payload['previous_role'] for e in board)
    assert selected('269a35c0')[0].signing == 'Kollektivunterschrift zu zweien'
    assert selected('42b4a508')[0].payload['article'] == '3a'
    capital = selected('6d154b6d')[0].payload
    assert (capital['capital'], capital['paid_up'], capital['nominal'], capital['previous_nominal']) == ("100'000", "75'000", '0.10', '0.01')
    corrected = selected('710ae056')[0]
    assert corrected.payload['notice_date_raw'] == '09.10.200'
    assert corrected.payload['nominal'] == '100' and corrected.payload['previous_nominal'] == '200'
    assert corrected.payload['signing_condition'] == 'avec le gérant président'
    foundation = selected('79b5d750')
    assert foundation[0].role == 'Vizepräsidentin' and foundation[0].signing is None
    assert foundation[1].role == 'Mitglied des Stiftungsrates'
    assert foundation[1].signing == 'ohne Zeichnungsberechtigung'
    assert selected('d238096b')[0].payload['postal_code'] == '1264'
    assert selected('f0c9ed26')[0].payload['foundation_date'] == '16.09.1998'
    assert selected('fa87e1f2')[0].payload['scope'] == 'amministrazione corrente e straordinaria'


@pytest.mark.parametrize('prefix,old,new', [
    ('0d40dd29', 'nouvel associé pour 5', 'nouvel associé pour 6'),
    ('0d40dd29', "titulaire de 15 parts de CHF 1'000", "titulaire de 15 parts de CHF 2'000"),
    ('6d154b6d', "non divisé en 1'000'000", "non divisé en 2'000'000"),
    ('710ae056', 'non pas associé, 70', 'non pas associé, 71'),
])
def test_inconsistent_repeated_values_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser364_leftovers(changed, *args[1:], **kwargs) == ([], changed)
