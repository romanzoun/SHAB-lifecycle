from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, MONEY, UID

PERSON = r'[^,;]+?'


def extract_parser365_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize sample-backed complete residual clauses after earlier rules."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', source_suffix=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('_date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except (ValueError, TypeError):
                return None
            if source_suffix and not re.search(re.escape(leftover.rstrip('.')) + source_suffix + r'\.?$', source_text):
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, place=None, role=None, signing=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, place=place, role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra})

    m = match(rf"(?P<transferor>{PERSON}), (?P<role_change>nommé président|jusqu'ici présidente), détient désormais (?P<remaining>\d+) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<transferred>\d+) parts de CHF (?P=nominal) à (?P<recipient>{PERSON}), (?P<origin>d'Italie|de France), à (?P<place>{PERSON})(?P<country>, FRA)?, (?P<recipient_role>nouvelle associée-gérante|nouvel associé-gérant et président) pour (?P=transferred) parts de CHF (?P=nominal)")
    if m:
        return [event('share_transfer_manager_presidency', m, currency='CHF')], ''

    # This supplied notice labels German body text as French. Keep that metadata.
    entries = []
    for i in range(1, 8):
        origin = rf'(?P<origin{i}>von [^,;]+|italienischer Staatsangehöriger|deutsche Staatsangehörige), in (?P<place{i}>[^,;]+)' if i < 7 else rf'von und in (?P<place{i}>[^,;]+)'
        role = ', Verwaltungsratmitglied' if i == 1 else ''
        entries.append(rf'(?P<name{i}>{PERSON}), ' + origin + role + ', Kollektivunterschrift zu zweien')
    m = match(rf'Gelöschte person: (?P<removed>{PERSON}), Kollektivunterschrift zu zweien\. Neu eingetragene Personen: ' + '; '.join(entries))
    if m:
        action = 'german_officers_french_notice'
        return [person(action, m, m['removed'], signing='Kollektivunterschrift zu zweien', change='removed')] + [person(action, m, m[f'name{i}'], m[f'place{i}'], 'Mitglied des Verwaltungsrates' if i == 1 else None, 'Kollektivunterschrift zu zweien', change='appointed') for i in range(1, 8)], ''

    m = match(r'Genussscheine neu: Ein Genussschein, mit Rechten auf Anteil am Bilanzgewinn und am Liquidationserlös gemäss Statuten', 'de')
    if m:
        return [event('profit_participation_certificate_rights', m, count='1', profit_participation=True, liquidation_proceeds_participation=True)], ''

    m = match(rf"Réinscription de la société radiée, réouverture de la faillite avec révocation de la suspension faute d'actif et liquidation de la faillite en la forme sommaire, selon décision du (?P<decision_date>{DATE}) du (?P<court>Tribunal de [^,;.]+)")
    if m:
        return [event('reinstatement_bankruptcy_reopened_summary', m, suspension_revoked=True)], ''

    m = match(rf'Persona iscritta corretta: (?P<surname1>{PERSON}), (?P<given_name1>{PERSON}), da (?P<origin1>{PERSON}), in (?P<place1>{PERSON}), socio e presidente della gerenza, con firma individuale, con una quota di CHF (?P<nominal1>{MONEY}) e con una quota di CHF (?P<nominal2>{MONEY}); (?P<surname2>{PERSON}), (?P<given_name2>{PERSON}), da (?P<origin2>{PERSON}), in (?P<place2>{PERSON}), gerente, con firma individuale', 'it')
    if m:
        return [person('corrected_manager_details_two_shares', m, m[f'surname{i}'] + ', ' + m[f'given_name{i}'], m[f'place{i}'], 'Gesellschafter und Vorsitzender der Geschäftsführung' if i == 1 else 'Geschäftsführer', 'Einzelunterschrift', currency='CHF') for i in (1, 2)], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que la raison de commerce de l'organe de révision est (?P<name>[^()]+?) \(et non (?P<previous_name>[^()]+?) comme publié\)")
    if m:
        return [event('auditor_company_name_corrected', m)], ''

    m = match(rf'Das Konkursverfahren wurde mit Entscheid vom (?P<closure_date>{DATE}) als geschlossen erklärt\. Die Gesellschaft wird von Amtes wegen gelöscht\. Die am (?P<deletion_date>{DATE}) gelöschte Gesellschaft wird aufgrund der Verfügung des (?P<court>Einzelrichters des Bezirksgerichts [^,;]+?) vom (?P<decision_date>{DATE}) zum Zwecke der Geltendmachung von abgetretenen Ansprüchen nach Art\. 260 SchKG wieder ins Handelsregister eingetragen und besteht entsprechend den früheren Eintragungen weiter', 'de')
    if m:
        return [event('reinstatement_assigned_claims_after_bankruptcy', m, legal_basis='Art. 260 SchKG')], ''

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) des (?P<court>Bezirksgerichts [^,;]+?) wurde die gewährte COVID-19-Stundung bis am (?P<until_date>{DATE}) verlängert', 'de')
    if m:
        return [event('covid19_moratorium_extended', m)], ''

    # Signing suffixes have already been consumed by earlier rules. Only restore
    # their association when the complete source confirms the exact suffix.
    m = match(rf'Administration: (?P<name1>{PERSON}), nommée présidente, laquelle signe individuellement, et (?P<name2>{PERSON}), de (?P<origin2>{PERSON}), à (?P<place2>{PERSON}), (?P<country2>FRA)', source_suffix=', avec signature collective à deux')
    if m:
        return [person('board_president_and_joint_member', m, m['name1'], role='Präsidentin des Verwaltungsrates', signing='Einzelunterschrift'), person('board_president_and_joint_member', m, m['name2'], m['place2'], 'Mitglied des Verwaltungsrates', 'Kollektivunterschrift zu zweien')], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vermögensübertragungsvertrag vom (?P<agreement_date>{DATE}) und Inventar per (?P<inventory_date>{DATE}) den Betriebsteil "(?P<business_unit>[^";]+)" mit Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient>[^,;]+), in (?P<place>[^,;]+) \((?P<recipient_uid>{UID})\)\. Gegenleistung: (?P<count>[\d\x27]+) Namenaktien zu CHF (?P<nominal>{MONEY})', 'de')
    if m:
        return [event('asset_transfer_business_unit_share_consideration', m, currency='CHF')], ''

    m = match(rf'(?P<name>{PERSON}), de et à (?P<place>{PERSON}) est nommé gérant', source_suffix=' avec signature collective à deux')
    if m:
        return [person('manager_appointed_same_origin_place', m, m['name'], m['place'], 'Geschäftsführer', 'Kollektivunterschrift zu zweien')], ''

    return [], leftover
