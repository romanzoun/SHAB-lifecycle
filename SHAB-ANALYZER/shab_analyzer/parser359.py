from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, MONEY

PERSON = r'[^,;.]+?'


def extract_parser359_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete residual clauses after all existing parser rules."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', required=()):
        if language != lang or any(fragment not in source_text for fragment in required):
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

    def person(action, m, name=None, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name or m['name'], place=m.groupdict().get('place') if place is None else place, role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra})

    m = match(rf'Nouveau membre du conseil de fondation avec le président ou les vices-présidents: (?P<name>{PERSON}), de (?P<origin>{PERSON}), à (?P<place>{PERSON}), secrétaire générale', required=(leftover.replace('Nouveau membre du conseil de fondation avec le président', 'Nouveau membre du conseil de fondation avec signature collective à deux avec le président'),))
    if m:
        return [person('foundation_secretary_restricted_collective_signing', m, role='Mitglied des Stiftungsrates, Sekretär', signing='Kollektivunterschrift zu zweien', signing_restriction='avec le président ou les vices-présidents')], ''

    m = match(rf'Par arrêt du (?P<decision_date>{DATE}), le Tribunal cantonal a annulé le jugement de faillite rendu le (?P<bankruptcy_date>{DATE})')
    if m:
        return [event('cantonal_court_bankruptcy_judgment_annulled', m)], ''

    m = match(r'Indirizzo della liquidazione: (?P<address>[^\n]+?)\. \[radiati: Indirizzo della liquidazione: (?P<previous_address>[^\n]+?)\.\]', 'it')
    if m:
        return [event('liquidation_address_replaced', m)], ''

    m = match(rf"L'associée (?P<transferor>{PERSON}) \((?P<register_id>[^()]+)\) a cédé (?P<transferred>\d+) parts de CHF (?P<nominal>{MONEY}) à l'associée-gérante (?P<recipient>{PERSON}) qui possède désormais (?P<recipient_count>\d+) parts de CHF (?P=nominal)")
    if m:
        return [event('corporate_associate_shares_transferred_to_manager', m, currency='CHF')], ''

    m = match(rf"L'inscription no (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que le siège demeure à (?P<place>{PERSON})")
    if m:
        return [event('registered_seat_retained_correction', m)], ''

    m = match(rf"Par suite de restructuration, l'associée devient: (?P<associate_name>[^()]+?) \((?P<register_id>[^()]+)\), à (?P<place>{PERSON}) \((?P<country>[^()]+)\)")
    if m:
        return [event('associate_changed_by_restructuring', m)], ''

    m = match(rf'(?P<transferor>{PERSON}) a cédé (?P<transferred>\d+) parts de CHF (?P<nominal>{MONEY}) à (?P<recipient>{PERSON}), de (?P<origin>{PERSON}), à (?P<place>{PERSON}), nouvel associé pour (?P=transferred) parts de CHF (?P=nominal); par conséquent (?P=transferor) est maintenant associé pour (?P<remaining>\d+) parts de CHF (?P=nominal)\. Gérants : les associés (?P=transferor), et (?P=recipient), nommé président, tous deux', required=(leftover + ' avec signature collective à deux; les pouvoirs du premier sont modifiés en ce sens',))
    if m:
        return [event('share_transfer_collective_managers', m, currency='CHF'), person('manager_collective_signing_changed', m, m['transferor'], 'Geschäftsführer', 'Kollektivunterschrift zu zweien', place=''), person('manager_president_collective_signing', m, m['recipient'], 'Vorsitzender der Geschäftsführung', 'Kollektivunterschrift zu zweien')], ''

    m = match(rf'Administration: (?P<name1>{PERSON}), nommé président, lequel continue à signer individuellement, (?P<name2>{PERSON}), de (?P<origin2>{PERSON}), à (?P<place2>{PERSON}), et (?P<name3>{PERSON}), de (?P<origin3>{PERSON}), à (?P<place3>{PERSON}), lesquels signent collectivement à deux')
    if m:
        return [person('board_president_keeps_individual_signing', m, m['name1'], 'Präsident', 'Einzelunterschrift', place='')] + [person('board_member_collective_signing', m, m[f'name{i}'], 'Mitglied des Verwaltungsrates', 'Kollektivunterschrift zu zweien', place=m[f'place{i}']) for i in (2, 3)], ''

    m = match(rf"Rectificatif: l'inscription n°(?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>[\d/]+)\) est rectifiée en ce sens qu'(?P<name>{PERSON}) est secrétaire général hors conseil \(et non membre du conseil de fondation comme publié\)")
    if m:
        return [person('secretary_outside_foundation_board_corrected', m, role='Sekretär ausserhalb des Stiftungsrates', previous_role='Mitglied des Stiftungsrates')], ''

    m = match(rf"L'associée-gérante (?P<transferor>{PERSON}) cède (?P<transferred>\d+) de ses (?P<previous_count>\d+) parts de CHF (?P<nominal>{MONEY}) à (?P<recipient>{PERSON}), de et à (?P<place>{PERSON}), nouvel associé-gérant et président (?P=transferor) reste titulaire de (?P<remaining>\d+) parts de CHF (?P=nominal)")
    if m and leftover.replace(f"nouvel associé-gérant et président {m['transferor']}", f"nouvel associé-gérant et président avec signature individuelle. {m['transferor']}") in source_text:
        return [event('share_transfer_new_presiding_manager', m, currency='CHF'), person('new_presiding_manager_individual_signing', m, m['recipient'], 'Vorsitzender der Geschäftsführung', 'Einzelunterschrift', origin=m['place'])], ''

    m = match(rf"L'associé-gérant (?P<transferor>{PERSON}), jusqu'ici titulaire de (?P<previous_count>\d+) parts de CHF (?P<nominal>{MONEY}), a cédé (?P<transferred>\d+) parts de CHF (?P=nominal) à (?P<recipient>{PERSON}), de et à (?P<place>{PERSON}), nouvel associé pour (?P=transferred) parts de CHF (?P=nominal), lequel signe individuellement\. L'associé (?P=transferor) est maintenant titulaire de (?P<remaining>\d+) parts de CHF (?P=nominal)")
    if m:
        return [event('share_transfer_new_associate_individual_signing', m, currency='CHF'), person('new_associate_individual_signing', m, m['recipient'], 'Gesellschafter', 'Einzelunterschrift', origin=m['place'])], ''

    m = match(rf"L'inscription (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name>{PERSON}) est toujours directrice")
    if m:
        return [person('director_role_retained_correction', m, role='Direktor')], ''

    return [], leftover
