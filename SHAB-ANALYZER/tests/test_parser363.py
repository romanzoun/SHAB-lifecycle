import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser363 import extract_parser363_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('14296b04', 'it.text.manager_president_identity_corrected.v1', 1), ('1c871906', 'fr.text.two_liquidators_individual_signing.v1', 2), ('3293f488', 'fr.text.share_transfer_to_existing_corporate_associate.v1', 1), ('462a9256', 'fr.text.board_president_name_corrected_hyphen_date.v1', 1), ('4e63c138', 'fr.text.erroneous_three_person_entry_deleted.v1', 1), ('66475661', 'de.text.public_institute_bearer_participation_authorized.v1', 1), ('740111db', 'fr.text.director_appointed_joint_signing.v1', 1), ('7ba42f80', 'fr.text.share_transfer_between_associate_managers.v1', 1), ('9974f6b7', 'fr.text.corporate_associate_transfer_to_manager.v1', 1), ('da5fb894', 'de.text.sole_proprietor_bankruptcy_reopened_after_appeal.v1', 1), ('dea8e644', 'it.text.unsigned_associate_identity_corrected.v1', 1), ('f223fea7', 'de.text.bearer_participation_book_entry_authorized.v1', 1)]
SUPPLIED_SHA256 = {'14296b04': '14296b049af3cd87fd7dce3278616abe15db54c91af4f9184633979e780dd1b8', '1c871906': '1c871906d97456959b51b97f03084c3edfcb5ca05080d75a31e33272288b67b2', '3293f488': '3293f488e72dd5a6132157bd18542465a2f56965c41c08deff7d0f63ab19021e', '462a9256': '462a925649727759b85bef89e14341bbaacda6e4e4144605a9317374ce36ff07', '4e63c138': '4e63c1388b7afd8d154c4df80c92a87ffcdb1f06c9b77ae6dfdc8c097b5e0f7f', '66475661': '664756615b6e93763ded744e0cc072d37c894a6da32bbe7f42747d3340a29ba4', '740111db': '740111db258c6d43c23d0d276de94372c8049ae269c6c15d7085010c6335fed6', '7ba42f80': '7ba42f801f1691cc7f7be8c6de9f7ed598c34b613dedc82ad1903785340f1d8a', '9974f6b7': '9974f6b71ae1e14f186c3823e400df389eead4cb38c11f84ab1831a23fe43a48', 'da5fb894': 'da5fb894e877ed14b94cddaf54a0ea14f2fc633960c2c3223d61e5e189e81df1', 'dea8e644': 'dea8e64443d444e3002d26ad5db0e9d64bf41b0c59a2a1a3da028cf3c27a1404', 'f223fea7': 'f223fea7d762c6b954cefb8ba8a93dbc3ba22309c2a21782eed560c921c6bd38'}

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
        return extract_parser363_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser363_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser363_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 445
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser363_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser363_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser363_leftovers(args[0], 'en', *args[2:], **kwargs)
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
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser363_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser363_leftovers(*args)
    assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e




@pytest.mark.parametrize('prefix', ['055ca238', '104e4b61', '268cf601', '31a56c77', '3c23f86c', '3e22246c', '4277fd71', '6e972990', 'bee03cb4', 'd9018797', 'e0d1f17e', 'e56b3a1d'])
def test_parser362_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser363_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for event in baseline.events:
        assert Event(**vars(event)) == event


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_optional_metadata_absent(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser363_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]



def test_payload_semantics():
    assert selected('14296b04')[0].signing == 'Einzelunterschrift'
    assert [e.role for e in selected('1c871906')] == ['Liquidator'] * 2
    assert [e.signing for e in selected('1c871906')] == ['Einzelunterschrift'] * 2
    assert selected('1c871906')[0].payload['place'] is None
    assert selected('3293f488')[0].payload['recipient_total'] == '190'
    assert selected('462a9256')[0].signing is None
    assert selected('462a9256')[0].payload['entry_date'] == '09-10-2020'
    assert selected('4e63c138')[0].event_type == 'organization_changed'
    assert selected('66475661')[0].payload['basis'] == 'listed_equity_rights'
    assert selected('740111db')[0].role == 'Direktor'
    assert selected('740111db')[0].signing == 'Kollektivunterschrift zu zweien'
    assert selected('7ba42f80')[0].payload['remaining'] == '375'
    assert selected('9974f6b7')[0].payload['transferred'] == '6'
    assert selected('da5fb894')[0].payload['time'] == '09.00'
    assert selected('dea8e644')[0].signing == 'ohne Zeichnungsberechtigung'
    assert selected('dea8e644')[0].payload['count'] == '10'
    assert selected('f223fea7')[0].payload['basis'] == 'book_entry_securities'


@pytest.mark.parametrize('text', ['', 'Unsupported clause', '   '])
def test_empty_and_unknown_residuals(text):
    assert extract_parser363_leftovers(text, 'fr', 'fixture', '', None, None, None) == ([], text.strip())



@pytest.mark.parametrize('prefix', ['3293f488', '7ba42f80', '9974f6b7'])
def test_inconsistent_share_nominal_preserved(prefix):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace('parts de CHF 100', 'parts de CHF 200', 1)
    assert extract_parser363_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,old,new', [('7ba42f80', '375', '374'), ('9974f6b7', '194', '193'), ('da5fb894', '09.00 Uhr', '25.00 Uhr'), ('462a9256', '09-10-2020', '31-02-2020')])
def test_invalid_counts_time_and_hyphen_date_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser363_leftovers(changed, *args[1:], **kwargs) == ([], changed)
