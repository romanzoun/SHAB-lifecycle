from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, COUNT, UID


def extract_parser335_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete sample-backed residues after all existing rules."""
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

    def person(action, m, name, role, signing=None, place=None, kind='officer_changed'):
        return _person_event(*context, kind, f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={**{k: v for k, v in m.groupdict().items() if k not in ('name', 'place')}, 'action': action})

    m = match(rf'L\'associé (?P<holder>{NAME}) a cédé (?P<transferred_count>{COUNT}) de ses (?P<previous_count>{COUNT}) parts sociales de CHF (?P<nominal>{MONEY}) à la société "(?P<recipient>{NAME})" \((?P<recipient_uid>{UID})\), à (?P<recipient_place>{NAME}), nouvelle associée\. Gérants: (?P<manager>{NAME}), d\'(?P<manager_origin>{NAME}), à (?P<place>{NAME}), président, et (?P=holder), lesquels signent individuellement', 'fr')
    if m:
        return [event('partial_share_transfer_to_company', m, 'ownership_changed', currency='CHF'), person('managers_individual_signing', m, m['manager'], 'Geschäftsführer und Vorsitzender', 'Einzelunterschrift', m['place']), person('managers_individual_signing', m, m['holder'], 'Geschäftsführer', 'Einzelunterschrift')], ''

    # Initials contain a full stop; do not broaden the common NAME grammar.
    m = match(r"(?P<name>[^,;]+), de (?P<origin>[^,;]+), à (?P<place>[^,;]+), est membre du conseil d'administration; n'exerce pas la signature sociale", 'fr')
    if m:
        return [person('board_member_without_signing', m, m['name'], 'Verwaltungsrat', 'ohne Zeichnungsberechtigung', m['place'])], ''

    m = match(rf"En complément à l'inscription no\. (?P<entry>{COUNT}) du (?P<entry_date>{DATE}), dépot d'un nouvel exemplaire des statuts", 'fr')
    if m:
        return [event('statutes_copy_filed_supplement', m)], ''

    m = match(rf"Fusione: ripresa di attivi e passivi di (?P<transferor>{NAME}), in (?P<transferor_place>{NAME}) \((?P<transferor_uid>{UID})\), secondo contratto di fusione del (?P<agreement_date>{DATE}) e bilancio al (?P<balance_date>{DATE}), che presenta attivi per CHF (?P<assets>{MONEY}), e passivi verso terzi per CHF (?P<liabilities>{MONEY}), con un'eccedenza passiva di CHF (?P<excess_liabilities>{MONEY})\. Conformemente all'attestazione di un perito revisore abilitato, la società assuntrice dispone di fondi propri liberamente disponibili equivalenti almeno all'ammontare dello scoperto e del sovraindebitamento\. La società assuntrice detiene tutte le azioni della società trasferente, per cui la fusione avviene senza aumento del capitale e senza attribuzione di azioni", 'it')
    if m:
        return [event('subsidiary_merger_excess_liabilities', m, 'ownership_changed', currency='CHF', no_capital_increase=True, no_share_allocation=True, freely_available_equity_confirmed=True)], ''

    m = match(r'Angaben zur Zweigniederlassung neu: \. Zweck der Zweigniederlassung: (?P<purpose>Erbringung von Dienstleistungen im Treuhandbereich[^\n]+?unter Ausschluss bewilligungs- oder genehmigungspflichtiger, insbesondere bankgeschäftlicher Tätigkeiten)', 'de')
    if m:
        return [event('branch_purpose_recorded', m)], ''

    # An older rule consumed "HR Ob". Resolve the fragment only with the
    # complete, anchored register statement from the original publication.
    if language == 'de' and leftover == 'erwallis':
        m = re.search(rf'Zweigniederlassung neu: \[Sitz\] (?P<branch_place>{NAME}) \((?P<branch_uid>{UID})\) HR (?P<register>Oberwallis)\.?$', source_text)
        if m:
            return [event('branch_register_completed', m)], ''

    m = match(rf'Fusion: Übernahme der Aktiven und der Passiven der (?P<transferor>{NAME}) \((?P<transferor_uid>{UID})\), in (?P<transferor_place>{NAME}), gemäss Fusionsvertrag vom (?P<agreement_date>{DATE}) und Bilanz per (?P<balance_date>{DATE})\. Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}), d\.h ein Passivenüberschuss von CHF (?P<excess_liabilities>{MONEY}) gehen auf die übernehmende Gesellschaft über\. Gemäss Bestätigung des zugelassenen Revisionsexperten liegen Rangrücktritte im Umfang des Kapitalverlustes und der Überschuldung der übertragenden Gesellschaft vor\. Da derselbe Gesellschafter sämtliche Stammanteile der an der Fusion beteiligten Gesellschaften hält, findet weder eine Kapitalerhöhung noch eine Zuteilung von Stammanteilen statt', 'fr')
    if m:
        return [event('common_owner_merger_subordinated_debt', m, 'ownership_changed', currency='CHF', no_capital_increase=True, no_share_allocation=True, subordinated_debt_confirmed=True)], ''

    m = match(rf'Genehmigte Partizipationskapitalerhöhung \[Ermächtigungsbeschluss vom (?P<authorization_date>{DATE})\]: Die am (?P<deletion_date>{DATE}) \(TR-Nr\. (?P<deletion_entry>{COUNT})\) fälschlicherweise gelöschte genehmigte Partizipationskapitalerhöhung wird gemäss den Belegen von TR-Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) erneut im Handelsregister eingetragen', 'de')
    if m:
        return [event('authorized_participation_capital_reinstated', m, 'capital_changed')], ''

    m = match(rf"Par suite de cession de (?P<transferred_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}), l'associé (?P<holder>{NAME}) est désormais titulaire de (?P<retained_count>{COUNT}) parts de CHF (?P=nominal) et, (?P<recipient>{NAME}), de (?P<recipient_origin>{NAME}), à (?P<place>{NAME}), est nouvel associé pour (?P<received_count>{COUNT}) parts de CHF (?P=nominal)\. Gérants: les associés (?P=holder), nommé président, et (?P=recipient), tous deux", 'fr')
    if m:
        # Signing was consumed upstream. Confirm it without inventing a value
        # when the optional source is unavailable.
        clause = leftover + ' avec signature individuelle'
        confirmed = re.search(r'(?<!\S)' + re.escape(clause) + r'\.?$', source_text)
        signing = 'Einzelunterschrift' if confirmed else None
        return [event('share_transfer_and_manager_presidency', m, 'ownership_changed', currency='CHF'), person('associate_manager_president', m, m['holder'], 'Gesellschafter und Geschäftsführer und Vorsitzender', signing), person('new_associate_manager', m, m['recipient'], 'Gesellschafter und Geschäftsführer', signing, m['place'])], ''

    m = match(rf'Trasferimento di patrimonio: Secondo contratto del (?P<agreement_date>{DATE}), la società ha trasferito attivi per CHF (?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY}) alla (?P<recipient>{NAME}), in (?P<recipient_place>{NAME}) \((?P<recipient_uid>{UID})\)\. Controprestazione: nessuna', 'it')
    if m:
        return [event('asset_transfer_no_consideration', m, 'ownership_changed', currency='CHF', no_consideration=True)], ''

    m = match(rf"(?P<departed1>{NAME}), et (?P<departed2>[^,;]+) ne sont plus associés ni gérants; leurs pouvoirs sont radiés; leurs (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) ont été cédées à (?P<recipient>{NAME}), de (?P<recipient_origin>{NAME}), à (?P<place>{NAME}), nouvel associé-gérant pour (?P=count) parts de CHF (?P=nominal)", 'fr')
    if m:
        return [event('all_shares_transferred_departing_managers', m, 'ownership_changed', currency='CHF'), *[person('associate_manager_removed', m, m[key], 'Gesellschafter und Geschäftsführer', kind='officer_removed') for key in ('departed1', 'departed2')], person('associate_manager_joined', m, m['recipient'], 'Gesellschafter und Geschäftsführer', place=m['place'])], ''

    m = match(rf'Die Generalversammlung hat mit Beschluss vom (?P<decision_date>{DATE}) die mit Beschluss vom (?P<introduction_date>{DATE}) eingeführte und mit Beschluss vom (?P<previous_date>{DATE}) geänderte genehmigte Kapitalerhöhung gemäss näherer Umschreibung in Art\. (?P<article>3a) der Statuten geändert\. \[bisher: Die Generalversammlung hat mit Beschluss vom (?P=previous_date) die mit Beschluss vom (?P=introduction_date) eingeführte genehmigte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten geändert\.\]', 'de')
    if m:
        return [event('authorized_capital_increase_amended', m, 'capital_changed')], ''

    return [], leftover
