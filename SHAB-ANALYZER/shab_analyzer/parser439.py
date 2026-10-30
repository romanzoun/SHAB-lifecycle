from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY
from .parser409 import NAME
from . import parser55, parser60, parser168, parser226

_LEGACY = (parser55._FR_STANDALONE_GROUP_SIGNING,
           parser60._FR_SHARE_TRANSFER_RESTRICTION,
           parser168._FR_ASSOCIATION_DISSOLVED_COMMITTEE_LIQUIDATORS,
           parser226._FR_ASSOCIATION_DISSOLVED_COLLECTIVE_LIQUIDATORS)


def extract_parser439_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete evidenced variants, preserving historical ownership."""
    leftover = text.strip()
    if any(pattern.search(leftover) for pattern in _LEGACY):
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

    def event(action, m, event_type='organization_changed', **extra):
        return _event(*context, event_type, f'{language}.text.{action}.v1',
                      {'action': action, **m.groupdict(), **extra})

    def person(action, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.persons.{action}.v1',
                             name, role=role, signing=signing, place=place,
                             extra={'action': action, **extra})

    m = match(rf"(?P<name>{NAME}) continue de signer collectivement à deux, désormais avec (?P<partner1>{NAME}), (?P<partner2>{NAME}) et (?P<partner3>{NAME})\. (?P<proxy1>{NAME}), (?P<proxy2>{NAME}), (?P<proxy3>{NAME}) et (?P<proxy4>{NAME}) continuent d'engager la société par leur procuration collective à deux, désormais avec avec (?P=partner1), (?P=partner2) et (?P=partner3)")
    if m:
        partners = [m[f'partner{i}'] for i in (1, 2, 3)]
        return [person('continued_signing_named_partners', m['name'], signing='Kollektivunterschrift zu zweien', signing_partners=partners)] + [person('continued_proxy_named_partners_duplicate_avec', m[f'proxy{i}'], signing='Kollektivprokura zu zweien', signing_partners=partners) for i in range(1, 5)], ''

    m = match(rf'Geslöschte Person: (?P<old_name>{NAME}), Gesellschafterin, Geschäftsführerin, Einzelunterschrift\. Neu eingetragene Person: (?P<name>{NAME}), von (?P<origin>{NAME}), in (?P<place>{NAME}), Gesellschafter, (?P<count>{COUNT}) Stammanteile zu CHF (?P<nominal>{MONEY}), Geschäftsführer, Einzelunterschrift')
    if m:
        return [person('removed', m['old_name'], 'Gesellschafterin, Geschäftsführerin', 'Einzelunterschrift'), person('appointed', m['name'], 'Gesellschafter, Geschäftsführer', 'Einzelunterschrift', m['place'], origin=m['origin'], share_count=m['count'], share_nominal=m['nominal'], currency='CHF')], ''

    # The three-digit year is retained verbatim; no corrected effective date is inferred.
    m = match(rf'Par arrêt du (?P<decision_date>{DATE}), Le président du Tribunal cantonal de la Cour des poursuites et faillites a rejeté le recours, et confirmé le jugement de faillite du (?P<judgment_date>{DATE}) prend effet le (?P<effective_date_raw>\d{{2}}\.\d{{2}}\.\d{{3}}), à (?P<effective_time>(?:[01]\d|2[0-3])h[0-5]\d)\. La raison de commerce redevient (?P<name>[^\n]+ en liquidation)')
    if m:
        return [event('bankruptcy_appeal_rejected_truncated_effective_year', m, 'status_changed', appeal_rejected=True, bankruptcy_confirmed=True)], ''

    def member(i):
        return rf'(?P<name{i}>{NAME}), (?:de|du) (?P<origin{i}>{NAME}), à (?P<place{i}>{NAME})'

    m = match(rf'Procuration collective à deux, sans autre restriction, a été conférée à (?P<name1>{NAME}), (?P<name2>{NAME}), maintenant domiciliée à (?P<place2>{NAME}), (?P<country2>[A-Z]{{3}}), et (?P<name3>{NAME}); leurs pouvoirs sont modifiés en ce sens\. Procuration collective à deux, sauf entre eux, a été conférée à ' + member(4) + ', ' + member(5) + r', (?P<country5>[A-Z]{3}), ' + member(6) + ', ' + member(7) + r', (?P<country7>[A-Z]{3}), et ' + member(8) + r', (?P<country8>[A-Z]{3})')
    if m:
        events = []
        for i in range(1, 9):
            extra = {key[:-1]: value for key, value in m.groupdict().items() if key.endswith(str(i)) and not key.startswith(('name', 'place'))}
            events.append(person('proxy_powers_changed' if i <= 3 else 'proxy_granted', m[f'name{i}'], signing='Kollektivprokura zu zweien', place=m.groupdict().get(f'place{i}'), signing_restriction='sans autre restriction' if i <= 3 else 'sauf entre eux', **extra))
        return events, ''

    m = match(member(1) + ', président, ' + member(2) + r", (?P<country2>[A-Z]{3}), et " + member(3) + r", sont membres du conseil d'administration, tous trois")
    if m:
        # A preceding parser can have removed the group signing clause. Only use
        # signing evidence adjacent to this exact residual, never unrelated text.
        signing = 'Kollektivunterschrift zu zweien' if leftover.rstrip('.') + ' avec signature collective à deux' in source_text else None
        return [person('board_members_president_foreign_residence', m[f'name{i}'], 'président' if i == 1 else "membre du conseil d'administration", signing, m[f'place{i}'], origin=m[f'origin{i}'], **({'country': m['country2']} if i == 2 else {})) for i in (1, 2, 3)], ''

    m = match('Nachtrag der Belege', 'de')
    if m:
        return [event('supporting_documents_supplement', m)], ''

    m = match(rf"L'association est dissoute par décision de l'assemblée générale du (?P<decision_date>{DATE})\. Liquidateurs: les membres du comité (?P<name1>{NAME}), président, (?P<name2>{NAME}), secrétaire et (?P<name3>{NAME}), trésorière, lesquels continuent à signer collectivement à deux")
    if m:
        return [event('association_dissolved_three_committee_liquidators', m, 'status_changed', dissolved=True)] + [person('liquidator_appointed_continued_collective_signing', m[f'name{i}'], 'Liquidator', 'Kollektivunterschrift zu zweien', committee_role=role) for i, role in ((1, 'président'), (2, 'secrétaire'), (3, 'trésorière'))], ''
    return [], text
