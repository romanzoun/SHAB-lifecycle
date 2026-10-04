from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_GIVEN_NAME_CORRECTED_COLON = re.compile(
    r"^Rectificatif:\s*l['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le prénom exact "
    r"de\s+(?P<previous_name>[^:.;]+?)\s+est\s*:\s*(?P<name>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PRESIDENT_FOREIGN_MEMBER = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé président\s+et\s+"
    r"(?P<member>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{2,3}),\s*tous deux\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATORS_APPOINTED_DIRECTORS = re.compile(
    r"^Les administrateurs\s+(?P<name1>[^,.;]+?)\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*nommés en outre directeurs,\s*"
    r"continuent à signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_DE_HEAD_OFFICE_SHARE_CAPITAL_LABELED = re.compile(
    r"^Kapital Hauptsitz neu:\s*Aktienkapital:\s*(?P<currency>[A-Z]{3})\s+"
    r"(?P<to_capital>[\d']+(?:\.\d+)?(?:\.--)?)\s*;\s*"
    r"Liberierung Aktienkapital:\s*(?P<to_paid_currency>[A-Z]{3})\s+"
    r"(?P<to_paid>[\d']+(?:\.\d+)?(?:\.--)?)\s*"
    r"\[bisher:\s*Kapital Hauptsitz:\s*Aktienkapital:\s*"
    r"(?P<from_currency>[A-Z]{3})\s+(?P<from_capital>[\d']+(?:\.\d+)?(?:\.--)?)\s*;\s*"
    r"Liberierung Aktienkapital:\s*(?P<from_paid_currency>[A-Z]{3})\s+"
    r"(?P<from_paid>[\d']+(?:\.\d+)?(?:\.--)?)\]\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_NAME_CORRECTED_WITH_NOTICE = re.compile(
    r"^L['’]inscription au journal\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que (?:le|les) "
    r"nom exact de la\s+(?P<role>gérante)\s+est\s+(?P<name>[^()]+?)\s+"
    r"et non pas\s*\((?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_APPOINTED_LIQUIDATOR = re.compile(
    r"^L['’]administrateur\s+(?P<name>[^,.;]+)\s+est désormais liquidateur "
    r"et continue de signer individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_NAME_CORRECTED_WITH_NOTICE = re.compile(
    r"^L['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que l['’]un des "
    r"administrateurs se nomme\s+(?P<name>[^()]+?)\s*"
    r"\(et non pas\s+(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_SEAT_AND_NAME_CHANGED = re.compile(
    r"^La succursale à\s+(?P<from_seat>[^()]+?)\s*"
    r"\((?P<branch_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*a transféré son siège à\s+"
    r"(?P<to_seat>[^,.;]+),\s*sous la nouvelle raison sociale\s+"
    r"(?P<name>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_PRESIDENT_AND_MEMBER = re.compile(
    r"^(?P<president>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<president_origin>[^,.;]+),\s*à\s+(?P<president_place>[^,.;]+),\s*"
    r"président,\s*et\s+(?P<member>[^,.;]+),\s*de et à\s+"
    r"(?P<member_place>[^,.;]+),\s*sont membres du conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_ORIGIN_PRESIDENT_AND_VICE = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*maintenant originaire de\s+"
    r"(?P<president_origin>[^,.;]+),\s*nommé président,\s*et\s+"
    r"(?P<vice>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<vice_origin>[^,.;]+),\s*à\s+(?P<vice_place>[^,.;]+),\s*"
    r"vice-président,\s*lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_ERRONEOUS_BANKRUPTCY_ENTRY_CANCELLED = re.compile(
    r"^L['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+ayant été opérée à tort,\s*"
    r"elle est annulée\.\s*Par conséquent la mention de la faillite est radiée "
    r"et la raison sociale redevient\s*:\s*(?P<name>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_MANAGER_APPOINTED = re.compile(
    r"^(?P<name>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+(?:\s*\([A-Z]{2}\))?),\s*à\s+"
    r"(?P<place>[^,.;]+)\s+est nommée gérante unique\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_AND_BUYER_SIGNING = re.compile(
    r"^(?P<seller>[^,.;]+)\s+a cédé\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de et à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"par conséquent\s+(?P=seller)\s+est maintenant associé pour\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+(?P<seller_nominal>[\d'.]+)\.\s*"
    r"Signature individuelle a été conférée à l['’]associé\s+(?P=buyer)\.?$",
    re.I | re.UNICODE,
)
_FR_ONE_SHARE_TRANSFER_UNSIGNED_BUYER = re.compile(
    r"^(?P<seller>[^,.;]+)\s+détient désormais\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+(?P<seller_nominal>[\d'.]+)\s+"
    r"par suite de cession d['’]une part de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{1,3}),\s*nouvel associé pour une part de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*sans signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_DEFINITIVE_MORATORIUM_WITH_COMMISSIONER = re.compile(
    r"^Par décision du\s+(?P<decision_date>\d{1,2}(?:er)?\s+"
    r"[A-Za-zÀ-ÿ]+\s+\d{4}),\s*(?P<authority>.+?)\s+a accordé au titulaire "
    r"un sursis concordataire définitif de\s+(?P<duration>[^,.;]+?)\s+et "
    r"désigné\s+(?P<commissioner>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*en qualité de commissaire au sursis\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_REMOVALS_PRESIDENT_AND_NEW_MEMBERS = re.compile(
    r"^(?P<removed1>[^,.;]+),\s*(?P<removed2>[^,.;]+)\s+"
    r"ne sont plus administrateurs;\s*leurs pouvoirs sont radiés\.\s*"
    r"(?P<president>[^,.;]+)\s+jusqu['’]ici administrateur est désormais "
    r"administrateur président\.\s*(?P<member1>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+)\s+et\s+(?P<member2>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*(?P<country2>[A-Z]{2,3})\s+sont membres du "
    r"conseil d['’]administration avec une signature collective à deux\.?$",
    re.I | re.UNICODE,
)


_FR_MONTHS = {
    "janvier": 1,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
}
_FR_NUMBERS = {
    "un": 1,
    "une": 1,
    "deux": 2,
    "trois": 3,
    "quatre": 4,
    "cinq": 5,
    "six": 6,
    "sept": 7,
    "huit": 8,
    "neuf": 9,
    "dix": 10,
    "onze": 11,
    "douze": 12,
}


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _french_date(raw: str) -> str:
    day, month, year = raw.lower().replace("1er", "1").split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _duration_months(raw: str) -> int | None:
    token = raw.strip().split()[0].lower()
    return int(token) if token.isdigit() else _FR_NUMBERS.get(token)


def _event(
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
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
        org_uid=org_uid,
        plz=plz,
        canton=canton,
        payload=payload,
    )


def _person_event(
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
    event_type: str,
    rule_id: str,
    name: str,
    *,
    place: str | None = None,
    role: str | None = None,
    signing: str | None = None,
    extra: dict | None = None,
) -> Event:
    clean_name = name.strip()
    clean_place = place.strip() if place else None
    return Event(
        publication_id=publication_id,
        published_at=published_at,
        event_type=event_type,
        rule_id=rule_id,
        org_uid=org_uid,
        person_key=person_key(name=clean_name, place=clean_place),
        plz=plz,
        canton=canton,
        role=role,
        signing=signing,
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser133_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 133."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_GIVEN_NAME_CORRECTED_COLON.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.given_name_corrected_colon.v1",
            match.group("name"),
            extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_ADMINISTRATION_PRESIDENT_FOREIGN_MEMBER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_president_foreign_member.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président du conseil d'administration",
                signing="Einzelunterschrift",
                extra={"action": "appointed_president"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                place=match.group("place"), role="administrateur",
                signing="Einzelunterschrift",
                extra={
                    "action": "appointed",
                    "heimat": match.group("origin").strip(),
                    "country": match.group("country").upper(),
                },
            ),
        ])

    match = _FR_ADMINISTRATORS_APPOINTED_DIRECTORS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administrators_appointed_directors.v1"
        for group in ("name1", "name2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(group),
                role="administrateur et directeur",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed_additional_role", "signing_continues": True},
            ))

    match = _DE_HEAD_OFFICE_SHARE_CAPITAL_LABELED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.head_office_share_capital_labeled.v1",
            {
                "scope": "head_office",
                "kind": "share_capital",
                "currency": match.group("currency").upper(),
                "from_nominal": match.group("from_capital"),
                "to_nominal": match.group("to_capital"),
                "from_paid": match.group("from_paid"),
                "to_paid": match.group("to_paid"),
            },
        ))

    match = _FR_MANAGER_NAME_CORRECTED_WITH_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.manager_name_corrected_with_notice.v1",
            match.group("name"), role=match.group("role"),
            extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_ADMINISTRATOR_APPOINTED_LIQUIDATOR.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_appointed_liquidator.v1",
            match.group("name"), role="administrateur et liquidateur",
            signing="Einzelunterschrift",
            extra={"action": "appointed_liquidator", "signing_continues": True},
        ))

    match = _FR_ADMINISTRATOR_NAME_CORRECTED_WITH_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_name_corrected_with_notice.v1",
            match.group("name"), role="administrateur",
            extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_BRANCH_SEAT_AND_NAME_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "fr.text.branch_seat_and_name_changed.v1",
            {
                "action": "seat_and_name_changed",
                "branch_uid": match.group("branch_uid"),
                "from_seat": match.group("from_seat").strip(),
                "to_seat": match.group("to_seat").strip(),
                "name": match.group("name").strip(),
            },
        ))

    match = _FR_BOARD_PRESIDENT_AND_MEMBER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.board_president_and_member.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                place=match.group("president_place"),
                role="président du conseil d'administration",
                signing="Einzelunterschrift",
                extra={
                    "action": "appointed",
                    "heimat": match.group("president_origin").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                place=match.group("member_place"), role="administrateur",
                signing="Einzelunterschrift",
                extra={
                    "action": "appointed",
                    "heimat": match.group("member_place").strip(),
                },
            ),
        ])

    match = _FR_ADMINISTRATION_ORIGIN_PRESIDENT_AND_VICE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_origin_president_and_vice.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président du conseil d'administration",
                signing="Einzelunterschrift",
                extra={
                    "action": "appointed_president_and_origin_changed",
                    "heimat": match.group("president_origin").strip(),
                    "origin_changed": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("vice"),
                place=match.group("vice_place"),
                role="vice-président du conseil d'administration",
                signing="Einzelunterschrift",
                extra={
                    "action": "appointed",
                    "heimat": match.group("vice_origin").strip(),
                },
            ),
        ])

    match = _FR_ERRONEOUS_BANKRUPTCY_ENTRY_CANCELLED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.erroneous_bankruptcy_entry_cancelled.v1",
            {
                "kind": "bankruptcy_entry_cancelled",
                "action": "revoked",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "entry_erroneous": True,
                "bankruptcy_mention_removed": True,
                "company_name_restored": match.group("name").strip(),
            },
        ))

    match = _FR_SOLE_MANAGER_APPOINTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.sole_manager_appointed.v1",
            match.group("name"), place=match.group("place"), role="gérante unique",
            signing="Einzelunterschrift",
            extra={
                "action": "appointed",
                "heimat": match.group("origin").strip(),
            },
        ))

    match = _FR_SHARE_TRANSFER_AND_BUYER_SIGNING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.share_transfer_and_buyer_signing.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        seller_count = _count(match.group("seller_count"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé",
                extra={
                    "action": "shares_transferred",
                    "counterparty": buyer,
                    "shares_before": seller_count + transferred,
                    "shares_transferred": transferred,
                    "shares_count": seller_count,
                    "share_nominal": match.group("seller_nominal"),
                    "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé", signing="Einzelunterschrift",
                extra={
                    "action": "shares_received_and_signing_granted",
                    "counterparty": seller,
                    "heimat": match.group("place").strip(),
                    "new_associate": True,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"),
                    "currency": "CHF",
                },
            ),
        ])

    match = _FR_ONE_SHARE_TRANSFER_UNSIGNED_BUYER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.one_share_transfer_unsigned_buyer.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        seller_count = _count(match.group("seller_count"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé",
                extra={
                    "action": "shares_transferred",
                    "counterparty": buyer,
                    "shares_before": seller_count + 1,
                    "shares_transferred": 1,
                    "shares_count": seller_count,
                    "share_nominal": match.group("seller_nominal"),
                    "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé",
                extra={
                    "action": "shares_received",
                    "counterparty": seller,
                    "heimat": match.group("origin").strip(),
                    "country": match.group("country").upper(),
                    "new_associate": True,
                    "without_signature": True,
                    "shares_received": 1,
                    "shares_count": 1,
                    "share_nominal": match.group("buyer_nominal"),
                    "currency": "CHF",
                },
            ),
        ])

    match = _FR_DEFINITIVE_MORATORIUM_WITH_COMMISSIONER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.definitive_moratorium_with_commissioner.v1"
        commissioner = match.group("commissioner").strip()
        commissioner_place = match.group("place").strip()
        common = {
            "commissioner": commissioner,
            "commissioner_place": commissioner_place,
        }
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id,
                {
                    "kind": "composition_moratorium_granted",
                    "moratorium_type": "definitive",
                    "subject": "sole_proprietor",
                    "decision_date": _french_date(match.group("decision_date")),
                    "authority": match.group("authority").strip(),
                    "duration": match.group("duration").strip(),
                    "duration_months": _duration_months(match.group("duration")),
                    **common,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, commissioner,
                place=commissioner_place, role="commissaire au sursis",
                extra={
                    "action": "appointed",
                    "heimat": match.group("origin").strip(),
                },
            ),
        ])

    match = _FR_BOARD_REMOVALS_PRESIDENT_AND_NEW_MEMBERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.board_removals_president_and_new_members.v1"
        for group in ("removed1", "removed2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group(group), role="administrateur",
                extra={"action": "removed", "signing_revoked": True},
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("president"),
            role="président du conseil d'administration",
            extra={
                "action": "appointed_president",
                "previous_role": "administrateur",
            },
        ))
        for index in (1, 2):
            extra = {
                "action": "appointed",
                "heimat": match.group(f"origin{index}").strip(),
            }
            if index == 2:
                extra["country"] = match.group("country2").upper()
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"member{index}"),
                place=match.group(f"place{index}"), role="administrateur",
                signing="Kollektivunterschrift zu zweien", extra=extra,
            ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
