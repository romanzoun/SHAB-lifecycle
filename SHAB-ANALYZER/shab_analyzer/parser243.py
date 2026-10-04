from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_FR_LIQUIDATION_ADDRESS_CORRECTION_TAIL = re.compile(
    r"^\[non:\s*Adresse de liquidation:\s*(?P<previous>.+?)\s*$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_EXTENDED_WITH_PREVIOUS = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+die definitive Nachlassstundung letztmals bis\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\s+verlängert\.\s*\[bisher:\s*"
    r"Mit Entscheid vom\s+(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"hat\s+(?P<previous_authority>.+?)\s+die definitive Nachlassstundung bis\s+"
    r"(?P<previous_until>\d{2}\.\d{2}\.\d{4})\s+verlängert\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_NAME_CORRECTION_AND_PRECISE_ADDRESS = re.compile(
    r"^Rectification:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\)\s+est rectifiée dans ce sens que le nom correct est\s+"
    r"(?P<name>[^()]+?)\s*\(et non pas\s+(?P<previous_name>[^)]+)\)\.\s*"
    r"Adresse précise:\s*(?P<address>.+?)\.?$",
    re.I | re.UNICODE,
)
_DE_DELETION_BLOCKED_FEDERAL_TAX = re.compile(
    r"^Die Gesellschaft kann aber mangels Zustimmung der eidgenössischen "
    r"Steuerverwaltung noch nicht gelöscht werden\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_REMOVED_UID_WITH_SPACE = re.compile(
    r"^Zweigniederlassung neu:\s*(?:\[Folgende Zweigniederlassungen sind "
    r"aufgehoben worden:\]\s*)?\[gestrichen:\s*(?P<place>[^()\]]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\s*\)\]\.?$",
    re.I | re.UNICODE,
)
_DE_SHARE_DISPOSAL_RESTRICTION_REVOKED = re.compile(
    r"^\[Die Verfügungsbeschränkung gemäss\s+(?P<decision_item>.+?)\s+des "
    r"Entscheides\s+(?P<decision_ref>[^\s]+)\s+des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wird aufgehoben\.\]\s*"
    r"\[gestrichen:\s*(?P<sale_restriction>Gemäss Verfügung .+? zu verkaufen\.)\]\.?\s*"
    r"\[gestrichen:\s*(?P<provisional_measure>Gemäss Verfügung .+? bestätigt\.)\]\.?$",
    re.I | re.UNICODE,
)
_FR_SELLER_TRANSFER_TO_TWO_UNSIGNED_ASSOCIATES = re.compile(
    r"^(?P<seller>[^,.;]+)\s+détient désormais\s+(?P<remaining>[\d']+)\s+parts "
    r"de CHF\s+(?P<nominal>[\d'.]+)\s+par suite de cession de\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<transfer_nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer1>[^,.;]+),\s*(?:de|du|des|d['’])\s+(?P<origin1>[^,.;()]+)\s*"
    r"\((?P<canton1>[A-Z]{2})\),\s*à\s+(?P<place1>[^,.;]+),\s*et à\s+"
    r"(?P<buyer2>[^,.;]+),\s*(?:de|du|des|d['’])\s+(?P<origin2>[^,.;()]+)\s*"
    r"\((?P<canton2>[A-Z]{2})\),\s*à\s+(?P<place2>[^,.;]+),\s*nouveaux associés "
    r"chacun pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*tous deux sans signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_FOREIGN_EXECUTIVE_COMMITTEE_MEMBER_UNSIGNED = re.compile(
    r"^(?P<name>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{2,3}),\s*est membre du comité "
    r"directeur,\s*sans signature\.?$",
    re.I | re.UNICODE,
)
_FR_ORIGIN_CHANGED_APPOINTED_LIQUIDATOR = re.compile(
    r"^(?P<name>[^,.;]+),\s*qui est maintenant (?:de|du|des|d['’])"
    r"(?P<origin>[^,.;()]+)(?:\s*\((?P<origin_canton>[A-Z]{2})\))?,\s*"
    r"est nommé liquidateur(?: avec (?P<signing>signature individuelle))?\.?$",
    re.I | re.UNICODE,
)
_IT_ART_155_DELETION_PROCEDURE_BLOCKED_CANTONAL = re.compile(
    r"^In base l['’]applicazione dell['’](?P<legal_basis>art\.\s*155 ORC) dalla "
    r"terza grida effettuata dal registro di commercio e pubblicata sul Foglio "
    r"Ufficiale Svizzero di Commercio \(FUSC\) in data\s+"
    r"(?P<call_date1>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<call_date2>\d{2}\.\d{2}\.\d{4})\s+e\s+"
    r"(?P<call_date3>\d{2}\.\d{2}\.\d{4}),\s*nessun interesse al mantenimento "
    r"dell['’]iscrizione della società è stato notificato\.\s*La procedura di "
    r"cancellazione d['’]ufficio della società è terminata,\s*ma la cancellazione "
    r"d['’]ufficio ai sensi dell['’]art\.\s*155 ORC della società non può ancora "
    r"essere effettuata mancando il consenso dell['’]\s*autorità fiscale cantonale\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_GIVEN_NAME_CORRECTED_APPOINTED_LIQUIDATOR = re.compile(
    r"^L['’]associé[ -]gérant et président\s+(?P<family>.+?)\s+"
    r"(?P<previous_given>[^,.; ]+),\s*dont le prénom exact est\s+"
    r"(?P<given>[^,.;]+),\s*désormais (?:de|du|des|d['’])(?P<origin>[^,.;]+),\s*"
    r"est nommé liquidateur(?: avec (?P<signing>signature individuelle))?\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ADMINISTRATORS_ROLE_CHANGES = re.compile(
    r"^Les administrateurs\s+(?P<name1>[^,.;]+),\s*nommé\s+"
    r"(?P<role1>directeur)\s+et\s+(?P<name2>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<previous_role2>directeur général),\s*continuent à signer "
    r"collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_DE_SOLE_PROPRIETOR_BANKRUPTCY_SUSPENDED = re.compile(
    r"^Mit Verfügung vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+der Beschwerde gegen die Konkurseröffnung vom\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+die aufschiebende Wirkung "
    r"erteilt\.\s*Infolgedessen besteht das Einzelunternehmen entsprechend den "
    r"bisherigen Eintragungen weiter\.\s*\[bisher:\s*(?P<previous>Mit Verfügung "
    r".+? den Konkurs eröffnet\.)\]\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_TO_ORGANIZATION = re.compile(
    r"^(?P<seller>[^,.;]+),\s*associé[ -]gérant,\s*cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>.+?)\s*"
    r"\((?P<buyer_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<buyer_place>[^,.;]+),\s*nouvelle associée avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_COMPOSITION_DIVIDEND_LIQUIDATION_EXTENDED = re.compile(
    r"^Par décision rendue le\s+(?P<decision_date>\d{1,2}(?:er)?\s+"
    r"[A-Za-zÀ-ÿ]+\s+\d{4}),\s*(?P<authority>.+?)\s+a prolongé jusqu['’]au\s+"
    r"(?P<until>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4})\s+la liquidation du "
    r"concordat-dividende daté du\s+(?P<agreement_date>\d{1,2}(?:er)?\s+"
    r"[A-Za-zÀ-ÿ]+\s+\d{4}),\s*présenté par la société à ses créanciers "
    r"chirographaires\.?$",
    re.I | re.UNICODE,
)
_FR_DEFINITIVE_MORATORIUM_COMPANY_COMMISSIONER = re.compile(
    r"^Par décision rendue le\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>.+?)\s+a accordé à la société un sursis concordataire "
    r"définitif de\s+(?P<duration>[^,.;]+?),\s*échéant le\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4}),\s*et désigné\s+"
    r"(?P<commissioner>.+?)\s*\((?P<commissioner_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"à\s+(?P<commissioner_place>[^,.;]+),\s*en qualité de commissaire au sursis\.?$",
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
_FR_NUMBERS = {
    "un": 1,
    "une": 1,
    "deux": 2,
    "trois": 3,
    "quatre": 4,
    "cinq": 5,
    "six": 6,
    "sept": 7,
    "huit": 8,
    "neuf": 9,
    "dix": 10,
    "onze": 11,
    "douze": 12,
}


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _french_date(raw: str) -> str:
    day, month, year = raw.casefold().replace("1er", "1", 1).split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _amount(raw: str) -> Decimal:
    return Decimal(raw.replace("'", ""))


def _duration_months(raw: str) -> int | None:
    token = raw.strip().casefold().split()[0]
    return int(token) if token.isdigit() else _FR_NUMBERS.get(token)


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


def extract_parser243_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 243."""
    del language  # Historical notices can contain text in another language.
    leftover = text.strip()

    match = _FR_LIQUIDATION_ADDRESS_CORRECTION_TAIL.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.liquidation_address_correction_tail.v1", {
                "kind": "liquidation_address", "action": "corrected",
                "to": match.group("previous").strip(),
            },
        )], ""

    match = _DE_DEFINITIVE_MORATORIUM_EXTENDED_WITH_PREVIOUS.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.definitive_moratorium_extended_previous.v1", {
                "kind": "composition_moratorium_extended", "moratorium_type": "definitive",
                "final_extension": True,
                "decision_date": _iso_date(match.group("decision_date")),
                "until": _iso_date(match.group("until")),
                "authority": match.group("authority").strip(),
                "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                "previous_until": _iso_date(match.group("previous_until")),
                "previous_authority": match.group("previous_authority").strip(),
            },
        )], ""

    match = _FR_NAME_CORRECTION_AND_PRECISE_ADDRESS.fullmatch(leftover)
    if match:
        rule_id = "fr.text.name_correction_and_precise_address.v1"
        reference = {
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_id": match.group("notice_id"),
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", rule_id, match.group("name"), extra={
                    "action": "name_corrected",
                    "previous_name": match.group("previous_name").strip(),
                    **reference,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", rule_id, {
                    "action": "precise_address_recorded",
                    "address": match.group("address").strip(),
                    **reference,
                },
            ),
        ], ""

    if _DE_DELETION_BLOCKED_FEDERAL_TAX.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.deletion_blocked_federal_tax.v1", {
                "kind": "deletion_blocked",
                "deletion_blocked_reason": "federal_tax_authority_consent_missing",
                "tax_authority_consent_missing": True,
            },
        )], ""

    match = _DE_BRANCH_REMOVED_UID_WITH_SPACE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_removed_uid_spacing.v1", {
                "action": "removed", "place": match.group("place").strip(),
                "branch_uid": match.group("uid"),
            },
        )], ""

    match = _DE_SHARE_DISPOSAL_RESTRICTION_REVOKED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.share_disposal_restriction_revoked.v1", {
                "kind": "share_disposal_restriction", "action": "revoked",
                "decision_item": match.group("decision_item").strip(),
                "decision_reference": match.group("decision_ref"),
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "previous_restrictions": [
                    match.group("sale_restriction").strip(),
                    match.group("provisional_measure").strip(),
                ],
            },
        )], ""

    match = _FR_SELLER_TRANSFER_TO_TWO_UNSIGNED_ASSOCIATES.fullmatch(leftover)
    if match:
        remaining = _count(match.group("remaining"))
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        if (
            transferred != 2 * buyer_count
            or len({
                _amount(match.group("nominal")),
                _amount(match.group("transfer_nominal")),
                _amount(match.group("buyer_nominal")),
            }) != 1
        ):
            return [], leftover
        rule_id = "fr.persons.transfer_to_two_unsigned_associates.v1"
        seller = match.group("seller").strip()
        buyers = [match.group("buyer1").strip(), match.group("buyer2").strip()]
        common = {"currency": "CHF", "share_nominal": match.group("nominal")}
        events = [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, seller, role="associé", extra={
                "action": "shares_transferred", "shares_transferred": transferred,
                "shares_count": remaining, "previous_shares_count": remaining + transferred,
                "counterparties": buyers, **common,
            },
        )]
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"buyer{index}"),
                place=match.group(f"place{index}"), role="associé", extra={
                    "action": "appointed_and_shares_received", "counterparty": seller,
                    "origin": match.group(f"origin{index}").strip(),
                    "origin_canton": match.group(f"canton{index}"),
                    "shares_received": buyer_count, "shares_count": buyer_count,
                    "without_signature": True, **common,
                },
            ))
        return events, ""

    match = _FR_FOREIGN_EXECUTIVE_COMMITTEE_MEMBER_UNSIGNED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.executive_committee_member_foreign_unsigned.v1",
            match.group("name"), place=match.group("place"),
            role="membre du comité directeur", extra={
                "action": "appointed", "origin": match.group("origin").strip(),
                "country": match.group("country").upper(), "without_signature": True,
            },
        )], ""

    match = _FR_ORIGIN_CHANGED_APPOINTED_LIQUIDATOR.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.origin_changed_appointed_liquidator.v1",
            match.group("name"), role="liquidateur",
            signing="Einzelunterschrift" if match.group("signing") else None, extra={
                "action": "origin_changed_and_appointed_liquidator",
                "origin": match.group("origin").strip(),
                "origin_canton": match.group("origin_canton"),
            },
        )], ""

    match = _IT_ART_155_DELETION_PROCEDURE_BLOCKED_CANTONAL.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.art155_deletion_procedure_blocked_cantonal.v1", {
                "kind": "official_deletion_procedure", "action": "completed",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "call_dates": [
                    _iso_date(match.group("call_date1")),
                    _iso_date(match.group("call_date2")),
                    _iso_date(match.group("call_date3")),
                ],
                "interest_notified": False, "deletion_blocked": True,
                "deletion_blocked_reason": "cantonal_tax_authority_consent_missing",
            },
        )], ""

    match = _FR_MANAGER_GIVEN_NAME_CORRECTED_APPOINTED_LIQUIDATOR.fullmatch(leftover)
    if match:
        family = match.group("family").strip()
        name = f"{family} {match.group('given').strip()}"
        previous_name = f"{family} {match.group('previous_given').strip()}"
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.manager_name_corrected_appointed_liquidator.v1",
            name, role="associé-gérant; président; liquidateur",
            signing="Einzelunterschrift" if match.group("signing") else None, extra={
                "action": "name_and_role_changed", "previous_name": previous_name,
                "origin": match.group("origin").strip(), "origin_changed": True,
                "appointed_liquidator": True,
            },
        )], ""

    match = _FR_TWO_ADMINISTRATORS_ROLE_CHANGES.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_administrators_role_changes.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role="administrateur; directeur", signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed_additional_role", "signing_continues": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                role="administrateur", signing="Kollektivunterschrift zu zweien", extra={
                    "action": "role_changed", "previous_role": match.group("previous_role2"),
                    "signing_continues": True,
                },
            ),
        ], ""

    match = _DE_SOLE_PROPRIETOR_BANKRUPTCY_SUSPENDED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.sole_proprietor_bankruptcy_suspended.v1", {
                "kind": "bankruptcy", "action": "suspended_on_appeal",
                "decision_date": _iso_date(match.group("decision_date")),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "authority": match.group("authority").strip(),
                "suspensive_effect": True, "previous_status_restored": True,
                "organization_kind": "sole_proprietorship",
                "previous": match.group("previous").strip(),
            },
        )], ""

    match = _FR_MANAGER_TRANSFER_TO_ORGANIZATION.fullmatch(leftover)
    if match:
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        remaining = _count(match.group("remaining"))
        buyer_count = _count(match.group("buyer_count"))
        if (
            before != transferred + remaining
            or transferred != buyer_count
            or len({
                _amount(match.group("nominal")),
                _amount(match.group("buyer_nominal")),
                _amount(match.group("remaining_nominal")),
            }) != 1
        ):
            return [], leftover
        rule_id = "fr.persons.manager_transfer_to_organization.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {"currency": "CHF", "share_nominal": match.group("nominal")}
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant", extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "previous_shares_count": before, "shares_transferred": transferred,
                    "shares_count": remaining, **common,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("buyer_place"),
                uid=match.group("buyer_uid"), role="associée", extra={
                    "action": "appointed_and_shares_received", "counterparty": seller,
                    "uid": match.group("buyer_uid"), "shares_received": transferred,
                    "shares_count": buyer_count, **common,
                },
            ),
        ], ""

    match = _FR_COMPOSITION_DIVIDEND_LIQUIDATION_EXTENDED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.composition_dividend_liquidation_extended.v1", {
                "kind": "composition_dividend_liquidation", "action": "extended",
                "decision_date": _french_date(match.group("decision_date")),
                "until": _french_date(match.group("until")),
                "agreement_date": _french_date(match.group("agreement_date")),
                "authority": match.group("authority").strip(),
                "creditor_class": "unsecured_creditors",
            },
        )], ""

    match = _FR_DEFINITIVE_MORATORIUM_COMPANY_COMMISSIONER.fullmatch(leftover)
    if match:
        rule_id = "fr.text.definitive_moratorium_company_commissioner.v1"
        commissioner = match.group("commissioner").strip()
        commissioner_uid = match.group("commissioner_uid")
        commissioner_place = match.group("commissioner_place").strip()
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "composition_moratorium_granted",
                    "moratorium_type": "definitive", "subject": "company",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "until": _iso_date(match.group("until")),
                    "duration": match.group("duration").strip(),
                    "duration_months": _duration_months(match.group("duration")),
                    "authority": match.group("authority").strip(),
                    "commissioner": commissioner, "commissioner_uid": commissioner_uid,
                    "commissioner_place": commissioner_place,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, commissioner, place=commissioner_place,
                uid=commissioner_uid, role="commissaire au sursis", extra={
                    "action": "appointed", "uid": commissioner_uid,
                },
            ),
        ], ""

    return [], leftover
