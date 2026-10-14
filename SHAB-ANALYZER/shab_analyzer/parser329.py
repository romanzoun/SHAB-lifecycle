from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, COUNT, UID


def extract_parser329_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Complete bounded sample clauses after earlier rules, without replacing events."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', source_pattern=None):
        if language not in ((lang,) if isinstance(lang, str) else lang):
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m:
            return None
        if source_pattern:
            s = re.search(r'(?<!\S)(?=\S)' + source_pattern + r'\.?$', source_text)
            if not s or any(s[k] != v for k, v in m.groupdict().items()):
                return None
            m = s
        try:
            for k, v in m.groupdict().items():
                if k.endswith('_date') and v is not None:
                    datetime.strptime(v, '%d.%m.%Y')
        except ValueError:
            return None
        return m

    def event(action, m, event_type='organization_changed', **extra):
        return _event(*context, event_type, f'{language}.text.{action}.v1', {**m.groupdict(), 'action': action, **extra})

    def person(action, m, name, role, signing=None, place=None, event_type='officer_changed', **extra):
        return _person_event(*context, event_type, f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={**m.groupdict(), 'action': action, **extra, 'name': name.strip(), 'place': place.strip() if place else None})

    m = match(rf"Par suite de cession d'une part de CHF (?P<nominal>{MONEY}), (?P<seller>{NAME}) est maintenant associé pour (?P<remaining>{COUNT}) parts de CHF (?P=nominal), et (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), est nouvel associé pour une part de CHF (?P=nominal), sans signature sociale")
    if m:
        return [event('single_share_transfer_unsigned_associate', m, 'ownership_changed', transferred='1', currency='CHF'), person('new_associate_without_signing', m, m['buyer'], 'Gesellschafter', 'ohne Zeichnungsberechtigung', m['place'], without_signing=True)], ''

    m = match(rf"L'associée (?P<seller>{NAME}) a cédé (?P<transferred>{COUNT}) de ses (?P<before>{COUNT}) parts sociales de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé\. Gérants: (?P=seller), nommé présidente, et (?P=buyer), lesquels signent collectivement à deux\. Les pouvoirs de (?P=seller) sont modifiés en ce sens")
    if m:
        if int(m['transferred'].replace("'", '')) > int(m['before'].replace("'", '')):
            return [], leftover
        return [event('share_transfer_collective_managers', m, 'ownership_changed', currency='CHF'), person('associate_manager_president_collective', m, m['seller'], 'Gesellschafterin, Geschäftsführerin, Präsidentin', 'Kollektivunterschrift zu zweien'), person('associate_manager_collective', m, m['buyer'], 'Gesellschafter, Geschäftsführer', 'Kollektivunterschrift zu zweien', m['place'])], ''

    pattern = rf"(?P<departed>{NAME}) n'est plus liquidateur; ses pouvors sont radiés\. (?P<name>[^,;]+), d'(?P<origin>{NAME}), à (?P<place>{NAME}), est liquidateur"
    # The supplied French clause carries German publication language metadata.
    m = match(pattern, lang=('fr', 'de'), source_pattern=pattern + r' avec signature individuelle')
    if m:
        return [person('liquidator_departed_powers_revoked', m, m['departed'], 'Liquidator', powers_removed=True), person('liquidator_appointed_individual', m, m['name'], 'Liquidator', 'Einzelunterschrift', m['place'])], ''

    m = match(rf'Par arrêt du (?P<decision_date>{DATE}), la (?P<court>{NAME}) a rejeté le recours contre le jugement du (?P<previous_decision_date>{DATE}), par conséquent, la faillite est prononcée avec effet à partir du (?P<effective_date>{DATE}) à (?P<effective_time>(?:[01]\d|2[0-3]):[0-5]\d)\. Par conséquent, sa raison sociale redevient: (?P<liquidation_name>[^;]+, en liquidation)')
    if m:
        return [event('bankruptcy_appeal_rejected_effective', m, 'status_changed', bankruptcy_opened=True, appeal_rejected=True)], ''

    m = match(rf"L'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que le capital-actions de CHF (?P<capital>{MONEY}) est divisé en (?P<count>{COUNT}) actions de CHF (?P<nominal>{MONEY}), nominatives \(et non pas de (?P<previous_count>{COUNT}) actions de CHF (?P<previous_nominal>{MONEY}), nominatives\)")
    if m:
        return [event('registered_share_count_corrected', m, 'capital_changed', corrected=True, currency='CHF', share_kind='nominatives')], ''

    m = match(rf"Liquidateurs: (?P<name1>{NAME}), président, (?P<name2>{NAME}), et (?P<name3>{NAME}), tous membres du conseil d'administration, lesquels continuent de signer collectivement à deux\. Les restrictions statutaires liées à la transmissibilité des actions sont levées de par la loi")
    if m:
        return [person('board_members_become_liquidators', m, m[f'name{i}'], 'Liquidator, Verwaltungsratspräsident' if i == 1 else 'Liquidator, Verwaltungsrat', 'Kollektivunterschrift zu zweien') for i in (1, 2, 3)] + [event('share_transfer_restrictions_lifted_by_law', m, restrictions_lifted=True)], ''

    pattern = rf'(?P<seller>{NAME}) a cédé (?P<transferred>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée pour (?P<buyer_count>{COUNT}) parts de CHF (?P=nominal), '
    ending = rf'Par conséquent, (?P=seller) est désormais titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)'
    m = match(pattern + ending, source_pattern=pattern + r'avec signature collective à deux\. ' + ending)
    if m:
        if m['transferred'] != m['buyer_count']:
            return [], leftover
        return [event('share_transfer_new_collective_associate', m, 'ownership_changed', currency='CHF'), person('new_associate_collective', m, m['buyer'], 'Gesellschafterin', 'Kollektivunterschrift zu zweien', m['place'])], ''

    m = match(rf'(?P<name1>{NAME}) et (?P<name2>{NAME}), tous deux gérants, signent désormais individuellement')
    if m:
        return [person('two_managers_sign_individually', m, m[f'name{i}'], 'Geschäftsführer', 'Einzelunterschrift', event_type='signing_authority_changed') for i in (1, 2)], ''

    m = match(rf'(?P<seller>{NAME}) a cédé (?P<transferred>{COUNT}) parts de CHF (?P<nominal>{MONEY}) aux associés (?P<buyer1>{NAME}), (?P<buyer2>{NAME}), (?P<buyer3>{NAME}) et (?P<buyer4>{NAME}), lesquels sont désormais chacun titulaire de (?P<buyer_count>{COUNT}) parts de CHF (?P=nominal)\. Par conséquent, (?P=seller) est maintenant titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)')
    if m:
        # The publication states only the total transferred, not each buyer's allocation.
        return [event('share_transfer_four_existing_associates', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf'Die im Sinne von Art\. 159 Abs\. 5 lit\. a HRegV am (?P<deletion_date>{DATE}) von Amtes wegen gelöschte Gesellschaft wird wieder in das Handelsregister eingetragen, nachdem der Konkursrichter des (?P<court>{NAME}) mit Urteil vom (?P<decision_date>{DATE}) die Wiedereröffnung des Konkursverfahrens als summarisches Verfahren mit Wirkung ab dem (?P<effective_date>{DATE}), (?P<effective_time>(?:[01]\d|2[0-3])\.[0-5]\d) Uhr, angeordnet hat\. \[bisher: Nachdem kein begründeter Einspruch gegen die Löschung erhoben wurde, wird die Gesellschaft im Sinne von Art\. 159 Abs\. 5 lit\. a HRegV von Amtes wegen gelöscht\.\]\. \[gestrichen: Das Konkursverfahren ist mit Urteil der Konkursrichterin vom (?P<previous_decision_date>{DATE}) mangels Aktiven eingestellt worden\.\]', 'de')
    if m:
        return [event('company_reinstated_summary_bankruptcy_reopened', m, 'status_changed', reinstated=True, bankruptcy_reopened=True, summary_proceedings=True)], ''

    m = match(rf"Procuration collective à deux, toutefois pas entre eux, est conférée à (?P<name1>{NAME}), d'(?P<origin1>{NAME}), à (?P<place1>{NAME}), et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME})")
    if m:
        return [person('joint_procuration_excluding_each_other', m, m[f'name{i}'], 'Prokurist', 'Kollektivprokura zu zweien', m[f'place{i}'], event_type='signing_authority_changed', signing_restriction='toutefois pas entre eux', excluded_signing_partner=m[f'name{3-i}']) for i in (1, 2)], ''

    m = match(rf'Vermögensübertragung: Der Verein überträgt gemäss Vermögensübertragungsvertrag vom (?P<agreement_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) auf den Verein "(?P<recipient_name>[^";]+)", in (?P<recipient_place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: CHF (?P<consideration>{MONEY})', 'de')
    if m:
        return [event('association_asset_transfer_cash_consideration', m, 'ownership_changed', currency='CHF')], ''

    return [], leftover
