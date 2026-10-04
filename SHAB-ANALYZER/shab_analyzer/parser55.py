from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_SHARE_TRANSFER_RESTRICTION = re.compile(
    r"(?P<new>Nouveau\s+)?avec restrictions quant à la transmissibilité "
    r"selon statuts\.?,?",
    re.I,
)
_FR_ADMINISTRATION_THREE = re.compile(
    r"Administration:\s*(?P<name1>[^,]+),\s*maintenant domicilié(?:e)? à\s*"
    r"(?P<place1>[^,]+),\s*nommé(?:e)?\s+(?P<role1>[^,]+),\s*"
    r"(?P<name2>[^,]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,]+),\s*à\s+(?P<place2>.+?),\s*"
    r"(?P<country2>[A-Z]{2,3}),\s*et\s+(?P<name3>[^,]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin3>[^,]+),\s*à\s*"
    r"(?P<place3>.+?),\s*(?P<country3>[A-ZÀ-Ÿ][A-Za-zÀ-ÿ'’ -]+),\s*"
    r"lesquels signent\s+(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?,?",
    re.I | re.UNICODE,
)
_FR_STANDALONE_GROUP_SIGNING = re.compile(
    r"avec signature (?P<sign>individuelle|collective(?:\s+à\s+deux)?)\.?,?",
    re.I,
)
_FR_LIQUIDATORS_CONTINUE_SIGNING = re.compile(
    r"Liquidateurs:\s*les administrateurs\s+(?P<name1>[^,]+),\s*"
    r"lequel continue à signer\s+(?P<sign1>individuellement|collectivement(?:\s+à\s+deux)?),?\s*"
    r"et\s+(?P<name2>[^,]+),\s*lequel continue à signer\s+"
    r"(?P<sign2>individuellement|collectivement(?:\s+à\s+deux)?)\.?,?",
    re.I | re.UNICODE,
)
_FR_COMMITTEE_MEMBER_WITHOUT_SIGNATURE = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,]+),\s*à\s+(?P<place>[^,.;]+),\s*est\s+"
    r"(?P<role>membre du comité),\s*sans signature(?: sociale)?\.?,?",
    re.I | re.UNICODE,
)
_IT_FUSION_SAME_OWNER = re.compile(
    r"Fusione:\s*ripresa di attivi e passivi di\s+(?P<absorbed_name>.+?),\s*"
    r"in\s+(?P<absorbed_place>[^()]+?)\s*\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"secondo il contratto di fusione del\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s*"
    r"e bilancio al\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta attivi "
    r"per CHF\s+(?P<assets>[\d'.]+)\s+e passivi verso terzi per CHF\s+"
    r"(?P<liabilities>[\d'.]+)\.\s*La totalità del capitale azionario delle due "
    r"società è detenuta dallo stesso azionista,\s*la fusione avviene dunque senza "
    r"aumento del capitale e senza attribuzione di azioni\.?,?",
    re.I | re.DOTALL,
)
_FR_LEGAL_BEARER_CONVERSION_THREE_CLASSES = re.compile(
    r"Le\s+(?P<date>\d{2}\.\d{2}\.\d{4}),\s*les\s+(?P<from_count>[\d']+)\s+"
    r"actions au porteur ont été converties de par la loi en actions nominatives\.\s*"
    r"Les statuts de la société n['’]ont pas encore été adaptés à la conversion,\s*"
    r"mais devront l['’]être lors de la prochaine modification\.\s*"
    r"Capital-actions:\s*CHF\s+(?P<total>[\d'.]+),\s*libéré à concurrence de CHF\s+"
    r"(?P<paid>[\d'.]+),\s*divisé en\s+(?P<count1>[\d']+)\s+actions de CHF\s+"
    r"(?P<nominal1>[\d'.]+)\s+(?P<rights1>à droit de vote privilégié),\s*"
    r"(?P<kind1>nominatives),\s*(?P<restriction1>liées selon statuts),\s*"
    r"(?P<count2>[\d']+)\s+actions de CHF\s+(?P<nominal2>[\d'.]+),\s*"
    r"(?P<kind2>nominatives),\s*et\s+(?P<count3>[\d']+)\s+actions de CHF\s+"
    r"(?P<nominal3>[\d'.]+),\s*(?P<kind3>nominatives)\.?,?",
    re.I,
)
_DE_LEGAL_BEARER_CONVERSION_ADAPTED = re.compile(
    r"Durch Beschluss der Generalversammlung vom\s+"
    r"(?P<adaptation_date>\d{2}\.\d{2}\.\d{4})\s+wurden die Statuten der "
    r"Gesellschaft an die am\s+(?P<conversion_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"von Gesetzes wegen erfolgte Umwandlung der Inhaberaktien in Namenaktien angepasst\.?,?",
    re.I,
)
_DE_COMPOSITION_AGREEMENT_CONFIRMED = re.compile(
    r"Mit Urteil vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+den Nachlassvertrag mit\s+"
    r"(?P<agreement_type>Dividendenvergleich)\s+bestätigt\.?,?",
    re.I,
)
_DE_REMOVED_COMPOSITION_MORATORIUM = re.compile(
    r"\[gestrichen:\s*Mit Verfügung vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+(?:"
    r"die definitive Nachlassstundung um\s+(?P<duration_ext>\w+)\s+Monate bis\s+"
    r"(?P<until_ext>\d{2}\.\d{2}\.\d{4})\s+(?P<action_ext>verlängert)|"
    r"eine definitive Nachlassstundung von\s+(?P<duration_grant>\w+)\s+Monaten bis zum\s+"
    r"(?P<until_grant>\d{2}\.\d{2}\.\d{4})\s+(?P<action_grant>gewährt)"
    r")\.\]\.?,?",
    re.I | re.DOTALL,
)
_FR_BRANCH_SEAT_TRANSFERRED = re.compile(
    r"La succursale de\s+(?P<from_place>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+a transféré son siège à\s+"
    r"(?P<to_place>.+?)\s*\(FOSC du\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"Id\s+(?P<notice_id>\d+)\)\.?,?",
    re.I,
)
_DE_ASSET_TRANSFER_NAMED_SOURCE = re.compile(
    r"Vermögensübertragung:\s*Die\s+(?P<source>.+?)\s+überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+und Inventar per\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+sowie Beschluss der\s+"
    r"(?P<authority>.+?)\s+vom\s+(?P<resolution_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+und Passiven \(Fremdkapital\) von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>.+?)(?=\s*$)",
    re.I | re.DOTALL,
)
_FR_PERSON_FIRST_NAME_CORRECTION = re.compile(
    r"Rectificatif:\s*l['’]inscription no\s+(?P<number>[\d']+)\s+du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<publication_date>\d{2}\.\d{2}\.\d{4})\s+p\.\s*"
    r"(?P<publication_page>\d+)/(?P<publication_id>\d+)\)\s+est rectifiée en ce "
    r"sens que l['’](?P<role>associé-gérant|associée-gérante)\s+"
    r"(?P<surname>.+?)\s+se nomme\s+(?P<first_name>[^ (]+)\s+"
    r"\(et non\s+(?P<previous_first_name>[^ )]+)\s+comme publié\)\.?,?",
    re.I | re.UNICODE,
)
_IT_NEW_REGISTERED_SHARES_FROM_MIXED_CLASSES = re.compile(
    r"Nuove azioni:\s*(?P<to_count>[\d']+)\s+azioni\s+"
    r"(?P<to_kind>nominative)\s+da CHF\s+(?P<to_nominal>[\d'.]+)\s*"
    r"\[finora:\s*(?P<from_count1>[\d']+)\s+azioni\s+"
    r"(?P<from_kind1>nominative)\s+da CHF\s+(?P<from_nominal1>[\d'.]+)\s+e\s+"
    r"(?P<from_count2>[\d']+)\s+azioni\s+(?P<from_kind2>al portatore)\s+"
    r"da CHF\s+(?P<from_nominal2>[\d'.]+)\]\.?",
    re.I,
)
_FR_MERGER_SUCCESSOR_DELETION = re.compile(
    r"Les actifs et les passifs envers les tiers sont repris par la société\s+"
    r"(?P<successor>.+?),\s*à\s+(?P<old_place>.+?)\s+"
    r"\(nouvellement à\s+(?P<new_place>[^)]+)\)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"La société est radiée par suite de fusion\.?,?",
    re.I | re.DOTALL,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{year}-{month}-{day}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _duration(raw: str) -> int | None:
    normalized = raw.lower()
    if normalized.isdigit():
        return int(normalized)
    return {"einen": 1, "einem": 1, "sechs": 6}.get(normalized)


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


def extract_parser55_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 55."""
    events: list[Event] = []
    leftover = text

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_SHARE_TRANSFER_RESTRICTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "fr.text.share_transfer_restriction.v6",
                {
                    "kind": "share_transfer_restriction",
                    "action": "added",
                    "basis": "statutes",
                    "wording_marked_new": bool(match.group("new")),
                },
            )
        )

    match = _FR_ADMINISTRATION_THREE.search(leftover)
    if match:
        consume(match)
        signing = _signing(match.group("sign"))
        people = (
            (
                match.group("name1"), match.group("place1"), match.group("role1"),
                {"domicile_changed": True},
            ),
            (
                match.group("name2"), match.group("place2"), "administrateur",
                {
                    "heimat": match.group("origin2").strip(),
                    "country": match.group("country2").strip(),
                },
            ),
            (
                match.group("name3"), match.group("place3"), "administrateur",
                {
                    "heimat": match.group("origin3").strip(),
                    "country": match.group("country3").strip(),
                },
            ),
        )
        for name, place, role, extra in people:
            for event_type in ("officer_changed", "signing_authority_changed"):
                events.append(
                    _person_event(
                        publication_id, published_at, org_uid, plz, canton,
                        event_type, "fr.persons.administration_three.v1", name,
                        place=place, role=role.strip(), signing=signing, extra=extra,
                    )
                )

    match = _FR_LIQUIDATORS_CONTINUE_SIGNING.search(leftover)
    if match:
        consume(match)
        for index in (1, 2):
            name = match.group(f"name{index}")
            signing = _signing(match.group(f"sign{index}"))
            for event_type in ("officer_changed", "signing_authority_changed"):
                events.append(
                    _person_event(
                        publication_id, published_at, org_uid, plz, canton,
                        event_type, "fr.persons.liquidators_continue_signing.v1", name,
                        role="administrateur et liquidateur", signing=signing,
                        extra={"continues_signing": True},
                    )
                )

    match = _FR_COMMITTEE_MEMBER_WITHOUT_SIGNATURE.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.committee_member_without_signature.v1",
                match.group("name"), place=match.group("place"),
                role=match.group("role"),
                extra={
                    "heimat": match.group("origin").strip(),
                    "without_signature": True,
                },
            )
        )

    match = _IT_FUSION_SAME_OWNER.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_merged", "it.text.fusion_same_owner.v1",
                {
                    "kind": "absorption",
                    "absorbed_name": match.group("absorbed_name").strip(),
                    "absorbed_place": match.group("absorbed_place").strip(),
                    "absorbed_uid": match.group("absorbed_uid"),
                    "agreement_date": _iso_date(match.group("agreement_date")),
                    "balance_date": _iso_date(match.group("balance_date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "same_shareholder": True,
                    "capital_increase": False,
                    "share_allocation": False,
                },
            )
        )

    match = _FR_LEGAL_BEARER_CONVERSION_THREE_CLASSES.search(leftover)
    if match:
        consume(match)
        total = match.group("total")
        paid = match.group("paid")
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.legal_bearer_conversion.v9",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _iso_date(match.group("date")),
                    "from_count": _count(match.group("from_count")),
                    "from_kind": "actions au porteur",
                    "to_kind": "actions nominatives",
                    "capital_total": total,
                    "paid": paid,
                    "paid_in_full": paid == total,
                    "statutes_adapted": False,
                    "share_classes": [
                        {
                            "count": _count(match.group("count1")),
                            "nominal": match.group("nominal1"),
                            "kind": match.group("kind1"),
                            "rights": match.group("rights1"),
                            "restriction": match.group("restriction1"),
                        },
                        {
                            "count": _count(match.group("count2")),
                            "nominal": match.group("nominal2"),
                            "kind": match.group("kind2"),
                        },
                        {
                            "count": _count(match.group("count3")),
                            "nominal": match.group("nominal3"),
                            "kind": match.group("kind3"),
                        },
                    ],
                },
            )
        )

    match = _DE_LEGAL_BEARER_CONVERSION_ADAPTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.legal_bearer_conversion_adapted.v4",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _iso_date(match.group("conversion_date")),
                    "adaptation_date": _iso_date(match.group("adaptation_date")),
                    "from_kind": "Inhaberaktien",
                    "to_kind": "Namenaktien",
                    "statutes_adapted": True,
                },
            )
        )

    match = _DE_COMPOSITION_AGREEMENT_CONFIRMED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.composition_agreement_confirmed.v1",
                {
                    "kind": "composition_agreement_confirmed",
                    "decision_date": _iso_date(match.group("date")),
                    "authority": match.group("authority").strip(),
                    "agreement_type": match.group("agreement_type"),
                },
            )
        )

    while True:
        match = _DE_REMOVED_COMPOSITION_MORATORIUM.search(leftover)
        if not match:
            break
        extended = bool(match.group("action_ext"))
        duration = match.group("duration_ext") or match.group("duration_grant")
        until = match.group("until_ext") or match.group("until_grant")
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.composition_moratorium_removed.v1",
                {
                    "kind": (
                        "composition_moratorium_extended"
                        if extended
                        else "composition_moratorium_granted"
                    ),
                    "action": "removed",
                    "decision_date": _iso_date(match.group("date")),
                    "until": _iso_date(until),
                    "duration_months": _duration(duration),
                    "authority": match.group("authority").strip(),
                    "historical_entry": True,
                },
            )
        )

    match = _FR_BRANCH_SEAT_TRANSFERRED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "seat_changed", "fr.text.branch_seat_transferred.v1",
                {
                    "scope": "branch",
                    "branch_uid": match.group("uid"),
                    "from": match.group("from_place").strip(),
                    "to": match.group("to_place").strip(),
                    "source_notice_date": _iso_date(match.group("notice_date")),
                    "source_notice_id": match.group("notice_id"),
                },
            )
        )

    match = _DE_ASSET_TRANSFER_NAMED_SOURCE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.asset_transfer_named_source.v1",
                {
                    "source": match.group("source").strip(),
                    "date": _iso_date(match.group("date")),
                    "inventory_date": _iso_date(match.group("inventory_date")),
                    "resolution_authority": match.group("authority").strip(),
                    "resolution_date": _iso_date(match.group("resolution_date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration": match.group("consideration").strip().rstrip("."),
                },
            )
        )

    match = _FR_PERSON_FIRST_NAME_CORRECTION.search(leftover)
    if match:
        consume(match)
        name = f"{match.group('surname').strip()} {match.group('first_name').strip()}"
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.first_name_correction.v1", name,
                role=match.group("role"),
                extra={
                    "action": "first_name_corrected",
                    "previous_first_name": match.group("previous_first_name"),
                    "entry_number": match.group("number"),
                    "entry_date": _iso_date(match.group("date")),
                    "source_notice_date": _iso_date(match.group("publication_date")),
                    "source_notice_page": match.group("publication_page"),
                    "source_notice_id": match.group("publication_id"),
                },
            )
        )

    match = _IT_NEW_REGISTERED_SHARES_FROM_MIXED_CLASSES.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "it.text.registered_shares_from_mixed_classes.v1",
                {
                    "kind": "bearer_to_registered_conversion",
                    "to_count": _count(match.group("to_count")),
                    "to_kind": match.group("to_kind"),
                    "to_nominal": match.group("to_nominal"),
                    "from_share_classes": [
                        {
                            "count": _count(match.group("from_count1")),
                            "kind": match.group("from_kind1"),
                            "nominal": match.group("from_nominal1"),
                        },
                        {
                            "count": _count(match.group("from_count2")),
                            "kind": match.group("from_kind2"),
                            "nominal": match.group("from_nominal2"),
                        },
                    ],
                },
            )
        )

    match = _FR_MERGER_SUCCESSOR_DELETION.search(leftover)
    if match:
        consume(match)
        common = {
            "successor": match.group("successor").strip(),
            "successor_uid": match.group("uid"),
            "successor_previous_place": match.group("old_place").strip(),
            "successor_place": match.group("new_place").strip(),
        }
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_merged", "fr.text.merger_successor_deletion.v1",
                {"kind": "absorbed_into", **common},
            )
        )
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_deleted", "fr.text.merger_successor_deletion.v1",
                {"reason": "merger", **common},
            )
        )

    match = _FR_STANDALONE_GROUP_SIGNING.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", "fr.persons.group_signing.v1",
                {
                    "scope": "previously_named_officers",
                    "signing": _signing(match.group("sign")),
                },
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
