from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_FOUNDATION_BOARD_ROLE_CHANGES_AND_NEW_MEMBERS = re.compile(
    r"^Les membres du conseil de fondation\s+(?P<name1>[^,.;]+),\s*"
    r"jusqu['’]ici\s+(?P<previous_role1>[^,.;]+),\s*maintenant\s+"
    r"(?P<role1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<previous_role2>[^,.;]+),\s*continuent à signer collectivement à deux\.\s*"
    r"(?P<name3>[^,.;]+),\s*de\s+"
    r"(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+),\s*"
    r"(?P<role3>président)\s+et\s+(?P<name4>[^,.;]+),\s*"
    r"de\s+(?P<origin4>[^,.;]+),\s*à\s+"
    r"(?P<place4>[^,.;]+),\s*(?P<country4>[A-Z]{1,3}),\s*"
    r"sont membres du conseil de fondation,\s*tous deux"
    r"(?:\s+avec signature collective à deux)?\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_REGISTERED_WITH_REFERENCE = re.compile(
    r"^Neue Zweigniederlassung:\s*(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*eingetragen am\s+"
    r"(?P<registration_date>\d{2}\.\d{2}\.\d{4})\s*\(SHAB vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_FULL_ADDRESS_AND_ADDITIONAL_ADDRESSES = re.compile(
    r"^Vollständige Adresse:\s*(?P<full_address>.+?)\.\s*"
    r"Neue zusätzliche Adressen:\s*(?P<additional_addresses>.+?)\.?$",
    re.I | re.UNICODE,
)
_DE_ADDRESS = re.compile(
    r"^(?P<street>.+?),\s*(?P<postal_code>\d{4})\s+"
    r"(?P<locality>.+?)(?:\s+(?P<canton>[A-Z]{2}))?$",
    re.UNICODE,
)
_FR_AUDITOR_NAME_CHANGED = re.compile(
    r"^(?P<previous_name>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"organe de révision,\s*a modifié sa raison de commerce en\s+"
    r"(?P<name>.+?)\s*\((?P=uid)\)\.?$",
    re.I | re.UNICODE,
)
_DE_OWNER_BANKRUPTCY_APPEAL_ENTRY_REMOVED_BY_ORDER = re.compile(
    r"^Mit Verfügung des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+ist der Beschwerde gegen die "
    r"Verfügung des\s+(?P<court>.+?)\s+vom\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+aufschiebende Wirkung "
    r"zuerkannt worden\.\s*Demnach wird die Eintragung betreffend Konkurs im "
    r"Handelsregister gestrichen\.\s*\[gestrichen:\s*Über die Inhaberin dieses "
    r"Einzelunternehmens ist mit Verfügung der\s+(?P<previous_court>.+?)\s+vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+mit Wirkung ab dem\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}[.:]\d{2})\s+Uhr,\s*der Konkurs eröffnet worden\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_APPOINTED_MANAGER_PRESIDENT_INDIVIDUAL = re.compile(
    r"^(?P<name>[^,.;]+),\s*associée,\s*nommée gérante et présidente,\s*"
    r"exerce désormais la signature sociale,\s*individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_PRESIDENCY_SWAPPED = re.compile(
    r"^(?P<name1>[^,.;]+),\s*jusqu['’]ici\s+(?P<previous_role1>vice-président),\s*"
    r"nommé\s+(?P<role1>président),\s*et\s+(?P<name2>[^,.;]+),\s*"
    r"jusqu['’]ici\s+(?P<previous_role2>président),\s*nommé\s+"
    r"(?P<role2>vice-président),\s*continuent à signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_ASSET_TRANSFER_ASSETS_ONLY_FOREIGN_CURRENCY = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré des actifs pour\s+"
    r"(?P<currency>[A-Z]{3})\s+(?P<assets>[\d'.]+)\s+à\s+(?P<recipient>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+(?P<place>[^.]+)\.\s*"
    r"Contre-prestation:\s*(?P=currency)\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_SIMULTANEOUS_CAPITAL_CHANGE_NO_INCREASE_DATE = re.compile(
    r"^Bei der Kapitalherabsetzung vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+werden\s+"
    r"(?P<count>[\d']+)\s+(?P<share_kind>vinkulierte Namenaktien)\s+zu CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+vernichtet\.\s*Gleichzeitig werden bei der "
    r"ordentlichen Kapitalerhöhung\s+(?P=count)\s+voll liberierte\s+"
    r"(?P=share_kind)\s+zu CHF\s+(?P=nominal)\s+ausgegeben\.?$",
    re.I | re.UNICODE,
)
_DE_COMPOSITION_AGREEMENT_WITH_REMOVED_MORATORIUM = re.compile(
    r"^Mit Entscheid des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde der ordentliche "
    r"Nachlassvertrag mit\s+(?P<agreement_type>Dividendenvergleich)\s+bestätigt\.\s*"
    r"\[gestrichen:\s*Mit Entscheid vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+hat das\s+"
    r"(?P<previous_authority>.+?)\s+der Gesellschaft die definitive "
    r"Nachlassstundung für die Dauer von\s+(?P<duration_months>\d+)\s+Monaten,\s*"
    r"d\.h\.\s*bis und mit dem\s+(?P<until>\d{2}\.\d{2}\.\d{4}),\s*gewährt\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBER_WITHOUT_SIGNATURE = re.compile(
    r"^(?P<name>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[^,.;]+),\s*est membre du conseil d['’]administration;\s*"
    r"n['’]exerce pas la signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATION_DISSOLUTION_TWO_LIQUIDATORS = re.compile(
    r"^L['’]association est dissoute par décision de l['’]assemblée générale du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.\s*Liquidateurs:\s*"
    r"(?P<name1>[^,.;]+),\s*maintenant domicilié à\s+(?P<place1>[^,.;]+),\s*"
    r"et\s+(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"(?P<country2>[A-Z]{1,3}),\s*lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_TWO_CLASS_RECAPITALIZATION_CLAIM_OFFSET = re.compile(
    r"^Bei der Kapitalherabsetzung vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+werden\s+"
    r"(?P<count1>[\d']+)\s+Namenaktien zu CHF\s+(?P<nominal1>[\d'.]+)\s*"
    r"\((?P<class1>Stammaktien)\)\s+und\s+(?P<count2>[\d']+)\s+Namenaktien "
    r"zu CHF\s+(?P<nominal2>[\d'.]+)\s*\((?P<class2>Vorzugsaktien)\)\s+zur "
    r"teilweisen Beseitigung einer Unterbilanz vernichtet\.\s*Gleichzeitig wird "
    r"bei der ordentlichen Kapitalerhöhung vom\s+(?P=date)\s+eine Forderung von\s+"
    r"(?P<claim_currency>[A-Z]{3})\s+(?P<claim>[\d'.]+)\s+verrechnet,\s*wofür\s+"
    r"(?P=count1)\s+voll liberierte Namenaktien zu CHF\s+(?P=nominal1)\s*"
    r"\((?P=class1)\)\s+und\s+(?P=count2)\s+Namenaktien zu CHF\s+"
    r"(?P=nominal2)\s*\((?P=class2)\)\s+ausgegeben werden\.?$",
    re.I | re.UNICODE,
)
_DE_MERGER_NUMERIC_REGISTRY_ID_ALL_INTERESTS_HELD = re.compile(
    r"^Fusion:\s*Übernahme der Aktiven und Passiven der\s+[\"“]"
    r"(?P<absorbed_name>.+?)[\"”]\s*\((?P<registry_id>\d{3}\.\d{3}\.\d{3})\),\s*"
    r"in\s+(?P<place>[^,.;]+),\s*gemäss Fusionsvertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Bilanz per\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\.\s*Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+gehen auf die übernehmende Gesellschaft über\.\s*"
    r"Da die übernehmende Gesellschaft sämtliche Stammanteile der übertragenden "
    r"Gesellschaft hält,\s*findet weder eine Kapitalerhöhung noch eine "
    r"Aktienzuteilung statt\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_BOARD_MEMBERS_REMOVED = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?P<name2>[^,.;]+)\s+ne sont plus membres du "
    r"conseil;\s*leurs pouvoirs sont radiés\.?$",
    re.I | re.UNICODE,
)
_FR_CORPORATE_ASSOCIATE_RENAMED_AND_RELOCATED = re.compile(
    r"^L['’]associée\s+(?P<previous_name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*qui a modifié sa raison de "
    r"commerce en\s+(?P<name>.+?)\s*\((?P=uid)\),\s*est désormais à\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


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


def extract_parser151_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 151."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_FOUNDATION_BOARD_ROLE_CHANGES_AND_NEW_MEMBERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.foundation_board_role_changes_and_new_members.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role=f"{match.group('role1')} du conseil de fondation",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "role_changed",
                    "previous_role": match.group("previous_role1"),
                    "continues_signing": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                role="membre du conseil de fondation",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "presidency_ended",
                    "previous_role": match.group("previous_role2"),
                    "continues_signing": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name3"),
                place=match.group("place3"), role="président du conseil de fondation",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed_president",
                    "origin": match.group("origin3").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name4"),
                place=match.group("place4"), role="membre du conseil de fondation",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed",
                    "origin": match.group("origin4").strip(),
                    "country": match.group("country4").upper(),
                },
            ),
        ])

    match = _DE_BRANCH_REGISTERED_WITH_REFERENCE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_registered_with_reference.v1",
            {
                "action": "registered", "place": match.group("place").strip(),
                "branch_uid": match.group("uid"),
                "registration_date": _iso_date(match.group("registration_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        ))

    match = _DE_FULL_ADDRESS_AND_ADDITIONAL_ADDRESSES.search(leftover)
    if match:
        raw_addresses = [match.group("full_address").strip()]
        raw_addresses.extend(
            item.strip() for item in match.group("additional_addresses").split(";")
        )
        parsed_addresses = [_DE_ADDRESS.fullmatch(item) for item in raw_addresses]
        if len(raw_addresses) >= 3 and all(parsed_addresses):
            consume(match)
            rule_id = "de.text.full_address_and_additional_addresses.v1"
            for index, (raw_address, address) in enumerate(
                zip(raw_addresses, parsed_addresses)
            ):
                assert address is not None
                events.append(_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "address_changed", rule_id,
                    {
                        "kind": "registered_address" if index == 0 else "additional_address",
                        "action": "completed" if index == 0 else "added",
                        "address": raw_address,
                        "street": address.group("street").strip(),
                        "postal_code": address.group("postal_code"),
                        "locality": address.group("locality").strip(),
                        "address_canton": address.group("canton"),
                    },
                ))

    match = _FR_AUDITOR_NAME_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.auditor_name_changed.v1",
            match.group("name"), uid=match.group("uid"), role="organe de révision",
            extra={
                "action": "name_changed",
                "previous_name": match.group("previous_name").strip(),
            },
        ))

    match = _DE_OWNER_BANKRUPTCY_APPEAL_ENTRY_REMOVED_BY_ORDER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.owner_bankruptcy_appeal_entry_removed_by_order.v1",
            {
                "kind": "bankruptcy", "scope": "owner",
                "action": "suspended_on_appeal",
                "decision_date": _iso_date(match.group("decision_date")),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "effective_date": _iso_date(match.group("effective_date")),
                "effective_time": match.group("effective_time").replace(".", ":"),
                "authority": match.group("authority").strip(),
                "court": match.group("court").strip(),
                "previous_court": match.group("previous_court").strip(),
                "previous_decision_date": _iso_date(match.group("previous_date")),
                "bankruptcy_entry_removed": True,
            },
        ))

    match = _FR_ASSOCIATE_APPOINTED_MANAGER_PRESIDENT_INDIVIDUAL.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_appointed_manager_president_individual.v1",
            match.group("name"), role="associée-gérante présidente",
            signing="Einzelunterschrift",
            extra={"action": "appointed_manager_and_president", "signing_changed": True},
        ))

    match = _FR_BOARD_PRESIDENCY_SWAPPED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.board_presidency_swapped.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role=match.group(f"role{index}"),
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "role_changed",
                    "previous_role": match.group(f"previous_role{index}"),
                    "continues_signing": True,
                },
            ))

    match = _FR_ASSET_TRANSFER_ASSETS_ONLY_FOREIGN_CURRENCY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.asset_transfer_assets_only_foreign_currency.v1",
            {
                "date": _iso_date(match.group("date")),
                "assets": match.group("assets"), "liabilities": None,
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration": match.group("consideration"),
                "currency": match.group("currency").upper(),
            },
        ))

    match = _DE_SIMULTANEOUS_CAPITAL_CHANGE_NO_INCREASE_DATE.search(leftover)
    if match:
        consume(match)
        count = _count(match.group("count"))
        common = {
            "count": count, "share_kind": match.group("share_kind"),
            "nominal": match.group("nominal"), "currency": "CHF",
        }
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.simultaneous_capital_change_no_increase_date.v1",
            {
                "kind": "simultaneous_reduction_and_increase",
                "date": _iso_date(match.group("date")),
                "reduction": {**common, "action": "cancelled"},
                "increase": {**common, "action": "issued", "fully_paid": True},
                "share_count_unchanged": True, "nominal_unchanged": True,
            },
        ))

    match = _DE_COMPOSITION_AGREEMENT_WITH_REMOVED_MORATORIUM.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.composition_agreement_confirmed_with_removed_moratorium.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id,
                {
                    "kind": "composition_agreement_confirmed",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "authority": match.group("authority").strip(),
                    "agreement_type": match.group("agreement_type"),
                    "ordinary": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id,
                {
                    "kind": "composition_moratorium_granted", "action": "removed",
                    "decision_date": _iso_date(match.group("previous_decision_date")),
                    "authority": match.group("previous_authority").strip(),
                    "duration_months": int(match.group("duration_months")),
                    "until": _iso_date(match.group("until")),
                },
            ),
        ])

    match = _FR_BOARD_MEMBER_WITHOUT_SIGNATURE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.board_member_without_signature.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil d'administration",
            extra={
                "action": "appointed", "origin": match.group("origin").strip(),
                "country": match.group("country").strip(), "without_signature": True,
            },
        ))

    match = _FR_ASSOCIATION_DISSOLUTION_TWO_LIQUIDATORS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.association_dissolution_two_liquidators.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id,
                {
                    "kind": "dissolution", "scope": "association",
                    "action": "dissolved", "date": _iso_date(match.group("date")),
                    "authority": "assemblée générale",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="liquidateur",
                signing="Einzelunterschrift",
                extra={"action": "appointed_liquidator", "domicile_changed": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="liquidateur",
                signing="Einzelunterschrift",
                extra={
                    "action": "appointed_liquidator",
                    "origin": match.group("origin2").strip(),
                    "country": match.group("country2").upper(),
                },
            ),
        ])

    match = _DE_TWO_CLASS_RECAPITALIZATION_CLAIM_OFFSET.search(leftover)
    if match:
        consume(match)
        classes = [
            {
                "kind": match.group(f"class{index}"),
                "count": _count(match.group(f"count{index}")),
                "nominal": match.group(f"nominal{index}"),
                "currency": "CHF",
            }
            for index in (1, 2)
        ]
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.two_class_recapitalization_claim_offset.v1",
            {
                "kind": "simultaneous_reduction_and_increase",
                "date": _iso_date(match.group("date")),
                "reduction": {
                    "action": "cancelled", "classes": classes,
                    "purpose": "partial_elimination_of_balance_sheet_deficit",
                },
                "increase": {
                    "action": "issued", "classes": classes,
                    "fully_paid": True,
                    "claim_offset": {
                        "currency": match.group("claim_currency").upper(),
                        "amount": match.group("claim"),
                    },
                },
            },
        ))

    match = _DE_MERGER_NUMERIC_REGISTRY_ID_ALL_INTERESTS_HELD.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "de.text.merger_numeric_registry_id_all_interests_held.v1",
            {
                "kind": "absorption",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("place").strip(),
                "absorbed_registry_id": match.group("registry_id"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "currency": "CHF", "liabilities_kind": "third_party_capital",
                "all_interests_held_by_acquirer": True,
                "capital_increase": False, "share_allocation": False,
                "transferred_interest_kind": "Stammanteile",
            },
        ))

    match = _FR_TWO_BOARD_MEMBERS_REMOVED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_board_members_removed.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group(f"name{index}"),
                role="membre du conseil",
                extra={"action": "removed", "signing_revoked": True},
            ))

    match = _FR_CORPORATE_ASSOCIATE_RENAMED_AND_RELOCATED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.corporate_associate_renamed_and_relocated.v1",
            match.group("name"), place=match.group("place"), uid=match.group("uid"),
            role="associée",
            extra={
                "action": "name_and_domicile_changed",
                "previous_name": match.group("previous_name").strip(),
            },
        ))

    return events, re.sub(r"\s+", " ", leftover).strip(" .,;")
