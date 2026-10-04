from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_OWNER_BANKRUPTCY_APPEAL_SUSPENDED_HISTORY = re.compile(
    r"^Mit Verfügung vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+der Beschwerde des Inhabers gegen das "
    r"erstinstanzliche Konkurserkenntnis die aufschiebende Wirkung erteilt\.\s*"
    r"\[bisher:\s*Mit Entscheid des\s+(?P<previous_authority>.+?)\s+vom\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+wurde über den Inhaber "
    r"dieses Einzelunternehmens mit Wirkung ab dem\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}[:.]\d{2})\s+Uhr,\s*der Konkurs eröffnet\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATES_DOMICILE_PRESIDENCY_PAIR = re.compile(
    r"^L['’]associée\s+(?P<name1>[^,.;]+),\s*maintenant domiciliée à\s+"
    r"(?P<place1>[^,.;]+),\s*nommée présidente,\s*signe désormais "
    r"individuellement\.\s*L['’]associée gérante\s+(?P<name2>[^,.;]+),\s*"
    r"maintenant domiciliée à\s+(?P<place2>[^,.;]+),\s*"
    r"(?P<country2>[A-Z]{1,3}),\s*jusqu['’]ici présidente,\s*continue à signer "
    r"individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_PRESIDENT_OR_VICE = re.compile(
    r"^Nouvelle membre du conseil de fondation avec le président ou le "
    r"vice-président\s*:\s*(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_ORGANIZATION_REMOVED_NOT_REGISTRATION_TEXT = re.compile(
    r"^Organisation neu:\s*\[Streichung der Organisation von Amtes wegen,\s*"
    r"da nicht zum Eintragungstext gehörend\.\]\.?$",
    re.I | re.UNICODE,
)
_IT_COMPOSITION_MORATORIUM_EXTENDED = re.compile(
    r"^Con decreto della\s+(?P<authority>.+?)\s+del\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*la moratoria concordataria "
    r"è prorogata fino al\s+(?P<until>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_REMOVED = re.compile(
    r"^(?P<name>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+"
    r"n['’]est plus organe de révision\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_EXACT_NAME_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le nom exact du "
    r"gérant\s+(?P<previous_name>.+?)\s+est\s+(?P<name>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_REVOCATION_CORRECTED_DISSOLUTION_CONTINUES = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que,\s*par décision "
    r"du\s+(?P<decision_date>\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4}),\s*(?P<authority>.+?)\s+avait prononcé la "
    r"révocation de la faillite,\s*cette décision n['’]ayant pas d['’]effet sur "
    r"la dissolution précédemment déclarée\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_COLLECTIVE_EXCEPT_TWO = re.compile(
    r"^Nouveau membre du conseil de fondation toutefois pas avec\s+"
    r"(?P<excluded1>[^,.;]+?)\s+et\s+(?P<excluded2>[^:.;]+)\s*:\s*"
    r"(?P<name>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADDITIONAL_ADDRESS_SUPPLEMENTED = re.compile(
    r"^Complément:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée en ce sens que l['’]autre "
    r"adresse est\s+(?P<street>.+?),\s*(?P<postal_code>\d{4})\s+"
    r"(?P<locality>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_POSTAL_BOX_REMOVED = re.compile(
    r"^La case postale\s+(?P<box>[^,.;]+),\s*(?P<postal_code>\d{4})\s+"
    r"(?P<locality>[^,.;]+)\s+est radiée\.?$",
    re.I | re.UNICODE,
)
_FR_PROXIES_REVOKED_APPOINTED_DIRECTORS = re.compile(
    r"^(?P<name1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+),\s*dont la procuration "
    r"collective à deux est éteinte,\s*sont nommés directeurs\.?\s*"
    r"(?P=name2)\s+signe désormais sans restriction\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_ADMINISTRATOR_INDIVIDUAL = re.compile(
    r"^(?P<name>[^,.;]+),\s*désormais seule administratrice,\s*"
    r"signe maintenant individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_SHARE_TRANSFER_PRESIDENCY = re.compile(
    r"^Jusqu['’]ici titulaire de\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*l['’]associé-gérant\s+(?P<seller>[^,.;]+),\s*"
    r"nommé président,\s*détient\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\s+par suite de cession de\s+"
    r"(?P<transferred>[\d']+)\s+parts à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé-gérant pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_IT_BRANCH_RELOCATED_SAME_UID = re.compile(
    r"^Nuova succursale:\s*(?P<place>[^()]+?)\s*\((?P<canton>[A-Z]{2})\)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s*\[finora:\s*"
    r"(?P<previous_place>[^()]+?)\s*\((?P<previous_canton>[A-Z]{2})\)\s*"
    r"\((?P=uid)\)\]\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_REINSTATED_FOR_LIQUIDATION_BY_DECISION = re.compile(
    r"^Die am\s+(?P<deletion_date>\d{2}\.\d{2}\.\d{4})\s+gelöschte "
    r"Gesellschaft wird auf Grund des Entscheids der\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+zum Zwecke der Liquidation "
    r"wieder in das Handelsregister eingetragen und besteht entsprechend den "
    r"früheren Eintragungen weiter\.\s*\[gestrichen:\s*(?P<previous>.+)\]\.?$",
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
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _french_date(raw: str) -> str:
    day, month, year = raw.lower().replace("1er", "1", 1).split()
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
    uid: str | None = None,
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
        person_key=person_key(name=clean_name, place=clean_place, uid=uid),
        plz=plz,
        canton=canton,
        role=role,
        signing=signing,
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser146_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 146."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_OWNER_BANKRUPTCY_APPEAL_SUSPENDED_HISTORY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.owner_bankruptcy_appeal_suspensive_effect_history.v1",
            {
                "kind": "bankruptcy_effect_suspended", "scope": "owner",
                "action": "suspensive_effect_granted",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "effective_date": _iso_date(match.group("effective_date")),
                "effective_time": match.group("effective_time").replace(".", ":"),
                "previous_authority": match.group("previous_authority").strip(),
            },
        ))

    match = _FR_ASSOCIATES_DOMICILE_PRESIDENCY_PAIR.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.associates_domicile_presidency_pair.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="associée présidente",
                signing="Einzelunterschrift",
                extra={
                    "action": "domicile_changed_and_appointed_president",
                    "domicile_changed": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="associée gérante",
                signing="Einzelunterschrift",
                extra={
                    "action": "domicile_and_role_changed",
                    "previous_role": "présidente", "domicile_changed": True,
                    "country": match.group("country2"), "signing_continues": True,
                },
            ),
        ])

    match = _FR_FOUNDATION_MEMBER_PRESIDENT_OR_VICE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.foundation_member_signing_president_or_vice.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil de fondation",
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "appointed", "heimat": match.group("origin").strip(),
                "required_with": ["président", "vice-président"],
            },
        ))

    match = _DE_ORGANIZATION_REMOVED_NOT_REGISTRATION_TEXT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.organization_removed_not_registration_text.v1",
            {
                "action": "removed_from_registration_text", "by_authority": True,
                "reason": "not_part_of_registration_text",
            },
        ))

    match = _IT_COMPOSITION_MORATORIUM_EXTENDED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.composition_moratorium_extended_until.v1",
            {
                "kind": "composition_moratorium_extended", "action": "extended",
                "decision_date": _iso_date(match.group("decision_date")),
                "until": _iso_date(match.group("until")),
                "authority": match.group("authority").strip(),
            },
        ))

    match = _FR_AUDITOR_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_removed", "fr.persons.auditor_removed_with_uid.v1",
            match.group("name"), uid=match.group("uid"), role="organe de révision",
            extra={"action": "removed", "uid": match.group("uid")},
        ))

    match = _FR_MANAGER_EXACT_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.manager_exact_name_corrected_notice.v1",
            match.group("name"), role="gérant",
            extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_BANKRUPTCY_REVOCATION_CORRECTED_DISSOLUTION_CONTINUES.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed",
            "fr.text.bankruptcy_revocation_correction_dissolution_continues.v1",
            {
                "kind": "bankruptcy_revoked", "action": "publication_corrected",
                "decision_date": _french_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "dissolution_continues": True,
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_FOUNDATION_MEMBER_COLLECTIVE_EXCEPT_TWO.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.foundation_member_collective_except_two.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil de fondation",
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "appointed", "heimat": match.group("origin").strip(),
                "excluded_with": [
                    match.group("excluded1").strip(), match.group("excluded2").strip()
                ],
            },
        ))

    match = _FR_ADDITIONAL_ADDRESS_SUPPLEMENTED.search(leftover)
    if match:
        consume(match)
        address = (
            f"{match.group('street').strip()}, {match.group('postal_code')} "
            f"{match.group('locality').strip()}"
        )
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.additional_address_supplemented.v1",
            {
                "kind": "additional_address", "action": "added",
                "address": address, "street": match.group("street").strip(),
                "postal_code": match.group("postal_code"),
                "locality": match.group("locality").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
                "source_kind": "supplement",
            },
        ))

    match = _FR_POSTAL_BOX_REMOVED.search(leftover)
    if match:
        consume(match)
        address = (
            f"case postale {match.group('box').strip()}, "
            f"{match.group('postal_code')} {match.group('locality').strip()}"
        )
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.postal_box_removed.v1",
            {
                "kind": "postal_box", "action": "removed", "address": address,
                "postal_box": match.group("box").strip(),
                "postal_code": match.group("postal_code"),
                "locality": match.group("locality").strip(),
            },
        ))

    match = _FR_PROXIES_REVOKED_APPOINTED_DIRECTORS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.proxies_revoked_appointed_directors.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="directeur", signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "proxy_revoked_and_appointed_director",
                    "previous_signing": "Kollektivprokura zu zweien",
                    "proxy_revoked": True,
                },
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", rule_id, match.group("name2"),
            role="directeur", signing="Kollektivunterschrift zu zweien",
            extra={"action": "restriction_removed", "signing_continues": True},
        ))

    match = _FR_SOLE_ADMINISTRATOR_INDIVIDUAL.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.sole_administrator_individual.v1",
            match.group("name"), role="administratrice unique",
            signing="Einzelunterschrift",
            extra={"action": "role_and_signing_changed"},
        ))

    match = _FR_MANAGER_SHARE_TRANSFER_PRESIDENCY.search(leftover)
    if match and (
        _count(match.group("before"))
        == _count(match.group("remaining")) + _count(match.group("transferred"))
        and match.group("nominal") == match.group("remaining_nominal")
        == match.group("buyer_nominal")
        and match.group("transferred") == match.group("buyer_count")
    ):
        consume(match)
        rule_id = "fr.persons.manager_share_transfer_presidency_fragment.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant président",
                extra={
                    **common, "action": "appointed_president_and_shares_transferred",
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé-gérant", signing="Einzelunterschrift",
                extra={
                    **common, "action": "appointed_and_shares_received",
                    "counterparty": seller, "heimat": match.group("origin").strip(),
                    "new_associate": True,
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                },
            ),
        ])

    match = _IT_BRANCH_RELOCATED_SAME_UID.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "it.text.branch_relocated_same_uid.v1",
            {
                "action": "moved", "branch_uid": match.group("uid"),
                "from": match.group("previous_place").strip(),
                "from_canton": match.group("previous_canton").upper(),
                "to": match.group("place").strip(),
                "to_canton": match.group("canton").upper(),
            },
        ))

    match = _DE_COMPANY_REINSTATED_FOR_LIQUIDATION_BY_DECISION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.company_reinstated_for_liquidation_by_decision.v1",
            {
                "kind": "registration_reinstated", "action": "reinstated",
                "reason": "liquidation", "liquidation_only": True,
                "company_continues": True,
                "deletion_date": _iso_date(match.group("deletion_date")),
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "decision_document": "entscheid",
                "previous": match.group("previous").strip(),
            },
        ))

    return events, re.sub(r"\s+", " ", leftover).strip(" .;")
