import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser379 import extract_parser379_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('3dfa636d', 'de.text.business_demerger_common_sole_associate.v1', 1), ('41fe5eaa', 'de.text.provisional_moratorium_extended_cantonal_single_judge.v1', 1), ('44dea9b3', 'fr.text.two_registered_share_classes_corrected.v1', 1), ('4e77eddb', 'fr.text.board_members_mutual_signing_exclusion.v1', 2), ('6e808700', 'fr.text.liquidation_name_translation_corporate_liquidator.v1', 2), ('70c60f1c', 'fr.text.three_board_members_mixed_signing.v1', 3), ('add5028a', 'de.text.erroneous_art155_deletion_revoked_bankruptcy.v1', 1), ('aebca844', 'fr.text.female_board_member_appointed_vice_president.v1', 1), ('b445b577', 'fr.text.foundation_pair_shared_origin_domicile.v1', 2), ('d243587f', 'fr.text.notice_management_membership_retained.v1', 1), ('e5479e52', 'fr.text.unsigned_board_members_residue.v1', 2), ('fe7e0c92', 'fr.text.four_board_members_two_excluded_pairs.v1', 4)]
SUPPLIED_SHA256 = {'3dfa636d': '3dfa636db7bdb0af7b939c7f1fe6013ba9ce1005eb1634ca8e2bb3dd4a80a784', '41fe5eaa': '41fe5eaac4a640cd6ff82a1a8f732058e5a44b0a2321806e3daa3487cbe99cb2', '44dea9b3': '44dea9b30f1d9d692eda4a3c22feccce30438b7c94cfca0789ee290a806162bf', '4e77eddb': '4e77eddb181d68ebd84484b4be0bf68a1f566b0f5cb97574e24c038261f155e7', '6e808700': '6e808700c163d8486f80bc24490e137d7bc68870535eee35ce57bf92e6902677', '70c60f1c': '70c60f1cc74944b505d3acaf618590a64d6d70c2be24d4de81a13cc888301a7d', 'add5028a': 'add5028a7770bd1acd729ab6c8a973e015233c7a8af2ecf3540b2f58b8789c25', 'aebca844': 'aebca84427c7ac6dc7c8e28e8d5aa0f89749728df5baf00179ad1bc68c7c00c3', 'b445b577': 'b445b577787a07ffb75b7e396d2136dd923923e5993ce8340aa0ba7649d6a3d3', 'd243587f': 'd243587f42eac06059eea24711c4b15a2a6ace7300a54bf636b79dec9860badb', 'e5479e52': 'e5479e52447ddd11fc5f5b0bf30b4a2a9e4c7d4b1d587e9597b128ceab52203b', 'fe7e0c92': 'fe7e0c92aa6d849023515f267e020ad9e7326eac63a6675e6193fa7e7a26775b'}
CONTEXT_REQUIRED = {"44dea9b3", "4e77eddb", "70c60f1c", "b445b577", "e5479e52"}

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
        return extract_parser379_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser379_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser379_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 383
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser379_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser379_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser379_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser379_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser379_leftovers(*args)
    if prefix in CONTEXT_REQUIRED:
        assert not events and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e



@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_optional_metadata_absent(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser379_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old



@pytest.mark.parametrize('version', [268, 271, 301, 330, 357, 378])
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
        assert extract_parser379_leftovers(*args, **kwargs) == ([], args[0])
        with patch.object(parser, 'extract_parser379_leftovers', lambda text, *a, **kw: ([], text)):
            assert parse_publication_xml(fixtures[0]) == actual
        with patch.object(parser, name, lambda text, *a, **kw: ([], text)):
            disabled = parse_publication_xml(fixtures[0])
        assert not any(e.rule_id in {case[1] for case in CASES} for e in disabled.events)
        checked += 1
    assert checked


@pytest.mark.parametrize('prefix', sorted(CONTEXT_REQUIRED))
def test_source_must_match_residue(prefix):
    _, (args, kwargs) = captured(prefix)
    assert extract_parser379_leftovers(*args, source_text='unrelated') == ([], args[0])
    # A similar publication with a different person/count cannot authorize this residue.
    source = kwargs['source_text']
    changed = source.replace('116\'997', '116\'998') if prefix == '44dea9b3' else source.replace(selected(prefix)[0].payload['name'], 'Autre Personne')
    assert changed != source
    assert extract_parser379_leftovers(*args, source_text=changed) == ([], args[0])


def test_payload_semantics():
    p = selected('3dfa636d')[0].payload
    assert (p['assets'], p['liabilities'], p['agreement_date']) == ("209'245'018.00", "74'279'344.00", '24.08.2020')
    assert p['capital_increased'] is False and p['shares_allocated'] is False
    a = selected('41fe5eaa')[0]
    assert a.event_type == 'status_changed'
    assert (a.payload['decision_date'], a.payload['until_date']) == ('28.10.2020', '11.01.2021')
    p = selected('44dea9b3')[0].payload
    assert (p['count1'], p['count2'], p['nominal1'], p['nominal2'], p['share_class']) == ("116'997", "17'018", '1', '1', 'A')
    assert p['transfer_restricted'] is True
    a, b = selected('4e77eddb')
    assert a.payload['not_with'] == ['Kouame Marie Francine']
    assert b.payload['not_with'] == ['Gurosheva Alexandra']
    assert b.payload['name'] == 'Kouame Francine'
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in (a,b))
    a, b = selected('6e808700')
    assert a.payload['translation'] == 'Mido Holdings SA en liquidation'
    assert b.role == 'liquidatrice' and b.signing is None
    assert b.payload['liquidator_uid'] == 'CHE-168.159.507'
    a, b, c = selected('70c60f1c')
    assert a.role == 'président' and a.signing == 'Einzelunterschrift'
    assert b.signing == c.signing == 'Kollektivunterschrift zu zweien'
    assert (b.payload['place'], c.payload['place'], c.role) == ('Veyrier', 'Genève', 'secrétaire')
    assert selected('add5028a')[0].payload['deletion_revoked'] is True
    a = selected('aebca844')[0]
    assert a.role == 'administratrice, vice-présidente' and a.signing == 'Einzelunterschrift'
    a,b = selected('b445b577')
    assert a.payload['origin'] == 'Kleinandelfingen'
    assert b.payload['origin'] == b.payload['place'] == 'Morges'
    assert a.signing == b.signing == 'Kollektivunterschrift zu zweien'
    assert selected('d243587f')[0].role == 'membre de la direction'
    assert [e.payload['place'] for e in selected('e5479e52')] == ['Romainmôtier', 'Nyon']
    assert all(e.signing == 'ohne Zeichnungsberechtigung' for e in selected('e5479e52'))
    events = selected('fe7e0c92')
    assert [e.role for e in events[:3]] == ['président', 'vice-président', 'secrétaire']
    assert [e.payload['not_with'] for e in events] == [[events[j].payload['name']] for j in (2,3,0,1)]


def test_foundation_legacy_patterns_retain_original_text():
    from shab_analyzer.parser120 import _FR_TWO_FOUNDATION_MEMBERS, extract_parser120_leftovers
    text = 'Nouveaux membres du conseil de fondation : Exemple Anne, de Genève, à Lausanne, et Exemple Paul, de Berne, à Morges'
    args = (text, 'fr', 'fixture', '', None, None, None)
    assert _FR_TWO_FOUNDATION_MEMBERS.fullmatch(text)
    assert extract_parser120_leftovers(*args)[0]
    assert extract_parser379_leftovers(*args) == ([], text)
    padded = '  ' + text + '  '
    assert extract_parser379_leftovers(padded, *args[1:]) == ([], padded)
