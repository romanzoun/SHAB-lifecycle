from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, COUNT


def extract_parser342_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Append bounded sample-backed clauses without replacing earlier events."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('_date'):
                        datetime.strptime(value, '%d.%m.%Y')
                    elif key.endswith('_date_text'):
                        day, month, year = value.split()
                        months = ('janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre')
                        datetime(int(year), months.index(month) + 1, int(day.removesuffix('er')))
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **{k: v for k, v in m.groupdict().items() if k not in ('name', 'place')}, **extra})

    m = match(rf'Die Generalversammlung hat mit Beschluss vom (?P<resolution_date>{DATE}) den Beschluss über die Ermächtigung einer genehmigten Kapitalerhöhung vom (?P<authorization_date>{DATE}) gemäss näherer Umschreibung in den Statuten angepasst\. \. Die Generalversammlung hat mit Beschluss vom (?P<conditional_resolution_date>{DATE}) die Statutenbestimmung über die bedingte Kapitalerhöhung vom (?P<conditional_authorization_date>{DATE}) geändert', 'de')
    if m:
        return [event('authorized_and_conditional_capital_clauses_amended', m, 'capital_changed')], ''

    m = match(rf'(?P<name>{NAME}), maintenant président, détient désormais (?P<remaining_count>{COUNT}) parts de CHF (?P<remaining_nominal>{MONEY}) par suite de cession de (?P<transferred_count>{COUNT}) parts de CHF (?P<transferred_nominal>{MONEY}) à (?P<recipient>{NAME}), de (?P<recipient_origin>{NAME}), au (?P<recipient_place>{NAME}), nouvel associé-gérant pour (?P<recipient_count>{COUNT}) parts de CHF (?P<recipient_nominal>{MONEY})')
    if m:
        return [event('share_transfer_president_and_new_manager', m, 'ownership_changed', currency='CHF'), person('shareholder_now_president', m, m['name'], 'Präsident'), person('shareholder_manager_appointed', m, m['recipient'], 'Geschäftsführer', place=m['recipient_place'])], ''

    m = match(rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que le membre du conseil (?P<name>{NAME}), n'est en réalité plus président")
    if m:
        return [person('council_presidency_corrected', m, m['name'], previous_role='Präsident', presidency_ended=True)], ''

    m = match(r'Wiedereintragung der Zweigniederlassung von Amtes wegen infolge irrtümlicher Löschung\. Firma Hauptsitz neu: (?P<principal_name>[^()]+?) \((?P<principal_translation1>[^()]+)\) \((?P<principal_translation2>[^()]+)\)', 'de')
    if m:
        return [event('branch_reinstated_principal_name_changed', m)], ''

    m = match(rf'\((?P<translation1>[^()]+ in Liquidation)\) \((?P<translation2>[^()]+ in liquidation)\)\. (?P<name>{NAME}), désormais à (?P<place>{NAME}), est élu liquidateur')
    if m:
        return [event('liquidation_name_translations', m), person('liquidator_elected_new_residence', m, m['name'], 'Liquidator', place=m['place'])], ''

    m = match(rf'persona iscritta corretta: (?P<surname>{NAME}), (?P<given_names>{NAME}), cittadino (?P<nationality>{NAME}), in (?P<place>{NAME}), membro, con firma individuale', 'it')
    if m:
        return [person('registered_member_corrected', m, m['surname'] + ' ' + m['given_names'], 'Mitglied', 'Einzelunterschrift', m['place'])], ''

    m = match(rf'Wiedereintragung der Zweigniederlassung von Amtes wegen infolge irrtümlicher Löschung \[Berichtigung des im SHAB Nr\. (?P<notice_number>{COUNT}) vom (?P<notice_date>{DATE}) publizierten TR-Eintrags Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE})\]', 'de')
    if m:
        return [event('branch_erroneous_deletion_reinstated_reference', m)], ''

    m = match(rf'(?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), FRA et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), sont membres du conseil de fondation, sans signature')
    if m:
        return [person('foundation_members_unsigned', m, m[f'name{i}'], 'Stiftungsrat', 'ohne Zeichnungsberechtigung', m[f'place{i}']) for i in (1, 2)], ''

    m = match(rf'Nouvel administateur sans signature: (?P<name>{NAME}), de et à (?P<place>{NAME})')
    if m:
        return [person('administrator_appointed_unsigned_typo', m, m['name'], 'Verwaltungsrat', 'ohne Zeichnungsberechtigung', m['place'], origin=m['place'])], ''

    # The malformed notice date is retained verbatim, never repaired or treated as a valid date.
    m = match(rf"L'inscription N° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date_raw>\d{{2}}\.\d{{4}}\.\d{{2}})\) est rectifiée en ce sens que le nom de famille de la présidente est (?P<name>{NAME}) \(et non pas (?P<previous_name>[^()]+)\)")
    if m:
        return [person('president_name_corrected_malformed_notice_date', m, m['name'], 'Präsident')], ''

    french_date = r'\d{1,2}(?:er)? (?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre) \d{4}'
    m = match(rf"Statuts modifiés le (?P<statutes_date_text>{french_date})\. Création autorisée d'un capital-participation fondée sur la décision d'autorisation du (?P<authorization_date_text>{french_date})\. Capital-participation entièrement libéré: CHF (?P<previous_capital>{MONEY}), divisé en (?P<previous_count>{COUNT}) bons de participation nominatifs de CHF (?P<previous_nominal>{MONEY}), Le conseil d'administration a modifié une clause statutaire relative à la création autorisée du capital-participation \(selon décision d'autorisation de l'assemblée générale du (?P<authorized_meeting_date_text>{french_date})\), par décision du (?P<authorized_board_date_text>{french_date}), pour le détail cf\. statuts\. Augmentation conditionnelle du capital-participation fondée sur la décision relative à l'octroi de droits du (?P<rights_date_text>{french_date})\. Nouveau capital-participation entièrement libéré: CHF (?P<capital>{MONEY}), divisé en (?P<count>{COUNT}) bons de participation nominatifs de CHF (?P<nominal>{MONEY}), avec restrictions quant à la transmissibilité selon statuts\. Le conseil d'administration a modifié une clause statutaire relative à la création conditionnelle du capital-participation \(selon décision relative à l'octroi de droits de l'assemblée générale du (?P<conditional_meeting_date_text>{french_date})\), par décision du (?P<conditional_board_date_text>{french_date}), pour le détail cf\. statuts")
    if m:
        original = leftover.replace(
            ", Le conseil d'administration", ", avec restrictions quant à la transmissibilité selon statuts. Le conseil d'administration", 1)
        if original not in source_text:
            return [], leftover
        return [event('authorized_and_conditional_participation_capital', m, 'capital_changed', currency='CHF', transfer_restricted=True)], ''

    m = match(rf'Diese infolge Konkurses im Sinne von Art\. 159 Abs\. 5 lit\. a HRegV am (?P<deletion_date>{DATE}) von Amtes wegen gelöschte Gesellschaft wird gemäss Entscheid des zuständigen Einzelgerichts vom (?P<decision_date>{DATE}) wieder in das Handelsregister eingetragen\. \[bisher: Nachdem kein begründeter Einspruch gegen die Löschung erhoben wurde, wird die Gesellschaft im Sinne von Art\. 159 Abs\. 5 lit\. a HRegV von Amtes wegen gelöscht\.\]', 'de')
    if m:
        return [event('court_order_reinstatement_after_bankruptcy_deletion', m)], ''

    return [], leftover
