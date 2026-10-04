from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_CONDITIONAL_PARTICIPATION_CAPITAL_INCREASE = re.compile(
    r"^Augmentation du capital-participation conditionnel,\s*fondée sur la "
    r"clause statutaire relative à la création d['’]un capital-participation "
    r"conditionnel modifiée en dernier lieu le\s+"
    r"(?P<clause_date>\d{2}\.\d{2}\.\d{4}),\s*par l['’]émission de\s+"
    r"(?P<issued>[\d']+)\s+bons de participation de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*nominatifs,\s*liés selon statuts\.\s*"
    r"Capital-participation:\s*CHF\s+(?P<total>[\d'.]+),\s*entièrement "
    r"libéré,\s*divisé en\s+(?P<count>[\d']+)\s+bons de participation de "
    r"CHF\s+(?P=nominal),\s*nominatifs,\s*liés selon statuts\.?$",
    re.I | re.UNICODE,
)
_FR_CONDITIONAL_SHARE_CAPITAL_CLAUSE_NO_DETAILS = re.compile(
    r"^L['’]assemblée générale a introduit une clause statutaire relative à "
    r"une augmentation du capital-actions au moyen d['’]un capital "
    r"conditionnel,\s*par décision du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_PROXY_REVOKED_APPOINTED_ADMINISTRATOR_PRESIDENT = re.compile(
    r"^(?P<name>[^,.;]+),\s*qui est maintenant à\s+(?P<place>[^,.;]+)\s+"
    r"et dont la procuration est éteinte,\s*est nommé\s+"
    r"(?P<role>administrateur président)(?:\s+avec signature "
    r"(?P<signing>individuelle))?\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGER_LIQUIDATORS = re.compile(
    r"^Liquidateurs:\s*les associés et gérants\s+(?P<name1>[^,.;]+?)\s+"
    r"et\s+(?P<name2>[^,.;]+?),\s*lesquels continuent à signer "
    r"individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_FOUR_COMMITTEE_ROLE_CHANGES = re.compile(
    r"^Les membres du comité\s+(?P<name1>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<previous_role1>[^,.;]+),\s*nommé\s+(?P<role1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<previous_role2>[^,.;]+),\s*nommé\s+(?P<role2>[^,.;]+),\s*"
    r"(?P<name3>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<previous_role3>[^,.;]+),\s*nommé\s+(?P<role3>[^,.;]+),\s*et\s+"
    r"(?P<name4>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<previous_role4>[^,.;]+),\s*nommé\s+(?P<role4>[^,.;]+),\s*"
    r"continuent à signer collectivement à deux mais sauf entre eux\.?$",
    re.I | re.UNICODE,
)
_DE_EXPIRED_AND_NEW_AUTHORIZED_CAPITAL_TYPO = re.compile(
    r"^\[Streichung der Statutenbestimmung über die genehmigte "
    r"Kapitalerhöhung infolge\s+(?:infolge\s+)?Ablaufs der zeitlichen "
    r"Befristung\.\]\s*\.\s*Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+eine genehmigte Kapitalerhöhung "
    r"gemäss näherer Umschreibung in den Statuten beschlossen\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_ASSET_TRANSFER_WITH_INVENTORY = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss "
    r"Vermögensübertragungsvertrag und Inventar vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s*von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_BECOMES_DIRECTOR = re.compile(
    r"^(?P<name>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<previous_role>membre du conseil de fondation),\s*maintenant\s+"
    r"(?P<role>directrice),\s*continue à signer individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_ORGANIZATION_BODIES = re.compile(
    r"^Organisation neu:\s*Organisation:\s*Generalversammlung,\s*Vorstand "
    r"von\s+(?P<minimum_board_members>\d+)\s+oder mehr Mitgliedern und "
    r"Revisionsstelle\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_GENERAL_BECOMES_DELEGATE_ADMINISTRATOR = re.compile(
    r"^(?P<name>[^,.;]+)\s+jusqu['’]ici\s+(?P<previous_role>directeur "
    r"général)\s+est désormais\s+(?P<role>administrateur délégué)\.?$",
    re.I | re.UNICODE,
)
_DE_DELETION_REASON_OMITTED = re.compile(
    r"^Mit dem im SHAB Nr\.\s*(?P<issue>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten TR-Nr\.\s*"
    r"(?P<entry>[\d']+)\s+vom\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"wurde der Löschunggrund irrtümlich nicht aufgeführt\.\s*Die "
    r"Gesellschaft wird gelöscht\.?$",
    re.I | re.UNICODE,
)
_DE_SOLE_PROPRIETOR_ASSET_TRANSFER_TWO_DATES = re.compile(
    r"^Vermögensübertragung:\s*Der Geschäftsinhaber überträgt gemäss "
    r"Vermögensübertragungsvertrag vom\s+"
    r"(?P<agreement_date1>\d{2}\.\d{2}\.\d{4})/"
    r"(?P<agreement_date2>\d{2}\.\d{2}\.\d{4})\s+und Inventar per\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s*von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<share_count>[\d']+)\s+zu\s+"
    r"(?P<paid_percent>\d+)\s*%\s*liberierte\s+"
    r"(?P<share_kind>Namenaktien)\s+zu CHF\s+"
    r"(?P<share_nominal>[\d'.]+)\s+und eine Forderung von CHF\s+"
    r"(?P<claim>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_IT_ASSET_ACQUISITION_INTENTION_FORMATION_LIMIT_EXCEEDED = re.compile(
    r"^Fatti particolari:\s*A seguito del superamento dell['’]importo massimo "
    r"dell['’]intenzione di assunzione di beni notificata in occasione della "
    r"costituzione,\s*la società ha modificato successivamente il proprio "
    r"statuto in merito alla clausola dell['’]intenzione di assunzione di beni "
    r"come segue:\s*la società intende assumere la part\.\s*"
    r"(?P<plot_number>[^ ]+)\s+RFD di\s+(?P<place>.+?)\s+per il prezzo di "
    r"CHF\s+(?P<price>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_AUDIT_WAIVER_ERRONEOUS_BRACKET = re.compile(
    r"^\[Der Verzicht auf eine eingeschränkte Revision wurde "
    r"fälschlicherweise eingetragen\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_SUSPENSIVE_EFFECT_DENIED = re.compile(
    r"^Par décision du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>.+?)\s+n['’]entre pas en matière sur la requête "
    r"d['’]effet suspensif et dit que le prononcé de faillite du\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+prend effet le\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*à\s*"
    r"(?P<effective_hour>\d{1,2})h(?P<effective_minute>\d{2})\.?$",
    re.I | re.UNICODE,
)
_FR_STATUTES_ALSO_AMENDED = re.compile(
    r"^Statuts modifiés également\.?$",
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


def extract_parser211_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 211."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_CONDITIONAL_PARTICIPATION_CAPITAL_INCREASE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.conditional_participation_capital_increase.v1", {
                "kind": "conditional_participation_capital_increase",
                "action": "increased",
                "clause_last_modified": _iso_date(match.group("clause_date")),
                "issued_participation_certificates": _count(match.group("issued")),
                "participation_certificates": _count(match.group("count")),
                "participation_certificate_nominal": match.group("nominal"),
                "total": match.group("total"),
                "currency": "CHF",
                "fully_paid": True,
                "participation_certificate_kind": "registered",
                "transfer_restricted_by_statutes": True,
            },
        )], ""

    match = _FR_CONDITIONAL_SHARE_CAPITAL_CLAUSE_NO_DETAILS.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.conditional_share_capital_clause_no_details.v1", {
                "kind": "conditional_share_capital_clause",
                "action": "introduced",
                "decision_date": _iso_date(match.group("date")),
            },
        )], ""

    match = _FR_PROXY_REVOKED_APPOINTED_ADMINISTRATOR_PRESIDENT.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed",
            "fr.persons.proxy_revoked_appointed_administrator_president.v1",
            match.group("name"), place=match.group("place"),
            role=match.group("role").lower(),
            signing="Einzelunterschrift" if match.group("signing") else None,
            extra={
                "action": "appointed_after_proxy_revoked",
                "proxy_revoked": True,
                "domicile_changed": True,
            },
        )], ""

    match = _FR_ASSOCIATE_MANAGER_LIQUIDATORS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.associate_managers_individual_liquidators.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(name_group),
                role="associé gérant liquidateur", signing="Einzelunterschrift",
                extra={"action": "appointed_liquidator", "signing_continues": True},
            )
            for name_group in ("name1", "name2")
        ], ""

    match = _FR_FOUR_COMMITTEE_ROLE_CHANGES.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.four_committee_role_changes.v1"
        names = [match.group(f"name{index}").strip() for index in range(1, 5)]
        events = []
        for index, name in enumerate(names, start=1):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, name,
                role=match.group(f"role{index}").strip(),
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "role_changed",
                    "previous_role": match.group(f"previous_role{index}").strip(),
                    "signing_continues": True,
                    "not_with": [other for other in names if other != name],
                },
            ))
        return events, ""

    match = _DE_EXPIRED_AND_NEW_AUTHORIZED_CAPITAL_TYPO.fullmatch(leftover)
    if match:
        rule_id = "de.text.expired_and_new_authorized_capital_typo.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause",
                    "action": "removed",
                    "reason": "time_limit_expired",
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause",
                    "action": "introduced",
                    "decision_date": _iso_date(match.group("date")),
                    "details_in_statutes": True,
                },
            ),
        ], ""

    match = _DE_COMPANY_ASSET_TRANSFER_WITH_INVENTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.company_asset_transfer_with_inventory.v1", {
                "agreement_date": _iso_date(match.group("date")),
                "inventory_date": _iso_date(match.group("date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"),
                "currency": "CHF",
            },
        )], ""

    match = _FR_FOUNDATION_MEMBER_BECOMES_DIRECTOR.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.foundation_member_becomes_director.v1",
            match.group("name"), role=match.group("role").lower(),
            signing="Einzelunterschrift", extra={
                "action": "role_changed",
                "previous_role": match.group("previous_role").lower(),
                "signing_continues": True,
            },
        )], ""

    match = _DE_ORGANIZATION_BODIES.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.organization_bodies.v1", {
                "action": "organization_recorded",
                "governing_bodies": [
                    "Generalversammlung", "Vorstand", "Revisionsstelle"
                ],
                "minimum_board_members": int(match.group("minimum_board_members")),
            },
        )], ""

    match = _FR_DIRECTOR_GENERAL_BECOMES_DELEGATE_ADMINISTRATOR.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed",
            "fr.persons.director_general_becomes_delegate_administrator.v1",
            match.group("name"), role=match.group("role").lower(), extra={
                "action": "role_changed",
                "previous_role": match.group("previous_role").lower(),
            },
        )], ""

    match = _DE_DELETION_REASON_OMITTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_deleted", "de.text.deletion_reason_omitted_correction.v1", {
                "action": "deleted_after_correction",
                "correction": "deletion_reason_previously_omitted",
                "issue": int(match.group("issue")),
                "notice_date": _iso_date(match.group("notice_date")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _DE_SOLE_PROPRIETOR_ASSET_TRANSFER_TWO_DATES.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred",
            "de.text.sole_proprietor_asset_transfer_two_agreement_dates.v1", {
                "agreement_dates": [
                    _iso_date(match.group("agreement_date1")),
                    _iso_date(match.group("agreement_date2")),
                ],
                "inventory_date": _iso_date(match.group("inventory_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration_kind": "registered_shares_and_claim",
                "share_count": _count(match.group("share_count")),
                "share_nominal": match.group("share_nominal"),
                "share_kind": match.group("share_kind"),
                "paid_percent": int(match.group("paid_percent")),
                "claim": match.group("claim"),
                "currency": "CHF",
            },
        )], ""

    match = _IT_ASSET_ACQUISITION_INTENTION_FORMATION_LIMIT_EXCEEDED.fullmatch(
        leftover
    )
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed",
            "it.text.asset_acquisition_intention_formation_limit_exceeded.v1", {
                "kind": "asset_acquisition_intention_clause",
                "action": "amended_after_limit_exceeded",
                "context": "formation",
                "asset_kind": "real_estate",
                "plot_number": match.group("plot_number"),
                "land_register": "RFD",
                "place": match.group("place").strip(),
                "price": match.group("price"),
                "currency": "CHF",
            },
        )], ""

    match = _DE_AUDIT_WAIVER_ERRONEOUS_BRACKET.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "audit_requirement_changed", "de.text.audit_waiver_erroneous_bracket.v1", {
                "kind": "limited_audit_waiver",
                "action": "erroneous_entry_corrected",
                "limited_audit_waived": False,
            },
        )], ""

    match = _FR_BANKRUPTCY_SUSPENSIVE_EFFECT_DENIED.fullmatch(leftover)
    if match:
        effective_time = (
            f"{int(match.group('effective_hour')):02d}:"
            f"{match.group('effective_minute')}"
        )
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.bankruptcy_suspensive_effect_denied.v1", {
                "kind": "bankruptcy",
                "action": "effective_after_suspensive_effect_denied",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "effective_date": _iso_date(match.group("effective_date")),
                "effective_time": effective_time,
                "suspensive_effect": False,
            },
        )], ""

    match = _FR_STATUTES_ALSO_AMENDED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.statutes_also_amended.v1", {
                "action": "amended",
                "additional_amendment": True,
            },
        )], ""

    return [], leftover
