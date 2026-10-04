from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_FOUNDATION_TRANSFER_TWO_CREDITS = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+et selon décision de "
    r"l['’]autorité de surveillance du\s+"
    r"(?P<approval_date>\d{2}\.\d{2}\.\d{4}),\s*la fondation a transféré "
    r"des actifs de CHF\s+(?P<assets>[\d'.]+)\s+et des passifs envers les "
    r"tiers de CHF\s+(?P<liabilities>[\d'.]+)\s+à\s+(?P<recipient>.+?),\s*"
    r"à\s+(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*une créance de CHF\s+(?P<credit1>[\d'.]+)\s+et "
    r"une créance de CHF\s+(?P<credit2>[\d'.]+)(?:\s+CHF)?\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_CHANGED_BY_ASSEMBLY = re.compile(
    r"^Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+die mit Beschluss vom\s+"
    r"(?P<authorization_date>\d{2}\.\d{2}\.\d{4})\s+eingeführte "
    r"genehmigte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten "
    r"geändert\.?$",
    re.I | re.UNICODE,
)
_FR_CONTRIBUTION_IN_KIND_VALUE_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée comme suit:\s*"
    r"Apport en nature selon contrat du\s+(?P<agreement_date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4}):\s*(?P<asset_count>[\d']+)\s+"
    r"(?P<asset_kind>actions au porteur) de CHF\s+(?P<asset_nominal>[\d'.]+)\s+"
    r"de la société\s+(?P<source>.+?)\s*"
    r"\((?P<source_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<source_place>[^,.;]+),\s*pour CHF\s+(?P<value>[\d'.]+)\s*"
    r"\(et non pour CHF\s+(?P<previous_value>[\d'.]+),\s*comme publié\);\s*"
    r"en contrepartie,\s*(?:il\s+)?est remis\s+(?P<share_count>[\d']+)\s+"
    r"(?P<share_kind>actions nominatives) de CHF\s+"
    r"(?P<share_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FIRST_NAME_CORRECTED_WITH_REFERENCE = re.compile(
    r"^L['’]inscription\s+(?:No|no|n°)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})"
    r"(?:\s*\(FOSC du\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s*"
    r"p\.\s*(?P<notice_ref>[\d/]+)\))?\s+est rectifiée en ce sens que\s+"
    r"(?P<subject>.+?)\s+se prénomme(?:\s+en réalité)?\s+"
    r"(?P<first_name>[^.;()]+?)"
    r"(?:\s*\(et non pas\s+(?P<previous_first_name>[^)]+)\))?\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_NAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:No|no|n°)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<previous_name>.+?)\s+porte en réalité le nom de\s+"
    r"(?P<name>.+?)\.?$",
    re.I | re.UNICODE,
)
_IT_ORGANIZATION_DISCLOSURE_REMOVED = re.compile(
    r"^Nuova organizzazione:\s*\[Nuova organizzazione:\s*"
    r"(?P<previous>[^\]]+?)\]\s*\[L['’]indicazione relativa "
    r"all['’]organizzazione è cancellata a seguito dell['’]abrogazione della "
    r"disposizione di cui all['’](?P<legal_basis>art\s+art\.\s*92\s+lett\s+j\s+ORC)"
    r"\]\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDER_CONTRIBUTION_UNPAID = re.compile(
    r"^Der Gründer hat,\s*wie sich nachträglich herausgestellt hat,\s*seine "
    r"anlässlich der Gründung bedingungslos versprochene Leistung der Einlagen "
    r"auf die von ihm gezeichneten Stammanteile nicht erfüllt,\s*womit das "
    r"Stammkapital nicht liberiert worden ist\.?$",
    re.I | re.UNICODE,
)
_DE_THIRD_BRANCH_AFTER_REGISTER_FRAGMENT = re.compile(
    r"^\(HR\s+(?P<previous_register>[A-Z]{2})\)\.\s*"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"\(HR\s+(?P<register>[A-Z]{2})\)\.?$",
    re.I | re.UNICODE,
)
_DE_SOLE_PROPRIETOR_ORIGIN_CHANGED = re.compile(
    r"^Eingetragene Person geändert:\s*(?P<name>[^,.;]+),\s*"
    r"(?P<role>Inhaberin|Inhaber),\s*"
    r"(?P<signing>Einzelunterschrift),\s*neu von\s+"
    r"(?P<origin>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_PROPRIETOR_ASSET_TRANSFER = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<agreement_date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4}),\s*le titulaire a transféré des actifs "
    r"pour CHF\s+(?P<assets>[\d'.]+)\s+et des passifs envers les tiers pour "
    r"CHF\s+(?P<liabilities>[\d'.]+),\s*à\s+(?P<recipient>.+?)\s+à\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*(?P<share_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<share_nominal>[\d'.]+)\s+et une créance de CHF\s+"
    r"(?P<credit>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_TRANSFER_TWO_DATES_SHARES = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat des\s+"
    r"(?P<agreement_date1>\d{2}\.\d{2}\.\d{4})\s+et\s+"
    r"(?P<agreement_date2>\d{2}\.\d{2}\.\d{4})\s+et selon décision de "
    r"l['’]autorité de surveillance du\s+"
    r"(?P<approval_date>\d{2}\.\d{2}\.\d{4}),\s*la fondation a transféré "
    r"des actifs de CHF\s+(?P<assets>[\d'.]+)\s+et des passifs envers les "
    r"tiers de CHF\s+(?P<liabilities>[\d'.]+),\s*soit un actif net de CHF\s+"
    r"(?P<net_assets>[\d'.]+)\s+à la société anonyme\s+(?P<recipient>.+?),\s*"
    r"à\s+(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation[.:]\s*(?P<share_count>[\d']+)\s+"
    r"(?P<share_kind>actions nominatives) de CHF\s+"
    r"(?P<share_nominal>[\d'.]+),\s*(?P<paid>entièrement libérées)\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDATION_ORGANIZATION = re.compile(
    r"^Organisation neu:\s*\[Organisation:\s*Stiftungsrat von\s+"
    r"(?P<minimum>\d+)\s+bis\s+(?P<maximum>\d+)\s+Mitgliedern und "
    r"(?P<auditor>Kontrollstelle)\]\.?$",
    re.I | re.UNICODE,
)
_FR_FOUR_PROCURATIONS_WITH_DEPUTY_DIRECTOR = re.compile(
    r"^Procuration collective à deux,\s*avec un directeur-adjoint,\s*"
    r"a été conférée à\s+(?P<name1>.+?),\s*(?P<name2>[^,;]+),\s*"
    r"(?P<name3>[^,;]+)\s+et\s+(?P<name4>[^;]+);\s*"
    r"leurs pouvoirs sont modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_PRESIDENCY_CHANGED = re.compile(
    r"^Les associés gérants\s+(?P<new_president>[^,.;]+),\s*nommé président "
    r"et\s+(?P<previous_president>[^,.;]+),\s*jusqu['’]ici président,\s*"
    r"continuent à signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_DE_COOPERATIVE_PERSONAL_LIABILITY_REMOVED = re.compile(
    r"^Haftung/Nachschusspflicht neu:\s*"
    r"\[Die persönliche Haftung wurde aus den Statuten entfernt\.\]\s*"
    r"\[gestrichen:\s*Haftung/Nachschusspflicht:\s*"
    r"(?P<previous>Persönliche und solidarische,\s*subsidiäre Haftbarkeit der "
    r"Genossenschafter)\.\]\.?$",
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
    day, month, year = raw.lower().split()
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
    role: str | None = None,
    signing: str | None = None,
    extra: dict | None = None,
) -> Event:
    clean_name = name.strip()
    return Event(
        publication_id=publication_id,
        published_at=published_at,
        event_type=event_type,
        rule_id=rule_id,
        org_uid=org_uid,
        person_key=person_key(name=clean_name),
        plz=plz,
        canton=canton,
        role=role,
        signing=signing,
        payload={"name": clean_name, "place": None, **(extra or {})},
    )


