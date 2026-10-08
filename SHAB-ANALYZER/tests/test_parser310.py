import hashlib
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser310 import extract_parser310_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('0035201a', 'it.text.wholly_owned_merger_uid_question_mark.v1', 1),
    ('03b44a71', 'de.text.manager_appointed_signing_retained.v1', 1),
    ('275f91dd', 'de.text.french_all_shares_transferred.v1', 1),
    ('3767ff94', 'de.text.previous_officer_entry_corrected.v1', 1),
    ('4548afe3', 'fr.text.bankruptcy_appeal_rejected.v1', 1),
    ('5f73e0ae', 'fr.text.two_intended_asset_acquisitions_revoked.v1', 1),
    ('65ca62e0', 'fr.text.three_signatories_restriction_removed.v1', 3),
    ('6c93d21b', 'de.text.shab_reference_corrected.v1', 1),
    ('70c8382e', 'de.text.audit_waiver_removed_auditor_elected.v1', 1),
    ('99b3c4c9', 'fr.text.existing_foreign_associate_shares_transfer.v1', 1),
    ('c1cd0a06', 'de.text.statutes_date_placeholder_corrected.v1', 1),
    ('d18d8cd0', 'de.text.shab_reference_corrected.v1', 1),
]


def path(prefix):
    paths = list(FIXTURES.glob(prefix + '*.xml'))
    assert len(paths) == 1
    return paths[0]


def invocation(prefix):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser310_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser310_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 315
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
    assert extract_parser310_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser310_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix', ['0035201a', '3767ff94', '4548afe3', '6c93d21b', '70c8382e', 'c1cd0a06', 'd18d8cd0'])
def test_invalid_dates_preserved(prefix):
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', args[0], count=1)
    assert changed != args[0]
    assert extract_parser310_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,old,new', [
    ('0035201a', 'senza aumento', 'con aumento'),
    ('03b44a71', 'Kollektivunterschrift zu zweien', 'Einzelunterschrift'),
    ('275f91dd', "n'est plus associé", 'reste associé'),
    ('3767ff94', 'Mitglied der Geschäftsleitung', 'Präsident'),
    ('4548afe3', 'a rejeté', 'a admis'),
    ('4548afe3', '12:00', '25:00'),
    ('5f73e0ae', 'abrogées', 'adoptées'),
    ('65ca62e0', 'sans restriction', 'avec restriction'),
    ('70c8382e', 'gestrichen', 'bestätigt'),
    ('99b3c4c9', 'titulaire de 20', 'titulaire de 21'),
    ('99b3c4c9', 'titulaire de 180', 'titulaire de 79'),
    ('c1cd0a06', 'irrtümlich', 'korrekt'),
])
def test_unsupported_or_inconsistent_terms_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser310_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads_and_roles():
    def selected(prefix):
        rule = next(rule for stem, rule, _ in CASES if stem == prefix)
        return [e for e in parse_publication_xml(path(prefix)).events if e.rule_id == rule]
    merger = selected('0035201a')[0]
    assert merger.event_type == 'company_merged'
    assert merger.payload['wholly_owned'] and not merger.payload['capital_increase']
    assert merger.payload['absorbed_uid'].startswith('CHE-')
    assert '?' not in merger.payload['absorbed_uid']
    assert selected('03b44a71')[0].role == 'Geschäftsführer'
    assert selected('3767ff94')[0].payload['place'] != selected('3767ff94')[0].payload['previous_place']
    people = selected('65ca62e0')
    assert len({e.person_key for e in people}) == 3
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in people)
    assert selected('99b3c4c9')[0].payload['recipient_register_id']
    for prefix in ('6c93d21b', 'd18d8cd0'):
        payload = selected(prefix)[0].payload
        assert payload['notice_date'] != payload['previous_notice_date']
