from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser409 import NAME
from . import parser137, parser120, parser168, parser195, parser204, parser288, parser364

_LEGACY = tuple(p for module in (parser137, parser120, parser168, parser195, parser204)
                for p in vars(module).values() if isinstance(p, re.Pattern))


def extract_parser425_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize bounded residual variants while retaining historical rule ownership."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
        return [], text
    # These historical rules define their patterns locally. Delegate unchanged.
    for old in (parser288.extract_parser288_leftovers, parser364.extract_parser364_leftovers):
        events, rest = old(text, language, publication_id, published_at, org_uid, plz, canton, source_text=source_text)
        if events or rest != text:
            return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language not in ((lang,) if isinstance(lang, str) else lang):
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

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name,
                             role=role, signing=signing, place=place,
                             extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    m = match(rf'(?P<name>{NAME}) est élu administrateur et continue à signer collectivement à deux')
    if m:
        return [person('administrator_elected_continued_collective_signing', m, m['name'], 'administrateur', 'Kollektivunterschrift zu zweien')], ''

    m = match(rf'Nuova sede: (?P<place>{NAME})\. \[La modifica di sede avviene in seguito al cambio di nome del Comune denominato (?P=place)\]', 'it')
    if m:
        return [event('seat_municipality_renamed', m, 'address_changed', municipality_renamed=True)], ''

    m = match(rf"L'associé-gérant (?P<seller>{NAME}) a cédé (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé pour (?P=count) parts de CHF (?P=nominal)\. Gérants: les associés (?P=seller), président, et (?P=buyer), tous deux")
    if m and source_text.endswith(leftover.rstrip('.') + ' avec signature individuelle.'):
        return [event('share_transfer_associate_manager_president_pair', m, 'ownership_changed', currency='CHF'),
                person('associate_manager_president_pair_after_transfer', m, m['seller'], 'gérant et président', 'Einzelunterschrift'),
                person('associate_manager_president_pair_after_transfer', m, m['buyer'], 'gérant', 'Einzelunterschrift', m['place'])], ''

    notice = rf'Der Eintrag Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) \(SHAB vom (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\)'
    m = match(notice + rf' ist wie folgt berichtigt: (?P<name>{NAME}), Kollektivprokura zu zweien, in (?P<place>{NAME}) \(und nicht in (?P<previous_place>{NAME})\)', 'de')
    if m:
        return [person('procuration_residence_corrected_notice', m, m['name'], signing='Kollektivprokura zu zweien', place=m['place'], corrected=True)], ''

    repeated = r'Der Eintrag Nr\. (?P=entry) vom (?P=entry_date) \(SHAB vom (?P=notice_date), Id (?P=notice_id)\)'
    m = match(notice + rf' ist wie folgt berichtigt: (?P<name1>{NAME}), Verwaltungsratsmitglied, Vizepräsident, Kollektivunterschrift zu zweien \(und nicht Verwaltungsratsmitglied, Präsident\)\. ' + repeated + rf' ist wie folgt ergänzt: (?P<name2>{NAME}), Verwaltungsratsmitglied, Vizepräsident, Kollektivunterschrift zu zweien, nun in (?P<place2>{NAME}), neu Verwaltungsratsmitglied, Präsident, Kollektivunterschrift zu zweien', ('de', 'fr'))
    if m:
        return [person('board_vice_president_corrected_notice', m, m['name1'], 'Verwaltungsratsmitglied, Vizepräsident', 'Kollektivunterschrift zu zweien', corrected=True, previous_role='Verwaltungsratsmitglied, Präsident'),
                person('board_president_supplemented_notice', m, m['name2'], 'Verwaltungsratsmitglied, Präsident', 'Kollektivunterschrift zu zweien', m['place2'], previous_role='Verwaltungsratsmitglied, Vizepräsident')], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que (?P<name>{NAME}) est nommé président \(et non (?P<previous_name>{NAME}) comme publié\)")
    if m:
        return [person('president_identity_corrected_notice', m, m['name'], 'président', corrected=True)], ''

    m = match(rf'Das Konkursverfahren wurde mit Entscheid vom (?P<decision_date>{DATE}) des (?P<court>{NAME}) als geschlossen erklärt', 'de')
    if m:
        return [event('bankruptcy_closed_court_after_date', m, 'status_changed', bankruptcy_closed=True)], ''

    m = match(rf'Nouveaux gérants: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}) et (?P<name2>{NAME}), des (?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<region2>[A-Z]{{2}}) (?P<country2>[A-Z]{{3}})')
    if m and source_text.endswith(leftover.rstrip('.') + ' avec signature collective à deux.'):
        return [person('new_managers_second_foreign_state', m, m['name'+i], 'gérant', 'Kollektivunterschrift zu zweien', m['place'+i]) for i in ('1', '2')], ''

    m = match(rf'(?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}) et (?P<name3>{NAME}), de et à (?P<place3>{NAME}), sont membres du conseil, toutes trois sans signature')
    if m:
        return [person('three_council_members_unsigned', m, m['name'+i], 'membre du conseil', 'ohne Zeichnungsberechtigung', m['place'+i]) for i in ('1', '2', '3')], ''

    registry = r'CH-\d{3}\.\d{4,7}(?:\.\d{3})?-\d'
    m = match(rf"Radiation de la mention de l'existence d'une succursale à (?P<place1>{NAME}) \((?P<registry_id1>{registry})\), (?P<place2>{NAME}) \((?P<registry_id2>{registry})\), et (?P<place3>{NAME})")
    if m:
        return [event('three_branch_mentions_removed_legacy_ids', m, mention_removed=True)], ''

    company = r'[^;\n]+?'
    m = match(rf"Nouveau numéro d'identification du siège principal: (?P<head_office_uid>{UID}) \[précédemment: (?P<previous_uid>{UID})\]\. Nouvelles dispositions pour la succursale: Le siège principal de cette succursale, (?P<previous_name>{company}), à (?P<previous_place>{NAME}) \((?P=previous_uid)\), a cessé d'exister à la suite de la fusion avec (?P<absorbing_name>{NAME}) \(nouvellement : (?P<name>{company}), à (?P<place>{NAME}) \((?P=head_office_uid)\)\. Les activités commerciales à (?P<branch_place>{NAME}) sont poursuivies en tant que succursale de (?P=name), à (?P=place) \((?P=head_office_uid)\), conformément à l'art\. 112 ORC", ('fr', 'de'))
    if m:
        return [event('branch_head_office_merger_continuation', m, continues=True)], ''

    # Only a remainder of an explicitly struck historical contribution, never a new transfer.
    m = match(rf'eingetragenen, unter der Bezeichnung "(?P<partnership>{NAME})" geführten Kollektivgesellschaft, in (?P<place>{NAME}), bestehend aus (?P<partners>[^\[\]\n]+?), gemäss Vertrag vom (?P<agreement_date>{DATE}) und Übernahmebilanz per (?P<balance_date>{DATE}) mit übernommenen Aktiven von CHF (?P<assets>{MONEY}(?:\.--)?) und Passiven von CHF (?P<liabilities>{MONEY}(?:\.--)?)\. Barmittel in der Höhe von CHF (?P<excluded_cash>{MONEY}(?:\.--)?) werden nicht übernommen\. Dafür werden (?P<issued_count>{COUNT}) Namenaktien zu CHF (?P<nominal>{MONEY}(?:\.--)?) ausgegeben und (?P<existing_count>{COUNT}) Namenaktien zu CHF (?P=nominal)(?:\.--)?, welche bisher mit CHF (?P<previous_paid>{MONEY}(?:\.--)?) liberiert waren, gelten nun als voll liberiert\.\]', 'de')
    if m and re.search(r'\[gestrichen: Sacheinlage: Die Gesellschaft übernimmt bei der Erhöhung der Liberierung und der Kapitalerhöhung vom ' + DATE + r' gemäss Art\. 181 OR das Geschäft der nicht im Handelsregister ' + re.escape(leftover) + r'\.?$', source_text):
        return [event('deleted_historical_contribution_partnership_detail', m, historical=True, deleted=True, currency='CHF')], ''
    return [], text