def extract_parser164_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 164."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_FOUNDATION_TRANSFER_TWO_CREDITS.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.foundation_transfer_two_credits.v1",
            {
                "source_kind": "foundation",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "supervisory_approval_date": _iso_date(match.group("approval_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities",
                "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration_claims": [
                    {"amount": match.group("credit1"), "currency": "CHF"},
                    {"amount": match.group("credit2"), "currency": "CHF"},
                ],
            },
        ))

    match = _DE_AUTHORIZED_CAPITAL_CHANGED_BY_ASSEMBLY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_changed_by_assembly.v1",
            {
                "kind": "authorized_capital_clause", "action": "modified",
                "decision_date": _iso_date(match.group("decision_date")),
                "authorization_date": _iso_date(match.group("authorization_date")),
                "details_in_statutes": True,
            },
        ))

    match = _FR_CONTRIBUTION_IN_KIND_VALUE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.contribution_in_kind_value_corrected.v1",
            {
                "kind": "contribution_in_kind", "action": "value_corrected",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
                "agreement_date": _french_date(match.group("agreement_date")),
                "contributed_assets": {
                    "count": _count(match.group("asset_count")),
                    "kind": match.group("asset_kind").lower(),
                    "nominal": match.group("asset_nominal"),
                    "currency": "CHF",
                    "issuer": match.group("source").strip(),
                    "issuer_uid": match.group("source_uid"),
                    "issuer_place": match.group("source_place").strip(),
                },
                "value": match.group("value"),
                "previous_incorrect_value": match.group("previous_value"),
                "consideration_shares": {
                    "count": _count(match.group("share_count")),
                    "kind": match.group("share_kind").lower(),
                    "nominal": match.group("share_nominal"),
                    "currency": "CHF",
                },
            },
        ))

    match = _FR_FIRST_NAME_CORRECTED_WITH_REFERENCE.search(leftover)
    if match:
        consume(match)
        subject = re.sub(
            r"^l['’](?:administrateur|administratrice)\s+", "",
            match.group("subject").strip(), flags=re.I,
        )
        first_name = match.group("first_name").strip()
        first_token = first_name.split()[0]
        if subject.casefold().endswith(first_token.casefold()):
            subject = subject[:-len(first_token)].rstrip()
        name = f"{subject} {first_name}".strip()
        payload = {
            "action": "first_name_corrected",
            "first_name": first_name,
            "previous_identity": match.group("subject").strip(),
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
        }
        if match.group("previous_first_name"):
            payload["previous_first_name"] = match.group("previous_first_name").strip()
        if match.group("notice_date"):
            payload["notice_date"] = _iso_date(match.group("notice_date"))
            payload["notice_ref"] = match.group("notice_ref")
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.first_name_corrected_with_reference.v1",
            name, role=(
                "administratrice"
                if re.match(r"^l['’]administratrice\b", match.group("subject"), re.I)
                else None
            ), extra=payload,
        ))

    match = _FR_PERSON_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.name_corrected_with_reference.v1",
            match.group("name"), extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _IT_ORGANIZATION_DISCLOSURE_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "it.text.organization_disclosure_removed_art92.v1",
            {
                "kind": "organization_disclosure", "action": "removed",
                "previous": match.group("previous").strip(),
                "reason": "legal_provision_repealed",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")).strip(),
            },
        ))

    match = _DE_FOUNDER_CONTRIBUTION_UNPAID.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.founder_contribution_unpaid.v1",
            {
                "kind": "capital_payment", "action": "corrected_to_unpaid",
                "capital_paid": False, "share_kind": "Stammanteile",
                "reason": "founder_contribution_not_fulfilled",
            },
        ))

    match = _DE_THIRD_BRANCH_AFTER_REGISTER_FRAGMENT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.third_branch_after_register_fragment.v1",
            {
                "action": "added", "place": match.group("place").strip(),
                "branch_uid": match.group("uid"),
                "register_canton": match.group("register").upper(),
                "previous_branch_register_canton": match.group("previous_register").upper(),
            },
        ))

    match = _DE_SOLE_PROPRIETOR_ORIGIN_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.sole_proprietor_origin_changed.v1",
            match.group("name"), role=match.group("role"),
            signing=match.group("signing"), extra={
                "action": "origin_changed", "origin": match.group("origin").strip(),
            },
        ))

    match = _FR_SOLE_PROPRIETOR_ASSET_TRANSFER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.sole_proprietor_asset_transfer.v1",
            {
                "source_kind": "sole_proprietor",
                "agreement_date": _french_date(match.group("agreement_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration_shares": {
                    "count": _count(match.group("share_count")),
                    "nominal": match.group("share_nominal"),
                    "currency": "CHF", "kind": "parts sociales",
                },
                "consideration_credit": match.group("credit"),
            },
        ))

    match = _FR_FOUNDATION_TRANSFER_TWO_DATES_SHARES.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.foundation_transfer_two_dates_shares.v1",
            {
                "source_kind": "foundation",
                "agreement_dates": [
                    _iso_date(match.group("agreement_date1")),
                    _iso_date(match.group("agreement_date2")),
                ],
                "supervisory_approval_date": _iso_date(match.group("approval_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "net_assets": match.group("net_assets"),
                "liabilities_kind": "third_party_liabilities", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration_shares": {
                    "count": _count(match.group("share_count")),
                    "kind": match.group("share_kind").lower(),
                    "nominal": match.group("share_nominal"),
                    "currency": "CHF", "paid_in_full": True,
                },
            },
        ))

    match = _DE_FOUNDATION_ORGANIZATION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.foundation_organization_recorded.v1",
            {
                "kind": "foundation_organization", "action": "recorded",
                "foundation_board": {
                    "minimum_members": int(match.group("minimum")),
                    "maximum_members": int(match.group("maximum")),
                },
                "audit_body": match.group("auditor"),
            },
        ))

    match = _FR_FOUR_PROCURATIONS_WITH_DEPUTY_DIRECTOR.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.four_procurations_with_deputy_director.v1"
        for index in range(1, 5):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                signing="Kollektivprokura zu zweien", extra={
                    "action": "procuration_changed",
                    "co_signs_with_role": "directeur-adjoint",
                    "previous_power_modified": True,
                },
            ))

    match = _FR_TWO_MANAGERS_PRESIDENCY_CHANGED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_managers_presidency_changed.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("new_president"),
                role="associé-gérant président",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed_president", "signing_continues": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("previous_president"),
                role="associé-gérant", signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "presidency_ended", "previous_role": "président",
                    "signing_continues": True,
                },
            ),
        ])

    match = _DE_COOPERATIVE_PERSONAL_LIABILITY_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "liability_changed", "de.text.cooperative_personal_liability_removed.v1",
            {
                "kind": "member_personal_liability", "action": "removed",
                "personal_liability": False,
                "previous": match.group("previous").strip(),
            },
        ))

    if not events:
        # This parser runs before historical fallback parsers so full correction
        # notices remain intact. Preserve punctuation their anchored rules need.
        return [], text
    return events, re.sub(r"\s+", " ", leftover).strip(" .,;")
