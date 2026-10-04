from __future__ import annotations

import re
import unicodedata

_UID_RE = re.compile(r"CHE-\d{3}\.\d{3}\.\d{3}")
_WS = re.compile(r"\s+")


def fold(text: str | None) -> str:
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_ = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    return _WS.sub(" ", ascii_.lower()).strip()


def person_key(*, name: str, place: str | None = None, uid: str | None = None) -> str:
    if uid and _UID_RE.fullmatch(uid.strip()):
        return f"uid:{uid.strip()}"
    parts = [fold(name)]
    if place:
        parts.append(fold(place))
    return "p:" + "|".join(parts)


def address_key(
    *,
    street: str | None = None,
    house: str | None = None,
    plz: str | None = None,
    town: str | None = None,
    co: str | None = None,
) -> str:
    bits = [fold(co), fold(street), fold(house), fold(plz), fold(town)]
    return "a:" + "|".join(b for b in bits if b)
