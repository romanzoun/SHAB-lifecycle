from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_DE_NEW_REGISTERED_PERSON_WITHOUT_ROLE = re.compile(
    r"^Neue eingetragene Person:\s*(?P<name>[^,.;]+),\s*von\s+"
    r"(?P<origin>[^,.;]+),\s*in\s+(?P<place>[^,.;]+),\s*"
    r"(?P<signing>Einzelunterschrift|Kollektivunterschrift(?: zu zweien)?)\.?$",
    re.I | re.UNICODE,
)
_DE_SHARES_ROLES_AND_NEW_DOMICILE = re.compile(
    r"^Eingetragene Person geändert:\s*(?P<name>[^,.;]+),\s*"
    r"(?P<role1>Gesellschafter(?:in)?),\s*(?P<count>[\d']+)\s+"
    r"Stammanteile zu CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"(?P<role2>Geschäftsführer(?:in)?),\s*"
    r"(?P<signing>Einzelunterschrift|Kollektivunterschrift(?: zu zweien)?),\s*"
    r"neu in\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_COMMITTEE_MEMBER_NAME_CORRECTED = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que "
    r"(?:la|le) membre du comité porte le nom de\s+(?P<name>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_TRANSFER_TO_NEW_UNSIGNED_ASSOCIATE = re.compile(
    r"^Les associés-gérants\s+(?P<seller1>[^,.;]+),\s*maintenant de\s+"
    r"(?P<seller1_origin>[^,.;]+),\s*à\s+(?P<seller1_place>[^,.;]+),\s*et\s+"
    r"(?P<seller2>[^,.;]+),\s*cèdent chacun\s+"
    r"(?P<transferred>[\d']+)\s+parts de leurs\s+(?P<before>[\d']+)\s+"
    r"parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<buyer_origin>[^,.;]+),\s*"
    r"à\s+(?P<buyer_place>[^,.;]+),\s*nouvel associé sans signature,\s*"
    r"avec\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*(?P=seller1)\s+et\s+"
    r"(?P=seller2)\s+restent titulaires de\s+(?P<remaining>[\d']+)\s+"
    r"parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\s+chacun\.?$",
    re.I | re.UNICODE,
)
_DE_PERSON_CORRECTION_ROLES_DOMICILE_LIQUIDATOR = re.compile(
    r"^Mit dem im SHAB Nr\.\s*(?P<issue>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{1,2}\.\s+[A-Za-zÄÖÜäöü]+\s+\d{4})\s+"
    r"publizierten TR-Nr\.\s*(?P<entry>[\d']+)\s+vom\s+"
    r"(?P<entry_date>\d{1,2}\.\s+[A-Za-zÄÖÜäöü]+\s+\d{4})\s+"
    r"wurde der bisherige Text nicht richtig publiziert\.\s*Korrekt wäre:\s*"
    r"(?P<name>[^,.;]+,\s*[^,.;]+),\s*von\s+(?P<origin>[^,.;]+),\s*"
    r"in\s+(?P<place>[^,.;]+),\s*(?P<role>Gesellschafter(?:in)? und "
    r"Geschäftsführer(?:in)? und Liquidator(?:in)?),\s*mit\s+"
    r"(?P<signing>Einzelunterschrift)\s*\[bisher:\s*in\s+"
    r"(?P<previous_place>[^,.;]+),\s*(?P<previous_role>Gesellschafter(?:in)? "
    r"und Geschäftsführer(?:in)?)\s+mit\s+"
    r"(?P<previous_signing>Einzelunterschrift)\]\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_ADMINISTRATORS_WITHOUT_SIGNATURE = re.compile(
    r"^Nouveaux administrateurs sans signature:\s*"
    r"(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*et\s+"
    r"(?P<name3>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_CAPITAL_THREE_PARTS_CORPORATE_TRANSFER = re.compile(
    r"^Le capital social de CHF\s+(?P<capital>[\d'.]+)\s+est désormais "
    r"divisé en\s+(?P<count1>[\d']+)\s+parts? sociales? de CHF\s+"
    r"(?P<nominal1>[\d'.]+),\s*(?P<count2>[\d']+)\s+parts? sociales? "
    r"de CHF\s+(?P<nominal2>[\d'.]+)\s+et\s+(?P<count3>[\d']+)\s+"
    r"parts? sociales? de CHF\s+(?P<nominal3>[\d'.]+),\s*détenues par\s+"
    r"(?P<seller>[^,.;]+)\.\s*(?P=seller)\s+cède sa part de CHF\s+"
    r"(?P<transferred_nominal>[\d'.]+)\s+à\s+(?P<buyer>.+?)\s*"
    r"\((?P<buyer_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<buyer_place>[^,.;]+),\s*nouvelle associée avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts? de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+);\s*(?P=seller)\s+reste titulaire de\s+"
    r"(?P<remaining_count1>[\d']+)\s+parts? de CHF\s+"
    r"(?P<remaining_nominal1>[\d'.]+)\s+et\s+"
    r"(?P<remaining_count2>[\d']+)\s+parts? de CHF\s+"
    r"(?P<remaining_nominal2>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_IT_ASSET_TRANSFER_CASH_CONSIDERATION = re.compile(
    r"^Trasferimento di patrimonio:\s*secondo contratto del\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+la società ha trasferito "
    r"alla\s+(?P<recipient>.+?),\s*(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*attivi per CHF\s+"
    r"(?P<assets>[\d'.]+)\s+e passivi verso terzi per CHF\s+"
    r"(?P<liabilities>[\d'.]+)\.\s*Controprestazione:\s*CHF\s+"
    r"(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_CORRECTED_WITH_NOTICE = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\)\s+est rectifiée dans le sens:\s*"
    r"(?P<name>[^,.;]+),\s*(?P<role>administrateur|administratrice),\s*"
    r"(?P<signing>signature individuelle)\s*\(et non pas\s+"
    r"(?P<previous_signing>signature collective à deux)\)\.?$",
    re.I | re.UNICODE,
)
_DE_SOLE_PROPRIETOR_ASSET_TRANSFER_WITHOUT_CONSIDERATION = re.compile(
    r"^Vermögensübertragung:\s*Der Geschäftsinhaber überträgt gemäss "
    r"Vertrag vom\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven "
    r"von CHF\s+(?P<assets>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*"
    r"in\s+(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>keine)\.?$",
    re.I | re.UNICODE,
)
_DE_PLURAL_PERSON_DOMICILE_CHANGED = re.compile(
    r"^Eingetragene Personen geändert:\s*(?P<name>[^,.;]+),\s*"
    r"(?P<signing>Kollektivunterschrift(?: zu zweien)?|Einzelunterschrift),\s*"
    r"nun in\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TRANSFER_RESTRICTION_AND_COMMUNICATIONS_REMOVED = re.compile(
    r"^Les\s+(?P<count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+ne sont plus restreintes quant à leur "
    r"transmissibilité selon les statuts\.\s*Complément:\s*"
    r"l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée en ce sens que les statuts "
    r"ne prévoient plus de clause particulière au sujet du mode de "
    r"communications aux actionnaires\.?$",
    re.I | re.UNICODE,
)
_DE_HEAD_OFFICE_SHARE_CAPITAL_AND_PAID_CHANGED = re.compile(
    r"^Kapital Hauptsitz neu:\s*(?P<currency>[A-Z]{3})\s+"
    r"(?P<to_capital>[\d'.]+);\s*Liberierung:\s*"
    r"(?P<to_paid_currency>[A-Z]{3})\s+(?P<to_paid>[\d'.]+)\s*"
    r"\[bisher:\s*Kapital Hauptsitz:\s*Aktienkapital:\s*"
    r"(?P<from_currency>[A-Z]{3})\s+(?P<from_capital>[\d'.]+)\.\s*"
    r"Liberierung:\s*(?P<from_paid_currency>[A-Z]{3})\s+"
    r"(?P<from_paid>[\d'.]+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_REMOVED_THREE_ASSOCIATES = re.compile(
    r"^(?P<removed1>[^,;]+),\s*(?P<removed2>[^,;]+)\s+ne sont plus "
    r"associés ni gérants;\s*leurs pouvoirs sont radiés;\s*leurs\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+"
    r"ont été cédées à\s+(?P<buyer1>[^,.;]+),\s*maintenant associée "
    r"pour\s+(?P<count1>[\d']+)\s+parts de CHF\s+(?P<nominal1>[\d'.]+),\s*"
    r"à\s+(?P<buyer2>[^,.;]+),\s*maintenant associé pour\s+"
    r"(?P<count2>[\d']+)\s+parts de CHF\s+(?P<nominal2>[\d'.]+),\s*et\s+"
    r"à\s+(?P<buyer3>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+),\s*nouvelle associée "
    r"pour\s+(?P<count3>[\d']+)\s+parts de CHF\s+(?P<nominal3>[\d'.]+)\.\s*"
    r"Gérants:\s*les associés\s+(?P=buyer1),\s*maintenant présidente,\s*"
    r"et\s+(?P=buyer2),\s*tous deux désormais avec signature individuelle,\s*"
    r"ainsi que\s+(?P=buyer3)\s+avec signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_REINSTATED_IN_LIQUIDATION_WITH_OFFICE = re.compile(
    r"^Die am\s+(?P<deletion_date>\d{2}\.\d{2}\.\d{4})\s+gelöschte "
    r"Gesellschaft\s*\(SHAB Nr\.\s*(?P<issue>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\)\s+wird auf Grund des "
    r"Entscheides vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+als in "
    r"Liquidation befindlich wieder in das Handelsregister eingetragen\.\s*"
    r"\[bisher:\s*Das Konkursverfahren wurde mit Entscheid vom\s+"
    r"(?P<bankruptcy_closed_date>\d{2}\.\d{2}\.\d{4})\s+als geschlossen "
    r"erklärt\.\s*Die Gesellschaft wird von Amtes wegen gelöscht\.\]\.?\s*"
    r"Liquidator:\s*(?P<liquidator>[^,.;]+),\s*(?P<street>[^,.;]+),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_DEFINITIVE_MORATORIUM_WITH_COMMISSIONER_UNTIL = re.compile(
    r"^Par prononcé rendu le\s+"
    r"(?P<decision_date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"(?P<authority>.+?)\s+a accordé à la société un sursis concordataire "
    r"définitif jusqu['’]au\s+"
    r"(?P<until>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.\s*"
    r"(?P<commissioner>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*est désigné "
    r"commissaire au sursis\.?$",
    re.I | re.UNICODE,
)


