import hashlib
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest
import shab_analyzer.parse as parser
from shab_analyzer.models import Event
from shab_analyzer.parser480 import extract_parser480_leftovers
from shab_analyzer.parser578 import extract_parser578_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '28d3ae1e56f18f38bb58b43d8ae520ad99e6ee776508e6e22ec2256612b497b4', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', '9387c8c6bba3bf6b0ccf6e327c0a1e138d6116df82109edb3fb1d8d718166315', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'b384461e6b7912d441606d7fc63d8b27c0032c5592759859619d3e50acc8e176', 'bc9cc7a83fa73db6a32e3fd6f88d6971c4c517dc5ae11ee1d181e6ef3c069b37', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
TARGET = DIGESTS[1]
ARGS = ('fr', 'fixture', '', None, None, None)


def target_text():
    source = next(ET.parse(FIXTURES / (TARGET + '.xml')).iter('publicationText')).text
    return "L'inscription au journal" + source.split("L'inscription au journal", 1)[1]


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('digest', DIGESTS)
def test_preserves_old_events(digest):
    path = FIXTURES / (digest + '.xml')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser578_leftovers', lambda text, *a: ([], text)):
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


def test_event_and_legacy_optional_metadata():
    events, rest = extract(target_text(), *ARGS)
    assert not rest and len(events) == 1
    event = events[0]
    assert event.event_type == 'signing_authority_changed'
    assert event.signing == 'Kollektivprokura zu zweien'
    assert event.payload['action'] == 'procuration_changed'
    assert event.payload['scope'] == 'head_office'
    assert event.payload['entry_date'] == '2020-08-12'
    assert event.payload['notice_date'] == '2020-08-17'
    assert (event.org_uid, event.plz, event.canton) == (None, None, None)
    assert Event(**vars(event)) == event
    legacy = Event('old', '', 'signing_authority_changed', 'old', payload={})
    assert Event(**vars(legacy)) == legacy


def test_old_proxy_boundary(tmp_path):
    text = 'Procuration collective à deux, limitée au siège principal, est conférée à Exemple Alice, de Genève, à Genève'
    assert extract_parser480_leftovers(text, *ARGS)[0]
    assert extract(text, *ARGS) == ([], text)
    tree = ET.parse(FIXTURES / (TARGET + '.xml'))
    next(tree.iter('publicationText')).text = text
    path = tmp_path / 'boundary.xml'
    tree.write(path, encoding='utf-8')
    result = parser.parse_publication_xml(path)
    with patch.object(parser, 'extract_parser578_leftovers', lambda text, *a: ([], text)):
        assert result == parser.parse_publication_xml(path)


@pytest.mark.parametrize('old,new', [('12.08.2020', '31.02.2020'), ('17.08.2020', '31.13.2020'), ('collective à deux', 'individuelle'), ('modifiée en ce sens', 'radiée')])
def test_unsupported(old, new):
    text = target_text().replace(old, new)
    assert extract(text, *ARGS) == ([], text)


def test_other_language():
    text = target_text()
    assert extract(text, 'de', *ARGS[1:]) == ([], text)
