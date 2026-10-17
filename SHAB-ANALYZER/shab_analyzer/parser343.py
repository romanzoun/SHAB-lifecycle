from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, COUNT


def extract_parser343_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize bounded residual clauses, preserving all earlier parser results."""
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
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **{k: v for k, v in m.groupdict().items() if k not in ('name', 'place')}, **extra})

    m = match(rf'Grenzüberschreitende Fusion nach den Vorschriften des IPRG: Übernahme der Aktiven und Passiven der (?P<absorbed_name>[^()]+?) in (?P<absorbed_place>[^()]+) \((?P<country>[A-Z]{{2}})\) \((?P<foreign_id>FL-\d{{4}}\.\d{{3}}\.\d{{3}}-\d)\), eine Aktiengesellschaft nach dem Recht des Staates (?P<jurisdiction>{NAME}), gemäss Fusionsvertrag vom (?P<agreement_date>{DATE}) und Bilanz per (?P<balance_date>{DATE})\. Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) gehen auf die übernehmende Gesellschaft über\. Da die übernehmende Gesellschaft sämtliche Aktien der übernommenen Gesellschaft hält, findet weder eine Kapitalerhöhung noch eine Aktienzuteilung statt', 'de')
    if m:
        return [event('cross_border_merger_wholly_owned_foreign_company', m, 'ownership_changed', currency='CHF', capital_increase=False, share_allocation=False)], ''

    m = match(rf'Statutendatum neu: (?P<statutes_date>{DATE})', 'de')
    if m:
        # Earlier parsers remove the correction bracket; require it in the source.
        correction = re.search(re.escape(leftover.rstrip('.')) + rf' \[nicht: (?P<previous_statutes_date>{DATE})\]', source_text)
        if correction:
            try:
                datetime.strptime(correction['previous_statutes_date'], '%d.%m.%Y')
            except ValueError:
                return [], leftover
            return [event('statutes_date_corrected', m, previous_statutes_date=correction['previous_statutes_date'])], ''

    m = match(rf'Mit Verfügung des (?P<court>{NAME}) vom (?P<decision_date>{DATE}) wurde der Konkurs widerrufen\. Infolgedessen besteht die Gesellschaft entsprechend den früheren Eintragungen weiter\. \[bisher: Mit Verfügung des (?P<previous_court>{NAME}) vom (?P<previous_decision_date>{DATE}) ist über diese Gesellschaft mit Wirkung ab dem (?P<effective_date>{DATE}), (?P<effective_time>\d{{2}}\.\d{{2}}) Uhr, der Konkurs eröffnet worden\.\]', 'de')
    if m:
        return [event('bankruptcy_revoked_company_continues', m)], ''

    m = match(rf"L'associée-gérante (?P<name>{NAME}), qui est nommée présidente, cède une part de CHF (?P<nominal>{MONEY}) à l'associé (?P<recipient>{NAME}), désormais titulaire de (?P<recipient_count>{COUNT}) parts de CHF (?P<recipient_nominal>{MONEY}), lequel est nommé gérant (?P<remaining_holder>{NAME}) reste titulaire de (?P<remaining_count>{COUNT}) parts de CHF (?P<remaining_nominal>{MONEY})")
    if m and m['name'] == m['remaining_holder']:
        signing_clause = f"lequel est nommé gérant avec signature individuelle. {m['remaining_holder']} reste titulaire"
        signing = 'Einzelunterschrift' if signing_clause in source_text else None
        return [event('share_transfer_manager_president', m, 'ownership_changed', currency='CHF', transferred_count='1'), person('shareholder_manager_president_appointed', m, m['name'], 'Präsident'), person('recipient_manager_appointed', m, m['recipient'], 'Geschäftsführer', signing)], ''

    m = match(rf'Die Einzelrichterin des (?P<court>{NAME}), Abteilung (?P<division>\d+), hat mit Entscheid vom (?P<decision_date>{DATE}) den ordentlichen Nachlassvertrag genehmigt\. Für den Vollzug des Nachlassvertrages wird die eingesetzte Sachwalterin (?P<administrator>[^()]+) \((?P<administrator_uid>CHE-\d{{3}}\.\d{{3}}\.\d{{3}})\), beauftragt\. \[bisher: Mit Entscheid der Einzelrichterin des (?P<previous_court>{NAME}), Abteilung (?P<previous_division>\d+), vom (?P<previous_decision_date>{DATE}) wurde eine Verlängerung der Nachlassstundung von zwei Monaten bis zum (?P<previous_end_date>{DATE}) bewilligt\.\]', 'de')
    if m:
        return [event('composition_agreement_approved_administrator_mandated', m)], ''

    m = match(rf'Mit Urteil vom (?P<decision_date>{DATE}) hat das Nachlassgericht des (?P<court>{NAME}) eine Verlängerung der COVID-19-Stundung von drei Monaten bis (?P<end_date>{DATE}) gewährt', 'de')
    if m:
        return [event('covid19_moratorium_extended', m, duration_months='3')], ''

    m = match(rf'Vollständige Adresse: (?P<address>[^,]+), (?P<postal_code>\d{{4}}) (?P<town>{NAME})\. Eingetragene Personen geändert: (?P<name1>{NAME}), Verwaltungsratsmitglied, Präsident, Kollektivunterschrift zu zweien, neu Verwaltungsratsmitglied, Präsident, Einzelunterschrift, nun von (?P<origin1>{NAME}) \(Gemeindefusion\), in (?P<place1>{NAME}); (?P<previous_name2>{NAME}), korrekterweise (?P<name2>{NAME}), Verwaltungsratsmitglied, Sekretärin, Kollektivunterschrift zu zweien, neu Verwaltungsratsmitglied, Sekretärin, Einzelunterschrift, nun von (?P<origin2>{NAME}) \(Gemeindefusion\), in (?P<place2>{NAME})\. Neu eingetragene Person: (?P<name3>{NAME}), von (?P<origin3>{NAME}), in (?P<place3>{NAME}), Verwaltungsratsmitglied, Vizepräsident, Einzelunterschrift')
    if m:
        return [event('complete_address_and_board_details', m)] + [person('board_details_updated', m, m[f'name{i}'], role, 'Einzelunterschrift', m[f'place{i}'], origin=m[f'origin{i}'], previous_signing='Kollektivunterschrift zu zweien' if i < 3 else None) for i, role in ((1, 'Präsident'), (2, 'Sekretärin'), (3, 'Vizepräsident'))], ''

    m = match(rf"L'associé (?P<name>{NAME}) est nommé gérant et président")
    if m:
        signing = 'Einzelunterschrift' if leftover.rstrip('.') + ' avec signature individuelle' in source_text else None
        return [person('associate_manager_and_president_appointed', m, m['name'], 'Geschäftsführer', signing, additional_role='Präsident')], ''

    m = match(rf"(?P<name1>{NAME}), jusqu'ici secrétaire, nommé vice-président, et (?P<name2>{NAME}), jusqu'ici vice-président, tous deux membres du conseil de fondation, continuent de signer collectivement à deux")
    if m:
        return [person('foundation_member_now_vice_president', m, m['name1'], 'Vizepräsident', 'Kollektivunterschrift zu zweien', previous_role='Sekretär'), person('foundation_member_no_longer_vice_president', m, m['name2'], 'Stiftungsrat', 'Kollektivunterschrift zu zweien', previous_role='Vizepräsident')], ''

    m = match(rf"Par décision du (?P<decision_date>{DATE}), l'assemblée générale a modifié la clause statutaire relative à l'augmentation conditionnelle du capital-participation introduite par décision du (?P<authorization_date>{DATE}); pour les détails, voir les statuts")
    if m:
        return [event('conditional_participation_capital_clause_amended', m, 'capital_changed')], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est complétée en ce sens que l'adresse de liquidation exacte est (?P<street>[^,]+) (?P<house_number>\d+), c/o (?P<care_of>[^,]+), (?P<postal_code>\d{{4}}) (?P<place>{NAME})")
    if m:
        return [event('liquidation_address_completed', m)], ''

    m = match(rf'Nouveaux membres du comité directeur : (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME})')
    if m:
        original = leftover.replace('comité directeur :', 'comité directeur avec signature collective à deux:')
        signing = 'Kollektivunterschrift zu zweien' if original.rstrip('.') in source_text else None
        return [person('executive_committee_member_appointed', m, m[f'name{i}'], 'Vorstand', signing, m[f'place{i}'], origin=m[f'origin{i}']) for i in (1, 2)], ''

    return [], leftover
