import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser350 import extract_parser350_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('1f50b356', 'fr.text.board_composition_collective_signing.v1', 4), ('255f9981', 'fr.text.liquidation_translations.v1', 3), ('3781a2a0', 'fr.text.definitive_composition_moratorium_granted.v1', 2), ('498a458e', 'de.text.corporate_shareholdings_changed.v1', 1), ('680ea7b5', 'de.text.registered_share_transfer_restriction_deleted_correction.v1', 1), ('868b9d7d', 'fr.text.board_members_elected_liquidators.v1', 2), ('a9b1dc25', 'fr.text.managers_presidency_collective_signing.v1', 4), ('cf290fb1', 'de.text.bankruptcy_reopened_company_reinstated.v1', 1), ('d065834b', 'fr.text.managers_liquidators_continued_individual_signing.v1', 2), ('d6058d56', 'fr.text.board_member_role_signing_correction.v1', 1), ('d6675037', 'de.text.company_dissolved_liquidation_name.v1', 2), ('e9370ab5', 'de.text.deceased_associate_share_allocation_unresolved.v1', 1)]
SUPPLIED_SHA256 = {'d6058d56': 'd6058d562828351fec26db17033a01f4d922bba1fbe4ffb1532fc5d3bdbb0b61', 'd6675037': 'd6675037eaa46b7de3cbb116bfdead4713d6496fb640bd5412f0d971ca626aeb', '3781a2a0': '3781a2a05ecef8ca900859cf71d878b00fedaed38b3ea49a0d43687ba7177474', '255f9981': '255f9981b61636e19573e0594c7a48e626398d2aa7c4f43a6fbb41967a1602ca', '868b9d7d': '868b9d7d4ab672a33ad21fedc74e8742e6b87c9c19c825fb07764bb54200f23d', '498a458e': '498a458e7892a5aa41da3cc05bfc5a1bbec39ca525644850bb5e6b14d070365a', 'a9b1dc25': 'a9b1dc25eb6b137770cbd7e3bfb79fa0a9fc3cc69eff72551d0142d4320c09e1', 'cf290fb1': 'cf290fb166ed2454d2ad18c8983708f69c235e42ee3820acd9972ef0ad5cfea3', 'd065834b': 'd065834b7ba777623befccb9e5352f45ff0e23dd8e73a3f99b650a47b90d2563', 'e9370ab5': 'e9370ab52913401b59ee7b74aef69b9438c1ce418032eddd658641444fac8420', '680ea7b5': '680ea7b50c4ea5ba99c00af2fdd5a04ed834f0f2f1d42123397ac8d265ad4632', '1f50b356': '1f50b3569dc47ba67faf279995ad47fc39b23ccf4d544e94d220d89041fde563'}

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
        return extract_parser350_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser350_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser350_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 382
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser350_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser350_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser350_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser350_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser350_leftovers(*args)
    assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e


@pytest.mark.parametrize('prefix', ['bcf422aa', '2ee7eb0d', 'c5fa5c4d', 'f2300fb5', '360fedd4', '0ab39892', 'c9b3ebd6', 'a1e7ae61', '6fa3fe10', 'c9637524', 'a60779f4', 'fa9ce006'])
def test_previous_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser350_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old


def test_payload_and_person_semantics():
    board = selected('1f50b356')
    assert [e.role for e in board] == ['Präsident', 'Vizepräsident', 'Verwaltungsrat', 'Verwaltungsrat']
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in board)
    assert len({e.person_key for e in board}) == 4
    shares = selected('498a458e')[0].payload
    assert (shares['previous_count'], shares['count1'], shares['count2'], shares['nominal']) == ('300', '102', '198', '100')
    assert shares['register1'] == '24058209' and shares['register2'] == '34278743'
    assert all(e.signing is None for e in selected('868b9d7d'))
    assert all(e.signing == 'Einzelunterschrift' for e in selected('d065834b'))
    correction = selected('d6058d56')[0]
    assert correction.role == 'Verwaltungsrat' and correction.signing is None
    assert correction.payload['notice_ref'] == '0/1004975407'
    assert selected('3781a2a0')[0].payload['end_date'] == '01.03.2021'
    assert selected('cf290fb1')[0].payload['decision_date'] == '27.08.2020'
    assert selected('e9370ab5')[0].payload['count'] == '100'
    assert selected('d6675037')[1].role == 'Liquidator'


def test_unbalanced_shareholdings_preserved():
    _, (args, kwargs) = captured('498a458e')
    text = args[0].replace('198 Stammanteile', '199 Stammanteile')
    assert extract_parser350_leftovers(text, *args[1:], **kwargs) == ([], text)


@pytest.mark.parametrize('prefix', ['0bd210d8', '20e004f9', '3ce9b632', '56179eca', '9f7e3aa9', 'c2d438fb', 'd10f9522', 'da81d9fb', 'e3ed525f', 'e6fa8515', 'ea435444', 'f9a68ce8'])
def test_parser349_results_unchanged(prefix):
    test_previous_results_unchanged_without_optional_attributes(prefix)
