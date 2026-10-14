from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, UID

# Written dates are retained verbatim in payloads, as in earlier parser rules.
DE_DATE = r'\d{1,2}\. (?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember) \d{4}'
FR_DATE = r'\d{1,2} (?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre) \d{4}'


def extract_parser322_leftovers(text, language, publication_id, published_at, org_uid, plz, canton):
    """Add events only for complete residual clauses; never replace legacy events."""
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
                        if re.fullmatch(DATE, value):
                            datetime.strptime(value, '%d.%m.%Y')
                        else:
                            months = 'Januar Februar März April Mai Juni Juli August September Oktober November Dezember'.split() if lang == 'de' else 'janvier février mars avril mai juin juillet août septembre octobre novembre décembre'.split()
                            day, month, year = value.replace('.', '').split()
                            datetime(int(year), months.index(month) + 1, int(day))
            except ValueError:
                return None
        return m

    def event(rule, m, kind='organization_changed', **extra):
        return _event(*context, kind, rule, {**m.groupdict(), 'action': rule.split('.')[2], **extra})

    m = match(rf"Mit dem Tagesregister Nr\. (?P<entry>\d+) vom (?P<entry_date>{DATE}) und mit dem SHAB Nr\. (?P<shab_number>\d+) vom (?P<publication_date>{DATE}) wurde (?P<name>{NAME}, {NAME}), von (?P<origin>{NAME}), in (?P<place>{NAME}), Kollektivunterschrift zu zweien versehentlich als mutiert aufgeführt\. Der Eintrag bleibt jedoch unverändert", 'de')
    if m:
        return [event('de.text.erroneous_person_mutation_unchanged.v1', m, unchanged=True)], ''

    m = match(rf"\[gestrichen: Die Generalversammlung hat mit Beschluss vom (?P<previous_decision_date>{DATE}) ein genehmigtes Kapital gemäss näherer Umschreibung in den Statuten eingeführt\.\]\. Die Generalversammlung hat mit Beschluss vom (?P<decision_date>{DATE}) ein genehmigtes Kapital gemäss näherer Umschreibung in den Statuten eingeführt", 'de')
    if m:
        return [event('de.text.authorized_capital_clause_replaced.v1', m, 'capital_changed', previous_clause_removed=True, new_clause_introduced=True)], ''

    m = match(rf"\[Mit Beschluss vom (?P<decision_date>{DATE}) hat die Generalversammlung die am (?P<authorization_date>{DATE}) beschlossene Statutenbestimmung über eine genehmigte Kapitalerhöhung aufgehoben\.\]", 'de')
    if m:
        return [event('de.text.bracketed_authorized_capital_clause_removed.v1', m, 'capital_changed', previous_clause_removed=True)], ''

    m = match(rf"Augmentation autorisée du capital-participation, fondée sur la décision d'autorisation du (?P<authorization_date>{DATE}), porté de CHF (?P<previous_capital>{MONEY}) à CHF (?P<capital>{MONEY}) par l'émission de (?P<issued>{MONEY}) bons de CHF (?P<nominal>{MONEY}), nominatifs, liés selon statuts\. Capital-participation: CHF (?P=capital), entièrement libéré, divisé en (?P<count>{MONEY}) bons de CHF (?P=nominal), nominatifs, liés selon statuts", 'fr')
    if m:
        amount = lambda key: Decimal(m[key].replace("'", ''))
        if amount('capital') != amount('count') * amount('nominal') or amount('capital') - amount('previous_capital') != amount('issued') * amount('nominal'):
            return [], leftover
        return [event('fr.text.authorized_participation_capital_increase.v1', m, 'capital_changed', currency='CHF', fully_paid=True)], ''

    m = match(rf"Vermögensübertragung: Der Geschäftsinhaber überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) auf die (?P<recipient>[^,]+), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: CHF (?P<consideration>{MONEY})", 'de')
    if m:
        return [event('de.text.proprietor_assets_transfer.v1', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft tritt einen Teil der Aktiven und Passiven an die "(?P<recipient>[^"\n]+)" \((?P<recipient_uid>{UID})\) mit Sitz in (?P<place>{NAME}) mittels Vermögensübertragungsvertrag vom (?P<agreement_date>{DATE}) mit Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von Fr\. (?P<liabilities>{MONEY}) ab\. Die Übertragung erfolgt ohne Gegenleistung', 'de')
    if m:
        return [event('de.text.partial_assets_transfer_without_consideration.v1', m, 'ownership_changed', currency='CHF', no_consideration=True)], ''

    m = match(rf'Transfert de patrimoine: selon contrat du (?P<agreement_date>{FR_DATE}), la société a transféré des actifs pour CHF (?P<assets>{MONEY}) et aucun passif envers les tiers à (?P<recipient>[^,]+), à (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Contre-prestation: (?P<fund_units>{MONEY}) parts du Fonds "(?P<fund>[^"\n]+)" \(ISIN (?P<isin>CH\d{{10}})\), géré par (?P<fund_manager>[^,]+) et créance de CHF (?P<claim>{MONEY})', 'fr')
    if m:
        return [event('fr.text.assets_transfer_fund_units_and_claim.v1', m, 'ownership_changed', currency='CHF', no_third_party_liabilities=True)], ''

    m = match(rf"Transfert de patrimoine: Selon contrat du (?P<agreement_date>{DATE}), le titulaire a transféré certains actifs pour CHF (?P<assets>{MONEY}) et certains passifs envers les tiers pour CHF (?P<liabilities>{MONEY}) à la société à responsabilité limitée (?P<recipient>[^,]+), à (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Contre-prestation: (?P<shares>\d+) parts sociales de CHF (?P<nominal>{MONEY}) et une créance de l'apporteur envers la société de CHF (?P<claim>{MONEY})", 'fr')
    if m:
        return [event('fr.text.proprietor_partial_transfer_shares_and_claim.v1', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf"L'inscription N°(?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée et complétée comme suit: Associés: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), chacun pour (?P<shares>\d+) parts de CHF (?P<nominal>{MONEY}); l'associé (?P=name2) n'exerce pas la signature sociale", 'fr')
    if m:
        rule = 'fr.text.associates_correction_unsigned_second.v1'
        return [event(rule, m, 'ownership_changed', currency='CHF')] + [_person_event(*context, 'officer_changed', rule, m['name'+str(i)], place=m['place'+str(i)], role='Gesellschafter', signing='ohne Zeichnungsberechtigung' if i == 2 else None, extra={'origin': m['origin'+str(i)], 'shares': m['shares'], 'nominal': m['nominal']}) for i in (1, 2)], ''

    m = match(rf"Con decisione del (?P<decision_date>{DATE}) la Camera di esecuzione e fallimenti del Tribunale d'appello del Cantone Ticino ha accordato effetto sospensivo al reclamo inoltrato contro la decisione di fallimento aperto nei confronti della titolare il (?P<bankruptcy_date>{DATE})\. \[finora: Il titolare è stato dichiarato in fallimento con decreto della Pretura del Distretto di Mendrisio-Sud del (?P=bankruptcy_date) a far tempo dal (?P=bankruptcy_date) alle ore (?P<bankruptcy_time>\d{{2}}:\d{{2}})\.\]", 'it')
    if m:
        try:
            datetime.strptime(m['bankruptcy_time'], '%H:%M')
        except ValueError:
            return [], leftover
        return [event('it.text.proprietor_bankruptcy_appeal_suspended.v1', m, suspensive_effect=True)], ''

    m = match(rf"Fusione: ripresa di attivi e passivi di (?P<absorbed>[^,]+), in (?P<place>{NAME}) \((?P<absorbed_uid>{UID})\), secondo il contratto di fusione del (?P<agreement_date>{DATE}) e bilancio al (?P<balance_date>{DATE}), che presenta attivi per CHF (?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY})\. La totalità del capitale azionario delle due società è detenuta dallo stesso azionista, la fusione avviene dunque senza aumento di capitale e senza attribuzione di azioni\. Conformemente all'attestazione di un perito revisore abilitato, dei crediti per un ammontare almeno equivalente allo scoperto, rispettivamente al sovraindebitamento, sono stati postergati", 'it')
    if m:
        return [event('it.text.common_owner_merger_subordinated_claims.v1', m, currency='CHF', capital_increase=False, share_allocation=False, claims_subordinated=True)], ''

    m = match(rf"Fusion: Übernahme der Aktiven und Passiven der (?P<absorbed>[^,]+), in (?P<place>{NAME}) \((?P<absorbed_uid>ChlE-\d{{3}}\.\d{{3}}\.\d{{3}})\) gemäss Fusionsvertrag vom (?P<agreement_date>{DE_DATE}) und Bilanz per (?P<balance_date>{DE_DATE})\. Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) gehen auf die übernehmende Gesellschaft über\. Da die übernehmende Gesellschaft mindestens im Umfang der Unterdeckung und Überschuldung über frei verwendbares Eigenkapital verfügt, sowie Gläubiger der übertragenden Gesellschaft mindestens im Umfang der Unterdeckung und Überschuldung im Rang hinter alle anderen Gläubiger zurückgetreten sind, sind die Voraussetzungen von Art\. 6 Abs\. 1 FusG für eine Fusion der übertragenden Gesellschaft mit der übernehmenden Gesellschaft gegeben\. Die Bestätigung eines staatlich beaufsichtigten Revisionsunternehmens, wonach die Voraussetzungen von Art\. 6 Abs\. 1 FusG für eine Fusion der übertragenden Gesellschaft mit der übernehmenden Gesellschaft gegeben sind, liegt vor\. Da sämtliche Aktien der an der Fusion beteiligten Gesellschaften durch dieselbe Aktionärin gehalten werden, findet weder eine Kapitalerhöhung noch eine Aktienzuteilung statt", 'de')
    if m:
        return [event('de.text.common_owner_merger_equity_and_subordination.v1', m, currency='CHF', capital_increase=False, share_allocation=False, uid_format_valid=False, claims_subordinated=True)], ''

    return [], leftover
