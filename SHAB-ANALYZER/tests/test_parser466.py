import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser466 import extract_parser466_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = '''02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11
0a22619b8199e35e9fe80975ac0f000d8d54a4ce10cc3eefc4880eb15547bbb0
1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e
2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3
3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232
7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad
88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7
89ce6ac882c9cb489e7a27c564c70bcef445693584cf7ac4413b34ed9d8cc7cf
8bb4f070db8be493d9d8774f0782f67efdbe36f44d408ddc67ebbdfbfb37152a
8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f
a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5
f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed'''.split()


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser466_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser466_leftovers', lambda text, *a, **kw: ([], text)):
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
    if index == 1:
        assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
        assert len(added) == 2 and rest == ''
        assert result.events == old.events + added
    else:
        assert (added, rest) == ([], args[0])
        assert result == old


def canonical_clauses():
    from shab_analyzer.parser466 import _COMBINED
    _, _, (args, _) = captured(1)
    m = _COMBINED.fullmatch(args[0].strip())
    prefix = f"L'inscription no {m['entry']} du {m['entry_date']} est rectifiée en ce sens que "
    return (
        prefix + f"les nouveaux statuts sont datés du {m['statutes_date']} (et non du: {m['previous_statutes_date']})",
        prefix + f"l'associé-gérant se nomme {m['name']} (et non {m['previous_name']})",
    )


def test_payload_compatibility_and_missing_optional_metadata():
    from shab_analyzer.parser87 import extract_parser87_leftovers
    from shab_analyzer.parser288 import extract_parser288_leftovers
    assert PARSER_VERSION == 484
    _, _, (args, kwargs) = captured(1)
    new, rest = extract(*args, **kwargs)
    old = []
    for clause, old_extract in zip(canonical_clauses(), (extract_parser288_leftovers, extract_parser87_leftovers)):
        events, remaining = old_extract(clause, *args[1:])
        assert remaining == '' and len(events) == 1
        old.extend(events)
    assert rest == '' and len(new) == len(old) == 2
    for before, after in zip(old, new):
        assert {k: v for k, v in vars(before).items() if k != 'rule_id'} == {
            k: v for k, v in vars(after).items() if k != 'rule_id'}
        assert after.rule_id == 'fr.text.statutes_date_and_associate_manager_name_corrected.v1'
        assert Event(**vars(before)) == before
    assert new[0].event_type == 'organization_changed'
    assert new[0].payload == {
        'action': 'statutes_corrected', 'correction': True, 'entry': '7040',
        'entry_date': '01.04.2021', 'statutes_date': '25.03.2021',
        'previous_statutes_date': '25.04.2021',
    }
    assert new[1].event_type == 'officer_changed'
    assert new[1].role == 'associé-gérant' and new[1].signing is None
    assert new[1].payload['action'] == 'name_corrected'
    assert new[1].payload['entry_date'] == '2021-04-01'
    optional, rest = extract(*args[:4], None, None, None)
    assert rest == '' and [e.payload for e in optional] == [e.payload for e in new]
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in optional)


def test_reject_unsupported_variants():
    _, _, (args, kwargs) = captured(1)
    for text in ('', args[0] + ' UNKNOWN',
                 args[0].replace('01.04.2021', '31.02.2021'),
                 args[0].replace('25.03.2021', '31.02.2021'),
                 args[0].replace('25.04.2021', '31.02.2021'),
                 args[0].replace('associé-gérant', 'directeur')):
        assert extract(text, *args[1:], **kwargs) == ([], text)
    assert extract(args[0], 'de', *args[2:]) == ([], args[0])


def test_no_old_rule_consumes_new_formulation():
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(1)
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser466_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
        events, rest = old(*args, **options)
        assert not events and rest == args[0], name


def test_standalone_corrections_remain_owned_by_old_rules():
    from shab_analyzer.parser87 import extract_parser87_leftovers
    from shab_analyzer.parser288 import extract_parser288_leftovers
    context = ('fr', 'fixture', '2021-04-06', None, None, None)
    for text, old_extract in zip(canonical_clauses(), (extract_parser288_leftovers, extract_parser87_leftovers)):
        baseline = old_extract(text, *context)
        assert baseline[0]
        added, rest = extract(text, *context)
        assert (added, rest) == ([], text)
        assert (added + old_extract(rest, *context)[0], old_extract(rest, *context)[1]) == baseline


@pytest.mark.parametrize('prefix', ['1910bfec', '1022c850'])
def test_legacy_pipeline_equal(prefix):
    import shab_analyzer.parse as parser
    paths = list(FIXTURES.glob(prefix + '*.xml'))
    assert len(paths) == 1
    result = parse_publication_xml(paths[0])
    with patch.object(parser, 'extract_parser466_leftovers', lambda text, *a, **kw: ([], text)):
        baseline = parse_publication_xml(paths[0])
    assert result == baseline
