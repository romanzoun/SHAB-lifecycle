from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_BANKRUPTCY_OPENED_AND_SUSPENDED = re.compile(
    r"^Par décision du (?P<bankruptcy_authority>.+?) du "
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*la société a été déclarée en "
    r"faillite par défaut des parties avec effet à partir du "
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*à\s*"
    r"(?P<effective_time>\d{1,2}h\d{2})\.\s*Le président du "
    r"(?P<suspension_authority>.+?) a prononcé le "
    r"(?P<suspension_date>\d{2}\.\d{2}\.\d{4}) l['’]effet suspensif de la "
    r"faillite rendue le (?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_NAME_AND_SEAT_CHANGED = re.compile(
    r"^Nouvelle raison sociale de l['’]associée?\s+(?P<previous>.+?):\s*"
    r"(?P<name>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s*"
    r"et nouveau siège:\s*(?P<place>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBERS_WITHOUT_SIGNATURE_PAIR = re.compile(
    r"^Nouveaux membres du conseil de fondation sans signature:\s*"
    r"(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s*(?P<place1>[^,.;]+),\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s*(?P<place2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBERS_DE_ET_A_PAIR = re.compile(
    r"^(?P<name1>[^,.;]+),\s*de et à\s*(?P<place1>[^,.;]+),\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s*(?P<place2>[^,.;]+),\s*"
    r"sont membres du conseil de fondation\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCHES_ADDED_SEQUENCE = re.compile(
    r"^Nouvelle succursale:\s*(?P<items>[^\[]+?)\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_ITEM = re.compile(
    r"(?P<place>[^.]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)(?:\.\s*|$)",
    re.I | re.UNICODE,
)
_FR_STATUTES_CHANGED_ORDINAL_DATE = re.compile(
    r"^Statuts modifiés le\s+(?P<date>1er\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_NOMINAL_REDUCTION_WITH_DISTRIBUTION = re.compile(
    r"^Bei der Kapitalherabsetzung vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"wird der Nennwert der\s+(?P<count>[\d']+)\s+(?P<share_kind>.+?)\s+zu CHF\s+"
    r"(?P<from_nominal>[\d'.]+)\s+auf CHF\s+(?P<to_nominal>[\d'.]+)\s+"
    r"herabgesetzt und der Herabsetzungsbetrag von CHF\s+(?P<reduction>[\d'.]+)\s+"
    r"im Umfang von CHF\s+(?P<cash>[\d'.]+)\s+in bar an die Aktionäre "
    r"zurückbezahlt sowie im Umfang von CHF\s+(?P<credit>[\d'.]+)\s+zur Gutschrift "
    r"auf Aktionärskonten verwendet;\s*die Beachtung der gesetzlichen Vorschriften "
    r"von (?P<legal_basis>Art\.\s*734 OR) wird mit öffentlicher Urkunde vom\s+"
    r"(?P<confirmation_date>\d{2}\.\d{2}\.\d{4})\s+festgestellt\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PRESIDENT_AND_NAMED_SECRETARY = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s*"
    r"(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{1,3}),\s*"
    r"(?P<president_role>président(?:e)?),\s*et\s*(?P<secretary>[^,.;]+),\s*"
    r"nommé(?:e)?\s+(?P<secretary_role>secrétaire),\s*lesquels signent\s*"
    r"(?P<sign>individuellement)\.?$",
    re.I | re.UNICODE,
)
_FR_AUTHORIZED_CAPITAL_CLAUSE_REMOVED = re.compile(
    r"^Suppression de la clause statutaire relative à l['’]augmentation autorisée "
    r"du capital fondée sur la décision d['’]autorisation du\s*"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_EXTENDED_BY_DECISION = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?:der|die|das)\s+(?P<authority>.+?)\s+die gewährte definitive "
    r"Nachlassstundung um\s+(?P<duration>\d+|ein(?:e|en)?|zwei|drei|vier|fünf|sechs)\s+"
    r"(?:Monat|Monate|Monaten) bis zum\s+(?P<until>\d{2}\.\d{2}\.\d{4})\s+verlängert\.?$",
    re.I | re.UNICODE,
)
_FR_OFFICER_DOMICILE_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:N[°ºo]|no|n°)?\s*(?P<entry>[\d']+)\s+du\s*"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée comme suit:\s*"
    r"l['’](?P<role>administratrice|administrateur)\s+(?P<name>[^,.;]+)\s+"
    r"est domicilié(?:e)? à\s+(?P<place>[^()]+?)\s*"
    r"\(et non à\s+(?P<previous_place>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_FULL_NAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:N[°ºo]|no|n°)?\s*(?P<entry>[\d']+)\s+du\s*"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que le "
    r"nom complet de\s+(?P<previous>[^,.;]+?)\s+est\s+(?P<name>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDATION_ASSET_TRANSFER_WITH_SUPERVISORY_ORDER = re.compile(
    r"^Vermögensübertragung:\s*Die Stiftung überträgt gemäss "
    r"Vermögensübertragungsvertrag vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+und "
    r"Inventar per\s+(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+sowie Verfügung "
    r"der Aufsichtsbehörde vom\s+(?P<order_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven "
    r"von CHF\s+(?P<assets>[\d'.]+)\s+und Passiven \(Fremdkapital\) von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_FULL_NAME_COMPLETED = re.compile(
    r"^L['’]inscription\s+(?:N[°ºo]|no|n°)?\s*(?P<entry>[\d']+)\s+du\s*"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est complétée comme suit:\s*"
    r"le nom du gérant est\s+(?P<name>[^()]+?)\s*"
    r"\(et non\s+(?P<previous>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_SEAT_CHANGED = re.compile(
    r"^Nouvelle succursale:\s*(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s*"
    r"\[précédemment:\s*(?P<previous_place>[^()]+?)\s*"
    r"\((?P<previous_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\]\.?$",
    re.I | re.UNICODE,
)
_DE_PERSON_PREVIOUS_TEXT_COMPLETED = re.compile(
    r"^Bei der Mutation von\s+(?P<name>[^,]+,\s*[^,]+),\s*von\s+"
    r"(?P<origin>[^,]+),\s*in\s+(?P<place>[^,]+),\s*"
    r"(?P<role>[^,]+),\s*mit\s+(?P<sign>Einzelunterschrift),\s*"
    r"mit einem Stammanteil von CHF\s+(?P<share1>[\d'.]+)\s+und mit einem "
    r"Stammanteil von CHF\s+(?P<share2>[\d'.]+)\s+wurde der Bishertext nicht "
    r"vollständig wiedergegeben nämlich:\s*bisher:\s*in\s+"
    r"(?P<previous_place>[^,]+),\s*mit einem Stammanteil von CHF\s+"
    r"(?P<previous_share>[\d'.]+)\.?$",
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
_DE_NUMBERS = {
    "ein": 1,
    "eine": 1,
    "einen": 1,
    "zwei": 2,
    "drei": 3,
    "vier": 4,
    "fünf": 5,
    "sechs": 6,
}


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{year}-{month}-{day}"


def _french_date(raw: str) -> str:
    day, month, year = raw.lower().replace("1er", "1").split()
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


def extract_parser83_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 83."""
    del language  # Historical publications can mix languages.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_BANKRUPTCY_OPENED_AND_SUSPENDED.search(leftover)
    if match:
        consume(match)
        common = {
            "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
            "scope": "company",
        }
        events.extend(
            [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "status_changed", "fr.text.company_bankruptcy_opened_by_default.v1",
                    {
                        "kind": "bankruptcy_opened",
                        "decision_date": _iso_date(match.group("decision_date")),
                        "effective_date": _iso_date(match.group("effective_date")),
                        "effective_time": match.group("effective_time").replace("h", ":"),
                        "authority": match.group("bankruptcy_authority").strip(),
                        "judgment_by_default": True,
                        "scope": "company",
                    },
                ),
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "status_changed", "fr.text.bankruptcy_effect_suspended_after_default.v1",
                    {
                        "kind": "bankruptcy_effect_suspended",
                        "decision_date": _iso_date(match.group("suspension_date")),
                        "authority": match.group("suspension_authority").strip(),
                        **common,
                    },
                ),
            ]
        )

    match = _FR_ASSOCIATE_NAME_AND_SEAT_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.associate_name_and_seat_changed.v1",
                match.group("name"), place=match.group("place"), uid=match.group("uid"),
                role="associée",
                extra={
                    "action": "name_and_seat_changed",
                    "previous_name": match.group("previous").strip(),
                },
            )
        )

    match = _FR_FOUNDATION_MEMBERS_WITHOUT_SIGNATURE_PAIR.search(leftover)
    if match:
        consume(match)
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.foundation_members_without_signature_pair.v1",
                    match.group(f"name{index}"), place=match.group(f"place{index}"),
                    role="membre du conseil de fondation",
                    extra={
                        "action": "appointed",
                        "heimat": match.group(f"origin{index}").strip(),
                        "without_signature": True,
                    },
                )
            )

    match = _FR_FOUNDATION_MEMBERS_DE_ET_A_PAIR.search(leftover)
    if match:
        consume(match)
        people = (
            (match.group("name1"), match.group("place1"), match.group("place1")),
            (match.group("name2"), match.group("place2"), match.group("origin2")),
        )
        for name, place, origin in people:
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.foundation_members_de_et_a_pair.v1",
                    name, place=place, role="membre du conseil de fondation",
                    signing="Kollektivunterschrift zu zweien",
                    extra={"action": "appointed", "heimat": origin.strip()},
                )
            )

    match = _FR_BRANCH_SEAT_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", "fr.text.branch_seat_changed.v1",
                {
                    "action": "seat_changed",
                    "place": match.group("place").strip(),
                    "uid": match.group("uid"),
                    "previous_place": match.group("previous_place").strip(),
                    "previous_uid": match.group("previous_uid"),
                },
            )
        )

    match = _FR_BRANCHES_ADDED_SEQUENCE.search(leftover)
    if match:
        items = list(_FR_BRANCH_ITEM.finditer(match.group("items")))
        covered = "".join(item.group(0) for item in items).strip(" .")
        expected = match.group("items").strip(" .")
        if items and covered == expected:
            consume(match)
            for item in items:
                events.append(
                    _event(
                        publication_id, published_at, org_uid, plz, canton,
                        "branch_changed", "fr.text.branches_added_sequence.v1",
                        {
                            "action": "added",
                            "place": item.group("place").strip(),
                            "uid": item.group("uid"),
                        },
                    )
                )

    match = _FR_STATUTES_CHANGED_ORDINAL_DATE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "fr.text.statutes_ordinal_date.v1",
                {"date": _french_date(match.group("date")), "raw": match.group(0)},
            )
        )

    match = _DE_NOMINAL_REDUCTION_WITH_DISTRIBUTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.nominal_reduction_with_distribution.v1",
                {
                    "kind": "nominal_value_reduction",
                    "date": _iso_date(match.group("date")),
                    "currency": "CHF",
                    "shares_count": _count(match.group("count")),
                    "share_kind": match.group("share_kind").strip(),
                    "from_nominal": match.group("from_nominal"),
                    "to_nominal": match.group("to_nominal"),
                    "reduction_amount": match.group("reduction"),
                    "cash_repayment": match.group("cash"),
                    "shareholder_account_credit": match.group("credit"),
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                    "confirmation_date": _iso_date(match.group("confirmation_date")),
                },
            )
        )

    match = _FR_ADMINISTRATION_PRESIDENT_AND_NAMED_SECRETARY.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_president_and_named_secretary.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("president"),
                    place=match.group("place"), role=match.group("president_role").lower(),
                    signing="Einzelunterschrift",
                    extra={
                        "action": "appointed",
                        "heimat": match.group("origin").strip(),
                        "country": match.group("country"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("secretary"),
                    role=match.group("secretary_role").lower(),
                    signing="Einzelunterschrift", extra={"action": "appointed"},
                ),
            ]
        )

    match = _FR_AUTHORIZED_CAPITAL_CLAUSE_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.authorized_capital_clause_removed.v1",
                {
                    "kind": "authorized_capital_clause",
                    "action": "removed",
                    "authorization_date": _iso_date(match.group("date")),
                },
            )
        )

    match = _DE_DEFINITIVE_MORATORIUM_EXTENDED_BY_DECISION.search(leftover)
    if match:
        consume(match)
        duration_raw = match.group("duration").lower()
        duration = int(duration_raw) if duration_raw.isdigit() else _DE_NUMBERS[duration_raw]
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.definitive_moratorium_extended_by_decision.v1",
                {
                    "kind": "composition_moratorium_extended",
                    "moratorium_type": "definitive",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "authority": match.group("authority").strip(),
                    "duration_months": duration,
                    "until": _iso_date(match.group("until")),
                },
            )
        )

    match = _FR_OFFICER_DOMICILE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.officer_domicile_corrected.v1",
                match.group("name"), place=match.group("place"), role=match.group("role").lower(),
                extra={
                    "action": "domicile_corrected",
                    "previous_place": match.group("previous_place").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                },
            )
        )

    match = _FR_PERSON_FULL_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.full_name_corrected.v1", match.group("name"),
                extra={
                    "action": "name_corrected",
                    "previous_name": match.group("previous").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                },
            )
        )

    match = _DE_FOUNDATION_ASSET_TRANSFER_WITH_SUPERVISORY_ORDER.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.foundation_asset_transfer_supervisory_order.v1",
                {
                    "date": _iso_date(match.group("date")),
                    "inventory_date": _iso_date(match.group("inventory_date")),
                    "supervisory_order_date": _iso_date(match.group("order_date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "currency": "CHF",
                    "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration": match.group("consideration"),
                },
            )
        )

    match = _FR_MANAGER_FULL_NAME_COMPLETED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.manager_full_name_completed.v1",
                match.group("name"), role="gérant",
                extra={
                    "action": "name_completed",
                    "previous_name": match.group("previous").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                },
            )
        )

    match = _DE_PERSON_PREVIOUS_TEXT_COMPLETED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "de.persons.previous_text_completed.v1",
                match.group("name"), place=match.group("place"), role=match.group("role"),
                signing="Einzelunterschrift",
                extra={
                    "action": "previous_text_completed",
                    "heimat": match.group("origin").strip(),
                    "shares": [match.group("share1"), match.group("share2")],
                    "previous_place": match.group("previous_place").strip(),
                    "previous_shares": [match.group("previous_share")],
                    "currency": "CHF",
                },
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
