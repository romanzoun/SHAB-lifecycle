from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_TRANSFER_TO_EXISTING_MANAGER = re.compile(
    r"^L['’]associé\s+(?P<seller>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"l['’]associé-gérant\s+(?P<buyer>[^,.;]+),\s*ce dernier possède désormais\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_LLC_SET_OFF_CAPITAL_INCREASE_AND_TRANSFORMATION = re.compile(
    r"^Umwandlung:\s*Die Gesellschaft mit beschränkter Haftung hat das "
    r"Stammkapital vorgängig durch Verrechnung einer Forderung von CHF\s+"
    r"(?P<claim>[\d'.]+)\s+auf CHF\s+(?P<capital>[\d'.]+)\s+erhöht und wird "
    r"gemäss Umwandlungsplan vom\s+(?P<plan_date>\d{2}\.\d{2}\.\d{4})\s+und "
    r"Bilanz per\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4})\s+mit Aktiven von "
    r"CHF\s+(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+in eine Aktiengesellschaft umgewandelt\.\s*"
    r"Der einzige Gesellschafter erhält für seine bisherigen Stammanteile\s+"
    r"(?P<shares>[\d']+)\s+zu\s+(?P<paid_percentage>\d+)%\s+liberierte Aktien "
    r"zu CHF\s+(?P<share_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_APPEAL_SUSPENSIVE_EFFECT_WITH_HISTORY = re.compile(
    r"^Selon ordonnance du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>.+?)\s+a accordé l['’]effet suspensif au recours du "
    r"titulaire contre le jugement de faillite de première instance\.\s*"
    r"\[précédemment:\s*Par décision du\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<lower_authority>.+?)\s+a prononcé la faillite du titulaire de "
    r"l['’]entreprise individuelle avec effet au\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*à\s*"
    r"(?P<time>\d{1,2}[.:]\d{2})\s+heures?\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_TWO_BOARD_PERSON_CHANGES = re.compile(
    r"^Eingetragene Personen neu oder mutierend:\s*"
    r"(?P<surname1>[^,;]+),\s*(?P<given1>[^,;]+),\s*"
    r"(?P<nationality1>[^,;]+),\s*in\s+(?P<place1>[^,;]+),\s*"
    r"(?P<role1>[^,;]+),\s*mit\s+(?P<signing1>Einzelunterschrift)\s*"
    r"\[bisher:\s*(?P<previous_role1>[^,;]+),\s*mit\s+"
    r"(?P<previous_signing1>Einzelunterschrift)\];\s*"
    r"(?P<surname2>[^,;]+),\s*(?P<given2>[^,;]+),\s*"
    r"(?P<nationality2>[^,;]+),\s*in\s+(?P<place2>[^,;]+),\s*"
    r"(?P<role2>[^,;]+),\s*(?P<without_signing>ohne Zeichnungsberechtigung)\.?$",
    re.I | re.UNICODE,
)
_FR_TRANSFER_TO_NEW_MANAGER_PRESIDENT = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvelle "
    r"associée-gérante présidente avec signature individuelle,\s*titulaire de\s+"
    r"(?P<buyer_count>[\d']+)\s+"
    r"parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*(?P=seller)\s+reste "
    r"titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUR_FOUNDATION_MEMBERS_MIXED_SIGNING = re.compile(
    r"^Nouveaux membres du conseil de fondation:\s*"
    r"(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"tous deux avec signature collective à deux,\s*"
    r"(?P<name3>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;()]+)\s*"
    r"\((?P<country3>[^)]+)\),\s*et\s+(?P<name4>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin4>[^,.;]+),\s*à\s+"
    r"(?P<place4>[^,.;()]+)\s*\((?P<country4>[^)]+)\),\s*"
    r"les deux sans signature\.?$",
    re.I | re.UNICODE,
)
_IT_TWO_BOARD_PERSON_CHANGES = re.compile(
    r"^Nuove persone iscritte o modifiche:\s*"
    r"(?P<surname1>[^,;]+),\s*(?P<given1>[^,;]+),\s*detto\s+"
    r"(?P<alias1>[^,;]+),\s*da\s+(?P<origin1>[^,;]+),\s*in\s+"
    r"(?P<place1>[^,;]+),\s*(?P<role1>[^,;]+),\s*con firma individuale\s*"
    r"\[finora:\s*(?P<previous_role1>[^,;]+),\s*con firma individuale\];\s*"
    r"(?P<surname2>[^,;]+),\s*(?P<given2>[^,;]+),\s*"
    r"(?P<nationality2>[^,;]+),\s*in\s+(?P<place2>[^,;()]+)\s*"
    r"\((?P<country2>[^)]+)\),\s*(?P<role2>[^,;]+),\s*"
    r"con firma individuale\.?$",
    re.I | re.UNICODE,
)
_FR_RESTRICTION_REMOVED_THEN_LIQUIDATOR = re.compile(
    r"^Les\s+(?P<count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*formant l['’]entier du capital-actions,\s*ne "
    r"sont plus restreintes quant à la transmissibilité selon l['’]"
    r"(?P<legal_basis>art\.\s*685a\s+al\.\s*3\s+CO)\.\s*"
    r"L['’]administratrice\s+(?P<name>[^,.;]+),\s*désormais à\s+"
    r"(?P<place>[^,.;]+),\s*est nommée liquidatrice avec signature "
    r"individuelle\.?$",
    re.I | re.UNICODE,
)
_FR_QUALIFIED_CONTRIBUTION_CLAUSE_REPEALED = re.compile(
    r"^Faits qualifiés:\s*\[Abrogation de la clause d['’]apport en nature et "
    r"de reprise de biens\]\s*\[biffé:\s*selon convention du\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+et bilan provisoire arrêté "
    r"au\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<details>sont apportés.+?)\s+Les actifs\s*\(.+?\)\s*s['’]élevant à "
    r"CHF\s+(?P<assets>[\d']+,\s*\d{2})\s+et les passifs.+?à CHF\s+"
    r"(?P<liabilities>[\d']+,\s*\d{2}),\s*l['’]actif net s['’]élève à CHF\s+"
    r"(?P<net_assets>[\d']+,\s*\d{2})\.\s*L['’]apport est accepté pour ce "
    r"prix et payé,\s*à due concurrence,\s*par remise au pair aux apporteurs "
    r"des\s+(?P<shares>[\d']+)\s+actions de CHF\s+"
    r"(?P<share_nominal>[\d'.-]+)\s+qui constituent le capital\]\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_TO_NEW_MANAGER = re.compile(
    r"^L['’]associé\s+(?P<seller>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts "
    r"sociales de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*(?P<country>[^,.;]+),\s*nouvel associé,\s*"
    r"lequel est en outre nommé gérant avec signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_PRESIDENT_TRANSFER_MALFORMED_SIGNING = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+),\s*qui est nommé président,\s*"
    r"cède\s+(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts "
    r"de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"gérant avec avec signature individuelle\.\s*(?P=seller)reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_INDIVIDUAL_PROCURATION_GRANTED = re.compile(
    r"^(?P<name>[^,.;]+)\s+engage désormais la société par sa procuration "
    r"individuelle\.?$",
    re.I | re.UNICODE,
)
_FR_TRANSFER_AND_TWO_MANAGERS = re.compile(
    r"^L['’]associé\s+(?P<seller>[^,.;]+)\s+détient\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+suite à "
    r"la cession de\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<transfer_nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé\.\s*Gérants:\s*les associés\s+"
    r"(?P=buyer),\s*nommé président,\s*et\s+(?P=seller),\s*tous deux avec "
    r"signature individuelle\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_AND_NEW_SIGNATORY = re.compile(
    r"^Ausgeschiedene Personen und erloschene Unterschriften:\s*"
    r"(?P<removed_surname>[^,;]+),\s*(?P<removed_given>[^,;]+),\s*von\s+"
    r"(?P<removed_origin>[^,;]+),\s*in\s+(?P<removed_place>[^,;]+),\s*mit\s+"
    r"(?P<removed_signing>Kollektivunterschrift zu zweien)\.\s*"
    r"Eingetragene Personen neu oder mutierend:\s*"
    r"(?P<new_surname>[^,;]+),\s*(?P<new_given>[^,;]+),\s*von\s+"
    r"(?P<new_origin>[^,;]+),\s*in\s+(?P<new_place>[^,;]+),\s*mit\s+"
    r"(?P<new_signing>Kollektivunterschrift zu zweien)\.?$",
    re.I | re.UNICODE,
)
_FR_MULTIPLE_COLLECTIVE_SIGNATORIES = re.compile(
    r"^(?!Les membres du comité\b)"
    r"(?P<names>[^,.;]+(?:,\s*[^,.;]+){4}\s+et\s+[^,.;]+),\s*"
    r"signent désormais collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_DE_EXTRAORDINARY_BANKRUPTCY_ADMINISTRATION_ADDRESS_FIRST = re.compile(
    r"^Als ausserordentliche Konkursverwaltung wird die\s+(?P<name>.+?),\s*"
    r"(?P<street>[^,]+),\s*(?P<postal_code>\d{4})\s+(?P<place>[^()]+?)\s*"
    r"\((?P<leader>.+?),\s*Rechtsanwalt,\s*als Mandatsleiter sowie\s*"
    r"(?P<deputy>.+?),\s*Rechtsanwalt,\s*als stellvertretender Mandatsleiter\) "
    r"eingesetzt\.\s*Die ausserordentliche Konkursverwaltung wird das "
    r"Konkursverfahren unter Mithilfe des\s+(?P<assisting_authority>[^.]+)\s+"
    r"durchführen\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", "").replace(".", ""))


