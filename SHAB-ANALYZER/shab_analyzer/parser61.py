from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_PERSON_ROLE_AND_SIGNING_CHANGED = re.compile(
    r"Eingetragene Person geändert:\s*(?P<name>[^,.;]+),\s*"
    r"(?P<previous_role>[^,.;]+),\s*"
    r"(?P<previous_sign>Einzelunterschrift|Kollektivunterschrift(?:\s+zu\s+zweien)?),\s*"
    r"neu\s+(?P<role>.+?),\s*"
    r"(?P<sign>Einzelunterschrift|Kollektivunterschrift(?:\s+zu\s+zweien)?)\.?$",
    re.I | re.UNICODE,
)
_DE_EXTRAORDINARY_BANKRUPTCY_ADMINISTRATION = re.compile(
    r"Als ausserordentliche Konkursverwaltung wird die\s+(?P<name>.+?)\s*"
    r"\(Mandatsleiter\s+(?P<representatives>[^)]+)\),\s*"
    r"(?P<address>[^.]+),\s*eingesetzt\.\s*"
    r"Das Konkursverfahren wird die ausserordentliche Konkursverwaltung unter Mithilfe "
    r"des\s+(?P<assisting_authority>[^.]+)\s+durchführen\.?$",
    re.I | re.UNICODE,
)
_DE_COOPERATIVE_MINIMUM_SHARE_OBLIGATION = re.compile(
    r"Pflichten neu:\s*(?P<obligations>Jeder Genossenschafter ist verpflichtet,\s*"
    r"mindestens einen Anteilschein zu CHF\s+(?P<nominal>[\d'.]+)\s+zu übernehmen)\.?$",
    re.I | re.UNICODE,
)
_DE_MULTI_RECIPIENT_SPIN_OFF = re.compile(
    r"Abspaltung:\s*Die Gesellschaften\s+(?P<recipient1>.+?),\s*in\s+"
    r"(?P<recipient_place1>[^()]+?)\s*\((?P<recipient_uid1>CHE-\d{3}\.\d{3}\.\d{3})\)\s+"
    r"und\s+(?P<recipient2>.+?),\s*in\s+(?P<recipient_place2>[^()]+?)\s*"
    r"\((?P<recipient_uid2>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"übernehmen von der\s+(?P<source>.+?),\s*in\s+(?P<source_place>[^()]+?)\s*"
    r"\((?P<source_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*je einen Teil des Vermögens\.\s*"
    r"Die Gesellschaft\s+(?P<subject>.+?)\s+übernimmt dabei gemäss Spaltungsvertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+"
    r"und Passiven \(Fremdkapital\) von CHF\s+(?P<liabilities>[\d'.]+)\.\s*"
    r"Da derselbe Aktionär sämtliche Aktien der an der Spaltung beteiligten "
    r"Gesellschaften hält,\s*findet weder eine Kapitalerhöhung noch eine "
    r"Aktienzuteilung statt\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_DISSOLUTION_FEMININE_AUTHORITY = re.compile(
    r"Auflösung der Rechtseinheit durch Konkurs gemäss Konkurserkenntnis der\s+"
    r"(?P<authority>.+?)\s+vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"mit Wirkung ab dem\s+(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<time>\d{1,2}[.:]\d{2})\s+Uhr\.?$",
    re.I | re.UNICODE,
)
_DE_DISSOLUTION_CORRECTION_DOMICILE_LOSS = re.compile(
    r"\[Die Bemerkung zur Auflösung ist nicht zutreffend,\s*"
    r"es besteht ledliglich ein Domizilverlust\]",
    re.I | re.UNICODE,
)

