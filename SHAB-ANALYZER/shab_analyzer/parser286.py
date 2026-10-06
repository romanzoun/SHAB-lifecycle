from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser286_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Extract fixture-backed complete clauses; retain unsupported or invalid residue."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', *, signed=False):
        if language != lang:
            return None
        candidate = leftover.removesuffix(' avec signature individuelle') if signed else leftover
        m = re.fullmatch(pattern + r'\.?', candidate)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(rule, **kw):
        return _event(*context, 'organization_changed', rule, kw)

    def person(rule, name, **kw):
        return _person_event(*context, 'officer_changed', rule, name, **kw)

    def number(value):
        return Decimal(value.replace("'", ''))

    def source_signing():
        clause = leftover.removesuffix(' avec signature individuelle')
        return clause + ' avec signature individuelle.' in source_text

    m = match(rf"Administration: (?P<name1>{NAME}), nommée présidente, et (?P<name2>{NAME}), jusqu'ici président, continuent à signer individuellement")
    if m:
        rule = 'fr.persons.board_president_changed.v1'
        return [person(rule, m['name1'], role='administratrice présidente', signing='Einzelunterschrift'), person(rule, m['name2'], role='administrateur', signing='Einzelunterschrift', extra={'previous_role': 'président'})], ''

    m = match(rf"L'associée (?P<name>{NAME}) est nommée gérante", signed=True)
    if m and source_signing():
        return [person('fr.persons.associate_appointed_manager.v1', m['name'], role='associée-gérante', signing='Einzelunterschrift')], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}) p\. (?P<page>\d+)/(?P<notice_id>\d+)\) est rectifiée en ce sens que l'associé-gérant se nomme (?P<name>{NAME}) \(et non (?P<previous_name>{NAME}) comme publié\)")
    if m:
        return [person('fr.persons.associate_manager_name_notice_corrected.v1', m['name'], role='associé-gérant', extra={'correction': True, **{k: v for k, v in m.groupdict().items() if k != 'name'}})], ''

    m = match(rf"Le montant de la commandite de l'associée (?P<associate>[^()]+?) \((?P<associate_uid>{UID})\) est réduit de CHF (?P<previous_amount>{MONEY}) à CHF (?P<amount>{MONEY})")
    if m and number(m['previous_amount']) > number(m['amount']) > 0:
        return [event('fr.text.limited_partner_contribution_reduced.v1', action='limited_partner_contribution_reduced', currency='CHF', **m.groupdict())], ''

    m = match(r"\)\. \) à l'adresse indiquée par l'associé ou ses ayants droit et figurant dans le registre des parts sociales")
    communication = "Communications aux associés: par tout moyen de transmission écrit (lettre recommandée, télécopie, courrier électronique, etc.) à l'adresse indiquée par l'associé ou ses ayants droit et figurant dans le registre des parts sociales."
    if m and communication in source_text:
        return [event('fr.text.associate_communications_registered_address.v1', action='communications_changed', recipients='associés', method='tout moyen de transmission écrit', address_source='registre des parts sociales', address_supplied_by='associé ou ses ayants droit')], ''

    m = match(rf'Mit Urteil vom (?P<decision_date>{DATE}) hat das Nachlassgericht des Bezirksgerichts (?P<court_place>{NAME}) die der Gesellschaft gewährte provisorische Nachlassstundung zufolge Sanierung aufgehoben\. \[bisher: Mit Entscheid vom (?P<previous_decision_date>{DATE}) hat der Einzelrichter im summarischen Verfahren des Bezirksgerichts (?P=court_place) eine provisorische Nachlassstundung von (?P<duration>vier) Monaten bis (?P<until_day>\d{{1,2}})\. Oktober (?P<until_year>\d{{4}}) gewährt\.\]', 'de')
    if m:
        try:
            until = datetime(int(m['until_year']), 10, int(m['until_day'])).strftime('%d.%m.%Y')
        except ValueError:
            return [], leftover
        return [event('de.text.provisional_moratorium_lifted_restructuring.v1', action='moratorium_lifted', reason='Sanierung', provisional=True, court='Nachlassgericht des Bezirksgerichts ' + m['court_place'], decision_date=m['decision_date'], previous_decision_date=m['previous_decision_date'], previous_duration_months=4, previous_until_date=until)], ''

    m = match(r"La liquidazione è terminta\. Ma la cancellazione della società non può ancora essere effettuata mancando il consenso dell'autorità fiscale cantonale", 'it')
    if m:
        return [event('it.text.liquidation_complete_tax_consent_pending_typo.v1', action='liquidation_completed', deletion_pending=True, pending_consent='autorità fiscale cantonale')], ''

    m = match(rf'Parts sociales de CHF (?P<nominal1>{MONEY}), CHF (?P<nominal2>{MONEY}) et CHF (?P<nominal3>{MONEY})')
    if m and all(number(v) > 0 for v in m.groupdict().values()):
        return [event('fr.text.three_cooperative_share_nominals.v1', action='share_nominals', currency='CHF', share_nominals=list(m.groupdict().values()))], ''

    m = match(rf'Rectificatif: la société en nom collectif ayant été radiée par erreur, elle est réinscrite comme ci-devant \(FOSC du (?P<notice_date>{DATE}), p\. (?P<page>\d+)/(?P<notice_id>\d+)\)')
    if m:
        return [event('fr.text.partnership_erroneous_deletion_reinstated.v1', action='reinstatement', correction=True, legal_form='société en nom collectif', reason='radiée par erreur', **m.groupdict())], ''

    m = match(rf"L'associé (?P<seller>{NAME}), maintenant domicilié à (?P<seller_place>{NAME}), (?P<seller_country>[A-Z]{{3}}), détient désormais une part de CHF (?P<nominal>{MONEY}) par suite de cession de une part de CHF (?P=nominal) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<buyer_place>{NAME}), (?P<buyer_country>[A-Z]{{3}}), nouvel associé pour une part de CHF (?P=nominal)", signed=True)
    if m and number(m['nominal']) > 0 and source_signing():
        rule = 'fr.persons.single_share_transferred_foreign_residences.v1'
        return [event(rule, action='share_transfer', seller=m['seller'], buyer=m['buyer'], shares=1, share_nominal=m['nominal']), person(rule, m['seller'], role='associé', place=m['seller_place'], extra={'country': m['seller_country'], 'shares': 1, 'share_nominal': m['nominal']}), person(rule, m['buyer'], role='associé', place=m['buyer_place'], signing='Einzelunterschrift', extra={'country': m['buyer_country'], 'origin': m['origin'], 'shares': 1, 'share_nominal': m['nominal']})], ''

    m = match(rf"L'inscription n°(?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que les statuts ont été adoptés le (?P<adoption_date>{DATE}), et non le (?P<previous_adoption_date>{DATE})")
    if m:
        return [event('fr.text.statutes_adoption_date_corrected.v1', action='statutes_adoption_date_corrected', correction=True, **m.groupdict())], ''

    m = match(rf'(?P<seller>{NAME}), associé, a cédé (?P<transferred>{COUNT}) de ses (?P<previous>{COUNT}) parts sociales de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]), nouvel associé, lequel est en outre nommé gérant', signed=True)
    if m and number(m['previous']) >= number(m['transferred']) > 0 and number(m['nominal']) > 0 and source_signing():
        rule = 'fr.persons.partial_share_transfer_new_manager.v1'
        return [event(rule, action='share_transfer', seller=m['seller'], buyer=m['buyer'], shares=int(number(m['transferred'])), share_nominal=m['nominal']), person(rule, m['seller'], role='associé', extra={'shares': int(number(m['previous']) - number(m['transferred'])), 'previous_shares': int(number(m['previous'])), 'share_nominal': m['nominal']}), person(rule, m['buyer'], role='associé-gérant', place=m['place'], signing='Einzelunterschrift', extra={'origin': m['origin'], 'country': m['country'], 'shares': int(number(m['transferred'])), 'share_nominal': m['nominal']})], ''

    return [], leftover
