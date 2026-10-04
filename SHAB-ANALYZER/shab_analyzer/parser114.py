from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_OWNER_BANKRUPTCY_EFFECT_SUSPENDED = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+der Beschwerde gegen den Entscheid des\s+"
    r"(?P<bankruptcy_court>.+?)\s+vom\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+betreffend "
    r"Konkurseröffnung aufschiebende Wirkung zuerkannt\.\s*Demnach wird die "
    r"Eintragung betreffend Konkurs im Handelsregister gestrichen\.\s*"
    r"\[bisher:\s*Über den Inhaber dieses Einzelunternehmens ist mit Entscheid "
    r"des\s+(?P=bankruptcy_court)\s+vom\s+(?P=bankruptcy_date)\s+mit Wirkung ab "
    r"dem\s+(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}[.:]\d{2})\s+Uhr der Konkurs eröffnet worden\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_CLOSURE_SUSPENDED = re.compile(
    r"^(?P<authority>Le président du Tribunal de l['’]arrondissement de .+?)\s+"
    r"a suspendu la clôture de la faillite le\s+(?P<date>\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_ADMINISTRATOR_SAME_ORIGIN_AND_PLACE = re.compile(
    r"^Nouvel administrateur\s*:\s*(?P<name>[^,.;]+),\s*du et au\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_MIXED_DE_REMOVED_FRENCH_OFFICERS = re.compile(
    r"^Gelöschte Personen:\s*(?P<name1>[^,;]+),\s*"
    r"(?P<role1>[^,;]+),\s*(?P<sign1>signature individuelle);\s*"
    r"(?P<name2>[^,;]+),\s*(?P<role2>[^,;]+),\s*"
    r"(?P<sign2>signature individuelle)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_APPOINTED_MANAGER_PRESIDENT_INDIVIDUAL = re.compile(
    r"^L['’]associé\s+(?P<name>[^,.;]+),\s*nommé gérant et président,\s*"
    r"signe désormais individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_LIMITED_PARTNERS_CONTRIBUTIONS_CHANGED = re.compile(
    r"^La commandite de l['’]associé commanditaire\s+(?P<name1>[^,.;]+)\s+"
    r"a été portée de CHF\s+(?P<from1>[\d'.]+)\s+à CHF\s+(?P<to1>[\d'.]+),\s*"
    r"et celle de l['’]associé commanditaire\s+(?P<name2>[^,.;]+)\s+"
    r"de CHF\s+(?P<from2>[\d'.]+)\s+à CHF\s+(?P<to2>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDATION_ASSET_TRANSFER_INVESTMENT_GROUP_CLAIM = re.compile(
    r"^Vermögensübertragung:\s*Die Stiftung überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven \(Fremdkapital\) von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*Anspruch an der Anlagegruppe\s+[\"“]"
    r"(?P<investment_group>.+?)[\"”]\s+der\s+(?P<claim_issuer>.+?)\s+"
    r"in der Höhe von CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_INCREASE = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+eine Erhöhung des genehmigten Kapitals "
    r"gemäss näherer Umschreibung in den Statuten beschlossen\.?$",
    re.I | re.UNICODE,
)
_DE_COMPOSITION_COMMISSIONER_APPOINTED = re.compile(
    r"^Mit Entscheid vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+wurde\s+"
    r"(?P<name>[^,.;]+),\s*c/o\s+(?P<organization>[^,.;]+),\s*in\s+"
    r"(?P<place>[^,;]+),\s*zum Sachwalter ernannt\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_LIQUIDATORS_SHARED_NEW_PLACE = re.compile(
    r"^(?P<name1>[^,.;]+?)\s+et\s+(?P<name2>[^,.;]+),\s*"
    r"désormais à\s+(?P<place>[^,.;]+),\s*sont nommés liquidateurs\.?$",
    re.I | re.UNICODE,
)
_DE_CORPORATION_ASSET_TRANSFER_NO_CONSIDERATION_ITEM = re.compile(
    r"Vermögensübertragung:\s*Die\s+(?P<source_kind>Aktiengesellschaft)\s+"
    r"überträgt gemäss Vertrag vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+und Passiven "
    r"\(Fremdkapital\) von CHF\s+(?P<liabilities>[\d'.]+)\s+auf die\s+"
    r"(?P<recipient>[\"“].+?[\"”])\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+"
    r"(?P<place>[^.]+)\.\s*Gegenleistung:\s*(?P<consideration>keine)\.?,?",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_NAMES_CORRECTED = re.compile(
    r"^Rectificatif:\s*L['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que les "
    r"administrateurs se nomment:\s*(?P<names>.+?)\s*\(et non\s+"
    r"(?P<previous_names>.+?),\s*comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_AUTHORIZED_CAPITAL_CLAUSE_MODIFIED = re.compile(
    r"^Par décision du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"l['’]assemblée générale a modifié la clause statutaire relative à "
    r"l['’]augmentation autorisée du capital introduite par décision du\s+"
    r"(?P<introduction_date>\d{2}\.\d{2}\.\d{4})\s+et modifiée le\s+"
    r"(?P<previous_modification_date>\d{2}\.\d{2}\.\d{4}):\s*"
    r"pour les détails,\s*voir les statuts\.?$",
    re.I | re.UNICODE,
)
_FR_DELEGATED_BOARD_MEMBER_SAME_ORIGIN_AND_PLACE = re.compile(
    r"^(?P<name>[^,.;]+),\s*de et à\s+(?P<place>[^,.;]+),\s*est\s+"
    r"(?P<role>membre délégué du conseil d['’]administration)\.?$",
    re.I | re.UNICODE,
)
_FR_REGISTERED_SHARE_RESTRICTION_STRUCTURE = re.compile(
    r"^(?P<newly_restricted_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<newly_restricted_nominal>[\d'.]+)\s+sont désormais\s*\.\s*"
    r"Capital-actions:\s*CHF\s+(?P<total>[\d'.]+),\s*entièrement libéré,\s*"
    r"divisé en\s+(?P<unrestricted_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<unrestricted_nominal>[\d'.]+),\s*nominatives et\s+"
    r"(?P<restricted_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<restricted_nominal>[\d'.]+),\s*nominatives,\s*"
    r"liées selon statuts\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_PROCEEDING_RESUMED_SHORT = re.compile(
    r"^Das Konkursverfahren wird nun durchgeführt,\s*da im Sinne von\s+"
    r"(?P<legal_basis>Art\.\s*230 Abs\.\s*2 SchKG)\s+die Durchführung des "
    r"Konkursverfahrens verlangt und die erforderliche Sicherheit geleistet "
    r"wurde\.?$",
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


def _french_date(raw: str) -> str:
    day, month, year = raw.strip().lower().replace("1er", "1").split()
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


def _split_french_names(raw: str) -> list[str]:
    return [part.strip() for part in re.split(r"\s*,\s*|\s+et\s+", raw) if part.strip()]


def extract_parser114_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 114."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_OWNER_BANKRUPTCY_EFFECT_SUSPENDED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.owner_bankruptcy_effect_suspended.v3",
            {
                "kind": "bankruptcy_effect_suspended", "scope": "owner",
                "decision_date": _iso_date(match.group("decision_date")),
                "bankruptcy_decision_date": _iso_date(match.group("bankruptcy_date")),
                "bankruptcy_effective_date": _iso_date(match.group("effective_date")),
                "bankruptcy_effective_time": match.group("effective_time").replace(".", ":"),
                "authority": match.group("authority").strip(),
                "bankruptcy_court": match.group("bankruptcy_court").strip(),
                "bankruptcy_registration_removed": True,
            },
        ))

    match = _FR_BANKRUPTCY_CLOSURE_SUSPENDED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.bankruptcy_closure_suspended.v2",
            {
                "kind": "bankruptcy_closure_suspended",
                "date": _french_date(match.group("date")),
                "authority": match.group("authority").strip(),
            },
        ))

    match = _FR_NEW_ADMINISTRATOR_SAME_ORIGIN_AND_PLACE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.new_administrator_same_origin_place.v1",
            match.group("name"), place=match.group("place"), role="administrateur",
            extra={"action": "appointed", "heimat": match.group("place").strip()},
        ))

    match = _MIXED_DE_REMOVED_FRENCH_OFFICERS.search(leftover)
    if match:
        consume(match)
        rule_id = "mixed.persons.removed_french_officers.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group(f"name{index}"),
                role=match.group(f"role{index}").strip(),
                signing="Einzelunterschrift", extra={"action": "removed"},
            ))

    match = _FR_ASSOCIATE_APPOINTED_MANAGER_PRESIDENT_INDIVIDUAL.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_appointed_manager_president_individual.v1",
            match.group("name"), role="gérant président", signing="Einzelunterschrift",
            extra={"action": "appointed", "previous_role": "associé"},
        ))

    match = _FR_LIMITED_PARTNERS_CONTRIBUTIONS_CHANGED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.limited_partnership_contributions_changed.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="associé commanditaire",
                extra={
                    "action": "limited_partnership_contribution_changed",
                    "previous_limited_partnership_contribution": match.group(f"from{index}"),
                    "limited_partnership_contribution": match.group(f"to{index}"),
                    "currency": "CHF",
                },
            ))

    match = _DE_FOUNDATION_ASSET_TRANSFER_INVESTMENT_GROUP_CLAIM.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.foundation_asset_transfer_investment_group_claim.v1",
            {
                "source_kind": "stiftung", "date": _iso_date(match.group("date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"),
                "consideration_kind": "investment_group_claim",
                "investment_group": match.group("investment_group").strip(),
                "claim_issuer": match.group("claim_issuer").strip(),
            },
        ))

    match = _DE_AUTHORIZED_CAPITAL_INCREASE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_increase_reworded.v1",
            {
                "kind": "authorized_increase", "action": "increased",
                "date": _iso_date(match.group("date")), "details_in_statutes": True,
            },
        ))

    match = _DE_COMPOSITION_COMMISSIONER_APPOINTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.composition_commissioner_appointed.v1",
            match.group("name"), place=match.group("place"), role="Sachwalter",
            extra={
                "action": "appointed", "decision_date": _iso_date(match.group("date")),
                "organization": match.group("organization").strip(),
            },
        ))

    match = _FR_TWO_LIQUIDATORS_SHARED_NEW_PLACE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_liquidators_shared_new_place.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group("place"), role="liquidateur",
                extra={"action": "appointed", "domicile_changed": True},
            ))

    transfer_matches = list(_DE_CORPORATION_ASSET_TRANSFER_NO_CONSIDERATION_ITEM.finditer(leftover))
    if transfer_matches:
        for item in transfer_matches:
            events.append(_event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.corporation_asset_transfer_no_consideration.v1",
                {
                    "source_kind": item.group("source_kind").lower(),
                    "date": _iso_date(item.group("date")),
                    "assets": item.group("assets"), "liabilities": item.group("liabilities"),
                    "liabilities_kind": "third_party_capital", "currency": "CHF",
                    "recipient": item.group("recipient").strip('"“”'),
                    "recipient_uid": item.group("uid"),
                    "recipient_place": item.group("place").strip(),
                    "consideration": item.group("consideration").lower(),
                    "gratuitous": True,
                },
            ))
        for item in reversed(transfer_matches):
            leftover = f"{leftover[:item.start()]} {leftover[item.end():]}"

    match = _FR_ADMINISTRATOR_NAMES_CORRECTED.search(leftover)
    if match:
        names = _split_french_names(match.group("names"))
        previous_names = _split_french_names(match.group("previous_names"))
        if names and len(names) == len(previous_names):
            consume(match)
            rule_id = "fr.persons.administrator_names_corrected.v1"
            reference = {
                "action": "name_corrected", "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            }
            for name, previous_name in zip(names, previous_names):
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, name, role="administrateur",
                    extra={**reference, "previous_name": previous_name},
                ))

    match = _FR_AUTHORIZED_CAPITAL_CLAUSE_MODIFIED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.authorized_capital_clause_modified.v3",
            {
                "kind": "authorized_capital_clause_modified", "action": "modified",
                "decision_date": _iso_date(match.group("decision_date")),
                "introduction_date": _iso_date(match.group("introduction_date")),
                "previous_modification_date": _iso_date(
                    match.group("previous_modification_date")
                ),
                "details_in_statutes": True,
            },
        ))

    match = _FR_DELEGATED_BOARD_MEMBER_SAME_ORIGIN_AND_PLACE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.delegated_board_member_same_origin_place.v1",
            match.group("name"), place=match.group("place"),
            role=match.group("role").strip(),
            extra={"action": "appointed", "heimat": match.group("place").strip()},
        ))

    match = _FR_REGISTERED_SHARE_RESTRICTION_STRUCTURE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.registered_share_restriction_structure.v2",
            {
                "kind": "share_structure", "action": "transfer_restriction_applied",
                "currency": "CHF", "total": match.group("total"),
                "fully_paid": True,
                "newly_restricted_count": _count(match.group("newly_restricted_count")),
                "newly_restricted_nominal": match.group("newly_restricted_nominal"),
                "unrestricted_count": _count(match.group("unrestricted_count")),
                "unrestricted_nominal": match.group("unrestricted_nominal"),
                "restricted_count": _count(match.group("restricted_count")),
                "restricted_nominal": match.group("restricted_nominal"),
                "share_kind": "nominatives", "restriction": "liées selon statuts",
            },
        ))

    match = _DE_BANKRUPTCY_PROCEEDING_RESUMED_SHORT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_proceeding_resumed_short.v1",
            {
                "kind": "bankruptcy_proceedings_resumed",
                "reason": "request_and_security",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "execution_requested": True, "security_provided": True,
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
