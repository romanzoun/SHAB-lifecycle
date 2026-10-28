import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser416 import extract_parser416_leftovers as extract, _LEGACY

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['0a88b18151235ef302c5e08a37b4a48bbde36f15fe75275fd4722c0d042665db', '0f2cc42588ddb6022c31b2b98933e0fefe681ec197d72dbd28e2f3b4511db7fc', '31433b0a30c45f59a04cc75cf1d147f1961185392201ac072503a4170bc565f2', '570eadf24f6ab33a883761b1b4a7f0dbe8148b970d5afd2ed6c3d0254ac407f1', '8351817a3bcfd6cb7b5888f1540fdd85dff6fc36a124daf1729fba182407f489', '8dd7748dbbe4194d50fd0f178df9965160cc60accac2e9cb6a401ad47c32dd34', '92348f44216e430680a47c59997c40353686c38d1f978dd861c54e050d1f9ce2', '992eb4aff42aa7b890fc10b13c1ea03b686e166dfc65f3e808b543256f1808c0', '9bdcd3260e2d75dc9465079f9b7ac23bfaa34195132f2b8953a9d930556ccd96', 'a2355bd72062da4cc4191842efc6d4afba4a986e8979848302c265da2e13357a', 'f4c105c66c0f7a39af6528486edfa984d12dbc5689552b6ff57f98acd1716ca6', 'fda23101bfd8f6c0ccc0495530174fa62ae5beabaf87db886a46ca1084c14f12']
COUNTS = [3, 3, 3, 1, 1, 1, 2, 4, 2, 1, 1, 1]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser416_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser416_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(path)
    assert len(calls) == 1
    return result, old, calls[0]


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('index', range(12))
def test_complete_and_unchanged_old_payloads(index):
    result, old, (args, kwargs) = captured(index)
    added, rest = extract(*args, **kwargs)
    assert PARSER_VERSION == 417
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    assert len(added) == COUNTS[index] and rest == ''
    assert old.leftover_text == args[0]
    assert result.events == old.events + added
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('index', range(12))
def test_unknown_suffix_language_and_invalid_dates(index):
    _, _, (args, kwargs) = captured(index)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract(changed, *args[1:], **kwargs) == ([], changed)
    assert extract(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index', range(12))
def test_missing_optional_metadata_and_source(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args[:4], None, None, None, **kwargs)
    assert len(events) == COUNTS[index] and rest == ''
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    events, rest = extract(*args)
    assert len(events) == COUNTS[index] and rest == ''


EXPECTED = [
 ('ownership_changed', {'count':'5', 'before':'20', 'remaining':'15'}),
 ('ownership_changed', {'remaining':'100', 'count':'100', 'seller_place':'Genève'}),
 ('status_changed', {'decision_date':'14.01.2021'}),
 ('organization_changed', {'historical_annotation':True, 'acquired_count1':"2'327", 'credit':"11'800.00"}),
 ('status_changed', {'corrected':True, 'entry':'502', 'notice_number':'11'}),
 ('organization_changed', {'corrected':True, 'company_uid':'CHE-104.355.247'}),
 ('ownership_changed', {'count':'80', 'before':'180', 'remaining':'100', 'buyer_count':'100'}),
 ('capital_changed', {'authorization_date':'29.11.2018', 'decision_date':'11.02.2021'}),
 ('ownership_changed', {'count':'40', 'remaining_each':'80', 'canton':'VD'}),
 ('company_deleted', {'decision_date':'22.12.2020'}),
 ('assets_transferred', {'assets':"1'200'024.95", 'liabilities':'0.00', 'consideration':'none'}),
 ('capital_changed', {'decision_date':'05.02.2021', 'previous_date':'12.01.2021'}),
]


@pytest.mark.parametrize('index', range(12))
def test_semantics(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    kind, fields = EXPECTED[index]
    assert rest == '' and events[0].event_type == kind
    for key, value in fields.items():
        assert events[0].payload[key] == value
    if index in (0, 1, 8):
        assert all(e.signing is None for e in events)
    if index == 0:
        assert events[1].role == 'associée-gérante' and events[2].role == 'président'
    if index == 2:
        assert all(e.role == 'liquidateur' and e.signing == 'Einzelunterschrift' for e in events[1:])
    if index == 3:
        assert 'acquired_nominal2' not in events[0].payload
    if index == 7:
        from shab_analyzer.parser195 import extract_parser195_leftovers
        expected, remainder = extract_parser195_leftovers(events[0].payload['legacy_clause'], *args[1:])
        assert remainder.strip(' .') == '' and events[1:2] == expected
        assert events[2].signing == events[3].signing == 'Kollektivunterschrift zu zweien'
    if index == 8:
        assert 'transferred_each' not in events[0].payload
    if index == 9:
        assert 'deletion_date' not in events[0].payload
    if index == 10:
        assert 'inventory_date' not in events[0].payload


LEGACY_TEXTS = [
 'Der Vorstand hat am 22.12.2020 beschlossen, auf den Eintrag des Vereins im Handelsregister per 23.12.2020 zu verzichten. Da dieser Verein kein nach kaufmännischer Art geführtes Gewerbe betreibt und somit nicht eintragungspflichtig ist, wird der auf ihn bezügliche Eintrag im Handelsregister gelöscht.',
 "Selon décision de l'Autorité de surveillance du 14.01.2021, la fondation est dissoute. Liquidateurs: les membres du conseil Test Anna, Test Bea, Test Clara, Test Dora et Test Eva.",
 "Suppression de la clause statutaire relative à l'augmentation autorisée du capital fondée sur la décision d'autorisation du 29.11.2018. Par décision du 11.02.2021, l'assemblée générale a introduit une clause statutaire relative à une augmentation autorisée du capital-actions. Pour les détails, voir les statuts.",
]


@pytest.mark.parametrize('pattern,text', list(zip(_LEGACY, LEGACY_TEXTS)))
def test_old_rule_boundaries_without_active_old_rules(pattern, text):
    assert pattern.fullmatch(text)
    assert extract(text, 'de' if text.startswith('Der ') else 'fr', 'p', '', None, None, None, source_text=text) == ([], text)


def test_old_event_without_optional_attributes():
    event = Event('p', '', 'officer_changed', 'legacy.rule', payload={'name':'Test Anna'})
    assert Event(**vars(event)) == event
    assert event.payload == {'name':'Test Anna'}
    assert event.role is None and event.signing is None


@pytest.mark.parametrize('index,before,after', [(0,'de ses 20 parts','de ses 21 parts'), (6,'de ses 180 parts','de ses 181 parts')])
def test_inconsistent_transfer_totals(index, before, after):
    _, _, (args, kwargs) = captured(index)
    changed = args[0].replace(before, after)
    assert changed != args[0]
    assert extract(changed, *args[1:], **kwargs) == ([], changed)
