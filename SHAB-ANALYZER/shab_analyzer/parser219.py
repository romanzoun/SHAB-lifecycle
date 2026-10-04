from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_BANKRUPTCY_SUSPENDED_NAME_RESTORED = re.compile(
    r"^Par ordonnance du\s+(?P<order_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"(?P<authority>.+?)\s+a suspendu l['’]exécution du jugement de faillite "
    r"rendu le\s+(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"Par conséquent sa raison sociale redevient:\s*(?P<name>.+?)\.?$",
    re.I | re.UNICODE,
)
_DE_ERRONEOUS_DELETION_REINSTATED = re.compile(
    r"^Die am\s+(?P<deletion_date>\d{2}\.\d{2}\.\d{4})\s+irrtümlich "
    r"gelöschte Gesellschaft wird wieder in das Handelsregister eingetragen "
    r"und besteht entsprechend den früheren Eintragungen weiter\.?$",
    re.I | re.UNICODE,
)
_FR_ORGANIZATION_SHARE_TRANSFER = re.compile(
    r"^(?P<seller>.+?)\s*\((?P<seller_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+"
    r"a cédé\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>.+?)\s*"
    r"\((?P<buyer_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<buyer_place>[^,.;]+),\s*nouvelle associée pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"par conséquent\s+(?P=seller)\s*\((?P=seller_uid)\)\s+est maintenant "
    r"associée pour\s+(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_STATUTES_STATUS_TYPO = re.compile(
    r"^Status modifiés le\s+(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_IT_COMPANY_NAME_LIQUIDATION = re.compile(
    r"^Nuova ditta:\s*(?P<name>.+?\s+in liquidazione)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ASSOCIATE_SHARE_TRANSFER = re.compile(
    r"^(?P<seller>[^,.;]+)\s+maintenant associée pour\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"par suite de cession de\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<transfer_nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+)\s+maintenant "
    r"associé pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_CONTINUED_AFTER_HEAD_OFFICE_MERGER = re.compile(
    r"^Angaben zur ist infolge Fusion mit der\s+(?P<merged_into>.+?),\s*in\s+"
    r"(?P<merged_into_place>[^,(]+)\s*\(neu:\s*(?P<successor>.+?),\s*in\s+"
    r"(?P<successor_place>[^)]+)\)\s*\((?P<successor_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"erloschen\.\s*Der Geschäftsbetrieb in\s+(?P<branch_place>[^.]+?)\s+wird "
    r"gemäss Art\.\s*112 HRegV als Zweigniederlassung der\s+(?P=successor),\s*"
    r"in\s+(?P=successor_place)\s*\((?P=successor_uid)\),\s*weitergeführt\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_WITHOUT_SIGNATURE = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*au\s+(?P<place>[^,.;]+),\s*nouvel associé avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"sans signature\.\s*(?P=seller)\s+reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_COMMITTEE_MEMBERS_APPOINTED_LIQUIDATORS = re.compile(
    r"^(?P<name1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+),\s*membres du comité,\s*"
    r"nommés liquidateurs,\s*continuent de signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TWO_SHARE_TRANSFERS = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+),\s*maintenant domicilié à\s+"
    r"(?P<seller_place>[^,.;]+)\s*\((?P<seller_canton>[A-Z]{2})\),\s*a cédé\s+"
    r"(?P<transfer1>[\d']+)\s+parts de CHF\s+(?P<nominal1>[\d'.]+)\s+à\s+"
    r"(?P<buyer1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*(?P<country1>[A-Z]{1,3}),\s*nouvelle associée "
    r"pour\s+(?P<count1>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal1>[\d'.]+)\s+"
    r"et\s+(?P<transfer2>[\d']+)\s+parts de CHF\s+(?P<nominal2>[\d'.]+)\s+à\s+"
    r"(?P<buyer2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*(?P<country2>[A-Z]{1,3}),\s*nouvel associé pour\s+"
    r"(?P<count2>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal2>[\d'.]+)\.\s*"
    r"Suite à ces cessions,\s*l['’]associé-gérant\s+(?P=seller)\s+possède désormais\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.\s*"
    r"Les nouveaux associés n['’]exercent pas la signature sociale\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_REVOKED_SOLE_PROPRIETOR = re.compile(
    r"^Mit Verfügung vom\s+(?P<revocation_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+den Konkurs widerrufen\.\s*Infolgedessen besteht "
    r"die Einzelunternehmung entsprechend den früheren Eintragungen weiter\.\s*"
    r"\[bisher:\s*Über den Inhaber dieses Einzelunternehmens ist mit Verfügung "
    r"des\s+(?P<previous_authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+mit Wirkung ab dem\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}\.\d{2})\s+Uhr,\s*der Konkurs eröffnet worden\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_DECISION_CORRECTED_AND_ANNULLED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\)\s+est rectifiée dans ce sens que par arrêt du\s+"
    r"(?P<ruling_date>\d{2}\.\d{2}\.\d{4}),\s*(?P<authority>.+?)\s+a admis "
    r"le recours du\s+(?P<appeal_date>\d{2}\.\d{2}\.\d{4})\s+et annulé la "
    r"décision de faillite du\s+(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s*"
    r"\(et non du\s+(?P<incorrect_date>\d{2}\.\d{2}\.\d{4})\)\s+de\s+"
    r"(?P<bankruptcy_authority>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_BEARER_SHARE_CAPITAL_STRUCTURE = re.compile(
    r"^Capital-actions nouveau:\s*(?P<currency>[A-Z]{3})\s+"
    r"(?P<capital>[\d'.]+),\s*entièrement libéré,\s*divisé en\s+"
    r"(?P<count>[\d']+)\s+actions de\s+(?P=currency)\s+"
    r"(?P<nominal>[\d'.]+)\s*\(jusqu['’]ici:\s*(?P<previous_count>[\d']+)\s+"
    r"actions de\s+(?P=currency)\s+(?P<previous_nominal>[\d'.]+)\),\s*"
    r"au porteur\.?$",
    re.I | re.UNICODE,
)
_DE_TWO_BRANCH_IDENTIFIERS = re.compile(
    r"^(?P<place1>[^.()]+?)\s*\((?P<uid1>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"(?P<place2>[^.()]+?)\s*\((?P<uid2>CHE-\d{3}\.\d{3}\.\d{3})\)\s*"
    r"\[bisher:\s*(?P<previous_place>[^()\[\]]+?)\s*"
    r"\((?P<previous_registry_id>CH-[\d.]+-\d)\)\]\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATION_DISSOLVED_TWO_LIQUIDATORS = re.compile(
    r"^L['’]association est dissoute par décision de l['’]assemblée générale du\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\.\s*Liquidateurs:\s*les membres "
    r"du comité exécutif\s+(?P<name1>[^,.;]+),\s*nommé président,\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*trésorier et secrétaire,\s*lesquels continuent à "
    r"signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_CASH_PRICE_ADJUSTMENT = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von\s+"
    r"(?P<currency>[A-Z]{3})\s+(?P<assets>[\d'.]+)\s+auf die\s+"
    r"(?P<recipient>.+?),\s*in\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*Gegenleistung:\s*"
    r"(?P=currency)\s+(?P<consideration>[\d'.]+),\s*welche gemäss vertraglicher "
    r"Preisanpassungsklausel angepasst werden wird\.?$",
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
    role: str | None = None,
    signing: str | None = None,
    uid: str | None = None,
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
        signing=signing.strip() if signing else None,
        payload={
            "name": clean_name,
            "place": clean_place,
            **({"uid": uid} if uid else {}),
            **(extra or {}),
        },
    )


def extract_parser219_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 219."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_BANKRUPTCY_SUSPENDED_NAME_RESTORED.fullmatch(leftover)
    if match:
        rule_id = "fr.text.bankruptcy_suspension_name_restored.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "bankruptcy", "action": "execution_suspended",
                    "order_date": _iso_date(match.group("order_date")),
                    "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                    "authority": match.group("authority").strip(),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_name_changed", rule_id, {
                    "action": "restored_after_bankruptcy_suspension",
                    "name": match.group("name").strip(),
                },
            ),
        ], ""

    match = _DE_ERRONEOUS_DELETION_REINSTATED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.erroneous_deletion_reinstated.v1", {
                "kind": "registry_reinstatement", "action": "reinstated",
                "deletion_date": _iso_date(match.group("deletion_date")),
                "deletion_was_erroneous": True,
                "previous_registration_continues": True,
            },
        )], ""

    match = _FR_ORGANIZATION_SHARE_TRANSFER.fullmatch(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        seller_count = _count(match.group("seller_count"))
        if transferred == buyer_count:
            rule_id = "fr.persons.organization_share_transfer.v1"
            common = {"currency": "CHF", "share_nominal": match.group("nominal")}
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller,
                    uid=match.group("seller_uid"), role="associée", extra={
                        **common, "organization": True,
                        "action": "shares_transferred", "counterparty": buyer,
                        "shares_before": seller_count + transferred,
                        "shares_transferred": transferred,
                        "shares_count": seller_count,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer,
                    place=match.group("buyer_place"), uid=match.group("buyer_uid"),
                    role="associée", extra={
                        "organization": True,
                        "action": "appointed_and_shares_received",
                        "counterparty": seller, "new_associate": True,
                        "shares_received": transferred, "shares_count": buyer_count,
                        "share_nominal": match.group("buyer_nominal"),
                        "currency": "CHF",
                    },
                ),
            ], ""

    match = _FR_STATUTES_STATUS_TYPO.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.statutes_changed_status_typo.v1", {
                "action": "changed", "date": _iso_date(match.group("date")),
                "source_heading_typo": "Status",
            },
        )], ""

    match = _IT_COMPANY_NAME_LIQUIDATION.fullmatch(leftover)
    if match:
        rule_id = "it.text.company_name_liquidation.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_name_changed", rule_id, {
                    "action": "changed", "name": match.group("name").strip(),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "liquidation", "action": "liquidation_name_recorded",
                },
            ),
        ], ""

    match = _FR_TWO_ASSOCIATE_SHARE_TRANSFER.fullmatch(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        seller_count = _count(match.group("seller_count"))
        rule_id = "fr.persons.two_associate_share_transfer.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associée", extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": seller_count + transferred,
                    "shares_transferred": transferred, "shares_count": seller_count,
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, role="associé", extra={
                    "action": "shares_received", "counterparty": seller,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ], ""

    match = _DE_BRANCH_CONTINUED_AFTER_HEAD_OFFICE_MERGER.fullmatch(leftover)
    if match:
        rule_id = "de.text.branch_continued_after_head_office_merger.v1"
        common = {
            "successor": match.group("successor").strip(),
            "successor_uid": match.group("successor_uid"),
            "successor_place": match.group("successor_place").strip(),
        }
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id, {
                    "action": "head_office_extinguished_by_merger",
                    "merged_into": match.group("merged_into").strip(),
                    "merged_into_place": match.group("merged_into_place").strip(),
                    **common,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id, {
                    "action": "business_continued_as_branch",
                    "place": match.group("branch_place").strip(),
                    "legal_basis": "Art. 112 HRegV", **common,
                },
            ),
        ], ""

    match = _FR_ASSOCIATE_TRANSFER_WITHOUT_SIGNATURE.fullmatch(leftover)
    if match:
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        remaining = _count(match.group("remaining"))
        buyer_count = _count(match.group("buyer_count"))
        if before - transferred == remaining and transferred == buyer_count:
            rule_id = "fr.persons.associate_transfer_without_signature.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé-gérant", extra={
                        "action": "shares_transferred", "counterparty": buyer,
                        "shares_before": before, "shares_transferred": transferred,
                        "shares_count": remaining,
                        "share_nominal": match.group("remaining_nominal"),
                        "currency": "CHF",
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé", extra={
                        "action": "appointed_and_shares_received",
                        "counterparty": seller, "new_associate": True,
                        "without_signature": True,
                        "heimat": match.group("origin").strip(),
                        "shares_received": transferred, "shares_count": buyer_count,
                        "share_nominal": match.group("buyer_nominal"),
                        "currency": "CHF",
                    },
                ),
            ], ""

    match = _FR_COMMITTEE_MEMBERS_APPOINTED_LIQUIDATORS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.committee_members_appointed_liquidators.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role="membre du comité et liquidateur",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed_liquidator", "signing_continues": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                role="membre du comité et liquidateur",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed_liquidator", "signing_continues": True},
            ),
        ], ""

    match = _FR_MANAGER_TWO_SHARE_TRANSFERS.fullmatch(leftover)
    if match:
        transfer1 = _count(match.group("transfer1"))
        transfer2 = _count(match.group("transfer2"))
        count1 = _count(match.group("count1"))
        count2 = _count(match.group("count2"))
        if transfer1 == count1 and transfer2 == count2:
            rule_id = "fr.persons.manager_two_share_transfers.v1"
            seller = match.group("seller").strip()
            remaining = _count(match.group("remaining"))
            buyers = []
            for index, transfer, count in ((1, transfer1, count1), (2, transfer2, count2)):
                buyers.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"buyer{index}"),
                    place=match.group(f"place{index}"),
                    role="associée" if index == 1 else "associé", extra={
                        "action": "appointed_and_shares_received",
                        "counterparty": seller, "new_associate": True,
                        "without_signature": True,
                        "heimat": match.group(f"origin{index}").strip(),
                        "country": match.group(f"country{index}"),
                        "shares_received": transfer, "shares_count": count,
                        "share_nominal": match.group(f"buyer_nominal{index}"),
                        "currency": "CHF",
                    },
                ))
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller,
                    place=match.group("seller_place"), role="associé-gérant", extra={
                        "action": "domicile_changed_and_shares_transferred",
                        "canton": match.group("seller_canton"),
                        "counterparties": [
                            match.group("buyer1").strip(), match.group("buyer2").strip()
                        ],
                        "shares_before": remaining + transfer1 + transfer2,
                        "shares_transferred": transfer1 + transfer2,
                        "shares_count": remaining,
                        "share_nominal": match.group("remaining_nominal"),
                        "currency": "CHF",
                    },
                ),
                *buyers,
            ], ""

    match = _DE_BANKRUPTCY_REVOKED_SOLE_PROPRIETOR.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_revoked_sole_proprietor.v1", {
                "kind": "bankruptcy", "action": "revoked",
                "revocation_date": _iso_date(match.group("revocation_date")),
                "authority": match.group("authority").strip(),
                "organization_kind": "sole_proprietorship",
                "previous_decision_date": _iso_date(match.group("decision_date")),
                "previous_effective_date": _iso_date(match.group("effective_date")),
                "previous_effective_time": match.group("effective_time").replace(".", ":"),
                "previous_authority": match.group("previous_authority").strip(),
                "previous_registration_continues": True,
            },
        )], ""

    match = _FR_BANKRUPTCY_DECISION_CORRECTED_AND_ANNULLED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.bankruptcy_decision_correction_annulled.v1", {
                "kind": "bankruptcy", "action": "decision_annulled_on_appeal",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
                "ruling_date": _iso_date(match.group("ruling_date")),
                "appeal_date": _iso_date(match.group("appeal_date")),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "incorrect_bankruptcy_date": _iso_date(match.group("incorrect_date")),
                "authority": match.group("authority").strip(),
                "bankruptcy_authority": match.group("bankruptcy_authority").strip(),
                "publication_corrected": True,
            },
        )], ""

    match = _FR_BEARER_SHARE_CAPITAL_STRUCTURE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.bearer_share_capital_structure.v1", {
                "action": "structure_changed", "capital": match.group("capital"),
                "currency": match.group("currency").upper(), "fully_paid": True,
                "shares_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"),
                "share_kind": "actions au porteur",
                "previous_shares_count": _count(match.group("previous_count")),
                "previous_share_nominal": match.group("previous_nominal"),
            },
        )], ""

    match = _DE_TWO_BRANCH_IDENTIFIERS.fullmatch(leftover)
    if match:
        rule_id = "de.text.two_branch_identifiers.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id, {
                    "action": "identifier_recorded",
                    "place": match.group("place1").strip(),
                    "branch_uid": match.group("uid1"),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id, {
                    "action": "identifier_replaced",
                    "place": match.group("place2").strip(),
                    "branch_uid": match.group("uid2"),
                    "previous_place": match.group("previous_place").strip(),
                    "previous_registry_id": match.group("previous_registry_id"),
                },
            ),
        ], ""

    match = _FR_ASSOCIATION_DISSOLVED_TWO_LIQUIDATORS.fullmatch(leftover)
    if match:
        rule_id = "fr.text.association_dissolved_two_liquidators.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "dissolution", "action": "dissolved",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "deciding_body": "assemblée générale",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role="président du comité exécutif et liquidateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_president_and_liquidator",
                    "signing_continues": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                role="trésorier et secrétaire du comité exécutif et liquidateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_liquidator", "signing_continues": True,
                },
            ),
        ], ""

    match = _DE_ASSET_TRANSFER_CASH_PRICE_ADJUSTMENT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_cash_price_adjustment.v1", {
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"),
                "liabilities": None, "currency": match.group("currency").upper(),
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"),
                "consideration_kind": "cash", "price_adjustment_clause": True,
            },
        )], ""

    return [], leftover
