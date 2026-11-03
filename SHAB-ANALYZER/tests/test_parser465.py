import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser465 import extract_parser465_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = '''02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11
1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e
2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3
3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232
7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad
88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7
89ce6ac882c9cb489e7a27c564c70bcef445693584cf7ac4413b34ed9d8cc7cf
8bb4f070db8be493d9d8774f0782f67efdbe36f44d408ddc67ebbdfbfb37152a
8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f
a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5
e686539f0f0dc84d4518524bf3315fae5e3f15bc20bfd3875ee2776389385a7e
f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed'''.split()


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser465_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser465_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(path)
    assert len(calls) == 1
    return result, old, calls[0]


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('index', range(12))
def test_pipeline_preserves_existing_events(index):
    result, old, (args, kwargs) = captured(index)
    added, rest = extract(*args, **kwargs)
    if index == 10:
        assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
        assert len(added) == 3 and rest == ''
        assert result.events == old.events + added
    else:
        assert (added, rest) == ([], args[0])
        assert result == old


def test_payload_compatibility_and_optional_attributes():
    from shab_analyzer.parser226 import extract_parser226_leftovers
    assert PARSER_VERSION == 472
    _, _, (args, kwargs) = captured(10)
    new, rest = extract(*args, **kwargs)
    canonical = args[0].replace(', président et', ' et').replace(', secrétaire,', ',')
    old, old_rest = extract_parser226_leftovers(canonical, *args[1:])
    assert rest == old_rest == '' and len(new) == len(old) == 3
    assert new[0].payload == {
        'kind': 'dissolution', 'action': 'dissolved',
        'decision_maker': 'assemblée générale', 'date': '2020-08-24',
    }
    for index, (before, after) in enumerate(zip(old, new)):
        assert after.event_type == before.event_type
        assert after.role == before.role and after.signing == before.signing
        expected = dict(before.payload)
        if index:
            expected['committee_role'] = ('président', 'secrétaire')[index - 1]
        assert after.payload == expected
        assert after.rule_id == 'fr.persons.association_dissolved_two_committee_roles.v1'
        assert Event(**vars(before)) == before  # Historical payload without new attribute.
        assert Event(**vars(after)) == after
    optional, rest = extract(*args[:4], None, None, None)
    assert rest == '' and [e.payload for e in optional] == [e.payload for e in new]
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in optional)
    assert extract(canonical, *args[1:]) == ([], canonical)


def test_reject_unsupported_variants():
    _, _, (args, kwargs) = captured(10)
    for text in ('', args[0] + ' UNKNOWN',
                 args[0].replace('24.08.2020', '31.02.2020'),
                 args[0].replace('secrétaire', 'trésorier'),
                 args[0].replace('collectivement à deux', 'individuellement')):
        assert extract(text, *args[1:], **kwargs) == ([], text)
    assert extract(args[0], 'de', *args[2:]) == ([], args[0])


def test_no_old_rule_consumes_new_formulation():
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(10)
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser465_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
        events, rest = old(*args, **options)
        assert not events and rest == args[0], name


@pytest.mark.parametrize('number, text', [
    (168, "L'association est dissoute par décision de l'assemblée générale du 30.06.2020. Liquidateurs: les membres du comité Exemple Anne et Exemple Paul, lesquels continuent à signer individuellement"),
    (226, "L'association est dissoute par décision de l'assemblée générale du 30.06.2020. Liquidateurs: les membres du comité Exemple Anne et Exemple Paul, lesquels continuent à signer collectivement à deux"),
    (439, "L'association est dissoute par décision de l'assemblée générale du 30.06.2020. Liquidateurs: les membres du comité Exemple Anne, président, Exemple Paul, secrétaire et Exemple Marie, trésorière, lesquels continuent à signer collectivement à deux"),
])
def test_legacy_ownership(number, text):
    import importlib
    old = getattr(importlib.import_module(f'shab_analyzer.parser{number}'), f'extract_parser{number}_leftovers')
    args = ('fr', 'fixture', '2020-09-01', None, None, None)
    before = old(text, *args)
    assert before[0]
    added, rest = extract(text, *args)
    assert (added, rest) == ([], text)
    assert (added + old(rest, *args)[0], old(rest, *args)[1]) == before


@pytest.mark.parametrize('fixture', [
    '02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11',
    '0ff08580133afd54acaab3b5fd3ec80e60b3d67318de5285ae0f9f0798be0957',
    '9e7a26d8-ab86-45db-9506-0f8c834dfda4',
])
def test_legacy_pipeline_equal(fixture):
    import shab_analyzer.parse as parser
    path = FIXTURES / (fixture + '.xml')
    result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser465_leftovers', lambda text, *a, **kw: ([], text)):
        baseline = parse_publication_xml(path)
    assert result == baseline
