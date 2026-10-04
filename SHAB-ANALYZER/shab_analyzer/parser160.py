from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_SIGN = (
    r"Einzelunterschrift|Kollektivunterschrift(?:\s+zu\s+zweien)?|ohne Unterschrift"
)
_FR_ORIGIN = r"(?:du|de la|des|de|d['’])\s*"

_DE_ENTITY_ASSET_TRANSFER_SHORT_FORM = re.compile(
    r"^Vermögensübertragung:\s*(?P<transferor>.+?)\s*überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>CHF\s+[\d'.]+|keine)\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDATION_AUDIT_EXEMPTION_GRANTED = re.compile(
    r"^Die Stiftung wurde mit Verfügung der Aufsichtsbehörde vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+von der Pflicht befreit,\s*"
    r"eine Revisionsstelle zu bezeichnen\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_SPLITS_SHARES_TO_TWO_NEW_ASSOCIATES_NO_SIGNATURE = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+),\s*maintenant\s+" + _FR_ORIGIN +
    r"(?P<seller_origin>[^,.;]+),\s*cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+),\s*par\s+"
    r"(?P<share1>[\d']+)\s+parts de CHF\s+(?P<nominal1>[\d'.]+)\s+à\s+"
    r"(?P<buyer1>[^,.;]+),\s*" + _FR_ORIGIN + r"(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*et\s+par\s+(?P<share2>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal2>[\d'.]+)\s+à\s+(?P<buyer2>[^,.;]+),\s*" + _FR_ORIGIN +
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+?)"
    r"(?:\s*\((?P<place2_canton>[A-Z]{2})\))?,\s*nouveaux associés sans signature\.\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BOARD_REMOVED_TWO_CHANGED_CORRECTED_AND_NEW = re.compile(
    r"^Gelöschte Person:\s*(?P<removed_name>[^,]+),\s*(?P<removed_role>.+?),\s*"
    r"(?P<removed_sign>" + _DE_SIGN + r")\.\s*"
    r"Eingetragene Personen geändert:\s*"
    r"(?P<name1>[^,]+),\s*(?P<prev1_role>.+?),\s*(?P<prev1_sign>" + _DE_SIGN + r"),\s*"
    r"neu\s+(?P<new1_role>.+?),\s*(?P<new1_sign>" + _DE_SIGN + r");\s*"
    r"(?P<name2>[^,]+),\s*korrekterweise\s+(?P<name2_correct>[^,]+),\s*"
    r"(?P<prev2_role>.+?),\s*(?P<prev2_sign>" + _DE_SIGN + r"),\s*"
    r"neu\s+(?P<new2_role>.+?),\s*(?P<new2_sign>" + _DE_SIGN + r");\s*"
    r"(?P<name3>[^,]+),\s*(?P<prev3_role>.+?),\s*(?P<prev3_sign>" + _DE_SIGN + r"),\s*"
    r"neu\s+(?P<new3_role>.+?),\s*(?P<new3_sign>" + _DE_SIGN + r")\.\s*"
    r"Neu eingetragene Person:\s*(?P<name4>[^,]+),\s*von und in\s+"
    r"(?P<place4>[^,]+),\s*(?P<role4>.+?),\s*(?P<sign4>" + _DE_SIGN + r")\.?$",
    re.I | re.UNICODE,
)
_DE_SOLE_SHAREHOLDER_REMOVED_REMAINING_INCREASED = re.compile(
    r"^Gelöschte Person:\s*(?P<removed_name>[^,]+),\s*(?P<removed_role>[^,]+),\s*"
    r"(?P<removed_count>\d+)\s+Stammanteile?\s+zu\s+CHF\s+(?P<removed_nominal>[\d'.]+),\s*"
    r"(?P<removed_sign>ohne Unterschrift)\.\s*"
    r"Eingetragene Person geändert:\s*(?P<name>[^,]+),\s*(?P<role>[^,]+),\s*"
    r"(?P<before_count>\d+)\s+Stammanteile?\s+zu\s+CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"(?P<title>[^,]+),\s*(?P<sign>Einzelunterschrift),\s*neu\s+(?P<role_new>[^,]+),\s*"
    r"(?P<new_count>\d+)\s+Stammanteile?\s+zu\s+CHF\s+(?P<new_nominal>[\d'.]+),\s*"
    r"(?P<title_new>[^,]+),\s*(?P<sign_new>Einzelunterschrift),\s*nun in\s+"
    r"(?P<place>[^.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_SOLE_PROPRIETORSHIP_CONTRIBUTION_FRAGMENT = re.compile(
    r"^eingetragenen Einzelunternehmens\s+(?P<name>.+?),\s*in\s+(?P<place>[^,]+),\s*"
    r"gemäss Vertrag vom\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und "
    r"Übernahmebilanz per\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4})\s+mit Aktiven "
    r"von CHF\s+(?P<assets>[\d'.]+)\s+und Passiven von CHF\s+"
    r"(?P<liabilities>[\d'.]+),\s*wofür\s+(?P<shares>\d+)\s+Stammanteile zu CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+ausgegeben und CHF\s+(?P<credit>[\d'.]+)\s+als "
    r"Forderung gutgeschrieben werden\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_DIRECTORS_INDIVIDUAL_SIGNATURE_SHARED_ORIGIN = re.compile(
    r"^Signature individuelle est conférée à\s+(?P<name1>[^,]+),\s*à\s+"
    r"(?P<place1>[^,.;]+?)(?:\s*\((?P<place1_canton>[A-Z]{2})\))?,\s*et\s+"
    r"(?P<name2>[^,]+),\s*à\s+(?P<place2>[^,.;]+),\s*tous deux\s+" + _FR_ORIGIN +
    r"(?P<origin>[^,.;]+),\s*(?P<role>[^.]+?)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_HISTORY_DELETED = re.compile(
    r"^\[gestrichen:\s*Mit Beschluss des Verwaltungsrates vom\s+"
    r"(?P<board_date>\d{2}\.\d{2}\.\d{4})\s+wird die Statutenbestimmung über die "
    r"mit Ermächtigungsbeschluss vom\s+(?P<authorization_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"beschlossene genehmigte Kapitalerhöhung geändert\.\]\.\s*"
    r"\[gestrichen:\s*Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+eine genehmigte Kapitalerhöhung "
    r"gemäss näherer Umschreibung in den Statuten beschlossen\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_PRESIDENT_AND_FOUR_MEMBERS_FOREIGN_COUNTRIES = re.compile(
    r"^Administration:\s*(?P<name1>[^,]+),\s*nommé président,\s*"
    r"(?P<name2>[^,]+),\s*" + _FR_ORIGIN + r"(?P<origin2>[^,]+),\s*à\s+"
    r"(?P<place2>[^,]+),\s*(?P<country2>[A-Z]{1,3}),\s*"
    r"(?P<name3>[^,]+),\s*" + _FR_ORIGIN + r"(?P<origin3>[^,]+),\s*à\s+"
    r"(?P<place3>[^,]+),\s*(?P<country3>[A-Z]{1,3}),\s*"
    r"(?P<name4>[^,]+),\s*" + _FR_ORIGIN + r"(?P<origin4>[^,]+),\s*à\s+"
    r"(?P<place4>[^,]+),\s*(?P<country4>[A-Z]{1,3}),\s*et\s+"
    r"(?P<name5>[^,]+),\s*" + _FR_ORIGIN + r"(?P<origin5>[^,]+),\s*à\s+"
    r"(?P<place5>[^,]+),\s*(?P<country5>[A-Z]{1,3}),\s*tous les quatre\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_FOUNDATION_BOARD_MEMBER_WITH_PRESIDENT_OR_VICE_PRESIDENT = re.compile(
    r"^Nouveau membre du conseil de fondation avec avec le président ou la "
    r"vice-présidente:\s*(?P<name>[^,]+),\s*" + _FR_ORIGIN +
    r"(?P<origin>[^,]+),\s*à\s+(?P<place>[^,]+),\s*(?P<role>[^.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_PRESIDENT_SECRETARY_SIGN_INDIVIDUALLY = re.compile(
    r"^(?P<name1>[^,]+),\s*président,\s*et\s+(?P<name2>[^,]+),\s*secrétaire,\s*"
    r"tous deux gérants,\s*signent désormais individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_DIRECTORS_APPOINTED_CONTINUE_COLLECTIVE_SIGNING = re.compile(
    r"^(?P<name1>[^,]+)\s+et\s+(?P<name2>[^,]+),\s*nommés directeurs,\s*"
    r"continuent à signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_TO_TWO_EXISTING_ASSOCIATES_RUNNING_TOTALS = re.compile(
    r"^(?P<seller>[^,]+),\s*associé,\s*cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+),\s*par\s+"
    r"(?P<share1>[\d']+)\s+parts de CHF\s+(?P<nominal1>[\d'.]+)\s+à\s+"
    r"(?P<buyer1>[^,]+),\s*associé,\s*désormais titulaire de\s+"
    r"(?P<buyer1_count>[\d']+)\s+parts de CHF\s+(?P<buyer1_nominal>[\d'.]+),\s*"
    r"et\s+par\s+(?P<share2>[\d']+)\s+parts de CHF\s+(?P<nominal2>[\d'.]+)\s+à\s+"
    r"(?P<buyer2>[^,]+),\s*associé-gérant,\s*désormais titulaire de\s+"
    r"(?P<buyer2_count>[\d']+)\s+parts de CHF\s+(?P<buyer2_nominal>[\d'.]+)\.\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_CEDE_SHARES_TO_ASSOCIATE_APPOINTED_MANAGER = re.compile(
    r"^Les associés-gérants\s+(?P<seller1>[^,]+)\s+et\s+(?P<seller2>[^,]+)\s+"
    r"cèdent chacun\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+de leurs\s+(?P<before1>[\d']+)\s+et\s+"
    r"(?P<before2>[\d']+)\s+parts de CHF\s+(?P<nominal2>[\d'.]+)\s+respectives,\s*"
    r"à l['’]associé\s+(?P<buyer>[^,]+),\s*lequel est nommé gérant\s+"
    r"désormais titulaire de\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*(?P=seller1)\s+et\s+(?P=seller2)\s+"
    r"restent titulaires respectivement de\s+(?P<remaining1>[\d']+)\s+et\s+"
    r"(?P<remaining2>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_RECTIFICATIF_ORIGIN_CORRECTED_AS_PUBLISHED = re.compile(
    r"^Rectificatif:\s*l['’]inscription\s*n[o°]\s*(?P<entry>\d+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*(?P<notice_id>[\d/]+)\)\s+"
    r"est rectifiée en ce sens que\s+(?P<name>[^,]+?)\s+est originaire\s+" +
    _FR_ORIGIN + r"(?P<origin>[^(]+?)\s*\(et non\s+" + _FR_ORIGIN +
    r"(?P<previous_origin>[^)]+?)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


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


