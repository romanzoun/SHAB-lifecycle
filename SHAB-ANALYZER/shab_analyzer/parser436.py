from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser409 import NAME
from . import parser55, parser60

# Historical search rules own partially consumed clauses as well.
_LEGACY = (parser55._FR_STANDALONE_GROUP_SIGNING,
           parser60._FR_SHARE_TRANSFER_RESTRICTION,
           parser60._FR_BOARD_MEMBERS_SEPARATE_ORIGINS)


def extract_parser436_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Add only complete evidenced residual variants, preserving old events."""
    leftover = text.strip()
    if any(pattern.search(leftover) for pattern in _LEGACY):
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

    def person(action, m, role, signing=None):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1',
                             m['name'], role=role, signing=signing,
                             place=m.groupdict().get('place'),
                             extra={'action': action, **m.groupdict()})

    m = match(rf'La liquidazione è terminata\. La cancellazione anticipata con conferma di un perito revisore abilitato del (?P<confirmation_date>{DATE}) non può ancora essere effettuata mancando il consenso delle autorità fiscali federali', 'it')
    if m:
        return [event('liquidation_finished_early_deletion_tax_consent_pending', m, 'status_changed', liquidation_completed=True, early_deletion_pending=True, federal_tax_consent_pending=True)], ''

    m = match(rf"Selon jugement du (?P<court>Tribunal de première instance) du (?P<decision_date>{DATE}), octroi d'un sursis concordataire définitif jusqu'au (?P<end_date>{DATE})")
    if m:
        return [event('definitive_composition_moratorium_granted_without_commissioner', m, 'status_changed', moratorium_granted=True, moratorium_type='définitif')], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(publication FOSC du (?P<notice_date>{DATE}) page (?P<notice_reference>\d+/\d+)\) est complétée en ce sens que l'associé (?P<name>{NAME}) est gérant")
    if m:
        return [person('associate_manager_role_entry_completed', m, 'gérant')], ''

    m = match(rf"Par jugement du (?P<decision_date>{DATE}), le président du (?P<court>Tribunal de l'arrondissement de {NAME}) a prononcé la réouverture de la faillite\. Par conséquent, la société est réinscrite d'office")
    if m:
        return [event('bankruptcy_reopened_official_reinstatement', m, 'status_changed', bankruptcy_reopened=True, reinstated=True)], ''

    m = match(rf'Nouveau membre du conseil de fondation : (?P<name>{NAME}), de et à (?P<place>{NAME}), trésorière')
    if m:
        # The signing clause was consumed upstream; require its original evidence.
        evidence = f"Nouveau membre du conseil de fondation avec signature collective à deux: {m['name']}, de et à {m['place']}, trésorière."
        signing = 'Kollektivunterschrift zu zweien' if evidence in source_text else None
        return [person('foundation_treasurer_appointed', m, 'trésorière', signing)], ''

    m = match(rf"conformément à l'article (?P<legal_basis>821a CO)\. par (?P<name>{NAME}) \((?P<liquidator_uid>{UID})\), à (?P<place>{NAME}), nommée liquidatrice")
    if m:
        return [person('corporate_liquidator_appointed_article_821a', m, 'Liquidator')], ''

    # Keep the malformed source UID verbatim as text; never repair it or emit it
    # as a normalized identifier. The second transfer has a regular UID.
    m = match(rf'''reprise des actifs et passifs de "(?P<absorbed_name1>[^"\n]+)" \((?P<absorbed_uid_text1>CHE-\d{{3}}\.\d{{4}}\.\d{{3}})\), à (?P<place1>{NAME}), selon contrat de fusion du (?P<agreement_date1>{DATE}) et bilan intermédiaire au (?P<balance_date1>{DATE}), présentant des actifs de CHF (?P<assets1>{MONEY}), des passifs envers les tiers de CHF (?P<liabilities1>{MONEY}), soit un excédent de passifs de CHF (?P<deficit>{MONEY})\. Conformément aux attestations d'un expert-réviseur agréé, la société reprenante dispose de fonds propres librement disponibles équivalent au moins au montant du découvert, et des créances ont été postposées d'un montant au moins équivalent au surendettement\. Reprise des actifs et passifs de "(?P<absorbed_name2>[^"\n]+)" \((?P<absorbed_uid2>{UID})\), à (?P<place2>{NAME}), selon contrat de fusion du (?P<agreement_date2>{DATE}) et bilan intermédiaire au (?P<balance_date2>{DATE}), présentant des actifs de CHF (?P<assets2>{MONEY}) et des passifs envers les tiers de CHF (?P<liabilities2>{MONEY}), soit un actif net de CHF (?P<net_assets>{MONEY})\. La société reprenante détenant l'ensemble des actions des sociétés transférantes, la fusion ne donne pas lieu à une augmentation du capital, ni à une attribution d'actions''')
    if m:
        amount = lambda key: Decimal(m[key].replace("'", ''))
        if amount('liabilities1') - amount('assets1') != amount('deficit') or amount('assets2') - amount('liabilities2') != amount('net_assets'):
            return [], text
        return [event('two_subsidiaries_merger_deficit_subordination_source_uid_typo', m, currency='CHF', capital_increase=False, share_allocation=False)], ''

    return [], text
