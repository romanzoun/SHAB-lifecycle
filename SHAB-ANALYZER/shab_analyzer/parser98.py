from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_UID_CORRECTION_PARENTHESES = re.compile(
    r"^Berichtigung der Eintragung Nr\.\s*(?P<entry>[\d']+) vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(SHAB vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s*(?P<notice_id>\d+)\):\s*"
    r"die richtige UID-Nummer lautet\s+(?P<to>CHE-\d{3}\.\d{3}\.\d{3})\s*"
    r"\(und nicht\s+(?P<from>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_FR_REINSTATEMENT_LIQUIDATORS_CONTINUE = re.compile(
    r"^La réinscription de la société a été ordonnée par jugement du\s+"
    r"(?P<authority>.+?)\s+du\s+(?P<date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"Par conséquent,\s*sa raison sociale demeure:\s*(?P<company_name>.+?)\.\s*"
    r"Les liquidateurs\s+(?P<name1>[^.;]+?)\s+et\s+(?P<name2>[^.;]+?)\s+"
    r"continuent à signer individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_RESTRICTIONS_REMOVED = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?P<role1>secrétaire),\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*(?P<role2>membres? du conseil d['’]administration),\s*"
    r"continuent de signer collectivement à deux,\s*mais désormais sans autre "
    r"restriction\.\s*(?P<name3>[^,.;]+),\s*maintenant domiciliée? à\s*"
    r"(?P<place3>[^,.;]+),\s*continue de signer par procuration,\s*"
    r"collectivement à deux,\s*mais désormais sans autre restriction\.?$",
    re.I | re.UNICODE,
)
_DE_ENDOWMENT_CAPITAL_INCREASED_TYPO = re.compile(
    r"^Kapital neu:\s*CHF\s+(?P<capital>[\d'.]+)\s*"
    r"\[bisher:\s*CHF\s+(?P<previous_capital>[\d'.]+)\]\.\s*"
    r"Liberierung Kapital neu:\s*CHF\s+(?P<paid>[\d'.]+)\s*"
    r"\[bisher:\s*CHF\s+(?P<previous_paid>[\d'.]+)\]\.\s*"
    r"Eröhung des Dotationskapitals gemäss Beschluss des\s+"
    r"(?P<authority>.+?)\s+vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"(?P<reason>.+?)\s+um CHF\s+(?P<increase>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_INDIVIDUAL_SIGNING = re.compile(
    r"^(?P<seller>[^,.;]+) a cédé\s+(?P<transferred>[\d']+) parts de CHF\s+"
    r"(?P<nominal>[\d'.]+) à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s*"
    r"(?P<place>[^,.;]+),\s*nouvelle associée pour\s+"
    r"(?P<buyer_count>[\d']+) parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"Par conséquent,\s*(?P=seller) est maintenant associée pour\s+"
    r"(?P<seller_count>[\d']+) parts de CHF\s+(?P<seller_nominal>[\d'.]+)\.\s*"
    r"Signature individuelle a été conférée à l['’]associée\s+(?P=buyer)\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTION_MEMBER_NAME_CORRECTED = re.compile(
    r"^Le nom exact du\s+(?P<role>membre de la direction) est\s+"
    r"(?P<name>.+?)\s*\(et non\s+(?P<previous_name>.+?)\)\.?$",
    re.I | re.UNICODE,
)
_DE_INCORRECT_STATUTES_DATE_FRAGMENT = re.compile(
    r"^\(nicht:\s*(?P<previous_date>\d{2}\.\d{2}\.\d{4})\)\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_THREE_SIGNATURES = re.compile(
    r"^,\s*(?P<head_office_country>[A-Z]{1,3})\.\s*"
    r"Signature collective à deux a été conférée à\s+"
    r"(?P<name1>[^,;]+),\s*à\s*(?P<place1>.+?),\s*(?P<country1>[A-Z]{1,3}),\s*"
    r"(?P<name2>[^,;]+),\s*à\s*(?P<place2>.+?),\s*(?P<country2>[A-Z]{1,3}),\s*"
    r"et\s*(?P<name3>[^,;]+),\s*d['’](?P<origin3>[^,;]+),\s*à\s*"
    r"(?P<place3>.+?),\s*(?P<country3>[A-Z]{1,3}),\s*"
    r"tous trois d['’](?P<nationality>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUR_MANAGERS_TRANSFER_UNSIGNED = re.compile(
    r"^Jusqu['’]ici titulaires de\s+(?P<before>[\d']+) parts de CHF\s+"
    r"(?P<nominal>[\d'.]+) chacun,\s*les associés-gérants\s+"
    r"(?P<name1>[^,.;]+),\s*(?P<name2>[^,.;]+),\s*"
    r"(?P<name3>[^,.;]+),\s*lequel est maintenant domicilié à\s*"
    r"(?P<place3>[^,.;]+),\s*(?P<country3>[A-Z]{1,3}),\s*et\s*"
    r"(?P<name4>[^,.;]+) détiennent chacun\s+(?P<remaining>[\d']+) parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+),\s*par suite de cession de\s+"
    r"(?P<transferred>[\d']+) parts de CHF\s+(?P<transferred_nominal>[\d'.]+) à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s*(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{1,3}),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+) parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"lequel n['’]exerce pas la signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_SIGNING_SUPPLEMENT = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) est complétée en ce sens que\s+"
    r"(?P<name1>[^,.;]+),\s*maintenant originaire de\s*(?P<origin1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*(?P<name3>[^,.;]+),\s*maintenant originaire de\s*"
    r"(?P<origin3>[^,.;]+),\s*(?P<name4>[^,.;]+),\s*(?P<name5>[^,.;]+) et\s*"
    r"(?P<name6>[^,.;]+),\s*maintenant domicilié à\s*(?P<place6>[^,.;]+),\s*"
    r"membres du conseil de fondation,\s*exercent désormais la signature sociale,\s*"
    r"collectivement à deux avec le président\.?$",
    re.I | re.UNICODE,
)
_DE_PENSION_FOUNDATION_ASSET_TRANSFER_CLAIMS = re.compile(
    r"^Vermögensübertragung:\s*Die\s+(?P<source_kind>Stiftung)\s*"
    r"\((?P<source_detail>[^)]+)\) überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}) Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+) auf die\s+(?P<recipient>.+?),\s*in\s*"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*CHF\s+(?P<consideration>[\d'.]+) getilgt durch Gewährung "
    r"von\s+(?P<claims>[\d']+) Ansprüchen an der Anlagegruppe\s+"
    r"[\"“](?P<investment_group>.+?)[\"”]\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBERS_WITHOUT_SIGNATURE_COLON = re.compile(
    r"^(?P<name1>[^,;]+),\s*de et à\s*(?P<place1>[^,;]+),\s*et\s*"
    r"(?P<name2>[^,;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,;]+),\s*à\s*(?P<place2>[^,;]+),\s*"
    r"sont membres du conseil de fondation:\s*ils n['’]exercent pas la "
    r"signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGER_ELECTED_LIQUIDATOR = re.compile(
    r"^L['’]associé-gérant\s+(?P<name>[^.;]+?)\s+est élu liquidateur\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_NAME_CORRECTED_SE_NOMME = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) est rectifiée en ce sens que\s+"
    r"(?P<previous_name>.+?)\s+se nomme\s+(?P<name>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_MANAGER_PRESIDENT = re.compile(
    r"^Nouveau gérant:\s*(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"au\s+(?P<place>[^,.;]+),\s*(?P<role>président)\.?$",
    re.I | re.UNICODE,
)
_FR_HEAD_OFFICE_IDENTIFIER_REPLACED = re.compile(
    r"^L['’]identification du siège principal sous le numéro\s+"
    r"(?P<from>CH-[\d-]+) est remplacée par le numéro d['’]identification "
    r"des entreprises\s*\(IDE/UID\)\s*\((?P<to>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{year}-{month}-{day}"


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


def extract_parser98_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 98."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_UID_CORRECTION_PARENTHESES.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_identifier_changed", "de.text.uid_correction_parentheses.v1",
            {
                "action": "corrected",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
                "from": match.group("from"),
                "to": match.group("to"),
            },
        ))

    match = _FR_REINSTATEMENT_LIQUIDATORS_CONTINUE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.reinstatement_liquidators_continue.v1"
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", rule_id,
            {
                "kind": "registration_reinstated",
                "action": "ordered",
                "date": _iso_date(match.group("date")),
                "authority": match.group("authority").strip(),
                "company_name_confirmed": match.group("company_name").strip(),
            },
        ))
        for group in ("name1", "name2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(group),
                role="liquidateur", signing="Einzelunterschrift",
                extra={"action": "continued"},
            ))

    match = _FR_SIGNING_RESTRICTIONS_REMOVED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.signing_restrictions_removed.v1"
        for group, role in (
            ("name1", match.group("role1")),
            ("name2", match.group("role2")),
        ):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(group),
                role=role.lower(), signing="Kollektivunterschrift zu zweien",
                extra={"action": "restriction_removed", "continued": True},
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", rule_id, match.group("name3"),
            place=match.group("place3"), signing="Kollektivprokura zu zweien",
            extra={
                "action": "domicile_changed_and_restriction_removed",
                "continued": True,
            },
        ))

    match = _DE_ENDOWMENT_CAPITAL_INCREASED_TYPO.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.endowment_capital_increased_typo.v1",
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
        ))

    match = _FR_ASSOCIATE_TRANSFER_INDIVIDUAL_SIGNING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.associate_transfer_individual_signing.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associée",
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
                role="associée", signing="Einzelunterschrift",
                extra={
                    "action": "appointed_and_signing_granted",
                    "heimat": match.group("origin").strip(),
                    "counterparty": seller,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"),
                    "currency": "CHF",
                },
            ),
        ])

    match = _FR_DIRECTION_MEMBER_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.direction_member_name_corrected.v1",
            match.group("name"), role=match.group("role"),
            extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
            },
        ))

    match = _DE_INCORRECT_STATUTES_DATE_FRAGMENT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.incorrect_statutes_date_fragment.v1",
            {
                "kind": "statutes_date",
                "action": "incorrect_value_removed",
                "previous_date": _iso_date(match.group("previous_date")),
            },
        ))

    match = _FR_BRANCH_THREE_SIGNATURES.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.branch_three_signatures.v1"
        people = (
            ("name1", "place1", "country1", None),
            ("name2", "place2", "country2", None),
            ("name3", "place3", "country3", match.group("origin3")),
        )
        for name_group, place_group, country_group, origin in people:
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(name_group),
                place=match.group(place_group),
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "granted",
                    "country": match.group(country_group),
                    "nationality": match.group("nationality").strip(),
                    "head_office_country": match.group("head_office_country"),
                    **({"origin": origin.strip()} if origin else {}),
                },
            ))

    match = _FR_FOUR_MANAGERS_TRANSFER_UNSIGNED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.four_managers_transfer_unsigned.v1"
        seller_names = [match.group(f"name{index}").strip() for index in range(1, 5)]
        before = _count(match.group("before"))
        remaining = _count(match.group("remaining"))
        buyer = match.group("buyer").strip()
        for index, seller in enumerate(seller_names, start=1):
            place = match.group("place3") if index == 3 else None
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, place=place,
                role="associé-gérant",
                extra={
                    "action": (
                        "domicile_changed_and_shares_transferred"
                        if index == 3 else "shares_transferred"
                    ),
                    "counterparty": buyer,
                    "shares_before": before,
                    "shares_transferred": before - remaining,
                    "shares_count": remaining,
                    "share_nominal": match.group("remaining_nominal"),
                    "currency": "CHF",
                    **({"country": match.group("country3")} if index == 3 else {}),
                },
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, buyer, place=match.group("place"),
            role="associé",
            extra={
                "action": "appointed",
                "heimat": match.group("origin").strip(),
                "country": match.group("country"),
                "counterparties": seller_names,
                "shares_received": _count(match.group("transferred")),
                "shares_count": _count(match.group("buyer_count")),
                "share_nominal": match.group("buyer_nominal"),
                "currency": "CHF",
                "without_signature": True,
            },
        ))

    match = _FR_FOUNDATION_SIGNING_SUPPLEMENT.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.foundation_signing_supplement.v1"
        for index in range(1, 7):
            extra = {
                "action": "signing_changed",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "signing_constraint": "avec le président",
            }
            if index in (1, 3):
                extra.update({
                    "action": "origin_and_signing_changed",
                    "heimat": match.group(f"origin{index}").strip(),
                })
            if index == 6:
                extra["action"] = "domicile_and_signing_changed"
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group("place6") if index == 6 else None,
                role="membre du conseil de fondation",
                signing="Kollektivunterschrift zu zweien",
                extra=extra,
            ))

    match = _DE_PENSION_FOUNDATION_ASSET_TRANSFER_CLAIMS.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.pension_foundation_asset_transfer_claims.v1",
            {
                "source_kind": match.group("source_kind").lower(),
                "source_detail": match.group("source_detail").strip(),
                "date": _iso_date(match.group("date")),
                "assets": match.group("assets"),
                "liabilities": None,
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"),
                "consideration_kind": "investment_group_claims",
                "claims_count": _count(match.group("claims")),
                "investment_group": match.group("investment_group").strip(),
                "currency": "CHF",
            },
        ))

    match = _FR_FOUNDATION_MEMBERS_WITHOUT_SIGNATURE_COLON.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.foundation_members_without_signature_colon.v1"
        people = (
            (match.group("name1"), match.group("place1"), match.group("place1")),
            (match.group("name2"), match.group("place2"), match.group("origin2")),
        )
        for name, place, origin in people:
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, name, place=place,
                role="membre du conseil de fondation",
                extra={
                    "action": "appointed",
                    "heimat": origin.strip(),
                    "without_signature": True,
                },
            ))

    match = _FR_ASSOCIATE_MANAGER_ELECTED_LIQUIDATOR.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_manager_elected_liquidator.v1",
            match.group("name"), role="associé-gérant et liquidateur",
            extra={
                "action": "elected_liquidator",
                "previous_role": "associé-gérant",
            },
        ))

    match = _FR_PERSON_NAME_CORRECTED_SE_NOMME.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.name_corrected_se_nomme.v1",
            match.group("name"),
            extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _FR_NEW_MANAGER_PRESIDENT.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.new_manager_president.v1",
            match.group("name"), place=match.group("place"),
            role=f"gérant et {match.group('role').lower()}",
            extra={
                "action": "appointed",
                "heimat": match.group("origin").strip(),
            },
        ))

    match = _FR_HEAD_OFFICE_IDENTIFIER_REPLACED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_identifier_changed", "fr.text.head_office_identifier_replaced.v1",
            {
                "scope": "head_office",
                "action": "replaced",
                "from": match.group("from"),
                "to": match.group("to"),
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
