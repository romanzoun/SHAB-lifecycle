from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, DATE, UID
from . import parser106, parser117, parser140, parser198, parser245

NAME = r'[^,;.\[\]\n]+?'
_LEGACY = tuple(p for module in (parser106, parser117, parser140, parser198, parser245)
                for p in vars(module).values() if isinstance(p, re.Pattern))
WRITTEN_DATE = r'\d{1,2} (?:janvier|septembre|juillet) \d{4}'


def extract_parser399_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Bounded residual variants; previously extracted events remain untouched."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', source_pattern=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m and source_pattern:
            source = re.search(source_pattern + r'\.(?:\s|$)', source_text)
            if not source or any(source.groupdict().get(k) != v for k, v in m.groupdict().items()):
                return None
            m = source
        if m:
            try:
                for date in re.findall(DATE, m[0]):
                    datetime.strptime(date, '%d.%m.%Y')
                for date in re.findall(WRITTEN_DATE, m[0]):
                    day, month, year = date.split()
                    datetime(int(year), {'janvier': 1, 'juillet': 7, 'septembre': 9}[month], int(day))
            except ValueError:
                return None
        return m

    def event(action, m, kind, **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, role=None, signing=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', m['name'], role=role, signing=signing, place=m.groupdict().get('place'), extra={'action': action, **m.groupdict(), **extra})

    m = match(rf"L'inscription no\. (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(publication FOSC du (?P<notice_date>{DATE}) page (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que l'associée est: (?P<associate>{NAME}) \((?P<associate_uid>{UID})\), à (?P<place>{NAME}), pour (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) \(et non: (?P<previous_name>{NAME}), de (?P<previous_origin>{NAME}), à (?P<previous_place>{NAME})\)")
    if m:
        return [event('corporate_associate_corrected_notice', m, 'ownership_changed', currency='CHF')], ''

    pattern = rf'Persona iscritta corretta: (?P<name>[^,;]+, [^,;]+), (?P<origin>cittadino italiano), in (?P<place>{NAME}), membro, con firma collettiva a due'
    m = match(pattern, 'it', pattern + r' \[no: (?P<previous_origin>cittadina italiana)\]')
    if m:
        return [person('italian_member_nationality_gender_corrected', m, role='membro', signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf'Die Gesellschaft hat mit Beschluss vom (?P<decision_date>{DATE}) eine Erhöhung des bedingten Partizipationskapitals gemäss näherer Umschreibung in den Statuten beschlossen\. \[bisher: Die Gesellschaft hat mit Beschluss vom (?P<previous_date>{DATE}) eine bedingte Erhöhung des Partizipationskapitals gemäss näherer Umschreibung in den Statuten beschlossen\.\]\. Die Gesellschaft hat mit Beschluss vom (?P=decision_date) eine Änderung des bedingten Kapitals gemäss näherer Umschreibung in den Statuten beschlossen\. \[bisher: Die Gesellschaft hat mit Beschluss vom (?P=previous_date) eine Änderung des bedingten Kapitals gemäss näherer Umschreibung in den Statuten beschlossen\.\]', 'de')
    if m:
        return [event('conditional_participation_increase_and_capital_amended', m, 'capital_changed')], ''

    m = match(rf'Eingetragene Person geändert: (?P<name>{NAME}), Gesellschafter, (?P<count>{COUNT}) Stammanteile zu CHF (?P<nominal>{MONEY}), Geschäftsführer, Einzelunterschrift, neu Gesellschafter, (?P=count) Stammanteile zu CHF (?P=nominal), ohne Unterschrift', 'de')
    if m:
        return [person('associate_manager_becomes_unsigned_associate', m, role='Gesellschafter', signing='ohne Unterschrift', previous_role='Gesellschafter, Geschäftsführer', previous_signing='Einzelunterschrift')], ''

    m = match(rf"Le capital-actions de CHF (?P<capital>{MONEY}) a été libéré ultérieurement à concurrence de CHF (?P<additional_paid>{MONEY})\. Capital-actions: CHF (?P=capital), entièrement libéré, divisé en (?P<count>{COUNT}) actions de CHF (?P<nominal>{MONEY}), nominatives")
    if m:
        return [event('share_capital_subsequently_fully_paid', m, 'capital_changed', currency='CHF', fully_paid=True)], ''

    m = match(r'Streichung der Statutenbestimmung über die bedingte Kapitalerhöhung infolge Erlöschens der Wandel- und/oder Optionsrechte', 'de')
    if m:
        return [event('conditional_capital_clause_removed_conversion_or_option_rights', m, 'statutes_changed')], ''

    m = match(rf"Augmentation conditionnelle du capital-participation porté de CHF (?P<previous_capital>{MONEY}) à CHF (?P<capital>{MONEY}), à savoir de CHF (?P<increase>{MONEY}), par l'émission de (?P<issued>{COUNT}) bons de participations de CHF (?P<nominal>{MONEY}), nominatifs\. Capital-participation: CHF (?P=capital), entièrement libéré, divisé en (?P<count>{COUNT}) bons de participation de CHF (?P=nominal), nominatifs\. L'assemblée générale a modifié la clause statutaire relative à l'augmentation conditionnelle du capital-participation par décision du (?P<decision_date>{DATE})")
    if m:
        return [event('conditional_participation_capital_increased_clause_amended', m, 'capital_changed', currency='CHF')], ''

    reference = rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}) p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que "
    m = match(reference + rf'(?P<name>{NAME}) est domicilié à (?P<place>{NAME}), (?P<region>[A-Z]{{2}}), (?P<country>[A-Z]{{3}}) \(et non pas à (?P<previous_place>{NAME}), (?P<previous_country>[A-Z]{{3}})\)')
    if m:
        return [person('domicile_state_country_corrected_notice', m)], ''

    m = match(rf"Par décision du (?P<decision_date>{WRITTEN_DATE}), le (?P<court>président du Tribunal de l'arrondissement de {NAME}) a accordé à la société un sursis concordataire de (?P<months_word>six) mois échéant le (?P<until_date>{WRITTEN_DATE})\. (?P<commissioner1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), et (?P<commissioner2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), sont désignés commissaires au sursis définitif")
    if m:
        return [event('definitive_moratorium_two_commissioners_written_dates', m, 'status_changed')], ''

    m = match(reference + rf'les statuts ont été modifiés le (?P<statutes_date>{DATE}) \(et non pas le (?P<previous_statutes_date>{DATE})\)')
    if m:
        return [event('statutes_date_corrected_notice_page', m, 'statutes_changed')], ''

    m = match(rf'Signature collective à deux a été conférée à (?P<name>{NAME}), nommée directrice, sa procuration est radiée')
    if m:
        return [person('female_director_joint_signing_comma_proxy_revoked', m, role='directrice', signing='Kollektivunterschrift zu zweien', previous_signing_revoked=True)], ''

    pattern = rf"Selon décision de son assemblée générale du (?P<decision_date>{WRITTEN_DATE}), l'association a prononcé sa dissolution\. La liquidation est opérée sous le nom: (?P<liquidation_name>{NAME}), par (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), élu liquidateur"
    m = match(pattern, source_pattern=pattern + r' avec signature individuelle')
    if m:
        return [event('association_dissolved_general_meeting_liquidation', m, 'status_changed'), person('association_liquidator_elected_individual_signing', m, role='liquidateur', signing='Einzelunterschrift')], ''
    return [], text
