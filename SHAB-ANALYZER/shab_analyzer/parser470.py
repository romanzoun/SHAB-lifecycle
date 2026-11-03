from __future__ import annotations

import re

from .parser253 import _event
from .parser208 import _DE_HEAD_OFFICE_MERGER_BRANCH_CONTINUES
from .parser219 import _DE_BRANCH_CONTINUED_AFTER_HEAD_OFFICE_MERGER as _OLD_MERGER
from .parser229 import _DE_BRANCH_CONTINUED_AFTER_HEAD_OFFICE_MERGER as _OLD_CORRECTION

_LEGACY = (_DE_HEAD_OFFICE_MERGER_BRANCH_CONTINUES, _OLD_MERGER, _OLD_CORRECTION)
_UID = r'CHE-\d{3}\.\d{3}\.\d{3}'
_SUCCESSOR = (
    r'(?P<successor>[^(),]+) \(bisher: (?P<previous_successor_name>[^()]+)\), '
    rf'in (?P<successor_place>[^(),]+) \((?P<successor_uid>{_UID})\)'
    r' wird die Zweigniederlassung gemäss Art\. 112 HRegV als Zweigniederlassung der '
    r'(?P=successor) weitergeführt'
)
_RESIDUE = re.compile(r'Angaben zur , mit der ' + _SUCCESSOR + r'\.?$')
_SOURCE = re.compile(
    r'Angaben zur Zweigniederlassung neu: Infolge Fusion der '
    rf'(?P<absorbed>[^(),]+), in (?P<absorbed_place>[^(),]+) \((?P<absorbed_uid>{_UID})\), '
    r'mit der ' + _SUCCESSOR + r'\. \[nicht: [^\[\]]+\.?\]'
)


def extract_parser470_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recover the evidenced branch continuation after upstream fusion extraction."""
    if language != 'de' or any(pattern.fullmatch(text.strip()) for pattern in _LEGACY):
        return [], text
    residue = _RESIDUE.fullmatch(text)
    if not residue or not source_text.startswith('Berichtigung des im SHAB '):
        return [], text
    source = _SOURCE.search(source_text)
    if not source or residue.groupdict() != {key: source[key] for key in residue.groupdict()}:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'branch_changed', 'de.text.branch_continuation_corrected_successor.v1',
        {'action': 'business_continued_as_branch', **residue.groupdict(),
         'legal_basis': 'Art. 112 HRegV', 'corrected': True},
    )], ''
