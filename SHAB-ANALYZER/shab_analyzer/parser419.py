from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY
from .parser409 import NAME
from .parser99 import _FR_DOMICILE_CORRECTED
from .parser135 import _FR_FOUNDATION_DISSOLVED_FIVE_LIQUIDATORS
from .parser140 import _DE_LEGACY_BRANCH_REMOVED_NESTED_LABELS
from .parser112 import _FR_BANKRUPTCY_APPEAL_SUSPENSIVE_EFFECT

_LEGACY = (_FR_DOMICILE_CORRECTED, _FR_FOUNDATION_DISSOLVED_FIVE_LIQUIDATORS,
           _DE_LEGACY_BRANCH_REMOVED_NESTED_LABELS, _FR_BANKRUPTCY_APPEAL_SUSPENSIVE_EFFECT)


def extract_parser419_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
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

    m = match(rf'Sitz neu: (?P<place>{NAME})\. \[(?P<reason>Anpassung des Sitzes infolge Namenänderung der Gemeinde)\]', 'de')
    if m:
        return [event('registered_office_municipality_namenaenderung', m)], ''

    m = match(rf"Selon décision de l'(?P<authority>Autorité cantonale de surveillance des fondations et des institutions de prévoyance) du (?P<decision_date>{DATE}), la fondation est dissoute\. Liquidateurs: les membres du conseil (?P<name1>{NAME}), président, (?P<name2>{NAME}), vice-présidente, (?P<name3>{NAME}), secrétaire, (?P<name4>{NAME}), (?P<name5>{NAME}) et (?P<name6>{NAME}), tous ; les pouvoirs de (?P=name5) sont modifiés en ce sens")
    if m and leftover.split('. Liquidateurs:', 1)[0] in source_text and ('Liquidateurs:' + leftover.split('. Liquidateurs:', 1)[1]).replace('tous ;', 'tous avec signature collective à deux;') in source_text:
        return [event('foundation_dissolved_six_council_liquidators', m, 'status_changed'),
                *[person('six_council_liquidators_collective', m, m[f'name{i}'], 'liquidateur', 'Kollektivunterschrift zu zweien', council_role={1: 'président', 2: 'vice-présidente', 3: 'secrétaire'}.get(i), signing_changed=i == 5) for i in range(1, 7)]], ''

    m = match(rf"Les membres du comité (?P<name1>{NAME}), jusqu'ici secrétaire, et (?P<name2>{NAME}), jusqu'ici trésorière, nommée secrétaire, signent désormais collectivement à deux, avec un membre du comité\. (?P<name3>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), est membre et trésorière du comité et signe collectivement à deux, avec un membre du comité")
    if m:
        return [person('committee_signing_with_committee_member', m, m[f'name{i}'], {1: 'membre du comité', 2: 'secrétaire', 3: 'membre et trésorière du comité'}[i], 'Kollektivunterschrift zu zweien', m['place'] if i == 3 else None, signing_partner_role='membre du comité', previous_role={1: 'secrétaire', 2: 'trésorière'}.get(i)) for i in range(1, 4)], ''

    m = match(rf'\((?P<translated_name>[^;\n]+ in liquidation)\), par (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), et (?P<name2>{NAME}), des (?P<origin2>{NAME}), à (?P<place2>{NAME}), sans signature, les deux liquidateurs')
    if m and leftover.replace(f"à {m['place1']}, et", f"à {m['place1']}, avec signature individuelle, et", 1) in source_text:
        return [event('association_liquidation_translated_name', m),
                person('association_two_liquidators_distinct_signing', m, m['name1'], 'liquidateur', 'Einzelunterschrift', m['place1']),
                person('association_two_liquidators_distinct_signing', m, m['name2'], 'liquidateur', 'ohne Zeichnungsberechtigung', m['place2'])], ''

    m = match(rf"Administration: (?P<name1>{NAME}), jusqu'ici directeur, nommé président, et (?P<name2>{NAME}), nommé vice-président, lesquels continuent à signer individuellement")
    if m:
        return [person('director_to_president_and_vice_president', m, m[f'name{i}'], 'président' if i == 1 else 'vice-président', 'Einzelunterschrift', previous_role='directeur' if i == 1 else None) for i in (1, 2)], ''

    m = match(rf'(?P<name1>{NAME}), (?P<name2>{NAME}), (?P<name3>{NAME}), qui est maintenant à (?P<place>{NAME}), et (?P<name4>{NAME}) signent désormais individuellement')
    if m:
        return [person('four_individual_signatures_one_residence', m, m[f'name{i}'], signing='Einzelunterschrift', place=m['place'] if i == 3 else None) for i in range(1, 5)], ''

    m = match(r'Zweigniederlassung neu: \[Folgende Zweigniederlassung ist bereits seit (?P<removed_since>Mai \d{4}) aufgehoben worden:\] \[gestrichen: (?P<place>[^()\]\n]+) \((?P<branch_id>CH-\d{3}\.\d\.\d{3}\.\d{3}-\d)\)\]', 'de')
    if m:
        return [event('branch_historical_removal_month', m, historical_annotation=True)], ''

    m = match(rf"Par arrêt du (?P<order_date>{DATE}), le (?P<court>Tribunal cantonal de Fribourg) a accordé l'effet suspensif au recours interjeté le (?P<appeal_date>{DATE}) contre la décision du (?P<decision_date>{DATE}) \((?P<legal_basis>art\. 159, al\. 1 let\. b ORC)\)")
    if m:
        return [event('bankruptcy_appeal_suspensive_effect_article159_1b', m, 'status_changed')], ''

    m = match(r'Das Einzelunternehmen wird auf Begehren der Inhaberin wieder im Handelsregister eingetragen\. \[bisher: Löschungsgrund: (?P<previous_deletion_reason>Das Einzelunternehmen wird infolge Fehlens der gesetzlichen Voraussetzungen der Eintragungspflicht auf Begehren der Inhaberin gelöscht\.)\]', 'de')
    if m:
        return [event('sole_proprietorship_reentered_at_owner_request', m, 'status_changed')], ''

    m = match(rf"(?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), d'(?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé-gérant titulaire de (?P=count) parts de CHF (?P=nominal), président")
    if m and 'nouvel associé-gérant avec signature individuelle, titulaire' in source_text and leftover.replace('nouvel associé-gérant titulaire', 'nouvel associé-gérant avec signature individuelle, titulaire') in source_text:
        if int(m['count'].replace("'", '')) >= int(m['before'].replace("'", '')):
            return [], text
        return [event('partial_transfer_new_manager_president', m, 'ownership_changed', currency='CHF'), person('new_associate_manager_president_transfer', m, m['buyer'], 'associé-gérant président', 'Einzelunterschrift', m['place'])], ''

    m = match(rf"(?P<name1>{NAME}), du (?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<country1>[A-Z]{{3}}), président, et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<country2>[A-Z]{{3}}), avec signature individuelle sont membres du conseil d'administration")
    if m and leftover.replace('président, et', 'président, avec signature collective à deux, et', 1) in source_text:
        return [person('board_pair_distinct_signing_country_codes', m, m[f'name{i}'], 'président' if i == 1 else "membre du conseil d'administration", 'Kollektivunterschrift zu zweien' if i == 1 else 'Einzelunterschrift', m[f'place{i}'], country=m[f'country{i}']) for i in (1, 2)], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que le domicile exact d'(?P<name>{NAME}) est (?P<place>{NAME}) \(et non (?P<previous_place>{NAME}) comme publié\)")
    if m:
        return [person('domicile_corrected_notice_reference', m, m['name'], place=m['place'], corrected=True)], ''
    return [], text
