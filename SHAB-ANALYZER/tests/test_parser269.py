import hashlib
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser269 import extract_parser269_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('17eaff0b', 'fr.text.limited_partnership_capital_increased.v1', 1),
    ('38a27172', 'fr.text.shareholder_communications_corrected.v1', 1),
    ('41777789', 'fr.persons.new_collective_procurists_typo.v1', 2),
    ('6e07670d', 'fr.persons.foundation_president_changed_unsigned.v1', 2),
    ('8500014d', 'de.text.branch_transferred_by_division.v1', 1),
    ('9332390e', 'fr.persons.board_president_corrected.v1', 1),
    ('a722e606', 'fr.persons.president_manager_name_corrected.v1', 1),
    ('b39e037c', 'fr.text.assets_transferred_no_liabilities_consideration.v1', 1),
    ('c9c1cd89', 'fr.persons.three_signatures_replaced_by_procuration.v1', 3),
    ('cc76bc05', 'fr.persons.paired_partial_share_transfers.v1', 4),
    ('eb49dd6f', 'fr.persons.corrected_president_partial_share_transfer.v1', 2),
    ('f3cd56fa', 'it.persons.member_director_corrected.v1', 1),
]


def path(prefix):
    matches = list(FIXTURES.glob(prefix + '*.xml'))
    assert len(matches) == 1
    return matches[0]


def selected(prefix):
    rule = next(rule for stem, rule, _ in CASES if stem == prefix)
    return [e for e in parse_publication_xml(path(prefix)).events if e.rule_id == rule]


def invocation(prefix):
    import shab_analyzer.parse as parser
    calls = []

    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser269_leftovers(*args, **kwargs)

    with patch.object(parser, 'extract_parser269_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION >= 269
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    events = [e for e in result.events if e.rule_id == rule]
    assert len(events) == count
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in events)
    if any(e.signing for e in events):
        assert not any(e.rule_id == 'fr.persons.group_signing.v1' for e in result.events)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser269_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['38a27172', '9332390e', 'a722e606', 'b39e037c'])
def test_invalid_date_preserved(prefix):
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', args[0])
    kwargs['source_text'] = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', kwargs['source_text'])
    assert extract_parser269_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['38a27172', 'cc76bc05', 'eb49dd6f', 'f3cd56fa'])
def test_source_required_and_bounded(prefix):
    args, kwargs = invocation(prefix)
    assert extract_parser269_leftovers(*args) == ([], args[0])
    assert extract_parser269_leftovers(*args, source_text=kwargs['source_text'] + ' UNKNOWN_SUFFIX') == ([], args[0])
    changed = kwargs['source_text'].replace('signature individuelle', 'signature collective à deux').replace('moyen de transmission écrit', 'moyen de transmission oral').replace('firma individuale', 'firma collettiva a due')
    assert changed != kwargs['source_text']
    assert extract_parser269_leftovers(*args, source_text=changed) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('17eaff0b', '20 décembre', '32 décembre'),
    ('17eaff0b', "1'146'000", "878'000"),
    ('cc76bc05', 'chacun 75', 'chacun 0'),
    ('cc76bc05', 'de 225 parts', 'de 226 parts'),
    ('eb49dd6f', 'pour 100 parts', 'pour 101 parts'),
    ('b39e037c', 'aucun passif', 'des passifs'),
    ('c9c1cd89', 'signature est radiée', 'signature est maintenue'),
    ('6e07670d', 'ne pas exercer', 'exercer'),
    ('8500014d', 'infolge Spaltung', 'infolge Fusion'),
])
def test_inconsistent_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    kwargs['source_text'] = kwargs['source_text'].replace(old, new)
    assert extract_parser269_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    capital = selected('17eaff0b')[0]
    assert capital.event_type == 'capital_changed' and capital.payload['date'] == '2019-12-20'
    assert capital.payload['before'] == "879'000" and capital.payload['after'] == "1'146'000"
    assert any(e.rule_id == 'fr.text.partnership_contract_amended.v1' for e in parse_publication_xml(path('17eaff0b')).events)
    assert selected('38a27172')[0].payload['recipients'] == 'actionnaires'
    assert not any(e.rule_id == 'fr.text.communications.v1' for e in parse_publication_xml(path('38a27172')).events)
    assert all(e.signing == 'Kollektivprokura zu zweien' for e in selected('41777789'))
    former, president = selected('6e07670d')
    assert former.payload['previous_role'] == 'présidente'
    assert president.role == 'président du conseil de fondation'
    assert all(e.signing is None and e.payload['without_signature'] for e in [former, president])
    assert selected('8500014d')[0].payload['reason'] == 'division'
    for prefix in ['9332390e', 'a722e606']:
        e = selected(prefix)[0]
        assert e.signing is None and e.payload['name'] != e.payload['previous_name']
    assets = selected('b39e037c')[0].payload
    assert assets['assets'] == "354'120" and assets['liabilities'] == assets['consideration'] == '0'
    assert assets['recipient_uid'] == 'CHE-195.998.597'
    assert all(e.signing == 'Kollektivprokura zu zweien' and e.payload['previous_signing_revoked'] for e in selected('c9c1cd89'))
    first, second, recipient1, recipient2 = selected('cc76bc05')
    assert [e.payload['shares_count'] for e in [first, second, recipient1, recipient2]] == [225, 225, 75, 75]
    assert first.payload['recipient'] == recipient1.payload['name'] and second.payload['recipient'] == recipient2.payload['name']
    assert recipient1.signing == recipient2.signing == 'Einzelunterschrift'
    corrected, recipient = selected('eb49dd6f')
    assert corrected.payload['previous_given_name'] == 'Yves' and corrected.payload['origin'] == 'Mont-Noble'
    assert corrected.payload['shares_count'] == recipient.payload['shares_count'] == 100
    assert recipient.signing == 'Einzelunterschrift'
    director = selected('f3cd56fa')[0]
    assert director.role == 'membro, direttore' and director.payload['previous_role'] == 'membro'
    assert director.payload['country'] == 'LT' and director.signing == 'Einzelunterschrift'