def _amount(raw: str) -> str:
    return re.sub(r",\s*", ".", raw)


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


def _share_transfer_events(
    match: re.Match[str],
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
    rule_id: str,
    *,
    seller_role: str,
    buyer_role: str,
    buyer_signing: str | None = None,
) -> list[Event]:
    transferred = _count(match.group("transferred"))
    nominal = match.group("nominal")
    seller = match.group("seller").strip()
    buyer = match.group("buyer").strip()
    before = _count(match.group("before")) if "before" in match.groupdict() else None
    remaining = (
        _count(match.group("remaining"))
        if "remaining" in match.groupdict() and match.group("remaining")
        else before - transferred if before is not None else None
    )
    buyer_count = (
        _count(match.group("buyer_count"))
        if "buyer_count" in match.groupdict() and match.group("buyer_count")
        else transferred
    )
    common = {
        "currency": "CHF",
        "share_nominal": nominal,
        "shares_transferred": transferred,
    }
    seller_extra = {
        **common,
        "action": "shares_transferred",
        "counterparty": buyer,
        **({"shares_before": before} if before is not None else {}),
        **({"shares_count": remaining} if remaining is not None else {}),
    }
    buyer_extra = {
        **common,
        "action": "shares_received",
        "counterparty": seller,
        "shares_received": transferred,
        "shares_count": buyer_count,
    }
    if "origin" in match.groupdict() and match.group("origin"):
        buyer_extra["origin"] = match.group("origin").strip()
    if "country" in match.groupdict() and match.group("country"):
        buyer_extra["country"] = match.group("country").strip()
    return [
        _person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, seller, role=seller_role,
            extra=seller_extra,
        ),
        _person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, buyer,
            place=match.group("place") if "place" in match.groupdict() else None,
            role=buyer_role, signing=buyer_signing, extra=buyer_extra,
        ),
    ]


