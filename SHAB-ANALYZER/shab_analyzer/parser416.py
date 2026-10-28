from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser409 import NAME
from .parser132 import _DE_ASSOCIATION_VOLUNTARY_DELETION
from .parser135 import _FR_FOUNDATION_DISSOLVED_FIVE_LIQUIDATORS
from .parser195 import (
    _FR_AUTHORIZED_CAPITAL_CLAUSE_REPLACED_NUMERIC_DATES,
    extract_parser195_leftovers,
)

_LEGACY = (_DE_ASSOCIATION_VOLUNTARY_DELETION,
           _FR_FOUNDATION_DISSOLVED_FIVE_LIQUIDATORS,
           _FR_AUTHORIZED_CAPITAL_CLAUSE_REPLACED_NUMERIC_DATES)


def extract_parser416_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Sample-backed, complete residual variants; preserve existing rule inputs."""
    leftover = text.strip()
    if any(pattern.fullmatch(leftover) for pattern in _LEGACY):
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

    def person(action, m, name, role, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name,
                             role=role, signing=signing, place=place,
                             extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    def number(m, key):
        return int(m[key].replace("'", ''))

    m = match(rf'(?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de et à (?P<place>{NAME}), nouvelle associée avec (?P=count) parts de CHF (?P=nominal), gérante (?P=seller), qui reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal), est nommé président')
    if m:
        if number(m, 'before') != number(m, 'count') + number(m, 'remaining'):
            return [], text
        return [event('share_transfer_new_manager_seller_president', m, 'ownership_changed', currency='CHF'),
                person('new_female_manager_share_transfer', m, m['buyer'], 'associée-gérante', place=m['place']),
                person('share_transfer_seller_named_president', m, m['seller'], 'président')], ''

    m = match(rf'(?P<seller>{NAME}), maintenant domicilié à (?P<seller_place>{NAME}), désormais président, détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<count>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé-gérant pour (?P=count) parts de CHF (?P=nominal)')
    if m:
        return [event('president_residence_share_transfer_new_manager', m, 'ownership_changed', currency='CHF'),
                person('share_transfer_president_residence_changed', m, m['seller'], 'président', place=m['seller_place']),
                person('share_transfer_new_associate_manager', m, m['buyer'], 'associé-gérant', place=m['place'])], ''

    m = match(rf"Selon décision de l'(?P<authority>Autorité cantonale de surveillance des fondations et des institutions de prévoyance) du (?P<decision_date>{DATE}), la fondation est dissoute\. Liquidateurs: les membres du conseil (?P<name1>{NAME}), président et (?P<name2>{NAME}), trésorier, lesquels continuent à signer individuellement")
    if m:
        return [event('foundation_dissolved_two_council_liquidators', m, 'status_changed'),
                *[person('foundation_two_council_liquidators', m, m[f'name{i}'], 'liquidateur', 'Einzelunterschrift', council_role=role) for i, role in ((1, 'président'), (2, 'trésorier'))]], ''

    m = match(rf"\[radiati: Conferimento in natura e assunzione di beni: sulla base del contratto del (?P<agreement_date>{DATE}), la società assume (?P<acquired_count1>{COUNT}) azioni al portatore da CHF (?P<acquired_nominal1>{MONEY}) della (?P<company1>{NAME}), (?P<acquired_count2>{COUNT}) azioni al portatore della (?P<company2>{NAME}) e (?P<acquired_count3>{COUNT}) azioni al portatore di nominali CHF (?P<acquired_nominal3>{MONEY}) della (?P<company3>{NAME}) contro attribuzione di (?P<issued_count>{COUNT}) azioni nominative da CHF (?P<issued_nominal>{MONEY}) e (?P<participation_count>{COUNT}) buoni di partecipazione nominativi da CHF (?P<participation_nominal>{MONEY})\. L'importo di CHF (?P<credit>{MONEY}) costituisce un credito verso la società\.\]", 'it')
    if m:
        return [event('historical_in_kind_contribution_clause_deleted', m, historical_annotation=True, currency='CHF')], ''

    m = match(rf"\[Rettifica dell'iscrizione del registro giornaliero no\. (?P<entry>{COUNT}) del (?P<entry_date>{DATE}), pubblicata nel FUSC no\. (?P<notice_number>{COUNT}) del (?P<notice_date>{DATE}); la fondazione è reiscritta, in quanto è stata erroneamente cancellata dal registro di commercio\.\]", 'it')
    if m:
        return [event('foundation_erroneous_deletion_reinstated_correction', m, 'status_changed', corrected=True)], ''

    m = match(rf'''L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE})\) est rectifiée en ce sens que la raison sociale de l'une des sociétés dont les actions ont fait l'objet de l'aport en nature est : "(?P<company_name>[^"\n]+)", \((?P<company_uid>{UID})\) et non (?P<previous_company_name>{NAME})''')
    if m:
        return [event('in_kind_contributed_company_name_corrected', m, corrected=True)], ''

    m = match(rf"L'associé-gérant (?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à l'associée-gérante (?P<buyer>{NAME}), maintenant à (?P<place>{NAME}), désormais titulaire de (?P<buyer_count>{COUNT}) parts de CHF (?P=nominal)\. (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        if number(m, 'before') != number(m, 'count') + number(m, 'remaining') or number(m, 'buyer_count') < number(m, 'count'):
            return [], text
        return [event('existing_female_manager_share_transfer_residence', m, 'ownership_changed', currency='CHF'),
                person('existing_female_manager_residence_changed', m, m['buyer'], 'associée-gérante', place=m['place'])], ''

    # The authorized-capital block belongs to parser195, including its payload.
    m = match(rf"Suppression de la clause statutaire relative à l'augmentation conditionnelle du capital fondée sur la décision d'autorisation du (?P<authorization_date>{DATE})\. Par décision du (?P<decision_date>{DATE}), l'assemblée générale a introduit une clause statutaire relative à une augmentation conditionnelle du capital-actions\. Pour les détails, voir les statuts\. (?P<legacy_clause>Suppression .+?Pour les détails, voir les statuts\.) (?P<name1>{NAME}), membre du conseil d'administration, nommé président, et (?P<name2>{NAME}), jusqu'ici président, continuent de signer collectivement à deux")
    if m and _FR_AUTHORIZED_CAPITAL_CLAUSE_REPLACED_NUMERIC_DATES.fullmatch(m['legacy_clause']):
        old, rest = extract_parser195_leftovers(m['legacy_clause'], language, *context)
        if not rest.strip(' .'):
            return [event('conditional_capital_clause_replaced_authorization_dates', m, 'capital_changed'), *old,
                    person('board_member_named_president_continued_signing', m, m['name1'], "président du conseil d'administration", 'Kollektivunterschrift zu zweien'),
                    person('previous_president_continued_board_signing', m, m['name2'], "membre du conseil d'administration", 'Kollektivunterschrift zu zweien', previous_role='président')], ''

    m = match(rf'(?P<seller1>{NAME}) et (?P<seller2>{NAME}) ont cédé (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) au nouvel associé (?P<buyer>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME}) \((?P<canton>[A-Z]{{2}})\), lequel est en outre nommé gérant Par conséquent, (?P=seller1) et (?P=seller2) sont maintenant associés chacun pour (?P<remaining_each>{COUNT}) parts de CHF (?P=nominal)')
    if m:
        # The text gives only the combined transfer; no per-seller allocation.
        return [event('two_sellers_combined_transfer_new_manager', m, 'ownership_changed', currency='CHF'),
                person('combined_transfer_new_associate_manager', m, m['buyer'], 'associé-gérant', place=m['place'])], ''

    m = match(rf'Der Vorstand hat am (?P<decision_date>{DATE}) beschlossen, auf den Eintrag des Vereins im Handelsregister zu verzichten\. Da dieser Verein kein nach kaufmännischer Art geführtes Gewerbe betreibt und somit nicht eintragungspflichtig ist, wird der auf ihn bezügliche Eintrag im Handelsregister gelöscht', 'de')
    if m:
        return [event('association_voluntary_deletion_without_effective_date', m, 'company_deleted', decision_body='board', reason='not_required_to_register', commercial_business=False)], ''

    m = match(rf'Vermögensübertragung: Der Verein überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) auf den (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: keine', 'de')
    if m:
        return [event('association_assets_transferred_without_inventory', m, 'assets_transferred', currency='CHF', consideration='none')], ''

    clause = r'Die Generalversammlung hat mit Beschluss vom {date} ein genehmigtes Partizipationsscheinkapital gemäss näherer Umschreibung in den Statuten geschaffen\.'
    m = match(clause.format(date=rf'(?P<decision_date>{DATE})') + r' \[bisher: ' + clause.format(date=rf'(?P<previous_date>{DATE})') + r'\]', 'de')
    if m:
        return [event('authorized_participation_capital_created_with_history', m, 'capital_changed')], ''
    return [], text
