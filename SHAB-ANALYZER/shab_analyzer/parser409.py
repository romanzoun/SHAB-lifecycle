from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from . import parser105, parser107, parser140, parser194, parser252

NAME = r'[^,;.\[\]\n]+?'
_LEGACY = (
    parser105._FR_FOUNDATION_MEMBER_WITH_PRESIDENT,
    parser105._DE_ASSET_TRANSFER_RECIPIENT_PLACE_UID,
    parser107._DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_HISTORY,
    parser140._FR_TWO_LIQUIDATORS_APPOINTED,
    parser140._FR_SIGNING_GRANTED_ROLE_AND_PROXY_REVOKED,
    parser194._DE_PREVIOUS_DOMICILE_OMITTED_CORRECTION,
    parser252._DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_PRIOR_CLAUSE,
)


def extract_parser409_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Only the bounded residual variants documented by release 409 fixtures."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for date in re.findall(DATE, m[0]):
                    datetime.strptime(date, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    m = match(rf'(?P<statutes_date>{DATE})\. Die Generalversammlung hat mit Beschluss vom (?P<decision_date>{DATE}) die Statutenbestimmung über die bedingte Kapitalerhöhung vom (?P<clause_date>{DATE}) geändert\. \[bisher: Die Gründungsversammlung hat mit Beschluss vom (?P=clause_date) eine bedingte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten eingeführt\.\]', 'de')
    if m:
        return [event('conditional_capital_changed_foundation_history', m, 'capital_changed')], ''

    m = match(rf"(?P<seller>{NAME}) jusqu'ici associée-gérante, pour (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}), détient maintenant (?P<remaining>{COUNT}) parts de CHF (?P=nominal), par suite de cession de (?P<count>{COUNT}) parts de CHF (?P=nominal) à l'associé-gérant (?P<buyer>{NAME}), lequel détient désormais (?P<buyer_count>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        number = lambda key: int(m[key].replace("'", ''))
        if number('before') != number('remaining') + number('count'):
            return [], text
        return [event('associate_manager_share_transfer_updated_holdings', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf'Finzione e modalità di firma corretti: (?P<surname>{NAME}), (?P<given_names>{NAME}), cittadino (?P<nationality>{NAME}), in (?P<place>{NAME}), direttore, con firma individuale', 'it')
    if m:
        return [person('director_function_signing_corrected_typo', m, m['surname'] + ', ' + m['given_names'], 'Direktor', 'Einzelunterschrift', m['place'], corrected=True)], ''

    m = match(rf'Bei der Mutation des Eintrages von (?P<name>{NAME}, {NAME}), (?P<nationality>{NAME}) Staatsangehöriger, in (?P<place>{NAME}) \((?P<country>[A-Z]{{2}})\), wurde der bisherige Wohnort in (?P<previous_place>{NAME}) \((?P<previous_country>[A-Z]{{2}})\) irrtümlich nicht aufgeführt', 'de')
    if m:
        return [person('previous_residence_omitted_corrected', m, m['name'], None, place=m['place'], corrected=True)], ''

    # Delegate the already supported second sentence to its original rule.
    prefix, separator, suffix = leftover.partition('. ')
    m = re.fullmatch(rf"(?P<name1>{NAME}), jusqu'ici sous-directrice et (?P<name2>{NAME}), jusqu'ici sous-directeur, nommés directeurs adjoints, continuent à signer collectivement à deux", prefix) if language == 'fr' else None
    if m and separator and parser140._FR_SIGNING_GRANTED_ROLE_AND_PROXY_REVOKED.fullmatch(suffix):
        old_events, rest = parser140.extract_parser140_leftovers(suffix, language, *context)
        if not rest.strip(' .'):
            return [person('two_deputy_directors_promoted', m, m[f'name{i}'], 'Stellvertretender Direktor', 'Kollektivunterschrift zu zweien') for i in (1, 2)] + old_events, ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<agreement_date>\d{{2}}\.\d{{2}} \d{{4}}) Aktiven von CHF (?P<assets>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: CHF (?P<consideration>{MONEY})', 'de')
    if m:
        try:
            datetime.strptime(m['agreement_date'], '%d.%m %Y')
        except ValueError:
            return [], text
        return [event('asset_transfer_missing_date_period', m, 'assets_transferred', currency='CHF')], ''

    m = match(rf'Kapitalherabsetzung und Wiedererhöhung: Bei der Kapitalherabsetzung vom (?P<decision_date>{DATE}) auf CHF (?P<reduced_capital>{MONEY}) zur teilweisen Beseitigung einer Unterbilanz werden (?P<destroyed_count>{COUNT}) Namenaktien zu CHF (?P<destroyed_nominal>{MONEY}) vernichtet\. Gleichzeitig werden durch ordentliche Kapitalerhöhung (?P<issued_count>{COUNT}) voll liberierte Namenaktien zu CHF (?P<issued_nominal>{MONEY}) ausgegeben', 'de')
    if m:
        return [event('capital_reduction_reincrease_partial_deficit', m, 'capital_changed', currency='CHF')], ''

    m = match(rf'(?P<name1>{NAME}) et (?P<name2>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), sont nommés liquidateurs')
    if m:
        original = leftover.rstrip('.') + ' avec signature individuelle'
        if original + '.' not in source_text and original not in source_text:
            return [], text
        return [person('two_liquidators_common_origin_place', m, m[f'name{i}'], 'Liquidator', 'Einzelunterschrift', m['place']) for i in (1, 2)], ''

    m = match(rf"La faillite de la société a été prononcée par jugement du (?P<court>Tribunal d'arrondissement de {NAME}) du (?P<decision_date>{DATE}), avec effet à partir du (?P<effective_date>{DATE}) à (?P<time>(?:[01]\d|2[0-3]):[0-5]\d)\. Par conséquuent, sa raison sociale devient: (?P<liquidation_name>{NAME}, en liquidation)")
    if m:
        return [event('bankruptcy_liquidation_name_consequence_typo', m, 'status_changed', bankrupt=True)], ''

    if language == 'fr' and leftover == 'toutes deux':
        # A leftover qualifier alone carries no new fact. Require the complete
        # original clause; its persons and signing events remain untouched.
        source = re.search(rf"(?P<name1>{NAME}), de et à (?P<place1>{NAME}) et (?P<name2>{NAME}), de et à (?P<place2>{NAME}), sont membres du conseil d'administration, toutes deux avec signature collective à deux\.?$", source_text)
        if source:
            return [], ''

    m = match(rf'(?P<name1>{NAME}), maintenant de (?P<origin1>{NAME}) et à (?P<place1>{NAME}), et (?P<name2>{NAME}) sont nommés liquidateurs')
    if m:
        original = leftover.rstrip('.') + ' avec signature individuelle'
        if original not in source_text:
            return [], text
        return [person('two_liquidators_first_origin_residence_changed', m, m[f'name{i}'], 'Liquidator', 'Einzelunterschrift', m['place1'] if i == 1 else None) for i in (1, 2)], ''

    m = match(rf'Nouveau membre du conseil de fondation avec le/la président\(e\): (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME})')
    if m:
        original = leftover.replace('avec le/la président(e):', 'avec signature collective à deux avec le/la président(e):')
        if original.rstrip('.') not in source_text:
            return [], text
        return [person('foundation_member_joint_signing_gendered_president', m, m['name'], 'Mitglied des Stiftungsrates', 'Kollektivunterschrift zu zweien', m['place'], signing_restriction='avec le/la président(e)')], ''
    return [], text
