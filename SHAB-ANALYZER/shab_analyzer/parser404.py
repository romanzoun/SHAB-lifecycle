from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from . import parser118, parser133, parser149, parser157, parser207, parser213

NAME = r'[^,;.\[\]\n]+?'
_LEGACY = tuple(p for module in (parser118, parser133, parser149, parser157, parser207, parser213)
                for p in vars(module).values() if isinstance(p, re.Pattern))


def extract_parser404_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Sample-backed residual clauses; earlier events and rule ownership are retained."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', evidence=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m:
            return None
        if evidence:
            source = re.search(r'(?<!\S)' + evidence + r'\.(?:\s|$)', source_text)
            if not source or any(source.groupdict().get(k) != v for k, v in m.groupdict().items()):
                return None
        try:
            for date in re.findall(DATE, m[0]):
                datetime.strptime(date, '%d.%m.%Y')
        except ValueError:
            return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, kind='officer_changed', **extra):
        return _person_event(*context, kind, f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    m = match(rf'Gelöschte Person: (?P<removed>{NAME}), Verwaltungsratsmitglied, Einzelunterschrift\. Neu eingetragene Person: (?P<name>{NAME}), deutscher Staatsangehöriger, in (?P<place>{NAME}), Verwaltungsratsmitglied, Einzelunterschrift')
    if m:
        return [person('board_replacement_german_national_fr_xml', m, m['removed'], 'Verwaltungsratsmitglied', 'Einzelunterschrift', kind='officer_removed'), person('board_replacement_german_national_fr_xml', m, m['name'], 'Verwaltungsratsmitglied', 'Einzelunterschrift', m['place'], nationality='deutscher Staatsangehöriger')], ''

    m = match(rf'Mit Verfügung vom (?P<decision_date>{DATE}) hat der Konkursrichter des (?P<court>{NAME}) über die Gesellschaft mit Wirkung ab dem (?P<effective_date>{DATE}), (?P<time>(?:[01]\d|2[0-3])\.[0-5]\d) Uhr, den Konkurs eröffnet; demnach ist die Gesellschaft aufgelöst', 'de')
    if m:
        return [event('company_bankruptcy_order_dissolution', m, dissolved=True)], ''

    m = match(rf'Fatti particolari: Compensazione crediti: CHF (?P<setoff>{MONEY}), contro attribuzione di (?P<count>{COUNT}) quote da CHF (?P<nominal>{MONEY})', 'it')
    if m:
        return [event('credit_setoff_quotas', m, 'capital_changed', currency='CHF')], ''

    m = match(rf"Par prononcé rendu le (?P<day>\d{{1,2}}) janvier (?P<year>\d{{4}}), le président du (?P<court>Tribunal de l'arrondissement de Lausanne) a accordé à la société un sursis concordataire définitif de six mois échéant le (?P<until_day>\d{{1,2}}) juin (?P<until_year>\d{{4}})\. (?P<name>{NAME}), d'(?P<origin>{NAME}), à (?P<place>{NAME}), est inscrit en qualité de commissaire au sursis")
    if m:
        try:
            decision = datetime(int(m['year']), 1, int(m['day']))
            until = datetime(int(m['until_year']), 6, int(m['until_day']))
        except ValueError:
            return [], text
        if until < decision:
            return [], text
        return [event('definitive_moratorium_six_months_commissioner', m, provisional=False, months=6, decision_date=decision.strftime('%d.%m.%Y'), until_date=until.strftime('%d.%m.%Y')), person('moratorium_commissioner_registered', m, m['name'], 'commissaire au sursis', place=m['place'])], ''

    m = match(rf'\[Nachtrag zum Eintrag des Konkurswiderrufs vom (?P<revocation_date>{DATE}): Anlässlich des Eintrags des Konkurswiderrufs wurde die Bemerkung zur Konkurseröffnung nicht gestrichen:\] \[gestrichen: Mit Entscheid vom (?P<decision_date>{DATE}) hat das (?P<court>{NAME}) den Konkurs über den Inhaber dieses Einzelunternehmens mit Wirkung ab dem (?P<effective_date>{DATE}), (?P<time>(?:[01]\d|2[0-3])\.[0-5]\d) Uhr, eröffnet\.\]', 'de')
    if m:
        return [event('bankruptcy_revocation_annotation_removed', m, bankruptcy_entry_removed=True)], ''

    m = match(rf'(?P<name1>{NAME}), qui est maintenant à (?P<place1>{NAME}), est nommé président\. Nouvel administrateur averc signature individuelle: (?P<name2>{NAME}), de (?P<origin>{NAME}), à (?P<place2>{NAME})')
    if m:
        return [person('president_residence_changed', m, m['name1'], 'président', place=m['place1']), person('new_administrator_signing_typo', m, m['name2'], 'administrateur', 'Einzelunterschrift', m['place2'])], ''

    m = match(rf'(?P<name>{NAME}) est élu trésorier et continue à signer collectivement à deux')
    if m:
        return [person('treasurer_elected_continued_signing', m, m['name'], 'trésorier', 'Kollektivunterschrift zu zweien', signing_continued=True)], ''

    m = match(rf"La succursale d'(?P<previous_place>{NAME}) \((?P<branch_uid>{UID})\) a transféré son siège à (?P<place>{NAME}) \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>{COUNT})\)")
    if m:
        return [event('branch_seat_transfer_notice_reference', m)], ''

    pattern = rf'Gelöschte Person: (?P<name>{NAME}), Kollektivprokura zu zweien mit einem Verwaltungsratsmitglied'
    m = match('mit einem Verwaltungsratsmitglied', evidence=pattern)
    if m:
        evidence = re.search(pattern, source_text)
        return [person('removed_proxy_signing_restriction', evidence, evidence['name'], signing='Kollektivprokura zu zweien', kind='officer_removed', signing_restriction='mit einem Verwaltungsratsmitglied')], ''

    pattern = rf'Les associés-gérants (?P<seller1>{NAME}), (?P<seller2>{NAME}), (?P<seller3>{NAME}) et (?P<seller4>{NAME}) cèdent chacun (?P<transferred>{COUNT}) de leurs (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé-gérant titulaire de (?P<received>{COUNT}) parts de CHF (?P=nominal)\. (?P=seller1), (?P=seller2), (?P=seller3) et (?P=seller4) restent chacun titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)'
    m = match(pattern, evidence=pattern.replace('nouvel associé-gérant titulaire', 'nouvel associé-gérant avec signature collective à deux, titulaire'))
    if m:
        n = lambda k: Decimal(m[k].replace("'", ''))
        if n('transferred') * 4 == n('received') and n('previous') - n('transferred') == n('remaining'):
            return [event('four_managers_share_transfer', m, 'ownership_changed', currency='CHF'), person('new_manager_joint_signing_four_sellers', m, m['buyer'], 'associé-gérant', 'Kollektivunterschrift zu zweien', m['place'])], ''

    pattern = rf"L'associé (?P<name1>{NAME}) est maintenant titulaire de (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}), suite à la cession de (?P<transferred>{COUNT}) parts de CHF (?P=nominal) à (?P<name2>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée pour (?P=transferred) parts de CHF (?P=nominal)\. Gérants: les associés (?P=name1), nommé président, et (?P=name2), tous deux"
    m = match(pattern, evidence=pattern + ' avec signature individuelle')
    if m:
        return [event('associate_transfer_two_managers', m, 'ownership_changed', currency='CHF'), person('associate_manager_president_appointed', m, m['name1'], 'associé, gérant président', 'Einzelunterschrift'), person('associate_manager_appointed', m, m['name2'], 'associée, gérante', 'Einzelunterschrift', m['place'])], ''

    m = match(rf"Les administratrices (?P<name1>{NAME}), nommée présidente, et (?P<name2>{NAME}), jusqu'ici présidente, continuent à signer collectivement à deux")
    if m:
        return [person('female_board_presidency_changed', m, m[f'name{i}'], 'administratrice, présidente' if i == 1 else 'administratrice', 'Kollektivunterschrift zu zweien', previous_role=None if i == 1 else 'présidente', signing_continued=True) for i in (1, 2)], ''
    return [], text
