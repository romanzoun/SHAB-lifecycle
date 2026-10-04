from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_ASSOCIATE_TRANSFER_AND_PRESIDENCY = re.compile(
    r"(?P<seller>[A-ZÀ-Ÿ][^,.;]+?)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"nouvel associé-gérant(?:\s+avec signature individuelle)?(?:,\s*|\s+)avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"(?P=seller),\s*qui reste titulaire de\s+(?P<seller_count>[\d']+)\s+"
    r"parts de CHF\s+(?P<seller_nominal>[\d'.]+),\s*est nommée\s+"
    r"(?P<seller_role>présidente)\.?,?",
    re.I | re.UNICODE,
)
_FR_COMPANY_REINSTATED_NUMERIC_DATE = re.compile(
    r"La société est réinscrite au registre du commerce conformément à la décision\s+"
    r"(?P<authority>.+?)\s+du\s+(?P<date>\d{2}\.\d{2}\.\d{4})\.?,?",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PAIR_WITH_SECOND_ROLE = re.compile(
    r"Administration:\s*(?P<name1>[^,.;]+),\s*nommé(?:e)?\s+(?P<role1>[^,.;]+),\s*"
    r"et\s+(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"(?P<role2>[^,.;]+),\s*lesquels signent\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?,?",
    re.I | re.UNICODE,
)
_FR_REGISTRATION_SUPPLEMENTED = re.compile(
    r"L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*"
    r"\(FOSC du\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"p\.\s*(?P<notice_page>\d+)/(?P<notice_id>\d+)\)\s+est complétée par la "
    r"mention de l['’]organe de publication,\s*soit\s+"
    r"(?P<publication_body>.+?),\s*et du mode de communication aux associés,\s*"
    r"soit\s+(?P<communication_mode>[^.]+)\.?,?",
    re.I | re.UNICODE,
)
_FR_LEGAL_CONVERSION_WITH_RESTRICTION = re.compile(
    r"Le\s+(?P<conversion_date>\d{2}\.\d{2}\.\d{4}),\s*les actions au porteur "
    r"ont été converties de par la loi en actions nominatives;\s*par décision de "
    r"l['’]assemblée générale du\s+(?P<adaptation_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"les statuts de la société ont été adaptés à la conversion\.\s*Les\s+"
    r"(?P<count>[\d']+)\s+actions de CHF\s+(?P<nominal>[\d'.]+),?\s*"
    r"nominatives sont désormais liées selon statuts\.\s*Capital-actions:\s*CHF\s+"
    r"(?P<total>[\d'.]+),\s*libéré à concurrence de CHF\s+(?P<paid>[\d'.]+),\s*"
    r"divisé en\s+(?P<capital_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<capital_nominal>[\d'.]+),\s*nominatives,\s*"
    r"(?P<restriction>liées selon statuts)\.?,?",
    re.I | re.UNICODE,
)
_FR_LEGAL_CONVERSION_CLASS_SPLIT = re.compile(
    r"Le\s+(?P<conversion_date>\d{2}\.\d{2}\.\d{4}),\s*les actions au porteur "
    r"ont été converties de par la loi en actions nominatives;\s*par décision de "
    r"l['’]assemblée générale du\s+(?P<adaptation_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"les statuts de la société ont été adaptés à la conversion\.\s*Division des\s+"
    r"(?P<from_count>[\d']+)\s+actions\s*\((?P<share_class>[^)]+)\)\s+de CHF\s+"
    r"(?P<from_nominal>[\d'.]+),\s*nominatives en\s+(?P<to_count>[\d']+)\s+"
    r"actions de CHF\s+(?P<to_nominal>[\d'.]+),\s*nominatives\.\s*"
    r"Capital-actions:\s*CHF\s+(?P<total>[\d'.]+),\s*libéré à concurrence de CHF\s+"
    r"(?P<paid>[\d'.]+),\s*divisé en\s+(?P<capital_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<capital_nominal>[\d'.]+),\s*(?P<kind>nominatives)\.?,?",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBERS_WITHOUT_SIGNATURE_DE = re.compile(
    r"(?P<name1>[A-ZÀ-Ÿ][^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*sans signature,\s*"
    r"et\s+(?P<name2>[A-ZÀ-Ÿ][^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*sans signature,\s*"
    r"sont membres du conseil d['’]administration\.?,?",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_THREE_SHARED_ORIGIN = re.compile(
    r"Administration:\s*(?P<name1>[^,.;]+),\s*nommé(?:e)?\s+(?P<role1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+)\s+et\s+(?P<name3>[^,.;]+),\s*tous deux\s+"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^.]+)\.\s*"
    r"Signature individuelle du président ou collective à deux des deux autres "
    r"membres du conseil d['’]administration\.?,?",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_THREE_DISTINCT = re.compile(
    r"Administration:\s*(?P<name1>[^,.;]+),\s*nommé(?:e)?\s+(?P<role1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*"
    r"à\s+(?P<place2>[^,.;]+)\s+et\s+(?P<name3>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin3>[^,.;]+),\s*à\s+"
    r"(?P<place3>[^,.;]+),\s*tous trois(?:\s+avec signature collective à deux)?\s*;\s*"
    r"les pouvoirs de\s+(?P<changed>[^,.;]+)\s+sont modifiés en ce sens\.?,?",
    re.I | re.UNICODE,
)
_IT_FOUNDATION_ORGANIZATION_REMOVED = re.compile(
    r"Nuova organizzazione:\s*\[L['’]indicazione relativa all['’]organizzazione è "
    r"cancellata a seguito dell['’]abrogazione della disposizione di cui "
    r"all['’]art\s+art\.\s*95 lett\.\s*h ORC\.\]\.\s*"
    r"\[La seguente indicazione è radiata in quanto non prevista quale iscrizione "
    r"nel registro di commercio delle fondazioni secondo l['’]art\.\s*95 ORC\.\]\s*"
    r"\[radiati:\s*Atto di fondazione modificato il\s*"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+con risoluzione del\s+"
    r"(?P<authority>.+?)\s+su punti non soggetti a pubblicazione\.\]\.?,?",
    re.I | re.UNICODE,
)
_DE_COMPOSITION_MORATORIUM_REPLACED = re.compile(
    r"Mit Entscheid des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde eine definitive "
    r"Nachlassstundung für die Dauer von\s+(?P<duration>\d+)\s+Monaten bis zum\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\s+gewährt\.\s*\[bisher:\s*Mit Entscheid "
    r"des\s+(?P<previous_authority>.+?)\s+vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+wurde eine provisorische "
    r"Nachlassstundung für die Dauer von\s+(?P<previous_duration>\d+)\s+Monaten "
    r"bis(?: zum)?\s+(?P<previous_until>\d{2}\.\d{2}\.\d{4})\s+gewährt\.\]\.?,?",
    re.I | re.UNICODE,
)
_DE_REMARK_DELETION_OMITTED = re.compile(
    r"Die Streichung dieser Bemerkung ging vergessen\.?,?", re.I | re.UNICODE
)
_FR_BRANCH_REGISTERED = re.compile(
    r"Inscription de la succursale de\s+(?P<place>.+?)\s+"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+au registre du commerce du canton "
    r"de\s+(?P<register_canton>.+?)\s+\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+(?P<notice_id>\d+)\)\.?,?",
    re.I | re.UNICODE,
)
_DE_EARLY_DELETION_POSTPONED = re.compile(
    r"Vorzeitige Löschung mit Bestätigung des zugelassenen Revisionsexperten vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+aufgeschoben mangels Zustimmungen der "
    r"eidg\.\s+und kant\.\s+Steuerverwaltungen\.?,?",
    re.I | re.UNICODE,
)
_FR_CONTRIBUTION_RULES_REMOVED_VARIANT = re.compile(
    r"La clause\s+(?P<statutory>statutaire\s+)?relative à\s+"
    r"(?P<clause>l['’]apport en nature et la reprise de biens effectuée|"
    r"la reprise de biens envisagée)(?:\s+à la constitution)?\s+"
    r"(?:est|a été) abrogée "
    r"conformément à l['’]art\.\s*628\s+al\.\s*4\s+CO\.?,?",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{year}-{month}-{day}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _signing(raw: str) -> str:
    return (
        "Einzelunterschrift"
        if "individ" in raw.lower()
        else "Kollektivunterschrift zu zweien"
    )


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


def extract_parser57_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 57."""
    events: list[Event] = []
    leftover = text

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_ASSOCIATE_TRANSFER_AND_PRESIDENCY.search(leftover)
    if match:
        consume(match)
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.associate_transfer_presidency.v1",
                seller, role=match.group("seller_role"),
                extra={
                    "action": "shares_transferred_and_appointed",
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("seller_count")),
                    "shares_nominal": match.group("seller_nominal"),
                },
            )
        )
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.associate_transfer_presidency.v1",
                buyer, place=match.group("place"), role="associé-gérant",
                signing="Einzelunterschrift",
                extra={
                    "action": "shares_received",
                    "counterparty": seller,
                    "heimat": match.group("origin").strip(),
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "shares_nominal": match.group("buyer_nominal"),
                },
            )
        )

    match = _FR_COMPANY_REINSTATED_NUMERIC_DATE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "fr.text.company_reinstated_numeric_date.v1",
                {
                    "kind": "registration_reinstated",
                    "date": _iso_date(match.group("date")),
                    "authority": match.group("authority").strip(),
                },
            )
        )

    match = _FR_ADMINISTRATION_PAIR_WITH_SECOND_ROLE.search(leftover)
    if match:
        consume(match)
        signing = _signing(match.group("sign"))
        people = (
            (match.group("name1"), None, match.group("role1"), {}),
            (
                match.group("name2"), match.group("place2"), match.group("role2"),
                {"heimat": match.group("origin2").strip()},
            ),
        )
        for name, place, role, extra in people:
            for event_type, rule_id in (
                ("officer_changed", "fr.persons.administration_pair_roles.v1"),
                ("signing_authority_changed", "fr.persons.administration_pair_roles_signing.v1"),
            ):
                events.append(
                    _person_event(
                        publication_id, published_at, org_uid, plz, canton,
                        event_type, rule_id, name, place=place, role=role.strip(),
                        signing=signing, extra=extra,
                    )
                )

    match = _FR_REGISTRATION_SUPPLEMENTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", "fr.text.registration_supplemented.v1",
                {
                    "action": "supplemented",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "source_notice_date": _iso_date(match.group("notice_date")),
                    "source_notice_page": match.group("notice_page"),
                    "source_notice_id": match.group("notice_id"),
                    "publication_body": match.group("publication_body").strip(),
                    "communication_mode": match.group("communication_mode").strip(),
                },
            )
        )

    match = _FR_LEGAL_CONVERSION_WITH_RESTRICTION.search(leftover)
    if match:
        consume(match)
        total = match.group("total")
        paid = match.group("paid")
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.legal_bearer_conversion_restricted.v1",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _iso_date(match.group("conversion_date")),
                    "adaptation_date": _iso_date(match.group("adaptation_date")),
                    "from_kind": "au porteur",
                    "to_kind": "nominatives",
                    "to_count": _count(match.group("count")),
                    "to_nominal": match.group("nominal"),
                    "capital_total": total,
                    "paid": paid,
                    "paid_in_full": paid == total,
                    "restriction": match.group("restriction"),
                    "statutes_adapted": True,
                },
            )
        )

    match = _FR_LEGAL_CONVERSION_CLASS_SPLIT.search(leftover)
    if match:
        consume(match)
        total = match.group("total")
        paid = match.group("paid")
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.legal_bearer_conversion_class_split.v1",
                {
                    "kind": "bearer_to_registered_conversion_and_share_split",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _iso_date(match.group("conversion_date")),
                    "adaptation_date": _iso_date(match.group("adaptation_date")),
                    "from_kind": "au porteur",
                    "to_kind": match.group("kind"),
                    "share_class": match.group("share_class"),
                    "split_from": {
                        "count": _count(match.group("from_count")),
                        "nominal": match.group("from_nominal"),
                    },
                    "split_to": {
                        "count": _count(match.group("to_count")),
                        "nominal": match.group("to_nominal"),
                    },
                    "capital_total": total,
                    "paid": paid,
                    "paid_in_full": paid == total,
                    "capital_count": _count(match.group("capital_count")),
                    "capital_nominal": match.group("capital_nominal"),
                    "statutes_adapted": True,
                },
            )
        )

    match = _FR_BOARD_MEMBERS_WITHOUT_SIGNATURE_DE.search(leftover)
    if match:
        consume(match)
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.board_members_without_signature.v2",
                    match.group(f"name{index}"), place=match.group(f"place{index}"),
                    role="membre du conseil d'administration",
                    extra={
                        "heimat": match.group(f"origin{index}").strip(),
                        "without_signature": True,
                    },
                )
            )

    match = _FR_ADMINISTRATION_THREE_SHARED_ORIGIN.search(leftover)
    if match:
        consume(match)
        place = match.group("place").strip()
        origin = match.group("origin").strip()
        people = (
            (match.group("name1"), None, match.group("role1"), "Einzelunterschrift", {}),
            (match.group("name2"), place, "administrateur", "Kollektivunterschrift zu zweien", {"heimat": origin}),
            (match.group("name3"), place, "administrateur", "Kollektivunterschrift zu zweien", {"heimat": origin}),
        )
        for name, person_place, role, signing, extra in people:
            for event_type, rule_id in (
                ("officer_changed", "fr.persons.administration_three_shared_origin.v1"),
                ("signing_authority_changed", "fr.persons.administration_three_shared_origin_signing.v1"),
            ):
                events.append(
                    _person_event(
                        publication_id, published_at, org_uid, plz, canton,
                        event_type, rule_id, name, place=person_place,
                        role=role.strip(), signing=signing, extra=extra,
                    )
                )

    match = _FR_ADMINISTRATION_THREE_DISTINCT.search(leftover)
    if match:
        consume(match)
        changed = match.group("changed").strip()
        people = (
            (match.group("name1"), None, match.group("role1"), {}),
            (
                match.group("name2"), match.group("place2"), "administrateur",
                {"heimat": match.group("origin2").strip()},
            ),
            (
                match.group("name3"), match.group("place3"), "administrateur",
                {"heimat": match.group("origin3").strip()},
            ),
        )
        for name, place, role, extra in people:
            if name.strip() == changed:
                extra["powers_changed"] = True
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.administration_three_distinct.v1",
                    name, place=place, role=role.strip(), extra=extra,
                )
            )

    match = _IT_FOUNDATION_ORGANIZATION_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", "it.text.foundation_organization_removed.v1",
                {
                    "action": "removed",
                    "reason": "registration_not_required",
                    "law": "Art. 95 ORC",
                    "entity_kind": "foundation",
                    "previous_foundation_deed_date": _iso_date(match.group("date")),
                    "previous_authority": match.group("authority").strip(),
                    "previous_detail": "non_public_changes",
                },
            )
        )

    match = _DE_COMPOSITION_MORATORIUM_REPLACED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.composition_moratorium_granted.v2",
                {
                    "kind": "composition_moratorium_granted",
                    "moratorium_type": "definitive",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "until": _iso_date(match.group("until")),
                    "duration_months": int(match.group("duration")),
                    "authority": match.group("authority").strip(),
                },
            )
        )
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.composition_moratorium_replaced.v1",
                {
                    "kind": "composition_moratorium_granted",
                    "moratorium_type": "provisional",
                    "action": "replaced",
                    "decision_date": _iso_date(match.group("previous_date")),
                    "until": _iso_date(match.group("previous_until")),
                    "duration_months": int(match.group("previous_duration")),
                    "authority": match.group("previous_authority").strip(),
                },
            )
        )

    match = _DE_REMARK_DELETION_OMITTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", "de.text.remark_deletion_omitted.v1",
                {"kind": "remark_deletion_omitted", "action": "removed"},
            )
        )

    match = _FR_BRANCH_REGISTERED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", "fr.text.branch_registered.v1",
                {
                    "action": "registered",
                    "place": match.group("place").strip(),
                    "branch_uid": match.group("uid"),
                    "register_canton": match.group("register_canton").strip(),
                    "source_notice_date": _iso_date(match.group("notice_date")),
                    "source_notice_id": match.group("notice_id"),
                },
            )
        )

    match = _DE_EARLY_DELETION_POSTPONED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.early_deletion_postponed.v1",
                {
                    "kind": "deletion_postponed",
                    "requested_early": True,
                    "audit_expert_confirmation_date": _iso_date(match.group("date")),
                    "tax_authority_consent_missing": True,
                    "authorities": ["federal_tax_authority", "cantonal_tax_authority"],
                },
            )
        )

    match = _FR_CONTRIBUTION_RULES_REMOVED_VARIANT.search(leftover)
    if match:
        consume(match)
        clause = match.group("clause").lower()
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "fr.text.contribution_rules_removed.v2",
                {
                    "action": "removed",
                    "kind": (
                        "contribution_in_kind_and_asset_acquisition"
                        if "apport en nature" in clause
                        else "intended_asset_acquisition"
                    ),
                    "legal_basis": "Art. 628 al. 4 CO",
                },
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
