from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_DELETION_PROCEDURE_BLOCKED_CANTONAL_TAX = re.compile(
    r"^Auf die durch das Handelsregisteramt gestützt auf (?P<legal_basis>Art\.\s*934 "
    r"Abs\.\s*2 OR sowie Art\.\s*152 Abs\.\s*1 HRegV) veranlasste und im SHAB "
    r"mit Meldungsnummer (?P<issue>[A-Z0-9-]+) publizierte Aufforderung haben sich "
    r"keine weiteren Betroffenen gemeldet\.\s*Das amtliche Verfahren zur Löschung "
    r"der Rechtseinheit ist damit abgeschlossen\.\s*Sie kann mangels Zustimmung des "
    r"kantonalen Steueramtes jedoch noch nicht gelöscht werden\.?$",
    re.I | re.UNICODE,
)
_FR_ANCILLARY_OBLIGATIONS_NEGATED = re.compile(
    r"^\[non:\s*Obligations de fournir des prestations accessoires,\s*droits de "
    r"préférence,\s*de préemption ou d['’]emption:\s*(?P<reference>pour les détails,\s*"
    r"voir les statuts)\.?\]\.?$",
    re.I | re.UNICODE,
)
_DE_ASSOCIATION_ASSET_TRANSFER_NO_CONSIDERATION = re.compile(
    r"^Vermögensübertragung:\s*Der (?P<source_kind>Verein) überträgt gemäss Vertrag "
    r"vom (?P<date>\d{2}\.\d{2}\.\d{4}) Aktiven von CHF (?P<assets>[\d'.]+) "
    r"und Passiven \(Fremdkapital\) von CHF (?P<liabilities>[\d'.]+) auf die "
    r"(?P<recipient>.+?),\s*in (?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*Gegenleistung:\s*keine\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_IDENTIFIER_REPLACED = re.compile(
    r"^Succursale:\s*(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s*"
    r"\[précédemment:\s*(?P<previous_place>[^()]+?)\s*"
    r"\((?P<previous_id>CH-[\d.-]+)\)\]\.?$",
    re.I | re.UNICODE,
)
_DE_REFERENCED_SOLE_PROPRIETOR_DELETION_REVOKED = re.compile(
    r"^Die Löschung des Einzelunternehmens unter der TR Nr\.\s*(?P<entry>[\d']+) "
    r"vom (?P<entry_date>\d{2}\.\d{2}\.\d{4}),\s*SHAB Nr\.\s*(?P<issue>\d+) "
    r"vom (?P<notice_date>\d{2}\.\d{2}\.\d{4}) erfolgte irrtümlich und wird "
    r"hiermit in allen Teilen widerrufen\.?$",
    re.I | re.UNICODE,
)
_FR_SOCIAL_SHARE_SPLIT_FOR_MANAGER = re.compile(
    r"^Division de la part sociale de CHF (?P<from_nominal>[\d'.]+) de "
    r"l['’]associé-gérant (?P<name>[^,.;]+) en (?P<count>[\d']+) parts de CHF "
    r"(?P<to_nominal>\d[\d']*(?:\.\d+)?)\.?(?:\s*\))?$",
    re.I | re.UNICODE,
)
_FR_PERSON_FULL_NAME_EXTENDED = re.compile(
    r"^(?P<previous_name>[^,.;]+) porte désormais le nom complet de "
    r"(?P<name>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_SIGNING_RESTRICTIONS_CONTINUE = re.compile(
    r"^(?P<name1>[^,.;]+) continue à signer collectivement à deux,\s*désormais "
    r"avec un administrateur\.\s*(?P<name2>[^,.;]+),\s*maintenant à "
    r"(?P<place2>[^,.;]+),\s*continue à engager la société par sa procuration "
    r"collective à deux,\s*désormais avec un administrateur\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_MENTION_REMOVED = re.compile(
    r"^Radiation de la mention de l['’]existence d['’]une succursale à "
    r"(?P<place>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_OUTBOUND_CROSS_BORDER_MERGER = re.compile(
    r"^Aktiven und Passiven \(Fremdkapital\) der Gesellschaft gehen infolge "
    r"grenzüberschreitender Fusion gemäss Fusionsvertrag vom "
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4}) und Bilanz per "
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4}) auf die (?P<successor>.+?) in "
    r"(?P<place>[^()]+?)\s*\((?P<country>[A-Z]{2})\)\s*"
    r"\((?P<registry_id>[^)]+)\),\s*nach dem Recht des Staates "
    r"(?P<jurisdiction>[^,.;]+),\s*über\.\s*Die Gläubigerschutzvorschriften "
    r"wurden beachtet\.\s*Die Gesellschaft wird gelöscht\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_ADMINISTRATOR_CONTINUES = re.compile(
    r"^(?P<name>[^,.;]+),\s*maintenant domicilié à (?P<place>[^,.;]+),\s*"
    r"jusqu['’]ici président,\s*reste seul administrateur et continue à signer "
    r"individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_TRADE_NAME_CHANGED = re.compile(
    r"^L['’]organe de révision (?P<previous_name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\) a modifié de raison de commerce en "
    r"(?P<name>.+?)\s*\((?P=uid)\)\.?$",
    re.I | re.UNICODE,
)
_IT_LIQUIDATION_ENDED_DELETION_BLOCKED_CANTONAL = re.compile(
    r"^La liquidazione è terminata\.\s*Ma la cancellazione anticipata con "
    r"conferma di un perito revisore abilitato del "
    r"(?P<confirmation_date>\d{2}\.\d{2}\.\d{4}) non può ancora essere "
    r"effettuata mancando il consenso dell['’]autorità fiscale cantonale\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_TO_NEW_MANAGER_FRAGMENT = re.compile(
    r"^(?P<seller>[^,.;]+),\s*associé-gérant,\s*cède (?P<transferred>[\d']+) "
    r"de ses (?P<before>[\d']+) parts de CHF (?P<nominal>[\d'.]+) à "
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à (?P<place>[^,.;]+),\s*nouvelle associée avec "
    r"(?P<buyer_count>[\d']+) parts de CHF (?P<buyer_nominal>[\d'.]+),\s*"
    r"gérante\s+(?P=seller),\s*lequel est élu président,\s*reste titulaire de "
    r"(?P<remaining>[\d']+) parts de CHF "
    r"(?P<remaining_nominal>\d[\d']*(?:\.\d+)?)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_CLAUSE_CHANGED_MISSING_SPACE = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom (?P<decision_date>\d{2}\.\d{2}\.\d{4})"
    r"die Bestimmung über genehmigtes Kapital vom "
    r"(?P<authorization_date>\d{2}\.\d{2}\.\d{4}) gemäss näherer Umschreibung in "
    r"den Statuten geändert\.?$",
    re.I | re.UNICODE,
)
_FR_LIQUIDATOR_AND_SHARE_RESTRICTION_REMOVED_FRAGMENT = re.compile(
    r"^par (?P<name>[^,.;]+),\s*de et à (?P<place>[^,.;]+),\s*élu liquidateur "
    r"Les (?P<count>[\d']+) actions nominatives de CHF (?P<nominal>[\d'.]+),\s*"
    r"formant la totalité du capital-actions,\s*ne sont désormais plus restreintes "
    r"quant à la transmissibilité \((?P<legal_basis>art\.\s*685a,\s*al\.\s*3 CO)\)\.?$",
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
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser137_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 137."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_DELETION_PROCEDURE_BLOCKED_CANTONAL_TAX.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.deletion_procedure_blocked_cantonal_tax.v1",
            {
                "kind": "deletion_blocked", "procedure_completed": True,
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "issues": [match.group("issue")], "affected_parties_responded": False,
                "tax_authority_consent_missing": True,
                "missing_consents": ["cantonal_tax_authority"],
            },
        ))

    match = _FR_ANCILLARY_OBLIGATIONS_NEGATED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.ancillary_obligations_negated_no_period.v1",
            {
                "kind": "ancillary_obligations", "action": "correction_negated",
                "statutes_reference": match.group("reference").strip(),
            },
        ))

    match = _DE_ASSOCIATION_ASSET_TRANSFER_NO_CONSIDERATION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.association_asset_transfer_no_consideration.v1",
            {
                "source_kind": match.group("source_kind").lower(),
                "date": _iso_date(match.group("date")), "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"), "consideration": None,
            },
        ))

    match = _FR_BRANCH_IDENTIFIER_REPLACED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "fr.text.branch_identifier_replaced.v1",
            {
                "action": "identifier_replaced", "place": match.group("place").strip(),
                "branch_uid": match.group("uid"),
                "previous_place": match.group("previous_place").strip(),
                "previous_branch_id": match.group("previous_id"),
            },
        ))

    match = _DE_REFERENCED_SOLE_PROPRIETOR_DELETION_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.referenced_sole_proprietor_deletion_revoked.v1",
            {
                "kind": "registration_reinstated", "action": "deletion_revoked",
                "scope": "sole_proprietor", "reason": "erroneous_deletion",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "issue": match.group("issue"),
                "notice_date": _iso_date(match.group("notice_date")),
                "registry_reinstated": True,
            },
        ))

    match = _FR_SOCIAL_SHARE_SPLIT_FOR_MANAGER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.social_share_split_for_manager.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "kind": "social_share_split", "action": "split", "currency": "CHF",
                    "from_count": 1, "from_nominal": match.group("from_nominal"),
                    "to_count": _count(match.group("count")),
                    "to_nominal": match.group("to_nominal"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"), role="associé-gérant",
                extra={
                    "action": "share_structure_changed",
                    "shares_count": _count(match.group("count")),
                    "share_nominal": match.group("to_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _FR_PERSON_FULL_NAME_EXTENDED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.full_name_extended.v1", match.group("name"),
            extra={
                "action": "name_changed",
                "previous_name": match.group("previous_name").strip(),
            },
        ))

    match = _FR_TWO_SIGNING_RESTRICTIONS_CONTINUE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_signing_restrictions_continue.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name1"),
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "restriction_changed", "signing_continues": True,
                    "signing_with_role": "administrateur",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name2"),
                place=match.group("place2"), signing="Kollektivprokura zu zweien",
                extra={
                    "action": "domicile_and_restriction_changed",
                    "signing_continues": True, "signing_with_role": "administrateur",
                },
            ),
        ])

    match = _FR_BRANCH_MENTION_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "fr.text.branch_mention_removed.v1",
            {"action": "removed", "place": match.group("place").strip()},
        ))

    match = _DE_OUTBOUND_CROSS_BORDER_MERGER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "de.text.outbound_cross_border_merger.v1",
            {
                "kind": "cross_border_merger", "direction": "outbound",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "successor_name": match.group("successor").strip(),
                "successor_place": match.group("place").strip(),
                "successor_country": match.group("country"),
                "successor_registry_id": match.group("registry_id").strip(),
                "successor_jurisdiction": match.group("jurisdiction").strip(),
                "creditor_protection_observed": True, "company_deleted": True,
            },
        ))

    match = _FR_SOLE_ADMINISTRATOR_CONTINUES.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.sole_administrator_continues.v1",
            match.group("name"), place=match.group("place"),
            role="seul administrateur", signing="Einzelunterschrift",
            extra={
                "action": "role_and_domicile_changed", "previous_role": "président",
                "signing_continues": True,
            },
        ))

    match = _FR_AUDITOR_TRADE_NAME_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.auditor_trade_name_changed_same_uid.v1",
            match.group("name"), uid=match.group("uid"), role="organe de révision",
            extra={
                "action": "registered_name_changed",
                "previous_name": match.group("previous_name").strip(),
                "uid": match.group("uid"), "previous_uid": match.group("uid"),
            },
        ))

    match = _IT_LIQUIDATION_ENDED_DELETION_BLOCKED_CANTONAL.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.liquidation_ended_deletion_blocked_cantonal.v1",
            {
                "kind": "liquidation_ended", "deletion_blocked": True,
                "requested_early_deletion": True,
                "audit_expert_confirmation_date": _iso_date(match.group("confirmation_date")),
                "deletion_blocked_reason": "cantonal_tax_authority_consent_missing",
            },
        ))

    match = _FR_MANAGER_TRANSFER_TO_NEW_MANAGER_FRAGMENT.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_transfer_to_new_manager_fragment.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant président",
                extra={
                    "action": "appointed_president_and_shares_transferred",
                    "counterparty": buyer,
                    "previous_shares_count": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("remaining_nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée-gérante", signing="Einzelunterschrift",
                extra={
                    "action": "appointed_and_shares_received", "counterparty": seller,
                    "origin": match.group("origin").strip(), "new_associate": True,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _DE_AUTHORIZED_CAPITAL_CLAUSE_CHANGED_MISSING_SPACE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_clause_changed_missing_space.v1",
            {
                "kind": "authorized_capital_clause", "action": "modified",
                "decision_date": _iso_date(match.group("decision_date")),
                "authorization_date": _iso_date(match.group("authorization_date")),
                "details_in_statutes": True,
            },
        ))

    match = _FR_LIQUIDATOR_AND_SHARE_RESTRICTION_REMOVED_FRAGMENT.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.liquidator_and_share_restriction_removed_fragment.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), role="liquidateur",
                signing="Einzelunterschrift", extra={"action": "appointed"},
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "kind": "share_transfer_restriction", "action": "removed",
                    "shares_count": _count(match.group("count")),
                    "share_kind": "actions nominatives",
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                    "entire_share_capital": True,
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                },
            ),
        ])

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
