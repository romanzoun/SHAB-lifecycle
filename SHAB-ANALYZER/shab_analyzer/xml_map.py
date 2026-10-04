from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from .keys import address_key
from .models import Event


def _ln(tag: str) -> str:
    return tag.split("}", 1)[-1]


def _child(el: ET.Element | None, name: str) -> ET.Element | None:
    if el is None:
        return None
    for child in el:
        if _ln(child.tag) == name:
            return child
    return None


def _text(el: ET.Element | None) -> str | None:
    if el is None or el.text is None:
        return None
    value = el.text.strip()
    return value or None


def _find(root: ET.Element, *path: str) -> ET.Element | None:
    current: ET.Element | None = root
    for name in path:
        current = _child(current, name)
        if current is None:
            return None
    return current


def _company_snapshot(block: ET.Element | None) -> dict:
    company = _child(block, "company") if block is not None else None
    address = _child(company, "address")
    capital = _child(block, "capital") if block is not None else None
    return {
        "name": _text(_child(company, "name")),
        "uid": _text(_child(company, "uid")),
        "seat": _text(_child(company, "seat")),
        "legal_form": _text(_child(company, "legalForm")),
        "plz": _text(_child(address, "swissZipCode")),
        "town": _text(_child(address, "town")),
        "street": _text(_child(address, "street")),
        "house": _text(_child(address, "houseNumber")),
        "co": _text(_child(address, "addressLine1")),
        "purpose": _text(_child(block, "purpose")),
        "capital_nominal": _text(_child(capital, "nominal")),
        "capital_paid": _text(_child(capital, "paid")),
        "no_address": _text(_child(company, "noAddress")),
    }


def _flag_true(el: ET.Element | None) -> bool:
    return (_text(el) or "").lower() == "true"


def _any_true(el: ET.Element | None) -> bool:
    if el is None:
        return False
    if _flag_true(el):
        return True
    return any(_any_true(child) for child in list(el))


def _meta(root: ET.Element) -> dict:
    meta = _child(root, "meta")
    title_el = _child(meta, "title")
    language = _text(_child(meta, "language"))
    title = None
    if title_el is not None and language:
        title = _text(_child(title_el, language))
    if not title and title_el is not None:
        for child in title_el:
            title = _text(child)
            if title:
                break
    return {
        "xml_id": _text(_child(meta, "id")),
        "rubric": _text(_child(meta, "rubric")),
        "sub_rubric": _text(_child(meta, "subRubric")),
        "language": language,
        "publication_number": _text(_child(meta, "publicationNumber")),
        "published_at": (_text(_child(meta, "publicationDate")) or "")[:10],
        "canton": _text(_child(meta, "cantons")),
        "title": title,
    }


def _base_event(
    publication_id: str,
    published_at: str,
    snap: dict,
    canton: str | None,
    event_type: str,
    rule_id: str,
    payload: dict,
) -> Event:
    return Event(
        publication_id=publication_id,
        published_at=published_at,
        event_type=event_type,
        rule_id=rule_id,
        org_uid=snap.get("uid"),
        person_key=None,
        plz=snap.get("plz"),
        canton=canton,
        payload=payload,
    )


