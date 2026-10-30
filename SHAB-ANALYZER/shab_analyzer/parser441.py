from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, NAME
from . import parser55, parser60, parser205

_LEGACY = (parser55._FR_STANDALONE_GROUP_SIGNING,
           parser60._FR_SHARE_TRANSFER_RESTRICTION,
           parser205._FR_MANAGER_NAME_CORRECTED_MISSPELLED_HEADER)


def extract_parser441_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete evidenced variants; preserve historical rule ownership."""
    if any(pattern.search(text) for pattern in _LEGACY):
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

    m = match(rf"Rectificatf: l'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC\. du (?P<notice_date>{DATE}) p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que l'administrateur président se nomme (?P<name>{NAME}) \(et non (?P<previous_name>{NAME}) comme publié\)")
    if m:
        return [person('administrator_president_name_corrected_misspelled_header', m['name'], role='administrateur président', **{k: v for k, v in m.groupdict().items() if k != 'name'}, source_wording='Rectificatf')], ''

    m = match(rf'Signature individuelle a été conférée à (?P<name>{NAME}), du et au (?P<place>{NAME})')
    if m:
        return [person('individual_signing_shared_origin_residence', m['name'], signing='Einzelunterschrift', place=m['place'], origin=m['place'])], ''

    m = match(rf'(?P<name>{NAME}) signe désormais par procuration collective à deux')
    if m:
        return [person('collective_proxy_signing_changed', m['name'], signing='Kollektivprokura zu zweien')], ''

    m = match(rf'Selon décision des associés du (?P<decision_date>{DATE}), la société est dissoute\. La liquidation a été opérée sous la raison de commerce: (?P<name>[^,;]+), en liquidation\. Liquidateurs: les associés (?P<name1>{NAME}) et (?P<name2>{NAME})')
    if m:
        return [_event(*context, 'status_changed', 'fr.text.partnership_dissolved_liquidation_operated.v1',
                       {'action': 'partnership_dissolved_liquidation_operated', **m.groupdict(), 'dissolved': True, 'liquidation_name': m['name'] + ', en liquidation'})] + [person('partner_liquidator_appointed', m[f'name{i}'], role='associé, liquidateur') for i in (1, 2)], ''

    m = match(rf'Persona iscritta corretta: (?P<surname>{NAME}), (?P<given_names>{NAME}), (?P<origin>cittadino italiano), in (?P<place>{NAME}), amministratore unico, con firma individuale', 'it')
    if m:
        return [person('sole_administrator_corrected_italian_citizenship', m['surname'] + ', ' + m['given_names'], role='amministratore unico', signing='Einzelunterschrift', place=m['place'], origin=m['origin'])], ''

    def member(i):
        return rf'(?P<name{i}>{NAME}), de (?P<origin{i}>{NAME}), à (?P<place{i}>{NAME}), signature collective à deux'

    m = match(member(1) + ', et ' + member(2) + ' sont membres du conseil de fondation')
    if m:
        return [person('foundation_members_pair_separate_signing_clauses', m[f'name{i}'], role='membre du conseil de fondation', signing='Kollektivunterschrift zu zweien', place=m[f'place{i}'], origin=m[f'origin{i}']) for i in (1, 2)], ''
    return [], text
