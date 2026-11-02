from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from .parser58 import _FR_SHARE_SPLIT, extract_parser58_leftovers

_FR_COMPLEMENTED_SHARE_SPLIT = re.compile(
    r"L'inscription no (?P<entry>[\d']+) du (?P<entry_date>\d{2}\.\d{2}\.\d{4}) "
    r"est complétée en ce sens que les (?P<from_count>[\d']+) actions de CHF "
    r"(?P<from_nominal>[\d'.]+) ont été divisées en (?P<to_count>[\d']+) "
    r"actions de CHF (?P<to_nominal>[\d'.]+)\. Capital-actions: CHF "
    r"(?P<total>[\d'.]+), libéré à concurrence de CHF (?P<paid>[\d'.]+), "
    r"divisé en (?P=to_count) actions de CHF (?P=to_nominal), nominatives\.?"
)


def extract_parser462_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    if language != 'fr' or _FR_SHARE_SPLIT.search(text):
        return [], text
    match = _FR_COMPLEMENTED_SHARE_SPLIT.fullmatch(text.strip())
    if not match:
        return [], text
    amount = lambda key: Decimal(match[key].replace("'", ''))
    try:
        entry_date = datetime.strptime(match['entry_date'], '%d.%m.%Y').date().isoformat()
        valid = (0 < amount('from_count') < amount('to_count')
                 and amount('to_nominal') > 0
                 and amount('from_count') * amount('from_nominal')
                 == amount('to_count') * amount('to_nominal') == amount('total')
                 and 0 <= amount('paid') <= amount('total'))
    except (ValueError, InvalidOperation):
        return [], text
    if not valid:
        return [], text
    canonical = (
        f"Division des {match['from_count']} actions de CHF {match['from_nominal']}, "
        f"nominatives, en {match['to_count']} actions de CHF {match['to_nominal']}, "
        f"nominatives. Capital-actions: CHF {match['total']}, libéré à concurrence "
        f"de CHF {match['paid']}, divisé en {match['to_count']} actions de CHF "
        f"{match['to_nominal']}, nominatives"
    )
    events, rest = extract_parser58_leftovers(
        canonical, language, publication_id, published_at, org_uid, plz, canton)
    if len(events) != 1 or rest.strip(' .'):
        return [], text
    events[0].rule_id = 'fr.text.share_split_entry_complemented.v1'
    events[0].payload.update(entry=match['entry'], entry_date=entry_date)
    return events, ''
