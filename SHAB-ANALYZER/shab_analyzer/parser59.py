from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_BANKRUPTCY_APPEAL_REJECTED_NUMERIC = re.compile(
    r"Par arrêt du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>.+?)\s+a rejeté le recours contre le jugement du\s+"
    r"(?P<judgment_date>\d{2}\.\d{2}\.\d{4}),\s*par conséquent,\s*"
    r"la faillite est prononcée avec effet à partir du\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+à\s+"
    r"(?P<time>\d{1,2}:\d{2})(?:\s+et|\.\s*Par conséquent,)?\s*"
    r"sa raison sociale devient:\s*(?P<name>.+?)\.?,?\s*$",
    re.I | re.UNICODE,
)
_FR_LIQUIDATORS_THREE = re.compile(
    r"Liquidateurs:\s*les administrateurs\s+(?P<name1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+)\s+et\s+(?P<name3>[^,.;]+),\s*lesquels "
    r"continuent à signer\s+(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?,?",
    re.I | re.UNICODE,
)
_FR_APPOINTED_ADMIN_PROCURATION_REVOKED = re.compile(
    r"Signature\s+(?P<sign>individuelle|collective(?:\s+à\s+deux)?)\s+"
    r"a été conférée à\s+(?P<name>[^,.;]+),\s*nommé(?:e)?\s+"
    r"(?P<role>administrateur|administratrice);\s*sa procuration est radiée\.?,?",
    re.I | re.UNICODE,
)
_FR_SOLE_PROPRIETOR_OFFICIAL_DELETION = re.compile(
    r"L['’]entreprise individuelle ayant cessé ses activités,\s*elle est radiée "
    r"d['’]office,\s*conformément à l['’]art\.\s*(?P<article>159a,\s*al\.\s*2,\s*lit\.\s*b ORC)\.?,?",
    re.I | re.UNICODE,
)
_DE_EMPTY_FUNDS_HEADING = re.compile(r"^\s*Mittel neu:\s*$", re.I | re.UNICODE)
_DE_SOLE_PROPRIETOR_ASSET_TRANSFER = re.compile(
    r"Vermögensübertragung:\s*Der Geschäftsinhaber überträgt gemäss "
    r"Vermögensübertragungsvertrag vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"und Inventar per\s+(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+und Passiven \(Fremdkapital\) "
    r"von CHF\s+(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*"
    r"in\s+(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>.+?)\.?,?\s*$",
    re.I | re.DOTALL | re.UNICODE,
)
_DE_COMPACT_PERSON_CHANGED_TWO_ROLES = re.compile(
    r"Eingetragene Person geändert:\s*(?P<name>[^,.;]+),\s*"
    r"(?P<role1>[^,.;]+),\s*(?P<role2>[^,.;]+),\s*"
    r"(?P<sign>Einzelunterschrift|Kollektivunterschrift(?:\s+zu\s+zweien)?),\s*"
    r"(?:nun|neu) in\s+(?P<place>[^.]+)\.?,?",
    re.I | re.UNICODE,
)
_FR_SHARE_SPLIT_WITHOUT_INITIAL_KIND = re.compile(
    r"Division des\s+(?P<from_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<from_nominal>[\d'.]+)\s+en\s+(?P<to_count>[\d']+)\s+actions "
    r"de CHF\s+(?P<to_nominal>[\d'.]+)\.\s*Capital-actions:\s*CHF\s+"
    r"(?P<total>[\d'.]+),\s*libéré à concurrence de CHF\s+(?P<paid>[\d'.]+),\s*"
    r"divisé en\s+(?P<capital_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<capital_nominal>[\d'.]+),\s*(?P<kind>nominatives)\.?,?",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_ASSET_TRANSFER_AUTHENTIC_AMENDMENT = re.compile(
    r"Transfert de patrimoine:\s*selon contrat et avenant authentiques des\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+et\s+"
    r"(?P<amendment_date>\d{2}\.\d{2}\.\d{4}),\s*inventaire au\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+et selon décision de "
    r"l['’]autorité de surveillance du\s+(?P<approval_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"la fondation a transféré des actifs de CHF\s+(?P<assets>[\d'.]+)\s+et "
    r"des passifs envers les tiers de CHF\s+(?P<liabilities>[\d'.]+)\s+à\s+"
    r"(?P<recipient>.+?)\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<place>[^.]+)\.\s*Contre-prestation:\s*(?P<consideration>.+?)\.?,?\s*$",
    re.I | re.DOTALL | re.UNICODE,
)
_FR_AUDITOR_RENAMED_PLAIN = re.compile(
    r"(?P<old_name>[A-ZÀ-Ÿ][^()]+?)\s+"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+a modifié sa raison de "
    r"commerce en\s+(?P<name>.+?)\.?,?\s*$",
    re.I | re.UNICODE,
)
_IT_AUTHORIZED_CAPITAL_INTRODUCED = re.compile(
    r"L['’]assemblea generale ha introdotto una disposizione statutaria relativa "
    r"all['’]aumento autorizzato del capitale azionario mediante decisione del\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.\s*Per i dettagli vedi statuti\.?,?",
    re.I | re.UNICODE,
)
_FR_NEW_SOLE_MANAGER = re.compile(
    r"Nouvelle gérante unique:\s*(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+)\.?,?",
    re.I | re.UNICODE,
)
_FR_CREDITORS_SATISFIED_DELETION = re.compile(
    r"Les créanciers ayant été désintéressés ou ayant obtenu des sûretés,\s*"
    r"la raison de commerce est radiée\.?,?",
    re.I | re.UNICODE,
)
_DE_REMOVED_COMPOSITION_MORATORIUM = re.compile(
    r"\[gestrichen:\s*Mit Entscheid des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+wurde eine definitive Nachlassstundung "
    r"für die Dauer von\s+(?P<duration>\d+)\s+Monaten bis zum\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\s+gewährt\.\]\.?,?",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_RESTRICTIONS_REMOVED = re.compile(
    r"Les restrictions quant à la transmissibilité des\s+"
    r"(?P<count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+sont supprimées\s*"
    r"\(art\.\s*685a,\s*al\.\s*3\s*CO\)\.?,?",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{year}-{month}-{day}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _signing(raw: str) -> str:
    return (
        "Einzelunterschrift"
        if "individ" in raw.lower() or raw.lower() == "einzelunterschrift"
        else "Kollektivunterschrift zu zweien"
    )


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


def extract_parser59_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 59."""
    events: list[Event] = []
    leftover = text

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_BANKRUPTCY_APPEAL_REJECTED_NUMERIC.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "fr.text.bankruptcy_appeal_rejected.v2",
                {
                    "kind": "bankruptcy_confirmed",
                    "appeal_outcome": "rejected",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "judgment_date": _iso_date(match.group("judgment_date")),
                    "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                    "bankruptcy_time": match.group("time"),
                    "authority": match.group("authority").strip(),
                    "company_name": match.group("name").strip(),
                    "in_liquidation": True,
                },
            )
        )

    match = _FR_LIQUIDATORS_THREE.search(leftover)
    if match:
        consume(match)
        signing = _signing(match.group("sign"))
        for index in (1, 2, 3):
            name = match.group(f"name{index}")
            for event_type, rule_id in (
                ("officer_changed", "fr.persons.liquidators_three.v1"),
                ("signing_authority_changed", "fr.persons.liquidators_three_signing.v1"),
            ):
                events.append(
                    _person_event(
                        publication_id, published_at, org_uid, plz, canton,
                        event_type, rule_id, name,
                        role="administrateur et liquidateur", signing=signing,
                        extra={"continues_signing": True},
                    )
                )

    match = _FR_APPOINTED_ADMIN_PROCURATION_REVOKED.search(leftover)
    if match:
        consume(match)
        signing = _signing(match.group("sign"))
        common = {"action": "appointed", "previous_signing": "procuration", "procuration_revoked": True}
        for event_type, rule_id in (
            ("officer_changed", "fr.persons.administrator_appointed.v1"),
            ("signing_authority_changed", "fr.persons.administrator_appointed_signing.v1"),
        ):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    event_type, rule_id, match.group("name"),
                    role=match.group("role"), signing=signing, extra=common,
                )
            )

    match = _FR_SOLE_PROPRIETOR_OFFICIAL_DELETION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_deleted", "fr.text.sole_proprietor_official_deletion.v1",
                {
                    "reason": "business_operations_ceased",
                    "deletion_mode": "ex_officio",
                    "legal_basis": re.sub(r"\s+", " ", match.group("article")),
                },
            )
        )

    match = _DE_EMPTY_FUNDS_HEADING.search(leftover)
    if match:
        consume(match)

    match = _DE_SOLE_PROPRIETOR_ASSET_TRANSFER.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.sole_proprietor_asset_transfer.v1",
                {
                    "source_kind": "sole_proprietor",
                    "date": _iso_date(match.group("date")),
                    "inventory_date": _iso_date(match.group("inventory_date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration": match.group("consideration").strip(),
                },
            )
        )

    match = _DE_COMPACT_PERSON_CHANGED_TWO_ROLES.search(leftover)
    if match:
        consume(match)
        signing = _signing(match.group("sign"))
        role = f"{match.group('role1').strip()}, {match.group('role2').strip()}"
        for event_type, rule_id in (
            ("officer_changed", "de.persons.compact_changed.v2"),
            ("signing_authority_changed", "de.persons.compact_changed_signing.v2"),
        ):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    event_type, rule_id, match.group("name"),
                    place=match.group("place"), role=role, signing=signing,
                    extra={"action": "domicile_changed"},
                )
            )

    match = _FR_SHARE_SPLIT_WITHOUT_INITIAL_KIND.search(leftover)
    if match:
        consume(match)
        total = match.group("total")
        paid = match.group("paid")
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.share_split.v2",
                {
                    "kind": "share_split",
                    "split_from": {
                        "count": _count(match.group("from_count")),
                        "nominal": match.group("from_nominal"),
                    },
                    "split_to": {
                        "count": _count(match.group("to_count")),
                        "nominal": match.group("to_nominal"),
                    },
                    "capital_total": total,
                    "paid": paid,
                    "paid_in_full": paid == total,
                    "capital_count": _count(match.group("capital_count")),
                    "capital_nominal": match.group("capital_nominal"),
                    "share_kind": match.group("kind"),
                },
            )
        )

    match = _FR_FOUNDATION_ASSET_TRANSFER_AUTHENTIC_AMENDMENT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "fr.text.foundation_asset_transfer.v2",
                {
                    "date": _iso_date(match.group("date")),
                    "amendment_date": _iso_date(match.group("amendment_date")),
                    "inventory_date": _iso_date(match.group("inventory_date")),
                    "supervisory_approval_date": _iso_date(match.group("approval_date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration": match.group("consideration").strip(),
                },
            )
        )

    match = _FR_AUDITOR_RENAMED_PLAIN.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.auditor_renamed.v11",
                match.group("name"), uid=match.group("uid"), role="organe de révision",
                extra={"action": "name_changed", "previous": match.group("old_name").strip()},
            )
        )

    match = _IT_AUTHORIZED_CAPITAL_INTRODUCED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "it.text.authorized_capital_clause_introduced.v1",
                {
                    "kind": "authorized_capital_clause",
                    "action": "introduced",
                    "decision_date": _iso_date(match.group("date")),
                    "details_in_statutes": True,
                },
            )
        )

    match = _FR_NEW_SOLE_MANAGER.search(leftover)
    if match:
        consume(match)
        for event_type, rule_id in (
            ("officer_changed", "fr.persons.sole_manager.v1"),
            ("signing_authority_changed", "fr.persons.sole_manager_signing.v1"),
        ):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    event_type, rule_id, match.group("name"),
                    place=match.group("place"), role="gérante unique",
                    signing="Einzelunterschrift",
                    extra={"heimat": match.group("origin").strip(), "action": "appointed"},
                )
            )

    match = _FR_CREDITORS_SATISFIED_DELETION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_deleted", "fr.text.creditors_satisfied_deletion.v1",
                {
                    "reason": "creditors_satisfied_or_secured",
                    "creditors_satisfied_or_secured": True,
                },
            )
        )

    match = _DE_REMOVED_COMPOSITION_MORATORIUM.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.composition_moratorium_removed.v2",
                {
                    "kind": "composition_moratorium_granted",
                    "action": "removed",
                    "moratorium_type": "definitive",
                    "decision_date": _iso_date(match.group("date")),
                    "duration_months": int(match.group("duration")),
                    "until": _iso_date(match.group("until")),
                    "authority": match.group("authority").strip(),
                },
            )
        )

    match = _FR_SHARE_TRANSFER_RESTRICTIONS_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "fr.text.share_transfer_restriction_removed.v5",
                {
                    "kind": "share_transfer_restriction",
                    "action": "removed",
                    "shares_count": _count(match.group("count")),
                    "nominal": match.group("nominal"),
                    "legal_basis": "art. 685a al. 3 CO",
                },
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
