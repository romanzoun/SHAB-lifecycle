from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser311_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
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
                    if key == 'effective_time':
                        datetime.strptime(value, '%H:%M')
            except ValueError:
                return None
        return m

    def event(rule, m, **extra):
        return _event(*context, 'organization_changed', rule, {'action': rule.split('.')[2], **m.groupdict(), **extra})

    def person(rule, m, key='name', role=None, signing=None):
        return _person_event(*context, 'officer_changed', rule, m[key], role=role, signing=signing, extra=m.groupdict())

    m = match(rf"Administration: (?P<name1>{NAME}), nommé président et (?P<name2>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), vice-présidente, tous deux avec signature individuelle", 'fr')
    if m:
        rule = 'fr.text.president_vice_president_individual_signing.v1'
        return [person(rule, m, 'name1', 'Präsident', 'Einzelunterschrift'), person(rule, m, 'name2', 'Vizepräsidentin', 'Einzelunterschrift')], ''

    m = match(rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que l'associé-gérant (?P<name>{NAME}) possède (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) \(et non (?P=count) parts de CHF de (?P<previous_nominal>{MONEY})\)", 'fr')
    if m:
        return [event('fr.text.associate_share_nominal_corrected.v1', m)], ''

    m = match(rf"Signature collective à deux a été conférée à l'associé (?P<name1>{NAME})\. L'associé (?P<name2>{NAME}) n'exerce plus la signature sociale", 'fr')
    if m:
        rule = 'fr.text.associates_signing_granted_removed.v1'
        return [person(rule, m, 'name1', signing='Kollektivunterschrift zu zweien'), person(rule, m, 'name2', signing='ohne Zeichnungsberechtigung')], ''

    m = match(rf"Radiation de la mention relative à l'introduction de la clause statutaire d'augmentation autorisée décidée le (?P<previous_date>{DATE})\. Par décision du (?P<decision_date>{DATE}), l'assemblée générale a introduit une clause statutaire relative à une augmentation autorisée du capital\. Pour les détails, voir les statuts", 'fr')
    if m:
        return [event('fr.text.authorized_capital_clause_replaced.v1', m)], ''

    m = match(rf"Vollständige Adresse: (?P<street>{NAME}), c/o (?P<care_of>{NAME}), (?P<postal_code>\d{{4}}) (?P<place>{NAME})\. Die Gesellschaft ist laut Beschluss der Generalversammlung vom (?P<decision_date>{DATE}) aufgelöst\. Die statutarische Klausel betreffend die Uebertragbarkeit der Namenaktien ist gelöscht\. Eingetragene Person geändert: (?P<name>{NAME}), Verwaltungsratsmitglied, Einzelunterschrift, neu Verwaltungsratsmitglied, Liquidator, Einzelunterschrift", 'de')
    if m:
        return [event('de.text.address_dissolution_transfer_clause_removed.v1', m, dissolved=True), person('de.text.address_dissolution_transfer_clause_removed.v1', m, role='Verwaltungsratsmitglied, Liquidator', signing='Einzelunterschrift')], ''

    m = match(rf"L'administratrice (?P<name>{NAME}), désormais de (?P<origin>{NAME}), est nommée secrétaire avec signature collective à deux", 'fr')
    if m:
        return [person('fr.text.administrator_secretary_origin_changed.v1', m, role='Sekretärin', signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf"Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient>{NAME}) \((?P<recipient_uid>{UID})\), in (?P<place>{NAME})\. Gegenleistung: CHF (?P<consideration>{MONEY}) als Darlehen gutgeschrieben", 'de')
    if m:
        return [event('de.text.asset_transfer_loan_consideration.v1', m)], ''

    m = match(rf"\[Streichung der Statutenbestimmung über die mit Ermächtigungsbeschluss vom (?P<authorization_date>{DATE}) eingeführte genehmigte Kapitalerhöhung infolge Ablaufs der zeitlichen Befristung\.\] \[gestrichen: Die Gesellschaft hat mit Beschluss vom (?P=authorization_date) die mit Beschluss vom (?P<previous_date>{DATE}) geänderte Bestimmung betreffend genehmigter Kapitalerhöhung gemäss näherer Umschreibung in den Statuten geändert\.\]", 'de')
    if m:
        return [event('de.text.amended_authorized_capital_expired.v1', m)], ''

    m = match(rf"Die Domiziänderung vom (?P<first_date>{DATE}) und vom (?P<second_date>{DATE}) wurde irrtümlich vorgenommen\. Das bisherige Rechtsdomizil bleibt unverändert bestehen", 'de')
    if m:
        return [event('de.text.two_erroneous_domicile_changes_reversed.v1', m)], ''

    m = match(rf"Con decisione del (?P<decision_date>{DATE}) la (?P<court>Camera di esecuzione e fallimenti del Tribunale d'appello del Cantone Ticino) ha accordato effetto sospensivo al reclamo inoltrato contro la decisione di fallimento aperto nei confronti del titolare l'(?P<bankruptcy_date>{DATE})\. \[finora: Il titolare è stato dichiarato in fallimento con decreto della (?P<previous_court>{NAME}) del (?P<previous_decision_date>{DATE}) a far tempo dal (?P=bankruptcy_date) alle ore (?P<effective_time>\d{{2}}:\d{{2}})\.\]", 'it')
    if m:
        return [event('it.text.owner_bankruptcy_appeal_suspensive_effect.v1', m)], ''

    m = match(rf"La fondation est dissoute par décision de son autorité de surveillance du (?P<decision_date>{DATE})\. Liquidateurs: (?P<name1>{NAME}), maintenant domiciliée à (?P<place>{NAME}), présidente, (?P<name2>{NAME}), secrétaire, (?P<name3>{NAME}) et (?P<name4>{NAME}), lesquels continuent de signer collectivement à deux", 'fr')
    if m:
        rule = 'fr.text.foundation_dissolved_four_liquidators.v1'
        return [event(rule, m, dissolved=True)] + [person(rule, m, 'name' + str(i), 'Liquidator', 'Kollektivunterschrift zu zweien') for i in range(1, 5)], ''

    m = match(rf"L'associé-gérant (?P<transferor1>{NAME}) cède (?P<transferred1>{COUNT}) de ses (?P<previous1>{COUNT}) parts de CHF (?P<nominal>{MONEY}), par (?P<allocation1>{COUNT}) parts à (?P<recipient1>{NAME}), de et à (?P<place1>{NAME}), et par (?P<allocation2>{COUNT}) part à (?P<recipient2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), nouveaux associés-gérants avec signature collective à deux\. L'associée-gérante (?P<transferor2>{NAME}) cède (?P<transferred2>{COUNT}) de ses (?P<previous2>{COUNT}) parts de CHF (?P=nominal), par (?P<allocation3>{COUNT}) parts à (?P=recipient2), maintenant titulaires de (?P<recipient2_count>{COUNT}) parts de CHF (?P=nominal), et par (?P<allocation4>{COUNT}) parts à (?P<recipient3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), nouvel associé-gérant avec signature collective à deux\. (?P=transferor1) reste titulaires de (?P<remaining1>{COUNT}) parts de CHF (?P=nominal) et (?P=transferor2) de (?P<remaining2>{COUNT}) parts de CHF (?P=nominal)", 'fr')
    if m:
        n = lambda key: int(m[key].replace("'", ''))
        if (n('allocation1') + n('allocation2') != n('transferred1') or n('allocation3') + n('allocation4') != n('transferred2') or n('transferred1') + n('remaining1') != n('previous1') or n('transferred2') + n('remaining2') != n('previous2') or n('allocation2') + n('allocation3') != n('recipient2_count')):
            return [], leftover
        source_clause = f"à {m['place2']}, nouveaux associés-gérants avec signature collective à deux."
        if source_clause not in source_text:
            return [], leftover
        rule = 'fr.text.two_managers_shares_split_three_recipients.v1'
        return [event(rule, m)] + [person(rule, m, 'recipient' + str(i), 'Gesellschafter und Geschäftsführer', 'Kollektivunterschrift zu zweien') for i in range(1, 4)], ''

    return [], leftover
