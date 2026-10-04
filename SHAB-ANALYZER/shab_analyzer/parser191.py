from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_DE_AUDITOR_UID_SUPPLEMENT = re.compile(
    r"^Bei der nachfolgenden Mutation wurde die bisherige Firmennummer nicht "
    r"publiziert\.\s*Deshalb erfolgt folgender Nachtrag:\s*"
    r"(?P<name>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+"
    r"(?P<place>[^,.;]+),\s*Revisionsstelle\s*\[bisher:\s*"
    r"(?P<previous_name>.+?)\s*\((?P<previous_registry_id>\d[^)]+)\)\]\.?$",
    re.I | re.UNICODE,
)
_FR_COMMITTEE_MEMBERS_WITHOUT_SIGNATURE = re.compile(
    r"^Nouveaux membres du comité,\s*sans signature sociale:\s*"
    r"(?P<members>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_WITH_COUNTRY = re.compile(
    r"(?P<name>[^,;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,;]+),\s*à\s*(?P<place>[^,;]+),\s*"
    r"(?P<country>[A-Z]{1,3})(?=\s*(?:,|$))",
    re.UNICODE,
)
_FR_OTHER_ADDRESS_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que l['’]autre "
    r"adresse est:\s*(?P<address>.+?)\s*\(et non\s+"
    r"(?P<previous_address>.+?),\s*comme publié\)\.?$",
    re.I | re.UNICODE,
)
_IT_CAPITAL_INCREASE_CONTRIBUTION_IN_KIND = re.compile(
    r"^Fatti particolari:\s*Conferimenti in natura:\s*in occasione "
    r"dell['’]aumento di capitale la società assume\s+"
    r"(?P<source_shares>[\d']+)\s+azioni nominative di nominali CHF\s+"
    r"(?P<source_nominal>[\d'.]+)\s+interamente liberate della\s+"
    r"(?P<source>.+?)\s*\((?P<source_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"in\s+(?P<source_place>[^,.;]+)\s+per il valore complessivo di CHF\s+"
    r"(?P<value>[\d'.]+)\s+accettato dalla società per tale importo,\s*"
    r"interamente computati sul capitale azionario,\s*contro attribuzione di\s+"
    r"(?P<issued_shares>[\d']+)\s+azioni nominative di nominali CHF\s+"
    r"(?P<issued_nominal>[\d'.]+)\s+interamente liberate\.\s*Contratto:\s*"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_COLLECTIVE_SIGNING_GRANTED = re.compile(
    r"^Signature collective à deux a été conférée à\s+"
    r"(?P<name>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*(?P<origin_country>[A-Z]{1,3}),\s*"
    r"à\s*(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{1,3})\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_INDIVIDUAL_SIGNINGS_SHARED_ORIGIN = re.compile(
    r"^Signature individuelle est conférée à\s+(?P<name1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*toutes deux à\s+(?P<place12>[^,.;]+),\s*et\s+"
    r"(?P<name3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+),\s*"
    r"toutes trois de\s+(?P<origin>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_OWNER_BANKRUPTCY_REVOKED = re.compile(
    r"^Par décision du\s+(?P<date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>.+?)\s+a prononcé la révocation de la faillite du titulaire\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_ASSETS_ONLY_NO_CONSIDERATION = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*keine\.?$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_WITH_COMMISSIONER_HISTORY = re.compile(
    r"^Mit Entscheid vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+eine definitive Nachlassstundung von\s+"
    r"(?P<duration>.+?)\s+bewilligt\.\s*Die\s+(?P<commissioner>.+?)\s*"
    r"\((?P<commissioner_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+"
    r"(?P<commissioner_place>.+?)\s+wurde als Sachwalterin eingesetzt\s*"
    r"\(Mandatsleiter:\s*(?P<leader1>.+?)\s+und\s+(?P<leader2>.+?)\)\.\s*"
    r"\[bisher:\s*Mit Entscheid vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<previous_authority>.+?)\s+die provisorische Nachlassstundung bis zum\s+"
    r"(?P<previous_until>\d{2}\.\d{2}\.\d{4})\s+bewilligt\.\s*Die\s+"
    r"(?P<previous_commissioner>.+?)\s*"
    r"\((?P<previous_commissioner_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+"
    r"(?P<previous_commissioner_place>.+?)\s+wurde als provisiorische "
    r"Sachwalterin eingesetzt\s*\(Mandatsleiter:\s*"
    r"(?P<previous_leader1>.+?)\s+und\s+(?P<previous_leader2>.+?)\)\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_DEFINITIVE_MORATORIUM_UNTIL_WITH_COMMISSIONER = re.compile(
    r"^Par décision du\s+(?P<date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"(?P<authority>.+?)\s+a accordé à\s+(?P<subject>.+?)\s+un sursis "
    r"concordataire définitif jusqu['’]au\s+"
    r"(?P<until>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.\s*"
    r"(?P<commissioner>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s*(?P<place>[^,.;]+),\s*"
    r"est désigné en qualité de commissaire au sursis\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_DISSOLVED_TWO_LIQUIDATORS = re.compile(
    r"^La fondation est dissoute par décision de son autorité de surveillance du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.\s*Liquidateurs:\s*"
    r"(?P<name1>[^,.;]+),\s*(?P<role1>président),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*(?P<role2>vice-présidente?),\s*"
    r"membres du conseil de fondation,\s*lesquels continuent de signer "
    r"collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_NAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+no\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que la "
    r"nouvelle raison sociale de l['’]organe de révision est\s+"
    r"(?P<name>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s*"
    r"\(et non pas\s+(?P<previous_name>.+?)\)\.?$",
    re.I | re.UNICODE,
)
_IT_FOUNDATION_DEED_DATE_CORRECTED = re.compile(
    r"^Data corretta dell['’]atto di fondazione:\s*"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s*"
    r"\[non:\s*(?P<previous_date>\d{2}\.\d{2}\.\d{4})\]\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_BOARD_MEMBERS_ONE_PRESIDENT = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s*(?P<place1>[^,.;]+),\s*"
    r"(?P<country1>[A-Z]{1,3}),\s*président,\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s*(?P<place2>[^,.;]+),\s*"
    r"(?P<country2>[A-Z]{1,3}),\s*sont membres du conseil d['’]administration"
    r"(?:\s+avec signature (?P<signing>individuelle))?\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_ORGANIZATION_DETAILS_CHANGED = re.compile(
    r"^L['’]associée\s+(?P<previous_name>.+?)\s*"
    r"\((?P<previous_registry_id>[^)]+)\)\s+a actuellement pour raison sociale, "
    r"numéro d['’]identification des entreprises et siège:\s*"
    r"(?P<name>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"à\s*(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_SOLE_PROPRIETOR_CONTRIBUTION_WITH_SHARES = re.compile(
    r"^eingetragenen Einzelunternehmens\s+(?P<source>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"gemäss Vertrag vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+und "
    r"Übernahmebilanz per\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4})\s+mit "
    r"Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+und Passiven von CHF\s+"
    r"(?P<liabilities>[\d'.]+),\s*wofür\s+(?P<shares>[\d']+)\s+"
    r"Stammanteile zu CHF\s+(?P<nominal>[\d'.]+)\s+ausgegeben werden\.?$",
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


def _amount(raw: str) -> Decimal:
    return Decimal(raw.replace("'", ""))


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
    clean_uid = uid.strip() if uid else None
    return Event(
        publication_id=publication_id,
        published_at=published_at,
        event_type=event_type,
        rule_id=rule_id,
        org_uid=org_uid,
        person_key=person_key(name=clean_name, place=clean_place, uid=clean_uid),
        plz=plz,
        canton=canton,
        role=role,
        signing=signing,
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def _fr_people_with_country(raw: str) -> list[dict[str, str]] | None:
    matches = list(_FR_PERSON_WITH_COUNTRY.finditer(raw))
    if not matches:
        return None
    cursor = 0
    for match in matches:
        separator = raw[cursor:match.start()]
        if cursor == 0:
            if separator.strip():
                return None
        elif not re.fullmatch(r"\s*,\s*(?:et\s+)?", separator, re.I | re.UNICODE):
            return None
        cursor = match.end()
    if raw[cursor:].strip(" ."):
        return None
    people = [
        {key: value.strip() for key, value in match.groupdict().items()}
        for match in matches
    ]
    people[-1]["name"] = re.sub(r"^et\s+", "", people[-1]["name"], flags=re.I)
    return people


def extract_parser191_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 191."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_AUDITOR_UID_SUPPLEMENT.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.auditor_uid_supplement.v1",
            match.group("name"), place=match.group("place"), uid=match.group("uid"),
            role="Revisionsstelle", extra={
                "action": "identification_supplemented", "uid": match.group("uid"),
                "previous_name": match.group("previous_name").strip(),
                "previous_registry_id": match.group("previous_registry_id").strip(),
            },
        )], ""

    match = _FR_COMMITTEE_MEMBERS_WITHOUT_SIGNATURE.fullmatch(leftover)
    if match:
        members = _fr_people_with_country(match.group("members"))
        if members:
            rule_id = "fr.persons.committee_members_without_signature.v1"
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, member["name"],
                    place=member["place"], role="membre du comité", extra={
                        "action": "appointed", "origin": member["origin"],
                        "country": member["country"], "without_signature": True,
                    },
                )
                for member in members
            ], ""

    match = _FR_OTHER_ADDRESS_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.other_address_corrected.v1", {
                "kind": "other_address", "action": "publication_corrected",
                "to": match.group("address").strip(),
                "from": match.group("previous_address").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _IT_CAPITAL_INCREASE_CONTRIBUTION_IN_KIND.fullmatch(leftover)
    if match:
        source_shares = _count(match.group("source_shares"))
        issued_shares = _count(match.group("issued_shares"))
        source_nominal = _amount(match.group("source_nominal"))
        issued_nominal = _amount(match.group("issued_nominal"))
        value = _amount(match.group("value"))
        if (
            source_shares == issued_shares
            and source_nominal == issued_nominal
            and source_shares * source_nominal == value
        ):
            return [_event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "it.text.capital_increase_contribution_in_kind.v1", {
                    "kind": "contribution_in_kind", "action": "capital_increased",
                    "source": match.group("source").strip(),
                    "source_uid": match.group("source_uid"),
                    "source_place": match.group("source_place").strip(),
                    "source_shares_count": source_shares,
                    "source_share_nominal": match.group("source_nominal"),
                    "value": match.group("value"),
                    "issued_shares_count": issued_shares,
                    "issued_share_nominal": match.group("issued_nominal"),
                    "fully_paid": True, "currency": "CHF",
                    "contract_date": _iso_date(match.group("date")),
                },
            )], ""

    match = _FR_COLLECTIVE_SIGNING_GRANTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.collective_signing_granted.v1",
            match.group("name"), place=match.group("place"),
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "granted", "origin": match.group("origin").strip(),
                "origin_country": match.group("origin_country"),
                "country": match.group("country"),
            },
        )], ""

    match = _FR_THREE_INDIVIDUAL_SIGNINGS_SHARED_ORIGIN.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.three_individual_signings_shared_origin.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                place=match.group("place12" if index < 3 else "place3"),
                signing="Einzelunterschrift", extra={
                    "action": "granted", "origin": match.group("origin").strip(),
                },
            )
            for index in (1, 2, 3)
        ], ""

    match = _FR_OWNER_BANKRUPTCY_REVOKED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.owner_bankruptcy_revoked_by_court.v1", {
                "kind": "bankruptcy_revoked", "scope": "owner",
                "action": "revoked", "decision_date": _iso_date(match.group("date")),
                "authority": match.group("authority").strip(),
            },
        )], ""

    match = _DE_ASSET_TRANSFER_ASSETS_ONLY_NO_CONSIDERATION.fullmatch(leftover)
    if match and leftover.count("Vermögensübertragung:") == 1:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_assets_only_no_consideration.v1", {
                "kind": "asset_transfer", "action": "transferred",
                "date": _iso_date(match.group("date")),
                "assets": match.group("assets"), "liabilities": None,
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": None, "currency": "CHF",
            },
        )], ""

    match = _DE_DEFINITIVE_MORATORIUM_WITH_COMMISSIONER_HISTORY.fullmatch(leftover)
    if match and match.group("commissioner_uid") == match.group("previous_commissioner_uid"):
        rule_id = "de.text.definitive_moratorium_with_commissioner_history.v1"
        commissioner = match.group("commissioner").strip()
        commissioner_place = match.group("commissioner_place").strip()
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "composition_moratorium_granted", "action": "granted",
                    "moratorium_type": "definitive",
                    "decision_date": _iso_date(match.group("date")),
                    "authority": match.group("authority").strip(),
                    "duration": match.group("duration").strip(), "duration_months": 6,
                    "commissioner": commissioner,
                    "commissioner_uid": match.group("commissioner_uid"),
                    "commissioner_place": commissioner_place,
                    "mandate_leaders": [
                        match.group("leader1").strip(), match.group("leader2").strip(),
                    ],
                    "previous_moratorium_type": "provisional",
                    "previous_decision_date": _iso_date(match.group("previous_date")),
                    "previous_until": _iso_date(match.group("previous_until")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, commissioner,
                place=commissioner_place, uid=match.group("commissioner_uid"),
                role="Sachwalterin", extra={
                    "action": "appointed", "uid": match.group("commissioner_uid"),
                    "mandate_leaders": [
                        match.group("leader1").strip(), match.group("leader2").strip(),
                    ],
                },
            ),
        ], ""

    match = _FR_DEFINITIVE_MORATORIUM_UNTIL_WITH_COMMISSIONER.fullmatch(leftover)
    if match:
        rule_id = "fr.text.definitive_moratorium_until_with_commissioner.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "composition_moratorium_granted", "action": "granted",
                    "moratorium_type": "definitive",
                    "decision_date": _french_date(match.group("date")),
                    "until": _french_date(match.group("until")),
                    "authority": match.group("authority").strip(),
                    "subject": match.group("subject").strip(),
                    "commissioner": match.group("commissioner").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("commissioner"),
                place=match.group("place"), role="commissaire au sursis", extra={
                    "action": "appointed", "origin": match.group("origin").strip(),
                },
            ),
        ], ""

    match = _FR_FOUNDATION_DISSOLVED_TWO_LIQUIDATORS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.foundation_dissolved_two_liquidators.v1"
        signing = "Kollektivunterschrift zu zweien"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "dissolution", "action": "dissolved",
                    "decision_date": _iso_date(match.group("date")),
                    "authority": "autorité de surveillance",
                },
            ),
            *[
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    role=f"{match.group(f'role{index}')}; membre du conseil de fondation; liquidateur",
                    signing=signing, extra={
                        "action": "appointed_liquidator", "signing_continues": True,
                    },
                )
                for index in (1, 2)
            ],
        ], ""

    match = _FR_AUDITOR_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.auditor_name_corrected.v1",
            match.group("name"), uid=match.group("uid"), role="organe de révision",
            extra={
                "action": "name_corrected", "uid": match.group("uid"),
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _IT_FOUNDATION_DEED_DATE_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "it.text.foundation_deed_date_corrected.v1", {
                "kind": "foundation_deed_date", "action": "corrected",
                "date": _iso_date(match.group("date")),
                "previous_date": _iso_date(match.group("previous_date")),
            },
        )], ""

    match = _FR_TWO_BOARD_MEMBERS_ONE_PRESIDENT.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_board_members_one_president.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role="président" if index == 1 else "membre du conseil d'administration",
                signing="Einzelunterschrift" if match.group("signing") else None,
                extra={
                    "action": "appointed", "origin": match.group(f"origin{index}").strip(),
                    "country": match.group(f"country{index}"),
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_ASSOCIATE_ORGANIZATION_DETAILS_CHANGED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_organization_details_changed.v1",
            match.group("name"), place=match.group("place"), uid=match.group("uid"),
            role="associée", extra={
                "action": "identity_and_seat_changed", "uid": match.group("uid"),
                "previous_name": match.group("previous_name").strip(),
                "previous_registry_id": match.group("previous_registry_id").strip(),
            },
        )], ""

    match = _DE_SOLE_PROPRIETOR_CONTRIBUTION_WITH_SHARES.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.sole_proprietor_contribution_with_shares.v1", {
                "kind": "contribution_in_kind", "action": "acquired",
                "source_kind": "sole_proprietorship",
                "source": match.group("source").strip(),
                "source_place": match.group("place").strip(),
                "source_uid": match.group("uid"),
                "contract_date": _iso_date(match.group("date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "issued_shares_count": _count(match.group("shares")),
                "issued_share_nominal": match.group("nominal"),
                "currency": "CHF",
            },
        )], ""

    return [], text
