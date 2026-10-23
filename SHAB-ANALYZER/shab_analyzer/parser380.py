from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, UID
from .parser84 import _FR_BOARD_MEMBERS_PAIR, _FR_BANKRUPTCY_PROCEEDINGS_SUSPENDED_TWO_DATES
from .parser54 import _DE_SPIN_OFF_ACQUISITION

NAME = r'[^,;.()]+?'
DATE = r'\d{2}\.\d{2}\.\d{4}'
FRENCH_MONTHS = ('janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre')
FRENCH_DATE = r'\d{1,2} (?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre) \d{4}'


def extract_parser380_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Bounded new variants; keep legacy patterns and existing events intact."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in (_FR_BOARD_MEMBERS_PAIR, _FR_BANKRUPTCY_PROCEEDINGS_SUSPENDED_TWO_DATES, _DE_SPIN_OFF_ACQUISITION)):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', suffix=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m and suffix and not re.search(re.escape(leftover.rstrip('.')) + suffix + r'\.', source_text):
            return None
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('date'):
                        if re.fullmatch(DATE, value):
                            datetime.strptime(value, '%d.%m.%Y')
                        elif re.fullmatch(FRENCH_DATE, value):
                            day, month, year = value.split()
                            datetime(int(year), FRENCH_MONTHS.index(month) + 1, int(day))
            except ValueError:
                return None
        return m

    def event(action, m, event_type='organization_changed', **extra):
        return _event(*context, event_type, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, place=None, role=None, signing=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, place=place, role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    m = match(rf"L'inscription (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name>{NAME}) reste directeur sans autre restriction")
    if m:
        return [person('notice_director_retained_without_restriction', m, m['name'], role='directeur', corrected=True, unrestricted=True)], ''

    m = match(rf'Abspaltung: Die Gesellschaft übernimmt von der (?P<transferor>{NAME}), neu (?P<transferor_new_name>{NAME}) \((?P<transferor_uid>{UID})\), in (?P<place>{NAME}), einen Teil des Vermögens\. Die Gesellschaft übernimmt dabei gemäss Spaltungsvertrag vom (?P<agreement_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Fremdkapital von CHF (?P<liabilities>{MONEY})\. Da die mitgliedschaftliche Kontinuität gewahrt ist, findet weder eine Kapitalerhöhung noch eine Aktienzuteilung statt', 'de')
    if m:
        return [event('demerger_renamed_transferor_continuity', m, currency='CHF', capital_increased=False, shares_allocated=False)], ''

    m = match(rf"(?P<authority>Le président du Tribunal de l'arrondissement de {NAME}) a prononcé le (?P<decision_date>{FRENCH_DATE}) l'effet suspensif de la procédure de faillite rendue le (?P<bankruptcy_date>{FRENCH_DATE})")
    if m:
        return [event('bankruptcy_suspensive_effect_prior_judgment', m, 'status_changed', suspensive_effect=True)], ''

    m = match(rf"Rectificati: l'inscription no (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que (?P<name1>{NAME}) et (?P<name2>{NAME}) engagent la société par leur procuration collective à deux, toutefois pas entre eux")
    if m:
        return [person('notice_joint_procuration_mutual_exclusion', m, m[f'name{i}'], signing='Kollektivprokura zu zweien', corrected=True, not_with=[m[f'name{3-i}']]) for i in (1, 2)], ''

    m = match(rf"(?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}) \((?P<country>{NAME})\), nouvel associé sans signature, avec (?P=count) parts de CHF (?P=nominal); (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)\. (?P=buyer), représenté par ses parents (?P<parent1>{NAME}) et (?P<parent2>{NAME}), est mineur au moment de l'inscription au registre du commerce")
    if m:
        return [event('partial_shares_transferred_minor_represented', m, currency='CHF'), person('minor_associate_without_signing', m, m['buyer'], m['place'], 'associé', 'ohne Zeichnungsberechtigung', minor=True, representatives=[m['parent1'], m['parent2']])], ''

    m = match(rf'\[Beitrags- oder Leistungspflichten der Genossenschafter gemäss näherer Umschreibung in den Statuten\.\] \[gestrichen: Jeder Genossenschafter ist zur Entrichtung einer Eintrittsgebühr von CHF (?P<previous_fee>{COUNT}\.--) verpflichtet\.\]', 'de')
    if m:
        return [event('cooperative_entry_fee_clause_deleted', m, currency='CHF', entry_fee_clause_deleted=True)], ''

    m = match(rf'Nouveaux membres du conseil de fondation sans signature: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<name2>{NAME}), de et à (?P<place2>{NAME}), et (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), trésorier')
    if m:
        return [person('three_new_foundation_members_unsigned_treasurer', m, m[f'name{i}'], m[f'place{i}'], 'membre du conseil de fondation' + (', trésorier' if i == 3 else ''), 'ohne Zeichnungsberechtigung', origin=m['place2'] if i == 2 else m[f'origin{i}']) for i in (1, 2, 3)], ''

    m = match(rf'Mit dem im SHAB Nr\. (?P<notice_number>\d+) vom (?P<notice_date>{DATE}) publizierten TR-Nr\. (?P<entry>\d+) vom (?P<entry_date>{DATE}) wurde der bisherige Text unvollständig publiziert\. Korrekt wäre: (?P<name>[^,]+, [^,]+), von (?P<origin>{NAME}), in (?P<place>{NAME}), Präsident des Verwaltungsrates, mit Einzelunterschrift \[bisher: in (?P<previous_place>{NAME}), Mitglied des Verwaltungsrates, mit Einzelunterschrift\]', 'de')
    if m:
        return [person('incomplete_notice_board_president_corrected', m, m['name'], m['place'], 'Präsident des Verwaltungsrates', 'Einzelunterschrift', corrected=True)], ''

    m = match(rf'(?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}) et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), sont membres du conseil')
    if m:
        return [person('board_pair_without_comma_before_and', m, m[f'name{i}'], m[f'place{i}'], 'membre du conseil') for i in (1, 2)], ''

    m = match(rf"(?P<seller>{NAME}) a cédé (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) au nouvel associé (?P<buyer>{NAME}), d'(?P<origin>{NAME}), à (?P<place>{NAME})\. Associés-gérants: (?P=seller), président, et (?P=buyer), chacun pour (?P=count) parts de CHF (?P=nominal), tous deux", suffix=' avec signature individuelle')
    if m:
        return [event('shares_transferred_two_individual_managers', m, currency='CHF'), person('transfer_seller_manager_president', m, m['seller'], role='associé-gérant, président', signing='Einzelunterschrift'), person('transfer_buyer_manager', m, m['buyer'], m['place'], 'associé-gérant', 'Einzelunterschrift')], ''

    m = match(rf"Administration: (?P<name1>{NAME}), jusqu'ici en outre directeur, nommé président, et (?P<name2>{NAME}), jusqu'ici sous-directeur, nommé en outre directeur général, continuent à signer individuellement\. Signature collective à deux, avec un administrateur, a été conférée à (?P<name3>{NAME}), jusqu'ici sous-directeur, nommé directeur et (?P<name4>{NAME}), jusqu'ici sous-directrice, nommée directrice; leurs pouvoirs sont modifiés en ce sens")
    if m:
        return [person('administration_management_roles_signing_amended', m, m[f'name{i}'], role=['président', 'administrateur, directeur général', 'directeur', 'directrice'][i-1], signing='Einzelunterschrift' if i < 3 else 'Kollektivunterschrift zu zweien', **({'with_role': 'administrateur'} if i > 2 else {})) for i in (1, 2, 3, 4)], ''

    m = match(rf'Signature individuelle a été conférée au directeur (?P<name>{NAME}); ses pouvoirs sont modifiés en ce sens')
    if m:
        return [person('director_individual_signing_powers_amended', m, m['name'], role='directeur', signing='Einzelunterschrift')], ''
    return [], text
