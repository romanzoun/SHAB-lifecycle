import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser377 import extract_parser377_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('06305f31', 'fr.text.two_administrator_liquidators_continue.v1', 2), ('1d682ca6', 'fr.text.relocated_administrator_appointed.v1', 1), ('202e099d', 'fr.text.individual_and_company_shares_transferred.v1', 1), ('206a9a7d', 'fr.text.two_signers_one_relocated.v1', 2), ('2b3c597d', 'fr.text.two_notices_administrator_name_corrected.v1', 1), ('60cb41b4', 'fr.text.notice_individual_signing_retained.v1', 1), ('81327c7a', 'fr.text.supervisory_authority_statutes_amended.v1', 1), ('98f09d3d', 'de.text.board_notice_correction_and_supplement.v1', 2), ('acc8bde5', 'fr.text.director_collective_signing_procuration_revoked.v1', 1), ('c1ad71cb', 'fr.text.notice_collective_signing_exclusions_corrected.v1', 1), ('cd8701de', 'de.text.bankruptcy_recourse_suspensive_effect_granted.v1', 1), ('e94278ab', 'fr.text.liquidation_company_name_retained_corrected.v1', 1)]
SUPPLIED_SHA256 = {'06305f31': '06305f31e48b654c4761670d7b1131c29801e2130678b581b561d87f7caeacdd', '1d682ca6': '1d682ca63ee69210d75fb9677dc04378eb329f750cbb155239f7abd374915238', '202e099d': '202e099d3ec14c8cc2b7a361714b56a99f108e09ad5e87fd2ed0110db308e61d', '206a9a7d': '206a9a7d5a4e5b8a034a6f02ef96d5584e403f88c187bac6a6f39143c4663913', '2b3c597d': '2b3c597de662698fddd3c57cb42b9835469a1ce20f3ccd42db1503c39c297c34', '60cb41b4': '60cb41b4334565be3d5953465d8be38b984d76dcaea2fd4d06eaa38b4b8626e9', '81327c7a': '81327c7adc8814d2f4be8ff4969c4a06e023141b05ccc1ec01a41abf3f3fa82e', '98f09d3d': '98f09d3dc033c58d8c63fcbb98c9c3c1e5a7a95f63a0739325c3e3547a8b87ee', 'acc8bde5': 'acc8bde5c29e59f5d937bcb08f9a041964d17d6a470940d2e49d3d86cc4c5739', 'c1ad71cb': 'c1ad71cb4a19f4cfd37bf941b9b26d235be21d0e14ce55f6a384bb5db5f7fa46', 'cd8701de': 'cd8701ded0b0ea17ee34773fbca493838dcf32599e6b17d4b82eba8dc519f88e', 'e94278ab': 'e94278ab95e04077b30c49b400f1d6a260bc992c0378d100f0b343035168f4f2'}

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
        return extract_parser377_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser377_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser377_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 410
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser377_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser377_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser377_leftovers(args[0], 'en', *args[2:], **kwargs)
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
    for date in set(re.findall(r'\d{2}[-.]\d{2}[-.]\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser377_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser377_leftovers(*args)
    assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e



@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_optional_metadata_absent(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser377_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old


@pytest.mark.parametrize('version', [276, 278, 357, 360, 376])
def test_earlier_rules_keep_ownership_when_disabled(version):
    import shab_analyzer.parse as parser
    source = (Path(__file__).parent / f'test_parser{version}.py').read_text()
    prefixes = set(re.findall(r"['\"]([0-9a-f]{8})(?:[0-9a-f]{56})?['\"]", source))
    name = f'extract_parser{version}_leftovers'
    original = getattr(parser, name)
    checked = 0
    for prefix in sorted(prefixes):
        fixtures = list(FIXTURES.glob(prefix + '*.xml'))
        if len(fixtures) != 1:
            continue
        calls = []
        def capture(*args, **kwargs):
            calls.append((args, kwargs))
            return original(*args, **kwargs)
        with patch.object(parser, name, capture):
            actual = parse_publication_xml(fixtures[0])
        if not calls or not original(*calls[0][0], **calls[0][1])[0]:
            continue
        args, kwargs = calls[0]
        assert extract_parser377_leftovers(*args, **kwargs) == ([], args[0])
        with patch.object(parser, 'extract_parser377_leftovers', lambda text, *a, **kw: ([], text)):
            assert parse_publication_xml(fixtures[0]) == actual
        with patch.object(parser, name, lambda text, *a, **kw: ([], text)):
            disabled = parse_publication_xml(fixtures[0])
        assert not any(e.rule_id in {case[1] for case in CASES} for e in disabled.events)
        checked += 1
    assert checked



def test_payload_semantics():
    a, b = selected('06305f31')
    assert a.role == b.role == 'administrateur, liquidateur'
    assert a.signing == b.signing == 'Einzelunterschrift'
    a = selected('1d682ca6')[0]
    assert a.role == 'administrateur' and a.signing is None
    p = selected('202e099d')[0].payload
    assert (p['transferred_each'], p['before'], p['after'], p['nominal']) == ('5', '19', '29', '200')
    assert p['seller_uid'] == 'CHE-319.273.949'
    a, b = selected('206a9a7d')
    assert a.payload['place'] == 'Montreux' and b.payload['place'] is None
    assert a.signing == b.signing == 'Kollektivunterschrift zu zweien'
    p = selected('2b3c597d')[0].payload
    assert (p['entry1'], p['entry2'], p['name'], p['previous_name']) == ('17929', '18456', 'Neocleous Andros', 'Noecleous Andros')
    assert selected('60cb41b4')[0].signing == 'Einzelunterschrift'
    assert selected('81327c7a')[0].payload['decision_date'] == '29.09.2020'
    assert selected('81327c7a')[0].event_type == 'statutes_changed'
    a, b = selected('98f09d3d')
    assert a.role == 'Verwaltungsratsmitglied, Vizepräsident'
    assert b.role == 'Verwaltungsratsmitglied, Geschäftsführer'
    assert a.payload['place'] == 'Ueberstorf' and b.payload['place'] is None
    a = selected('acc8bde5')[0]
    assert a.role == 'directeur' and a.payload['procuration_revoked'] is True
    a = selected('c1ad71cb')[0]
    assert a.payload['not_with'] == ['Pilet Olivier', 'Vuillet Nicolas']
    assert a.payload['previous_excluded'] == 'Rickli Didier'
    a = selected('cd8701de')[0]
    assert a.event_type == 'status_changed' and a.payload['suspensive_effect'] is True
    assert a.payload['appeal_date'] == '06.11.2020'
    a = selected('e94278ab')[0]
    assert a.payload['liquidation'] is True
    assert a.payload['company'] == a.payload['previous_company'] == 'SIMULPRO SA'


@pytest.mark.parametrize('version,pattern,text', [
    (99, '_FR_ADMINISTRATOR_LIQUIDATORS_CONTINUE', 'Liquidateurs: les administrateurs Exemple Anne, maintenant domiciliée à Genève, et Exemple Paul, lesquels continuent à signer individuellement'),
    (116, '_FR_ADMINISTRATION_AND_DIRECTOR_SIGNING_CHANGES', 'Administration: Exemple Anne, nommée présidente et Exemple Paul, tous deux avec signature collective à deux; les pouvoirs de Exemple Anne sont modifiés en ce sens. Exemple Jean, nommé directeur, signe désormais collectivement à deux sans autre restriction; sa procuration est radiée'),
    (143, '_DE_BANKRUPTCY_APPEAL_SUSPENSIVE_EFFECT', 'Mit Urteil vom 10.11.2020 hat das Kantonsgericht Freiburg der Beschwerde vom 06.11.2020 gegen das Konkurseröffnungsurteil vom 26.10.2020 die aufschiebende Wirkung erteilt'),
    (209, '_FR_SIGNING_EXCLUSIONS_AND_NEW_ADMINISTRATOR', 'Exemple Anne continue à signer collectivement à deux, désormais pas avec Exemple Paul, Exemple Jean. Nouvel administrateur avec signature collective à deux, toutefois pas avec Exemple Paul, ni Exemple Jean: Exemple Marc, de Genève, à Lausanne'),
])
def test_reused_legacy_patterns_preserve_remainder(version, pattern, text):
    from importlib import import_module
    module = import_module(f'shab_analyzer.parser{version}')
    args = (text, 'de' if version == 143 else 'fr', 'fixture', '', None, None, None)
    assert getattr(module, pattern).fullmatch(text)
    assert getattr(module, f'extract_parser{version}_leftovers')(*args)[0]
    assert extract_parser377_leftovers(*args) == ([], text)
    padded = '  ' + text + '  '
    assert extract_parser377_leftovers(padded, *args[1:]) == ([], padded)
