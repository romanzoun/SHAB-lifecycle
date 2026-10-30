from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser409 import NAME
from .parser432 import MONTH
from . import parser55, parser60

# Search ownership includes partially consumed historical clauses.
_LEGACY = (parser60._FR_SHARE_TRANSFER_RESTRICTION,
           parser55._FR_STANDALONE_GROUP_SIGNING,
           parser60._FR_BOARD_MEMBERS_SEPARATE_ORIGINS)


def extract_parser435_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete evidenced clauses and preserve historical ownership."""
    leftover = text.strip()
    if any(p.search(leftover) for p in _LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern):
        if language != 'fr':
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
        return _event(*context, kind, f'fr.text.{action}.v1',
                      {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'fr.text.{action}.v1',
                             name, role=role, signing=signing, place=place,
                             extra={'action': action, **m.groupdict(), **extra, 'place': place})

    def number(value):
        return Decimal(value.replace("'", ''))

    m = match(rf'Par décision du (?P<decision_date>{DATE}), le (?P<court>{NAME}) a révoqué la faillite du titulaire')
    if m:
        return [event('sole_proprietor_bankruptcy_revoked_civil_judge', m, 'status_changed', bankruptcy_revoked=True)], ''

    m = match(rf'Les (?P<count>{COUNT}) bons de participation au porteur de CHF (?P<nominal>{MONEY}) sont convertis en (?P=count) bons de participation nominatifs de CHF (?P=nominal)\. Suppression des (?P<deleted_count>{COUNT}) bons de jouissance nominatifs donnant droit à une part du bénéfice net de la société et du produit de liquidation net')
    if m and all(number(m[k]) > 0 for k in ('count', 'nominal', 'deleted_count')):
        return [event('participation_certificates_converted_profit_certificates_removed', m, 'capital_changed', currency='CHF', participation_form='nominatifs', previous_participation_form='au porteur', profit_certificates_removed=True)], ''

    m = match(rf"L'associé (?P<seller>{NAME}) a cédé (?P<count>{COUNT}) de ses (?P<previous_count>{COUNT}) parts sociales de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé\. Gérants: (?P=seller), nommé président, et (?P=buyer), lesquels signent individuellement")
    if m and 0 < number(m['count']) < number(m['previous_count']) and number(m['nominal']) > 0:
        return [event('associate_share_transfer_managers_individual_signing', m, 'ownership_changed', currency='CHF'),
                person('transferor_manager_president_appointed', m, m['seller'], 'président', 'Einzelunterschrift'),
                person('recipient_manager_individual_signing', m, m['buyer'], 'gérant', 'Einzelunterschrift', m['place'])], ''

    m = match(rf'(?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<previous_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée-gérante avec (?P=count) parts de CHF (?P=nominal)\. (?P=seller), qui est nommé président, reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)')
    if m and all(number(m[k]) > 0 for k in ('count', 'remaining', 'nominal')) and number(m['count']) + number(m['remaining']) == number(m['previous_count']):
        return [event('share_transfer_female_manager_remaining_holdings', m, 'ownership_changed', currency='CHF'),
                person('transferor_president_appointed', m, m['seller'], 'président'),
                person('female_recipient_manager_appointed', m, m['buyer'], 'associée-gérante', place=m['place'])], ''

    m = match(rf"Les informations relatives aux personnes disposant d'un pouvoir de représentation pour toute l'entreprise sont radiées conformément à l'art\. 110, al\. 1, let\. e ORC, suite à la modification du droit du registre du commerce\. Est concernée: (?P<name>{NAME})")
    if m:
        return [event('enterprise_representation_information_removed_named_person', m, representation_information_removed=True, legal_basis='art. 110, al. 1, let. e ORC')], ''

    m = match(rf"Transfert de patrimoine: selon contrat du (?P<agreement_day>\d{{1,2}}) (?P<agreement_month>{MONTH}) (?P<agreement_year>\d{{4}}) et selon décision de l'autorité de surveillance du (?P<decision_day>\d{{1,2}}) (?P<decision_month>{MONTH}) (?P<decision_year>\d{{4}}), la fondation a transféré des actifs de CHF (?P<assets>{MONEY}) et des passifs envers les tiers de CHF (?P<liabilities>{MONEY}) à (?P<recipient>{NAME}), à (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Contre-prestation: créances pour un total de CHF (?P<receivables>{MONEY})")
    if m:
        months = MONTH.removeprefix('(?:').removesuffix(')').split('|')
        try:
            for prefix in ('agreement', 'decision'):
                datetime(int(m[prefix + '_year']), months.index(m[prefix + '_month']) + 1, int(m[prefix + '_day']))
        except ValueError:
            return [], text
        return [event('foundation_asset_transfer_receivables_written_dates', m, 'assets_transferred', currency='CHF')], ''

    m = match(rf'Administration: (?P<name1>{NAME}), nommé président, lequel continue à signer individuellement et (?P<name2>{NAME} ép\. {NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]{{3}})')
    if m:
        return [person('board_president_continues_individual_signing', m, m['name1'], 'président', 'Einzelunterschrift'),
                person('board_member_appointed_without_stated_signing', m, m['name2'], 'administrateur', place=m['place'])], ''

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name1>{NAME}) reste membre et président du conseil d'administration et continue de signer individuellement et (?P<name2>{NAME}) est nommée membre du conseil d'administration \(et non pas présidente\)")
    if m:
        return [person('board_president_retained_correction', m, m['name1'], 'président', 'Einzelunterschrift', corrected=True),
                person('female_board_member_role_corrected', m, m['name2'], "membre du conseil d'administration", corrected=True, previously_reported_role='présidente')], ''

    return [], text
