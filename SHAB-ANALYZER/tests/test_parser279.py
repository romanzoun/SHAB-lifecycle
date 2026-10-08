import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser279 import extract_parser279_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('169a874d', 'fr.persons.two_administrators_liquidators_restrictions_removed.v1', 3), ('1d0b47fb', 'de.text.definitive_moratorium_replaces_provisional.v1', 2), ('294ac46a', 'fr.persons.sequential_transfers_manager_procuration_ended.v1', 3), ('3354dfac', 'de.text.cooperative_share_nominal_changed.v1', 1), ('5b8859ac', 'fr.text.establishments_removed_branch_uids.v1', 1), ('5f781b1a', 'fr.persons.associate_transfer_unsigned_shared_origin.v1', 2), ('7b237b4d', 'fr.persons.liquidatrice_shared_origin.v1', 2), ('84b15a2c', 'fr.persons.administrator_corrected_director.v1', 1), ('d0810eba', 'fr.persons.three_associates_transfer_removed.v1', 4), ('dbd91803', 'de.text.asset_transfer_no_consideration.v1', 1), ('e7c2c521', 'fr.persons.manager_supplement_cens_typo.v1', 1), ('f1f5410d', 'fr.persons.associate_liquidatrice_translated_name.v1', 2)]


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
        return extract_parser279_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser279_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 319
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
    assert extract_parser279_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser279_leftovers(args[0], 'de' if args[1] == 'it' else 'it', *args[2:], **kwargs) == ([], args[0])



@pytest.mark.parametrize('prefix,old,new', [
 ('84b15a2c','10.03.2020','31.02.2020'),
 ('1d0b47fb','13.02.2020','31.02.2020'),
 ('dbd91803','17.03.2020','31.02.2020'),
 ('294ac46a','avec 6 parts','avec 7 parts'),
 ('294ac46a','de 7 parts','de 8 parts'),
 ('3354dfac','300.00','0.00'),
 ('169a874d','Les 100 actions','Les 0 actions'),
 ('5f781b1a','pour 92 parts','pour 93 parts'),
 ('d0810eba','de 200 parts','de 99 parts'),
 ('f1f5410d','signature individuelle','signature collective à deux'),
])
def test_invalid_facts_preserved(prefix, old, new):
 args, kwargs = invocation(prefix)
 changed = args[0].replace(old,new,1)
 assert changed != args[0]
 assert extract_parser279_leftovers(changed,*args[1:],**kwargs) == ([],changed)


def test_payloads():
 assert selected('169a874d')[0].payload['action'] == 'share_transfer_restrictions_removed'
 assert all(e.payload['previous_signing_removed'] for e in selected('169a874d')[1:])
 assert selected('84b15a2c')[0].role == 'directeur'
 assert selected('84b15a2c')[0].payload['correction']
 assert selected('e7c2c521')[0].payload['supplement']
 assert selected('7b237b4d')[1].signing == 'Einzelunterschrift'
 assert selected('f1f5410d')[1].role == 'associée-gérante liquidatrice'
 assert selected('3354dfac')[0].payload['nominal'] == '300.00'
 assert selected('dbd91803')[0].payload['consideration'] == 'Keine'
 assert selected('dbd91803')[0].payload['recipient_uid'] == 'CHE-150.843.780'
 assert [e.payload['shares'] for e in selected('5f781b1a')] == [108,92]
 assert selected('5f781b1a')[1].payload['without_signature']
 removed = selected('d0810eba')
 assert all(e.event_type == 'officer_removed' and e.payload['signing_removed'] for e in removed[:3])
 assert [e.payload['transferred_shares'] for e in removed[:3]] == [34,33,33]
 assert removed[3].payload['shares'] == 200
 assert [e.payload['shares'] for e in selected('294ac46a')] == [7,7,6]
 assert selected('294ac46a')[2].payload['procuration_ended']
 assert len(selected('5b8859ac')[0].payload['branches']) == 3
 assert selected('1d0b47fb')[0].payload['duration_months'] == 6
 assert selected('1d0b47fb')[1].role == 'Sachwalter'
