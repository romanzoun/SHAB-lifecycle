from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY


def extract_parser324_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Append sample-supported residual events without replacing legacy payloads."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('_date') and value is not None:
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {**m.groupdict(), 'action': action, **extra})

    def person(action, m, suffix='', role=None, signing=None):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', m['name'+suffix], place=m.groupdict().get('place'+suffix), role=role, signing=signing, extra={**m.groupdict(), 'action': action})

    m = match(rf'Administration: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), président, (?P<name2>{NAME}), secrétaire, nommé délégué, (?P<name3>{NAME}), jusqu’ici directeur, maintenant délégué, (?P<name4>{NAME}), jusqu’ici président, maintenant délégué et (?P<name5>{NAME}), de (?P<origin5>{NAME}), à (?P<place5>{NAME}), tous'.replace('’', "'"))
    if m and leftover + ' avec signature collective à deux.' in source_text:
        return [person('administration_delegates_collective_signing', m, str(i), role=role, signing='Kollektivunterschrift zu zweien') for i, role in enumerate(['Präsident', 'Sekretär, Delegierter', 'Delegierter', 'Delegierter', 'Verwaltungsrat'], 1)], ''

    m = match(rf'Mit 3-seitigem Auszug aus dem Entscheid mit Seite 1, 8 und 9 des (?P<court>Kreisgerichts {NAME}) vom (?P<decision_date>{DATE}) wurde die definitive Nachlassstundung um (?P<extension>zwei Monate), d\.h\. ab (?P<from_date>{DATE}) bis zum (?P<until_date>{DATE}) verlängert\. \[bisher: Mit Entscheid des (?P=court) vom (?P<previous_decision_date>{DATE}) wurde die definitive Nachlassstundung um (?P<previous_extension>vier Monate), d\.h\. bis zum (?P<previous_until_date>{DATE}) verlängert\.\]', 'de')
    if m:
        return [event('definitive_moratorium_extension_replaced', m, months='2', previous_clause_removed=True)], ''

    # These are removed historical clauses, not new contributions or acquisitions.
    m = match(rf'eingetragene Benutzungsrechte im Werte und Preise von CHF (?P<assets>{MONEY})\.--, wofür (?P<shares>{MONEY}) Namenaktien zu CHF (?P<nominal>{MONEY})\.-- ausgegeben werden und CHF (?P<loan>{MONEY})\.- als Darlehen bestehen bleiben\.\]\. (?P<removed_clauses>(?:\[gestrichen: Sacheinlage/Sachübernahme: Die Gesellschaft übernimmt bei der Kapitalerhöhung vom {DATE} gemäss Sacheinlagevertrag vom {DATE}[^\[\]]+\.\]\. )*\[gestrichen: Sacheinlage/Sachübernahme: Die Gesellschaft übernimmt bei der Kapitalerhöhung vom {DATE} gemäss Sacheinlagevertrag vom {DATE}[^\[\]]+\.\])', 'de')
    if m:
        clauses = re.findall(r'\[gestrichen: Sacheinlage/Sachübernahme: [^\[\]]+\]', source_text)
        if clauses and source_text.endswith((leftover, leftover + '.')) and any('sowie ' + leftover.split('].', 1)[0] + ']' in clause for clause in clauses):
            dates = re.findall(DATE, m['removed_clauses'])
            try:
                for date in dates:
                    datetime.strptime(date, '%d.%m.%Y')
            except ValueError:
                return [], leftover
            return [event('historical_contribution_clauses_removed', m, previous_clause_removed=True, removed_clause_count=len(clauses), currency='CHF')], ''

    m = match(rf'Administration: (?P<name1>{NAME}), maintenant originaire de (?P<origin1>{NAME}), nommée présidente et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), lesquels signent individuellement')
    if m:
        return [person('administration_president_and_member_individual_signing', m, str(i), role='Präsidentin' if i == 1 else 'Verwaltungsrat', signing='Einzelunterschrift') for i in (1, 2)], ''

    m = match(rf"Par suite de cession de (?P<transferred_shares>\d+) parts de CHF (?P<nominal>{MONEY}), le gérant-président (?P<name1>{NAME}) est maintenant associé pour (?P<remaining_shares>\d+) parts de CHF (?P=nominal), et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<country2>[A-Z]{{3}}), est nouvel associé pour (?P=transferred_shares) parts de CHF (?P=nominal) et n'exerce pas la signature sociale")
    if m:
        return [event('share_transfer_manager_and_unsigned_associate', m, 'ownership_changed', currency='CHF'), person('share_transfer_manager_and_unsigned_associate', m, '2', role='Gesellschafter', signing='ohne Zeichnungsberechtigung')], ''

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat der (?P<court>Handelsgerichtspräsident des Kantons [^,;]+?) die Genossenschaft aufgelöst und ihre Liquidation nach den statutarischen und gesetzlichen Bestimmungen \(Art\. (?P<article>913 OR)\) angeordnet', 'de')
    if m:
        return [event('cooperative_court_dissolution', m, dissolved=True, liquidation_ordered=True)], ''

    m = match(rf"L'associé-gérant (?P<name1>{NAME}), qui est nommé président, cède (?P<transferred_shares>\d+) de ses (?P<previous_shares>\d+) parts de CHF (?P<nominal>{MONEY}) à (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), nouvelle associée avec (?P=transferred_shares) parts de CHF (?P=nominal), gérante (?P=name1) reste titulaire de (?P<remaining_shares>\d+) parts de CHF (?P=nominal)")
    if m and int(m['previous_shares']) == int(m['transferred_shares']) + int(m['remaining_shares']):
        supporting = f"gérante avec signature individuelle. {m['name1']} reste titulaire de {m['remaining_shares']} parts de CHF {m['nominal']}."
        if supporting in source_text:
            return [event('manager_share_transfer_president_appointed', m, 'ownership_changed', currency='CHF'), person('manager_share_transfer_president_appointed', m, '1', role='Gesellschafter, Geschäftsführer, Präsident'), person('manager_share_transfer_president_appointed', m, '2', role='Gesellschafterin, Geschäftsführerin', signing='Einzelunterschrift')], ''

    m = match(rf'Mit Urteil vom (?P<decision_date>{DATE}) hat das (?P<court>Handelsgericht des Kantons {NAME}) die Anweisung erteilt, (?P<name>{NAME}) als einzelzeichnungsberechtigte Sachwalterin im Handelsregister einzutragen\. \[bisher: Mit superprovisorischen Verfügung vom (?P<previous_decision_date>{DATE}) hat das (?P=court) die Anweisung erteilt, (?P=name) als einzelzeichnungsberechtigte Sachwalterin im Handelsregister einzutragen\.\]', 'de')
    if m:
        return [person('court_administrator_order_replaced', m, role='Sachwalterin', signing='Einzelunterschrift')], ''

    m = match(rf'Signature collective à deux de (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]{{3}}), secrétaire générale et membre de la direction')
    if m:
        return [person('general_secretary_management_collective_signing', m, role='Generalsekretärin, Mitglied der Geschäftsleitung', signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf"Les administrateurs (?P<name1>{NAME}), jusqu'ici secrétaire, nommé président, (?P<name2>{NAME}), jusqu'ici président, maintenant vice-président, continuent à signer collectivement à deux\. L'administratrice (?P<name3>{NAME}), jusqu'ici vice-présidente, maintenant secrétaire, continue à signer individuellement\. (?P<name4>{NAME}), d'(?P<origin4>{NAME}), au (?P<place4>{NAME}), (?P<country4>[A-Z]{{3}}), est membre du conseil d'administration")
    if m and leftover + ' avec signature collective à deux.' in source_text:
        return [person('administration_roles_and_signing_retained', m, str(i), role=role, signing='Einzelunterschrift' if i == 3 else 'Kollektivunterschrift zu zweien') for i, role in enumerate(['Präsident', 'Vizepräsident', 'Sekretärin', 'Verwaltungsrat'], 1)], ''

    m = match(rf"Augmentation ordinaire du capital-participations de CHF (?P<previous_capital>{MONEY}) à CHF (?P<capital>{MONEY}), à savoir de CHF (?P<increase>{MONEY}), entièrement libéré, par l'émission de (?P<issued>\d+) bons de CHF (?P<nominal>{MONEY}), nominatifs, liés selon statuts\. Capital-participation: CHF (?P=capital), entièrement libéré, divisé en (?P<count>\d+) bons de CHF (?P=nominal), nominatifs, liés selon statuts")
    if m:
        amount = lambda key: Decimal(m[key].replace("'", ''))
        if amount('capital') == amount('count') * amount('nominal') and amount('increase') == amount('capital') - amount('previous_capital') == amount('issued') * amount('nominal'):
            return [event('ordinary_participation_capital_increase', m, 'capital_changed', currency='CHF', fully_paid=True, restricted_transfer=True)], ''

    m = match(rf"Nouveaux membres du comité sans signature: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}) \((?P<country1>{NAME})\), et (?P<name2>{NAME}), d'(?P<origin2>{NAME}), à (?P<place2>{NAME}) \((?P<country2>{NAME})\)")
    if m:
        return [person('committee_members_without_signing', m, str(i), role='Vorstandsmitglied', signing='ohne Zeichnungsberechtigung') for i in (1, 2)], ''

    return [], leftover
