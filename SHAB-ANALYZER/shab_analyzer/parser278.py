from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY


def extract_parser278_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete sample-backed clauses; preserve unsupported residue."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang, source=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m:
            return None
        if source:
            s = re.search(source + r'\.?$', source_text)
            if not s or any(s[k] != v for k, v in m.groupdict().items()):
                return None
            m = s
        try:
            for k, v in m.groupdict().items():
                if k.endswith('date'):
                    datetime.strptime(v, '%d.%m.%Y')
        except ValueError:
            return None
        return m

    def person(rule, name, event_type='officer_changed', **kw):
        return _person_event(*context, event_type, rule, name, **kw)

    def event(rule, **payload):
        return _event(*context, 'organization_changed', rule, payload)

    def num(value):
        return Decimal(value.replace("'", ''))

    m = match(rf"(?P<name>{NAME}), dont la procuration est éteinte, est nommé sous-directeur et engage désormais la société par sa signature collective à deux", 'fr')
    if m:
        return [person('fr.persons.procuration_ended_deputy_director.v1', m['name'], role='sous-directeur', signing='Kollektivunterschrift zu zweien', extra={'procuration_ended': True})], ''

    m = match(rf"L'inscription n°(?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est complétée en ce sens que l'administrateur (?P<name>{NAME}) est président du conseil d'administration", 'fr')
    if m:
        return [person('fr.persons.administrator_presidency_supplement.v1', m['name'], role='administrateur président', extra={'supplement': True, 'entry': m['entry'], 'entry_date': m['entry_date']})], ''

    m = match(rf"L'inscription n°(?P<entry>{COUNT}) est rectifiée en ce sens que l'associée porte le nom de (?P<name>[^;]+?) \(RSIN (?P<rsin>\d{{9}})\)", 'fr')
    if m:
        return [person('fr.persons.corporate_associate_name_corrected_rsin.v1', m['name'], role='associée', extra={'correction': True, 'entry': m['entry'], 'rsin': m['rsin']})], ''

    p = rf"Persona iscritta corretta: (?P<surname>{NAME}), (?P<given>{NAME}), cittadino (?P<nationality>{NAME}), in (?P<place>{NAME}), socio, senza diritto di firma, con (?P<shares>{COUNT}) quote da CHF (?P<nominal>{MONEY})"
    m = match(p, 'it', p + rf' \[no: (?P<previous_surname>{NAME}), (?P=given)\]')
    if m and num(m['shares']) > 0 and num(m['nominal']) > 0:
        return [person('it.persons.associate_name_corrected_unsigned_shares.v1', m['surname']+' '+m['given'], role='socio', place=m['place'], extra={'correction': True, 'previous_name': m['previous_surname']+' '+m['given'], 'nationality': m['nationality'], 'without_signature': True, 'shares': int(num(m['shares'])), 'share_nominal': m['nominal']})], ''

    p = rf"(?P<name1>{NAME}) et (?P<name2>{NAME}) ont cédé (?P<transferred>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<name3>{NAME}), de et à (?P<place>{NAME}), nouvel associé pour (?P<received>{COUNT}) parts de CHF (?P=nominal); par conséquent (?P=name1) et (?P=name2) sont maintenant chacun associé pour (?P<remaining>{COUNT}) parts de CHF (?P=nominal)\. L'associé (?P=name3) est en outre nommé gérant"
    m = match(p + ' avec signature collective à deux', 'fr')
    if m and num(m['transferred']) == num(m['received']) and all(num(m[k]) > 0 for k in ('nominal', 'received', 'remaining')):
        rule = 'fr.persons.two_holders_transfer_appointed_manager.v1'
        return [person(rule, m['name'+str(i)], role='associé', extra={'shares': int(num(m['remaining'])), 'share_nominal': m['nominal']}) for i in (1, 2)] + [person(rule, m['name3'], role='associé-gérant', place=m['place'], signing='Kollektivunterschrift zu zweien', extra={'origin': m['place'], 'shares': int(num(m['received'])), 'share_nominal': m['nominal']})], ''

    m = match(rf"L'associé-gérant et président (?P<name1>{NAME}) cède (?P<transferred>{COUNT}) de ses (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<name2>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée sans signature\. (?P=name1) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)", 'fr')
    if m and num(m['nominal']) > 0 and 0 < num(m['transferred']) < num(m['previous']) and num(m['remaining']) == num(m['previous'])-num(m['transferred']):
        rule = 'fr.persons.president_transfer_unsigned_associate.v1'
        return [person(rule, m['name1'], role='associé-gérant et président', extra={'shares': int(num(m['remaining'])), 'transferred_shares': int(num(m['transferred'])), 'share_nominal': m['nominal']}), person(rule, m['name2'], role='associée', place=m['place'], extra={'origin': m['origin'], 'shares': int(num(m['transferred'])), 'share_nominal': m['nominal'], 'without_signature': True})], ''

    p = rf"L'associé-gérant (?P<name1>{NAME}) a cédé (?P<count2>{COUNT}) parts de CHF (?P<nominal>{MONEY}) au gérant (?P<name2>{NAME}), maintenant domicilié à (?P<place2>{NAME}), nouvel associé pour (?P=count2) parts de CHF (?P=nominal) et (?P<count3>{COUNT}) parts de CHF (?P=nominal) à (?P<name3>{NAME}), du (?P<origin3>{NAME}), à (?P<place3>{NAME}), (?P<country3>[A-Z]), nouvel associé pour (?P=count3) parts de CHF (?P=nominal); "
    m = match(p + "n'exerce pas la signature sociale", 'fr', p + "il n'exerce pas la signature sociale")
    if m and all(num(m[k]) > 0 for k in ('nominal', 'count2', 'count3')):
        rule = 'fr.persons.manager_transfer_two_associates.v1'
        return [person(rule, m['name1'], role='associé-gérant', extra={'transferred_shares': int(num(m['count2'])+num(m['count3'])), 'share_nominal': m['nominal']}), person(rule, m['name2'], role='associé-gérant', place=m['place2'], extra={'received_shares': int(num(m['count2'])), 'share_nominal': m['nominal']}), person(rule, m['name3'], role='associé', place=m['place3'], extra={'origin': m['origin3'], 'country': m['country3'], 'received_shares': int(num(m['count3'])), 'share_nominal': m['nominal'], 'without_signature': True})], ''

    m = match(rf"Radiation de la restriction statutaire de transmissibilité des (?P<count>{COUNT}) actions de CHF (?P<nominal>{MONEY}), nominatives \(art\. 685a, al 3 CO\)\. Liquidateurs: les administrateurs (?P<name1>{NAME}), (?P<name2>{NAME}), (?P<name3>{NAME}) et (?P<name4>{NAME}), lesquels continuent à signer collectivement à deux", 'fr')
    if m and num(m['count']) > 0 and num(m['nominal']) > 0:
        rule = 'fr.persons.administrators_liquidators_restrictions_removed.v1'
        return [event(rule, action='share_transfer_restrictions_removed', count=m['count'], nominal=m['nominal'], legal_basis='art. 685a, al 3 CO')] + [person(rule, m['name'+str(i)], role='administrateur liquidateur', signing='Kollektivunterschrift zu zweien', extra={'signing_continued': True}) for i in (1, 2, 3, 4)], ''

    m = match(rf"Signature collective à deux, sauf entre eux et sauf avec (?P<excluded>{NAME}(?:, {NAME})* et {NAME}), a été conférée à (?P<name1>{NAME}), du (?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<name2>{NAME}), d'(?P<origin2>{NAME}), à (?P<place2>{NAME}) et (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME})", 'fr')
    if m:
        excluded = re.split(r', | et ', m['excluded'])
        return [person('fr.persons.three_signers_mutual_and_named_exclusions.v1', m['name'+str(i)], place=m['place'+str(i)], signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin'+str(i)], 'signing_excluded_partners': excluded, 'signing_excluded_among_group': [m['name'+str(j)] for j in (1, 2, 3) if j != i]}) for i in (1, 2, 3)], ''

    # The added members have a bounded list grammar, including initials and a country code.
    member = r"(?P<name>[^,;]+?), (?:de |d'|du )(?P<origin>[^,;]+?), (?:à |au )(?P<place>[^,;]+?)(?:, (?P<country>[A-Z]{3}))?"
    m = match(r"(?P<removed>[^.;]+?) ne sont plus membres du conseil de fondation\. (?P<added>.+) sont membres du conseil de fondation sans signature", 'fr')
    if m:
        added = m['added'].removesuffix(',').replace(' et ', ', ')
        members = []
        position = 0
        while position < len(added):
            entry = re.match(member + r'(?=, |$)', added[position:])
            if not entry:
                break
            members.append(entry.groupdict())
            position += entry.end()
            if position < len(added):
                position += 2
        if position == len(added) and members:
            rule = 'fr.persons.foundation_members_replaced_unsigned.v1'
            removed = re.split(r', | et ', m['removed'])
            return [person(rule, name, event_type='officer_removed', role='membre du conseil de fondation') for name in removed] + [person(rule, item['name'], role='membre du conseil de fondation', place=item['place'], extra={'origin': item['origin'], 'country': item['country'], 'without_signature': True}) for item in members], ''

    m = match(rf"Par décision présidentielle du (?P<decision_date>{DATE}) du (?P<court>{NAME}), l'effet suspensif est accordé au recours formé contre la décision de faillite du (?P<bankruptcy_date>{DATE}) \(rectificatif de la décision du (?P<corrected_date>{DATE})\)\. \[biffé: Par décision du (?P=corrected_date) prononcée par le (?P<previous_court>{NAME}), le titulaire de cette entreprise individuelle a été déclaré en faillite avec effet le (?P<effective_date>{DATE}) à (?P<hour>\d{{2}})h(?P<minute>\d{{2}})\]", 'fr')
    if m and int(m['hour']) < 24 and int(m['minute']) < 60:
        return [event('fr.text.bankruptcy_appeal_suspended_corrected.v1', action='bankruptcy_suspended', correction=True, previous_effective_time=m['hour']+':'+m['minute'], **m.groupdict())], ''

    m = match(r'Nachträgliche Liste des Belegs', 'de', r'Nachtrag zum im SHAB Nr\. (?P<notice_number>\d+) vom (?P<notice_date>'+DATE+r') publizierten TR-Eintrag Nr\. (?P<entry>\d+) vom (?P<entry_date>'+DATE+r') [^.]+? - [^,]+, in [^,]+, CHE-\d{3}\.\d{3}\.\d{3}, Einzelunternehmen \(SHAB Nr\. \d+ vom '+DATE+r', Publ\. \d+\)\. Nachträgliche Liste des Belegs')
    if m:
        return [event('de.text.document_list_supplement.v1', action='document_list_supplement', **m.groupdict())], ''

    return [], leftover
