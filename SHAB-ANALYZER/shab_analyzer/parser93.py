from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_SHARE_TRANSFER_STATUTORY_DEROGATION = re.compile(
    r"^Les statuts dérogent à la loi quant aux modalités du transfert des "
    r"parts sociales:\s*pour les détails,\s*voir les statuts\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_NAME_CORRECTED_CE_SENS = re.compile(
    r"^Rectification:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\)\s+est rectifiée dans ce sens que le nom exact est\s+"
    r"(?P<name>.+?)\s+et non pas\s+(?P<previous_name>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_SUPPLEMENTED_SHARE_TRANSFER_DEROGATION = re.compile(
    r"^Complément à l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\):\s*Les statuts dérogent à la loi quant aux "
    r"modalités du transfert des parts sociales:\s*pour les détails,\s*"
    r"voir les statuts\.?$",
    re.I | re.UNICODE,
)
_FR_LIQUIDATOR_APPOINTED_AFTER_MOVE = re.compile(
    r"^(?P<name>[^,.;]+),\s*qui est maintenant à\s+(?P<place>[^,.;]+),\s*"
    r"est nommé\s+(?P<role>liquidateur)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_TO_NEW_UNSIGNED = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>.+?),\s*nouvel associé sans "
    r"signature avec\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*(?P=seller)\s+reste titulaire de\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_ROLE_SWAP_AND_NEW_MEMBERS = re.compile(
    r"^(?P<name1>[^,.;]+),\s*jusqu['’]ici\s+(?P<previous_role1>directeur),\s*"
    r"nommé\s+(?P<role1>membre du conseil d['’]administration),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<previous_role2>membre du conseil d['’]administration),\s*nommé\s+"
    r"(?P<role2>directeur),\s*continuent de signer\s+"
    r"(?P<sign>collectivement à deux)\.\s*"
    r"(?P<new1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*(?P<country1>[A-Z]),\s*"
    r"et\s+(?P<new2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"(?P<country2>[A-Z]),\s*tous deux de\s+(?P<origin>[^,.;]+),\s*"
    r"sont membres du conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_FR_PARTNERSHIP_START_DATE_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+p\.\s*"
    r"(?P<notice_page>[\d/]+)\)\s+est rectifiée en ce sens que la société "
    r"en nom collectif a commencé le\s+(?P<date>\d{1,2}(?:er)?\s+\w+\s+\d{4})\s+"
    r"et non le\s+(?P<previous_date>\d{1,2}(?:er)?\s+\w+\s+\d{4})\s+"
    r"comme publié\.?$",
    re.I | re.UNICODE,
)
_DE_ADDITIONAL_ADDRESS_FRAGMENT = re.compile(
    r"^(?P<street_number>\d+[A-Za-z]?),\s*(?P<postal_code>\d{4})\s+"
    r"(?P<town>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSET_TRANSFER_UID_BEFORE_PLACE = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré des actifs "
    r"pour CHF\s+(?P<assets>[\d'.]+)\s+et des passifs envers les tiers pour "
    r"CHF\s+(?P<liabilities>[\d'.]+),\s*à\s+(?P<recipient>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+à\s+(?P<place>[^.]+)\.\s*"
    r"Contre-prestation:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_LIQUIDATION_ADDRESS_CHANGED = re.compile(
    r"^\[gestrichen:\s*Liquidationsadresse:\s*(?P<previous_street>.+?),\s*"
    r"(?P<previous_postal_code>\d{4})\s+(?P<previous_town>[^\]]+?)\]\.?\s*"
    r"Liquidationsadresse:\s*(?P<street>.+?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<town>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ORGANIZATION_SHARE_NOMINAL_CORRECTED = re.compile(
    r"^L['’]inscription\s+N°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_page>[\d/]+)\)\s+est rectifiée comme suit:\s*"
    r"(?P<name>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+est associée "
    r"pour\s+(?P<count>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s*"
    r"\(et non de CHF\s+(?P<previous_nominal>[\d'.]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_ENDOWMENT_CAPITAL_INCREASED_CANTON_COUNCIL = re.compile(
    r"^Kapital neu:\s*CHF\s+(?P<capital>[\d'.]+)\s*"
    r"\[bisher:\s*CHF\s+(?P<previous_capital>[\d'.]+)\]\.\s*"
    r"Liberierung Kapital neu:\s*CHF\s+(?P<paid>[\d'.]+)\s*"
    r"\[bisher:\s*CHF\s+(?P<previous_paid>[\d'.]+)\]\.\s*"
    r"Erhöhung des Dotationskapitals gemäss Beschluss der Kantonsrates\s+"
    r"(?P<authority>.+?)\s+vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"(?P<reason>.+?)\s+um CHF\s+(?P<increase>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_INCOMING_SPIN_OFF_MEMBERSHIP_CONTINUITY = re.compile(
    r"^Abspaltung:\s*Die Gesellschaft übernimmt von der\s+(?P<source>.+?),\s*"
    r"in\s+(?P<source_place>[^()]+?)\s*"
    r"\((?P<source_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*einen Teil des "
    r"Vermögens\.\s*Die Gesellschaft übernimmt dabei gemäss Spaltungsvertrag "
    r"vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven \(Fremdkapital\) von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\.\s*Da die mitgliedschaftliche Kontinuität "
    r"gewahrt ist,\s*findet weder eine Kapitalerhöhung noch eine Zuteilung von "
    r"Stammanteilen statt\.?$",
    re.I | re.UNICODE,
)
_FR_UID_CORRECTED = re.compile(
    r"^Rectification de l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\):\s*le numéro IDE correct est\s+"
    r"(?P<to>CHE-\d{3}\.\d{3}\.\d{3})\s*\(et non pas\s+"
    r"(?P<from>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_PERSON_WITH_COLLECTIVE_SIGNING = re.compile(
    r"^Gelöschte Person:\s*(?P<name>[^,.;]+),\s*"
    r"(?P<sign>Kollektivunterschrift(?:\s+zu\s+zweien)?)\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_IDENTIFIERS_ASSIGNED = re.compile(
    r"^L['’]identification de la succursale à\s+(?P<address1>.+?),\s*"
    r"est maintenant\s*\((?P<uid1>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"et à\s+(?P<address2>.+?)\s*"
    r"\((?P<uid2>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
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
        payload={
            "name": clean_name,
            "place": clean_place,
            **({"uid": uid} if uid else {}),
            **(extra or {}),
        },
    )


def extract_parser93_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 93."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_SUPPLEMENTED_SHARE_TRANSFER_DEROGATION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "fr.text.share_transfer_derogation_supplemented.v1",
                {
                    "kind": "share_transfer_rules",
                    "action": "publication_supplemented",
                    "share_transfer_rules": "statutory_derogation",
                    "details_in_statutes": True,
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_id": match.group("notice_id"),
                },
            )
        )

    match = _FR_SHARE_TRANSFER_STATUTORY_DEROGATION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "fr.text.share_transfer_derogation.v1",
                {
                    "kind": "share_transfer_rules",
                    "action": "introduced",
                    "share_transfer_rules": "statutory_derogation",
                    "details_in_statutes": True,
                },
            )
        )

    match = _FR_PERSON_NAME_CORRECTED_CE_SENS.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.name_corrected_with_notice.v2",
                match.group("name"),
                extra={
                    "action": "name_corrected",
                    "previous_name": match.group("previous_name").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_id": match.group("notice_id"),
                },
            )
        )

    match = _FR_LIQUIDATOR_APPOINTED_AFTER_MOVE.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.liquidator_appointed_after_move.v1",
                match.group("name"), place=match.group("place"),
                role=match.group("role"),
                extra={"action": "appointed_liquidator", "domicile_changed": True},
            )
        )

    match = _FR_ASSOCIATE_TRANSFER_TO_NEW_UNSIGNED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.associate_transfer_new_unsigned.v1"
        transferred = _count(match.group("transferred"))
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("seller"), role="associé",
                    extra={
                        "action": "shares_transferred",
                        "counterparty": match.group("buyer").strip(),
                        "shares_before": _count(match.group("before")),
                        "shares_transferred": transferred,
                        "shares_count": _count(match.group("seller_count")),
                        "share_nominal": match.group("seller_nominal"),
                        "currency": "CHF",
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("buyer"),
                    place=match.group("place"), role="associé",
                    extra={
                        "action": "appointed",
                        "counterparty": match.group("seller").strip(),
                        "new_associate": True,
                        "without_signature": True,
                        "heimat": match.group("origin").strip(),
                        "shares_received": transferred,
                        "shares_count": _count(match.group("buyer_count")),
                        "share_nominal": match.group("buyer_nominal"),
                        "currency": "CHF",
                    },
                ),
            ]
        )

    match = _FR_BOARD_ROLE_SWAP_AND_NEW_MEMBERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.board_role_swap_and_new_members.v1"
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    role=match.group(f"role{index}"),
                    signing="Kollektivunterschrift zu zweien",
                    extra={
                        "action": "role_changed",
                        "previous_role": match.group(f"previous_role{index}"),
                        "signing_continues": True,
                    },
                )
            )
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"new{index}"),
                    place=match.group(f"place{index}"),
                    role="membre du conseil d'administration",
                    extra={
                        "action": "appointed",
                        "heimat": match.group("origin").strip(),
                        "country_code": match.group(f"country{index}").upper(),
                    },
                )
            )

    match = _FR_PARTNERSHIP_START_DATE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", "fr.text.partnership_start_date_corrected.v1",
                {
                    "kind": "business_start_date",
                    "action": "corrected",
                    "legal_form": "société en nom collectif",
                    "date": _french_date(match.group("date")),
                    "previous_date": _french_date(match.group("previous_date")),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_page": match.group("notice_page"),
                },
            )
        )

    match = _DE_ADDITIONAL_ADDRESS_FRAGMENT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", "de.text.additional_address_fragment_completion.v1",
                {
                    "kind": "additional_address",
                    "action": "completed",
                    "street_number": match.group("street_number"),
                    "postal_code": match.group("postal_code"),
                    "town": match.group("town").strip(),
                    "fragment": match.group(0).rstrip("."),
                },
            )
        )

    match = _FR_ASSET_TRANSFER_UID_BEFORE_PLACE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "fr.text.asset_transfer_uid_before_place.v1",
                {
                    "date": _iso_date(match.group("date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "currency": "CHF",
                    "recipient": match.group("recipient").strip(),
                    "recipient_uid": match.group("uid"),
                    "recipient_place": match.group("place").strip(),
                    "consideration": f"CHF {match.group('consideration')}",
                    "consideration_kind": "cash",
                    "consideration_amount": match.group("consideration"),
                },
            )
        )

    match = _DE_LIQUIDATION_ADDRESS_CHANGED.search(leftover)
    if match:
        consume(match)
        previous = (
            f"{match.group('previous_street').strip()}, "
            f"{match.group('previous_postal_code')} {match.group('previous_town').strip()}"
        )
        current = (
            f"{match.group('street').strip()}, "
            f"{match.group('postal_code')} {match.group('town').strip()}"
        )
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", "de.text.liquidation_address_changed.v1",
                {
                    "kind": "liquidation_address",
                    "action": "changed",
                    "from": previous,
                    "to": current,
                    "postal_code": match.group("postal_code"),
                    "town": match.group("town").strip(),
                },
            )
        )

    match = _FR_ORGANIZATION_SHARE_NOMINAL_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.organization_share_nominal_corrected.v1",
                match.group("name"), uid=match.group("uid"), role="associée",
                extra={
                    "action": "share_nominal_corrected",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_page": match.group("notice_page"),
                    "shares_count": _count(match.group("count")),
                    "shares_nominal": match.group("nominal"),
                    "previous_shares_nominal": match.group("previous_nominal"),
                    "currency": "CHF",
                },
            )
        )

    match = _DE_ENDOWMENT_CAPITAL_INCREASED_CANTON_COUNCIL.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.endowment_capital_increased.v2",
                {
                    "kind": "endowment_capital_increase",
                    "currency": "CHF",
                    "from_nominal": match.group("previous_capital"),
                    "to_nominal": match.group("capital"),
                    "from_paid": match.group("previous_paid"),
                    "to_paid": match.group("paid"),
                    "increase": match.group("increase"),
                    "decision_date": _iso_date(match.group("date")),
                    "authority": match.group("authority").strip(),
                    "reason": match.group("reason").strip(),
                },
            )
        )

    match = _DE_INCOMING_SPIN_OFF_MEMBERSHIP_CONTINUITY.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.spin_off_acquisition_llc.v1",
                {
                    "kind": "spin_off_acquisition",
                    "source": match.group("source").strip(),
                    "source_place": match.group("source_place").strip(),
                    "source_uid": match.group("source_uid"),
                    "date": _iso_date(match.group("date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "currency": "CHF",
                    "membership_continuity": True,
                    "capital_increase": False,
                    "share_allocation": False,
                    "share_kind": "Stammanteile",
                },
            )
        )

    match = _FR_UID_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_identifier_changed", "fr.text.company_identifier_corrected.v3",
                {
                    "scope": "organization",
                    "action": "corrected",
                    "from": match.group("from"),
                    "to": match.group("to"),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_id": match.group("notice_id"),
                },
            )
        )

    match = _DE_REMOVED_PERSON_WITH_COLLECTIVE_SIGNING.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", "de.persons.removed_person_collective_signing.v1",
                match.group("name"), signing=match.group("sign"),
                extra={"action": "removed", "language_override": "de"},
            )
        )

    match = _FR_BRANCH_IDENTIFIERS_ASSIGNED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.branch_identifiers_assigned.v1"
        for index in (1, 2):
            events.append(
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "branch_changed", rule_id,
                    {
                        "action": "identifier_assigned",
                        "scope": "branch",
                        "address": match.group(f"address{index}").strip(),
                        "branch_uid": match.group(f"uid{index}"),
                    },
                )
            )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
