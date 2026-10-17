from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser347_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Append complete, sample-backed clauses after all existing rules."""
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
                    if key == 'time':
                        datetime.strptime(value, '%H:%M')
            except ValueError:
                return None
        return m

    def event(action, m):
        return _event(*context, 'organization_changed', f'{language}.text.{action}.v1', {'action': action, **m.groupdict()})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **m.groupdict(), **extra})

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat der Präsident des Zivilkreisgerichts (?P<court_place>{NAME}) die Verlängerung der definitiven Nachlassstundung um sechs Monate bis (?P<end_date>{DATE}) bewilligt', 'de')
    if m:
        return [event('definitive_moratorium_six_month_extension_approved', m)], ''

    m = match(rf'Gemäss TR (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) wurde (?P<surname>{NAME}), (?P<given_name>{NAME}), von (?P<origin>{NAME}), in (?P<place>{NAME}), Mitglied des Stiftungsrates, mit Kollektivunterschrift zu zweien \[bisher: Mitglied des Stiftungsrates, mit Kollektivunterschrift zu zweien mit dem Präsidenten\] publiziert, korrekt wäre (?P=surname), (?P=given_name), von (?P=origin), in (?P=place), Mitglied des Stiftungsrates, mit Kollektivunterschrift zu zweien \[bisher: Mitglied des Stiftungsrates, mit Kollektivunterschrift zu zweien mit dem Präsidenten, in (?P<previous_place>{NAME})\]', 'de')
    if m:
        return [person('foundation_board_previous_place_corrected', m, m['surname'] + ' ' + m['given_name'], 'Mitglied des Stiftungsrates', 'Kollektivunterschrift zu zweien', m['place'], previous_signing='Kollektivunterschrift zu zweien mit dem Präsidenten')], ''

    m = match(rf"(?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<country1>[A-Z]{{3}}), présidente, et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), avec signature collective à deux, sont membres du conseil d'administration")
    if m:
        return [person('board_president_and_member_collective_signing', m, m[f'name{i}'], 'Präsident' if i == 1 else 'Verwaltungsrat', 'Kollektivunterschrift zu zweien', m[f'place{i}']) for i in (1, 2)], ''

    m = match(rf'Il fallimento è stato revocato con decreto della Pretura del Distretto di (?P<court_place>{NAME}) del (?P<decision_date>{DATE})\. La situazione è ristabilita come in precedenza\. \[radiati: Con decreto della Pretura del Distretto di (?P=court_place) del (?P<moratorium_date>{DATE}) è stata revocata la moratoria a scopo di concordato\. Il titolare è stato dichiarato in fallimento con decreto della Pretura del Distretto di (?P=court_place) del (?P<bankruptcy_date>{DATE}) a far tempo dal (?P<effective_date>{DATE}) alle ore (?P<time>\d{{2}}:\d{{2}})\.\]', 'it')
    if m:
        return [event('bankruptcy_revoked_previous_situation_restored', m)], ''

    m = match(rf'Nouveaux associés: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}) et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), lesquels signent collectivement à deux, avec (?P<partner1>{NAME}) ou (?P<partner2>{NAME}) ou (?P<partner3>{NAME})')
    if m:
        signing = 'Kollektivunterschrift zu zweien mit ' + ' oder '.join(m[f'partner{i}'] for i in (1, 2, 3))
        return [person('new_associates_restricted_collective_signing', m, m[f'name{i}'], 'Gesellschafter', signing, m[f'place{i}']) for i in (1, 2)], ''

    m = match(rf'Bei TR (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) wurde die bisherige Firmennummer der Revisionsstelle nicht publiziert\. Korrekt wäre: (?P<name>{NAME}) \((?P<uid>{UID})\), in (?P<place>{NAME}), Revisionsstelle \[bisher: (?P=name) \((?P<previous_uid>CH-\d{{3}}\.\d\.\d{{3}}\.\d{{3}}-\d)\)\]', 'de')
    if m:
        return [event('auditor_previous_registration_number_corrected', m)], ''

    m = match(rf"Par décision du (?P<decision_date>{DATE}) prononcée par le Tribunal de (?P<court_place>{NAME}), la société en nom collectif est réinscrite d'office")
    if m:
        return [event('general_partnership_reinstated_by_court', m)], ''

    m = match(rf'Nouvelle raison sociale et nouveau siège du réviseur: (?P<name>{NAME}) \((?P<uid>{UID})\), maintenant à (?P<place>{NAME})')
    if m:
        return [event('auditor_name_and_seat_changed', m)], ''

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\) est complétée dans ce sens: (?P<name>{NAME}), directeur adjoint, signature collective à deux, avec un administrateur")
    if m:
        return [person('deputy_director_signing_completed', m, m['name'], 'Vizedirektor', 'Kollektivunterschrift zu zweien mit einem Verwaltungsrat')], ''

    m = match(rf'Die Generalversammlung hat mit Beschluss vom (?P<decision_date>{DATE}) den Beschluss über die Ermächtigung einer genehmigten Kapitalerhöhung vom (?P<authorization_date>{DATE}) gemäss näherer Umschreibung in den Statuten angepasst\. \[gestrichen: Die Generalversammlung hat mit Beschluss vom (?P=authorization_date) den Beschluss über die Ermächtigung einer genehmigten Kapitalerhöhung vom (?P<previous_authorization_date>{DATE}) gemäss näherer Umschreibung in den Statuten angepasst\.\]', 'de')
    if m:
        return [event('authorized_capital_increase_resolution_amended', m)], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que le capital-actions de CHF (?P<capital>{MONEY}), entièrement libéré, est divisé en (?P<count>{COUNT}) actions de CHF (?P<nominal>{MONEY}), au porteur \(et non en (?P<previous_count>{COUNT}) actions de CHF (?P<previous_nominal>{MONEY})\)")
    if m:
        return [event('bearer_share_count_corrected', m)], ''

    m = match(rf'Administration: (?P<name1>{NAME}), nommé président, (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), et (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), leslquels signent collectivement à deux')
    if m:
        return [person('board_president_and_members_collective_signing_typo', m, m[f'name{i}'], 'Präsident' if i == 1 else 'Verwaltungsrat', 'Kollektivunterschrift zu zweien', m.groupdict().get(f'place{i}')) for i in (1, 2, 3)], ''

    return [], leftover
