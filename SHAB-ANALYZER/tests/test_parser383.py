import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser383 import extract_parser383_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
SUPPLIED_SHA256 = ['0309a3532ddf5c0b6e4a449359fe8af135fa9c967a53053e24ee9d58f7293a32', '22f8ceebd3a3d793e697d429aaf76bdbc613fb4fc9cceaf6768600cbe20a8adf', '31f05281c7d0012a978ff8e613911b057ecb61ca76de4c045c2a4d9ad2f55219', '38b2c89cd65b4f31ca1b3e39e3f1ade5753215092622a26e96cd32af51ffdbad', '508a581d1fbb50daae7e23710944588444e277d1e1477a69dceda0aaa21bff65', '776176b864aaa6f0b4a5992f59a483cbf185615b83afa0daaa5e32e4724ca804', '7f274233d11e9beb846b5a9d89c7a18583650c3e23eab2e818179fe33fb3fff9', '9533df724aa5147c80a7f459d3b5461867c470d9c7a6d570d1d22950fb78fe44', 'b2b3b80c8a471932d417138b5ceea81a648ded234939c00ee8eb67b75fe8e830', 'be694a6f10d3113021b696fd51d601024d9c7d17d8fe019b5cd4c771acc9a3b6', 'bf860501533a9156eebd30667ea7f11a46cbc8c1762679bf6439a5c048120556', 'fb7db4b32471d547a70d22a996e2aff33fdb88290244440c03e0272955d8c278']
CONTEXT_REQUIRED = {'31f05281', '776176b8', 'fb7db4b3'}

