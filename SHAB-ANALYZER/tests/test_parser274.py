import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser274 import extract_parser274_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('13550227', 'fr.persons.manager_transfer_unsigned_associate.v1', 2),
    ('20893d39', 'fr.text.appeal_suspensive_effect.v1', 1),
    ('313a8d61', 'fr.persons.signing_corrected_typo.v1', 1),
    ('3dda52b3', 'fr.persons.foundation_secretary_becomes_director.v1', 1),
    ('477d9e1f', 'fr.persons.manager_transfer_collective_president.v1', 2),
    ('5eaa9827', 'de.text.finma_provisional_confirmation.v1', 1),
    ('6d2e9f9a', 'de.text.registration_supporting_documents.v1', 1),
    ('733562e9', 'it.text.asset_transfer_without_consideration.v1', 1),
    ('86741012', 'fr.persons.president_and_directors_board_appointments.v1', 3),
    ('9a06de45', 'fr.persons.president_two_new_administratrices.v1', 3),
    ('b03716f8', 'fr.persons.civil_status_name_and_signer_corrected.v1', 2),
    ('b8c76c5d', 'fr.persons.manager_president_surname_corrected.v1', 1),
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
        return extract_parser274_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser274_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION >= 274
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
    assert extract_parser274_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,old,new', [
    ('13550227', 'détient 150', 'détient 151'),
    ('477d9e1f', 'cède 100', 'cède 101'),
    ('20893d39', '07.02.2020', '31.02.2020'),
    ('5eaa9827', '18.02.2020', '31.02.2020'),
    ('733562e9', '30.01.2020', '32.01.2020'),
    ('313a8d61', 'individuellement', 'collectivement à deux'),
    ('6d2e9f9a', 'Generalversammlung', 'Verwaltungsrat'),
    ('b03716f8', '28.05.2018', '32.05.2018'),
    ('b8c76c5d', '09.01.2020', '32.01.2020'),
])
def test_unsupported_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new, 1)
    assert changed != args[0]
    assert extract_parser274_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['477d9e1f', '9a06de45'])
def test_signing_requires_source_evidence(prefix):
    args, kwargs = invocation(prefix)
    kwargs['source_text'] = kwargs['source_text'].replace('avec signature collective à deux', 'sans signature')
    assert extract_parser274_leftovers(*args, **kwargs) == ([], args[0])


def test_payloads():
    seller, buyer = selected('13550227')
    assert seller.payload['previous_shares'] == 200 and seller.payload['shares'] == 150
    assert buyer.payload['shares'] == 50 and buyer.payload['without_signature'] and buyer.signing is None
    assert selected('20893d39')[0].payload['action'] == 'suspensive_effect_granted'
    assert selected('313a8d61')[0].signing == 'Einzelunterschrift'
    director = selected('3dda52b3')[0]
    assert director.role == 'directrice' and director.payload['signing_continued']
    seller, president = selected('477d9e1f')
    assert seller.payload['shares'] == president.payload['shares'] == 100
    assert president.role == 'associé-gérant président' and president.signing == 'Kollektivunterschrift zu zweien'
    assert selected('5eaa9827')[0].payload['authority'] == 'FINMA'
    assert len(selected('6d2e9f9a')[0].payload['documents']) == 3
    transfer = selected('733562e9')[0]
    assert transfer.payload['assets'] == "536'715.18" and transfer.payload['liabilities'] == '0.00'
    assert transfer.payload['consideration'] == 'none' and transfer.payload['recipient_uid'].startswith('CHE-')
    president, *directors = selected('86741012')
    assert president.role == 'administrateur président'
    assert all(e.payload['previous_role'] == 'directeur' and e.payload['signing_continued'] for e in directors)
    president, *members = selected('9a06de45')
    assert president.signing == 'Einzelunterschrift'
    assert all(e.role == 'administratrice' and e.signing == 'Kollektivunterschrift zu zweien' for e in members)
    renamed, signer = selected('b03716f8')
    assert renamed.signing is None and renamed.payload['erroneous_procuration_removed']
    assert signer.signing == 'Kollektivunterschrift zu zweien' and signer.payload['previous_name'] != signer.payload['name']
    corrected = selected('b8c76c5d')[0]
    assert corrected.role == 'gérante présidente' and corrected.payload['name_scope'] == 'surname'
