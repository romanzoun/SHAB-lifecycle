from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_DE_FIRST_SUPPLEMENT_DOCUMENT_OMITTED = re.compile(
    r"^,?\s*bei ersten Nachtrag im SHAB Nr\.\s*N\s*(?P<issue>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten TR-Eintrag Nr\.\s*N\s*"
    r"(?P<entry>[\d']+)\s+vom\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"wurde der Beleg versehentlich nicht genommen\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_APPOINTED_DIRECTOR_INDIVIDUAL = re.compile(
    r"^L['’]associé\s+(?P<name>[^,.;]+)\s+est nommé\s+(?P<role>directeur)\s+"
    r"et engage désormais la société par sa\s+(?P<signing>signature individuelle)\.?$",
    re.I | re.UNICODE,
)
_FR_OMITTED_FOUNDING_ASSET_ACQUISITION = re.compile(
    r"^Lors de sa fondation,\s*la société a omis de déclarer la reprise de biens "
    r"envisagée suivante qui a été réalisée selon contrat du\s+"
    r"(?P<date1>\d{2}\.\d{2}\.\d{4})\s+respectivement du\s+"
    r"(?P<date2>\d{2}\.\d{2}\.\d{4}):\s*"
    r"(?P<count1>[\d']+)\s+actions de CHF\s+(?P<nominal1>[\d'.]+)\s+au porteur "
    r"entièrement libérées de\s+(?P<company1>.+?)\s*"
    r"\((?P<uid1>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"pour le prix de CHF\s+(?P<price1>[\d'.]+);\s*"
    r"(?P<count2>[\d']+)\s+actions de CHF\s+(?P<nominal2>[\d'.]+)\s+au porteur "
    r"entièrement libérées de\s+(?P<company2>.+?)\s*"
    r"\((?P<uid2>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"pour le prix de CHF\s+(?P<price2>[\d'.]+);\s*"
    r"(?P<count3>[\d']+)\s+actions de CHF\s+(?P<nominal3>[\d'.]+)\s+au porteur "
    r"entièrement libérées de\s+(?P<company3>.+?)\s*"
    r"\((?P<uid3>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+(?P<place3>[^,.;]+),\s*"
    r"d['’]une valeur de CHF\s+(?P<value3>[\d'.]+)\s+ainsi que des actifs "
    r"d['’]une valeur de CHF\s+(?P<other_assets>[\d'.]+)\s+et des passifs "
    r"d['’]une valeur de CHF\s+(?P<liabilities>[\d'.]+)\s+sans autre contrepartie\.?$",
    re.I | re.UNICODE,
)
_FR_REGISTERED_SHARE_STRUCTURE_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le capital-actions "
    r"est divisé en\s+(?P<count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*avec restrictions quant à la transmissibilité selon "
    r"statuts\s*\(et non\s+(?P<previous_count>[\d']+)\s+actions "
    r"nominatives de CHF\s+(?P<previous_nominal>[\d'.]+)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_INTRODUCED = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"eine genehmigte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten "
    r"beschlossen\.?$",
    re.I | re.UNICODE,
)
_DE_DOMICILE_SUPPLEMENTED_WITH_REFERENCES = re.compile(
    r"^Mit im SHAB vom\s+(?P<notice_date>\d{2}\.\d{2}\.\d{2})\s+publiziertem "
    r"TR-Eintrag vom\s+(?P<entry_date>\d{2}\.\d{2}\.\d{2})\s+wurde bei\s+"
    r"(?P<name>[^,.;]+,\s*[^,.;]+)\s+der Wohnort\s+(?P<place>[^,.;]+)\s+"
    r"nachgetragen,\s*welcher bei ihrem im SHAB vom\s+"
    r"(?P<original_notice_date>\d{2}\.\d{2}\.\d{2})\s+publizierten Neueintrag "
    r"mit TR vom\s+(?P<original_entry_date>\d{2}\.\d{2}\.\d{2})\s+nicht erfasst wurde\.?$",
    re.I | re.UNICODE,
)
_FR_ASSET_TRANSFER_RECIPIENT_BEFORE_PLACE = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré des actifs pour CHF\s+"
    r"(?P<assets>[\d'.]+)\s+et des passifs envers les tiers pour CHF\s+"
    r"(?P<liabilities>[\d'.]+),\s*à\s+"
    r"(?P<recipient>(?!la société\b)[^,]+?)\s+à\s+"
    r"(?P<place>[^(),.;]+)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ENTERPRISE_REINSTATED_CORRECTION = re.compile(
    r"^Rectificatif:\s*l['’]inscription de la radiation de l['’]entreprise ayant été "
    r"opérée par erreur,\s*l['’]entreprise est réinscrite comme ci-devant\s*"
    r"\(FOSC du\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_PROPRIETOR_REINSTATED_EX_OFFICIO = re.compile(
    r"^\[biffé:\s*(?P<previous>Raison radiée par suite de cessation d['’]activité\.)\]\s*\.\s*"
    r"L['’]entreprise individuelle a été radiée par erreur\.\s*"
    r"Elle est réinscrite d['’]office\.?$",
    re.I | re.UNICODE,
)
_IT_COMPANY_BANKRUPTCY_EFFECT_SUSPENDED = re.compile(
    r"^Con decreto del\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"(?P<authority>.+?)\s+ha accordato effetto sospensivo al reclamo inoltrato "
    r"contro la decisione di apertura del fallimento della\s+"
    r"(?P<bankruptcy_court>.+?)\s+del\s+(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"L['’]iscrizione nel registro di commercio relativa al fallimento viene "
    r"pertanto cancellata\.\s*\[radiati:\s*(?P<previous>La società è stata dichiarata "
    r"in fallimento.+?a far tempo dal\s+(?P<effective_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"alle ore\s+(?P<effective_time>\d{1,2}:\d{2})\.)\]\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_FR_MANAGER_FOUR_SHARE_TRANSFERS = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+détient désormais\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+par suite "
    r"de cession de\s+(?P<count1>[\d']+)\s+parts de CHF\s+(?P<nominal1>[\d'.]+)\s+"
    r"à\s+(?P<buyer1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*nouvel associé-gérant et président pour\s+"
    r"(?P<buyer_count1>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal1>[\d'.]+)\s+"
    r"avec signature individuelle,\s*de\s+(?P<count2>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal2>[\d'.]+)\s+à\s+"
    r"(?P<buyer2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*nouvelle associée pour\s+"
    r"(?P<buyer_count2>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal2>[\d'.]+),\s*"
    r"de\s+(?P<count3>[\d']+)\s+parts de CHF\s+(?P<nominal3>[\d'.]+)\s+à\s+"
    r"(?P<buyer3>[^,.;]+),\s*de\s+(?P<origin3>[^,.;]+),\s*à\s+"
    r"(?P<place3>[^,.;]+),\s*(?P<country3>[A-Z]),\s*nouvelle associée pour\s+"
    r"(?P<buyer_count3>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal3>[\d'.]+),\s*"
    r"et de\s+(?P<count4>[\d']+)\s+parts de CHF\s+(?P<nominal4>[\d'.]+)\s+à\s+"
    r"(?P<buyer4>[^,.;]+),\s*de\s+(?P<origin4>[^,.;]+),\s*à\s+"
    r"(?P<place4>[^,.;]+),\s*(?P<country4>[A-Z]),\s*nouvel associé pour\s+"
    r"(?P<buyer_count4>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal4>[\d'.]+),\s*"
    r"tous trois sans signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_DELETED_AFTER_HEAD_OFFICE = re.compile(
    r"^La succursale est radiée par suite de la radiation du siège principal suite "
    r"à la clôture de la procédure de faillite au\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_CAPITAL_SUPPLEMENT_WITH_NOTICE_ID = re.compile(
    r"^Complément à l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+(?P<notice_id>\d+)\):\s*"
    r"Capital social:\s*CHF\s+(?P<total>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_COOPERATIVE_LIABILITY_ENTRY_REMOVED = re.compile(
    r"^Haftung/Nachschusspflicht neu:\s*"
    r"\[(?P<reason1>Streichung des Eintrags aufgrund geänderter "
    r"Eintragungsvorschriften\.)\]\s*"
    r"\[gestrichen:\s*(?P<previous>Haftung:\s*ohne persönliche Haftung)\]\.\s*"
    r"Pflichten neu:\s*(?P<obligations>.+?)\.\s*"
    r"\[(?P<reason2>Streichung des Eintrags aufgrund geänderter "
    r"Eintragungsvorschriften\.)\]\s*"
    r"\[bisher:\s*Pflichten:\s*(?P<previous_obligations>.+?)\]\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_CORRECTED = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est corrigée en ce sens que "
    r"l['’]organe de révision est\s+(?P<name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+(?P<place>[^,.;]+)\s+"
    r"et non pas\s+(?P<previous_name>.+?)\s*"
    r"\((?P<previous_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<previous_place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    if len(year) == 2:
        year = f"20{year}"
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _money(raw: str) -> Decimal:
    return Decimal(raw.rstrip(".").replace("'", ""))


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


def extract_parser202_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 202."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_FIRST_SUPPLEMENT_DOCUMENT_OMITTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.first_supplement_document_omitted.v1", {
                "action": "missing_document_recorded",
                "issue": match.group("issue"),
                "notice_date": _iso_date(match.group("notice_date")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_ASSOCIATE_APPOINTED_DIRECTOR_INDIVIDUAL.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_appointed_director_individual.v1",
            match.group("name"), role=match.group("role"),
            signing="Einzelunterschrift", extra={"action": "appointed"},
        )], ""

    match = _FR_OMITTED_FOUNDING_ASSET_ACQUISITION.fullmatch(leftover)
    if match:
        acquisitions = [
            {
                "company": match.group(f"company{index}").strip(),
                "uid": match.group(f"uid{index}"),
                "place": match.group(f"place{index}").strip(),
                "shares_count": _count(match.group(f"count{index}")),
                "share_nominal": match.group(f"nominal{index}"),
                "share_kind": "bearer",
                "fully_paid": True,
                **(
                    {"price": match.group(f"price{index}")}
                    if index in (1, 2)
                    else {"value": match.group("value3")}
                ),
            }
            for index in (1, 2, 3)
        ]
        if (
            _money(match.group("value3")) + _money(match.group("other_assets"))
            == _money(match.group("liabilities"))
        ):
            return [_event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "fr.text.omitted_founding_asset_acquisition.v1", {
                    "kind": "intended_asset_acquisition",
                    "action": "declared_after_formation",
                    "agreement_dates": [
                        _iso_date(match.group("date1")),
                        _iso_date(match.group("date2")),
                    ],
                    "acquisitions": acquisitions,
                    "other_assets": match.group("other_assets"),
                    "liabilities": match.group("liabilities"),
                    "other_consideration": False,
                    "currency": "CHF",
                },
            )], ""

    match = _FR_REGISTERED_SHARE_STRUCTURE_CORRECTED.fullmatch(leftover)
    if match and (
        _count(match.group("count")) * _money(match.group("nominal"))
        == _count(match.group("previous_count"))
        * _money(match.group("previous_nominal"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.registered_share_structure_corrected.v2", {
                "kind": "share_structure", "action": "publication_corrected",
                "shares_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"),
                "share_kind": "actions nominatives",
                "transfer_restricted": True,
                "previous_shares_count": _count(match.group("previous_count")),
                "previous_share_nominal": match.group("previous_nominal"),
                "currency": "CHF", "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _DE_AUTHORIZED_CAPITAL_INTRODUCED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_introduced.v3", {
                "kind": "authorized_capital_clause", "action": "introduced",
                "decision_date": _iso_date(match.group("date")),
                "basis": "statutes",
            },
        )], ""

    match = _DE_DOMICILE_SUPPLEMENTED_WITH_REFERENCES.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.domicile_supplemented_with_references.v1",
            match.group("name"), place=match.group("place"), extra={
                "action": "domicile_supplemented",
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "original_entry_date": _iso_date(match.group("original_entry_date")),
                "original_notice_date": _iso_date(match.group("original_notice_date")),
            },
        )], ""

    match = _FR_ASSET_TRANSFER_RECIPIENT_BEFORE_PLACE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.asset_transfer_recipient_before_place.v1", {
                "date": _iso_date(match.group("date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party",
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration": match.group("consideration"),
                "currency": "CHF",
            },
        )], ""

    match = _FR_ENTERPRISE_REINSTATED_CORRECTION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.enterprise_reinstated_correction.v1", {
                "kind": "registration_reinstated", "action": "reinstated",
                "reason": "erroneous_deletion",
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_SOLE_PROPRIETOR_REINSTATED_EX_OFFICIO.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.sole_proprietor_reinstated_ex_officio.v1", {
                "kind": "registration_reinstated", "action": "reinstated",
                "scope": "sole_proprietorship", "reason": "erroneous_deletion",
                "ex_officio": True, "previous": match.group("previous").strip(),
            },
        )], ""

    match = _IT_COMPANY_BANKRUPTCY_EFFECT_SUSPENDED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.company_bankruptcy_effect_suspended_entry_removed.v1", {
                "kind": "bankruptcy_effect_suspended", "scope": "company",
                "decision_date": _iso_date(match.group("decision_date")),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "bankruptcy_effective_date": _iso_date(match.group("effective_date")),
                "bankruptcy_effective_time": match.group("effective_time"),
                "authority": match.group("authority").strip(),
                "bankruptcy_court": match.group("bankruptcy_court").strip(),
                "bankruptcy_entry_removed": True,
                "previous": match.group("previous").strip(),
            },
        )], ""

    match = _FR_MANAGER_FOUR_SHARE_TRANSFERS.fullmatch(leftover)
    if match:
        counts = [_count(match.group(f"count{index}")) for index in (1, 2, 3, 4)]
        buyer_counts = [
            _count(match.group(f"buyer_count{index}")) for index in (1, 2, 3, 4)
        ]
        nominals = {
            match.group("nominal"),
            *(match.group(f"nominal{index}") for index in (1, 2, 3, 4)),
            *(match.group(f"buyer_nominal{index}") for index in (1, 2, 3, 4)),
        }
        if counts == buyer_counts and len(nominals) == 1:
            rule_id = "fr.persons.manager_four_share_transfers.v1"
            seller = match.group("seller").strip()
            buyers = [match.group(f"buyer{index}").strip() for index in (1, 2, 3, 4)]
            common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
            events = [_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant", extra={
                    "action": "shares_transferred", "counterparties": buyers,
                    "shares_before": _count(match.group("seller_count")) + sum(counts),
                    "shares_transferred": sum(counts),
                    "shares_count": _count(match.group("seller_count")), **common,
                },
            )]
            roles = [
                "associé-gérant et président", "associée", "associée", "associé",
            ]
            for index in (1, 2, 3, 4):
                extra = {
                    "action": "appointed_and_shares_received", "counterparty": seller,
                    "shares_received": counts[index - 1],
                    "shares_count": buyer_counts[index - 1],
                    "origin": match.group(f"origin{index}").strip(), **common,
                }
                if index > 1:
                    extra["without_signature"] = True
                if index in (3, 4):
                    extra["country"] = match.group(f"country{index}")
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"buyer{index}"),
                    place=match.group(f"place{index}"), role=roles[index - 1],
                    signing="Einzelunterschrift" if index == 1 else None, extra=extra,
                ))
            return events, ""

    match = _FR_BRANCH_DELETED_AFTER_HEAD_OFFICE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "fr.text.branch_deleted_after_head_office_bankruptcy.v1", {
                "action": "deleted", "reason": "head_office_deleted_after_bankruptcy",
                "bankruptcy_closed_date": _iso_date(match.group("date")),
            },
        )], ""

    match = _FR_SHARE_CAPITAL_SUPPLEMENT_WITH_NOTICE_ID.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.share_capital_supplement_notice_id.v1", {
                "kind": "share_capital", "action": "publication_supplemented",
                "total": match.group("total"), "currency": "CHF",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        )], ""

    match = _DE_COOPERATIVE_LIABILITY_ENTRY_REMOVED.fullmatch(leftover)
    if match:
        rule_id = "de.text.cooperative_liability_entry_removed.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id, {
                    "kind": "member_liability", "action": "entry_removed",
                    "previous": match.group("previous").strip(),
                    "reason": "changed_registration_rules",
                    "duplicate_removal_note": (
                        match.group("reason1") == match.group("reason2")
                    ),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id, {
                    "kind": "member_obligations", "action": "changed",
                    "obligations": match.group("obligations").strip(),
                    "previous_obligations": match.group("previous_obligations").strip(),
                },
            ),
        ], ""

    match = _FR_AUDITOR_CORRECTED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.auditor_corrected.v1"
        reference = {
            "action": "publication_corrected", "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group("previous_name"),
                place=match.group("previous_place"), uid=match.group("previous_uid"),
                role="organe de révision", extra={**reference, "replacement": match.group("name").strip()},
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
