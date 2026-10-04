from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_DEPUTY_DIRECTOR_AND_BOARD_PAIR = re.compile(
    r"^(?P<deputy>[^.;]+?)\s+est nommé\s+(?P<deputy_role>directeur adjoint)\.\s*"
    r"(?P<president>[^,.;]+),\s*de\s+(?P<president_origin>[^,.;]+),\s*à\s+"
    r"(?P<president_place>[^,.;]+),\s*(?P<president_role>président),\s*"
    r"(?:avec signature collective à deux,\s*)?et\s+(?P<delegate>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<delegate_origin>[^,.;]+),\s*à\s+"
    r"(?P<delegate_place>[^,.;]+),\s*(?P<delegate_role>délégué),\s*"
    r"avec signature collective à deux,\s*sont membres du conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_FR_PRESIDENT_AND_TWO_RESTRICTED_ADMINISTRATORS = re.compile(
    r"^(?P<president>[^.;]+?)\s+est élu\s+(?P<president_role>président)\.\s*"
    r"Nouveaux administrateurs(?: avec signature collective à deux)?,?\s*"
    r"toutefois pas entre eux:\s*(?P<name1>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,;]+),\s*à\s*"
    r"(?P<place1>[^,.;]+),\s*et\s*(?P<name2>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*à\s*"
    r"(?P<place2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATORS_COLLECTIVE_SIGNING = re.compile(
    r"^Les administrateurs\s+(?P<names>.+?)\s+signent désormais "
    r"(?P<signing>collectivement à deux)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_GIVEN_NAME_CHANGED = re.compile(
    r"^L['’](?P<role>administrateur)\s+(?P<surname>\S+)\s+"
    r"(?P<previous_first_name>[^.;]+?)\s+porte maintenant le prénom de\s+"
    r"(?P<first_name>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_BOARD_LIQUIDATORS = re.compile(
    r"^Liquidateurs:\s*(?P<name1>[^,.;]+),\s*(?P<role1>président),\s*"
    r"(?P<name2>[^,.;]+),\s*(?P<role2>secrétaire),\s*et\s*"
    r"(?P<name3>[^,.;]+),\s*(?P<role3>délégué),\s*"
    r"membres du conseil d['’]administration,\s*lesquels continue(?:nt)? de "
    r"signer (?P<signing>individuellement)\.?$",
    re.I | re.UNICODE,
)
_DE_BOARD_DELEGATE_ROLE_REMOVED = re.compile(
    r"^Eingetragene Person geändert:\s*(?P<name>[^,.;]+),\s*"
    r"(?P<previous_role1>Verwaltungsratsmitglied),\s*"
    r"(?P<previous_role2>Delegierter),\s*"
    r"(?P<previous_signing>Kollektivunterschrift zu zweien),\s*neu\s*"
    r"(?P<role>Verwaltungsratsmitglied),\s*"
    r"(?P<signing>Kollektivunterschrift zu zweien)\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBER_SIGNING_REVOKED = re.compile(
    r"^Le membre du conseil d['’]administration\s+(?P<name>[^,.;]+),\s*"
    r"jusqu['’]ici\s+(?P<previous_role>trésorier),\s*n['’]exerce plus la "
    r"signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ADMINISTRATOR_ROLES_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(publication FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+page\s+"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<name1>[^,.;]+),\s*d['’](?P<origin1>[^,.;]+),\s*à\s*"
    r"(?P<place1>[^,.;]+)\s+est\s+(?P<role1>administrateur président)\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s*"
    r"(?P<place2>[^,.;]+)\s+est\s+(?P<role2>administrateur)\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDATION_DISSOLVED_BY_AUTHORITY = re.compile(
    r"^(?:Name neu:\s*(?P<name>.+? in Liquidation)\.\s*)?"
    r"Die Stiftung ist gemäss Verfügung der\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+vom Amtes wegen per\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4})\s+aufgehoben\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_AND_THREE_MANAGERS = re.compile(
    r"^(?P<seller>[^,.;]+),\s*associé,\s*a cédé\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts sociales "
    r"de CHF\s+(?P<nominal>[\d'.]+),\s*soit\s+(?P<buyer_count1>[\d']+)\s+à\s+"
    r"(?P<buyer1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*et\s+"
    r"(?P<buyer_count2>[\d']+)\s+à\s+(?P<buyer2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*tous deux du\s+(?P<country>[^,.;]+),\s*"
    r"nouveaux associés\.\s*(?P=seller)\s+reste ainsi titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts sociales de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.\s*Gérants:\s*(?P=seller),\s*"
    r"nommé président,\s*(?P=buyer1)\s+et\s+(?P=buyer2),\s*lesquels signent "
    r"(?P<signing>individuellement)\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_BRANCH_REGISTER_FRAGMENT = re.compile(
    r"^HR\s+(?P<register_canton>[A-Z]{2})\]$", re.I | re.UNICODE
)
_FR_FOUNDATION_MEMBER_COLLECTIVE_SAME_ORIGIN_PLACE = re.compile(
    r"^Nouveau membre du conseil de fondation\s*:\s*(?P<name>[^,.;]+),\s*"
    r"de et à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_THREE_INDIVIDUAL = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*de\s+"
    r"(?P<president_origin>[^,.;]+),\s*à\s+(?P<president_place>[^,.;]+),\s*"
    r"(?P<president_country>[A-Z]{1,3}),\s*président,\s*"
    r"(?P<delegate>[^,.;]+),\s*nommée\s+(?P<delegate_role>déléguée)\s+et\s+"
    r"(?P<member>[^,.;]+),\s*de\s+(?P<member_origin>[^,.;]+),\s*à\s+"
    r"(?P<member_place>[^,.;]+),\s*(?P<member_country>[A-Z]{1,3}),\s*"
    r"tous trois\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_WITHOUT_SIGNATURE = re.compile(
    r"^Nouvelle membre du conseil de fondation sans signature:\s*"
    r"(?P<name>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_SAME_SHAREHOLDER = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di\s+(?P<absorbed_name>.+?),\s*"
    r"in\s+(?P<absorbed_place>[^()]+?)\s*\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"secondo il contratto di fusione del\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"e bilancio al\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta "
    r"attivi per CHF\s+(?P<assets>[\d'.]+)\s+e passivi verso terzi per CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s*\.\s*La totalità del capitale azionario delle "
    r"due società è detenuta dallo stesso azionista,\s*la fusione avviene dunque "
    r"senza aumento di capitale e senza attribuzione di azioni\.?$",
    re.I | re.UNICODE,
)
_DE_TWO_REGISTERED_PERSON_CHANGES = re.compile(
    r"^Eingetragene Personen geändert:\s*(?P<name1>[^,.;]+),\s*"
    r"(?P<previous_role11>Gesellschafter),\s*(?P<count1>[\d']+)\s+Stammanteile "
    r"zu CHF\s+(?P<nominal1>[\d'.]+),\s*(?P<previous_role12>Geschäftsführer),\s*"
    r"(?P<previous_signing1>Einzelunterschrift),\s*neu\s*"
    r"(?P<role1>Gesellschafter),\s*(?P<new_count1>[\d']+)\s+Stammanteile zu CHF\s+"
    r"(?P<new_nominal1>[\d'.]+),\s*(?P<without1>ohne Unterschrift);\s*"
    r"(?P<name2>[^,.;]+),\s*(?P<previous_role2>vorsitzender Geschäftsführer),\s*"
    r"(?P<previous_signing2>Einzelunterschrift),\s*neu\s*"
    r"(?P<role2>Geschäftsführer),\s*(?P<signing2>Einzelunterschrift)\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _split_fr_names(raw: str) -> list[str]:
    return [
        value.strip()
        for value in re.split(r",\s*(?:et\s+)?|\s+et\s+", raw)
        if value.strip()
    ]


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


def extract_parser127_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 127."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_DEPUTY_DIRECTOR_AND_BOARD_PAIR.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.deputy_director_and_board_pair.v1"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("deputy"),
            role=match.group("deputy_role"), extra={"action": "appointed"},
        ))
        for prefix in ("president", "delegate"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(prefix),
                place=match.group(f"{prefix}_place"),
                role=match.group(f"{prefix}_role"),
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed",
                    "heimat": match.group(f"{prefix}_origin").strip(),
                },
            ))

    match = _FR_PRESIDENT_AND_TWO_RESTRICTED_ADMINISTRATORS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.president_and_two_restricted_administrators.v1"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("president"),
            role=match.group("president_role"), extra={"action": "appointed_president"},
        ))
        restricted_names = [match.group("name1").strip(), match.group("name2").strip()]
        for index in (1, 2):
            other = restricted_names[1 if index == 1 else 0]
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="administrateur",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed",
                    "heimat": match.group(f"origin{index}").strip(),
                    "not_with": other,
                },
            ))

    match = _FR_ADMINISTRATORS_COLLECTIVE_SIGNING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administrators_collective_signing.v1"
        for name in _split_fr_names(match.group("names")):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, name, role="administrateur",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "modified"},
            ))

    match = _FR_ADMINISTRATOR_GIVEN_NAME_CHANGED.search(leftover)
    if match:
        consume(match)
        name = f"{match.group('surname')} {match.group('first_name').strip()}"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_given_name_changed.v1",
            name, role=match.group("role"),
            extra={
                "action": "name_changed",
                "previous_name": (
                    f"{match.group('surname')} {match.group('previous_first_name').strip()}"
                ),
            },
        ))

    match = _FR_THREE_BOARD_LIQUIDATORS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.three_board_liquidators.v1"
        for index in (1, 2, 3):
            role = f"liquidateur {match.group(f'role{index}')}"
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role=role, signing="Einzelunterschrift",
                extra={
                    "action": "appointed_liquidator",
                    "previous_role": "membre du conseil d'administration",
                    "signing_continues": True,
                },
            ))

    match = _DE_BOARD_DELEGATE_ROLE_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.board_delegate_role_removed.v1",
            match.group("name"), role=match.group("role"),
            signing=match.group("signing"),
            extra={
                "action": "role_changed",
                "previous_roles": [
                    match.group("previous_role1"), match.group("previous_role2")
                ],
                "previous_signing": match.group("previous_signing"),
            },
        ))

    match = _FR_BOARD_MEMBER_SIGNING_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.board_member_signing_revoked.v1",
            match.group("name"), role="membre du conseil d'administration",
            extra={
                "action": "revoked", "signing_revoked": True,
                "previous_role": match.group("previous_role"),
            },
        ))

    match = _FR_TWO_ADMINISTRATOR_ROLES_CORRECTED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_administrator_roles_corrected.v1"
        common = {
            "action": "role_corrected", "correction": True,
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_ref": match.group("notice_ref"),
        }
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role=match.group(f"role{index}"),
                extra={
                    **common, "heimat": match.group(f"origin{index}").strip(),
                },
            ))

    match = _DE_FOUNDATION_DISSOLVED_BY_AUTHORITY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.foundation_dissolved_by_authority.v1",
            {
                "kind": "dissolution", "scope": "foundation",
                "action": "dissolved_ex_officio",
                "decision_date": _iso_date(match.group("decision_date")),
                "effective_date": _iso_date(match.group("effective_date")),
                "authority": match.group("authority").strip(),
                **(
                    {"company_name": match.group("name").strip()}
                    if match.group("name") else {}
                ),
            },
        ))

    match = _FR_ASSOCIATE_TRANSFER_AND_THREE_MANAGERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.associate_transfer_and_three_managers.v1"
        nominal = match.group("nominal")
        seller = match.group("seller").strip()
        buyer_names = [match.group("buyer1").strip(), match.group("buyer2").strip()]
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, seller, role="associé-gérant président",
            signing="Einzelunterschrift",
            extra={
                "action": "shares_transferred_and_appointed_president",
                "counterparties": buyer_names,
                "previous_shares_count": _count(match.group("before")),
                "shares_transferred": _count(match.group("transferred")),
                "shares_count": _count(match.group("remaining")),
                "share_nominal": nominal, "currency": "CHF",
            },
        ))
        for index in (1, 2):
            received = _count(match.group(f"buyer_count{index}"))
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"buyer{index}"),
                place=match.group(f"place{index}"), role="associé-gérant",
                signing="Einzelunterschrift",
                extra={
                    "action": "appointed_manager_and_shares_received",
                    "new_associate": True, "country": match.group("country").strip(),
                    "counterparty": seller, "shares_received": received,
                    "shares_count": received, "share_nominal": nominal,
                    "currency": "CHF",
                },
            ))

    match = _DE_REMOVED_BRANCH_REGISTER_FRAGMENT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.removed_branch_register_fragment.v1",
            {
                "action": "removed", "fragment_only": True,
                "register_canton": match.group("register_canton").upper(),
            },
        ))

    match = _FR_FOUNDATION_MEMBER_COLLECTIVE_SAME_ORIGIN_PLACE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed",
            "fr.persons.foundation_member_collective_same_origin_place.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil de fondation",
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "appointed", "heimat": match.group("place").strip(),
            },
        ))

    match = _FR_ADMINISTRATION_THREE_INDIVIDUAL.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_three_individual.v2"
        people = (
            (
                "president", "président", "president_place",
                "president_origin", "president_country", "appointed",
            ),
            ("delegate", match.group("delegate_role"), None, None, None, "role_changed"),
            (
                "member", "administrateur", "member_place",
                "member_origin", "member_country", "appointed",
            ),
        )
        for name_group, role, place_group, origin_group, country_group, action in people:
            extra = {"action": action}
            if origin_group:
                extra["heimat"] = match.group(origin_group).strip()
            if country_group:
                extra["country"] = match.group(country_group)
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(name_group),
                place=match.group(place_group) if place_group else None,
                role=role, signing="Einzelunterschrift", extra=extra,
            ))

    match = _FR_FOUNDATION_MEMBER_WITHOUT_SIGNATURE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.foundation_member_without_signature.v2",
            match.group("name"), place=match.group("place"),
            role="membre du conseil de fondation",
            signing="ohne Zeichnungsberechtigung",
            extra={
                "action": "appointed", "heimat": match.group("origin").strip(),
                "without_signature": True,
            },
        ))

    match = _IT_MERGER_SAME_SHAREHOLDER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "it.text.merger_same_shareholder.v1",
            {
                "kind": "absorption",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"), "currency": "CHF",
                "same_shareholder": True, "capital_increase": False,
                "share_allocation": False,
            },
        ))

    match = _DE_TWO_REGISTERED_PERSON_CHANGES.search(leftover)
    if match:
        consume(match)
        rule_id = "de.persons.two_registered_person_changes.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role=match.group("role1"),
                extra={
                    "action": "roles_and_signing_changed",
                    "previous_roles": [
                        match.group("previous_role11"), match.group("previous_role12")
                    ],
                    "previous_signing": match.group("previous_signing1"),
                    "shares_count": _count(match.group("new_count1")),
                    "share_nominal": match.group("new_nominal1"),
                    "currency": "CHF", "without_signature": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                role=match.group("role2"), signing=match.group("signing2"),
                extra={
                    "action": "role_changed",
                    "previous_role": match.group("previous_role2"),
                    "previous_signing": match.group("previous_signing2"),
                },
            ),
        ])

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
