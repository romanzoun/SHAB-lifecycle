import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser287 import extract_parser287_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('0ffbb8ed', 'fr.persons.residence_canton_corrected.v1', 1), ('1aabcf0b', 'de.text.auditor_identity_corrected.v1', 1), ('220146c0', 'fr.text.erroneous_entry_cancelled.v1', 1), ('24c6ce60', 'de.text.foundation_assets_transferred_for_claims.v1', 1), ('55b2438c', 'de.text.additional_addresses_deleted_demerger.v1', 1), ('60538691', 'fr.text.bankruptcy_closed_reinstatement_facts_retained.v1', 1), ('674fce4f', 'fr.persons.share_transfer_manager_president.v1', 3), ('7512a3bd', 'de.text.additional_addresses_demerger_acquisition.v1', 1), ('b9b1d0ae', 'fr.text.auditor_identity_corrected_notice_typo.v1', 1), ('ca4d9134', 'fr.persons.two_foundation_members_collective_signing.v1', 2), ('d29421d7', 'fr.text.definitive_moratorium_commissioner.v1', 2), ('e3301d77', 'fr.persons.origin_changed_variant.v1', 1)]


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
        return extract_parser287_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser287_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 314
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
    assert extract_parser287_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser287_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('0ffbb8ed', '10.03.2020', '31.02.2020'),
    ('1aabcf0b', '24.02.2020', '31.02.2020'),
    ('220146c0', '27.02.2020', '31.02.2020'),
    ('24c6ce60', '28.02.2020', '31.02.2020'),
    ('24c6ce60', "38'670'000.00", '0'),
    ('24c6ce60', "226'777", '0'),
    ('24c6ce60', '170.52', '0'),
    ('55b2438c', '09.03.2020', '31.02.2020'),
    ('60538691', '05.03.2020', '31.02.2020'),
    ('674fce4f', 'CHF 100', 'CHF 0'),
    ('674fce4f', 'cession de 100', 'cession de 0'),
    ('7512a3bd', "1'394'541", '0'),
    ('7512a3bd', '370 Aktien', '0 Aktien'),
    ('b9b1d0ae', '14.12.2018', '31.02.2018'),
    ('d29421d7', '2 mars', '32 mars'),
    ('d29421d7', '2 septembre', '31 septembre'),
    ('d29421d7', 'septembre 2020', 'septembre 2019'),
])
def test_invalid_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new, 1)
    assert changed != args[0]
    assert extract_parser287_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,suffix', [('674fce4f', ' avec signature individuelle'), ('ca4d9134', ' avec signature collective à deux')])
def test_signing_requires_same_clause(prefix, suffix):
    args, kwargs = invocation(prefix)
    changed = args[0].removesuffix(suffix)
    events, residue = extract_parser287_leftovers(changed, *args[1:], **kwargs)
    assert residue == '' and any(e.signing for e in events)
    for source in ('', changed + '. Autre personne' + suffix + '.'):
        assert extract_parser287_leftovers(changed, *args[1:], source_text=source) == ([], changed)


def test_payloads():
    residence = selected('0ffbb8ed')[0]
    assert residence.payload['place'] == 'Cugy (VD)' and residence.payload['previous_place'] == 'Cugy (FR)'
    assert residence.role is None and residence.signing is None
    auditor = selected('1aabcf0b')[0].payload
    assert auditor['auditor_uid'] == 'CHE-105.821.542' and auditor['previous_auditor_uid'] == 'CHE-105.821.588'
    assert auditor['correction']
    assert selected('220146c0')[0].payload['action'] == 'entry_cancelled'
    assets = selected('24c6ce60')[0].payload
    assert assets['assets'] == "38'670'000.00" and assets['claims'] == "226'777"
    assert assets['claim_value'] == '170.52' and assets['valuation_date'] == '28.02.2020'
    deletion = selected('55b2438c')[0].payload
    assert deletion['recipient_uid'] == 'CHE-102.646.886' and deletion['plan_date'] == '09.03.2020'
    assert "Route d'Onnens 46" in deletion['deleted_addresses']
    reinstatement = selected('60538691')[0].payload
    assert reinstatement['previous_facts_retained'] and reinstatement['decision_date'] == '05.03.2020'
    transfer = selected('674fce4f')
    assert [e.payload['shares'] for e in transfer] == [100, 100, 100]
    assert transfer[1].role == 'associé-gérant président' and transfer[1].signing is None
    assert transfer[2].role == 'associée-gérante' and transfer[2].signing == 'Einzelunterschrift'
    acquisition = selected('7512a3bd')[0].payload
    assert acquisition['assets'] == "1'394'541" and acquisition['liabilities'] == "1'136'805"
    assert acquisition['shares'] == '370' and acquisition['nominal'] == '500'
    assert acquisition['transferor_uid'] == 'CHE-105.968.665' and ';' in acquisition['new_addresses']
    corrected = selected('b9b1d0ae')[0].payload
    assert corrected['auditor_uid'] == 'CHE-102.136.421' and corrected['previous_auditor_uid'] == 'CHE-359.590.155'
    board = selected('ca4d9134')
    assert [e.payload['place'] for e in board] == ['Confignon', 'Genève']
    assert all(e.role == 'membre du conseil de fondation' and e.signing == 'Kollektivunterschrift zu zweien' for e in board)
    moratorium = selected('d29421d7')
    assert moratorium[0].payload['decision_date'] == '02.03.2020'
    assert moratorium[0].payload['until_date'] == '02.09.2020' and moratorium[0].payload['provisional'] is False
    assert moratorium[1].role == 'commissaire au sursis' and moratorium[1].signing is None
    origin = selected('e3301d77')[0]
    assert origin.payload['origin'] == 'Pregny-Chambésy' and origin.payload['place'] is None
