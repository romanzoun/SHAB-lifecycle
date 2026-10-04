from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_CAPITAL_CLAUSES_REMOVED = re.compile(
    r"^Streichung der Statutenbestimmung über die mit Ermächtigungsbeschluss vom\s+"
    r"(?P<authorization_date>\d{2}\.\d{2}\.\d{4})\s+eingeführte genehmigte "
    r"Kapitalerhöhung infolge Ablaufs der zeitlichen Befristung\.\s*"
    r"\[Die Bestimmung über die bedingte Kapitalerhöhung ist aufgehoben,\s*"
    r"da bis zum heutigen Zeitpunkt weder Options- noch Wandelrechte ausgegeben wurden\.\]\s*\.?\s*"
    r"\[gestrichen:\s*Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<history_date1>\d{2}\.\d{2}\.\d{4})\s+den Beschluss über die Einführung "
    r"einer bedingten Kapitalerhöhung vom\s+(?P<introduction_date1>\d{2}\.\d{2}\.\d{4})\s+"
    r"gemäss näherer Umschreibung in den Statuten angepasst\.\]\s*\.?\s*"
    r"\[gestrichen:\s*Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<history_date2>\d{2}\.\d{2}\.\d{4})\s+den Beschluss über die Einführung "
    r"einer bedingten Kapitalerhöhung vom\s+(?P<introduction_date2>\d{2}\.\d{2}\.\d{4})\s+"
    r"gemäss näherer Umschreibung in den Statuten angepasst\.\]\s*\.?\s*"
    r"\[gestrichen:\s*Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<history_date3>\d{2}\.\d{2}\.\d{4})\s+den Beschluss über die Einführung "
    r"einer bedingten Kapitalerhöhung vom\s+(?P<introduction_date3>\d{2}\.\d{2}\.\d{4})\s+"
    r"gemäss näherer Umschreibung in den Statuten angepasst\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_PARTICIPATION_CAPITAL_INCREASES = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<authorized_date>\d{2}\.\d{2}\.\d{4})\s+eine genehmigte Erhöhung des "
    r"Partizipationskapitals gemäss näherer Umschreibung in den Statuten beschlossen\.\s*"
    r"Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<conditional_date>\d{2}\.\d{2}\.\d{4})\s+eine bedingte Erhöhung des "
    r"Partizipationskapitals gemäss näherer Umschreibung in den Statuten beschlossen\.?$",
    re.I | re.UNICODE,
)
_DE_SOLE_PROPRIETOR_DELETION_CORRECTED = re.compile(
    r"^Die Löschung des Einzelunternehmens\s*\(SHAB Nr\.\s*(?P<issue>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\)\s+ist zu Unrecht erfolgt und wird "
    r"hiermit berichtigt\.\s*\[bisher:\s*(?P<previous>.+?)\]\.?$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_LAST_EXTENDED = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+die definitive Nachlassstundung bis\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\s+letztmals verlängert\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_SHARE_TRANSFER_AND_PRESIDENCY = re.compile(
    r"^L['’](?P<seller_role>associé-gérant)\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:(?:du|de la|des|de)\s+|d['’])(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"gérant président\s*;\s*(?P=seller)\s+reste titulaire de\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ORGANIZATION_SHARE_TRANSFER_FINAL_HOLDINGS = re.compile(
    r"^(?P<seller>.+?)\s*\((?P<seller_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^.;]+)\.\s*Associées:\s*(?P=seller)\s*\((?P=seller_uid)\)\s+"
    r"pour\s+(?P<seller_count>[\d']+)\s+parts de CHF\s+(?P<seller_nominal>[\d'.]+)\s+"
    r"et\s+(?P=buyer)\s+pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_SUSPENDED_BY_CANTONAL_COURT = re.compile(
    r"^(?P<authority>La présidente de la Cour des poursuites et faillites du "
    r"Tribunal cantonal)\s+a prononcé le\s+(?P<date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4})\s+l['’]effet suspensif de la faillite\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_DELETION_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+n['’]est pas radié(?:e)?\s*;\s*demeure inscrit(?:e)? "
    r"en qualité de\s+(?P<role>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_DELEGATE_PRESIDENT_PAIR = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*(?P<previous_role>délégué),\s*"
    r"nommé président,\s*et\s+(?P<member>[^,.;]+),\s*lesquels signent désormais "
    r"individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_SELLERS_TRANSFER_TO_NEW_MANAGER = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller1>[^,.;]+)\s+cède\s+"
    r"(?P<transferred1>[\d']+)\s+de ses\s+(?P<before1>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal1>[\d'.]+)\s+et les associés\s+(?P<seller2>[^,.;]+)\s+et\s+"
    r"(?P<seller3>[^,.;]+)\s+chacun\s+(?P<transferred23>[\d']+)\s+de leurs\s+"
    r"(?P<before23>[\d']+)\s+parts de CHF\s+(?P<nominal23>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:(?:du|de la|des|de)\s+|d['’])(?P<origin>[^,.;]+),\s*"
    r"(?:à|au|aux)\s+(?P<place>[^,.;]+),\s*nouvel associé avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"gérant secrétaire\s+(?P=seller1),\s*qui est nommé président,\s*"
    r"reste titulaire de\s+(?P<seller1_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller1_nominal>[\d'.]+)\s*;\s*(?P=seller2)\s+et\s+(?P=seller3)\s+"
    r"restent titulaires de\s+(?P<seller23_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller23_nominal>[\d'.]+)\s+chacun\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_FOUNDATION_MEMBERS_REPLACED = re.compile(
    r"^(?P<removed1>[^,.;]+),\s*(?P<removed2>[^,.;]+),\s*"
    r"(?P<removed3>[^,.;]+)\s+ne sont plus membres du conseil de fondation\.\s*"
    r"(?P<name1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"et\s+(?P<name3>[^,.;]+),\s*de et à\s+(?P<place3>[^,.;]+),\s*"
    r"sont membres du conseil de fondation,\s*sans signature\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_APPOINTMENTS = re.compile(
    r"^L['’]associée-gérante\s+(?P<president>[^,.;]+)\s+est élu(?:e)? présidente\.\s*"
    r"L['’]associée\s+(?P<manager>[^,.;]+)\s+est nommée gérante,\s*sans signature\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_TO_ORGANIZATION = re.compile(
    r"^(?P<seller>[^,.;]+)\s+a cédé\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>.+?)\s*"
    r"\((?P<buyer_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"nouvelle associée pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\s*;\s*par conséquent\s+(?P=seller)\s+est "
    r"maintenant associé pour\s+(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_FULLY_OWNED = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di\s+(?P<absorbed_name>.+?),\s*"
    r"in\s+(?P<absorbed_place>[^()]+?)\s*\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"secondo (?:il\s+)?contratto di fusione del\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+e bilancio al\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\s*,\s*che presenta attivi per CHF\s+"
    r"(?P<assets>[\d'.]+)\s+e passivi verso terzi per CHF\s+"
    r"(?P<liabilities>[\d'.]+)\.\s*La società assuntrice detiene tutte le azioni "
    r"della società trasferente,\s*per cui la fusione avviene senza aumento di "
    r"capitale e senza attribuzione di azioni\.?$",
    re.I | re.UNICODE,
)
_FR_LIQUIDATION_ADDRESS_CORRECTED_COLON = re.compile(
    r"^L['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que "
    r"l['’]adresse de liquidation est\s*:\s*(?P<address>.+?)\s*"
    r"\(et non pas\s+(?P<previous_address>.+?)\)\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_TO_UNSIGNED_ASSOCIATE_COMMA = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:(?:du|de la|des|de)\s+|d['’])(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*nouvel associé sans signature,\s*avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\s*;\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
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
    role: str | None = None,
    signing: str | None = None,
    uid: str | None = None,
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


def extract_parser117_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 117."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_CAPITAL_CLAUSES_REMOVED.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.capital_clauses_removed.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "kind": "authorized_capital_clause", "action": "removed",
                    "authorization_date": _iso_date(match.group("authorization_date")),
                    "reason": "authorization_expired",
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "kind": "conditional_capital_clause", "action": "removed",
                    "reason": "no_option_or_conversion_rights_issued",
                    "introduction_date": _iso_date(match.group("introduction_date1")),
                    "previous_amendment_dates": [
                        _iso_date(match.group("history_date1")),
                        _iso_date(match.group("history_date2")),
                        _iso_date(match.group("history_date3")),
                    ],
                },
            ),
        ])

    match = _DE_PARTICIPATION_CAPITAL_INCREASES.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.participation_capital_increases.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "kind": "authorized_participation_capital_increase",
                    "action": "authorized",
                    "decision_date": _iso_date(match.group("authorized_date")),
                    "details_in_statutes": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "kind": "conditional_participation_capital_increase",
                    "action": "authorized",
                    "decision_date": _iso_date(match.group("conditional_date")),
                    "details_in_statutes": True,
                },
            ),
        ])

    match = _DE_SOLE_PROPRIETOR_DELETION_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.sole_proprietor_deletion_corrected.v1",
            {
                "kind": "registration_reinstated", "scope": "sole_proprietor",
                "action": "deletion_reversed", "reason": "erroneous_deletion",
                "notice_number": match.group("issue"),
                "notice_date": _iso_date(match.group("notice_date")),
                "previous": match.group("previous").strip(),
            },
        ))

    match = _DE_DEFINITIVE_MORATORIUM_LAST_EXTENDED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.definitive_moratorium_last_extended.v1",
            {
                "kind": "composition_moratorium_extended",
                "moratorium_type": "definitive", "last_extension": True,
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "until": _iso_date(match.group("until")),
            },
        ))

    match = _FR_MANAGER_SHARE_TRANSFER_AND_PRESIDENCY.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_share_transfer_and_presidency.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant",
                extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("seller_nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé-gérant président",
                extra={
                    "action": "shares_received_and_appointed", "counterparty": seller,
                    "heimat": match.group("origin").strip(), "new_associate": True,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _FR_ORGANIZATION_SHARE_TRANSFER_FINAL_HOLDINGS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.organization_share_transfer_final_holdings.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, uid=match.group("seller_uid"),
                role="associée",
                extra={
                    "uid": match.group("seller_uid"), "action": "shares_transferred",
                    "counterparty": buyer, "shares_transferred": transferred,
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("seller_nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, role="associée",
                extra={
                    "action": "shares_received", "counterparty": seller,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _FR_BANKRUPTCY_SUSPENDED_BY_CANTONAL_COURT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.bankruptcy_suspended_cantonal_court.v1",
            {
                "kind": "bankruptcy_suspended",
                "decision_date": _french_date(match.group("date")),
                "authority": match.group("authority").strip(),
            },
        ))

    match = _FR_DIRECTOR_DELETION_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.director_deletion_corrected.v1",
            match.group("name"), role=match.group("role").strip(),
            extra={
                "action": "deletion_reversed", "remains_registered": True,
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _FR_ADMINISTRATION_DELEGATE_PRESIDENT_PAIR.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_delegate_president_pair.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="délégué et président", signing="Einzelunterschrift",
                extra={
                    "action": "appointed_president_and_signing_changed",
                    "previous_role": match.group("previous_role"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("member"),
                role="membre de l'administration", signing="Einzelunterschrift",
                extra={"action": "signing_changed"},
            ),
        ])

    match = _FR_THREE_SELLERS_TRANSFER_TO_NEW_MANAGER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.three_sellers_transfer_to_new_manager.v1"
        seller1 = match.group("seller1").strip()
        seller2 = match.group("seller2").strip()
        seller3 = match.group("seller3").strip()
        buyer = match.group("buyer").strip()
        transferred1 = _count(match.group("transferred1"))
        transferred23 = _count(match.group("transferred23"))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, seller1, role="associé-gérant et président",
            extra={
                "action": "shares_transferred_and_appointed_president",
                "counterparty": buyer, "shares_before": _count(match.group("before1")),
                "shares_transferred": transferred1,
                "shares_count": _count(match.group("seller1_count")),
                "share_nominal": match.group("seller1_nominal"), "currency": "CHF",
            },
        ))
        for seller in (seller2, seller3):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé",
                extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before23")),
                    "shares_transferred": transferred23,
                    "shares_count": _count(match.group("seller23_count")),
                    "share_nominal": match.group("seller23_nominal"), "currency": "CHF",
                },
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, buyer, place=match.group("place"),
            role="associé-gérant secrétaire",
            extra={
                "action": "shares_received_and_appointed", "new_associate": True,
                "heimat": match.group("origin").strip(),
                "counterparties": [seller1, seller2, seller3],
                "shares_received": transferred1 + 2 * transferred23,
                "shares_count": _count(match.group("buyer_count")),
                "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
            },
        ))

    match = _FR_THREE_FOUNDATION_MEMBERS_REPLACED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.three_foundation_members_replaced.v1"
        for index in range(1, 4):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group(f"removed{index}"),
                role="membre du conseil de fondation", extra={"action": "removed"},
            ))
        additions = (
            (1, match.group("origin1"), match.group("place1")),
            (2, match.group("origin2"), match.group("place2")),
            (3, match.group("place3"), match.group("place3")),
        )
        for index, origin, place in additions:
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"), place=place,
                role="membre du conseil de fondation",
                extra={
                    "action": "appointed", "heimat": origin.strip(),
                    "without_signature": True,
                },
            ))

    match = _FR_MANAGER_APPOINTMENTS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_appointments.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="associée-gérante et présidente",
                extra={"action": "appointed_president"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("manager"),
                role="associée-gérante",
                extra={"action": "appointed_manager", "without_signature": True},
            ),
        ])

    match = _FR_SHARE_TRANSFER_TO_ORGANIZATION.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.share_transfer_to_organization.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé",
                extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "counterparty_uid": match.group("buyer_uid"),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("seller_nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                uid=match.group("buyer_uid"), role="associée",
                extra={
                    "uid": match.group("buyer_uid"), "action": "shares_received",
                    "counterparty": seller, "new_associate": True,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _IT_MERGER_FULLY_OWNED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "it.text.merger_fully_owned.v1",
            {
                "kind": "absorption",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "currency": "CHF", "all_shares_held_by_acquirer": True,
                "capital_increase": False, "share_allocation": False,
            },
        ))

    match = _FR_LIQUIDATION_ADDRESS_CORRECTED_COLON.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.liquidation_address_corrected_colon.v1",
            {
                "scope": "liquidation", "action": "corrected",
                "address": match.group("address").strip(),
                "previous_address": match.group("previous_address").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _FR_SHARE_TRANSFER_TO_UNSIGNED_ASSOCIATE_COMMA.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.share_transfer_to_unsigned_associate_comma.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé",
                extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("seller_nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé",
                extra={
                    "action": "shares_received", "counterparty": seller,
                    "heimat": match.group("origin").strip(), "new_associate": True,
                    "without_signature": True, "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
