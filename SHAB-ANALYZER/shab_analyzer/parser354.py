from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, UID


def extract_parser354_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete sample-backed residues without replacing earlier events."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', source_pattern=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m:
            return None
        if source_pattern:
            source = re.search(source_pattern + r'\.?$', source_text)
            if not source or source.groupdict() != m.groupdict():
                return None
        try:
            for key, value in m.groupdict().items():
                if key.endswith('_date'):
                    datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            return None
        return m

    def event(action, m):
        return _event(*context, 'organization_changed', f'{language}.text.{action}.v1', {'action': action, **m.groupdict()})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **m.groupdict(), **extra, 'name': name})

    m = match(rf"(?P<name>{NAME}), directrice, jusqu'ici présidente du conseil d'administration, désormais administratrice unique, continue de signer individuellement")
    if m:
        return [person('sole_director_continued_individual_signing', m, m['name'], 'Mitglied des Verwaltungsrats', 'Einzelunterschrift', previous_role="présidente du conseil d'administration", sole_director=True, additional_role='directrice')], ''

    m = match(rf"Con decreto della (?P<court>{NAME}) del (?P<decision_date>{DATE}), è stato omologato il concordato ordinario concluso tra la società e i suoi creditori\. L'esecuzione del concordato viene affidata al commissario, il quale potrà prendere tutti i provvedimenti necessari per l'esecuzione e garantirne l'adempimento", 'it')
    if m:
        return [event('ordinary_composition_confirmed_commissioner_execution', m)], ''

    m = match(rf"L'inscription no\. (?P<entry>\d+) du (?P<entry_date>{DATE}) \(publication FOSC du (?P<notice_date>{DATE}), page (?P<notice_ref>\d+/\d+)\) est complétée en ce sens que l'obligation de fournir des prestations accessoires, droits de préférence, de préemption ou d'emption prévue par les statuts est supprimée")
    if m:
        return [event('ancillary_obligations_removal_supplement', m)], ''

    m = match(rf"L'inscription No (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name>{NAME}) se voit attribuer une procuration collective à deux, limitée à l'établissement principal \(et non pas une signature collective à deux, limitée à l'établissement principal\)")
    if m:
        return [person('head_office_collective_procuration_corrected', m, m['name'], signing='Kollektivprokura zu zweien', signing_scope='établissement principal')], ''

    m = match(rf'Mit Entscheid des (?P<court>[^.;]+?), vom (?P<decision_date>{DATE}) wurde eine provisorische Nachlassstundung von zwei Monaten bis zum (?P<end_date>{DATE}) bewilligt\. Als Sachwalterin wird die (?P<commissioner>{NAME}) \((?P<commissioner_uid>{UID})\), Herr (?P<representative>{NAME}), (?P<address>{NAME}), (?P<postal_code>\d{{4}}) (?P<place>{NAME}), ernannt', 'de')
    if m:
        return [event('provisional_moratorium_commissioner_appointed', m)], ''

    pattern = rf"(?P<transferor>{NAME}) a cédé (?P<transferred>\d+) parts de CHF (?P<nominal>{MONEY}) à (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]{{3}}), nouvel associé pour (?P=transferred) parts de CHF (?P=nominal); par conséquent, (?P=transferor) est maintenant associé pour (?P<remaining>\d+) parts de CHF (?P=nominal)\. L'associé (?P=name) est nommé gérant"
    m = match(pattern, source_pattern=pattern + ' avec signature individuelle')
    if m:
        return [event('shares_transferred_remaining_holding', m), person('transferee_manager_individual_signing', m, m['name'], 'Geschäftsführer', 'Einzelunterschrift', m['place'])], ''

    m = match(r"Le président de la Cour des poursuites et faillites du Tribunal cantonal a prononcé l'effet suspensif de la procédure de faillite le (?P<decision_day>\d{1,2}) août (?P<decision_year>\d{4})")
    if m:
        try:
            datetime(int(m['decision_year']), 8, int(m['decision_day']))
        except ValueError:
            return [], leftover
        return [event('bankruptcy_suspensive_effect_ordered', m)], ''

    m = match(rf'(?P<name1>{NAME}) maintenant à (?P<place1>{NAME}) \((?P<country1>{NAME})\) et (?P<name2>{NAME}) de (?P<origin2>{NAME})')
    if m:
        return [person('officer_residence_updated', m, m['name1'], place=m['place1']), person('officer_origin_updated', m, m['name2'])], ''

    m = match(rf"(?P<transferor>{NAME}) \((?P<transferor_uid>{UID})\) cède (?P<transferred>\d+) de ses (?P<previous>\d+) parts de CHF (?P<nominal>{MONEY}) à l'associé (?P<recipient>{NAME}), désormais titulaire de (?P<recipient_holding>\d+) parts de CHF (?P=nominal)\. (?P=transferor) reste titulaire de (?P<remaining>\d+) parts de CHF (?P=nominal)")
    if m and int(m['previous']) == int(m['transferred']) + int(m['remaining']):
        return [event('corporate_shares_transferred_remaining_holding', m)], ''

    m = match(rf'Aktiengesellschaft\. Mit Entscheid vom (?P<decision_date>{DATE}) hat der (?P<court>{NAME}) ab (?P<start_date>{DATE}) eine Verlängerung der definitiven Nachlassstundung für die Dauer von (?P<duration_months>\d+) Monaten bis zum (?P<end_day>\d{{1,2}})\. November (?P<end_year>\d{{4}}) gewährt', 'de')
    if m:
        try:
            datetime(int(m['end_year']), 11, int(m['end_day']))
        except ValueError:
            return [], leftover
        return [event('definitive_moratorium_extended', m)], ''

    pattern = rf"L'inscription no (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE})\)"
    m = match(pattern, source_pattern=pattern + rf' est rectifiée en ce sens que {NAME} se prénomme en réalité {NAME} \(et non pas {NAME}\)')
    if m:
        return [event('given_name_correction_entry_reference', m)], ''

    m = match(rf'(?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}) et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), sont membres du comité, sans signature')
    if m:
        return [person('committee_members_without_signing_appointed', m, m[f'name{i}'], 'Vorstandsmitglied', 'ohne Zeichnungsberechtigung', m[f'place{i}']) for i in (1, 2)], ''

    return [], leftover