def map_hr_xml(path: Path, publication_id: str | None = None) -> tuple[dict, list[Event], str]:
    """Return (notice_meta, xml_events, publication_text)."""
    tree = ET.parse(path)
    root = tree.getroot()
    meta = _meta(root)
    pub_id = publication_id or meta["xml_id"] or path.stem
    content = _child(root, "content")
    text = _text(_child(content, "publicationText")) or ""
    new = _company_snapshot(_child(content, "commonsNew"))
    actual = _company_snapshot(_child(content, "commonsActual"))
    published_at = meta["published_at"]
    canton = meta["canton"]
    transaction = _find(root, "content", "transaction")
    is_registration = _flag_true(_child(transaction, "registration"))
    delete_el = _child(transaction, "delete") if transaction is not None else None
    changements = _find(root, "content", "transaction", "update", "changements")

    events: list[Event] = []
    if is_registration:
        events.append(
            _base_event(
                pub_id,
                published_at,
                new,
                canton,
                "company_registered",
                "xml.hr01.registration.v1",
                {"name": new.get("name"), "seat": new.get("seat"), "purpose": new.get("purpose")},
            )
        )
        meta["org_uid"] = new.get("uid")
        meta["plz"] = new.get("plz")
        meta["publication_text"] = text
        meta["publication_id"] = pub_id
        return meta, events, text

    if delete_el is not None:
        deletion_date = _text(_child(delete_el, "deletionDate"))
        note = None
        for pattern in (
            r"La società è cancellata[^.]*",
            r"Die Gesellschaft ist gelöscht[^.]*",
            r"Die Gesellschaft ist erloschen[^.]*",
            r"Die Liquidation ist durchgeführt[^.]*",
            r"La société est radiée[^.]*",
        ):
            match = re.search(pattern, text, re.I)
            if match:
                note = match.group(0).strip()
                break
        events.append(
            _base_event(
                pub_id,
                published_at,
                actual,
                canton,
                "company_deleted",
                "xml.hr03.deletion.v1",
                {"deletion_date": deletion_date, "name": actual.get("name"), "note": note},
            )
        )
        meta["others"] = False
        meta["org_uid"] = actual.get("uid")
        meta["plz"] = actual.get("plz")
        meta["publication_id"] = pub_id
        meta["publication_text"] = text
        meta["company_name"] = actual.get("name")
        return meta, events, text

    def emit_if_changed(field: str, event_type: str, rule_id: str) -> None:
        before = actual.get(field)
        after = new.get(field)
        if before != after:
            events.append(
                _base_event(
                    pub_id,
                    published_at,
                    new,
                    canton,
                    event_type,
                    rule_id,
                    {"from": before, "to": after},
                )
            )

    emit_if_changed("name", "company_name_changed", "xml.hr02.name.v1")
    emit_if_changed("seat", "seat_changed", "xml.hr02.seat.v1")
    addr_before = address_key(
        street=actual.get("street"),
        house=actual.get("house"),
        plz=actual.get("plz"),
        town=actual.get("town"),
        co=actual.get("co"),
    )
    addr_after = address_key(
        street=new.get("street"),
        house=new.get("house"),
        plz=new.get("plz"),
        town=new.get("town"),
        co=new.get("co"),
    )
    if addr_before != addr_after:
        events.append(
            _base_event(
                pub_id,
                published_at,
                new,
                canton,
                "address_changed",
                "xml.hr02.address.v1",
                {"from": addr_before, "to": addr_after, "from_plz": actual.get("plz"), "to_plz": new.get("plz")},
            )
        )
    emit_if_changed("purpose", "purpose_changed", "xml.hr02.purpose.v1")
    if actual.get("capital_nominal") != new.get("capital_nominal") or actual.get("capital_paid") != new.get(
        "capital_paid"
    ):
        events.append(
            _base_event(
                pub_id,
                published_at,
                new,
                canton,
                "capital_changed",
                "xml.hr02.capital.v1",
                {
                    "from_nominal": actual.get("capital_nominal"),
                    "to_nominal": new.get("capital_nominal"),
                    "from_paid": actual.get("capital_paid"),
                    "to_paid": new.get("capital_paid"),
                },
            )
        )

    bankruptcy = _find(root, "content", "transaction", "update", "changements", "statusChanged", "bankruptcy")
    liquidation = _find(root, "content", "transaction", "update", "changements", "statusChanged", "liquidation")
    if _any_true(bankruptcy):
        note = None
        match = re.search(r"Das Konkursverfahren[^.]+", text)
        if match:
            note = match.group(0).strip()
        events.append(
            _base_event(
                pub_id,
                published_at,
                new,
                canton,
                "status_changed",
                "xml.hr02.bankruptcy.v1",
                {"kind": "bankruptcy", "note": note},
            )
        )
    elif _any_true(liquidation):
        events.append(
            _base_event(
                pub_id,
                published_at,
                new,
                canton,
                "status_changed",
                "xml.hr02.liquidation.v1",
                {"kind": "liquidation"},
            )
        )

    others = _flag_true(_child(changements, "others")) if changements is not None else False
    meta["others"] = others
    meta["org_uid"] = new.get("uid") or actual.get("uid")
    meta["plz"] = new.get("plz") or actual.get("plz")
    meta["publication_id"] = pub_id
    meta["publication_text"] = text
    meta["company_name"] = new.get("name")
    return meta, events, text
