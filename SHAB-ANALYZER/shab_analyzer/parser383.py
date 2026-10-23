from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, UID
from .parser137 import _FR_BRANCH_MENTION_REMOVED
from .parser203 import _FR_ASSOCIATE_TRANSFER_TO_MANAGER_PRESIDENT

NAME = r'[^,;.()\[\]]+?'
DATE = r'\d{2}\.\d{2}\.\d{4}'


def extract_parser383_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize bounded new clauses, preserving all upstream events and residue."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in (_FR_BRANCH_MENTION_REMOVED, _FR_ASSOCIATE_TRANSFER_TO_MANAGER_PRESIDENT)):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, role, signing, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', m['name'], place=m.groupdict().get('place'), role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra})

    m = match(rf'Mit dem SHAB-Nr\. (?P<notice>\d+) vom (?P<notice_date>{DATE}) publizierten TR-Text (?P<entry>\d+/\d{{4}}) wurden nicht die vollständigen Angaben aufgeführt\. Korrekt wäre: (?P<name>{NAME}, {NAME}), von (?P<origin>{NAME}), in (?P<place>{NAME}), Geschäftsführer und Gesellschafter, mit Einzelunterschrift \[bisher: (?P<previous_nationality>{NAME}) Staatsangehöriger, Gesellschafter und Geschäftsführer, mit Kollektivunterschrift zu zweien, mit (?P<previous_count>{COUNT}) Stammanteilen zu je CHF (?P<previous_nominal>{MONEY})\]', 'de')
    if m:
        return [person('manager_associate_incomplete_notice_corrected', m, 'Geschäftsführer und Gesellschafter', 'Einzelunterschrift', corrected=True)], ''

    m = match(rf"L'associée-gérante (?P<seller>{NAME}) cède (?P<transferred>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), d'(?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé-gérant titulaire de (?P=transferred) parts de CHF (?P=nominal); (?P=seller) est désormais titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)")
    if not m:
        m = match(rf"(?P<seller>{NAME}) cède (?P<transferred>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé sans signature, avec (?P=transferred) parts de CHF (?P=nominal); (?P=seller) reste titulaire d'une part de CHF (?P=nominal)")
    if m:
        remaining = m.groupdict().get('remaining', '1')
        number = lambda v: Decimal(v.replace("'", ''))
        if number(m['transferred']) + number(remaining) != number(m['before']) or number(m['transferred']) <= 0 or number(remaining) <= 0:
            return [], text
        return [event('partial_share_transfer_new_associate_single_or_plural_remainder', m, remaining_count=remaining, currency='CHF', buyer_role='associé-gérant' if 'remaining' in m.groupdict() else 'associé', **({'buyer_signing': 'ohne Zeichnungsberechtigung'} if 'remaining' not in m.groupdict() else {}))], ''

    m = match(r'sur un point non soumis à modification')
    if m:
        source = re.search(rf'Statuts modifiés le (?P<statutes_date>{DATE}) sur un point non soumis à modification\.$', source_text)
        if source:
            try:
                datetime.strptime(source['statutes_date'], '%d.%m.%Y')
            except ValueError:
                return [], text
            return [event('statutes_modified_attested_non_modification_wording', source)], ''

    m = match(rf'L\'inscription no\. (?P<entry>\d+) du (?P<entry_date>{DATE}) \(publication FOSC du (?P<notice_date>{DATE}) page (?P<notice_page>\d+)/ (?P<notice_id>\d+)\) est rectifiée en ce sens que l\'administrateur et président porte de nom de "(?P<name>{NAME})" \(et non: "(?P<previous_name>{NAME})"\)')
    if m:
        return [event('administrator_president_name_notice_corrected', m, 'publication_corrected')], ''

    m = match(r'Gallen')
    if m and re.search(r"Radiation de la mention de l'existence d'une succursale à St\. Gallen\.$", source_text):
        return [event('branch_mention_deleted_sankt_gallen', m, place='St. Gallen')], ''

    m = match(rf'\[Gemäss Mitteilung der Sachwalterin, (?P<trustee>{NAME}), in (?P<place>{NAME}) \((?P<uid>{UID})\), vom (?P<decision_date>{DATE}) ist der Nachlassvertrag abgeschlossen\.\] \[gestrichen: Die Einzelrichterin des Bezirksgerichts (?P<court_place>{NAME}), Abteilung (?P<division>\d+), hat mit Entscheid vom (?P<approval_date>{DATE}) den ordentlichen Nachlassvertrag genehmigt\. Für den Vollzug des Nachlassvertrages wird die eingesetzte Sachwalterin (?P=trustee) \((?P=uid)\), beauftragt\.\]\. \[gestrichen: Mit Entscheid der Einzelrichterin des Bezirksgerichts (?P=court_place), Abteilung (?P=division), vom (?P<moratorium_date>{DATE}) wurde eine definitive Nachlassstundung von sechs Monaten bis (?P<end_date>{DATE}) bewilligt\. Als Sachwalterin wird die (?P=trustee), in (?P=place) \((?P=uid)\), ernannt\.\]', 'de')
    if m:
        return [event('composition_agreement_completed_historical_clauses_deleted', m, 'status_changed', historical_clauses_deleted=True)], ''

    m = match(r"Par décision du (?P<decision_day>\d{1,2}) octobre (?P<decision_year>\d{4}), le président du Tribunal d'arrondissement de (?P<court_place>[^,;.]+) a rejeté la requête de restitution de délai, révoqué l'effet suspensif et confirmé le jugement rendu le (?P<judgment_day>\d{1,2}) mai (?P<judgment_year>\d{4})")
    if m:
        try:
            dates = {k + '_date': datetime(int(m[k + '_year']), month, int(m[k + '_day'])).strftime('%d.%m.%Y') for k, month in [('decision', 10), ('judgment', 5)]}
        except ValueError:
            return [], text
        return [event('deadline_restitution_rejected_judgment_confirmed', m, 'status_changed', **dates)], ''

    m = match(rf"En complément de l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\), dépôt d'un nouvel exemplaire des statuts")
    if m:
        return [event('statutes_copy_deposited_notice_supplement', m, 'publication_corrected')], ''

    m = match(rf'Haftung/Nachschusspflicht neu: \[Streichung des Eintrags aufgrund geänderter Eintragungsvorschriften\.\] \[gestrichen: Ohne persönliche Haftung und ohne Nachschusspflicht\.\]\. Pflichten neu: \[Anpassung aufgrund geänderter Eintragungsvorschriften\.\] \[gestrichen: Pflichten: Jeder Genossenschafter hat mindestens einen Anteilschein zu CHF (?P<previous_nominal>{COUNT}\.--) zu übernehmen\.\]\. Beitrags- oder Leistungspflichten der Genossenschafter gemäss näherer Umschreibung in den Statuten', 'de')
    if m:
        return [event('cooperative_obligations_registration_rules_updated', m, historical_clauses_deleted=True)], ''

    m = match(rf'Fatti particolari: \[radiati: Conferimenti in natura: apporto di (?P<previous_shares>{COUNT}) azioni al portatore da CHF (?P<previous_nominal>{COUNT}\.\-\-) cadauna della (?P<contributed_company>{NAME}) \((?P<register_id>CH-\d{{3}}\.\d\.\d{{3}}\.\d{{3}}-\d)\), in (?P<place>{NAME}) per il valore complessivo di CHF (?P<value>{COUNT}\.\-\-), accettato dalla società per tale importo e computato sul capitale sociale, contro rimessa all\'apportatore di (?P<count>{COUNT}) quote da CHF (?P<nominal>{COUNT}\.\-\-) Contratto: (?P<agreement_date>{DATE})\.\]', 'it')
    if m:
        return [event('historical_contribution_in_kind_clause_deleted', m, historical_clause_deleted=True, currency='CHF')], ''

    m = match(rf"par (?P<name>{NAME}), d'(?P<origin>{NAME}), au (?P<place>{NAME}), liquidatrice")
    if m and re.search(r'La liquidation est opérée sous la raison de commerce: [^;\n]+?, en liquidation ' + re.escape(leftover.rstrip('.')) + r' avec signature individuelle\.$', source_text):
        return [person('liquidator_appointed_origin_au_domicile', m, 'liquidatrice', 'Einzelunterschrift')], ''
    return [], text
