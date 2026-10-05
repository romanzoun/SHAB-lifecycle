import hashlib
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser266 import extract_parser266_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('2770f762', 'it.text.foreign_head_office_capital_changed.v1', 1),
    ('29d0fae4', 'fr.persons.foundation_member_restricted_signing.v1', 2),
    ('36281be9', 'fr.persons.deputy_director_restricted_signing.v1', 1),
    ('3a1c457f', 'de.text.company_name_translations.v1', 1),
    ('4284b392', 'fr.persons.new_manager_president.v1', 1),
    ('718f1a3b', 'fr.persons.administrator_replaced_restricted_signing.v1', 2),
    ('73d2c5ad', 'de.text.authorized_participation_capital_changed.v1', 1),
    ('94053a9f', 'de.persons.auditor_renamed.v1', 1),
    ('b2bf344e', 'de.text.assets_transferred_investment_claims.v1', 1),
    ('bc63ac68', 'fr.persons.director_name_corrected.v1', 1),
    ('c148bbb3', 'fr.persons.administrator_liquidator.v1', 1),
    ('ff2fb0c8', 'fr.text.preferred_shares_converted.v1', 1),
]
SOURCE_CASES = ['29d0fae4', '4284b392', '718f1a3b', '73d2c5ad', 'bc63ac68', 'c148bbb3', 'ff2fb0c8']


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
        return extract_parser266_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser266_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 267
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    events = [e for e in result.events if e.rule_id == rule]
    assert len(events) == count
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in events)
    assert not any(e.rule_id == 'fr.persons.group_signing.v1' for e in result.events)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser266_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', SOURCE_CASES)
def test_source_required_and_bounded(prefix):
    args, kwargs = invocation(prefix)
    assert extract_parser266_leftovers(*args) == ([], args[0])
    kwargs['source_text'] += ' UNKNOWN_SUFFIX'
    assert extract_parser266_leftovers(*args, **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix', ['73d2c5ad', 'b2bf344e', 'bc63ac68'])
def test_invalid_date_preserved(prefix):
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', args[0])
    kwargs['source_text'] = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', kwargs['source_text'])
    assert extract_parser266_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,old,new', [
    ('29d0fae4', 'avec signature collective à deux', 'avec signature individuelle'),
    ('4284b392', 'avec signature individuelle', 'avec signature collective à deux'),
    ('718f1a3b', 'avec signature collective à deux', 'avec signature individuelle'),
    ('73d2c5ad', '23.01.2020', '24.01.2020'),
    ('bc63ac68', 'avec signature collective à deux', 'avec signature individuelle'),
    ('c148bbb3', 'avec signature individuelle', 'avec signature collective à deux'),
    ('ff2fb0c8', 'liées selon statuts', 'non liées'),
])
def test_source_disagreement_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    assert old in kwargs['source_text']
    kwargs['source_text'] = kwargs['source_text'].replace(old, new)
    assert extract_parser266_leftovers(*args, **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('2770f762', "7'001 azioni", "7'002 azioni"),
    ('2770f762', "7'001 azioni", "7'001.5 azioni"),
    ('73d2c5ad', '133 Genussscheine', '133.5 Genussscheine'),
    ('2770f762', "7'000 azioni", '0 azioni'),
    ('ff2fb0c8', "500'000 actions", "500'001 actions"),
    ('ff2fb0c8', "300'000 actions", "600'000 actions"),
    ('c148bbb3', '100 actions', '0 actions'),
    ('b2bf344e', "39'901.641 Ansprüche", '0 Ansprüche'),
    ('b2bf344e', 'Klasse 1', 'Klasse 3'),
])
def test_inconsistent_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    kwargs['source_text'] = kwargs['source_text'].replace(old, new)
    assert changed != args[0]
    assert extract_parser266_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    head = selected('2770f762')[0].payload
    assert head['capital'] == "7'001'000" and head['previous_capital'] == "7'000'000" and head['currency'] == 'EUR'
    removed, new = selected('29d0fae4')
    assert removed.signing == 'ohne Zeichnungsberechtigung'
    assert new.signing == 'Kollektivunterschrift zu zweien'
    assert new.payload['authorized_partner_roles'] == ['trésorier', 'secrétaire']
    deputy = selected('36281be9')[0]
    assert deputy.role == 'sous-directrice' and deputy.payload['procuration_removed']
    assert deputy.payload['excluded_partner'] == 'Menoni Johana'
    assert len(selected('3a1c457f')[0].payload['translations']) == 4
    assert selected('4284b392')[0].signing == 'Einzelunterschrift'
    removed, new = selected('718f1a3b')
    assert removed.event_type == 'officer_removed' and new.signing == 'Kollektivunterschrift zu zweien'
    assert new.payload['authorized_partners'] == ['Pasquier Laurent', 'Pasquier Jacques']
    assert selected('73d2c5ad')[0].payload['date'] == '23.01.2020'
    certificates = [e for e in parse_publication_xml(path('73d2c5ad')).events if e.rule_id == 'de.text.profit_participation_certificates_changed.v1']
    assert len(certificates) == 1 and certificates[0].payload['count'] == "12'175" and certificates[0].payload['previous_count'] == '133'
    auditor = selected('94053a9f')[0]
    assert auditor.role == 'Revisionsorgan' and auditor.payload['uid'] == 'CHE-230.955.198'
    transfer = selected('b2bf344e')[0].payload
    assert transfer['assets'] == "171'521'644.09" and len(transfer['claims']) == 4
    assert [c['class'] for c in transfer['claims']] == ['1', '2', '1', '2']
    assert transfer['effective_date'] == '01.01.2020'
    corrected = selected('bc63ac68')[0]
    assert corrected.payload['previous_name'] != corrected.payload['name'] and corrected.signing == 'Kollektivunterschrift zu zweien'
    assert selected('c148bbb3')[0].signing == 'Einzelunterschrift'
    restrictions = [e for e in parse_publication_xml(path('c148bbb3')).events if e.rule_id == 'fr.text.share_transfer_restriction_removed.v1']
    assert len(restrictions) == 1 and restrictions[0].payload['transfer_restricted'] is False
    converted = selected('ff2fb0c8')[0].payload
    assert converted['converted'] == "300'000" and converted['transfer_restricted'] is True
