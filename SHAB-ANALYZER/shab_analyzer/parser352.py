from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser352_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Append supported residual facts without replacing earlier events."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('_date'):
                        datetime.strptime(value, '%d-%m-%Y' if '-' in value else '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, **extra):
        return _event(*context, 'organization_changed', f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **m.groupdict(), **extra, 'name': name})

    m = match(rf"L'associé-gérant (?P<name1>{NAME}) a cédé (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) au nouvel associé (?P<name2>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME}), lequel est en outre nommé gérant (?P=name1), nommé président, est désormais titulaire de (?P<remaining_count>{COUNT}) parts de CHF (?P=nominal) et continue de signer individuellement")
    if m and all(Decimal(m[k].replace("'", '')) > 0 for k in ('count', 'nominal', 'remaining_count')):
        return [event('associate_transfer_manager_president', m, currency='CHF'), person('associate_manager_president_continued_signing', m, m['name1'], 'Vorsitzender der Geschäftsführung', 'Einzelunterschrift'), person('new_associate_manager_appointed', m, m['name2'], 'Geschäftsführer', place=m['place'])], ''

    m = match(rf'Les membres du conseil de fondation (?P<name1>{NAME}), (?P<name2>{NAME}), (?P<name3>{NAME}) et (?P<name4>{NAME}), signent désormais collectivement à deux, sans restriction\. La secrétaire générale (?P<name5>{NAME}), signent désormais collectivement à deux, sans restriction')
    if m:
        return [person('foundation_officers_unrestricted_collective_signing', m, m[f'name{i}'], 'Stiftungsrat' if i < 5 else 'Generalsekretärin', 'Kollektivunterschrift zu zweien', signing_restrictions_removed=True) for i in range(1, 6)], ''

    m = match(r"L'inscription (?P<entry>\d+) du (?P<entry_date>\d{2}-\d{2}-\d{4}) \(FOSC du (?P<notice_date>\d{2}-\d{2}-\d{4}), p\. (?P<notice_ref>\d+/\d+)\) est complétée en ce sens que la mention relative à l'obligation de fournir des prestations accessoires, droits de préférence, de préemption ou d'emption selon statuts est supprimée")
    if m:
        return [event('ancillary_obligations_mention_deleted_correction', m)], ''

    m = match(rf"Selon contrat de transfert de patrimoine du (?P<agreement_date>{DATE}), le titulaire a transféré certains actifs pour CHF (?P<assets>{MONEY}) à la société à responsabilité limitée (?P<recipient>{NAME}), (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Contre-prestation: une créance de CHF (?P<consideration>{MONEY}) en faveur de l'apporteur")
    if m:
        return [event('sole_proprietor_assets_transferred_for_claim', m, currency='CHF')], ''

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat das (?P<court>{NAME}) die COVID-19-Stundung um (?P<months>\d+) Monate bis am (?P<end_date>{DATE}) verlängert', 'de')
    if m:
        return [event('covid_moratorium_extended', m)], ''

    m = match(rf'Les membres du conseil de fondation (?P<name1>{NAME}), (?P<name2>{NAME}) et (?P<name3>{NAME}) sont inscrits en qualité de liquidateurs')
    if m:
        return [person('foundation_board_members_liquidators', m, m[f'name{i}'], 'Liquidator', previous_role='membre du conseil de fondation') for i in range(1, 4)], ''

    # French month names are validated as dates, while preserving their source form.
    written_date = r'\d{1,2} (?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre) \d{4}'
    m = match(rf"Par décision du (?P<court>{NAME}) du (?P<decision_written>{written_date}), la présidente a révoqué l'effet suspensif accordé le (?P<suspension_written>{written_date}), confirmé que la faillite de la société et dit que celle-ci prend effet le (?P<effective_written>{written_date}) à (?P<time>\d{{2}}h\d{{2}})")
    if m:
        months = 'janvier février mars avril mai juin juillet août septembre octobre novembre décembre'.split()
        try:
            for key in ('decision_written', 'suspension_written', 'effective_written'):
                day, month, year = m[key].split()
                datetime(int(year), months.index(month)+1, int(day))
            datetime.strptime(m['time'], '%Hh%M')
        except ValueError:
            return [], leftover
        return [event('bankruptcy_suspensive_effect_revoked', m)], ''

    m = match(rf'Die mit Verfügung der Aufsichtsbehörde vom (?P<exemption_date>{DATE}) gewährte Befreiung von der Revisionsstellenpflicht wird mit Verfügung der Aufsichtsbehörde vom (?P<revocation_date>{DATE}) widerrufen\. \[bisher: Die Stiftung wurde mit Verfügung der Aufsichtsbehörde vom (?P=exemption_date) von der Pflicht befreit, eine Revisionsstelle zu bezeichnen\.\]', 'de')
    if m:
        return [event('foundation_auditor_exemption_revoked', m)], ''

    m = match(rf'(?P<name>{NAME}), nommé directeur, est maintenant originaire de (?P<origin>{NAME})')
    if m:
        return [person('director_appointed_origin_changed', m, m['name'], 'Direktor', origin=m['origin'])], ''

    # Earlier translation parsing stops at the period in Ltd. Require full context.
    if language == 'de' and leftover == 'Ltd)':
        m = re.search(r'Uebersetzungen der Firma neu: \((?P<translation>[^.]+ Ltd)\)\.?$', source_text)
        if m:
            return [event('company_translation_complete', m)], ''

    m = match(rf"Radiation de la mention de l'existence d'une succursale à (?P<deleted_branches>{NAME}), (?P<deleted_registered_branch>{NAME}) \((?P<deleted_register>CH-\d{{3}}\.\d{{4}}\.\d{{3}}-\d)\), (?P<deleted_other>{NAME}) et (?P<deleted_last>{NAME})\. La succursale de (?P<previous_place>{NAME}) a transféré son siège à (?P<place>{NAME}) \((?P<branch_uid>{UID})\)")
    if m:
        return [event('branch_mentions_deleted_and_seat_transferred', m)], ''

    m = match(rf"Fusione: ripresa di attivi e passivi di (?P<absorbed_name>{NAME}), in (?P<absorbed_place>{NAME}) \((?P<absorbed_uid>{UID})\), secondo contratto di fusione del (?P<agreement_date>{DATE}) e bilancio al (?P<balance_date>{DATE}), che presenta attivi per CHF (?P<assets>{MONEY}), e passivi verso terzi per CHF (?P<liabilities>{MONEY})\. Conformemente all'attestazione di un perito revisore abilitato, la società assuntrice dispone di fondi propri liberamente disponibili equivalenti almeno all'ammontare dello scoperto\. La società assuntrice detiene tutte le azioni della società trasferente, per cui la fusione avviene senza aumento del capitale e senza attribuzione di azioni", 'it')
    if m:
        return [event('merger_wholly_owned_available_equity_attestation', m, currency='CHF', capital_increased=False, shares_allocated=False)], ''

    return [], leftover
