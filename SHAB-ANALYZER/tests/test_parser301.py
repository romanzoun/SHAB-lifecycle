import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser301 import extract_parser301_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('0d1c2e2d', 'it.text.wholly_owned_merger_no_allocation.v1', 1),
    ('551f322c', 'fr.persons.foundation_members_treasurer.v1', 2),
    ('5b75fc16', 'de.text.authorized_capital_revocation_omission.v1', 1),
    ('5c4a7f00', 'de.text.demerger_common_shareholder_assets.v1', 1),
    ('988e42c0', 'de.text.corporate_associate_renamed.v1', 1),
    ('9fd8ce14', 'fr.persons.six_liquidators_appointed.v1', 6),
    ('b3984ed0', 'de.text.bankruptcy_petition_rejected_continued.v1', 1),
    ('b72c3c56', 'fr.text.definitive_moratorium_deadline_extended.v1', 1),
    ('c8c7d689', 'it.text.reinstatement_bankruptcy_reopened.v1', 1),
    ('cd8e51a0', 'fr.text.domicile_locality_spelling_corrected.v1', 1),
    ('d72bf261', 'fr.persons.associate_manager_liquidator_origin.v1', 1),
    ('e4b0e389', 'fr.persons.president_now_sole_administrator.v1', 1),
]


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
        return extract_parser301_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser301_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 302
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
    assert extract_parser301_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser301_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])

@pytest.mark.parametrize('prefix', ['0d1c2e2d', '5b75fc16', '5c4a7f00', 'b3984ed0', 'c8c7d689', 'cd8e51a0'])
def test_invalid_dates_preserved(prefix):
    import re
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', args[0], count=1)
    assert changed != args[0]
    assert extract_parser301_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('old,new', [('5 mai', '32 mai'), ('9 novembre', '31 novembre')])
def test_invalid_written_dates_preserved(old, new):
    args, kwargs = invocation('b72c3c56')
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser301_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['551f322c', '9fd8ce14', 'd72bf261', 'e4b0e389'])
def test_unknown_signing_preserved(prefix):
    args, kwargs = invocation(prefix)
    changed = args[0].replace('signature collective à deux', 'signature inconnue').replace('signature individuelle', 'signature inconnue')
    assert changed != args[0]
    assert extract_parser301_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    merger = selected('0d1c2e2d')[0].payload
    assert merger['assets'] == "311'494.43" and merger['liabilities'] == "115'418.56"
    assert merger['capital_increase'] is False and merger['share_allocation'] is False
    members = selected('551f322c')
    assert [e.payload['place'] for e in members] == ['Lutry', 'Zurich']
    assert members[0].role.endswith('trésorier')
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in members)
    assert selected('5b75fc16')[0].payload['revocation_date'] == '15.04.2015'
    demerger = selected('5c4a7f00')[0].payload
    assert demerger['assets'] == "2'299'783.74" and demerger['capital_increase'] is False
    corporate = selected('988e42c0')[0].payload
    assert corporate['register'] == 'HRB 6126' and corporate['count'] == '200'
    assert corporate['previous_name'] != corporate['name']
    liquidators = selected('9fd8ce14')
    assert len({e.person_key for e in liquidators}) == 6
    assert all(e.role == 'liquidateur' and e.signing == 'Kollektivunterschrift zu zweien' for e in liquidators)
    assert selected('b3984ed0')[0].payload['decision_date'] == '30.04.2020'
    moratorium = selected('b72c3c56')[0].payload
    assert moratorium['decision_date'] == '05.05.2020' and moratorium['deadline_date'] == '09.11.2020'
    reopening = selected('c8c7d689')[0].payload
    assert reopening['reinstatement_date'] == '12.05.2020' and reopening['reopening_date'] == '14.05.2020'
    assert reopening['closure_date'] == '21.01.2020' and reopening['opening_date'] == '17.07.2017'
    locality = selected('cd8e51a0')[0].payload
    assert locality['place'] == 'Chêne-Bourg' and locality['previous_place'] == 'Chène-Bourg'
    liquidator = selected('d72bf261')[0]
    assert liquidator.payload['origin'] == 'Montreux' and liquidator.signing == 'Einzelunterschrift'
    administrator = selected('e4b0e389')[0]
    assert administrator.role == 'administrateur unique' and administrator.signing == 'Einzelunterschrift'
    assert administrator.payload['previous_signing'] == 'Kollektivunterschrift zu zweien'


def test_changed_register_preserved():
    args, kwargs = invocation('988e42c0')
    changed = args[0].rsplit('HRB 6126', 1)
    changed = 'HRB 6127'.join(changed)
    assert extract_parser301_leftovers(changed, *args[1:], **kwargs) == ([], changed)
