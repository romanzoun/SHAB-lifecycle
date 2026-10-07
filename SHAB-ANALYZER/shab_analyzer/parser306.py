from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event, _french_date
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser306_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
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

    m = match(rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que le capital est porté de CHF (?P<previous_capital>{MONEY}) à CHF (?P<capital>{MONEY}) par l'émission de (?P<issued>{COUNT}) parts de CHF (?P<nominal>{MONEY}) avec obligation de fournir des prestations accessoires, droits de préférence, de préemption ou d'emption selon statuts, entièrement libérées en espèces, souscrites à concurrence de (?P<subscription1>{COUNT}) parts de CHF (?P=nominal) par l'associé-gérant (?P<name1>{NAME}), qui possède désormais (?P<count1>{COUNT}) parts de CHF (?P=nominal), à concurrence de (?P<subscription2>{COUNT}) parts de CHF (?P=nominal) à (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}) nouvel associé pour de (?P=subscription2) parts de CHF (?P=nominal), et à concurrence de (?P<subscription3>{COUNT}) parts de CHF (?P=nominal) à (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), nouvel associé pour de (?P=subscription3) parts de CHF (?P=nominal)", 'fr')
    if m:
        return [event('fr.text.capital_subscription_corrected.v1', m)], ''

    m = match(rf"Con decisione del Dipartimento federale dell'intero in (?P<authority_place>{NAME}) del (?P<decision_date>{DATE}) è stata constatata la conclusione della liquidazione, ma la cancellazione non può essere effettuata mancando il consenso delle autorità fiscali federali e cantonali", 'it')
    if m:
        return [event('it.text.liquidation_completed_tax_consent_pending.v1', m)], ''

    m = match(rf"Par décision rendue le (?P<decision_date>(?:1er|\d{{1,2}}) (?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre) \d{{4}}), le président du Tribunal de l'arrondissement de (?P<district>{NAME}) a constaté que la procédure de liquidation du concordat est terminée", 'fr')
    if m:
        return [event('fr.text.composition_liquidation_completed.v1', m)], ''

    m = match(rf'(?P<name>{NAME}) maintenant domiciliée à (?P<place>{NAME}), (?P<country>[A-Z]{{3}})', 'fr')
    if m:
        return [person('fr.text.officer_domicile_country_changed.v1', m, place=m['place'])], ''

    m = match(rf"Con decreto della Pretura del Distretto di (?P<district>{NAME}) del (?P<decision_date>{DATE}) è stato omologato il concordato ordinario concluso tra la società e i suoi creditori\. L'esecuzione del concordato viene affidata al commissario, il quale potrà prendere tutti i provvedimenti necessari per l'esecuzione e garantirne l'adempimento\. \[finora: Con decreto della Pretura del Distretto di (?P=district) del (?P<previous_date>{DATE}), alla società è stata concessa una moratoria a scopo di concordato di (?P<months>{COUNT}) mesi\.\]", 'it')
    if m:
        return [event('it.text.ordinary_composition_approved.v1', m)], ''

    m = match(rf"L'inscription N°(?P<entry>{COUNT}) du (?P<entry_date>{DATE}) a été modifiée comme suit: (?P<name>{NAME}) est associé pour (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) \(et non de CHF (?P<previous_nominal>{MONEY})\) à droit de vote privilégié", 'fr')
    if m:
        return [event('fr.text.preferred_share_nominal_corrected.v1', m)], ''

    m = match(rf'Succursale: (?P<place>{NAME}) \((?P<uid>{UID})\) \[finora: (?P<previous_place>{NAME})\]', 'it')
    if m:
        return [event('it.text.branch_place_changed.v1', m)], ''

    m = match(rf'Gegen die Löschung von Amtes wegen gemäss Art\. (?P<article>159 Abs\. 5 lit\. a HRegV) wurde begründeter Einspruch erhoben', 'de')
    if m:
        return [event('de.text.official_deletion_opposed.v1', m)], ''

    m = match(rf'Nouvel associé indéfiniment responsable: (?P<name>{NAME}), de et à (?P<place>{NAME}) avec signature collective à deux', 'fr', rf'Nouvel associé indéfiniment responsable: (?P<name>{NAME}), de et à (?P<place>{NAME}) avec signature collective à deux')
    if m:
        return [person('fr.text.unlimited_partner_collective_signing.v1', m, place=m['place'], role='associé indéfiniment responsable', signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE})\) est rectifiée en se cens que dans le but convient de lire (?P<wording>{NAME}) et non (?P<previous_wording>{NAME})", 'fr', rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE})\) est rectifiée en se cens que dans le but il convient de lire (?P<wording>{NAME}) et non (?P<previous_wording>{NAME})")
    if m:
        return [event('fr.text.purpose_wording_corrected.v1', m)], ''

    m = match(rf'Das Bundesgericht hat mit Verfügung vom (?P<decision_date>{DATE}) der Beschwerde gegen das Urteil des Obergerichts des Kantons (?P<court_canton>{NAME}) vom (?P<judgment_date>{DATE}) betreffend Konkurseröffnung superprovisorisch aufschiebende Wirkung in dem Sinne zuerkannt, als der Konkurs eröffnet bleibt, jedoch bis zum Entscheid des Bundesgerichts Vollstreckungsmassnahmen zu unterbleiben haben, mit anderen Worten das Konkursverfahren nicht gefördert werden darf, aber bereits getroffene Sicherungsmassnahmen aufrecht erhalten bleiben', 'de')
    if m:
        return [event('de.text.bankruptcy_enforcement_provisionally_suspended.v1', m)], ''

    m = match(rf"Par ordonnance du (?P<decision_date>{DATE}), le Tribunal cantonal a suspendu l'exécution du jugement de faillite rendu le (?P<judgment_date>{DATE})\. Par conséquent sa raison sociale redevient: (?P<business>{NAME})", 'fr')
    if m:
        return [event('fr.text.bankruptcy_execution_suspended_name_restored.v1', m)], ''

    return [], leftover
