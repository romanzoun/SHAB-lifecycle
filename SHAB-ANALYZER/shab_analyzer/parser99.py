from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_TRANSLATIONS_REMOVED_STATUTES_CORRECTED = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) est complétée en ce sens que les "
    r"versions linguistiques de la raison sociale sont radiées\.\s*"
    r"Raison sociale:\s*(?P<name>.+?)\.\s*L['’]inscription est rectifiée en ce "
    r"sens que les statuts ont été modifiés le\s+"
    r"(?P<statutes_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_LIQUIDATORS_CONTINUE = re.compile(
    r"^Liquidateurs:\s*les administrateurs\s+(?P<name1>[^,.;]+),\s*"
    r"maintenant domicilié(?:e)? à\s*(?P<place1>[^,.;]+),\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*lesquels continuent à signer "
    r"(?P<sign>individuellement)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_BOARD_MEMBERS = re.compile(
    r"^(?P<name1>[^,.;]+),\s*de et à\s*(?P<place1>[^,.;]+),\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s*(?P<place2>[^,.;]+),\s*"
    r"sont membres du conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_DE_NAMED_SOURCE_ASSET_TRANSFER = re.compile(
    r"^Vermögensübertragung:\s*Die\s+(?P<source>.+?)\s+überträgt gemäss "
    r"Vermögensübertragungsvertrag vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+und Passiven "
    r"\(Fremdkapital\) von CHF\s+(?P<liabilities>[\d'.]+)\s+auf die\s+"
    r"(?P<recipient>.+?),\s*in\s*(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_TRANSFER_TO_NEW_MANAGER_PRESIDENT = re.compile(
    r"^Jusqu['’]ici titulaire de\s+(?P<before>[\d']+) parts de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*l['’]associé-gérant\s+(?P<seller>[^,.;]+),\s*"
    r"nommé président,\s*détient\s+(?P<remaining>[\d']+) parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+) par suite de cession de\s+"
    r"(?P<transferred>[\d']+) parts à\s+(?P<buyer>[^,.;]+),\s*"
    r"de et à\s*(?P<place>[^,.;]+),\s*nouvel associé-gérant pour\s+"
    r"(?P<buyer_count>[\d']+) parts de CHF\s+(?P<buyer_nominal>[\d'.]+),?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_SUSPENSION_REVERSED = re.compile(
    r"^Der\s+(?P<authority>Einzelrichter des Kantonsgerichts von .+?)\s+hat mit "
    r"Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+die am\s+"
    r"(?P<suspension_date>\d{2}\.\d{2}\.\d{4})\s+angeordnete Einstellung des "
    r"Konkursverfahrens aufgehoben und die Durchführung des summarischen "
    r"Konkursverfahrens angeordnet\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_PERSON_INDIVIDUAL_PROXY = re.compile(
    r"^Gelöschte Person:\s*(?P<name>[^,.;]+),\s*"
    r"(?P<sign>Einzelprokura)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_WITH_PRESIDENCY = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+),\s*lequel est élu président,\s*"
    r"cède\s+(?P<transferred>[\d']+) de ses\s+(?P<before>[\d']+) parts de CHF\s+"
    r"(?P<nominal>[\d'.]+) à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s*"
    r"(?P<place>[^,.;]+),\s*nouvelle associée avec\s+"
    r"(?P<buyer_count>[\d']+) parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"gérante\s+(?P=seller) reste titulaire de\s+(?P<remaining>[\d']+) parts de "
    r"CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_CONTINUED_AND_NEW = re.compile(
    r"^Administration:\s*(?P<name1>[^,.;]+),\s*nommé\s+"
    r"(?P<role1>président et directeur),\s*lequel continue à signer\s+"
    r"(?P<sign1>individuellement)\s+et\s+(?P<name2>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*à\s*"
    r"(?P<place2>[^,.;]+),?$",
    re.I | re.UNICODE,
)
_FR_THREE_PROXIES_NOT_BETWEEN_THEM = re.compile(
    r"^Procuration collective à deux,\s*toutefois pas entre eux,\s*est conférée à\s+"
    r"(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s*(?P<place1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*de et à\s*(?P<place2>[^,.;]+?)"
    r"(?:\s*\((?P<canton2>[A-Z]{2})\))?,\s*et\s*"
    r"(?P<name3>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin3>[^,.;]+),\s*à\s*(?P<place3>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_DOMICILE_CORRECTED = re.compile(
    r"^Le domicile exact de\s+(?P<name>.+?)\s+est\s+(?P<place>.+?)\s+"
    r"\(et non\s+(?P<previous_place>.+?)\)\.?$",
    re.I | re.UNICODE,
)
_FR_AUDIT_WAIVER_MENTION_REMOVED = re.compile(
    r"^Complément:\s*l['’]inscription n°\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_id>\d+)\) est complétée en ce sens que la mention relative à "
    r"la renonciation à l['’]organe de révision est radiée\.?$",
    re.I | re.UNICODE,
)
_FR_HEAD_OFFICE_REPRESENTATIVE_REMOVED_LEGACY = re.compile(
    r"^,?\s*12\.2013,\s*p\.\s*0/\d+\)\.\s*Suite à la modification du droit "
    r"du registre du commerce et en application de l['’]art\.\s*110,\s*al\.\s*1 "
    r"ORC,\s*les informations relatives aux personnes disposant d['’]un pouvoir de "
    r"représentation pour toute l['’]entreprise sont radiées\.\s*Par conséquent,\s*"
    r"l['’]inscription de\s+(?P<name>.+?)\s+est supprimée\.?$",
    re.I | re.UNICODE,
)
_DE_INTENDED_PARTICIPATION_ACQUISITION_REMOVED = re.compile(
    r"^\[gestrichen:\s*beabsichtigte Sachübernahme:\s*"
    r"(?P<count>[\d']+) neu auszugebende Partizipationsscheine der\s+"
    r"[\"“](?P<company>.+?)[\"”]\s*\((?P<registry_id>CH-[\d.]+-\d)\),\s*"
    r"in\s+(?P<place>[^,.;]+),\s*zum Preis von CHF\s+(?P<price>[\d'.]+)\]\."
    r"(?:\s*Ferner)?$",
    re.I | re.UNICODE,
)
_DE_HEAD_OFFICE_IDENTIFIER_AND_CAPITAL = re.compile(
    r"^Neue Identifikationsnummer Hauptsitz:\s*(?P<to_id>[^\[]+?)\s*"
    r"\[bisher:\s*Identifikationsnummer Hauptsitz:\s*(?P<from_id>[^\]]+?)\]\.\s*"
    r"Kapital Hauptsitz neu:\s*(?P<currency>[A-Z]{3})\s+(?P<to_capital>[\d'.]+);\s*"
    r"Liberierung:\s*(?P<paid_currency>[A-Z]{3})\s+(?P<to_paid>[\d'.]+)\s*"
    r"\[bisher:\s*Kapital Hauptsitz:\s*(?P<from_currency>[A-Z]{3})\s+"
    r"(?P<from_capital>[\d'.]+);\s*Liberierung:\s*"
    r"(?P<from_paid_currency>[A-Z]{3})\s+(?P<from_paid>[\d'.]+)\]\.?$",
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


def extract_parser99_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 99."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_TRANSLATIONS_REMOVED_STATUTES_CORRECTED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.translations_removed_statutes_corrected.v1"
        common = {
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
        }
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_name_changed", rule_id,
                {
                    **common,
                    "action": "translations_removed",
                    "company_name": match.group("name").strip(),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id,
                {
                    **common,
                    "action": "date_corrected",
                    "date": _iso_date(match.group("statutes_date")),
                },
            ),
        ])

    match = _FR_ADMINISTRATOR_LIQUIDATORS_CONTINUE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administrator_liquidators_continue.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group("place1") if index == 1 else None,
                role="administrateur et liquidateur",
                signing="Einzelunterschrift",
                extra={
                    "action": (
                        "domicile_changed_and_appointed_liquidator"
                        if index == 1 else "appointed_liquidator"
                    ),
                    "signing_continued": True,
                },
            ))

    match = _FR_TWO_BOARD_MEMBERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_board_members_collective.v1"
        for index in (1, 2):
            place = match.group(f"place{index}")
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=place, role="membre du conseil d'administration",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed",
                    "heimat": (
                        place if index == 1 else match.group("origin2").strip()
                    ),
                },
            ))

    match = _DE_NAMED_SOURCE_ASSET_TRANSFER.search(leftover)
    if match:
        consume(match)
        consideration = match.group("consideration").strip()
        consideration_amount = re.search(
            r"in der Höhe von CHF\s+([\d'.]+)$", consideration, re.I
        )
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.named_source_asset_transfer_no_inventory.v1",
            {
                "source": match.group("source").strip(),
                "date": _iso_date(match.group("date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": consideration,
                "consideration_kind": (
                    "none" if consideration.lower() == "keine"
                    else "investment_group_claim"
                ),
                "consideration_amount": (
                    consideration_amount.group(1) if consideration_amount else None
                ),
                "gratuitous": consideration.lower() == "keine",
            },
        ))

    match = _FR_TRANSFER_TO_NEW_MANAGER_PRESIDENT.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.transfer_to_new_manager_president.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller,
                role="associé-gérant et président",
                signing="Einzelunterschrift",
                extra={
                    "action": "elected_president_and_shares_transferred",
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("remaining_nominal"),
                    "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé-gérant", signing="Einzelunterschrift",
                extra={
                    "action": "appointed_and_shares_received",
                    "heimat": match.group("place").strip(),
                    "counterparty": seller,
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"),
                    "currency": "CHF",
                },
            ),
        ])

    match = _DE_BANKRUPTCY_SUSPENSION_REVERSED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_suspension_reversed.v1",
            {
                "kind": "bankruptcy_proceedings_resumed",
                "action": "suspension_revoked",
                "decision_date": _iso_date(match.group("decision_date")),
                "suspension_date": _iso_date(match.group("suspension_date")),
                "authority": match.group("authority").strip(),
                "procedure": "summary_bankruptcy",
            },
        ))

    match = _DE_REMOVED_PERSON_INDIVIDUAL_PROXY.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_removed", "de.persons.removed_individual_proxy.v1",
            match.group("name"), signing=match.group("sign"),
            extra={"action": "removed"},
        ))

    match = _FR_MANAGER_TRANSFER_WITH_PRESIDENCY.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_transfer_with_presidency.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller,
                role="associé-gérant et président",
                signing="Einzelunterschrift",
                extra={
                    "action": "elected_president_and_shares_transferred",
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("remaining_nominal"),
                    "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée-gérante", signing="Einzelunterschrift",
                extra={
                    "action": "appointed_and_shares_received",
                    "heimat": match.group("origin").strip(),
                    "counterparty": seller,
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"),
                    "currency": "CHF",
                },
            ),
        ])

    match = _FR_ADMINISTRATION_CONTINUED_AND_NEW.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_continued_and_new.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role=match.group("role1").lower(), signing="Einzelunterschrift",
                extra={"action": "roles_changed", "signing_continued": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="administrateur",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed",
                    "heimat": match.group("origin2").strip(),
                },
            ),
        ])

    match = _FR_THREE_PROXIES_NOT_BETWEEN_THEM.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.three_proxies_not_between_them.v1"
        people = (
            ("name1", "place1", match.group("origin1"), None),
            ("name2", "place2", match.group("place2"), match.group("canton2")),
            ("name3", "place3", match.group("origin3"), None),
        )
        for name_group, place_group, origin, place_canton in people:
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(name_group),
                place=match.group(place_group), signing="Kollektivprokura zu zweien",
                extra={
                    "action": "granted",
                    "heimat": origin.strip(),
                    "signing_restriction": "not_between_them",
                    **({"place_canton": place_canton} if place_canton else {}),
                },
            ))

    match = _FR_DOMICILE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.domicile_corrected_exact.v1",
            match.group("name"), place=match.group("place"),
            extra={
                "action": "domicile_corrected",
                "previous_place": match.group("previous_place").strip(),
            },
        ))

    match = _FR_AUDIT_WAIVER_MENTION_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "audit_requirement_changed", "fr.text.audit_waiver_mention_removed.v2",
            {
                "kind": "limited_audit_waiver",
                "action": "revoked",
                "waiver_mention_removed": True,
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        ))

    match = _FR_HEAD_OFFICE_REPRESENTATIVE_REMOVED_LEGACY.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_removed", "fr.persons.head_office_representative_removed_legacy.v1",
            match.group("name"),
            role="personne disposant d'un pouvoir de représentation",
            extra={
                "action": "functions_and_signatures_removed",
                "legal_basis": "art. 110 al. 1 ORC",
            },
        ))

    match = _DE_INTENDED_PARTICIPATION_ACQUISITION_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.intended_participation_acquisition_removed.v1",
            {
                "kind": "intended_asset_acquisition",
                "action": "removed",
                "asset": "participation_certificates",
                "count": _count(match.group("count")),
                "company": match.group("company").strip(),
                "registry_id": match.group("registry_id"),
                "place": match.group("place").strip(),
                "price": match.group("price"),
                "currency": "CHF",
            },
        ))

    match = _DE_HEAD_OFFICE_IDENTIFIER_AND_CAPITAL.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.head_office_identifier_and_capital.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_identifier_changed", rule_id,
                {
                    "scope": "head_office",
                    "action": "changed",
                    "from": match.group("from_id").strip(),
                    "to": match.group("to_id").strip(),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "scope": "head_office",
                    "currency": match.group("currency"),
                    "from_nominal": match.group("from_capital"),
                    "to_nominal": match.group("to_capital"),
                    "from_paid": match.group("from_paid"),
                    "to_paid": match.group("to_paid"),
                },
            ),
        ])

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
