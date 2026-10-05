from pathlib import Path
import hashlib
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser263 import extract_parser263_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('0a0450d5', 'fr.persons.partial_share_transfer_president_communications.v1', 4),
    ('1edf751e', 'fr.text.foundation_dissolved_council_liquidators.v1', 4),
    ('2248d0c8', 'de.persons.deleted_board_member_unsigned.v1', 1),
    ('2e00899f', 'de.text.branch_places_replaced_uid.v1', 2),
    ('3602764b', 'fr.text.previous_seat_supplemented.v1', 1),
    ('40af845d', 'fr.persons.associate_social_signing_individual.v1', 1),
    ('54df9720', 'fr.persons.four_origins_one_residence_corrected.v1', 4),
    ('7d33efbf', 'it.text.registration_maintained_deletion_clause_removed.v1', 1),
    ('8850549a', 'fr.text.asset_transfer_shares_and_claim.v1', 1),
    ('a03f0622', 'fr.text.unpublished_purpose_change_supplemented.v1', 1),
    ('c6b501ba', 'fr.text.bankruptcy_judgment_void_name_restored.v1', 1),
    ('cd672254', 'fr.persons.multiclass_shares_three_recipients.v1', 4),
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
    captured = []
    def capture(*args, **kwargs):
        result = extract_parser263_leftovers(*args, **kwargs)
        if result[0]:
            captured.append((args, kwargs))
        return result
    with patch.object(parser, 'extract_parser263_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(captured) == 1
    return captured[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 263
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    events = selected(prefix)
    assert len(events) == count
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in events)
    assert not any(e.rule_id == 'fr.persons.group_signing.v1' for e in result.events)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser263_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['0a0450d5', '2e00899f', '7d33efbf', '8850549a', 'a03f0622'])
def test_source_required(prefix):
    args, kwargs = invocation(prefix)
    assert extract_parser263_leftovers(*args) == ([], args[0])
    kwargs['source_text'] += ' UNKNOWN'
    assert extract_parser263_leftovers(*args, **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('0a0450d5', 'ses 200', 'ses 201'),
    ('0a0450d5', 'cède 20', 'cède 0'),
    ('cd672254', 'ses 20', 'ses 21'),
    ('cd672254', 'chacun avec 10', 'chacun avec 11'),
    ('cd672254', '691.80, sans', '691.81, sans'),
])
def test_inconsistent_shares_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    assert old in args[0]
    changed = args[0].replace(old, new)
    kwargs['source_text'] = kwargs['source_text'].replace(old, new)
    assert extract_parser263_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['1edf751e', '3602764b', '54df9720', '7d33efbf', '8850549a', 'a03f0622', 'c6b501ba'])
def test_invalid_dates_preserved(prefix):
    import re
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', args[0])
    kwargs['source_text'] = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', kwargs['source_text'])
    assert extract_parser263_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    seller, buyer, communications, clause = selected('0a0450d5')
    assert seller.payload['shares_count'] == 180 and seller.payload['shares_transferred'] == 20
    assert seller.role == 'associé-gérant président' and seller.signing is None
    assert buyer.payload['shares_count'] == 20 and buyer.signing == 'Einzelunterschrift'
    assert communications.payload['method'] == 'par écrit ou par courriel'
    assert clause.payload['article'] == '628 al. 4 CO'
    foundation = selected('1edf751e')
    assert foundation[0].payload['action'] == 'dissolved'
    assert all(e.role == 'liquidateur' and e.signing is None for e in foundation[1:])
    assert selected('2248d0c8')[0].event_type == 'officer_removed'
    branches = selected('2e00899f')
    assert [(e.payload['previous_place'], e.payload['place']) for e in branches] == [('Wäldi', 'Frauenfeld'), ('Winterthur', 'Winterthur')]
    assert selected('3602764b')[0].payload['previous_place'] == 'Lucerne'
    assert selected('40af845d')[0].signing == 'Einzelunterschrift'
    corrections = selected('54df9720')
    assert all(e.payload['origin'] == 'Jorat-Mézières (Carrouge) VD' for e in corrections)
    assert [e.payload['place'] for e in corrections] == [None, None, None, 'Lucens']
    assert selected('7d33efbf')[0].payload['action'] == 'registration_maintained'
    transfer = selected('8850549a')[0].payload
    assert transfer['assets'] == "7'222'623.79" and transfer['liabilities'] == "5'386'222.78"
    assert transfer['shares_count'] == 100 and transfer['claim'] == "1'736'401.01"
    assert selected('a03f0622')[0].payload['detail'] == 'not_subject_to_publication'
    assert selected('c6b501ba')[0].payload['action'] == 'bankruptcy_void'
    seller, *buyers = selected('cd672254')
    assert seller.payload['shares_nominal'] == "1'007.40"
    assert [e.payload['shares_nominal'] for e in buyers] == ['691.80', '150.40', '150.40']
    assert all(e.signing == 'ohne Unterschrift' and e.payload['shares_count'] == 10 for e in buyers)


def test_superseded_fragment_events_removed():
    for prefix, obsolete in [('0a0450d5', 'fr.text.communications.v1'), ('2e00899f', 'de.text.branch_added.v1'), ('7d33efbf', 'it.text.liquidation_ended.v1')]:
        result = parse_publication_xml(path(prefix))
        assert not any(e.rule_id == obsolete for e in result.events)


@pytest.mark.parametrize('prefix,old,new', [
    ('0a0450d5', 'signature individuelle', 'UNKNOWN_SIGNING'),
    ('2e00899f', 'Frauenfeld (CHE-330.536.985)', 'Frauenfeld (CHE-330.536.986)'),
    ('8850549a', 'liées selon statuts', 'UNKNOWN_RESTRICTION'),
])
def test_source_facts_must_agree(prefix, old, new):
    args, kwargs = invocation(prefix)
    assert old in kwargs['source_text']
    kwargs['source_text'] = kwargs['source_text'].replace(old, new)
    assert extract_parser263_leftovers(*args, **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix', ['0a0450d5', 'cd672254'])
def test_same_seller_required(prefix):
    args, kwargs = invocation(prefix)
    old = selected(prefix)[0].payload['name'] + ' reste titulaire'
    assert old in args[0]
    changed = args[0].replace(old, 'UNKNOWN_SELLER reste titulaire')
    kwargs['source_text'] = kwargs['source_text'].replace(old, 'UNKNOWN_SELLER reste titulaire')
    assert extract_parser263_leftovers(changed, *args[1:], **kwargs) == ([], changed)
