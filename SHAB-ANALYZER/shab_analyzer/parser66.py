from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_SIGNING_GRANTED_AFTER_PROXY = re.compile(
    r"^Signature collective à deux a été conférée à (?P<name>[^,.;]+),\s*"
    r"maintenant domicilié(?:e)? à (?P<place>[^,.;]+),\s*nommé(?:e)? "
    r"(?P<role>directeur adjoint|directrice adjointe);\s*sa procuration est radiée\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_MANAGER_PRESIDENT = re.compile(
    r"^(?P<seller>[^,.;]+) cède (?P<transferred>[\d']+) de ses "
    r"(?P<before>[\d']+) parts de CHF (?P<nominal>[\d'.]+) à "
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"à (?P<place>[^,.;]+),\s*nouvelle associée-gérante sans signature,\s*avec "
    r"(?P<buyer_count>[\d']+) part(?:s)? de CHF (?P<buyer_nominal>[\d'.]+);\s*"
    r"(?P=seller),\s*qui reste titulaire de (?P<remaining>[\d']+) parts de CHF "
    r"(?P<remaining_nominal>[\d'.]+),\s*est nommée (?P<seller_role>présidente)\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_NAME_ACTUAL = re.compile(
    r"^(?P<previous>[^,.;]+) porte en réalité le nom de (?P<name>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_NAME_CORRECTED = re.compile(
    r"^L['’]inscription No (?P<entry>[\d']+) du (?P<entry_date>\d{2}\.\d{2}\.\d{4}) "
    r"est rectifiée en ce sens que le nom du (?P<role>gérant) est "
    r"[\"“](?P<name>[^\"”]+)[\"”] \(et non pas (?P<previous>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_ADDITIONAL_ADDRESS_SEQUENCE = re.compile(
    r"^(?P<first>Gallerstrasse\s+\d+,\s*\d{4}\s+[^.]+)\.\s*"
    r"Weitere Adresse:\s*(?P<second>[^.]+)\.\s*"
    r"Weitere Adresse:\s*(?P<third>[^.]+)\.\s*"
    r"Weitere Adresse:\s*(?P<fourth>[^.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SOCIAL_SHARE_SPLIT = re.compile(
    r"^La part sociale de CHF (?P<from_nominal>[\d'.]+) a été divisée en "
    r"(?P<count>[\d']+) parts de CHF (?P<nominal>[\d'.]+),\s*qui se répartiront "
    r"de la manière suivante:\s*(?P<name>[^,.;]+) a (?P<owner_count>[\d']+) parts "
    r"de CHF (?P<owner_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_QUALIFIED_FACT_REMOVED = re.compile(
    r"^Nouveaux faits qualifiés:\s*\[La disposition statutaire sur les apports en "
    r"nature et la reprise de biens lors de la fondation du "
    r"(?P<foundation_date>\d{2}\.\d{2}\.\d{4}) est abrogée\]\s*"
    r"\[biffé:\s*(?P<previous>.+)\]\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_FR_QUALIFIED_FACT_AMOUNTS = re.compile(
    r"actifs de CHF (?P<assets>[\d'.-]+).*?passifs de CHF (?P<liabilities>[\d'.-]+).*?"
    r"contrat d['’]apports en nature du (?P<agreement_date>\d{2}\.\d{2}\.\d{4}) "
    r"et bilan au (?P<balance_date>\d{2}\.\d{2}\.\d{4}).*?"
    r"prix de CHF (?P<accepted_value>[\d'.-]+).*?attribuées (?P<shares>[\d']+) "
    r"actions nominatives de CHF (?P<nominal>[\d'.-]+).*?solde de CHF "
    r"(?P<credit>[\d'.-]+)",
    re.I | re.DOTALL | re.UNICODE,
)
_IT_CONTRIBUTION_IN_KIND = re.compile(
    r"^Fatti particolari:\s*Conferimenti in natura e assunzione di beni:\s*"
    r"La società assume attivi e passivi verso terzi della ditta individuale "
    r"(?P<source>.+?),\s*in (?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\) "
    r"sulla base del bilancio al (?P<balance_date>\d{2}\.\d{2}\.\d{4}) che presenta "
    r"attivi per CHF (?P<assets>[\d'.]+) e passivi verso terzi per CHF "
    r"(?P<liabilities>[\d'.]+),\s*contro rimessa di (?P<count>[\d']+) quote sociali "
    r"di nominali da CHF (?P<nominal>[\d'.]+)\.\s*L['’]importo di CHF "
    r"(?P<credit>[\d'.]+) verrà iscritto a bilancio quale credito verso la società\.\s*"
    r"Contratto:\s*(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_FR_SHARE_CAPITAL_CORRECTED = re.compile(
    r"^Rectification:\s*l['’]inscription n° (?P<entry>[\d']+) du "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) \(FOSC du "
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*page (?P<page>\d+)\) est rectifiée "
    r"comme suit:\s*Capital-actions nouveau:\s*CHF (?P<total>[\d']+) "
    r"\(jusqu['’]ici:\s*CHF (?P<previous_total>[\d']+)\),\s*libéré à concurrence de "
    r"CHF (?P<paid>[\d']+) \(jusqu['’]ici:\s*CHF (?P<previous_paid>[\d']+)\),\s*"
    r"divisé en (?P<count>[\d']+) actions de CHF (?P<nominal>[\d']+) "
    r"\(jusqu['’]ici:\s*(?P<previous_count>[\d']+) actions de CHF "
    r"(?P<previous_nominal>[\d']+)\),\s*nominatives et avec\s*"
    r"\(et non pas CHF (?P<incorrect_total>[\d']+),\s*libéré à concurrence de CHF "
    r"(?P<incorrect_paid>[\d']+),\s*divisé en (?P<incorrect_count>[\d']+) actions de "
    r"CHF (?P<incorrect_nominal>[\d']+),\s*nominatives\)\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_PROXIES_NOT_AMONG_THEMSELVES = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?P<name2>[^,.;]+) et (?P<name3>[^,.;]+),\s*"
    r"les trois dont la signature est radiée,\s*engagent désormais la société par "
    r"leur procuration collective à deux,\s*toutefois pas entre eux\.?$",
    re.I | re.UNICODE,
)
_DE_REGISTER_ENTRY_SUPPLEMENT = re.compile(
    r"^\[Nachtrag zu TR (?P<entry>[\d']+) vom "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\]\.?$",
    re.I | re.UNICODE,
)
_DE_PERSON_PUBLICATION_CORRECTED = re.compile(
    r"^Im SHAB Nr\. (?P<issue>\d+) vom (?P<notice_date>\d{2}\.\d{2}\.\d{4}) "
    r"publizierten TR-Eintrag (?P<entry>[\d']+)/(?P<entry_year>\d{4}) wurde "
    r"irrtümlich folgendes publiziert;\s*(?P<incorrect>.+?)\.\s*Korrekt ist:\s*"
    r"(?P<correct>.+)\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_DE_CORRECT_PERSON = re.compile(
    r"^(?P<name>.+?),\s*(?P<nationality>[^,]+ Staatsangehöriger),\s*in "
    r"(?P<place>[^()]+?)\s*\((?P<country>[A-Z]{2,3})\),\s*"
    r"(?P<role>.+?),\s*mit (?P<sign>Kollektivunterschrift zu zweien|Einzelunterschrift) "
    r"\[bisher:\s*(?P<previous>.+)\]$",
    re.I | re.DOTALL | re.UNICODE,
)
_FR_LIQUIDATOR_TYPO = re.compile(
    r"^Lquidateur:\s*l['’](?P<previous_role>administrateur) (?P<name>[^,.;]+),\s*"
    r"lequel continue à signer (?P<sign>individuellement)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_TO_COMPANY = re.compile(
    r"^(?P<seller>[^,.;]+) a cédé (?P<transferred>[\d']+) parts de CHF "
    r"(?P<nominal>[\d'.]+) à (?P<buyer>.+?) "
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à (?P<place>[^,.;]+),\s*"
    r"nouvelle associée pour (?P<buyer_count>[\d']+) parts de CHF "
    r"(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_CANCELLED_CORRECTION_SOLE_ADMIN = re.compile(
    r"^L['’]inscription No (?P<entry>[\d']+) du (?P<entry_date>\d{2}\.\d{2}\.\d{4}) "
    r"est annulée en ce sens que (?P<name>[^,.;]+),\s*de et à (?P<place>[^,.;]+),\s*"
    r"reste (?P<role>administrateur unique)\.?$",
    re.I | re.UNICODE,
)
_FR_TRANSFER_AND_ASSOCIATE_SUMMARY = re.compile(
    r"^(?P<seller>[^,.;]+) a cédé (?P<transferred>[\d']+) parts de CHF "
    r"(?P<nominal>[\d'.]+) à la directrice (?P<buyer>[^,.;]+)\.\s*Associés:\s*"
    r"(?P=seller) et (?P=buyer) chacun associé pour (?P<count>[\d']+) parts de CHF "
    r"(?P<summary_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{year}-{month}-{day}"


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
        person_key=(f"uid:{uid}" if uid else person_key(name=clean_name, place=clean_place)),
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


def extract_parser66_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 66."""
    del language  # Historical records can contain a different language in this field.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_SIGNING_GRANTED_AFTER_PROXY.search(leftover)
    if match:
        consume(match)
        common = {
            "action": "appointed_and_signing_changed",
            "domicile_changed": True,
            "previous_signing": "procuration",
            "previous_signing_revoked": True,
        }
        for event_type, rule_id in (
            ("officer_changed", "fr.persons.deputy_director_after_proxy.v1"),
            ("signing_authority_changed", "fr.persons.deputy_director_after_proxy_signing.v1"),
        ):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    event_type, rule_id, match.group("name"), place=match.group("place"),
                    role=match.group("role"), signing="Kollektivunterschrift zu zweien",
                    extra=common,
                )
            )

    match = _FR_ASSOCIATE_TRANSFER_MANAGER_PRESIDENT.search(leftover)
    if match:
        consume(match)
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.associate_transfer_manager_president.v1",
                    seller, role=match.group("seller_role"),
                    extra={
                        "action": "shares_transferred_and_appointed",
                        "counterparty": buyer,
                        "shares_before": _count(match.group("before")),
                        "shares_transferred": _count(match.group("transferred")),
                        "shares_count": _count(match.group("remaining")),
                        "shares_nominal": match.group("remaining_nominal"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.associate_transfer_manager_president.v1",
                    buyer, place=match.group("place"), role="associée-gérante",
                    extra={
                        "action": "shares_received_and_appointed",
                        "heimat": match.group("origin").strip(),
                        "counterparty": seller,
                        "shares_received": _count(match.group("transferred")),
                        "shares_count": _count(match.group("buyer_count")),
                        "shares_nominal": match.group("buyer_nominal"),
                        "without_signature": True,
                    },
                ),
            ]
        )

    match = _FR_PERSON_NAME_ACTUAL.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.name_corrected_actual.v1",
                match.group("name"),
                extra={"action": "name_corrected", "previous": match.group("previous").strip()},
            )
        )

    match = _FR_MANAGER_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.manager_name_corrected.v1",
                match.group("name"), role=match.group("role"),
                extra={
                    "action": "name_corrected",
                    "previous": match.group("previous").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                },
            )
        )

    match = _DE_ADDITIONAL_ADDRESS_SEQUENCE.search(leftover)
    if match:
        consume(match)
        addresses = [f"St. {match.group('first').strip()}"] + [
            match.group(group).strip() for group in ("second", "third", "fourth")
        ]
        for address in addresses:
            events.append(
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "address_changed", "de.text.additional_address_sequence.v1",
                    {"action": "added", "kind": "additional_address", "address": address},
                )
            )

    match = _FR_SOCIAL_SHARE_SPLIT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.social_share_split.v1",
                {
                    "kind": "social_share_split",
                    "split_from": {"count": 1, "nominal": match.group("from_nominal")},
                    "split_to": {
                        "count": _count(match.group("count")),
                        "nominal": match.group("nominal"),
                    },
                    "currency": "CHF",
                },
            )
        )
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.associate_after_share_split.v1",
                match.group("name"), role="associée",
                extra={
                    "action": "shares_reallocated",
                    "shares_count": _count(match.group("owner_count")),
                    "shares_nominal": match.group("owner_nominal"),
                },
            )
        )

    match = _FR_QUALIFIED_FACT_REMOVED.search(leftover)
    if match:
        consume(match)
        previous = re.sub(r"\s+", " ", match.group("previous")).strip()
        payload = {
            "action": "removed",
            "kind": "contribution_in_kind_and_asset_acquisition",
            "foundation_date": _iso_date(match.group("foundation_date")),
            "previous": previous,
        }
        amounts = _FR_QUALIFIED_FACT_AMOUNTS.search(previous)
        if amounts:
            payload.update(
                {
                    "assets": amounts.group("assets"),
                    "liabilities": amounts.group("liabilities"),
                    "agreement_date": _iso_date(amounts.group("agreement_date")),
                    "balance_date": _iso_date(amounts.group("balance_date")),
                    "accepted_value": amounts.group("accepted_value"),
                    "consideration_shares": _count(amounts.group("shares")),
                    "consideration_nominal": amounts.group("nominal"),
                    "credit": amounts.group("credit"),
                }
            )
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "fr.text.qualified_fact_removed.v1", payload,
            )
        )

    match = _IT_CONTRIBUTION_IN_KIND.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "it.text.contribution_in_kind_corrected.v1",
                {
                    "kind": "contribution_in_kind_and_asset_acquisition",
                    "source": match.group("source").strip(),
                    "source_place": match.group("place").strip(),
                    "source_uid": match.group("uid"),
                    "balance_date": _iso_date(match.group("balance_date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "consideration_shares": _count(match.group("count")),
                    "consideration_nominal": match.group("nominal"),
                    "credit": match.group("credit"),
                    "agreement_date": _iso_date(match.group("agreement_date")),
                },
            )
        )

    match = _FR_SHARE_CAPITAL_CORRECTED.search(leftover)
    if match:
        consume(match)
        common = {
            "action": "corrected",
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "source_notice_date": _iso_date(match.group("notice_date")),
            "source_notice_page": match.group("page"),
        }
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.share_capital_corrected.v1",
                {
                    **common,
                    "currency": "CHF",
                    "total": match.group("total"),
                    "previous_total": match.group("previous_total"),
                    "paid": match.group("paid"),
                    "previous_paid": match.group("previous_paid"),
                    "count": _count(match.group("count")),
                    "nominal": match.group("nominal"),
                    "previous_count": _count(match.group("previous_count")),
                    "previous_nominal": match.group("previous_nominal"),
                    "share_kind": "actions nominatives",
                    "transfer_restricted_by_statutes": True,
                    "incorrect": {
                        "total": match.group("incorrect_total"),
                        "paid": match.group("incorrect_paid"),
                        "count": _count(match.group("incorrect_count")),
                        "nominal": match.group("incorrect_nominal"),
                    },
                },
            )
        )

    match = _FR_THREE_PROXIES_NOT_AMONG_THEMSELVES.search(leftover)
    if match:
        consume(match)
        for group in ("name1", "name2", "name3"):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", "fr.persons.three_proxies_excluded.v1",
                    match.group(group), signing="Kollektivprokura zu zweien",
                    extra={
                        "action": "signing_replaced",
                        "previous_signing_revoked": True,
                        "not_among_themselves": True,
                    },
                )
            )

    match = _DE_REGISTER_ENTRY_SUPPLEMENT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", "de.text.register_entry_supplement.v1",
                {
                    "action": "supplemented",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                },
            )
        )

    match = _DE_PERSON_PUBLICATION_CORRECTED.search(leftover)
    if match:
        consume(match)
        correct = match.group("correct").strip().rstrip(".")
        common = {
            "action": "corrected",
            "source_issue": match.group("issue"),
            "source_notice_date": _iso_date(match.group("notice_date")),
            "entry": match.group("entry"),
            "entry_year": match.group("entry_year"),
            "incorrect": match.group("incorrect").strip(),
            "correct": correct,
        }
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", "de.text.person_publication_corrected.v1", common,
            )
        )
        person = _DE_CORRECT_PERSON.search(correct)
        if person:
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "de.persons.publication_corrected.v1",
                    person.group("name"), place=person.group("place"),
                    role=person.group("role"), signing=person.group("sign"),
                    extra={
                        "action": "publication_corrected",
                        "nationality": person.group("nationality").strip(),
                        "country": person.group("country"),
                        "previous": person.group("previous").strip(),
                    },
                )
            )

    match = _FR_LIQUIDATOR_TYPO.search(leftover)
    if match:
        consume(match)
        common = {"action": "appointed", "previous_role": match.group("previous_role")}
        for event_type, rule_id in (
            ("officer_changed", "fr.persons.liquidator_typo_heading.v1"),
            ("signing_authority_changed", "fr.persons.liquidator_typo_heading_signing.v1"),
        ):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    event_type, rule_id, match.group("name"), role="liquidateur",
                    signing="Einzelunterschrift", extra=common,
                )
            )

    match = _FR_ASSOCIATE_TRANSFER_TO_COMPANY.search(leftover)
    if match:
        consume(match)
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", "fr.persons.associate_transfer_company_full.v1",
                    seller, role="associé",
                    extra={
                        "action": "shares_transferred",
                        "counterparty": buyer,
                        "counterparty_uid": match.group("uid"),
                        "shares_transferred": transferred,
                        "shares_nominal": match.group("nominal"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.associate_transfer_company_full.v1",
                    buyer, place=match.group("place"), uid=match.group("uid"),
                    role="associée",
                    extra={
                        "action": "shares_received",
                        "counterparty": seller,
                        "shares_received": transferred,
                        "shares_count": _count(match.group("buyer_count")),
                        "shares_nominal": match.group("buyer_nominal"),
                    },
                ),
            ]
        )

    match = _FR_CANCELLED_CORRECTION_SOLE_ADMIN.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.cancelled_correction_sole_admin.v1",
                match.group("name"), place=match.group("place"), role=match.group("role"),
                signing="Einzelunterschrift",
                extra={
                    "action": "registration_cancelled_and_role_confirmed",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "remains_in_role": True,
                },
            )
        )

    match = _FR_TRANSFER_AND_ASSOCIATE_SUMMARY.search(leftover)
    if match:
        consume(match)
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        remaining = _count(match.group("count"))
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.transfer_associate_summary.v1",
                    seller, role="associé",
                    extra={
                        "action": "shares_transferred",
                        "counterparty": buyer,
                        "shares_before": remaining + transferred,
                        "shares_transferred": transferred,
                        "shares_count": remaining,
                        "shares_nominal": match.group("summary_nominal"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.transfer_associate_summary.v1",
                    buyer, role="associée",
                    extra={
                        "action": "shares_received",
                        "existing_role": "directrice",
                        "counterparty": seller,
                        "shares_received": transferred,
                        "shares_count": remaining,
                        "shares_nominal": match.group("summary_nominal"),
                    },
                ),
            ]
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
