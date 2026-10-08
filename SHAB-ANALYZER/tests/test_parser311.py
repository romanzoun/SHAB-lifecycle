import hashlib
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser311 import extract_parser311_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('0a032e52', 'fr.text.president_vice_president_individual_signing.v1', 2),
    ('0b58d851', 'fr.text.associate_share_nominal_corrected.v1', 1),
    ('24848acc', 'fr.text.associates_signing_granted_removed.v1', 2),
    ('26efe42e', 'fr.text.authorized_capital_clause_replaced.v1', 1),
    ('8e01716e', 'de.text.address_dissolution_transfer_clause_removed.v1', 2),
    ('9242e7d9', 'fr.text.administrator_secretary_origin_changed.v1', 1),
    ('a60aa3c1', 'de.text.asset_transfer_loan_consideration.v1', 1),
    ('b104c4d8', 'de.text.amended_authorized_capital_expired.v1', 1),
    ('cf98828b', 'de.text.two_erroneous_domicile_changes_reversed.v1', 1),
    ('dd84ec94', 'it.text.owner_bankruptcy_appeal_suspensive_effect.v1', 1),
    ('e6200fa5', 'fr.text.two_managers_shares_split_three_recipients.v1', 4),
    ('f15aa450', 'fr.text.foundation_dissolved_four_liquidators.v1', 5),
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
        return extract_parser311_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser311_leftovers', capture):
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
    assert extract_parser311_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser311_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix', ['0b58d851', '26efe42e', '8e01716e', 'a60aa3c1', 'b104c4d8', 'cf98828b', 'dd84ec94', 'f15aa450'])
def test_invalid_dates_preserved(prefix):
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', args[0], count=1)
    assert changed != args[0]
    assert extract_parser311_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,old,new', [
    ('0a032e52', 'signature individuelle', 'signature collective à deux'),
    ('24848acc', "n'exerce plus", 'exerce'),
    ('26efe42e', 'introduit', 'supprimé'),
    ('8e01716e', 'ist gelöscht', 'bleibt bestehen'),
    ('9242e7d9', 'secrétaire', 'présidente'),
    ('a60aa3c1', 'als Darlehen', 'in bar'),
    ('b104c4d8', 'Ablaufs', 'Verlängerung'),
    ('cf98828b', 'irrtümlich', 'korrekt'),
    ('dd84ec94', '09:00', '25:00'),
    ('dd84ec94', 'ha accordato', 'ha negato'),
    ('e6200fa5', 'de 6 parts', 'de 7 parts'),
    ('e6200fa5', 'titulaires de 3 parts', 'titulaires de 4 parts'),
    ('e6200fa5', 'par 3 parts à Perron', 'par 2 parts à Perron'),
    ('f15aa450', 'collectivement à deux', 'individuellement'),
])
def test_unsupported_terms_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser311_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads_and_roles():
    def selected(prefix):
        rule = next(rule for stem, rule, _ in CASES if stem == prefix)
        return [e for e in parse_publication_xml(path(prefix)).events if e.rule_id == rule]
    assert [e.role for e in selected('0a032e52')] == ['Präsident', 'Vizepräsidentin']
    assert [e.signing for e in selected('24848acc')] == ['Kollektivunterschrift zu zweien', 'ohne Zeichnungsberechtigung']
    assert selected('8e01716e')[0].payload['dissolved']
    assert selected('8e01716e')[1].signing == 'Einzelunterschrift'
    assert selected('9242e7d9')[0].role == 'Sekretärin'
    assert selected('a60aa3c1')[0].payload['recipient_uid'].startswith('CHE-')
    assert selected('0b58d851')[0].payload['nominal'] != selected('0b58d851')[0].payload['previous_nominal']
    for prefix, count in [('e6200fa5', 3), ('f15aa450', 4)]:
        people = [e for e in selected(prefix) if e.person_key]
        assert len({e.person_key for e in people}) == count
        assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in people)
