from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, UID
from .parser200 import _FR_TWO_PROCURATIONS_GRANTED
from .parser179 import _DE_AUTHORIZED_CAPITAL_MODIFIED_WITH_HISTORY

NAME = r'[^,;.()]+?'
DATE = r'\d{2}\.\d{2}\.\d{4}'


def extract_parser381_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Bounded new variants; keep legacy patterns and existing events intact."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in (_FR_TWO_PROCURATIONS_GRANTED, _DE_AUTHORIZED_CAPITAL_MODIFIED_WITH_HISTORY)):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', suffix=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m and suffix and not re.search(re.escape(leftover.rstrip('.')) + suffix + r'\.', source_text):
            return None
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, event_type='organization_changed', **extra):
        return _event(*context, event_type, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, place=None, role=None, signing=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, place=place, role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) und Inventar per (?P<inventory_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) auf die (?P<recipient>{NAME}) \((?P<recipient_uid>{UID})\), in (?P<place>{NAME})\. Gegenleistung: keine', 'de')
    if m:
        return [event('assets_transferred_inventory_no_consideration', m, currency='CHF', consideration='keine')], ''

    m = match(rf"Par décision du (?P<decision_date>{DATE}), l'autorité de surveillance de la fondation a dispensé la fondation de désigner un organe de révision")
    if m:
        return [event('foundation_supervisor_audit_exemption', m, 'audit_requirement_changed', audit_exempt=True)], ''

    m = match(rf'(?P<name>{NAME}) est nommé administrateur ; sa procuration est radiée')
    if m and re.search(re.escape(m['name']) + r' est nommé administrateur avec signature collective à deux; sa procuration est radiée\.', source_text):
        return [person('administrator_appointed_procuration_revoked', m, m['name'], role='administrateur', signing='Kollektivunterschrift zu zweien', procuration_revoked=True)], ''

    m = match(r'Da der Inhaber den Geschäftsbetrieb weiterführt, sind die Voraussetzungen für eine Löschung gemäss Art\. 159 Abs\. 5 lit\. a HRegV nicht erfüllt\. Die Eintragung bleibt folglich bestehen', 'de')
    if m:
        return [event('sole_proprietor_continued_business_registration_retained', m, 'status_changed', registration_retained=True, legal_basis='Art. 159 Abs. 5 lit. a HRegV')], ''

    m = match(rf'\[Streichung aufgrund Abweisung der Beschwerden gemäss Entscheid des Kantonsgerichts (?P<court_place>[^;\[\]]+?) vom (?P<decision_date>{DATE})\] \[gestrichen: Das Kantonsgericht (?P=court_place) hat der Beschwerde gegen die Verfügung des Kreisgerichts (?P<district>{NAME}) vom (?P<revocation_date>{DATE}) betreffend Widerruf sowie der Beschwerde gegen die Verfügung des Kreisgerichts (?P=district) vom (?P<extension_date>{DATE}) betreffend Verlängerung der Covid-19-Stundung aufschiebende Wirkung zuerkannt\. Die Stundung wird vorläufig bis zur Rechtskraft des Beschwerdeentscheids verlängert\. \]', 'de')
    if m:
        return [event('covid_moratorium_appeal_suspension_clause_deleted', m, 'status_changed', previous_clause_deleted=True)], ''

    m = match(rf'(?P<name>{NAME}), maintenant à (?P<place>{NAME}), dont la procuration est éteinte, est nommée liquidatrice', suffix=' avec signature individuelle')
    if m:
        return [person('moved_liquidator_procuration_extinguished', m, m['name'], m['place'], 'liquidatrice', 'Einzelunterschrift', procuration_revoked=True)], ''

    m = match(rf"(?P<name1>{NAME}), nommée présidente, et (?P<name2>{NAME}), jusqu'ici président, membres du conseil de fondation, continuent de signer collectivement à deux")
    if m:
        return [person('foundation_presidency_pair_continued_joint_signing', m, m[f'name{i}'], role='membre du conseil de fondation' + (', présidente' if i == 1 else ''), signing='Kollektivunterschrift zu zweien') for i in (1, 2)], ''

    # Dotted married surnames are explicitly bounded to the attested abbreviation.
    dotted_name = r'[^,;.()]+?(?: ép\. [^,;.()]+?)?'
    m = match(rf'Administration: (?P<name1>{NAME}), nommé président, lequel continue à signer individuellement, et (?P<name2>{dotted_name}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<country2>[A-Z]{{3}}), (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), et (?P<name4>{NAME}), de (?P<origin4>{NAME}), à (?P<place4>{NAME})', suffix=', avec signature collective à deux')
    if m:
        return [person('four_administrators_president_individual_others_joint', m, m[f'name{i}'], m.groupdict().get(f'place{i}'), 'président' if i == 1 else 'administrateur', 'Einzelunterschrift' if i == 1 else 'Kollektivunterschrift zu zweien') for i in (1, 2, 3, 4)], ''

    m = match(rf'Berichtigung der Eintragung Nr\. (?P<entry>\d+) vom (?P<entry_date>{DATE}) \(SHAB vom (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\): (?P<name>{NAME}), Gesellschafterin, (?P<count>{COUNT}) Stammanteile zu CHF (?P<nominal>{MONEY}), Geschäftsführerin, Einzelunterschrift, in (?P<place>{NAME}) \(und nicht in (?P<previous_place>{NAME})\)', 'de')
    if m:
        return [person('associate_manager_domicile_notice_corrected', m, m['name'], m['place'], 'Gesellschafterin, Geschäftsführerin', 'Einzelunterschrift', corrected=True, currency='CHF')], ''

    m = match(rf'Procuration collective à deux est conférée à (?P<name1>{NAME}) et (?P<name2>{NAME}), les deux de et à (?P<place>{NAME})')
    if m:
        return [person('joint_procuration_pair_shared_origin_domicile', m, m[f'name{i}'], m['place'], signing='Kollektivprokura zu zweien', origin=m['place']) for i in (1, 2)], ''

    m = match(rf'(?P<name>{NAME}), associé-gérant, est liquidateur', suffix=' avec signature individuelle')
    if m:
        return [person('associate_manager_liquidator_individual_signing', m, m['name'], role='associé-gérant, liquidateur', signing='Einzelunterschrift')], ''

    m = match(rf'Die Gesellschaft hat mit Beschluss vom (?P<decision_date>{DATE}) die mit Beschluss vom (?P<introduction_date>{DATE}) eingeführte und mit Beschluss vom (?P<amendment_date>{DATE}) geänderte genehmigte Kapitalerhöhung gemäss näherer Umschreibung in Art\. (?P<article>\d+(?:\.\d+)+) der Statuten geändert\. \[bisher: Die Gesellschaft hat mit Beschluss vom (?P=amendment_date) die mit Beschluss vom (?P=introduction_date) eingeführte genehmigte Kapitalerhöhung gemäss näherer Umschreibung in Art\. (?P=article) der Statuten geändert\.\]', 'de')
    if m:
        return [event('authorized_capital_amended_single_prior_amendment', m, 'capital_changed')], ''
    return [], text
