from __future__ import annotations

import re
from datetime import datetime

from .parser57 import _FR_BRANCH_REGISTERED
from .parser159 import _FR_BRANCH_REGISTERED_AT
from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, UID


def extract_parser320_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete sample-backed clauses; preserve unsupported input."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang):
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

    def event(rule, m, kind='organization_changed', **extra):
        return _event(*context, kind, rule, {**m.groupdict(), 'action': rule.split('.')[2], **extra})

    def person(rule, m, key, role, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', rule, m[key], role=role, signing=signing, place=m[place] if place else None, extra={**m.groupdict(), **extra})

    merger = rf'Fusion: Übernahme der Aktiven und Passiven des Vereins (?P<absorbed>[^()]+) \((?P<absorbed_uid>{UID})\), in (?P<place>{NAME}), gemäss Fusionsvertrag vom (?P<agreement_date>{DATE}) und Bilanz per (?P<balance_date>{DATE})\. Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) gehen auf den übernehmenden Verein über\. Die Mitglieder des übertragenden Vereins werden zu Mitgliedern des übernehmenden Vereins'
    parts = leftover.split('. Fusion: ')
    if language == 'de' and len(parts) == 2:
        events = []
        for i, part in enumerate(parts):
            original = leftover
            leftover = part if i == 0 else 'Fusion: ' + part
            m = match(merger, 'de')
            leftover = original
            if not m:
                break
            events.append(event('de.text.two_association_mergers.v1', m, currency='CHF', members_transferred=True))
        if len(events) == 2:
            return events, ''

    m = match(rf"Radiation de la mention de l'existence d'une succursale à (?P<place1>[^()]+ \([A-Z]{{2}}\)) \((?P<branch_uid1>{UID})\) et au (?P<place2>[^()]+) \((?P<branch_uid2>{UID})\)", 'fr')
    if m:
        return [event('fr.text.two_branch_mentions_removed.v1', m, mention_removed=True)], ''

    m = match(rf"Fusione: ripresa di attivi e passivi di (?P<absorbed>[^,]+), in (?P<place>{NAME}) \((?P<absorbed_uid>{UID})\), secondo il contratto di fusione del (?P<agreement_date>{DATE}) e bilancio al (?P<balance_date>{DATE}), che presenta attivi per CHF (?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY})\. Conformemente all'attestazione di un perito revisore abilitato, la società assuntrice dispone di fondi propri liberamente disponibili equivalenti almeno all'ammontare dello scoperto\. La società assuntrice detiene tutte le azioni della società trasferente, per cui la fusione avviene senza aumento del capitale e senza attribuzione di azioni", 'it')
    if m:
        return [event('it.text.subsidiary_merger_free_equity.v1', m, currency='CHF', free_equity_confirmed=True, capital_increase=False, share_allocation=False)], ''

    m = match(rf'Trasferimento di patrimonio: secondo contratto del (?P<agreement_date>{DATE}), la società ha trasferito attivi per CHF (?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY}) alla (?P<recipient>[^,]+), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Controprestazione: nessuna', 'it')
    if m:
        return [event('it.text.asset_transfer_without_consideration.v1', m, 'ownership_changed', currency='CHF', consideration_none=True)], ''

    m = match(rf"Rectification de l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\): La succursale ayant été radiée par erreur, elle est réinscrite", 'fr')
    if m:
        return [event('fr.text.branch_erroneous_deletion_reinstated.v1', m, 'status_changed', reinstated=True)], ''

    m = match(rf"L'inscription (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que le numéro correct d'identification est le (?P<corrected_uid>{UID})", 'fr')
    if m:
        return [event('fr.text.uid_corrected.v1', m)], ''

    m = match(rf'Transfert de patrimoine: Selon contrat du (?P<agreement_date>{DATE}), la société a transféré des actifs pour CHF (?P<assets>{MONEY}) et des passifs envers les tiers pour CHF (?P<liabilities>{MONEY}) à la société "(?P<recipient>[^"\n]+)", à (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Contre-prestation: CHF (?P<consideration>{MONEY})', 'fr')
    if m:
        return [event('fr.text.asset_transfer_cash_consideration.v1', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf"Par suite de cession de (?P<transferred>\d+) parts de CHF (?P<nominal>{MONEY}), (?P<seller>{NAME}) est maintenant associé pour (?P<remaining>\d+) parts de CHF (?P=nominal), et (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]{{3}}), est nouvel associé pour (?P<buyer_count>\d+) parts de CHF (?P=nominal)\. Signature collective à deux conférée à l'associé (?P=buyer)", 'fr')
    if m:
        if int(m['transferred']) != int(m['buyer_count']):
            return [], leftover
        rule = 'fr.text.share_transfer_new_associate_joint_signing.v1'
        return [event(rule, m, 'ownership_changed', currency='CHF'), person(rule, m, 'buyer', 'Gesellschafter', 'Kollektivunterschrift zu zweien', 'place')], ''

    m = match(rf'Inscription de la succursale de (?P<place>[^()]+) \((?P<branch_uid>{UID})\) au registre du commerce du (?P<register>[^()]+) \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\)', 'fr')
    if m:
        if _FR_BRANCH_REGISTERED.search(leftover) or _FR_BRANCH_REGISTERED_AT.search(leftover):
            return [], leftover
        payload = {
            'action': 'registered',
            'branch_uid': m['branch_uid'],
            'place': m['place'].strip(),
            'register_canton': m['register'].strip(),
            'source_notice_date': datetime.strptime(m['notice_date'], '%d.%m.%Y').date().isoformat(),
            'source_notice_id': m['notice_id'],
        }
        return [_event(*context, 'branch_changed', 'fr.text.branch_registration_notice.v1', payload)], ''

    m = match(rf'Les nom et prénom exacts de la gérante sont (?P<name>[^()]+) \(et non (?P<previous_name>[^()]+) comme publié\)', 'fr')
    if m:
        return [person('fr.text.manager_full_name_corrected.v1', m, 'name', 'Geschäftsführerin')], ''

    m = match(rf'Nouveaux statuts (?P<statutes_date>{DATE})', 'fr')
    if m:
        return [event('fr.text.new_statutes_date.v1', m)], ''

    m = match(rf"(?P<name1>{NAME}), jusqu'ici vice-président, nommé président, et (?P<name2>{NAME}), jusqu'ici président, membres du conseil d'administration, continuent de signer collectivement à deux", 'fr')
    if m:
        rule = 'fr.text.board_chair_and_former_chair_joint_signing.v1'
        return [person(rule, m, 'name1', 'Präsident des Verwaltungsrates', 'Kollektivunterschrift zu zweien', previous_role='Vizepräsident des Verwaltungsrates'), person(rule, m, 'name2', 'Mitglied des Verwaltungsrates', 'Kollektivunterschrift zu zweien', previous_role='Präsident des Verwaltungsrates')], ''

    return [], leftover
