from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser313_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete sample-backed clauses; retain unsupported input atomically."""
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

    def people(rule, m, roles, signing):
        return [_person_event(*context, 'officer_changed', rule, m[f'name{i}'], place=m.groupdict().get(f'place{i}'), role=role, signing=signing, extra=m.groupdict()) for i, role in enumerate(roles, 1)]

    m = match(rf"Les membres du conseil (?P<name1>{NAME}), maintenant domicilié à (?P<place1>{NAME}), jusqu'ici vice-président, nommé président, et (?P<name2>{NAME}), jusqu'ici président, nommé vice-président, continuent à signer individuellement", 'fr')
    if m:
        if not source_text.startswith('Fondation '):
            return [], leftover
        return people('fr.text.council_president_vice_president_swap.v1', m, ['Mitglied des Stiftungsrates, Präsident', 'Mitglied des Stiftungsrates, Vizepräsident'], 'Einzelunterschrift'), ''

    m = match(rf'(?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), sont membres du comité avec signature collective à deux', 'fr')
    if m:
        return people('fr.text.two_committee_members_distinct_places.v1', m, ['Mitglied des Vorstandes'] * 2, 'Kollektivunterschrift zu zweien'), ''

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat der Einzelrichter am Kantonsgericht eine COVID-19-Stundung von (?P<months>{COUNT}) Monaten gemäss der COVID-19-Verordnung Insolvenzrecht bewilligt', 'de')
    if m:
        return [event('de.text.covid19_deferral_granted.v1', m)], ''

    m = match(rf"Les associés gérants (?P<name1>{NAME}), nommé président, et (?P<name2>{NAME}), jusqu'ici présidente, continuent à signer individuellement", 'fr')
    if m:
        return people('fr.text.associate_managers_presidency_changed.v1', m, ['Gesellschafter und Geschäftsführer, Präsident', 'Gesellschafterin und Geschäftsführerin'], 'Einzelunterschrift'), ''

    m = match(rf"(?P<name1>{NAME}), d'(?P<origin1>{NAME}), à (?P<place1>{NAME}), président et (?P<name2>{NAME}), d'(?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<country2>[A-Z]{{3}}), sont membres du conseil d'administration, avec signature individuelle", 'fr')
    if m:
        return people('fr.text.two_administrators_foreign_place.v1', m, ['Mitglied des Verwaltungsrates, Präsident', 'Mitglied des Verwaltungsrates'], 'Einzelunterschrift'), ''

    m = match(rf'Liquidateurs: les gérants (?P<name1>{NAME}) et (?P<name2>{NAME}), lesquels continuent à signer indidivuellement', 'fr')
    if m:
        return people('fr.text.two_manager_liquidators_signing_typo.v1', m, ['Geschäftsführer und Liquidator'] * 2, 'Einzelunterschrift'), ''

    m = match(rf"L'inscription no\. (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(publication FOSC du (?P<notice_date>{DATE}) page (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que l'associé-gérant et président (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), détient (?P<count1>{COUNT}) parts de CHF (?P<nominal1>{MONEY}) \(et non: (?P<previous_count>{COUNT}) parts de CHF (?P<previous_nominal>{MONEY})\), et la gérante (?P<name2>[^,;]+?), de (?P<origin2>{NAME}), à (?P<place2>{NAME}) est également associée pour (?P<count2>{COUNT}) parts de CHF (?P<nominal2>{MONEY})", 'fr')
    if m:
        return people('fr.text.associate_holdings_corrected_manager_added.v1', m, ['Gesellschafter und Geschäftsführer, Präsident', 'Gesellschafterin und Geschäftsführerin'], None), ''

    m = match(rf'\[gestrichen: Die Generalversammlung hat mit Beschluss vom (?P<previous_date>{DATE}) den Beschluss über die Ermächtigung einer genehmigten Kapitalerhöhung vom (?P<original_date>{DATE}) gemäss näherer Umschreibung in den Statuten angepasst\.\]\. Die Generalversammlung hat mit Beschluss vom (?P<resolution_date>{DATE}) den Beschluss über die Ermächtigung einer genehmigten Kapitalerhöhung vom (?P=previous_date) gemäss näherer Umschreibung in den Statuten angepasst\. \[gestrichen: Die Generalversammlung hat mit Beschluss vom (?P=previous_date) die Statutenbestimmung über die bedingte Kapitalerhöhung vom (?P=original_date) geändert\.\]\. Die Generalversammlung hat mit Beschluss vom (?P=resolution_date) die Statutenbestimmung über die bedingte Kapitalerhöhung vom (?P=previous_date) geändert', 'de')
    if m:
        return [event('de.text.authorized_conditional_capital_resolutions_replaced.v1', m)], ''

    m = match(rf'\[Streichung der Statutenbestimmung über die mit Ermächtigungsbeschluss vom (?P<authorization_date>{DATE}) eingeführte genehmigte Kapitalerhöhung infolge Fristablauf\.\] \. Die Gesellschaft hat mit Beschluss vom (?P<resolution_date>{DATE}) eine genehmigte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten beschlossen', 'de')
    if m:
        return [event('de.text.expired_authorized_capital_replaced.v1', m)], ''

    m = match(rf'eingetragenen Einzelunternehmens "(?P<business>[^"\n]+)", in (?P<place>{NAME}), gemäss Vertrag vom (?P<agreement_date>{DATE}) und Übernahmebilanz per (?P<balance_date>{DATE}) mit Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) im Wert und zum Preis von CHF (?P<price>{MONEY}) übernommen', 'de')
    if m:
        prefix = 'Die Gesellschaft hat in Realisierung der bei der Gründung nicht offen gelegten Absicht das Geschäft des nicht im Handelsregister '
        if prefix + leftover not in source_text:
            return [], leftover
        return [event('de.text.undisclosed_intent_unregistered_business_acquired.v1', m, registered=False, intent_disclosed_at_formation=False)], ''

    m = match(rf'Les associés (?P<name1>{NAME}), (?P<name2>{NAME}) et (?P<name3>{NAME}), nommés gérants, continuent à signer collectviement à deux', 'fr')
    if m:
        return people('fr.text.three_associates_managers_signing_typo.v1', m, ['Gesellschafter und Geschäftsführer'] * 3, 'Kollektivunterschrift zu zweien'), ''

    m = match(rf"Fusione: secondo il contratto di fusione del (?P<agreement_date>{DATE}) e bilancio al (?P<balance_date>{DATE}) ripresa di attivi e passivi di (?P<absorbed_name1>{NAME}), in (?P<place1>{NAME}) \((?P<absorbed_uid1>{UID})\), che presenta attivi per CHF (?P<assets1>{MONEY}), nei quali sono comprese tutte le azioni della società assuntrice, e passivi verso terzi per CHF (?P<liabilities1>{MONEY}), con uno scoperto di CHF (?P<shortfall1>{MONEY}) e ripresa di attivi e passivi di (?P<absorbed_name2>{NAME}), in (?P<place2>{NAME}) \((?P<absorbed_uid2>{UID})\), che presenta attivi per CHF (?P<assets2>{MONEY}) e passivi verso terzi per CHF (?P<liabilities2>{MONEY}), con un'eccedenza passiva di CHF (?P<shortfall2>{MONEY})\. Conformemente all'attestazione di un perito revisore abilitato, dei crediti per un ammontare almeno equivalente allo scoperto, rispettivamente ai sovraindebitamenti delle società trasferenti e della società assuntrice, sono stati postergati\. La fusione avviene senza aumento di capitale visto che gli azionisti della società trasferente a seguito della fusione ricevono le azioni proprie della società assuntrice e visto che la totalità del capitale azionario delle altre società è detenuta dallo stesso azionista", 'it')
    if m:
        rule = 'it.text.two_mergers_subordination_own_shares.v1'
        return [event(rule, m, 'company_merged', absorbed_uid=m[f'absorbed_uid{i}'], absorbed_name=m[f'absorbed_name{i}'], capital_increase=False, claims_subordinated=True) for i in (1, 2)], ''

    return [], leftover
