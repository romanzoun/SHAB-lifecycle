import hashlib
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser305 import extract_parser305_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('24d5d212', 'fr.text.two_signing_restrictions_removed.v1', 2),
    ('2cfc1386', 'fr.text.share_transfer_two_new_managers.v1', 3),
    ('35dbac85', 'de.text.two_branches_deleted.v1', 1),
    ('4c2a40c0', 'fr.text.branch_place_corrected.v1', 1),
    ('4f17cbea', 'fr.text.liquidation_translations_liquidator.v1', 2),
    ('7025dd14', 'de.text.conditional_capital_adjusted.v1', 1),
    ('70dc8c3a', 'de.text.intended_asset_acquisition_deleted.v1', 1),
    ('88050de2', 'fr.text.administration_president_three_collective.v1', 4),
    ('94f293f8', 'de.text.cooperative_shares_liability_additional_contributions.v1', 1),
    ('bbb0bb4a', 'fr.text.administration_president_delegate_secretary.v1', 3),
    ('cfc2a10d', 'fr.text.branch_deleted.v1', 1),
    ('dbf951de', 'fr.text.given_names_domicile_corrected.v1', 1),
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
        return extract_parser305_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser305_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 310
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
    assert extract_parser305_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser305_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix', ['7025dd14', '70dc8c3a'])
def test_invalid_dates_preserved(prefix):
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', args[0], count=1)
    kwargs['source_text'] = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', kwargs['source_text'])
    assert extract_parser305_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,old,new', [
    ('24d5d212', 'sans restriction', 'avec restriction'),
    ('2cfc1386', 'signature collective à deux', 'signature individuelle'),
    ('4f17cbea', 'signature individuelle', 'signature collective à deux'),
    ('88050de2', 'signer individuellement', 'signer collectivement à deux'),
    ('bbb0bb4a', 'signature individuelle', 'signature collective à deux'),
    ('94f293f8', 'Persönliche Haftung', 'Keine persönliche Haftung'),
])
def test_unsupported_terms_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser305_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('source_change', ['', 'deleted', 'mismatch'])
def test_deleted_acquisition_requires_source(source_change):
    args, kwargs = invocation('70dc8c3a')
    source = kwargs['source_text']
    kwargs['source_text'] = {'': '', 'deleted': source.replace('[gestrichen:', '[bisher:'), 'mismatch': source.replace("500'000", "600'000")}[source_change]
    assert extract_parser305_leftovers(*args, **kwargs) == ([], args[0])


def test_payloads():
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in selected('24d5d212'))
    transfer, *managers = selected('2cfc1386')
    assert transfer.payload['transferred'] == '66'
    assert [transfer.payload[f'count{i}'] for i in (1, 2, 3, 4)] == ['68', '66', '33', '33']
    assert all(e.role == 'associé gérant' for e in managers)
    assert selected('35dbac85')[0].payload['place1'] != selected('35dbac85')[0].payload['place2']
    assert selected('4c2a40c0')[0].payload['uid'] == 'CHE-396.294.519'
    assert selected('4f17cbea')[1].signing == 'Einzelunterschrift'
    assert selected('7025dd14')[0].payload['resolution_date'] == '18.05.2020'
    acquisition = selected('70dc8c3a')[0].payload
    assert acquisition['foundation_date'] == '04.12.2001' and acquisition['maximum'] == "500'000"
    assert [e.signing for e in selected('88050de2')] == ['Einzelunterschrift'] + ['Kollektivunterschrift zu zweien'] * 3
    assert selected('94f293f8')[0].payload['nominal'] == '100.00'
    assert [e.role for e in selected('bbb0bb4a')] == ['présidente', 'délégué', 'secrétaire']
    assert [e.signing for e in selected('bbb0bb4a')] == ['Einzelunterschrift'] + ['Kollektivunterschrift zu zweien'] * 2
    assert selected('cfc2a10d')[0].payload['uid'] == 'CHE-225.343.894'
    corrected = selected('dbf951de')[0]
    assert corrected.payload['name'] == 'Hänni Yann Karim'
    assert corrected.payload['previous_name'] == 'Hänni Yann-Karim'
    assert corrected.payload['place'] == 'Sullens'
