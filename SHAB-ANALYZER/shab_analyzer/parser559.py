from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event
from .parser267 import DATE, MONEY

_DETAILS = re.compile(
    rf'eingetragenen Einzelunternehmens "(?P<business_name>[^"\n]+)", '
    r'(?P<address>[^,;\n]+), (?P<postal_code>\d{4}) (?P<place>[^,.;\n]+), '
    rf'bestehend aus (?P<goods>[^;\n]+?) zum Preis von CHF (?P<price>{MONEY})\.?'
)
_HEADING = (
    'Sachübernahme: Die Gesellschaft übernimmt bei der Gründung gemäss Vertrag '
    rf'und Inventarliste vom (?P<agreement_date>{DATE}) alle Einrichtungsgegenstände '
    'und den Lagerbestand des nicht im Handelsregister '
)


def extract_parser559_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Complete the evidenced correction of an unregistered trader's asset purchase."""
    if language != 'de':
        return [], text
    match = _DETAILS.fullmatch(text.strip())
    if not match:
        return [], text
    # Require both the corrected clause and its explicitly superseded typo.
    # The legacy qualified-facts event already owns the heading and is preserved.
    tail = text.strip().removesuffix('.') + '.'
    evidence = re.search(
        r'Qualifizierte Tatbestände neu: ' + _HEADING + re.escape(tail)
        + r' \[nicht: ' + _HEADING.replace('(?P<agreement_date>', '(?P<previous_date>')
        .replace('Einrichtungsgegenstände', 'Eintrichtungsgegenstände')
        + re.escape(tail) + r'\]', source_text,
    )
    if not evidence or evidence['agreement_date'] != evidence['previous_date']:
        return [], text
    try:
        datetime.strptime(evidence['agreement_date'], '%d.%m.%Y')
    except ValueError:
        return [], text
    if Decimal(match['price'].replace("'", '')) <= 0:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton, 'statutes_changed',
        'de.text.formation_asset_purchase_inventory_corrected.v1',
        {**match.groupdict(), 'agreement_date': evidence['agreement_date'],
         'action': 'formation_asset_purchase_inventory_corrected',
         'kind': 'asset_acquisition', 'currency': 'CHF', 'corrected': True,
         'transferor_registered': False},
    )], ''
