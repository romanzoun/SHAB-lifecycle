from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser314_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete sample-backed clauses and preserve unsupported input."""
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

    def event(rule, m, kind='organization_changed', **extra):
        return _event(*context, kind, rule, {'action': rule.split('.')[2], **m.groupdict(), **extra})

    def person(rule, m, role, signing=None):
        return _person_event(*context, 'officer_changed', rule, m['name'], place=m.groupdict().get('place'), role=role, signing=signing, extra=m.groupdict())

    m = match(rf'Der Eintrag Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) \(SHAB vom (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\) ist wie folgt berichtigt: (?P<name>{NAME}), (?P<nationality>{NAME}) Staatsangehöriger, in (?P<place>{NAME}), Geschäftsführer, Einzelunterschrift \(nicht (?P<previous_nationality>{NAME}) Staatsangehöriger\)', 'de')
    if m:
        return [person('de.text.manager_nationality_corrected.v1', m, 'Geschäftsführer', 'Einzelunterschrift')], ''

    m = match(rf'Diese infolge Konkurses im Sinne von Art\. 159 Abs\. 5 lit\. a HRegV am (?P<deletion_date>{DATE}) von Amtes wegen gelöschte Gesellschaft wird wieder als durch Konkurs aufgelöst in das Handelsregister eingetragen, nachdem der Konkursrichter mit Verfügung vom (?P<decision_date>{DATE}) die Wiedereröffnung eines summarischen Verfahrens angeordnet hat', 'de')
    if m:
        return [event('de.text.bankruptcy_summary_proceedings_reopened.v1', m, dissolved_by_bankruptcy=True)], ''

    m = match(rf"Rectificatif: l'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que (?P<name>{NAME}) cède ses (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) \(et non ses (?P<previous_count>{COUNT}) parts de CHF (?P<previous_nominal>{MONEY}), comme publié\)", 'fr')
    if m:
        return [event('fr.text.transferred_share_nominal_corrected.v1', m)], ''

    m = match(rf"Suppression de la clause statutaire relative à l'augmentation autorisée du capital fondée sur la décision d'autorisation du (?P<authorization_date>{DATE}), le montant de l'augmentation ayant été atteint \[ou : le délai étant écoulé\]", 'fr')
    if m:
        return [event('fr.text.authorized_capital_deleted_amount_reached.v1', m)], ''

    m = match(rf'Nouvel administrateur avec signature collective à deux: (?P<name>{NAME}), de (?P<origin>{NAME}), au (?P<place>{NAME}) \((?P<country>{NAME})\)', 'fr')
    if m:
        return [person('fr.text.new_administrator_foreign_residence.v1', m, 'Mitglied des Verwaltungsrates', 'Kollektivunterschrift zu zweien')], ''

    m = match(rf"L'associé-gérant (?P<name>{NAME}) cède (?P<transferred_count>{COUNT}) de ses (?P<previous_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<recipient>{NAME}) \((?P<recipient_uid>{UID})\), à (?P<recipient_place>{NAME}), nouvelle associée\. (?P=name) reste titulaire de (?P<remaining_count>{COUNT}) parts de CHF (?P=nominal)", 'fr')
    if m:
        number = lambda key: int(m[key].replace("'", ''))
        if number('transferred_count') + number('remaining_count') != number('previous_count'):
            return [], leftover
        return [event('fr.text.partial_shares_transferred_legal_entity.v1', m)], ''

    m = match(rf"Vermögensübertragung: Der Geschäftsinhaber überträgt gemäss Vermögensübertragungsvertrag vom (?P<agreement_date>{DATE}) und Inventar per (?P<inventory_date>{DATE}) einen Teil der Aktiven in Höhe von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) in Höhe von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient>[^,;\n]+?), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: (?P<share_count>{COUNT}) zu 100% liberierte Namenaktien zu CHF (?P<nominal>{MONEY}) und eine Forderung von CHF (?P<claim>{MONEY})", 'de')
    if m:
        return [event('de.text.partial_assets_transferred_shares_claim.v1', m, fully_paid=True)], ''

    m = match(rf"Fusione: ripresa di attivi e passivi di (?P<absorbed_name>{NAME}), in (?P<place>{NAME}) \((?P<absorbed_uid>{UID})\), secondo il contratto di fusione del (?P<agreement_date>{DATE}) e bilancio al (?P<balance_date>{DATE}), che presenta attivi per CHF (?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY})\. La totalità del capitale delle due società è detenuta dalla stessa persona, la fusione avviene dunque senza aumento del capitale azionario e senza attribuzione di azioni", 'it')
    if m:
        return [event('it.text.merger_same_person_no_share_allocation.v1', m, 'company_merged', capital_increase=False, shares_allocated=False)], ''

    m = match(rf"Fusione: ripresa di attivi e passivi della (?P<absorbed_name>{NAME}) \((?P<absorbed_uid>{UID})\), in (?P<place>{NAME}), secondo il contratto di fusione del (?P<agreement_date>{DATE}) e bilancio al (?P<balance_date>{DATE}), che presenta attivi per CHF (?P<assets>{MONEY}), e passivi verso terzi per CHF (?P<liabilities>{MONEY})\. La totalità del capitale azionario delle due società è detenuta dallo stesso azionista, la fusione avviene dunque senza aumento di capitale e senza attribuzione di azioni", 'it')
    if m:
        return [event('it.text.merger_uid_before_place_common_shareholder.v1', m, 'company_merged', capital_increase=False, shares_allocated=False)], ''

    m = match(rf"Fusion : reprise des actifs et des passifs de la société « (?P<absorbed_name>{NAME}) », à (?P<place>{NAME}) \((?P<absorbed_uid>{UID})\), selon contrat de fusion du (?P<agreement_date>{DATE}) et bilan au (?P<balance_date>{DATE}), présentant des actifs de CHF (?P<assets>{MONEY}) et des passifs envers les tiers de CHF (?P<liabilities>{MONEY}), soit un excédent de passifs de CHF (?P<shortfall>{MONEY})\. Conformément à l'attestation d'un expert-réviseur agréé, le découvert et le surendettement de la société transférante sont couverts par une créance postposée et par des fonds propres librement disponibles de la société reprenante\. La totalité du capital-actions des deux sociétés étant détenue par la même actionnaire, la fusion ne donne pas lieu à une augmentation du capital, ni à une attribution d'actions", 'fr')
    if m:
        amount = lambda key: Decimal(m[key].replace("'", ''))
        if amount('liabilities') - amount('assets') != amount('shortfall'):
            return [], leftover
        return [event('fr.text.merger_shortfall_subordinated_claim_free_equity.v1', m, 'company_merged', capital_increase=False, shares_allocated=False, claims_subordinated=True)], ''

    m = match(rf"Fusion: Übernahme der Aktiven und Passiven \(Fremdkapital\) der (?P<absorbed_name>{NAME}), in (?P<place>{NAME}) \((?P<absorbed_uid>{UID})\), gemäss Fusionsvertrag vom (?P<agreement_date>{DATE}) und Bilanz per (?P<balance_date>{DATE})\. Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) gehen auf die übernehmende Gesellschaft über\. Da die übernehmende Gesellschaft sämtliche Stammanteile der übertragenden Gesellschaft hält, findet weder eine Kapitalerhöhung noch eine Zuteilung von Stammanteilen statt", 'de')
    if m:
        return [event('de.text.merger_wholly_owned_no_stammanteile.v1', m, 'company_merged', capital_increase=False, shares_allocated=False)], ''

    def merger_clause(i):
        return rf'Fusion: Übernahme der Aktiven und Passiven \(Fremdkapital\) der "(?P<absorbed_name{i}>[^"\n]+)" \((?P<absorbed_uid{i}>{UID})\) mit Sitz in (?P<place{i}>{NAME}), gemäss Fusionsvertrag vom (?P<agreement_date{i}>{DATE}) und Bilanz per (?P<balance_date{i}>{DATE})\. Aktiven von CHF (?P<assets{i}>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities{i}>{MONEY}) gehen auf die übernehmende Gesellschaft über\. Da derselbe Gesellschafter sämtliche Anteile der an der Fusion beteiligten Gesellschaften hält, findet weder eine Kapitalerhöhung noch eine Aktienzuteilung statt'

    m = match(merger_clause(1) + r'\. ' + merger_clause(2), 'de')
    if m:
        try:
            for i in (1, 2):
                for key in ('agreement_date', 'balance_date'):
                    datetime.strptime(m[f'{key}{i}'], '%d.%m.%Y')
        except ValueError:
            return [], leftover
        return [event('de.text.two_mergers_common_member_no_allocation.v1', m, 'company_merged', absorbed_uid=m[f'absorbed_uid{i}'], absorbed_name=m[f'absorbed_name{i}'], capital_increase=False, shares_allocated=False) for i in (1, 2)], ''

    return [], leftover
