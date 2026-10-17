from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, COUNT, UID


def extract_parser338_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete sample-backed residues without replacing earlier events."""
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
        return _event(*context, kind, f'{language}.text.{action}.v1', {**m.groupdict(), 'action': action, **extra})

    def person(action, m, name, role=None, signing=None, place=None):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **{k: v for k, v in m.groupdict().items() if k not in ('name', 'place')}})

    m = match(rf"Signature collective à deux est conférée à (?P<name1>{NAME}), à (?P<place1>{NAME}), (?P<name2>{NAME}), à (?P<place2>{NAME}), tous deux de (?P<origin12>{NAME}), et (?P<name3>{NAME}), d'(?P<origin3>{NAME}), à (?P<place3>{NAME})")
    if m:
        return [person('three_collective_signatories', m, m[f'name{i}'], signing='Kollektivunterschrift zu zweien', place=m[f'place{i}']) for i in range(1, 4)], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est complétée en ce sens que le prénom de (?P<previous_name>{NAME}) est (?P<given_names>{NAME})")
    if m:
        return [event('given_names_complemented', m)], ''

    m = match(rf'Nouveau membre du comité toutefois avec le président ou le directeur général: (?P<name>{NAME}), de et à (?P<place>{NAME})')
    if m:
        original = leftover.replace('comité toutefois', 'comité avec signature collective à deux, toutefois')
        if original not in source_text:
            return [], leftover
        return [person('committee_member_restricted_signing', m, m['name'], 'Vorstandsmitglied', 'Kollektivunterschrift zu zweien mit dem Präsidenten oder dem Generaldirektor', m['place'])], ''

    m = match(r"Par décision de (?P<court>[^,]+?) de (?P<decision_day>\d{1,2}) juin (?P<decision_year>\d{4}), l'établissement principal a été déclaré en faillite avec effet à partir du (?P<effective_day>\d{1,2}) juin (?P<effective_year>\d{4}), à (?P<effective_time>\d{2}h\d{2})\. Nouvelle raison de commerce de la succursale: (?P<new_name>[^,.;]+? en liquidation)")
    if m:
        try:
            for prefix in ('decision', 'effective'):
                datetime.strptime(f"{m[prefix + '_day']}.06.{m[prefix + '_year']}", '%d.%m.%Y')
            datetime.strptime(m['effective_time'], '%Hh%M')
        except ValueError:
            return [], leftover
        return [event('principal_bankruptcy_branch_name', m, 'status_changed')], ''

    m = match(rf'\[bisher: (?P<previous_place>{NAME})\]\. (?P<place>{NAME}) \((?P<branch_uid>{UID})\) \[bisher: (?P=place) \((?P<previous_registration>CH-\d{{3}}\.\d\.\d{{3}}\.\d{{3}}-\d)\)\]\. \[Änderung der Zweigniederlassungen (?P=previous_place) und (?P=place) aufgrund geänderter Eintragungspraxis\.\]', 'de')
    if m:
        return [event('branch_registration_practice_changed', m)], ''

    m = match(rf"L'associée (?P<holder>{NAME}) \((?P<registration>[^()]+)\) cède (?P<transferred_count>{COUNT}) de ses (?P<previous_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à l'associée-gérante (?P<recipient>{NAME}), désormais titulaire de (?P<received_total>{COUNT}) parts de CHF (?P=nominal)\. (?P=holder) \((?P=registration)\) reste titulaire de (?P<retained_count>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        return [event('corporate_share_transfer_to_manager', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf'Persona iscritta corretta: (?P<surname>{NAME}), (?P<given_names>{NAME}), cittadina (?P<nationality>{NAME}), in (?P<place>{NAME}), socia, senza diritto di firma, con (?P<count>{COUNT}) quote da CHF (?P<nominal>{MONEY})', 'it')
    if m:
        return [person('unsigned_associate_corrected', m, f"{m['surname']}, {m['given_names']}", 'Gesellschafterin', 'ohne Zeichnungsberechtigung', m['place'])], ''

    m = match(rf"Les associées (?P<holder1>{NAME}) \((?P<uid1>{UID})\) et (?P<holder2>{NAME}) \((?P<uid2>{UID})\) ont cédé (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<intermediary>{NAME}) \((?P<intermediary_uid>{UID})\), à (?P<intermediary_place>{NAME}), qui a elle-même cédé ses (?P=count) parts de CHF (?P=nominal) à (?P<recipient>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé pour (?P=count) parts de CHF (?P=nominal); lequel associé n'exerce pas la signature sociale\. Par conséquent, (?P=holder2) \((?P=uid2)\) et (?P=holder1) \((?P=uid1)\) sont désormais titulaires chacune de (?P<retained_count>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        return [event('successive_share_transfers', m, 'ownership_changed', currency='CHF'), person('unsigned_transfer_recipient', m, m['recipient'], 'Gesellschafter', 'ohne Zeichnungsberechtigung', m['place'])], ''

    m = match(rf'Le membre du conseil de fondation (?P<name>{NAME}) continue à signer collectivement à deux, désormais sans restriction\. Nouveaux membre du conseil de fondation : (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), président, et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), secrétaire')
    if m:
        original = leftover.replace('fondation :', 'fondation avec signature collective à deux:')
        if original not in source_text:
            return [], leftover
        return [person('foundation_signing_unrestricted', m, m['name'], 'Stiftungsrat', 'Kollektivunterschrift zu zweien')] + [person('foundation_officers_joined', m, m[f'name{i}'], role, 'Kollektivunterschrift zu zweien', m[f'place{i}']) for i, role in ((1, 'Präsident des Stiftungsrates'), (2, 'Sekretär des Stiftungsrates'))], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(publication FOSC du (?P<notice_date>{DATE}) page (?P<notice_ref>\d+/\d+)\) est rectifiée en ce ses que l'administrateur porte le nom de (?P<name>{NAME}) \(et non: (?P<previous_name>[^()]+)\)")
    if m:
        return [person('administrator_name_corrected_typo', m, m['name'], 'Verwaltungsrat')], ''

    m = match(rf'(?P<holder1>{NAME}) détient désormais (?P<count1>{COUNT}) parts de CHF (?P<nominal>{MONEY}) et (?P<holder2>{NAME}) détient désormais (?P<count2>{COUNT}) parts de CHF (?P=nominal) par suite de cession de (?P<transferred_count>{COUNT}) parts de CHF (?P=nominal) à (?P<recipient>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé-gérant pour (?P=transferred_count) parts de CHF (?P=nominal) sans signature')
    if m:
        return [event('share_transfer_unsigned_manager', m, 'ownership_changed', currency='CHF'), person('unsigned_associate_manager_joined', m, m['recipient'], 'Gesellschafter und Geschäftsführer', 'ohne Zeichnungsberechtigung', m['place'])], ''

    m = match(rf'Nouveaux gérants: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}) et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<country>[A-Z]{{3}}), Le gérant (?P<name3>{NAME}), nommé président, signe désormais collectivement à deux')
    if m:
        original = leftover.replace(', Le gérant', ', avec signature collective à deux. Le gérant')
        if original not in source_text:
            return [], leftover
        return [person('managers_collective_signing', m, m[f'name{i}'], 'Geschäftsführer' if i < 3 else 'Vorsitzender der Geschäftsführung', 'Kollektivunterschrift zu zweien', m[f'place{i}'] if i < 3 else None) for i in range(1, 4)], ''

    return [], leftover
