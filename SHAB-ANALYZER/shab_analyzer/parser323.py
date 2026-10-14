from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, UID
from .parser322 import FR_DATE


def extract_parser323_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete residual clauses after all legacy rules have run."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def valid_dates(values):
        try:
            for key, value in values.items():
                if key.endswith('_date'):
                    if re.fullmatch(DATE, value):
                        datetime.strptime(value, '%d.%m.%Y')
                    else:
                        day, month, year = value.split()
                        months = 'janvier février mars avril mai juin juillet août septembre octobre novembre décembre'.split()
                        datetime(int(year), months.index(month) + 1, int(day))
        except ValueError:
            return False
        return True

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        return m if m and valid_dates(m.groupdict()) else None

    def event(action, m, kind='organization_changed', **extra):
        rule = f'{language}.text.{action}.v1'
        return _event(*context, kind, rule, {**m.groupdict(), 'action': action, **extra})

    def person(action, m, *, role=None, signing=None):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', m['name'], place=m.groupdict().get('place'), role=role, signing=signing, extra={**m.groupdict(), 'action': action})

    m = match(r'\((?P<branch_label>[^()\n]+)\)')
    if m:
        source = re.search(rf"Inscription de la mention de l'existence d'une succursale à (?P<place>{NAME}) \((?P<branch_uid>{UID})\) \(" + re.escape(m['branch_label']) + r'\)\.?$', source_text)
        if source:
            return [event('branch_label_added', m, **source.groupdict())], ''

    m = match(rf"Transfert de patrimoine: selon contrat du (?P<agreement_date>{DATE}) et inventaire au (?P<inventory_date>{DATE}), la société a transféré des actifs pour CHF (?P<assets>{MONEY}) et des passifs envers les tiers pour CHF (?P<liabilities>{MONEY}) à la société (?P<recipient>[^,]+), à (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Contre-prestation: (?P<shares>{MONEY}) actions nominatives de CHF (?P<nominal>{MONEY}) entièrement libérées\. \[Modification des statuts \.\]")
    if m and '[Modification des statuts sur un point non soumis à publication.]' in source_text:
        return [event('assets_transfer_registered_shares', m, 'ownership_changed', currency='CHF', fully_paid=True, statutes_unpublished_point=True)], ''

    m = match(rf"(?P<notice_tail>\d{{2}}\.\d{{4}}, p\. \d+/\d+\))\. Par suite de changement d'état civil (?P<previous_name>{NAME}) porte désormais le nom de (?P<name>{NAME})")
    if m:
        source = re.search(rf"\(FOSC du (?P<notice_date>{DATE}), p\. \d+/\d+\)\. Par suite de changement d'état civil " + re.escape(m['previous_name']) + ' porte désormais le nom de ' + re.escape(m['name']) + r'\.?$', source_text)
        if source and valid_dates(source.groupdict()) and source.group(0).split('.', 1)[1].startswith(m['notice_tail']):
            e = person('civil_status_name_changed', m)
            e.payload.update(source.groupdict())
            return [e], ''

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat das (?P<court>Obergericht des Kantons {NAME}) die Beschwerde gegen das Konkurserkenntnis gutgeheissen und die mit Verfügung vom (?P<bankruptcy_date>{DATE}) des (?P<bankruptcy_court>Kantonsgericht {NAME}) angeordnete Konkurseröffnung aufgehoben', 'de')
    if m:
        return [event('bankruptcy_order_revoked_on_appeal', m, bankruptcy_revoked=True, appeal_upheld=True)], ''

    m = match(rf"L'administrateur (?P<name>{NAME}), n'exerce plus la signature sociale")
    if m:
        return [person('administrator_signing_revoked', m, role='Verwaltungsrat', signing='ohne Zeichnungsberechtigung')], ''

    m = match(rf'Auf die durch das Handelsregisteramt gestützt auf Art\. (?P<article>155 HRegV) veranlassten und Schweiz\. Handelsamtsblatt \(SHAB\) vom (?P<call1_date>{DATE}), (?P<call2_date>{DATE}) und (?P<call3_date>{DATE}) publizierten Rechnungsrufe wurde kein Interesse an der Aufrechterhaltung der Eintragung geltend gemacht\. Das amtliche Verfahren zur Löschung der Gesellschaft ist damit abgeschlossen, weil die Gesellschaft keine Geschäftstätigkeit mehr aufweist und keine verwertbaren Aktiven mehr hat\. Die Gesellschaft kann mangels Zustimmungen der eidg\. und kant\. Steuerverwaltung noch nicht gelöscht werden', 'de')
    if m:
        return [event('official_deletion_pending_tax_consent', m, deletion_pending=True, procedure_completed=True, no_business_activity=True, no_realizable_assets=True)], ''

    m = match(rf"L'associé-gérant et président (?P<transferor>{NAME}) détient désormais (?P<remaining_shares>\d+) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<transferred_shares>\d+) parts de CHF (?P=nominal) à (?P<recipient>{NAME}), désormais associé-gérant pour (?P=transferred_shares) parts de CHF (?P=nominal)")
    if m:
        return [event('associate_manager_share_transfer', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf"Par prononcé rendu le (?P<decision_date>{FR_DATE}), le (?P<court>président du Tribunal d'arrondissement de {NAME}) a prolongé de (?P<months>\d+) mois le sursis concordataire accordé à la société, soit jusqu'au (?P<until_date>{FR_DATE})")
    if m:
        return [event('composition_moratorium_extended', m)], ''

    m = match(rf"Division des (?P<previous_count>{MONEY}) actions de CHF (?P<previous_nominal>{MONEY}) en (?P<count>{MONEY}) actions de CHF (?P<nominal>{MONEY}), toutes nominatives, \. Capital-actions: CHF (?P<capital>{MONEY}), libéré à concurrence de CHF (?P<paid_capital>{MONEY}), divisé en (?P=count) actions de CHF (?P=nominal), nominatives, liées selon statuts")
    if m:
        amount = lambda key: Decimal(m[key].replace("'", ''))
        source_clause = f"Division des {m['previous_count']} actions de CHF {m['previous_nominal']} en {m['count']} actions de CHF {m['nominal']}, toutes nominatives, liées selon statuts."
        if source_clause in source_text and amount('previous_count') * amount('previous_nominal') == amount('capital') == amount('count') * amount('nominal') and amount('paid_capital') <= amount('capital'):
            return [event('registered_share_split', m, 'capital_changed', currency='CHF', restricted_transfer=True)], ''

    m = match(rf'(?P<name>{NAME}) continue de signer individuellement, mais désormais par procuration')
    if m:
        return [person('individual_signing_changed_to_procuration', m, signing='Einzelprokura')], ''

    m = match(rf"Nouveau numéro d'identification du siège principal: (?P<headquarters_uid>{UID})\. Date des nouveaux statuts du siège principal: \[biffé\]\. Nouvelle inscription au RC du siège principal: \[biffé\] \[biffé: Inscription au RC du siège principal : (?P<previous_registration_date>{DATE})\]")
    if m:
        return [event('headquarters_uid_and_registration_clauses_changed', m, statutes_date_clause_removed=True, registration_clause_removed=True)], ''

    m = match(rf"L'inscription (?P<entry>\d+) du (?P<entry_date>{DATE}) est complétée en ce sens que (?P<name>{NAME}) est désormais domicilié à (?P<place>{NAME})")
    if m:
        return [person('person_domicile_entry_completed', m)], ''

    return [], leftover
