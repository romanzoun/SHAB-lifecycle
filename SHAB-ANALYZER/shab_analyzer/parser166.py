from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_BOARD_MEMBER_FRAGMENT = re.compile(
    r"^(?P<name>[^,.;]+),\s*(?:de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;()]+?)\s*\((?P<canton>[A-Z]{2})\)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_STATUTES_CHANGED_BY_AUTHORITY = re.compile(
    r"^Par décision du\s+(?P<date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>.+?)\s+a prononcé la modification des statuts\.?$",
    re.I | re.UNICODE,
)
_FR_REINSTATEMENT_WITH_LIQUIDATION_FACTS = re.compile(
    r"^Selon décision du\s+(?P<date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>.+?)\s+a ordonné la réinscription de la société au "
    r"registre du commerce\.\s*Les faits inscrits relatifs au liquidateur et "
    r"à l['’]adresse de liquidation demeurent valables\.?$",
    re.I | re.UNICODE,
)
_DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_WITH_HISTORY = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+die mit Beschluss vom\s+"
    r"(?P<authorization_date>\d{2}\.\d{2}\.\d{4})\s+geänderte Bestimmung "
    r"betreffend bedingter Kapitalerhöhung gemäss näherer Umschreibung in "
    r"den Statuten geändert\.\s*\[bisher:\s*Die Gesellschaft hat mit Beschluss "
    r"vom\s+(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+die mit "
    r"Beschluss vom\s+(?P<introduction_date>\d{2}\.\d{2}\.\d{4})\s+geänderte "
    r"Bestimmung betreffend bedingter Kapitalerhöhung gemäss näherer "
    r"Umschreibung in den Statuten geändert\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_ASSOCIATION_ASSET_TRANSFER_FOR_SHARES = re.compile(
    r"^Vermögensübertragung:\s*Der Verein überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<count>[\d']+)\s+(?P<share_kind>Namenaktien) zu "
    r"CHF\s+(?P<nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_IDENTIFIER_CORRECTED_NO_ARTICLE = re.compile(
    r"^L['’]inscription\s+no\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que le "
    r"numéro IDE de l['’]organe de révision\s+(?P<name>.+?)\s+est\s+"
    r"(?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\s*\(et non pas\s+"
    r"(?P<previous_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_FR_ENTRY_SUPPLEMENT_REFERENCE = re.compile(
    r"^Complément à l['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\)\s*:\s*$",
    re.I | re.UNICODE,
)
_FR_PROXY_REVOKED_APPOINTED_DIRECTOR = re.compile(
    r"^(?P<name>[^,.;]+),\s*dont la procuration est éteinte,\s*est nommé "
    r"directeur et engage désormais la société par sa signature collective "
    r"à deux\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_SHARE_TRANSFER = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à la gérante\s+(?P<buyer>[^,.;]+),\s*"
    r"nouvelle associée avec\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*(?P=seller)\s+reste titulaire de\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_CONDITIONAL_PARTICIPATION_CAPITAL_CLAUSE = re.compile(
    r"^L['’]assemblée générale a introduit une clause statutaire relative à "
    r"une création conditionnelle d['’]un capital-participations par décision du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*pour les détails,\s*voir les statuts\.?$",
    re.I | re.UNICODE,
)
_FR_CORPORATE_ASSOCIATE_RENAMED_RELOCATED_NUMERIC_ID = re.compile(
    r"^L['’]associée\s+(?P<previous_name>.+?)\s+qui a modifié sa raison "
    r"sociale en\s+(?P<name>.+?)\s*\((?P<registry_id>\d+)\),\s*est "
    r"maintenant à\s+(?P<place>[^()]+?)\s*\((?P<country>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_GROUP_SIGNING_CORRECTED = re.compile(
    r"^L['’]inscription\s+no\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<names>.+?)\s+signent en réalité collectivement à deux pour "
    r"l['’]établissement principal\s*\(et non pas par procuration\)\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBERS_WITHOUT_SIGNATURE = re.compile(
    r"^(?P<members>.+?),\s*sont membres du conseil d['’]administration sans "
    r"signature\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBER_ITEM = re.compile(
    r"(?:,\s*)?(?:et\s+)?(?P<name>[^,]+),\s*"
    r"(?:(?:de et à)\s+(?P<same_place>[^,]+)|"
    r"(?:(?:de la|de l['’]|du|des|de|d['’])\s*)"
    r"(?P<origin>[^,]+),\s*à\s+(?P<place>[^,]+))",
    re.I | re.UNICODE,
)
_FR_ASSOCIATION_DISSOLUTION_COMMITTEE_LIQUIDATORS = re.compile(
    r"^L['’]association est dissoute par décision de l['’]assemblée générale du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.\s*Liquidateurs:\s*les membres du "
    r"comité\s+(?P<name1>[^,.;]+?)\s+et\s+(?P<name2>[^,.;]+?)\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_BUYER_MANAGER_SELLER_PRESIDENT = re.compile(
    r"^(?P<seller>[^,.;]+)\s+a cédé\s+(?P<transferred>[\d']+)\s+parts de "
    r"CHF\s+(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"lequel associé est en outre nommé gérant\s+(?P=seller),\s*nommé "
    r"président,\s*est désormais titulaire de\s+(?P<seller_count>[\d']+)\s+"
    r"parts de CHF\s+(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_CLAUSE_CHANGED = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+die mit Beschluss vom\s+"
    r"(?P<introduction_date>\d{2}\.\d{2}\.\d{4})\s+eingeführte genehmigte "
    r"Kapitalerhöhung gemäss näherer Umschreibung in den Statuten geändert\.?$",
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
    uid: str | None = None,
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
        person_key=person_key(name=clean_name, place=clean_place, uid=uid),
        plz=plz,
        canton=canton,
        role=role,
        signing=signing,
        payload={
            "name": clean_name,
            "place": clean_place,
            **({"uid": uid} if uid else {}),
            **(extra or {}),
        },
    )


