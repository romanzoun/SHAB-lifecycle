from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser312_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete sample-backed clauses, preserving unsupported input."""
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
            except ValueError:
                return None
        return m

    def event(rule, m, event_type='organization_changed', **extra):
        return _event(*context, event_type, rule, {'action': rule.split('.')[2], **m.groupdict(), **extra})

    def person(rule, m, key='name', role=None):
        return _person_event(*context, 'officer_changed', rule, m[key], place=m.groupdict().get('place'), role=role, signing='Kollektivunterschrift zu zweien', extra=m.groupdict())

    m = match(rf'Signature collective à deux est conférée à (?P<name1>{NAME}), et (?P<name2>{NAME}), tous deux de (?P<origin>{NAME}), à (?P<place>{NAME})', 'fr')
    if m:
        rule = 'fr.text.two_signatories_shared_origin_place.v1'
        return [person(rule, m, 'name1'), person(rule, m, 'name2')], ''

    m = match(rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}) p\. (?P<notice_ref>{COUNT})\) est complétée par la radiation de la mention relative à la renonciation au contrôle restreint", 'fr')
    if m:
        return [event('fr.text.audit_waiver_removal_entry_completed.v1', m)], ''

    m = match(rf"Division de la part de de CHF (?P<previous_nominal>{MONEY}) de l'associée (?P<associate>[^;]+?), en une part de CHF (?P<nominal1>{MONEY}) et une part de CHF (?P<nominal2>{MONEY}); par conséquent, l'associée (?P=associate), détient désormais une part de CHF (?P=nominal1) et une part de CHF (?P=nominal2)", 'fr')
    if m:
        amount = lambda key: Decimal(m[key].replace("'", ''))
        if amount('nominal1') + amount('nominal2') != amount('previous_nominal'):
            return [], leftover
        return [event('fr.text.associate_share_split_two_nominals.v1', m)], ''

    m = match(rf'Abspaltung: Die Gesellschaft übernimmt von der (?P<transferor>{NAME}) \((?P<transferor_uid>{UID})\), in (?P<place>{NAME}), einen Teil des Vermögens\. Die Gesellschaft übernimmt dabei gemäss Spaltungsvertrag vom (?P<agreement_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY})\. Da die mitgliedschaftliche Kontinuität gewahrt ist, findet weder eine Kapitalerhöhung noch eine Aktienzuteilung statt', 'de')
    if m:
        return [event('de.text.demerger_assets_membership_continuity.v1', m, capital_increase=False, share_allocation=False)], ''

    m = match(rf'Trasferimento di patrimonio: secondo contratto del (?P<agreement_date>{DATE}), la società ha trasferito attivi per CHF (?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY}) alla (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Controprestazione: (?P<consideration>{MONEY})\. La controprestazione potrà diminuire in base alle clausole di adeguamento del prezzo previste dal contratto di trasferimento', 'it')
    if m:
        return [event('it.text.asset_transfer_adjustable_consideration.v1', m, consideration_may_decrease=True)], ''

    m = match(r'Die Streichung des opting outs anlässlich der Wahl der Revisionsstelle war vergessen worden', 'de')
    if m:
        return [event('de.text.audit_waiver_removal_omitted.v1', m)], ''

    m = match(rf'Inscription de la succursale de (?P<place>{NAME}) \((?P<branch_uid>{UID})\) au registre de commerce du (?P<register>{NAME}) \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_ref>{COUNT})\)', 'fr')
    if m:
        return [event('fr.text.branch_register_entry_notice.v1', m)], ''

    m = match(rf'Le membre du comité (?P<name>{NAME}), nommé secrétaire, signe désormais collectivement à deux', 'fr')
    if m:
        return [person('fr.text.committee_secretary_collective_signing.v1', m, role='Mitglied des Vorstandes, Sekretär')], ''

    m = match(r'\[Publikationspflichtige Tatsachen haben keine Änderung erfahren\.\]', 'de')
    if m:
        return [event('de.text.reportable_facts_unchanged.v1', m, reportable_facts_changed=False)], ''

    m = match(rf'\[Streichung der Statutenbestimmung über die mit Ermächtigungsbeschluss vom (?P<authorization_date>{DATE}) eingeführte genehmigte Kapitalerhöhung infolge Ablaufs der zeitlichen Befristung\.\] \[gestrichen: Die Gesellschaft hat mit Beschluss vom (?P=authorization_date) eine Änderung des genehmigten Kapitals gemäss näherer Umschreibung in den Statuten beschlossen\.\]', 'de')
    if m:
        return [event('de.text.authorized_capital_change_expired.v1', m)], ''

    merger = rf'Fusion: Übernahme der Aktiven und Passiven des Vereins (?P<absorbed_name>{NAME}), in (?P<place>{NAME}) \((?P<absorbed_uid>{UID})\), gemäss Fusionsvertrag vom (?P<agreement_date>{DATE}) und Bilanz per (?P<balance_date>{DATE})\. Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) gehen auf die übernehmende Gesellschaft über\. Da die Mitglieder des übertragenden Vereins bereits an der übernehmenden Gesellschaft beteiligt sind, findet weder eine Kapitalerhöhung noch eine Zuteilung von Stammanteilen statt'
    # Require the entire pair before emitting either merger event.
    if language == 'de':
        clauses = leftover.split('. Fusion: ')
        if len(clauses) == 2:
            matches = [re.fullmatch(merger + r'\.?', clause) for clause in (clauses[0], 'Fusion: ' + clauses[1])]
            if all(matches):
                try:
                    for m in matches:
                        for key in ('agreement_date', 'balance_date'):
                            datetime.strptime(m[key], '%d.%m.%Y')
                except ValueError:
                    return [], leftover
                return [event('de.text.two_association_mergers_existing_members.v1', m, 'company_merged', capital_increase=False, share_allocation=False) for m in matches], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que la traduction anglaise de la succursale est (?P<corrected_translation>[^;]+?) \(et non pas (?P<previous_translation>[^;]+?)\)", 'fr')
    if m:
        return [event('fr.text.branch_english_translation_corrected.v1', m)], ''

    return [], leftover
