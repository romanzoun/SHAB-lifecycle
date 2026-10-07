import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser297 import extract_parser297_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('10b959bd', 'de.text.authorized_participation_capital_expired.v1', 1), ('158f3c28', 'de.text.bearer_shares_listed_securities.v1', 1), ('4149c115', 'fr.text.publication_communications_completed.v1', 1), ('5a3d6bd1', 'de.text.profit_certificates_word_corrected.v1', 1), ('70b935a2', 'fr.persons.given_name_origin_residence_corrected.v1', 1), ('742b23bf', 'fr.persons.board_roles_de_xml.v1', 2), ('7a05bec7', 'de.text.assets_transfer_sole_proprietorship.v1', 1), ('7be44b47', 'fr.persons.liquidator_origin_changed.v1', 1), ('9c8e9b3c', 'fr.persons.share_transfer_two_managers.v1', 3), ('a609bb9e', 'fr.persons.board_signing_corrected.v1', 1), ('b7aaac44', 'fr.persons.manager_replaced_de_xml.v1', 2), ('ba0d2e07', 'fr.text.share_voting_privilege_corrected.v1', 1)]


def path(prefix):
    paths = list(FIXTURES.glob(prefix + '*.xml'))
    assert len(paths) == 1
    return paths[0]


def selected(prefix):
    rule = next(rule for stem, rule, _ in CASES if stem == prefix)
    return [e for e in parse_publication_xml(path(prefix)).events if e.rule_id == rule]


def invocation(prefix):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser297_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser297_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 307
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
    assert extract_parser297_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser297_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])



@pytest.mark.parametrize('prefix', ['10b959bd', '4149c115', '7a05bec7', 'a609bb9e'])
def test_invalid_dates_preserved(prefix):
    import re
    args, kwargs = invocation(prefix)
    old = re.search(r"\d{2}\.\d{2}\.\d{4}", args[0])[0]
    changed = args[0].replace(old, '31.02.2020')
    assert extract_parser297_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['7be44b47', '9c8e9b3c', 'b7aaac44'])
def test_source_signing_required(prefix):
    args, kwargs = invocation(prefix)
    assert extract_parser297_leftovers(*args, source_text='') == ([], args[0])
    changed = kwargs['source_text'].replace('signature individuelle', 'signature collective à deux')
    assert extract_parser297_leftovers(*args, source_text=changed) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('10b959bd', '06.04.2016', '07.04.2016'),
    ('9c8e9b3c', "9 parts de CHF 1'000", "8 parts de CHF 1'000"),
    ('ba0d2e07', '80 actions', '81 actions'),
])
def test_inconsistent_repeated_values_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new, 1)
    assert extract_parser297_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_reversed_correction_dates_preserved():
    args, kwargs = invocation('a609bb9e')
    changed = args[0].replace('14.07.2017', '20.07.2017')
    assert extract_parser297_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    assert selected('10b959bd')[0].payload['action'] == 'authorized_capital_expired'
    assert selected('158f3c28')[0].payload['reason'] == 'listed_securities'
    assert len(selected('4149c115')[0].payload['communication_methods']) == 3
    assert selected('5a3d6bd1')[0].payload['removed_word'] == 'SHAB'
    corrected = selected('70b935a2')[0]
    assert corrected.payload['given_names'] == 'José Antonio'
    assert corrected.payload['origin'] == 'Mex (VD)'
    assert corrected.payload['place'] == 'Renens (VD)'
    president, director = selected('742b23bf')
    assert president.role == 'président'
    assert director.role == 'administrateur'
    assert director.payload['previous_role'] == 'président'
    assert president.signing == director.signing == 'Kollektivunterschrift zu zweien'
    transfer = selected('7a05bec7')[0]
    assert transfer.payload['assets'] == transfer.payload['consideration'] == "30'000.00"
    assert transfer.payload['recipient_uid'] == 'CHE-343.102.679'
    liquidator = selected('7be44b47')[0]
    assert liquidator.role == 'liquidatrice' and liquidator.signing == 'Einzelunterschrift'
    transfer, previous, new = selected('9c8e9b3c')
    assert transfer.payload['transferred'] == '9' and transfer.payload['remaining'] == '11'
    assert previous.role == 'associé, gérant président'
    assert new.role == 'associée, gérante' and new.payload['origin'] == 'France'
    assert previous.signing == new.signing == 'Einzelunterschrift'
    assert selected('a609bb9e')[0].signing == 'Kollektivunterschrift zu zweien'
    removed, appointed = selected('b7aaac44')
    assert removed.event_type == 'officer_removed' and removed.signing is None
    assert appointed.role == 'gérant' and appointed.signing == 'Einzelunterschrift'
    assert selected('ba0d2e07')[0].payload['privileged_class'] == 2
