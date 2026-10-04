from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_FR_MANAGER_APPOINTED_LIQUIDATOR = re.compile(
    r"^(?P<name>[^,.;]+),\s*(?P<previous_role>associé-gérant),\s*est nommé "
    r"(?P<role>liquidateur);\s*continue de signer individuellement\.?$",
    re.I | re.UNICODE,
)
_IT_LIQUIDATION_COMPLETED_DELETION_BLOCKED = re.compile(
    r"^La liquidazione è terminta\.\s*Ma la cancellazione della società "
    r"non può ancora essere effettuata mancando il consenso dell['’]autorità "
    r"fiscale federale\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_CAPITAL_SUPPLEMENTED = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(publication FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+page\s+"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée en ce sens que le capital-actions "
    r"de la société est de\s+(?P<currency>[A-Z]{3})\s+(?P<total>[\d'.]+),\s*"
    r"entièrement libéré,\s*divisé en\s+(?P<count>[\d']+)\s+actions de\s+"
    r"(?P=currency)\s+(?P<nominal>[\d'.]+),\s*(?P<share_kind>au porteur)\.?$",
    re.I | re.UNICODE,
)
_FR_HOLDER_NAME_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription\s+n[°o]\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le nom exact "
    r"du titulaire est\s+(?P<name>[^()]+?)\s*\(et non\s+"
    r"(?P<previous_name>.+?)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_CANTONAL_APPEAL_INADMISSIBLE = re.compile(
    r"^Par arrêt du\s+(?P<decision_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"(?P<authority>.+?)\s+a déclaré le recours irrecevable et dit que la "
    r"requête d['’]effet suspensif est sans objet\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_ROLE_CHANGES_AND_SIGNING = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<president_previous_role>secrétaire),\s*nommé\s+président,\s*"
    r"(?P<former_president>[^,.;]+),\s*jusqu['’]ici\s+président,\s*"
    r"(?P<member>[^,.;]+)\s+et\s+(?P<secretary>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*secrétaire\.\s*"
    r"Signature individuelle de\s+(?P=former_president)\s+ou collective à deux "
    r"des autres administrateurs\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_ORGANIZATION_SECTION_REMOVED = re.compile(
    r"^Radiation de la rubrique relative à l['’]organisation de la fondation,\s*"
    r"plus soumise à inscription\.\s*Statuts modifiés en conséquence le\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGERS_APPOINTED_LIQUIDATORS = re.compile(
    r"^Liquidateurs:\s*les associés gérants\s+(?P<name1>[^,.;]+)\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*maintenant domicilié à\s+(?P<place2>[^,.;]+),\s*"
    r"lesquels continuent à signer individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_OPENED_AND_DISSOLVED = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+über die Gesellschaft mit Wirkung ab dem\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}\.\d{2})\s+Uhr,\s*den Konkurs eröffnet,\s*"
    r"womit sie aufgelöst ist\.?$",
    re.I | re.UNICODE,
)
_FR_ORGANIZATION_MULTI_SHARE_TRANSFER = re.compile(
    r"^(?P<seller>.+?)\s+\((?P<seller_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de\s+"
    r"(?P<currency>[A-Z]{3})\s+(?P<nominal>[\d'.]+)\s+"
    r"(?P<allocations>.+);\s*(?P=seller)\s+\((?P=seller_uid)\)\s+reste titulaire "
    r"de\s+(?P<remaining>[\d']+)\s+parts de\s+(?P=currency)\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_FR_SHARE_ALLOCATION = re.compile(
    r"(?:^|\b(?:et\s+)?par\s+)(?P<count>[\d']+)\s+parts à\s+"
    r"(?P<buyer>[^,(]+?)(?:\s+\((?P<registry_id>\d{8,})\))?,\s*à\s+"
    r"(?P<place>[^(),]+?)\s*\((?P<country>[^)]+)\),\s*"
    r"nouvel(?P<feminine>le)? associé(?:e)? avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de\s+(?P<currency>[A-Z]{3})\s+"
    r"(?P<nominal>[\d'.]+)",
    re.I | re.UNICODE,
)
_FR_MANAGER_SHARE_TRANSFER = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de\s+"
    r"(?P<currency>[A-Z]{3})\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé(?: avec\s+"
    r"(?P<buyer_signing>signature individuelle))?\.?\s*(?P=seller)\s+reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de\s+(?P=currency)\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_PARTNERSHIP_CONTINUED_AS_SOLE_TRADER = re.compile(
    r"^Die Gesellschaft hat sich infolge Ausscheidens des Gesellschafters\s+"
    r"(?P<departed>.+?)\s+aufgelöst\.\s*Die Firma ist erloschen\.\s*Der "
    r"Gesellschafter\s+(?P<continuing>.+?)\s+führt im Sinne von\s+"
    r"(?P<legal_basis>Art\.\s*579 OR)\s+das Geschäft als Einzelkaufmann fort\.?$",
    re.I | re.UNICODE,
)
_DE_MISSING_REGISTRY_ID_CORRECTED_TYPO = re.compile(
    r"^Im SHAB Nr\.\s*(?P<notice>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten TR[ -]Eintrag\s+"
    r"(?P<entry>[\d/]+)\s+wurdte irrtümlich die CH-Nummer weggelassen\.\s*"
    r"Richtig ist:\s*\[bisher:\s*(?P<name>.+?)\s*"
    r"\((?P<registry_id>CH-[\d.]+-\d)\)\]\.?$",
    re.I | re.UNICODE,
)
_DE_LLC_EQUITY_CAPITAL_INCREASE_AND_TRANSFORMATION = re.compile(
    r"^Umwandlung:\s*Die Gesellschaft mit beschränkter Haftung hat das "
    r"Stammkapital durch Liberierung aus frei verwendbarem Eigenkapital auf\s+"
    r"(?P<currency>[A-Z]{3})\s+(?P<capital>[\d'.]+)\s+erhöht und wird gemäss "
    r"Umwandlungsplan vom\s+(?P<plan_date>\d{2}\.\d{2}\.\d{4})\s+und Bilanz per\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\s+mit Aktiven von\s+(?P=currency)\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von\s+"
    r"(?P=currency)\s+(?P<liabilities>[\d'.]+)\s+in eine Aktiengesellschaft "
    r"umgewandelt\.\s*Der Gesellschafter erhält für seine bisherigen Stammanteile\s+"
    r"(?P<shares>[\d']+)\s+Namenaktien zu\s+(?P=currency)\s+"
    r"(?P<share_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FEMALE_MANAGER_SHARE_TRANSFER_AND_SIGNING = re.compile(
    r"^L['’]associée-gérante\s+(?P<seller>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+parts de\s+(?P<currency>[A-Z]{3})\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de\s+(?P=currency)\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*Signature individuelle a été conférée "
    r"à l['’]associé\s+(?P=buyer)\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_CORRECTED_WITH_NOTICE = re.compile(
    r"^L['’]inscription\s+N[°ºo]\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que l['’]organe de "
    r"révision n['’]est pas\s+(?P<previous_name>.+?)\s*"
    r"\((?P<previous_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+mais\s+"
    r"(?P<name>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)


_FRENCH_MONTHS = {
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


def _iso_french_date(raw: str) -> str:
    day, month, year = raw.lower().split()
    return f"{int(year):04d}-{_FRENCH_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _money(raw: str) -> Decimal:
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
    return Event(
        publication_id=publication_id,
        published_at=published_at,
        event_type=event_type,
        rule_id=rule_id,
        org_uid=org_uid,
        person_key=person_key(name=clean_name, place=clean_place, uid=uid),
        plz=plz,
        canton=canton,
        role=role.strip() if role else None,
        signing=signing,
        payload={
            "name": clean_name,
            "place": clean_place,
            **({"uid": uid} if uid else {}),
            **(extra or {}),
        },
    )


def extract_parser223_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 223."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_MANAGER_APPOINTED_LIQUIDATOR.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.manager_appointed_liquidator.v1",
            match.group("name"), role="associé-gérant et liquidateur",
            signing="Einzelunterschrift", extra={
                "action": "appointed_liquidator",
                "previous_role": match.group("previous_role"),
            },
        )], ""

    if _IT_LIQUIDATION_COMPLETED_DELETION_BLOCKED.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.liquidation_completed_deletion_blocked.v1", {
                "kind": "liquidation", "action": "completed",
                "deletion_pending": True, "deletion_blocked": True,
                "deletion_blocked_reason": "federal_tax_authority_consent_missing",
                "source_typo": "terminta",
            },
        )], ""

    match = _FR_SHARE_CAPITAL_SUPPLEMENTED.fullmatch(leftover)
    if match and _money(match.group("total")) == (
        _count(match.group("count")) * _money(match.group("nominal"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.share_capital_supplemented_bearer.v1", {
                "kind": "share_structure", "action": "publication_supplemented",
                "currency": match.group("currency").upper(),
                "total": match.group("total"), "fully_paid": True,
                "shares_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"),
                "share_kind": "bearer", "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_HOLDER_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.holder_name_corrected.v1",
            match.group("name"), role="titulaire", extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_CANTONAL_APPEAL_INADMISSIBLE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.cantonal_appeal_inadmissible.v1", {
                "kind": "appeal", "action": "inadmissible",
                "decision_date": _iso_french_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "suspensive_effect_request": "moot",
            },
        )], ""

    match = _FR_BOARD_ROLE_CHANGES_AND_SIGNING.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.board_role_changes_and_signing.v1"
        common_signing = "Kollektivunterschrift zu zweien"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président du conseil d'administration", signing=common_signing,
                extra={"action": "appointed_president", "previous_role": "secrétaire"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("former_president"),
                role="administrateur", signing="Einzelunterschrift",
                extra={"action": "role_and_signing_changed", "previous_role": "président"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                role="administrateur", signing=common_signing,
                extra={"action": "registered"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("secretary"),
                place=match.group("place"), role="secrétaire du conseil d'administration",
                signing=common_signing, extra={
                    "action": "registered", "origin": match.group("origin").strip(),
                },
            ),
        ], ""

    match = _FR_FOUNDATION_ORGANIZATION_SECTION_REMOVED.fullmatch(leftover)
    if match:
        rule_id = "fr.text.foundation_organization_section_removed.v1"
        date = _iso_date(match.group("date"))
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id, {
                    "kind": "foundation_organization", "action": "register_section_removed",
                    "reason": "no_longer_subject_to_registration",
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id, {
                    "action": "modified_consequently", "date": date,
                },
            ),
        ], ""

    match = _FR_ASSOCIATE_MANAGERS_APPOINTED_LIQUIDATORS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.associate_managers_appointed_liquidators.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role="associé-gérant et liquidateur", signing="Einzelunterschrift",
                extra={"action": "appointed_liquidator"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="associé-gérant et liquidateur",
                signing="Einzelunterschrift", extra={
                    "action": "appointed_liquidator", "domicile_changed": True,
                },
            ),
        ], ""

    match = _DE_BANKRUPTCY_OPENED_AND_DISSOLVED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_opened_and_dissolved.v1", {
                "kind": "bankruptcy", "action": "opened",
                "decision_date": _iso_date(match.group("decision_date")),
                "effective_date": _iso_date(match.group("effective_date")),
                "effective_time": match.group("effective_time").replace(".", ":"),
                "authority": match.group("authority").strip(),
                "organization_dissolved": True,
            },
        )], ""

    match = _FR_ORGANIZATION_MULTI_SHARE_TRANSFER.fullmatch(leftover)
    if match:
        allocations_text = re.sub(
            r",\s*les\s+\w+\s+de\s+[^,]+,\s*sans signature,\s*et\s+",
            " ", match.group("allocations"), flags=re.I | re.UNICODE,
        )
        allocations = list(_FR_SHARE_ALLOCATION.finditer(allocations_text))
        allocations_leftover = re.sub(
            r"[\s,]+", "", _FR_SHARE_ALLOCATION.sub("", allocations_text)
        )
        transferred = _count(match.group("transferred"))
        before = _count(match.group("before"))
        remaining = _count(match.group("remaining"))
        nominal = match.group("nominal")
        currency = match.group("currency").upper()
        if (
            allocations
            and not allocations_leftover
            and sum(_count(item.group("count")) for item in allocations) == transferred
            and all(
                _count(item.group("count")) == _count(item.group("buyer_count"))
                and item.group("nominal") == nominal
                and item.group("currency").upper() == currency
                for item in allocations
            )
            and before - transferred == remaining
            and match.group("remaining_nominal") == nominal
        ):
            rule_id = "fr.persons.organization_multi_share_transfer.v1"
            seller = match.group("seller").strip()
            events = [_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, uid=match.group("seller_uid"),
                role="associée", extra={
                    "action": "shares_transferred", "shares_before": before,
                    "shares_transferred": transferred, "shares_count": remaining,
                    "share_nominal": nominal, "currency": currency,
                },
            )]
            for item in allocations:
                count = _count(item.group("count"))
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, item.group("buyer"),
                    place=item.group("place"), role=(
                        "associée" if item.group("feminine") else "associé"
                    ), extra={
                        "action": "shares_received", "counterparty": seller,
                        "registry_id": item.group("registry_id"),
                        "country": item.group("country").strip(),
                        "new_associate": True, "shares_received": count,
                        "shares_count": count, "share_nominal": nominal,
                        "currency": currency, "signing_authority": False,
                    },
                ))
            return events, ""

    match = _FR_MANAGER_SHARE_TRANSFER.fullmatch(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        before = _count(match.group("before"))
        remaining = _count(match.group("remaining"))
        if (
            before - transferred == remaining
            and match.group("nominal") == match.group("remaining_nominal")
        ):
            rule_id = "fr.persons.manager_share_transfer.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            values = {
                "share_nominal": match.group("nominal"),
                "currency": match.group("currency").upper(),
            }
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé-gérant", extra={
                        "action": "shares_transferred", "counterparty": buyer,
                        "shares_before": before, "shares_transferred": transferred,
                        "shares_count": remaining, **values,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé", signing=(
                        "Einzelunterschrift" if match.group("buyer_signing") else None
                    ), extra={
                        "action": "shares_received", "counterparty": seller,
                        "origin": match.group("origin").strip(), "new_associate": True,
                        "shares_received": transferred, "shares_count": transferred,
                        **values,
                    },
                ),
            ], ""

    match = _DE_PARTNERSHIP_CONTINUED_AS_SOLE_TRADER.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_deleted", "de.text.partnership_continued_as_sole_trader.v1", {
                "reason": "partner_exit", "dissolved": True,
                "departed_partner": match.group("departed").strip(),
                "company_extinguished": True, "business_continued": True,
                "continuing_owner": match.group("continuing").strip(),
                "successor_legal_form": "sole_proprietorship",
                "source_legal_form": "Einzelkaufmann",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
            },
        )], ""

    match = _DE_MISSING_REGISTRY_ID_CORRECTED_TYPO.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.missing_registry_id_corrected_typo.v1", {
                "action": "registry_identifier_completed",
                "name": match.group("name").strip(),
                "registry_id": match.group("registry_id"),
                "entry": match.group("entry"), "notice": match.group("notice"),
                "notice_date": _iso_date(match.group("notice_date")),
                "source_typo": "wurdte",
            },
        )], ""

    match = _DE_LLC_EQUITY_CAPITAL_INCREASE_AND_TRANSFORMATION.fullmatch(leftover)
    if match and _money(match.group("capital")) == (
        _count(match.group("shares")) * _money(match.group("share_nominal"))
    ):
        rule_id = "de.text.llc_equity_capital_increase_and_transformation.v1"
        currency = match.group("currency").upper()
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "share_capital", "action": "increased",
                    "to": match.group("capital"), "currency": currency,
                    "from_omitted_in_source": True,
                    "financing_source": "freely_disposable_equity",
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
                    "liabilities": match.group("liabilities"),
                    "currency": currency, "shares_issued": _count(match.group("shares")),
                    "share_kind": "Namenaktien",
                    "share_nominal": match.group("share_nominal"),
                    "shareholder_count": 1,
                },
            ),
        ], ""

    match = _FR_FEMALE_MANAGER_SHARE_TRANSFER_AND_SIGNING.fullmatch(leftover)
    if match and (
        _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and match.group("nominal") == match.group("buyer_nominal")
    ):
        rule_id = "fr.persons.female_manager_share_transfer_and_signing.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        values = {
            "shares_count": _count(match.group("transferred")),
            "share_nominal": match.group("nominal"),
            "currency": match.group("currency").upper(),
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associée-gérante", extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_transferred": values["shares_count"],
                    "share_nominal": values["share_nominal"],
                    "currency": values["currency"],
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé", signing="Einzelunterschrift", extra={
                    "action": "shares_received_and_signing_granted",
                    "counterparty": seller, "origin": match.group("origin").strip(),
                    "new_associate": True, "shares_received": values["shares_count"],
                    **values,
                },
            ),
        ], ""

    match = _FR_AUDITOR_CORRECTED_WITH_NOTICE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.auditor_corrected_with_notice.v1"
        reference = {
            "action": "publication_corrected", "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_ref": match.group("notice_ref"),
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group("previous_name"),
                uid=match.group("previous_uid"), role="organe de révision", extra={
                    **reference, "replacement": match.group("name").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), uid=match.group("uid"),
                role="organe de révision", extra={
                    **reference, "replaces": match.group("previous_name").strip(),
                },
            ),
        ], ""

    return [], leftover
