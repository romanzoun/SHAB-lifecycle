from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser310_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete sample-backed clauses; retain unsupported input."""
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
                    if key == 'effective_time':
                        datetime.strptime(value, '%H:%M')
            except ValueError:
                return None
        return m

    def event(rule, m, event_type='organization_changed', **extra):
        return _event(*context, event_type, rule, {'action': rule.split('.')[2], **m.groupdict(), **extra})

    def person(rule, m, key='name', role=None, signing=None):
        return _person_event(*context, 'officer_changed', rule, m[key], place=m.groupdict().get('place'), role=role, signing=signing, extra=m.groupdict())

    m = match(rf"Fusione: ripresa di attivi e passivi di (?P<absorbed_name>{NAME}), in (?P<absorbed_place>{NAME}) \((?P<absorbed_uid>{UID})\?\), secondo il contratto di fusione del (?P<agreement_date>{DATE}) e bilancio al (?P<balance_date>{DATE}), che presenta attivi per CHF (?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY})\. La società assuntrice detiene tutte le azioni della società trasferente, per cui la fusione avviene senza aumento di capitale e senza attribuzione di azioni", 'it')
    if m:
        return [event('it.text.wholly_owned_merger_uid_question_mark.v1', m, 'company_merged', capital_increase=False, share_allocation=False, wholly_owned=True, uid_annotation='?')], ''

    m = match(rf"Eingetragene Person geändert: (?P<name>{NAME}), Kollektivunterschrift zu zweien, neu Geschäftsführer, Kollektivunterschrift zu zweien", 'de')
    if m:
        return [person('de.text.manager_appointed_signing_retained.v1', m, role='Geschäftsführer', signing='Kollektivunterschrift zu zweien')], ''

    # This French clause occurs in a German-labelled publication in the supplied sample.
    m = match(rf"(?P<transferor>{NAME}), qui n'est plus associé, cède ses (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<recipient>{NAME}) \((?P<recipient_uid>{UID})\), à (?P<place>{NAME}), nouvelle associée, titulaire de (?P=count) parts de CHF (?P=nominal)", 'de')
    if m:
        return [event('de.text.french_all_shares_transferred.v1', m)], ''

    m = match(rf"Mit dem SHAB Nr\. (?P<notice_number>{COUNT}) vom (?P<notice_date>{DATE}) publizierten TR-Eintrags Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) wurde der bisher Text nicht richtig aufgeführt, richtig wäre: (?P<name>{NAME}, {NAME}), von (?P<origin>{NAME}), in (?P<place>{NAME}), Mitglied der Geschäftsleitung, mit Kollektivunterschrift zu zweien \[bisher: in (?P<previous_place>{NAME}), Mitglied des Verwaltungsrates, Mitglied der Geschäftsleitung, mit Kollektivunterschrift zu zweien\]", 'de')
    if m:
        return [person('de.text.previous_officer_entry_corrected.v1', m, role='Mitglied der Geschäftsleitung', signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf"Par arrêt du (?P<decision_date>{DATE}), la (?P<court>{NAME}) a rejeté le recours contre le jugement du (?P<judgment_date>{DATE}), par conséquent, la faillite est prononcée avec effet à partir du (?P<effective_date>{DATE}) à (?P<effective_time>\d{{2}}:\d{{2}})", 'fr')
    if m:
        return [event('fr.text.bankruptcy_appeal_rejected.v1', m)], ''

    m = match(r"La clause relative aux deux reprises de biens envisagées ont été abrogées conformément à l'art\. (?P<article>628 al\. 4 CO)", 'fr')
    if m:
        return [event('fr.text.two_intended_asset_acquisitions_revoked.v1', m)], ''

    m = match(rf"(?P<name1>{NAME}), (?P<name2>{NAME}) et (?P<name3>{NAME}) continuent à engager la société par leur signature collective à deux, désormais sans restriction", 'fr')
    if m:
        rule = 'fr.text.three_signatories_restriction_removed.v1'
        return [person(rule, m, 'name' + str(i), signing='Kollektivunterschrift zu zweien') for i in (1, 2, 3)], ''

    m = match(rf"Das Zitat lautet richtig SHAB Nr\. (?P<notice_number>{COUNT}) vom (?P<notice_date>{DATE}), nicht SHAB Nr\. (?P<previous_notice_number>{COUNT}) vom (?P<previous_notice_date>{DATE})", 'de')
    if m:
        return [event('de.text.shab_reference_corrected.v1', m)], ''

    m = match(rf"\[Verzicht auf eingeschränkte Revision gestrichen, da eine Revisionsstelle gewählt wurde\.\] \[gestrichen: Laut Erklärung des Verwaltungsrates vom (?P<declaration_date>{DATE}) untersteht die Gesellschaft keiner ordentlichen Revision und verzichtet auf eine eingeschränkte Revision\.\]", 'de')
    if m:
        return [event('de.text.audit_waiver_removed_auditor_elected.v1', m)], ''

    m = match(rf"L'associé-gérant (?P<transferor>{NAME}), désormais d'(?P<origin>{NAME}), cède (?P<transferred_count>{COUNT}) de ses (?P<previous_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à l'associée (?P<recipient>[^;]+?) \((?P<recipient_register_id>\d+[A-Z])\), désormais titulaire de (?P<recipient_count>{COUNT}) parts de CHF (?P=nominal)\. (?P=transferor) reste titulaire de (?P<remaining_count>{COUNT}) parts de CHF (?P=nominal)", 'fr')
    if m:
        number = lambda key: int(m[key].replace("'", ''))
        if number('previous_count') != number('transferred_count') + number('remaining_count') or number('recipient_count') < number('transferred_count'):
            return [], leftover
        return [event('fr.text.existing_foreign_associate_shares_transfer.v1', m)], ''

    m = match(rf'Als Statutendatum wurde irrtümlich "Datum der öffentlichen Urkunde" anstelle von (?P<statutes_date>{DATE}) eingetragen', 'de')
    if m:
        return [event('de.text.statutes_date_placeholder_corrected.v1', m)], ''

    return [], leftover
