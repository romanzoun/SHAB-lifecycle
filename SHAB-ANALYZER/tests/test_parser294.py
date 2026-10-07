import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser294 import extract_parser294_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('0fcd02ea', 'de.text.spin_off_new_company_typo.v1', 1),
    ('19e95c6a', 'fr.persons.two_existing_liquidators.v1', 2),
    ('1ead5206', 'fr.text.principal_name_language_added.v1', 1),
    ('5133bb17', 'de.text.dividend_composition_confirmed.v1', 1),
    ('70fff009', 'fr.persons.collective_signing_conferred.v1', 1),
    ('85649655', 'de.text.previous_notice_citation_corrected.v1', 1),
    ('9d696b3b', 'fr.persons.associate_individual_signing.v1', 1),
    ('b54e3444', 'de.text.authorized_conditional_capital_amended.v1', 2),
    ('c69e8e99', 'fr.persons.deputy_director_procuration_removed.v1', 1),
    ('d0c72a3e', 'fr.persons.two_directors_signing_incomplete_place.v1', 2),
    ('d9d22be1', 'de.persons.board_departure_signing_changed_fr_xml.v1', 2),
    ('da12c3bf', 'it.text.planned_asset_acquisition_expired.v1', 1),
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
        return extract_parser294_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser294_leftovers', capture):
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
    assert extract_parser294_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser294_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('5133bb17', '30.03.2020', '31.02.2020'),
    ('5133bb17', '13.03.2020', '13.03.2021'),
    ('85649655', '25.03.2020', '31.02.2020'),
    ('b54e3444', '24.04.2020', '31.04.2020'),
    ('b54e3444', '20.04.2018', '20.04.2028'),
    ('b54e3444', 'bedingten', 'unbekannten'),
    ('da12c3bf', '29.01.1997', '32.01.1997'),
])
def test_invalid_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser294_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_removed_signing_requires_source_evidence():
    args, kwargs = invocation('c69e8e99')
    for source in ['', kwargs['source_text'].replace('collective à deux', 'individuelle')]:
        assert extract_parser294_leftovers(*args, source_text=source) == ([], args[0])


def test_payloads():
    assert selected('0fcd02ea')[0].payload['recipient_new'] is True
    assert len(selected('1ead5206')[0].payload['translations']) == 2
    assert all(e.role == 'liquidateur' and e.signing == 'Einzelunterschrift' for e in selected('19e95c6a'))
    assert selected('5133bb17')[0].payload['kind'] == 'dividend_composition'
    assert selected('85649655')[0].payload['wrong_notice'] == '30'
    assert selected('85649655')[0].payload['notice'] == '60'
    assert selected('70fff009')[0].signing == 'Kollektivunterschrift zu zweien'
    assert selected('9d696b3b')[0].signing == 'Einzelunterschrift'
    assert [e.payload['kind'] for e in selected('b54e3444')] == ['genehmigten', 'bedingten']
    deputy = selected('c69e8e99')[0]
    assert deputy.role == 'sous-directeur' and deputy.payload['procuration_removed'] is True
    directors = selected('d0c72a3e')
    assert directors[0].payload['place'] is None
    assert directors[0].payload['origin_place_text'] == 'de et Anières'
    assert all(e.role == 'directeur' and e.signing == 'Kollektivunterschrift zu zweien' for e in directors)
    board = selected('d9d22be1')
    assert board[0].event_type == 'officer_removed'
    assert board[0].payload['action'] == 'removed' and board[0].signing is None
    assert board[1].signing == 'Einzelunterschrift'
    assert board[1].payload['previous_signing'] == 'ohne Zeichnungsberechtigung'
    assert selected('da12c3bf')[0].payload['reason'] == 'over_ten_years'
