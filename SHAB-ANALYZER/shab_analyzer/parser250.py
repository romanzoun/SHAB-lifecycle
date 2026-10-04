from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_BRANCH_REINSTATED_SHORT = re.compile(
    r"^Angaben zur Zweigniederlassung neu:\s*Wiedereintragung der "
    r"Zweigniederlassung,\s*da die Löschung\s*\(TR Nr\.\s*(?P<entry>[\d']+)\s+"
    r"vom\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4}),\s*SHAB Nr\.\s*"
    r"(?P<issue>\d+)\s+vom\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4})\)\s+"
    r"irrtümlich erfolgt ist\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_PRESIDENT_TRANSFER_TO_NEW_MANAGER = re.compile(
    r"^(?P<seller>[^,.;]+),\s*nommé président des gérants,\s*détient désormais\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+par suite "
    r"de cession de\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<transfer_nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé-gérant "
    r"pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_AND_BOARD_ROLE_SWAP = re.compile(
    r"^Ausgeschiedene Personen und erloschene Unterschriften:\s*"
    r"(?P<removed_surname>[^,;]+),\s*(?P<removed_given>[^,;]+),\s*von\s+"
    r"(?P<removed_origin>[^,;]+),\s*in\s+(?P<removed_place>[^,;.]+),\s*mit\s+"
    r"(?P<removed_signing>[^.;]+)\.\s*Eingetragene Personen neu oder mutierend:\s*"
    r"(?P<surname1>[^,;]+),\s*(?P<given1>[^,;]+),\s*von\s+"
    r"(?P<origin1>[^,;]+),\s*in\s+(?P<place1>[^,;]+),\s*"
    r"(?P<role1>[^,;\[]+),\s*mit\s+(?P<signing1>[^;\[]+)\s*"
    r"\[bisher:\s*(?P<previous_role1>[^,;\]]+),\s*mit\s+"
    r"(?P<previous_signing1>[^;\]]+)\];\s*"
    r"(?P<surname2>[^,;]+),\s*(?P<given2>[^,;]+),\s*von\s+"
    r"(?P<origin2>[^,;]+),\s*in\s+(?P<place2>[^,;]+),\s*"
    r"(?P<role2>[^,;\[]+),\s*mit\s+(?P<signing2>[^;\[]+)\s*"
    r"\[bisher:\s*(?P<previous_role2>[^,;\]]+),\s*mit\s+"
    r"(?P<previous_signing2>[^;\]]+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_FOUR_BOARD_MEMBERS_NO_SIGNING_CLAUSE = re.compile(
    r"^(?P<name1>[^,;]+),\s*de\s+(?P<origin1>[^,;]+),\s*à\s+"
    r"(?P<place1>[^,;]+),\s*(?P<country1>[A-Z]{1,3}),\s*"
    r"(?P<name2>[^,;]+),\s*d['’](?P<origin2>[^,;]+),\s*à\s+"
    r"(?P<place2>[^,;]+),\s*(?P<country2>[A-Z]{1,3}),\s*"
    r"(?P<name3>[^,;]+),\s*des\s+(?P<origin3>[^,;]+),\s*à\s+"
    r"(?P<place3>[^,;]+),\s*(?P<country3>[A-Z]{1,3}),\s*et\s+"
    r"(?P<name4>[^,;]+),\s*de\s+(?P<origin4>[^,;]+),\s*à\s+"
    r"(?P<place4>[^,;]+),\s*sont membres du conseil d['’]administration,\s*"
    r"tous quatre\.?$",
    re.I | re.UNICODE,
)
_FR_INDIVIDUAL_PROXY_GRANTED_SHORT = re.compile(
    r"^(?P<name>[^,.;]+)\s+a désormais une procuration individuelle\.?$",
    re.I | re.UNICODE,
)
_FR_PROXY_REVOKED_DEPUTY_DIRECTOR_RESTRICTED = re.compile(
    r"^(?P<name>[^,.;]+),\s*dont la procuration est éteinte,\s*est nommée\s+"
    r"(?P<role>directrice adjointe)\s+avec\s+"
    r"(?P<required_with>un directeur ou le directeur général)\.?$",
    re.I | re.UNICODE,
)
_FR_SEVEN_LIQUIDATORS_MIXED_CONTINUING_SIGNING = re.compile(
    r"^(?P<name1>[^,.;]+),\s*lequel continue à signer collectivement à deux,\s*"
    r"(?P<name2>[^,.;]+),\s*(?P<name3>[^,.;]+),\s*lesquels continuent à "
    r"signer collectivement à deux,\s*toutefois pas entre eux,\s*"
    r"(?P<name4>[^,.;]+),\s*(?P<name5>[^,.;]+),\s*(?P<name6>[^,.;]+),\s*"
    r"et\s+(?P<name7>[^,.;]+),\s*sont nommés liquidateurs\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_AND_PRESIDENCY = re.compile(
    r"^Jusqu['’]ici titulaire de\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*l['’]associée-gérante\s+(?P<seller>[^,.;]+)\s+"
    r"détient\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\s+par suite de cession de\s+"
    r"(?P<transferred>[\d']+)\s+parts à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé-gérant "
    r"pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*L['’]associée-gérante\s+(?P<seller_again>[^,.;]+),\s*"
    r"nommée présidente,\s*signe maintenant collectivement à deux,\s*"
    r"ses pouvoirs étant modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_FR_NON_PUBLIC_FACTS_CONNECTOR = re.compile(
    r"^sur des faits non soumis à publication\.?$", re.I | re.UNICODE
)
_FR_REMOVED_PERSON_TYPO = re.compile(
    r"^Personne radi[eé]é?e?:\s*(?P<name>[^,.;]+),\s*(?P<role>associée),\s*"
    r"(?P<signing>signature individuelle)\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_ADDED_ORGANIZATION_SPACED_UID = re.compile(
    r"^Zweigniederlassung neu:\s*(?P<name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\s*\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_ORIGIN_CORRECTED_PARENTHESES = re.compile(
    r"^L['’]inscription\s+N°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée comme suit:\s*"
    r"l['’](?P<role>administratrice)\s+(?P<name>[^,.;]+)\s+est originaire de la\s+"
    r"(?P<origin>[^()]+?)\s*\(et non de la\s+(?P<previous_origin>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_DEFINITIVE_MORATORIUM_EXTENDED_TEXT_DATES = re.compile(
    r"^Par décision du\s+(?P<decision_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"(?P<authority>.+?)\s+a prolongé le sursis concordataire définitif "
    r"accordé au\s+(?P<subject>titulaire)\s+jusqu['’]au\s+"
    r"(?P<until>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_MORATORIUM_EXTENSION_WITH_HISTORY = re.compile(
    r"^Mit Entscheid der\s+(?P<authority>.+?),\s*vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde eine Verlängerung der "
    r"Nachlassstundung von\s+(?P<duration>\w+)\s+Monaten bis zum\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\s+bewilligt\.\s*"
    r"\[bisher:\s*Mit Entscheid der\s+(?P<previous_authority>.+?),\s*vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde eine Verlängerung "
    r"der Nachlassstundung von\s+(?P<previous_duration>\w+)\s+Monaten bis zum\s+"
    r"(?P<previous_until>\d{2}\.\d{2}\.\d{4})\s+bewilligt\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFERS_ALL_TO_UNSIGNED_ASSOCIATE = re.compile(
    r"^Le gérant\s+(?P<seller>[^,.;]+)\s+a cédé ses\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*de et à\s+(?P<place>[^,.;]+),\s*nouvelle associée "
    r"pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+);\s*elle n['’]exerce pas la signature sociale\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_REINSTATED_ERRONEOUS_DELETION_ART_260 = re.compile(
    r"^Mit TR\s+(?P<entry>[\d']+)\s+vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+wurde die Gesellschaft irrtümlich "
    r"gelöscht\.\s*Demzufolge wird sie hiermit wieder eingetragen und der folgende "
    r"Bemerkungstext publiziert:\s*Das Konkursverfahren wurde mit Urteil des\s+"
    r"(?P<authority>.+?)\s+vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+als "
    r"geschlossen erklärt und das Handelsregisteramt angewiesen,\s*die Löschung "
    r"der Gesellschaft erst auf Anweisung des Konkursamtes hin vorzunehmen\.\s*"
    r"Die Eintragung bleibt nur zum Zweck der Geltendmachung von abgetretenen "
    r"Ansprüchen nach\s+(?P<legal_basis>Art\.\s*260 SchKG)\s+erhalten und die "
    r"Verfügungsbefugnisse der Organe der Gesellschaft leben nicht wieder auf\.\s*"
    r"\[bisher:\s*Das Konkursverfahren wurde mit Urteil des\s+"
    r"(?P<previous_authority>.+?)\s+vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+als geschlossen erklärt\.\s*"
    r"Die Gesellschaft wird von Amtes wegen gelöscht\.\]\.?$",
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
_GERMAN_NUMBERS = {
    "ein": 1,
    "eine": 1,
    "einen": 1,
    "zwei": 2,
    "drei": 3,
    "vier": 4,
    "fünf": 5,
    "sechs": 6,
}


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _french_date(raw: str) -> str:
    day, month, year = raw.casefold().replace("1er", "1", 1).split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", "").replace(".", ""))


def _duration_months(raw: str) -> int | None:
    token = raw.strip().casefold()
    return int(token) if token.isdigit() else _GERMAN_NUMBERS.get(token)


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
        role=role.strip() if role else None,
        signing=signing,
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser250_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 250."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_BRANCH_REINSTATED_SHORT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.branch_reinstated_short.v1", {
                "kind": "registration_reinstated", "scope": "branch",
                "action": "reinstated", "reason": "erroneous_deletion",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_issue": int(match.group("issue")),
                "notice_date": _iso_date(match.group("notice_date")),
            },
        )], ""

    match = _FR_MANAGER_PRESIDENT_TRANSFER_TO_NEW_MANAGER.fullmatch(leftover)
    if match:
        remaining = _count(match.group("remaining"))
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        if (
            transferred == buyer_count
            and len({
                match.group("nominal"), match.group("transfer_nominal"),
                match.group("buyer_nominal"),
            }) == 1
        ):
            rule_id = "fr.persons.manager_president_transfer_to_new_manager.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            common = {"currency": "CHF", "share_nominal": match.group("nominal")}
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé-gérant président",
                    extra={
                        "action": "appointed_president_and_shares_transferred",
                        "shares_before": remaining + transferred,
                        "shares_transferred": transferred, "shares_count": remaining,
                        "counterparty": buyer, **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé-gérant", extra={
                        "action": "appointed_and_shares_received",
                        "new_associate": True, "origin": match.group("origin").strip(),
                        "shares_received": transferred, "shares_count": buyer_count,
                        "counterparty": seller, **common,
                    },
                ),
            ], ""

    match = _DE_REMOVED_AND_BOARD_ROLE_SWAP.fullmatch(leftover)
    if match:
        rule_id = "de.persons.removed_and_board_role_swap.v1"
        events = [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_removed", rule_id,
            f"{match.group('removed_surname')}, {match.group('removed_given')}",
            place=match.group("removed_place"),
            signing=match.group("removed_signing").strip(), extra={
                "action": "removed", "origin": match.group("removed_origin").strip(),
            },
        )]
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id,
                f"{match.group(f'surname{index}')}, {match.group(f'given{index}')}",
                place=match.group(f"place{index}"), role=match.group(f"role{index}"),
                signing=match.group(f"signing{index}").strip(), extra={
                    "action": "role_changed", "origin": match.group(f"origin{index}").strip(),
                    "previous_role": match.group(f"previous_role{index}").strip(),
                    "previous_signing": match.group(f"previous_signing{index}").strip(),
                },
            ))
        return events, ""

    match = _FR_FOUR_BOARD_MEMBERS_NO_SIGNING_CLAUSE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.four_board_members_no_signing_clause.v1"
        events = []
        for index in (1, 2, 3, 4):
            extra = {
                "action": "appointed", "origin": match.group(f"origin{index}").strip(),
                "group_count": 4,
            }
            country = match.groupdict().get(f"country{index}")
            if country:
                extra["country"] = country
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role="membre du conseil d'administration", extra=extra,
            ))
        return events, ""

    match = _FR_INDIVIDUAL_PROXY_GRANTED_SHORT.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.individual_proxy_granted_short.v1",
            match.group("name"), signing="Einzelprokura", extra={"action": "granted"},
        )], ""

    match = _FR_PROXY_REVOKED_DEPUTY_DIRECTOR_RESTRICTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.proxy_revoked_deputy_director_restricted.v1",
            match.group("name"), role=match.group("role"), extra={
                "action": "appointed", "previous_signing": "Kollektivprokura",
                "previous_signing_revoked": True,
                "signing_requires": match.group("required_with").strip(),
            },
        )], ""

    match = _FR_SEVEN_LIQUIDATORS_MIXED_CONTINUING_SIGNING.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.seven_liquidators_mixed_continuing_signing.v1"
        events = []
        for index in range(1, 8):
            extra = {"action": "appointed_liquidator"}
            signing = None
            if index in (1, 2, 3):
                signing = "Kollektivunterschrift zu zweien"
                extra["signing_continues"] = True
            if index in (2, 3):
                extra["not_with"] = match.group("name3" if index == 2 else "name2").strip()
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="liquidateur", signing=signing, extra=extra,
            ))
        return events, ""

    match = _FR_MANAGER_TRANSFER_AND_PRESIDENCY.fullmatch(leftover)
    if match:
        before = _count(match.group("before"))
        remaining = _count(match.group("remaining"))
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        seller = match.group("seller").strip()
        if (
            seller.casefold() == match.group("seller_again").strip().casefold()
            and before == remaining + transferred
            and transferred == buyer_count
            and len({
                match.group("nominal"), match.group("remaining_nominal"),
                match.group("buyer_nominal"),
            }) == 1
        ):
            rule_id = "fr.persons.manager_transfer_and_presidency.v1"
            buyer = match.group("buyer").strip()
            common = {"currency": "CHF", "share_nominal": match.group("nominal")}
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller,
                    role="associée-gérante présidente",
                    signing="Kollektivunterschrift zu zweien", extra={
                        "action": "appointed_president_and_shares_transferred",
                        "powers_modified": True, "shares_before": before,
                        "shares_transferred": transferred, "shares_count": remaining,
                        "counterparty": buyer, **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé-gérant", extra={
                        "action": "appointed_and_shares_received", "new_associate": True,
                        "origin": match.group("origin").strip(),
                        "shares_received": transferred, "shares_count": buyer_count,
                        "counterparty": seller, **common,
                    },
                ),
            ], ""

    if _FR_NON_PUBLIC_FACTS_CONNECTOR.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.non_public_facts_connector.v1", {
                "kind": "non_public_facts", "action": "scope_recorded",
                "publication_required": False,
            },
        )], ""

    match = _FR_REMOVED_PERSON_TYPO.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_removed", "fr.persons.removed_person_radiee_typo.v1",
            match.group("name"), role=match.group("role"),
            signing="Einzelunterschrift", extra={"action": "removed"},
        )], ""

    match = _DE_BRANCH_ADDED_ORGANIZATION_SPACED_UID.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_added_organization_spaced_uid.v1", {
                "action": "added", "name": match.group("name").strip(),
                "branch_uid": re.sub(r"\s+", "", match.group("uid")).upper(),
            },
        )], ""

    match = _FR_ADMINISTRATOR_ORIGIN_CORRECTED_PARENTHESES.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected",
            "fr.persons.administrator_origin_corrected_parentheses.v1",
            match.group("name"), role=match.group("role").lower(), extra={
                "action": "origin_corrected", "origin": match.group("origin").strip(),
                "previous_origin": match.group("previous_origin").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_DEFINITIVE_MORATORIUM_EXTENDED_TEXT_DATES.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.definitive_moratorium_extended_text_dates.v1", {
                "kind": "composition_moratorium_extended", "action": "extended",
                "moratorium_type": "definitive",
                "decision_date": _french_date(match.group("decision_date")),
                "until": _french_date(match.group("until")),
                "authority": match.group("authority").strip(),
                "subject": match.group("subject").lower(),
            },
        )], ""

    match = _DE_MORATORIUM_EXTENSION_WITH_HISTORY.fullmatch(leftover)
    if match and (
        match.group("authority").strip() == match.group("previous_authority").strip()
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.moratorium_extension_with_history.v1", {
                "kind": "composition_moratorium_extended", "action": "extended",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "duration_months": _duration_months(match.group("duration")),
                "until": _iso_date(match.group("until")),
                "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                "previous_duration_months": _duration_months(
                    match.group("previous_duration")
                ),
                "previous_until": _iso_date(match.group("previous_until")),
            },
        )], ""

    match = _FR_MANAGER_TRANSFERS_ALL_TO_UNSIGNED_ASSOCIATE.fullmatch(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        if transferred == buyer_count and match.group("nominal") == match.group("buyer_nominal"):
            rule_id = "fr.persons.manager_transfers_all_to_unsigned_associate.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            common = {"currency": "CHF", "share_nominal": match.group("nominal")}
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="gérant", extra={
                        "action": "all_shares_transferred", "shares_before": transferred,
                        "shares_transferred": transferred, "shares_count": 0,
                        "counterparty": buyer, **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associée", extra={
                        "action": "appointed_and_shares_received", "new_associate": True,
                        "origin": match.group("place").strip(),
                        "shares_received": transferred, "shares_count": buyer_count,
                        "counterparty": seller, "signing_authority": False, **common,
                    },
                ),
            ], ""

    match = _DE_COMPANY_REINSTATED_ERRONEOUS_DELETION_ART_260.fullmatch(leftover)
    if match and (
        match.group("authority").strip() == match.group("previous_authority").strip()
        and match.group("decision_date") == match.group("previous_decision_date")
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.company_reinstated_erroneous_deletion_art260.v1", {
                "kind": "registration_reinstated", "action": "reinstated",
                "reason": "erroneous_deletion", "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "bankruptcy_action": "proceedings_closed",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "deletion_only_on_bankruptcy_office_instruction": True,
                "purpose": "assertion_of_assigned_claims",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "governing_body_powers_restored": False,
                "previous_action": "bankruptcy_closed_and_company_deleted_ex_officio",
            },
        )], ""

    return [], leftover
