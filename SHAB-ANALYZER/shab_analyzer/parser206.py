from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_TWO_MANAGER_SHARE_TRANSFERS = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller1>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred1>[\d']+)\s+parts de CHF\s+(?P<nominal1>[\d'.]+)\s+à\s+"
    r"(?P<buyer1>[^,.;]+),\s*de\s+(?P<origin1>[^,;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*nouvel associé-gérant pour\s+"
    r"(?P<count1>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal1>[\d'.]+),\s*"
    r"avec signature individuelle\.\s*"
    r"L['’]associé-gérant\s+(?P<seller2>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred2>[\d']+)\s+parts de CHF\s+(?P<nominal2>[\d'.]+)\s+à\s+"
    r"(?P<buyer2>[^,.;]+),\s*de\s+(?P<origin2>[^,;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*nouvel associé-gérant pour\s+"
    r"(?P<count2>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal2>[\d'.]+),\s*"
    r"avec signature individuelle\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ORIGINS_AND_TWO_SIGNINGS = re.compile(
    r"^(?P<origin_name1>[^,.;]+?)\s+et\s+(?P<origin_name2>[^,.;]+?)\s+"
    r"sont maintenant originaires de\s+(?P<origin>[^.]+)\.\s*"
    r"Signature collective à deux a été conférée à\s+"
    r"(?P<sign_name1>[^,.;]+),\s*ainsi qu['’]à\s+(?P<sign_name2>[^,.;]+),\s*"
    r"tous deux de\s+(?P<sign_origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_START_DATE_CORRECTED = re.compile(
    r"^L['’]inscription\s+N°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que la "
    r"société à commencé le\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s*"
    r"\(et non pas le\s+(?P<previous_date>\d{2}\.\d{2}\.\d{4})\)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_NEW_FOUNDATION_MEMBERS = re.compile(
    r"^Nouveaux membres du conseil de fondation avec signature collective à deux\s*:\s*"
    r"(?P<name1>[^,.;]+),\s*de et à\s+(?P<place1>[^,.;]+),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_REMOVED_AND_APPOINTED = re.compile(
    r"^(?P<removed>[^,.;]+)\s+n['’]est plus administratrice;\s*sa signature "
    r"est radiée\.\s*Nouvel administrateur avec signature individuelle\s*:\s*"
    r"(?P<name>[^,.;]+),\s*"
    r"de\s+(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_REGISTERED_PERSON_RENAMED_WITH_SIGNING = re.compile(
    r"^Eingetragene Person geändert:\s*(?P<previous_name>[^,.;]+),\s*"
    r"(?P<signing>Kollektivprokura zu zweien),\s*nun\s+"
    r"(?P<name>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_DECISION_REPLACED = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+eine weitere genehmigte "
    r"Kapitalerhöhung gemäss näherer Umschreibung in den Statuten beschlossen\.\s*"
    r"\[bisher:\s*Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+eine weitere genehmigte "
    r"Kapitalerhöhung gemäss näherer Umschreibung in den Statuten beschlossen\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ADMINISTRATORS_WITHOUT_SIGNATURE = re.compile(
    r"^Nouveaux administrateurs sans signature:\s*"
    r"(?P<name1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*et\s+(?P<name2>[^,.;]+),\s*de et à\s+"
    r"(?P<place2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_REGISTERED_PERSON_NAME_CORRECTED_WITH_SHARES = re.compile(
    r"^Eingetragene Person geändert:\s*(?P<previous_name>[^,.;]+),\s*"
    r"(?P<role1>Gesellschafter),\s*(?P<count>[\d']+)\s+Stammanteile zu CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*(?P<role2>Geschäftsführer),\s*"
    r"(?P<signing>Einzelunterschrift),\s*korrekterweise\s+"
    r"(?P<name>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_OWNER_BANKRUPTCY_APPEAL_ENTRY_REMOVED = re.compile(
    r"^Mit Mitteilung des\s+(?P<appeal_court>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+ist dem Rekurs gegen den "
    r"Entscheid des\s+(?P<bankruptcy_court>.+?)\s+vom\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+betreffend "
    r"Konkurseröffnung aufschiebende Wirkung zuerkannt worden\.\s*Demnach wird "
    r"die Eintragung betreffend Konkurseröffnung über die Inhaberin im "
    r"Handelsregister gestrichen\.\s*\[bisher:\s*Mit Entscheid der\s+"
    r"(?P<previous_authority>.+?)\s+vom\s+(?P=bankruptcy_date)\s+ist über die "
    r"Inhaberin mit Wirkung ab dem\s+(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}[.:]\d{2})\s+Uhr,\s*der Konkurs eröffnet "
    r"worden\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_TO_NEW_PRESIDENT = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+),\s*maintenant domicilié à\s+"
    r"(?P<seller_place>[^,.;]+),\s*détient\s+(?P<seller_count>[\d']+)\s+parts "
    r"de CHF\s+(?P<nominal>[\d'.]+),\s*par suite de cession de\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<transfer_nominal>[\d'.]+)\s+"
    r"à\s+(?P<buyer>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<buyer_place>[^,.;]+),\s*nouvelle associée-gérante,\s*nommée "
    r"présidente,\s*pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*avec signature individuelle\.?$",
    re.I | re.UNICODE,
)
_DE_ORIGIN_SUPPLEMENT_AND_SIGNING_CHANGE = re.compile(
    r"^Bei der nachfolgenden Mutation wurde der bisherige zusätzliche Heimatort "
    r"nicht publiziert\.\s*Deshalb erfolgt folgender Nachtrag:\s*"
    r"(?P<name>[^,.;]+,\s*[^,.;]+),\s*von\s+(?P<origin>[^,.;]+),\s*in\s+"
    r"(?P<place>[^,.;]+),\s*(?P<role>Mitglied des Stiftungsrates),\s*mit\s+"
    r"(?P<signing>Kollektivunterschrift zu zweien)\s*\[bisher:\s*und\s+"
    r"(?P<additional_origin>[^,.;]+),\s*(?P<previous_role>Mitglied des "
    r"Stiftungsrates),\s*(?P<previous_signing>ohne Zeichnungsberechtigung)\]\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZATION_DATE_CORRECTED = re.compile(
    r"^Beim Bisher-Text wurde das Datum des Ermächtigungsbeschlusses irrtümlich "
    r"mit\s+(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+aufgeführt\.\s*"
    r"Richtig wäre:\s*(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_CLAUSE_REMOVED_WITH_HISTORY = re.compile(
    r"^\[Streichung der Statutenbestimmung über die mit Ermächtigungsbeschluss "
    r"vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+eingeführte genehmigte "
    r"Kapitalerhöhung\.\]\s*\[gestrichen:\s*Die Gesellschaft hat mit Beschluss "
    r"vom\s+(?P<history_date>\d{2}\.\d{2}\.\d{4})\s+eine genehmigte "
    r"Kapitalerhöhung gemäss näherer Umschreibung in den Statuten beschlossen\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_FOUNDATION_MEMBERS_WITH_PRESIDENT = re.compile(
    r"^Nouveaux membres du conseil de fondation avec signature collective à "
    r"deux avec le président:\s*"
    r"(?P<name1>[^,.;]+),\s*de et à\s+(?P<place1>[^,.;]+),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*de et à\s+(?P<place2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_CLOSED_AND_DELETED = re.compile(
    r"^Das Konkursverfahren wurde mit Verfügung des zuständigen Einzelgerichts "
    r"vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+als geschlossen erklärt\.\s*"
    r"Die Gesellschaft wird von Amtes wegen gelöscht\.?$",
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
        payload={
            "name": clean_name,
            "place": clean_place,
            **(extra or {}),
        },
    )


