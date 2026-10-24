import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser380 import extract_parser380_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('05333cd2', 'fr.text.notice_director_retained_without_restriction.v1', 1), ('1c7ba564', 'de.text.demerger_renamed_transferor_continuity.v1', 1), ('33cc8c03', 'fr.text.bankruptcy_suspensive_effect_prior_judgment.v1', 1), ('3f9b9fa5', 'fr.text.notice_joint_procuration_mutual_exclusion.v1', 2), ('85753150', 'fr.text.partial_shares_transferred_minor_represented.v1', 2), ('9af77be3', 'de.text.cooperative_entry_fee_clause_deleted.v1', 1), ('a33bfccc', 'fr.text.three_new_foundation_members_unsigned_treasurer.v1', 3), ('b8617e26', 'de.text.incomplete_notice_board_president_corrected.v1', 1), ('bf5a6b85', 'fr.text.board_pair_without_comma_before_and.v1', 2), ('d57c4b32', 'fr.text.shares_transferred_two_individual_managers.v1', 3), ('ddca2ed0', 'fr.text.administration_management_roles_signing_amended.v1', 4), ('ee237ad8', 'fr.text.director_individual_signing_powers_amended.v1', 1)]
SUPPLIED_SHA256 = {'05333cd2': '05333cd2e3d2931576a8376d90ae43dbb51394ef1723347a6257f0a36eafc8f4', '1c7ba564': '1c7ba564dac9faecf08f390fc6ed43f029ee344ace40cc6788fe268e9a8d8dd8', '33cc8c03': '33cc8c0398ec347b8062a7ad48cc41bec1468ace840ad20e1a7b6c10b95cdff9', '3f9b9fa5': '3f9b9fa5b6f6d6b5b449bbbfbdb1be03d2122d2552dda70bd1469ad4a7227f53', '85753150': '857531501d97c914aed44c4742b5f9d83c7b27a5638f7c5d4dfc3bd703dd9e51', '9af77be3': '9af77be32674ad52f0e31c4640b2c7957601be19fa32661896e9197b843886f7', 'a33bfccc': 'a33bfcccd8fe5efe507b0fde81451ba1803e4d59de416f4d94ac5e167a025698', 'b8617e26': 'b8617e2600fbc27b921bccb98043972cf86f808797cb7d56bfcc4460162e5bf1', 'bf5a6b85': 'bf5a6b85cae1318a30509d77414eab21d8796cf4959b087de74bd77f8fd7c659', 'd57c4b32': 'd57c4b32bfe5f9fed044a8f31de6c5bd40d20508d5bb65add7390cfe4287251b', 'ddca2ed0': 'ddca2ed0e9fb44d6427d3e6de0eeedc53930bb4287e6c1ed5e2bb43683858e98', 'ee237ad8': 'ee237ad879ae961919b33bfd4bcc5ba94e4e08a499a5c875a941d1cda01af243'}
CONTEXT_REQUIRED = {"d57c4b32"}

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
        return extract_parser380_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser380_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser380_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 387
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser380_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser380_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser380_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser380_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser380_leftovers(*args)
    if prefix in CONTEXT_REQUIRED:
        assert not events and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e



