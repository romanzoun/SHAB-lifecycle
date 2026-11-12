import re
from pathlib import Path

import pytest

from shab_analyzer.models import Event
from shab_analyzer.parser376 import extract_parser376_leftovers
from shab_analyzer.parser532 import extract_parser532_leftovers


@pytest.mark.parametrize('padding', ['', '  '])
@pytest.mark.parametrize('metadata', [(None, None, None), ('uid', '8000', 'ZH')])
def test_judgment_remains_owned_by_parser376(padding, metadata):
    fixture = next((Path(__file__).parent / 'fixtures').glob('4da7e6fc*.xml'))
    publication = re.search(r'<publicationText>(.*?)</publicationText>', fixture.read_text()).group(1)
    text = padding + publication[publication.index('Die am '):] + padding
    args = ('de', 'fixture', '', *metadata)
    old_events, old_rest = extract_parser376_leftovers(text, *args)
    assert old_events
    added, remaining = extract_parser532_leftovers(text, *args)
    assert (added, remaining) == ([], text)
    assert extract_parser376_leftovers(remaining, *args) == (old_events, old_rest)


def test_disposition_payload_without_optional_metadata():
    fixture = next((Path(__file__).parent / 'fixtures').glob('2d312106*.xml'))
    publication = re.search(r'<publicationText>(.*?)</publicationText>', fixture.read_text()).group(1)
    text = publication[publication.index('Die am '):]
    events, rest = extract_parser532_leftovers(text, 'de', 'fixture', '', None, None, None)
    populated, populated_rest = extract_parser532_leftovers(text, 'de', 'fixture', '', 'uid', '8000', 'ZH')
    assert len(events) == len(populated) == 1
    assert rest == populated_rest == ''
    assert events[0].payload == populated[0].payload
    assert events[0].org_uid is None and events[0].plz is None and events[0].canton is None
    assert 'previous' not in events[0].payload
    legacy = Event('fixture', '', 'status_changed', 'legacy', payload={'kind': 'registration_reinstated'})
    assert Event(**vars(legacy)) == legacy
    assert 'previous' not in legacy.payload
