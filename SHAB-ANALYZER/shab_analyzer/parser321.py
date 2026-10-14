from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, UID


def extract_parser321_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Only consume complete supported residual clauses after all legacy rules."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('_date'):
                        datetime.strptime(value.replace('-', '.'), '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(rule, m, kind='organization_changed', **extra):
        return _event(*context, kind, rule, {**m.groupdict(), 'action': rule.split('.')[2], **extra})

    def person(rule, m, key, role, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', rule, m[key], role=role, signing=signing, place=m[place] if place else None, extra=extra)

    m = match(rf"L'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée quant à l'orthographe du nom des")
    corrected = re.search(rf"personnes inscrites: (?P<name1>{NAME}), associé avec (?P<count>\d+) parts sociales de CHF (?P<nominal>{MONEY}), est gérant et président avec signature individuelle, et (?P<name2>{NAME}) est gérante avec signature individuelle\.$", source_text)
    if m and corrected:
        rule = 'fr.text.registered_names_correction_reference.v1'
        return [event(rule, m), person(rule, corrected, 'name1', 'Gesellschafter und Vorsitzender der Geschäftsführung', 'Einzelunterschrift', shares=corrected['count'], nominal=corrected['nominal']), person(rule, corrected, 'name2', 'Geschäftsführerin', 'Einzelunterschrift')], ''

    m = match(rf"L'inscription (?P<entry>\d+) du (?P<entry_date>\d{{2}}-\d{{2}}-\d{{4}}) est complétée en ce sens que la raison sociale redevient (?P<company_name>[^,]+), en liquidation")
    if m:
        return [event('fr.text.liquidation_company_name_restored.v1', m, 'company_name_changed', liquidation=True)], ''

    m = match(rf"L'inscription No (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que le nom de l'administrateur est (?P<name>[^()]+) \(et non pas (?P<previous_name>[^()]+)\)")
    if m:
        return [person('fr.text.administrator_spelling_corrected.v1', m, 'name', 'Mitglied des Verwaltungsrates', previous_name=m['previous_name'], entry=m['entry'], entry_date=m['entry_date'])], ''

    m = match(rf"Signature collective à deux est conférée à (?P<name1>{NAME}), à (?P<place1>{NAME}), et (?P<name2>{NAME}), à (?P<place2>{NAME}), tous deux d'(?P<origin>{NAME}), directeurs")
    if m:
        rule = 'fr.text.two_directors_joint_signing_different_places.v1'
        return [person(rule, m, 'name'+str(i), 'Direktor', 'Kollektivunterschrift zu zweien', 'place'+str(i), origin=m['origin']) for i in (1, 2)], ''

    m = match(rf'Signature individuelle ou collective à deux a été conférée à (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), directeur')
    if m:
        return [person('fr.text.director_alternative_signing.v1', m, 'name', 'Direktor', 'Einzelunterschrift oder Kollektivunterschrift zu zweien', 'place', origin=m['origin'])], ''

    m = match(rf"(?P<name1>{NAME}), jusqu'ici président, et (?P<name2>{NAME}), maintenant domicilié à (?P<place>{NAME}), nommé président, tous deux membres du conseil de fondation, continuent de signer collectivement à deux")
    if m:
        rule = 'fr.text.foundation_chair_change_joint_signing.v1'
        return [person(rule, m, 'name1', 'Mitglied des Stiftungsrates', 'Kollektivunterschrift zu zweien', previous_role='Präsident des Stiftungsrates'), person(rule, m, 'name2', 'Präsident des Stiftungsrates', 'Kollektivunterschrift zu zweien', 'place')], ''

    m = match(rf"Vermögensübertragung: Die Gesellschaft überträgt gemäss Vermögensübertragungsvertrag vom (?P<agreement_date>{DATE}) und Inventar per (?P<inventory_date>{DATE}) Aktiven von (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient>[^,]+), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: CHF (?P<consideration>{MONEY})", 'de')
    if m:
        return [event('de.text.asset_transfer_assets_without_currency.v1', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf"Suppression de la clause statutaire relative à l'augmentation autorisée du capital-actions, fondée sur la décision d'autorisation du (?P<authorization_date>{DATE}) \. Par décision du (?P<decision_date>{DATE}), l'assemblée générale a introduit une nouvelle clause d'augmentation autorisée du capital-actions, pour les détails, cf\. statuts")
    if m:
        return [event('fr.text.authorized_capital_clause_replaced.v1', m, 'capital_changed', previous_clause_removed=True, new_clause_introduced=True)], ''

    # The earlier translation event remains intact; this adds the complete names.
    m = match(r'\) \((?P<italian>Accademia [^()]+ \(ASSM\))\) \((?P<english>Swiss Academy [^()]+ \(SAMS\))\)', 'de')
    translations = re.search(r'Uebersetzungen des Namens neu: \((?P<french>[^()]+ \(ASSM\))\)', source_text)
    if m and translations:
        return [event('de.text.nested_name_translations_completed.v1', m, 'company_name_changed', french=translations['french'])], ''

    m = match(rf"(?P<seller>{NAME}), associé-gérant président, cède (?P<transferred>\d+) de ses (?P<before>\d+) parts de CHF (?P<nominal>{MONEY}), par (?P<each>\d+) parts de CHF (?P=nominal), chacun, à (?P<buyer1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), et (?P<buyer2>{NAME}), d'(?P<origin2>{NAME}), à (?P<place2>{NAME}), nouveaux associés, chacun avec (?P=each) parts de CHF (?P=nominal), sans signature\. (?P=seller) reste titulaire de (?P<remaining>\d+) parts de CHF (?P=nominal)")
    if m:
        if int(m['transferred']) != 2 * int(m['each']) or int(m['before']) - int(m['transferred']) != int(m['remaining']):
            return [], leftover
        rule = 'fr.text.two_unsigned_associates_share_transfer.v1'
        return [event(rule, m, 'ownership_changed', currency='CHF')] + [person(rule, m, 'buyer'+str(i), 'Gesellschafter', 'ohne Zeichnungsberechtigung', 'place'+str(i), origin=m['origin'+str(i)]) for i in (1, 2)], ''

    m = match(rf"L'associé-gérant (?P<seller>{NAME}) cède (?P<transferred>\d+) de ses (?P<before>\d+) parts de CHF (?P<nominal>{MONEY}), par (?P<each>\d+) parts à (?P<buyer1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), et par (?P=each) parts de CHF (?P=nominal) à (?P<buyer2>{NAME}), de et à (?P<place2>{NAME}), nouveaux associés avec (?P=each) parts de CHF (?P=nominal) chacun, gérants (?P=seller), qui est élu président des gérants et continue à signer individuellement, reste titulaire de (?P<remaining>\d+) parts de CHF (?P=nominal)")
    if m and 'gérants avec signature collective à deux.' in source_text:
        if int(m['transferred']) != 2 * int(m['each']) or int(m['before']) - int(m['transferred']) != int(m['remaining']):
            return [], leftover
        rule = 'fr.text.two_new_managers_share_transfer.v1'
        return [event(rule, m, 'ownership_changed', currency='CHF'), person(rule, m, 'seller', 'Vorsitzender der Geschäftsführung', 'Einzelunterschrift')] + [person(rule, m, 'buyer'+str(i), 'Gesellschafter und Geschäftsführer', 'Kollektivunterschrift zu zweien', 'place'+str(i)) for i in (1, 2)], ''

    m = match(rf"Fusion : reprise des actifs et des passifs de la société « (?P<absorbed>[^«»]+) », à (?P<place>{NAME}) \((?P<absorbed_uid>{UID})\), selon contrat de fusion du (?P<agreement_date>{DATE}) et bilan au (?P<balance_date>{DATE}), présentant des actifs de CHF (?P<assets>{MONEY}) et des passifs envers les tiers de CHF (?P<liabilities>{MONEY}), soit un excédent de passifs de CHF (?P<deficit>{MONEY})\. Conformément à l'attestation de l'entreprise de révision soumise à la surveillance de l'Etat, le découvert et le surendettement de la société transférante sont couverts par une créance postposée de CHF (?P<subordinated_claim>{MONEY}) et par des fonds propres librement disponibles de la société reprenante\. La totalité du capital-actions de la société reprenante et (?P<ownership_percent>\d+)% du capital-actions de la société transférante étant détenue par la même actionnaire, la fusion ne donne pas lieu à une augmentation du capital, ni à une attribution d'actions\. Les actionnaires minoritaires de la société transférante reçoivent un dédommagement de CHF (?P<compensation_per_share>{MONEY}) par action nominative")
    if m:
        amount = lambda key: Decimal(m[key].replace("'", ''))
        if amount('liabilities') - amount('assets') != amount('deficit') or not 0 < int(m['ownership_percent']) < 100:
            return [], leftover
        return [event('fr.text.merger_subordination_minority_compensation.v1', m, currency='CHF', capital_increase=False, share_allocation=False)], ''

    return [], leftover
