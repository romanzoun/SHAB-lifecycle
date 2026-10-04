from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_ASSOCIATE_TRANSFER_TO_DIRECTOR = re.compile(
    r"^L['’]associé\s+(?P<seller>[^,.;]+)\s+détient désormais\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+(?P<seller_nominal>[\d'.]+)\s+"
    r"par suite de cession de\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<transfer_nominal>[\d'.]+)\s+au directeur\s+(?P<buyer>[^,.;]+),\s*"
    r"désormais associé pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\s+et qui continue de signer individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGER_ROLE_SUPPLEMENT = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(publication FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+page\s+"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée en ce sens que l['’]associé "
    r"sans signature sociale\s+(?P<name>[^,.;]+)\s+est également gérant\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_SIGNINGS_WITH_ADMINISTRATOR = re.compile(
    r"^Signature collective à deux,\s*toutefois avec un administrateur,\s*"
    r"est conférée à\s+(?P<name1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*à\s+(?P<place2>[^,();]+)\s*"
    r"\((?P<country2>[^)]+)\),\s*toutes deux de\s+(?P<origin>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_PROCURATION_GRANTED = re.compile(
    r"^Procuration collective à deux toutefois limitée à la succursale est "
    r"conférée à\s+(?P<name>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_APPEAL_REJECTED = re.compile(
    r"^Par arrêt de la\s+(?P<authority>Cour des poursuites et faillites du "
    r"Tribunal cantonal)\s+du\s+(?P<date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"le recours est rejeté et le jugement confirmé\.?$",
    re.I | re.UNICODE,
)
_FR_ADDRESS_REMOVED = re.compile(
    r"^Adresse radiée:\s*(?P<address>.+?)\.?$", re.I | re.UNICODE
)
_FR_TWO_ADMINISTRATORS_TYPO_INDIVIDUAL = re.compile(
    r"^Nouveaux administreurs avec signature individuelle\s*:\s*"
    r"(?P<name1>.+?),\s*à\s+(?P<place1>[^,();]+)\s*\((?P<country1>[^)]+)\),\s*"
    r"et\s+(?P<name2>.+?),\s*à\s+(?P<place2>[^,();]+)\s*"
    r"\((?P<country2>[^)]+)\),\s*les deux de\s+(?P<origin>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ADMINISTRATORS_APPOINTED_DIRECTORS = re.compile(
    r"^Les administrateurs\s+(?P<name1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+),\s*"
    r"nommés en outre directeurs,\s*continuent à signer individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_OFFICE_ADDRESS_REMOVED = re.compile(
    r"^\[gestrichen:\s*Geschäftsstelle:\s*(?P<address>[^\]]+?)\.?\]\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_PROCURATIONS_GRANTED = re.compile(
    r"^Procuration collective à deux est conférée à\s+(?P<name1>.+?),\s*"
    r"à\s+(?P<place1>[^,.;]+),\s*et\s+(?P<name2>[^,.;]+),\s*"
    r"à\s+(?P<place2>[^,.;]+),\s*tous deux de\s+(?P<origin>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_NEW_ASSOCIATE_REMAINING = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+détient désormais\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+(?P<seller_nominal>[\d'.]+)\s+"
    r"par suite de cession de\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<transfer_nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de et à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"sans signature sociale\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_AND_THREE_MANAGEMENT_CHANGES = re.compile(
    r"^Ausgeschiedene Personen und erloschene Unterschriften:\s*"
    r"(?P<removed_surname>[^,;]+),\s*(?P<removed_given>[^,;]+),\s*"
    r"(?P<removed_origin>[^,;]+),\s*in\s+(?P<removed_place>[^,;]+),\s*"
    r"(?P<removed_role>Geschäftsführer),\s*mit\s+"
    r"(?P<removed_signing>Kollektivunterschrift zu zweien)\.\s*"
    r"Eingetragene Personen neu oder mutierend:\s*"
    r"(?P<surname1>[^,;]+),\s*(?P<given1>[^,;]+),\s*"
    r"(?P<origin1>[^,;]+),\s*in\s+(?P<place1>[^,;]+),\s*"
    r"(?P<role1>Vize-Vorsitzender der Geschäftsführung),\s*mit\s+"
    r"(?P<signing1>Kollektivunterschrift zu zweien)\s*"
    r"\[bisher:\s*(?P<previous_role1>Vorsitzender der Geschäftsführung),\s*"
    r"mit\s+(?P<previous_signing1>Kollektivunterschrift zu zweien)\];\s*"
    r"(?P<surname2>[^,;]+),\s*(?P<given2>[^,;]+),\s*"
    r"(?P<origin2>[^,;]+),\s*in\s+(?P<place2>[^,;]+),\s*"
    r"(?P<role2>Vorsitzender der Geschäftsführung),\s*mit\s+"
    r"(?P<signing2>Kollektivunterschrift zu zweien)\s*"
    r"\[bisher:\s*(?P<previous_role2>Vize-Vorsitzender der Geschäftsführung),\s*"
    r"mit\s+(?P<previous_signing2>Kollektivunterschrift zu zweien)\];\s*"
    r"(?P<surname3>[^,;]+),\s*(?P<given3>[^,;]+),\s*"
    r"(?P<origin3>[^,;]+),\s*in\s+(?P<place3>[^,;]+),\s*"
    r"(?P<role3>Geschäftsführer),\s*mit\s+"
    r"(?P<signing3>Kollektivunterschrift zu zweien)\.?$",
    re.I | re.UNICODE,
)
_FR_NAME_CORRECTION_REALITY = re.compile(
    r"^L['’]inscription\s+(?:No|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est corrigée en ce sens que\s+"
    r"(?P<previous_name>[^,.;]+)\s+porte en réalité le nom\s+"
    r"(?P<name>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_CLAUSE_EXPIRED = re.compile(
    r"^\[Die Bestimmung über die mit Beschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+eingeführte genehmigte "
    r"Kapitalerhöhung wird infolge Zeitablaufs gestrichen\.\]\s*"
    r"\[bisher:\s*(?P<previous>Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+eine genehmigte "
    r"Kapitalerhöhung gemäss näherer Umschreibung in den Statuten beschlossen\.)\]\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDATION_ORGANIZATION_AND_AUDIT_WAIVER = re.compile(
    r"^Organisation neu:\s*\[gestrichen:\s*Organisation:\s*"
    r"(?P<previous_organization>[^\]]+?)\.\]\.?\s*"
    r"\[Weitere Urkundenänderungen nicht publikationspflichtiger Tatsachen\]\.?\s*"
    r"Die Stiftung wurde mit Verfügung der\s+(?P<authority>Aufsichtsbehörde)\s+vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+von der Pflicht befreit,\s*"
    r"eine Revisionsstelle zu bezeichnen\.?$",
    re.I | re.UNICODE,
)
_FR_PROXY_REPLACED_BY_COLLECTIVE_SIGNING = re.compile(
    r"^(?P<name>[^,.;]+),\s*dont la procuration est éteinte,\s*"
    r"signe maintenant collectivement à deux\.?$",
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
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _fr_written_date(raw: str) -> str:
    day, month, year = raw.split()
    return f"{int(year):04d}-{_FR_MONTHS[month.casefold()]:02d}-{int(day):02d}"


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


def extract_parser200_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 200."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_ASSOCIATE_TRANSFER_TO_DIRECTOR.fullmatch(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        nominals = {
            match.group("seller_nominal"),
            match.group("transfer_nominal"),
            match.group("buyer_nominal"),
        }
        if transferred == buyer_count and len(nominals) == 1:
            rule_id = "fr.persons.associate_transfer_to_director.v1"
            common = {"share_nominal": match.group("buyer_nominal"), "currency": "CHF"}
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("seller"),
                    role="associé", extra={
                        "action": "shares_transferred",
                        "shares_transferred": transferred,
                        "shares_count": _count(match.group("seller_count")),
                        "counterparty": match.group("buyer").strip(), **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("buyer"),
                    role="directeur, associé", signing="Einzelunterschrift", extra={
                        "action": "shares_received_and_appointed_associate",
                        "shares_received": transferred, "shares_count": buyer_count,
                        "previous_role": "directeur", "signing_continues": True,
                        **common,
                    },
                ),
            ], ""

    match = _FR_ASSOCIATE_MANAGER_ROLE_SUPPLEMENT.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_manager_role_supplement.v1",
            match.group("name"), role="associé, gérant", extra={
                "action": "role_added", "previous_role": "associé",
                "role_added": "gérant", "without_signature": True,
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_TWO_SIGNINGS_WITH_ADMINISTRATOR.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_signings_with_administrator.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "signing_granted", "origin": match.group("origin").strip(),
                    "with": "un administrateur",
                    **({"country": match.group("country2").strip()} if index == 2 else {}),
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_BRANCH_PROCURATION_GRANTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.branch_procuration_granted.v1",
            match.group("name"), place=match.group("place"),
            role="fondé de procuration", signing="Kollektivprokura zu zweien", extra={
                "action": "procuration_granted", "origin": match.group("origin").strip(),
                "scope": "branch",
            },
        )], ""

    match = _FR_BANKRUPTCY_APPEAL_REJECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.bankruptcy_appeal_rejected.v1", {
                "kind": "bankruptcy_appeal", "action": "rejected",
                "judgment_confirmed": True,
                "authority": match.group("authority").strip(),
                "decision_date": _fr_written_date(match.group("date")),
            },
        )], ""

    match = _FR_ADDRESS_REMOVED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.address_removed_direct.v1", {
                "kind": "additional_address", "action": "removed",
                "address": match.group("address").strip(),
            },
        )], ""

    match = _FR_TWO_ADMINISTRATORS_TYPO_INDIVIDUAL.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_administrators_typo_individual.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="administrateur",
                signing="Einzelunterschrift", extra={
                    "action": "appointed", "origin": match.group("origin").strip(),
                    "country": match.group(f"country{index}").strip(),
                    "source_wording": "administreurs",
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_TWO_ADMINISTRATORS_APPOINTED_DIRECTORS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_administrators_appointed_directors.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="administrateur, directeur", signing="Einzelunterschrift", extra={
                    "action": "role_added", "previous_role": "administrateur",
                    "role_added": "directeur", "signing_continues": True,
                },
            )
            for index in (1, 2)
        ], ""

    match = _DE_OFFICE_ADDRESS_REMOVED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "de.text.office_address_removed_after_additional.v1", {
                "kind": "office_address", "action": "removed",
                "address": match.group("address").strip().rstrip("."),
            },
        )], ""

    match = _FR_TWO_PROCURATIONS_GRANTED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_procurations_granted.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="fondé de procuration",
                signing="Kollektivprokura zu zweien", extra={
                    "action": "procuration_granted", "origin": match.group("origin").strip(),
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_MANAGER_TRANSFER_NEW_ASSOCIATE_REMAINING.fullmatch(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        nominals = {
            match.group("seller_nominal"),
            match.group("transfer_nominal"),
            match.group("buyer_nominal"),
        }
        if transferred == buyer_count and len(nominals) == 1:
            rule_id = "fr.persons.manager_transfer_new_associate_remaining.v1"
            common = {"share_nominal": match.group("buyer_nominal"), "currency": "CHF"}
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("seller"),
                    role="associé-gérant", extra={
                        "action": "shares_transferred", "shares_transferred": transferred,
                        "shares_count": _count(match.group("seller_count")),
                        "counterparty": match.group("buyer").strip(), **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("buyer"),
                    place=match.group("place"), role="associé", extra={
                        "action": "appointed_and_shares_received",
                        "shares_received": transferred, "shares_count": buyer_count,
                        "origin": match.group("place").strip(),
                        "without_signature": True, **common,
                    },
                ),
            ], ""

    match = _DE_REMOVED_AND_THREE_MANAGEMENT_CHANGES.fullmatch(leftover)
    if match:
        rule_id = "de.persons.removed_and_three_management_changes.v1"
        events = [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_removed", rule_id,
            f"{match.group('removed_surname')}, {match.group('removed_given')}",
            place=match.group("removed_place"), role=match.group("removed_role"),
            signing=match.group("removed_signing"), extra={
                "action": "removed", "origin": match.group("removed_origin").strip(),
            },
        )]
        for index in (1, 2, 3):
            extra = {
                "action": "changed" if index < 3 else "appointed",
                "origin": match.group(f"origin{index}").strip(),
            }
            if index < 3:
                extra.update({
                    "previous_role": match.group(f"previous_role{index}"),
                    "previous_signing": match.group(f"previous_signing{index}"),
                })
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id,
                f"{match.group(f'surname{index}')}, {match.group(f'given{index}')}",
                place=match.group(f"place{index}"), role=match.group(f"role{index}"),
                signing=match.group(f"signing{index}"), extra=extra,
            ))
        return events, ""

    match = _FR_NAME_CORRECTION_REALITY.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.name_correction_reality.v1",
            match.group("name"), extra={
                "action": "name_corrected", "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _DE_AUTHORIZED_CAPITAL_CLAUSE_EXPIRED.fullmatch(leftover)
    if match and match.group("date") == match.group("previous_date"):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_clause_expired_decision.v1", {
                "kind": "authorized_capital_clause", "action": "removed",
                "authorization_date": _iso_date(match.group("date")),
                "reason": "authorization_period_elapsed",
                "previous": match.group("previous").strip(),
            },
        )], ""

    match = _DE_FOUNDATION_ORGANIZATION_AND_AUDIT_WAIVER.fullmatch(leftover)
    if match:
        rule_id = "de.text.foundation_organization_and_audit_waiver.v1"
        decision_date = _iso_date(match.group("date"))
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id, {
                    "action": "removed", "previous": match.group("previous_organization").strip(),
                    "other_deed_changes_not_publishable": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "audit_requirement_changed", rule_id, {
                    "kind": "audit_waiver", "action": "granted",
                    "audit_waived": True, "decision_date": decision_date,
                    "authority": match.group("authority").strip(),
                },
            ),
        ], ""

    match = _FR_PROXY_REPLACED_BY_COLLECTIVE_SIGNING.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed",
            "fr.persons.proxy_replaced_by_collective_signing.v1",
            match.group("name"), signing="Kollektivunterschrift zu zweien", extra={
                "action": "procuration_revoked_and_signing_granted",
                "procuration_revoked": True,
            },
        )], ""

    return [], leftover