@lru_cache(None)
def captured(digest):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser383_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser383_leftovers', capture):
        result = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert len(calls) == 1
    return result, calls[0]

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_complete_and_unchanged_legacy_payloads(digest):
    import shab_analyzer.parse as parser
    result, (args, kwargs) = captured(digest)
    added, rest = extract_parser383_leftovers(*args, **kwargs)
    assert PARSER_VERSION == 390
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(added) == 1 and not rest
    with patch.object(parser, 'extract_parser383_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(FIXTURES / (digest + '.xml'))
    assert result.events == old.events + added
    assert old.leftover_text == args[0]
    assert all(Event(**vars(e)) == e for e in added)

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_unknown_suffix_and_language_preserve_input(digest):
    _, (args, kwargs) = captured(digest)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser383_leftovers(changed, *args[1:], **kwargs) == ([], changed)
    assert extract_parser383_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_missing_optional_source_and_invalid_dates(digest):
    _, (args, kwargs) = captured(digest)
    events, rest = extract_parser383_leftovers(*args)
    if digest[:8] in CONTEXT_REQUIRED:
        assert not events and rest == args[0]
    else:
        assert len(events) == 1 and not rest
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract_parser383_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_old_event_without_new_optional_attributes():
    event = Event('p', '2020-01-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {} and Event(**vars(event)) == event


def test_legacy_pattern_ownership_even_without_old_parser():
    from shab_analyzer.parser137 import _FR_BRANCH_MENTION_REMOVED
    from shab_analyzer.parser203 import _FR_ASSOCIATE_TRANSFER_TO_MANAGER_PRESIDENT
    texts = [
        "Radiation de la mention de l'existence d'une succursale à Lausanne.",
        "Alpha Anne, maintenant à Lausanne, cède 19 de ses 20 parts de CHF 100 à Beta Bob, de Genève, à Lausanne, nouvel associé avec 19 parts de CHF 100, gérant avec signature individuelle, président. Alpha Anne reste titulaire d'une part de CHF 100.",
    ]
    for pattern, text in zip((_FR_BRANCH_MENTION_REMOVED, _FR_ASSOCIATE_TRANSFER_TO_MANAGER_PRESIDENT), texts):
        assert pattern.fullmatch(text)
        assert extract_parser383_leftovers(text, 'fr', 'p', '', None, None, None, source_text=text) == ([], text)

# Explicit expectations for each sample-backed variant, independent of matching.
EXPECTED = {
    '0309a353': ('officer_changed', 'manager_associate_incomplete_notice_corrected', {'corrected': True, 'origin': 'Zürich'}, 'Geschäftsführer und Gesellschafter', 'Einzelunterschrift'),
    '22f8ceeb': ('organization_changed', 'partial_share_transfer_new_associate_single_or_plural_remainder', {'transferred': '60', 'before': '240', 'remaining_count': '180', 'buyer_role': 'associé-gérant'}, None, None),
    '31f05281': ('organization_changed', 'statutes_modified_attested_non_modification_wording', {'statutes_date': '20.11.2020'}, None, None),
    '38b2c89c': ('organization_changed', 'partial_share_transfer_new_associate_single_or_plural_remainder', {'transferred': '19', 'before': '20', 'remaining_count': '1', 'buyer_role': 'associé', 'buyer_signing': 'ohne Zeichnungsberechtigung'}, None, None),
    '508a581d': ('publication_corrected', 'administrator_president_name_notice_corrected', {'entry': '18564', 'notice_id': '1005012254'}, None, None),
    '776176b8': ('organization_changed', 'branch_mention_deleted_sankt_gallen', {'place': 'St. Gallen'}, None, None),
    '7f274233': ('status_changed', 'composition_agreement_completed_historical_clauses_deleted', {'decision_date': '10.11.2020', 'historical_clauses_deleted': True}, None, None),
    '9533df72': ('status_changed', 'deadline_restitution_rejected_judgment_confirmed', {'decision_date': '05.10.2020', 'judgment_date': '11.05.2020'}, None, None),
    'b2b3b80c': ('publication_corrected', 'statutes_copy_deposited_notice_supplement', {'entry': '6886', 'notice_ref': '8/5024030'}, None, None),
    'be694a6f': ('organization_changed', 'cooperative_obligations_registration_rules_updated', {'previous_nominal': '500.--', 'historical_clauses_deleted': True}, None, None),
    'bf860501': ('organization_changed', 'historical_contribution_in_kind_clause_deleted', {'count': '20', 'nominal': '1\'000.--', 'historical_clause_deleted': True, 'agreement_date': '11.07.2008'}, None, None),
    'fb7db4b3': ('officer_changed', 'liquidator_appointed_origin_au_domicile', {'origin': 'Emmen', 'place': 'Mont-sur-Lausanne'}, 'liquidatrice', 'Einzelunterschrift'),
}

@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_expected_event_meaning(digest):
    _, (args, kwargs) = captured(digest)
    events, _ = extract_parser383_leftovers(*args, **kwargs)
    event, = events
    kind, action, payload, role, signing = EXPECTED[digest[:8]]
    assert event.event_type == kind
    assert event.rule_id == args[1] + '.text.' + action + '.v1'
    assert event.payload['action'] == action
    assert event.role == role and event.signing == signing
    for key, value in payload.items():
        assert event.payload[key] == value

@pytest.mark.parametrize('digest', [d for d in SUPPLIED_SHA256 if d[:8] in CONTEXT_REQUIRED])
def test_context_is_required_and_cannot_be_replaced(digest):
    _, (args, kwargs) = captured(digest)
    assert extract_parser383_leftovers(*args, source_text='Unrelated publication.') == ([], args[0])

@pytest.mark.parametrize('prefix', ['22f8ceeb', '38b2c89c'])
def test_inconsistent_transfer_counts_rejected(prefix):
    digest = next(d for d in SUPPLIED_SHA256 if d.startswith(prefix))
    _, (args, kwargs) = captured(digest)
    changed = args[0].replace('de ses 240', 'de ses 241').replace('de ses 20', 'de ses 21')
    assert extract_parser383_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_invalid_natural_language_date_rejected():
    digest = next(d for d in SUPPLIED_SHA256 if d.startswith('9533df72'))
    _, (args, kwargs) = captured(digest)
    changed = args[0].replace('5 octobre', '32 octobre')
    assert extract_parser383_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_related_legacy_share_transfer_remains_owned_by_parser282():
    from shab_analyzer.parser282 import extract_parser282_leftovers
    text = "Alpha Anne cède 19 de ses 20 parts de CHF 100 à Beta Bob, d'Entlebuch, à Lausanne, nouvel associé sans signature, avec 19 parts de CHF 100; Alpha Anne reste titulaire de 1 part de CHF 100."
    context = ('fr', 'p', '', None, None, None)
    old_events, old_rest = extract_parser282_leftovers(text, *context)
    assert len(old_events) == 2 and not old_rest
    # Direct invocation isolates 383 even if the earlier extractor is absent.
    assert extract_parser383_leftovers(text, *context, source_text=text) == ([], text)
