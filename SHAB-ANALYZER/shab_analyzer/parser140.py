from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_TWO_LIQUIDATORS_APPOINTED = re.compile(
    r"^(?P<name1>[^,.;]+?)\s+et\s+(?P<name2>[^,.;]+?)\s+"
    r"sont nommés liquidateurs\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_RESTRICTIONS_FALL = re.compile(
    r"^Les restrictions quant à la transmissibilité des\s+"
    r"(?P<count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+tombent\s*"
    r"\((?P<legal_basis>art\.\s*685a,\s*al\.\s*3\s*CO)\)\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_GRANTED_ROLE_AND_PROXY_REVOKED = re.compile(
    r"^Signature\s+(?P<sign>individuelle|collective à deux)\s+a été conférée à\s+"
    r"(?P<name>[^,.;]+),\s*nommé(?:e)?\s+(?P<role>[^,.;]+);\s*"
    r"sa procuration est radiée\.?$",
    re.I | re.UNICODE,
)
_FR_MERGER_AGREEMENT_DATE_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:n[o°]\.?)?\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*"
    r"\(publication FOSC du\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"page\s+(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le "
    r"contrat de fusion est daté du\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s*"
    r"\(et non du\s+(?P<previous_date>\d{2}\.\d{2}\.\d{4})\)\.?$",
    re.I | re.UNICODE,
)
_FR_STATUTES_ADOPTION_DATE_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}[.-]\d{2}[.-]\d{4})\s*"
    r"\(FOSC du\s+(?P<notice_date>\d{2}[.-]\d{2}[.-]\d{4}),\s*"
    r"p\.\s*(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que les "
    r"statuts ont été adoptés le(?:\s+le)?\s+(?P<date>\d{2}[.-]\d{2}[.-]\d{4})\s*"
    r"\(et non le\s+(?P<previous_date>\d{2}[.-]\d{2}[.-]\d{4})\)\.?$",
    re.I | re.UNICODE,
)
_DE_PREVIOUS_BRANCH_PLACE = re.compile(
    r"^\[bisher:\s*(?P<previous_place>Lengnau BE|Romanshorn)\]\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_PROCURATIONS_REVOKED = re.compile(
    r"^Les procurations de\s+(?P<name1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+)\s+et\s+(?P<name3>[^,;]+?)\s+sont radiées\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_AND_DIRECTOR_LIQUIDATORS = re.compile(
    r"^Le gérant\s+(?P<name1>[^,.;]+?)\s+et le directeur\s+"
    r"(?P<name2>[^,.;]+?)\s+sont désormais liquidateurs et continuent de signer "
    r"individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_FOREIGN_BOARD_MEMBERS_WITHOUT_SIGNATURE = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:(?:du|de la|des|de)\s+|d['’])"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<country1>[A-Z]{2,3}),\s*et\s+(?P<name2>[^,.;]+),\s*"
    r"(?:(?:du|de la|des|de)\s+|d['’])(?P<origin2>[^,.;]+),\s*"
    r"à\s+(?P<place2>[^,.;]+),\s*(?P<country2>[A-Z]{2,3}),\s*"
    r"sont membres du conseil sans signature\.?$",
    re.I | re.UNICODE,
)
_DE_PERSON_RESIDENCE_CHANGED_ABROAD = re.compile(
    r"^Eingetragene Person geändert:\s*(?P<name>[^,.;]+),\s*"
    r"(?P<role>[^,.;]+),\s*(?P<sign>Kollektivunterschrift zu zweien|"
    r"Einzelunterschrift),\s*neu wohnhaft in\s+(?P<place>[^()]+?)\s*"
    r"\((?P<country>[A-Z]{2,3})\)\.?$",
    re.I | re.UNICODE,
)
_DE_ORGANIZATION_REMOVED_TYPO = re.compile(
    r"^Organisation neu:\s*\[gestrichen aufgrund geänderter "
    r"Eintragungsvorschrften\]\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_PRESIDENT_TRANSFER_TO_NEW_MANAGER = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+),\s*lequel est nommé président,\s*"
    r"cède\s+(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de "
    r"CHF\s+(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:(?:du|de la|des|de)\s+|d['’])(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvelle associée-gérante\s+"
    r"(?P=seller)\s+reste titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_ROLE_RETRACTED = re.compile(
    r"^Rectification de la publication dans la FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\.\s*"
    r"(?P<notice_ref>\d+):\s*(?P<name>[^,.;]+),\s*"
    r"(?:(?:du|de la|des|de)\s+|d['’])(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*n['’]est pas gérante\.?$",
    re.I | re.UNICODE,
)
_DE_LEGACY_BRANCH_REMOVED_NESTED_LABELS = re.compile(
    r"^Zweigniederlassung neu:\s*\[Folgende Zweigniederlassung wurde aufgehoben:\]\s*"
    r"\[gestrichen:\s*(?P<place>[^()\]]+?)\s*"
    r"\((?P<branch_id>CH-[\d.-]+)\)\]\.?$",
    re.I | re.UNICODE,
)
_IT_LIQUIDATION_TRANSLATIONS = re.compile(
    r"^Traduzioni della ragione sociale in liquidazione:\s*"
    r"\((?P<german>[^()]+)\)\s*\((?P<english>[^()]+)\)\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = re.split(r"[.-]", raw)
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _signing(raw: str) -> str:
    if "individ" in raw.lower() or "einzel" in raw.lower():
        return "Einzelunterschrift"
    return "Kollektivunterschrift zu zweien"


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


def extract_parser140_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 140."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_TWO_LIQUIDATORS_APPOINTED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_liquidators_appointed.v1"
        for group in ("name1", "name2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(group), role="liquidateur",
                extra={"action": "appointed_liquidator"},
            ))

    match = _FR_SHARE_TRANSFER_RESTRICTIONS_FALL.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.share_transfer_restrictions_fall.v1",
            {
                "kind": "share_transfer_restriction", "action": "removed",
                "shares_count": _count(match.group("count")),
                "share_kind": "actions nominatives",
                "nominal": match.group("nominal"), "currency": "CHF",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
            },
        ))

    match = _FR_SIGNING_GRANTED_ROLE_AND_PROXY_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.signing_granted_role_proxy_revoked.v1",
            match.group("name"), role=match.group("role").strip(),
            signing=_signing(match.group("sign")),
            extra={"action": "appointed", "proxy_revoked": True},
        ))

    match = _FR_MERGER_AGREEMENT_DATE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.merger_agreement_date_corrected.v1",
            {
                "kind": "merger_agreement_date", "action": "corrected",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
                "date": _iso_date(match.group("date")),
                "previous_published_date": _iso_date(match.group("previous_date")),
            },
        ))

    match = _FR_STATUTES_ADOPTION_DATE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.statutes_adoption_date_corrected.v1",
            {
                "kind": "statutes_adoption_date", "action": "corrected",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
                "date": _iso_date(match.group("date")),
                "previous_published_date": _iso_date(match.group("previous_date")),
            },
        ))

    match = _DE_PREVIOUS_BRANCH_PLACE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.previous_branch_place.v1",
            {
                "action": "seat_changed", "previous_place":
                match.group("previous_place").strip(),
            },
        ))

    match = _FR_THREE_PROCURATIONS_REVOKED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.three_procurations_revoked.v1"
        for group in ("name1", "name2", "name3"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(group),
                extra={"action": "revoked", "previous_signing": "procuration"},
            ))

    match = _FR_MANAGER_AND_DIRECTOR_LIQUIDATORS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_and_director_appointed_liquidators.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role="gérant et liquidateur", signing="Einzelunterschrift",
                extra={"action": "appointed_liquidator", "signing_continues": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                role="directeur et liquidateur", signing="Einzelunterschrift",
                extra={"action": "appointed_liquidator", "signing_continues": True},
            ),
        ])

    match = _FR_TWO_FOREIGN_BOARD_MEMBERS_WITHOUT_SIGNATURE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_foreign_board_members_without_signature.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="membre du conseil",
                extra={
                    "action": "appointed",
                    "heimat": match.group(f"origin{index}").strip(),
                    "country": match.group(f"country{index}").upper(),
                    "without_signature": True,
                },
            ))

    match = _DE_PERSON_RESIDENCE_CHANGED_ABROAD.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.residence_changed_abroad.v1",
            match.group("name"), place=match.group("place"),
            role=match.group("role").strip(), signing=_signing(match.group("sign")),
            extra={"action": "domicile_changed", "country": match.group("country")},
        ))

    match = _DE_ORGANIZATION_REMOVED_TYPO.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.organization_removed_typo.v1",
            {"action": "removed", "reason": "changed_registration_rules"},
        ))

    match = _FR_MANAGER_PRESIDENT_TRANSFER_TO_NEW_MANAGER.search(leftover)
    if match and match.group("nominal") == match.group("remaining_nominal"):
        consume(match)
        rule_id = "fr.persons.manager_president_transfer_to_new_manager.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller,
                role="associé-gérant et président",
                extra={
                    **common, "action": "appointed_president_and_shares_transferred",
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée-gérante",
                extra={
                    **common, "action": "appointed_and_shares_received",
                    "counterparty": seller, "heimat": match.group("origin").strip(),
                    "shares_received": transferred, "shares_count": transferred,
                },
            ),
        ])

    match = _FR_MANAGER_ROLE_RETRACTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.manager_role_retracted.v1",
            match.group("name"), place=match.group("place"), role="gérante",
            extra={
                "action": "role_retracted", "role_active": False,
                "heimat": match.group("origin").strip(),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _DE_LEGACY_BRANCH_REMOVED_NESTED_LABELS.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.legacy_branch_removed_nested_labels.v1",
            {
                "action": "removed", "place": match.group("place").strip(),
                "previous_branch_id": match.group("branch_id"),
            },
        ))

    match = _IT_LIQUIDATION_TRANSLATIONS.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_name_changed", "it.text.liquidation_translations.v1",
            {
                "action": "liquidation_translations_recorded",
                "translations": {
                    "de": match.group("german").strip(),
                    "en": match.group("english").strip(),
                },
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