def extract_parser160_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 160."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_ENTITY_ASSET_TRANSFER_SHORT_FORM.search(leftover)
    if match:
        consume(match)
        consideration_raw = match.group("consideration").strip()
        if consideration_raw.lower() == "keine":
            consideration_extra = {"consideration": "keine", "gratuitous": True}
        else:
            amount = consideration_raw.split("CHF", 1)[1].strip()
            consideration_extra = {"consideration": amount, "gratuitous": False}
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.entity_asset_transfer_short_form.v1",
            {
                "transferor": match.group("transferor").strip(),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital",
                "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                **consideration_extra,
            },
        ))

    match = _DE_FOUNDATION_AUDIT_EXEMPTION_GRANTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "audit_requirement_changed", "de.text.foundation_audit_exemption_granted.v1",
            {
                "kind": "audit_exemption",
                "action": "granted",
                "scope": "foundation",
                "decision_date": _iso_date(match.group("date")),
                "authority": "Aufsichtsbehörde",
            },
        ))

    match = _FR_MANAGER_SPLITS_SHARES_TO_TWO_NEW_ASSOCIATES_NO_SIGNATURE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_splits_shares_to_two_new_associates_no_signature.v1"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("seller"),
            place=match.group("seller_origin"), role="associé-gérant",
            extra={
                "action": "shares_transferred",
                "shares_before": _count(match.group("before")),
                "shares_transferred": _count(match.group("transferred")),
                "shares_count": _count(match.group("remaining")),
                "share_nominal": match.group("remaining_nominal"),
            },
        ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("buyer1"),
            place=match.group("place1"), role="associé",
            extra={
                "action": "appointed_and_shares_received",
                "new_associate": True,
                "origin": match.group("origin1").strip(),
                "shares_received": _count(match.group("share1")),
                "shares_count": _count(match.group("share1")),
                "share_nominal": match.group("nominal1"),
                "without_signature": True,
            },
        ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("buyer2"),
            place=match.group("place2"), role="associé",
            extra={
                "action": "appointed_and_shares_received",
                "new_associate": True,
                "origin": match.group("origin2").strip(),
                "shares_received": _count(match.group("share2")),
                "shares_count": _count(match.group("share2")),
                "share_nominal": match.group("nominal2"),
                "without_signature": True,
            },
        ))

    match = _DE_BOARD_REMOVED_TWO_CHANGED_CORRECTED_AND_NEW.search(leftover)
    if match:
        consume(match)
        rule_id = "de.persons.board_removed_two_changed_corrected_and_new.v1"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_removed", rule_id, match.group("removed_name"),
            role=match.group("removed_role").strip(),
            signing=match.group("removed_sign"),
            extra={"action": "removed"},
        ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("name1"),
            role=match.group("new1_role").strip(),
            signing=match.group("new1_sign"),
            extra={
                "action": "role_changed",
                "previous_role": match.group("prev1_role").strip(),
                "previous_signing": match.group("prev1_sign"),
            },
        ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("name2_correct"),
            role=match.group("new2_role").strip(),
            signing=match.group("new2_sign"),
            extra={
                "action": "role_changed",
                "name_corrected": True,
                "previous_name": match.group("name2").strip(),
                "previous_role": match.group("prev2_role").strip(),
                "previous_signing": match.group("prev2_sign"),
            },
        ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("name3"),
            role=match.group("new3_role").strip(),
            signing=match.group("new3_sign"),
            extra={
                "action": "role_changed",
                "previous_role": match.group("prev3_role").strip(),
                "previous_signing": match.group("prev3_sign"),
            },
        ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("name4"),
            place=match.group("place4"), role=match.group("role4").strip(),
            signing=match.group("sign4"),
            extra={"action": "appointed", "heimat": match.group("place4").strip()},
        ))

    match = _DE_SOLE_SHAREHOLDER_REMOVED_REMAINING_INCREASED.search(leftover)
    if match:
        consume(match)
        rule_id = "de.persons.sole_shareholder_removed_remaining_increased.v1"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_removed", rule_id, match.group("removed_name"),
            role=match.group("removed_role").strip(),
            signing=match.group("removed_sign"),
            extra={
                "action": "removed",
                "shares_count": int(match.group("removed_count")),
                "share_nominal": match.group("removed_nominal"),
            },
        ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("name"),
            place=match.group("place"),
            role=f"{match.group('role_new').strip()}, {match.group('title_new').strip()}",
            signing=match.group("sign_new"),
            extra={
                "action": "shares_increased_and_relocated",
                "shares_before": int(match.group("before_count")),
                "shares_count": int(match.group("new_count")),
                "share_nominal": match.group("new_nominal"),
                "previous_role": f"{match.group('role').strip()}, {match.group('title').strip()}",
                "previous_signing": match.group("sign"),
            },
        ))

    match = _DE_SOLE_PROPRIETORSHIP_CONTRIBUTION_FRAGMENT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.sole_proprietorship_contribution_fragment.v1",
            {
                "kind": "contribution_in_kind",
                "action": "shares_issued",
                "source_kind": "einzelunternehmen",
                "source_name": match.group("name").strip(),
                "source_place": match.group("place").strip(),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "shares_issued": int(match.group("shares")),
                "share_nominal": match.group("nominal"),
                "currency": "CHF",
                "credited_amount": match.group("credit"),
            },
        ))

    match = _FR_TWO_DIRECTORS_INDIVIDUAL_SIGNATURE_SHARED_ORIGIN.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_directors_individual_signature_shared_origin.v1"
        for name_key, place_key in (("name1", "place1"), ("name2", "place2")):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(name_key),
                place=match.group(place_key), role=match.group("role").strip(),
                signing="individuelle",
                extra={
                    "action": "signature_granted",
                    "origin": match.group("origin").strip(),
                },
            ))

    match = _DE_AUTHORIZED_CAPITAL_HISTORY_DELETED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_history_deleted.v1",
            {
                "kind": "authorized_capital",
                "action": "history_deleted",
                "board_resolution_date": _iso_date(match.group("board_date")),
                "authorization_date": _iso_date(match.group("authorization_date")),
                "decision_date": _iso_date(match.group("decision_date")),
                "deleted": True,
            },
        ))

    match = _FR_BOARD_PRESIDENT_AND_FOUR_MEMBERS_FOREIGN_COUNTRIES.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.board_president_and_four_members_foreign_countries.v1"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("name1"),
            role="président", extra={"action": "appointed"},
        ))
        for name_key, origin_key, place_key, country_key in (
            ("name2", "origin2", "place2", "country2"),
            ("name3", "origin3", "place3", "country3"),
            ("name4", "origin4", "place4", "country4"),
            ("name5", "origin5", "place5", "country5"),
        ):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(name_key),
                place=match.group(place_key), role="membre du conseil d'administration",
                extra={
                    "action": "appointed",
                    "origin": match.group(origin_key).strip(),
                    "country": match.group(country_key),
                },
            ))

    match = _FR_NEW_FOUNDATION_BOARD_MEMBER_WITH_PRESIDENT_OR_VICE_PRESIDENT.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed",
            "fr.persons.new_foundation_board_member_with_president_or_vice_president.v1",
            match.group("name"), place=match.group("place"),
            role=f"membre du conseil de fondation, {match.group('role').strip()}",
            extra={
                "action": "appointed",
                "origin": match.group("origin").strip(),
                "co_signs_with": "président ou vice-présidente",
            },
        ))

    match = _FR_TWO_MANAGERS_PRESIDENT_SECRETARY_SIGN_INDIVIDUALLY.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_managers_president_secretary_sign_individually.v1"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", rule_id, match.group("name1"),
            role="gérant, président", signing="individuelle",
            extra={"action": "signing_changed"},
        ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", rule_id, match.group("name2"),
            role="gérant, secrétaire", signing="individuelle",
            extra={"action": "signing_changed"},
        ))

    match = _FR_TWO_DIRECTORS_APPOINTED_CONTINUE_COLLECTIVE_SIGNING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_directors_appointed_continue_collective_signing.v1"
        for key in ("name1", "name2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(key),
                role="directeur", signing="collectivement à deux",
                extra={"action": "appointed", "signing_continues": True},
            ))

    match = _FR_SHARE_TRANSFER_TO_TWO_EXISTING_ASSOCIATES_RUNNING_TOTALS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.share_transfer_to_two_existing_associates_running_totals.v1"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("seller"), role="associé",
            extra={
                "action": "shares_transferred",
                "shares_before": _count(match.group("before")),
                "shares_transferred": _count(match.group("transferred")),
                "shares_count": _count(match.group("remaining")),
                "share_nominal": match.group("remaining_nominal"),
            },
        ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("buyer1"), role="associé",
            extra={
                "action": "shares_received",
                "counterparty": match.group("seller").strip(),
                "shares_received": _count(match.group("share1")),
                "shares_count": _count(match.group("buyer1_count")),
                "share_nominal": match.group("buyer1_nominal"),
            },
        ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("buyer2"), role="associé-gérant",
            extra={
                "action": "shares_received",
                "counterparty": match.group("seller").strip(),
                "shares_received": _count(match.group("share2")),
                "shares_count": _count(match.group("buyer2_count")),
                "share_nominal": match.group("buyer2_nominal"),
            },
        ))

    match = _FR_TWO_MANAGERS_CEDE_SHARES_TO_ASSOCIATE_APPOINTED_MANAGER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_managers_cede_shares_to_associate_appointed_manager.v1"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("seller1"), role="associé-gérant",
            extra={
                "action": "shares_transferred",
                "shares_before": _count(match.group("before1")),
                "shares_transferred": _count(match.group("transferred")),
                "shares_count": _count(match.group("remaining1")),
                "share_nominal": match.group("remaining_nominal"),
            },
        ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("seller2"), role="associé-gérant",
            extra={
                "action": "shares_transferred",
                "shares_before": _count(match.group("before2")),
                "shares_transferred": _count(match.group("transferred")),
                "shares_count": _count(match.group("remaining2")),
                "share_nominal": match.group("remaining_nominal"),
            },
        ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("buyer"), role="gérant",
            extra={
                "action": "appointed_and_shares_received",
                "promoted": True,
                "shares_received": _count(match.group("transferred")) * 2,
                "shares_count": _count(match.group("buyer_count")),
                "share_nominal": match.group("buyer_nominal"),
            },
        ))

    match = _FR_RECTIFICATIF_ORIGIN_CORRECTED_AS_PUBLISHED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.rectificatif_origin_corrected_as_published.v1",
            {
                "kind": "person_origin",
                "action": "origin_corrected",
                "name": match.group("name").strip(),
                "origin": match.group("origin").strip(),
                "previous_origin": match.group("previous_origin").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        ))

    return events, re.sub(r"\s+", " ", leftover).strip(" .,;")
