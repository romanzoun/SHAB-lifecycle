from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser409 import NAME
from . import parser52, parser58, parser65, parser79, parser85, parser92, parser132, parser232

# Historical compiled patterns retain ownership, including isolated calls.
_LEGACY = tuple(p for module in (parser52, parser58, parser65, parser79,
                                 parser85, parser92, parser132, parser232)
                for p in vars(module).values() if isinstance(p, re.Pattern))


def extract_parser429_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
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

    notice = rf"Rectificatif: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que "
    m = match(notice + rf"le capital-actions de CHF (?P<capital>{MONEY}) est divisé en (?P<count>{COUNT}) actions nominatives de CHF (?P<nominal>{MONEY}),? \(et non (?P<previous_count>{COUNT}) actions nominatives de CHF (?P<previous_nominal>{MONEY}) comme publié\)")
    if m:
        return [event('registered_share_division_corrected', m, 'capital_changed', corrected=True, currency='CHF')], ''

    m = match(notice + r'l\'apport en nature et reprise de biens, selon contrat du (?P<contract_day>\d{1,2}) (?P<contract_month>mars) (?P<contract_year>\d{4}), des actifs et des passifs envers les tiers concerne l\'entreprise individuelle non inscrite au Registre du commercede "(?P<contributed_company>[^"\n]+)" \(et non "(?P<previous_contributed_company>[^"\n]+)" comme publié\)')
    if m:
        try:
            datetime(int(m['contract_year']), 3, int(m['contract_day']))
        except ValueError:
            return [], text
        return [event('unregistered_contributed_business_name_corrected', m, 'capital_changed', corrected=True)], ''

    m = match(rf'(?P<seller>{NAME}) détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<count>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé pour (?P=count) parts de CHF (?P=nominal), sans signature sociale')
    if m:
        return [event('partial_share_transfer_new_associate_no_signing', m, 'ownership_changed', currency='CHF', buyer_signing='ohne Zeichnungsberechtigung')], ''

    # Only the new month variant; November remains owned by parser406.
    m = match(r"Selon décision de son assemblée générale du (?P<day>\d{1,2}) (?P<month>septembre) (?P<year>\d{4}), l'association a prononcé sa dissolution")
    if m:
        try:
            datetime(int(m['year']), 9, int(m['day']))
        except ValueError:
            return [], text
        return [event('association_dissolved_written_september_date', m, 'status_changed', dissolved=True)], ''

    m = match(rf'Anteilscheine neu: \[Die Anteilscheine sind aufgehoben worden\.\] \[gestrichen: Anteilscheine zu Fr\. (?P<previous_nominal>\d+)\.--\]\. Mit Beschluss der Generalversammlung vom (?P<decision_date>{DATE}) werden die Anteilscheine zu CHF (?P<nominal>{MONEY}) aufgehoben und als Kautionsforderung der Genossenschafter verbucht; die Beachtung der gesetzlichen Vorschriften von Art\. 874 Abs\. 2 i\.V\.m\. Art\. 734 OR wird mit öffentlicher Urkunde vom (?P<confirmation_date>{DATE}) festgestellt', 'de')
    if m:
        return [event('cooperative_certificates_cancelled_deposit_claim', m, 'capital_changed', cancelled=True, currency='CHF')], ''

    m = match(rf"Le siège principal de la société (?P<previous_company>{NAME}) \((?P<previous_uid>{UID})\) a été radié par suite de fusion avec la société (?P<recipient>{NAME}) \((?P<recipient_uid>{UID})\)\. Les inscriptions de la succursale sont maintenues selon l'article 112 al\. 1 ORC\. Nouvelle raison sociale et numéro d'identification du siège principal: (?P<company>{NAME}) \((?P=recipient_uid)\)")
    if m:
        return [event('head_office_merger_branch_entries_retained', m, branch_entries_retained=True)], ''

    m = match(rf'Division des (?P<before>{COUNT}) parts de CHF (?P<previous_nominal>{MONEY}) en (?P<split_count>{COUNT}) parts de CHF (?P<nominal>{MONEY})\. Par conséquent (?P<seller>{NAME}) est associée-gérante pour (?P=split_count) parts de CHF (?P=nominal)\. Par suite de cession de (?P<count>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée-gérante pour (?P=count) parts de CHF (?P=nominal), (?P=seller), maintenant également présidente, détient désormais (?P<remaining>{COUNT}) parts de CHF (?P=nominal)')
    if m:
        return [event('share_split_transfer_female_managers', m, 'ownership_changed', currency='CHF'), person('seller_manager_appointed_president_after_split', m, m['seller'], 'associée-gérante présidente'), person('new_female_manager_after_split', m, m['buyer'], 'associée-gérante', place=m['place'])], ''

    m = match(rf'Die Gesellschaft wird gemäss Entscheid des (?P<court>{NAME}) vom (?P<decision_date>{DATE}) wieder in das Handelsregister eingetragen\. \[Die in Bezug auf den Liquidator bisher eingetragenen Tatsachen gelten weiterhin\.\]', 'de')
    if m:
        return [event('reinstatement_liquidator_facts_retained', m, 'status_changed', reinstated=True, liquidator_facts_retained=True)], ''

    m = match(rf'(?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}) est membre du conseil, sans signature')
    if m:
        return [person('council_member_no_comma_no_signing', m, m['name'], 'membre du conseil', 'ohne Zeichnungsberechtigung', m['place'])], ''

    m = match(rf'Berichtigung der Eintragung Nummer (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) \(SHAB vom (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\) : (?P<name>{NAME}), Einzelunterschrift \(und nicht Kollektivunterschrift zu zweien\)', 'de')
    if m:
        return [person('individual_signing_corrected_entry_number', m, m['name'], signing='Einzelunterschrift', corrected=True, previous_signing='Kollektivunterschrift zu zweien')], ''

    # A legacy name rule consumed the prefix ending in S.; resolve only an
    # evidenced abbreviation fragment, never a complete legacy name clause.
    m = match(r'A\., en liquidation')
    if m:
        source = re.search(r'Par conséquent, sa raison sociale devient: (?P<company_name>[^;\n]+? S\.A\., en liquidation)\.$', source_text)
        if source:
            return [event('liquidation_name_abbreviation_fragment', source, 'organization_changed', in_liquidation=True)], ''
    return [], text