@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_optional_metadata_absent(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser380_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old



@pytest.mark.parametrize('version', [282, 325, 354, 366, 376, 377, 378, 379])
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
        assert extract_parser380_leftovers(*args, **kwargs) == ([], args[0])
        with patch.object(parser, 'extract_parser380_leftovers', lambda text, *a, **kw: ([], text)):
            assert parse_publication_xml(fixtures[0]) == actual
        with patch.object(parser, name, lambda text, *a, **kw: ([], text)):
            disabled = parse_publication_xml(fixtures[0])
        assert not any(e.rule_id in {case[1] for case in CASES} for e in disabled.events)
        checked += 1
    assert checked



def test_payload_semantics():
    e = selected('05333cd2')[0]
    assert e.role == 'directeur' and e.signing is None
    assert e.payload['corrected'] and e.payload['unrestricted']
    p = selected('1c7ba564')[0].payload
    assert (p['assets'], p['liabilities'], p['agreement_date']) == ("3'803'590.46", "1'126'694.78", '10.11.2020')
    assert not p['capital_increased'] and not p['shares_allocated']
    e = selected('33cc8c03')[0]
    assert e.event_type == 'status_changed'
    assert (e.payload['decision_date'], e.payload['bankruptcy_date']) == ('27 octobre 2020', '15 octobre 2020')
    a, b = selected('3f9b9fa5')
    assert a.payload['not_with'] == [b.payload['name']]
    assert b.payload['not_with'] == [a.payload['name']]
    assert a.signing == b.signing == 'Kollektivprokura zu zweien'
    e, officer = selected('85753150')
    assert (e.payload['count'], e.payload['before'], e.payload['remaining']) == ('168', '500', '332')
    assert officer.payload['minor'] and len(officer.payload['representatives']) == 2
    assert officer.signing == 'ohne Zeichnungsberechtigung'
    p = selected('9af77be3')[0].payload
    assert p['previous_fee'] == '200.--' and p['entry_fee_clause_deleted']
    a, b, c = selected('a33bfccc')
    assert b.payload['origin'] == b.payload['place'] == 'Champoz'
    assert c.role == 'membre du conseil de fondation, trésorier'
    assert all(e.signing == 'ohne Zeichnungsberechtigung' for e in (a, b, c))
    e = selected('b8617e26')[0]
    assert e.payload['place'] == 'Feusisberg' and e.payload['previous_place'] == 'Bertschikon'
    assert e.role == 'Präsident des Verwaltungsrates' and e.signing == 'Einzelunterschrift'
    assert [e.payload['place'] for e in selected('bf5a6b85')] == ['Thônex', 'Thônex']
    assert all(e.signing is None for e in selected('bf5a6b85'))
    transfer, a, b = selected('d57c4b32')
    assert transfer.payload['count'] == '10' and transfer.payload['nominal'] == "1'000"
    assert a.signing == b.signing == 'Einzelunterschrift'
    assert a.role == 'associé-gérant, président' and b.payload['place'] == 'Genève'
    a, b, c, d = selected('ddca2ed0')
    assert a.signing == b.signing == 'Einzelunterschrift'
    assert c.signing == d.signing == 'Kollektivunterschrift zu zweien'
    assert c.payload['with_role'] == d.payload['with_role'] == 'administrateur'
    assert [e.role for e in (a,b,c,d)] == ['président', 'administrateur, directeur général', 'directeur', 'directrice']
    e = selected('ee237ad8')[0]
    assert e.role == 'directeur' and e.signing == 'Einzelunterschrift'


def test_context_required_matches_exact_managers_and_signing():
    _, (args, kwargs) = captured('d57c4b32')
    for source in ('unrelated', kwargs['source_text'].replace('signature individuelle', 'signature collective à deux'), kwargs['source_text'].replace('Ali Khalaid', 'Autre Exemple')):
        assert extract_parser380_leftovers(*args, source_text=source) == ([], args[0])


@pytest.mark.parametrize('text,pattern', [
    ('Exemple Anne, de Genève, à Lausanne, et Exemple Paul, de Berne, à Morges, sont membres du conseil', '_FR_BOARD_MEMBERS_PAIR'),
    ("Le président du Tribunal de l'arrondissement de Lausanne a prononcé le 27 octobre 2020 l'effet suspensif de la procédure de faillite le 15 octobre 2020", '_FR_BANKRUPTCY_PROCEEDINGS_SUSPENDED_TWO_DATES'),
])
def test_legacy_patterns_keep_original_rest(text, pattern):
    import shab_analyzer.parser84 as old
    assert getattr(old, pattern).fullmatch(text)
    args = ('fr', 'fixture', '', None, None, None)
    assert old.extract_parser84_leftovers(text, *args)[0]
    for original in (text, '  ' + text + '  '):
        assert extract_parser380_leftovers(original, *args) == ([], original)


def test_invalid_french_calendar_date_preserved():
    _, (args, kwargs) = captured('33cc8c03')
    for date in ('27 octobre 2020', '15 octobre 2020'):
        changed = args[0].replace(date, '31 février 2020')
        assert extract_parser380_leftovers(changed, *args[1:], **kwargs) == ([], changed)
