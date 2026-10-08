import hashlib
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser309 import extract_parser309_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('12212a15', 'fr.text.given_names_corrected.v1', 1), ('357c82f7', 'fr.text.two_administrators_individual_signing.v1', 2), ('5f033a26', 'fr.text.german_two_signatories.v1', 2), ('6f674d2c', 'fr.text.voting_privileged_shares_transfer.v1', 3), ('933219ca', 'de.text.interim_custodian_registered.v1', 1), ('b1109606', 'de.text.association_reinstated.v1', 1), ('c3909b52', 'de.text.assets_transferred_without_consideration.v1', 1), ('c8128db4', 'fr.text.associate_manager_surname_corrected.v1', 1), ('cef8630c', 'de.text.sole_proprietorship_reinstated.v1', 1), ('e0189fbd', 'it.text.auditor_erroneous_entry_corrected.v1', 1), ('e6ecd344', 'fr.text.manager_president_shares_transfer.v1', 3), ('fc31f74c', 'fr.text.shares_transferred_three_unsigned_associates.v1', 4)]


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
        return extract_parser309_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser309_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 313
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
    assert extract_parser309_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser309_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])





@pytest.mark.parametrize('prefix', ['12212a15', '933219ca', 'b1109606', 'c3909b52', 'c8128db4'])
def test_invalid_dates_preserved(prefix):
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', args[0], count=1)
    assert changed != args[0]
    assert extract_parser309_leftovers(changed, *args[1:], **kwargs) == ([], changed)

@pytest.mark.parametrize('prefix', ['357c82f7', '6f674d2c', 'e6ecd344'])
def test_signing_source_required(prefix):
    args, kwargs = invocation(prefix)
    for source in ['', kwargs['source_text'].replace('signature individuelle', 'signature collective à deux')]:
        assert extract_parser309_leftovers(*args, source_text=source) == ([], args[0])

@pytest.mark.parametrize('prefix,old,new', [
    ('933219ca', 'einzelzeichnungsberechtigte', 'kollektivzeichnungsberechtigte'),
    ('b1109606', 'wieder', 'nicht wieder'),
    ('c3909b52', 'Gegenleistung: keine', 'Gegenleistung: unbekannt'),
    ('cef8630c', 'erneut', 'nicht erneut'),
    ('e0189fbd', 'erroneamente', 'correttamente'),
    ('fc31f74c', 'sans signature sociale', 'avec signature individuelle'),
    ('6f674d2c', 'privilégiées quant au droit de vote', 'ordinaires'),
    ('e6ecd344', 'continue à signer individuellement', 'sans signature'),
])
def test_unsupported_terms_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser309_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads_and_roles():
    assert selected('12212a15')[0].payload['given_names'] != selected('12212a15')[0].payload['previous_given_names']
    assert all(e.signing == 'Einzelunterschrift' for e in selected('357c82f7'))
    assert len({e.person_key for e in selected('5f033a26')}) == 2
    assert selected('6f674d2c')[0].payload['transferred_count1'] == '70'
    assert selected('933219ca')[0].role == 'Sachwalterin'
    assert selected('c3909b52')[0].payload['assets'] == "8'335'020.80"
    assert selected('c8128db4')[0].payload['surname'] != selected('c8128db4')[0].payload['previous_surname']
    assert selected('e6ecd344')[1].role == 'président des gérants'
    assert all(e.signing == 'ohne Zeichnungsberechtigung' for e in selected('fc31f74c')[1:])
    result = parse_publication_xml(path('cef8630c'))
    assert not any(e.rule_id == 'de.text.sole_proprietor_closed.v1' for e in result.events)
    result = parse_publication_xml(path('e0189fbd'))
    assert not any(e.rule_id == 'it.text.audit_waiver.v1' for e in result.events)

@pytest.mark.parametrize('prefix,old,new', [
    ('6f674d2c', 'titulaire de 70', 'titulaire de 71'),
    ('e6ecd344', 'titulaire de 51', 'titulaire de 52'),
    ('fc31f74c', 'cession de 42', 'cession de 43'),
])
def test_inconsistent_share_totals_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    kwargs['source_text'] = kwargs['source_text'].replace(old, new)
    assert changed != args[0]
    assert extract_parser309_leftovers(changed, *args[1:], **kwargs) == ([], changed)
