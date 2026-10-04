from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_EXPIRED_CAPITAL_CLAUSE = re.compile(r",?\s*le délai étant écoulé", re.I)
_DE_COOPERATIVE_OBLIGATIONS = re.compile(
    r"Pflichten neu:\s*(?P<obligations>Beitrags- oder Leistungspflichten der "
    r"Genossenschafter gemäss näherer Umschreibung in den Statuten)\.?",
    re.I,
)
_DE_CAPITAL_PAID_IN = re.compile(
    r"Das Stammkapital wurde im Betrag von (?P<currency>[A-Z]{3}) "
    r"(?P<amount>[\d'.]+) nachliberiert\.?",
    re.I,
)
_FR_FIRST_NAME_CHANGED = re.compile(
    r"(?P<old_name>[A-ZÀ-Ÿ][^.;]+?)\s+se prénomme (?:maintenant|désormais)\s+"
    r"(?P<name>[A-ZÀ-Ÿ][^.;]+)\.?",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PAIR = re.compile(
    r"Administration:\s*(?P<name1>[^,]+),\s*nommé(?:e)?\s+(?P<role1>[^,]+),\s*et\s*"
    r"(?P<name2>[^,]+),\s*(?:du |de la |de l['’]|des |de |d['’])"
    r"(?P<origin2>[^,]+),\s*à\s+(?P<place2>[^,]+),\s*lesquels signent\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?",
    re.I | re.UNICODE,
)
_FR_APPOINTED_WITH_SIGNING = re.compile(
    r"Signature\s+(?P<sign>individuelle|collective(?:\s+à\s+deux)?)\s+de\s+"
    r"(?P<name>[^,;]+),\s*nommé(?:e)?\s+(?P<role>[^;]+);\s*"
    r"sa procuration est radiée\.?",
    re.I | re.UNICODE,
)
_FR_INTERMEDIATED_BEARER_SHARES = re.compile(
    r"Toutes les actions au porteur de la société étant émises sous forme de titres "
    r"intermédiés au sens de la loi fédérale sur les titres intermédiés,\s*"
    r"elle est autorisée à en avoir\.?",
    re.I,
)
_DE_INTERMEDIATED_BEARER_SHARES = re.compile(
    r"Die Gesellschaft hat sämtliche Inhaberaktien als Bucheffekten im Sinne des "
    r"Bucheffektengesetzes ausgestaltet und ist daher befugt,\s*"
    r"Inhaberaktien zu halten\.?",
    re.I,
)
_DE_ECCLESIASTICAL_FOUNDATION = re.compile(
    r"Die Stiftung ist eine kirchliche Stiftung, die nicht der staatlichen Aufsicht "
    r"unterstellt ist und aufgrund des kirchlichen Charakters keine Revisionsstelle "
    r"bezeichnen muss\.\s*Die kirchliche Aufsicht wird wahrgenommen durch die\s+"
    r"(?P<authority>.+?)\s+mit Geschäftsstelle in\s+(?P<office>[^.]+)\.\s*"
    r"\[gestrichen:\s*Stiftungsrat:\s*mindestens\s+(?P<minimum>\d+) Mitglieder\]\.?",
    re.I,
)
_FR_SHARE_RESTRICTION_WITH_CAPITAL = re.compile(
    r"Les\s+(?P<count>[\d']+)\s+actions de CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"nominatives,\s*sont désormais liées selon statuts\.\s*"
    r"Capital-actions:\s*CHF\s+(?P<total>[\d'.]+),\s*libéré à concurrence de CHF\s+"
    r"(?P<paid>[\d'.]+),\s*divisé en\s+(?P<capital_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<capital_nominal>[\d'.]+),\s*nominatives,\s*liées selon statuts\.?",
    re.I,
)
_DE_FORMER_DOMICILE = re.compile(
    r"Die Gesellschaft ist nicht mehr am\s+(?P<address>.+?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<town>[^,]+),\s*domiziliert\.?",
    re.I,
)
_DE_BRANCH_BUSINESS_CEASED = re.compile(
    r"Angaben zur Zweigniederlassung neu:\s*Der Geschäftsbetrieb der "
    r"Zweigniederlassung hat aufgehört\.\s*Sie kann mangels Zustimmung der "
    r"kantonalen Steuerverwaltung aber noch nicht gelöscht werden\.?",
    re.I,
)
_FR_SOCIAL_CAPITAL_CLASSES = re.compile(
    r"Le capital social de CHF\s+(?P<total>[\d'.]+)\s+est désormais composé de\s+"
    r"(?P<count1>[\d']+)\s+parts de CHF\s+(?P<nominal1>[\d'.]+),\s*"
    r"(?P<rights1>privilégiées quant au droit de vote),\s*et\s*"
    r"(?P<count2>[\d']+)\s+parts de CHF\s+(?P<nominal2>[\d'.]+),\s*"
    r"dont\s+(?P<holder>[^.]+?)\s+est titulaire\.?",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MULTI_CLASS_TRANSFER = re.compile(
    r"(?P<seller>[A-ZÀ-Ÿ][^,.;]+),\s*maintenant à\s+(?P<seller_place>[^,.;]+),\s*"
    r"cède\s+(?P<sold1>[\d']+)\s+parts de CHF\s+(?P<nominal1>[\d'.]+),\s*"
    r"privilégiées quant au droit de vote,\s*et\s+(?P<sold2>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal2>[\d'.]+),\s*à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du |de la |de l['’]|des |de |d['’])(?P<origin>[^,]+),\s*à\s*"
    r"(?P<buyer_place>[^,.;]+),\s*nouvel associé avec\s+(?P<buyer_count1>[\d']+)\s+"
    r"parts de CHF\s+(?P<buyer_nominal1>[\d'.]+),\s*privilégiées quant au droit de vote,\s*"
    r"et\s+(?P<buyer_count2>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal2>[\d'.]+),\s*"
    r"sans signature\.\s*(?P=seller) reste titulaire de\s+(?P<seller_count1>[\d']+)\s+"
    r"parts de CHF\s+(?P<seller_nominal1>[\d'.]+),\s*privilégiées quant au droit de vote,\s*"
    r"et\s+(?P<seller_count2>[\d']+)\s+parts de CHF\s+(?P<seller_nominal2>[\d'.]+)\.?",
    re.I | re.UNICODE,
)
_DE_LIQUIDATION_MEASURE_EXTENDED = re.compile(
    r"Mit Verfügung des (?P<authority>Handelsgerichtspräsidenten des Kantons St\.\s*Gallen) "
    r"vom (?P<order_date>\d{2}\.\d{2}\.\d{4}) war das Amt für Handelsregister und "
    r"Notariate des Kantons St\.?Gallen angewiesen worden,\s*(?P<liquidator>.+?)\s+als "
    r"Liquidator einzutragen\.\s*Gemäss Entscheid des Handelsgerichtspräsidenten vom "
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}) dauert die Massnahme,\s*bis die Liquidation "
    r"der Gesellschaft abgeschlossen ist,\s*längstens jedoch bis Ende\s+(?P<until_year>\d{4})\.\s*"
    r"\[bisher:.*?\]\.?",
    re.I | re.DOTALL,
)
_FR_OFFICIAL_DELETION_NO_OPPOSITION = re.compile(
    r"Aucune opposition motivée n['’]ayant été présentée,\s*la société est radiée "
    r"d['’]office,\s*conformément à l['’]art\.\s*159,\s*al\.\s*5,\s*let\.\s*a\s+aORC\.?",
    re.I,
)
_FR_FOUNDATION_TREASURER = re.compile(
    r"Le membre du conseil de fondation\s+(?P<name>[^.;]+?)\s+est nommé(?:e)?\s+"
    r"(?P<role>trésori(?:er|ère))\s+avec\s+(?P<sign>signature individuelle|"
    r"signature collective(?:\s+à\s+deux)?)\.?",
    re.I | re.UNICODE,
)
_FR_THREE_FOUNDATION_MEMBERS = re.compile(
    r"Nouveaux membres du conseil de fondation sans signature:\s*"
    r"(?P<name1>[^,]+),\s*(?:du |de la |de l['’]|des |de |d['’])(?P<origin1>[^,]+),\s*"
    r"à\s+(?P<place1>[^,]+),\s*(?P<name2>[^,]+),\s*"
    r"(?:du |de la |de l['’]|des |de |d['’])(?P<origin2>[^,]+),\s*à\s+"
    r"(?P<place2>[^,]+),\s*et\s+(?P<name3>[^,]+),\s*"
    r"(?:du |de la |de l['’]|des |de |d['’])(?P<origin3>[^,]+),\s*à\s+"
    r"(?P<place3>[^.]+)\.?",
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
    payload = {"name": name, "place": place, **(extra or {})}
    return Event(
        publication_id=publication_id,
        published_at=published_at,
        event_type=event_type,
        rule_id=rule_id,
        org_uid=org_uid,
        person_key=person_key(name=name, place=place),
        plz=plz,
        canton=canton,
        role=role,
        signing=signing,
        payload=payload,
    )


def extract_parser50_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 50."""
    events: list[Event] = []
    leftover = text

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_EXPIRED_CAPITAL_CLAUSE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.capital_clause_expired.v1",
                {
                    "kind": "authorized_capital_clause",
                    "action": "expired",
                    "reason": "authorization_period_elapsed",
                },
            )
        )

    match = _DE_COOPERATIVE_OBLIGATIONS.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "de.text.cooperative_obligations.v2",
                {
                    "kind": "member_obligations",
                    "action": "changed",
                    "obligations": match.group("obligations"),
                },
            )
        )

    match = _DE_CAPITAL_PAID_IN.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "de.text.share_capital_paid_in.v1",
                {
                    "kind": "capital_paid_in",
                    "currency": match.group("currency").upper(),
                    "amount": match.group("amount"),
                },
            )
        )

    match = _FR_FIRST_NAME_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.first_name_changed.v1",
                match.group("name").strip(),
                extra={
                    "action": "first_name_changed",
                    "previous": match.group("old_name").strip(),
                },
            )
        )

    match = _FR_ADMINISTRATION_PAIR.search(leftover)
    if match:
        consume(match)
        signing = _signing(match.group("sign"))
        people = (
            (match.group("name1").strip(), None, match.group("role1").strip(), {}),
            (
                match.group("name2").strip(),
                match.group("place2").strip(),
                "administrateur",
                {"heimat": match.group("origin2").strip()},
            ),
        )
        for name, place, role, extra in people:
            for event_type, rule_id in (
                ("officer_changed", "fr.persons.administration_pair.v3"),
                (
                    "signing_authority_changed",
                    "fr.persons.administration_pair_signing.v3",
                ),
            ):
                events.append(
                    _person_event(
                        publication_id,
                        published_at,
                        org_uid,
                        plz,
                        canton,
                        event_type,
                        rule_id,
                        name,
                        place=place,
                        role=role,
                        signing=signing,
                        extra=extra,
                    )
                )

    match = _FR_APPOINTED_WITH_SIGNING.search(leftover)
    if match:
        consume(match)
        signing = _signing(match.group("sign"))
        common = {
            "previous_signing": "procuration",
            "procuration_revoked": True,
        }
        for event_type in ("officer_changed", "signing_authority_changed"):
            events.append(
                _person_event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    event_type,
                    "fr.persons.appointed_signing.v2",
                    match.group("name").strip(),
                    role=match.group("role").strip(),
                    signing=signing,
                    extra=common,
                )
            )

    for pattern, rule_id in (
        (_FR_INTERMEDIATED_BEARER_SHARES, "fr.text.bearer_shares_authorized.v3"),
        (_DE_INTERMEDIATED_BEARER_SHARES, "de.text.bearer_shares_authorized.v3"),
    ):
        match = pattern.search(leftover)
        if not match:
            continue
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                rule_id,
                {
                    "kind": "bearer_shares_authorized",
                    "reason": "intermediated_securities",
                },
            )
        )
        break

    match = _DE_ECCLESIASTICAL_FOUNDATION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "organization_changed",
                "de.text.ecclesiastical_foundation.v1",
                {
                    "kind": "ecclesiastical_supervision",
                    "state_supervision": False,
                    "audit_required": False,
                    "supervisory_authority": match.group("authority").strip(),
                    "supervisory_office": match.group("office").strip(),
                    "previous_minimum_board_members": int(match.group("minimum")),
                    "board_minimum_removed": True,
                },
            )
        )

    match = _FR_SHARE_RESTRICTION_WITH_CAPITAL.search(leftover)
    if match:
        consume(match)
        total = match.group("total")
        paid = match.group("paid")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.share_transfer_restriction.v5",
                {
                    "kind": "share_transfer_restricted",
                    "action": "added",
                    "basis": "statutes",
                    "capital_total": total,
                    "paid": paid,
                    "paid_in_full": paid == total,
                    "shares_count": _count(match.group("capital_count")),
                    "nominal": match.group("capital_nominal"),
                },
            )
        )

    match = _DE_FORMER_DOMICILE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "address_changed",
                "de.text.domicile_removed.v1",
                {
                    "action": "removed",
                    "address": match.group("address").strip(),
                    "postal_code": match.group("postal_code"),
                    "town": match.group("town").strip(),
                },
            )
        )

    match = _DE_BRANCH_BUSINESS_CEASED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "branch_changed",
                "de.text.branch_closed_pending_deletion.v2",
                {
                    "action": "closed",
                    "business_operations_ceased": True,
                    "deletion_pending": True,
                    "reason": "cantonal_tax_authority_approval_pending",
                },
            )
        )

    match = _FR_SOCIAL_CAPITAL_CLASSES.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.social_capital_composition.v2",
                {
                    "kind": "share_structure",
                    "currency": "CHF",
                    "total": match.group("total"),
                    "holder": match.group("holder").strip(),
                    "share_classes": [
                        {
                            "count": _count(match.group("count1")),
                            "nominal": match.group("nominal1"),
                            "rights": match.group("rights1"),
                        },
                        {
                            "count": _count(match.group("count2")),
                            "nominal": match.group("nominal2"),
                        },
                    ],
                },
            )
        )

    match = _FR_ASSOCIATE_MULTI_CLASS_TRANSFER.search(leftover)
    if match:
        consume(match)
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        events.append(
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.associate_multi_class_transfer.v1",
                seller,
                place=match.group("seller_place").strip(),
                role="associé",
                extra={
                    "action": "domicile_and_shareholding_changed",
                    "transferred_share_classes": [
                        {
                            "count": _count(match.group("sold1")),
                            "nominal": match.group("nominal1"),
                            "rights": "privilégiées quant au droit de vote",
                        },
                        {
                            "count": _count(match.group("sold2")),
                            "nominal": match.group("nominal2"),
                        },
                    ],
                    "share_classes": [
                        {
                            "count": _count(match.group("seller_count1")),
                            "nominal": match.group("seller_nominal1"),
                            "rights": "privilégiées quant au droit de vote",
                        },
                        {
                            "count": _count(match.group("seller_count2")),
                            "nominal": match.group("seller_nominal2"),
                        },
                    ],
                },
            )
        )
        events.append(
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.associate_multi_class_transfer.v1",
                buyer,
                place=match.group("buyer_place").strip(),
                role="associé",
                extra={
                    "action": "shares_received",
                    "heimat": match.group("origin").strip(),
                    "without_signature": True,
                    "share_classes": [
                        {
                            "count": _count(match.group("buyer_count1")),
                            "nominal": match.group("buyer_nominal1"),
                            "rights": "privilégiées quant au droit de vote",
                        },
                        {
                            "count": _count(match.group("buyer_count2")),
                            "nominal": match.group("buyer_nominal2"),
                        },
                    ],
                },
            )
        )

    match = _DE_LIQUIDATION_MEASURE_EXTENDED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.liquidation_measure_extended.v1",
                {
                    "kind": "liquidation_measure_extended",
                    "authority": match.group("authority").strip(),
                    "original_order_date": _iso_date(match.group("order_date")),
                    "decision_date": _iso_date(match.group("decision_date")),
                    "liquidator": match.group("liquidator").strip(),
                    "until": f"{match.group('until_year')}-12-31",
                    "completion_may_end_measure_earlier": True,
                },
            )
        )

    match = _FR_OFFICIAL_DELETION_NO_OPPOSITION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "company_deleted",
                "fr.text.official_deletion_no_opposition.v1",
                {
                    "reason": "no_reasoned_opposition",
                    "action": "deleted_ex_officio",
                    "legal_basis": "art. 159 al. 5 let. a aORC",
                },
            )
        )

    match = _FR_FOUNDATION_TREASURER.search(leftover)
    if match:
        consume(match)
        signing = _signing(match.group("sign"))
        for event_type, rule_id in (
            ("officer_changed", "fr.persons.foundation_treasurer.v1"),
            (
                "signing_authority_changed",
                "fr.persons.foundation_treasurer_signing.v1",
            ),
        ):
            events.append(
                _person_event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    event_type,
                    rule_id,
                    match.group("name").strip(),
                    role=match.group("role").strip(),
                    signing=signing,
                    extra={"previous": "membre du conseil de fondation"},
                )
            )

    match = _FR_THREE_FOUNDATION_MEMBERS.search(leftover)
    if match:
        consume(match)
        for index in range(1, 4):
            events.append(
                _person_event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.foundation_members_without_signature.v1",
                    match.group(f"name{index}").strip(),
                    place=match.group(f"place{index}").strip(),
                    role="membre du conseil de fondation",
                    extra={
                        "heimat": match.group(f"origin{index}").strip(),
                        "without_signature": True,
                    },
                )
            )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
