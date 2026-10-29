from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser409 import NAME
from . import parser51, parser57, parser59, parser80, parser89, parser98, parser100

# Reuse historical patterns: even isolated calls must leave their input intact.
_LEGACY = tuple(p for module in (parser51, parser57, parser59, parser80,
                                 parser89, parser98, parser100)
                for p in vars(module).values() if isinstance(p, re.Pattern))


def extract_parser430_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
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
        return _event(*context, kind, f'{language}.text.{action}.v1',
                      {'action': action, **m.groupdict(), **extra})

    def person(action, m, role, signing, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1',
                             m['name'], role=role, signing=signing,
                             place=m.groupdict().get('place'),
                             extra={'action': action, **m.groupdict(), **extra})

    m = match(rf"Par prononcé rendu le (?P<decision_date>{DATE}), le (?P<court>{NAME}) a accordé à la société une prolongation du sursis concordataire définitif jusqu'au (?P<until_date>{DATE})")
    if m:
        return [event('definitive_moratorium_extended_numeric_dates', m, 'status_changed', extended=True)], ''

    m = match(rf'(?P<name>{NAME}), directeur, continue de signer collectivement à deux, mais désormais sans autre restriction')
    if m:
        return [person('director_continues_signing_unrestricted', m, 'directeur', 'Kollektivunterschrift zu zweien', signing_restriction='sans autre restriction')], ''

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat der (?P<court>Einzelrichter am Kantonsgericht) die provisorische Nachlassstundung infolge Sanierung aufgehoben', 'de')
    if m:
        return [event('provisional_moratorium_lifted_restructuring', m, 'status_changed', lifted=True, reason='Sanierung')], ''

    # CHF transfers retain their historical owners; only the evidenced USD variant.
    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) Aktiven von USD (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von USD (?P<liabilities>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: USD (?P<consideration>{MONEY})', 'de')
    if m:
        return [event('asset_transfer_usd_cash_consideration', m, 'assets_transferred', currency='USD')], ''

    m = match(rf'(?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), nouvel associé avec (?P=count) parts de CHF (?P=nominal)\. (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)')
    if m:
        return [event('share_transfer_new_associate_without_origin', m, 'ownership_changed', currency='CHF')], ''

    m = match(r'Autres adresse: (?P<address>[^\n]+?), (?P<postal_code>\d{4}) (?P<place>[^.;\n]+)')
    if m:
        return [event('additional_address_plural_typo', m, 'address_changed')], ''

    m = match(r'\[Die Gesellschaft hat eine Revisionsstelle eingetragen\. Die Eintragung des Revisionsverzichts erfolgte irrtümlich und wird gestrichen\.\]', 'de')
    if m:
        return [event('erroneous_audit_waiver_deleted', m, corrected=True, audit_waiver_deleted=True, auditor_registered=True)], ''

    m = match(rf"(?P<seller1>{NAME}) et (?P<seller2>{NAME}), associés, ont cédés (?P<each>{COUNT}) de leurs (?P<before>{COUNT}) parts sociales respectives de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée avec (?P<buyer_count>{COUNT}) parts sociales de CHF (?P=nominal), laquelle n'exerce pas la signature sociale\. (?P=seller1) et (?P=seller2) détiennent désormais, chacun, (?P<remaining>{COUNT}) parts sociales de CHF (?P=nominal)")
    if m:
        return [event('two_associates_transfer_respective_shares', m, 'ownership_changed', currency='CHF', buyer_signing='ohne Zeichnungsberechtigung')], ''

    m = match(rf'Mit Entscheid des (?P<court>{NAME}) vom (?P<decision_date>{DATE}) wurde eine definitive Nachlassstundung für die Dauer von (?P<months>{COUNT}) Monaten gewährt\. \[bisher: Mit Entscheid des (?P=court) vom (?P<previous_date>{DATE}) wurde eine provisorische Nachlassstundung für die Dauer von (?P<previous_months>{COUNT}) Monaten gewährt\.\]', 'de')
    if m:
        return [event('definitive_moratorium_replaces_provisional_duration', m, 'status_changed', definitive=True)], ''

    m = match(r'Organe de publication: (?P<publication_organ>Feuille officielle suisse du commerce)')
    if m:
        return [event('publication_organ_full_french_name', m)], ''

    m = match(rf'\[Les statuts originaires datent du (?P<statutes_date>{DATE}) et non du (?P<previous_statutes_date>{DATE})\]')
    if m:
        return [event('original_statutes_date_corrected_brackets', m, corrected=True)], ''

    # The clause specifies signing partners, but does not state a signing mode.
    m = match(rf'Nouveau membre du comité avec la présidente ou la vice-présidente: (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), secrétaire')
    if m:
        return [person('committee_secretary_with_president_or_deputy', m, 'secrétaire', None, signing_restriction='avec la présidente ou la vice-présidente')], ''
    return [], text
