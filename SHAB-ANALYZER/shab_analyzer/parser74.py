from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_OMITTED_NO_CHANGE_NOTE = re.compile(
    r"^Die Bemerkung, dass die publikationspflichtigen Tatsachen keine Änderung "
    r"erfahren haben, wurde irrtümlich vergessen\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_CONTRIBUTION_IN_KIND_CONTINUATION = re.compile(
    r'^eingetragenen Einzelfirma ["“](?P<source>.+?)["”] gemäss Sacheinlagevertrag '
    r"vom (?P<agreement_date>\d{2}\.\d{2}\.\d{4}) und Bilanz per "
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4}) mit Aktiven von CHF "
    r"(?P<assets>[\d'.-]+) und Passiven von CHF (?P<liabilities>[\d'.-]+) "
    r"zum Preis von CHF (?P<accepted_value>[\d'.-]+), wofür "
    r"(?P<shares>[\d']+) Namenaktien zu CHF (?P<nominal>[\d'.-]+) "
    r"ausgegeben werden\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_CORRECTION_INTRODUCTION = re.compile(
    r"^Die Eintragung Nr\.\s*(?P<entry>[\d']+) vom "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) \(SHAB vom "
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\) ist wie folgt berichtigt:$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_DOMICILE_SUPPLEMENTED = re.compile(
    r"^L['’]inscription (?:no|n°)\s*(?P<entry>[\d']+) du "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) est complétée en ce sens que "
    r"l['’]administratrice présidente (?P<name>.+?) est maintenant "
    r"domiciliés? à (?P<place>[^,.;]+),\s*(?P<country>[A-Z]{2,3})\.?$",
    re.I | re.UNICODE,
)
_IT_CONDITIONAL_CAPITAL_CLAUSE = re.compile(
    r"^L['’]assemblea generale ha introdotto una disposizione statutaria relativa "
    r"all['’]aumento condizionale del capitale(?: azionario)? mediante decisione del "
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.\s*Per i dettagli vedi statuti\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_APPOINTMENTS_WITH_TYPO = re.compile(
    r"^L['’]administrateur (?P<president>[^,.;]+),\s*nom{2,3}é président,\s*"
    r"continue à signer individuellement\.\s*"
    r"(?P<secretary>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<secretary_origin>[^,.;]+),\s*à\s*(?P<secretary_place>[^,.;]+),\s*"
    r"secrétaire,\s*et\s*(?P<member>[^,.;]+),\s*de et à\s*"
    r"(?P<member_place>[^,.;]+),\s*sont membres du conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_FR_NON_PUBLIC_STATUTES_TYPO = re.compile(
    r"^sutr des points non soumis à publication\.?$",
    re.I | re.UNICODE,
)
_DE_COOPERATIVE_AUDIT_WAIVER = re.compile(
    r"^Gemäss Erklärung aller Gründer vom (?P<date>\d{2}\.\d{2}\.\d{4}) "
    r"untersteht die (?P<entity>Genossenschaft) keiner ordentlichen Revision und "
    r"verzichtet auf eine eingeschränkte Revision\.?$",
    re.I | re.UNICODE,
)
_IT_OWNER_BANKRUPTCY_PARTIALLY_SUSPENDED = re.compile(
    r"^\[radiati:\s*Il titolare è stato dichiarato in fallimento con decreto della "
    r"(?P<court>.+?) del (?P<opening_date>\d{2}\.\d{2}\.\d{4}) a far tempo dal "
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}) alle ore (?P<effective_time>\d{2}:\d{2})\.\]\.\s*"
    r"Con decisione del (?P<decision_date>\d{2}\.\d{2}\.\d{4}) "
    r"(?P<authority>.+?) ha accordato effetto sospensivo parziale al reclamo inoltrato "
    r"contro la decisione di fallimento aperto nei confronti del titolare il "
    r"(?P<appealed_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_AND_MANAGER_APPOINTMENT = re.compile(
    r"^(?P<seller>[^,.;]+),\s*nommée présidente,\s*a cédé "
    r"(?P<transferred>[\d']+) parts de CHF (?P<nominal>[\d'.]+) à "
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s*(?P<place>[^,.;]+),\s*nouvelle associée pour "
    r"(?P<buyer_count>[\d']+) parts de CHF (?P<buyer_nominal>[\d'.]+);\s*"
    r"laquelle associée est en outre nommée gérante\.?$",
    re.I | re.UNICODE,
)
_DE_PREVIOUS_PERSON_RECORD_CORRECTED = re.compile(
    r"^Gemäss TR (?P<entry>[\d']+) vom (?P<entry_date>\d{2}\.\d{2}\.\d{4}) wurde "
    r"(?P<last>[^,.;]+),\s*(?P<first>[^,.;]+),\s*von\s*(?P<origin>[^,.;]+),\s*"
    r"in\s*(?P<place>[^(),.;]+)\s*\((?P<place_canton>[A-Z]{2})\),\s*"
    r"(?P<roles>.+?),\s*mit Einzelunterschrift\s*\[bisher:\s*"
    r"(?P<incorrect>[^\]]+)\]\s*publiziert,\s*der bisher Text wäre korrekt\s*"
    r"\[(?P<correct>[^\]]+)\]\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_REGISTER_SUFFIX = re.compile(
    r"^\(HR\s+(?P<register_canton>[A-Z]{2})\)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_ORGANIZATION_NAME_CORRECTED = re.compile(
    r"^L['’]inscription (?:no|n°)\s*(?P<entry>[\d']+) du "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) est rectifiée en ce sens que la nouvelle "
    r"associée porte la raison sociale suivante:\s*(?P<name>.+?)\s*"
    r"\((?P<registry_id>[^)]+)\) et non (?P<previous>.+?)\s*"
    r"\((?P<previous_registry_id>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_MALFORMED_NEW_UID = re.compile(
    r"^,?\s*mit\s*:\s*\.\s*UID neu:\s*(?P<to>CHE-\d{3}\.\d{3}\.\d{3})\.?$",
    re.I | re.UNICODE,
)
_FR_COMMISSIONER = re.compile(
    r"^Commissaire:\s*(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"à\s*(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGERS_AFTER_TRANSFER = re.compile(
    r"^(?P<seller>[^,.;]+) a cédé (?P<transferred>[\d']+) parts de CHF "
    r"(?P<nominal>[\d'.]+) à (?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s*"
    r"(?P<place>[^,.;]+)\.\s*Associés-gérants:\s*(?P=seller) pour "
    r"(?P<seller_count>[\d']+) parts de CHF (?P<seller_nominal>[\d'.]+),\s*"
    r"nommé président,\s*et\s*(?P=buyer) pour (?P<buyer_count>[\d']+) parts de "
    r"CHF (?P<buyer_nominal>[\d'.]+),\s*tous deux\.?$",
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


def extract_parser74_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 74."""
    del language  # Historical records can contain a different language in this field.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_OMITTED_NO_CHANGE_NOTE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", "de.text.omitted_no_change_note.v1",
                {
                    "action": "supplemented",
                    "kind": "no_change_note",
                    "publication_relevant_facts_changed": False,
                    "previously_omitted_by_error": True,
                },
            )
        )

    match = _DE_REMOVED_CONTRIBUTION_IN_KIND_CONTINUATION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "de.text.contribution_in_kind_removed_continuation.v1",
                {
                    "action": "removed",
                    "kind": "contribution_in_kind",
                    "source": match.group("source").strip(),
                    "source_kind": "unregistered_sole_proprietorship",
                    "agreement_date": _iso_date(match.group("agreement_date")),
                    "balance_date": _iso_date(match.group("balance_date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "accepted_value": match.group("accepted_value"),
                    "consideration_shares": _count(match.group("shares")),
                    "consideration_nominal": match.group("nominal"),
                    "currency": "CHF",
                },
            )
        )

    match = _DE_CORRECTION_INTRODUCTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", "de.text.correction_introduction.v1",
                {
                    "action": "corrected",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                },
            )
        )

    match = _FR_ADMINISTRATOR_DOMICILE_SUPPLEMENTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.administrator_domicile_supplemented.v1",
                match.group("name"), place=match.group("place"),
                role="administratrice présidente",
                extra={
                    "action": "domicile_supplemented",
                    "domicile_changed": True,
                    "country": match.group("country"),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                },
            )
        )

    match = _IT_CONDITIONAL_CAPITAL_CLAUSE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "it.text.conditional_capital_clause_without_azionario.v1",
                {
                    "kind": "conditional_capital_clause",
                    "action": "introduced",
                    "decision_date": _iso_date(match.group("date")),
                    "details_in_statutes": True,
                },
            )
        )

    match = _FR_BOARD_APPOINTMENTS_WITH_TYPO.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.board_appointments_nommme_typo.v1"
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président du conseil d'administration",
                signing="Einzelunterschrift",
                extra={"action": "role_changed", "signing_continues": True},
            )
        )
        for name_group, origin, place, role in (
            (
                "secretary", match.group("secretary_origin"),
                match.group("secretary_place"), "secrétaire du conseil d'administration",
            ),
            ("member", match.group("member_place"), match.group("member_place"),
             "membre du conseil d'administration"),
        ):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(name_group), place=place,
                    role=role, signing="Einzelunterschrift",
                    extra={"action": "appointed", "heimat": origin.strip()},
                )
            )

    match = _FR_NON_PUBLIC_STATUTES_TYPO.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "fr.text.non_public_statutes_sutr_typo.v1",
                {
                    "kind": "non_public_statute_changes",
                    "non_public_changes": True,
                    "publication_relevant_facts_changed": False,
                },
            )
        )

    match = _DE_COOPERATIVE_AUDIT_WAIVER.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "audit_requirement_changed", "de.text.cooperative_audit_waiver.v1",
                {
                    "kind": "limited_audit_waiver",
                    "action": "granted",
                    "date": _iso_date(match.group("date")),
                    "declarants": "all_founders",
                    "entity_kind": match.group("entity").lower(),
                    "ordinary_audit_required": False,
                },
            )
        )

    match = _IT_OWNER_BANKRUPTCY_PARTIALLY_SUSPENDED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "it.text.owner_bankruptcy_partially_suspended.v1",
                {
                    "kind": "bankruptcy_effect_suspended",
                    "scope": "owner",
                    "suspension": "partial",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "bankruptcy_decision_date": _iso_date(match.group("opening_date")),
                    "appealed_decision_date": _iso_date(match.group("appealed_date")),
                    "effective_at": (
                        f"{_iso_date(match.group('effective_date'))}T"
                        f"{match.group('effective_time')}"
                    ),
                    "authority": match.group("authority").strip(),
                    "bankruptcy_court": match.group("court").strip(),
                    "previous_entry_removed": True,
                },
            )
        )

    match = _FR_ASSOCIATE_TRANSFER_AND_MANAGER_APPOINTMENT.search(leftover)
    if match:
        consume(match)
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        rule_id = "fr.persons.associate_transfer_manager_appointment.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller,
                    role="associée-gérante présidente", signing="Einzelunterschrift",
                    extra={
                        "action": "shares_transferred_and_appointed",
                        "counterparty": buyer,
                        "shares_transferred": transferred,
                        "shares_nominal": match.group("nominal"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associée-gérante", signing="Einzelunterschrift",
                    extra={
                        "action": "shares_received_and_appointed",
                        "heimat": match.group("origin").strip(),
                        "counterparty": seller,
                        "shares_received": transferred,
                        "shares_count": _count(match.group("buyer_count")),
                        "shares_nominal": match.group("buyer_nominal"),
                    },
                ),
            ]
        )

    match = _DE_PREVIOUS_PERSON_RECORD_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", "de.persons.previous_signing_corrected.v1",
                f"{match.group('last').strip()}, {match.group('first').strip()}",
                place=match.group("place"), role=match.group("roles").strip(),
                signing="Einzelunterschrift",
                extra={
                    "action": "previous_record_corrected",
                    "heimat": match.group("origin").strip(),
                    "place_canton": match.group("place_canton"),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "incorrect_previous": match.group("incorrect").strip(),
                    "correct_previous": match.group("correct").strip(),
                },
            )
        )

    match = _DE_BRANCH_REGISTER_SUFFIX.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", "de.text.branch_register_suffix.v1",
                {
                    "action": "register_specified",
                    "register_canton": match.group("register_canton").upper(),
                    "applies_to_previous_branch": True,
                },
            )
        )

    match = _FR_ASSOCIATE_ORGANIZATION_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.associate_organization_name_corrected.v1",
                match.group("name"), role="associée",
                extra={
                    "action": "name_corrected",
                    "previous": match.group("previous").strip(),
                    "registry_id": match.group("registry_id").strip(),
                    "previous_registry_id": match.group("previous_registry_id").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                },
            )
        )

    match = _DE_MALFORMED_NEW_UID.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_identifier_changed", "de.text.malformed_new_uid.v1",
                {"scope": "organization", "action": "changed", "to": match.group("to")},
            )
        )

    match = _FR_COMMISSIONER.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.commissioner.v1",
                match.group("name"), place=match.group("place"), role="commissaire",
                signing="Einzelunterschrift",
                extra={"action": "appointed", "heimat": match.group("origin").strip()},
            )
        )

    match = _FR_ASSOCIATE_MANAGERS_AFTER_TRANSFER.search(leftover)
    if match:
        consume(match)
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        rule_id = "fr.persons.associate_managers_after_transfer.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller,
                    role="associé-gérant président", signing="Einzelunterschrift",
                    extra={
                        "action": "shares_transferred_and_appointed",
                        "counterparty": buyer,
                        "shares_transferred": transferred,
                        "shares_count": _count(match.group("seller_count")),
                        "shares_nominal": match.group("seller_nominal"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé-gérant", signing="Einzelunterschrift",
                    extra={
                        "action": "shares_received_and_appointed",
                        "heimat": match.group("origin").strip(),
                        "counterparty": seller,
                        "shares_received": transferred,
                        "shares_count": _count(match.group("buyer_count")),
                        "shares_nominal": match.group("buyer_nominal"),
                    },
                ),
            ]
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
