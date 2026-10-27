from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser409 import NAME
from . import parser100, parser119, parser196, parser206

_LEGACY = (
    parser100._FR_AUTHORIZED_CAPITAL_CLAUSE_REMOVED_SHARES,
    parser119._FR_TWO_COLLECTIVE_PROXIES_NOT_TOGETHER,
    parser206._DE_AUTHORIZED_CAPITAL_DECISION_REPLACED,
    parser196._DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED,
)


def extract_parser410_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Bounded residual variants from the release 410 fixtures."""
    leftover = text.strip()
    if any(pattern.fullmatch(leftover) for pattern in _LEGACY):
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

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que la version anglaise de la raison sociale est (?P<english_name>[^\n]+? Ltd)\. Raison sociale: (?P<company_name>[^\n()]+) \((?P<german_name>[^\n()]+)\) \((?P=english_name)\)")
    if m:
        return [event('english_company_name_corrected', m, corrected=True)], ''

    m = match(rf'Die Generalversammlung hat mit Beschluss vom (?P<authorization_date>{DATE}) eine weitere genehmigte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten eingeführt\. Die Generalversammlung hat mit Beschluss vom (?P<decision_date>{DATE}) die Statutenbestimmung über die bedingte Kapitalerhöhung vom (?P<clause_date>{DATE}) geändert', 'de')
    if m:
        suffix = leftover.split('. ', 1)[1]
        if parser196._DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED.fullmatch(suffix):
            old, rest = parser196.extract_parser196_leftovers(suffix, language, *context)
            if not rest.strip(' .'):
                return [event('further_authorized_capital_introduced', m, 'capital_changed')] + old, ''
        return [], text

    m = match(rf'Mit der Eintragung Ref\. (?P<reference>{COUNT}), TR (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) und Publikation SHAB Nr\. (?P<notice>{COUNT}) vom (?P<notice_date>{DATE}) wurde als letztes SHAB-Zitat irrtümlich SHAB Nr\. (?P<previous_notice>{COUNT}) vom (?P<previous_date>{DATE}) genannt\. Statt korrekt SHAB Nr\. (?P<correct_notice>{COUNT}) vom (?P<correct_date>{DATE})', 'de')
    if m:
        return [event('previous_notice_reference_corrected', m, corrected=True)], ''

    m = match(rf'Bei der nachfolgenden Mutation wurde der bisherige Wohnort nicht publiziert\. Deshalb erfolgt folgender Nachtrag: (?P<name>{NAME}, {NAME}), von (?P<origin>{NAME}), in (?P<place>{NAME}), Gesellschafter und Geschäftsführer, mit Einzelunterschrift, mit (?P<count>{COUNT}) Stammanteilen zu je CHF (?P<nominal>{MONEY}) \[bisher: Gesellschafter und Vorsitzender der Geschäftsführung, mit Einzelunterschrift, in (?P<previous_place>{NAME}), mit (?P<previous_count>{COUNT}) Stammanteilen zu je CHF (?P=nominal)\.\]', 'de')
    if m:
        return [person('previous_residence_shareholding_supplement', m, m['name'], 'Gesellschafter und Geschäftsführer', 'Einzelunterschrift', m['place'], corrected=True)], ''

    # The first sentence belongs to parser100 even in isolation. Delegate it
    # unchanged, and only add the newly supported conditional clause/officer.
    prefix, separator, suffix = leftover.partition(". L'assemblée")
    if language == 'fr' and separator and parser100._FR_AUTHORIZED_CAPITAL_CLAUSE_REMOVED_SHARES.fullmatch(prefix):
        tail = "L'assemblée" + suffix
        m = re.fullmatch(rf"L'assemblée générale du (?P<decision_date>{DATE}) a modifié la clause statutaire relative à l'augmentation conditionnelle du capital-actions prise par décision du (?P<clause_date>{DATE}); pour les détails, voir les statuts \(art\. (?P<article>3b al\. 2)\)\. Nouvel administrateur: (?P<name>{NAME}), de et à (?P<place>{NAME})\.?", tail)
        if m:
            try:
                for date in re.findall(DATE, leftover):
                    datetime.strptime(date, '%d.%m.%Y')
            except ValueError:
                return [], text
            old, rest = parser100.extract_parser100_leftovers(prefix + separator[:1], language, *context)
            if not rest.strip(' .'):
                return old + [event('conditional_capital_clause_changed_article', m, 'capital_changed'), person('administrator_common_origin_place', m, m['name'], 'Mitglied des Verwaltungsrates', place=m['place'])], ''

    m = match(rf"L'associé (?P<seller>{NAME}) est maintenant titulaire de (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}) suite à la cession de (?P<count>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]{{3}}), nouvelle associée pour (?P=count) parts de CHF (?P=nominal), nommée gérante")
    if m:
        return [event('shares_transferred_new_associate_manager', m, 'ownership_changed', currency='CHF'), person('new_associate_manager_after_transfer', m, m['buyer'], 'Gesellschafterin und Geschäftsführerin', place=m['place'])], ''

    m = match(rf'Procuration collective à deux, pas entre eux est ni avec (?P<excluded>{NAME}, {NAME}, {NAME}, {NAME}, {NAME}, {NAME} et {NAME}) est conférée à (?P<name1>{NAME}), du (?P<origin1>{NAME}), à (?P<place1>{NAME}), et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME})')
    if m:
        return [person('joint_procuration_exclusions_typo', m, m[f'name{i}'], 'Prokurist', 'Kollektivprokura zu zweien', m[f'place{i}'], signing_restriction='pas entre eux est ni avec ' + m['excluded'], excluded_signing_partner=m[f'name{3-i}']) for i in (1, 2)], ''

    m = match(rf"Procuration collective à deux toutefois pas entre eux est conférée à (?P<name1>{NAME}), d'(?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), et (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME})")
    if m:
        return [person('three_proxies_not_together', m, m[f'name{i}'], 'Prokurist', 'Kollektivprokura zu zweien', m[f'place{i}'], signing_restriction='toutefois pas entre eux', excluded_signing_partners=[m[f'name{j}'] for j in (1, 2, 3) if j != i]) for i in (1, 2, 3)], ''

    m = match(r"L'associée (?P<name>[^\n]+?), dont le nouveau numéro est le \((?P<registry_id>[A-Z0-9]+)\) a transféré son siège à (?P<place>[^\n()]+) \((?P<country>[^\n()]+)\)")
    if m:
        return [event('corporate_associate_registry_and_seat_changed', m, 'ownership_changed')], ''

    m = match(rf"L'assemblée générale a supprimé une clause statutaire relative à une augmentation autorisée du capital \(selon décision du (?P<authorization_date>{DATE})\) par décision du (?P<decision_date>{DATE})")
    if m:
        return [event('authorized_capital_clause_removed_numeric_dates', m, 'capital_changed')], ''

    m = match(rf'(?P<seller>{NAME}), maintenant à (?P<place>{NAME}), cède ses (?P<count1>{COUNT}) de ses (?P<before1>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer1>{NAME}), désormais titulaire de (?P<buyer_count1>{COUNT}) parts de CHF (?P=nominal)\. (?P=seller) reste titulaire de (?P<remaining1>{COUNT}) parts de CHF (?P=nominal)\. (?P=seller) cède (?P<count2>{COUNT}) de ses (?P=remaining1) parts de CHF (?P=nominal) à (?P<buyer2>{NAME}), maintenant titulaire de (?P<buyer_count2>{COUNT}) parts de CHF (?P=nominal)\. (?P=seller) reste titulaire de (?P<remaining2>{COUNT}) parts de CHF (?P=nominal)')
    if m:
        n = lambda key: int(m[key].replace("'", ''))
        if n('before1') != n('count1') + n('remaining1') or n('remaining1') != n('count2') + n('remaining2'):
            return [], text
        return [event('two_share_transfers_first_count_typo', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf"L'associée (?P<seller>[^\n]+?) \((?P<seller_uid>{UID})\) cède (?P<count>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}), par 10 à (?P<buyer1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}) \((?P<country1>{NAME})\), par 10 parts de CHF (?P=nominal) à (?P<buyer2>{NAME}), de et à (?P<place2>{NAME}), par 10 parts de CHF (?P=nominal) à Copropriété formée de (?P<coowner1>{NAME}), de (?P<origin2>{NAME}), et (?P<coowner2>{NAME}), de (?P<origin3>{NAME}), tous deux à (?P<coowner_place>{NAME}), dont le représentant commun est (?P<representative>{NAME}), de (?P<representative_origin>{NAME}), à (?P<representative_place>{NAME}), par 10 parts de CHF (?P=nominal) à (?P<buyer4>[^\n]+?) \((?P<buyer4_uid>{UID})\), à (?P<place4>{NAME}), par 60 parts de CHF (?P=nominal) à (?P<buyer5>[^\n]+?) \((?P<buyer5_id>\d+)\), à (?P<place5>{NAME}) \((?P<country5>{NAME})\), par 10 parts de CHF (?P=nominal) à (?P<buyer6>[^\n]+?) \((?P<buyer6_id>[\d ]+ R\.C\.S\. [^()\n]+)\), à (?P<place6>{NAME}) \((?P<country6>{NAME})\), et par 20 parts de CHF (?P=nominal) à (?P<buyer7>[^\n]+?) \((?P<buyer7_uid>{UID})\), à (?P<place7>{NAME}), nouveaux associés\. (?P<seller_short>[^\n]+?) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        n = lambda key: int(m[key].replace("'", ''))
        if m['seller'] != m['seller_short'] or n('count') != 130 or n('before') != n('count') + n('remaining'):
            return [], text
        return [event('shares_transferred_seven_recipients_coownership', m, 'ownership_changed', currency='CHF', recipient_counts=['10', '10', '10', '10', '60', '10', '20'])], ''
    return [], text
