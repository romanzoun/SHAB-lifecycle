import hashlib
import inspect
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.models import Event
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parser577 import extract_parser577_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', '913c9ba3b66b6682b1260c4225304462d533a45cea4fb191a93035922e35f837', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = '913c9ba3b66b6682b1260c4225304462d533a45cea4fb191a93035922e35f837'
ARGS = ('it', 'fixture', '', None, None, None)


def target_text():
    source = next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text
    return 'Fusione:' + source.split('Fusione:', 1)[1]


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', DIGESTS)
def test_pipeline_preserves_old_results(digest):
    path = FIXTURES / (digest + '.xml')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser577_leftovers', lambda text, *a: ([], text)):
        old = parser.parse_publication_xml(path)
    remaining = list(result.events)
    for event in old.events:
        remaining.remove(event)
    if digest == TARGET:
        added, rest = extract(old.leftover_text, old.language, old.publication_id,
                              old.published_at, old.org_uid, old.plz, old.canton)
        assert len(added) == 1
        assert all(event in result.events for event in added)
        assert rest.endswith(result.leftover_text)
    else:
        assert result == old


def test_payload_optional_metadata_and_legacy_schema():
    events, rest = extract(target_text(), *ARGS)
    assert rest == '' and len(events) == 1
    event = events[0]
    assert event.event_type == 'company_merged'
    assert event.payload == {
        'kind': 'absorption', 'absorbed_name': 'BonusCard.ch AG',
        'absorbed_place': 'Zürich', 'absorbed_uid': 'CHE-112.789.317',
        'agreement_date': '2021-04-16', 'balance_date': '2020-12-31',
        'assets': "164'109'192.00", 'liabilities': "98'409'718.00",
        'currency': 'CHF', 'all_shares_held_by_acquirer': True,
        'capital_increase': False, 'share_allocation': False,
    }
    assert (event.org_uid, event.plz, event.canton, event.role, event.signing) == (None,) * 5
    assert Event(**vars(event)) == event
    legacy = Event('old', '', 'company_merged', 'old', payload={'kind': 'absorption'})
    assert Event(**vars(legacy)) == legacy
    assert PARSER_VERSION >= 577


def test_no_old_rule_owns_sample():
    from shab_analyzer.text_extras import extract_text_extras
    text = target_text().removesuffix('.')
    assert extract_text_extras(text, *ARGS, set())[0] == []
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser577_leftovers':
            continue
        options = {'source_text': target_text()} if 'source_text' in inspect.signature(old).parameters else {}
        assert old(text, *ARGS, **options) == ([], text), name


@pytest.mark.parametrize('variant', ['di', 'simple'])
def test_old_rule_boundary(variant, tmp_path):
    from shab_analyzer.parser117 import extract_parser117_leftovers
    from shab_analyzer.parser382 import extract_parser382_leftovers
    text = target_text()
    if variant == 'di':
        text = text.replace('aumento del capitale', 'aumento di capitale')
        old_extract = extract_parser117_leftovers
    else:
        text = text.replace('BonusCard.ch AG', 'BonusCard AG')
        old_extract = extract_parser382_leftovers
    assert old_extract(text, *ARGS)[0]
    assert extract(text, *ARGS) == ([], text)
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    next(tree.iter('publicationText')).text = text
    path = tmp_path / 'boundary.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser577_leftovers', lambda text, *a: ([], text)):
        assert result == parser.parse_publication_xml(path)


@pytest.mark.parametrize('old,new', [
    ('16.04.2021', '31.02.2021'), ('31.12.2020', '31.13.2020'),
    ('tutte le azioni', 'alcune azioni'), ('senza aumento', 'con aumento'),
    ('CHF', 'EUR'),
])
def test_unsupported_variants(old, new):
    text = target_text().replace(old, new)
    assert extract(text, *ARGS) == ([], text)


@pytest.mark.parametrize('language', ['de', 'fr', None])
def test_other_languages(language):
    text = target_text()
    assert extract(text, language, *ARGS[1:]) == ([], text)


def test_context_and_unsupported_residue():
    events, _ = extract(target_text(), 'it', 'pub', '2021-04-20', 'CHE-000.000.000', '6900', 'TI')
    assert (events[0].publication_id, events[0].published_at, events[0].org_uid,
            events[0].plz, events[0].canton) == ('pub', '2021-04-20', 'CHE-000.000.000', '6900', 'TI')
    for text in ('', target_text() + ' Altro.', target_text().split(' La società')[0]):
        assert extract(text, *ARGS) == ([], text)
