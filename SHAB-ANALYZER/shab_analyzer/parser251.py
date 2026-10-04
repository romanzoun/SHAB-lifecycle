from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_PROVISIONAL_TO_DEFINITIVE_MORATORIUM = re.compile(
    r"^\[gestrichen:\s*Mit Entscheid der\s+(?P<previous_authority>.+?),\s*vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde eine "
    r"provisorische Nachlassstundung von\s+(?P<previous_duration>\w+)\s+Monaten "
    r"bis\s+(?P<previous_until>\d{2}\.\d{2}\.\d{4})\s+bewilligt\.\s*"
    r"Als Sachwalterin wird\s+(?P<previous_commissioner>.+?)\s+ernannt\.\]\.?\s*"
    r"Mit Entscheid der\s+(?P<authority>.+?),\s*vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde eine definitive "
    r"Nachlassstundung von\s+(?P<duration>\w+)\s+Monaten bis\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\s+bewilligt\.\s*Als Sachwalterin wird\s+"
    r"(?P<commissioner>.+?)\s+ernannt\.?$",
    re.I | re.UNICODE,
)
_FR_TRANSFER_AND_TWO_MANAGERS = re.compile(
    r"^Par suite de cession de\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*(?P<seller>[^,.;]+)\s+est maintenant associé "
    r"pour\s+(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+),\s*et\s+(?P<buyer>[^,.;]+),\s*de et à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d']+(?:\.\d+)?)\.\s*Gérants:\s*les associés\s+"
    r"(?P<manager1>[^,.;]+),\s*président,\s*et\s+(?P<manager2>[^,.;]+),\s*"
    r"tous deux(?: avec signature individuelle)?\.?$",
    re.I | re.UNICODE,
)
_FR_NAME_CORRECTED_FOSC_REFERENCE = re.compile(
    r"^L['’]inscription\s+(?:No|no|n°)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+p\.(?P<notice_page>\d+)\s+"
    r"est corrigée en ce sens que\s+(?P<previous_name>.+?)\s+porte en réalité "
    r"le nom de\s+(?P<name>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_NAME_CORRECTED_RECTIFICATION = re.compile(
    r"^Rectification:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\)\s+est rectifiée dans ce sens que le nom correct est\s+"
    r"(?P<name>.+?\.)\(et non pas\s+(?P<previous_name>.+?\.)\)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_PRESIDENT_AND_NEW_ADMINISTRATOR = re.compile(
    r"^Administrateur:\s*(?P<president>[^,.;]+),\s*nommée présidente,\s*et\s+"
    r"(?P<administrator>[^,.;]+),\s*d['’](?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_PREVIOUS_PLACE_RESIDUE = re.compile(
    r"^\[bisher:\s*(?P<place>Zürich)\s*\]\.?$", re.I | re.UNICODE
)
_FR_MANAGER_SHARE_TRANSFER_HOLDINGS = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à "
    r"l['’]associé-gérant\s+(?P<buyer>[^,.;]+)\.\s*Associés-gérants:\s*"
    r"(?P<seller_again>[^,.;]+)\s+pour\s+(?P<seller_count>[\d']+)\s+parts de "
    r"CHF\s+(?P<seller_nominal>[\d'.]+),\s*président,\s*et\s+"
    r"(?P<buyer_again>[^,.;]+)\s+pour\s+(?P<buyer_count>[\d']+)\s+parts de "
    r"CHF\s+(?P<buyer_nominal>[\d'.]+),\s*tous deux"
    r"(?: avec signature individuelle)?\s*;\s*les pouvoirs du "
    r"dernier sont modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_TRANSFER_ALL_TO_NEW_MANAGER = re.compile(
    r"^(?P<seller1>[^,.;]+)\s+et\s+(?P<seller2>[^,.;]+),\s*qui ne sontt? plus "
    r"associés-gérants et dont la signature est radiée,\s*cèdent respectivement "
    r"leurs\s+(?P<count1>[\d']+)\s+et\s+(?P<count2>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>.+?)\s+de et à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé-gérant"
    r"(?: avec signature individuelle)?,\s*avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_LIQUIDATORS_MANAGER_ROLES = re.compile(
    r"^Liquidateurs:\s*(?P<president>[^,.;]+),\s*gérant,\s*nommé président,\s*"
    r"et\s+(?P<manager>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nommé gérant,\s*lesquels signent "
    r"individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_DEFINITIVE_MORATORIUM_EXTENDED_DURATION = re.compile(
    r"^Par prononcé rendu le\s+(?P<decision_date>\d{1,2}(?:er)?\s+"
    r"[A-Za-zÀ-ÿ]+\s+\d{4}),\s*(?P<authority>.+?)\s+a prolongé le sursis "
    r"concordataire définitif accordé à la société de\s+(?P<duration>\w+)\s+"
    r"mois,\s*soit jusqu['’]au\s+(?P<until>\d{1,2}(?:er)?\s+"
    r"[A-Za-zÀ-ÿ]+\s+\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_OMITTED_PREVIOUS_REGISTRY_ID_CORRECTED = re.compile(
    r"^Im SHAB Nr\.\s*(?P<issue>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten TR-Eintrag\s+"
    r"(?P<entry>[\d']+)/(?P<entry_year>\d{4})\s+wurde irrtümlich das\s+"
    r"\[bisher:\s*\((?P<previous_registry_id>CH-[\d.]+-\d)\)\]\s+weggelassen\.\s*"
    r"Korrekt ist\s+\[bisher:\s*(?P<name>.+?)\s+"
    r"\((?P<registry_id>CH-[\d.]+-\d)\)\]\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_WITH_PRESIDENT = re.compile(
    r"^Nouveau membre du conseil de fondation"
    r"(?: avec signature collective à deux,)?\s*toutefois avec le président:\s*"
    r"(?P<name>[^,.;]+),\s*d['’](?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ERRONEOUS_DIRECTOR_ENTRY_REVERTED = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+étant intervenue de manière "
    r"erronée et prématurément,\s*les mentions antérieures sont rétablies,\s*"
    r"en ce sens que\s+(?P<director>[^,.;]+)\s+reste directeur"
    r"(?: avec signature collective à deux)?,\s*et que\s+"
    r"(?P<not_director>[^,.;]+)\s+n['’]est pas directeur avec signature "
    r"collective à deux\.?$",
    re.I | re.UNICODE,
)
_IT_HEAD_OFFICE_NAME_SUPPLEMENT = re.compile(
    r"^,?\s*Sede principale a:\s*(?P<head_office>[^.]+)\.\s*"
    r"\[Al momento dell['’]iscrizione nel registro di commercio della succursale "
    r"non è stata iscritta la ditta dello stabilimento principale\.\]\.\s*"
    r"Nome della ditta della sede principale:\s*(?P<name>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PRESIDENT_SECRETARY = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*président,\s*et\s+"
    r"(?P<secretary>[^,.;]+),\s*nommé secrétaire,\s*lesquels signent "
    r"collectivement à deux\.\s*Les pouvoirs du second sont modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_FR_LIMITED_PARTNER_REDUCED_AND_ORGANIZATION_ADDED = re.compile(
    r"^La commandite de l['’]associée commanditaire\s+(?P<existing>.+?)\s*"
    r"\((?P<existing_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+a été réduite de "
    r"CHF\s+(?P<from>[\d'.]+)\.-\s+à CHF\s+(?P<to>[\d'.]+)\.-\.\s*"
    r"Nouvelle associée commanditaire:\s*(?P<new>.+?)\s*"
    r"\((?P<new_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*pour une commandite de CHF\s+"
    r"(?P<contribution>[\d'.]+)\.-\.?$",
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
_NUMBERS = {
    "ein": 1,
    "eine": 1,
    "einen": 1,
    "un": 1,
    "une": 1,
    "zwei": 2,
    "deux": 2,
    "drei": 3,
    "trois": 3,
    "vier": 4,
    "quatre": 4,
    "fünf": 5,
    "cinq": 5,
    "sechs": 6,
    "six": 6,
}


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _french_date(raw: str) -> str:
    day, month, year = raw.casefold().replace("1er", "1", 1).split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", "").replace(".", ""))


def _duration_months(raw: str) -> int | None:
    token = raw.strip().casefold()
    return int(token) if token.isdigit() else _NUMBERS.get(token)


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
        role=role.strip() if role else None,
        signing=signing,
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser251_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 251."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_PROVISIONAL_TO_DEFINITIVE_MORATORIUM.fullmatch(leftover)
    if match and (
        match.group("authority").strip().casefold()
        == match.group("previous_authority").strip().casefold()
        and match.group("commissioner").strip().casefold()
        == match.group("previous_commissioner").strip().casefold()
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.provisional_to_definitive_moratorium.v1", {
                "kind": "composition_moratorium_changed",
                "action": "provisional_replaced_by_definitive",
                "moratorium_type": "definitive",
                "decision_date": _iso_date(match.group("decision_date")),
                "duration_months": _duration_months(match.group("duration")),
                "until": _iso_date(match.group("until")),
                "authority": match.group("authority").strip(),
                "commissioner": match.group("commissioner").strip(),
                "previous_moratorium_type": "provisional",
                "previous_decision_date": _iso_date(
                    match.group("previous_decision_date")
                ),
                "previous_duration_months": _duration_months(
                    match.group("previous_duration")
                ),
                "previous_until": _iso_date(match.group("previous_until")),
            },
        )], ""

    match = _FR_TRANSFER_AND_TWO_MANAGERS.fullmatch(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        seller_count = _count(match.group("seller_count"))
        buyer_count = _count(match.group("buyer_count"))
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        if (
            seller.casefold() == match.group("manager1").strip().casefold()
            and buyer.casefold() == match.group("manager2").strip().casefold()
            and transferred == buyer_count
            and len({
                match.group("nominal"), match.group("seller_nominal"),
                match.group("buyer_nominal"),
            }) == 1
        ):
            rule_id = "fr.persons.transfer_and_two_managers.v1"
            common = {"currency": "CHF", "share_nominal": match.group("nominal")}
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller,
                    role="associé-gérant président", signing="Einzelunterschrift",
                    extra={
                        "action": "appointed_manager_president_after_share_transfer",
                        "shares_before": seller_count + transferred,
                        "shares_transferred": transferred,
                        "shares_count": seller_count,
                        "counterparty": buyer,
                        **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé-gérant", signing="Einzelunterschrift", extra={
                        "action": "appointed_and_shares_received",
                        "new_associate": True,
                        "origin": match.group("place").strip(),
                        "shares_received": transferred,
                        "shares_count": buyer_count,
                        "counterparty": seller,
                        **common,
                    },
                ),
            ], ""

    match = _FR_NAME_CORRECTED_FOSC_REFERENCE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.persons.name_corrected_fosc_reference.v1",
            match.group("name"), extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_page": int(match.group("notice_page")),
            },
        )], ""

    match = _FR_NAME_CORRECTED_RECTIFICATION.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.persons.name_corrected_rectification.v1",
            match.group("name"), extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        )], ""

    match = _FR_ADMINISTRATOR_PRESIDENT_AND_NEW_ADMINISTRATOR.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administrator_president_and_new_administrator.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="présidente du conseil d'administration",
                signing="Einzelunterschrift", extra={"action": "appointed_president"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("administrator"),
                place=match.group("place"), role="administrateur",
                signing="Einzelunterschrift", extra={
                    "action": "appointed",
                    "origin": match.group("origin").strip(),
                },
            ),
        ], ""

    match = _DE_BRANCH_PREVIOUS_PLACE_RESIDUE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_previous_place_residue.v1", {
                "action": "previous_place_recorded",
                "previous_place": match.group("place").strip(),
            },
        )], ""

    match = _FR_MANAGER_SHARE_TRANSFER_HOLDINGS.fullmatch(leftover)
    if match:
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        seller_count = _count(match.group("seller_count"))
        buyer_count = _count(match.group("buyer_count"))
        if (
            seller.casefold() == match.group("seller_again").strip().casefold()
            and buyer.casefold() == match.group("buyer_again").strip().casefold()
            and len({
                match.group("nominal"), match.group("seller_nominal"),
                match.group("buyer_nominal"),
            }) == 1
            and buyer_count >= transferred
        ):
            rule_id = "fr.persons.manager_share_transfer_holdings.v1"
            common = {"currency": "CHF", "share_nominal": match.group("nominal")}
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller,
                    role="associé-gérant président", signing="Einzelunterschrift",
                    extra={
                        "action": "shares_transferred_and_appointed_president",
                        "shares_before": seller_count + transferred,
                        "shares_transferred": transferred,
                        "shares_count": seller_count,
                        "counterparty": buyer,
                        **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, role="associé-gérant",
                    signing="Einzelunterschrift", extra={
                        "action": "shares_received_and_powers_changed",
                        "powers_modified": True,
                        "shares_before": buyer_count - transferred,
                        "shares_received": transferred,
                        "shares_count": buyer_count,
                        "counterparty": seller,
                        **common,
                    },
                ),
            ], ""

    match = _FR_TWO_MANAGERS_TRANSFER_ALL_TO_NEW_MANAGER.fullmatch(leftover)
    if match:
        count1 = _count(match.group("count1"))
        count2 = _count(match.group("count2"))
        buyer_count = _count(match.group("buyer_count"))
        if (
            count1 + count2 == buyer_count
            and match.group("nominal") == match.group("buyer_nominal")
        ):
            rule_id = "fr.persons.two_managers_transfer_all_to_new_manager.v1"
            buyer = match.group("buyer").strip()
            common = {"currency": "CHF", "share_nominal": match.group("nominal")}
            events = []
            for name_group, count in (("seller1", count1), ("seller2", count2)):
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", rule_id, match.group(name_group),
                    role="associé-gérant", extra={
                        "action": "removed_and_all_shares_transferred",
                        "signing_revoked": True,
                        "shares_before": count,
                        "shares_transferred": count,
                        "shares_count": 0,
                        "counterparty": buyer,
                        **common,
                    },
                ))
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé-gérant", signing="Einzelunterschrift", extra={
                    "action": "appointed_and_shares_received",
                    "new_associate": True,
                    "origin": match.group("place").strip(),
                    "shares_received": buyer_count,
                    "shares_count": buyer_count,
                    **common,
                },
            ))
            return events, ""

    match = _FR_TWO_LIQUIDATORS_MANAGER_ROLES.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_liquidators_manager_roles.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="gérant, liquidateur président", signing="Einzelunterschrift",
                extra={"action": "appointed_liquidator_president"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("manager"),
                place=match.group("place"), role="gérant, liquidateur",
                signing="Einzelunterschrift", extra={
                    "action": "appointed_manager_and_liquidator",
                    "origin": match.group("origin").strip(),
                },
            ),
        ], ""

    match = _FR_DEFINITIVE_MORATORIUM_EXTENDED_DURATION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.definitive_moratorium_extended_duration.v1", {
                "kind": "composition_moratorium_extended",
                "action": "extended",
                "moratorium_type": "definitive",
                "decision_date": _french_date(match.group("decision_date")),
                "duration_months": _duration_months(match.group("duration")),
                "until": _french_date(match.group("until")),
                "authority": match.group("authority").strip(),
            },
        )], ""

    match = _DE_OMITTED_PREVIOUS_REGISTRY_ID_CORRECTED.fullmatch(leftover)
    if match and (
        match.group("previous_registry_id").casefold()
        == match.group("registry_id").casefold()
    ):
        registry_id = match.group("registry_id")
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected",
            "de.persons.omitted_previous_registry_id_corrected.v1",
            match.group("name"), extra={
                "action": "omitted_person_and_registry_id_restored",
                "registry_id": registry_id,
                "previous_value": f"({registry_id})",
                "entry": match.group("entry"),
                "entry_year": int(match.group("entry_year")),
                "notice_issue": int(match.group("issue")),
                "notice_date": _iso_date(match.group("notice_date")),
            },
        )], ""

    match = _FR_FOUNDATION_MEMBER_WITH_PRESIDENT.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.foundation_member_with_president.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil de fondation",
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "appointed",
                "origin": match.group("origin").strip(),
                "required_with": "président",
            },
        )], ""

    match = _FR_ERRONEOUS_DIRECTOR_ENTRY_REVERTED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.erroneous_director_entry_reverted.v1"
        common = {
            "action": "erroneous_entry_reverted",
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", rule_id, match.group("director"),
                role="directeur", signing="Kollektivunterschrift zu zweien", extra={
                    **common,
                    "restored": True,
                    "remains_director": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", rule_id, match.group("not_director"),
                extra={
                    **common,
                    "incorrect_role": "directeur",
                    "incorrect_signing": "Kollektivunterschrift zu zweien",
                    "appointment_reverted": True,
                },
            ),
        ], ""

    match = _IT_HEAD_OFFICE_NAME_SUPPLEMENT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_name_changed", "it.text.head_office_name_supplement.v1", {
                "kind": "head_office_name",
                "scope": "head_office",
                "action": "publication_supplemented",
                "head_office": match.group("head_office").strip(),
                "name": match.group("name").strip(),
                "previously_omitted": True,
            },
        )], ""

    match = _FR_ADMINISTRATION_PRESIDENT_SECRETARY.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administration_president_secretary.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                place=match.group("place"),
                role="président du conseil d'administration",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_president",
                    "origin": match.group("origin").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("secretary"),
                role="secrétaire du conseil d'administration",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_secretary_and_powers_changed",
                    "powers_modified": True,
                },
            ),
        ], ""

    match = _FR_LIMITED_PARTNER_REDUCED_AND_ORGANIZATION_ADDED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.limited_partner_reduced_and_organization_added.v2"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("existing"),
                uid=match.group("existing_uid"), role="associée commanditaire",
                extra={
                    "action": "limited_partnership_contribution_changed",
                    "previous_limited_partnership_contribution": match.group("from"),
                    "limited_partnership_contribution": match.group("to"),
                    "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("new"),
                uid=match.group("new_uid"), place=match.group("place"),
                role="associée commanditaire", extra={
                    "action": "appointed",
                    "new_associate": True,
                    "limited_partnership_contribution": match.group("contribution"),
                    "currency": "CHF",
                },
            ),
        ], ""

    return [], leftover
