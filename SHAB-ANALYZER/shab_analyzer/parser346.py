from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT


def extract_parser346_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Append bounded, sample-backed events without replacing legacy results."""
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
                if 'time' in m.groupdict():
                    datetime.strptime(m['time'], '%H.%M')
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed'):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict()})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **m.groupdict(), **extra})

    m = match(rf'Mit TR-Eintrag Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) wurde irrtümlich nur das Statutendatum vom (?P<statutes_date>{DATE}) erfasst', 'de')
    if m:
        return [event('statutes_date_incomplete_entry_reported', m)], ''

    m = match(rf'Die rechtliche Zuordnung der Stammanteile des verstorbenen Gesellschafters (?P<name>{NAME}) ist zurzeit nicht bekannt', 'de')
    if m:
        return [event('deceased_holder_shares_assignment_unknown', m, 'ownership_changed')], ''

    m = match(rf'Die im Sinne von Art\. 159 Abs\. 5 lit\. a HRegV am (?P<deletion_date>{DATE}) von Amtes wegen gelöschte Gesellschaft wird wieder in das Handelsregister eingetragen, nachdem die Konkursrichterin des Bezirksgerichts (?P<court_place>{NAME}) mit Urteil vom (?P<decision_date>{DATE}) die Wiedereröffnung des Konkursverfahrens als summarisches Verfahren mit Wirkung ab dem (?P<effective_date>{DATE}), (?P<time>\d{{2}}\.\d{{2}}) Uhr, angeordnet hat\. \[bisher: Nachdem kein begründeter Einspruch gegen die Löschung erhoben wurde, wird die Gesellschaft im Sinne von Art\. 159 Abs\. 5 lit\. a HRegV von Amtes wegen gelöscht\.\]\. \[gestrichen: Das Konkursverfahren ist mit Urteil des Konkursrichters vom (?P<previous_decision_date>{DATE}) mangels Aktiven eingestellt worden\.\]', 'de')
    if m:
        return [event('reinstated_after_summary_bankruptcy_reopened', m)], ''

    m = match(rf"Rectificatif: l'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}) p\. (?P<page>\d+)/(?P<notice_id>\d+)\) est rectifiée en ce sens que l'adresse exacte est: (?P<address>[^.;]+)")
    if m:
        return [event('registered_address_corrected', m)], ''

    m = match(r'Der ursprünglich französischsprachige Umwandlungstatbestand wurde anlässlich des Sitzverlegungseintrages versehentlich nicht in die deutsche Amtssprache übersetzt', 'de')
    if m:
        return [event('transformation_translation_omission_reported', m)], ''

    m = match(rf'Administration: (?P<name1>{NAME}), nommé président, lequel continue à signer individuellement, (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<country2>[A-Z]{{3}}), et (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), lesquels signent collectivement à deux')
    if m:
        return [person('board_president_continued_individual_signing', m, m['name1'], 'Präsident', 'Einzelunterschrift')] + [person('board_member_collective_signing', m, m[f'name{i}'], 'Verwaltungsrat', 'Kollektivunterschrift zu zweien', m[f'place{i}']) for i in (2, 3)], ''

    m = match(rf"Les administrateurs (?P<name1>{NAME}), nommée présidente, et (?P<name2>{NAME}), jusqu'ici président, nommé délégué, continuent à signer collectivement à deux")
    if m:
        return [person('board_roles_changed_continued_signing', m, m['name1'], 'Präsident', 'Kollektivunterschrift zu zweien'), person('board_roles_changed_continued_signing', m, m['name2'], 'Delegierter', 'Kollektivunterschrift zu zweien', previous_role='Präsident')], ''

    m = match(rf'Mit dem SHAB Nr\. (?P<notice_number>{COUNT}) vom (?P<notice_date>{DATE}) publizierten TR-Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) wurde der bisher Text bei (?P<referenced_name>{NAME}) nicht korrekt aufgeführt, richtig wäre: (?P<surname>{NAME}), (?P<given_name>{NAME}), von (?P<origin>{NAME}), in (?P<place>{NAME}), Präsident des Vorstandes, mit Kollektivunterschrift zu zweien \[bisher: Vizepräsident des Vorstandes, in (?P<previous_place>{NAME}), mit Kollektivunterschrift zu zweien\]', 'de')
    if m:
        return [person('board_previous_details_corrected', m, m['surname'] + ' ' + m['given_name'], 'Präsident des Vorstandes', 'Kollektivunterschrift zu zweien', m['place'], previous_role='Vizepräsident des Vorstandes')], ''

    m = match(rf"Administration: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), président, (?P<name2>{NAME}), jusqu'ici président, avec signature collective à deux et (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), sans signature sociale")
    if m:
        return [person('board_president_collective_signing', m, m['name1'], 'Präsident', 'Kollektivunterschrift zu zweien', m['place1']), person('former_president_board_member', m, m['name2'], 'Verwaltungsrat', 'Kollektivunterschrift zu zweien', previous_role='Präsident'), person('board_member_without_signing', m, m['name3'], 'Verwaltungsrat', 'ohne Zeichnungsberechtigung', m['place3'])], ''

    m = match(rf"Procuration individuelle a été conférée à (?P<name1>{NAME}), ainsi qu'à (?P<name2>{NAME}), tous deux de et à (?P<place>{NAME})")
    if m:
        return [person('individual_procuration_two_persons', m, m[f'name{i}'], signing='Einzelprokura', place=m['place']) for i in (1, 2)], ''

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\) est rectifiée\. Les personnes suivantes ayant été radiées par erreur, elles sont réinscrites: (?P<name1>{NAME}), de (?P<origin1>[^;]+?), à (?P<place1>{NAME}), sous-directeur, signature collective à deux; (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), procuration collective à deux")
    if m:
        return [person('erroneously_deleted_officer_reinstated', m, m['name1'], 'Vizedirektor', 'Kollektivunterschrift zu zweien', m['place1']), person('erroneously_deleted_procuration_reinstated', m, m['name2'], signing='Kollektivprokura zu zweien', place=m['place2'])], ''

    m = match(rf'Mit Urteil vom (?P<decision_date>{DATE}) hat das Nachlassgericht des Bezirksgerichts (?P<court_place>{NAME}) letztmals die COVID-19-Stundung um drei Monate bis am (?P<end_date>{DATE}) verlängert', 'de')
    if m:
        return [event('covid19_moratorium_final_extension', m)], ''

    return [], leftover