def extract_parser233_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 233."""
    del language  # Historical publications regularly contain another language.
    leftover = text.strip()

    match = _FR_TRANSFER_TO_EXISTING_MANAGER.fullmatch(leftover)
    if match and match.group("nominal") == match.group("buyer_nominal"):
        rule_id = "fr.persons.transfer_to_existing_manager.v1"
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {
            "currency": "CHF", "share_nominal": match.group("nominal"),
            "shares_transferred": transferred,
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé", extra={
                    **common, "action": "shares_transferred", "counterparty": buyer,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, role="associé-gérant", extra={
                    **common, "action": "shares_received", "counterparty": seller,
                    "shares_received": transferred, "shares_count": buyer_count,
                },
            ),
        ], ""

    match = _DE_LLC_SET_OFF_CAPITAL_INCREASE_AND_TRANSFORMATION.fullmatch(leftover)
    if match:
        rule_id = "de.text.llc_setoff_capital_increase_and_transformation.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "share_capital", "action": "increased_by_set_off",
                    "claim_set_off": match.group("claim"),
                    "to": match.group("capital"), "currency": "CHF",
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "legal_form_changed", rule_id, {
                    "action": "transformed",
                    "from_legal_form": "Gesellschaft mit beschränkter Haftung",
                    "to_legal_form": "Aktiengesellschaft",
                    "transformation_plan_date": _iso_date(match.group("plan_date")),
                    "balance_sheet_date": _iso_date(match.group("balance_date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"), "currency": "CHF",
                    "shares_issued": _count(match.group("shares")),
                    "share_kind": "Aktien",
                    "share_nominal": match.group("share_nominal"),
                    "paid_percentage": int(match.group("paid_percentage")),
                    "shareholder_count": 1,
                },
            ),
        ], ""

    match = _FR_BANKRUPTCY_APPEAL_SUSPENSIVE_EFFECT_WITH_HISTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed",
            "fr.text.bankruptcy_appeal_suspensive_effect_with_history.v1", {
                "kind": "bankruptcy_suspended", "action": "suspensive_effect_granted",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "appeal_by": "sole_proprietor",
                "previous_bankruptcy_decision_date": _iso_date(
                    match.group("bankruptcy_date")
                ),
                "previous_bankruptcy_effective_at": (
                    f"{_iso_date(match.group('effective_date'))}T"
                    f"{match.group('time').replace('.', ':')}"
                ),
                "lower_authority": match.group("lower_authority").strip(),
            },
        )], ""

    match = _DE_TWO_BOARD_PERSON_CHANGES.fullmatch(leftover)
    if match:
        rule_id = "de.persons.two_board_person_changes_cross_language.v1"
        first_name = f"{match.group('surname1').strip()}, {match.group('given1').strip()}"
        second_name = f"{match.group('surname2').strip()}, {match.group('given2').strip()}"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, first_name, place=match.group("place1"),
                role=match.group("role1").strip(), signing="Einzelunterschrift",
                extra={
                    "action": "role_changed",
                    "nationality": match.group("nationality1").strip(),
                    "previous_role": match.group("previous_role1").strip(),
                    "previous_signing": "Einzelunterschrift",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, second_name, place=match.group("place2"),
                role=match.group("role2").strip(), extra={
                    "action": "appointed",
                    "nationality": match.group("nationality2").strip(),
                    "signing_authority": False,
                },
            ),
        ], ""

    match = _FR_TRANSFER_TO_NEW_MANAGER_PRESIDENT.fullmatch(leftover)
    if match:
        expected_remaining = _count(match.group("before")) - _count(match.group("transferred"))
        nominals = {
            match.group("nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }
        if (
            len(nominals) == 1
            and expected_remaining == _count(match.group("remaining"))
            and _count(match.group("transferred")) == _count(match.group("buyer_count"))
        ):
            events = _share_transfer_events(
                match, publication_id, published_at, org_uid, plz, canton,
                "fr.persons.transfer_to_new_manager_president.v1",
                seller_role="associé", buyer_role="associée-gérante présidente",
                buyer_signing="Einzelunterschrift",
            )
            events[1].payload["new_associate"] = True
            return events, ""

    match = _FR_FOUR_FOUNDATION_MEMBERS_MIXED_SIGNING.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.four_foundation_members_mixed_signing.v1"
        events = []
        for index in (1, 2, 3, 4):
            signed = index < 3
            extra = {
                "action": "appointed",
                "origin": match.group(f"origin{index}").strip(),
                "signing_authority": signed,
            }
            if index > 2:
                extra["country"] = match.group(f"country{index}").strip()
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role="membre du conseil de fondation",
                signing="Kollektivunterschrift zu zweien" if signed else None,
                extra=extra,
            ))
        return events, ""

    match = _IT_TWO_BOARD_PERSON_CHANGES.fullmatch(leftover)
    if match:
        rule_id = "it.persons.two_board_person_changes_cross_language.v1"
        first_name = f"{match.group('surname1').strip()}, {match.group('given1').strip()}"
        second_name = f"{match.group('surname2').strip()}, {match.group('given2').strip()}"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, first_name, place=match.group("place1"),
                role=match.group("role1").strip(), signing="Einzelunterschrift",
                extra={
                    "action": "role_changed", "alias": match.group("alias1").strip(),
                    "origin": match.group("origin1").strip(),
                    "previous_role": match.group("previous_role1").strip(),
                    "previous_signing": "Einzelunterschrift",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, second_name, place=match.group("place2"),
                role=match.group("role2").strip(), signing="Einzelunterschrift",
                extra={
                    "action": "appointed",
                    "nationality": match.group("nationality2").strip(),
                    "country": match.group("country2").strip(),
                },
            ),
        ], ""

    match = _FR_RESTRICTION_REMOVED_THEN_LIQUIDATOR.fullmatch(leftover)
    if match:
        rule_id = "fr.text.restriction_removed_then_liquidator.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "share_transfer_restriction", "action": "removed",
                    "shares_count": _count(match.group("count")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                    "share_kind": "actions nominatives", "entire_share_capital": True,
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), role="administratrice, liquidatrice",
                signing="Einzelunterschrift", extra={
                    "action": "appointed_liquidator", "previous_role": "administratrice",
                },
            ),
        ], ""

    match = _FR_QUALIFIED_CONTRIBUTION_CLAUSE_REPEALED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.legacy_contribution_clause_repealed.v1", {
                "kind": "contribution_and_asset_acquisition_clause",
                "action": "removed",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_sheet_date": _iso_date(match.group("balance_date")),
                "assets": _amount(match.group("assets")),
                "liabilities": _amount(match.group("liabilities")),
                "net_assets": _amount(match.group("net_assets")),
                "currency": "CHF", "shares_issued": _count(match.group("shares")),
                "share_nominal": match.group("share_nominal").rstrip(".-"),
                "contribution_details": match.group("details").strip(),
            },
        )], ""

    match = _FR_MANAGER_TRANSFER_TO_NEW_MANAGER.fullmatch(leftover)
    if match and _count(match.group("transferred")) <= _count(match.group("before")):
        events = _share_transfer_events(
            match, publication_id, published_at, org_uid, plz, canton,
            "fr.persons.transfer_to_new_associate_manager.v1",
            seller_role="associé", buyer_role="associé-gérant",
            buyer_signing="Kollektivunterschrift zu zweien",
        )
        events[1].payload["new_associate"] = True
        events[1].payload["appointed_manager"] = True
        return events, ""

    match = _FR_MANAGER_PRESIDENT_TRANSFER_MALFORMED_SIGNING.fullmatch(leftover)
    if match:
        expected_remaining = _count(match.group("before")) - _count(match.group("transferred"))
        nominals = {
            match.group("nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }
        if (
            len(nominals) == 1
            and expected_remaining == _count(match.group("remaining"))
            and _count(match.group("transferred")) == _count(match.group("buyer_count"))
        ):
            events = _share_transfer_events(
                match, publication_id, published_at, org_uid, plz, canton,
                "fr.persons.manager_president_transfer_malformed_signing.v1",
                seller_role="associé-gérant président", buyer_role="associé-gérant",
                buyer_signing="Einzelunterschrift",
            )
            events[0].payload["action"] = "shares_transferred_and_appointed_president"
            events[1].payload["new_associate"] = True
            return events, ""

    match = _FR_INDIVIDUAL_PROCURATION_GRANTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.individual_procuration_granted.v1",
            match.group("name"), signing="Einzelprokura", extra={
                "action": "procuration_granted", "procuration": "individual",
            },
        )], ""

    match = _FR_TRANSFER_AND_TWO_MANAGERS.fullmatch(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        remaining = _count(match.group("remaining"))
        if match.group("nominal") == match.group("transfer_nominal"):
            rule_id = "fr.persons.transfer_and_two_managers.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            common = {
                "currency": "CHF", "share_nominal": match.group("nominal"),
                "shares_transferred": transferred,
            }
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé-gérant",
                    signing="Einzelunterschrift", extra={
                        **common, "action": "shares_transferred",
                        "counterparty": buyer, "shares_count": remaining,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé-gérant président", signing="Einzelunterschrift",
                    extra={
                        **common, "action": "shares_received_and_appointed_president",
                        "counterparty": seller, "shares_received": transferred,
                        "shares_count": transferred,
                        "origin": match.group("origin").strip(), "new_associate": True,
                    },
                ),
            ], ""

    match = _DE_REMOVED_AND_NEW_SIGNATORY.fullmatch(leftover)
    if match:
        rule_id = "de.persons.removed_and_new_collective_signatory.v1"
        removed_name = (
            f"{match.group('removed_surname').strip()}, "
            f"{match.group('removed_given').strip()}"
        )
        new_name = f"{match.group('new_surname').strip()}, {match.group('new_given').strip()}"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, removed_name,
                place=match.group("removed_place"),
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "removed", "origin": match.group("removed_origin").strip(),
                    "signing_revoked": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, new_name, place=match.group("new_place"),
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group("new_origin").strip(),
                },
            ),
        ], ""

    match = _FR_MULTIPLE_COLLECTIVE_SIGNATORIES.fullmatch(leftover)
    if match:
        names_text = match.group("names")
        before_last, separator, last = names_text.rpartition(" et ")
        names = [name.strip() for name in before_last.split(",") if name.strip()]
        if separator and last.strip():
            names.append(last.strip())
        if len(names) >= 2:
            rule_id = "fr.persons.multiple_collective_signatories.v1"
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", rule_id, name,
                    signing="Kollektivunterschrift zu zweien", extra={
                        "action": "signing_changed",
                    },
                )
                for name in names
            ], ""

    match = _DE_EXTRAORDINARY_BANKRUPTCY_ADMINISTRATION_ADDRESS_FIRST.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed",
            "de.text.extraordinary_bankruptcy_administration_address_first.v1", {
                "kind": "bankruptcy_administration", "action": "appointed",
                "administration_type": "extraordinary",
                "name": match.group("name").strip(),
                "street": match.group("street").strip(),
                "postal_code": match.group("postal_code"),
                "place": match.group("place").strip(),
                "representatives": [
                    {
                        "name": match.group("leader").strip(),
                        "profession": "Rechtsanwalt", "role": "Mandatsleiter",
                    },
                    {
                        "name": match.group("deputy").strip(),
                        "profession": "Rechtsanwalt",
                        "role": "stellvertretender Mandatsleiter",
                    },
                ],
                "assisting_authority": match.group("assisting_authority").strip(),
            },
        )], ""

    return [], leftover
