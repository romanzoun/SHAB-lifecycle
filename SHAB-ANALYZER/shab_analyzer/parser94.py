from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_SHAREHOLDER_COMMUNICATIONS_AND_STATUTES = re.compile(
    r"^Mitteilung an die Aktionäre:\s*(?P<mode>[^.]+)\.\s*"
    r"Statuten geändert am\s+(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_SOLE_PROPRIETOR_DELETION_REVOKED_NONCOMMENCEMENT = re.compile(
    r"^Die Löschung dieses Einzelunternehmens erfolgte irrtümlich und wird in "
    r"allen Teilen widerrufen\.\s*Das Einzelunternehmen besteht gemäss den "
    r"früheren Einträgen weiter\.\s*\[bisher:\s*(?P<previous>Das "
    r"Einzelunternehmen wird infolge Nichtaufnahme des Geschäftsbetriebes "
    r"gelöscht\.)\]\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_THREE_TWO_PLACES = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommée\s+"
    r"(?P<president_role>présidente),\s*(?P<member1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*et\s+(?P<member2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*(?P<country2>[^,.;]+),\s*tous deux des\s+"
    r"(?P<origin>[^,.;]+),\s*lesquels signent\s+"
    r"(?P<sign>collectivement à deux)\.?$",
    re.I | re.UNICODE,
)
_DE_SOLE_PROPRIETOR_BUSINESS_UNIT_TRANSFER = re.compile(
    r"^Vermögensübertragung:\s*Der Geschäftsinhaber überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+den Betriebsteil\s+"
    r"(?P<business_unit>.+?)\s+mit Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+"
    r"auf die\s+(?P<recipient>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"in\s+(?P<place>[^.]+)\.\s*Gegenleistung:\s*(?P<share_count>[\d']+)\s+"
    r"Stammanteile zu CHF\s+(?P<share_nominal>[\d'.]+)\s+und Gutschrift einer "
    r"Forderung von CHF\s+(?P<receivable>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_PEOPLE_INDIVIDUAL_SIGNING_TYPO = re.compile(
    r"^(?P<name1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+)\s+signent désormais\s+"
    r"(?P<sign>individuellment)\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDATION_TRANSFER_CONTRACT_AND_ORDER = re.compile(
    r"^Vermögensübertragung:\s*Die Stiftung überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+und Verfügung der Aufsichtsbehörde vom\s+"
    r"(?P<order_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven \(Fremdkapital\) von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>keine)\.?$",
    re.I | re.UNICODE,
)
_IT_HEAD_OFFICE_IDENTIFIER_AND_SEAT_NO_HISTORY = re.compile(
    r"^,?\s*Sede principale a:\s*(?P<context_seat>[^.]+)\.\s*"
    r"Nuovo numero di identificazione della sede principale:\s*"
    r"(?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\.\s*Nuova sede principale:\s*"
    r"(?P<seat>[^\[]+?)\s*\[finora:\s*(?P<previous_seat>[^\]]+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_SUPPLEMENT_SINGLE_APPOINTMENT = re.compile(
    r"^Complément:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_page>[\d/]+)\)\s+est complétée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+est nommé\s+(?P<role>directeur adjoint)\.?$",
    re.I | re.UNICODE,
)
_DE_COOPERATIVE_SHARE_CERTIFICATES_CONTINUATION = re.compile(
    r"^,\s*CHF\s+(?P<current2>[\d'.]+),\s*CHF\s+(?P<current3>[\d'.]+)\s*"
    r"\[bisher:\s*CHF\s+(?P<previous1>[\d'.]+),\s*CHF\s+"
    r"(?P<previous2>[\d'.]+),\s*CHF\s+(?P<previous3>[\d'.]+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_SUPPLEMENT_DOUBLE_APPOINTMENT = re.compile(
    r"^Complément:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_page>[\d/]+)\)\s+est complétée en ce sens que\s+"
    r"(?P<name1>[^,.;]+)\s+est nommé\s+(?P<role1>président)\s+et\s+"
    r"(?P<name2>[^,.;]+)\s+(?P<role2>vice-président)\.?$",
    re.I | re.UNICODE,
)
_FR_BEARER_CONVERSION_NOMINAL_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_page>[\d/]+)\)\s+est rectifiée en ce sens que les\s+"
    r"(?P<count>[\d']+)\s+actions au porteur de CHF\s+(?P<nominal>[\d'.]+)\s+"
    r"\(et non de CHF\s+(?P<previous_nominal>[\d'.]+)\s+comme publié\),\s*"
    r"formant l['’]entier du capital-actions,\s*sont converties en\s+"
    r"(?P<to_count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<to_nominal>[\d'.]+)\s+\(et non de CHF\s+"
    r"(?P<previous_to_nominal>[\d'.]+)\s+comme publié\),?\.?$",
    re.I | re.UNICODE,
)
_FR_MORATORIUM_EXTENDED_WRITTEN_DURATION = re.compile(
    r"^Par prononcé rendu le\s+(?P<decision_date>\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4}),\s*(?P<authority>.+?)\s+a prolongé de\s+"
    r"(?P<duration>six)\s+mois le sursis concordataire accordé à la société,\s*"
    r"soit jusqu['’]au\s+(?P<until>\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_LIMITED_PARTNERS = re.compile(
    r"^Nouveaux associés commanditaires:\s*(?P<name1>[^,.;]+),\s*de\s+"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<country1>[A-Z]{2,3}),\s*(?P<name2>[^,.;]+),\s*de\s+"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*et\s+"
    r"(?P<name3>[^,.;]+),\s*de\s+(?P<origin3>[^,.;]+),\s*à\s+"
    r"(?P<place3>[^,.;]+),\s*chacun avec une commandite de CHF\s+"
    r"(?P<amount>[\d'.]+);\s*ils n['’]exercent pas la signature sociale\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_INVENTORY_RECEIVABLE = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+und Inventar per\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven \(Fremdkapital\) von CHF\s+"
    r"(?P<liabilities>[\d'.]+),?\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*Forderung von CHF\s+(?P<receivable>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_UID_CORRECTED_SPACE = re.compile(
    r"^Rectification de l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\):\s*le numéro IDE correct est\s+"
    r"(?P<to>CHE[ -]\d{3}\.\d{3}\.\d{3})\s*\(et non pas\s+"
    r"(?P<from>CHE[ -]\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_DE_LIQUIDATION_END_REPORT_CORRECTED = re.compile(
    r"^\[Gemäss Mitteilung der einzigen Liquidatorin ist die Liquidation,\s*"
    r"entgegen der früheren Meldung,\s*noch nicht beendet\.\]\s*"
    r"\[gestrichen:\s*Liquidation beendet\.\]\.?$",
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
    day, month, year = raw.lower().replace("1er", "1").split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _uid(raw: str) -> str:
    return re.sub(r"^CHE[ -]", "CHE-", raw.strip(), flags=re.I).upper()


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


