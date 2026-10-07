from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID
from .parser301 import MONTHS, WRITTEN_DATE


def extract_parser302_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete sample-backed clauses, preserving unsupported input."""
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
                    elif key.endswith('_written'):
                        day, month, year = value.split()
                        datetime(int(year), MONTHS[month], int(day))
            except ValueError:
                return None
        return m

    def event(rule, action, m):
        return _event(*context, 'organization_changed', rule, {'action': action, **m.groupdict()})

    def person(rule, name, **payload):
        return _person_event(*context, 'officer_changed', rule, name, **payload)

    m = match(rf'Die Generalversammlung hat mit Beschluss vom (?P<decision_date>{DATE}) den Beschluss über die Ermächtigung einer genehmigten Kapitalerhöhung vom (?P<authorization_date>{DATE}) gemäss näherer Umschreibung in den Statuten angepasst\. \[bisher: Die Generalversammlung hat mit Beschluss vom (?P<previous_decision_date>{DATE}) den Beschluss über die Ermächtigung einer genehmigten Kapitalerhöhung vom (?P<previous_authorization_date>{DATE}) gemäss näherer Umschreibung in den Statuten angepasst\.\]\. Die Generalversammlung hat mit Beschluss vom (?P<conditional_decision_date>{DATE}) die Statutenbestimmung über die bedingte Kapitalerhöhung vom (?P<conditional_date>{DATE}) geändert\. \[bisher: Die Generalversammlung hat mit Beschluss vom (?P<previous_conditional_decision_date>{DATE}) die Statutenbestimmung über die bedingte Kapitalerhöhung vom (?P<previous_conditional_date>{DATE}) angepasst\.\]', 'de')
    if m:
        return [event('de.text.authorized_conditional_capital_amended.v1', 'authorized_conditional_capital_amended', m)], ''

    m = match(rf'Liquidationsadresse: (?P<address>[^.;]+?)\. \[gestrichen: Liquidationsadresse: (?P<previous_address>[^.;]+?)\.\]', 'de')
    if m:
        return [event('de.text.liquidation_address_corrected.v1', 'liquidation_address_corrected', m)], ''

    m = match(rf'Vermögensübertragung: Der Geschäftsinhaber überträgt gemäss Vertrag vom (?P<contract_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient>{NAME}) \((?P<recipient_uid>{UID})\), in (?P<place>{NAME})\. Gegenleistung: (?P<share_count>{COUNT}) Namenaktien zu CHF (?P<nominal>{MONEY}) un CHF (?P<claim>{MONEY}) als Forderung gutgeschrieben', 'de')
    if m:
        return [event('de.text.business_assets_transferred_shares_claim.v1', 'business_assets_transferred_shares_claim', m)], ''

    m = match(rf'Die Gesellschaft hat mit Beschluss vom (?P<decision_date>{DATE}) die mit Beschluss vom (?P<introduction_date>{DATE}) eingeführte und mit Beschluss vom (?P<amendment_date>{DATE}) geänderte Bestimmung betreffend bedingter Kapitalerhöhung gemäss näherer Umschreibung in den Statuten geändert\. \[bisher: Die Gesellschaft hat mit Beschluss vom (?P<previous_decision_date>{DATE}) die mit Beschluss vom (?P<previous_introduction_date>{DATE}) eingeführte Bestimmung betreffend bedingter Kapitalerhöhung gemäss näherer Umschreibung in den Statuten geändert\.\]', 'de')
    if m:
        return [event('de.text.conditional_capital_repeated_amendment.v1', 'conditional_capital_repeated_amendment', m)], ''

    m = match(rf'Par suite de fusion, les (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) de (?P<previous_name>[^;]+?) \((?P<previous_uid>{UID})\) sont transférées à (?P<name>[^;]+?) \((?P<uid>{UID})\), à (?P<place>{NAME}), nouvelle associée', 'fr')
    if m:
        return [event('fr.text.merger_corporate_associate_transfer.v1', 'merger_corporate_associate_transfer', m)], ''

    m = match(rf'Mit Urteil vom (?P<decision_date>{DATE}) hat das (?P<court>{NAME}) eine COVID\-19\-Stundung für drei Monate bis (?P<deadline_date>{DATE}) gewährt', 'de')
    if m:
        return [event('de.text.covid_moratorium_three_months.v1', 'covid_moratorium_three_months', m)], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_reference>\d+/\d+)\) est rectifiée en ce sens que le nom exact du nouveau membre du conseil de fondation est (?P<name>{NAME}) \(et non (?P<previous_name>{NAME}) comme publié\)", 'fr')
    if m:
        return [person('fr.persons.foundation_member_name_corrected.v1', m['name'], role='membre du conseil de fondation', extra=m.groupdict())], ''

    m = match(rf'Das (?P<appeal_court>{NAME}) hat mit Verfügung vom (?P<decision_date>{DATE}) der Beschwerde gegen die Verfügung des (?P<court>{NAME}) vom (?P<appealed_date>{DATE}) betreffend Konkurseröffnung superprovisorisch die aufschiebende Wirkung zuerkannt\. Demnach wird die Eintragung betreffend Konkurs im Handelsregister gestrichen\. \[bisher: Mit Verfügung vom (?P<previous_decision_date>{DATE}) hat das (?P<previous_court>{NAME}) über das Vermögen des Inhabers mit Wirkung ab dem (?P<opening_date>{DATE}), (?P<opening_time>(?:[01]\d|2[0-3])\.[0-5]\d) Uhr, den Konkurs eröffnet\.\]', 'de')
    if m:
        return [event('de.text.bankruptcy_appeal_provisional_suspension.v1', 'bankruptcy_appeal_provisional_suspension', m)], ''

    m = match(rf"Par décision du (?P<decision_date>{DATE}), le (?P<court>{NAME}) a annulé la faillite du titulaire de l'entreprise prononcée le (?P<opening_date>{DATE}); l'inscription est rétablie comme ci\-devant \(FOSC No (?P<notice_number>{COUNT}) du (?P<notice_date>{DATE}) publ\. No (?P<notice_id>{COUNT})\)", 'fr')
    if m:
        return [event('fr.text.proprietor_bankruptcy_annulled.v1', 'proprietor_bankruptcy_annulled', m)], ''

    m = match(rf'Réunion des (?P<previous_count>{COUNT}) actions de CHF (?P<previous_nominal>{MONEY}), nominatives, liées selon statuts, en (?P<new_count>{COUNT}) actions de CHF (?P<new_nominal>{MONEY})\. Capital\-actions: CHF (?P<capital>{MONEY}), entièrement libéré, divisé en (?P<count>{COUNT}) actions de CHF (?P<nominal>{MONEY}), nominatives, liées selon statuts', 'fr')
    if m:
        return [event('fr.text.registered_shares_consolidated.v1', 'registered_shares_consolidated', m)], ''

    m = match(rf"Suppression de la clause statutaire relative à l'augmentation autorisée du capital \(fondée sur la décision d'autorisation du (?P<authorization_written>{WRITTEN_DATE})\), le délai étant écoulé\. Les (?P<previous_count>{COUNT}) actions nominatives de CHF (?P<previous_nominal>{MONEY}) sont transformées en (?P<converted_count>{COUNT}) actions nominatives de CHF (?P<converted_nominal>{MONEY})\. (?P<reclassified_count>{COUNT}) actions nominatives ordinaires de CHF (?P<reclassified_nominal>{MONEY}) sont transformées en (?P<converted_c_count>{COUNT}) actions nominatives de type C de CHF (?P<converted_c_nominal>{MONEY}), privilégiées quant au produit de liquidation et/ou de distribution, (?P<converted_d_count>{COUNT}) actions nominatives de type D de CHF (?P<converted_d_nominal>{MONEY}) et (?P<converted_e_count>{COUNT}) actions nominatives de type E de CHF (?P<converted_e_nominal>{MONEY})\. Nouveau capital\-actions: CHF (?P<capital>{MONEY}), entièrement libéré, divisé en (?P<ordinary_count>{COUNT}) actions nominatives ordinaires de CHF (?P<ordinary_nominal>{MONEY}), (?P<b_count>{COUNT}) actions nominatives de type B de CHF (?P<b_nominal>{MONEY}), privilégiées quant au produit de liquidation et/ou de distribution, (?P<c_count>{COUNT}) actions nominatives de type C de CHF (?P<c_nominal>{MONEY}), privilégiées quant au produit de liquidation et/ou de distribution, (?P<d_count>{COUNT}) actions nominatives de type D de CHF (?P<d_nominal>{MONEY}), privilégiées quant au produit de liquidation et/ou de distribution, et (?P<e_count>{COUNT}) actions nominatives de type E de CHF (?P<e_nominal>{MONEY}), privilégiées quant au produit de liquidation et/ou de distribution, toutes avec restrictions quant à la transmissibilité selon statuts\. L'assemblée générale a modifié deux clauses statutaires relatives à une augmentation autorisée du capital \(selon décisions d'autorisation du (?P<authorized_written>{WRITTEN_DATE})\) par décision du (?P<authorized_decision_written>{WRITTEN_DATE})\. Pour les détails, voir les statuts\. L'assemblée générale a modifié une clause statutaire relative à une augmentation conditionnelle du capital \(selon décision relative à l'octroi de droits du (?P<conditional_written>{WRITTEN_DATE})\) par décision du (?P<conditional_decision_written>{WRITTEN_DATE})\. Pour les détails, voir les statuts", 'fr')
    if m:
        return [event('fr.text.share_classes_capital_provisions_amended.v1', 'share_classes_capital_provisions_amended', m)], ''

    m = match(rf"Administration: (?P<name1>{NAME}), président, jusqu'ici directeur, (?P<name2>{NAME}), secrétaire, nommé directeur, et (?P<name3>{NAME}), de et à (?P<place>{NAME})\. Signature collective à deux de (?P=name1) ou (?P=name3), ou individuelle de (?P=name2); les pouvoirs de ce dernier sont modifiés en ce sens", 'fr')
    if m:
        return [person('fr.persons.administrators_mixed_signing.v1', m['name1'], role='administrateur, président', signing='Kollektivunterschrift zu zweien', extra={'previous_role': 'directeur'}), person('fr.persons.administrators_mixed_signing.v1', m['name2'], role='administrateur, secrétaire, directeur', signing='Einzelunterschrift'), person('fr.persons.administrators_mixed_signing.v1', m['name3'], place=m['place'], role='administrateur', signing='Kollektivunterschrift zu zweien', extra={'origin': m['place']})], ''

    return [], leftover
