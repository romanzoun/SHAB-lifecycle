from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_PROXY_REVOKED_DIRECTOR = re.compile(
    r"^(?P<name>[^,.;]+),\s*dont la procuration est éteinte,\s*"
    r"est nommé(?:e)?\s+(?P<role>directeur|directrice) avec un administrateur\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_WITH_LIABILITIES = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+"
    r"und Passiven von CHF\s+(?P<liabilities>[\d'.]+)"
    r"(?:\s+(?P<liabilities_kind>\(Fremdkapital\)))?\s+auf die\s+"
    r"(?P<recipient>.+?),\s*in\s+(?P<place>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:?\s*(?P<consideration>.+?)\.?$",
    re.I | re.UNICODE,
)
_DE_CLAIM_CONSIDERATION = re.compile(
    r"Eine Forderung über CHF\s+(?P<amount>[\d'.]+)$", re.I | re.UNICODE
)
_DE_SHARES_AND_CLAIM_CONSIDERATION = re.compile(
    r"CHF\s+(?P<count>[\d']+)\s+Namenaktien zu CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+und eine Forderungsgutschrift von CHF\s+"
    r"(?P<claim>[\d'.]+)$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_SUSPENDED_DATE_BEFORE = re.compile(
    r"^(?P<authority>Le président du Tribunal de l['’]arrondissement de .+?)\s+"
    r"a prononcé le\s+(?P<date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4})\s+l['’]effet suspensif de la faillite\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_SUSPENDED_DATE_AFTER = re.compile(
    r"^(?P<authority>Le président du Tribunal de l['’]arrondissement de .+?)\s+"
    r"a prononcé l['’]effet suspensif de la faillite le\s+"
    r"(?P<date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4})\.\s*La raison de commerce redevient:?\s+"
    r"(?P<name>.+?)\.?$",
    re.I | re.UNICODE,
)
_DE_ERRONEOUS_NEW_REGISTRATION_DELETED = re.compile(
    r"^Mit dem im SHAB-Nr\.\s*(?P<issue>\d+) vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}) publizierten TR-Eintrag\s+"
    r"(?P<entry>\d+)/(?P<entry_year>\d{4}) wurde das Einzelunternehmen "
    r"irrtümlich durch Neueintrag anstatt mittels Sitzverlegung eingetragen\.\s*"
    r"Somit erfolgt folgende Löschung\.\s*Der Eintrag dieses Einzelunternehmens "
    r"erfolgte irrtümlich durch Neueintrag in\s+(?P<place>.+?)\s+anstatt mittels "
    r"Sitzverlegung der\s+(?P<source>.+?)\s+von\s+(?P<previous_place>.+?)\.\s*"
    r"Der Neueintrag wird somit widerrufen und dieses Einzelunternehmen gelöscht\.?$",
    re.I | re.UNICODE,
)
_FR_LIQUIDATORS_AND_SIGNING_REMOVALS = re.compile(
    r"^Liquidateurs:\s*(?P<name1>[^,.;]+),\s*"
    r"(?P<roles1>gérant et président),\s*et\s+(?P<name2>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*à\s*"
    r"(?P<place2>[^,.;]+),\s*lesquels signent collectivement à deux;\s*"
    r"les pouvoirs de\s+(?P=name1)\s+sont modifiés en ce sens\.\s*"
    r"(?P<removed1>[^,.;]+)\s+et\s+(?P<removed2>[^,.;]+),\s*"
    r"tous deux gérants,\s*n['’]exercent plus la signature sociale\.?$",
    re.I | re.UNICODE,
)
_IT_COMPANY_BANKRUPTCY_EFFECT_SUSPENDED = re.compile(
    r"^Con decreto del\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"(?P<authority>.+?)\s+ha accordato effetto sospensivo al reclamo inoltrato "
    r"contro la decisione di apertura del fallimento della\s+"
    r"(?P<court>.+?)\s+del\s+(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"L['’]iscrizione nel registro di commercio relativa allo scioglimento della "
    r"società a seguito di fallimento viene pertanto cancellata\.\s*"
    r"\[finora:\s*La società è sciolta in seguito a fallimento pronunciato con "
    r"decreto della\s+(?P<previous_court>.+?)\s+del\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+a far tempo dal\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}) alle ore\s+"
    r"(?P<effective_time>\d{2}:\d{2})\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_JOINT_ASSOCIATE_TRANSFER = re.compile(
    r"^(?P<seller1>[^,.;]+)\s+et\s+(?P<seller2>[^,.;]+)\s+ont cédé\s+"
    r"(?P<transferred>[\d']+) parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s*(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{1,3}),\s*nouvelle associée pour\s+"
    r"(?P<buyer_count>[\d']+) parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"laquelle associée est en outre nommée gérante\s*"
    r"Par conséquent,\s*(?P=seller1)\s+et\s+(?P=seller2)\s+sont désormais "
    r"titulaires de,\s*respectivement,\s*(?P<seller1_count>[\d']+) parts de CHF\s+"
    r"(?P<seller1_nominal>[\d'.]+)\s+et\s+(?P<seller2_count>[\d']+) parts de CHF\s+"
    r"(?P<seller2_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PRESIDENT_AND_MEMBER = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé(?:e)? président(?:e)?,\s*"
    r"lequel continue à signer individuellement\s+et\s+(?P<member>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s*"
    r"(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{1,3}),?\s*$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_MOVE_AND_MEMBER = re.compile(
    r"^Administration\s*:\s*(?P<president>[^,.;]+),?\s*maintenant domicilié(?:e)? à\s*"
    r"(?P<president_place>[^,.;]+),\s*(?P<president_country>[A-Z]{2,3}),\s*"
    r"nommé(?:e)? président(?:e)?,\s*et\s+(?P<member>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s*"
    r"(?P<member_place>[^,.;]+),\s*tous deux\.?$",
    re.I | re.UNICODE,
)
_IT_FOUNDATION_ORGANIZATION_CHANGED = re.compile(
    r"^Nuova organizzazione:\s*\[Organizzazione:\s*(?P<current>[^\]]+?)\]\.?\s*"
    r"\[finora:\s*Organizzazione:\s*(?P<previous>[^\]]+?)\]\s*"
    r"Atto di fondazione modificato con decisione del\s+(?P<authority>.+?),\s*"
    r"in\s+(?P<authority_place>[^,.;]+),\s*quale autorità di vigilanza,\s*"
    r"in data\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"su punti non soggetti a pubblicazione\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBERS_PAIR_COLLECTIVE = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s*(?P<place1>[^,.;]+),\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*de et à\s*(?P<place2>[^,.;]+),\s*"
    r"sont membres du conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBERS_PAIR_WITHOUT_SIGNATURE = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s*(?P<place1>[^,.;]+),\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s*(?P<place2>[^,.;]+),\s*"
    r"sont membres du conseil d['’]administration sans signature\.?$",
    re.I | re.UNICODE,
)
_DE_PREVIOUS_DOMICILE_CORRECTED = re.compile(
    r"^\[Der bisherige Wohnsitz von\s+(?P<name>.+?)\s+war\s+"
    r"(?P<place>[^()]+?)\s*\(nicht:\s*(?P<previous_place>[^)]+)\)\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_ORGANIZATION_RENAMED_AND_MOVED = re.compile(
    r"^Nouvelle raison sociale et nouveau siège de l['’]associée\s+"
    r"[\"“](?P<old_name>.+?)[\"”]\s+"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\):\s*"
    r"[\"“](?P<name>.+?)[\"”],\s*(?P<place>.+?)\.?$",
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
    return f"{year}-{month}-{day}"


def _french_date(raw: str) -> str:
    day, month, year = raw.strip().lower().split()
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
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser76_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 76."""
    del language  # Historical records can contain a different language in this field.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_PROXY_REVOKED_DIRECTOR.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.proxy_revoked_director.v1",
                match.group("name"), role=match.group("role").lower(),
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed",
                    "previous_signing": "procuration",
                    "previous_signing_revoked": True,
                    "signing_restriction": "avec un administrateur",
                },
            )
        )

    match = _DE_ASSET_TRANSFER_WITH_LIABILITIES.search(leftover)
    if match:
        consume(match)
        consideration = match.group("consideration").strip()
        payload = {
            "date": _iso_date(match.group("date")),
            "assets": match.group("assets"),
            "liabilities": match.group("liabilities"),
            "currency": "CHF",
            "liabilities_kind": (
                "third_party_capital" if match.group("liabilities_kind") else None
            ),
            "recipient": match.group("recipient").strip(),
            "recipient_place": match.group("place").strip(),
            "recipient_uid": match.group("uid"),
            "consideration": consideration,
        }
        claim = _DE_CLAIM_CONSIDERATION.fullmatch(consideration)
        shares = _DE_SHARES_AND_CLAIM_CONSIDERATION.fullmatch(consideration)
        if claim:
            payload.update(
                {
                    "consideration_kind": "claim",
                    "consideration_amount": claim.group("amount"),
                }
            )
        elif shares:
            payload.update(
                {
                    "consideration_kind": "registered_shares_and_claim_credit",
                    "shares_count": _count(shares.group("count")),
                    "share_nominal": shares.group("nominal"),
                    "claim_credit": shares.group("claim"),
                }
            )
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.asset_transfer_with_liabilities.v1",
                payload,
            )
        )

    for pattern, rule_id in (
        (_FR_BANKRUPTCY_SUSPENDED_DATE_BEFORE, "fr.text.bankruptcy_effect_suspended.v2"),
        (_FR_BANKRUPTCY_SUSPENDED_DATE_AFTER, "fr.text.bankruptcy_effect_suspended.v2"),
    ):
        match = pattern.search(leftover)
        if match:
            consume(match)
            payload = {
                "kind": "bankruptcy_effect_suspended",
                "decision_date": _french_date(match.group("date")),
                "authority": match.group("authority").strip(),
            }
            restored_name = match.groupdict().get("name")
            if restored_name:
                payload["company_name_restored"] = restored_name.strip()
            events.append(
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "status_changed", rule_id, payload,
                )
            )
            break

    match = _DE_ERRONEOUS_NEW_REGISTRATION_DELETED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_deleted", "de.text.erroneous_new_registration_deleted.v1",
                {
                    "kind": "registration_cancelled",
                    "reason": "new_registration_instead_of_seat_transfer",
                    "issue": match.group("issue"),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "entry": match.group("entry"),
                    "entry_year": int(match.group("entry_year")),
                    "erroneous_place": match.group("place").strip(),
                    "source_company": match.group("source").strip(),
                    "previous_place": match.group("previous_place").strip(),
                    "new_registration_revoked": True,
                },
            )
        )

    match = _FR_LIQUIDATORS_AND_SIGNING_REMOVALS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.liquidators_and_signing_removals.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("name1"),
                    role="gérant, président et liquidateur",
                    signing="Kollektivunterschrift zu zweien",
                    extra={"action": "appointed_liquidator", "powers_changed": True},
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("name2"),
                    place=match.group("place2"), role="liquidatrice",
                    signing="Kollektivunterschrift zu zweien",
                    extra={
                        "action": "appointed_liquidator",
                        "heimat": match.group("origin2").strip(),
                    },
                ),
            ]
        )
        for group in ("removed1", "removed2"):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", rule_id, match.group(group),
                    role="gérant",
                    extra={"action": "revoked", "signing_revoked": True},
                )
            )

    match = _IT_COMPANY_BANKRUPTCY_EFFECT_SUSPENDED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "it.text.company_bankruptcy_effect_suspended.v1",
                {
                    "kind": "bankruptcy_effect_suspended",
                    "scope": "company",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                    "effective_at": (
                        f"{_iso_date(match.group('effective_date'))}T"
                        f"{match.group('effective_time')}"
                    ),
                    "authority": match.group("authority").strip(),
                    "bankruptcy_court": match.group("court").strip(),
                    "previous_entry_removed": True,
                },
            )
        )

    match = _FR_JOINT_ASSOCIATE_TRANSFER.search(leftover)
    if match:
        consume(match)
        seller_names = [match.group("seller1").strip(), match.group("seller2").strip()]
        buyer = match.group("buyer").strip()
        rule_id = "fr.persons.joint_associate_transfer.v1"
        for index, seller in enumerate(seller_names, start=1):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé",
                    extra={
                        "action": "shares_adjusted_after_joint_transfer",
                        "counterparty": buyer,
                        "joint_transferors": seller_names,
                        "shares_transferred_jointly": _count(match.group("transferred")),
                        "shares_count": _count(match.group(f"seller{index}_count")),
                        "shares_nominal": match.group(f"seller{index}_nominal"),
                    },
                )
            )
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée-gérante", signing="Einzelunterschrift",
                extra={
                    "action": "shares_received_and_appointed",
                    "heimat": match.group("origin").strip(),
                    "country": match.group("country"),
                    "counterparties": seller_names,
                    "shares_received": _count(match.group("buyer_count")),
                    "shares_count": _count(match.group("buyer_count")),
                    "shares_nominal": match.group("buyer_nominal"),
                },
            )
        )

    match = _FR_ADMINISTRATION_PRESIDENT_AND_MEMBER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_president_and_member.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("president"),
                    role="président", signing="Einzelunterschrift",
                    extra={"action": "appointed", "signing_continues": True},
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("member"),
                    place=match.group("place"), role="administrateur",
                    signing="Kollektivunterschrift zu zweien",
                    extra={
                        "action": "appointed",
                        "heimat": match.group("origin").strip(),
                        "country": match.group("country"),
                    },
                ),
            ]
        )

    match = _FR_ADMINISTRATION_MOVE_AND_MEMBER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_move_and_member.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("president"),
                    place=match.group("president_place"), role="président",
                    signing="Einzelunterschrift",
                    extra={
                        "action": "role_and_domicile_changed",
                        "country": match.group("president_country"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("member"),
                    place=match.group("member_place"), role="administrateur",
                    signing="Einzelunterschrift",
                    extra={
                        "action": "appointed",
                        "heimat": match.group("origin").strip(),
                    },
                ),
            ]
        )

    match = _IT_FOUNDATION_ORGANIZATION_CHANGED.search(leftover)
    if match:
        consume(match)
        rule_id = "it.text.foundation_organization_changed.v1"
        events.extend(
            [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "organization_changed", rule_id,
                    {
                        "kind": "foundation_organization",
                        "action": "changed",
                        "from": match.group("previous").strip(" ."),
                        "to": match.group("current").strip(" ."),
                    },
                ),
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "statutes_changed", "it.text.foundation_deed_non_public_changes.v1",
                    {
                        "date": _iso_date(match.group("date")),
                        "authority": match.group("authority").strip(),
                        "authority_place": match.group("authority_place").strip(),
                        "kind": "non_public_changes",
                    },
                ),
            ]
        )

    match = _FR_BOARD_MEMBERS_PAIR_COLLECTIVE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.board_members_pair_collective.v1"
        people = (
            (
                match.group("name1"), match.group("place1"),
                {"heimat": match.group("origin1").strip()},
            ),
            (match.group("name2"), match.group("place2"), {}),
        )
        for name, place, extra in people:
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, name, place=place,
                    role="membre du conseil d'administration",
                    signing="Kollektivunterschrift zu zweien",
                    extra={"action": "appointed", **extra},
                )
            )

    match = _FR_BOARD_MEMBERS_PAIR_WITHOUT_SIGNATURE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.board_members_pair_without_signature.v3"
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    place=match.group(f"place{index}"),
                    role="membre du conseil d'administration",
                    extra={
                        "action": "appointed",
                        "heimat": match.group(f"origin{index}").strip(),
                        "without_signature": True,
                    },
                )
            )

    match = _DE_PREVIOUS_DOMICILE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "de.persons.previous_domicile_corrected.v1",
                match.group("name"), place=match.group("place"),
                extra={
                    "action": "previous_domicile_corrected",
                    "previous_place": match.group("previous_place").strip(),
                },
            )
        )

    match = _FR_ASSOCIATE_ORGANIZATION_RENAMED_AND_MOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed",
                "fr.persons.associate_organization_renamed_and_moved.v1",
                match.group("name"), place=match.group("place"), uid=match.group("uid"),
                role="associée",
                extra={
                    "action": "name_and_seat_changed",
                    "previous": match.group("old_name").strip(),
                    "registry_id": match.group("uid"),
                },
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
