from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY


def extract_parser328_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Complete bounded sample clauses after earlier rules, without replacing events."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', source_pattern=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m:
            return None
        if source_pattern:
            s = re.search(source_pattern + r'\.?$', source_text)
            if not s or any(s[k] != v for k, v in m.groupdict().items()):
                return None
            m = s
        try:
            for k, v in m.groupdict().items():
                if k.endswith('_date') and v is not None:
                    datetime.strptime(v, '%d.%m.%Y')
        except ValueError:
            return None
        return m

    def event(action, m, event_type='organization_changed', **extra):
        return _event(*context, event_type, f'{language}.text.{action}.v1', {**m.groupdict(), 'action': action, **extra})

    def person(action, m, name, role, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={**m.groupdict(), 'action': action, **extra})

    m = match(r'Nouveau capital au 00', source_pattern=rf'Nouveau capital au siège principal: (?P<currency>USD) (?P<capital>{MONEY})')
    if m:
        return [event('head_office_capital_recorded', m, 'capital_changed', scope='head_office')], ''

    m = match(rf'Diese Gesellschaft hat sich infolge Todes des Gesellschafters (?P<deceased>{NAME}) (?<!nicht )aufgelöst\. Die Firma ist erloschen\. Der Gesellschafter (?P<successor>{NAME}) führt im Sinne von Art\. 579 OR das Geschäft als Einzelkaufmann fort', 'de')
    if m:
        return [event('partnership_dissolved_business_continued', m, 'status_changed', dissolved=True, business_continued=True, continuation_form='Einzelkaufmann')], ''

    m = match(rf"L'inscription no (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que le nom (?P<previous_name>{NAME}) s'orthographie (?P<name>{NAME})")
    if m:
        return [event('surname_spelling_corrected', m, 'publication_corrected', corrected=True)], ''

    m = match(rf'Mit Entscheid des (?P<court>{NAME}) vom (?P<decision_date>{DATE}) wurde der eröffnete Konkurs widerrufen\. Infolgedessen besteht die Firma entsprechend den früheren Eintragungen weiter\. \[bisher: Mit Verfügung des (?P<previous_court>{NAME}) vom (?P<previous_decision_date>{DATE}) wurde die Beschwerde des Gesuchgegners abgewiesen\. Infolgedessen wird mit Wirkung ab (?P<previous_effective>\d+\. November \d{{4}}, \d{{2}}\.\d{{2}} Uhr), der Konkurs neu eröffnet\.\]', 'de')
    if m:
        return [event('bankruptcy_revoked_previous_registration_restored', m, 'status_changed', bankruptcy_revoked=True)], ''

    pattern = rf'La société est dissoute\. (?P<name1>{NAME}), (?P<name2>{NAME}) et (?P<name3>{NAME}) sont nommés liquidateurs'
    m = match(pattern, source_pattern=rf'La société est dissoute\. La liquidation est opérée sous la raison de commerce: (?P<liquidation_name>[^.]+)\. (?P<name1>{NAME}), (?P<name2>{NAME}) et (?P<name3>{NAME}) sont nommés liquidateurs avec signature individuelle')
    if m:
        return [event('dissolution_and_liquidators_appointed', m, 'status_changed', dissolved=True)] + [person('liquidators_appointed_individual_signing', m, m[f'name{i}'], 'Liquidator', 'Einzelunterschrift') for i in (1, 2, 3)], ''

    pattern = rf"Les administrateurs (?P<name1>{NAME}), jusqu'ici vice-président, nommé président et (?P<name2>{NAME}), jusqu'ici président, maintenant vice-président, continuent à signer collectivement à deux\. (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}) et (?P<name4>{NAME}), de (?P<origin4>{NAME}), à (?P<place4>{NAME}), sont membres du conseil d'administration, tous deux"
    m = match(pattern, source_pattern=pattern + r' avec signature collective à deux')
    if m:
        return [person('board_presidency_exchanged', m, m['name1'], 'Verwaltungsratspräsident', 'Kollektivunterschrift zu zweien', previous_role='vice-président'), person('board_presidency_exchanged', m, m['name2'], 'Vizepräsident', 'Kollektivunterschrift zu zweien', previous_role='président')] + [person('board_members_appointed_collective_signing', m, m[f'name{i}'], 'Verwaltungsrat', 'Kollektivunterschrift zu zweien', m[f'place{i}']) for i in (3, 4)], ''

    m = match(rf"(?P<name1>{NAME}), nommé président, et (?P<name2>{NAME}), directeur général, jusqu'ici président, membres du conseil d'administration, continuent de signer collectivement à deux")
    if m:
        return [person('board_president_appointed_signing_retained', m, m['name1'], 'Verwaltungsratspräsident', 'Kollektivunterschrift zu zweien'), person('board_general_director_role_changed', m, m['name2'], 'Verwaltungsrat, Generaldirektor', 'Kollektivunterschrift zu zweien', previous_role='président')], ''

    m = match(rf'Die Umschreibung der mit Beschluss der Generalversammlung vom (?P<introduction_date>{DATE}) eingeführten Bestimmung und bereits am (?P<previous_change_date>{DATE}) geänderte Bestimmung über das genehmigte Kapital wurde mit Beschluss der Generalversammlung vom (?P<decision_date>{DATE}) geändert\. \[gestrichen: \]', 'de')
    if m:
        return [event('authorized_capital_provision_changed', m, 'capital_changed')], ''

    m = match(r'Adjonction de la version anglaise de la raison de commerce: (?P<name>[^\[\]]+) \[(?P<english_name>[^\[\]]+)\]')
    if m:
        return [event('english_company_name_added', m)], ''

    m = match(rf"Par jugement du (?P<decision_date>{DATE}), le (?P<court>{NAME}) a prolongé le sursis concordataire définitif accordé à la société jusqu'au (?P<end_date>{DATE})")
    if m:
        return [event('definitive_composition_stay_extended', m, 'status_changed', definitive_stay=True)], ''

    m = match(rf"Suppression de la clause statutaire relative à l'augmentation autorisée du capital fondée sur la décision d'autorisation du (?P<authorization_date>{DATE}) \. L'assemblée générale a introduit une clause statutaire relative à une augmentation conditionnelle du capital par décision du (?P<decision_date>{DATE}) Pour les détails, voir les statuts")
    if m:
        return [event('authorized_clause_removed_conditional_clause_introduced', m, 'capital_changed', authorized_clause_removed=True, conditional_clause_introduced=True)], ''

    m = match(rf"La clause d'augmentation conditionnelle du capital-actions décidée par l'assemblée générale du (?P<introduction_date>{DATE}) a été modifiée selon décision du (?P<decision_date>{DATE}) \(pour les détails voir les statuts\)")
    if m:
        return [event('conditional_capital_clause_changed', m, 'capital_changed')], ''

    return [], leftover
