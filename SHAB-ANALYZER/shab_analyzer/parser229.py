from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_DEFINITIVE_MORATORIUM_EXTENDED_DECISION = re.compile(
    r"^Par décision du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>.+?)\s+a prolongé le sursis concordataire définitif "
    r"jusqu['’]au\s+(?P<until>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_SOLE_PROPRIETOR_ERRONEOUS_DELETION_REVOKED = re.compile(
    r"^Das (?P<entity>Einzelunternehmen) wurde vom (?P<authority>.+?) mittels "
    r"TR-Eintrag Nr\.\s*(?P<entry>\d+) vom "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}),\s*publiziert im SHAB Nr\.\s*"
    r"(?P<notice>\d+) vom (?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"irrtümlich gelöscht\.\s*Der genannte Löschungseintrag wird deshalb "
    r"hiermit widerrufen\.\s*\[gestrichen:\s*(?P<previous>.+)\]\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_FR_ORGANIZATION_TRANSFER_TO_TWO_ASSOCIATES = re.compile(
    r"^Jusqu['’]ici titulaire de\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*l['’]associée\s+(?P<seller>.+?)\s*"
    r"\(no\s+(?P<seller_registry_id>[^)]+)\)\s+détient\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\s+"
    r"par suite de cession de\s+(?P<transferred1>[\d']+)\s+parts au gérant\s+"
    r"(?P<buyer1>[^,.;]+),\s*nouvel associé pour\s+"
    r"(?P<buyer_count1>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal1>[\d'.]+),\s*"
    r"et de\s+(?P<transferred2>[\d']+)\s+parts à\s+(?P<buyer2>[^,.;]+),\s*"
    r"de\s+(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"(?P<country2>[A-Z]{1,3}),\s*nouvelle associée pour\s+"
    r"(?P<buyer_count2>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal2>[\d'.]+),\s*"
    r"laquelle n['’]exerce pas la signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_SUSPENSIVE_EFFECT_REQUEST_GRANTED = re.compile(
    r"^La présidente de la\s+(?P<authority>.+?)\s+a admis la requête "
    r"d['’]effet suspensif le\s+(?P<decision_date>\d{1,2}\s+"
    r"[A-Za-zÀ-ÿ]+\s+\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_NAME_CORRECTED_NOTICE = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que\s+"
    r"(?!l['’]|la\s|le\s)(?P<previous_name>[^,.;]+)\s+se nomme\s+"
    r"(?!en réalité\b)(?P<name>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_AND_NAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens qu['’]une "
    r"signature collective à deux,\s*avec un administrateur,\s*a été conférée à\s+"
    r"(?P<name>[^()]+?)\s*\(et non pas\s+(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_MISSING_REGISTRY_ID_CORRECTED_ENTRY_SLASH = re.compile(
    r"^Im SHAB Nr\.\s*(?P<notice>\d+) vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten TR[ -]Eintrag\s+"
    r"(?P<entry>[\d/]+)\s+wurde irrtümlich die CH-Nummer weggelassen\.\s*"
    r"Richtig ist:\s*\[bisher:\s*(?P<name>.+?)\s*"
    r"\((?P<registry_id>CH-[\d.]+-\d)\)\]\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_NEW_ASSOCIATE_NO_COUNT = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,()]+?)\s*"
    r"\((?P<country>[^)]+)\),\s*nouvel associé(?:\s+avec\s+"
    r"(?P<buyer_signing>signature collective à deux))?\.?\s+"
    r"(?P=seller)\s+reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_COMMITTEE_TREASURER_ORIGIN_DOMICILE = re.compile(
    r"^Le membre du comité et trésorier\s+(?P<name>[^,.;]+)\s+est originaire "
    r"d['’](?P<origin>[^,.;]+),\s*domicilié à\s+(?P<place>[^,.;]+)\s+et "
    r"continue de signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_AUTHORIZED_CAPITAL_CLAUSE_INTRODUCED = re.compile(
    r"^L['’]assemblée générale a introduit une clause statutaire relative à une "
    r"augmentation autorisée du capital par décision du\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}):\s*pour les détails,\s*"
    r"voir les statuts\.?$",
    re.I | re.UNICODE,
)
_DE_LEGACY_BRANCH_REMOVED_RESIDUE = re.compile(
    r"^\]\.?\s*\[folgende Zweigniederlassung wird gelöscht\]\.?\s*"
    r"\[gestrichen:\s*(?P<place>[^()\]]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\]\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDATION_AUDIT_EXEMPTION_REVOKED_AUTHORITY_ORDER = re.compile(
    r"^Mit Verfügung vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat die "
    r"Aufsichtsbehörde ihre Verfügung vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4}),\s*mit welcher die "
    r"Stiftung von der Pflicht zur Bezeichnung einer Revisionsstelle befreit "
    r"worden ist,\s*widerrufen\.\s*\[bisher:\s*Die Stiftung wurde mit "
    r"Verfügung der Aufsichtsbehörde vom\s+"
    r"(?P<previous_text_date>\d{2}\.\d{2}\.\d{4})\s+von der Pflicht befreit,\s*"
    r"eine Revisionsstelle zu bezeichnen\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_FORMATION_ASSET_ACQUISITION_MENTION_REMOVED = re.compile(
    r"^La mention relative à la reprise de bien effectuée à la constitution "
    r"est radiée\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_CONTINUED_AFTER_HEAD_OFFICE_MERGER = re.compile(
    r"^Angaben zur ist infolge Fusion mit der\s+(?P<previous_name>.+?),\s*in\s+"
    r"(?P<previous_place>[^()]+?)\s*\(neu:\s*(?P<successor_name>.+?),\s*in\s+"
    r"(?P<successor_place>[^,()]+),\s*(?P<successor_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"erloschen\.\s*Der Geschäftsbetrieb in\s+(?P<branch_place>.+?)\s+wird "
    r"gemäss\s+(?P<legal_basis>Art\.\s*112 HRegV)\s+als Zweigniederlassung der\s+"
    r"(?P=successor_name),\s*in\s+(?P=successor_place)\s+"
    r"\((?P=successor_uid)\),\s*weitergeführt\.\s*"
    r"\[Streichung der Löschungsbemerkung bzw\. Berichtigung des im SHAB-Nr\.\s*"
    r"(?P<notice>\d+) vom\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten "
    r"TR-Eintrags Nr\.\s*(?P<entry>\d+) vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\]\.?$",
    re.I | re.UNICODE,
)
_IT_LIQUIDATION_ENDED_DELETION_BLOCKED = re.compile(
    r"^La liquidazione è terminata\.\s*La cancellazione della società non può "
    r"essere effettuata mancando il consenso dell['’]autorità fiscale federale\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_DOMICILES_CORRECTED = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name1>[^,.;]+)\s+est domicilié à\s+(?P<place1>[^,.;]+)\s+et\s+"
    r"(?P<name2>[^,.;]+)\s+est domicilié à\s+(?P<place2>[^,.;]+),\s*"
    r"(?P<country2>[A-Z]{1,3})\.?$",
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


def extract_parser229_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 229."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_DEFINITIVE_MORATORIUM_EXTENDED_DECISION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.definitive_moratorium_extended_decision.v1", {
                "kind": "composition_moratorium_extended", "action": "extended",
                "moratorium_type": "definitive",
                "decision_date": _iso_date(match.group("decision_date")),
                "until": _iso_date(match.group("until")),
                "authority": match.group("authority").strip(),
            },
        )], ""

    match = _DE_SOLE_PROPRIETOR_ERRONEOUS_DELETION_REVOKED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.sole_proprietor_erroneous_deletion_revoked.v1", {
                "kind": "registry_deletion", "action": "revoked_as_erroneous",
                "organization_kind": match.group("entity"),
                "authority": match.group("authority").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice": match.group("notice"),
                "notice_date": _iso_date(match.group("notice_date")),
                "previous_deleted_text": match.group("previous").strip(),
            },
        )], ""

    match = _FR_ORGANIZATION_TRANSFER_TO_TWO_ASSOCIATES.fullmatch(leftover)
    if match:
        before = _count(match.group("before"))
        remaining = _count(match.group("remaining"))
        transferred1 = _count(match.group("transferred1"))
        transferred2 = _count(match.group("transferred2"))
        buyer_count1 = _count(match.group("buyer_count1"))
        buyer_count2 = _count(match.group("buyer_count2"))
        if (
            before == remaining + transferred1 + transferred2
            and transferred1 == buyer_count1
            and transferred2 == buyer_count2
            and len({
                match.group("nominal"), match.group("remaining_nominal"),
                match.group("buyer_nominal1"), match.group("buyer_nominal2"),
            }) == 1
        ):
            rule_id = "fr.persons.organization_transfer_to_two_associates.v1"
            seller = match.group("seller").strip()
            buyer1 = match.group("buyer1").strip()
            buyer2 = match.group("buyer2").strip()
            common = {"currency": "CHF", "share_nominal": match.group("nominal")}
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associée", extra={
                        "action": "shares_transferred", "shares_before": before,
                        "shares_transferred": transferred1 + transferred2,
                        "shares_count": remaining,
                        "counterparties": [buyer1, buyer2],
                        "foreign_registry_id": match.group("seller_registry_id").strip(),
                        **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer1, role="associé-gérant", extra={
                        "action": "appointed_associate_and_shares_received",
                        "shares_received": transferred1, "shares_count": buyer_count1,
                        "counterparty": seller, **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer2, place=match.group("place2"),
                    role="associée", extra={
                        "action": "appointed_and_shares_received",
                        "shares_received": transferred2, "shares_count": buyer_count2,
                        "counterparty": seller, "origin": match.group("origin2").strip(),
                        "country": match.group("country2"),
                        "signing_authority": False, **common,
                    },
                ),
            ], ""

    match = _FR_SUSPENSIVE_EFFECT_REQUEST_GRANTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.suspensive_effect_request_granted.v1", {
                "kind": "suspensive_effect", "action": "granted",
                "decision_date": _french_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
            },
        )], ""

    match = _FR_PERSON_NAME_CORRECTED_NOTICE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.persons.name_corrected_notice_short.v1",
            match.group("name"), extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_SIGNING_AND_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed",
            "fr.persons.signing_and_name_corrected_with_administrator.v1",
            match.group("name"), signing="Kollektivunterschrift zu zweien", extra={
                "action": "name_corrected_and_signing_granted",
                "previous_name": match.group("previous_name").strip(),
                "signing_restriction": "avec un administrateur",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _DE_MISSING_REGISTRY_ID_CORRECTED_ENTRY_SLASH.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.missing_registry_id_corrected_entry_slash.v1", {
                "action": "registry_identifier_completed",
                "name": match.group("name").strip(),
                "registry_id": match.group("registry_id"),
                "entry": match.group("entry"),
                "notice": match.group("notice"),
                "notice_date": _iso_date(match.group("notice_date")),
            },
        )], ""

    match = _FR_MANAGER_TRANSFER_NEW_ASSOCIATE_NO_COUNT.fullmatch(leftover)
    if match:
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        remaining = _count(match.group("remaining"))
        if (
            before == transferred + remaining
            and match.group("nominal") == match.group("remaining_nominal")
        ):
            rule_id = "fr.persons.manager_transfer_new_associate_no_count.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            common = {"currency": "CHF", "share_nominal": match.group("nominal")}
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé-gérant", extra={
                        "action": "shares_transferred", "shares_before": before,
                        "shares_transferred": transferred, "shares_count": remaining,
                        "counterparty": buyer, **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé",
                    signing=(
                        "Kollektivunterschrift zu zweien"
                        if match.group("buyer_signing") else None
                    ), extra={
                        "action": "appointed_and_shares_received",
                        "shares_received": transferred, "shares_count": transferred,
                        "counterparty": seller, "origin": match.group("origin").strip(),
                        "country": match.group("country").strip(), **common,
                    },
                ),
            ], ""

    match = _FR_COMMITTEE_TREASURER_ORIGIN_DOMICILE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.committee_treasurer_origin_domicile.v1",
            match.group("name"), place=match.group("place"),
            role="membre du comité et trésorier",
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "origin_and_domicile_recorded",
                "origin": match.group("origin").strip(), "signing_continues": True,
            },
        )], ""

    match = _FR_AUTHORIZED_CAPITAL_CLAUSE_INTRODUCED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.authorized_capital_clause_introduced_colon.v1", {
                "kind": "authorized_capital_clause", "action": "introduced",
                "decision_date": _iso_date(match.group("decision_date")),
                "details_in_statutes": True,
            },
        )], ""

    match = _DE_LEGACY_BRANCH_REMOVED_RESIDUE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.legacy_branch_removed_residue.v1", {
                "action": "removed", "place": match.group("place").strip(),
                "branch_uid": match.group("uid"),
            },
        )], ""

    match = _DE_FOUNDATION_AUDIT_EXEMPTION_REVOKED_AUTHORITY_ORDER.fullmatch(leftover)
    if match and match.group("previous_decision_date") == match.group("previous_text_date"):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "audit_requirement_changed",
            "de.text.foundation_audit_exemption_revoked_authority_order.v1", {
                "kind": "auditor_appointment_exemption", "action": "revoked",
                "entity": "foundation",
                "decision_date": _iso_date(match.group("decision_date")),
                "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                "authority": "Aufsichtsbehörde", "auditor_required": True,
            },
        )], ""

    if _FR_FORMATION_ASSET_ACQUISITION_MENTION_REMOVED.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.formation_asset_acquisition_mention_removed.v1", {
                "kind": "formation_asset_acquisition_mention", "action": "removed",
            },
        )], ""

    match = _DE_BRANCH_CONTINUED_AFTER_HEAD_OFFICE_MERGER.fullmatch(leftover)
    if match:
        rule_id = "de.text.branch_continued_after_head_office_merger_correction.v1"
        reference = {
            "notice": match.group("notice"),
            "notice_date": _iso_date(match.group("notice_date")),
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
        }
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id, {
                    "action": "continued_after_head_office_merger",
                    "branch_place": match.group("branch_place").strip(),
                    "previous_head_office_name": match.group("previous_name").strip(),
                    "previous_head_office_place": match.group("previous_place").strip(),
                    "successor_name": match.group("successor_name").strip(),
                    "successor_place": match.group("successor_place").strip(),
                    "successor_uid": match.group("successor_uid"),
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                    **reference,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", rule_id, {
                    "kind": "deletion_remark", "action": "removed_and_entry_corrected",
                    **reference,
                },
            ),
        ], ""

    if _IT_LIQUIDATION_ENDED_DELETION_BLOCKED.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.liquidation_ended_deletion_blocked.v1", {
                "kind": "liquidation_ended", "deletion_blocked": True,
                "deletion_blocked_reason": "federal_tax_authority_consent_missing",
            },
        )], ""

    match = _FR_TWO_DOMICILES_CORRECTED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_domiciles_corrected_short.v1"
        reference = {
            "action": "domicile_corrected", "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), extra=reference,
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"),
                extra={**reference, "country": match.group("country2")},
            ),
        ], ""

    return [], leftover
