from __future__ import annotations


def extract_parser500_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Keep historical formulations with their owners.

    Version 500 fixes late routing to parser80 in parse.py. No new syntax or
    payload is introduced: the exposed clause is already owned by parser80.
    """
    return [], text