def extract_parser206_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 206."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_TWO_MANAGER_SHARE_TRANSFERS.fullmatch(leftover)
    if match and all(
        _count(match.group(f"transferred{index}")) == _count(match.group(f"count{index}"))
        and match.group(f"nominal{index}") == match.group(f"buyer_nominal{index}")
        for index in (1, 2)
    ):
        rule_id = "fr.persons.two_manager_share_transfers.v1"
        events: list[Event] = []
        for index in (1, 2):
            seller = match.group(f"seller{index}").strip()
            buyer = match.group(f"buyer{index}").strip()
            common = {
                "currency": "CHF",
                "share_nominal": match.group(f"nominal{index}"),
                "shares_transferred": _count(match.group(f"transferred{index}")),
            }
            events.extend([
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé-gérant",
                    extra={**common, "action": "shares_transferred", "counterparty": buyer},
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer,
                    place=match.group(f"place{index}"), role="associé-gérant",
                    signing="Einzelunterschrift", extra={
                        **common,
                        "action": "appointed_and_shares_received",
                        "counterparty": seller,
                        "origin": match.group(f"origin{index}").strip(),
                        "shares_count": _count(match.group(f"count{index}")),
                    },
                ),
            ])
        return events, ""

    match = _FR_TWO_ORIGINS_AND_TWO_SIGNINGS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_origins_and_two_signings.v1"
        events = [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"origin_name{index}"),
                extra={"action": "origin_changed", "origin": match.group("origin").strip()},
            )
            for index in (1, 2)
        ]
        events.extend(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"sign_name{index}"),
                place=match.group("place"), signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "signing_granted",
                    "origin": match.group("sign_origin").strip(),
                },
            )
            for index in (1, 2)
        )
        return events, ""

    match = _FR_COMPANY_START_DATE_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.company_start_date_corrected.v1", {
                "kind": "company_start_date", "action": "corrected",
                "date": _iso_date(match.group("date")),
                "previous_date": _iso_date(match.group("previous_date")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_TWO_NEW_FOUNDATION_MEMBERS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_new_foundation_members.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="membre du conseil de fondation",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group("place1").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="membre du conseil de fondation",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group("origin2").strip(),
                },
            ),
        ], ""

    match = _FR_ADMINISTRATOR_REMOVED_AND_APPOINTED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administrator_removed_and_appointed.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group("removed"),
                role="administratrice", extra={
                    "action": "removed", "signing_revoked": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), role="administrateur",
                signing="Einzelunterschrift", extra={
                    "action": "appointed", "origin": match.group("origin").strip(),
                },
            ),
        ], ""

    match = _DE_REGISTERED_PERSON_RENAMED_WITH_SIGNING.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.registered_person_renamed_with_signing.v1",
            match.group("name"), signing="Kollektivprokura zu zweien", extra={
                "action": "name_changed",
                "previous_name": match.group("previous_name").strip(),
            },
        )], ""

    match = _DE_AUTHORIZED_CAPITAL_DECISION_REPLACED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_decision_replaced.v1", {
                "kind": "authorized_capital_clause", "action": "decision_replaced",
                "decision_date": _iso_date(match.group("date")),
                "previous_decision_date": _iso_date(match.group("previous_date")),
                "additional_authorized_increase": True,
                "details_in_statutes": True,
            },
        )], ""

    match = _FR_TWO_ADMINISTRATORS_WITHOUT_SIGNATURE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_administrators_without_signature.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="administrateur", extra={
                    "action": "appointed", "origin": match.group("origin1").strip(),
                    "without_signature": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="administrateur", extra={
                    "action": "appointed", "origin": match.group("place2").strip(),
                    "without_signature": True,
                },
            ),
        ], ""

    match = _DE_REGISTERED_PERSON_NAME_CORRECTED_WITH_SHARES.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.registered_person_name_corrected_shares.v1",
            match.group("name"), role="Gesellschafter, Geschäftsführer",
            signing="Einzelunterschrift", extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "shares_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"),
                "currency": "CHF",
            },
        )], ""

    match = _DE_OWNER_BANKRUPTCY_APPEAL_ENTRY_REMOVED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.owner_bankruptcy_appeal_entry_removed.v2", {
                "kind": "bankruptcy_effect_suspended", "scope": "owner",
                "action": "registry_entry_removed",
                "decision_date": _iso_date(match.group("decision_date")),
                "appeal_court": match.group("appeal_court").strip(),
                "bankruptcy_court": match.group("bankruptcy_court").strip(),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "bankruptcy_effective_date": _iso_date(match.group("effective_date")),
                "bankruptcy_effective_time": match.group("effective_time").replace(".", ":"),
                "bankruptcy_entry_removed": True,
            },
        )], ""

    match = _FR_MANAGER_TRANSFER_TO_NEW_PRESIDENT.fullmatch(leftover)
    if match and (
        match.group("nominal") == match.group("transfer_nominal")
        == match.group("buyer_nominal")
        and _count(match.group("transferred")) == _count(match.group("buyer_count"))
    ):
        rule_id = "fr.persons.manager_transfer_to_new_president.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        remaining = _count(match.group("seller_count"))
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller,
                place=match.group("seller_place"), role="associé-gérant",
                signing="Einzelunterschrift", extra={
                    **common, "action": "moved_and_shares_transferred",
                    "counterparty": buyer, "shares_before": remaining + transferred,
                    "shares_transferred": transferred, "shares_count": remaining,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer,
                place=match.group("buyer_place"),
                role="associée-gérante, présidente", signing="Einzelunterschrift",
                extra={
                    **common, "action": "appointed_president_and_shares_received",
                    "counterparty": seller, "origin": match.group("origin").strip(),
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                },
            ),
        ], ""

    match = _DE_ORIGIN_SUPPLEMENT_AND_SIGNING_CHANGE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.origin_supplement_and_signing_change.v1",
            match.group("name"), place=match.group("place"),
            role="Mitglied des Stiftungsrates",
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "origin_supplemented_and_signing_changed",
                "origin": match.group("origin").strip(),
                "additional_origin": match.group("additional_origin").strip(),
                "previous_signing": "ohne Zeichnungsberechtigung",
            },
        )], ""

    match = _DE_AUTHORIZATION_DATE_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.authorization_date_corrected.v1", {
                "kind": "authorized_capital_resolution_date", "action": "corrected",
                "date": _iso_date(match.group("date")),
                "previous_date": _iso_date(match.group("previous_date")),
            },
        )], ""

    match = _DE_AUTHORIZED_CAPITAL_CLAUSE_REMOVED_WITH_HISTORY.fullmatch(leftover)
    if match and match.group("date") == match.group("history_date"):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_clause_removed_history_short.v1", {
                "kind": "authorized_capital_clause", "action": "removed",
                "authorization_date": _iso_date(match.group("date")),
                "previous_entry_removed": True,
                "details_in_statutes": True,
            },
        )], ""

    match = _FR_TWO_FOUNDATION_MEMBERS_WITH_PRESIDENT.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_foundation_members_with_president.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role="membre du conseil de fondation",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed",
                    "origin": match.group(f"place{index}").strip(),
                    "co_signs_with": "président",
                },
            )
            for index in (1, 2)
        ], ""

    match = _DE_BANKRUPTCY_CLOSED_AND_DELETED.fullmatch(leftover)
    if match:
        rule_id = "de.text.bankruptcy_closed_and_deleted_ex_officio.v1"
        date = _iso_date(match.group("date"))
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "bankruptcy_closed", "date": date,
                    "authority": "zuständiges Einzelgericht",
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_deleted", rule_id, {
                    "action": "deleted_ex_officio", "reason": "bankruptcy_closed",
                    "date": date,
                },
            ),
        ], ""

    return [], leftover
