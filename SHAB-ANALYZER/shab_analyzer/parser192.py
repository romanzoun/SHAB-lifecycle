from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_NAME_AND_DOMICILE_CHANGED = re.compile(
    r"^(?P<previous_name>[^,.;]+?)\s+porte désormais le nom et le prénom de\s+"
    r"(?P<name>[^,.;]+),\s*elle est maintenant domiciliée à\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_ORGANIZATION_CLAUSE_REMOVED = re.compile(
    r"^Organisation neu:\s*\[Streichung aufgrund neuer "
    r"Eintragungsvorschriften\]\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_NAME_CORRECTED = re.compile(
    r"^R[ée]ctification:\s*le n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\)\s+est r[ée]ctifiée dans ce sens:\s*"
    r"(?P<name>[^,.;]+),\s*(?P<role>administratrice?),\s*"
    r"signature individuelle\s*\(et non pas\s+"
    r"(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_WITH_PRESIDENT = re.compile(
    r"^Nouvelle administratrice (?:avec signature collective à deux,\s*)?"
    r"toutefois avec le/la président\(e\):\s*"
    r"(?P<name>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s*(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PRESIDENT_AND_SECRETARY = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s*"
    r"(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{1,3}),\s*président\s+et\s+"
    r"(?P<secretary>[^,;]+?),\s*nommé secrétaire,\s*"
    r"lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ADMINISTRATORS_NOT_WITH_EACH_OTHER = re.compile(
    r"^Nouveaux administrateurs (?:avec signature collective à deux\s+)?"
    r"toutefois pas entre eux:\s*"
    r"(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s*(?P<place1>[^,.;]+),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s*(?P<place2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_MIXED_SIGNING = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*à\s*"
    r"(?P<place1>[^,.;]+),\s*(?P<country1>[A-Z]{1,3}),\s*président,\s*"
    r"(?P<director>[^,.;]+),\s*nommée en outre directrice,\s*"
    r"lesquels signent individuellement,\s*"
    r"(?P<name3>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin3>[^,.;]+),\s*à\s*(?P<place3>[^,.;]+),\s*"
    r"(?P<country3>[A-Z]{1,3}),\s*"
    r"(?P<name4>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin4>[^,.;]+),\s*à\s*(?P<place4>[^,.;]+),\s*"
    r"(?P<country4>[A-Z]{1,3}),\s*et\s*"
    r"(?P<name5>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin5>[^,.;]+),\s*à\s*(?P<place5>[^,.;]+),\s*"
    r"(?P<country5>[A-Z]{1,3}),\s*lesquels n['’]exercent pas la signature "
    r"sociale\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_PRESIDENCY_SWAPPED = re.compile(
    r"^Les membres du conseil(?! de fondation)\s+"
    r"(?P<president>[^,.;]+),\s*nommé président\s+et\s+"
    r"(?P<previous_president>[^,.;]+),\s*jusqu['’]ici président,\s*"
    r"continuent à signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATION_ASSET_TRANSFER_NO_CONSIDERATION = re.compile(
    r"^Transfert de patrimoine:\s*Selon contrat du\s+"
    r"(?P<date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"l['’]association a transféré des actifs pour CHF\s+"
    r"(?P<assets>[\d'.]+)\s+et des passifs envers les tiers pour CHF\s+"
    r"(?P<liabilities>[\d'.]+),\s*à\s+(?P<recipient>.+?)\s+à\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*aucune\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_AND_PRESIDENCY = re.compile(
    r"^L['’]associée-gérante\s+(?P<seller>[^,.;]+),\s*qui est élue présidente,\s*"
    r"cède\s+(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+"
    r"parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s*"
    r"(?P<place>[^,.;]+),\s*nouvelle associée avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"gérante(?:\s+avec signature individuelle)?\s*;\s*"
    r"(?P=seller)\s+reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SIX_ASSOCIATES_REALLOCATED = re.compile(
    r"^(?P<seller1>[^,.;]+)\s+et\s+(?P<seller2>[^,.;]+)\s+ont cédé\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer1>[^,.;]+),\s*(?P<buyer2>[^,.;]+),\s*"
    r"(?P<buyer3>[^,.;]+)\s+et\s+(?P<buyer4>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s*"
    r"(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{1,3})\.\s*Associés:\s*"
    r"(?P=buyer1)\s+pour\s+(?P<count1>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal1>[\d'.]+),\s*(?P=seller2)\s+pour\s+"
    r"(?P<count2>[\d']+)\s+parts de CHF\s+(?P<nominal2>[\d'.]+),\s*"
    r"(?P=buyer2)\s+pour\s+(?P<count3>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal3>[\d'.]+),\s*(?P=buyer3)\s+pour\s+"
    r"(?P<count4>[\d']+)\s+parts de CHF\s+(?P<nominal4>[\d'.]+),\s*"
    r"(?P=seller1)\s+pour\s+(?P<count5>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal5>[\d'.]+)\s+et\s+(?P=buyer4)\s+nouvel associé pour\s+"
    r"(?P<count6>[\d']+)\s+parts de CHF\s+(?P<nominal6>[\d'.]+),\s*"
    r"lequel n['’]exerce pas la signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_APPOINTED_MANAGER = re.compile(
    r"^L['’]associé\s+(?P<name>[^,.;]+)\s+a été nommé gérant"
    r"(?:\s+avec signature individuelle)?\.?$",
    re.I | re.UNICODE,
)
_DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_WITH_HISTORY = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+die mit Beschluss vom\s+"
    r"(?P<introduced_date>\d{2}\.\d{2}\.\d{4})\s+eingeführte und mit "
    r"Beschlüssen vom\s+(?P<amendment_dates>.+?)\s+abgeänderte bedingte "
    r"Kapitalerhöhung erneut abgeändert gemäss näherer Umschreibung in den "
    r"Statuten\.\s*\[bisher:\s*Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+die mit Beschluss vom\s+"
    r"(?P<previous_introduced_date>\d{2}\.\d{2}\.\d{4})\s+eingeführte und mit "
    r"Beschlüsse[n]? vom\s+(?P<previous_amendment_dates>.+?)\s+abgeänderte "
    r"bedingte Kapitalerhöhung erneut abgeändert gemäss näherer Umschreibung "
    r"in den Statuten\]\.?$",
    re.I | re.UNICODE,
)
_DE_STATUTES_DATE_CORRECTED = re.compile(
    r"^Das korrekte Statutendatum ist der\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+und nicht der\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_EXTENDED_UNTIL_WRITTEN = re.compile(
    r"^Mit Entscheid vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+hat das\s+"
    r"(?P<authority>.+?)\s+die definitive Nachlassstundung um\s+"
    r"(?P<duration>\w+)\s+Monate bis\s+"
    r"(?P<until>\d{1,2}\.\s+[A-Za-zÄÖÜäöü]+\s+\d{4})\s+verlängert\.?$",
    re.I | re.UNICODE,
)
_FR_PROVISIONAL_MORATORIUM_WITH_COMMISSIONER = re.compile(
    r"^Par prononcé rendu le\s+"
    r"(?P<date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"(?P<authority>.+?)\s+a accordé à la société un sursis concordataire "
    r"provisoire de\s+(?P<duration>\w+)\s+mois\.\s*"
    r"(?P<commissioner>[^,.;]+),\s*de et à\s+(?P<place>[^,.;]+),\s*"
    r"est inscrit en qualité de commissaire provisoire\.?$",
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
_DE_MONTHS = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}
_NUMBER_WORDS = {
    "un": 1,
    "une": 1,
    "deux": 2,
    "trois": 3,
    "quatre": 4,
    "cinq": 5,
    "six": 6,
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
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _written_date(raw: str, months: dict[str, int]) -> str:
    day, month, year = raw.lower().replace("1er", "1").replace(".", "").split()
    return f"{int(year):04d}-{months[month]:02d}-{int(day):02d}"


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


def extract_parser192_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 192."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_NAME_AND_DOMICILE_CHANGED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.name_and_first_name_and_domicile_changed.v1",
            match.group("name"), place=match.group("place"), extra={
                "action": "name_and_domicile_changed",
                "previous_name": match.group("previous_name").strip(),
            },
        )], ""

    if _DE_ORGANIZATION_CLAUSE_REMOVED.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.organization_clause_removed.v1", {
                "kind": "organization_clause", "action": "removed",
                "reason": "new_registration_rules",
            },
        )], ""

    match = _FR_ADMINISTRATOR_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_name_corrected_typo.v1",
            match.group("name"), role=match.group("role").lower(),
            signing="Einzelunterschrift", extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        )], ""

    match = _FR_ADMINISTRATOR_WITH_PRESIDENT.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_with_president.v1",
            match.group("name"), place=match.group("place"),
            role="administratrice", signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "appointed", "origin": match.group("origin").strip(),
                "signing_restriction": "with president",
            },
        )], ""

    match = _FR_ADMINISTRATION_PRESIDENT_AND_SECRETARY.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administration_president_and_secretary_individual.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                place=match.group("place"), role="président",
                signing="Einzelunterschrift", extra={
                    "action": "role_confirmed", "origin": match.group("origin").strip(),
                    "country": match.group("country"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("secretary"),
                role="secrétaire", signing="Einzelunterschrift",
                extra={"action": "appointed_secretary"},
            ),
        ], ""

    match = _FR_TWO_ADMINISTRATORS_NOT_WITH_EACH_OTHER.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_administrators_not_with_each_other.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="administrateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed",
                    "origin": match.group(f"origin{index}").strip(),
                    "cannot_sign_with_each_other": True,
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_ADMINISTRATION_MIXED_SIGNING.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administration_mixed_signing.v1"
        events = [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                place=match.group("place1"), role="président",
                signing="Einzelunterschrift", extra={
                    "action": "role_confirmed", "origin": match.group("origin1").strip(),
                    "country": match.group("country1"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("director"),
                role="directrice", signing="Einzelunterschrift",
                extra={"action": "appointed_additional_director"},
            ),
        ]
        for index in (3, 4, 5):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="administrateur",
                extra={
                    "action": "role_confirmed",
                    "origin": match.group(f"origin{index}").strip(),
                    "country": match.group(f"country{index}"),
                    "without_signature": True,
                },
            ))
        return events, ""

    match = _FR_BOARD_PRESIDENCY_SWAPPED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.board_presidency_swapped_signing_continues.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président", signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed_president", "signing_continues": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("previous_president"),
                role="membre du conseil", signing="Kollektivunterschrift zu zweien",
                extra={"action": "presidency_ended", "previous_role": "président",
                       "signing_continues": True},
            ),
        ], ""

    match = _FR_ASSOCIATION_ASSET_TRANSFER_NO_CONSIDERATION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.association_asset_transfer_no_consideration.v1", {
                "source_kind": "association",
                "agreement_date": _written_date(match.group("date"), _FR_MONTHS),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration_kind": "none", "gratuitous": True,
            },
        )], ""

    match = _FR_MANAGER_TRANSFER_AND_PRESIDENCY.fullmatch(leftover)
    if match and (
        _count(match.group("before"))
        == _count(match.group("transferred")) + _count(match.group("remaining"))
        and _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and len({match.group("nominal"), match.group("buyer_nominal"),
                 match.group("remaining_nominal")}) == 1
    ):
        rule_id = "fr.persons.manager_transfer_and_presidency.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {"currency": "CHF", "share_nominal": match.group("nominal")}
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller,
                role="associée-gérante présidente", extra={
                    **common, "action": "shares_transferred_and_appointed_president",
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée-gérante", signing="Einzelunterschrift", extra={
                    **common, "action": "shares_received_and_appointed_manager",
                    "counterparty": seller, "origin": match.group("origin").strip(),
                    "shares_received": _count(match.group("buyer_count")),
                    "shares_count": _count(match.group("buyer_count")),
                    "new_associate": True,
                },
            ),
        ], ""

    match = _FR_SIX_ASSOCIATES_REALLOCATED.fullmatch(leftover)
    if match and len({match.group("nominal"), *(
        match.group(f"nominal{index}") for index in range(1, 7)
    )}) == 1:
        rule_id = "fr.persons.six_associates_shares_reallocated.v1"
        names = [
            match.group("buyer1"), match.group("seller2"),
            match.group("buyer2"), match.group("buyer3"),
            match.group("seller1"), match.group("buyer4"),
        ]
        events = []
        for index, name in enumerate(names, start=1):
            is_new = index == 6
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, name,
                place=match.group("place") if is_new else None,
                role="associé", extra={
                    "action": "shares_reallocated",
                    "shares_count": _count(match.group(f"count{index}")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                    "aggregate_shares_transferred": _count(match.group("transferred")),
                    **({"new_associate": True,
                        "origin": match.group("origin").strip(),
                        "country": match.group("country"),
                        "without_signature": True} if is_new else {}),
                },
            ))
        return events, ""

    match = _FR_ASSOCIATE_APPOINTED_MANAGER.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_appointed_manager.v1",
            match.group("name"), role="associé-gérant", signing="Einzelunterschrift",
            extra={"action": "appointed_manager"},
        )], ""

    match = _DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_WITH_HISTORY.fullmatch(leftover)
    if match and match.group("introduced_date") == match.group("previous_introduced_date"):
        dates = re.findall(r"\d{2}\.\d{2}\.\d{4}", match.group("amendment_dates"))
        previous_dates = re.findall(
            r"\d{2}\.\d{2}\.\d{4}", match.group("previous_amendment_dates")
        )
        if dates and previous_dates:
            return [_event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.conditional_capital_clause_changed_history.v1", {
                    "kind": "conditional_capital_clause", "action": "changed",
                    "date": _iso_date(match.group("date")),
                    "introduced_date": _iso_date(match.group("introduced_date")),
                    "amendment_dates": [_iso_date(value) for value in dates],
                    "previous_date": _iso_date(match.group("previous_date")),
                    "previous_amendment_dates": [
                        _iso_date(value) for value in previous_dates
                    ],
                    "details_in_statutes": True,
                },
            )], ""

    match = _DE_STATUTES_DATE_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.statutes_date_corrected.v2", {
                "kind": "statutes_date", "action": "corrected",
                "date": _iso_date(match.group("date")),
                "previous_date": _iso_date(match.group("previous_date")),
            },
        )], ""

    match = _DE_DEFINITIVE_MORATORIUM_EXTENDED_UNTIL_WRITTEN.fullmatch(leftover)
    if match and match.group("duration").lower() in _NUMBER_WORDS:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.definitive_moratorium_extended_written_until.v1", {
                "kind": "composition_moratorium_extended", "action": "extended",
                "moratorium_type": "definitive",
                "decision_date": _iso_date(match.group("date")),
                "authority": match.group("authority").strip(),
                "duration_months": _NUMBER_WORDS[match.group("duration").lower()],
                "until": _written_date(match.group("until"), _DE_MONTHS),
            },
        )], ""

    match = _FR_PROVISIONAL_MORATORIUM_WITH_COMMISSIONER.fullmatch(leftover)
    if match and match.group("duration").lower() in _NUMBER_WORDS:
        rule_id = "fr.text.provisional_moratorium_with_commissioner.v1"
        commissioner = match.group("commissioner").strip()
        place = match.group("place").strip()
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "composition_moratorium_granted", "action": "granted",
                    "moratorium_type": "provisional",
                    "decision_date": _written_date(match.group("date"), _FR_MONTHS),
                    "authority": match.group("authority").strip(),
                    "duration_months": _NUMBER_WORDS[match.group("duration").lower()],
                    "commissioner": commissioner,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, commissioner, place=place,
                role="commissaire provisoire", extra={
                    "action": "appointed", "origin": place,
                },
            ),
        ], ""

    return [], text
