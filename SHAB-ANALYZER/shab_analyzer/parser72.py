from __future__ import annotations

import re

from .keys import person_key
from .models import Event


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
_FR_WRITTEN_DATE = (
    r"\d{1,2}(?:er)?\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|"
    r"septembre|octobre|novembre|décembre)\s+\d{4}"
)

_FR_ARBITRATION_CLAUSE = re.compile(
    r"^Les statuts comportent une clause d['’]arbitrage;\s*"
    r"pour les détails,\s*voir les statuts\.?$",
    re.I | re.UNICODE,
)
_FR_STATUTES_DATE_CORRECTION_WRITTEN = re.compile(
    rf"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+) du\s+"
    rf"(?P<entry_date>\d{{2}}\.\d{{2}}\.\d{{4}})\s+\(FOSC du\s+"
    rf"(?P<notice_date>\d{{2}}\.\d{{2}}\.\d{{4}}),\s*p\.\s*"
    rf"(?P<notice_page>\d+)/(?P<notice_id>\d+)\)\s+est rectifiée en ce sens que "
    rf"les statuts ont été modifiés le\s+(?P<date>{_FR_WRITTEN_DATE})\s+"
    rf"\(et non le\s+(?P<previous_date>{_FR_WRITTEN_DATE})\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_SINGLE_DOMICILE_CHANGED = re.compile(
    r"^(?P<name>[^,.;]+)\s+(?:est\s+)?maintenant domicilié(?:e)? à\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_DEFINITIVE_MORATORIUM_GRANTED = re.compile(
    rf"^Par prononcé rendu le\s+(?P<decision_date>{_FR_WRITTEN_DATE}),\s*"
    rf"(?P<authority>.+?)\s+a accordé à la société un sursis concordataire "
    rf"définitif jusqu['’]au\s+(?P<until>{_FR_WRITTEN_DATE})\.?$",
    re.I | re.UNICODE,
)
_FR_SIX_MANAGERS_SIGNING_GRANTED = re.compile(
    r"^Signature individuelle est conférée à\s+"
    r"(?P<name1>[^,.;]+),\s*(?P<name2>[^,.;]+),\s*(?P<name3>[^,.;]+),\s*"
    r"les trois à\s+(?P<place123>[^,.;]+),\s*"
    r"(?P<name4>[^,.;]+),\s*(?P<name5>[^,.;]+),\s*secrétaire,\s*"
    r"les deux à\s+(?P<place45>[^,.;]+),\s*et\s+"
    r"(?P<name6>[^,.;]+),\s*à\s+(?P<place6>[^,.;]+),\s*"
    r"les six d['’](?P<origin>[^,.;]+),\s*tous gérants\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_SIGNING_AND_PROXY = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé(?:e)? président(?:e)?,\s*"
    r"(?P<signed>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<signed_origin>[^,.;]+),\s*à\s+(?P<signed_place>[^,.;]+),\s*"
    r"(?P<signed_country>[A-Z]),\s*lesquels signent individuellement,\s*"
    r"(?P<member>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<member_origin>[^,.;]+),\s*à\s+(?P<member_place>[^,.;]+),\s*et\s*"
    r"(?P<proxy>[^,.;]+)\s*;\s*la procuration du dernier est radiée\.?$",
    re.I | re.UNICODE,
)
_FR_CONTRIBUTION_IN_KIND_MENTION_REMOVED = re.compile(
    r"^Radiation de la mention relative aux apports en nature effectués "
    r"à la constitution de la société\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_MANAGER_PRESIDENT = re.compile(
    r"^(?P<seller>[^,.;]+) cède (?P<transferred>[\d']+) de ses "
    r"(?P<before>[\d']+) parts de CHF (?P<nominal>[\d'.]+) à "
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"à (?P<place>[^,.;]+?)(?:\s*\((?P<country>[^)]+)\))?,\s*"
    r"nouvel associé avec (?P<buyer_count>[\d']+) parts de CHF "
    r"(?P<buyer_nominal>[\d'.]+),\s*gérant (?P=seller),\s*qui est élu "
    r"président des gérants et continue à signer individuellement,\s*reste titulaire "
    r"de (?P<remaining>[\d']+) parts de CHF (?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_IT_HEAD_OFFICE_CAPITAL_CHANGED = re.compile(
    r"^,?\s*Sede principale a:\s*Sede principale:\s*(?P<head_office>[^.]+)\.\s*"
    r"Nuovo capitale sociale/responsabilità della sede principale:\s*"
    r"(?P<currency>[A-Z]{3})\s+(?P<to_total>[\d']+)\.--\s+diviso in\s+"
    r"(?P<to_count>[\d']+) azioni da\s+(?P=currency)\s+"
    r"(?P<to_nominal>[\d']+)\.--\s+interamente liberato\.\s*"
    r"\[finora:\s*Nuovo capitale sociale/responsabilità della sede principale:\s*"
    r"(?P=currency)\s+(?P<from_total>[\d']+)\.--\s+diviso in\s+"
    r"(?P<from_count>[\d']+) azioni da\s+(?P=currency)\s+"
    r"(?P<from_nominal>[\d']+)\.--\s+interamente liberato\]\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBERS_REPLACED = re.compile(
    r"^(?P<removed>.+?)\s+ne sont plus membres du conseil de fondation\.\s*"
    r"(?P<name1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*de et à\s+(?P<place2>[^,.;]+),\s*"
    r"(?P<name3>[^,.;]+),\s*du\s+(?P<origin3>[^,.;]+),\s*à\s+"
    r"(?P<place3>[^,.;]+),\s*(?P<country3>[A-Z]{1,3}),\s*"
    r"(?P<name4>[^,.;]+),\s*de\s+(?P<origin4>[^,.;]+),\s*à\s+"
    r"(?P<place4>[^,.;]+),\s*(?P<country4>[A-Z]{1,3}),\s*"
    r"(?P<name5>[^,.;]+),\s*d['’](?P<origin5>[^,.;]+),\s*à\s+"
    r"(?P<place5>[^,.;]+),\s*(?P<country5>[A-Z]{1,3}),\s*"
    r"sont membres du conseil de fondation,\s*sans signature sociale\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_PERSON_MISSPELLED = re.compile(
    r"^Gelösche Person:\s*(?P<name>[^,.;]+),\s*(?P<role>[^,.;]+),\s*"
    r"(?P<sign>Einzelunterschrift|Kollektivunterschrift(?:\s+zu\s+zweien)?)\.?$",
    re.I | re.UNICODE,
)
_FR_DOMICILE_CORRECTION_SHORT = re.compile(
    r"^L['’]inscription n[°o]\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+) est domicilié(?:e)? à\s+(?P<place>[^()]+?)\s+"
    r"\(et non à\s+(?P<previous_place>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_RESTRICTION_REMOVED_WITH_ROLE = re.compile(
    r"^(?P<name>[^,.;]+),\s*(?P<role>[^,.;]+),\s*continue de signer "
    r"collectivement à deux,\s*désormais sans restriction\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_NO_CONSIDERATION = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+"
    r"und Passiven von CHF\s+(?P<liabilities>[\d'.]+)\s+auf die\s+"
    r"(?P<recipient>.+?),\s*in\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*Gegenleistung:\s*keine\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATES_TRANSFER_AND_MANAGERS = re.compile(
    r"^(?P<seller>[^,.;]+) a cédé (?P<transferred>[\d']+) parts de CHF "
    r"(?P<nominal>[\d'.]+) à (?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvelle associée pour (?P<buyer_count>[\d']+) "
    r"parts de CHF (?P<buyer_nominal>[\d'.]+)\.\s*Par conséquent,\s*"
    r"(?P=seller) est maintenant associé pour (?P<seller_count>[\d']+) parts de CHF "
    r"(?P<seller_nominal>[\d'.]+)\.\s*Gérants:\s*les associés\s+"
    r"(?P=seller),\s*nommé président,\s*et\s*(?P=buyer),\s*tous deux\.?$",
    re.I | re.UNICODE,
)
_IT_SUPERVISOR_AND_ORGANIZATION_REMOVED = re.compile(
    r"^Autorità di vigilanza:\s*(?P<authority>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+(?P<place>[^.]+)\.\s*"
    r"\[L['’]indicazione relativa all['’]organizzazione è cancellata a seguito "
    r"dell['’]abrogazione della disposizione di cui all['’]"
    r"(?P<law>art\.\s*95 cpv\.\s*1 lett\.\s*h ORC)\.\]\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{year}-{month}-{day}"


def _french_date(raw: str) -> str:
    day, month, year = re.sub(r"(?<=\d)er\b", "", raw.strip().lower()).split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _signing(raw: str) -> str:
    return (
        "Einzelunterschrift"
        if "individ" in raw.lower() or "einzel" in raw.lower()
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


def extract_parser72_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 72."""
    del language  # Historical records can contain a different language in this field.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_ARBITRATION_CLAUSE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "fr.text.arbitration_clause.v1",
                {"kind": "arbitration_clause", "present": True, "details_in_statutes": True},
            )
        )

    match = _FR_STATUTES_DATE_CORRECTION_WRITTEN.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "fr.text.statutes_date_correction_written.v1",
                {
                    "action": "corrected",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_page": match.group("notice_page"),
                    "notice_id": match.group("notice_id"),
                    "date": _french_date(match.group("date")),
                    "previous_date": _french_date(match.group("previous_date")),
                },
            )
        )

    match = _FR_SINGLE_DOMICILE_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.single_domicile_changed.v1",
                match.group("name"), place=match.group("place"),
                extra={"action": "domicile_changed", "domicile_changed": True},
            )
        )

    match = _FR_DEFINITIVE_MORATORIUM_GRANTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "fr.text.definitive_moratorium_granted.v1",
                {
                    "kind": "composition_moratorium_granted",
                    "provisional": False,
                    "decision_date": _french_date(match.group("decision_date")),
                    "until": _french_date(match.group("until")),
                    "authority": match.group("authority").strip(),
                },
            )
        )

    match = _FR_SIX_MANAGERS_SIGNING_GRANTED.search(leftover)
    if match:
        consume(match)
        for index, place in (
            (1, match.group("place123")),
            (2, match.group("place123")),
            (3, match.group("place123")),
            (4, match.group("place45")),
            (5, match.group("place45")),
            (6, match.group("place6")),
        ):
            role = "secrétaire et gérant" if index == 5 else "gérant"
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", "fr.persons.six_managers_signing_granted.v1",
                    match.group(f"name{index}"), place=place, role=role,
                    signing="Einzelunterschrift",
                    extra={"action": "granted", "heimat": match.group("origin").strip()},
                )
            )

    match = _FR_ADMINISTRATION_SIGNING_AND_PROXY.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_signing_and_proxy.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("president"),
                    role="président", signing="Einzelunterschrift",
                    extra={"action": "appointed"},
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("signed"),
                    place=match.group("signed_place"), role="administrateur",
                    signing="Einzelunterschrift",
                    extra={
                        "action": "appointed",
                        "heimat": match.group("signed_origin").strip(),
                        "country": match.group("signed_country"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("member"),
                    place=match.group("member_place"), role="administrateur",
                    extra={
                        "action": "appointed",
                        "heimat": match.group("member_origin").strip(),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", rule_id, match.group("proxy"),
                    extra={"action": "revoked", "previous_signing": "procuration"},
                ),
            ]
        )

    match = _FR_CONTRIBUTION_IN_KIND_MENTION_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "fr.text.contribution_in_kind_mention_removed.v1",
                {
                    "kind": "contribution_in_kind",
                    "action": "mention_removed",
                    "at_incorporation": True,
                },
            )
        )

    match = _FR_ASSOCIATE_TRANSFER_MANAGER_PRESIDENT.search(leftover)
    if match:
        consume(match)
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        rule_id = "fr.persons.associate_transfer_manager_president.v2"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé et président des gérants",
                    signing="Einzelunterschrift",
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
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé",
                    extra={
                        "action": "shares_received",
                        "heimat": match.group("origin").strip(),
                        "country": match.group("country"),
                        "counterparty": seller,
                        "shares_received": _count(match.group("transferred")),
                        "shares_count": _count(match.group("buyer_count")),
                        "shares_nominal": match.group("buyer_nominal"),
                    },
                ),
            ]
        )

    match = _IT_HEAD_OFFICE_CAPITAL_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "it.text.head_office_capital_changed.v1",
                {
                    "scope": "head_office",
                    "head_office": match.group("head_office").strip(),
                    "currency": match.group("currency"),
                    "from_total": match.group("from_total"),
                    "to_total": match.group("to_total"),
                    "from_count": _count(match.group("from_count")),
                    "to_count": _count(match.group("to_count")),
                    "from_nominal": match.group("from_nominal"),
                    "to_nominal": match.group("to_nominal"),
                    "paid_in_full": True,
                },
            )
        )

    match = _FR_FOUNDATION_MEMBERS_REPLACED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.foundation_members_replaced.v1"
        for name in [part.strip() for part in match.group("removed").split(",")]:
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", rule_id, name, role="membre du conseil de fondation",
                    extra={"action": "removed"},
                )
            )
        additions = (
            (1, match.group("origin1"), match.group("place1"), None),
            (2, match.group("place2"), match.group("place2"), None),
            (3, match.group("origin3"), match.group("place3"), match.group("country3")),
            (4, match.group("origin4"), match.group("place4"), match.group("country4")),
            (5, match.group("origin5"), match.group("place5"), match.group("country5")),
        )
        for index, origin, place, country in additions:
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    place=place, role="membre du conseil de fondation",
                    extra={
                        "action": "appointed",
                        "heimat": origin.strip(),
                        "country": country,
                        "without_signature": True,
                    },
                )
            )

    match = _DE_REMOVED_PERSON_MISSPELLED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", "de.persons.removed_misspelled_heading.v1",
                match.group("name"), role=match.group("role"),
                signing=_signing(match.group("sign")), extra={"action": "removed"},
            )
        )

    match = _FR_DOMICILE_CORRECTION_SHORT.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.domicile_correction_short.v1",
                match.group("name"), place=match.group("place"),
                extra={
                    "action": "domicile_corrected",
                    "previous_place": match.group("previous_place").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                },
            )
        )

    match = _FR_SIGNING_RESTRICTION_REMOVED_WITH_ROLE.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed",
                "fr.persons.signing_restriction_removed_with_role.v1",
                match.group("name"), role=match.group("role"),
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "restriction_removed", "signing_continues": True},
            )
        )

    match = _DE_ASSET_TRANSFER_NO_CONSIDERATION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.asset_transfer_no_consideration.v1",
                {
                    "date": _iso_date(match.group("date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration": "keine",
                    "gratuitous": True,
                },
            )
        )

    match = _FR_ASSOCIATES_TRANSFER_AND_MANAGERS.search(leftover)
    if match:
        consume(match)
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        rule_id = "fr.persons.associates_transfer_and_managers.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller,
                    role="associé et président des gérants",
                    extra={
                        "action": "shares_transferred_and_appointed",
                        "counterparty": buyer,
                        "shares_transferred": _count(match.group("transferred")),
                        "shares_count": _count(match.group("seller_count")),
                        "shares_nominal": match.group("seller_nominal"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associée et gérante",
                    extra={
                        "action": "shares_received_and_appointed",
                        "heimat": match.group("origin").strip(),
                        "counterparty": seller,
                        "shares_received": _count(match.group("transferred")),
                        "shares_count": _count(match.group("buyer_count")),
                        "shares_nominal": match.group("buyer_nominal"),
                    },
                ),
            ]
        )

    match = _IT_SUPERVISOR_AND_ORGANIZATION_REMOVED.search(leftover)
    if match:
        consume(match)
        events.extend(
            [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "supervisor_changed", "it.text.supervisor_existing_form.v1",
                    {
                        "to": match.group("authority").strip(),
                        "uid": match.group("uid"),
                        "place": match.group("place").strip(),
                    },
                ),
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "organization_changed", "it.text.organization_removed.v2",
                    {
                        "action": "removed",
                        "reason": "changed_registration_rules",
                        "law": re.sub(r"\s+", " ", match.group("law")).strip(),
                    },
                ),
            ]
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
