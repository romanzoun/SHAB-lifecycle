from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, COUNT, UID


def extract_parser337_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete sample-backed residues after all existing rules."""
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
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {**m.groupdict(), 'action': action, **extra})

    def person(action, m, name, role, signing=None, place=None):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **{k: v for k, v in m.groupdict().items() if k not in ('name', 'place')}})

    m = match(rf"L'associé-gérant (?P<holder>{NAME}) cède (?P<transferred_count>{COUNT}) de ses (?P<previous_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à l'associé-gérant (?P<recipient>{NAME}) désormais titulaire de (?P<received_total>{COUNT}) parts de CHF (?P=nominal)\. (?P=holder) reste titulaire de (?P<retained_count>{COUNT}) parts de CHF (?P=nominal)", 'fr')
    if m:
        return [event('share_transfer_between_managers', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf'Mit Verfügung vom (?P<decision_date>{DATE}) hat das (?P<court>{NAME}) im summarischen Verfahren eine Verlängerung der definitiven Nachlassstundung bis zum (?P<extension_until>\d{{1,2}}\. Januar \d{{4}}) gewährt', 'de')
    if m:
        try:
            datetime.strptime(m['extension_until'].replace('Januar', '01'), '%d. %m %Y')
        except ValueError:
            return [], leftover
        return [event('definitive_composition_moratorium_extended', m)], ''

    # A bracketed correction is historical text, never a new capital operation.
    m = match(rf"\[non: Capital-actions réduit de CHF (?P<previous_capital>{MONEY}) à CHF (?P<reduced_capital>{MONEY}) par suite de pertes et destruction de (?P<cancelled_count>{COUNT}) actions au porteur de CHF (?P<nominal>{MONEY})\. Capital-actions reporté simultanément à CHF (?P=previous_capital) par l'émission de (?P=cancelled_count) actions au porteur de CHF (?P=nominal), entièrement libérées par compensation d'une créance de CHF (?P<previous_offset_claim>{MONEY})\.\]", 'fr')
    if m:
        return [event('capital_correction_previous_wording', m, currency='CHF', historical=True)], ''

    m = match(rf'Nouvel administrateur toutefois avec (?P<partner1>{NAME}) ou (?P<partner2>{NAME}): (?P<name>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME})', 'fr')
    if m:
        source = f"Nouvel administrateur avec signature collective à deux, toutefois avec {m['partner1']} ou {m['partner2']}: {m['name']}, du {m['origin']}, à {m['place']}"
        if source not in source_text:
            return [], leftover
        return [person('board_member_restricted_collective_signing', m, m['name'], 'Verwaltungsrat', f"Kollektivunterschrift zu zweien mit {m['partner1']} oder {m['partner2']}", m['place'])], ''

    m = match(rf'Division des (?P<previous_count>{COUNT}) parts de CHF (?P<previous_nominal>{MONEY}) en (?P<split_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) qui sont reparties de la manière suivante: (?P<holder>{NAME}) a (?P=split_count) parts de CHF (?P=nominal)\. (?P=holder) détient désormais (?P<retained_count>{COUNT}) parts de CHF (?P=nominal) par suite de cession de (?P<transferred_count>{COUNT}) parts de CHF (?P=nominal) à (?P<recipient>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé pour (?P=transferred_count) parts de CHF (?P=nominal) sans signature sociale', 'fr')
    if m:
        return [event('share_split_and_transfer', m, 'ownership_changed', currency='CHF'), person('unsigned_associate_joined', m, m['recipient'], 'Gesellschafter', 'ohne Zeichnungsberechtigung', m['place'])], ''

    m = match(rf'L\'associée "(?P<holder>[^"]+)" a cédé (?P<transferred_count>{COUNT}) de ses (?P<previous_count>{COUNT}) parts sociales de CHF (?P<nominal>{MONEY}) à "(?P<recipient>[^"]+)" \(BVI Company Nr\. (?P<registration_number>\d+)\), à (?P<place>{NAME}), (?P<country>{NAME}), nouvelle associée', 'fr')
    if m:
        return [event('corporate_share_transfer', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf"Réduction du capital-actions de CHF (?P<previous_capital>{MONEY}) à CHF (?P<reduced_capital>{MONEY}) par destruction de (?P<cancelled_count>{COUNT}) actions nominatives de CHF (?P<nominal>{MONEY}), pour supprimer un excédent de passifs constaté au bilan\. Augmentation ordinaire simultanée du capital-actions\. Nouveau capital-actions entièrement libéré: (?P<new_capital>{MONEY}), divisé en (?P<new_count>{COUNT}) actions nominatives de CHF (?P=nominal)", 'fr')
    if m:
        return [event('capital_reduction_simultaneous_increase', m, 'capital_changed', currency='CHF')], ''

    m = match(rf'Übernahme der Aktiven und Passiven der (?P<absorbed_name>{NAME}), in (?P<absorbed_place>{NAME}) \((?P<absorbed_uid>{UID})\), gemäss Fusionsvertrag vom (?P<agreement_date>{DATE}) und Fusionsbilanz per (?P<balance_date>{DATE})\. Aktiven von CHF (?P<assets>{MONEY}) und Passiven von CHF (?P<liabilities>{MONEY}) gehen auf die übernehmende Gesellschaft über\. Gemäss Bestätigung der zugelassenen Revisionsexpertin liegen Rangrücktritte im Umfang der Unterdeckung und Überschuldung vor\. Da die übernehmende Gesellschaft sämtliche Aktien der übertragenden Gesellschaft hält, findet weder eine Kapitalerhöhung noch eine Aktienzuteilung statt', 'de')
    if m:
        return [event('subsidiary_merger_subordinated_debt', m, 'company_merged', currency='CHF')], ''

    m = match(rf"Fatti particolari: \. Conferimenti in natura e assunzione di beni: sulla base del contratto del (?P<agreement_date>{DATE}) e del bilancio al (?P<balance_date>{DATE}), che presenta attivi per CHF (?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY}), la società assume attivi e passivi della (?P<transferor>{NAME}), in (?P<place>{NAME}) \((?P<transferor_uid>{UID})\), contro attribuzione di (?P<share_count>{COUNT}) quote sociali da CHF (?P<nominal>{MONEY})\. L'importo di CHF (?P<credit>{MONEY}) verrà iscritto a bilancio quale credito verso la società", 'it')
    if m:
        return [event('contribution_in_kind_and_asset_takeover', m, currency='CHF')], ''

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) opérée le (?P<entry_date>{DATE}) au registre du commerce du canton de (?P<register_canton>{NAME}) \(FOSC du (?P<notice_date>{DATE})\) est complétée par la mention selon laquelle (?P<count>{COUNT}) bons de jouissance donnant droit à une part du bénéfice net selon statuts ont été émis par la société", 'fr')
    if m:
        return [event('profit_participation_certificates_complement', m)], ''

    m = match(rf"Les (?P<count>{COUNT}) actions e CHF (?P<nominal>{MONEY}) nominatives sont maintenant \. Capital-actions: CHF (?P<capital>{MONEY}), entièrement libéré, divisé en (?P=count) actions de CHF (?P=nominal), nominatives, liées selon statuts", 'fr')
    if m:
        return [event('registered_shares_transfer_restricted', m, 'capital_changed', currency='CHF')], ''

    m = match(rf"Nouveaux administrateurs sans signature: (?P<name1>{NAME}), du (?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), et (?P<name3>{NAME}), de (?P<origin3>{NAME}), au (?P<place3>{NAME})", 'fr')
    if m:
        return [person('unsigned_board_members_joined', m, m[f'name{i}'], 'Verwaltungsrat', 'ohne Zeichnungsberechtigung', m[f'place{i}']) for i in range(1, 4)], ''

    return [], leftover
