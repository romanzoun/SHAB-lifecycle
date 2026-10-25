from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, DATE
from .parser391 import NAME as LEGACY_ASSET_TRANSFER_NAME
from . import parser54, parser93, parser115, parser151, parser176, parser221

NAME = r'[^,;.\[\]\n]+?'
UID = r'CHE-\d{3}\.\d{3}\.\d{3}'
# Parser 391 defines this expression inline, rather than exporting a constant.
ASSET_TRANSFER_NO_CONSIDERATION_PATTERN = rf'Transfert de patrimoine: Selon contrat du (?P<agreement_date>{DATE}), la société a transféré des actifs pour CHF (?P<assets>{MONEY}) et des passifs envers les tiers pour CHF (?P<liabilities>{MONEY}), soit un actif net de CHF (?P<net_assets>{MONEY}), à la société (?P<recipient>{LEGACY_ASSET_TRANSFER_NAME}) \((?P<recipient_uid>{UID})\), à (?P<place>{LEGACY_ASSET_TRANSFER_NAME})\. Contre-prestation: aucune'
# Predecessor expressions keep ownership, including in isolated calls.
_LEGACY = tuple(p for module in (parser54, parser93, parser115, parser151, parser176, parser221)
                for p in vars(module).values() if isinstance(p, re.Pattern))


