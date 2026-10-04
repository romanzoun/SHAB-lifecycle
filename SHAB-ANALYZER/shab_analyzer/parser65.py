from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_IT_STATUTES_DATE_CORRECTED = re.compile(
    r"^Data corretta degli statuti:\s*(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGERS_PAIR = re.compile(
    r"^(?P<header>Gérants|Gérance):\s*(?P<president>[^,.;]+),\s*"
    r"nommé(?:e)? président,?\s*et\s*(?P<manager>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s*"
    r"(?P<place>[^,.;]+),\s*lesquels signent\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PAIR_WITH_MOVE = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*maintenant domicilié(?:e)? à\s*"
    r"(?P<president_place>[^,.;]+),\s*(?P<president_country>[A-Z]{2,3}),\s*"
    r"nommé(?:e)?\s+(?P<president_role>président(?:e)?)\s+et\s+"
    r"(?P<secretary>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s*(?P<secretary_place>[^,.;]+),\s*"
    r"(?P<secretary_role>secrétaire),\s*lesquels signent\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_WITH_REMAINDER = re.compile(
    r"^L['’]associé(?:e)?\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s*"
    r"(?P<place>[^,.;]+),\s*nouvel(?:le)? associé(?:e)?\s+avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_CONTINUATIONS = re.compile(
    r"^à\s+(?P<place1>[^(),.;]+)\s*\((?P<uid1>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"et\s+à\s+(?P<place2>[^(),.;]+)\s*\((?P<uid2>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_DE_PREVIOUS_BRANCH_REGISTER = re.compile(
    r"^\[bisher:\s*(?P<place>[^()\]]+?)\s*\(HR\s+(?P<register_canton>[A-Z]{2})\)\]\.?$",
    re.I | re.UNICODE,
)
_DE_NON_PUBLIC_FACTS_NOTE = re.compile(
    r"^\[ohne Änderung publikationspflichtiger Tatsachen\]\.?$",
    re.I | re.UNICODE,
)
_DE_SIGNING_CORRECTION = re.compile(
    r"^Infolge Systemfehler wurde beim bisher Text die Zeichnungsberechtigung falsch "
    r"aufgeführt\.\s*Korrekt wäre:\s*\[bisher:\s*(?P<correct>[^\]]+)\]\s*"
    r"und nicht\s*\[bisher:\s*(?P<incorrect>[^\]]+)\]\.?$",
    re.I | re.UNICODE,
)
_DE_MORATORIUM_EXTENDED_LAST_TIME = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+die definitive Nachlassstundung letztmalig bis\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\s+verlängert\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_CLOSURE_REVOKED = re.compile(
    r"^Mit Verfügung vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+die Verfügung vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+über den Konkursschluss "
    r"widerrufen\.\s*Infolgedessen besteht die Gesellschaft entsprechend den früheren "
    r"Eintragungen weiter\.\s*\[gestrichen:\s*Das Konkursverfahren wurde mit Verfügung "
    r"des zuständigen Einzelgerichts vom\s+(?P<closing_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"als geschlossen erklärt\.\s*Die Gesellschaft wird von Amtes wegen gelöscht\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_PROPRIETOR_REINSTATED = re.compile(
    r"^La radiation de l['’]entreprise individuelle étant intervenue par erreur,\s*"
    r"l['’]inscription est rétablie\.?$",
    re.I | re.UNICODE,
)
_DE_ART_934_CANTONAL_TAX_BLOCKED = re.compile(
    r"^Das amtliche Verfahren zur Löschung der Rechtseinheit gemäss\s+"
    r"(?P<legal_basis>Art\.\s*934 OR i\.V\.m\. Art\.\s*153 HRegV)\s+ist gemäss "
    r"rechtskräftiger Verfügung vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+abgeschlossen\.\s*"
    r"Die Rechtseinheit kann mangels Zustimmung der\s+"
    r"(?P<tax_authority>kantonalen Steuerverwaltung)\s+noch nicht gelöscht werden\.?$",
    re.I | re.UNICODE,
)
_DE_ART_934_AOR_SHAB_BLOCKED = re.compile(
    r"^Auf die durch das Handelsregisteramt gestützt auf\s+"
    r"(?P<legal_basis>Art\.\s*934 Abs\.\s*2 aOR sowie Art\.\s*152 Abs\.\s*1 HRegV)\s+"
    r"veranlassten und im SHAB mit Meldungsnummern\s+(?P<issues>.+?)\s+publizierten "
    r"Aufforderungen haben sich keine weiteren Betroffenen gemeldet\.\s*Das amtliche "
    r"Verfahren zur Löschung der Rechtseinheit ist damit abgeschlossen\.\s*Sie kann "
    r"mangels Zustimmung der Eidgenössischen Steuerverwaltung jedoch noch nicht gelöscht werden\.?$",
    re.I | re.UNICODE,
)
_FR_LEGAL_BEARER_CONVERSION_AND_LIQUIDATOR = re.compile(
    r"^Le\s+(?P<day>\d{1,2})(?:er)?\s+"
    r"(?P<month>janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+"
    r"(?P<year>\d{4}),\s*les actions au porteur ont été converties de par la loi en "
    r"actions nominatives\.\s*Par décision de l['’]assemblée générale du\s+"
    r"(?P<adaptation_date>\d{2}\.\d{2}\.\d{4}),\s*les statuts de la société ont été "
    r"adaptés à la conversion\.\s*(?P<name>[^,.;]+),\s*qui est maintenant à\s+"
    r"(?P<place>[^,.;]+),\s*est nommé(?:e)?\s+(?P<role>liquidateur|liquidatrice)\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_SPLIT_AND_CAPITAL_BAND = re.compile(
    r"^Division des\s+(?P<from_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<from_nominal>[\d., ]+),\s*nominatives,\s*en\s+"
    r"(?P<to_count>[\d']+)\s+actions de CHF\s+(?P<to_nominal>[\d., ]+),\s*"
    r"nominatives\.\s*Capital-actions:\s*CHF\s+(?P<total>[\d']+),\s*entièrement "
    r"libéré,\s*divisé en\s+(?P<capital_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<capital_nominal>[\d., ]+),\s*nominatives\.\s*Suppression de la clause "
    r"statutaire relative à une marge de fluctuation du capital fondée sur la décision "
    r"de l['’]assemblée générale du\s+(?P<removed_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"L['’]assemblée générale a introduit une clause statutaire relative à une marge de "
    r"fluctuation du capital-actions par décision du\s+"
    r"(?P<introduced_date>\d{2}\.\d{2}\.\d{4});\s*pour les détails,\s*voir les statuts\.?$",
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
    return f"{year}-{month}-{day}"


def _french_date(day: str, month: str, year: str) -> str:
    return f"{int(year):04d}-{_FR_MONTHS[month.lower()]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _decimal(raw: str) -> str:
    return raw.replace(" ", "").replace(",", ".")


def _signing(raw: str) -> str:
    return (
        "Einzelunterschrift"
        if "individ" in raw.lower()
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


def extract_parser65_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 65."""
    del language  # Historical records can contain a different language in this field.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _IT_STATUTES_DATE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", "it.text.statutes_date_corrected.v1",
                {
                    "kind": "statutes_date",
                    "action": "corrected",
                    "date": _iso_date(match.group("date")),
                },
            )
        )

    match = _FR_MANAGERS_PAIR.search(leftover)
    if match:
        consume(match)
        signing = _signing(match.group("sign"))
        people = (
            (match.group("president"), None, "président", {"action": "role_changed"}),
            (
                match.group("manager"), match.group("place"), "gérant",
                {"action": "appointed", "heimat": match.group("origin").strip()},
            ),
        )
        for name, place, role, extra in people:
            for event_type, rule_id in (
                ("officer_changed", "fr.persons.managers_pair.v1"),
                ("signing_authority_changed", "fr.persons.managers_pair_signing.v1"),
            ):
                events.append(
                    _person_event(
                        publication_id, published_at, org_uid, plz, canton,
                        event_type, rule_id, name, place=place, role=role,
                        signing=signing, extra=extra,
                    )
                )

    match = _FR_ADMINISTRATION_PAIR_WITH_MOVE.search(leftover)
    if match:
        consume(match)
        signing = _signing(match.group("sign"))
        people = (
            (
                match.group("president"), match.group("president_place"),
                match.group("president_role"),
                {
                    "action": "role_and_domicile_changed",
                    "country": match.group("president_country"),
                },
            ),
            (
                match.group("secretary"), match.group("secretary_place"),
                match.group("secretary_role"),
                {"action": "appointed", "heimat": match.group("origin").strip()},
            ),
        )
        for name, place, role, extra in people:
            for event_type, rule_id in (
                ("officer_changed", "fr.persons.administration_pair_move.v1"),
                ("signing_authority_changed", "fr.persons.administration_pair_move_signing.v1"),
            ):
                events.append(
                    _person_event(
                        publication_id, published_at, org_uid, plz, canton,
                        event_type, rule_id, name, place=place, role=role,
                        signing=signing, extra=extra,
                    )
                )

    match = _FR_ASSOCIATE_TRANSFER_WITH_REMAINDER.search(leftover)
    if match:
        consume(match)
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        nominal = match.group("nominal")
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.associate_transfer_remainder.v1",
                    seller, role="associé",
                    extra={
                        "action": "shares_transferred",
                        "counterparty": buyer,
                        "shares_before": _count(match.group("before")),
                        "shares_transferred": transferred,
                        "shares_count": _count(match.group("remaining")),
                        "shares_nominal": match.group("remaining_nominal"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.associate_transfer_remainder.v1",
                    buyer, place=match.group("place"), role="associé",
                    extra={
                        "action": "shares_received",
                        "heimat": match.group("origin").strip(),
                        "counterparty": seller,
                        "shares_received": transferred,
                        "shares_count": _count(match.group("buyer_count")),
                        "shares_nominal": match.group("buyer_nominal"),
                        "transferred_nominal": nominal,
                    },
                ),
            ]
        )

    match = _FR_BRANCH_CONTINUATIONS.search(leftover)
    if match:
        consume(match)
        for index in (1, 2):
            events.append(
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "branch_changed", "fr.text.branch_added_continuation.v1",
                    {
                        "action": "added",
                        "place": match.group(f"place{index}").strip(),
                        "branch_uid": match.group(f"uid{index}"),
                    },
                )
            )

    match = _DE_PREVIOUS_BRANCH_REGISTER.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", "de.text.branch_previous_register.v1",
                {
                    "action": "register_changed",
                    "previous_place": match.group("place").strip(),
                    "previous_register_canton": match.group("register_canton").upper(),
                },
            )
        )

    match = _DE_NON_PUBLIC_FACTS_NOTE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "de.text.non_public_facts_note.v1",
                {"kind": "non_public_facts", "publishable_facts_changed": False},
            )
        )

    match = _DE_SIGNING_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", "de.text.signing_correction_system_error.v1",
                {
                    "kind": "signing_authority",
                    "reason": "system_error",
                    "correct": match.group("correct").strip(),
                    "incorrect": match.group("incorrect").strip(),
                },
            )
        )

    match = _DE_MORATORIUM_EXTENDED_LAST_TIME.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.composition_moratorium_extended_last_time.v1",
                {
                    "kind": "composition_moratorium_extended",
                    "moratorium_type": "definitive",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "until": _iso_date(match.group("until")),
                    "authority": match.group("authority").strip(),
                    "final_extension": True,
                },
            )
        )

    match = _DE_BANKRUPTCY_CLOSURE_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.bankruptcy_closure_revoked.v1",
                {
                    "kind": "bankruptcy_closure_revoked",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                    "previous_closing_date": _iso_date(match.group("closing_date")),
                    "authority": match.group("authority").strip(),
                    "company_continues": True,
                    "official_deletion_revoked": True,
                },
            )
        )

    match = _FR_SOLE_PROPRIETOR_REINSTATED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "fr.text.sole_proprietor_reinstated.v1",
                {
                    "kind": "registration_reinstated",
                    "entity": "sole_proprietorship",
                    "reason": "erroneous_deletion",
                },
            )
        )

    match = _DE_ART_934_CANTONAL_TAX_BLOCKED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.art_934_deletion_blocked_cantonal.v1",
                {
                    "kind": "deletion_blocked",
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                    "procedure_completed": True,
                    "decision_date": _iso_date(match.group("date")),
                    "tax_authority": match.group("tax_authority"),
                    "tax_authority_consent_missing": True,
                },
            )
        )

    match = _DE_ART_934_AOR_SHAB_BLOCKED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.art_934_aor_deletion_blocked.v1",
                {
                    "kind": "deletion_blocked",
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                    "procedure_completed": True,
                    "issues": [
                        issue.strip()
                        for issue in re.split(r",\s*|\s+und\s+", match.group("issues"))
                    ],
                    "affected_parties_responded": False,
                    "tax_authority": "Eidgenössische Steuerverwaltung",
                    "tax_authority_consent_missing": True,
                },
            )
        )

    match = _FR_LEGAL_BEARER_CONVERSION_AND_LIQUIDATOR.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.legal_bearer_conversion_with_liquidator.v1",
                {
                    "kind": "bearer_to_registered_conversion",
                    "conversion_date": _french_date(
                        match.group("day"), match.group("month"), match.group("year")
                    ),
                    "adaptation_date": _iso_date(match.group("adaptation_date")),
                    "from": "actions au porteur",
                    "to": "actions nominatives",
                    "by_law": True,
                    "statutes_adapted": True,
                },
            )
        )
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.liquidator_after_conversion.v1",
                match.group("name"), place=match.group("place"),
                role=match.group("role"),
                extra={"action": "appointed", "domicile_changed": True},
            )
        )

    match = _FR_SHARE_SPLIT_AND_CAPITAL_BAND.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.share_split_micro_nominal.v1",
                {
                    "kind": "share_split",
                    "split_from": {
                        "count": _count(match.group("from_count")),
                        "nominal": _decimal(match.group("from_nominal")),
                    },
                    "split_to": {
                        "count": _count(match.group("to_count")),
                        "nominal": _decimal(match.group("to_nominal")),
                    },
                    "currency": "CHF",
                    "capital_total": match.group("total"),
                    "paid": match.group("total"),
                    "paid_in_full": True,
                    "capital_count": _count(match.group("capital_count")),
                    "capital_nominal": _decimal(match.group("capital_nominal")),
                    "share_kind": "actions nominatives",
                },
            )
        )
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "fr.text.capital_band_replaced.v1",
                {
                    "kind": "capital_band",
                    "action": "replaced",
                    "removed_decision_date": _iso_date(match.group("removed_date")),
                    "introduced_decision_date": _iso_date(match.group("introduced_date")),
                },
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