def _french_board_members(raw: str) -> list[dict[str, str]] | None:
    members: list[dict[str, str]] = []
    position = 0
    while position < len(raw):
        match = _FR_BOARD_MEMBER_ITEM.match(raw, position)
        if not match:
            return None
        same_place = match.group("same_place")
        members.append({
            "name": match.group("name").strip(),
            "origin": (same_place or match.group("origin")).strip(),
            "place": (same_place or match.group("place")).strip(),
        })
        position = match.end()
    return members if len(members) >= 2 else None


def _french_names(raw: str) -> list[str]:
    return [
        name.strip()
        for name in re.split(r",\s*|\s+et\s+", raw, flags=re.I)
        if name.strip()
    ]


def extract_parser166_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 166."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()
    events: list[Event] = []

    match = _FR_BOARD_MEMBER_FRAGMENT.fullmatch(leftover)
    if match:
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.board_member_fragment.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil d'administration",
            signing="Einzelunterschrift", extra={
                "action": "appointed", "origin": match.group("origin").strip(),
                "place_canton": match.group("canton").upper(),
            },
        ))
        return events, ""

    match = _FR_FOUNDATION_STATUTES_CHANGED_BY_AUTHORITY.fullmatch(leftover)
    if match:
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.foundation_statutes_changed_by_authority.v1",
            {
                "kind": "foundation_statutes", "action": "modified",
                "decision_date": _iso_date(match.group("date")),
                "authority": match.group("authority").strip(),
                "non_public_points": True,
            },
        ))
        return events, ""

    match = _FR_REINSTATEMENT_WITH_LIQUIDATION_FACTS.fullmatch(leftover)
    if match:
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.reinstatement_liquidation_facts_valid.v1",
            {
                "kind": "company_reinstated", "action": "reinstatement_ordered",
                "decision_date": _iso_date(match.group("date")),
                "authority": match.group("authority").strip(),
                "liquidator_facts_remain_valid": True,
                "liquidation_address_remains_valid": True,
            },
        ))
        return events, ""

    match = _DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_WITH_HISTORY.fullmatch(leftover)
    if match:
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.conditional_capital_clause_changed_history.v1",
            {
                "kind": "conditional_capital_clause", "action": "modified",
                "decision_date": _iso_date(match.group("decision_date")),
                "authorization_date": _iso_date(match.group("authorization_date")),
                "previous_decision_date": _iso_date(
                    match.group("previous_decision_date")
                ),
                "introduction_date": _iso_date(match.group("introduction_date")),
                "details_in_statutes": True,
            },
        ))
        return events, ""

    match = _DE_ASSOCIATION_ASSET_TRANSFER_FOR_SHARES.fullmatch(leftover)
    if match:
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.association_asset_transfer_for_shares.v1",
            {
                "source_kind": "association",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": {
                    "kind": match.group("share_kind"),
                    "count": _count(match.group("count")),
                    "nominal": match.group("nominal"), "currency": "CHF",
                },
            },
        ))
        return events, ""

    match = _FR_AUDITOR_IDENTIFIER_CORRECTED_NO_ARTICLE.fullmatch(leftover)
    if match:
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.auditor_identifier_corrected_no_article.v1",
            match.group("name"), uid=match.group("uid"), role="organe de révision",
            extra={
                "action": "identifier_corrected",
                "previous_uid": match.group("previous_uid"),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))
        return events, ""

    match = _FR_ENTRY_SUPPLEMENT_REFERENCE.fullmatch(leftover)
    if match:
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.entry_supplement_reference.v1",
            {
                "kind": "registry_entry_supplement", "action": "supplemented",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        ))
        return events, ""

    match = _FR_PROXY_REVOKED_APPOINTED_DIRECTOR.fullmatch(leftover)
    if match:
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.proxy_revoked_appointed_director.v1",
            match.group("name"), role="directeur",
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "appointed_and_signing_changed",
                "previous_signing": "procuration", "previous_signing_revoked": True,
            },
        ))
        return events, ""

    match = _FR_MANAGER_SHARE_TRANSFER.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.manager_share_transfer.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller"),
                role="associé-gérant", extra={
                    "action": "shares_transferred",
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("seller_nominal"),
                    "currency": "CHF", "counterparty": match.group("buyer").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"),
                role="associée-gérante", extra={
                    "action": "shares_received", "new_associate": True,
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"),
                    "currency": "CHF", "counterparty": match.group("seller").strip(),
                },
            ),
        ])
        return events, ""

    match = _FR_CONDITIONAL_PARTICIPATION_CAPITAL_CLAUSE.fullmatch(leftover)
    if match:
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.conditional_participation_capital_clause.v1",
            {
                "kind": "conditional_participation_capital_clause",
                "action": "introduced",
                "decision_date": _iso_date(match.group("date")),
                "details_in_statutes": True,
            },
        ))
        return events, ""

    match = _FR_CORPORATE_ASSOCIATE_RENAMED_RELOCATED_NUMERIC_ID.fullmatch(leftover)
    if match:
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed",
            "fr.persons.corporate_associate_renamed_relocated_numeric_id.v1",
            match.group("name"), place=match.group("place"), role="associée",
            extra={
                "action": "name_and_domicile_changed",
                "previous_name": match.group("previous_name").strip(),
                "registry_id": match.group("registry_id"),
                "country": match.group("country").strip(),
            },
        ))
        return events, ""

    match = _FR_GROUP_SIGNING_CORRECTED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.group_signing_corrected.v1"
        reference = {
            "action": "signing_corrected",
            "previous_signing": "procuration",
            "scope": "établissement principal",
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_ref": match.group("notice_ref"),
        }
        for name in _french_names(match.group("names")):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, name,
                signing="Kollektivunterschrift zu zweien", extra=reference,
            ))
        return events, ""

    match = _FR_BOARD_MEMBERS_WITHOUT_SIGNATURE.fullmatch(leftover)
    if match:
        members = _french_board_members(match.group("members"))
        if members:
            rule_id = "fr.persons.board_members_without_signature.v1"
            for member in members:
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, member["name"],
                    place=member["place"], role="membre du conseil d'administration",
                    extra={
                        "action": "appointed", "origin": member["origin"],
                        "without_signature": True,
                    },
                ))
            return events, ""

    match = _FR_ASSOCIATION_DISSOLUTION_COMMITTEE_LIQUIDATORS.fullmatch(leftover)
    if match:
        rule_id = "fr.text.association_dissolution_committee_liquidators.v1"
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", rule_id,
            {
                "kind": "dissolution", "scope": "association",
                "action": "dissolved", "date": _iso_date(match.group("date")),
                "authority": "assemblée générale",
            },
        ))
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="liquidateur", signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed_liquidator",
                    "previous_role": "membre du comité",
                },
            ))
        return events, ""

    match = _FR_SHARE_TRANSFER_BUYER_MANAGER_SELLER_PRESIDENT.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.share_transfer_buyer_manager_seller_president.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"),
                place=match.group("place"), role="associé-gérant",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_and_shares_received",
                    "origin": match.group("origin").strip(), "new_associate": True,
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                    "counterparty": match.group("seller").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller"),
                role="associé-gérant président",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_president_and_shares_transferred",
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("seller_nominal"), "currency": "CHF",
                    "counterparty": match.group("buyer").strip(),
                },
            ),
        ])
        return events, ""

    match = _DE_AUTHORIZED_CAPITAL_CLAUSE_CHANGED.fullmatch(leftover)
    if match:
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_clause_changed.v1",
            {
                "kind": "authorized_capital_clause", "action": "modified",
                "decision_date": _iso_date(match.group("decision_date")),
                "introduction_date": _iso_date(match.group("introduction_date")),
                "details_in_statutes": True,
            },
        ))
        return events, ""

    return [], text
