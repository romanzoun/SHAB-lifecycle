from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_FR_ADMINISTRATOR_PRESIDENT_APPOINTMENT_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;()]+?)\s+est nommé administrateur président\s*"
    r"\(et non\s+(?P<previous_name>[^,.;()]+?)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_ADMINISTRATOR_PRESIDENT_NAME_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le nouvel "
    r"administrateur président se nomme\s+(?P<name>[^,.;()]+?)\s*"
    r"\(et non\s+(?P<previous_name>[^,.;()]+?)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_PARTICIPATION_CAPITAL_PAID_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(publication FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+page\s+"
    r"(?P<notice_ref>[\d/]+)\)\s+es[rt] rectifiée en ce sens que le "
    r"capital-participation est libéré à concurrence de CHF\s+"
    r"(?P<paid>[\d'.]+)\s*\(et non de CHF\s+"
    r"(?P<previous_paid>[\d'.]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_ART_155_NUMBERED_CALLS_COMPLETED = re.compile(
    r"^Auf die durch das Handelsregisteramt gestützt auf\s+"
    r"(?P<legal_basis>Art\.\s*155 HRegV)\s+veranlassten und im Schweiz\.\s*"
    r"Handelsamtsblatt Nr\.\s*(?P<issue1>\d+),\s*(?P<issue2>\d+)\s+und\s+"
    r"(?P<issue3>\d+)\s+publizierten Rechnungsrufe haben sich keine "
    r"Gesellschafter/und Gläubiger/innen gemeldet\.\s*Das amtliche Verfahren "
    r"zur Löschung der Gesellschaft ist damit abgeschlossen\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_COMMITTEE_MEMBERS_WITH_CANTONS = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:de\s+|d['’])(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;()]+)\s*\((?P<canton1>[A-Z]{2})\),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*(?:de\s+|d['’])(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;()]+)\s*\((?P<canton2>[A-Z]{2})\),\s*"
    r"sont membres du comité avec signature individuelle\.?$",
    re.I | re.UNICODE,
)
_DE_DISSOLUTION_AND_ASSOCIATE_MANAGER_LIQUIDATOR = re.compile(
    r"^Die Gesellschaft wird gemäss Beschluss der Gesellschafterversammlung vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+aufgelöst\.\s*"
    r"Eingetragene Person geändert:\s*(?P<name>[^,.;]+),\s*"
    r"(?P<previous_role1>Gesellschafterin),\s*"
    r"(?P<previous_count>[\d']+)\s+Stammanteile zu CHF\s+"
    r"(?P<previous_nominal>[\d'.]+),\s*"
    r"(?P<previous_role2>Geschäftsführerin),\s*"
    r"(?P<previous_signing>Einzelunterschrift),\s*neu\s+"
    r"(?P<role1>Gesellschafterin),\s*(?P<count>[\d']+)\s+Stammanteile zu "
    r"CHF\s+(?P<nominal>[\d'.]+),\s*(?P<role2>Geschäftsführerin),\s*"
    r"(?P<role3>Liquidatorin),\s*(?P<signing>Einzelunterschrift)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_AND_TWO_MANAGERS = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:de\s+|d['’])(?P<origin>[^,.;()]+)\s*"
    r"\((?P<canton>[A-Z]{2})\),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé "
    r"pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*Gérants:\s*les associés\s+"
    r"(?P=seller),\s*président et\s+(?P=buyer),\s*tous deux avec signature "
    r"individuelle\.?$",
    re.I | re.UNICODE,
)
_DE_TWO_ASSET_TRANSFERS_EUR_CONSIDERATION = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<date1>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets1>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities1>[\d'.]+)\s+auf die\s+(?P<recipient1>.+?)\s*"
    r"\((?P<uid1>CHE-\d{3}\.\d{3}\.\d{3})\)\s+in\s+"
    r"(?P<place1>[^.]+)\.\s*Gegenleistung:\s*EUR\s+"
    r"(?P<consideration1>[\d'.]+)\.\s*Die Gesellschaft überträgt gemäss "
    r"Vertrag vom\s+(?P<date2>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets2>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities2>[\d'.]+)\s+auf die\s+(?P<recipient2>.+?)\s*"
    r"\((?P<uid2>CHE-\d{3}\.\d{3}\.\d{3})\)\s+in\s+"
    r"(?P<place2>[^.]+)\.\s*Gegenleistung:\s*EUR\s+"
    r"(?P<consideration2>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_AND_ADDED_BOARD_MEMBER = re.compile(
    r"^Gelöschte Person:\s*(?P<removed>[^,.;]+),\s*"
    r"(?P<removed_role>Verwaltungsratsmitglied),\s*"
    r"(?P<removed_signing>Einzelunterschrift)\.\s*Neu eingetragene Person:\s*"
    r"(?P<added>[^,.;]+),\s*(?P<nationality>[^,.;]+),\s*in\s+"
    r"(?P<place>[^,.;]+),\s*(?P<role1>Verwaltungsratsmitglied),\s*"
    r"(?P<role2>Vizepräsident),\s*(?P<signing>Einzelunterschrift)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_BOARD_REPLACEMENT_NO_SIGNATURE = re.compile(
    r"^(?P<removed>.+?)\s+ne sont plus membres du conseil de fondation\.\s*"
    r"(?P<name1>[^,.;]+),\s*de et à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*(?:de\s+|d['’])(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*et\s+(?P<name3>[^,.;]+),\s*"
    r"(?:de\s+|d['’])(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+),\s*"
    r"sont membres du conseil de fondation;\s*ils n['’]exercent pas la "
    r"signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_LIQUIDATORS_APPOINTED = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?P<name2>[^,.;]+),\s*et\s+"
    r"(?P<name3>[^,.;]+)\s+sont nommés liquidateurs avec signature collective "
    r"à deux\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_MANAGERS_TRANSFER_TO_NEW_MANAGER = re.compile(
    r"^Les associés-gérants\s+(?P<seller1>[^,.;]+),\s*"
    r"(?P<seller2>[^,.;]+)\s+et\s+(?P<seller3>[^,.;]+)\s+cèdent chacun\s+"
    r"(?P<transferred>[\d']+)\s+de leurs\s+(?P<before>[\d']+)\s+parts de "
    r"CHF\s+(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:de\s+|d['’])(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"nouvel associé avec\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*gérant avec signature collective à deux\.\s*"
    r"(?P=seller1),\s*"
    r"(?P=seller2)\s+et\s+(?P=seller3)\s+restent chacun titulaires de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_MERGER_SOLE_SHARE_HELD = re.compile(
    r"^Fusion:\s*Übernahme der Aktiven und der Passiven der\s+"
    r"(?P<absorbed_name>.+?),\s*(?P<absorbed_place>[^()]+?)\s*"
    r"\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+gemäss "
    r"Fusionsvertrag vom\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und "
    r"der Bilanz per\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4})\.\s*Aktiven "
    r"von CHF\s+(?P<assets>[\d'.]+)\s+und Fremdkapital von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+gehen auf die übernehmende Gesellschaft "
    r"über\.\s*Da die übernehmende Gesellschaft den einzigen Stammanteil der "
    r"übertragenden Gesellschaft hält,\s*findet weder eine Kapitalerhöhung "
    r"noch eine Stammanteilzuteilung statt\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_AND_TWO_INDIVIDUAL_MANAGERS = re.compile(
    r"^L['’]associé\s+(?P<seller>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts sociales "
    r"à\s+(?P<buyer_transfer>[^,.;]+),\s*(?:de\s+|d['’])"
    r"(?P<origin>[^,.;()]+)\s*\((?P<canton>[A-Z]{2})\),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé\.\s*Gérants:\s*"
    r"(?P=seller),\s*nommé président,\s*et\s+(?P<buyer_manager>[^,.;]+),\s*"
    r"lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_LLC_TO_CORPORATION_TRANSFORMATION_CORRECTED = re.compile(
    r"^Transformation:\s*capital social porté préalablement de CHF\s+"
    r"(?P<from_capital>[\d'.]+)\s+à CHF\s+(?P<to_capital>[\d'.]+)\s+par "
    r"apport en espèces contre remise en échange à l['’]associée\s+"
    r"(?P<contributor>.+?),\s*à\s+(?P<contributor_place>[^()]+?)\s*"
    r"\((?P<contributor_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+de\s+"
    r"(?P<parts_issued>[\d']+)\s+parts sociales de CHF\s+"
    r"(?P<part_nominal>[\d'.]+)\.\s*La société à responsabilité limitée est "
    r"transformée en société anonyme conformément au projet de transformation "
    r"du\s+(?P<plan_date>\d{2}\.\d{2}\.\d{4})\s+et bilan intermédiaire au\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\s+présentant des actifs de CHF\s+"
    r"(?P<assets>[\d'.]+)\s+et des passifs envers les tiers de CHF\s+"
    r"(?P<liabilities>[\d'.]+),\s*soit un actif net de CHF\s+"
    r"(?P<net_assets>[\d'.]+)\.\s*En tenant compte de l['’]augmentation de "
    r"capital préalable,\s*l['’]actionnaire reçoit\s+"
    r"(?P<class_a_count>[\d']+)\s+actions au porteur\s*\(type A\)\s+de CHF\s+"
    r"(?P<class_a_nominal>[\d'.]+)\s+de valeur nominale et\s+"
    r"(?P<class_b_count>[\d']+)\s+actions au porteur\s*\(type B\)\s+de CHF\s+"
    r"(?P<class_b_nominal>[\d'.]+)\s*\[non:\s*"
    r"(?P<previous>Transformation:\s*capital social porté préalablement .+?"
    r"et\s+(?P<previous_class_b_count>[\d']+)\s+actions au porteur\s*"
    r"\(type B\)\s+de CHF\s+(?P<previous_class_b_nominal>[\d'.]+))\]\.?$",
    re.I | re.UNICODE,
)
_FR_CONDITIONAL_PARTICIPATION_CAPITAL_INCREASE = re.compile(
    r"^Augmentation conditionnelle du capital-participation,\s*fondée sur la "
    r"décision relative à l['’]octroi de droits du\s+"
    r"(?P<rights_date>\d{2}\.\d{2}\.\d{4}),\s*porté de CHF\s+"
    r"(?P<from_capital>[\d'.]+)\s+à CHF\s+(?P<to_capital>[\d'.]+),\s*par "
    r"l['’]émission de\s+(?P<issued_count>[\d']+)\s+bons de participation de "
    r"CHF\s+(?P<issued_nominal>[\d'.]+),\s*nominatifs,\s*liés selon statuts\.\s*"
    r"Capital-participation:\s*CHF\s+(?P<reported_capital>[\d'.]+),\s*"
    r"entièrement libéré,\s*divisé en\s+(?P<total_count>[\d']+)\s+bons de "
    r"participation de CHF\s+(?P<total_nominal>[\d'.]+),\s*nominatifs,\s*"
    r"liés selon statuts\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


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


def _correction_context(match: re.Match[str]) -> dict:
    return {
        "action": "publication_corrected",
        "entry": match.group("entry"),
        "entry_date": _iso_date(match.group("entry_date")),
        "notice_date": _iso_date(match.group("notice_date")),
        "notice_ref": match.group("notice_ref"),
    }


def extract_parser242_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 242."""
    del language  # Historical publications regularly contain another language.
    leftover = text.strip()

    for pattern, rule_id in (
        (
            _FR_ADMINISTRATOR_PRESIDENT_APPOINTMENT_CORRECTED,
            "fr.persons.administrator_president_appointment_corrected.v1",
        ),
        (
            _FR_NEW_ADMINISTRATOR_PRESIDENT_NAME_CORRECTED,
            "fr.persons.new_administrator_president_name_corrected.v1",
        ),
    ):
        match = pattern.fullmatch(leftover)
        if match:
            return [_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                role="administrateur président", extra={
                    **_correction_context(match),
                    "previous_name": match.group("previous_name").strip(),
                    "name_corrected": True,
                },
            )], ""

    match = _FR_PARTICIPATION_CAPITAL_PAID_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.participation_capital_paid_corrected.v1",
            {
                **_correction_context(match),
                "kind": "participation_capital_paid_amount",
                "paid": match.group("paid"),
                "previous_paid": match.group("previous_paid"),
                "currency": "CHF",
            },
        )], ""

    match = _DE_ART_155_NUMBERED_CALLS_COMPLETED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.art_155_numbered_calls_completed.v1",
            {
                "kind": "deletion_procedure_completed",
                "action": "completed",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "notice_issue_numbers": [
                    int(match.group("issue1")),
                    int(match.group("issue2")),
                    int(match.group("issue3")),
                ],
                "shareholders_or_creditors_responded": False,
            },
        )], ""

    match = _FR_TWO_COMMITTEE_MEMBERS_WITH_CANTONS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_committee_members_with_cantons.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="membre du comité",
                signing="Einzelunterschrift",
                extra={
                    "action": "appointed",
                    "origin": match.group(f"origin{index}").strip(),
                    "residence_canton": match.group(f"canton{index}"),
                },
            )
            for index in (1, 2)
        ], ""

    match = _DE_DISSOLUTION_AND_ASSOCIATE_MANAGER_LIQUIDATOR.fullmatch(leftover)
    if match:
        if (
            _count(match.group("previous_count")) != _count(match.group("count"))
            or _amount(match.group("previous_nominal")) != _amount(match.group("nominal"))
        ):
            return [], leftover
        rule_id = "de.text.dissolution_and_associate_manager_liquidator.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "dissolution", "action": "dissolved",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "decision_maker": "Gesellschafterversammlung",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                role="Gesellschafterin; Geschäftsführerin; Liquidatorin",
                signing=match.group("signing"), extra={
                    "action": "appointed_liquidator",
                    "previous_role": "Gesellschafterin; Geschäftsführerin",
                    "shares_count": _count(match.group("count")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
        ], ""

    match = _FR_MANAGER_TRANSFER_AND_TWO_MANAGERS.fullmatch(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        if (
            transferred != buyer_count
            or _amount(match.group("nominal")) != _amount(match.group("buyer_nominal"))
        ):
            return [], leftover
        rule_id = "fr.persons.manager_transfer_and_two_managers.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller"),
                role="associé-gérant; président", signing="Einzelunterschrift", extra={
                    "action": "shares_transferred_and_appointed_president",
                    "counterparty": match.group("buyer").strip(),
                    "shares_transferred": transferred,
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"),
                place=match.group("place"), role="associé-gérant",
                signing="Einzelunterschrift", extra={
                    "action": "appointed_and_shares_received",
                    "counterparty": match.group("seller").strip(),
                    "origin": match.group("origin").strip(),
                    "origin_canton": match.group("canton"),
                    "shares_received": transferred, "shares_count": buyer_count,
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ], ""

    match = _DE_TWO_ASSET_TRANSFERS_EUR_CONSIDERATION.fullmatch(leftover)
    if match:
        rule_id = "de.text.two_asset_transfers_eur_consideration.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", rule_id, {
                    "agreement_date": _iso_date(match.group(f"date{index}")),
                    "assets": match.group(f"assets{index}"),
                    "liabilities": match.group(f"liabilities{index}"),
                    "liabilities_kind": "third_party_capital",
                    "currency": "CHF",
                    "recipient": match.group(f"recipient{index}").strip(),
                    "recipient_uid": match.group(f"uid{index}"),
                    "recipient_place": match.group(f"place{index}").strip(),
                    "consideration": match.group(f"consideration{index}"),
                    "consideration_currency": "EUR",
                },
            )
            for index in (1, 2)
        ], ""

    match = _DE_REMOVED_AND_ADDED_BOARD_MEMBER.fullmatch(leftover)
    if match:
        rule_id = "de.persons.removed_and_added_board_member.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group("removed"),
                role=match.group("removed_role"), extra={
                    "action": "removed",
                    "previous_signing": match.group("removed_signing"),
                    "signing_revoked": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("added"),
                place=match.group("place"),
                role=f"{match.group('role1')}; {match.group('role2')}",
                signing=match.group("signing"), extra={
                    "action": "appointed",
                    "nationality": match.group("nationality").strip(),
                },
            ),
        ], ""

    match = _FR_FOUNDATION_BOARD_REPLACEMENT_NO_SIGNATURE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.foundation_board_replacement_no_signature.v1"
        removed_names = [
            name.strip()
            for name in re.split(r",\s*|\s+et0?\s+", match.group("removed"))
            if name.strip()
        ]
        removed = [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, name,
                role="membre du conseil de fondation", extra={"action": "removed"},
            )
            for name in removed_names
        ]
        added = []
        for index in (1, 2, 3):
            origin = match.group("place1") if index == 1 else match.group(f"origin{index}")
            added.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role="membre du conseil de fondation", extra={
                    "action": "appointed", "origin": origin.strip(),
                    "without_signature": True,
                },
            ))
        return removed + added, ""

    match = _FR_THREE_LIQUIDATORS_APPOINTED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.three_liquidators_appointed.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="liquidateur", signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed_liquidator"},
            )
            for index in (1, 2, 3)
        ], ""

    match = _FR_THREE_MANAGERS_TRANSFER_TO_NEW_MANAGER.fullmatch(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        before = _count(match.group("before"))
        remaining = _count(match.group("remaining"))
        buyer_count = _count(match.group("buyer_count"))
        amounts = {
            _amount(match.group(group))
            for group in ("nominal", "buyer_nominal", "remaining_nominal")
        }
        if before - transferred != remaining or 3 * transferred != buyer_count or len(amounts) != 1:
            return [], leftover
        rule_id = "fr.persons.three_managers_transfer_to_new_manager.v1"
        sellers = [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"seller{index}"),
                role="associé-gérant", extra={
                    "action": "shares_transferred",
                    "counterparty": match.group("buyer").strip(),
                    "previous_shares_count": before,
                    "shares_transferred": transferred, "shares_count": remaining,
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            )
            for index in (1, 2, 3)
        ]
        buyer = _person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("buyer"),
            place=match.group("place"), role="associé-gérant",
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "appointed_and_shares_received",
                "origin": match.group("origin").strip(),
                "shares_received": buyer_count, "shares_count": buyer_count,
                "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
            },
        )
        return sellers + [buyer], ""

    match = _DE_MERGER_SOLE_SHARE_HELD.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "de.text.merger_sole_share_held.v1", {
                "kind": "merger",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"), "currency": "CHF",
                "acquirer_owned_sole_share": True,
                "capital_increase": False, "share_allocation": False,
            },
        )], ""

    match = _FR_ASSOCIATE_TRANSFER_AND_TWO_INDIVIDUAL_MANAGERS.fullmatch(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        before = _count(match.group("before"))
        if transferred > before:
            return [], leftover
        rule_id = "fr.persons.associate_transfer_and_two_individual_managers.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller"),
                role="associé-gérant; président", signing="Einzelunterschrift",
                extra={
                    "action": "shares_transferred_and_appointed_president",
                    "counterparty": match.group("buyer_transfer").strip(),
                    "previous_shares_count": before,
                    "shares_transferred": transferred,
                    "shares_count": before - transferred,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer_manager"),
                place=match.group("place"), role="associé-gérant",
                signing="Einzelunterschrift", extra={
                    "action": "appointed_and_shares_received",
                    "name_in_transfer": match.group("buyer_transfer").strip(),
                    "origin": match.group("origin").strip(),
                    "origin_canton": match.group("canton"),
                    "shares_received": transferred, "shares_count": transferred,
                },
            ),
        ], ""

    match = _FR_LLC_TO_CORPORATION_TRANSFORMATION_CORRECTED.fullmatch(leftover)
    if match:
        from_capital = _amount(match.group("from_capital"))
        to_capital = _amount(match.group("to_capital"))
        part_value = _count(match.group("parts_issued")) * _amount(match.group("part_nominal"))
        net_assets = _amount(match.group("assets")) - _amount(match.group("liabilities"))
        issued_capital = (
            _count(match.group("class_a_count")) * _amount(match.group("class_a_nominal"))
            + _count(match.group("class_b_count")) * _amount(match.group("class_b_nominal"))
        )
        valid = (
            to_capital - from_capital == part_value
            and net_assets == _amount(match.group("net_assets"))
            and issued_capital == to_capital
            and _count(match.group("previous_class_b_count")) == _count(match.group("class_b_count"))
        )
        if not valid:
            return [], leftover
        rule_id = "fr.text.llc_to_corporation_transformation_corrected.v1"
        common = {
            "action": "corrected",
            "previous_text": match.group("previous").strip(),
            "previous_class_b_nominal": match.group("previous_class_b_nominal"),
        }
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    **common, "kind": "capital_increase_before_transformation",
                    "from_capital": match.group("from_capital"),
                    "to_capital": match.group("to_capital"), "currency": "CHF",
                    "contribution_kind": "cash",
                    "contributor": match.group("contributor").strip(),
                    "contributor_place": match.group("contributor_place").strip(),
                    "contributor_uid": match.group("contributor_uid"),
                    "social_parts_issued": _count(match.group("parts_issued")),
                    "social_part_nominal": match.group("part_nominal"),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "legal_form_changed", rule_id, {
                    **common, "action": "transformed_and_corrected",
                    "from_legal_form": "société à responsabilité limitée",
                    "to_legal_form": "société anonyme",
                    "transformation_plan_date": _iso_date(match.group("plan_date")),
                    "balance_sheet_date": _iso_date(match.group("balance_date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "net_assets": match.group("net_assets"), "currency": "CHF",
                    "share_classes": [
                        {
                            "class": "A", "kind": "actions au porteur",
                            "count": _count(match.group("class_a_count")),
                            "nominal": match.group("class_a_nominal"),
                        },
                        {
                            "class": "B", "kind": "actions au porteur",
                            "count": _count(match.group("class_b_count")),
                            "nominal": match.group("class_b_nominal"),
                        },
                    ],
                },
            ),
        ], ""

    match = _FR_CONDITIONAL_PARTICIPATION_CAPITAL_INCREASE.fullmatch(leftover)
    if match:
        from_capital = _amount(match.group("from_capital"))
        to_capital = _amount(match.group("to_capital"))
        issued_value = _count(match.group("issued_count")) * _amount(match.group("issued_nominal"))
        reported_capital = _amount(match.group("reported_capital"))
        total_value = _count(match.group("total_count")) * _amount(match.group("total_nominal"))
        if (
            to_capital - from_capital != issued_value
            or to_capital != reported_capital
            or reported_capital != total_value
            or _amount(match.group("issued_nominal")) != _amount(match.group("total_nominal"))
        ):
            return [], leftover
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.conditional_participation_capital_increase.v1",
            {
                "kind": "conditional_participation_capital_increase",
                "action": "increased",
                "rights_decision_date": _iso_date(match.group("rights_date")),
                "from_capital": match.group("from_capital"),
                "to_capital": match.group("to_capital"), "currency": "CHF",
                "issued_count": _count(match.group("issued_count")),
                "issued_nominal": match.group("issued_nominal"),
                "total_count": _count(match.group("total_count")),
                "share_kind": "bons de participation nominatifs",
                "fully_paid": True, "transfer_restricted_by_statutes": True,
            },
        )], ""

    return [], leftover
