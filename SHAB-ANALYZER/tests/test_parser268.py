import hashlib
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser268 import extract_parser268_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('07b1ff34', 'de.persons.board_name_origin_corrected.v1', 1),
    ('10e86114', 'fr.persons.deputy_general_management_corrected.v1', 1),
    ('204c6838', 'fr.text.registered_share_conversion_completed.v1', 1),
    ('258266b6', 'fr.persons.proprietor_name_corrected.v1', 1),
    ('31da2fec', 'fr.text.statutes_copy_filed.v1', 1),
    ('5a7a1878', 'de.text.definitive_moratorium_extended.v1', 1),
    ('655a080c', 'fr.text.contribution_receivable_corrected.v1', 1),
    ('97bdd080', 'fr.persons.associate_elected_president_manager.v1', 1),
    ('9c44d946', 'de.text.erroneous_deletion_revoked.v1', 1),
    ('b28a4f0f', 'fr.persons.board_president_vice_president_collective.v1', 2),
    ('d98268ba', 'fr.persons.two_managers_partial_share_transfer.v1', 3),
    ('e5c6d320', 'fr.persons.court_annulment_reinstatements.v1', 5),
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
        return extract_parser268_leftovers(*args, **kwargs)

    with patch.object(parser, 'extract_parser268_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION >= 268
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
    assert extract_parser268_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['07b1ff34', '10e86114', '204c6838', '258266b6', '31da2fec', '5a7a1878', '655a080c', 'e5c6d320'])
def test_invalid_date_preserved(prefix):
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', args[0])
    kwargs['source_text'] = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', kwargs['source_text'])
    assert extract_parser268_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_source_required_and_bounded():
    args, kwargs = invocation('b28a4f0f')
    assert extract_parser268_leftovers(*args) == ([], args[0])
    for source in [kwargs['source_text'] + ' UNKNOWN_SUFFIX', kwargs['source_text'].replace('avec signature collective à deux', 'avec signature individuelle')]:
        assert extract_parser268_leftovers(*args, source_text=source) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('204c6838', "1'300'000", "1'300'001"),
    ('204c6838', "13'000", '0'),
    ('655a080c', "334'000", "334'001"),
    ('655a080c', '10 septembre', '31 septembre'),
    ('655a080c', '451 à 455', '456 à 455'),
    ('d98268ba', '90 et 88', '91 et 88'),
    ('d98268ba', 'avec 20 parts', 'avec 21 parts'),
    ('d98268ba', 'chacun 10', 'chacun 0'),
    ('5a7a1878', '15.06.2020', '09.02.2020'),
    ('97bdd080', 'signature individuelle', 'signature collective à deux'),
    ('e5c6d320', 'sont nulles', 'sont valables'),
    ('9c44d946', 'irrtümlich gelöscht', 'rechtmässig gelöscht'),
])
def test_inconsistent_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    kwargs['source_text'] = kwargs['source_text'].replace(old, new)
    assert extract_parser268_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    corrected = selected('07b1ff34')[0]
    assert corrected.payload['origin'] == 'Genève' and corrected.payload['previous_origin'] == 'Lausanne'
    assert corrected.payload['name'] != corrected.payload['previous_name']
    deputy = selected('10e86114')[0]
    assert deputy.role == 'membre de la direction générale adjoint' and deputy.signing is None
    cap = selected('204c6838')[0]
    assert cap.event_type == 'capital_changed'
    assert cap.payload['share_kind'] == 'registered' and cap.payload['previous_share_kind'] == 'bearer'
    assert cap.payload['fully_paid'] and cap.payload['capital'] == "1'300'000"
    proprietor = selected('258266b6')[0]
    assert proprietor.role == 'titulaire' and proprietor.payload['name'] != proprietor.payload['previous_name']
    assert selected('31da2fec')[0].payload['action'] == 'new_copy_filed'
    moratorium = selected('5a7a1878')[0]
    assert moratorium.event_type == 'status_changed' and moratorium.payload['definitive']
    assert moratorium.payload['until_date'] == '15.06.2020'
    contribution = selected('655a080c')[0].payload
    assert contribution['agreement_date'] == '2019-09-10'
    assert contribution['balance'] == "334'000" and contribution['previous_balance'] == "343'000"
    manager = selected('97bdd080')[0]
    assert manager.role == 'associé gérant président' and manager.signing == 'Einzelunterschrift'
    assert selected('9c44d946')[0].payload['previous_deletion_revoked']
    president, vice = selected('b28a4f0f')
    assert president.role == 'président' and president.payload['previous_role'] == 'secrétaire'
    assert vice.role == 'vice-président' and vice.payload['country'] == 'GB'
    assert president.signing == vice.signing == 'Kollektivunterschrift zu zweien'
    first, second, recipient = selected('d98268ba')
    assert [first.payload['shares_count'], second.payload['shares_count'], recipient.payload['shares_count']] == [90, 88, 20]
    assert recipient.payload['without_signature'] and recipient.signing is None
    annulment, *people = selected('e5c6d320')
    assert annulment.event_type == 'organization_changed' and annulment.payload['action'] == 'registration_changes_annulled'
    assert [e.event_type for e in people] == ['officer_changed', 'officer_changed', 'officer_removed', 'officer_removed']
    assert [e.signing for e in people] == ['Einzelunterschrift', 'Kollektivunterschrift zu zweien'] * 2