_FR_SHARE_TRANSFORMATION = re.compile(
    r"Les\s+(?P<from_count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<from_nominal>[\d'.]+)\s+sont transformées en\s+"
    r"(?P<to_count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<to_nominal>[\d'.]+),?\s*$",
    re.I | re.UNICODE,
)
_FR_NEW_MANAGER_SECRETARY = re.compile(
    r"Nouveau gérant:\s*(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*(?P<role>secrétaire),?\s*$",
    re.I | re.UNICODE,
)
_FR_ADDRESSES_REMOVED_DIRECT = re.compile(
    r"Adresses radiées:\s*(?P<address>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_HEAD_OFFICE_NAME_FEMININE_TYPO = re.compile(
    r"Nouvelle raison sociale du siège principale:\s*(?P<name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_FR_ADDRESS_SPECIFIED = re.compile(
    r"Adresse précisée:\s*(?P<address>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_FIRST_NAME_CHANGED_DIRECT = re.compile(
    r"(?P<previous>[A-ZÀ-Ÿ][^.;]+?)\s+se prénomme\s+"
    r"(?P<name>[A-ZÀ-Ÿ][^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_LEGAL_BEARER_CONVERSION_ADAPTED_SEMICOLON = re.compile(
    r"Le\s+(?P<conversion_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"les actions au porteur ont été converties de par la loi en actions nominatives;\s*"
    r"par décision de l['’]assemblée générale du\s+"
    r"(?P<adaptation_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"les statuts de la société ont été adaptés à la conversion\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_DOMICILE_CHANGED = re.compile(
    r"Personne modifiée:\s*(?P<name>[^,.;]+),\s*(?P<role>[^,.;]+),\s*"
    r"(?P<sign>signature individuelle|signature collective(?:\s+à\s+deux)?),\s*"
    r"maintenant à\s+(?P<place>[^.;]+)\.?$",
    re.I | re.UNICODE,
)

_IT_HEAD_OFFICE_IDENTIFIER = re.compile(
    r",?\s*Sede principale a:\s*(?P<seat>[^.]+)\.\s*"
    r"Nuovo numero di identificazione della sede principale:\s*"
    r"(?P<to>CHE-\d{3}\.\d{3}\.\d{3})\s*"
    r"\[finora:\s*Numero dell['’]identificazione della sede principale:\s*"
    r"(?P<from>[^\]]+)\]\.?$",
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
        if "individ" in raw.lower() or "einzel" in raw.lower()
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


def extract_parser61_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 61."""
    events: list[Event] = []
    leftover = text

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    if language == "de":
        match = _DE_PERSON_ROLE_AND_SIGNING_CHANGED.search(leftover)
        if match:
            consume(match)
            signing = _signing(match.group("sign"))
            previous_signing = _signing(match.group("previous_sign"))
            common = {
                "action": "role_and_signing_changed",
                "previous_role": match.group("previous_role").strip(),
                "previous_signing": previous_signing,
            }
            for event_type, rule_id in (
                ("officer_changed", "de.persons.role_and_signing_changed.v1"),
                (
                    "signing_authority_changed",
                    "de.persons.role_and_signing_changed_signing.v1",
                ),
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
                        match.group("name"),
                        role=match.group("role").strip(),
                        signing=signing,
                        extra=common,
                    )
                )

        match = _DE_EXTRAORDINARY_BANKRUPTCY_ADMINISTRATION.search(leftover)
        if match:
            consume(match)
            representatives = [
                value.strip()
                for value in re.split(r"\s+und/oder\s+", match.group("representatives"))
            ]
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "organization_changed",
                    "de.text.extraordinary_bankruptcy_administration.v1",
                    {
                        "kind": "bankruptcy_administration",
                        "action": "appointed",
                        "administration_type": "extraordinary",
                        "name": match.group("name").strip(),
                        "representatives": representatives,
                        "address": match.group("address").strip(),
                        "assisting_authority": match.group("assisting_authority").strip(),
                    },
                )
            )

        match = _DE_COOPERATIVE_MINIMUM_SHARE_OBLIGATION.search(leftover)
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
                    "de.text.cooperative_minimum_share_obligation.v1",
                    {
                        "kind": "member_obligations",
                        "action": "changed",
                        "obligations": match.group("obligations").strip(),
                        "minimum_share_certificates": 1,
                        "currency": "CHF",
                        "nominal": match.group("nominal"),
                    },
                )
            )

        match = _DE_MULTI_RECIPIENT_SPIN_OFF.search(leftover)
        if match:
            consume(match)
            recipients = [
                {
                    "name": match.group(f"recipient{index}").strip(),
                    "place": match.group(f"recipient_place{index}").strip(),
                    "uid": match.group(f"recipient_uid{index}"),
                }
                for index in (1, 2)
            ]
            subject = match.group("subject").strip()
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "assets_transferred",
                    "de.text.multi_recipient_spin_off_acquisition.v1",
                    {
                        "kind": "spin_off_acquisition",
                        "date": _iso_date(match.group("date")),
                        "source": match.group("source").strip(),
                        "source_place": match.group("source_place").strip(),
                        "source_uid": match.group("source_uid"),
                        "recipients": recipients,
                        "subject_recipient": subject,
                        "assets": match.group("assets"),
                        "liabilities": match.group("liabilities"),
                        "capital_increase": False,
                        "share_allocation": False,
                    },
                )
            )

        match = _DE_BANKRUPTCY_DISSOLUTION_FEMININE_AUTHORITY.search(leftover)
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
                    "de.text.bankruptcy_dissolution.v2",
                    {
                        "kind": "bankruptcy_opened",
                        "decision_date": _iso_date(match.group("decision_date")),
                        "effective_date": _iso_date(match.group("effective_date")),
                        "effective_time": match.group("time").replace(".", ":"),
                        "authority": match.group("authority").strip(),
                        "entity_dissolved": True,
                    },
                )
            )

        match = _DE_DISSOLUTION_CORRECTION_DOMICILE_LOSS.search(leftover)
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
                    "de.text.dissolution_correction_domicile_loss.v1",
                    {
                        "kind": "dissolution_correction",
                        "correction": True,
                        "dissolved": False,
                        "reason": "domicile_loss_only",
                    },
                )
            )

    if language == "fr":
        match = _FR_SHARE_TRANSFORMATION.search(leftover)
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
                    "fr.text.registered_share_transformation.v1",
                    {
                        "kind": "share_split",
                        "share_kind": "actions nominatives",
                        "split_from": {
                            "count": _count(match.group("from_count")),
                            "nominal": match.group("from_nominal"),
                        },
                        "split_to": {
                            "count": _count(match.group("to_count")),
                            "nominal": match.group("to_nominal"),
                        },
                    },
                )
            )

        match = _FR_NEW_MANAGER_SECRETARY.search(leftover)
        if match:
            consume(match)
            events.append(
                _person_event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.manager_secretary.v1",
                    match.group("name"),
                    place=match.group("place"),
                    role=f"gérant, {match.group('role').strip()}",
                    extra={
                        "action": "appointed",
                        "heimat": match.group("origin").strip(),
                    },
                )
            )

        match = _FR_ADDRESSES_REMOVED_DIRECT.search(leftover)
        if match:
            consume(match)
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "address_changed",
                    "fr.text.addresses_removed_direct.v1",
                    {
                        "action": "removed",
                        "address": match.group("address").strip(),
                    },
                )
            )

        match = _FR_HEAD_OFFICE_NAME_FEMININE_TYPO.search(leftover)
        if match:
            consume(match)
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "company_name_changed",
                    "fr.text.head_office_name_feminine_typo.v1",
                    {
                        "scope": "head_office",
                        "to": match.group("name").strip(),
                        "head_office_uid": match.group("uid"),
                    },
                )
            )

        match = _FR_ADDRESS_SPECIFIED.search(leftover)
        if match:
            consume(match)
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "address_changed",
                    "fr.text.address_specified.v1",
                    {
                        "action": "specified",
                        "to": match.group("address").strip(),
                    },
                )
            )

        match = _FR_FIRST_NAME_CHANGED_DIRECT.search(leftover)
        if match:
            consume(match)
            events.append(
                _person_event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.first_name_changed_direct.v1",
                    match.group("name"),
                    extra={
                        "action": "first_name_changed",
                        "previous": match.group("previous").strip(),
                    },
                )
            )

        match = _FR_LEGAL_BEARER_CONVERSION_ADAPTED_SEMICOLON.search(leftover)
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
                    "fr.text.legal_bearer_conversion_adapted.v4",
                    {
                        "kind": "bearer_to_registered_conversion",
                        "legal_basis": "by_operation_of_law",
                        "conversion_date": _iso_date(match.group("conversion_date")),
                        "adaptation_date": _iso_date(match.group("adaptation_date")),
                        "from_kind": "au porteur",
                        "to_kind": "nominatives",
                        "statutes_adapted": True,
                    },
                )
            )

        match = _FR_PERSON_DOMICILE_CHANGED.search(leftover)
        if match:
            consume(match)
            events.append(
                _person_event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.domicile_changed.v1",
                    match.group("name"),
                    place=match.group("place"),
                    role=match.group("role").strip(),
                    signing=_signing(match.group("sign")),
                    extra={"action": "domicile_changed"},
                )
            )

    if language == "it":
        match = _IT_HEAD_OFFICE_IDENTIFIER.search(leftover)
        if match:
            consume(match)
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "company_identifier_changed",
                    "it.text.head_office_identifier.v2",
                    {
                        "scope": "head_office",
                        "head_office_seat": match.group("seat").strip(),
                        "from": match.group("from").strip(),
                        "to": match.group("to"),
                    },
                )
            )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
