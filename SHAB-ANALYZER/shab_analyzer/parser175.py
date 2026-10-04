from __future__ import annotations

import re
from decimal import Decimal

from .keys import person_key
from .models import Event


_FR_ORIGIN = r"(?:du|de la|des|de|d['’])\s*"

_DE_ASSET_TRANSFER_REAL_ESTATE_SHARES_CREDIT = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+mit Inventar per\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+),\s*darunter die Grundstücke\s+"
    r"(?P<real_estate>.+?)\s+und Fremdkapital von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+"
    r"(?P<place>[^.]+)\.\s*Gegenleistung:\s*(?P<share_count>[\d']+)\s+"
    r"(?P<share_kind>Namenaktien) zu CHF\s+(?P<share_nominal>[\d'.]+)\s+"
    r"und Gutschrift von CHF\s+(?P<credit>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_COLLECTIVE_EXCEPT_LIST = re.compile(
    r"^Nouveau membre du conseil de fondation toutefois pas avec\s+"
    r"(?P<excluded>.+?)\s*:\s*(?P<name>[^,.;]+),\s*" + _FR_ORIGIN
    + r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_SUSPENSION_REVOKED = re.compile(
    r"^Mit Verfügung des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+ist die Einstellung mangels "
    r"Aktiven widerrufen worden\.\s*\[bisher:\s*Das Konkursverfahren ist mit "
    r"Verfügung des\s+(?P<previous_authority>.+?)\s+vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+mangels Aktiven eingestellt "
    r"worden\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_INTERIM_FOUNDATION_MANDATE_ENDED = re.compile(
    r"^\[gestrichen:\s*Mit Verfügung der\s+(?P<previous_authority>.+?)\s+vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+wurden die Stiftungsräte "
    r"abgesetzt und deren Unterschriften gelöscht\.\s*Zudem wurde\s+"
    r"(?P<name>.+?)\s+als interimistischer Stiftungsrat mit Einzelunterschrift "
    r"eingesetzt\.\]\.?\s*Mit Verfügung der\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wird festgestellt,\s*dass das "
    r"Mandat des eingesetzten interimistischen Stiftungsrats\s+(?P=name)\s+seit\s+"
    r"(?P<end_date>\d{2}\.\d{2}\.\d{4})\s+beendet ist\.?$",
    re.I | re.UNICODE,
)
_DE_HEAD_OFFICE_OWNER_BANKRUPTCY = re.compile(
    r"^Bemerkungen zum Hauptsitz neu:\s*Mit Entscheid des\s+"
    r"(?P<authority>.+?)\s+vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"wurde über den Inhaber dieses Einzelunternehmens am Hauptsitz,\s*mit "
    r"Wirkung ab dem\s+(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}[:.]\d{2})\s+Uhr,\s*der Konkurs eröffnet\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_PROPRIETOR_ASSET_TRANSFER_PARTS_CLAIM = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<agreement_date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"le titulaire a transféré des actifs pour CHF\s+(?P<assets>[\d'.]+)\s+"
    r"et des passifs envers les tiers pour CHF\s+(?P<liabilities>[\d'.]+),\s*"
    r"à\s+(?P<recipient>.+?)\s+à\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*Contre-prestation:\s*"
    r"(?P<share_count>[\d']+)\s+(?P<share_kind>parts) de CHF\s+"
    r"(?P<share_nominal>[\d'.]+),\s*créance de CHF\s+(?P<claim>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_NAME_NEW = re.compile(
    r"^Firma neu:\s*(?P<name>[^.]+)\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_ALL_SHARES_WITH_AVAILABLE_EQUITY = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di\s+(?P<absorbed_name>.+?),\s*"
    r"in\s+(?P<absorbed_place>[^()]+?)\s*"
    r"\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*secondo contratto di "
    r"fusione del\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+e bilancio al\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta attivi per CHF\s+"
    r"(?P<assets>[\d'.]+),?\s+e passivi verso terzi per CHF\s+"
    r"(?P<liabilities>[\d'.]+)\.\s*Conformemente all['’]attestazione di un "
    r"perito revisore abilitato,\s*la società assuntrice dispone di fondi propri "
    r"liberamente disponibili equivalenti almeno all['’]ammontare dello "
    r"scoperto\.\s*La società assuntrice detiene tutte le azioni della società "
    r"trasferente,\s*per cui la fusione avviene senza aumento di capitale e "
    r"senza attribuzione di azioni\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_WITH_THREE_SIGNERS = re.compile(
    r"^Nouveau membre du conseil de fondation avec le président,\s*le "
    r"vice-président ou le trésorier:\s*(?P<name>[^,.;]+),\s*" + _FR_ORIGIN
    + r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<role>[^.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUR_BOARD_MEMBERS_COLLECTIVE = re.compile(
    r"^(?P<name1>[^,.;]+),\s*" + _FR_ORIGIN + r"(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,.;]+),\s*(?P<name2>[^,.;]+),\s*" + _FR_ORIGIN
    + r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"(?P<country2>[A-Z]{1,3}),\s*(?P<name3>[^,.;]+),\s*" + _FR_ORIGIN
    + r"(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+)\s+et\s+"
    r"(?P<name4>[^,.;]+),\s*" + _FR_ORIGIN + r"(?P<origin4>[^,.;]+),\s*"
    r"sont membres du conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_CLAUSE_EXPIRED = re.compile(
    r"^\[Streichung der Statutenbestimmung über die mit Ermächtigungsbeschluss "
    r"vom\s+(?P<authorization_date>\d{2}\.\d{2}\.\d{4})\s+eingeführte "
    r"genehmigte Kapitalerhöhung infolge Ablauf der zeitlichen Befristung\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_CONDITIONAL_CAPITAL_CLAUSE_REMOVED_NO_RIGHTS = re.compile(
    r"^Suppression de la clause statutaire relative à l['’]augmentation "
    r"conditionnelle du capital-actions,\s*fondée sur la décision relative à "
    r"l['’]octroi de droits du\s+(?P<authorization_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"aucun droit n['’]ayant été accordé\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGERS_REMOVED_NEW_LIQUIDATORS = re.compile(
    r"^(?P<removed1>.+?)\s+et\s+(?P<removed2>.+?)\s+ne sont plus "
    r"gérants,\s*ni liquidateurs;\s*leur signature est radiée\.\s*Signature "
    r"collective à deux est conférée à\s+(?P<name1>[^,.;]+),\s*"
    r"(?P<role1>gérant président),\s*et\s+(?P<name2>[^,.;]+),\s*"
    r"(?P<role2>gérant),\s*tous deux\s+" + _FR_ORIGIN
    + r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^(),.;]+)\s*"
    r"\((?P<country>[^)]+)\),\s*liquidateurs\.?$",
    re.I | re.UNICODE,
)
_DE_OWNER_BANKRUPTCY_APPEAL_SUSPENSIVE_HISTORY = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat das\s+"
    r"(?P<authority>.+?)\s+der Beschwerde gegen den Entscheid des\s+"
    r"(?P<bankruptcy_authority>.+?)\s+vom\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4}),\s*mit dem über den Inhaber "
    r"des Einzelunternehmens der Konkurs eröffnet wurde,\s*die aufschiebende "
    r"Wirkung gewährt\.\s*\[bisher:\s*Über den Inhaber dieses Einzelunternehmens "
    r"ist mit Entscheid des\s+(?P<previous_authority>.+?)\s+vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+mit Wirkung ab dem\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}[:.]\d{2})\s+Uhr,\s*der Konkurs eröffnet "
    r"worden\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDING_BUSINESS_ACQUISITION_REGISTERED_SHARES = re.compile(
    r"^eingetragenen Einzelunternehmens\s+(?P<source>.+?),\s*in\s+"
    r"(?P<source_place>[^,.;]+),\s*gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Übernahmebilanz per\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\s+mit Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven von CHF\s+(?P<liabilities>[\d'.]+),\s*"
    r"wofür\s+(?P<share_count>[\d']+)\s+(?P<share_kind>Namenaktien) zu CHF\s+"
    r"(?P<share_nominal>[\d'.]+)\s+ausgegeben und CHF\s+(?P<credit>[\d'.]+)\s+"
    r"als Forderung gutgeschrieben werden\.?$",
    re.I | re.UNICODE,
)
_DE_CORRECTION_REPEALED_MARKER = re.compile(
    r"^\[aufgehoben\]\.?$",
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
    day, month, year = raw.casefold().replace("1er", "1").split()
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


def extract_parser175_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 175."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_ASSET_TRANSFER_REAL_ESTATE_SHARES_CREDIT.fullmatch(leftover)
    if match and (
        _amount(match.group("assets")) - _amount(match.group("liabilities"))
        == _count(match.group("share_count")) * _amount(match.group("share_nominal"))
        + _amount(match.group("credit"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_real_estate_shares_credit.v1", {
                "source_kind": "company",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "inventory_date": _iso_date(match.group("inventory_date")),
                "assets": match.group("assets"),
                "assets_include_real_estate": True,
                "real_estate": match.group("real_estate").strip(),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "borrowed_capital",
                "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration_kind": "registered_shares_and_credit",
                "consideration_shares_count": _count(match.group("share_count")),
                "consideration_share_kind": match.group("share_kind"),
                "consideration_share_nominal": match.group("share_nominal"),
                "consideration_credit": match.group("credit"),
            },
        )], ""

    match = _FR_FOUNDATION_MEMBER_COLLECTIVE_EXCEPT_LIST.fullmatch(leftover)
    if match:
        excluded = [
            name.strip()
            for name in re.split(r"\s*,\s*|\s+et\s+", match.group("excluded"))
            if name.strip()
        ]
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.foundation_member_collective_except_list.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil de fondation",
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "appointed",
                "origin": match.group("origin").strip(),
                "excluded_co_signers": excluded,
            },
        )], ""

    match = _DE_BANKRUPTCY_SUSPENSION_REVOKED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_suspension_revoked.v2", {
                "kind": "bankruptcy_proceedings_suspension",
                "action": "revoked",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "previous_action": "suspended_for_lack_of_assets",
                "previous_decision_date": _iso_date(match.group("previous_date")),
                "previous_authority": match.group("previous_authority").strip(),
            },
        )], ""

    match = _DE_INTERIM_FOUNDATION_MANDATE_ENDED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_removed", "de.persons.interim_foundation_mandate_ended.v1",
            match.group("name"), role="interimistischer Stiftungsrat",
            signing="Einzelunterschrift",
            extra={
                "action": "mandate_ended",
                "end_date": _iso_date(match.group("end_date")),
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "previous_supervisory_decision_date": _iso_date(
                    match.group("previous_date")
                ),
                "previous_authority": match.group("previous_authority").strip(),
                "previous_note_removed": True,
            },
        )], ""

    match = _DE_HEAD_OFFICE_OWNER_BANKRUPTCY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.head_office_owner_bankruptcy.v1", {
                "kind": "bankruptcy_opened",
                "scope": "head_office_owner",
                "action": "opened",
                "decision_date": _iso_date(match.group("decision_date")),
                "effective_date": _iso_date(match.group("effective_date")),
                "effective_time": match.group("effective_time").replace(".", ":"),
                "authority": match.group("authority").strip(),
            },
        )], ""

    match = _FR_SOLE_PROPRIETOR_ASSET_TRANSFER_PARTS_CLAIM.fullmatch(leftover)
    if match and (
        _amount(match.group("assets")) - _amount(match.group("liabilities"))
        == _count(match.group("share_count")) * _amount(match.group("share_nominal"))
        + _amount(match.group("claim"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.sole_proprietor_asset_transfer_parts_claim.v1", {
                "source_kind": "sole_proprietor",
                "agreement_date": _french_date(match.group("agreement_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities",
                "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration_kind": "shares_and_claim",
                "consideration_shares_count": _count(match.group("share_count")),
                "consideration_share_kind": match.group("share_kind").lower(),
                "consideration_share_nominal": match.group("share_nominal"),
                "consideration_claim": match.group("claim"),
            },
        )], ""

    match = _DE_COMPANY_NAME_NEW.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_name_changed", "de.text.company_name_new_correction.v1", {
                "action": "corrected",
                "name": match.group("name").strip(),
            },
        )], ""

    match = _IT_MERGER_ALL_SHARES_WITH_AVAILABLE_EQUITY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "it.text.merger_all_shares_available_equity.v1", {
                "kind": "absorption",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities",
                "currency": "CHF",
                "sufficient_free_equity_confirmed": True,
                "expert_confirmation": True,
                "acquirer_owns_all_shares": True,
                "capital_increase": False,
                "share_allocation": False,
            },
        )], ""

    match = _FR_FOUNDATION_MEMBER_WITH_THREE_SIGNERS.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.foundation_member_three_signer_options.v1",
            match.group("name"), place=match.group("place"),
            role=f"membre du conseil de fondation, {match.group('role').strip()}",
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "appointed",
                "origin": match.group("origin").strip(),
                "required_with": ["président", "vice-président", "trésorier"],
            },
        )], ""

    match = _FR_FOUR_BOARD_MEMBERS_COLLECTIVE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.four_board_members_collective.v1"
        events = []
        for index in (1, 2, 3, 4):
            extra = {
                "action": "appointed",
                "origin": match.group(f"origin{index}").strip(),
            }
            country = match.groupdict().get(f"country{index}")
            if country:
                extra["country"] = country
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.groupdict().get(f"place{index}"),
                role="membre du conseil d'administration",
                signing="Kollektivunterschrift zu zweien",
                extra=extra,
            ))
        return events, ""

    match = _DE_AUTHORIZED_CAPITAL_CLAUSE_EXPIRED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_clause_expired.v1", {
                "kind": "authorized_capital_clause",
                "action": "removed",
                "authorization_date": _iso_date(match.group("authorization_date")),
                "reason": "time_limit_expired",
            },
        )], ""

    match = _FR_CONDITIONAL_CAPITAL_CLAUSE_REMOVED_NO_RIGHTS.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.conditional_capital_clause_removed_no_rights.v1", {
                "kind": "conditional_capital_clause",
                "action": "removed",
                "authorization_date": _iso_date(match.group("authorization_date")),
                "rights_granted": False,
            },
        )], ""

    match = _FR_MANAGERS_REMOVED_NEW_LIQUIDATORS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.managers_removed_new_liquidators.v1"
        events = []
        for group in ("removed1", "removed2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group(group),
                role="gérant et liquidateur",
                extra={"action": "removed", "signing_revoked": True},
            ))
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group("place"),
                role=f"{match.group(f'role{index}')} et liquidateur",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed",
                    "origin": match.group("origin").strip(),
                    "country": match.group("country").strip(),
                },
            ))
        return events, ""

    match = _DE_OWNER_BANKRUPTCY_APPEAL_SUSPENSIVE_HISTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.owner_bankruptcy_appeal_suspensive_history.v1", {
                "kind": "bankruptcy_effect_suspended",
                "scope": "owner",
                "action": "suspensive_effect_granted",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "bankruptcy_decision_date": _iso_date(match.group("bankruptcy_date")),
                "bankruptcy_authority": match.group("bankruptcy_authority").strip(),
                "previous_decision_date": _iso_date(match.group("previous_date")),
                "previous_authority": match.group("previous_authority").strip(),
                "previous_effective_date": _iso_date(match.group("effective_date")),
                "previous_effective_time": match.group("effective_time").replace(".", ":"),
            },
        )], ""

    match = _DE_FOUNDING_BUSINESS_ACQUISITION_REGISTERED_SHARES.fullmatch(leftover)
    if match and (
        _amount(match.group("assets")) - _amount(match.group("liabilities"))
        == _count(match.group("share_count")) * _amount(match.group("share_nominal"))
        + _amount(match.group("credit"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred",
            "de.text.founding_business_acquisition_registered_shares.v1", {
                "kind": "contribution_in_kind_and_asset_acquisition",
                "source": match.group("source").strip(),
                "source_place": match.group("source_place").strip(),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "currency": "CHF",
                "shares_issued": _count(match.group("share_count")),
                "share_kind": match.group("share_kind"),
                "share_nominal": match.group("share_nominal"),
                "receivable": match.group("credit"),
            },
        )], ""

    match = _DE_CORRECTION_REPEALED_MARKER.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "audit_requirement_changed", "de.text.audit_waiver_correction_repealed.v1", {
                "kind": "limited_audit_waiver",
                "action": "previous_entry_removed",
                "limited_audit_waived": False,
                "previous_entry_erroneous": True,
            },
        )], ""

    return [], text
