from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, COUNT, UID


def extract_parser336_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume only complete, sample-backed residues after the legacy rules."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang):
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
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={**{k: v for k, v in m.groupdict().items() if k not in ('name', 'place')}, 'action': action})

    # The supplied publication metadata is French for these German clauses.
    m = match(rf'Eingetragene Personen neu oder mutierend: (?P<name>{NAME}) \((?P<auditor_uid>{UID})\), in (?P<place>{NAME}), Revisionsstelle', 'fr')
    if m:
        return [person('registered_auditor_recorded', m, m['name'], 'Revisionsstelle', place=m['place'])], ''

    m = match(rf'Die Gesellschaft ist laut Beschluss der Generalversammlung vom (?P<decision_date>{DATE}) aufgelöst\. Neue Firma: (?P<company>{NAME}) \((?P<translation>{NAME})\)\. Eingetragene Person geändert: (?P<previous_name>[^,;]+), korrekterweise (?P<name>{NAME}), Verwaltungsratsmitglied, Einzelunterschrift, neu Verwaltungsratsmitglied, Liquidator, Einzelunterschrift\. Neu eingetragene Person: (?P<new_name>{NAME}), von und in (?P<place>{NAME}), Liquidator, Einzelunterschrift', 'fr')
    if m:
        return [event('dissolution_and_liquidation_name', m), person('board_liquidator_name_corrected', m, m['name'], 'Verwaltungsrat und Liquidator', 'Einzelunterschrift'), person('liquidator_joined', m, m['new_name'], 'Liquidator', 'Einzelunterschrift', m['place'])], ''

    m = match(rf"La clause d'augmentation autorisée du capital-actions décidée par l'assemblée générale du (?P<authorization_date>{DATE}) a été supprimée selon décision de l'assemblée générale du (?P<decision_date>{DATE})", 'fr')
    if m:
        return [event('authorized_capital_clause_deleted', m, 'capital_changed')], ''

    m = match(rf'(?P<name>{NAME}), maintenant au (?P<place>{NAME}), est nommée administratrice et continue à engager la société par sa signature individuelle\. Nouvel administrateur : (?P<president>{NAME}), du (?P<origin>{NAME}), au (?P<president_place>{NAME}), président', 'fr')
    if m:
        confirmed = re.search(r'Nouvel administrateur avec signature individuelle: ' + re.escape(m['president']) + r', du ' + re.escape(m['origin']) + r', au ' + re.escape(m['president_place']) + r', président\.?$', source_text)
        return [person('board_member_residence_and_role', m, m['name'], 'Verwaltungsrat', 'Einzelunterschrift', m['place']), person('board_president_joined', m, m['president'], 'Verwaltungsrat und Präsident', 'Einzelunterschrift' if confirmed else None, m['president_place'])], ''

    m = match(rf"La faillite de la société a été prononcée par jugement du Tribunal de première instance du (?P<judgment_date>{DATE}), avec effet à partir du (?P<effective_date>{DATE}) à (?P<effective_time>(?:[01]\d|2[0-3]):[0-5]\d)\. Par conséquent\. sa raison sociale devient: (?P<company>[^;]+?)\. La procédure de faillite a été suspendue faute d'actif par jugement du Tribunal de première instance du (?P<suspension_date>{DATE})", 'fr')
    if m:
        return [event('bankruptcy_and_suspension_no_assets', m)], ''

    # Conversely, this French clause carries German publication metadata.
    m = match(rf"Signature collective à deux est conférée à (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<name3>{NAME}), de (?P<origin3>{NAME}), au (?P<place3>{NAME}), tous trois directeurs, et (?P<name4>{NAME}), d'(?P<origin4>{NAME}), à (?P<place4>{NAME})", 'de')
    if m:
        return [person('directors_and_signatory_collective', m, m[f'name{i}'], 'Direktor' if i < 4 else None, 'Kollektivunterschrift zu zweien', m[f'place{i}']) for i in range(1, 5)], ''

    m = match(rf"L'associé-gérant (?P<holder>{NAME}), qui est nommé président, cède (?P<transferred_count>{COUNT}) de ses (?P<previous_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<recipient>{NAME}), de (?P<origin>{NAME}), au (?P<place>{NAME}), nouvelle associée avec (?P<received_count>{COUNT}) parts de CHF (?P=nominal), gérante (?P=holder) reste titulaire de (?P<retained_count>{COUNT}) parts de CHF (?P=nominal)", 'fr')
    if m:
        return [event('partial_share_transfer_manager_presidency', m, 'ownership_changed', currency='CHF'), person('associate_manager_president', m, m['holder'], 'Gesellschafter und Geschäftsführer und Vorsitzender'), person('associate_manager_joined', m, m['recipient'], 'Gesellschafter und Geschäftsführer', place=m['place'])], ''

    if language == 'fr' and leftover == 'lequel signe individuellement':
        m = re.search(rf'Nouvel associé indéfiniment responsable: (?P<name>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME}), lequel signe individuellement\.?$', source_text)
        if m:
            return [person('unlimited_partner_individual_signing', m, m['name'], 'unbeschränkt haftender Gesellschafter', 'Einzelunterschrift', m['place'])], ''

    m = match(rf'Mit Beschluss der Generalversammlung vom (?P<decision_date>{DATE}) wird die Statutenbestimmung über die mit Ermächtigungsbeschluss vom (?P<authorization_date>{DATE}) beschlossene genehmigte Kapitalerhöhung gestrichen\. \[gestrichen: Die Generalversammlung hat mit Beschluss vom (?P=authorization_date) den Beschluss über die Ermächtigung einer genehmigten Kapitalerhöhung vom (?P<introduction_date>{DATE}) gemäss näherer Umschreibung in den Statuten angepasst\.\]', 'de')
    if m:
        return [event('authorized_capital_provision_deleted', m, 'capital_changed')], ''

    m = match(rf"L'associée (?P<holder>{NAME}) est désormais titulaire de (?P<retained_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) suite à la cession d'une part sociale de CHF (?P=nominal) à (?P<recipient>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée pour 1 part de CHF (?P=nominal), laquelle signe collectivement à deux avec la gérante", 'fr')
    if m:
        return [event('single_share_transfer_restricted_signing', m, 'ownership_changed', currency='CHF', transferred_count='1'), person('new_associate_signing_with_manager', m, m['recipient'], 'Gesellschafter', 'Kollektivunterschrift zu zweien mit der Geschäftsführerin', m['place'])], ''

    m = match(rf"En complément de l'inscription no\. (?P<entry>{COUNT}) du (?P<entry_date>{DATE}), dépot d'un nouvel exemplaire des statuts", 'fr')
    if m:
        return [event('statutes_copy_filed_complement', m)], ''

    m = match(r"Ressources: (?P<resources>terrains, immeubles et installations; finances d'entrée; entrées et recettes diverses; paiement des cotisations; subventions; dons, legs et divers; excédent annuel de l'activité) \[biffé: parts de membres de CHF (?P<previous_nominal>" + MONEY + r")\.-- ou d'un multiple de ce chiffre\]", 'fr')
    if m:
        return [event('association_resources_replaced', m, currency='CHF')], ''

    return [], leftover
