from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY


def extract_parser351_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete sample-backed residues after all earlier parsers."""
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
            except ValueError:
                return None
        return m

    def event(action, m, **extra):
        return _event(*context, 'organization_changed', f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'fr.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **m.groupdict(), **extra, 'name': name})

    def number(m, key):
        return Decimal(m[key].replace("'", ''))

    m = match(rf"Les associés gérants (?P<name1>{NAME}), jusqu'ici président, et (?P<name2>{NAME}), nommé président, continuent à signer individuellement")
    if m:
        return [person('associate_managers_presidency_changed', m, m['name1'], 'Geschäftsführer', 'Einzelunterschrift', previous_role='président'), person('associate_managers_presidency_changed', m, m['name2'], 'Vorsitzender der Geschäftsführung', 'Einzelunterschrift')], ''

    # Initials in this non-representative branch registration list contain dots.
    m = match(r"Suite à la modification du droit du registre du commerce et en application de l'art\. 114 al\. 1, lit\. f ORC, les informations relatives aux personnes qui ne sont pas habilitées à représenter la succursale sont radiées\. Par conséquent, l'inscription de (?P<name1>[^,;]+), (?P<name2>[^,;]+), (?P<name3>[^,;]+), (?P<name4>[^,;]+) et (?P<name5>[^,;.]+) est radiée")
    if m:
        return [person('branch_non_representative_registration_deleted', m, m[f'name{i}'], registration_deleted=True) for i in range(1, 6)], ''

    m = match(rf"Division de (?P<old_count>{COUNT}) actions jusqu'ici de CHF (?P<old_nominal>{MONEY}) en (?P<new_count>{COUNT}) actions de CHF (?P<new_nominal>{MONEY})\. Capital-actions: CHF (?P<capital>{MONEY}), entièrement libéré, divisé en (?P<other_count>{COUNT}) actions de CHF (?P<other_nominal>{MONEY}) et (?P=new_count) actions de CHF (?P=new_nominal), toutes nominatives")
    if m and all(number(m,k)>0 for k in ('old_count','old_nominal','new_count','new_nominal','capital','other_count','other_nominal')) and number(m,'old_count')*number(m,'old_nominal') == number(m,'new_count')*number(m,'new_nominal') and number(m,'capital') == number(m,'other_count')*number(m,'other_nominal')+number(m,'new_count')*number(m,'new_nominal'):
        return [event('registered_shares_split_composition', m, currency='CHF')], ''

    m = match(rf'(?P<name1>{NAME}), de et à (?P<place1>{NAME}) et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), sont membres du conseil de fondation')
    if m:
        return [person('foundation_board_members_appointed', m, m[f'name{i}'], 'Stiftungsrat', place=m[f'place{i}'], origin=m['place1'] if i == 1 else m['origin2']) for i in (1, 2)], ''

    m = match(rf"L'inscription N°(?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est corrigée en ce sens que (?P<name>{NAME}) n'est pas sous-directrice mais directrice adjointe")
    if m:
        return [person('deputy_director_role_corrected', m, m['name'], 'stellvertretende Direktorin', previous_role='sous-directrice')], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens qu'une signature collective à deux est conféré à (?P<name>{NAME}), gérant \(et non une signature individuelle, comme publié\)")
    if m:
        return [person('manager_collective_signing_corrected', m, m['name'], 'Geschäftsführer', 'Kollektivunterschrift zu zweien', previous_signing='signature individuelle')], ''

    m = match(rf"(?P<name1>{NAME}) a cédé (?P<transferred_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) au nouvel associé (?P<name2>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME})\. Par conséquent, (?P=name1) est désormais titulaire de (?P<remaining_count>{COUNT}) parts de CHF (?P=nominal)\. Gérants: (?P=name1), nommé président, lequel continue de signer individuellement et (?P=name2)")
    if m and all(number(m,k)>0 for k in ('transferred_count','nominal','remaining_count')):
        return [event('associate_shares_transferred_managers', m, currency='CHF'), person('associate_manager_president_appointed', m, m['name1'], 'Vorsitzender der Geschäftsführung', 'Einzelunterschrift'), person('associate_manager_appointed', m, m['name2'], 'Geschäftsführer', place=m['place'], origin=m['origin'])], ''

    uid = r'CHE-\d{3}\.\d{3}\.\d{3}'
    m = match(rf'(?P<company1>{NAME}) \((?P<uid1>{uid})\) cède (?P<transferred_count>{COUNT}) de ses (?P<old_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<company2>{NAME}) \((?P<uid2>{uid})\), désormais titulaire de (?P<recipient_count>{COUNT}) parts de CHF (?P=nominal)\. (?P=company1) \((?P=uid1)\) a désormais (?P<remaining_count>{COUNT}) parts de CHF (?P=nominal)')
    if m and all(number(m,k)>0 for k in ('transferred_count','old_count','nominal','recipient_count','remaining_count')) and number(m,'old_count') == number(m,'transferred_count')+number(m,'remaining_count') and number(m,'recipient_count') >= number(m,'transferred_count'):
        return [event('corporate_associate_shares_transferred', m, currency='CHF')], ''

    m = match(rf'Das unter der TR Nr\. (?P<entry>\d+) vom (?P<entry_date>{DATE}) gelöschte Einzelunternehmen wird auf Antrag des Inhabers gemäss Art\. 116 Abs\. 3 lit\. b HRegV wieder in das Handelsregister eingetragen\. \[gestrichen: Das Einzelunternehmen wird infolge Fehlens der gesetzlichen Voraussetzungen der Eintragungspflicht auf Begehren des Inhabers im Handelsregister gelöscht\.\]', 'de')
    if m:
        return [event('sole_proprietorship_reinstated_owner_request', m)], ''

    m = match(rf"La part sociale de CHF (?P<old_nominal>{MONEY}) est transformée en (?P<count>{COUNT}) parts sociales de CHF (?P<nominal>{MONEY}), détenues par l'associé-gérant (?P<name>{NAME})")
    if m and all(number(m,k)>0 for k in ('old_nominal','count','nominal')) and number(m,'old_nominal') == number(m,'count')*number(m,'nominal'):
        return [event('associate_share_split', m, currency='CHF')], ''

    # French wording with German XML metadata, as supplied; retain French rule IDs.
    m = match(rf"L'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), Id\. (?P<notice_id>\d+)\) est rectifiée dans ce sens: (?P<name1>{NAME}), gérant, signature collective à deux \(et non pas gérant, président, signature collective à deux\); (?P<name2>{NAME}), gérant, président, signature collective à deux \(et non pas gérant, signature collective à deux\)", language if language in ('de', 'fr') else 'fr')
    if m:
        return [person('managers_presidency_corrected', m, m['name1'], 'Geschäftsführer', 'Kollektivunterschrift zu zweien', previous_role='gérant, président'), person('managers_presidency_corrected', m, m['name2'], 'Vorsitzender der Geschäftsführung', 'Kollektivunterschrift zu zweien', previous_role='gérant')], ''

    m = match(rf"(?P<name1>{NAME}) et (?P<name2>{NAME}), jusqu'ici directeurs, maintenant membre de la direction, continuent à signer collectivement à deux")
    if m:
        return [person('directors_now_management_members', m, m[f'name{i}'], 'Mitglied der Geschäftsleitung', 'Kollektivunterschrift zu zweien', previous_role='directeur') for i in (1, 2)], ''

    return [], leftover
