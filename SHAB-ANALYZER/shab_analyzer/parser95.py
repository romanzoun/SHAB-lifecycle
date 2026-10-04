from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_COMMITTEE_SIGNING_SUPPLEMENTS = re.compile(
    r"^Les inscriptions\s+(?P<entry1>[\d']+)\s+du\s+"
    r"(?P<entry_date1>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date1>\d{2}-\d{2}-\d{4}),\s*p\.\s*(?P<page1>[\d/]+)\)\s+"
    r"et\s+(?P<entry2>[\d']+)\s+du\s+"
    r"(?P<entry_date2>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date2>\d{2}-\d{2}-\d{4}),\s*p\.\s*(?P<page2>[\d/]+)\)\s+"
    r"sont complétées en ce sens que,\s*conformément aux statuts,\s*"
    r"les membres du comité\s+(?P<name1>[^,.;]+),\s*(?P<name2>[^,.;]+)\s+"
    r"et\s+(?P<name3>[^,.;]+)\s+signent\s+(?P<sign>collectivement à deux),\s*"
    r"mais avec le président,\s*le trésorier ou le secrétaire général\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_SIGNATURE_REMAINING = re.compile(
    r"^(?P<seller>.+?)\s+a cédé\s+(?P<transferred>[\d']+)\s+parts? de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?:(?P<country>[A-Z]),\s*)?nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts? de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"Signature individuelle a été conférée à l['’]associé\s+(?P=buyer)\.\s*"
    r"Par conséquent,\s*(?P=seller)\s+est\s+(?:désormais|maintenant) titulaire de\s+"
    r"(?P<seller_count>[\d']+)\s+parts? de CHF\s+(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_NAME_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_page>[\d/]+)\)\s+est rectifiée en ce sens que le nom exact de "
    r"la\s+(?P<role>gérante)\s+est\s+(?P<name>.+?)\s*"
    r"\(et non est\s+(?P<previous_name>.+?)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_INCOMING_SPIN_OFF = re.compile(
    r"^Séparation:\s*la société reprend une partie du patrimoine de\s+"
    r"(?P<source>.+?),\s*à\s+(?P<source_place>[^()]+?)\s*"
    r"\((?P<source_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"selon contrat de scission du\s+(?P<date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"La société reprend ainsi des actifs de CHF\s+(?P<assets>[\d'.]+)\s+"
    r"et des passifs envers les tiers de CHF\s+(?P<liabilities>[\d'.]+),\s*"
    r"soit un actif net de CHF\s+(?P<net>[\d'.]+)\.\s*"
    r"La totalité du capital social des deux sociétés étant détenue par la même "
    r"associée,\s*la scission ne donne pas lieu à une augmentation du capital,\s*"
    r"ni à une attribution de parts sociales au sein de la société reprenante\.?$",
    re.I | re.UNICODE,
)
_FR_ERRONEOUS_APPOINTMENTS_RESTORED = re.compile(
    r"^L['’]inscription N°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+étant erronée,\s*"
    r"la situation antérieure est restaurée en ce sens que\s+"
    r"(?P<name1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+)\s+n['’]ont pas été "
    r"nommés\s+(?P<role>directeur)\s*\(leurs pouvoirs sont radiés\),\s*et que\s+"
    r"(?P<name3>[^,.;]+),\s*(?P<current_roles>membre et secrétaire du conseil "
    r"d['’]administration),\s*n['’]a pas été nommé\s+"
    r"(?P<incorrect_role>directeur général);\s*continue de signer\s+"
    r"(?P<sign>collectivement à deux)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_DISSOLUTION_AND_LIQUIDATORS = re.compile(
    r"^L['’](?P<authority>Autorité de surveillance .+?)\s+a pris acte de la "
    r"dissolution de la fondation par décision du\s+"
    r"(?P<date>\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|"
    r"septembre|octobre|novembre|décembre)\s+\d{4})\.\s*"
    r"(?P<name1>[^,.;]+),\s*(?P<name2>[^,.;]+),\s*"
    r"(?P<name3>[^,.;]+)\s+et\s+(?P<name4>[^,.;]+)\s+sont nommés liquidateurs\.?$",
    re.I | re.UNICODE,
)
_DE_TECHNICAL_CORRECTION = re.compile(
    r"^\[Technische Berichtigung\]\.?$", re.I | re.UNICODE
)
_FR_ASSOCIATE_TRANSFER_MISSING_PREPOSITION = re.compile(
    r"^(?P<seller>[^,.;]+),\s*(?P<seller_role>associé-gérant),\s*cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+(?P<buyer>[^,.;]+),\s*désormais à\s+"
    r"(?P<place>[^,.;]+),\s*nouvelle associée avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_SEAT_CHANGED = re.compile(
    r"^Nouveau siège de la succursale à\s+(?P<from>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\):\s*(?P<to>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_MIXED_PERSON_REPLACEMENT = re.compile(
    r"^Gelöschte Person:\s*(?P<removed>[^,.;]+),\s*"
    r"(?P<removed_sign>Kollektivunterschrift zu zweien)\.\s*"
    r"Neu eingetragene Person:\s*(?P<added>[^,.;]+),\s*von\s+"
    r"(?P<origin>[^,.;]+),\s*in\s+(?P<place>[^,.;]+),\s*"
    r"(?P<added_sign>Kollektivunterschrift zu zweien)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_BOARD_REPLACEMENT = re.compile(
    r"^(?P<removed_signed>.+?),\s*dont la signature est radiée,\s*"
    r"(?P<removed_unsigned>.+?),\s*inscrits sans signature,\s*"
    r"ne sont plus membres du conseil de fondation\.\s*"
    r"Nouveaux membres du conseil de fondation:\s*"
    r"(?P<vice>[^,.;]+),\s*de et à\s+(?P<vice_place>[^,.;]+),\s*vice-président\s+"
    r"(?P<name1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*(?P<name2>[^,.;]+),\s*de\s+"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"(?P<name3>[^,.;]+),\s*de\s+(?P<origin3>[^,.;]+),\s*à\s+"
    r"(?P<place3>[^,.;]+),\s*(?P<name4>[^,.;]+),\s*(?P<name5>[^,.;]+),\s*"
    r"tous deux de et à\s+(?P<shared_place>[^,.;]+),\s*et\s+"
    r"(?P<name6>[^,.;]+),\s*de\s+(?P<origin6>[^,.;]+),\s*à\s+"
    r"(?P<place6>[^,.;]+),\s*les six sans signature\.?$",
    re.I | re.UNICODE,
)
_DE_CORRECTED_DOCUMENT_LIST = re.compile(
    r"^:\s*(?P<documents>1\.\s*.+?,\s*2\.\s*.+?,\s*3\.\s*.+?,\s*4\.\s*.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_AND_PRESIDENCY = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé-gérant avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"(?P=seller),\s*qui reste titulaire de\s+(?P<seller_count>[\d']+)\s+"
    r"parts de CHF\s+(?P<seller_nominal>[\d'.]+),\s*est nommé président\.?$",
    re.I | re.UNICODE,
)
_DE_CAPITAL_BAND_ARTICLE = re.compile(
    r"^Kapitalband gemäss näherer Umschreibung in\s+(?P<article>Art\.\s*[^.]+)\s+"
    r"der Statuten\.?$",
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


def _iso_date(raw: str) -> str:
    day, month, year = re.split(r"[.-]", raw)
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _french_date(raw: str) -> str:
    day, month, year = raw.lower().replace("1er", "1").split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


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


def extract_parser95_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 95."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_COMMITTEE_SIGNING_SUPPLEMENTS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.committee_signing_supplements.v1"
        references = [
            {
                "entry": match.group(f"entry{index}"),
                "entry_date": _iso_date(match.group(f"entry_date{index}")),
                "notice_date": _iso_date(match.group(f"notice_date{index}")),
                "notice_page": match.group(f"page{index}"),
            }
            for index in (1, 2)
        ]
        for index in (1, 2, 3):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", rule_id, match.group(f"name{index}"),
                    role="membre du comité", signing="Kollektivunterschrift zu zweien",
                    extra={
                        "action": "registration_supplemented",
                        "signing_constraint": (
                            "avec le président, le trésorier ou le secrétaire général"
                        ),
                        "references": references,
                    },
                )
            )

    match = _FR_SHARE_TRANSFER_SIGNATURE_REMAINING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.share_transfer_signature_remaining.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé",
                    extra={
                        "action": "shares_transferred",
                        "counterparty": buyer,
                        "shares_transferred": transferred,
                        "shares_count": _count(match.group("seller_count")),
                        "share_nominal": match.group("seller_nominal"),
                        "currency": "CHF",
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé", signing="Einzelunterschrift",
                    extra={
                        "action": "appointed",
                        "counterparty": seller,
                        "new_associate": True,
                        "heimat": match.group("origin").strip(),
                        "country_code": match.group("country"),
                        "shares_received": transferred,
                        "shares_count": _count(match.group("buyer_count")),
                        "share_nominal": match.group("buyer_nominal"),
                        "currency": "CHF",
                    },
                ),
            ]
        )

    match = _FR_MANAGER_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.manager_name_corrected_ce_sens.v1",
                match.group("name"), role=match.group("role"),
                extra={
                    "action": "name_corrected",
                    "previous_name": match.group("previous_name").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_page": match.group("notice_page"),
                },
            )
        )

    match = _FR_INCOMING_SPIN_OFF.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "fr.text.spin_off_acquisition_llc.v1",
                {
                    "kind": "spin_off_acquisition",
                    "source": match.group("source").strip(),
                    "source_place": match.group("source_place").strip(),
                    "source_uid": match.group("source_uid"),
                    "date": _iso_date(match.group("date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "net_assets": match.group("net"),
                    "currency": "CHF",
                    "common_owner": True,
                    "capital_increase": False,
                    "share_allocation": False,
                    "share_kind": "parts sociales",
                },
            )
        )

    match = _FR_ERRONEOUS_APPOINTMENTS_RESTORED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.erroneous_appointments_restored.v1"
        reference = {
            "action": "erroneous_appointment_reversed",
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
        }
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", rule_id, match.group(f"name{index}"),
                    role=match.group("role"),
                    extra={**reference, "powers_revoked": True},
                )
            )
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name3"),
                role=match.group("current_roles"),
                signing="Kollektivunterschrift zu zweien",
                extra={
                    **reference,
                    "incorrect_role": match.group("incorrect_role"),
                    "signing_continues": True,
                },
            )
        )

    match = _FR_FOUNDATION_DISSOLUTION_AND_LIQUIDATORS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.foundation_dissolution_liquidators.v1"
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id,
                {
                    "kind": "dissolution",
                    "date": _french_date(match.group("date")),
                    "authority": match.group("authority").strip(),
                    "authority_action": "acknowledged",
                },
            )
        )
        for index in (1, 2, 3, 4):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    role="liquidateur", signing="Kollektivunterschrift zu zweien",
                    extra={"action": "appointed"},
                )
            )

    match = _DE_TECHNICAL_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", "de.text.technical_correction.v1",
                {"kind": "technical_correction"},
            )
        )

    match = _FR_ASSOCIATE_TRANSFER_MISSING_PREPOSITION.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.share_transfer_missing_preposition.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role=match.group("seller_role"),
                    extra={
                        "action": "shares_transferred",
                        "counterparty": buyer,
                        "shares_before": _count(match.group("before")),
                        "shares_transferred": transferred,
                        "shares_count": _count(match.group("seller_count")),
                        "share_nominal": match.group("seller_nominal"),
                        "currency": "CHF",
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associée",
                    extra={
                        "action": "appointed",
                        "counterparty": seller,
                        "new_associate": True,
                        "shares_received": transferred,
                        "shares_count": _count(match.group("buyer_count")),
                        "share_nominal": match.group("buyer_nominal"),
                        "currency": "CHF",
                    },
                ),
            ]
        )

    match = _FR_BRANCH_SEAT_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", "fr.text.branch_seat_changed_uid.v1",
                {
                    "action": "seat_changed",
                    "scope": "branch",
                    "branch_uid": match.group("uid"),
                    "from": match.group("from").strip(),
                    "to": match.group("to").strip(),
                },
            )
        )

    match = _DE_MIXED_PERSON_REPLACEMENT.search(leftover)
    if match:
        consume(match)
        rule_id = "de.persons.mixed_language_replacement.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", rule_id, match.group("removed"),
                    signing=match.group("removed_sign"),
                    extra={"action": "removed", "language_override": "de"},
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("added"),
                    place=match.group("place"), signing=match.group("added_sign"),
                    extra={
                        "action": "appointed",
                        "heimat": match.group("origin").strip(),
                        "language_override": "de",
                    },
                ),
            ]
        )

    match = _FR_FOUNDATION_BOARD_REPLACEMENT.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.foundation_board_replacement_extended.v1"
        removed_signed = [
            name.strip() for name in match.group("removed_signed").split(",")
        ]
        removed_unsigned = [
            name.strip() for name in match.group("removed_unsigned").split(",")
        ]
        for name in removed_signed:
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", rule_id, name,
                    role="membre du conseil de fondation",
                    extra={"action": "removed", "signature_revoked": True},
                )
            )
        for name in removed_unsigned:
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", rule_id, name,
                    role="membre du conseil de fondation",
                    extra={"action": "removed", "without_signature": True},
                )
            )
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("vice"),
                place=match.group("vice_place"), role="vice-président",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed", "heimat": match.group("vice_place")},
            )
        )
        additions = (
            ("name1", "origin1", "place1", "France"),
            ("name2", "origin2", "place2", "France"),
            ("name3", "origin3", "place3", None),
            ("name4", "shared_place", "shared_place", None),
            ("name5", "shared_place", "shared_place", None),
            ("name6", "origin6", "place6", "France"),
        )
        for name_group, origin_group, place_group, country in additions:
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(name_group),
                    place=match.group(place_group),
                    role="membre du conseil de fondation",
                    extra={
                        "action": "appointed",
                        "heimat": match.group(origin_group).strip(),
                        "country": country,
                        "without_signature": True,
                    },
                )
            )

    match = _DE_CORRECTED_DOCUMENT_LIST.search(leftover)
    if match:
        consume(match)
        documents = [
            document.strip()
            for document in re.split(r"(?:^|,\s*)\d+\.\s*", match.group("documents"))
            if document.strip()
        ]
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", "de.text.corrected_document_list.v1",
                {"kind": "document_list", "action": "corrected", "documents": documents},
            )
        )

    match = _FR_SHARE_TRANSFER_AND_PRESIDENCY.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.share_transfer_and_presidency.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="président",
                    extra={
                        "action": "role_changed_and_shares_transferred",
                        "previous_role": "associé-gérant",
                        "counterparty": buyer,
                        "shares_before": _count(match.group("before")),
                        "shares_transferred": transferred,
                        "shares_count": _count(match.group("seller_count")),
                        "share_nominal": match.group("seller_nominal"),
                        "currency": "CHF",
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé-gérant", signing="Einzelunterschrift",
                    extra={
                        "action": "appointed",
                        "counterparty": seller,
                        "heimat": match.group("origin").strip(),
                        "shares_received": transferred,
                        "shares_count": _count(match.group("buyer_count")),
                        "share_nominal": match.group("buyer_nominal"),
                        "currency": "CHF",
                    },
                ),
            ]
        )

    match = _DE_CAPITAL_BAND_ARTICLE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.capital_band_article.v1",
                {
                    "kind": "capital_band",
                    "action": "introduced",
                    "basis": "statutes",
                    "article": match.group("article").strip(),
                    "details_in_statutes": True,
                },
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
