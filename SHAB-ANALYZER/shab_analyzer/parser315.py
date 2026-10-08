from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser315_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
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
            except ValueError:
                return None
        return m

    def amount(m, key):
        return Decimal(m[key].replace("'", ''))

    def event(rule, m, kind='organization_changed', **extra):
        return _event(*context, kind, rule, {'action': rule.split('.')[2], **m.groupdict(), **extra})

    def person(rule, m, key, role, signing=None, place_key=None):
        return _person_event(*context, 'officer_changed', rule, m[key], place=m[place_key] if place_key else None, role=role, signing=signing, extra=m.groupdict())

    m = match(r'Die Eintragung des Verzichts auf die eingeschränkte Revision erfolgte irrtümlich, da eine Revisionsstelle gewählt worden ist\. \[Der Verzicht auf eine eingeschränkte Revision wird gestrichen\.\]', 'de')
    if m:
        return [event('de.text.erroneous_audit_waiver_deleted.v1', m, audit_waiver=False)], ''

    m = match(rf'\[finora: Con dichiarazione del consiglio di amministrazione del (?P<declaration_date>{DATE}), la società non è soggetta alla revisione ordinaria e rinuncia a una revisione limitata\.\]', 'it')
    if m:
        return [event('it.text.previous_audit_waiver_deleted.v1', m, audit_waiver=False)], ''

    m = match(rf"Radiation de la mention relative à la renonciation à l'organe de révision\. Rrgane de révision: (?P<auditor>{NAME}) \((?P<auditor_uid>{UID})\), à (?P<place>{NAME})", 'fr')
    if m:
        return [event('fr.text.audit_waiver_deleted_auditor_typo.v1', m, audit_waiver=False)], ''

    m = match(rf"La raison de commerce et le numéro d'identification de l'unique associée (?P<previous_name>[^;\n]+?) sont maintenent (?P<name>[^;\n]+?) \((?P<registration_number>\d+)\)", 'fr')
    if m:
        return [event('fr.text.sole_associate_name_number_changed_typo.v1', m)], ''

    m = match(rf"(?P<name>{NAME}) cède (?P<transferred_count>{COUNT}) de ses (?P<previous_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<recipient>{NAME}), d'(?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé sans signature\. (?P=name) reste titulaire de (?P<remaining_count>{COUNT}) parts de CHF (?P=nominal)", 'fr')
    if m:
        if amount(m, 'transferred_count') + amount(m, 'remaining_count') != amount(m, 'previous_count'):
            return [], leftover
        rule = 'fr.text.partial_shares_transferred_unsigned_associate.v1'
        return [event(rule, m), person(rule, m, 'recipient', 'Gesellschafter', 'ohne Zeichnungsberechtigung', 'place')], ''

    m = match(rf"(?P<name>{NAME}), associée-gérante, cède (?P<transferred_count>{COUNT}) de ses (?P<previous_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<recipient>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé avec (?P=transferred_count) parts de CHF (?P=nominal), gérant avec signature collective à deux\. (?P=name), qui reste titulaire de (?P<remaining_count>{COUNT}) parts de CHF (?P=nominal), est nommée présidente; elle continue de signer individuellement", 'fr')
    if m:
        if amount(m, 'transferred_count') + amount(m, 'remaining_count') != amount(m, 'previous_count'):
            return [], leftover
        rule = 'fr.text.partial_shares_transferred_manager_president.v1'
        return [event(rule, m), person(rule, m, 'recipient', 'Gesellschafter und Geschäftsführer', 'Kollektivunterschrift zu zweien', 'place'), person(rule, m, 'name', 'Vorsitzende der Geschäftsführung', 'Einzelunterschrift')], ''

    m = match(rf'Administration: (?P<name1>{NAME}), des (?P<origin1>{NAME}), à (?P<place1>{NAME}), président, et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), lesquels signent individuellement', 'fr')
    if m:
        rule = 'fr.text.two_administrators_individual_signing.v1'
        return [person(rule, m, 'name1', 'Präsident des Verwaltungsrates', 'Einzelunterschrift', 'place1'), person(rule, m, 'name2', 'Mitglied des Verwaltungsrates', 'Einzelunterschrift', 'place2')], ''

    m = match(rf"Le membre du conseil (?P<name1>{NAME}), jusqu'ici trésorier, n'exerce plus la signature sociale\. (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), trésorière, avec signature collective à deux et (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), sans signature sont membres du conseil", 'fr')
    if m:
        rule = 'fr.text.board_treasurer_signing_revoked_members_added.v1'
        return [person(rule, m, 'name1', 'Mitglied des Vorstandes', 'ohne Zeichnungsberechtigung'), person(rule, m, 'name2', 'Mitglied des Vorstandes und Kassierin', 'Kollektivunterschrift zu zweien', 'place2'), person(rule, m, 'name3', 'Mitglied des Vorstandes', 'ohne Zeichnungsberechtigung', 'place3')], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) ohne Passiven auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung CHF (?P<consideration>{MONEY})', 'de')
    if m:
        return [event('de.text.assets_transferred_without_liabilities.v1', m, liabilities='0')], ''

    m = match(rf'Fusion: Übernahme der Aktiven und Passiven der (?P<absorbed_name>{NAME}), in (?P<place>{NAME}) \((?P<absorbed_uid>{UID}), gemäss Fusionsvertrag vom (?P<agreement_date>{DATE}) und Bilanz per (?P<balance_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von (?P<liabilities>{MONEY}) gehen auf die übernehmende Gesellschaft über\. Da dieselben Aktionäre sämtliche Aktien der an der Fusion beteiligten Gesellschaften halten, findet weder eine Kapitalerhöhung noch eine Aktienzuteilung statt', 'de')
    if m:
        return [event('de.text.merger_common_shareholders_missing_punctuation.v1', m, 'company_merged', capital_increase=False, shares_allocated=False)], ''

    m = match(rf"(?P<resolution_date>{DATE})\. Réduction du capital-actions de CHF (?P<previous_capital>{MONEY}) à CHF (?P<reduced_capital>{MONEY}) par destruction de (?P<count>{COUNT}) actions nominatives de CHF (?P<nominal>{MONEY}), liées selon statuts, entièrement libérées et simultanément augmentation ordinaire du capital par compensation de créance d'un montant total de CHF (?P<claim>{MONEY}), contre remise en échange de (?P=count) actions nominatives de CHF (?P=nominal), liées selon statuts, entièrement libérées", 'fr')
    if m:
        reduction = amount(m, 'previous_capital') - amount(m, 'reduced_capital')
        if reduction != amount(m, 'count') * amount(m, 'nominal') or reduction != amount(m, 'claim'):
            return [], leftover
        return [event('fr.text.capital_reduced_increased_claim_offset.v1', m, fully_paid=True)], ''

    m = match(rf'Aktienkapital neu: CHF (?P<capital>{MONEY}) \[bisher: CHF (?P=capital)\]\. Liberierung Aktienkapital neu: CHF (?P=capital) \[bisher: CHF (?P=capital)\]\. Aktien neu: (?P<count>{COUNT}) Namenaktien zu CHF (?P<nominal>{MONEY}) \[bisher: (?P=count) Namenaktien zu CHF (?P=nominal)\]\. Bei der Kapitalherabsetzung vom (?P<reduction_date>{DATE}) wird der Nennwert der (?P=count) Namenaktien zu CHF (?P=nominal) auf CHF (?P<reduced_nominal>0\.00) herabgesetzt\. Gleichzeitig wird bei der Kapitalerhöhung vom (?P<increase_date>{DATE}) der Nennwert dieser Aktien auf CHF (?P=nominal) erhöht\. Bei der ordentlichen Kapitalerhöhung vom (?P<offset_date>{DATE}) werden Forderungen in der Höhe von CHF (?P<claim>{MONEY}) verrechnet', 'de')
    if m:
        if amount(m, 'capital') != amount(m, 'count') * amount(m, 'nominal'):
            return [], leftover
        return [event('de.text.capital_nominal_zero_restored_claim_offset.v1', m, fully_paid=True)], ''

    return [], leftover
