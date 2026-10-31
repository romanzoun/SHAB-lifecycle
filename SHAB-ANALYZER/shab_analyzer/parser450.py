from __future__ import annotations

import re
from datetime import datetime

from .parser191 import _DE_DEFINITIVE_MORATORIUM_WITH_COMMISSIONER_HISTORY
from .parser238 import _FR_SIMPLE_ASSOCIATE_SHARE_TRANSFER
from .parser253 import _event, _person_event
from .parser267 import COUNT, DATE, MONEY, NAME, UID

LEGACY = (_DE_DEFINITIVE_MORATORIUM_WITH_COMMISSIONER_HISTORY,
          _FR_SIMPLE_ASSOCIATE_SHARE_TRANSFER)


def extract_parser450_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume only complete evidenced variants, leaving historical rules intact."""
    if any(pattern.search(text.strip()) for pattern in LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', text.strip())
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat das (?P<authority>{NAME}) die provisorische Nachlassstundung bis zum (?P<until_date>{DATE}) bewilligt\. Die (?P<commissioner>{NAME}) \((?P<commissioner_uid>{UID})\), in (?P<commissioner_place>{NAME}), wurde als provisorische Sachwalterin eingesetzt \(Mandatsleiter: (?P<leader1>[^();]+?) und (?P<leader2>[^();]+?)\)', 'de')
    if m:
        payload = dict(m.groupdict())
        for key in ('decision_date', 'until_date'):
            payload[key] = datetime.strptime(payload[key], '%d.%m.%Y').date().isoformat()
        return [
            _event(*context, 'status_changed', 'de.text.provisional_moratorium_two_mandate_leaders.v1', {**payload, 'kind': 'composition_moratorium_granted', 'action': 'granted', 'moratorium_type': 'provisional'}),
            _person_event(*context, 'officer_changed', 'de.persons.provisional_commissioner_two_mandate_leaders.v1', m['commissioner'], place=m['commissioner_place'], role='provisorische Sachwalterin', extra={**payload, 'action': 'appointed'}),
        ], ''

    m = match(rf'(?P<seller>{NAME}) cède (?P<count>1) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) au gérant (?P<buyer>{NAME}), nouvel associé, avec 1 part de CHF (?P=nominal)\. (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)', 'fr')
    if m:
        if int(m['before'].replace("'", '')) != 1 + int(m['remaining'].replace("'", '')):
            return [], text
        return [_event(*context, 'ownership_changed', 'fr.text.single_share_transfer_existing_manager_comma.v1', {**m.groupdict(), 'action': 'partial_transfer', 'currency': 'CHF'})], ''

    m = match(rf"Par jugement du (?P<authority>Tribunal de première instance) du (?P<decision_date>{DATE}), l'inscription (?P<cancelled_entry>{COUNT}) du (?P<cancelled_entry_date>{DATE}) est définitivement radiée et l'inscription (?P<confirmed_entry>{COUNT}) du (?P<confirmed_entry_date>{DATE}) est confirmée", 'fr')
    if m:
        payload = dict(m.groupdict())
        for key in ('decision_date', 'cancelled_entry_date', 'confirmed_entry_date'):
            payload[key] = datetime.strptime(payload[key], '%d.%m.%Y').date().isoformat()
        return [_event(*context, 'publication_corrected', 'fr.text.judgment_entry_cancelled_other_confirmed.v1', {**payload, 'kind': 'registration_cancelled', 'action': 'registration_cancelled_and_confirmed'})], ''
    return [], text
