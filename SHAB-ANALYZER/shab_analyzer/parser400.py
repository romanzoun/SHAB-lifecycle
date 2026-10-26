from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, DATE, UID
from . import parser56, parser98, parser101, parser112, parser174, parser384

NAME = r'[^,;.\[\]\n]+?'
_LEGACY = tuple(p for module in (parser56, parser98, parser101, parser112, parser174, parser384)
                for p in vars(module).values() if isinstance(p, re.Pattern))


def extract_parser400_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Only complete residual variants; preserve all upstream events and payloads."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', source_pattern=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m and source_pattern:
            source = re.search(r'(?<!\S)(?=\S)' + source_pattern + r'\.(?:\s|$)', source_text)
            if not source or any(source.groupdict().get(k) != v for k, v in m.groupdict().items()):
                return None
            m = source
        if m:
            try:
                for date in re.findall(DATE, m[0]):
                    datetime.strptime(date, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, kind, **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name=None, role=None, signing=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name or m['name'], role=role, signing=signing, place=(None if name is not None and name == m.groupdict().get('seller') else m.groupdict().get('place')), extra={'action': action, **m.groupdict(), **({'place': None} if name is not None and name == m.groupdict().get('seller') else {}), **extra})

    m = match(rf'La réinscription de la société a été ordonnée par décision de la (?P<authority>Justice de Paix du District de {NAME}) du (?P<decision_date>{DATE})\. Les faits inscrits au moment de la radiation demeurent valables')
    if m:
        return [event('reinstatement_peace_court_previous_facts_valid', m, 'status_changed')], ''

    m = match(rf'Signature collective à deux pour les affaires de la succursale a été conférée à (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), directrice')
    if m:
        return [person('branch_female_director_joint_signing_granted', m, role='directrice', signing='Kollektivunterschrift zu zweien', signing_scope='affaires de la succursale')], ''

    m = match(rf"L'associé (?P<seller>{NAME}) a cédé (?P<count>{COUNT}) de ses (?P<previous_count>{COUNT}) parts sociales de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]), nouvelle associée\. Gérants: (?P=seller), nommé président, et (?P=buyer)\. Signature individuelle du président ou collective à deux de l'autre gérante")
    if m:
        return [event('associate_transfer_new_female_manager_president', m, 'ownership_changed', currency='CHF'), person('transfer_manager_president_individual', m, m['seller'], role='gérant président', signing='Einzelunterschrift'), person('transfer_female_manager_joint', m, m['buyer'], role='gérante', signing='Kollektivunterschrift zu zweien')], ''

    m = match(r"L'associazione deve essere cancellata d'ufficio conformemente all'art\. (?P<article>155 vORC), in quanto priva di attività economica e di attivi\. La cancellazione non può tuttavia essere effettuata mancando il consenso delle autorità fiscali federali e cantonali", 'it')
    if m:
        return [event('association_deletion_blocked_tax_consent', m, 'status_changed')], ''

    m = match(rf'(?P<seller>{NAME}) détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<count>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer>{NAME}) qui détient désormais (?P<buyer_count>{COUNT}) parts de CHF (?P=nominal)')
    if m:
        return [event('associate_transfer_both_resulting_holdings', m, 'ownership_changed', currency='CHF')], ''

    pattern = rf"par (?P<name>{NAME}), d'(?P<origin>{NAME}), à (?P<place>{NAME}), liquidateur"
    m = match(pattern, source_pattern=r'La liquidation est opérée sous la raison de commerce: [^\n]+? en liquidation ' + pattern + r' avec signature individuelle')
    if m:
        return [person('liquidator_commercial_name_individual', m, role='liquidateur', signing='Einzelunterschrift')], ''

    pattern = rf'Persona iscritta corretta: (?P<name>[^,;]+, [^,;]+), (?P<origin>cittadina italiana), in (?P<place>{NAME}), socia e presidente della gerenza, con firma individuale, con (?P<count>{COUNT}) quote da CHF (?P<nominal>{MONEY})'
    m = match(pattern, 'it', pattern + r' \[no: (?P<previous_name>[^\]]+)\]')
    if m:
        return [person('italian_associate_president_name_corrected', m, role='socia e presidente della gerenza', signing='Einzelunterschrift')], ''

    m = match(rf"L'associé-gérant président (?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<previous_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à l'associé-gérant (?P<buyer>{NAME}), désormais titulaire de (?P<buyer_count>{COUNT}) parts de CHF (?P=nominal)\. (?P=seller) reste titulaire d'une part de CHF (?P=nominal)")
    if m:
        return [event('manager_president_transfer_retains_one_share', m, 'ownership_changed', remaining='1', currency='CHF')], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) und Inventar vom (?P<inventory_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Passiven von CHF (?P<liabilities>{MONEY}) \(Fremdkapital\) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung CHF (?P<consideration>{MONEY})', 'de')
    if m:
        return [event('company_asset_transfer_inventory_postposed_liabilities', m, 'assets_transferred', currency='CHF')], ''

    m = match(r'\[Firmenübersetzung Nachtrag\]', 'de')
    if m:
        return [event('company_translation_supplement_note', m, 'company_name_changed', supplement=True)], ''

    pattern = rf"(?P<name>{NAME}) est nommé membre du conseil d'administration avec le président ou le vice-président; sa procuration est radiée"
    source = rf"(?P<name>{NAME}) est nommé membre du conseil d'administration avec signature collective à deux avec le président ou le vice-président; sa procuration est radiée"
    m = match(pattern, source_pattern=source)
    if m:
        return [person('board_member_joint_president_proxy_revoked', m, role="membre du conseil d'administration", signing='Kollektivunterschrift zu zweien', signing_restriction='avec le président ou le vice-président', previous_signing_revoked=True)], ''

    m = match(rf'Signature collective à deux, avec un administrateur, a été conférée à (?P<name1>{NAME}) et (?P<name2>{NAME}), nommées directrices; leur procuration est radiée')
    if m:
        return [person('two_female_directors_joint_board_member_proxy_revoked', m, m[key], role='directrice', signing='Kollektivunterschrift zu zweien', signing_restriction='avec un administrateur', previous_signing_revoked=True) for key in ('name1', 'name2')], ''
    return [], text
