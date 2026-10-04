from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_DE_AUDITOR_RENAMED_SAME_UID = re.compile(
    r"^Eingetragene Person geändert:\s*(?P<previous_name>.+?)\s*"
    r"\((?P<previous_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"(?P<role>Revisionsstelle),\s*neue Firma:\s*(?P<name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_APPEAL_SUSPENDED_WITH_HISTORY = re.compile(
    r"^(?P<authority>Der Abteilungspräsident der .+?)\s+hat mit Entscheid vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+der gegen die Konkurseröffnung "
    r"erhobenen Beschwerde aufschiebende Wirkung zuerkannt\.\s*"
    r"\[gestrichen:\s*Über die Inhaberin dieses Einzelunternehmens ist mit "
    r"Entscheid des\s+(?P<bankruptcy_court>.+?)\s+vom\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<bankruptcy_time>\d{1,2}\.\d{2})\s+Uhr,\s*der Konkurs eröffnet worden\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_COMMITTEE_MEMBERS = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s*(?P<place1>[^,.;]+),\s*"
    r"(?P<country1>[A-Z]{2,3}),\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s*(?P<place2>[^,.;]+),\s*et\s*"
    r"(?P<name3>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin3>[^,.;]+),\s*à\s*(?P<place3>[^,.;]+),\s*"
    r"(?P<country3>[A-Z]{2,3}),\s*sont membres du comité"
    r"(?P<collective>\s+avec signature collective à deux)?\.?$",
    re.I | re.UNICODE,
)
_FR_CORPORATE_ASSOCIATE_TRANSFER_TO_THREE = re.compile(
    r"^(?P<seller>.+?)\s*\((?P<seller_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+par\s+(?P<count1>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal1>[\d'.]+)\s+à\s+(?P<buyer1>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*à\s*"
    r"(?P<place1>[^,.;]+),\s*par\s+(?P<count2>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal2>[\d'.]+)\s+à\s+(?P<buyer2>.+?)\s*"
    r"\((?P<registry2>[^)]+)\),\s*à\s*(?P<place2>.+?),\s*et par\s+"
    r"(?P<count3>[\d']+)\s+parts de CHF\s+(?P<nominal3>[\d'.]+)\s+à\s+"
    r"(?P<buyer3>.+?)\s*\((?P<registry3>[^)]+)\),\s*au\s*"
    r"(?P<place3>.+?),\s*les trois nouveaux associés,\s*chacun avec "
    r"respectivement\s+(?P<repeat1>[\d']+),\s*(?P<repeat2>[\d']+)\s+et\s+"
    r"(?P<repeat3>[\d']+)\s+parts de CHF\s+(?P<repeat_nominal>[\d'.]+);\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ERRONEOUS_DELETION_CANCELLED_ON_REQUEST = re.compile(
    r"^La radiation ayant été opérée à tort,\s*elle est annulée à la demande "
    r"de l['’]interressée\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_ROLE_AND_SIGNING_CHANGES = re.compile(
    r"^Le membre du conseil\s+(?P<vice_president>[^,.;]+),\s*nommé "
    r"vice-président,\s*signe désormais collectivement à deux\.\s*"
    r"La membre du conseil\s+(?P<former_vice_president>[^,.;]+),\s*"
    r"jusqu['’]ici vice-présidente,\s*n['’]exerce plus la signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_AND_PRESIDENT_APPOINTMENT = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s*(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{1,3}),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"nommé en outre gérant président(?P<individual>\s+avec signature individuelle)?"
    r"\s*\.?(?:\s+Par conséquent,)?\s*"
    r"(?P=seller)\s+est maintenant associé pour\s+(?P<remaining>[\d']+)\s+"
    r"parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_HEAD_OFFICE_CAPITAL_WITH_PAYMENT_HISTORY = re.compile(
    r"^Kapital Hauptsitz neu:\s*(?P<currency>[A-Z]{3})\s+"
    r"(?P<total>[\d'.]+);\s*Liberierung:\s*(?P=currency)\s+"
    r"(?P<paid>[\d'.]+)\s*\[bisher:\s*Aktienkapital:\s*(?P=currency)\s+"
    r"(?P<previous_total>[\d'.]+);\s*Liberierung:\s*(?P=currency)\s+"
    r"(?P<previous_paid>[\d'.]+)\]\.?$",
    re.I | re.UNICODE,
)
_DE_SUPPORTING_DOCUMENT_CORRECTED = re.compile(
    r"^\[Der Beleg wurde berichtigt\.\]\.?$", re.I | re.UNICODE
)
_DE_DECEASED_OWNER_ESTATE_LIQUIDATION = re.compile(
    r"^Der Inhaber ist gestorben\.\s*Über den Nachlass ist mit Verfügung des\s+"
    r"(?P<authority>.+?)\s+vom\s+(?P<date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<time>\d{1,2}\.\d{2})\s+Uhr,\s*die konkursamtliche Liquidation "
    r"eröffnet worden\.?$",
    re.I | re.UNICODE,
)
_DE_COOPERATIVE_NOMINAL_REDUCTION_UNDERBALANCE = re.compile(
    r"^Anteilscheine neu:\s*(?P<new>[\d'.]+)\s*\[bisher:\s*"
    r"(?P<currency>[A-Z]{3})\s+(?P<previous>[\d'.]+)\]\.\s*Mit Beschluss der "
    r"Generalversammlung vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+wird der "
    r"Nennwert der Anteilscheine zu\s+(?P=currency)\s+(?P<repeated_previous>[\d'.]+)\s+"
    r"zur Beseitigung einer Unterbilanz auf\s+(?P=currency)\s+"
    r"(?P<repeated_new>[\d'.]+)\s+herabgesetzt\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_PROPRIETOR_TRANSFER_SHARES_CLAIM_DELETION = re.compile(
    r"^Transfert de patrimoine:\s*Selon contrat du\s+"
    r"(?P<date>\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|"
    r"septembre|octobre|novembre|décembre)\s+\d{4}),\s*le titulaire a transféré "
    r"des actifs pour CHF\s+(?P<assets>[\d'.]+)\s+et des passifs envers les "
    r"tiers pour CHF\s+(?P<liabilities>[\d'.]+)\s+à\s+(?P<recipient>.+?),\s*"
    r"à\s+(?P<place>[^()]+?)\s*\((?P<canton>[^)]+)\)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*Contre-prestation:\s*"
    r"(?P<shares>[\d']+)\s+actions de CHF\s+(?P<nominal>[\d'.]+)\s+et "
    r"créance de CHF\s+(?P<claim>[\d'.]+)\.\s*L['’]entreprise individuelle "
    r"est radiée par suite de transfert de patrimoine\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_BRANCH_IDENTIFIERS = re.compile(
    r"^Nouveau numéro d['’]identification des succursales à\s+"
    r"(?P<place1>[^(),.;]+)\s*\((?P<uid1>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"(?P<place2>[^(),.;]+)\s*\((?P<uid2>CHE-\d{3}\.\d{3}\.\d{3})\)\s+et\s+"
    r"(?P<place3>[^(),.;]+)\s*\((?P<uid3>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_NAME_CORRECTED = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^(),.;]+)\s*\(et non pas\s+(?P<previous_name>[^(),.;]+)\)\s+"
    r"est administratrice(?P<individual>\s+avec signature individuelle)?\.?$",
    re.I | re.UNICODE,
)
_FR_CAPITAL_ENTRY_SUPPLEMENTED_BASIC = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée par la rubrique suivante:\s*"
    r"Capital:\s*(?P<currency>[A-Z]{3})\s+(?P<capital>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_AUTHORIZATION_ADJUSTED = re.compile(
    r"^Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+den Beschluss über die Ermächtigung "
    r"einer genehmigten Kapitalerhöhung vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+gemäss näherer Umschreibung "
    r"in den Statuten angepasst\.?$",
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
    day, month, year = raw.strip().lower().split()
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


def extract_parser188_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 188."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_AUDITOR_RENAMED_SAME_UID.fullmatch(leftover)
    if match and match.group("previous_uid") == match.group("uid"):
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.auditor_renamed_same_uid.v1",
            match.group("name"), uid=match.group("uid"), role=match.group("role"),
            extra={
                "action": "company_name_changed",
                "previous_name": match.group("previous_name").strip(),
                "previous_uid": match.group("previous_uid"),
            },
        )], ""

    match = _DE_BANKRUPTCY_APPEAL_SUSPENDED_WITH_HISTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_appeal_suspended_with_history.v1", {
                "kind": "bankruptcy_effect_suspended",
                "action": "suspended_on_appeal",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "bankruptcy_time": match.group("bankruptcy_time").replace(".", ":"),
                "bankruptcy_court": match.group("bankruptcy_court").strip(),
                "previous_bankruptcy_entry_removed": True,
            },
        )], ""

    match = _FR_THREE_COMMITTEE_MEMBERS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.three_committee_members.v1"
        events = []
        for index in (1, 2, 3):
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
                place=match.group(f"place{index}"), role="membre du comité",
                signing=(
                    "Kollektivunterschrift zu zweien"
                    if match.group("collective") else None
                ),
                extra=extra,
            ))
        return events, ""

    match = _FR_CORPORATE_ASSOCIATE_TRANSFER_TO_THREE.fullmatch(leftover)
    if match:
        counts = [_count(match.group(f"count{index}")) for index in (1, 2, 3)]
        repeats = [_count(match.group(f"repeat{index}")) for index in (1, 2, 3)]
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        remaining = _count(match.group("remaining"))
        nominals = {
            match.group("nominal"), match.group("nominal1"),
            match.group("nominal2"), match.group("nominal3"),
            match.group("repeat_nominal"), match.group("remaining_nominal"),
        }
        if counts == repeats and sum(counts) == transferred and before - transferred == remaining and len(nominals) == 1:
            rule_id = "fr.persons.corporate_associate_transfer_to_three.v1"
            seller = match.group("seller").strip()
            events = [_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, uid=match.group("seller_uid"),
                role="associé", extra={
                    "action": "shares_transferred",
                    "shares_before": before,
                    "shares_transferred": transferred,
                    "shares_count": remaining,
                    "share_nominal": match.group("nominal"),
                    "currency": "CHF",
                },
            )]
            buyer_data = (
                (1, match.group("origin1"), None),
                (2, None, match.group("registry2")),
                (3, None, match.group("registry3")),
            )
            for index, origin, registry_id in buyer_data:
                extra = {
                    "action": "shares_received",
                    "counterparty": seller,
                    "new_associate": True,
                    "shares_received": counts[index - 1],
                    "shares_count": counts[index - 1],
                    "share_nominal": match.group("nominal"),
                    "currency": "CHF",
                }
                if origin:
                    extra["origin"] = origin.strip()
                if registry_id:
                    extra["registry_id"] = registry_id
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"buyer{index}"),
                    place=match.group(f"place{index}"), role="associé", extra=extra,
                ))
            return events, ""

    if _FR_ERRONEOUS_DELETION_CANCELLED_ON_REQUEST.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.erroneous_deletion_cancelled_on_request.v1", {
                "kind": "registration_reinstated", "action": "reinstated",
                "reason": "erroneous_deletion", "requested_by_affected_party": True,
            },
        )], ""

    match = _FR_BOARD_ROLE_AND_SIGNING_CHANGES.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.board_role_and_signing_changes.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("vice_president"),
                role="vice-président", signing="Kollektivunterschrift zu zweien",
                extra={"action": "role_and_signing_changed", "previous_role": "membre du conseil"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id,
                match.group("former_vice_president"), role="membre du conseil",
                extra={
                    "action": "signing_revoked",
                    "previous_role": "vice-présidente",
                    "previous_signing": "signature sociale",
                    "signing_revoked": True,
                },
            ),
        ], ""

    match = _FR_MANAGER_TRANSFER_AND_PRESIDENT_APPOINTMENT.fullmatch(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        if transferred == buyer_count and len({
            match.group("nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }) == 1:
            rule_id = "fr.persons.manager_transfer_and_president_appointment.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé",
                    extra={
                        "action": "shares_transferred",
                        "counterparty": buyer,
                        "shares_transferred": transferred,
                        "shares_count": _count(match.group("remaining")),
                        "share_nominal": match.group("nominal"), "currency": "CHF",
                        "previous_role": "associé-gérant",
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé-gérant président",
                    signing=("Einzelunterschrift" if match.group("individual") else None),
                    extra={
                        "action": "appointed_and_shares_received",
                        "counterparty": seller,
                        "origin": match.group("origin").strip(),
                        "country": match.group("country"),
                        "new_associate": True,
                        "shares_received": buyer_count,
                        "shares_count": buyer_count,
                        "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                    },
                ),
            ], ""

    match = _DE_HEAD_OFFICE_CAPITAL_WITH_PAYMENT_HISTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.head_office_capital_payment_history.v1", {
                "kind": "head_office_share_capital", "action": "changed",
                "currency": match.group("currency").upper(),
                "from_total": match.group("previous_total"),
                "to_total": match.group("total"),
                "from_paid": match.group("previous_paid"),
                "to_paid": match.group("paid"),
            },
        )], ""

    if _DE_SUPPORTING_DOCUMENT_CORRECTED.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.supporting_document_corrected.v1", {
                "kind": "supporting_document", "action": "corrected",
            },
        )], ""

    match = _DE_DECEASED_OWNER_ESTATE_LIQUIDATION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.deceased_owner_estate_liquidation.v1", {
                "kind": "estate_bankruptcy_liquidation", "action": "opened",
                "owner_deceased": True,
                "date": _iso_date(match.group("date")),
                "time": match.group("time").replace(".", ":"),
                "authority": match.group("authority").strip(),
            },
        )], ""

    match = _DE_COOPERATIVE_NOMINAL_REDUCTION_UNDERBALANCE.fullmatch(leftover)
    if match and (
        match.group("previous") == match.group("repeated_previous")
        and match.group("new") == match.group("repeated_new")
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.cooperative_nominal_reduction_underbalance.v1", {
                "kind": "cooperative_share_nominal_reduction",
                "action": "reduced",
                "decision_date": _iso_date(match.group("date")),
                "from_nominal": match.group("previous"),
                "to_nominal": match.group("new"),
                "currency": match.group("currency").upper(),
                "reason": "eliminate_underbalance",
            },
        )], ""

    match = _FR_SOLE_PROPRIETOR_TRANSFER_SHARES_CLAIM_DELETION.fullmatch(leftover)
    if match and (
        _amount(match.group("assets")) - _amount(match.group("liabilities"))
        == _count(match.group("shares")) * _amount(match.group("nominal"))
        + _amount(match.group("claim"))
    ):
        rule_id = "fr.text.sole_proprietor_transfer_shares_claim_deletion.v1"
        common = {
            "agreement_date": _french_date(match.group("date")),
            "recipient": match.group("recipient").strip(),
            "recipient_place": match.group("place").strip(),
            "recipient_canton": match.group("canton"),
            "recipient_uid": match.group("uid"),
        }
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", rule_id, {
                    **common, "source_kind": "sole_proprietor",
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "liabilities_kind": "third_party_liabilities",
                    "currency": "CHF",
                    "consideration_kind": "shares_and_claim",
                    "consideration_shares_count": _count(match.group("shares")),
                    "consideration_share_nominal": match.group("nominal"),
                    "consideration_claim": match.group("claim"),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_deleted", rule_id, {
                    **common, "reason": "asset_transfer", "action": "deleted",
                },
            ),
        ], ""

    match = _FR_THREE_BRANCH_IDENTIFIERS.fullmatch(leftover)
    if match:
        rule_id = "fr.text.three_branch_identifiers.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id, {
                    "action": "identifier_assigned",
                    "place": match.group(f"place{index}").strip(),
                    "branch_uid": match.group(f"uid{index}"),
                },
            )
            for index in (1, 2, 3)
        ], ""

    match = _FR_ADMINISTRATOR_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_name_corrected.v1",
            match.group("name"), role="administratrice",
            signing=("Einzelunterschrift" if match.group("individual") else None),
            extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_CAPITAL_ENTRY_SUPPLEMENTED_BASIC.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.capital_entry_supplemented_basic.v1", {
                "kind": "share_capital", "action": "publication_supplemented",
                "capital": match.group("capital"),
                "currency": match.group("currency").upper(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _DE_AUTHORIZED_CAPITAL_AUTHORIZATION_ADJUSTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_authorization_adjusted.v1", {
                "kind": "authorized_capital_clause", "action": "modified",
                "decision_date": _iso_date(match.group("date")),
                "previous_decision_date": _iso_date(match.group("previous_date")),
                "details_in_statutes": True,
            },
        )], ""

    return [], text
