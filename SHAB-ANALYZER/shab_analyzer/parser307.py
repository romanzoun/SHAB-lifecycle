from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event, _french_date
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser307_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete sample-backed clauses, preserving unsupported input."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang, source_pattern=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m and source_pattern:
            source = re.search(source_pattern + r'\.?$', source_text)
            if not source or any(source[k] != v for k, v in m.groupdict().items()):
                return None
            m = source
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('_date'):
                        datetime.fromisoformat(_french_date(value)) if ' ' in value else datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(rule, m):
        return _event(*context, 'organization_changed', rule, {'action': rule.split('.')[2], **m.groupdict()})

    def person(rule, m, key='name', **kwargs):
        return _person_event(*context, 'officer_changed', rule, m[key], extra=m.groupdict(), **kwargs)

    m = match(rf"""Der Einzelrichter des Bezirksgerichts (?P<district>{NAME}), Abteilung (?P<division>{COUNT}), hat mit Entscheid vom (?P<decision_date>{DATE}) den ordentlichen Nachlassvertrag genehmigt\. Für den Vollzug des Nachlassvertrages wird die eingesetzte Sachwalterin (?P<executor>{NAME}) \((?P<executor_uid>{UID})\), (?P<street>{NAME}), (?P<postal_code>\d{{4}}) (?P<place>{NAME}), Patentträger (?P<representatives>{NAME}), beauftragt""", 'de')
    if m:
        return [event('de.text.ordinary_composition_approved_executor.v1', m)], ''

    m = match(rf"""Par arrêt du (?P<decision_date>{DATE}), la Cour de justice a constaté la nullité du jugement de faillite du (?P<judgment_date>{DATE})\. Par conséquent, le titulaire est réinscrit et le prononcé de la faillite, de même que sa suspension et la radiation d'office sont radiées""", 'fr')
    if m:
        return [event('fr.text.bankruptcy_nullity_holder_reinstated.v1', m)], ''

    m = match(rf"""La publication N°(?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que la commune de domicile de (?P<name>{NAME}) est (?P<place>{NAME}) \(et non pas (?P<previous_place>{NAME})\)""", 'fr')
    if m:
        return [person('fr.text.officer_domicile_corrected.v1', m, place=m['place'])], ''

    m = match(rf"""(?P<seller1>{NAME}) \((?P<seller1_uid>{UID})\) et (?P<seller2>{NAME}) \((?P<seller2_uid>{UID})\), qui ne sont plus associées, cèdent chacune leurs (?P<transferred_each>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}) \((?P<buyer_uid>{UID})\), à (?P<place>{NAME}), nouvelle associée, titulaire de (?P<count>{COUNT}) parts de CHF (?P=nominal)""", 'fr')
    if m:
        return [event('fr.text.two_corporate_partners_shares_transferred.v1', m)], ''

    m = match(rf"""Nouvelle gérante: (?P<name>{NAME}), d'(?P<origin>{NAME}), à (?P<place>{NAME}), (?P<region>[A-Z]{{2}}) (?P<country>[A-Z]{{3}})(?: avec signature individuelle)?""", 'fr', rf"""Nouvelle gérante: (?P<name>{NAME}), d'(?P<origin>{NAME}), à (?P<place>{NAME}), (?P<region>[A-Z]{{2}}) (?P<country>[A-Z]{{3}}) avec signature individuelle""")
    if m:
        return [person('fr.text.manager_foreign_domicile_individual_signing.v1', m, place=m['place'], role='gérante', signing='Einzelunterschrift')], ''

    m = match(rf"""(?P<seller>{NAME}) cède (?P<transferred>{COUNT}) de ses (?P<previous_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<name>{NAME}), d'(?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée avec (?P=transferred) part de CHF (?P=nominal), sans signature\. (?P=seller) est désormais titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)""", 'fr')
    if m:
        return [event('fr.text.partial_share_transfer_unsigned_partner.v1', m)], ''

    m = match(rf"""\[gestrichen: Gemäss Erklärung der Geschäftsführung vom (?P<declaration_date>{DATE}) untersteht die Gesellschaft der ordentlichen Revision nicht und verzichtet auf eine eingeschränkte Revision\.\]""", 'de')
    if m:
        return [event('de.text.audit_opt_out_deleted.v1', m)], ''

    m = match(rf"""Création autorisée d'un capital-participation fondée sur la décision d'autorisation du (?P<authorization_date>(?:1er|\d{{1,2}}) (?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre) \d{{4}})\. Capital-participation entièrement libéré: CHF (?P<capital>{MONEY}), divisé en (?P<count>{COUNT}) bons de participation nominatifs de CHF (?P<nominal>{MONEY}), (?:avec restrictions quant à la transmissibilité selon statuts\. )?Le conseil d'administration a modifié une clause statutaire relative à la création autorisée d'un capital-participation \(selon décision d'autorisation de l'assemblée générale du (?P=authorization_date)\) par décision du (?P<decision_date>(?:1er|\d{{1,2}}) (?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre) \d{{4}})\. Pour les détails, voir les statuts""", 'fr', rf"""Création autorisée d'un capital-participation fondée sur la décision d'autorisation du (?P<authorization_date>(?:1er|\d{{1,2}}) (?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre) \d{{4}})\. Capital-participation entièrement libéré: CHF (?P<capital>{MONEY}), divisé en (?P<count>{COUNT}) bons de participation nominatifs de CHF (?P<nominal>{MONEY}), avec restrictions quant à la transmissibilité selon statuts\. Le conseil d'administration a modifié une clause statutaire relative à la création autorisée d'un capital-participation \(selon décision d'autorisation de l'assemblée générale du (?P=authorization_date)\) par décision du (?P<decision_date>(?:1er|\d{{1,2}}) (?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre) \d{{4}})\. Pour les détails, voir les statuts""")
    if m:
        return [event('fr.text.authorized_participation_capital_clause_changed.v1', m)], ''

    m = match(rf"""Vermögensübertragung: Die Aktiengesellschaft überträgt gemäss Vertrag vom (?P<contract_date>{DATE}) (?P<count>{COUNT}) Namenaktien zu CHF (?P<nominal>{MONEY}) der "(?P<issuer>{NAME})" \((?P<issuer_uid>{UID})\), in (?P<issuer_place>{NAME}), auf die "(?P<recipient>{NAME})" \((?P<recipient_uid>{UID})\), in (?P<recipient_place>{NAME}), zum Preis von CHF (?P<price>{MONEY})\. Gegenleistung: keine""", 'de')
    if m:
        return [event('de.text.registered_shares_asset_transfer_no_consideration.v1', m)], ''

    m = match(rf"""Mit Urteil vom (?P<decision_date>{DATE}) hat die Einzelrichterin im summarischen Verfahren des Bezirksgerichts (?P<district>{NAME}) die gewährte definitive Nachlassstundung um (?P<months>sechs) Monate bis (?P<end_date>{DATE}) verlängert""", 'de')
    if m:
        return [event('de.text.definitive_composition_moratorium_extended.v1', m)], ''

    m = match(rf"""(?P<name>{NAME}), nommé vice-président du conseil, signe désormais collectivement à deux""", 'fr')
    if m:
        return [person('fr.text.vice_president_collective_signing.v1', m, role='vice-président du conseil', signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf"""\[gestrichen: Die Generalversammlung hat mit Beschluss vom (?P<previous_date>{DATE}) die mit Beschluss vom (?P<original_date>{DATE}) geänderte genehmigte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten angepasst\.\]\. Die Generalversammlung hat mit Beschluss vom (?P<decision_date>{DATE}) die mit Beschluss vom (?P=previous_date) geänderte genehmigte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten angepasst""", 'de')
    if m:
        return [event('de.text.authorized_capital_increase_amendment_replaced.v1', m)], ''

    return [], leftover