def extract_parser395_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    leftover = text.strip()
    if (any(p.fullmatch(leftover) for p in _LEGACY)
            or re.fullmatch(ASSET_TRANSFER_NO_CONSIDERATION_PATTERN + r'\.?', leftover)):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
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
                             extra={'action': action, **m.groupdict(), **extra, 'name': name})

    m = match(rf'Abspaltung: Die Gesellschaft übernimmt von der (?P<transferor>{NAME}) \((?P<transferor_uid>{UID})\), in (?P<place>{NAME}), einen Teil des Vermögens\. Die Gesellschaft übernimmt dabei gemäss Spaltungsvertrag vom (?P<agreement_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY})\. Da die Aktionäre der übertragenden sowie der übernehmenden Gesellschaft identisch sind und somit die mitgliedschaftliche Kontinuität gewährleistet ist, findet weder eine Kapitalerhöhung noch eine Aktienzuteilung statt', 'de')
    if m:
        return [event('spin_off_identical_shareholders_no_capital_increase', m, currency='CHF', capital_increase=False, share_allocation=False)], ''

    if language == 'fr':
        # Unlike parser348's "a été", these clauses describe "est" changes.
        pattern = rf"La commandite de l'associée commanditaire (?P<name>[^()]+) \((?P<uid>{UID})\) est (?P<change>réduite|portée) de CHF (?P<previous_amount>{COUNT})\.- à CHF (?P<amount>{COUNT})\.-"
        matches = [re.fullmatch(pattern, clause) for clause in leftover.rstrip('.').split('. ')]
        if matches and all(matches):
            amount = lambda m, key: Decimal(m[key].replace("'", ''))
            if all(amount(m, 'amount') > 0 and ((amount(m, 'amount') < amount(m, 'previous_amount')) if m['change'] == 'réduite' else (amount(m, 'amount') > amount(m, 'previous_amount'))) for m in matches):
                return [event('corporate_limited_partner_contribution_changed_present', m, currency='CHF') for m in matches], ''

    m = match(rf"L'associée-gérante (?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par (?P<each>{COUNT}) parts de CHF (?P=nominal) chacun aux associés (?P<buyer1>{NAME}), maintenant à (?P<place1>{NAME}), et (?P<buyer2>{NAME}), maintenant à (?P<place2>{NAME}), tous deux désormais titulaires de (?P<holding>{COUNT}) parts de CHF (?P=nominal)\. (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        n = lambda key: int(m[key].replace("'", ''))
        if n('count') == 2 * n('each') and n('previous') - n('count') == n('remaining') and n('holding') >= n('each'):
            return [event('female_manager_transfer_two_existing_associates', m, currency='CHF')], ''
        return [], text

    m = match(rf"Par arrêt du (?P<decision_date>{DATE}), le (?P<court>Tribunal cantonal) a admis l'appel et annulé la décision du (?P<lower_court>Tribunal civil) du (?P<previous_decision_date>{DATE})")
    if m:
        return [event('cantonal_appeal_civil_decision_annulled', m, 'status_changed')], ''

    m = match(rf"L'administratrice (?P<previous_name>{NAME}), laquelle se nomme maintenant (?P<name>{NAME}), est désormais de (?P<origin>{NAME})")
    if m:
        return [person('female_administrator_name_and_origin_changed', m, m['name'], 'administratrice')], ''

    m = match(rf'Administration: (?P<name1>{NAME}), nommé président, et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<country2>[A-Z]{{3}}), avec signature collective à deux')
    if m:
        # Only the second administrator is explicitly granted signing here.
        return [person('administrator_president_appointed_before_new_member', m, m['name1'], 'président'), person('administrator_collective_signing_foreign_residence', m, m['name2'], 'administrateur', 'Kollektivunterschrift zu zweien', m['place2'])], ''

    m = match(rf'Transfert de patrimoine: Selon contrat du (?P<agreement_date>{DATE}), la société a transféré des actifs pour CHF (?P<assets>{MONEY}) et des passifs envers les tiers pour CHF (?P<liabilities>{MONEY}), soit un actif net de CHF (?P<net_assets_raw>{COUNT}\.\d{{3}}\.\d{{2}}), à la société (?P<recipient>{NAME}) \((?P<recipient_uid>{UID})\), à (?P<place>{NAME})\. Contre-prestation: (?P<consideration>aucune)')
    if m:
        # Preserve the published net amount verbatim; do not guess its punctuation.
        return [event('asset_transfer_explicit_net_amount_no_consideration', m, currency='CHF')], ''

    m = match(rf'Gérants: (?P<name1>{NAME}), nommé président, et (?P<name2>{NAME}), de et à (?P<place2>{NAME}), lesquels signent individuellement')
    if m:
        return [person('two_managers_president_individual_signing', m, m['name1'], 'gérant, président', 'Einzelunterschrift'), person('two_managers_president_individual_signing', m, m['name2'], 'gérant', 'Einzelunterschrift', m['place2'], origin=m['place2'])], ''

    m = match(rf'Le nom complet du titulaire est (?P<name>{NAME})')
    if m:
        return [person('holder_full_name_stated', m, m['name'], 'titulaire')], ''

    m = match(rf'\[Mit Verfügung vom (?P<revocation_date>{DATE}) hat die Aufsichtsbehörde die Verfügung vom (?P<exemption_date>{DATE}) betreffend Befreiung von der Revisionsstellenpflicht widerrufen\.\] \[gestrichen: Die Stiftung wurde mit Verfügung der Aufsichtsbehörde vom (?P=exemption_date) von der Pflicht befreit, eine Revisionsstelle zu bezeichnen\.\]', 'de')
    if m:
        return [event('foundation_auditor_exemption_revoked_bracketed', m, auditor_exemption=False)], ''

    m = match(rf'Vermögensübertragung: Das Institut des öffentlichen Rechts überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}), Inventar per (?P<inventory_date>{DATE}) und Beschluss des Verwaltungsrats vom (?P<resolution_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: CHF (?P<consideration>{MONEY})', 'de')
    if m:
        return [event('public_institute_asset_transfer_board_resolution', m, currency='CHF')], ''

    m = match(rf"L'inscription au journal n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name>{NAME}) et non pas \((?P<previous_name>{NAME})\) de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]{{3}}), est membre du conseil d'administration")
    if m:
        return [person('administrator_name_corrected_journal_entry', m, m['name'], "membre du conseil d'administration", place=m['place'], correction=True)], ''
    return [], text
