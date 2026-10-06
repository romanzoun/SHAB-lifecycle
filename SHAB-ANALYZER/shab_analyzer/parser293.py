from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser293_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete sample-backed clauses, retaining unsupported residue."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(rule, **payload):
        return _event(*context, 'organization_changed', rule, payload)

    def person(rule, name, **payload):
        return _person_event(*context, 'officer_changed', rule, name, **payload)

    def number(value):
        return Decimal(value.replace("'", ''))

    m = match(r'Nouvelles traductions du nom: \((?P<translation1>[^()]+)\) \((?P<translation2>[^()]+)\) \((?P<translation3>[^()]+)\)')
    if m:
        return [event('fr.text.three_name_translations.v1', action='company_translations_changed', translations=[m[f'translation{i}'] for i in (1, 2, 3)])], ''

    m = match(rf'Rectificatif: la raison de commerce ayant été radiée par erreur, elle est réinscrite à la demande du titulaire comme ci devant \(FOSC (?P<notice_date>{DATE}), p\. (?P<reference>\d+/\d+)\)')
    if m:
        return [event('fr.text.erroneous_deletion_owner_reinstatement.v1', action='reinstated', at_owner_request=True, **m.groupdict())], ''

    m = match(rf'Genehmigte Kapitalerhöhung gestützt auf den Gewährungsbeschluss vom (?P<decision_date>{DATE})', 'de')
    if m:
        return [event('de.text.authorized_capital_grant_resolution.v1', action='authorized_capital_increase', **m.groupdict())], ''

    # Both transfers must be recognized before consuming this compound clause.
    split = rf'Abspaltung: Die Gesellschaft überträgt die "(?P<unit>[^"\n]+)" gemäss Spaltungsvertrag vom (?P<contract_date>{DATE}) mit Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) auf die "(?P<recipient>[^"\n]+)" \((?P<recipient_uid>{UID})\), in (?P<place>{NAME})\. Das Aktienkapital der Gesellschaft wird nicht herabgesetzt'
    if language == 'de':
        parts = leftover.rstrip('.').split('. Abspaltung: ')
        if len(parts) == 2:
            matches = [re.fullmatch(split, part if i == 0 else 'Abspaltung: ' + part) for i, part in enumerate(parts)]
            if all(matches):
                try:
                    for m in matches:
                        datetime.strptime(m['contract_date'], '%d.%m.%Y')
                    valid = all(number(m['assets']) > 0 and 0 <= number(m['liabilities']) <= number(m['assets']) for m in matches)
                except ValueError:
                    valid = False
                if valid:
                    return [event('de.text.two_spin_offs_capital_unchanged.v1', action='spin_off', currency='CHF', capital_reduced=False, **m.groupdict()) for m in matches], ''

    m = match(rf'Succursale radiée: (?P<place>{NAME}) \((?P<branch_uid>{UID})\) \(FOSC (?P<notice_date>{DATE}), Id\. (?P<notice_id>\d+)\)')
    if m:
        return [event('fr.text.branch_deleted_notice_reference.v1', action='branch_deleted', **m.groupdict())], ''

    m = match(rf'Vermögensübertragung: Der Verein überträgt gemäss Vertrag vom (?P<first_day>\d{{2}}\.\d{{2}}\.)/(?P<contract_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Fremdkapital von CHF (?P<liabilities>{MONEY}) auf das (?P<recipient>[^();]+) \((?P<recipient_uid>{UID})\), in (?P<place>{NAME}), eine selbständige Stiftung des öffentlichen Rechts\. Gegenleistung: keine', 'de')
    if m:
        first_date = m['first_day'] + m['contract_date'][-4:]
        try:
            valid = datetime.strptime(first_date, '%d.%m.%Y') <= datetime.strptime(m['contract_date'], '%d.%m.%Y')
        except ValueError:
            valid = False
        if valid and number(m['assets']) > 0 and 0 <= number(m['liabilities']) <= number(m['assets']):
            return [event('de.text.association_assets_public_foundation.v1', action='asset_transfer', currency='CHF', consideration='none', recipient_legal_form='selbständige Stiftung des öffentlichen Rechts', first_date=first_date, **m.groupdict())], ''

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\) est complétée dans ce sens: (?P<name>{NAME}), procuration collective à deux, selon art\. (?P<article>459 al\. 2 CO)")
    if m:
        fields = m.groupdict()
        name = fields.pop('name')
        return [person('fr.persons.procuration_article_entry_completed.v1', name, signing='Kollektivprokura zu zweien', extra=fields)], ''

    m = match(rf"L'associé-gérant (?P<transferor>{NAME}) détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<transferred>{COUNT}) parts de CHF (?P=nominal) à (?P<recipient>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}, [A-Z]{{3}}), nouvelle associée pour (?P=transferred) parts de CHF (?P=nominal) sans signature sociale")
    if m and all(number(m[key]) > 0 for key in ('remaining', 'nominal', 'transferred')):
        rule = 'fr.persons.share_transfer_foreign_associate.v1'
        return [event(rule, action='share_transfer', currency='CHF', **m.groupdict()), person(rule, m['transferor'], role='associé-gérant', extra={'shares': m['remaining'], 'nominal': m['nominal']}), person(rule, m['recipient'], role='associée', place=m['place'], signing='ohne Zeichnungsberechtigung', extra={'origin': m['origin'], 'shares': m['transferred'], 'nominal': m['nominal']})], ''

    m = match(r'Die Vorzugsaktien gewähren Vorrechte bezüglich Dividendenausschüttung gemäss näherer Umschreibung in den Statuten', 'de')
    if m:
        return [event('de.text.preferred_shares_dividend_rights.v1', action='preferred_share_rights', rights='Dividendenausschüttung')], ''

    m = match(rf"Selon décision de Département fédéral de l'intérieur du (?P<decision_date>{DATE}) la mention relative à la renonciation au contrôle restreint est radiée")
    if m:
        return [event('fr.text.federal_department_audit_waiver_removed.v1', action='audit_waiver_removed', authority="Département fédéral de l'intérieur", **m.groupdict())], ''

    m = match(r"La société est dissoute suite à l'expiration de la durée prévue par le contrat de société")
    if m:
        return [event('fr.text.dissolution_contract_term_expired.v1', action='dissolved', reason='contract_term_expired')], ''

    m = match(rf'\[gestrichen: Mit Beschluss des Verwaltungsrates vom (?P<board_date>{DATE}) wird die Statutenbestimmung über die mit Ermächtigungsbeschluss vom (?P<authorization_date>{DATE}) beschlossene genehmigte Kapitalerhöhung geändert\.\]\. \. \[gestrichen: Mit Beschluss der Generalversammlung vom (?P<assembly_date>{DATE}) wird die mit Gewährungsbeschluss vom (?P<grant_date>{DATE}) beschlossene bedingte Kapitalerhöhung geändert\.\]\. \[Streichung der Statutenbestimmung über die bedingte Kapitalerhöhung infolge Erlöschen der Optionsrechte\.\]', 'de')
    if m and datetime.strptime(m['authorization_date'], '%d.%m.%Y') <= datetime.strptime(m['board_date'], '%d.%m.%Y') and datetime.strptime(m['grant_date'], '%d.%m.%Y') <= datetime.strptime(m['assembly_date'], '%d.%m.%Y'):
        return [event('de.text.capital_clauses_removed_options_expired.v1', action='capital_clauses_removed', conditional_reason='option_rights_expired', **m.groupdict())], ''

    return [], leftover
