from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_NEW_PERSON_MISSPELLED = re.compile(
    r"Nouvelle personne isncrite:\s*(?P<name>[^,]+),\s*"
    r"de\s+(?P<origin>[^,]+),\s*à\s+(?P<place>[^,]+),\s*"
    r"(?P<sign>procuration collective à deux)\.?",
    re.I | re.UNICODE,
)
_IT_BRANCH_WITHOUT_UID = re.compile(
    r"Nuova succursale:\s*(?P<place>[^().]+?)\s*(?:\.(?:\s|$)|$)",
    re.I | re.UNICODE,
)
_FR_FIRST_POWERS_CHANGED = re.compile(
    r";?\s*les pouvoirs du premier sont modifiés en ce sens\.?,?", re.I
)
_DE_CAPITAL_REDUCTION_AND_INCREASE = re.compile(
    r"Aktienkapital neu:\s*(?P<currency>[A-Z]{3})\s+(?P<total>[\d'.]+)\s*"
    r"\[bisher:\s*[A-Z]{3}\s+(?P<previous_total>[\d'.]+)\]\.\s*"
    r"Liberierung Aktienkapital neu:\s*[A-Z]{3}\s+(?P<paid>[\d'.]+)\s*"
    r"\[bisher:\s*[A-Z]{3}\s+(?P<previous_paid>[\d'.]+)\]\.\s*"
    r"Aktien neu:\s*(?P<count>[\d']+)\s+Namenaktien zu\s+[A-Z]{3}\s+"
    r"(?P<nominal>[\d'.]+)\s*\[bisher:\s*(?P<previous_count>[\d']+)\s+"
    r"Namenaktien zu\s+[A-Z]{3}\s+(?P<previous_nominal>[\d'.]+)\]\.\s*"
    r"Bei der Kapitalherabsetzung vom\s+(?P<reduction_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"werden\s+(?P<destroyed_count>[\d']+)\s+Namenaktien zu\s+[A-Z]{3}\s+"
    r"(?P<destroyed_nominal>[\d'.]+)\s+vernichtet\.\s*"
    r"Gleichzeitig werden bei der Kapitalerhöhung vom\s+"
    r"(?P<increase_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"(?P<issued_count>[\d']+)\s+voll liberierte Namenaktien zu\s+[A-Z]{3}\s+"
    r"(?P<issued_nominal>[\d'.]+)\s+ausgegeben\.?,?",
    re.I,
)
_FR_AUDITOR_IDENTIFIER_REPLACED = re.compile(
    r"Le numéro d'identification\s+(?P<old_id>CH-[\d-]+)\s+de l'organe de révision\s+"
    r'"(?P<name>[^"]+)"\s+à\s+(?P<place>[^.]+?)\s+est remplacé par le numéro '
    r"d'identification des entreprises \(IDE/UID\)\s+"
    r"(?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\.?,?",
    re.I | re.UNICODE,
)
_DE_OWNER_CONTINUES = re.compile(
    r"Der Inhaber führt den Geschäftsbetrieb weiter\.\s*"
    r"Die Eintragung bleibt bestehen\.?,?",
    re.I,
)
_FR_ASSOCIATE_TRANSFER_STEP = re.compile(
    r"(?:[Ll]['’](?P<seller_role>associé(?:e)?(?:-gérant(?:e)?)?(?: et président)?)\s+)?"
    r"(?P<seller>[A-ZÀ-Ÿ][^,.;]+?)(?:,\s*maintenant à\s+(?P<seller_place>[^,.;]+))?\s*,?\s*"
    r"cède\s+(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?:l['’](?P<buyer_role>associé(?:e)?(?:-gérant(?:e)?)?)\s+)?"
    r"(?P<buyer>[^,.;]+),\s*désormais titulaire de\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"(?P=seller) reste titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?,?",
    re.I | re.UNICODE,
)
_FR_TWO_NAMES_AND_ORIGIN_CHANGED = re.compile(
    r"(?P<old1>[A-ZÀ-Ÿ][^,.;]+),\s*qui se nomme désormais\s+(?P<name1>[^,.;]+),\s*"
    r"et\s+(?P<old2>[A-ZÀ-Ÿ][^,.;]+),\s*qui se nomme désormais\s+"
    r"(?P<name2>[^,.;]+),\s*sont maintenant de\s+(?P<origin>[^.]+)\.?,?",
    re.I | re.UNICODE,
)
_FR_THREE_DEPUTY_DIRECTORS = re.compile(
    r"Signature\s+(?P<sign1>collective à deux),\s*"
    r"(?P<restriction>avec un administrateur, un directeur ou un sous-directeur),\s*"
    r"a été conférée à\s+(?P<name1>[^,.;]+),\s*nommée sous-directrice;\s*"
    r"sa procuration est radiée\.\s*"
    r"(?P<name2>[^,.;]+)\s+et\s+(?P<name3>[^,.;]+),\s*nommés sous-directeurs,\s*"
    r"signent désormais\s+(?P<sign23>collectivement à deux),\s*"
    r"sans autre restriction\.?,?",
    re.I | re.UNICODE,
)
_IT_OWNER_BANKRUPTCY_EFFECT_SUSPENDED = re.compile(
    r"Con decisione del\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"(?P<authority>.+?)\s+ha accordato effetto sospensivo al reclamo inoltrato "
    r"contro la decisione di fallimento aperto nei confronti del titolare il\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"\[finora:\s*(?P<previous>Il titolare è stato dichiarato in fallimento.+?)\]\.?",
    re.I | re.DOTALL | re.UNICODE,
)
_IT_NON_PUBLIC_STATUTE_NOTE = re.compile(
    r"\[Statuto modificato su punti non soggetti a pubblicazione\.?\]", re.I
)
_IT_SHARE_TRANSFER_RESTRICTION = re.compile(
    r"Nuova limitazione della trasferibilità:\s*"
    r"\[La trasferibilità delle azioni nominative è limitata dallo statuto\]\.?,?",
    re.I | re.UNICODE,
)
_FR_ORGANIZATION_REMOVED = re.compile(
    r"Nouvelle organisation:\s*\[biffé\]\.?,?", re.I
)
_FR_RESTRICTION_REMOVED_AND_LIQUIDATORS = re.compile(
    r"Radiation de la restriction statutaire de transmissibilité des\s+"
    r"(?P<count>[\d']+)\s+actions de CHF\s+(?P<nominal>[\d'.]+),\s*nominatives\s*"
    r"\(art\.\s*685a,\s*al\.?\s*3\s*CO\)\.\s*"
    r"Liquidateurs:\s*les administrateurs\s+(?P<name1>[^,.;]+),\s*"
    r"maintenant domicilié à\s+(?P<place1>[^,.;]+),\s*(?P<country1>[A-Z]{3}),\s*"
    r"et\s+(?P<name2>[^,.;]+),\s*lesquels continuent à signer\s+"
    r"(?P<sign>individuellement)\.?,?",
    re.I | re.UNICODE,
)
_DE_SOLE_PROPRIETOR_CLOSED = re.compile(
    r"Das Einzelunternehmen ist infolge Geschäftsaufgabe erloschen\.?,?", re.I
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
    payload = {"name": name, "place": place, **(extra or {})}
    return Event(
        publication_id=publication_id,
        published_at=published_at,
        event_type=event_type,
        rule_id=rule_id,
        org_uid=org_uid,
        person_key=person_key(name=name, place=place, uid=uid),
        plz=plz,
        canton=canton,
        role=role,
        signing=signing,
        payload=payload,
    )


def extract_parser51_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 51."""
    events: list[Event] = []
    leftover = text

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_NEW_PERSON_MISSPELLED.search(leftover)
    if match:
        consume(match)
        name = match.group("name").strip()
        place = match.group("place").strip()
        extra = {"heimat": match.group("origin").strip()}
        for event_type, rule_id in (
            ("officer_changed", "fr.persons.new_person_misspelled.v1"),
            ("signing_authority_changed", "fr.persons.new_person_misspelled_signing.v1"),
        ):
            events.append(
                _person_event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    event_type,
                    rule_id,
                    name,
                    place=place,
                    signing="Kollektivprokura zu zweien",
                    extra=extra,
                )
            )

    match = _IT_BRANCH_WITHOUT_UID.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "branch_changed",
                "it.text.branch_added_without_uid.v1",
                {"action": "added", "place": match.group("place").strip()},
            )
        )

    match = _FR_FIRST_POWERS_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.first_powers_changed.v1",
                {"action": "modified", "subject": "first_named_person"},
            )
        )

    match = _DE_CAPITAL_REDUCTION_AND_INCREASE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "de.text.capital_reduction_and_increase.v1",
                {
                    "kind": "capital_reduction_and_increase",
                    "currency": match.group("currency").upper(),
                    "total": match.group("total"),
                    "previous_total": match.group("previous_total"),
                    "paid": match.group("paid"),
                    "previous_paid": match.group("previous_paid"),
                    "shares_count": _count(match.group("count")),
                    "nominal": match.group("nominal"),
                    "previous_shares_count": _count(match.group("previous_count")),
                    "previous_nominal": match.group("previous_nominal"),
                    "reduction_date": _iso_date(match.group("reduction_date")),
                    "destroyed_shares_count": _count(match.group("destroyed_count")),
                    "increase_date": _iso_date(match.group("increase_date")),
                    "issued_shares_count": _count(match.group("issued_count")),
                    "issued_fully_paid": True,
                },
            )
        )

    match = _FR_AUDITOR_IDENTIFIER_REPLACED.search(leftover)
    if match:
        consume(match)
        uid = match.group("uid")
        events.append(
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.auditor_identifier_replaced.v1",
                match.group("name").strip(),
                place=match.group("place").strip(),
                uid=uid,
                role="organe de révision",
                extra={
                    "action": "identifier_replaced",
                    "previous_registry_id": match.group("old_id"),
                    "uid": uid,
                },
            )
        )

    match = _DE_OWNER_CONTINUES.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.sole_proprietor_continues.v1",
                {
                    "kind": "business_continued",
                    "scope": "sole_proprietor",
                    "registration_remains": True,
                },
            )
        )

    transfer_matches = list(_FR_ASSOCIATE_TRANSFER_STEP.finditer(leftover))
    if transfer_matches:
        for match in reversed(transfer_matches):
            consume(match)
        for match in transfer_matches:
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            nominal = match.group("nominal")
            events.append(
                _person_event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.associate_transfer_sequence.v1",
                    seller,
                    place=(match.group("seller_place") or "").strip() or None,
                    role=(match.group("seller_role") or "associé").strip(),
                    extra={
                        "action": "shares_transferred",
                        "counterparty": buyer,
                        "shares_transferred": _count(match.group("transferred")),
                        "previous_shares_count": _count(match.group("before")),
                        "shares_count": _count(match.group("remaining")),
                        "shares_nominal": nominal,
                    },
                )
            )
            events.append(
                _person_event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.associate_transfer_sequence.v1",
                    buyer,
                    role=(match.group("buyer_role") or "associé").strip(),
                    extra={
                        "action": "shares_received",
                        "counterparty": seller,
                        "shares_received": _count(match.group("transferred")),
                        "shares_count": _count(match.group("buyer_count")),
                        "shares_nominal": match.group("buyer_nominal"),
                    },
                )
            )

    match = _FR_TWO_NAMES_AND_ORIGIN_CHANGED.search(leftover)
    if match:
        consume(match)
        origin = match.group("origin").strip()
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.name_and_origin_changed.v1",
                    match.group(f"name{index}").strip(),
                    extra={
                        "action": "name_and_origin_changed",
                        "previous_name": match.group(f"old{index}").strip(),
                        "heimat": origin,
                    },
                )
            )

    match = _FR_THREE_DEPUTY_DIRECTORS.search(leftover)
    if match:
        consume(match)
        people = (
            (
                match.group("name1").strip(),
                "sous-directrice",
                {
                    "previous_signing": "procuration",
                    "procuration_revoked": True,
                    "signing_restriction": match.group("restriction").strip(),
                },
            ),
            (match.group("name2").strip(), "sous-directeur", {"without_other_restriction": True}),
            (match.group("name3").strip(), "sous-directeur", {"without_other_restriction": True}),
        )
        for name, role, extra in people:
            for event_type, rule_id in (
                ("officer_changed", "fr.persons.deputy_directors.v1"),
                ("signing_authority_changed", "fr.persons.deputy_directors_signing.v1"),
            ):
                events.append(
                    _person_event(
                        publication_id,
                        published_at,
                        org_uid,
                        plz,
                        canton,
                        event_type,
                        rule_id,
                        name,
                        role=role,
                        signing="Kollektivunterschrift zu zweien",
                        extra=extra,
                    )
                )

    match = _IT_OWNER_BANKRUPTCY_EFFECT_SUSPENDED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "it.text.owner_bankruptcy_effect_suspended.v1",
                {
                    "kind": "bankruptcy_effect_suspended",
                    "scope": "owner",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                    "authority": match.group("authority").strip(),
                    "previous": match.group("previous").strip(),
                },
            )
        )

    match = _IT_NON_PUBLIC_STATUTE_NOTE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "it.text.non_public_statute_note.v1",
                {"kind": "non_public_changes"},
            )
        )

    match = _IT_SHARE_TRANSFER_RESTRICTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "it.text.share_transfer_restriction.v2",
                {
                    "kind": "share_transfer_restricted",
                    "action": "added",
                    "basis": "statutes",
                    "share_kind": "azioni nominative",
                },
            )
        )

    match = _FR_ORGANIZATION_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "organization_changed",
                "fr.text.organization_removed.v1",
                {"action": "removed", "kind": "organization"},
            )
        )

    match = _FR_RESTRICTION_REMOVED_AND_LIQUIDATORS.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.share_transfer_restriction_removed.v3",
                {
                    "kind": "share_transfer_restriction",
                    "action": "removed",
                    "legal_basis": "art. 685a al. 3 CO",
                    "shares_count": _count(match.group("count")),
                    "nominal": match.group("nominal"),
                },
            )
        )
        for name, place, country in (
            (
                match.group("name1").strip(),
                match.group("place1").strip(),
                match.group("country1").upper(),
            ),
            (match.group("name2").strip(), None, None),
        ):
            for event_type, rule_id in (
                ("officer_changed", "fr.persons.administrators_liquidators.v1"),
                ("signing_authority_changed", "fr.persons.administrators_liquidators_signing.v1"),
            ):
                events.append(
                    _person_event(
                        publication_id,
                        published_at,
                        org_uid,
                        plz,
                        canton,
                        event_type,
                        rule_id,
                        name,
                        place=place,
                        role="liquidateur",
                        signing="Einzelunterschrift",
                        extra={"previous_role": "administrateur", "country": country},
                    )
                )

    match = _DE_SOLE_PROPRIETOR_CLOSED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "company_deleted",
                "de.text.sole_proprietor_closed.v1",
                {"reason": "business_ceased", "scope": "sole_proprietor"},
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
