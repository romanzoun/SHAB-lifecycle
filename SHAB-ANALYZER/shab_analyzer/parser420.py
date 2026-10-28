from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser409 import NAME
from .parser237 import _FR_BRANCH_LEGACY_IDENTIFIER_REPLACED

# Legacy identifiers can resemble locality annotations: keep parser 237 in charge.
_LEGACY = (_FR_BRANCH_LEGACY_IDENTIFIER_REPLACED,)


def extract_parser420_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Sample-backed complete residual clauses, preserving previous events."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for date in re.findall(DATE, m[0]):
                    datetime.strptime(date, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name,
                             role=role, signing=signing, place=place,
                             extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    m = match(rf'In der am (?P<entry_date>{DATE}) unter TR-Nr\. (?P<entry>{COUNT}) vorgenommenen Eintragung wurde bei (?P<name1>[^;\[\]\n]+?) der Bisher-Text unvollständig wiedergegeben\. Richtig: \[bisher: (?P<previous_name1>[^;\[\]\n]+?), mit (?P<count1>{COUNT}) Stammanteilen zu je CHF (?P<nominal1>{MONEY})\]\. Bei (?P<name2>[^;\[\]\n]+?) wurde der Bisher-Text ebenfalls unvollständig wiedergegeben\. Richtig: \[bisher: (?P<previous_name2>[^;\[\]\n]+?), mit (?P<count2>{COUNT}) Stammanteilen zu je CHF (?P<nominal2>{MONEY})\]', 'de')
    if m:
        return [event('two_previous_shareholdings_supplemented', m, corrected=True, historical_annotation=True)], ''

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\) est rectifiée dans ce sens: (?P<name>{NAME}), signature collective à deux avec un administrateur \(et non pas (?P<previous_name>{NAME})\)")
    if m:
        return [person('name_corrected_signing_with_administrator', m, m['name'], signing='Kollektivunterschrift zu zweien', corrected=True, signing_partner_role='administrateur')], ''

    m = match(rf'Die am (?P<deletion_date>{DATE}) gelöschte Rechtseinheit wird aufgrund der Verfügung des (?P<court>Einzelrichters des Kreisgerichts St\. Gallen) vom (?P<decision_date>{DATE}) zum Zwecke der Liquidation im Sinne von (?P<legal_basis>Art\. 935 OR i\.V\.m\. Art\. 164 HRegV) wieder in das Handelsregister eingetragen und besteht entsprechend den früheren Eintragungen weiter\. \[bisher: (?P<previous_deletion_reason>Die Gesellschaft wird gemäss Art\. 159 Abs\. 5 lit\. a HRegV von Amtes wegen gelöscht\.)\]', 'de')
    if m:
        return [event('entity_reentered_for_liquidation_article935', m, 'status_changed')], ''

    m = match(rf'(?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<country1>[A-Z]{{3}}) et (?P<name2>{NAME}), de et à (?P<place2>{NAME}), sont membres du conseil, sans signature')
    if m:
        return [person('council_pair_unsigned_country_code', m, m[f'name{i}'], 'membre du conseil', 'ohne Zeichnungsberechtigung', m[f'place{i}'], origin=m['origin1'] if i == 1 else m['place2'], country=m['country1'] if i == 1 else None) for i in (1, 2)], ''

    m = match(rf'Nouveau membre du conseil de fondation pas avec (?P<excluded1>{NAME}), (?P<excluded2>{NAME}), (?P<excluded3>{NAME}), (?P<excluded4>{NAME}) et (?P<excluded5>{NAME}): (?P<name>{NAME}), de et à (?P<place>{NAME})')
    if m and leftover.replace('fondation pas avec', 'fondation avec signature collective à deux, pas avec', 1) in source_text:
        return [person('foundation_member_five_excluded_signatories', m, m['name'], 'membre du conseil de fondation', 'Kollektivunterschrift zu zweien', m['place'], excluded_partners=[m[f'excluded{i}'] for i in range(1, 6)], signing_restriction='not_with')], ''

    m = match(rf'(?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée avec (?P=count) parts de CHF (?P=nominal), sans signature\. (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)')
    if m:
        count, before, remaining = (int(m[k].replace("'", '')) for k in ('count', 'before', 'remaining'))
        if count <= 0 or remaining <= 0 or count + remaining != before:
            return [], text
        return [event('partial_transfer_new_unsigned_associate_du_origin', m, 'ownership_changed', currency='CHF'), person('new_unsigned_associate_du_origin', m, m['buyer'], 'associée', 'ohne Zeichnungsberechtigung', m['place'])], ''

    m = match(rf'(?P<seller>{NAME}) détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<count>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer1>{NAME}), associée désormais pour (?P<total1>{COUNT}) parts de CHF (?P=nominal), et à (?P<buyer2>{NAME}), associée désormais pour (?P<total2>{COUNT}) parts de CHF (?P=nominal)')
    if m:
        # The wording does not specify an allocation per recipient.
        return [event('share_transfer_two_existing_associates_totals', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf'Die Mutation der Zeichnungsberechtigung sowie der Wohnortangabe von (?P<name>{NAME}) erfolgt von Amtes gemäss (?P<legal_basis>Art\. 152 HRegV)', 'de')
    if m:
        return [event('official_signing_and_residence_mutation_annotation', m)], ''

    m = match(rf"La succursale d'(?P<place>{NAME}) \((?P<branch_uid>{UID})\) est radiée \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\)")
    if m:
        return [event('branch_deleted_uid_notice_reference', m)], ''

    m = match(rf'(?P<name>{NAME}), nommée sous-directrice, signe désormais collectivement à deux, avec un administrateur ou un directeur; sa procuration est radiée')
    if m:
        return [person('subdirector_signing_administrator_or_director_proxy_removed', m, m['name'], 'sous-directrice', 'Kollektivunterschrift zu zweien', signing_partner_roles=['administrateur', 'directeur'], procuration_removed=True)], ''

    m = match(rf'Nouvelle succursale: (?P<place>{NAME}) \((?P<branch_uid>{UID})\) \[précédemment: (?P<previous_place>{NAME}) \((?P<previous_municipality>{NAME})\)\]')
    if m:
        return [event('branch_place_annotation_previous_locality', m)], ''

    m = match(rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens qu'un membre du conseil se nomme (?P<name>{NAME}) \(et non pas (?P<previous_name>{NAME})\)")
    if m:
        return [person('council_member_name_corrected_no_entry', m, m['name'], 'membre du conseil', corrected=True)], ''
    return [], text
