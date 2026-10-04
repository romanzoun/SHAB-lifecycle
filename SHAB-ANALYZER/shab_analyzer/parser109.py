from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_ORGANIZATION_ENTRY_REMOVED = re.compile(
    r"^Organisation neu:\s*\[Gestrichene Angaben über die Organisation aufgrund "
    r"geänderter Eintragungsvorschriften gem\.\s*(?P<legal_basis>Art\.\s*95 HRegV)\]\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_DOMICILE_CHANGED = re.compile(
    r"^(?P<name>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"est désormais domiciliée? à\s*(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_DISSOLUTION_REENTERED_AFTER_SUSPENSIVE_EFFECT = re.compile(
    r"^\[gestrichen:\s*(?P<previous>Mit Entscheid .+?Demnach wird die Eintragung "
    r"der Auflösung der Gesellschaft im Handelsregister gestrichen\.)\]\.?\s*"
    r"Mit Entscheid des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}:\d{2})\s+Uhr,\s*wurde die Gesellschaft gemäss\s+"
    r"(?P<legal_basis>Art\.\s*731b OR)\s+aufgelöst und ihre Liquidation nach den "
    r"Vorschriften über den Konkurs angeordnet\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_DE_NEW_ADDITIONAL_POSTAL_ADDRESS = re.compile(
    r"^Neue zusätzliche Adresse:\s*(?P<address>Postfach\s+[^,.;]+),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<locality>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_SIGNING_CHANGED_TO_INDIVIDUAL = re.compile(
    r"^L['’]associée?\s+(?P<name>[^,.;]+),\s*signe désormais "
    r"individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_REGISTRATION_NOTICE = re.compile(
    r"^Eintragung der Zweigniederlassung von\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+im Handelsregister des Kantons\s+"
    r"(?P<registry_canton>[^()]+?)\s*\(SHAB vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+(?P<notice_id>\d+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_SOCIAL_CAPITAL_DIVIDED = re.compile(
    r"^Le capital social est désormais divisé en\s+(?P<count>[\d']+)\s+parts de\s+"
    r"(?P<currency>[A-Z]{3})\s+(?P<nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGERS_APPOINTED_INDIVIDUAL_LIQUIDATORS = re.compile(
    r"^Liquidateurs:\s*les gérants\s+(?P<name1>[^,.;]+?)\s+et\s+"
    r"(?P<name2>[^,.;]+?),\s*lesquels continuent à signer individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_GENERAL_APPOINTED_ADMINISTRATOR = re.compile(
    r"^Le directeur général\s+(?P<name>[^,.;]+)\s+est nommé administrateur,\s*"
    r"continue de signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_APPEAL_SUSPENSIVE_EFFECT = re.compile(
    r"^Par décision présidentielle du\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+du\s+"
    r"(?P<authority>Tribunal Cantonal du Valais),\s*l['’]effet suspensif est "
    r"accordé au recours formé contre la décision de faillite\.?$",
    re.I | re.UNICODE,
)
_FR_PARTICIPATION_CAPITAL_CREATED = re.compile(
    r"^Création ordinaire d['’]un capital-participation entièrement libéré:\s*"
    r"(?P<currency>[A-Z]{3})\s+(?P<total>[\d'.]+),\s*divisé en\s+"
    r"(?P<count>[\d']+)\s+bons de participation nominatifs de\s+"
    r"(?P=currency)\s+(?P<nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_COMMITTEE_MEMBERS_PAIR = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,.;]+),\s*et\s+(?P<name2>[^,.;]+),\s*"
    r"de et à\s+(?P<place2>[^,.;]+),\s*sont membres du comité\.?$",
    re.I | re.UNICODE,
)
_DE_CROSS_BORDER_MERGER_SAME_SHAREHOLDER = re.compile(
    r"^Grenzüberschreitende Fusion gemäss\s+(?P<legal_basis>Art\.\s*163a IPRG):\s*"
    r"Übernahme der Aktiven und Passiven der\s+(?P<absorbed_name>.+?),\s*in\s+"
    r"(?P<absorbed_place>[^(),]+?)\s*\((?P<absorbed_country>[A-Z]{2});\s*"
    r"Reg\.-Nr\.\s*(?P<absorbed_registry_id>[^)]+)\),\s*gemäss Fusionsvertrag "
    r"vom\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Bilanz per\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*wonach Aktiven von\s+"
    r"(?P<currency>[A-Z]{3})\s+(?P<assets>[\d'.]+)\s+und Passiven "
    r"\(Fremdkapital\) von\s+(?P=currency)\s+(?P<liabilities>[\d'.]+)\s+auf die "
    r"übernehmende Gesellschaft übergehen\.\s*Da dieselbe Aktionärin alle Aktien "
    r"beider an der Fusion beteiligten Gesellschaften hält,\s*findet weder eine "
    r"Kapitalerhöhung noch eine Aktienzuteilung statt\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_ADMINISTRATOR = re.compile(
    r"^Nouvelle administratrice\s*:\s*(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^()]+?)\s*(?:\((?P<canton>[A-Z]{2})\))?\.?$",
    re.I | re.UNICODE,
)
_FR_VOTING_PREFERRED_SHARE_SPLIT = re.compile(
    r"^Division des\s+(?P<from_count>[\d']+)\s+actions jusqu['’]ici de\s+"
    r"(?P<currency>[A-Z]{3})\s+(?P<from_nominal>[\d'.]+)\s+en\s+"
    r"(?P<preferred_count>[\d']+)\s+actions de\s+(?P=currency)\s+"
    r"(?P<preferred_nominal>[\d'.]+),\s*privilégiées quant au droit de vote et\s+"
    r"(?P<ordinary_count>[\d']+)\s+actions de\s+(?P=currency)\s+"
    r"(?P<ordinary_nominal>[\d'.]+)\.\s*Capital-actions:\s*(?P=currency)\s+"
    r"(?P<total>[\d'.]+),\s*entièrement libéré,\s*divisé en\s+"
    r"(?P=preferred_count)\s+actions de\s+(?P=currency)\s+"
    r"(?P=preferred_nominal),\s*privilégiées quant au droit de vote et\s+"
    r"(?P=ordinary_count)\s+actions de\s+(?P=currency)\s+"
    r"(?P=ordinary_nominal),\s*toutes nominatives\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_SIGNATURES_REVOKED_AND_LIQUIDATOR_APPOINTED = re.compile(
    r"^La signature des associés-gérants\s+(?P<name1>[^,.;]+?)\s+et\s+"
    r"(?P<name2>[^,.;]+?)\s+est radiée\.\s*Liquidatrice\s*:\s*"
    r"(?P<liquidator>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+)\.?$",
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
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser109_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 109."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_ORGANIZATION_ENTRY_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.organization_entry_removed_art_95.v1",
            {
                "action": "entry_removed",
                "reason": "registration_rules_changed",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
            },
        ))

    match = _FR_PERSON_DOMICILE_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.domicile_changed_with_origin.v1",
            match.group("name"), place=match.group("place"),
            extra={
                "action": "domicile_changed",
                "origin": match.group("origin").strip(),
            },
        ))

    match = _DE_DISSOLUTION_REENTERED_AFTER_SUSPENSIVE_EFFECT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed",
            "de.text.dissolution_reentered_after_suspensive_effect.v1",
            {
                "kind": "judicial_dissolution",
                "action": "reentered",
                "decision_date": _iso_date(match.group("decision_date")),
                "effective_time": match.group("effective_time"),
                "authority": match.group("authority").strip(),
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "liquidation_procedure": "bankruptcy_rules",
                "previous_suspensive_effect_entry_removed": True,
                "previous": match.group("previous").strip(),
            },
        ))

    match = _DE_NEW_ADDITIONAL_POSTAL_ADDRESS.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "de.text.new_additional_postal_address.v1",
            {
                "action": "added",
                "kind": "additional_address",
                "address": match.group("address").strip(),
                "postal_code": match.group("postal_code"),
                "locality": match.group("locality").strip(),
            },
        ))

    match = _FR_ASSOCIATE_SIGNING_CHANGED_TO_INDIVIDUAL.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_signing_individual.v1",
            match.group("name"), role="associée",
            signing="Einzelunterschrift",
            extra={"action": "signing_changed"},
        ))

    match = _DE_BRANCH_REGISTRATION_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_registration_notice.v1",
            {
                "action": "registered",
                "place": match.group("place").strip(),
                "branch_uid": match.group("uid"),
                "registry_canton": match.group("registry_canton").strip(),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        ))

    match = _FR_SOCIAL_CAPITAL_DIVIDED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.social_capital_divided.v1",
            {
                "kind": "social_share_structure",
                "currency": match.group("currency").upper(),
                "shares_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"),
            },
        ))

    match = _FR_MANAGERS_APPOINTED_INDIVIDUAL_LIQUIDATORS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.managers_individual_liquidators.v1"
        for group in ("name1", "name2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(group),
                role="gérant et liquidateur", signing="Einzelunterschrift",
                extra={"action": "appointed_liquidator", "signing_continues": True},
            ))

    match = _FR_DIRECTOR_GENERAL_APPOINTED_ADMINISTRATOR.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.director_general_appointed_administrator.v1",
            match.group("name"), role="administrateur",
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "appointed_administrator",
                "previous_role": "directeur général",
                "signing_continues": True,
            },
        ))

    match = _FR_BANKRUPTCY_APPEAL_SUSPENSIVE_EFFECT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.bankruptcy_appeal_suspensive_effect.v1",
            {
                "kind": "bankruptcy_effect_suspended",
                "action": "suspended_on_appeal",
                "decision_date": _iso_date(match.group("date")),
                "authority": match.group("authority"),
            },
        ))

    match = _FR_PARTICIPATION_CAPITAL_CREATED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.participation_capital_created.v1",
            {
                "kind": "participation_capital_created",
                "currency": match.group("currency").upper(),
                "total": match.group("total"),
                "fully_paid": True,
                "participation_certificates_count": _count(match.group("count")),
                "participation_certificate_nominal": match.group("nominal"),
                "registered": True,
            },
        ))

    match = _FR_COMMITTEE_MEMBERS_PAIR.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.committee_members_pair.v1"
        for index in (1, 2):
            place = match.group(f"place{index}")
            origin = match.group("origin1") if index == 1 else place
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=place, role="membre du comité",
                extra={"action": "appointed", "origin": origin.strip()},
            ))

    match = _DE_CROSS_BORDER_MERGER_SAME_SHAREHOLDER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "de.text.cross_border_merger_same_shareholder.v1",
            {
                "kind": "cross_border_merger",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_country": match.group("absorbed_country"),
                "absorbed_registry_id": match.group("absorbed_registry_id").strip(),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "currency": match.group("currency").upper(),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "same_shareholder": True,
                "capital_increase": False,
                "share_allocation": False,
            },
        ))

    match = _FR_NEW_ADMINISTRATOR.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.new_administrator.v1",
            match.group("name"), place=match.group("place"), role="administratrice",
            extra={
                "action": "appointed",
                "origin": match.group("origin").strip(),
                "place_canton": match.group("canton"),
            },
        ))

    match = _FR_VOTING_PREFERRED_SHARE_SPLIT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.voting_preferred_share_split.v1",
            {
                "kind": "share_split_and_classes",
                "currency": match.group("currency").upper(),
                "previous_count": _count(match.group("from_count")),
                "previous_nominal": match.group("from_nominal"),
                "total": match.group("total"),
                "fully_paid": True,
                "registered": True,
                "classes": [
                    {
                        "kind": "voting_preferred",
                        "count": _count(match.group("preferred_count")),
                        "nominal": match.group("preferred_nominal"),
                    },
                    {
                        "kind": "ordinary",
                        "count": _count(match.group("ordinary_count")),
                        "nominal": match.group("ordinary_nominal"),
                    },
                ],
            },
        ))

    match = _FR_MANAGER_SIGNATURES_REVOKED_AND_LIQUIDATOR_APPOINTED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_signatures_revoked_liquidator_appointed.v1"
        for group in ("name1", "name2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(group),
                role="associé-gérant",
                extra={"action": "revoked", "signing_revoked": True},
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("liquidator"),
            place=match.group("place"), role="liquidatrice",
            extra={
                "action": "appointed_liquidator",
                "origin": match.group("origin").strip(),
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
