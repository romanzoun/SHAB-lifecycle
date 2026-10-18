from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, MONEY, UID

PERSON = r'[^,;.]+?'


def extract_parser357_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Append complete, fixture-backed residual facts after the earlier parsers."""
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

    def event(action, m, **extra):
        return _event(*context, 'organization_changed', f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name=None, role=None, signing=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name or m['name'], place=m.groupdict().get('place'), role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra})

    m = match(rf'Name neu: (?P<new_name>[^.;]+ in Liquidation)\. Mit Entscheiden vom (?P<first_decision_date>{DATE}) und (?P<second_decision_date>{DATE}) hat das (?P<court>[^.;]+) den Verein gemäss Art\. (?P<article>69c ZGB) aufgelöst und seine Liquidation nach den Vorschriften über den Konkurs angeordnet', 'de')
    if m:
        return [event('association_dissolved_by_court_bankruptcy_liquidation', m)], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<page>\d+)\) est rectifiée en ce sens: Parts sociales de CHF (?P<minimum_nominal>{MONEY}) à CHF (?P<maximum_nominal>{MONEY})")
    if m:
        return [event('cooperative_share_nominal_range_corrected', m)], ''

    m = match(rf"Fusione: ripresa di attivi e passivi di (?P<absorbed_name>.+?), in (?P<absorbed_place>{PERSON}) \((?P<absorbed_uid>{UID})\), secondo il contratto di fusione del (?P<agreement_date>{DATE}) e bilancio al (?P<balance_date>{DATE}), che presenta attivi per CHF (?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY})\. Conformemente all'attestazione di un perito revisore abilitato, la società trasferente dispone di fondi propri liberamente disponibili equivalenti almeno all'ammontare dello scoperto e e del sovraindebitamento della società assuntrice\. La società assuntrice detiene tutte le azioni della società trasferente, per cui la fusione avviene senza aumento del capitale e senza attribuzione di azioni", 'it')
    if m:
        return [event('merger_transferor_equity_attestation', m, currency='CHF', capital_increased=False, shares_allocated=False, equity_holder='transferor')], ''

    m = match(rf"Signature collective à deux limitée à l'établissement principal a été conférée à (?P<name1>{PERSON}), (?P<name2>{PERSON}), (?P<name3>{PERSON}) et (?P<name4>{PERSON}), nommés sous-directeurs; leur procuration est radiée")
    if m:
        return [person('subdirector_appointed_procuration_terminated', m, m[f'name{i}'], 'Vizedirektor', 'Kollektivunterschrift zu zweien', signing_restriction="limitée à l'établissement principal", procuration_terminated=True) for i in range(1, 5)], ''

    m = match(rf"Par décision du (?P<decision_date>{DATE}), l'assemblée générale a introduit une clause statutaire relative à une augmentation autorisée du capital-actions\. Pour les détails, voir les statuts")
    if m:
        return [event('authorized_capital_statutory_clause_introduced', m)], ''

    m = match(rf"L'associé (?P<transferor>{PERSON}) a cédé (?P<transferred>\d+) parts de CHF (?P<nominal>{MONEY}) à (?P<name>{PERSON}), du (?P<origin>{PERSON}), à (?P<place>{PERSON}), (?P<country>[A-Z]{{3}}), nouvel associé pour (?P=transferred) parts de CHF (?P=nominal), sans signature sociale; par conséquent, (?P=transferor) est maintenant associé pour (?P<remaining>\d+) parts de CHF (?P=nominal)")
    if m:
        return [event('shares_transferred_new_associate_without_signing', m), person('new_associate_without_signing', m, signing='ohne Zeichnungsberechtigung')], ''

    m = match(r'Zweigniederlassung neu: (?P<place>[^.;]+) \((?P<branch_uid>CHE \d{3}\.\d{3}\.\d{3})\)', 'de')
    if m:
        return [event('branch_added_spaced_uid', m)], ''

    m = match(rf"L'inscription no (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que le nom exact du titulaire est (?P<name>{PERSON}) \(et non pas (?P<previous_name>{PERSON})\)")
    if m:
        return [person('proprietor_name_corrected', m)], ''

    m = match(rf'(?P<name>{PERSON}), de (?P<origin>{PERSON}), à (?P<place>{PERSON})')
    if m and re.search(re.escape(leftover) + rf', {PERSON}, de {PERSON}, à {PERSON}, et {PERSON}, de {PERSON}, à {PERSON}, sont membres du conseil sans signature\.?$', source_text):
        return [person('council_member_without_signing', m, role='Mitglied des Stiftungsrats', signing='ohne Zeichnungsberechtigung')], ''

    m = match(rf'(?P<holder>.+?) \((?P<holder_uid>{UID})\) est désormais titulaire de (?P<count>\d+) parts de CHF (?P<nominal>{MONEY})')
    if m:
        return [event('corporate_associate_holding_changed', m)], ''

    m = match(rf'(?P<name1>{PERSON}) et (?P<name2>{PERSON}), signent désormais collectivement à deux, sans autre restriction')
    if m:
        return [person('collective_signing_restriction_removed', m, m[f'name{i}'], signing='Kollektivunterschrift zu zweien', signing_restriction_removed=True) for i in (1, 2)], ''

    m = match(rf"(?P<name>{PERSON}), jusqu'ici directeur, est maintenant membre du conseil d'administration et continue à signer individuellement")
    if m:
        return [person('director_becomes_board_member_keeps_individual_signing', m, role='Mitglied des Verwaltungsrats', signing='Einzelunterschrift', previous_role='directeur')], ''

    return [], leftover
