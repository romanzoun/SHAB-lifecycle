from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_MANAGER_SHARE_TRANSFER = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+) de ses\s+(?P<before>[\d']+) parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à l['’]associé-gérant\s+(?P<buyer>[^,.;]+),\s*"
    r"désormais tit(?:u|ut)laire de\s+(?P<buyer_count>[\d']+) parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*(?P=seller)\s+reste titulaire de\s+"
    r"(?P<seller_count>[\d']+) parts de CHF\s+(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_CORRECTED_WITH_PERSON = re.compile(
    r"^L['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+signe collective à deux,?\s+avec\s+"
    r"(?P<with_person>[^()]+?)\s*\(et non individuellement\)\.?$",
    re.I | re.UNICODE,
)
_DE_STATUTES_DATE_CORRECTED_SHORT = re.compile(
    r"^Statutendatum richtig:\s*(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_IT_COMMISSIONER_APPOINTMENT_EXTENDED = re.compile(
    r"^Con decisione del\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*la\s+"
    r"(?P<authority>.+?)\s+ha prorogato la nomina del commissario\s+"
    r"(?P<name>[^,.;]+?)\s+fino al\s+(?P<until>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_REGISTRATION_SUPPLEMENT_HEADER = re.compile(
    r"^L['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) est complétée sur les points suivants:\s*$",
    re.I | re.UNICODE,
)
_FR_TRANSFER_TO_UNSIGNED_MANAGER = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+) de ses\s+"
    r"(?P<before>[\d']+) parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*de et à\s+(?P<place>[^,.;]+),\s*"
    r"nouvelle associée-gérante sans signature,\s*avec\s+"
    r"(?P<buyer_count>[\d']+) part(?:s)? de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"(?P=seller),\s*qui reste titulaire de\s+(?P<seller_count>[\d']+) part(?:s)? "
    r"de CHF\s+(?P<seller_nominal>[\d'.]+),\s*est nommé président\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_CONDITIONAL_CAPITAL_CLAUSES = re.compile(
    r"^L['’]assemblée générale a introduit deux clauses statutaires relatives à "
    r"des augmentations conditionnelles du capital-actions par décision du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4});\s*pour les détails,\s*voir les statuts\.?$",
    re.I | re.UNICODE,
)
_FR_ADDITIONAL_CONTRIBUTION_CLAUSE_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+) "
    r"du\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*(?P<page>\d+)/"
    r"(?P<notice_id>\d+)\) est rectifiée en ce sens que les statuts modifiés en "
    r"date du\s+(?P<day>\d{1,2})\s+(?P<month>[A-Za-zÀ-ÿ]+)\s+(?P<year>\d{4}) "
    r"ne prévoient plus de clause particulière relative aux versements supplémentaires\.?$",
    re.I | re.UNICODE,
)
_FR_REPRESENTATIVE_NAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) est rectifiée en ce sens que "
    r"l['’]un des représentants se nomme\s+(?P<name>[^()]+?)\s*"
    r"\(et non\s+(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_RESTRICTIONS_REMOVED_TYPO = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?P<role1>secrétaire),\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*(?P<role2>membres? du conseil d['’]administrations?),\s*"
    r"continuent de signer collectivement à deux,?\s*mais désormais sans autre "
    r"restriction\.\s*(?P<name3>[^,.;]+),\s*maintenant domiciliée? à\s*"
    r"(?P<place3>[^,.;]+),\s*continue de signer par procuration,\s*"
    r"collectivement à deux,?\s*mais désormais sans autre restriction\.?$",
    re.I | re.UNICODE,
)
_FR_DOMICILE_CORRECTED_NOTICE = re.compile(
    r"^L['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+est domiciliée? à\s+(?P<place>[^()]+?)\s*"
    r"\(et non pas à\s+(?P<previous_place>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_SELLERS_TRANSFER_TO_UNSIGNED_ASSOCIATE = re.compile(
    r"^L['’]associée\s+(?P<seller1>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred1>[\d']+) de ses\s+(?P<before1>[\d']+) parts sociales de "
    r"CHF\s+(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé\.\s*"
    r"L['’]associé\s+(?P<seller2>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred2>[\d']+) de ses\s+(?P<before2>[\d']+) parts sociales de "
    r"CHF\s+(?P<nominal2>[\d'.]+)\s+à\s+(?P=buyer),\s*lequel est ainsi titulaire "
    r"de\s+(?P<buyer_count>[\d']+) parts sociales de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+);\s*n['’]exerce pas la signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_COURT_DECISION_REVOKED = re.compile(
    r"^Par décision du\s+(?P<decision_day>\d{1,2})\s+"
    r"(?P<decision_month>[A-Za-zÀ-ÿ]+)\s+(?P<decision_year>\d{4}),\s*"
    r"(?P<authority>.+?)\s+a dit que sa décision rendue le\s+"
    r"(?P<original_day>\d{1,2})\s+(?P<original_month>[A-Za-zÀ-ÿ]+)\s+"
    r"(?P<original_year>\d{4}) est annulée,\s*le prononcé du\s+"
    r"(?P<decisive_day>\d{1,2})\s+(?P<decisive_month>[A-Za-zÀ-ÿ]+)\s+"
    r"(?P<decisive_year>\d{4}) étant décisif\.?$",
    re.I | re.UNICODE,
)
_FR_LEGACY_AUDITOR_REMOVED = re.compile(
    r"^(?P<name>.+?)\s+\((?P<registry_id>CH-[\d.-]+-\d)\)\s+n['’]est plus "
    r"organe de révision\.?$",
    re.I | re.UNICODE,
)
_FR_AUTHORIZED_CAPITAL_CLAUSE_REMOVED_SHARES = re.compile(
    r"^Suppression de la clause statutaire relative à l['’]augmentation autorisée "
    r"du capital-actions,?\s*fondée sur la décision d['’]autorisation du\s*"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_NEW_PERSON_MIXED_LANGUAGE = re.compile(
    r"^Neu eingetragene Person:\s*(?P<name>[^,.;]+),\s*von\s+"
    r"(?P<origin>[^,.;]+),\s*in\s+(?P<place>[^,.;]+),\s*"
    r"(?P<role>[^,.;]+),\s*(?P<sign>Einzelunterschrift)\.?$",
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


def _fr_date(day: str, month: str, year: str) -> str:
    return f"{int(year):04d}-{_FR_MONTHS[month.lower()]:02d}-{int(day):02d}"


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


def extract_parser100_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 100."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_MANAGER_SHARE_TRANSFER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_share_transfer_typo.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant",
                extra={
                    "action": "shares_transferred",
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("seller_nominal"),
                    "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, role="associé-gérant",
                extra={
                    "action": "shares_received",
                    "counterparty": seller,
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"),
                    "currency": "CHF",
                },
            ),
        ])

    match = _FR_SIGNING_CORRECTED_WITH_PERSON.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.signing_corrected_with_person.v1",
            match.group("name"), signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "corrected",
                "previous_signing": "Einzelunterschrift",
                "with": match.group("with_person").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _DE_STATUTES_DATE_CORRECTED_SHORT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.statutes_date_corrected_short.v1",
            {
                "kind": "statutes_date",
                "action": "corrected",
                "date": _iso_date(match.group("date")),
            },
        ))

    match = _IT_COMMISSIONER_APPOINTMENT_EXTENDED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "it.persons.commissioner_appointment_extended.v1",
            match.group("name"), role="commissario",
            extra={
                "action": "appointment_extended",
                "decision_date": _iso_date(match.group("decision_date")),
                "until": _iso_date(match.group("until")),
                "authority": match.group("authority").strip(),
            },
        ))

    match = _FR_REGISTRATION_SUPPLEMENT_HEADER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.registration_supplement_points.v1",
            {
                "action": "registration_supplemented",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "details_in_accompanying_events": True,
            },
        ))

    match = _FR_TRANSFER_TO_UNSIGNED_MANAGER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.transfer_to_unsigned_manager_president.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller,
                role="associé-gérant et président",
                extra={
                    "action": "shares_transferred_and_appointed_president",
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("seller_nominal"),
                    "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée-gérante",
                extra={
                    "action": "appointed_and_shares_received",
                    "heimat": match.group("place").strip(),
                    "counterparty": seller,
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"),
                    "currency": "CHF",
                    "without_signature": True,
                },
            ),
        ])

    match = _FR_TWO_CONDITIONAL_CAPITAL_CLAUSES.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.two_conditional_capital_clauses.v1",
            {
                "kind": "conditional_capital_clause",
                "action": "introduced",
                "clause_count": 2,
                "decision_date": _iso_date(match.group("date")),
                "details_in_statutes": True,
            },
        ))

    match = _FR_ADDITIONAL_CONTRIBUTION_CLAUSE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.additional_contribution_clause_corrected.v1",
            {
                "kind": "additional_contribution_clause",
                "action": "removed",
                "correction": True,
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_page": match.group("page"),
                "notice_id": match.group("notice_id"),
                "statutes_date": _fr_date(
                    match.group("day"), match.group("month"), match.group("year")
                ),
            },
        ))

    match = _FR_REPRESENTATIVE_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.representative_name_corrected.v1",
            match.group("name"), role="représentant",
            extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _FR_SIGNING_RESTRICTIONS_REMOVED_TYPO.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.signing_restrictions_removed_typo.v1"
        for group, role in (
            ("name1", match.group("role1")),
            ("name2", match.group("role2")),
        ):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(group),
                role=role.lower(), signing="Kollektivunterschrift zu zweien",
                extra={"action": "restriction_removed", "continued": True},
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", rule_id, match.group("name3"),
            place=match.group("place3"), signing="Kollektivprokura zu zweien",
            extra={
                "action": "domicile_changed_and_restriction_removed",
                "continued": True,
            },
        ))

    match = _FR_DOMICILE_CORRECTED_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.domicile_corrected_notice.v1",
            match.group("name"), place=match.group("place"),
            extra={
                "action": "domicile_corrected",
                "previous_place": match.group("previous_place").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _FR_TWO_SELLERS_TRANSFER_TO_UNSIGNED_ASSOCIATE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_sellers_transfer_to_unsigned_associate.v1"
        buyer = match.group("buyer").strip()
        for index, role in ((1, "associée"), (2, "associé")):
            transferred = _count(match.group(f"transferred{index}"))
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"seller{index}"), role=role,
                extra={
                    "action": "shares_transferred",
                    "counterparty": buyer,
                    "shares_before": _count(match.group(f"before{index}")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group(f"before{index}")) - transferred,
                    "share_nominal": match.group("nominal" if index == 1 else "nominal2"),
                    "currency": "CHF",
                },
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, buyer, place=match.group("place"),
            role="associé",
            extra={
                "action": "appointed_and_shares_received",
                "heimat": match.group("origin").strip(),
                "shares_received": (
                    _count(match.group("transferred1"))
                    + _count(match.group("transferred2"))
                ),
                "shares_count": _count(match.group("buyer_count")),
                "share_nominal": match.group("buyer_nominal"),
                "currency": "CHF",
                "without_signature": True,
            },
        ))

    match = _FR_COURT_DECISION_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.court_decision_revoked_decisive_order.v1",
            {
                "kind": "court_decision_revoked",
                "decision_date": _fr_date(
                    match.group("decision_day"),
                    match.group("decision_month"),
                    match.group("decision_year"),
                ),
                "original_decision_date": _fr_date(
                    match.group("original_day"),
                    match.group("original_month"),
                    match.group("original_year"),
                ),
                "decisive_order_date": _fr_date(
                    match.group("decisive_day"),
                    match.group("decisive_month"),
                    match.group("decisive_year"),
                ),
                "authority": match.group("authority").strip(),
            },
        ))

    match = _FR_LEGACY_AUDITOR_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_removed", "fr.persons.legacy_auditor_removed.v1",
            match.group("name"), role="organe de révision",
            extra={"action": "removed", "registry_id": match.group("registry_id")},
        ))

    match = _FR_AUTHORIZED_CAPITAL_CLAUSE_REMOVED_SHARES.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.authorized_capital_clause_removed_shares.v1",
            {
                "kind": "authorized_capital_clause",
                "action": "removed",
                "authorization_date": _iso_date(match.group("date")),
            },
        ))

    match = _DE_NEW_PERSON_MIXED_LANGUAGE.search(leftover)
    if match:
        consume(match)
        rule_id = "de.persons.new_person_mixed_language.v1"
        common = {
            "place": match.group("place"),
            "role": match.group("role"),
            "signing": "Einzelunterschrift",
        }
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=common["place"], role=common["role"], signing=common["signing"],
                extra={"action": "appointed", "heimat": match.group("origin").strip()},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name"),
                place=common["place"], role=common["role"], signing=common["signing"],
                extra={"action": "granted"},
            ),
        ])

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
