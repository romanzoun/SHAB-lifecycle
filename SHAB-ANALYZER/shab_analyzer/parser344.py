from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, COUNT


def extract_parser344_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete residual clauses without replacing earlier events."""
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

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **{k: v for k, v in m.groupdict().items() if k not in ('name', 'place')}, **extra})

    m = match(rf'(?P<statutes_date>{DATE})\. \[Streichung der Statutenbestimmung über die genehmigte Kapitalerhöhung infolge Ablaufs der zeitlichen Befristung\.\] \. \[Streichung der Statutenbestimmung über die bedingte Kapitalerhöhung infolge Erlöschens der Optionsrechte\.\]', 'de')
    if m:
        # The preceding parser consumed the heading and first (duplicate) date.
        if f"Statutenänderung: {m['statutes_date']}. {m['statutes_date']}." in source_text:
            return [event('authorized_capital_clause_expired', m, 'capital_changed'), event('conditional_capital_clause_options_expired', m, 'capital_changed')], ''

    m = match(r'Statuts modifiés les (?P<day1>\d{1,2}) juin et (?P<day2>\d{1,2}) juillet (?P<year>\d{4})')
    if m:
        try:
            dates = [datetime(int(m['year']), month, int(m[key])).strftime('%d.%m.%Y') for month, key in ((6, 'day1'), (7, 'day2'))]
        except ValueError:
            return [], leftover
        return [event('statutes_amended_multiple_dates', m, statutes_dates=dates)], ''

    m = match(rf'Eingetragene Person geändert: (?P<name>{NAME}), Kollektivunterschrift zu zweien, neu Einzelunterschrift', 'de')
    if m:
        return [person('registered_person_signing_changed', m, m['name'], signing='Einzelunterschrift', previous_signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf'La reprise de biens envisagée à la constitution consistant en un bien immobilier correspondant à la parcelle (?P<parcel>\d+) de la Commune de (?P<municipality>{NAME}) a été réalisée par contrat du (?P<agreement_date>{DATE}) pour le prix de CHF (?P<price>{MONEY})')
    if m:
        return [event('planned_property_acquisition_completed', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\) est rectifiée dans ce sens: (?P<name>{NAME}), administrateur, président, signature collective à deux, est domicilié à (?P<place>[^()]+) \(et non pas à (?P<previous_place>[^()]+)\)")
    if m:
        return [person('board_president_residence_corrected', m, m['name'], 'Präsident', 'Kollektivunterschrift zu zweien', m['place'], additional_role='Verwaltungsrat')], ''

    m = match(rf'Nouvel associé: (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), sans signature sociale')
    if m:
        return [person('associate_appointed_without_signing', m, m['name'], 'Gesellschafter', 'ohne Zeichnungsberechtigung', m['place'])], ''

    m = match(rf'Le gérant (?P<name1>{NAME}), signe désormais collectivement à deux\. Nouveaux gérants: (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<country2>[A-Z]{{3}}) et (?P<name3>{NAME}), de et à (?P<place3>{NAME}), président, lesquels signent individuellement')
    if m:
        return [person('manager_signing_changed', m, m['name1'], 'Geschäftsführer', 'Kollektivunterschrift zu zweien'), person('manager_appointed', m, m['name2'], 'Geschäftsführer', 'Einzelunterschrift', m['place2'], origin=m['origin2']), person('manager_president_appointed', m, m['name3'], 'Geschäftsführer', 'Einzelunterschrift', m['place3'], origin=m['place3'], additional_role='Präsident')], ''

    m = match(rf"Les membres du conseil d'administration (?P<name1>{NAME}), (?P<name2>{NAME}), (?P<name3>{NAME}), (?P<name4>{NAME}) et (?P<name5>{NAME}), signent désormais collectivement à deux")
    if m:
        return [person('board_member_signing_changed', m, m[f'name{i}'], 'Verwaltungsrat', 'Kollektivunterschrift zu zweien') for i in range(1, 6)], ''

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name1>{NAME}), membre du comité, continue de signer collectivement à deux\. (?P<name2>{NAME}), membre et trésorière du comité, exerce désormais la signature sociale, collectivement à deux")
    if m:
        return [person('committee_member_signing_corrected', m, m['name1'], 'Vorstand', 'Kollektivunterschrift zu zweien'), person('committee_treasurer_signing_granted', m, m['name2'], 'Vorstand', 'Kollektivunterschrift zu zweien', additional_role='Kassierin')], ''

    m = match(rf'Mit Entscheid des zuständigen Einzelgerichts vom (?P<decision_date>{DATE}) wurde über die bereits aufgelöste Gesellschaft mit Wirkung ab dem (?P<effective_date>{DATE}), (?P<effective_time>\d{{2}}:\d{{2}}) Uhr, der Konkurs wieder eröffnet', 'de')
    if m:
        try:
            datetime.strptime(m['effective_time'], '%H:%M')
        except ValueError:
            return [], leftover
        return [event('bankruptcy_reopened_dissolved_company', m)], ''

    m = match(r'Sede principale a: Sede principale: (?P<head_office>[^()]+) \((?P<country>[A-Z]{2})\)\. Nuove disposizioni per la succursale: La succursale è soppressa a seguito della radiazione della sede principale, ma la cancellazione non può essere effettuata mancando il consenso delle autorità fiscali federali e cantonali', 'it')
    if m:
        return [event('branch_suppressed_deletion_pending_tax_consent', m, deletion_completed=False)], ''

    m = match(rf'Die Gründungsstatuten datieren vom (?P<statutes_date>{DATE}), nicht vom (?P<previous_statutes_date>{DATE})', 'de')
    if m:
        return [event('founding_statutes_date_corrected', m)], ''

    return [], leftover
