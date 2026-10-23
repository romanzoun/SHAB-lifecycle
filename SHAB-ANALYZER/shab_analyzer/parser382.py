from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, UID
from .parser67 import _FR_ADMINISTRATORS_SIGN_INDIVIDUALLY
from .parser246 import _DE_BANKRUPTCY_CLOSED_DELETION_DEFERRED_FOR_CLAIMS
from .parser250 import _DE_COMPANY_REINSTATED_ERRONEOUS_DELETION_ART_260

NAME = r'[^,;.()\[\]]+?'
DATE = r'\d{2}\.\d{2}\.\d{4}'
LEGACY_PATTERNS = (
    _FR_ADMINISTRATORS_SIGN_INDIVIDUALLY,
    _DE_BANKRUPTCY_CLOSED_DELETION_DEFERRED_FOR_CLAIMS,
    _DE_COMPANY_REINSTATED_ERRONEOUS_DELETION_ART_260,
)


def extract_parser382_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize only bounded new variants; preserve legacy ownership and residue."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in LEGACY_PATTERNS):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', *, raw_balance=False):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('date') and not (raw_balance and key == 'balance_date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, i, role=None, signing=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', m[f'name{i}'], place=m.groupdict().get(f'place{i}'), role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra})

    m = match(rf'(?P<name1>{NAME}) et (?P<name2>{NAME}), qui est maintenant de (?P<origin2>{NAME}), signent désormais individuellement')
    if m:
        return [person('pair_individual_signing_second_origin_changed', m, i, signing='Einzelunterschrift') for i in (1, 2)], ''

    m = match(rf"(?P<name1>{NAME}), nommé président, et (?P<name2>{NAME}), jusqu'ici président, tous deux membres du conseil d'administration, continuent de signer collectivement à deux")
    if m:
        return [person('board_presidency_pair_continued_joint_signing', m, i, role="membre du conseil d'administration" + (', président' if i == 1 else ''), signing='Kollektivunterschrift zu zweien') for i in (1, 2)], ''

    m = match(rf'Das Konkursverfahren ist mit Verfügung des Konkursrichters des Regionalgerichts (?P<court_place>{NAME}) vom (?P<decision_date>{DATE}) abgeschlossen\. Die Eintragung bleibt nur zum Zweck der Geltendmachung von abgetretenen Ansprüchen nach Art\. 260 SchKG erhalten\. Die Verfügungsbefugnisse der Organe der (?P<name>[^;\[\]]+?) leben nicht wieder auf', 'de')
    if m:
        return [event('bankruptcy_closed_registration_retained_assigned_claims', m, 'status_changed', registration_retained=True, organs_authority_restored=False, legal_basis='Art. 260 SchKG')], ''

    m = match(r'\[Die Gesellschaft wurde irrtümlich gelöscht\. Sie wird deshalb wieder als sich in Liquidation befindlich in das Handelsregister eingetragen\.\] \[gestrichen: Löschung von Amtes wegen gemäss Art\. 159 HRegV, nachdem kein begründeter Einspruch gegen die Löschung erhoben wurde\]', 'de')
    if m:
        return [event('erroneous_deletion_reinstated_in_liquidation', m, 'status_changed', reinstated=True, in_liquidation=True, legal_basis='Art. 159 HRegV')], ''

    m = match(rf'\[Nachtrag des Publikationsorgans zum im SHAB Nr\. (?P<notice_number>\d+) vom (?P<notice_date>{DATE}) publizierten TR-Eintrag Nr\. (?P<entry>\d+) vom (?P<entry_date>{DATE})\.\]', 'de')
    if m:
        return [event('publication_organ_notice_supplement', m, 'publication_corrected')], ''

    merger = rf'Fusione: ripresa di attivi e passivi di (?P<absorbed_name>{NAME}), in (?P<absorbed_place>{NAME}) \((?P<absorbed_uid>{UID})\), secondo '
    balance = rf'contratto di fusione del (?P<agreement_date>{DATE}) e bilancio al (?P<balance_date>{DATE}), che presenta attivi per CHF (?P<assets>{MONEY})'
    m = match(merger + balance + rf", e passivi verso terzi per CHF (?P<liabilities>{MONEY})\. Conformemente all'attestazione di un perito revisore abilitato, dei crediti per un ammontare almeno equivalente allo scoperto e al sovraindebitamento sono stati postergati\. La totalità del capitale azionario delle due società è detenuta dallo stesso azionista, per cui la fusione avviene senza aumento del capitale e senza attribuzione di azioni", 'it', raw_balance=True)
    if m:
        try:
            datetime.strptime(m['balance_date'], '%d.%m.%Y')
            valid = True
        except ValueError:
            valid = False
        return [event('common_shareholder_merger_subordinated_claims_raw_balance', m, currency='CHF', capital_increase=False, share_allocation=False, claims_subordinated=True, balance_date_valid=valid)], ''

    m = match(merger + 'il ' + balance + rf' e passivi verso terzi per CHF (?P<liabilities>{MONEY})\. La società assuntrice detiene tutte le azioni della società trasferente, per cui la fusione avviene senza aumento del capitale e senza attribuzione di azioni', 'it')
    if m:
        return [event('wholly_owned_merger_without_capital_increase', m, currency='CHF', capital_increase=False, share_allocation=False)], ''

    m = match(rf'Nouveaux associés: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), avec signature collective à deux, avec (?P<partner1>{NAME}) ou (?P<partner2>{NAME}) ou (?P<partner3>{NAME}) ou (?P<partner4>{NAME})')
    if m:
        # The first person's individual signature was already emitted upstream.
        original = f"Nouveaux associés: {m['name1']}, de {m['origin1']}, à {m['place1']}, avec signature individuelle et {m['name2']}, de {m['origin2']}, à {m['place2']}, avec signature collective à deux, avec " + ' ou '.join(m[f'partner{i}'] for i in (1, 2, 3, 4)) + '.'
        if original in source_text:
            return [person('new_associates_mixed_restricted_signing', m, 1, role='associé', signing='Einzelunterschrift'), person('new_associates_mixed_restricted_signing', m, 2, role='associée', signing='Kollektivunterschrift zu zweien', signing_restriction='avec ' + ' ou '.join(m[f'partner{i}'] for i in (1, 2, 3, 4)))], ''

    m = match(rf"Par décision de la présidente du Tribunal de l'arrondissement de (?P<court_place>{NAME}) du (?P<day>\d{{1,2}}) octobre (?P<year>\d{{4}}), l'association a été déclarée dissoute conformément à l'article 154 ORC; sa liquidation a été ordonnée selon les dispositions applicables à la faillite\. La raison de commerce devient: (?P<name>[^;\[\]]+ en liquidation)")
    if m:
        try:
            decision_date = datetime(int(m['year']), 10, int(m['day'])).strftime('%d.%m.%Y')
        except ValueError:
            return [], text
        return [event('association_judicial_dissolution_bankruptcy_liquidation', m, 'status_changed', decision_date=decision_date, legal_basis='article 154 ORC', in_liquidation=True)], ''

    m = match(rf'Eingetragene Person geändert: (?P<previous_name>{NAME}) \((?P<uid>{UID})\), Revisionsorgan, neu mit dem Namen (?P<name>{NAME}) \((?P=uid)\)', 'de')
    if m:
        return [event('auditor_name_changed_same_uid', m, 'auditor_changed', role='Revisionsorgan')], ''

    m = match(rf"Le jugement de faillite du Tribunal de première instance du (?P<bankruptcy_date>{DATE}) a été rendu à tort, puisque la créance objet de la poursuite a été acquitée en capital, intérêts et frais préalablement au prononcé de la faillite, ce qui a été constaté et rectifié par jugement du Tribunal de première instance du (?P<decision_date>{DATE})\. C'est pour ce motif que l'inscription (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) a été radiée \(et non par suite d'annulation ou de révocation de la faillite\)\. L'inscription (?P<corrected_entry>\d+) du (?P<corrected_entry_date>{DATE}) \(FOSC du (?P<corrected_notice_date>{DATE}), p\. (?P<corrected_notice_ref>\d+/\d+)\) est rectifiée en ce sens")
    if m:
        return [event('erroneous_bankruptcy_paid_before_judgment_corrected', m, 'publication_corrected', debt_paid_before_bankruptcy=True)], ''

    m = match(rf'Umwandlung: Die Gesellschaft mit beschränkter Haftung hat das Stammkapital auf CHF (?P<capital>{MONEY}) erhöht und wird gemäss Umwandlungsplan vom (?P<plan_date>{DATE}) und Bilanz per (?P<balance_date>{DATE}) mit Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) in eine Aktiengesellschaft umgewandelt\. Die Überschuldung und die Unterdeckung wurden anlässlich der Kapitalerhöhung vom (?P<increase_date>{DATE}) beseitigt\. Die Gesellschafter erhalten für ihre bisherigen Stammanteile (?P<shares>{COUNT}) Aktien zu CHF (?P<nominal>{MONEY})\. \. Bei der ordentlichen Kapitalerhöhung vom (?P=increase_date) werden Forderungen in der Höhe von CHF (?P<offset>{MONEY}) verrechnet, wofür (?P<offset_shares>{COUNT}) Namenaktien zu CHF (?P=nominal) ausgegeben werden', 'de')
    if m:
        return [event('conversion_capital_increase_deficit_eliminated', m, currency='CHF', target_legal_form='Aktiengesellschaft', deficit_eliminated=True), event('ordinary_capital_increase_claims_offset_after_conversion', m, 'capital_changed', currency='CHF')], ''
    return [], text
