from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, UID
from . import parser56, parser130, parser155, parser242

NAME = r'[^,;\[\]\n]+?'
DATE = r'\d{2}\.\d{2}\.\d{4}'
# Earlier compiled patterns retain ownership, including in isolation tests.
_LEGACY = tuple(p for module in (parser56, parser130, parser155, parser242)
                for p in vars(module).values() if isinstance(p, re.Pattern))


def extract_parser391_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Parse only complete residual clauses; preserve unsupported input verbatim."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', *, candidate=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover if candidate is None else candidate)
        if m:
            try:
                for date in re.findall(r'\d{2}[.-]\d{2}[.-]\d{4}', m[0]):
                    datetime.strptime(date, '%d-%m-%Y' if '-' in date else '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, kind='officer_changed', **extra):
        return _person_event(*context, kind, f'{language}.text.{action}.v1', m['name'], extra={'action': action, **m.groupdict(), **extra})

    m = match(rf'Die Genossenschaft ist mit Beschluss der Generalversammlung vom (?P<decision_date>{DATE}) aufgelöst', 'de')
    if m:
        return [event('cooperative_dissolved_general_meeting', m, 'status_changed')], ''
    m = match(rf"Par ordonnance du (?P<suspension_date>{DATE}), le Tribunal cantonal a suspendu l'exécution du jugement de faillite rendu le (?P<bankruptcy_date>{DATE})\. Par ordonnance du (?P<closure_date>{DATE}), le Tribunal cantonal a classé le dossier, le recourant ayant renoncé à son recours")
    if m:
        return [event('bankruptcy_execution_suspended_appeal_withdrawn', m, 'status_changed', appeal_withdrawn=True)], ''
    m = match(r"La mention relative à l'organisation de la société est radiée, celle-ci n'étant plus obligatoire")
    if m:
        return [event('organization_statement_removed_no_longer_required', m)], ''
    m = match(rf'Transfert de patrimoine: Selon contrat du (?P<agreement_date>{DATE}), la société a transféré des actifs pour CHF (?P<assets>{MONEY}) et des passifs envers les tiers pour CHF (?P<liabilities>{MONEY}), soit un actif net de CHF (?P<net_assets>{MONEY}), à la société (?P<recipient>{NAME}) \((?P<recipient_uid>{UID})\), à (?P<place>{NAME})\. Contre-prestation: aucune')
    if m:
        return [event('asset_transfer_no_consideration', m, currency='CHF', consideration='aucune')], ''
    m = match(rf"Le montant du capital-participation conditionnel figurant dans les statuts déposés à l'appui de l'inscription (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>\d{{2}}-\d{{2}}-\d{{4}}), p\. (?P<notice_ref>\d+/\d+)\) étant erroné, les statuts sont corrigés sur ce point")
    if m:
        return [event('conditional_participation_capital_statutes_corrected', m, 'capital_changed')], ''
    m = match(rf'Transfert de patrimoine: selon contrat du (?P<agreement_date>{DATE}), la société a transféré (?P<count>{COUNT}) actions nominatives de CHF (?P<nominal>{MONEY}) de la société "(?P<company>[^"\n]+)" à (?P<company_place>{NAME}) \((?P<company_uid>{UID})\) à la société (?P<recipient>{NAME}), à (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Contre-prestation: aucune')
    if m:
        return [event('asset_transfer_registered_shares_no_consideration', m, currency='CHF', consideration='aucune')], ''
    m = match(rf"L'associée-gérante (?P<seller>{NAME}) détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<count>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer>{NAME}), associée-gérante et présidente désormais pour (?P<buyer_count>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        return [event('female_managers_share_transfer_existing_president', m, currency='CHF')], ''
    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vermögensübertragungsvertrag vom (?P<agreement_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung CHF (?P<consideration>{MONEY})', 'de')
    if m:
        return [event('asset_transfer_assets_only_no_inventory', m, currency='CHF')], ''
    # Exclude the two-person variant owned by parser300 even if it is disabled.
    m = match(r"Les pouvoirs d'(?P<name>[^,;.\n]+) sont radiés")
    if m and ' et ' not in m['name']:
        return [person('single_person_powers_revoked_elision', m, powers_revoked=True)], ''
    m = match(rf"L'associé-gérant (?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}) au directeur (?P<buyer>{NAME}), nouvel associé, avec (?P=count) parts de CHF (?P=nominal); (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        return [event('manager_share_transfer_to_existing_director', m, currency='CHF')], ''
    # Only the plural, four-company notice with post-UID places is supported here.
    component = rf"(?:reprise|Reprise) des actifs et passifs de (?P<transferor>{NAME}) \((?P<transferor_uid>{UID})\), à (?P<place>{NAME}), selon contrat de fusion du (?P<agreement_date>{DATE}) et bilan intermédiaire au (?P<balance_date>{DATE}), présentant des actifs de CHF (?P<assets>{MONEY}) et des passifs envers les tiers de CHF (?P<liabilities>{MONEY}), soit un actif net de CHF (?P<net_assets>{MONEY})\. La totalité du capital-actions(?P<capital_social> et du capital social)? des sociétés fusionnantes étant détenue par le même actionnaire(?P<associate> et associé)?, la fusion ne donne pas lieu à une augmentation du capital, ni à une attribution d'actions"
    if language == 'fr' and leftover.startswith('Fusions: '):
        parts = re.split(r'\. (?=Reprise des actifs et passifs de )', leftover[len('Fusions: '):])
        matches = [match(component, candidate=part) for part in parts]
        if len(matches) == 4 and all(matches) and all(bool(m['capital_social']) == bool(m['associate']) for m in matches):
            return [event('four_company_merger_same_owner', m, currency='CHF') for m in matches], ''
    m = match(rf"Rectification de l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\): (?P<name>{NAME}), associé, signature collective à deux, à (?P<place>{NAME}) \(et non pas à (?P<previous_place>[^()]+)\)")
    if m:
        return [_person_event(*context, 'officer_changed', 'fr.text.associate_residence_corrected_notice.v1', m['name'], role='associé', signing='Kollektivunterschrift zu zweien', place=m['place'], extra={'action': 'associate_residence_corrected_notice', **m.groupdict()})], ''
    return [], text
