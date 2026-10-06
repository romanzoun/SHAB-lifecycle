from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser287_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Parse complete fixture-backed clauses and retain unsupported residue."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
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

    m = match(rf"Rectificatif: l'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<page>\d+)/(?P<notice_id>\d+)\) est rectifiée en ce sens que (?P<name>{NAME}) est à (?P<place>{NAME}) \(et non à (?P<previous_place>{NAME}), comme publié\)")
    if m:
        return [person('fr.persons.residence_canton_corrected.v1', m['name'], place=m['place'], extra={'correction': True, **{k: v for k, v in m.groupdict().items() if k not in ('name', 'place')}})], ''

    m = match(rf'Berichtigung der Eintragung Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) \(SHAB vom (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\): Revisionsstelle: (?P<auditor>{NAME}) \((?P<auditor_uid>{UID})\) \(und nicht (?P<previous_auditor>{NAME}) \((?P<previous_auditor_uid>{UID})\)\)', 'de')
    if m:
        return [event('de.text.auditor_identity_corrected.v1', action='auditor_corrected', correction=True, **m.groupdict())], ''

    m = match(rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) ayant été opérée par erreur, elle est supprimée")
    if m:
        return [event('fr.text.erroneous_entry_cancelled.v1', action='entry_cancelled', reason='opérée par erreur', **m.groupdict())], ''

    m = match(rf'Vermögensübertragung: Die Stiftung überträgt gemäss Vertrag vom (?P<contract_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: (?P<claims>{COUNT}) Ansprüche an der Anlagegruppe "(?P<investment_group>[^"\n]+)" der (?P=recipient) in der Höhe von je CHF (?P<claim_value>{MONEY}) aufgrund des Nettoinventarwertes per (?P<valuation_date>{DATE})', 'de')
    if m and all(number(m[k]) > 0 for k in ('assets', 'claims', 'claim_value')):
        return [event('de.text.foundation_assets_transferred_for_claims.v1', action='asset_transfer', currency='CHF', **m.groupdict())], ''

    m = match(rf"Gelöschte weiteren Adressen: (?P<deleted_addresses>[^;]+?)\. Abspaltung: Ein Teil der Aktiven und Passiven gehen gemäss Spaltungsplan vom (?P<plan_date>{DATE}) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\) über", 'de')
    if m:
        return [event('de.text.additional_addresses_deleted_demerger.v1', action='demerger', **m.groupdict())], ''

    m = match(rf'La réinscription de la société, radiée par suite de clôture de faillite, a été ordonnée par décision du (?P<court>Tribunal de première instance) du (?P<decision_date>{DATE})\. Les faits inscrits au moment de la radiation demeurent valables')
    if m:
        return [event('fr.text.bankruptcy_closed_reinstatement_facts_retained.v1', action='reinstatement', previous_deletion_reason='clôture de faillite', previous_facts_retained=True, **m.groupdict())], ''

    m = match(rf"L'associé-gérant (?P<seller>{NAME}), nommé président, détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<transferred>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée-gérante pour (?P=transferred) parts de CHF (?P=nominal)(?: avec signature individuelle)?")
    if m and all(number(m[k]) > 0 for k in ('remaining', 'transferred', 'nominal')) and leftover.removesuffix(' avec signature individuelle') + ' avec signature individuelle.' in source_text:
        rule = 'fr.persons.share_transfer_manager_president.v1'
        return [event(rule, action='share_transfer', seller=m['seller'], buyer=m['buyer'], shares=int(number(m['transferred'])), share_nominal=m['nominal']), person(rule, m['seller'], role='associé-gérant président', extra={'shares': int(number(m['remaining'])), 'share_nominal': m['nominal']}), person(rule, m['buyer'], role='associée-gérante', place=m['place'], signing='Einzelunterschrift', extra={'origin': m['origin'], 'shares': int(number(m['transferred'])), 'share_nominal': m['nominal']})], ''

    m = match(rf"Neue weiteren Adressen: (?P<new_addresses>[^;]+; [^;]+?)\. Abspaltung: Die Gesellschaft übernimmt dabei gemäss Spaltungsvertrag vom (?P<contract_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) von der (?P<transferor>{NAME}), in (?P<place>{NAME}) \((?P<transferor_uid>{UID})\)\. Die Aktionäre der übertragenden Gesellschaft erhalten (?P<shares>{COUNT}) Aktien zu CHF (?P<nominal>{MONEY})", 'de')
    if m and all(number(m[k]) > 0 for k in ('assets', 'liabilities', 'shares', 'nominal')):
        return [event('de.text.additional_addresses_demerger_acquisition.v1', action='demerger_acquisition', currency='CHF', **m.groupdict())], ''

    m = match(rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}) p, (?P<page>\d+)/(?P<notice_id>\d+)\) est rectifiée en ce sens que l'organe de révision est: (?P<auditor>{NAME}) \((?P<auditor_uid>{UID})\), à (?P<place>{NAME}) \(et non (?P<previous_auditor>{NAME}) \((?P<previous_auditor_uid>{UID})\)\)")
    if m:
        return [event('fr.text.auditor_identity_corrected_notice_typo.v1', action='auditor_corrected', correction=True, **m.groupdict())], ''

    m = match(rf'(?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}) et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), sont membres du conseil de fondation, tous deux(?: avec signature collective à deux)?')
    if m and leftover.removesuffix(' avec signature collective à deux') + ' avec signature collective à deux.' in source_text:
        rule = 'fr.persons.two_foundation_members_collective_signing.v1'
        return [person(rule, m['name' + i], role='membre du conseil de fondation', place=m['place' + i], signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin' + i]}) for i in ('1', '2')], ''

    m = match(rf"Par prononcé rendu le (?P<decision_day>\d{{1,2}}) mars (?P<decision_year>\d{{4}}), le président du (?P<court>Tribunal de l'arrondissement de la Broye et du Nord vaudois) a accordé à la société un sursis concordataire définitif jusqu'au (?P<until_day>\d{{1,2}}) septembre (?P<until_year>\d{{4}})\. (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), est désigné comme commissaire au sursis")
    if m:
        try:
            decision = datetime(int(m['decision_year']), 3, int(m['decision_day']))
            until = datetime(int(m['until_year']), 9, int(m['until_day']))
        except ValueError:
            return [], leftover
        if until <= decision:
            return [], leftover
        rule = 'fr.text.definitive_moratorium_commissioner.v1'
        return [event(rule, action='moratorium_granted', provisional=False, court=m['court'], decision_date=decision.strftime('%d.%m.%Y'), until_date=until.strftime('%d.%m.%Y')), person(rule, m['name'], role='commissaire au sursis', place=m['place'], extra={'origin': m['origin']})], ''

    m = match(rf'(?P<name>{NAME}) est maintenant originaire à (?P<origin>{NAME})')
    if m:
        return [person('fr.persons.origin_changed_variant.v1', m['name'], extra={'origin': m['origin']})], ''

    return [], leftover
