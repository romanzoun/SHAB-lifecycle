from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, MONEY, UID

PERSON = r'[^,;.]+?'


def extract_parser363_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume only complete sample-backed residual clauses after earlier parsers."""
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
                        datetime.strptime(value.replace('-', '.'), '%d.%m.%Y')
                if 'time' in m.groupdict():
                    datetime.strptime(m['time'], '%H.%M')
            except (ValueError, TypeError):
                return None
        return m

    def event(action, m=None, **extra):
        return _event(*context, 'organization_changed', f'{language}.text.{action}.v1', {'action': action, **(m.groupdict() if m else {}), **extra})

    def person(action, m, name, place=None, role=None, signing=None):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, place=place, role=role, signing=signing, extra={'action': action, **m.groupdict()})

    m = match(rf'Persona iscritta corretta: (?P<surname>{PERSON}), (?P<given_name>{PERSON}), da (?P<origin>{PERSON}), in (?P<place>{PERSON}), presidente della gerenza, con firma individuale', 'it')
    if m:
        return [person('manager_president_identity_corrected', m, m['surname'] + ', ' + m['given_name'], m['place'], 'Vorsitzender der Geschäftsführung', 'Einzelunterschrift')], ''

    m = match(rf'Persona iscritta corretta: (?P<surname>{PERSON}), (?P<given_name>{PERSON}), da (?P<origin>{PERSON}), in (?P<place>{PERSON}), socio, senza diritto di firma, con (?P<count>\d+) quote da CHF (?P<nominal>{MONEY})', 'it')
    if m:
        return [person('unsigned_associate_identity_corrected', m, m['surname'] + ', ' + m['given_name'], m['place'], 'Gesellschafter', 'ohne Zeichnungsberechtigung')], ''

    m = match(rf"Liquidateurs: l'associé gérant (?P<name1>{PERSON}) et (?P<name2>{PERSON}), de (?P<origin2>{PERSON}), à (?P<place2>{PERSON}), (?P<country2>[A-Z]{{3}}), lesquels signent individuellement")
    if m:
        return [person('two_liquidators_individual_signing', m, m[f'name{i}'], m['place2'] if i == 2 else None, 'Liquidator', 'Einzelunterschrift') for i in (1, 2)], ''

    m = match(rf'(?P<transferor>{PERSON}) détient désormais (?P<remaining>\d+) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<transferred>\d+) parts de CHF (?P=nominal) à (?P<recipient>.+?) \((?P<recipient_uid>{UID})\), associée désormais pour (?P<recipient_total>\d+) parts de CHF (?P=nominal)')
    if m:
        return [event('share_transfer_to_existing_corporate_associate', m, currency='CHF')], ''

    m = match(rf"L'inscription (?P<entry>\d+) du (?P<entry_date>\d{{2}}-\d{{2}}-\d{{4}}) est rectifiée en ce sens que l'administrateur président se nomme (?P<name>{PERSON}) \(et non (?P<previous_name>{PERSON})\)")
    if m:
        return [person('board_president_name_corrected_hyphen_date', m, m['name'], role='Präsident des Verwaltungsrates')], ''

    m = match(rf"L'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) ayant été opérée par erreur, la mention relative à Messieurs (?P<name1>{PERSON}), (?P<name2>{PERSON}) et (?P<name3>{PERSON}) est radiée")
    if m:
        return [event('erroneous_three_person_entry_deleted', m)], ''

    m = match(rf'Signature collective à deux de (?P<name>{PERSON}), nommé directeur')
    if m:
        return [person('director_appointed_joint_signing', m, m['name'], role='Direktor', signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf'(?P<transferor>{PERSON}), associé-gérant président, cède (?P<transferred>\d+) de ses (?P<before>\d+) parts de CHF (?P<nominal>{MONEY}) à (?P<recipient>{PERSON}), associé-gérant, désormais titulaire de (?P<recipient_total>\d+) parts de CHF (?P=nominal)\. (?P=transferor) reste titulaire de (?P<remaining>\d+) parts de CHF (?P=nominal)')
    if m and int(m['before']) == int(m['transferred']) + int(m['remaining']):
        return [event('share_transfer_between_associate_managers', m, currency='CHF')], ''

    m = match(rf"Jusqu'ici titulaire de (?P<before>\d+) parts de CHF (?P<nominal>{MONEY}), l'associeé (?P<transferor>.+?) \((?P<transferor_uid>{UID})\) détient (?P<remaining>\d+) parts de CHF (?P=nominal) par suite de cession de (?P<transferred>\d+) parts au gérant (?P<recipient>[^,;]+?), nouvel associé pour (?P=transferred) parts de CHF (?P=nominal)")
    if m and int(m['before']) == int(m['remaining']) + int(m['transferred']):
        return [event('corporate_associate_transfer_to_manager', m, currency='CHF')], ''

    m = match(rf'Mit Verfügung des (?P<appeal_court>Obergerichts des Kantons [^,;.]+) vom (?P<decision_date>{DATE}) wurde die Beschwerde des Gesuchgegners abgewiesen\. Der Entscheid des (?P<original_court>Bezirksgerichts [^,;.]+) vom (?P<original_date>{DATE}) wird aufgehoben und über den Inhaber dieses Einzelunternehmens mit Wirkung ab dem (?P<bankruptcy_date>{DATE}), (?P<time>\d{{2}}\.\d{{2}}) Uhr der Konkurs neu eröffnet', 'de')
    if m:
        return [event('sole_proprietor_bankruptcy_reopened_after_appeal', m)], ''

    if match(re.escape('Das Institut des öffentlichen Rechts hat Beteiligungsrechte an einer Börse kotiert und ist daher befugt, Inhaber-Partizipationsscheine zu halten'), 'de'):
        return [event('public_institute_bearer_participation_authorized', basis='listed_equity_rights')], ''
    if match(re.escape('Die Gesellschaft hat sämtliche Inhaberpartizipationsscheine als Bucheffekten im Sinne des Bucheffektengesetzes ausgestaltet und ist daher befugt, Inhaberpartizipationsscheine zu halten'), 'de'):
        return [event('bearer_participation_book_entry_authorized', basis='book_entry_securities')], ''

    return [], leftover