_GERMAN_MONTHS = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}
_FRENCH_MONTHS = {
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


def _word_date(raw: str, months: dict[str, int]) -> str:
    day, month, year = raw.casefold().replace("1er", "1").replace(".", "", 1).split()
    return f"{int(year):04d}-{months[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _amount(raw: str) -> Decimal:
    return Decimal(raw.replace("'", ""))


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
        role=role.strip() if role else None,
        signing=signing,
        payload={
            "name": clean_name,
            "place": clean_place,
            **({"uid": uid} if uid else {}),
            **(extra or {}),
        },
    )


def extract_parser248_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 248."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_NEW_REGISTERED_PERSON_WITHOUT_ROLE.fullmatch(leftover)
    if match:
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "de.persons.new_registered_without_role.v1",
                match.group("name"), place=match.group("place"),
                signing=match.group("signing"), extra={
                    "action": "appointed", "origin": match.group("origin").strip(),
                },
            )
        ], ""

    match = _DE_SHARES_ROLES_AND_NEW_DOMICILE.fullmatch(leftover)
    if match:
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "de.persons.shares_roles_domicile_changed.v1",
                match.group("name"), place=match.group("place"),
                role=f"{match.group('role1')}, {match.group('role2')}",
                signing=match.group("signing"), extra={
                    "action": "domicile_changed",
                    "shares_count": _count(match.group("count")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            )
        ], ""

    match = _FR_COMMITTEE_MEMBER_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.committee_member_name_corrected.v1",
                match.group("name"), role="membre du comité", extra={
                    "action": "name_corrected", "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                },
            )
        ], ""

    match = _FR_TWO_MANAGERS_TRANSFER_TO_NEW_UNSIGNED_ASSOCIATE.fullmatch(leftover)
    if match:
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        remaining = _count(match.group("remaining"))
        buyer_count = _count(match.group("buyer_count"))
        if not (
            before - transferred == remaining
            and transferred * 2 == buyer_count
            and len({
                match.group("nominal"), match.group("buyer_nominal"),
                match.group("remaining_nominal"),
            }) == 1
        ):
            return [], leftover
        rule_id = "fr.persons.two_managers_transfer_to_new_unsigned_associate.v1"
        common = {
            "shares_before": before, "shares_transferred": transferred,
            "shares_count": remaining, "share_nominal": match.group("nominal"),
            "currency": "CHF", "counterparty": match.group("buyer").strip(),
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller1"),
                place=match.group("seller1_place"), role="associé-gérant",
                extra={
                    **common, "action": "origin_domicile_and_shares_changed",
                    "origin": match.group("seller1_origin").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller2"),
                role="associé-gérant", extra={**common, "action": "shares_transferred"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"),
                place=match.group("buyer_place"), role="associé",
                signing="ohne Unterschrift", extra={
                    "action": "appointed_and_shares_received",
                    "origin": match.group("buyer_origin").strip(),
                    "counterparties": [
                        match.group("seller1").strip(), match.group("seller2").strip()
                    ],
                    "shares_received": buyer_count, "shares_count": buyer_count,
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ], ""

    match = _DE_PERSON_CORRECTION_ROLES_DOMICILE_LIQUIDATOR.fullmatch(leftover)
    if match:
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "de.persons.correction_roles_domicile_liquidator.v1",
                match.group("name"), place=match.group("place"),
                role=match.group("role"), signing=match.group("signing"), extra={
                    "action": "correction",
                    "origin": match.group("origin").strip(),
                    "previous_place": match.group("previous_place").strip(),
                    "previous_role": match.group("previous_role").strip(),
                    "previous_signing": match.group("previous_signing"),
                    "issue": int(match.group("issue")),
                    "notice_date": _word_date(
                        match.group("notice_date"), _GERMAN_MONTHS
                    ),
                    "entry": match.group("entry"),
                    "entry_date": _word_date(
                        match.group("entry_date"), _GERMAN_MONTHS
                    ),
                },
            )
        ], ""

    match = _FR_THREE_ADMINISTRATORS_WITHOUT_SIGNATURE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.three_administrators_without_signature.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="administrateur",
                signing="ohne Unterschrift", extra={
                    "action": "appointed",
                    "origin": match.group(f"origin{index}").strip(),
                },
            )
            for index in (1, 2, 3)
        ], ""

    match = _FR_CAPITAL_THREE_PARTS_CORPORATE_TRANSFER.fullmatch(leftover)
    if match:
        initial = [
            (_count(match.group(f"count{index}")), match.group(f"nominal{index}"))
            for index in (1, 2, 3)
        ]
        remaining = [
            (
                _count(match.group(f"remaining_count{index}")),
                match.group(f"remaining_nominal{index}"),
            )
            for index in (1, 2)
        ]
        buyer_count = _count(match.group("buyer_count"))
        transferred_nominal = match.group("transferred_nominal")
        if not (
            sum(count * _amount(nominal) for count, nominal in initial)
            == _amount(match.group("capital"))
            and buyer_count == 1
            and transferred_nominal == match.group("buyer_nominal")
            and initial[1] == (buyer_count, transferred_nominal)
            and remaining == [initial[0], initial[2]]
        ):
            return [], leftover
        rule_id = "fr.persons.capital_three_parts_corporate_transfer.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "share_structure", "capital": match.group("capital"),
                    "currency": "CHF",
                    "parts": [
                        {"count": count, "nominal": nominal}
                        for count, nominal in initial
                    ],
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé", extra={
                    "action": "share_transferred", "counterparty": buyer,
                    "shares_transferred": buyer_count,
                    "transferred_share_nominal": transferred_nominal,
                    "holdings": [
                        {"count": count, "nominal": nominal}
                        for count, nominal in remaining
                    ],
                    "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer,
                place=match.group("buyer_place"), uid=match.group("buyer_uid"),
                role="associée", extra={
                    "action": "appointed_and_share_received", "counterparty": seller,
                    "shares_received": buyer_count, "shares_count": buyer_count,
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ], ""

    match = _IT_ASSET_TRANSFER_CASH_CONSIDERATION.fullmatch(leftover)
    if match:
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "it.text.asset_transfer_cash_consideration.v1", {
                    "source_kind": "company",
                    "agreement_date": _iso_date(match.group("agreement_date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "liabilities_kind": "third_party_liabilities",
                    "currency": "CHF", "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration": match.group("consideration"),
                    "consideration_kind": "cash",
                },
            )
        ], ""

    match = _FR_SIGNING_CORRECTED_WITH_NOTICE.fullmatch(leftover)
    if match:
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.signing_corrected_with_notice.v1",
                match.group("name"), role=match.group("role"),
                signing="Einzelunterschrift", extra={
                    "action": "signing_corrected",
                    "previous_signing": "Kollektivunterschrift zu zweien",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_id": match.group("notice_id"),
                },
            )
        ], ""

    match = _DE_SOLE_PROPRIETOR_ASSET_TRANSFER_WITHOUT_CONSIDERATION.fullmatch(leftover)
    if match:
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred",
                "de.text.sole_proprietor_asset_transfer_without_consideration.v1", {
                    "source_kind": "sole_proprietor",
                    "agreement_date": _iso_date(match.group("agreement_date")),
                    "assets": match.group("assets"), "currency": "CHF",
                    "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration_kind": "none", "gratuitous": True,
                },
            )
        ], ""

    match = _DE_PLURAL_PERSON_DOMICILE_CHANGED.fullmatch(leftover)
    if match:
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "de.persons.plural_domicile_changed.v1",
                match.group("name"), place=match.group("place"),
                signing=match.group("signing"), extra={"action": "domicile_changed"},
            )
        ], ""

    match = _FR_TRANSFER_RESTRICTION_AND_COMMUNICATIONS_REMOVED.fullmatch(leftover)
    if match:
        rule_id = "fr.text.transfer_restriction_and_communications_removed.v1"
        notice = {
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_ref": match.group("notice_ref"),
        }
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "share_transfer_restriction", "action": "removed",
                    "shares_count": _count(match.group("count")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                    "share_kind": "nominative",
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id, {
                    **notice, "kind": "shareholder_communications_clause",
                    "action": "removed",
                },
            ),
        ], ""

    match = _DE_HEAD_OFFICE_SHARE_CAPITAL_AND_PAID_CHANGED.fullmatch(leftover)
    if match and len({
        match.group("currency"), match.group("to_paid_currency"),
        match.group("from_currency"), match.group("from_paid_currency"),
    }) == 1:
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed",
                "de.text.head_office_share_capital_and_paid_changed.v1", {
                    "scope": "head_office", "kind": "share_capital",
                    "currency": match.group("currency").upper(),
                    "from_nominal": match.group("from_capital"),
                    "to_nominal": match.group("to_capital"),
                    "from_paid": match.group("from_paid"),
                    "to_paid": match.group("to_paid"),
                },
            )
        ], ""

    match = _FR_TWO_MANAGERS_REMOVED_THREE_ASSOCIATES.fullmatch(leftover)
    if match:
        incoming_total = sum(_count(match.group(f"count{index}")) for index in (1, 2, 3))
        if not (
            len({
                match.group("nominal"), match.group("nominal1"),
                match.group("nominal2"), match.group("nominal3"),
            }) == 1
            and incoming_total >= _count(match.group("transferred"))
        ):
            return [], leftover
        rule_id = "fr.persons.two_managers_removed_three_associates.v1"
        events = [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group(f"removed{index}"),
                role="associé-gérant", signing="Unterschrift erloschen", extra={
                    "action": "removed", "powers_revoked": True,
                    "group_shares_transferred": _count(match.group("transferred")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            )
            for index in (1, 2)
        ]
        roles = {
            1: "associée-gérante présidente",
            2: "associé-gérant",
            3: "associée-gérante",
        }
        for index in (1, 2, 3):
            extra = {
                "action": "holding_and_management_changed",
                "shares_count": _count(match.group(f"count{index}")),
                "share_nominal": match.group(f"nominal{index}"), "currency": "CHF",
            }
            if index == 3:
                extra["origin"] = match.group("origin3").strip()
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"buyer{index}"),
                place=match.group("place3") if index == 3 else None,
                role=roles[index],
                signing=(
                    "Kollektivunterschrift zu zweien"
                    if index == 3
                    else "Einzelunterschrift"
                ),
                extra=extra,
            ))
        return events, ""

    match = _DE_COMPANY_REINSTATED_IN_LIQUIDATION_WITH_OFFICE.fullmatch(leftover)
    if match:
        rule_id = "de.text.company_reinstated_in_liquidation_with_office.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "reinstated_in_liquidation", "action": "reinstated",
                    "deletion_date": _iso_date(match.group("deletion_date")),
                    "decision_date": _iso_date(match.group("decision_date")),
                    "issue": int(match.group("issue")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "previous_bankruptcy_closed_date": _iso_date(
                        match.group("bankruptcy_closed_date")
                    ),
                    "in_liquidation": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("liquidator"),
                place=match.group("place"), role="Liquidator", extra={
                    "action": "appointed", "organization": True,
                    "address": {
                        "street": match.group("street").strip(),
                        "postal_code": match.group("postal_code"),
                        "place": match.group("place").strip(),
                    },
                },
            ),
        ], ""

    match = _FR_DEFINITIVE_MORATORIUM_WITH_COMMISSIONER_UNTIL.fullmatch(leftover)
    if match:
        rule_id = "fr.text.definitive_moratorium_with_commissioner_until.v1"
        decision_date = _word_date(match.group("decision_date"), _FRENCH_MONTHS)
        until = _word_date(match.group("until"), _FRENCH_MONTHS)
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "definitive_moratorium", "decision_date": decision_date,
                    "until": until, "authority": match.group("authority").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("commissioner"),
                place=match.group("place"), role="commissaire au sursis", extra={
                    "action": "appointed", "origin": match.group("origin").strip(),
                    "decision_date": decision_date, "until": until,
                },
            ),
        ], ""

    return [], leftover
