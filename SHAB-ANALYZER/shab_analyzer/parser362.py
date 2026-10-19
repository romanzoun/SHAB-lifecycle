from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, MONEY

PERSON = r'[^,;.]+?'
UID = r'CHE-\d{3}\.\d{3}\.\d{3}'


def extract_parser362_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize bounded residual clauses without replacing earlier events."""
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
            except (ValueError, TypeError):
                return None
        return m

    def event(action, m, **extra):
        return _event(*context, 'organization_changed', f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, place, role=None, signing=None):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, place=place, role=role, signing=signing, extra={'action': action, **m.groupdict()})

    m = match(rf'Nouveaux associés: (?P<name1>{PERSON}), de (?P<origin1>{PERSON}), à (?P<place1>{PERSON}) et (?P<name2>[^,;]+?), de (?P<origin2>{PERSON}), à (?P<place2>{PERSON}), (?P<country2>[A-Z]{{3}})')
    if m:
        return [person('two_new_associates', m, m[f'name{i}'], m[f'place{i}'], 'Gesellschafter') for i in (1, 2)], ''

    m = match(rf"Radiée par erreur, l'entreprise est réinscrite comme ci-devant \(FOSC No (?P<notice_number>\d+) du (?P<notice_date>{DATE}), publ\. (?P<notice_id>\d+)\)")
    if m:
        return [event('enterprise_erroneous_deletion_reinstated', m)], ''

    m = match(rf'(?P<transferor>[^;]+?) \((?P<transferor_uid>{UID})\) détient désormais (?P<remaining>\d+) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<transferred>\d+) parts de CHF (?P=nominal) à (?P<recipient>{PERSON}), désormais associé-gérant pour (?P=transferred) parts de CHF (?P=nominal)')
    if m:
        return [event('share_transfer_existing_associate_manager', m, currency='CHF')], ''

    m = match(rf'Modifiche: (?P<name>[^;]+?) \((?P<uid>{UID})\) \[ (?P<register_id>CH-[\d.]+-\d)\], in (?P<place>{PERSON}), liquidatrice \]', 'it')
    if m:
        return [person('corporate_liquidator_modified', m, m['name'], m['place'], 'Liquidatorin')], ''

    m = match(rf"L'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que le premier prénom de Monsieur (?P<surname>{PERSON}) s'orthographie (?P<given_name>{PERSON}), et non pas (?P<previous_given_name>{PERSON})")
    if m:
        return [event('officer_first_given_name_corrected', m)], ''

    m = match(rf"L'effet suspensif a été accordé au recours, à l'encontre de la décision de faillite du (?P<bankruptcy_date>{DATE}), selon prononcé du (?P<court>tribunal cantonal du canton du [^,;.]+) du (?P<decision_date>{DATE})")
    if m:
        return [event('bankruptcy_appeal_suspensive_effect', m)], ''

    m = match(rf'Mit TR-Nr\. (?P<original_entry>\d+) vom (?P<original_entry_date>{DATE}) hätte (?P<name>{PERSON}), von (?P<origin>{PERSON}), in (?P<place>{PERSON}), zusätzlich zur Funktion Direktor, als Mitglied des Verwaltungsrates eingetragen werden sollen, deshalb wurde der Nachtrag unter TR-Nr\. (?P<supplement_entry>\d+) vom (?P<supplement_date>{DATE}) im SHAB Nr\. (?P<notice_number>\d+) vom (?P<notice_date>{DATE}) publiziert', 'de')
    if m:
        return [person('board_membership_supplement_explained', m, m['name'], m['place'], 'Mitglied des Verwaltungsrates')], ''

    m = match(rf'Séparation: Selon projet de scission du (?P<plan_date>{DATE}), la société a transféré une partie de ses actifs et passifs à la nouvelle société (?P<recipient>[^;]+?) \((?P<recipient_uid>{UID})\), à (?P<place>{PERSON})')
    if m:
        return [event('demerger_to_new_company', m)], ''

    m = match(rf'Vorzeitige Löschung mit Bestätigung des zugelassenen Revisionsexperten vom (?P<confirmation_date>{DATE}) aufgeschoben mangels Zustimmung der kant\. Steuerverwaltung', 'de')
    if m:
        return [event('early_deletion_deferred_tax_consent', m)], ''

    m = match(rf"Signature collective à deux est conférée à (?P<name1>{PERSON}), de (?P<origin1>{PERSON}), directrice, (?P<name2>{PERSON}), de (?P<origin2>{PERSON}), et (?P<name3>{PERSON}), de (?P<origin3>{PERSON}), les trois à (?P<place>{PERSON})")
    if m:
        return [person('three_officers_joint_signing', m, m[f'name{i}'], m['place'], 'Direktorin' if i == 1 else None, 'Kollektivunterschrift zu zweien') for i in (1, 2, 3)], ''

    m = match(rf'Neue Identifikationsnummer Hauptsitz: (?P<head_office_id>\d+)\. Kapital Hauptsitz neu: Kapital Hauptsitz: GBP (?P<capital>{MONEY}); Liberierung GBP (?P<paid_up>{MONEY}); Anteile: (?P<count>[\d\']+) zu GBP (?P<nominal>{MONEY}) \[bisher: Kapital Hauptsitz: GBP (?P<previous_capital>{MONEY}); Liberierung GBP (?P<previous_paid_up>{MONEY})\]', 'de')
    if m:
        return [event('head_office_identity_capital_changed', m, currency='GBP')], ''

    m = match(rf'Fusion: Übernahme der Aktiven und Passiven der (?P<absorbed_name>.+?), in (?P<absorbed_place>[^()]+?) \(CHE- (?P<absorbed_uid>{UID})\), gemäss Fusionsvertrag vom (?P<agreement_date>{DATE}) und Bilanz per (?P<balance_date>{DATE})\. Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) gehen auf die übernehmende Gesellschaft über\. Da dieselben Aktionärin sämtliche Aktien der an der Fusion beteiligten Gesellschaften hält, findet weder eine Kapitalerhöhung noch eine Aktienzuteilung statt', 'de')
    if m:
        return [event('merger_common_shareholder_duplicated_uid_prefix', m, currency='CHF')], ''

    return [], leftover
