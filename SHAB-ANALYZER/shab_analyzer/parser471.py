from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event
from .parser63 import _DE_COMPANY_NAME_CORRECTED
from .parser81 import _DE_UID_CORRECTION

_LEGACY = (_DE_COMPANY_NAME_CORRECTED, _DE_UID_CORRECTION)
_DATE = r'\d{2}\.\d{2}\.\d{4}'
_PURPOSE_REGISTER_ERROR = re.compile(
    rf'Mit der TR-Nr\. (?P<entry>\d+) vom (?P<entry_date>{_DATE}) wurde vom '
    r'Handelsregister (?P<register_place>[^,;.\n]+) ein unzutreffender Zweck der Gesellschaft '
    r'in das Handelsregister eingetragen\. Es handelt sich dabei um ein offensichtliches '
    r'Versehen des Handelsregisters (?P=register_place)\. Der unzutreffende Zweck wurde mit '
    rf'TR-Nr\. (?P<correction_entry>\d+) vom (?P<correction_date>{_DATE}) im Sinne der '
    r'Handelsregisteranmeldung der Gesellschaft berichtigt\.?'
)


def extract_parser471_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Record an official register error correction without inventing purpose wording."""
    if language != 'de' or any(p.fullmatch(text.strip()) for p in _LEGACY):
        return [], text
    match = _PURPOSE_REGISTER_ERROR.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        for key in ('entry_date', 'correction_date'):
            datetime.strptime(match[key], '%d.%m.%Y')
    except ValueError:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'organization_changed', 'de.text.purpose_register_error_corrected.v1',
        {'action': 'purpose_register_error_corrected', **match.groupdict()},
    )], ''
