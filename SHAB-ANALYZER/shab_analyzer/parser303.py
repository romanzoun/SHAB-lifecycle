from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser303_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete sample-backed clauses; preserve unsupported input."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('_date'):
                        datetime.strptime(value, '%d.%m.%Y')
                    elif key.endswith('_written'):
                        datetime.strptime(value.replace('März', '03'), '%d. %m %Y')
            except ValueError:
                return None
        return m

    def event(rule, action, m):
        return _event(*context, 'organization_changed', rule, {'action': action, **m.groupdict()})

    m = match(rf"""L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<reference>\d+/\d+)\) est rectifiée en ce sens que le nom de la localité dans le domicile social est (?P<place>{NAME}) \(et non pas (?P<previous_place>{NAME})\)""", 'fr')
    if m:
        return [event('fr.text.domicile_locality_corrected.v1', 'domicile_locality_corrected', m)], ''

    m = match(rf"""\[gestrichen: Mit Entscheid der Einzelrichterin des (?P<court>[^.;]+?), Abteilung (?P<division>\d+), vom (?P<opening_date>{DATE}) ist über die Inhaberin mit Wirkung ab dem (?P<effective_date>{DATE}), (?P<time>(?:[01]\d|2[0-3])\.[0-5]\d) Uhr, der Konkurs eröffnet worden\.\]\. Mit Mitteilung des (?P<appeal_court>{NAME}) vom (?P<decision_date>{DATE}) ist dem Rekurs gegen den Entscheid des (?P<previous_court>{NAME}) vom (?P<appealed_date>{DATE}) betreffend Konkurseröffnung aufschiebende Wirkung zuerkannt worden\. Demnach wird die Eintragung betreffend Konkurseröffnung über die Inhaberin im Handelsregister gestrichen""", 'de')
    if m:
        return [event('de.text.proprietor_bankruptcy_appeal_suspended.v1', 'proprietor_bankruptcy_appeal_suspended', m)], ''

    m = match(rf"""Name neu: (?P<name>{NAME}) in Liquidation\. Mit Entscheid vom (?P<decision_date>{DATE}) hat das (?P<court>{NAME}) den Verein aufgelöst und die (?P<liquidator>{NAME}), in (?P<place>{NAME}) \((?P<uid>{UID})\), als Sachwalterin und Liquidatorin eingesetzt""", 'de')
    if m:
        return [event('de.text.association_dissolved_corporate_liquidator.v1', 'association_dissolved_corporate_liquidator', m)], ''

    m = match(rf"""L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name>{NAME}) est toujours membre du conseil d'administration; seule sa fonction de président a été radiée\. ll continue de signer collectivement à deux avec (?P<partner1>{NAME}) ou (?P<partner2>{NAME})""", 'fr')
    if m:
        return [_person_event(*context, 'officer_changed', 'fr.text.administrator_presidency_corrected.v1', m['name'], role="membre du conseil d'administration", signing='Kollektivunterschrift zu zweien', extra={**m.groupdict(), 'removed_role': 'président', 'signing_partners': [m['partner1'], m['partner2']]})], ''

    m = match(rf"""Complément: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<reference>\d+/\d+)\) est complétée en ce sens que la raison sociale de la nouvelle associée est désormais (?P<name>[^();]+?) \((?P<uid>{UID})\) \(et non plus (?P<previous_name>{NAME}), comme publié\)""", 'fr')
    if m:
        return [event('fr.text.corporate_associate_name_completed.v1', 'corporate_associate_name_completed', m)], ''

    m = match(rf"""Radiation de la mention relative aux apports en nature et à la reprise de biens envisagée à la constitution de la société\. Radiation du mode de communication aux actionnaires""", 'fr')
    if m:
        return [event('fr.text.contribution_and_communication_clauses_deleted.v1', 'contribution_and_communication_clauses_deleted', m)], ''

    m = match(rf"""Die Gesellschaft wird gemäss Entscheid des (?P<court>{NAME}) vom (?P<decision_date>{DATE}) wieder in das Handelsregister eingetragen\. Die in Bezug auf die Liquidatorin und das Liquidationsdomizil bisher eingetragenen Tatsachen gelten weiterhin""", 'de')
    if m:
        return [event('de.text.reinstatement_liquidation_details_retained.v1', 'reinstatement_liquidation_details_retained', m)], ''

    m = match(rf"""Vorzeitige Löschung mit Bestätigung des zugelassenen Revisionsexperten vom (?P<confirmation_date>{DATE}) aufgeschoben mangels Zustimmungen der eidg\. und kant\. Steuerverwaltung""", 'de')
    if m:
        return [event('de.text.early_deletion_tax_consent_pending.v1', 'early_deletion_tax_consent_pending', m)], ''

    m = match(rf"""L'associé-gérant (?P<seller>{NAME}), lequel est nommé président, cède (?P<transferred>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé-gérant avec signature individuelle\. (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P<remaining_nominal>{MONEY})""", 'fr')
    if m:
        if int(m['before'].replace("'", '')) != int(m['transferred'].replace("'", '')) + int(m['remaining'].replace("'", '')) or m['nominal'] != m['remaining_nominal']:
            return [], leftover
        rule = 'fr.text.associate_manager_transfer_presidency.v1'
        return [event(rule, 'associate_manager_transfer_presidency', m),
                _person_event(*context, 'officer_changed', rule, m['seller'], role='associé-gérant, président'),
                _person_event(*context, 'officer_changed', rule, m['buyer'], place=m['place'], role='associé-gérant', signing='Einzelunterschrift', extra={'origin': m['origin']})], ''

    m = match(rf"""Berichtigung der Eintragung Nr\. (?P<entry>{COUNT}) vom (?P<entry_written>\d{{1,2}}\. März \d{{4}}) \(SHAB vom (?P<notice_written>\d{{1,2}}\. März \d{{4}}), No\. (?P<notice_number>{COUNT}), S\. (?P<page>{COUNT})\): (?P<name>[^;]+?) \(und nicht (?P<previous_name>[^;]+?)\)\. Aktienkapital neu: CHF (?P<capital>{MONEY}), liberiert mit CHF (?P<paid>{MONEY}), eingeteilt in (?P<count>{COUNT}) Namenaktien zu CHF (?P<nominal>{MONEY}) \(bisher in (?P<a_count>{COUNT}) Inhaberaktien zu CHF (?P<a_nominal>{MONEY}), Kat\. A und (?P<b_count>{COUNT}) Inhaberaktien zu CHF (?P<b_nominal>{MONEY}), Kat\. B\)\. Die Übertragbarkeit der Namenaktien ist nach Massgabe der Statuten beschränkt\. Mitteilung an die Aktionäre: schriftlich oder per E-Mail\. Statuten geändert am (?P<statutes_date>{DATE})""", 'de')
    if m:
        return [event('de.text.company_name_share_conversion_corrected.v1', 'company_name_share_conversion_corrected', m)], ''

    m = match(rf"""Vermögensübertragung: Die Gesellschaft überträgt gemäss Vermögensübertragungsvertrag vom (?P<contract_date>{DATE}) einen Teil der Aktiven und Passiven auf die "(?P<recipient>{NAME})" \((?P<uid>{UID})\) mit Sitz in (?P<place>{NAME}), mit Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY})\. Die Übertragung erfolgt ohne Gegenleistung""", 'de')
    if m:
        return [event('de.text.partial_assets_transferred_without_consideration.v1', 'partial_assets_transferred_without_consideration', m)], ''

    m = match(rf"""(?P<seller1>{NAME}) et (?P<seller2>{NAME}), associés, ont cédés chacun (?P<each>{COUNT}) de leurs (?P<before>{COUNT}) parts sociales de CHF (?P<nominal>{MONEY}), à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé avec (?P<buyer_count>{COUNT}) parts sociales de CHF (?P<buyer_nominal>{MONEY}), lequel est en outre nommé gérant avec signature collective à deux""", 'fr')
    if m:
        if 2 * int(m['each'].replace("'", '')) != int(m['buyer_count'].replace("'", '')) or int(m['each'].replace("'", '')) > int(m['before'].replace("'", '')) or m['nominal'] != m['buyer_nominal']:
            return [], leftover
        rule = 'fr.text.two_associates_transfer_new_manager.v1'
        return [event(rule, 'two_associates_transfer_new_manager', m),
                _person_event(*context, 'officer_changed', rule, m['buyer'], place=m['place'], role='associé, gérant', signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin']})], ''

    return [], leftover
