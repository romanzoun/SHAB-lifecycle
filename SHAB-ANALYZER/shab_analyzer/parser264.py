from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event

DATE = r'\d{2}\.\d{2}\.\d{4}'
NAME = r'[^,;]+?'
MONEY = r"[\d']+(?:\.\d+|\.--)?"
UID = r'CHE-\d{3}\.\d{3}\.\d{3}'


def extract_parser264_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Parse bounded, sample-backed clauses, checking source for consumed facts."""
    del language
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern):
        m = re.fullmatch(pattern + r'\.?', leftover, re.I)
        if m:
            try:
                for k, v in m.groupdict().items():
                    if k.endswith('date'):
                        datetime.strptime(v, '%d.%m.%Y')
                    if k == 'time':
                        datetime.strptime(v, '%H.%M')
            except ValueError:
                return None
        return m

    def source(pattern, m):
        s = re.search(pattern + r'\.?$', source_text, re.I) if m else None
        return s if s and all(v is None or s[k] == v for k, v in m.groupdict().items()) else None

    def event(event_type, rule, **payload):
        return _event(*context, event_type, rule, payload)

    def person(rule, name, **kwargs):
        return _person_event(*context, 'officer_changed', rule, name, **kwargs)

    m = match(rf"Par décision présidentielle du (?P<date>{DATE}) du (?P<court>{NAME}), l'effet suspensif est octroyé au recours formé contre la décision de faillite")
    if m:
        return [event('status_changed', 'fr.text.bankruptcy_appeal_suspensive_effect.v1', **m.groupdict(), action='suspensive_effect_granted')], ''

    m = match(rf'(?P<date>{DATE})\. Mittel neu: (?P<means>[^\[\]]+) \[bisher: Mittel: (?P<previous_means>[^\[\]]+)\. \]')
    s = source(rf'Statutenänderung: (?P<first_date>{DATE})\. (?P<date>{DATE})\. Mittel neu: (?P<means>[^\[\]]+) \[bisher: Mittel: (?P<previous_means>[^\[\]]+)\. \]\. \[Weitere Änderungen berühren keine publikationspflichtigen Tatsachen\.\]', m)
    if s:
        return [event('statutes_changed', 'de.text.second_statutes_date_means_changed.v1', date=datetime.strptime(m['date'], '%d.%m.%Y').date().isoformat()), event('organization_changed', 'de.text.second_statutes_date_means_changed.v1', action='means_changed', means=[v.strip() for v in m['means'].split(';')], previous_means=m['previous_means'])], ''

    m = match(rf'Bemerkungen zum Hauptsitz neu: Mit Entscheid des (?P<court>{NAME}), Abteilung (?P<division>\d+), vom (?P<date>{DATE}) ist über den Hauptsitz mit Wirkung ab dem (?P<effective_date>{DATE}), (?P<time>\d{{2}}\.\d{{2}}) Uhr, der Konkurs eröffnet worden')
    if m:
        return [event('status_changed', 'de.text.head_office_bankruptcy_opened.v1', **m.groupdict(), scope='head_office', action='bankruptcy_opened')], ''

    m = match(rf"L'inscription no\. (?P<entry>\d+) du (?P<entry_date>{DATE}) \(publication FOSC du (?P<notice_date>{DATE}) page (?P<notice_ref>\d+/\d+)\) est complétée en ce sens que les (?P<count>[\d']+) actions de CHF (?P<nominal>{MONEY}) sont privilégiées, en sus du droit de vote, quant au dividende et quant au produit de liquidation")
    if m:
        return [event('capital_changed', 'fr.text.preferred_share_rights_supplemented.v1', **m.groupdict(), action='rights_supplemented', shares_count=int(m['count'].replace("'", '')), rights=['vote', 'dividend', 'liquidation_proceeds'], currency='CHF')], ''

    m = match(rf'Les membres du comité exécutif (?P<a>{NAME}) et (?P<b>{NAME}), signent désormais individuellement')
    if m:
        return [person('fr.persons.executive_committee_individual_signing.v1', m[k], role='membre du comité exécutif', signing='Einzelunterschrift', extra={'action': 'signing_changed'}) for k in 'ab'], ''

    m = match(rf'\[bisher: (?P<place>{NAME}) \((?P<previous_uid>CH-\d{{3}}\.\d\.\d{{3}}\.\d{{3}}-\d)\) HR (?P<register_canton>[A-Z]{{2}})\]\. (?P<added_place>{NAME}) \((?P<added_uid>{UID})\)')
    s = source(rf'Zweigniederlassung neu: (?P<place>{NAME}) \((?P<uid>{UID})\) \[bisher: (?P=place) \((?P<previous_uid>CH-\d{{3}}\.\d\.\d{{3}}\.\d{{3}}-\d)\) HR (?P<register_canton>[A-Z]{{2}})\]\. (?P<added_place>{NAME}) \((?P<added_uid>{UID})\)', m)
    if s:
        rule = 'de.text.branch_uid_replaced_and_branch_added.v1'
        return [event('branch_changed', rule, action='updated', place=s['place'], branch_uid=s['uid'], previous_uid=s['previous_uid'], register_canton=s['register_canton']), event('branch_changed', rule, action='added', place=s['added_place'], branch_uid=s['added_uid'])], ''

    m = match(rf'Das Statutendatum vom (?P<date>{DATE}) wurde irrtümlich erfasst und wird somit gestrichen')
    if m:
        return [event('statutes_changed', 'de.text.erroneous_statutes_date_deleted.v1', **m.groupdict(), action='deleted')], ''

    address = r'(?P<street_{k}>[^,;\[\]]+), (?P<postal_code_{k}>\d{{4}}) (?P<place_{k}>[^.;\[\]]+)'
    m = match(r'\[gestrichen: Weitere Geschäftsstelle: ' + address.format(k='a') + r'\.\]\. \[gestrichen: Weitere Geschäftsstelle: ' + address.format(k='b') + r'\]')
    if m:
        return [event('address_changed', 'de.text.two_business_offices_deleted.v1', action='removed', kind='business_office', street=m['street_'+k], postal_code=m['postal_code_'+k], place=m['place_'+k]) for k in 'ab'], ''

    m = match(rf'(?:Anteilscheine neu: CHF (?P<nominal>{MONEY}) )?\[bisher: CHF (?P<previous_nominal>{MONEY})\]')
    s = source(rf'Anteilscheine neu: CHF (?P<nominal>{MONEY}) \[bisher: CHF (?P<previous_nominal>{MONEY})\]', m)
    if s:
        return [event('capital_changed', 'de.text.cooperative_share_nominal_changed.v1', **s.groupdict(), currency='CHF', kind='cooperative_share_certificate', action='changed')], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que l'assemblée générale a introduit une clause statutaire relative à une augmentation autorisée du capital par décision du (?P<day>\d{{1,2}}) décembre (?P<year>\d{{4}}) \(et non du (?P<previous_day>\d{{1,2}}) décembre (?P<previous_year>\d{{4}}), comme publié\)")
    if m:
        try:
            corrected = datetime(int(m['year']), 12, int(m['day'])).date().isoformat()
            previous = datetime(int(m['previous_year']), 12, int(m['previous_day'])).date().isoformat()
        except ValueError:
            return [], leftover
        return [event('capital_changed', 'fr.text.authorized_capital_decision_date_corrected.v1', **m.groupdict(), action='corrected', decision_date=corrected, previous_decision_date=previous)], ''

    pattern = rf"(?P<seller>{NAME}) est désomais associé pour (?P<remaining>\d+) parts de CHF (?P<nominal>{MONEY}) suite à la cession de une part de CHF (?P<transfer_nominal>{MONEY}) à l'associée (?P<buyer>{NAME}) désormais associée pour (?P<received>\d+) parts de CHF (?P<buyer_nominal>{MONEY})\. Gérants: les associés (?P=seller), président, et (?P=buyer), tous deux"
    m = match(pattern + r'(?: avec signature individuelle)?')
    s = source(pattern + r' avec signature individuelle', m)
    if s and int(m['remaining']) > 0 and int(m['received']) > 0 and len({m[k] for k in ('nominal', 'transfer_nominal', 'buyer_nominal')}) == 1:
        rule = 'fr.persons.one_share_transfer_two_managers.v1'
        return [person(rule, m['seller'], role='associé-gérant président', signing='Einzelunterschrift', extra={'action': 'shares_transferred', 'shares_count': int(m['remaining']), 'shares_transferred': 1, 'shares_nominal': m['nominal']}), person(rule, m['buyer'], role='associée-gérante', signing='Einzelunterschrift', extra={'action': 'shares_received', 'shares_count': int(m['received']), 'shares_received': 1, 'shares_nominal': m['nominal']})], ''

    m = match(rf'Auflösung der Genossenschaft durch Konkurs gemäss Konkurserkenntnis des (?P<court>{NAME}) vom (?P<date>{DATE}) mit Wirkung ab dem (?P<effective_date>{DATE}), (?P<time>\d{{2}}\.\d{{2}}) Uhr')
    if m:
        return [event('status_changed', 'de.text.cooperative_dissolved_bankruptcy.v1', **m.groupdict(), action='dissolved_by_bankruptcy')], ''
    return [], leftover
