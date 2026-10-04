from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_TWO_MEMBERS_SIGNING_CHANGED_TO_WITH_ADMINISTRATOR = re.compile(
    r"^(?P<name1>[^,.;]+?)\s+jusqu['’]ici avec une signature collective à deux "
    r"signe désormais avec un administrateur et\s+(?P<name2>[^,.;]+?)\s+"
    r"jusqu['’]ici avec une signature collective à deux signe désormais avec "
    r"un administrateur\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_AGREEMENT_ZERO_LIABILITIES = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss "
    r"Vermögensübertragungsvertrag vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+und Passiven \(Fremdkapital\) "
    r"vom CHF\s+(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>Keine)\.?$",
    re.I | re.UNICODE,
)
_FR_REINSTATEMENT_ORDERED_BY_SUPERPROVISIONAL_MEASURES = re.compile(
    r"^La réinscription de la société dans l['’]état antérieur à sa radiation "
    r"a été ordonnée par décision sur mesures superprovisionnelles de la\s+"
    r"(?P<authority>.+?)\s+du\s+(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_BOARD_MEMBERS_APPOINTED = re.compile(
    r"^(?P<name1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*(?P<name2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),"
    r"\s*à\s+(?P<place2>[^,.;]+),\s*et\s+(?P<name3>[^,.;]+),\s*de\s+"
    r"(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+),\s*sont membres du "
    r"conseil\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_SIGNATURE_REVOKED = re.compile(
    r"^L['’]associée\s+(?P<name>[^,.;]+)\s+n['’]exerce plus la signature "
    r"sociale\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_AMENDMENT_CLARIFYING_REAL_ESTATE = re.compile(
    r"^Mit Datum vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+wurde ein Nachtrag "
    r"erstellt zur Präzisierung der Übernahme der Liegenschaften im Rahmen "
    r"des Vermögensübertragungsvertrages vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_EXISTING_ASSOCIATE_RUNNING_TOTAL = re.compile(
    r"^(?P<seller>[^,.;]+?)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+?),\s*désormais titulaire de\s+"
    r"(?P<buyer_count>[\d']+)\s+parts? de CHF\s+(?P<buyer_nominal>[\d'.]+)\."
    r"\s*(?P=seller)\s+a désormais\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_AUDIT_OPT_OUT_DECLARATION_REVOKED_NEW_AUDITOR = re.compile(
    r"^Die Erklärung vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+über den "
    r"Verzicht auf die eingeschränkte Revision ist gelöscht worden\.\s*"
    r"Neue Revisionsstelle:\s*(?P<name>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),"
    r"\s*in\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_CLAUSE_CHANGED_WITH_HISTORY_TYPO = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})"
    r"\s+die mit Beschluss vom\s+(?P<introduced_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"eingführte und mit Beschluss vom\s+(?P<amended_date>\d{2}\.\d{2}\.\d{4})"
    r"\s+geänderte Bestimmung betreffend genehmigter Kapitalerhöhung gemäss "
    r"näherer Umschreibung in den Statuten geändert\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_PROMOTIONS_AND_SIGNING_CHANGED = re.compile(
    r"^L['’]associé\s+(?P<name1>[^,.;]+)\s+a été nommé gérant et président"
    r"\s*;\s*ses pouvoirs sont modifiés en ce sens\.\s*Le gérant\s+"
    r"(?P<name2>[^,.;]+),\s*nommé vice-président,\s*signe désormais "
    r"collectivement à deux;\s*ses pouvoirs sont modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_DE_CONDITIONAL_CAPITAL_CLAUSE_REINTRODUCED_AFTER_REPEAL = re.compile(
    r"^\[(?P<previous_note>Die Bestimmung über die bedingte Kapitalerhöhung "
    r"ist aufgehoben,.*?)\]\s*\.\s*Die Generalversammlung hat mit Beschluss "
    r"vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+eine bedingte Kapitalerhöhung "
    r"gemäss näherer Umschreibung in den Statuten eingeführt\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_PRESIDENT_AND_THREE_MEMBERS_COLLECTIVE_SIGNING = re.compile(
    r"^Administration:\s*(?P<name1>[^,.;]+),\s*nommé président,\s*"
    r"(?P<name2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*(?P<name3>[^,.;]+),\s*de\s+"
    r"(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+)\s+et\s+"
    r"(?P<name4>[^,.;]+),\s*de\s+(?P<origin4>[^,.;]+),\s*à\s+"
    r"(?P<place4>[^,.;]+),\s*tous trois avec signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_MANAGERS_APPOINTED_WITH_COUNTRY_FRANCE = re.compile(
    r"^Nouveaux gérants:\s*(?P<name1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),"
    r"\s*à\s+(?P<place1>[^,.;]+),\s*F,\s*président,\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*F\.?$",
    re.I | re.UNICODE,
)
_DE_ECCLESIASTICAL_SUPERVISION_BY_BISHOP = re.compile(
    r"^Die kirchliche Aufsicht wird wahrgenommen durch den Bischof des "
    r"Bistums\s+(?P<diocese>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_MERGER_ABSORPTION_SAME_SHAREHOLDER_NO_CAPITAL_INCREASE = re.compile(
    r'^Fusion:\s*Übernahme der Aktiven und Passiven \(Fremdkapital\) der\s*'
    r'"(?P<absorbed_name>[^"]+)"\s*\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\)'
    r'\s*mit Sitz in\s+(?P<absorbed_seat>[^,.;]+),\s*gemäss Fusionsvertrag vom'
    r'\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Fusionsbilanz per\s+'
    r'(?P<balance_sheet_date>\d{2}\.\d{2}\.\d{4})\.\s*Aktiven von CHF\s+'
    r"(?P<assets>[\d'.]+)\s+und Passiven \(Fremdkapital\) von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+gehen auf die übernehmende Gesellschaft "
    r"über\.\s*Da dieselbe Aktionärin sämtliche Aktien der an der Fusion "
    r"beteiligten Gesellschaften hält,\s*findet weder eine Kapitalerhöhung "
    r"noch eine Aktienzuteilung statt\.\s*Die übernehmende Gesellschaft "
    r"verfügt gemäss Bestätigung der zugelassenen Revisionsexpertin vom\s+"
    r"(?P<confirmation_date>\d{2}\.\d{2}\.\d{4})\s+über frei verwendbares "
    r"Eigenkapital im Umfang des Kapitalverlustes und der Überschuldung der "
    r"übertragenden Gesellschaft\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_NEW_ASSOCIATE_MANAGER_AND_PRESIDENT_APPOINTED = re.compile(
    r"^(?P<seller>[^,.;]+?)\s+a cédé\s+(?P<transferred>[\d']+)\s+parts de "
    r"CHF\s+(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+?),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),"
    r"\s*lequel associé est en outre nommé gérant\s+(?P=seller),\s*nommée "
    r"présidente,\s*est maintenant associée pour\s+(?P<remaining>[\d']+)"
    r"\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
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


def extract_parser158_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 158."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_TWO_MEMBERS_SIGNING_CHANGED_TO_WITH_ADMINISTRATOR.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_members_signing_changed_to_with_administrator.v1"
        for group in ("name1", "name2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(group),
                extra={
                    "action": "changed",
                    "previous_signing": "collective_two",
                    "new_requirement": "avec un administrateur",
                },
            ))

    match = _DE_ASSET_TRANSFER_AGREEMENT_ZERO_LIABILITIES.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_agreement_zero_liabilities.v1",
            {
                "date": _iso_date(match.group("date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital",
                "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration").lower(),
                "gratuitous": True,
            },
        ))

    match = _FR_REINSTATEMENT_ORDERED_BY_SUPERPROVISIONAL_MEASURES.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.reinstatement_ordered_by_superprovisional_measures.v1",
            {
                "kind": "reinstatement",
                "action": "ordered",
                "legal_basis": "mesures superprovisionnelles",
                "authority": match.group("authority").strip(),
                "decision_date": _iso_date(match.group("date")),
            },
        ))

    match = _FR_THREE_BOARD_MEMBERS_APPOINTED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.three_board_members_appointed.v1"
        for index in (1, 2, 3):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="membre du conseil",
                extra={
                    "action": "appointed",
                    "origin": match.group(f"origin{index}").strip(),
                },
            ))

    match = _FR_ASSOCIATE_SIGNATURE_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.associate_signature_revoked.v1",
            match.group("name"), role="associée",
            extra={"action": "revoked"},
        ))

    match = _DE_ASSET_TRANSFER_AMENDMENT_CLARIFYING_REAL_ESTATE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_amendment_clarifying_real_estate.v1",
            {
                "kind": "asset_transfer_amendment",
                "action": "clarified",
                "subject": "real_estate",
                "amendment_date": _iso_date(match.group("date")),
                "agreement_date": _iso_date(match.group("agreement_date")),
            },
        ))

    match = _FR_SHARE_TRANSFER_EXISTING_ASSOCIATE_RUNNING_TOTAL.search(leftover)
    if match:
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        remaining = _count(match.group("remaining"))
        nominals = {
            match.group("nominal"),
            match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }
        if before == transferred + remaining and len(nominals) == 1:
            consume(match)
            rule_id = "fr.persons.share_transfer_existing_associate_running_total.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
            events.extend([
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé",
                    extra={
                        **common, "action": "shares_transferred", "counterparty": buyer,
                        "shares_before": before, "shares_transferred": transferred,
                        "shares_count": remaining,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, role="associé",
                    extra={
                        **common, "action": "shares_received", "counterparty": seller,
                        "shares_received": transferred,
                        "shares_count": _count(match.group("buyer_count")),
                    },
                ),
            ])

    match = _DE_AUDIT_OPT_OUT_DECLARATION_REVOKED_NEW_AUDITOR.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "auditor_changed", "de.text.audit_opt_out_declaration_revoked_new_auditor.v1",
            {
                "kind": "audit_opt_out",
                "action": "revoked",
                "declaration_date": _iso_date(match.group("date")),
                "new_auditor": match.group("name").strip(),
                "new_auditor_uid": match.group("uid"),
                "new_auditor_place": match.group("place").strip(),
            },
        ))

    match = _DE_AUTHORIZED_CAPITAL_CLAUSE_CHANGED_WITH_HISTORY_TYPO.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_clause_changed_with_history_typo.v1",
            {
                "kind": "authorized_capital_clause",
                "action": "changed",
                "decision_date": _iso_date(match.group("date")),
                "introduced_date": _iso_date(match.group("introduced_date")),
                "amended_date": _iso_date(match.group("amended_date")),
                "details_in_statutes": True,
                "source_spelling_malformed": True,
            },
        ))

    match = _FR_MANAGER_PROMOTIONS_AND_SIGNING_CHANGED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_promotions_and_signing_changed.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role="gérant, président",
                extra={"action": "appointed"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name2"),
                role="gérant, vice-président",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed_and_signing_changed"},
            ),
        ])

    match = _DE_CONDITIONAL_CAPITAL_CLAUSE_REINTRODUCED_AFTER_REPEAL.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.conditional_capital_clause_reintroduced_after_repeal.v1",
            {
                "kind": "conditional_capital_clause",
                "action": "introduced",
                "decision_date": _iso_date(match.group("date")),
                "previous_action": "repealed",
                "previous_reason": re.sub(r"\s+", " ", match.group("previous_note").strip()),
                "details_in_statutes": True,
            },
        ))

    match = _FR_BOARD_PRESIDENT_AND_THREE_MEMBERS_COLLECTIVE_SIGNING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.board_president_and_three_members_collective_signing.v1"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("name1"), role="président",
            extra={"action": "appointed"},
        ))
        for index in (2, 3, 4):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="administrateur",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed",
                    "origin": match.group(f"origin{index}").strip(),
                },
            ))

    match = _FR_NEW_MANAGERS_APPOINTED_WITH_COUNTRY_FRANCE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.new_managers_appointed_with_country_france.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="gérant, président",
                extra={
                    "action": "appointed", "origin": match.group("origin1").strip(),
                    "country": "France",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="gérant",
                extra={
                    "action": "appointed", "origin": match.group("origin2").strip(),
                    "country": "France",
                },
            ),
        ])

    match = _DE_ECCLESIASTICAL_SUPERVISION_BY_BISHOP.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.ecclesiastical_supervision_by_bishop.v1",
            {
                "kind": "ecclesiastical_supervision",
                "authority": "Bischof",
                "diocese": match.group("diocese").strip(),
            },
        ))

    match = _DE_MERGER_ABSORPTION_SAME_SHAREHOLDER_NO_CAPITAL_INCREASE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "merger", "de.text.merger_absorption_same_shareholder_no_capital_increase.v1",
            {
                "kind": "absorption",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "absorbed_seat": match.group("absorbed_seat").strip(),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_sheet_date": _iso_date(match.group("balance_sheet_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital",
                "currency": "CHF",
                "same_shareholder": True,
                "capital_increase": False,
                "share_allocation": False,
                "auditor_confirmation_date": _iso_date(match.group("confirmation_date")),
            },
        ))

    match = _FR_SHARE_TRANSFER_NEW_ASSOCIATE_MANAGER_AND_PRESIDENT_APPOINTED.search(leftover)
    if match:
        nominals = {
            match.group("nominal"),
            match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }
        if len(nominals) == 1:
            consume(match)
            rule_id = "fr.persons.share_transfer_new_associate_manager_and_president_appointed.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            transferred = _count(match.group("transferred"))
            common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
            events.extend([
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associée, présidente",
                    extra={
                        **common, "action": "shares_transferred_and_appointed_president",
                        "counterparty": buyer, "shares_transferred": transferred,
                        "shares_count": _count(match.group("remaining")),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé, gérant",
                    extra={
                        **common, "action": "appointed_and_shares_received",
                        "counterparty": seller, "new_associate": True,
                        "origin": match.group("origin").strip(),
                        "shares_received": transferred,
                        "shares_count": _count(match.group("buyer_count")),
                    },
                ),
            ])

    return events, re.sub(r"\s+", " ", leftover).strip(" .,;")
