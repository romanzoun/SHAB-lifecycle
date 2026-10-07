import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser283 import extract_parser283_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('006a6114', 'fr.text.headquarters_uid_replaced.v1', 1), ('3b7614d1', 'fr.text.branch_registration_notice.v1', 1), ('493e8810', 'fr.persons.two_board_members_liquidators.v1', 2), ('4a952e97', 'fr.text.share_count_corrected.v1', 1), ('9c7685c9', 'fr.persons.corporate_associate_name_seat_changed.v1', 1), ('a586ada0', 'fr.persons.foundation_vice_president_local_origin.v1', 1), ('ac9bc7be', 'fr.persons.thirteen_signatures_procuration_revoked.v1', 13), ('bfb9ba5c', 'fr.persons.transfer_manager_president_missing_buyer_nominal.v1', 2), ('db129574', 'de.text.bankruptcy_summary_proceedings_reopened.v1', 1), ('db9cf682', 'fr.persons.board_president_secretary_signing.v1', 2), ('e16852ab', 'it.text.branch_closed_tax_consents_pending.v1', 1), ('f0d1129a', 'fr.persons.transfer_new_associate_manager_individual.v1', 2)]


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
        return extract_parser283_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser283_leftovers', capture):
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
    assert extract_parser283_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser283_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('3b7614d1', '04.03.2020', '31.02.2020'),
    ('4a952e97', '16.03.2020', '31.04.2020'),
    ('4a952e97', "14'077 actions", "14'078 actions"),
    ('4a952e97', 'CHF 10', 'CHF 0'),
    ('bfb9ba5c', 'CHF 100', 'CHF 0'),
    ('db129574', '19.03.2020', '31.02.2020'),
    ('f0d1129a', 'CHF 200', 'CHF 0'),
    ('ac9bc7be', 'leur procuration est radiée', 'leur procuration subsiste'),
])
def test_invalid_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new, 1)
    assert changed != args[0]
    assert extract_parser283_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['493e8810', 'a586ada0', 'db9cf682', 'f0d1129a'])
def test_source_signing_required(prefix):
    args, kwargs = invocation(prefix)
    kwargs['source_text'] = ''
    assert extract_parser283_leftovers(*args, **kwargs) == ([], args[0])


def test_payloads():
    assert selected('006a6114')[0].payload['headquarters_uid'] == 'CHE-105.215.815'
    assert selected('3b7614d1')[0].payload['branch_uid'] == 'CHE-208.058.725'
    liquidators = selected('493e8810')
    assert liquidators[0].payload['place'] is None
    assert liquidators[1].payload['place'] == 'Chamoson'
    assert all(e.role == 'liquidateur' and e.signing == 'Kollektivunterschrift zu zweien' for e in liquidators)
    assert selected('4a952e97')[0].payload['count'] == "14'077"
    corporate = selected('9c7685c9')[0]
    assert corporate.payload['name'] == 'SFDC International Holding B.V.'
    assert corporate.payload['country'] == 'Pays-Bas'
    foundation = selected('a586ada0')[0]
    assert foundation.payload['origin'] == foundation.payload['place'] == 'Vallorbe'
    assert foundation.signing == 'Kollektivunterschrift zu zweien'
    signers = selected('ac9bc7be')
    assert len({e.person_key for e in signers}) == 13
    assert signers[1].payload['place'] == 'Lausanne'
    assert signers[8].payload['place'] == 'Genève'
    assert all(e.payload['procuration_revoked'] for e in signers)
    transfer = selected('bfb9ba5c')
    assert [e.payload['shares'] for e in transfer] == [100, 100]
    assert transfer[1].payload['share_nominal'] is None
    assert transfer[1].signing == 'ohne Zeichnungsberechtigung'
    assert selected('db129574')[0].payload['dissolved_by_bankruptcy']
    board = selected('db9cf682')
    assert [e.signing for e in board] == ['Einzelunterschrift', 'Kollektivunterschrift zu zweien']
    assert selected('e16852ab')[0].payload['deletion_blocked']
    transfer = selected('f0d1129a')
    assert [e.payload['shares'] for e in transfer] == [35, 35]
    assert transfer[1].role == 'associé-gérant'
    assert transfer[1].signing == 'Einzelunterschrift'