def extract_parser94_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 94."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_SHAREHOLDER_COMMUNICATIONS_AND_STATUTES.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.shareholder_communications_and_statutes.v1"
        events.extend(
            [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "organization_changed", rule_id,
                    {
                        "kind": "communications",
                        "audience": "shareholders",
                        "to": match.group("mode").strip(),
                    },
                ),
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "statutes_changed", rule_id,
                    {"date": _iso_date(match.group("date"))},
                ),
            ]
        )

    match = _DE_SOLE_PROPRIETOR_DELETION_REVOKED_NONCOMMENCEMENT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed",
                "de.text.sole_proprietor_deletion_revoked_noncommencement.v1",
                {
                    "kind": "registration_reinstated",
                    "action": "deletion_revoked",
                    "scope": "sole_proprietor",
                    "reason": "erroneous_deletion",
                    "previous_reason": "business_not_commenced",
                    "business_continues": True,
                    "removed_fact": match.group("previous").strip(),
                },
            )
        )

    match = _FR_ADMINISTRATION_THREE_TWO_PLACES.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_three_two_places.v1"
        signing = "Kollektivunterschrift zu zweien"
        people = (
            (match.group("president"), None, match.group("president_role"), {}),
            (
                match.group("member1"), match.group("place1"),
                "membre du conseil d'administration",
                {"heimat": match.group("origin").strip()},
            ),
            (
                match.group("member2"), match.group("place2"),
                "membre du conseil d'administration",
                {
                    "heimat": match.group("origin").strip(),
                    "country": match.group("country2").strip(),
                },
            ),
        )
        for name, place, role, extra in people:
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, name, place=place, role=role,
                    signing=signing, extra={"action": "appointed", **extra},
                )
            )

    match = _DE_SOLE_PROPRIETOR_BUSINESS_UNIT_TRANSFER.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.sole_proprietor_business_unit_transfer.v1",
                {
                    "source_kind": "sole_proprietor",
                    "date": _iso_date(match.group("date")),
                    "business_unit": match.group("business_unit").strip(),
                    "assets": match.group("assets"),
                    "liabilities": None,
                    "currency": "CHF",
                    "recipient": match.group("recipient").strip(),
                    "recipient_uid": match.group("uid"),
                    "recipient_place": match.group("place").strip(),
                    "consideration": {
                        "share_kind": "Stammanteile",
                        "share_count": _count(match.group("share_count")),
                        "share_nominal": match.group("share_nominal"),
                        "receivable": match.group("receivable"),
                        "currency": "CHF",
                    },
                },
            )
        )

    match = _FR_TWO_PEOPLE_INDIVIDUAL_SIGNING_TYPO.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_people_individual_signing_typo.v1"
        for group in ("name1", "name2"):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", rule_id, match.group(group),
                    signing="Einzelunterschrift",
                    extra={"action": "signing_changed", "source_spelling": match.group("sign")},
                )
            )

    match = _DE_FOUNDATION_TRANSFER_CONTRACT_AND_ORDER.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.foundation_asset_transfer_contract_order.v1",
                {
                    "source_kind": "foundation",
                    "date": _iso_date(match.group("date")),
                    "supervisory_order_date": _iso_date(match.group("order_date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "currency": "CHF",
                    "recipient": match.group("recipient").strip(),
                    "recipient_uid": match.group("uid"),
                    "recipient_place": match.group("place").strip(),
                    "consideration": None,
                    "gratuitous": True,
                },
            )
        )

    match = _IT_HEAD_OFFICE_IDENTIFIER_AND_SEAT_NO_HISTORY.search(leftover)
    if match:
        consume(match)
        rule_id = "it.text.head_office_identifier_and_seat_no_history.v1"
        events.extend(
            [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "company_identifier_changed", rule_id,
                    {
                        "scope": "head_office",
                        "action": "assigned",
                        "to": match.group("uid"),
                    },
                ),
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "seat_changed", rule_id,
                    {
                        "scope": "head_office",
                        "from": match.group("previous_seat").strip(),
                        "to": match.group("seat").strip(),
                        "context_seat": match.group("context_seat").strip(),
                    },
                ),
            ]
        )

    match = _FR_SUPPLEMENT_SINGLE_APPOINTMENT.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.supplemented_single_appointment.v1",
                match.group("name"), role=match.group("role"),
                extra={
                    "action": "appointed",
                    "publication_action": "supplemented",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_page": match.group("notice_page"),
                },
            )
        )

    match = _DE_COOPERATIVE_SHARE_CERTIFICATES_CONTINUATION.search(leftover)
    if match:
        consume(match)
        previous = [
            match.group("previous1"),
            match.group("previous2"),
            match.group("previous3"),
        ]
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.cooperative_share_certificates_continuation.v1",
                {
                    "kind": "cooperative_share_certificates",
                    "currency": "CHF",
                    "from_nominals": previous,
                    "to_nominals": [
                        previous[0],
                        match.group("current2"),
                        match.group("current3"),
                    ],
                },
            )
        )

    match = _FR_SUPPLEMENT_DOUBLE_APPOINTMENT.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.supplemented_double_appointment.v1"
        reference = {
            "publication_action": "supplemented",
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_page": match.group("notice_page"),
        }
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    role=match.group(f"role{index}"),
                    extra={"action": "appointed", **reference},
                )
            )

    match = _FR_BEARER_CONVERSION_NOMINAL_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.bearer_conversion_nominal_corrected.v1",
                {
                    "kind": "bearer_to_registered_conversion",
                    "action": "corrected",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_page": match.group("notice_page"),
                    "from_count": _count(match.group("count")),
                    "from_kind": "actions au porteur",
                    "from_nominal": match.group("nominal"),
                    "to_count": _count(match.group("to_count")),
                    "to_kind": "actions nominatives",
                    "to_nominal": match.group("to_nominal"),
                    "previous_from_nominal": match.group("previous_nominal"),
                    "previous_to_nominal": match.group("previous_to_nominal"),
                    "currency": "CHF",
                },
            )
        )

    match = _FR_MORATORIUM_EXTENDED_WRITTEN_DURATION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "fr.text.composition_moratorium_extended_written.v1",
                {
                    "kind": "composition_moratorium_extended",
                    "decision_date": _french_date(match.group("decision_date")),
                    "until": _french_date(match.group("until")),
                    "duration_months": 6,
                    "authority": match.group("authority").strip(),
                },
            )
        )

    match = _FR_THREE_LIMITED_PARTNERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.three_limited_partners.v1"
        for index in (1, 2, 3):
            extra = {
                "action": "appointed",
                "heimat": match.group(f"origin{index}").strip(),
                "limited_partnership_contribution": match.group("amount"),
                "currency": "CHF",
                "without_signature": True,
            }
            if index == 1:
                extra["country_code"] = match.group("country1").upper()
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    place=match.group(f"place{index}"), role="associé commanditaire",
                    extra=extra,
                )
            )

    match = _DE_ASSET_TRANSFER_INVENTORY_RECEIVABLE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.asset_transfer_inventory_receivable.v1",
                {
                    "date": _iso_date(match.group("date")),
                    "inventory_date": _iso_date(match.group("inventory_date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "currency": "CHF",
                    "recipient": match.group("recipient").strip(),
                    "recipient_uid": match.group("uid"),
                    "recipient_place": match.group("place").strip(),
                    "consideration_kind": "receivable",
                    "consideration": match.group("receivable"),
                },
            )
        )

    match = _FR_UID_CORRECTED_SPACE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_identifier_changed", "fr.text.company_identifier_corrected_space.v1",
                {
                    "scope": "organization",
                    "action": "corrected",
                    "from": _uid(match.group("from")),
                    "to": _uid(match.group("to")),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_id": match.group("notice_id"),
                },
            )
        )

    match = _DE_LIQUIDATION_END_REPORT_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.liquidation_end_report_corrected.v1",
                {
                    "kind": "liquidation_continues",
                    "action": "end_report_corrected",
                    "liquidation_ended": False,
                    "source": "sole_liquidator_notification",
                },
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
