import re
from pathlib import Path

import pytest

from shab_analyzer.models import Event
from shab_analyzer.parser391 import extract_parser391_leftovers
from shab_analyzer.parser395 import extract_parser395_leftovers


@pytest.mark.parametrize('net', ["2'797'015.75", '2797015.75', '2797015'])
def test_valid_asset_transfer_keeps_legacy_payload_and_input(net):
    fixture = Path(__file__).parent / 'fixtures' / '77f41871b77981f2c97e4cf39bd4a74f4ea769e78b4443229fba31bc789de90f.xml'
    publication = re.search(r'<publicationText>(.*?)</publicationText>', fixture.read_text()).group(1)
    text = '  ' + publication[publication.index('Transfert de patrimoine:'):].replace("2'797.015.75", net) + '  '
    args = ('fr', 'p', '2020-12-01', None, None, None)
    old, rest = extract_parser391_leftovers(text, *args)
    assert not rest and len(old) == 1
    assert old[0].event_type == 'organization_changed'
    assert old[0].rule_id == 'fr.text.asset_transfer_no_consideration.v1'
    assert old[0].payload == {
        'action': 'asset_transfer_no_consideration', 'agreement_date': '11.11.2020',
        'assets': "2'872'015.75", 'liabilities': "75'000", 'net_assets': net,
        'recipient': 'Les Charmoises holding SA', 'recipient_uid': 'CHE-170.322.573',
        'place': 'Crésuz', 'currency': 'CHF', 'consideration': 'aucune',
    }
    assert extract_parser395_leftovers(text, *args) == ([], text)
    assert extract_parser395_leftovers(text, *args, source_text=publication) == ([], text)
    assert extract_parser391_leftovers(text, *args) == (old, rest)
    assert Event(**vars(old[0])) == old[0]


def test_legacy_event_without_optional_attributes_still_loads():
    event = Event('p', '2020-12-01', 'organization_changed', 'legacy.rule')
    assert event.payload == {}
    assert event.role is None and event.signing is None
    assert Event(**vars(event)) == event
