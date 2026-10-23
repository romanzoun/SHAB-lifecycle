from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, UID
from .parser99 import _FR_ADMINISTRATOR_LIQUIDATORS_CONTINUE
from .parser116 import _FR_ADMINISTRATION_AND_DIRECTOR_SIGNING_CHANGES
from .parser143 import _DE_BANKRUPTCY_APPEAL_SUSPENSIVE_EFFECT
from .parser209 import _FR_SIGNING_EXCLUSIONS_AND_NEW_ADMINISTRATOR

NAME = r'[^,;.()]+?'
DATE = r'\d{2}[.-]\d{2}[.-]\d{4}'
LEGACY = (_FR_ADMINISTRATOR_LIQUIDATORS_CONTINUE,
          _FR_ADMINISTRATION_AND_DIRECTOR_SIGNING_CHANGES,
          _DE_BANKRUPTCY_APPEAL_SUSPENSIVE_EFFECT,
          _FR_SIGNING_EXCLUSIONS_AND_NEW_ADMINISTRATOR)


def extract_parser377_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize bounded sample variants, preserving prior rule ownership."""
    leftover = text.strip()
    if any(pattern.fullmatch(leftover) for pattern in LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('date'):
                        datetime.strptime(value.replace('-', '.'), '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, event_type='organization_changed', **extra):
        return _event(*context, event_type, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, place=None, role=None, signing=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, place=place, role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    m = match(rf'Liquidateurs: les administrateurs (?P<name1>{NAME}) et (?P<name2>{NAME}) lesquels continuent à signer individuellement')
    if m:
        return [person('two_administrator_liquidators_continue', m, m[key], role='administrateur, liquidateur', signing='Einzelunterschrift') for key in ('name1', 'name2')], ''

    m = match(rf'(?P<name>{NAME}), maintenant à (?P<place>{NAME}), est nommé administrateur')
    if m:
        return [person('relocated_administrator_appointed', m, m['name'], m['place'], 'administrateur')], ''

    m = match(rf"(?P<seller1>{NAME}), et (?P<seller2>{NAME}) \((?P<seller_uid>{UID})\) ne sont plus associés; leurs parts, respectivement (?P<transferred_each>{COUNT}) parts de CHF (?P<nominal>{MONEY}) chacun, ont été cédées à (?P<buyer>{NAME}) jusqu'ici associé, gérant, pour (?P<before>{COUNT}) parts de CHF (?P=nominal), lequel détient désormais (?P<after>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        return [event('individual_and_company_shares_transferred', m)], ''

    m = match(rf'(?P<name1>{NAME}), maintenant à (?P<place>{NAME}), et (?P<name2>{NAME}) signent désormais collectivement à deux')
    if m:
        return [person('two_signers_one_relocated', m, m['name1'], m['place'], signing='Kollektivunterschrift zu zweien'), person('two_signers_one_relocated', m, m['name2'], signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf"Les inscriptions (?P<entry1>{COUNT}) du (?P<entry1_date>{DATE}) \(FOSC du (?P<notice1_date>{DATE}), p\. (?P<notice1_ref>\d+/\d+)\) et (?P<entry2>{COUNT}) du (?P<entry2_date>{DATE}) \(FOSC (?P<notice2_date>{DATE}), p\. (?P<notice2_ref>\d+/\d+)\) sont rectifiées en ce sens que l'administrateur porte le nom de (?P<name>{NAME}) \(et non (?P<previous_name>{NAME})\)")
    if m:
        return [person('two_notices_administrator_name_corrected', m, m['name'], role='administrateur')], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), conserve son pouvoir de signature individuelle")
    if m:
        return [person('notice_individual_signing_retained', m, m['name'], m['place'], signing='Einzelunterschrift')], ''

    m = match(rf"Statuts modifiés selon décision de l'autorité de surveillance du (?P<decision_date>{DATE})")
    if m:
        return [event('supervisory_authority_statutes_amended', m, 'statutes_changed')], ''

    notice = rf'Der Eintrag Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) \(SHAB vom (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\)'
    repeated_notice = r'Der Eintrag Nr\. (?P=entry) vom (?P=entry_date) \(SHAB vom (?P=notice_date), Id (?P=notice_id)\)'
    m = match(notice + rf' ist wie folgt berichtigt: (?P<name1>{NAME}), Verwaltungsratsmitglied, Vizepräsident, Einzelunterschrift, in (?P<place>{NAME}) \(und nicht (?P<previous_name1>{NAME}), Verwaltungsratsmitglied, Vizepräsident, Geschäftsführer, Einzelunterschrift, in (?P<previous_place>{NAME})\)\. ' + repeated_notice + rf' ist wie folgt ergänzt: (?P<previous_name2>{NAME}), Verwaltungsratsmitglied, Einzelunterschrift, neu Verwaltungsratsmitglied, Geschäftsführer, Einzelunterschrift, korrekterweise (?P<name2>{NAME})', 'de')
    if m:
        return [person('board_notice_correction_and_supplement', m, m['name1'], m['place'], 'Verwaltungsratsmitglied, Vizepräsident', 'Einzelunterschrift'), person('board_notice_correction_and_supplement', m, m['name2'], role='Verwaltungsratsmitglied, Geschäftsführer', signing='Einzelunterschrift')], ''

    m = match(rf'(?P<name>{NAME}), nommé directeur, signe désormais collectivement à deux, sans autre restriction; sa procuration est radiée')
    if m:
        return [person('director_collective_signing_procuration_revoked', m, m['name'], role='directeur', signing='Kollektivunterschrift zu zweien', procuration_revoked=True, signing_restrictions_removed=True)], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que (?P<name>{NAME}) continue de signer collectivement à deux, désormais pas avec (?P<excluded1>{NAME}) \(et non (?P<previous_excluded>{NAME}), comme publié\), ni (?P<excluded2>{NAME})")
    if m:
        return [person('notice_collective_signing_exclusions_corrected', m, m['name'], signing='Kollektivunterschrift zu zweien', not_with=[m['excluded1'], m['excluded2']])], ''

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat das (?P<court>{NAME}) dem Rekurs vom (?P<appeal_date>{DATE}) gegen das Konkurseröffnungsurteil vom (?P<bankruptcy_date>{DATE}) die aufschiebende Wirkung erteilt \((?P<legal_basis>Art\. 159 Abs\. 2 HRegV)\)', 'de')
    if m:
        return [event('bankruptcy_recourse_suspensive_effect_granted', m, 'status_changed', suspensive_effect=True)], ''

    m = match(rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que la raison sociale demeure: (?P<company>{NAME}), en liquidation \(et non pas devient (?P<previous_company>{NAME})\)")
    if m:
        return [event('liquidation_company_name_retained_corrected', m, liquidation=True)], ''
    return [], text
