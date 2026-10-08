import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser299 import extract_parser299_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('1d2fc93c', 'de.text.endowment_capital_land_transfer.v1', 1), ('3397385b', 'fr.text.registered_share_nominal_corrected.v1', 1), ('369cb7aa', 'de.persons.associate_manager_signing_removed.v1', 1), ('586e79dc', 'fr.persons.foreign_foundation_president_vice_president.v1', 2), ('59c989e5', 'de.persons.association_board_changes_fr_xml.v1', 3), ('71ee60d4', 'fr.persons.board_president_two_members_signing.v1', 3), ('8134c6a7', 'fr.text.liquidation_share_restrictions_removed.v1', 2), ('9fc37c70', 'de.text.reinstatement_assigned_claims.v1', 1), ('def7c90b', 'fr.persons.foundation_liquidators_mixed_signing.v1', 7), ('e0a618a2', 'fr.persons.foundation_signing_with_president.v1', 3), ('f5aba329', 'fr.persons.board_signing_with_delegates.v1', 5), ('ff0de531', 'de.text.authorized_conditional_capital_provisions_changed.v1', 1)]


def path(prefix):
    paths = list(FIXTURES.glob(prefix + '*.xml'))
    assert len(paths) == 1
    return paths[0]


def selected(prefix):
    rule = next(rule for stem, rule, _ in CASES if stem == prefix)
    return [e for e in parse_publication_xml(path(prefix)).events if e.rule_id == rule]


def invocation(prefix):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser299_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser299_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 316
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    events = [e for e in result.events if e.rule_id == rule]
    assert len(events) == count
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in events)
    if any(e.signing for e in events):
        assert not any(e.rule_id == 'fr.persons.group_signing.v1' for e in result.events)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser299_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser299_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])



@pytest.mark.parametrize('prefix', ['1d2fc93c', '3397385b', '9fc37c70', 'ff0de531'])
def test_invalid_dates_preserved(prefix):
    import re
    args, kwargs = invocation(prefix)
    changed = re.sub(r"\d{2}\.\d{2}\.\d{4}", '31.02.2020', args[0], count=1)
    assert changed != args[0]
    assert extract_parser299_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    capital = selected('1d2fc93c')[0].payload
    assert capital['capital'] == "5'100'000.00"
    assert capital['previous_capital'] == "3'600'000.00"
    assert capital['increase'] == "1'500'000.00" and capital['parcel'] == 'C3789'
    nominal = selected('3397385b')[0].payload
    assert nominal['nominal'] == '100' and nominal['previous_nominal'] == '10'
    assert nominal['count'] == "1'000" and nominal['fully_paid'] is True
    associate = selected('369cb7aa')[0]
    assert associate.role == 'Gesellschafterin' and associate.signing == 'ohne Unterschrift'
    assert associate.payload['count'] == '5' and associate.payload['previous_signing'] == 'Einzelunterschrift'
    foreign = selected('586e79dc')
    assert [e.payload['country'] for e in foreign] == ['DEU', 'USA']
    assert foreign[1].payload['region'] == 'UT'
    assert all(e.signing == 'Einzelunterschrift' for e in foreign)
    board = selected('59c989e5')
    assert [e.role for e in board] == ['Vizepräsidentin des Vorstandes', 'Mitglied des Vorstandes, Aktuarin', 'Mitglied des Vorstandes']
    assert board[1].payload['previous_signing'] == 'ohne Zeichnungsberechtigung'
    assert selected('71ee60d4')[0].signing == 'Einzelunterschrift'
    restrictions, liquidator = selected('8134c6a7')
    assert restrictions.payload['count'] == "1'000" and restrictions.payload['nominal'] == '100'
    assert liquidator.role == 'liquidateur' and liquidator.signing == 'Einzelunterschrift'
    assert selected('9fc37c70')[0].payload['purpose'] == 'assigned_claims'
    liquidators = selected('def7c90b')
    assert all(e.role == 'liquidateur' for e in liquidators)
    assert [e.signing for e in liquidators] == ['Kollektivunterschrift zu zweien'] * 3 + ['ohne Unterschrift'] * 4
    foundation = selected('e0a618a2')
    assert foundation[0].signing == 'Einzelunterschrift'
    assert all(e.payload['signing_partners'] == [foundation[0].payload['name']] for e in foundation[1:])
    directors = selected('f5aba329')
    delegates = [e.payload['name'] for e in directors[:2]]
    assert directors[0].payload['signing_partners'] == [delegates[1]]
    assert directors[1].payload['signing_partners'] == [delegates[0]]
    assert all(e.payload['signing_partners'] == delegates for e in directors[2:])
    provisions = selected('ff0de531')[0].payload
    assert provisions['authorized_decision_date'] == provisions['conditional_decision_date'] == '01.04.2020'
    assert provisions['authorized_introduction_date'] == provisions['conditional_introduction_date'] == '29.03.2017'


@pytest.mark.parametrize('prefix', ['586e79dc', '8134c6a7', 'def7c90b', 'e0a618a2', 'f5aba329'])
def test_unsupported_signing_preserved(prefix):
    args, kwargs = invocation(prefix)
    changed = args[0].replace('signature individuelle', 'signature inconnue').replace('Signature individuelle', 'Signature inconnue').replace('collective à deux', 'collective à trois')
    assert changed != args[0]
    assert extract_parser299_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_inconsistent_share_counts_preserved():
    args, kwargs = invocation('369cb7aa')
    changed = args[0].replace('neu Gesellschafterin, 5', 'neu Gesellschafterin, 6')
    assert extract_parser299_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_inconsistent_delegate_reference_preserved():
    args, kwargs = invocation('f5aba329')
    changed = args[0].replace('Signature collective à deux de Gruner Romain', 'Signature collective à deux de INCONNU')
    assert extract_parser299_leftovers(changed, *args[1:], **kwargs) == ([], changed)
