from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_ERRONEOUS_OFFICIAL_DELETION_REINSTATED = re.compile(
    r"^\[biffé:\s*Aucune opposition n['’]ayant été formée,\s*cette raison "
    r"sociale est radiée d['’]office,\s*conformément à l['’]art\.\s*"
    r"(?P<article>159 al\.\s*5 ORC)\.\]\.?\s*La société ayant été radiée "
    r"par erreur,\s*elle est réinscrite comme précédemment\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGER_PRESIDENT_INDIVIDUAL_SIGNING = re.compile(
    r"^(?:(?P<previous_name>[^,.;]+?)\s+qui se prénomme désormais\s+"
    r"(?P<given_names>[^,.;]+),\s*est maintenant à\s+"
    r"(?P<place>[^,.;]+)\.\s*)?"
    r"Signature individuelle est conférée à l['’]associé\s+"
    r"(?P<name>[^,.;]+),\s*(?P<role>gérant président)\.?$",
    re.I | re.UNICODE,
)
_FR_OTHER_ADDRESS_CORRECTED_WITHOUT_NOTICE = re.compile(
    r"^L['’]inscription\s+(?:N°|n°|no)?\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée comme suit\s*:\s*"
    r"l['’]autre adresse est\s+[\"“](?P<address>"
    r"(?P<post_office_box>Case postale\s+\d+),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<place>[^\"”]+))[\"”]\s*"
    r"\(et non\s+(?P<previous_place>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_COLLECTIVE_SIGNING_TYPO = re.compile(
    r"^Siganture collective à deux est conférée à\s+(?P<name1>.+?),\s*"
    r"et\s+(?P<name2>.+?),\s*toutes deux de\s+(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*(?P<role>gérantes)\.?$",
    re.I | re.UNICODE,
)
_IT_CORRECT_PERSON_WITHOUT_SHARES = re.compile(
    r"^Nome corretto:\s*(?P<surname>[^,.;]+),\s*(?P<given_names>[^,.;]+),\s*"
    r"da\s+(?P<origin>[^,.;]+),\s*in\s+(?P<place>[^,.;]+),\s*"
    r"(?P<role>[^,.;]+),\s*con firma\s+(?P<signing>individuale)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_PRESIDENT_INDIVIDUAL_SIGNING_TYPO = re.compile(
    r"^L['’](?P<role>administrateur président)\s+(?P<name>[^,.;]+)\s+"
    r"signe désormais\s+(?P<signing>indiviuellement)\.?$",
    re.I | re.UNICODE,
)
_FR_SHAREHOLDER_COMMUNICATION_RECIPIENT_CORRECTED = re.compile(
    r"^Rectification de l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\):\s*Communication aux\s+"
    r"(?P<recipients>actionnaires)\s*\(et non pas\s+"
    r"(?P<previous_recipients>associés)\):\s*(?P<method>FOSC)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_REGISTERED_SHARE_CLASSES_ORDER_CORRECTED = re.compile(
    r"^Nouvelles actions:\s*(?P<count1>[\d']+)\s+actions\s+"
    r"(?P<kind1>nominatives) de CHF\s+(?P<nominal1>[\d'.]+)\s*"
    r"\((?P<rights1>privilégiées quant au droit de vote)\)\s+et\s+"
    r"(?P<count2>[\d']+)\s+actions\s+(?P<kind2>nominatives) de CHF\s+"
    r"(?P<nominal2>[\d'.]+)\s*\[non:\s*(?P<previous_count1>[\d']+)\s+"
    r"actions\s+(?P<previous_kind1>nominatives) de CHF\s+"
    r"(?P<previous_nominal1>[\d'.]+)\s+et\s+"
    r"(?P<previous_count2>[\d']+)\s+actions\s+"
    r"(?P<previous_kind2>nominatives) de CHF\s+"
    r"(?P<previous_nominal2>[\d'.]+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_NAME_CORRECTED_NOTICE_REFERENCE = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(publication FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+page\s+"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens qu['’]un "
    r"administrateur(?:\s+avec signature\s+(?P<signing>individuelle))?\s+"
    r"se nomme\s+(?P<name>[^()]+?)\s*\(et non\s+"
    r"(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_COMMON_SHAREHOLDER_NO_CAPITAL_INCREASE = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di\s+(?P<absorbed_name>.+?),\s*"
    r"in\s+(?P<absorbed_place>[^()]+?)\s*\(\s*"
    r"(?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\s*\),\s*"
    r"secondo il contratto di fusione del\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+e bilancio al\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta attivi per CHF\s+"
    r"(?P<assets>[\d'.]+)\s+e passivi verso terzi per CHF\s+"
    r"(?P<liabilities>[\d'.]+)\.\s*La totalità del capitale azionario delle "
    r"due società è detenuta dallo stesso azionista,\s*la fusione avviene dunque "
    r"senza aumento di capitale e senza attribuzione di azioni\.?$",
    re.I | re.UNICODE,
)
_FR_SINGLE_SHARE_TRANSFER_NEW_UNSIGNED_ASSOCIATE = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred_word>une)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé sans signature,\s*titulaire d['’]"
    r"(?P<buyer_count>[\d']+)\s+part de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"(?P<seller_again>[^,.;]+)\s+reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ASSOCIATES_APPOINTED_MANAGERS = re.compile(
    r"^L['’]associé\s+(?P<name1>[^,.;]+)\s+est désormais\s+"
    r"(?P<role1>gérant et président)(?:\s+avec signature\s+"
    r"(?P<signing1>collective à deux))?\.\s*L['’]associé\s+"
    r"(?P<name2>[^,.;]+),\s*maintenant domicilié à\s+"
    r"(?P<place2>[^,.;]+),\s*(?P<country2>[A-Z]),\s*est désormais\s+"
    r"(?P<role2>gérant) avec signature\s+(?P<signing2>collective à deux)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_DISSOLUTION_FOUR_LIQUIDATORS = re.compile(
    r"^Selon décision de l['’](?P<authority>Autorité cantonale de surveillance "
    r"des fondations et des institutions de prévoyance)\s+du\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*la fondation est dissoute\.\s*"
    r"Liquidateurs:\s*les membres du conseil\s+(?P<name1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*(?P<name3>[^,.;]+)\s+et\s+"
    r"(?P<name4>[^,.;]+),\s*lesquels continuent à signer "
    r"collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_NEW_FOUNDATION_MEMBERS_SHARED_PLACE = re.compile(
    r"^Nouveaux membres du conseil de fondation(?:\s+avec signature\s+"
    r"(?P<signing>collective à deux))?\s*:\s*"
    r"(?P<name1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*et\s+"
    r"(?P<name3>[^,.;]+),\s*de\s+(?P<origin3>[^,.;]+),\s*"
    r"les trois à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_BOARD_MEMBERS_WITHOUT_SIGNATURE_ORIGINS = re.compile(
    r"^(?P<name1>[^,.;]+),\s*d['’](?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,.;]+),\s*et\s+(?P<name2>[^,.;]+),\s*"
    r"d['’](?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"sont membres du conseil sans signature\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_CLOSURE_DATE_CORRECTION_RESIDUE = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que\s*"
    r"\(et non le\s+(?P<previous_date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+"
    r"\d{4}),\s*celle-ci correspondant à la date de suspension de la "
    r"liquidation\)\.?$",
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
    day, month, year = raw.casefold().replace("1er", "1", 1).split()
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
        role=role.strip() if role else None,
        signing=signing,
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser253_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 253."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_ERRONEOUS_OFFICIAL_DELETION_REINSTATED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.erroneous_official_deletion_reinstated.v1", {
                "kind": "registration_reinstated", "action": "reinstated",
                "reason": "erroneous_deletion",
                "previous_deletion_reason": "no_opposition_after_official_deletion",
                "previous_deletion_legal_basis": f"art. {match.group('article')}",
            },
        )], ""

    match = _FR_ASSOCIATE_MANAGER_PRESIDENT_INDIVIDUAL_SIGNING.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_manager_president_individual_signing.v1",
            match.group("name"), place=match.group("place"), role=match.group("role"),
            signing="Einzelunterschrift", extra={
                "action": "signing_granted", "associate": True,
                "previous_name": (
                    match.group("previous_name").strip()
                    if match.group("previous_name") else None
                ),
            },
        )], ""

    match = _FR_OTHER_ADDRESS_CORRECTED_WITHOUT_NOTICE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.other_address_corrected_without_notice.v1", {
                "kind": "other_address", "action": "corrected",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "address": match.group("address").strip(),
                "post_office_box": match.group("post_office_box").strip(),
                "postal_code": match.group("postal_code"),
                "place": match.group("place").strip(),
                "previous_place": match.group("previous_place").strip(),
            },
        )], ""

    match = _FR_TWO_MANAGERS_COLLECTIVE_SIGNING_TYPO.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_managers_collective_signing_typo.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group("place"), role="gérante",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_and_signing_granted",
                    "origin": match.group("origin").strip(),
                    "source_typo": "Siganture",
                },
            )
            for index in (1, 2)
        ], ""

    match = _IT_CORRECT_PERSON_WITHOUT_SHARES.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "it.persons.correct_person_without_shares.v1",
            f"{match.group('surname').strip()}, {match.group('given_names').strip()}",
            place=match.group("place"), role=match.group("role"),
            signing="Einzelunterschrift", extra={
                "action": "details_corrected",
                "origin": match.group("origin").strip(),
            },
        )], ""

    match = _FR_ADMINISTRATOR_PRESIDENT_INDIVIDUAL_SIGNING_TYPO.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed",
            "fr.persons.administrator_president_individual_signing_typo.v1",
            match.group("name"), role=match.group("role"),
            signing="Einzelunterschrift", extra={
                "action": "signing_changed", "source_typo": match.group("signing"),
            },
        )], ""

    match = _FR_SHAREHOLDER_COMMUNICATION_RECIPIENT_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed",
            "fr.text.shareholder_communication_recipient_corrected.v1", {
                "kind": "communications", "action": "recipient_corrected",
                "recipients": "shareholders", "previous_recipients": "associates",
                "method": match.group("method").upper(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        )], ""

    match = _FR_TWO_REGISTERED_SHARE_CLASSES_ORDER_CORRECTED.fullmatch(leftover)
    if match:
        current = [
            (_count(match.group("count1")), match.group("nominal1")),
            (_count(match.group("count2")), match.group("nominal2")),
        ]
        previous = [
            (_count(match.group("previous_count1")), match.group("previous_nominal1")),
            (_count(match.group("previous_count2")), match.group("previous_nominal2")),
        ]
        if current == list(reversed(previous)):
            return [_event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.two_registered_share_classes_order_corrected.v1", {
                    "kind": "share_structure", "action": "share_class_order_corrected",
                    "currency": "CHF",
                    "share_classes": [
                        {
                            "count": current[0][0], "nominal": current[0][1],
                            "share_kind": "actions nominatives",
                            "voting_privileged": True,
                        },
                        {
                            "count": current[1][0], "nominal": current[1][1],
                            "share_kind": "actions nominatives",
                            "voting_privileged": False,
                        },
                    ],
                    "previous_published_order": [
                        {"count": count, "nominal": nominal}
                        for count, nominal in previous
                    ],
                },
            )], ""

    match = _FR_ADMINISTRATOR_NAME_CORRECTED_NOTICE_REFERENCE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_name_corrected_notice_reference.v1",
            match.group("name"), role="administrateur",
            signing="Einzelunterschrift" if match.group("signing") else None,
            extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _IT_MERGER_COMMON_SHAREHOLDER_NO_CAPITAL_INCREASE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "it.text.merger_common_shareholder_no_capital_increase.v2", {
                "kind": "merger",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "currency": "CHF", "same_shareholder": True,
                "capital_increase": False, "share_allocation": False,
            },
        )], ""

    match = _FR_SINGLE_SHARE_TRANSFER_NEW_UNSIGNED_ASSOCIATE.fullmatch(leftover)
    if match:
        transferred = 1
        before = _count(match.group("before"))
        buyer_count = _count(match.group("buyer_count"))
        remaining = _count(match.group("remaining"))
        same_seller = (
            match.group("seller").strip().casefold()
            == match.group("seller_again").strip().casefold()
        )
        same_nominal = len({
            match.group("nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }) == 1
        if (
            same_seller and same_nominal and before - transferred == remaining
            and transferred == buyer_count
        ):
            rule_id = "fr.persons.single_share_transfer_new_unsigned_associate.v2"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            common = {"currency": "CHF", "share_nominal": match.group("nominal")}
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé", extra={
                        **common, "action": "shares_transferred", "counterparty": buyer,
                        "shares_before": before, "shares_transferred": transferred,
                        "shares_count": remaining,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé", extra={
                        **common, "action": "appointed_and_shares_received",
                        "origin": match.group("origin").strip(), "counterparty": seller,
                        "shares_received": transferred, "shares_count": buyer_count,
                        "new_associate": True, "without_signature": True,
                    },
                ),
            ], ""

    match = _FR_TWO_ASSOCIATES_APPOINTED_MANAGERS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_associates_appointed_managers.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role="associé-gérant président",
                signing=(
                    "Kollektivunterschrift zu zweien"
                    if match.group("signing1") else None
                ), extra={
                    "action": "appointed_manager_president",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="associé-gérant",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_manager_and_domicile_changed",
                    "country": match.group("country2").upper(),
                },
            ),
        ], ""

    match = _FR_FOUNDATION_DISSOLUTION_FOUR_LIQUIDATORS.fullmatch(leftover)
    if match:
        rule_id = "fr.text.foundation_dissolution_four_liquidators.v1"
        events = [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", rule_id, {
                "kind": "dissolution", "action": "dissolved",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
            },
        )]
        events.extend(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="membre du conseil, liquidateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_liquidator",
                    "previous_role": "membre du conseil",
                    "signing_continues": True,
                },
            )
            for index in range(1, 5)
        )
        return events, ""

    match = _FR_THREE_NEW_FOUNDATION_MEMBERS_SHARED_PLACE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.three_new_foundation_members_shared_place.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group("place"), role="membre du conseil de fondation",
                signing=(
                    "Kollektivunterschrift zu zweien"
                    if match.group("signing") else None
                ),
                extra={
                    "action": "appointed",
                    "origin": match.group(f"origin{index}").strip(),
                },
            )
            for index in range(1, 4)
        ], ""

    match = _FR_TWO_BOARD_MEMBERS_WITHOUT_SIGNATURE_ORIGINS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_board_members_without_signature_origins.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="membre du conseil",
                extra={
                    "action": "appointed",
                    "origin": match.group(f"origin{index}").strip(),
                    "without_signature": True,
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_BANKRUPTCY_CLOSURE_DATE_CORRECTION_RESIDUE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected",
            "fr.text.bankruptcy_closure_date_correction_residue.v1", {
                "kind": "bankruptcy_closure_date", "action": "date_corrected",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
                "corrected_date": _iso_date(match.group("entry_date")),
                "previous_published_date": _french_date(match.group("previous_date")),
                "previous_date_kind": "liquidation_suspension",
            },
        )], ""

    return [], leftover
