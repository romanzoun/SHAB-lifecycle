import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser424 import extract_parser424_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['1b71a549e183cef410201e40ad16a7bc3c2bcb4df44043e47795dcc7f55ff9d8', '4730503234af3068382632da87fa5aad5809b4f227506f52c77ffae628742ce7', '4836ea65cb2436af16b0d8629693b1313bfc09347ddd183dfcfc9e6987418021', '665b99dc7e6f3310b1d8cb6f2c517c24cc7ce987c0f57cc75640e80ccc9039e1', '84034801d78068eafef50e2029cf6fd21fb575127bb1b220b793ac7e7e989bb8', 'ac205bd8b9e6380f6087bccf297d7e67250a5d5812a14be080ff6f52ad16bc80', 'ad8b058f8fa106f202ecf500cbbbcf3912eec7e5d162ba3663aca4fdb565db7b', 'd143196d47529ae0f7632518ce938d8d14074645bfaa53c6013b733bb3a77b9e', 'dac2e202ade3b1f44d32db4db8725cb6911232bcaf9b0c5af1a4b7f4a7de2033', 'de97d942759554b01fc86b124938c09c3f5dd4f31c224a4c76271a44082ae0ea', 'e81bcfbbeaa44aa84c26ccf71e8cf0ab19083d8550083b6f0b79670f35a49f66', 'ef86ca207a8fbd57550f4e1de3054c8a5f7fff0b90b4355b2a8fbc7d1157129f']
COUNTS = [1, 1, 1, 1, 1, 1, 1, 3, 1, 1, 2, 1]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser424_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser424_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert PARSER_VERSION == 436
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
    if index in (2, 4):
        assert events == [] and rest == args[0]
    else:
        assert len(events) == COUNTS[index] and rest == ''



def test_old_event_without_optional_attributes():
    event = Event('p', '', 'officer_changed', 'legacy.rule', payload={'name': 'Test Anna'})
    assert Event(**vars(event)) == event
    assert event.payload == {'name': 'Test Anna'}
    assert event.role is None and event.signing is None




@pytest.mark.parametrize('index', range(12))
def test_no_overlap_with_old_rules_even_in_isolation(index):
    # Exercise every historical extractor on the complete clause in isolation.
    import inspect
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(index)
    for name, old_extract in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser424_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name





EXPECTED = [
    ('status_changed', 'definitive_moratorium_final_extension_without_history'),
    ('officer_changed', 'associate_manager_full_name'),
    ('ownership_changed', 'single_share_transfer_new_associate_no_signing_statement'),
    ('organization_changed', 'branch_deleted_without_canton'),
    ('officer_changed', 'new_manager_collective_signing_three'),
    ('publication_corrected', 'given_name_and_residence_corrected_typo'),
    ('publication_corrected', 'three_notices_given_name_corrected'),
    ('ownership_changed', 'partial_share_transfer_manager_president_pair'),
    ('publication_corrected', 'corporate_domicile_country_corrected'),
    ('officer_changed', 'associate_signing_revoked'),
    ('officer_changed', 'foundation_member_pair_trailing_unsigned'),
    ('address_changed', 'branch_seat_municipality_merger_typo'),
]

@pytest.mark.parametrize('index', range(12))
def test_semantics(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    kind, action = EXPECTED[index]
    assert rest == ''
    assert events[0].event_type == kind
    assert events[0].payload['action'] == action
    if index == 2:
        assert events[0].payload['transferred_count'] == '1'
        assert 'buyer_signing' not in events[0].payload
    if index == 4:
        assert events[0].role == 'gérante'
        assert events[0].signing == 'Kollektivunterschrift zu dreien'
    if index == 7:
        assert [e.role for e in events[1:]] == ['gérant et président', 'gérant']
        assert all(e.signing == 'Einzelunterschrift' for e in events[1:])
    if index == 8:
        assert events[0].payload['country'] == 'FRA'
        assert events[0].payload['previous_country'] == 'AUT'
    if index in (9, 10):
        assert all(e.signing == 'ohne Zeichnungsberechtigung' for e in events)

@pytest.mark.parametrize('index', [2, 4])
def test_wrong_source_preserves_input(index):
    _, _, (args, kwargs) = captured(index)
    assert extract(*args, source_text='Unrelated source.') == ([], args[0])

@pytest.mark.parametrize('text,lang,version', [
    ('La succursale de Lausanne (VD) est radiée', 'fr', 220),
    ('Nouveaux membres du conseil de fondation sans signature: Test Anna, de Lausanne, à Genève, et Test Paul, de Genève, à Lausanne', 'fr', 83),
    ("L'associé gérant Test Paul n'exerce plus la signature sociale", 'fr', 418),
    ('Mit Entscheid vom 01.01.2021 hat das Gericht die definitive Nachlassstundung letztmals bis 01.07.2021 verlängert. [bisher: Mit Entscheid vom 01.07.2020 hat das Gericht die definitive Nachlassstundung bis 01.01.2021 verlängert.]', 'de', 243),
])
def test_old_rule_ownership(text, lang, version):
    import importlib
    old = getattr(importlib.import_module(f'shab_analyzer.parser{version}'), f'extract_parser{version}_leftovers')
    events, rest = old(text, lang, 'p', '', None, None, None)
    assert events and rest == ''
    padded = '  ' + text + '  '
    assert extract(padded, lang, 'p', '', None, None, None) == ([], padded)


def test_parser384_keeps_collective_signing_clause():
    from shab_analyzer.parser384 import extract_parser384_leftovers
    _, _, (args, kwargs) = captured(2)
    source = args[0].rstrip('.') + ' avec signature collective à deux.'
    events, rest = extract_parser384_leftovers(*args, source_text=source)
    assert events and rest == ''
    assert extract(*args, source_text=source) == ([], args[0])
