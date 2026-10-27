import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser381 import extract_parser381_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('0359dca5', 'de.text.assets_transferred_inventory_no_consideration.v1', 1), ('044aa01c', 'fr.text.foundation_supervisor_audit_exemption.v1', 1), ('0a030783', 'fr.text.administrator_appointed_procuration_revoked.v1', 1), ('0b36d2a2', 'de.text.sole_proprietor_continued_business_registration_retained.v1', 1), ('22c8b347', 'de.text.covid_moratorium_appeal_suspension_clause_deleted.v1', 1), ('6fced291', 'fr.text.moved_liquidator_procuration_extinguished.v1', 1), ('7217fec0', 'fr.text.foundation_presidency_pair_continued_joint_signing.v1', 2), ('8da03525', 'fr.text.four_administrators_president_individual_others_joint.v1', 4), ('aecc57f2', 'de.text.associate_manager_domicile_notice_corrected.v1', 1), ('bd9a3f44', 'fr.text.joint_procuration_pair_shared_origin_domicile.v1', 2), ('cde67070', 'fr.text.associate_manager_liquidator_individual_signing.v1', 1), ('e7cd0f41', 'de.text.authorized_capital_amended_single_prior_amendment.v1', 1)]
SUPPLIED_SHA256 = {'0359dca5': '0359dca588575d29fb1e18033f912380a7139b767e3bf7119fbcd073ee626d1a', '044aa01c': '044aa01ca3b7db20bbbbc76121139a7f35aaed4352aa434bc298b2d52a1157ec', '0a030783': '0a030783f081d1f8d723746bdf720ce6cd080fb68e159d9a002394f89d4e3755', '0b36d2a2': '0b36d2a26fa33c7870b65ab9de264444abc63649ed02148b2249d58b1009cade', '22c8b347': '22c8b34764ae00b1ccf0fd6d98d1016ce81b8af41fc20c9f8a2e8ff4ac94d198', '6fced291': '6fced291573b638957da17b5cab83b2975dafc5fa4ccb5e384fb93fdcf3bfd13', '7217fec0': '7217fec0b7fbbb1f12ca8f30807096344f86909099c5c8603a9331553e7f423a', '8da03525': '8da0352508e299bace5e14763d3244f76a7ef56f816d0e62fd3f7c226830c5b1', 'aecc57f2': 'aecc57f2b04a3ea12f5d7dc0688cda497cbabc8c299b7f87c6210eec2caad1f2', 'bd9a3f44': 'bd9a3f447eef6c93b450b585763325e155e1e989be1068ad208d4c348a44b72e', 'cde67070': 'cde67070d576c78d9c56e2145de092503d8c4388329056403015f9515e2223b9', 'e7cd0f41': 'e7cd0f41330e5b5ace97f7f335c2456edc688f7cfaf8d59c7f831604d48f1f63'}
CONTEXT_REQUIRED = {'0a030783', '6fced291', '8da03525', 'cde67070'}

def path(prefix):
    paths = list(FIXTURES.glob(prefix + '*.xml'))
    assert len(paths) == 1
    return paths[0]


