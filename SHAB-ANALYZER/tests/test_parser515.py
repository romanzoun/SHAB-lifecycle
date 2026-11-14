import hashlib
import inspect
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parser515 import extract_parser515_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '19fe1921e06403670c72eec2e1a9f462706a952924cd15e99b55829271c3a05c', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = '19fe1921e06403670c72eec2e1a9f462706a952924cd15e99b55829271c3a05c'
ARGS = ('de', 'fixture', '', None, None, None)


def target_text():
    source = next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text
    return 'Die Gesellschaft' + source.split('Die Gesellschaft', 1)[1]


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', DIGESTS)
def test_pipeline_preserves_existing_events(digest):
    path = FIXTURES / (digest + '.xml')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser515_leftovers', lambda text, *a, **kw: ([], text)):
        old = parser.parse_publication_xml(path)
    remaining = list(result.events)
    for event in old.events:
        remaining.remove(event)
    if digest == TARGET:
        added, rest = extract(old.leftover_text, old.language, old.publication_id,
                              old.published_at, old.org_uid, old.plz, old.canton)
        assert len(added) == 3
        assert all(e in result.events for e in added)
        assert rest.endswith(result.leftover_text)
    else:
        assert result == old


def test_payload_and_missing_optional_attributes():
    from shab_analyzer.keys import person_key
    events, rest = extract(target_text(), *ARGS)
    assert len(events) == 3 and rest == ''
    status, company, officer = events
    assert status.event_type == 'status_changed'
    assert status.payload == {
        'action': 'dissolution_new_name_associate_manager_liquidator',
        'decision_date': '30.03.2021', 'dissolved': True,
    }
    assert company.event_type == 'company_name_changed'
    assert company.payload == {
        'action': 'liquidation_name',
        'liquidation_name': 'Rohrbach Markus GmbH in Liquidation',
    }
    assert officer.event_type == 'officer_changed'
    assert officer.payload == {'name': 'Rohrbach Markus', 'place': None}
    assert officer.role == 'Gesellschafter, Geschäftsführer, Liquidator'
    assert officer.signing == 'Einzelunterschrift'
    assert officer.person_key == person_key(name='Rohrbach Markus', place=None)
    for event in events:
        assert event.org_uid is event.plz is event.canton is None
        assert Event(**vars(event)) == event
    legacy = Event('legacy', '', 'officer_changed', 'legacy', payload={'name': 'Example'})
    assert Event(**vars(legacy)) == legacy
    assert legacy.role is legacy.signing is None
    assert 'decision_date' not in legacy.payload
    assert PARSER_VERSION == 549


def test_no_old_rule_owns_input():
    from shab_analyzer.text_extras import extract_text_extras
    text = target_text().removesuffix('.')
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser515_leftovers':
            continue
        options = {'source_text': text} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('old,new', [
    ('30.03.2021', '31.02.2021'),
    ('Gesellschafter, Geschäftsführer, Einzelunterschrift, neu',
     'Geschäftsführer, Einzelunterschrift, neu'),
    ('Gesellschafter, Geschäftsführer, Liquidator', 'Liquidator'),
    ('Neue Firma:', 'Firma:'),
    ('Einzelunterschrift.', 'Kollektivunterschrift zu zweien.'),
])
def test_unsupported_variants(old, new):
    text = target_text().replace(old, new)
    assert extract(text, *ARGS) == ([], text)


@pytest.mark.parametrize('language', ['fr', 'it', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


def test_context_and_unmatched():
    for text in ('', target_text() + ' Suite.', target_text().split('Neue Firma:')[0]):
        assert extract(text, *ARGS) == ([], text)
    events, _ = extract(target_text(), 'de', 'pub', '2020-01-01', 'uid', '2000', 'NE')
    assert all((e.publication_id, e.published_at, e.org_uid, e.plz, e.canton) ==
               ('pub', '2020-01-01', 'uid', '2000', 'NE') for e in events)


@pytest.mark.parametrize('variant', ['role', 'double_period', 'female', 'corrected'])
def test_existing_rule_boundary(variant, tmp_path):
    from shab_analyzer.parser61 import extract_parser61_leftovers
    from shab_analyzer.parser408 import extract_parser408_leftovers
    from shab_analyzer.parser378 import extract_parser378_leftovers
    from shab_analyzer.parser411 import extract_parser411_leftovers
    text = target_text()
    if variant == 'role':
        text = text.replace('Gesellschafter, Geschäftsführer, Einzelunterschrift, neu',
                            'Geschäftsführer, Einzelunterschrift, neu')
        old = extract_parser61_leftovers
    elif variant == 'double_period':
        text = text.replace('Neue Firma: Rohrbach Markus GmbH in Liquidation.', '.')
        old = extract_parser408_leftovers
    elif variant == 'female':
        text = text.replace('Gesellschafter', 'Gesellschafterin').replace(
            'Geschäftsführer', 'Geschäftsführerin').replace('Liquidator,', 'Liquidatorin,')
        text = text.replace('Gesellschafterin, Geschäftsführerin',
                            'Gesellschafterin, 20 Stammanteile zu CHF 100, Geschäftsführerin')
        # Keep the statutory assembly wording unchanged.
        text = text.replace('Gesellschafterinversammlung', 'Gesellschafterversammlung')
        old = extract_parser378_leftovers
    else:
        text = text.replace('Rohrbach Markus, Gesellschafter,',
                            'Rohrbach Markus, korrekterweise Rohrbach Marcus, Gesellschafter,')
        text = text.replace('Gesellschafter, Geschäftsführer',
                            'Gesellschafter, 20 Stammanteile zu CHF 100, Geschäftsführer')
        old = extract_parser411_leftovers
    language = 'fr' if variant == 'double_period' else 'de'
    assert old(text, language, *ARGS[1:])[0]
    assert extract(text, language, *ARGS[1:]) == ([], text)
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    next(tree.iter('language')).text = language
    element = next(tree.iter('publicationText'))
    element.text = element.text.split('Die Gesellschaft', 1)[0] + text
    path = tmp_path / 'boundary.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser515_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parser.parse_publication_xml(path)
