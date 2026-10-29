from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser409 import NAME
from . import parser50, parser56, parser114, parser153, parser154, parser213, parser223

# Preserve the ownership of the related historical patterns, including in isolation.
_LEGACY = tuple(p for module in (parser50, parser56, parser114, parser153, parser154, parser213, parser223)
                for p in vars(module).values() if isinstance(p, re.Pattern))


def extract_parser426_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Bounded residual variants from the release 426 fixtures."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language not in ((lang,) if isinstance(lang, str) else lang):
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for date in re.findall(DATE, m[0]):
                    datetime.strptime(date, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name,
                             role=role, signing=signing, place=place,
                             extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    m = match(rf'Der Eintrag Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) \(SHAB vom (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\) ist wie folgt ergänzt: Neue zusätzliche Adresse: (?P<street>{NAME}), (?P<postal_code>\d{{4}}) (?P<place>{NAME})', ('de', 'fr'))
    if m:
        return [event('additional_address_supplemented_notice', m, 'address_changed', supplemented=True)], ''

    m = match(rf"Radiation de la mention de l'existence de succursales à (?P<place1>{NAME}), (?P<place2>{NAME}) et (?P<place3>{NAME})")
    if m:
        return [event('three_branch_mentions_removed_plural', m, mention_removed=True)], ''

    m = match(rf"Par décision du (?P<decision_date>{DATE}), l'assemblée générale a introduit une clause statutaire relative à une augmentation conditionnelle du capital-actions\. Pour les détails, voir les statuts")
    if m:
        return [event('conditional_capital_clause_introduced_decision_first', m, 'capital_changed', introduced=True)], ''

    m = match(rf'Mit Verfügung vom (?P<decision_date>{DATE}) hat das (?P<appeal_court>[^;\n]+?) der Beschwerde gegen den Entscheid des Konkursrichters des (?P<court>[^;\n]+?) vom (?P<bankruptcy_date>{DATE}) betreffend Konkurseröffnung aufschiebende Wirkung zuerkannt\. Demnach wird die Eintragung betreffend Konkurs im Handelsregister gestrichen\. \[bisher: Über die Inhaberin dieses Einzelunternehmens ist mit Entscheid des Konkursrichters des (?P=court) vom (?P=bankruptcy_date) mit Wirkung ab dem (?P<effective_date>{DATE}), (?P<time>(?:[01]\d|2[0-3])\.[0-5]\d) Uhr der Konkurs eröffnet worden\.\]', 'de')
    if m:
        return [event('female_owner_bankruptcy_appeal_suspended_order', m, 'status_changed', suspensive_effect=True, bankruptcy_entry_removed=True)], ''

    m = match(rf'(?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée avec (?P=count) parts de CHF (?P=nominal), gérante (?P=seller), qui est nommé président, reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)')
    if m and re.search(r'nouvelle associée avec ' + re.escape(m['count']) + r' parts de CHF ' + re.escape(m['nominal']) + r', gérante avec signature individuelle\. ' + re.escape(m['seller']) + r', qui est nommé président, reste titulaire de ' + re.escape(m['remaining']) + r' parts de CHF ' + re.escape(m['nominal']) + r'\.?$', source_text):
        return [event('share_transfer_new_female_manager_seller_president', m, 'ownership_changed', currency='CHF'),
                person('new_female_associate_manager_after_transfer', m, m['buyer'], 'gérante', 'Einzelunterschrift', m['place']),
                person('seller_manager_president_after_transfer', m, m['seller'], 'président')], ''

    m = match(r'Da die Gesellschaft sämtliche Inhaber-Partizipationsscheine als Bucheffekten im Sinne des Bucheffektengesetzes ausgestaltet hat, ist sie befugt, sie zu halten', 'de')
    if m:
        return [event('bearer_participation_certificates_intermediated_authorized', m, 'capital_changed', intermediated=True)], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(publication FOSC du (?P<notice_date>{DATE}), page (?P<notice_ref>\d+/\d+)\) est rectifiée dans ce sens que l'associée (?P<name>{NAME}) détient (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) \(et non: (?P<previous_count>{COUNT}) parts de CHF (?P=nominal)\)")
    if m:
        return [event('associate_share_count_corrected_notice', m, 'ownership_changed', corrected=True, currency='CHF')], ''

    # The published new identifier is short; preserve it verbatim, never repair it.
    m = match(rf'Nuova succursale: (?P<place>{NAME}) \((?P<branch_uid>CHE-\d{{3}}\.\d{{3}}\.\d{{2}})\) \[finora: (?P<previous_place>{NAME}) \((?P<previous_uid>{UID})\)\]', 'it')
    if m:
        return [event('branch_location_changed_short_published_uid', m, 'address_changed')], ''

    m = match(rf"Administration: (?P<name1>{NAME}), jusqu'ici directeur, nommé président et (?P<name2>{NAME}), maintenant domicilié à (?P<place2>{NAME}), lesquels continuent à signer individuellement")
    if m:
        return [person('director_appointed_president_pair_continued_signing', m, m['name1'], 'président', 'Einzelunterschrift', previous_role='directeur'),
                person('administrator_pair_residence_changed_continued_signing', m, m['name2'], 'administrateur', 'Einzelunterschrift', m['place2'])], ''

    m = match(rf'Par décision du (?P<decision_date>{DATE}), le (?P<court>{NAME}) a déclaré irrecevable le recours contre le jugement de faillite du (?P<bankruptcy_date>{DATE})')
    if m:
        return [event('bankruptcy_appeal_declared_inadmissible', m, 'status_changed', appeal_inadmissible=True)], ''

    m = match(rf'Persona iscritta corretta: (?P<surname>{NAME}), (?P<given_names>{NAME}), da (?P<origin>{NAME}), in (?P<place>{NAME}), direttore, con firma collettiva a due', 'it')
    if m:
        return [person('director_identity_corrected_collective_signing', m, m['surname'] + ', ' + m['given_names'], 'direttore', 'Kollektivunterschrift zu zweien', m['place'], corrected=True)], ''

    m = match(rf'Die am (?P<deletion_date>{DATE}) irrtümlich gelöschte Gesellschaft wird zum Zwecke der Liquidation wieder in das Handelsregister eingetragen, da noch verwertbare Aktiven vorliegen\. Die Gesellschaft besteht entsprechend den früheren Eintragungen weiter\. \[bisher: Nachdem gegen die Löschung kein begründeter Einspruch erhoben wurde, wird die Gesellschaft in Anwendung von Art\. 159 Abs\. 5 HRegV von Amtes wegen gelöscht\.\]\. \[Berichtrigung des im SHAB Nr\. (?P<notice_number>{COUNT}) vom (?P<notice_date>{DATE}) publizierten TR-Eintrags Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE})\.\]', 'de')
    if m:
        return [event('erroneous_deletion_reinstated_for_liquidation_corrected_notice', m, 'status_changed', reinstated=True, in_liquidation=True, corrected=True)], ''
    return [], text
