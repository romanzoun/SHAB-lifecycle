import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser293 import extract_parser293_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('2ae020a0', 'fr.text.three_name_translations.v1', 1),
    ('41ebf0d0', 'fr.text.erroneous_deletion_owner_reinstatement.v1', 1),
    ('5e7231e0', 'de.text.authorized_capital_grant_resolution.v1', 1),
    ('801c37b4', 'de.text.two_spin_offs_capital_unchanged.v1', 2),
    ('8774dad8', 'fr.text.branch_deleted_notice_reference.v1', 1),
    ('9f02af44', 'de.text.association_assets_public_foundation.v1', 1),
    ('aede429a', 'fr.persons.procuration_article_entry_completed.v1', 1),
    ('bfe80258', 'fr.persons.share_transfer_foreign_associate.v1', 3),
    ('d7231d5d', 'de.text.preferred_shares_dividend_rights.v1', 1),
    ('d77e3a0c', 'fr.text.federal_department_audit_waiver_removed.v1', 1),
    ('d9181a4e', 'fr.text.dissolution_contract_term_expired.v1', 1),
    ('e20924c2', 'de.text.capital_clauses_removed_options_expired.v1', 1),
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
        return extract_parser293_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser293_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 308
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
    assert extract_parser293_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser293_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('41ebf0d0', '11.02.2020', '31.02.2020'),
    ('5e7231e0', '28.09.2018', '31.09.2018'),
    ('801c37b4', '08.04.2020', '31.04.2020'),
    ('801c37b4', "116'032'305.00", '0.00'),
    ('8774dad8', '30.01.2020', '32.01.2020'),
    ('9f02af44', '22.08./30.10.2019', '31.02./30.10.2019'),
    ('9f02af44', '22.08./30.10.2019', '22.11./30.10.2019'),
    ('9f02af44', "240'300.70", "2'240'300.70"),
    ('aede429a', '31.03.2020', '31.02.2020'),
    ('aede429a', '459 al. 2 CO', '459 al. 3 CO'),
    ('bfe80258', '196 parts', '0 parts'),
    ('bfe80258', 'CHF 100', 'CHF 0'),
    ('bfe80258', 'pour 4 parts', 'pour 5 parts'),
    ('d77e3a0c', '17.02.2020', '31.02.2020'),
    ('e20924c2', '20.08.2018', '31.02.2018'),
    ('e20924c2', '05.05.2010', '05.05.2020'),
])
def test_invalid_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser293_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_compound_spin_off_atomic():
    args, kwargs = invocation('801c37b4')
    changed = args[0].replace('Geschäftseinheit Pigmente', 'Geschäftseinheit Pigmente" UNKNOWN')
    assert extract_parser293_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    assert len(selected('2ae020a0')[0].payload['translations']) == 3
    assert selected('41ebf0d0')[0].payload['at_owner_request'] is True
    assert selected('5e7231e0')[0].payload['decision_date'] == '28.09.2018'
    splits = selected('801c37b4')
    assert splits[0].payload['unit'] != splits[1].payload['unit']
    assert splits[0].payload['recipient_uid'] != splits[1].payload['recipient_uid']
    assert all(e.payload['capital_reduced'] is False for e in splits)
    assert splits[0].payload['assets'] == "116'032'305.00"
    assert splits[1].payload['liabilities'] == "142'133'047.00"
    assert selected('8774dad8')[0].payload['action'] == 'branch_deleted'
    assets = selected('9f02af44')[0].payload
    assert assets['first_date'] == '22.08.2019' and assets['contract_date'] == '30.10.2019'
    assert assets['consideration'] == 'none' and assets['currency'] == 'CHF'
    procuration = selected('aede429a')[0]
    assert procuration.signing == 'Kollektivprokura zu zweien'
    assert procuration.payload['article'] == '459 al. 2 CO'
    transfer = selected('bfe80258')
    assert transfer[0].payload['remaining'] == '196' and transfer[0].payload['transferred'] == '4'
    assert transfer[1].role == 'associé-gérant' and transfer[1].signing is None
    assert transfer[2].signing == 'ohne Zeichnungsberechtigung' and transfer[2].payload['shares'] == '4'
    assert transfer[2].payload['place'].endswith(', POL')
    assert selected('d7231d5d')[0].payload['rights'] == 'Dividendenausschüttung'
    assert selected('d77e3a0c')[0].payload['action'] == 'audit_waiver_removed'
    assert selected('d9181a4e')[0].payload['reason'] == 'contract_term_expired'
    capital = selected('e20924c2')[0].payload
    assert capital['conditional_reason'] == 'option_rights_expired'
    assert capital['board_date'] == '20.08.2018' and capital['grant_date'] == '05.05.2010'
