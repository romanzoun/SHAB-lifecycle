from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_ASSOCIATE_MANAGER_TRANSFER = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+) de ses\s+(?P<before>[\d']+) parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à l['’]associé-gérant\s+(?P<buyer>.+?)\s+"
    r"désormais titulaire de\s+(?P<buyer_count>[\d']+) parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*L['’]associé-gérant\s+(?P=seller)\s+"
    r"reste titulaire de\s+(?P<seller_count>[\d']+) parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_AUTHORIZED_CAPITAL_INTRODUCED = re.compile(
    r"^L['’]assemblée générale a introduit une clause statutaire relative à une "
    r"augmentation autorisée du capital par décision du\s+"
    r"(?P<date>\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|"
    r"septembre|octobre|novembre|décembre)\s+\d{4})\.\s*"
    r"Pour les détails,\s*voir les statuts\.?$",
    re.I | re.UNICODE,
)
_DE_OUTGOING_SPIN_OFF_TWO_RECIPIENTS = re.compile(
    r"^Abspaltung:\s*Ein Teil der Aktiven und Passiven geht gemäss Spaltungsplan vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+auf die neu gegründete\s+"
    r"(?P<recipient1>.+?),\s*in\s+(?P<place1>[^()]+?)\s*"
    r"\((?P<uid1>CHE-\d{3}\.\d{3}\.\d{3})\)\s+und die neu gegründete\s+"
    r"(?P<recipient2>.+?),\s*in\s+(?P<place2>[^()]+?)\s*"
    r"\((?P<uid2>CHE-\d{3}\.\d{3}\.\d{3})\)\s+über\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_WITH_NEW_HOLDER = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+) de ses\s+"
    r"(?P<before>[\d']+) parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*nouvel associé sans signature,\s*"
    r"titulaire de\s+(?P<buyer_count>[\d']+) parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*(?P=seller)\s+a maintenant\s+"
    r"(?P<seller_count>[\d']+) parts de CHF\s+(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_PURPOSE = re.compile(
    r"^Der Zweck der Zweigniederlassung besteht darin,\s*(?P<purpose>.+)\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_DE_REMOVED_PERSON_AND_AUDITOR_REPLACED = re.compile(
    r"^Gelöschte Person:\s*(?P<person>[^,.;]+),\s*"
    r"(?P<person_role1>[^,.;]+),\s*(?P<person_role2>[^,.;]+),\s*"
    r"(?P<person_sign>Einzelunterschrift|Kollektivunterschrift(?:\s+zu\s+zweien)?)\.\s*"
    r"(?P<old_auditor>.+?)\s*\((?P<old_registry>CH-[\d-]+)\),\s*Revisionsstelle\.\s*"
    r"Neu eingetragene Person:\s*(?P<new_auditor>.+?)\s*"
    r"\((?P<new_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+"
    r"(?P<new_place>[^,.;]+),\s*Revisionsstelle\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_WITHOUT_LIABILITIES = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_APPOINTED_MANAGER = re.compile(
    r"^L['’]associé\s+(?P<name>[^,.;]+)\s+est nommé gérant\.?$",
    re.I | re.UNICODE,
)
_DE_PROFIT_CERTIFICATE_SINGULAR = re.compile(
    r"^Genussscheine neu:\s*(?P<count>1) Genussschein,\s*"
    r"mit Rechten auf\s+(?P<rights>.+?)\s+gemäss Statuten\.?$",
    re.I | re.UNICODE,
)
_IT_OWNER_BANKRUPTCY_PARTIALLY_SUSPENDED = re.compile(
    r"^Con decisione del\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"(?P<authority>.+?)\s+ha accordato effetto sospensivo parziale al reclamo "
    r"inoltrato contro la decisione di fallimento aperto nei confronti del titolare il\s+"
    r"(?P<appealed_date>\d{2}\.\d{2}\.\d{4})\.\s*\[finora:\s*"
    r"Il titolare è stato dichiarato in fallimento con decreto della\s+"
    r"(?P<bankruptcy_court>.+?)\s+del\s+(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"a far tempo dal\s+(?P<effective_date>\d{2}\.\d{2}\.\d{4})\s+alle ore\s+"
    r"(?P<effective_time>\d{2}[.:]\d{2})\.\]\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_FR_COMMITTEE_MEMBER_SAME_PLACE = re.compile(
    r"^(?P<name>[^,.;]+),\s*de et à\s+(?P<place>[^,.;]+),\s*"
    r"est membre du comité,\s*sans signature\.?$",
    re.I | re.UNICODE,
)
_IT_AUDIT_WAIVER_CON_DECLARATION = re.compile(
    r"^Con dichiarazione del\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+la società "
    r"non è soggetta alla revisione ordinaria e rinuncia a una revisione limitata\.?$",
    re.I | re.UNICODE,
)
_FR_CANTONAL_COURT_BANKRUPTCY_SUSPENDED = re.compile(
    r"^(?P<authority>La présidente de la Cour des poursuites et faillites du "
    r"Tribunal cantonal) a prononcé l['’]effet suspensif de la procédure de "
    r"faillite le\s+(?P<date>\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|"
    r"juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_NEW_ASSOCIATE = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+) de ses\s+"
    r"(?P<before>[\d']+) parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*nouvelle associée avec\s+"
    r"(?P<buyer_count>[\d']+) parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"(?P=seller)\s+reste titulaire d['’](?P<seller_count>[\d']+) part(?:s)? de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_AOR_SHAB_DELETION_BLOCKED = re.compile(
    r"^Auf die durch das Handelsregisteramt gestützt auf\s+"
    r"(?P<legal_basis>Art\.\s*934 Abs\.\s*2 aOR sowie Art\.\s*152 Abs\.\s*1 HRegV)\s+"
    r"veranlassten und im SHAB mit Meldungsnummern\s+(?P<issues>.+?)\s+"
    r"publizierten Aufforderungen haben sich keine weiteren Betroffenen gemeldet\.\s*"
    r"Das amtliche Verfahren zur Löschung der Rechtseinheit ist damit abgeschlossen\.\s*"
    r"Sie kann mangels Zustimmung des kantonalen Steueramtes jedoch noch nicht "
    r"gelöscht werden\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_IT_INTENDED_ASSET_ACQUISITION_REMOVED = re.compile(
    r"^Fatti particolari:\s*\[no:\s*Intenzione di assunzione beni:\s*"
    r"la società intende acquistare\s+(?P<asset>.+?)\s+per il prezzo di CHF\s+"
    r"(?P<price>[\d'.]+)\.\]\.?$",
    re.I | re.DOTALL | re.UNICODE,
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


def _french_date(raw: str) -> str:
    day, month, year = raw.strip().lower().split()
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


def _share_transfer_events(
    match: re.Match[str],
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
    rule_id: str,
    *,
    seller_role: str = "associé",
    buyer_role: str = "associé",
    buyer_place: str | None = None,
    buyer_extra: dict | None = None,
) -> list[Event]:
    seller = match.group("seller").strip()
    buyer = match.group("buyer").strip()
    transferred = _count(match.group("transferred"))
    return [
        _person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, seller, role=seller_role,
            extra={
                "action": "shares_transferred",
                "counterparty": buyer,
                "shares_before": _count(match.group("before")),
                "shares_transferred": transferred,
                "shares_count": _count(match.group("seller_count")),
                "shares_nominal": match.group("seller_nominal"),
            },
        ),
        _person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, buyer, place=buyer_place, role=buyer_role,
            extra={
                "action": "shares_received",
                "counterparty": seller,
                "shares_received": transferred,
                "shares_count": _count(match.group("buyer_count")),
                "shares_nominal": match.group("buyer_nominal"),
                **(buyer_extra or {}),
            },
        ),
    ]


