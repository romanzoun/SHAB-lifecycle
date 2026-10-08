import hashlib
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser307 import extract_parser307_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('0e9aea4a', 'de.text.ordinary_composition_approved_executor.v1', 1), ('19378de0', 'fr.text.bankruptcy_nullity_holder_reinstated.v1', 1), ('1d412303', 'fr.text.officer_domicile_corrected.v1', 1), ('4f968c40', 'fr.text.two_corporate_partners_shares_transferred.v1', 1), ('8eaef12e', 'fr.text.manager_foreign_domicile_individual_signing.v1', 1), ('9ac606c3', 'fr.text.partial_share_transfer_unsigned_partner.v1', 1), ('bda31f85', 'de.text.audit_opt_out_deleted.v1', 1), ('d4d3b668', 'fr.text.authorized_participation_capital_clause_changed.v1', 1), ('dc6bbc0f', 'de.text.registered_shares_asset_transfer_no_consideration.v1', 1), ('dc7d6d67', 'de.text.definitive_composition_moratorium_extended.v1', 1), ('f761dc64', 'fr.text.vice_president_collective_signing.v1', 1), ('fcfb5f59', 'de.text.authorized_capital_increase_amendment_replaced.v1', 1)]


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
        return extract_parser307_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser307_leftovers', capture):
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
    assert extract_parser307_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser307_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])



@pytest.mark.parametrize('prefix', ['0e9aea4a', '19378de0', '1d412303', 'bda31f85', 'dc6bbc0f', 'dc7d6d67', 'fcfb5f59'])
def test_invalid_dates_preserved(prefix):
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', args[0], count=1)
    kwargs['source_text'] = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', kwargs['source_text'], count=1)
    assert changed != args[0]
    assert extract_parser307_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['8eaef12e', 'd4d3b668'])
def test_source_required(prefix):
    args, kwargs = invocation(prefix)
    kwargs['source_text'] = ''
    assert extract_parser307_leftovers(*args, **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('8eaef12e', 'signature individuelle', 'signature collective à deux'),
    ('d4d3b668', 'restrictions quant à la transmissibilité', 'liberté de transmissibilité'),
    ('d4d3b668', "4'999.98", "5'999.98"),
])
def test_source_mismatch_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    assert old in kwargs['source_text']
    kwargs['source_text'] = kwargs['source_text'].replace(old, new)
    assert extract_parser307_leftovers(*args, **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('0e9aea4a', 'genehmigt', 'abgelehnt'),
    ('19378de0', 'nullité', 'validité'),
    ('9ac606c3', 'sans signature', 'avec signature individuelle'),
    ('bda31f85', 'gestrichen', 'bestätigt'),
    ('dc6bbc0f', 'Gegenleistung: keine', 'Gegenleistung: unbekannt'),
    ('dc7d6d67', 'definitive', 'provisorische'),
    ('f761dc64', 'collectivement à deux', 'individuellement'),
])
def test_unsupported_terms_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser307_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_invalid_french_date_preserved():
    args, kwargs = invocation('d4d3b668')
    changed = args[0].replace('29 avril 2020', '31 avril 2020')
    kwargs['source_text'] = kwargs['source_text'].replace('29 avril 2020', '31 avril 2020')
    assert extract_parser307_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    assert selected('0e9aea4a')[0].payload['executor_uid'] == 'CHE-102.671.430'
    assert selected('19378de0')[0].payload['judgment_date'] == '16.09.2019'
    assert selected('1d412303')[0].payload['place'] == 'Neuchâtel'
    shares = selected('4f968c40')[0].payload
    assert (shares['transferred_each'], shares['count'], shares['nominal']) == ('105', '210', '100')
    manager = selected('8eaef12e')[0]
    assert manager.role == 'gérante' and manager.signing == 'Einzelunterschrift'
    assert (manager.payload['region'], manager.payload['country']) == ('NJ', 'USA')
    transfer = selected('9ac606c3')[0].payload
    assert (transfer['previous_count'], transfer['transferred'], transfer['remaining']) == ('20', '1', '19')
    assert selected('bda31f85')[0].payload['declaration_date'] == '15.04.2008'
    capital = selected('d4d3b668')[0].payload
    assert (capital['capital'], capital['count'], capital['nominal']) == ("4'999.98", "499'998", '0.01')
    asset = selected('dc6bbc0f')[0].payload
    assert (asset['count'], asset['nominal'], asset['price']) == ('240', "1'000.00", "2'991'200.00")
    assert selected('dc7d6d67')[0].payload['end_date'] == '26.10.2020'
    vice = selected('f761dc64')[0]
    assert vice.role == 'vice-président du conseil' and vice.signing == 'Kollektivunterschrift zu zweien'
    assert selected('fcfb5f59')[0].payload['original_date'] == '03.05.2016'
