from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY
from .parser409 import NAME
from . import parser58, parser107, parser132, parser165, parser200, parser217

# Historical expressions retain ownership, including when called in isolation.
_LEGACY = tuple(p for module in (parser58, parser107, parser132, parser165,
                                 parser200, parser217)
                for p in vars(module).values() if isinstance(p, re.Pattern))


def extract_parser431_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume new complete clauses; preserve historical rule ownership."""
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

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1',
                             name, role=role, signing=signing, place=place,
                             extra={'action': action, **m.groupdict(), **extra})

    m = match(rf'Das (?P<court>{NAME}) hat mit Entscheid vom (?P<decision_date>{DATE}) die Wiedereintragung der am (?P<deletion_date>{DATE}) gelöschten Gesellschaft in das Handelsregister angeordnet, (?P<name>{NAME}), von (?P<origin>{NAME}), in (?P<place>{NAME}), als Liquidator eingesetzt und folgende Adresse als Liquidationsadresse bestimmt: (?P<liquidation_address>c/o [^;\n]+?, [^;\n]+?, [^;\n]+? \d+[a-z]?, \d{{4}} {NAME})', 'de')
    if m:
        action = 'reinstatement_liquidator_liquidation_address'
        return [event(action, m, reinstated=True), person(action, m, m['name'], 'Liquidator', place=m['place'])], ''

    m = match(rf'Le membre du conseil de fondation (?P<name>{NAME}) signe maintenant collectivement à deux')
    if m:
        return [person('foundation_member_now_collective_signing', m, m['name'], 'membre du conseil de fondation', 'Kollektivunterschrift zu zweien')], ''

    m = match(rf'Mit Entscheid des Konkursrichters des (?P<court>{NAME}) vom (?P<decision_date>{DATE}) ist das Konkursverfahren geschlossen worden', 'de')
    if m:
        return [event('bankruptcy_closed_by_decision', m, 'status_changed', bankruptcy_closed=True)], ''

    m = match(rf'(?P<seller>{NAME}) détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<count>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé-gérant pour (?P=count) parts de CHF (?P=nominal)')
    if m:
        return [event('share_transfer_new_associate_manager', m, 'ownership_changed', currency='CHF'), person('new_associate_manager_after_transfer', m, m['buyer'], 'associé-gérant', place=m['place'])], ''

    m = match(rf"(?P<name1>{NAME}), président, et (?P<name2>{NAME}), secrétaire, membres du conseil d'administration et directeurs, signent désormais individuellement")
    if m:
        return [person('board_members_and_directors_individual_signing', m, m[f'name{i}'], role, 'Einzelunterschrift') for i, role in ((1, "président, membre du conseil d'administration et directeur"), (2, "secrétaire, membre du conseil d'administration et directeur"))], ''

    m = match(r"Statuti modificati: \[(?P<statutes_regulation>È previsto unicamente un regolamento dell'Istituto di previdenza del Cantone Ticino che regola questioni organizzative\.)\]\. \[Radiate: (?P<previous_statutes>[\d., ]+)\]\. Nuovi privilegi statutari: \[(?P<capital_note>L'istituti di diritto pubblico non dispone di un capitale di dotazione la seguente indicazione è radiata\.)\] \[radiati: Capitale: (?P<previous_capital>[^\[\]\n]+)\]\. Costituto dal Gran Consiglio della Repubblica e Cantone Ticino mediante l'adozione della (?P<founding_law>Legge sulla Cassa pensioni dei dipendenti dello Stato del " + DATE + r")\. \[finora: Base legale: (?P<previous_legal_basis>[^\[\]\n]+)\]\. Base legale: (?P<legal_basis>Legge sull'Istituto di previdenza del Cantone Ticino del " + DATE + r" \(RL 174\.100\))\. \[finora: Base legale: (?P=previous_legal_basis)\]\. Organizzazione: (?P<organization>organo supremo dell'Istituto di previdenza composto da (?P<members>\d+) membri, (?P<insured_representatives>\d+) dei quali rappresentanti degli assicurati e (?P<employer_representatives>\d+) dei datori di lavoro, il quale definisce l'organizzazione dell'Istituto\.) \[finora: Organizzazione: (?P<previous_organization>organo supremo di \d+ membri)\]", 'it')
    if m:
        return [event('public_pension_institution_statutes_legal_basis_organization', m)], ''

    m = match(r'\((?P<german_name>[^()\n]+ in Liquidation)\) \((?P<english_name>[^()\n]+ in liquidation)\)')
    if m:
        return [event('two_liquidation_name_translations', m)], ''

    m = match(rf'Mediante decisione della (?P<authority>Pretura di {NAME}) del (?P<decision_date>{DATE}), la fondazione è stata soppressa\. La cancellazione non può tuttavia essere effettuata mancando il consenso delle autorità fiscali federali e cantonali', 'it')
    if m:
        return [event('foundation_suppressed_tax_consent_pending', m, 'status_changed', suppressed=True, deletion_pending=True)], ''

    m = match(rf"Administration: (?P<president>{NAME}), nommée présidente, et (?P<secretary>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), secrétaire\. Signature individuelle de la présidente ou collective à deux du secrétaire du conseil d'administration")
    if m:
        return [person('president_secretary_asymmetric_signing', m, m['president'], 'présidente', 'Einzelunterschrift'), person('president_secretary_asymmetric_signing', m, m['secretary'], 'secrétaire', 'Kollektivunterschrift zu zweien', m['place'])], ''

    m = match(rf'(?P<name>{NAME}) maintenant domicilié à (?P<place>{NAME}), (?P<country>[A-Z]{{3}})')
    if m:
        return [person('domicile_abroad_without_comma', m, m['name'], place=m['place'])], ''

    m = match(rf"L'associé (?P<seller>{NAME}) détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}), par suite de cession de (?P<count>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]{{3}}), nouvel associé pour (?P=count) parts de CHF (?P=nominal), sans signature sociale")
    if m:
        return [event('associate_transfer_foreign_unsigned_buyer', m, 'ownership_changed', currency='CHF', buyer_signing='ohne Zeichnungsberechtigung')], ''
    return [], text