def extract_parser78_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 78."""
    del language  # Historical publications can mix languages.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_ASSOCIATE_MANAGER_TRANSFER.search(leftover)
    if match:
        consume(match)
        events.extend(
            _share_transfer_events(
                match, publication_id, published_at, org_uid, plz, canton,
                "fr.persons.associate_manager_transfer.v1",
                seller_role="associé-gérant", buyer_role="associé-gérant",
            )
        )

    match = _FR_AUTHORIZED_CAPITAL_INTRODUCED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.authorized_capital_clause_introduced.v1",
                {
                    "kind": "authorized_capital_clause",
                    "action": "introduced",
                    "decision_date": _french_date(match.group("date")),
                },
            )
        )

    match = _DE_OUTGOING_SPIN_OFF_TWO_RECIPIENTS.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.outgoing_spin_off_two_recipients.v1",
                {
                    "kind": "spin_off_distribution",
                    "date": _iso_date(match.group("date")),
                    "scope": "part_of_assets_and_liabilities",
                    "recipients": [
                        {
                            "name": match.group(f"recipient{index}").strip(),
                            "place": match.group(f"place{index}").strip(),
                            "uid": match.group(f"uid{index}"),
                            "newly_founded": True,
                        }
                        for index in (1, 2)
                    ],
                },
            )
        )

    match = _FR_ASSOCIATE_TRANSFER_WITH_NEW_HOLDER.search(leftover)
    if match:
        consume(match)
        events.extend(
            _share_transfer_events(
                match, publication_id, published_at, org_uid, plz, canton,
                "fr.persons.associate_transfer_new_holder.v1",
                buyer_place=match.group("place"),
                buyer_extra={
                    "heimat": match.group("origin").strip(),
                    "without_signature": True,
                    "new_associate": True,
                },
            )
        )

    match = _DE_BRANCH_PURPOSE.search(leftover)
    if match:
        consume(match)
        purpose = match.group("purpose").strip().rstrip(".")
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "purpose_changed", "de.text.branch_purpose.v1",
                {"scope": "branch", "purpose": purpose},
            )
        )

    match = _DE_REMOVED_PERSON_AND_AUDITOR_REPLACED.search(leftover)
    if match:
        consume(match)
        rule_id = "de.persons.removed_person_and_auditor_replaced.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", rule_id, match.group("person"),
                    role=(
                        f"{match.group('person_role1').strip()}, "
                        f"{match.group('person_role2').strip()}"
                    ),
                    signing=match.group("person_sign"),
                    extra={"action": "removed"},
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", rule_id, match.group("old_auditor"),
                    role="Revisionsstelle",
                    extra={
                        "action": "removed",
                        "registry_id": match.group("old_registry"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("new_auditor"),
                    place=match.group("new_place"), uid=match.group("new_uid"),
                    role="Revisionsstelle",
                    extra={"action": "appointed", "uid": match.group("new_uid")},
                ),
            ]
        )

    match = _DE_ASSET_TRANSFER_WITHOUT_LIABILITIES.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.asset_transfer_without_liabilities.v1",
                {
                    "date": _iso_date(match.group("date")),
                    "assets": match.group("assets"),
                    "currency": "CHF",
                    "liabilities_transferred": False,
                    "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration": f"CHF {match.group('consideration')}",
                    "consideration_kind": "cash",
                    "consideration_amount": match.group("consideration"),
                },
            )
        )

    match = _FR_ASSOCIATE_APPOINTED_MANAGER.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.associate_appointed_manager.v1",
                match.group("name"), role="associé-gérant",
                signing="Einzelunterschrift",
                extra={"action": "appointed", "previous_role": "associé"},
            )
        )

    match = _DE_PROFIT_CERTIFICATE_SINGULAR.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.participation_certificate_added_singular.v1",
                {
                    "kind": "participation_certificates",
                    "action": "added",
                    "to_count": _count(match.group("count")),
                    "rights": match.group("rights").strip(),
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
                    "kind": "bankruptcy_effect_partially_suspended",
                    "scope": "sole_proprietor_owner",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "authority": match.group("authority").strip(),
                    "appealed_bankruptcy_date": _iso_date(match.group("appealed_date")),
                    "bankruptcy_court": match.group("bankruptcy_court").strip(),
                    "bankruptcy_decision_date": _iso_date(match.group("bankruptcy_date")),
                    "bankruptcy_effective_date": _iso_date(match.group("effective_date")),
                    "bankruptcy_effective_time": match.group("effective_time").replace(".", ":"),
                },
            )
        )

    match = _FR_COMMITTEE_MEMBER_SAME_PLACE.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.committee_member_same_place.v1",
                match.group("name"), place=match.group("place"), role="membre du comité",
                extra={"action": "appointed", "without_signature": True},
            )
        )

    match = _IT_AUDIT_WAIVER_CON_DECLARATION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "audit_requirement_changed", "it.text.audit_waiver_con_declaration.v1",
                {
                    "kind": "limited_audit_waiver",
                    "action": "granted",
                    "date": _iso_date(match.group("date")),
                },
            )
        )

    match = _FR_CANTONAL_COURT_BANKRUPTCY_SUSPENDED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "fr.text.cantonal_court_bankruptcy_suspended.v1",
                {
                    "kind": "bankruptcy_effect_suspended",
                    "date": _french_date(match.group("date")),
                    "authority": match.group("authority"),
                },
            )
        )

    match = _FR_ASSOCIATE_TRANSFER_NEW_ASSOCIATE.search(leftover)
    if match:
        consume(match)
        events.extend(
            _share_transfer_events(
                match, publication_id, published_at, org_uid, plz, canton,
                "fr.persons.associate_transfer_new_associate.v1",
                buyer_extra={"new_associate": True},
            )
        )

    match = _DE_AOR_SHAB_DELETION_BLOCKED.search(leftover)
    if match:
        consume(match)
        issues = re.findall(r"BH\d{2}-\d+", match.group("issues"), re.I)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.aor_shab_deletion_blocked.v1",
                {
                    "kind": "deletion_blocked",
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                    "procedure_completed": True,
                    "issues": issues,
                    "affected_parties_responded": False,
                    "tax_authority": "cantonal_tax_office",
                    "tax_authority_consent_missing": True,
                },
            )
        )

    match = _IT_INTENDED_ASSET_ACQUISITION_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "it.text.intended_asset_acquisition_removed.v1",
                {
                    "kind": "intended_asset_acquisition",
                    "action": "removed_as_incorrect",
                    "asset": match.group("asset").strip(),
                    "price": match.group("price"),
                    "currency": "CHF",
                },
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
