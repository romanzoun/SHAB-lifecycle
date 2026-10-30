from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, NAME
from . import parser55, parser60


def extract_parser442_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete evidenced variants, retaining historical rule ownership."""
    if any(p.search(text) for p in (parser55._FR_STANDALONE_GROUP_SIGNING,
                                    parser60._FR_SHARE_TRANSFER_RESTRICTION)):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', text.strip())
        if m:
            try:
                for date in re.findall(DATE, m[0]):
                    datetime.strptime(date, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def person(action, name, *, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.persons.{action}.v1', name,
                             role=role, signing=signing, place=place, extra={'action': action, **extra})

    m = match(r'\[Weitere Adresse wird im Handelsregister gestrichen\] \[gestrichen: Weitere Geschäftsadresse: (?P<street>[^,;]+), (?P<postal_code>\d{4}) (?P<place>[^\[\];]+)\]', 'de')
    if m:
        return [_event(*context, 'address_changed', 'de.text.additional_business_address_deleted_bracketed.v1',
                       {'action': 'additional_business_address_deleted_bracketed', **m.groupdict(), 'deleted': True})], ''

    m = match(rf"Par décision du président du Tribunal de l'arrondissement de (?P<court_place>[^,.;]+) du (?P<decision_date>{DATE}), la société a été déclarée dissoute conformément aux articles (?P<legal_basis>154 aORC et 908 CO); sa liquidation a été ordonnée selon les dispositions applicables à la faillite")
    if m:
        return [_event(*context, 'status_changed', 'fr.text.cooperative_court_dissolution_908.v1',
                       {'action': 'cooperative_court_dissolution_908', **m.groupdict(), 'dissolved': True, 'bankruptcy_liquidation': True})], ''

    m = match(rf'Eingetragene Person geändert: (?P<name>{NAME}), Verwaltungsratsmitglied, Sekretär, Kollektivunterschrift zu zweien, neu Verwaltungsratsmitglied, Sekretär, Einzelunterschrift', 'de')
    if m:
        return [person('board_secretary_individual_signing_changed', m['name'], role='Verwaltungsratsmitglied, Sekretär', signing='Einzelunterschrift', previous_signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que la vice-présidente s'appelle (?P<name>{NAME}) \(et non pas (?P<previous_name>{NAME})\)")
    if m:
        return [person('vice_president_name_corrected_without_notice', m['name'], role='vice-présidente', **{k: v for k, v in m.groupdict().items() if k != 'name'})], ''

    m = match(rf'Administration: (?P<name1>{NAME}), nommé président, et (?P<name2>{NAME}), de et à (?P<place2>{NAME}), vice-président, lesquels signent individuellement')
    if m:
        return [person('president_appointed_shared_individual_signing', m['name1'], role='président', signing='Einzelunterschrift'),
                person('vice_president_shared_origin_residence_individual_signing', m['name2'], role='vice-président', signing='Einzelunterschrift', place=m['place2'], origin=m['place2'])], ''
    return [], text
