from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_BOARD_MEMBERS_WITHOUT_SIGNING = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,.;]+)(?:,\s*(?P<country1>[A-Z]{1,3}))?,\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*"
    r"à\s+(?P<place2>[^,.;]+),\s*sont membres? du conseil d['’]administration;\s*"
    r"ils n['’]exercent pas la signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_ADMIN_PROXY_REVOKED = re.compile(
    r"^(?P<name>[^,.;]+)\s+est nommé(?:e)?\s+(?P<role>administrateur unique|"
    r"administratrice unique)\s*;\s*sa procuration est radiée\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_REINSTATED_AFTER_ERRONEOUS_ART_155_DELETION = re.compile(
    r"^Die aufgrund irrtümlich nach\s+(?P<legal_basis>Art\.\s*155\s+HRegV)\s+"
    r"eingeleitetem Verfahren am\s+(?P<deletion_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"gelöschte Gesellschaft wird entsprechend den früheren Eintragungen wieder in "
    r"das Handelsregister eingetragen\.\s*\[bisher:\s*(?P<previous>.+)\]\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_FR_PAIR_ORIGIN_CHANGED = re.compile(
    r"^(?P<name1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+)\s+sont (?:maintenant|désormais) "
    r"originaires de\s+(?P<origin>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_PAIR_DOMICILE_CHANGED = re.compile(
    r"^(?P<name1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+)\s+sont (?:maintenant|désormais) "
    r"à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_REPLACED_AFTER_EXHAUSTION = re.compile(
    r"^\[Streichung der Statutenbestimmung über die mit Ermächtigungsbeschluss vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+eingeführte genehmigte "
    r"Kapitalerhöhung infolge Ausschöpfung des Erhöhungsbetrages\.\]\s*\.?\s*"
    r"Die Gesellschaft hat mit Beschluss vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"eine genehmigte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten "
    r"beschlossen\.?$",
    re.I | re.UNICODE,
)
_DE_GRATUITOUS_REAL_ESTATE_TRANSFER = re.compile(
    r"^Vermögensübertragung:\s*Der\s+(?P<transferor_type>Verein|die Gesellschaft)\s+"
    r"überträgt gemäss Vertrag vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+unentgeltlich\s+"
    r"(?P<asset>.+?),\s*auf die\s+(?P<recipient>.+?),\s*in\s+(?P<place>.+?)\s+"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*Gegenleistung:\s*keine\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_FR_STATUTES_DATE_CORRECTION = re.compile(
    r"^L['’]inscription\s+(?:No|n°)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que les "
    r"statuts ont été modifiés le\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"\(et non pas le\s+(?P<previous_date>\d{2}\.\d{2}\.\d{4})\)\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_PROPRIETOR_BANKRUPTCY = re.compile(
    r"^\[gestrichen:\s*Über den Inhaber dieses Einzelunternehmens ist mit Verfügung "
    r"des\s+(?P<authority>.+?)\s+vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"mit Wirkung ab dem\s+(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<time>\d{1,2}[.:]\d{2})\s+Uhr,\s*der Konkurs eröffnet worden\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_ADDITIONAL_ADDRESSES = re.compile(
    r"^(?:Weitere Adresse:\s*[^.]+(?:\.\s*|$)){2,}$",
    re.I | re.UNICODE,
)
_DE_ADDITIONAL_ADDRESS_ITEM = re.compile(
    r"Weitere Adresse:\s*(?P<street>.*?),\s*(?P<postal_code>\d{4})\s+"
    r"(?P<locality>[^.]+?)(?=\.|$)",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_EFFECT_SUSPENDED_BY_CANTONAL_COURT = re.compile(
    r"^Par prononcé du\s+(?P<decision_date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4}),\s*(?P<authority>.+?)\s+a admis la requête "
    r"d['’]effet suspensif de la faillite rendue le\s+"
    r"(?P<bankruptcy_date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_LIQUIDATION_NAME_FRAGMENT = re.compile(
    r"^(?P<fragment>.+\b(?:AG|GmbH|Genossenschaft|Stiftung|Verein)\s+in Liquidation)$",
    re.I | re.UNICODE,
)
_DE_DELETION_AFTER_TAX_APPROVALS = re.compile(
    r"^Nachdem die Zustimmungen der Steuerverwaltungen eingegangen sind,\s*wird die "
    r"Firma im Handelsregister gelöscht\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBERS_PAIR = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*sont membres? du conseil,\s*tous deux\.?$",
    re.I | re.UNICODE,
)
_IT_PROPRIETOR_BANKRUPTCY_REVOKED = re.compile(
    r"^Il fallimento del titolare pronunciato con decreto del\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+dalla\s+"
    r"(?P<bankruptcy_court>.+?)\s+è stato annullato con decreto della\s+"
    r"(?P<authority>.+?)\s+del\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"La situazione è ristabilita come in precedenza\.\s*"
    r"\[radiati:\s*(?P<previous>.+?)\s*\]\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_FR_ADMINISTRATION_DIFFERENT_SIGNING = re.compile(
    r"^Administration:\s*(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<role1>président|présidente),\s*et\s*(?P<name2>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+)\.\s*Signature collective à deux du président ou "
    r"individuelle de l['’]autre membre du conseil d['’]administration\.?$",
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
    return f"{year}-{month}-{day}"


def _french_written_date(raw: str) -> str:
    day, month, year = raw.strip().lower().split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


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
        event_type="officer_changed",
        rule_id=rule_id,
        org_uid=org_uid,
        person_key=person_key(name=clean_name, place=clean_place),
        plz=plz,
        canton=canton,
        role=role,
        signing=signing,
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser70_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 70."""
    del language  # Historical records can contain a different language in this field.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_BOARD_MEMBERS_WITHOUT_SIGNING.search(leftover)
    if match:
        consume(match)
        for index in (1, 2):
            extra = {
                "action": "appointed",
                "heimat": match.group(f"origin{index}").strip(),
                "without_signature": True,
            }
            country = match.groupdict().get(f"country{index}")
            if country:
                extra["country"] = country
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "fr.persons.board_members_without_signing.v2",
                    match.group(f"name{index}"), place=match.group(f"place{index}"),
                    role="membre du conseil d'administration", extra=extra,
                )
            )

    match = _FR_SOLE_ADMIN_PROXY_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "fr.persons.sole_admin_proxy_revoked.v1", match.group("name"),
                role=match.group("role"),
                extra={"action": "appointed", "previous_signing": "procuration"},
            )
        )

    match = _DE_COMPANY_REINSTATED_AFTER_ERRONEOUS_ART_155_DELETION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.company_reinstated_erroneous_art155.v1",
                {
                    "kind": "registration_reinstated",
                    "reason": "erroneous_official_deletion_procedure",
                    "deletion_date": _iso_date(match.group("deletion_date")),
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                    "previous": match.group("previous").strip(),
                    "company_continues": True,
                },
            )
        )

    match = _FR_PAIR_ORIGIN_CHANGED.search(leftover)
    if match:
        consume(match)
        for group in ("name1", "name2"):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "fr.persons.pair_origin_changed.v1", match.group(group),
                    extra={
                        "action": "origin_changed",
                        "heimat": match.group("origin").strip(),
                        "origin_changed": True,
                    },
                )
            )

    match = _FR_PAIR_DOMICILE_CHANGED.search(leftover)
    if match:
        consume(match)
        for group in ("name1", "name2"):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "fr.persons.pair_domicile_changed.v1", match.group(group),
                    place=match.group("place"),
                    extra={"action": "domicile_changed", "domicile_changed": True},
                )
            )

    match = _DE_AUTHORIZED_CAPITAL_REPLACED_AFTER_EXHAUSTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.authorized_capital_replaced_exhausted.v1",
                {
                    "kind": "authorized_increase",
                    "action": "replaced_after_exhaustion",
                    "previous_authorization_date": _iso_date(match.group("previous_date")),
                    "date": _iso_date(match.group("date")),
                },
            )
        )

    match = _DE_GRATUITOUS_REAL_ESTATE_TRANSFER.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.gratuitous_real_estate_transfer.v1",
                {
                    "date": _iso_date(match.group("date")),
                    "asset": match.group("asset").strip(),
                    "asset_kind": "real_estate",
                    "transferor_type": match.group("transferor_type").lower(),
                    "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration": "keine",
                    "consideration_amount": None,
                    "gratuitous": True,
                },
            )
        )

    match = _FR_STATUTES_DATE_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "fr.text.statutes_date_correction.v1",
                {
                    "action": "date_corrected",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "date": _iso_date(match.group("date")),
                    "previous_date": _iso_date(match.group("previous_date")),
                },
            )
        )

    match = _DE_REMOVED_PROPRIETOR_BANKRUPTCY.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.proprietor_bankruptcy_removed.v1",
                {
                    "kind": "bankruptcy",
                    "action": "removed",
                    "scope": "sole_proprietor",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "effective_date": _iso_date(match.group("effective_date")),
                    "effective_time": match.group("time"),
                    "authority": match.group("authority").strip(),
                },
            )
        )

    match = _DE_ADDITIONAL_ADDRESSES.search(leftover)
    if match:
        address_matches = list(_DE_ADDITIONAL_ADDRESS_ITEM.finditer(match.group(0)))
        if len(address_matches) >= 2:
            consume(match)
            for address_match in address_matches:
                street = address_match.group("street").strip()
                postal_code = address_match.group("postal_code")
                locality = address_match.group("locality").strip()
                events.append(
                    _event(
                        publication_id, published_at, org_uid, plz, canton,
                        "address_changed", "de.text.additional_addresses_sequence.v2",
                        {
                            "action": "added",
                            "address": f"{street}, {postal_code} {locality}",
                            "street": street,
                            "postal_code": postal_code,
                            "locality": locality,
                        },
                    )
                )

    match = _FR_BANKRUPTCY_EFFECT_SUSPENDED_BY_CANTONAL_COURT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "fr.text.bankruptcy_effect_suspended_request.v1",
                {
                    "kind": "bankruptcy_effect_suspended",
                    "decision_date": _french_written_date(match.group("decision_date")),
                    "bankruptcy_date": _french_written_date(match.group("bankruptcy_date")),
                    "authority": match.group("authority").strip(),
                    "request_granted": True,
                },
            )
        )

    match = _DE_LIQUIDATION_NAME_FRAGMENT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.liquidation_name_fragment.v1",
                {
                    "kind": "liquidation",
                    "action": "indicated_by_company_name",
                    "name_fragment": match.group("fragment").strip(),
                },
            )
        )

    match = _DE_DELETION_AFTER_TAX_APPROVALS.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_deleted", "de.text.deletion_after_tax_approvals.v1",
                {"reason": "tax_authority_approvals_received"},
            )
        )

    match = _FR_BOARD_MEMBERS_PAIR.search(leftover)
    if match:
        consume(match)
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "fr.persons.board_members_pair.v2", match.group(f"name{index}"),
                    place=match.group(f"place{index}"), role="membre du conseil",
                    extra={
                        "action": "appointed",
                        "heimat": match.group(f"origin{index}").strip(),
                    },
                )
            )

    match = _IT_PROPRIETOR_BANKRUPTCY_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "it.text.proprietor_bankruptcy_revoked.v1",
                {
                    "kind": "bankruptcy_revoked",
                    "scope": "sole_proprietor",
                    "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                    "decision_date": _iso_date(match.group("decision_date")),
                    "bankruptcy_court": match.group("bankruptcy_court").strip(),
                    "authority": match.group("authority").strip(),
                    "previous_status_restored": True,
                    "previous": match.group("previous").strip(),
                },
            )
        )

    match = _FR_ADMINISTRATION_DIFFERENT_SIGNING.search(leftover)
    if match:
        consume(match)
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "fr.persons.administration_different_signing.v1",
                    match.group("name1"), place=match.group("place1"),
                    role=match.group("role1"), signing="Kollektivunterschrift zu zweien",
                    extra={
                        "action": "appointed",
                        "heimat": match.group("origin1").strip(),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "fr.persons.administration_different_signing.v1",
                    match.group("name2"), place=match.group("place2"),
                    role="membre du conseil d'administration",
                    signing="Einzelunterschrift",
                    extra={
                        "action": "appointed",
                        "heimat": match.group("origin2").strip(),
                    },
                ),
            ]
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
