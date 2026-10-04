from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_AUTHORIZED_CAPITAL_LEGACY = re.compile(
    r"^Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+ein genehmigtes Kapital gemäss "
    r"näherer Umschreibung in den Statuten eingeführt\.?$",
    re.I | re.UNICODE,
)
_IT_SHARE_TRANSFER_RESTRICTION_REMOVED_LEGACY = re.compile(
    r"^Nuova limitazione della trasferibilità:\s*"
    r"\[La limitazione alla trasferibilità delle azioni nominative è abrogata\.\]\s*"
    r"\[radiati:\s*La trasferibilità delle azioni nominative è limitata dallo statuto\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_TO_COMPANY = re.compile(
    r"^(?P<seller>.+?)\s+détient désormais\s+(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\s+par suite de cession de\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>.+?)\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel(?:le)? associé(?:e)? pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_DOCUMENT_SUPPLEMENTED = re.compile(
    r"^Der Beleg wurde nachgetragen\.?$", re.I | re.UNICODE
)
_FR_OFFICIAL_DELETION_ART_159A = re.compile(
    r"^Raison de commerce radiée d['’]office conformément à\s+"
    r"l['’](?P<legal_basis>art\.\s*159a,\s*al\.\s*1,\s*lit\.\s*a,\s*ORC)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_APPOINTED_MANAGER = re.compile(
    r"^L['’]associé\s+(?P<name>.+?)\s+nommé\s+(?P<role>gérant),\s*"
    r"signe désormais\s+(?P<sign>individuellement)\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_ASSETS_ONLY = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss "
    r"Vermögensübertragungsvertrag vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+auf die\s+(?P<recipient>.+?)\s+"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+(?P<place>[^.]+)\.\s*"
    r"Gegenleistung:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_PARTNERSHIP_CONTINUED_AS_SOLE_PROPRIETORSHIP = re.compile(
    r"^Die Gesellschaft hat sich infolge Ausscheidens des Gesellschafters\s+"
    r"(?P<departed>.+?)\s+aufgelöst\.\s*Die Firma ist erloschen\.\s*"
    r"Der Gesellschafter\s+(?P<continuing>.+?)\s+führt im Sinne von\s+"
    r"(?P<legal_basis>Art\.\s*579 OR)\s+das Geschäft als Einzelunternehmen fort\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATES_REMOVED_AND_SHARES_TRANSFERRED = re.compile(
    r"^(?P<removed1>[^,.;]+),\s*(?P<removed2>[^,.;]+)\s+ne sont plus associés "
    r"ni gérants,\s*leurs pouvoirs étant radiés;\s*leurs\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+"
    r"ont été cédées à\s+(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé-gérant "
    r"pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),?\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_REGISTERED_SHORT_CANTON = re.compile(
    r"^Inscription de la succursale de\s+(?P<place>.+?)\s+"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+au registre du commerce de\s+"
    r"(?P<register_canton>.+?)\s+\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+(?P<notice_id>\d+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_IDENTIFIER_CORRECTED_SHORT_LABEL = re.compile(
    r"^Le numéro IDE\s+(?P<from>CHE-\d{3}\.\d{3}\.\d{3})\s+étant erroné,\s*"
    r"est remplacé par le numéro IDE suivant:\s*"
    r"(?P<to>CHE-\d{3}\.\d{3}\.\d{3})\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_ROLE_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n[°o]\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_page>\d+)/(?P<notice_id>\d+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<name>.+?)\s+est nommé\s+(?P<role>gérant)\s+"
    r"\(et non\s+(?P<previous_role>président)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_ANCILLARY_OBLIGATIONS_REMOVED_ARTICLE = re.compile(
    r"^Suppression de l['’]obligation de fournir des prestations accessoires,\s*"
    r"droits de préférence,\s*de préemption ou d['’]emption selon les statuts\.?$",
    re.I | re.UNICODE,
)
_FR_COMPACT_APPOINTMENT = re.compile(
    r"^(?P<name>[^,.;]+?)\s+est nommé(?:e)?\s+(?P<role>vice-président(?:e)?)\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_PROCEEDING_RESUMED = re.compile(
    r"^Das Konkursverfahren wird nun durchgeführt,\s*da im Sinne von\s+"
    r"(?P<legal_basis>Art\.\s*230 Abs\.\s*2 SchKG)\s+die Durchführung des "
    r"Konkursverfahrens verlangt und die erforderliche Sicherheit geleistet wurde\.\s*"
    r"\[bisher:\s*Das Konkursverfahren ist mit Urteil des\s+"
    r"(?P<authority>.+?)\s+vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"mangels Aktiven eingestellt worden\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_NAME_AND_BANKRUPTCY = re.compile(
    r"^Neue Firma:\s*(?P<new_name>[^()]+?)\s*"
    r"(?P<translations>(?:\([^)]*\)\s*)*)\.\s*Mit Entscheid vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+(?P<authority>.+?)\s+"
    r"über die Gesellschaft den Konkurs mit Wirkung ab dem\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<time>\d{1,2}[.:]\d{2})\s+Uhr,\s*eröffnet\.?$",
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
        person_key=(f"uid:{uid}" if uid else person_key(name=clean_name, place=clean_place)),
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


def extract_parser64_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 64."""
    del language  # Historical records can contain a different language in this field.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_AUTHORIZED_CAPITAL_LEGACY.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.authorized_capital_legacy.v1",
                {
                    "kind": "authorized_capital_clause",
                    "action": "introduced",
                    "date": _iso_date(match.group("date")),
                    "basis": "statutes",
                },
            )
        )

    match = _IT_SHARE_TRANSFER_RESTRICTION_REMOVED_LEGACY.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "it.text.share_transfer_restriction_removed.v2",
                {
                    "kind": "share_transfer_restricted",
                    "action": "removed",
                    "previously_restricted_by_statutes": True,
                },
            )
        )

    match = _FR_ASSOCIATE_TRANSFER_TO_COMPANY.search(leftover)
    if match:
        consume(match)
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {
            "shares_transferred": _count(match.group("transferred")),
            "transferred_nominal": match.group("nominal"),
        }
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.associate_transfer_to_company.v1",
                    seller, role="associé",
                    extra={
                        "action": "shares_transferred",
                        "counterparty": buyer,
                        "counterparty_uid": match.group("uid"),
                        "shares_count": _count(match.group("seller_count")),
                        "shares_nominal": match.group("seller_nominal"),
                        **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.associate_transfer_to_company.v1",
                    buyer, place=match.group("place"), uid=match.group("uid"),
                    role="associée",
                    extra={
                        "action": "shares_received",
                        "counterparty": seller,
                        "shares_received": _count(match.group("transferred")),
                        "shares_count": _count(match.group("buyer_count")),
                        "shares_nominal": match.group("buyer_nominal"),
                    },
                ),
            ]
        )

    match = _DE_DOCUMENT_SUPPLEMENTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", "de.text.document_supplemented.v1",
                {"kind": "supporting_document", "action": "supplemented"},
            )
        )

    match = _FR_OFFICIAL_DELETION_ART_159A.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_deleted", "fr.text.official_deletion_art_159a.v1",
                {
                    "reason": "official_deletion",
                    "deletion_mode": "ex_officio",
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                },
            )
        )

    match = _FR_ASSOCIATE_APPOINTED_MANAGER.search(leftover)
    if match:
        consume(match)
        common = {"action": "appointed", "existing_role": "associé"}
        for event_type, rule_id in (
            ("officer_changed", "fr.persons.associate_appointed_manager.v1"),
            ("signing_authority_changed", "fr.persons.associate_appointed_manager_signing.v1"),
        ):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    event_type, rule_id, match.group("name"),
                    role=match.group("role"), signing="Einzelunterschrift", extra=common,
                )
            )

    match = _DE_ASSET_TRANSFER_ASSETS_ONLY.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.asset_transfer_assets_only.v1",
                {
                    "date": _iso_date(match.group("date")),
                    "assets": match.group("assets"),
                    "recipient": match.group("recipient").strip(),
                    "recipient_uid": match.group("uid"),
                    "recipient_place": match.group("place").strip(),
                    "consideration": f"CHF {match.group('consideration')}",
                },
            )
        )

    match = _DE_PARTNERSHIP_CONTINUED_AS_SOLE_PROPRIETORSHIP.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_deleted", "de.text.partnership_continued_as_sole_proprietorship.v1",
                {
                    "reason": "partner_exit",
                    "departed_partner": match.group("departed").strip(),
                    "company_extinguished": True,
                    "business_continued": True,
                    "continuing_owner": match.group("continuing").strip(),
                    "successor_legal_form": "sole_proprietorship",
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                },
            )
        )

    match = _FR_ASSOCIATES_REMOVED_AND_SHARES_TRANSFERRED.search(leftover)
    if match:
        consume(match)
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        nominal = match.group("nominal")
        for group in ("removed1", "removed2"):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", "fr.persons.associates_removed_transfer.v1",
                    match.group(group), role="associé-gérant",
                    extra={
                        "action": "removed",
                        "signing_revoked": True,
                        "shares_transferred_jointly": transferred,
                        "shares_nominal": nominal,
                        "counterparty": buyer,
                    },
                )
            )
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.associates_removed_transfer.v1",
                buyer, place=match.group("place"), role="associé-gérant",
                extra={
                    "action": "shares_received",
                    "heimat": match.group("origin").strip(),
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "shares_nominal": match.group("buyer_nominal"),
                },
            )
        )

    match = _FR_BRANCH_REGISTERED_SHORT_CANTON.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", "fr.text.branch_registered_short_canton.v1",
                {
                    "action": "registered",
                    "place": match.group("place").strip(),
                    "branch_uid": match.group("uid"),
                    "register_canton": match.group("register_canton").strip(),
                    "source_notice_date": _iso_date(match.group("notice_date")),
                    "source_notice_id": match.group("notice_id"),
                },
            )
        )

    match = _FR_COMPANY_IDENTIFIER_CORRECTED_SHORT_LABEL.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_identifier_changed", "fr.text.company_identifier_corrected.v2",
                {
                    "scope": "organization",
                    "action": "corrected",
                    "from": match.group("from"),
                    "to": match.group("to"),
                },
            )
        )

    match = _FR_PERSON_ROLE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.role_corrected.v1",
                match.group("name"), role=match.group("role"),
                extra={
                    "action": "role_corrected",
                    "previous_role": match.group("previous_role"),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "source_notice_date": _iso_date(match.group("notice_date")),
                    "source_notice_page": match.group("notice_page"),
                    "source_notice_id": match.group("notice_id"),
                },
            )
        )

    match = _FR_ANCILLARY_OBLIGATIONS_REMOVED_ARTICLE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "fr.text.ancillary_obligations_removed.v3",
                {
                    "kind": "ancillary_obligations_and_preferential_rights",
                    "action": "removed",
                },
            )
        )

    match = _FR_COMPACT_APPOINTMENT.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.compact_appointment.v1",
                match.group("name"), role=match.group("role"),
                extra={"action": "appointed"},
            )
        )

    match = _DE_BANKRUPTCY_PROCEEDING_RESUMED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.bankruptcy_proceeding_resumed.v1",
                {
                    "kind": "bankruptcy_proceedings_resumed",
                    "reason": "request_and_security",
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                    "execution_requested": True,
                    "security_provided": True,
                    "previous_status": "suspended_lack_of_assets",
                    "previous_decision_date": _iso_date(match.group("date")),
                    "authority": match.group("authority").strip(),
                },
            )
        )

    match = _DE_COMPANY_NAME_AND_BANKRUPTCY.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.bankruptcy_opened_name_prefix.v1",
                {
                    "kind": "bankruptcy_opened",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "effective_date": _iso_date(match.group("effective_date")),
                    "effective_time": match.group("time").replace(".", ":"),
                    "authority": match.group("authority").strip().rstrip(","),
                    "new_company_name": match.group("new_name").strip(),
                    "new_translations": re.findall(
                        r"\(([^()]*)\)", match.group("translations")
                    ),
                },
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
