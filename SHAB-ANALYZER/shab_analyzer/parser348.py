from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser348_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Append complete, sample-backed clauses after all existing rules."""
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
                    if key == 'time':
                        datetime.strptime(value, '%H:%M')
            except ValueError:
                return None
        return m

    def event(action, m):
        return _event(*context, 'organization_changed', f'{language}.text.{action}.v1', {'action': action, **m.groupdict()})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **m.groupdict(), **extra, 'name': name})


    m = match(rf'Berichtigung der Eintragung Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) \(SHAB vom (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\): die richtige UID-Nummer lautet (?P<uid>{UID}) \(und nicht (?P<previous_uid>\d{{3}}\.\d{{3}}\.\d{{3}})\)', 'de')
    if m:
        return [event('organization_uid_corrected', m)], ''

    m = match(rf'Mit Erklärung vom (?P<declaration_date>{DATE}) wurde auf eine eingeschränkte Revision verzichtet', 'de')
    if m:
        return [event('limited_audit_waived_by_declaration', m)], ''

    m = match(rf'Das Konkursverfahren wurde mit Verfügung des Gerichtspräsidiums (?P<court_place>{NAME}) vom (?P<decision_date>{DATE}) mangels Aktiven eingestellt', 'de')
    if m:
        return [event('bankruptcy_discontinued_insufficient_assets', m)], ''

    m = match(rf'Das Konkursverfahren wurde mit Urteil der Konkursrichterin vom (?P<decision_date>{DATE}) als geschlossen erklärt und das Handelsregisteramt angewiesen, die Löschung der Gesellschaft erst auf Anweisung des Konkursamtes hin vorzunehmen\. Die Eintragung bleibt nur zum Zweck der Geltendmachung von abgetretenen Ansprüchen nach Art\. 260 SchKG erhalten und die Verfügungsbefugnisse der Organe der Gesellschaft leben nicht wieder auf', 'de')
    if m:
        return [event('bankruptcy_closed_registration_retained_for_assigned_claims', m)], ''

    m = match(rf'Par décision du (?P<decision_date>{DATE}), le Tribunal régional du (?P<court_place>{NAME}) a mis à néant le jugement de faillite du (?P<bankruptcy_date>{DATE}) concernant le titulaire')
    if m:
        return [event('proprietor_bankruptcy_judgment_annulled', m)], ''

    m = match(rf'Nouveaux membres du conseil de fondation avec le président ou le vice-président: (?P<name1>{NAME}), de (?P<origin1>{NAME}), et (?P<name2>{NAME}), de (?P<origin2>{NAME}), tous deux à (?P<place>{NAME})')
    if m:
        return [person('foundation_members_with_president_or_vice_president', m, m[f'name{i}'], 'Mitglied des Stiftungsrates', place=m['place'], signing_partner_roles=['président', 'vice-président']) for i in (1, 2)], ''

    m = match(rf"Administration: (?P<name1>{NAME}), nommée présidente et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<country2>[A-Z]{{3}}), lesquelles signent individuellement")
    if m:
        return [person('board_president_and_member_individual_signing', m, m[f'name{i}'], 'Präsidentin' if i == 1 else 'Verwaltungsrat', 'Einzelunterschrift', m.groupdict().get(f'place{i}')) for i in (1, 2)], ''

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name>{NAME}), membre et président du conseil d'administration, signe individuellement \(et non pas collectivement à deux\) et que Monsieur (?P<surname>{NAME}) porte les prénoms (?P<given_names>{NAME}) \(et non pas (?P<previous_given_names>{NAME})\)")
    if m:
        return [person('board_president_signing_corrected', m, m['name'], 'Präsident', 'Einzelunterschrift', previous_signing='Kollektivunterschrift zu zweien'), person('officer_given_names_corrected', m, m['surname'] + ' ' + m['given_names'])], ''

    m = match(rf"L'assemblée générale du (?P<decision_date>{DATE}) a supprimé la clause statutaire relative à l'augmentation autorisée du capital-actions adoptée le (?P<authorization_date>{DATE})\. L'assemblée générale du (?P=decision_date) a modifié la clause statutaire relative à l'augmentation conditionnelle du capital-actions prise par décision du (?P<conditional_authorization_date>{DATE}); pour les détails, voir les statuts \(art\. 3b al\. 2\)")
    if m:
        return [event('authorized_capital_clause_deleted_conditional_clause_amended', m)], ''

    m = match(rf"Par décision du (?P<decision_date>{DATE}), l'assemblée générale a modifié la clause statutaire relative à l'augmentation conditionnelle du capital-actions introduite par décision du (?P<authorization_date>{DATE}); pour les détails, voir les statuts\. L'administrateur (?P<name1>{NAME}), nommé président, et l'administrateur (?P<name2>{NAME}), jusqu'ici président, nommé vice-président, continuent de signer collectivement à deux")
    if m:
        return [event('conditional_capital_clause_amended', m)] + [person('board_president_vice_president_continued_signing', m, m[f'name{i}'], 'Präsident' if i == 1 else 'Vizepräsident', 'Kollektivunterschrift zu zweien') for i in (1, 2)], ''

    # Validate the entire sequence before accepting any individual clause.
    if language == 'fr':
        signing_pattern = rf'(?P<name>{NAME}) continue à signer collectivement à deux, désormais avec (?P<partner1>{NAME}), (?P<partner2>{NAME}) et (?P<partner3>{NAME})'
        clauses = leftover.rstrip('.').split('. ')
        matches = [re.fullmatch(signing_pattern, clause) for clause in clauses]
        if matches and all(matches):
            return [person('continued_collective_signing_named_partners', m, m['name'], signing='Kollektivunterschrift zu zweien', authorized_partners=[m[f'partner{i}'] for i in (1, 2, 3)]) for m in matches], ''

        contribution_pattern = rf"La commandite de l'associée commanditaire (?P<name>[^()]+) \((?P<uid>{UID})\) a été (?P<change>réduite|portée) de CHF (?P<previous_amount>{COUNT})\.- à CHF (?P<amount>{COUNT})\.-"
        matches = [re.fullmatch(contribution_pattern, clause) for clause in leftover.rstrip('.').split('. ')]
        if matches and all(matches):
            from decimal import Decimal
            def amount(m, key):
                return Decimal(m[key].replace("'", ''))
            if all(amount(m, 'amount') > 0 and ((amount(m, 'amount') < amount(m, 'previous_amount')) if m['change'] == 'réduite' else (amount(m, 'amount') > amount(m, 'previous_amount'))) for m in matches):
                return [event('limited_partner_contribution_changed', m) for m in matches], ''

    return [], leftover
