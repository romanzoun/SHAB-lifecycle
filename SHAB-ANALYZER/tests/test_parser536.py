import hashlib
import inspect
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser536 import extract_parser536_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '48c47af1fafcbb55081f309c92b0f24210a79410cd1670951c6fd2e91dbdd78a', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = '48c47af1fafcbb55081f309c92b0f24210a79410cd1670951c6fd2e91dbdd78a'
ARGS = ('fr', 'fixture', '', None, None, None)


def source_text():
    return next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text


def target_text():
    source = source_text()
    return source[source.index('Complément:'):].rstrip('.')


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', DIGESTS)
def test_pipeline_preserves_existing_results(digest):
    path = FIXTURES / (digest + '.xml')
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    with patch.object(parser, 'extract_parser536_leftovers', capture):
        result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser536_leftovers', lambda text, *a, **kw: ([], text)):
        old = parser.parse_publication_xml(path)
    assert len(calls) == 1
    added, rest = extract(*calls[0][0], **calls[0][1])
    remaining = list(result.events)
    for event in old.events + added:
        remaining.remove(event)
    if digest == TARGET:
        assert len(added) == 2
        assert rest.strip(' .').endswith(result.leftover_text)
    else:
        assert added == []
        assert result == old


def test_payload_and_missing_optional_attributes():
    events, rest = extract(target_text(), *ARGS)
    assert rest == '' and len(events) == 2
    for event, name in zip(events, ['Amaudruz Aurore', 'Fuchs Guillaume']):
        assert event.event_type == 'officer_changed'
        assert event.rule_id == 'fr.persons.entry_supplemented_two_directors_referenced.v1'
        assert event.role == 'directeur'
        assert event.signing is None
        assert event.payload == {
            'name': name, 'place': None, 'action': 'appointed', 'entry': '2667',
            'entry_date': '2021-02-05', 'correction_kind': 'supplement',
            'notice_date': '2021-02-10', 'notice_ref': '0/1005097375',
        }
        assert (event.org_uid, event.plz, event.canton) == (None, None, None)
        assert Event(**vars(event)) == event
        legacy = Event(**{**vars(event), 'payload': {k: v for k, v in event.payload.items()
                                                   if k not in ('notice_date', 'notice_ref')}})
        assert Event(**vars(legacy)) == legacy
        assert 'notice_date' not in legacy.payload and 'notice_ref' not in legacy.payload
    assert extract(target_text(), *ARGS, source_text=source_text()) == (events, rest)
    assert PARSER_VERSION == 546


def test_context():
    events, _ = extract(target_text(), 'fr', 'pub', '2021', 'uid', '1000', 'GE')
    assert len(events) == 2
    for event in events:
        assert (event.publication_id, event.published_at, event.org_uid, event.plz, event.canton) == (
            'pub', '2021', 'uid', '1000', 'GE')


@pytest.mark.parametrize('language', ['de', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


@pytest.mark.parametrize('before,after', [
    ('05.02.2021', '31.02.2021'), ('10.02.2021', '31.02.2021'),
    ('sont directeurs', 'sont administrateurs'),
    (' et Fuchs Guillaume', ''), ('Amaudruz Aurore', ''),
    ('0/1005097375', 'UNKNOWN'),
])
def test_unsupported_unchanged(before, after):
    text = target_text().replace(before, after)
    assert text != target_text()
    assert extract(text, *ARGS) == ([], text)


def test_unknown():
    for text in ('', 'UNKNOWN', target_text() + ' UNKNOWN'):
        assert extract(text, *ARGS) == ([], text)


def test_no_old_rule_owns_target():
    text = target_text()
    from shab_analyzer.text_extras import extract_text_extras
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser536_leftovers':
            continue
        options = {'source_text': source_text()} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


def test_legacy_boundary():
    from shab_analyzer.parser236 import _FR_ENTRY_SUPPLEMENTED_TWO_DIRECTORS
    fixture = FIXTURES / '62089d4c-9cfa-4cf2-ab91-47819e603b6c.xml'
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return [], args[0]
    with patch.object(parser, 'extract_parser236_leftovers', capture):
        parser.parse_publication_xml(fixture)
    args, kwargs = calls[0]
    assert _FR_ENTRY_SUPPLEMENTED_TWO_DIRECTORS.fullmatch(args[0].strip())
    assert parser.extract_parser236_leftovers(*args, **kwargs)[0]
    assert extract(*args, **kwargs) == ([], args[0])
    result = parser.parse_publication_xml(fixture)
    with patch.object(parser, 'extract_parser536_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parser.parse_publication_xml(fixture)


def test_existing_payload_meaning_is_preserved():
    from shab_analyzer.parser236 import extract_parser236_leftovers
    from shab_analyzer.parser536 import _FR_REFERENCED_DIRECTOR_SUPPLEMENT
    match = _FR_REFERENCED_DIRECTOR_SUPPLEMENT.fullmatch(target_text())
    text = (f"L'inscription {match['entry']} du {match['entry_date']} "
            f"est complétée en ce sens que {match['body']}")
    old_events, old_rest = extract_parser236_leftovers(text, *ARGS)
    events, rest = extract(target_text(), *ARGS)
    assert old_rest == rest == ''
    assert len(old_events) == len(events) == 2
    for old, event in zip(old_events, events):
        assert {k: v for k, v in event.payload.items()
                if k not in ('notice_date', 'notice_ref')} == old.payload
        assert {k: v for k, v in vars(event).items()
                if k not in ('rule_id', 'payload')} == {
                    k: v for k, v in vars(old).items() if k not in ('rule_id', 'payload')}
        assert Event(**vars(old)) == old
