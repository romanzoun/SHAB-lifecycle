import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser316 import extract_parser316_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('01ce440c', 'de.text.capital_increased_gmbh_converted_ag.v1', 1),
    ('03b0c5fb', 'fr.text.partial_shares_transferred_existing_manager.v1', 2),
    ('044592e3', 'fr.text.two_foundation_members_foreign_residence.v1', 2),
    ('1436495d', 'fr.text.administrators_president_secretary_signing_continued.v1', 3),
    ('477e226e', 'de.text.bankruptcy_opened_french_publication.v1', 1),
    ('5ba3aa97', 'it.text.officers_removed_changed_german_publication.v1', 7),
    ('6ef3505e', 'fr.text.shares_transferred_missing_preposition.v1', 1),
    ('c3055561', 'fr.text.committee_members_joint_three_restricted.v1', 2),
    ('c90ae03e', 'fr.text.associate_manager_signing_corrected_notice.v1', 1),
    ('e93c96a4', 'de.text.bearer_shares_previous_register_state_restored.v1', 1),
    ('ecef3c43', 'fr.text.individual_signing_continued_corrected_notice.v1', 1),
    ('f488c8f1', 'fr.text.two_administrators_second_unsigned.v1', 2),
]


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
        return extract_parser316_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser316_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    result, _ = captured(prefix)
    rule = next(rule for stem, rule, _ in CASES if stem == prefix)
    return [e for e in result.events if e.rule_id == rule]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 319
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    events = selected(prefix)
    assert len(events) == count
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in events)
    if any(e.signing for e in events):
        assert not any(e.rule_id == 'fr.persons.group_signing.v1' for e in result.events)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser316_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser316_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]


@pytest.mark.parametrize('prefix', ['01ce440c', '477e226e', 'c90ae03e', 'e93c96a4', 'ecef3c43'])
def test_invalid_dates_preserved(prefix):
    _, (args, kwargs) = captured(prefix)
    dates = set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0]))
    assert dates
    for date in dates:
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser316_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed


@pytest.mark.parametrize('prefix,old,new', [
    ('01ce440c', "CHF 100'000.00", "CHF 100'001.00"),
    ('03b0c5fb', '140 parts', '141 parts'),
    ('044592e3', 'collective à deux', 'individuelle'),
    ('1436495d', 'individuellement', 'collectivement'),
    ('477e226e', '10.30 Uhr', '24.30 Uhr'),
    ('477e226e', '10.30 Uhr', '10.60 Uhr'),
    ('5ba3aa97', 'con procura collettiva a due', 'con procura individuale'),
    ('6ef3505e', '50 parts de CHf', '49 parts de CHf'),
    ('c3055561', 'avec les deux vice-présidents', 'sans restriction'),
    ('c90ae03e', '(non individuelle)', '(non collective)'),
    ('e93c96a4', "[bisher: 3'000'000", "[bisher: 3'000'001"),
    ('ecef3c43', '(et non pas collectivement à deux)', '(et non pas individuellement)'),
    ('f488c8f1', "n'exerce pas la signature sociale", 'exerce la signature sociale'),
])
def test_unsupported_terms_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    events, leftover = extract_parser316_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


def test_payloads_roles_and_signing():
    conversion = selected('01ce440c')[0]
    assert conversion.payload['previous_legal_form'] == 'GmbH'
    assert conversion.payload['legal_form'] == 'AG'
    transfer = selected('03b0c5fb')
    assert transfer[0].payload['transferred_count'] == '60'
    assert transfer[0].payload['remaining_count'] == '140'
    assert transfer[1].role == 'Gesellschafterin und Geschäftsführerin'
    assert transfer[1].signing is None
    assert [e.signing for e in selected('044592e3')] == ['Kollektivunterschrift zu zweien'] * 2
    admin = selected('1436495d')
    assert [e.role for e in admin] == ['Präsident des Verwaltungsrates', 'Sekretär des Verwaltungsrates', 'Mitglied des Verwaltungsrates']
    assert all(e.signing == 'Einzelunterschrift' for e in admin)
    assert selected('477e226e')[0].payload['dissolved_by_bankruptcy'] is True
    italian = selected('5ba3aa97')
    assert [e.event_type for e in italian] == ['officer_removed'] * 2 + ['officer_changed'] * 5
    assert all(e.payload['removed'] for e in italian[:2])
    assert all(not e.payload['removed'] for e in italian[2:])
    assert [e.signing for e in italian] == ['ohne Zeichnungsberechtigung'] * 2 + ['Kollektivunterschrift zu zweien'] * 5
    assert italian[2].role == 'Delegierter des Verwaltungsrates und Direktor'
    assert italian[3].role == 'Mitglied des Verwaltungsrates und Direktor'
    assert selected('6ef3505e')[0].payload['registration_number'] == 'B114022'
    assert all(e.signing == 'Kollektivunterschrift zu dreien mit dem Präsidenten und einem Vizepräsidenten oder mit den beiden Vizepräsidenten' for e in selected('c3055561'))
    assert selected('c90ae03e')[0].signing == 'Kollektivunterschrift zu zweien'
    assert selected('e93c96a4')[0].payload['share_type'] == 'Inhaberaktien'
    assert selected('ecef3c43')[0].signing == 'Einzelunterschrift'
    assert [e.signing for e in selected('f488c8f1')] == ['Kollektivunterschrift zu zweien', 'ohne Zeichnungsberechtigung']
