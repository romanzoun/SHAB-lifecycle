from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser409 import NAME
from . import parser83, parser133, parser220, parser243

_LEGACY = (parser83._FR_FOUNDATION_MEMBERS_WITHOUT_SIGNATURE_PAIR,
           parser133._FR_ONE_SHARE_TRANSFER_UNSIGNED_BUYER,
           parser220._FR_BRANCH_DELETED,
           parser243._DE_DEFINITIVE_MORATORIUM_EXTENDED_WITH_PREVIOUS)


def extract_parser424_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume only complete, attested residual clauses, retaining legacy ownership."""
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
                for date in re.findall(r'\d{2}[.-]\d{2}[.-]\d{4}', m[0]):
                    datetime.strptime(date.replace('-', '.'), '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name,
                             role=role, signing=signing, place=place,
                             extra={'action': action, **m.groupdict(), **extra})

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat (?P<court>{NAME}) die definitive Nachlassstundung letztmals bis (?P<end_date>{DATE}) verlängert', 'de')
    if m:
        return [event('definitive_moratorium_final_extension_without_history', m, 'status_changed', final_extension=True)], ''

    m = match(rf"Le nom complet de l'associé gérant est (?P<name>{NAME})")
    if m:
        return [person('associate_manager_full_name', m, m['name'], 'associé gérant', corrected=True)], ''

    m = match(rf"(?P<seller>{NAME}) détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession d'une part de CHF (?P=nominal) à (?P<buyer>{NAME}), d'(?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé pour une part de CHF (?P=nominal)")
    if m:
        # Parser 384 owns this clause when collective signing was removed upstream.
        # Require the complete unsigned source clause; no inference from missing context.
        if not source_text.endswith(leftover.rstrip('.') + '.'):
            return [], text
        return [event('single_share_transfer_new_associate_no_signing_statement', m, 'ownership_changed', transferred_count='1', currency='CHF')], ''

    m = match(r'La succursale de (?P<place>[^(),;.\n]+) est radiée')
    if m:
        return [event('branch_deleted_without_canton', m, deleted=True)], ''

    m = match(rf'Nouvelle gérante: (?P<name>{NAME}), de (?P<origin>{NAME}), au (?P<place>{NAME}) à trois')
    if m:
        source_clause = leftover.removesuffix('.').removesuffix(' à trois') + ' avec signature collective à trois.'
        if not source_text.endswith(source_clause):
            return [], text
        return [person('new_manager_collective_signing_three', m, m['name'], 'gérante', 'Kollektivunterschrift zu dreien', m['place'])], ''

    m = match(rf"Rectificatif: l'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}) p\. (?P<notice_ref>\d+/\d+)\) est rectifée en ce sens que (?P<previous_name>{NAME}), dont le prénom exact est (?P<given_name>{NAME}), est à (?P<place>{NAME}) \(et non à (?P<previous_place>{NAME}) comme publié\)")
    if m:
        return [event('given_name_and_residence_corrected_typo', m, 'publication_corrected', corrected=True)], ''

    notice = rf'{COUNT} du {DATE} \(FOSC du \d{{2}}-\d{{2}}-\d{{4}}, p\. \d+/\d+\)'
    m = match(rf'Les inscriptions (?P<notices>{notice}, {notice} et {notice}) sont rectifiées en ce sens que (?P<previous_name>{NAME}) porte en réalité le prénom de (?P<given_name>{NAME})')
    if m:
        return [event('three_notices_given_name_corrected', m, 'publication_corrected', corrected=True)], ''

    m = match(rf"L'associé (?P<seller>{NAME}) a cédé (?P<count>{COUNT}) de ses (?P<before>{COUNT}) parts sociales de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), d'(?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé\. Gérants: (?P=seller), nommé président, et (?P=buyer), lesquels signent individuellement")
    if m:
        return [event('partial_share_transfer_manager_president_pair', m, 'ownership_changed', currency='CHF'),
                person('transfer_manager_president_pair', m, m['seller'], 'gérant et président', 'Einzelunterschrift'),
                person('transfer_manager_president_pair', m, m['buyer'], 'gérant', 'Einzelunterschrift', m['place'])], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name>[^()\n]+?) \((?P<registry_id>\d{{3}} \d{{3}} \d{{3}})\) est domiciliée à (?P<place>{NAME}), (?P<country>[A-Z]{{3}}) \(et non (?P<previous_place>{NAME}), (?P<previous_country>[A-Z]{{3}})\)")
    if m:
        return [event('corporate_domicile_country_corrected', m, 'publication_corrected', corrected=True)], ''

    m = match(rf"L'associé (?!gérant )(?P<name>{NAME}) n'exerce plus la signature sociale")
    if m:
        return [person('associate_signing_revoked', m, m['name'], 'associé', 'ohne Zeichnungsberechtigung', signing_revoked=True)], ''

    m = match(rf'Nouveaux membres du conseil de fondation: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), sans signature')
    if m:
        return [person('foundation_member_pair_trailing_unsigned', m, m['name'+i], 'membre du conseil de fondation', 'ohne Zeichnungsberechtigung', m['place'+i]) for i in ('1', '2')], ''

    m = match(rf'Par suite de fusion de communes, le siège de la succurasale de (?P<previous_place>{NAME}) \((?P<branch_uid>{UID})\) devient (?P<place>{NAME})')
    if m:
        return [event('branch_seat_municipality_merger_typo', m, 'address_changed', municipality_merger=True)], ''
    return [], text