@lru_cache(None)
def captured(prefix):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser381_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser381_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser381_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 407
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser381_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser381_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser381_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_bytes_match_supplied_samples(prefix, rule, count):
    supplied_sha256 = SUPPLIED_SHA256
    fixture = path(prefix)
    assert fixture.stem == supplied_sha256[prefix]
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == supplied_sha256[prefix]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_dates_and_optional_source(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    for date in set(re.findall(r'\d{2}[-.]\d{2}[-.]\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser381_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser381_leftovers(*args)
    if prefix in CONTEXT_REQUIRED:
        assert not events and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e



@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_optional_metadata_absent(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser381_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old



@pytest.mark.parametrize('version', [259, 265, 270, 273, 277, 294, 299, 304, 305, 309, 346, 361, 364, 377, 380])
def test_earlier_rules_keep_ownership_when_disabled(version):
    import shab_analyzer.parse as parser
    source = (Path(__file__).parent / f'test_parser{version}.py').read_text()
    prefixes = set(re.findall(r"['\"]([0-9a-f]{8})(?:[0-9a-f]{56})?['\"]", source))
    name = f'extract_parser{version}_leftovers'
    original = getattr(parser, name)
    checked = 0
    for prefix in sorted(prefixes):
        fixtures = list(FIXTURES.glob(prefix + '*.xml'))
        if len(fixtures) != 1:
            continue
        calls = []
        def capture(*args, **kwargs):
            calls.append((args, kwargs))
            return original(*args, **kwargs)
        with patch.object(parser, name, capture):
            actual = parse_publication_xml(fixtures[0])
        if not calls or not original(*calls[0][0], **calls[0][1])[0]:
            continue
        args, kwargs = calls[0]
        assert extract_parser381_leftovers(*args, **kwargs) == ([], args[0])
        with patch.object(parser, 'extract_parser381_leftovers', lambda text, *a, **kw: ([], text)):
            assert parse_publication_xml(fixtures[0]) == actual
        with patch.object(parser, name, lambda text, *a, **kw: ([], text)):
            disabled = parse_publication_xml(fixtures[0])
        assert not any(e.rule_id in {case[1] for case in CASES} for e in disabled.events)
        checked += 1
        break  # One owned fixture per version; additional legacy regressions run separately.
    assert checked




def test_payload_semantics():
    transfer = selected('0359dca5')[0]
    assert transfer.event_type == 'organization_changed'
    assert transfer.payload['assets'] == "1'038'938.50"
    assert transfer.payload['consideration'] == 'keine'
    assert 'liabilities' not in transfer.payload  # No liabilities are stated.
    exemption = selected('044aa01c')[0]
    assert exemption.event_type == 'audit_requirement_changed'
    assert exemption.payload['audit_exempt'] is True
    administrator = selected('0a030783')[0]
    assert administrator.role == 'administrateur'
    assert administrator.signing == 'Kollektivunterschrift zu zweien'
    assert administrator.payload['procuration_revoked'] is True
    assert selected('0b36d2a2')[0].payload['registration_retained'] is True
    clause = selected('22c8b347')[0]
    assert clause.event_type == 'status_changed'
    assert clause.payload['previous_clause_deleted'] is True
    assert clause.payload['decision_date'] == '18.11.2020'
    liquidator = selected('6fced291')[0]
    assert liquidator.role == 'liquidatrice' and liquidator.signing == 'Einzelunterschrift'
    assert liquidator.payload['procuration_revoked'] is True
    a, b = selected('7217fec0')
    assert a.role == 'membre du conseil de fondation, présidente'
    assert b.role == 'membre du conseil de fondation'
    assert a.signing == b.signing == 'Kollektivunterschrift zu zweien'
    a, b, c, d = selected('8da03525')
    assert a.signing == 'Einzelunterschrift'
    assert b.signing == c.signing == d.signing == 'Kollektivunterschrift zu zweien'
    assert ' ép. ' in b.payload['name']
    correction = selected('aecc57f2')[0]
    assert correction.payload['corrected'] is True
    assert correction.payload['count'] == '200' and correction.payload['nominal'] == '100'
    assert correction.payload['place'] == 'Ueberstorf'
    assert correction.payload['previous_place'] == 'Uetendorf'
    a, b = selected('bd9a3f44')
    assert a.signing == b.signing == 'Kollektivprokura zu zweien'
    assert a.payload['origin'] == b.payload['place'] == 'Rougemont'
    assert selected('cde67070')[0].role == 'associé-gérant, liquidateur'
    assert selected('cde67070')[0].signing == 'Einzelunterschrift'
    capital = selected('e7cd0f41')[0]
    assert capital.event_type == 'capital_changed'
    assert capital.payload['article'] == '3.1.1'
    assert capital.payload['amendment_date'] == '27.06.2019'


@pytest.mark.parametrize('prefix', sorted(CONTEXT_REQUIRED))
def test_signing_context_must_match_exact_person_and_phrase(prefix):
    _, (args, kwargs) = captured(prefix)
    for source in ('', 'unrelated', kwargs['source_text'].replace('signature individuelle', 'signature collective à trois').replace('signature collective à deux', 'signature collective à trois')):
        assert extract_parser381_leftovers(*args, source_text=source) == ([], args[0])
    name = selected(prefix)[0].payload['name']
    assert extract_parser381_leftovers(*args, source_text=kwargs['source_text'].replace(name, 'Autre Exemple')) == ([], args[0])


@pytest.mark.parametrize('text,version,pattern', [
    ('Procuration collective à deux est conférée à Exemple Anne, à Lausanne, et Exemple Paul, à Morges, tous deux de Berne', 200, '_FR_TWO_PROCURATIONS_GRANTED'),
    ('Die Gesellschaft hat mit Beschluss vom 01.02.2020 die mit Beschluss vom 01.02.2018 eingeführte und mit Beschlüssen vom 01.02.2019 geänderte genehmigte Kapitalerhöhung erneut abgeändert gemäss näherer Umschreibung in den Statuten. [bisher: Die Generalversammlung hat mit Beschluss vom 01.02.2019 die mit Beschluss vom 01.02.2018 eingeführte und mit Beschlüssen vom 01.02.2019 geänderte genehmigte Kapitalerhöhung erneut abgeändert gemäss näherer Umschreibung in den Statuten.]', 179, '_DE_AUTHORIZED_CAPITAL_MODIFIED_WITH_HISTORY'),
])
def test_existing_patterns_keep_unmodified_rest(text, version, pattern):
    from importlib import import_module
    old = import_module(f'shab_analyzer.parser{version}')
    assert getattr(old, pattern).fullmatch(text)
    assert extract_parser381_leftovers(text, 'fr' if version == 200 else 'de', 'fixture', '', None, None, None) == ([], text)
