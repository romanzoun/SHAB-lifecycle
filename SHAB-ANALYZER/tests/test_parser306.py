import hashlib
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser306 import extract_parser306_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('0cd33a49', 'fr.text.capital_subscription_corrected.v1', 1), ('26031015', 'it.text.liquidation_completed_tax_consent_pending.v1', 1), ('49bae8db', 'fr.text.composition_liquidation_completed.v1', 1), ('71e8ca0f', 'fr.text.officer_domicile_country_changed.v1', 1), ('7ad33f1f', 'it.text.ordinary_composition_approved.v1', 1), ('7e328e01', 'fr.text.preferred_share_nominal_corrected.v1', 1), ('80f97823', 'it.text.branch_place_changed.v1', 1), ('83779273', 'de.text.official_deletion_opposed.v1', 1), ('83f7900c', 'fr.text.unlimited_partner_collective_signing.v1', 1), ('a6c94c7d', 'fr.text.purpose_wording_corrected.v1', 1), ('b930863e', 'de.text.bankruptcy_enforcement_provisionally_suspended.v1', 1), ('c7d7a822', 'fr.text.bankruptcy_execution_suspended_name_restored.v1', 1)]


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
        return extract_parser306_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser306_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 318
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
    assert extract_parser306_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser306_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])



@pytest.mark.parametrize('prefix', ['0cd33a49', '26031015', '7ad33f1f', '7e328e01', 'a6c94c7d', 'b930863e', 'c7d7a822'])
def test_invalid_dates_preserved(prefix):
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', args[0], count=1)
    kwargs['source_text'] = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', kwargs['source_text'], count=1)
    assert extract_parser306_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_invalid_french_date_preserved():
    args, kwargs = invocation('49bae8db')
    changed = args[0].replace('1er avril', '31 avril')
    assert extract_parser306_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['83f7900c', 'a6c94c7d'])
def test_source_required(prefix):
    args, kwargs = invocation(prefix)
    kwargs['source_text'] = ''
    assert extract_parser306_leftovers(*args, **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('83f7900c', 'signature collective à deux', 'signature individuelle'),
    ('a6c94c7d', 'Russell Bedford', 'Russell Bedford Changed'),
])
def test_source_mismatch_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    kwargs['source_text'] = kwargs['source_text'].replace(old, new)
    assert extract_parser306_leftovers(*args, **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('26031015', 'mancando il consenso', 'ottenuto il consenso'),
    ('83779273', 'begründeter Einspruch', 'kein Einspruch'),
    ('b930863e', 'Konkurs eröffnet bleibt', 'Konkurs aufgehoben wird'),
    ('7e328e01', 'droit de vote privilégié', 'droit de vote ordinaire'),
    ('7ad33f1f', 'concordato ordinario', 'concordato sconosciuto'),
])
def test_unsupported_terms_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser306_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    capital = selected('0cd33a49')[0].payload
    assert (capital['previous_capital'], capital['capital'], capital['issued']) == ("20'000", "100'000", '800')
    assert [capital[f'subscription{i}'] for i in (1, 2, 3)] == ['134', '333', '333']
    assert capital['count1'] == '334'
    assert selected('26031015')[0].payload['decision_date'] == '28.02.2020'
    assert selected('49bae8db')[0].payload['decision_date'] == '1er avril 2020'
    domicile = selected('71e8ca0f')[0]
    assert domicile.payload['country'] == 'FRA' and domicile.payload['place'] == 'Chens-sur-Léman'
    assert selected('7ad33f1f')[0].payload['months'] == '6'
    shares = selected('7e328e01')[0].payload
    assert (shares['count'], shares['nominal'], shares['previous_nominal']) == ('20', "1'000", '500')
    branch = selected('80f97823')[0].payload
    assert (branch['place'], branch['previous_place'], branch['uid']) == ('Monteceneri', 'Rivera', 'CHE-314.867.395')
    assert selected('83779273')[0].payload['article'] == '159 Abs. 5 lit. a HRegV'
    partner = selected('83f7900c')[0]
    assert partner.role == 'associé indéfiniment responsable' and partner.signing == 'Kollektivunterschrift zu zweien'
    purpose = selected('a6c94c7d')[0].payload
    assert (purpose['wording'], purpose['previous_wording']) == ('Russell Bedford', 'Russel Bedford')
    assert selected('b930863e')[0].payload['judgment_date'] == '20.03.2020'
    assert selected('c7d7a822')[0].payload['business'] == 'Auto-Moto Leal Sàrl'
