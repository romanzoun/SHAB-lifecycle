from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, UID


def extract_parser319_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume bounded sample-backed clauses, leaving unsupported input intact."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang, source_pattern=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m:
            return None
        if source_pattern:
            s = re.search(source_pattern + r'\.?$', source_text)
            if not s or any(s[k] != v for k, v in m.groupdict().items()):
                return None
            m = s
        try:
            for k, v in m.groupdict().items():
                if k.endswith('_dash_date'):
                    datetime.strptime(v, '%d-%m-%Y')
                elif k.endswith('_date'):
                    datetime.strptime(v, '%d.%m.%Y')
                elif k == 'time':
                    datetime.strptime(v, '%H.%M')
        except ValueError:
            return None
        return m

    def event(rule, m, kind='organization_changed', **extra):
        return _event(*context, kind, rule, {**m.groupdict(), 'action': rule.split('.')[2], **extra})

    def person(rule, m, key, role=None, signing=None, place=None, kind='officer_changed', **extra):
        return _person_event(*context, kind, rule, m[key], role=role, signing=signing, place=m[place] if place else None, extra={**m.groupdict(), **extra})

    m = match(rf"Rectification: l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\) est rectifiée dans le sens que le domicile correct de (?P<name>{NAME}) est à (?P<place>[^()]+) \(et non pas à (?P<previous_place>[^()]+)\)", 'fr')
    if m:
        return [person('fr.text.person_residence_corrected.v1', m, 'name', place='place')], ''

    m = match(rf"L'inscription No (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que l'administrateur unique (?P<name>{NAME}) signe individuellement \(et non pas collectivement à deux\)", 'fr')
    if m:
        return [person('fr.text.sole_director_signing_corrected.v1', m, 'name', 'Einziges Mitglied des Verwaltungsrates', 'Einzelunterschrift', previous_signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf'Persona iscritta corretta: (?P<surname>{NAME}), (?P<given>{NAME}), da (?P<origin>{NAME}), in (?P<place>{NAME}), membro, direttore generale, con firma collettiva a due', 'it')
    if m:
        rule = 'it.text.board_member_general_director_corrected.v1'
        return [_person_event(*context, 'officer_changed', rule, m['surname'] + ', ' + m['given'], place=m['place'], role='Mitglied des Verwaltungsrates und Generaldirektor', signing='Kollektivunterschrift zu zweien', extra=m.groupdict())], ''

    m = match(rf"Suite à l'ouverture de la faillite de l'établissement principal, sa raison sociale devient: (?P<head_name>[^()]+) \((?P<head_uid>{UID})\)\. Par conséquent, la raison de commerce de la succursale devient: (?P<branch_name>[^.]+)", 'fr')
    if m:
        return [event('fr.text.branch_name_head_office_bankruptcy.v1', m, 'status_changed', head_office_bankrupt=True)], ''

    tail = rf'toutefois pas avec (?P<excluded1>{NAME}), (?P<excluded2>{NAME}) et (?P<excluded3>{NAME}), ni entre elles: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), et (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME})'
    m = match('Nouveaux membres du conseil de fondation avec signature collective à deux, ' + tail, 'fr', 'Nouveaux membres du conseil de fondation avec signature collective à deux, ' + tail)
    if m:
        rule = 'fr.text.foundation_members_excluded_joint_signing.v1'
        return [person(rule, m, f'name{i}', 'Mitglied des Stiftungsrates', 'Kollektivunterschrift zu zweien', f'place{i}', signing_excluded_with=[m[f'excluded{j}'] for j in (1, 2, 3)], signing_between_appointees=False) for i in (1, 2, 3)], ''

    address = r'(?P<address>c/o (?P<care_of>[^,]+), (?P<street>[^,]+), (?P<postal_code>\d{4}) (?P<place>[^.]+))'
    m = match(r'\[biffé: Adresse de liquidation : ' + address, 'fr', r'\[biffé: Adresse de liquidation: (?P<previous_address>[^\]]+)\]\. Adresse de liquidation : ' + address)
    if m:
        return [event('fr.text.liquidation_address_replaced.v1', m)], ''

    transfer = rf"L'associé-gérant, (?P<seller>{NAME}), qui est nommé président, cède (?P<transferred>\d+) de ses (?P<before>\d+) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé avec (?P<buyer_count>\d+) parts de CHF (?P=nominal), gérant"
    ending = rf"(?P=seller) reste titulaire de (?P<remaining>\d+) parts de CHF (?P=nominal)"
    m = match(transfer + r' avec signature individuelle\. ' + ending, 'fr', transfer + r' avec signature individuelle\. ' + ending)
    if m:
        if int(m['before']) != int(m['transferred']) + int(m['remaining']) or m['transferred'] != m['buyer_count']:
            return [], leftover
        rule = 'fr.text.share_transfer_manager_chair_appointed.v1'
        return [event(rule, m, 'ownership_changed', currency='CHF'), person(rule, m, 'seller', 'Vorsitzender der Geschäftsführung'), person(rule, m, 'buyer', 'Geschäftsführer', 'Einzelunterschrift', 'place')], ''

    m = match(rf'Mit Beschluss der Generalversammlung vom (?P<decision_date>{DATE}) wird die Statutenbestimmung über die mit Ermächtigungsbeschluss vom (?P<previous_date>{DATE}) beschlossene genehmigte Kapitalerhöhung gestrichen\. \. Die Generalversammlung hat mit Beschluss vom (?P=decision_date) eine genehmigte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten eingeführt', 'de')
    if m:
        return [event('de.text.authorized_capital_replaced.v1', m, previous_authorization_removed=True, new_authorization_introduced=True)], ''

    m = match(rf'Fusion: Übernahme der Aktiven und Passiven der (?P<absorbed>[^,]+), in (?P<place>{NAME}) \((?P<absorbed_uid_raw>CHE- {UID})\) , gemäss Fusionsvertrag vom (?P<agreement_date>{DATE}) und Bilanz per (?P<balance_date>{DATE})\. Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}), d\.h\. ein Passivenüberschuss von CHF (?P<deficit>{MONEY}), gehen auf die übernehmende Gesellschaft über\. Die übernehmende Gesellschaft verfügt gemäss Bestätigung des zugelassenen Revisionsexperten über frei verwendbares Eigenkapital im Umfang der Unterdeckung und der Überschuldung\. Da die übernehmende Gesellschaft sämtliche Anteile an der übertragenden Gesellschaft hält, findet weder eine Kapitalerhöhung noch eine Aktienzuteilung statt', 'de')
    if m:
        return [event('de.text.subsidiary_merger_deficit_malformed_uid.v1', m, currency='CHF', uid_malformed=True, capital_increase=False, share_allocation=False)], ''

    merger = rf'Fusione: ripresa di attivi e passivi di (?P<absorbed>[^,]+), in (?P<place>{NAME}) \((?P<absorbed_uid>{UID})\), secondo (?:il )?contratto di fusione del (?P<agreement_date>{DATE}) e bilancio al (?P<balance_date>{DATE}), che presenta attivi per CHF (?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY})\. '
    subordinate = r"Conformemente all'attestazione di un perito revisore abilitato, dei crediti per un ammontare almeno equivalente allo scoperto(?: della società assuntrice)? sono stati postergati\. "
    common = "La totalità del capitale azionario delle due società è detenuta dallo stesso azionista, la fusione avviene dunque senza aumento di capitale e senza attribuzione di azioni"
    m = match(merger + subordinate + common, 'it')
    if m:
        return [event('it.text.common_shareholder_merger_subordinated_claims.v1', m, currency='CHF', claims_subordinated=True, capital_increase=False, share_allocation=False)], ''

    subsidiary = r'La società assuntrice detiene tutte le azioni della società trasferente, per cui la fusione avviene senza aumento (?:del capitale|di capitale) e senza attribuzione di azioni'
    parts = leftover.split('. Fusione: ')
    if language == 'it' and len(parts) == 2:
        events = []
        for i, part in enumerate(parts):
            part = part if i == 0 else 'Fusione: ' + part
            # Reuse full-clause and date validation for both notices atomically.
            original = leftover
            leftover = part
            m = match(merger + (subordinate if i else '') + subsidiary, 'it')
            leftover = original
            if not m:
                break
            events.append(event('it.text.two_subsidiary_mergers.v1', m, currency='CHF', claims_subordinated=bool(i), capital_increase=False, share_allocation=False))
        if len(events) == 2:
            return events, ''

    asset = rf'Trasferimento di patrimonio: secondo contratto del (?P<agreement_date>{DATE}), la società ha trasferito attivi per CHF (?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY}) alla (?P<recipient>[^,]+?) , in (?P<place>{NAME}) \((?P<recipient_uid_raw>{UID}(?P<uid_marker>\??))\)\. Controprestazione: nessuna'
    parts = leftover.split('. Trasferimento di patrimonio: ')
    if language == 'it' and len(parts) == 2:
        events = []
        for i, part in enumerate(parts):
            original = leftover
            leftover = part if i == 0 else 'Trasferimento di patrimonio: ' + part
            m = match(asset, 'it')
            leftover = original
            if not m or m['uid_marker'] != ('?' if i else ''):
                break
            events.append(event('it.text.two_asset_transfers_without_consideration.v1', m, currency='CHF', consideration_none=True, uid_malformed=bool(m['uid_marker'])))
        if len(events) == 2:
            return events, ''

    return [], leftover
