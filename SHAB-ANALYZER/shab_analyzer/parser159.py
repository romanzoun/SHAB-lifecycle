from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_WITH_HISTORY = re.compile(
    r"^L['’]assemblée générale a modifié une clause statutaire relative à une "
    r"augmentation conditionnelle du capital\s*\(selon décision du\s+"
    r"(?P<day1>\d{1,2})\s+(?P<month1>[a-zéûô]+)\s+(?P<year1>\d{4}),\s*"
    r"modifiée le\s+(?P<day2>\d{1,2})\s+(?P<month2>[a-zéûô]+)\s+"
    r"(?P<year2>\d{4})\)\s*par décision du\s+(?P<day3>\d{1,2})\s+"
    r"(?P<month3>[a-zéûô]+)\s+(?P<year3>\d{4})\.\s*"
    r"Pour les détails,\s*voir les statuts\.?$",
    re.I | re.UNICODE,
)
_DE_DISSOLUTION_LIQUIDATOR_APPOINTED_WITH_ADDRESS = re.compile(
    r"^Die Gesellschaft ist laut Beschluss der Generalversammlung vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+aufgelöst\.\s*"
    r"Die Liquidation wird unter der Firma:\s*(?P<liq_name>.+?)\s+durchgeführt\.\s*"
    r"Eingetragene Person geändert:\s*(?P<name>[^,]+),\s*(?P<previous>.+?),\s*"
    r"neu\s+(?P<new_role>[^,]+),\s*(?P<new_title>[^,]+),\s*Liquidator,\s*"
    r"(?P<new_signing>[^.]+)\.\s*Liquidationsadresse:\s*(?P<address>.+)$",
    re.I | re.UNICODE,
)
_FR_BRANCH_REGISTERED_AT = re.compile(
    r"^Inscription de la succursale de\s+(?P<place>.+?)\s+"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+au registre du commerce du canton "
    r"d[eu]\s+(?P<register_canton>.+?)\s+\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>[\d/]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_ADDITIONAL_ADDRESSES_BATCH_WITH_DUPLICATE_MARKER = re.compile(
    r"^\]\.\s*"
    r"Weitere Adresse:\s*(?P<new1>[^\[]+?)\s*\[bisher:\s*"
    r"(?:Weitere Geschäftsadresse:\s*)?(?P<old1>[^\]]+?)\.?\]\.\s*"
    r"Weitere Adresse:\s*(?P<new2>[^\[]+?)\s*\[bisher:\s*"
    r"(?:Weitere Adresse:\s*)?(?P<old2>[^\]]+?)\.?\]\.\s*"
    r"\[bisher:\s*(?:Weitere Adresse:\s*)?(?P<dup_old>[^\]]+?)\.?\]\.\s*"
    r"Weitere Adresse:\s*(?P<new3>[^\[]+?)\s*\[bisher:\s*"
    r"(?:Weitere Adresse:\s*)?(?P<old3>[^\]]+?)\.?\]\.?$",
    re.I | re.UNICODE,
)
_IT_BANKRUPTCY_SUSPENSION_REVOKED_REACTIVATED = re.compile(
    r"^\[radiati:\s*La procedura di fallimento è stata sospesa per mancanza di "
    r"attivo con decreto della\s+(?P<previous_authority>.+?)\s+del\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\.\s*(?P<deletion_warning>.+?)\]\.\s*"
    r"Con decreto della\s+(?P<authority>.+?)\s+del\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+la sospensione del fallimento per "
    r"mancanza di attivo è stata revocata\.\s*"
    r"La procedura di fallimento è riattivata\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_PREVIOUS_PLACE_MALFORMED_BRACKET = re.compile(
    r"^\[bisher:\s*(?P<place>[^(]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\]\.?$",
    re.I | re.UNICODE,
)
_FR_OFFICIAL_DECISION_NAME_CHANGED = re.compile(
    r"^Par suite de décision officielle,\s*(?P<previous_name>[^,.;]+?)\s+"
    r"porte désormais le nom de\s+(?P<name>[^,.;]+?)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_BOARD_MEMBERS_DE_ET_A_NO_SIGNATURE = re.compile(
    r"^(?P<name1>[^,.;]+),\s*de et à\s+(?P<place1>[^,.;]+),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>.+?),\s*"
    r"sont membres du conseil d['’]administration;\s*"
    r"ils n['’]exercent pas la signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATION_NO_LONGER_HAS_ADDRESS_AT_SEAT = re.compile(
    r"^L['’]association ne dispose plus d['’]adresse à son siège statutaire\.?$",
    re.I | re.UNICODE,
)
_FR_LIQUIDATOR_APPOINTED_AND_FIVE_MANAGERS_SIGNATURE_REVOKED = re.compile(
    r"^L['’]?associé-gérant président\s+(?P<liquidator>[^,.;]+),\s*"
    r"dont la signature est radiée,\s*est nommé liquidateur\s*"
    r"La signature des associés-gérants\s+(?P<name1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*(?P<name3>[^,.;]+),\s*(?P<name4>[^,.;]+)\s+et\s+"
    r"(?P<name5>[^,.;]+),\s*est radiée\.?$",
    re.I | re.UNICODE,
)
_FR_RECTIFICATION_ORIGIN_CORRECTED_WITH_NOTICE = re.compile(
    r"^Rectification:\s*l['’]inscription\s*n°\s*(?P<entry>\d+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+Id\s+(?P<notice_id>\d+)\)\s+"
    r"est rectifiée dans ce sens que l['’]origine correcte est\s+"
    r"(?P<origin>.+?)\s*\(et non pas\s+(?P<previous_origin>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PRESIDENT_RELOCATED_AND_SECRETARY_APPOINTED = re.compile(
    r"^Administration:\s*(?P<name1>[^,.;]+),\s*maintenant domicilié(?:e)? à\s+"
    r"(?P<place1>[^,.;]+),\s*(?P<country1>[A-Z]{1,3}),\s*(?P<role1>président),"
    r"\s*et\s+(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"(?P<role2>secrétaire),\s*lesquels signent collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_DE_AUDIT_OPT_OUT_DECLARATION_DELETED_NEW_AUDITOR = re.compile(
    r"^Die Erklärung vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+über den "
    r"Verzicht auf die eingeschränkte Revision ist gelöscht\.\s*"
    r"Neue Revisionsstelle:\s*(?P<name>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),"
    r"\s*in\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_PERSON_CORRECTION_INCOMPLETE_INFO_TR_TEXT = re.compile(
    r"^Mit dem SHAB Nr\.\s*(?P<issue>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten TR-Text\s*"
    r"(?P<entry>\d+/\d{4})\s+wurden im bisher Text nicht die vollständigen "
    r"Angaben aufgeführt\.\s*Korrekt wäre\s+(?P<name>[^,.;]+,\s*[^,.;]+),\s*"
    r"von\s+(?P<origin>[^,.;]+),\s*in\s+(?P<place>.+?)\s+mit\s+"
    r"(?P<signing>Kollektivunterschrift zu zweien)\s*\[bisher:\s*"
    r"(?P<previous_role>[^,\]]+),\s*mit\s+(?P<previous_signing>[^,\]]+),\s*"
    r"in\s+(?P<previous_place>[^\]]+)\]$",
    re.I | re.UNICODE,
)
_FR_IDENTITY_ERROR_BANKRUPTCY_NULLIFIED_HOMONYM_RESTORED = re.compile(
    r"^Par suite d['’]une erreur de personne,\s*l['’]inscription de la "
    r"faillite de la succession répudiée du titulaire de l['’]entreprise "
    r"est nulle et non avenue parce que concernant un homonyme;\s*"
    r"l['’]inscription est rétablie comme ci-devant\s*\(FOSC\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*(?P<notice_id>[\d/]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MEMBERS_APPOINTED_CONTINUE_COLLECTIVE_SIGNING = re.compile(
    r"^(?P<name1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+),\s*nommés membres du "
    r"conseil d['’]administration,\s*continuent à signer collectivement à "
    r"deux\.?$",
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


def _fr_date(day: str, month: str, year: str) -> str:
    return f"{int(year):04d}-{_FR_MONTHS[month.lower()]:02d}-{int(day):02d}"


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


def extract_parser159_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 159."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_WITH_HISTORY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.conditional_capital_clause_changed_with_history.v1",
            {
                "kind": "conditional_capital_clause",
                "action": "changed",
                "decision_date": _fr_date(
                    match.group("day3"), match.group("month3"), match.group("year3")
                ),
                "introduced_date": _fr_date(
                    match.group("day1"), match.group("month1"), match.group("year1")
                ),
                "amended_date": _fr_date(
                    match.group("day2"), match.group("month2"), match.group("year2")
                ),
                "details_in_statutes": True,
            },
        ))

    match = _DE_DISSOLUTION_LIQUIDATOR_APPOINTED_WITH_ADDRESS.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.dissolution_by_general_assembly_with_liquidator.v1",
            {
                "kind": "dissolution",
                "action": "dissolved",
                "authority": "Generalversammlung",
                "decision_date": _iso_date(match.group("date")),
                "liquidation_name": match.group("liq_name").strip(),
            },
        ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.dissolution_officer_role_changed_to_liquidator.v1",
            match.group("name"),
            role=f"{match.group('new_role').strip()}, {match.group('new_title').strip()}",
            signing=match.group("new_signing").strip(),
            extra={
                "action": "appointed_liquidator",
                "previous": match.group("previous").strip(),
            },
        ))
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "de.text.liquidation_address_noted.v1",
            {
                "kind": "liquidation_address",
                "action": "changed",
                "to": match.group("address").strip(),
            },
        ))

    match = _FR_BRANCH_REGISTERED_AT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "fr.text.branch_registered_at.v1",
            {
                "action": "registered",
                "place": match.group("place").strip(),
                "branch_uid": match.group("uid"),
                "register_canton": match.group("register_canton").strip(),
                "source_notice_date": _iso_date(match.group("notice_date")),
                "source_notice_id": match.group("notice_id"),
            },
        ))

    match = _DE_ADDITIONAL_ADDRESSES_BATCH_WITH_DUPLICATE_MARKER.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.additional_addresses_batch_with_duplicate_marker.v1"
        for new_key, old_key in (("new1", "old1"), ("new2", "old2"), ("new3", "old3")):
            events.append(_event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", rule_id,
                {
                    "kind": "additional_address",
                    "action": "changed",
                    "to": match.group(new_key).strip(),
                    "from": match.group(old_key).strip(),
                },
            ))

    match = _IT_BANKRUPTCY_SUSPENSION_REVOKED_REACTIVATED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.bankruptcy_suspension_revoked_reactivated.v1",
            {
                "kind": "bankruptcy_reopened",
                "action": "suspension_revoked",
                "decision_date": _iso_date(match.group("date")),
                "authority": match.group("authority").strip(),
                "previous_state": "suspended_for_lack_of_assets",
                "previous_decision_date": _iso_date(match.group("previous_date")),
                "previous_authority": match.group("previous_authority").strip(),
                "previous_deletion_warning": match.group("deletion_warning").strip(),
            },
        ))

    match = _DE_BRANCH_PREVIOUS_PLACE_MALFORMED_BRACKET.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_previous_place_malformed_bracket.v1",
            {
                "action": "previous_place_noted",
                "previous_place": match.group("place").strip(),
                "previous_uid": match.group("uid"),
                "source_bracket_malformed": True,
            },
        ))

    match = _FR_OFFICIAL_DECISION_NAME_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.official_decision_name_changed.v1",
            match.group("name"),
            extra={
                "action": "name_changed",
                "reason": "official_decision",
                "previous_name": match.group("previous_name").strip(),
            },
        ))

    match = _FR_TWO_BOARD_MEMBERS_DE_ET_A_NO_SIGNATURE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_board_members_appointed_no_signature.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="membre du conseil d'administration",
                extra={
                    "action": "appointed", "heimat": match.group("place1").strip(),
                    "without_signature": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="membre du conseil d'administration",
                extra={
                    "action": "appointed", "heimat": match.group("origin2").strip(),
                    "without_signature": True,
                },
            ),
        ])

    match = _FR_ASSOCIATION_NO_LONGER_HAS_ADDRESS_AT_SEAT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.association_no_address_at_seat.v1",
            {
                "kind": "no_legal_domicile",
                "scope": "association_seat",
                "raw": match.group(0).strip(),
            },
        ))

    match = _FR_LIQUIDATOR_APPOINTED_AND_FIVE_MANAGERS_SIGNATURE_REVOKED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.liquidator_appointed_and_five_managers_signature_revoked.v1"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("liquidator"),
            role="associé-gérant, président",
            extra={"action": "appointed_liquidator", "signature_revoked": True},
        ))
        for key in ("name1", "name2", "name3", "name4", "name5"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(key),
                role="associé-gérant",
                extra={"action": "signature_revoked"},
            ))

    match = _FR_RECTIFICATION_ORIGIN_CORRECTED_WITH_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.rectification_origin_corrected_with_notice.v1",
            {
                "action": "origin_corrected",
                "origin": match.group("origin").strip(),
                "previous_origin": match.group("previous_origin").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        ))

    match = _FR_ADMINISTRATION_PRESIDENT_RELOCATED_AND_SECRETARY_APPOINTED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_president_relocated_and_secretary_appointed.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role=match.group("role1"),
                signing="collectivement à deux",
                extra={"action": "relocated", "country": match.group("country1")},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role=match.group("role2"),
                signing="collectivement à deux",
                extra={"action": "appointed", "origin": match.group("origin2").strip()},
            ),
        ])

    match = _DE_AUDIT_OPT_OUT_DECLARATION_DELETED_NEW_AUDITOR.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "auditor_changed", "de.text.audit_opt_out_declaration_deleted_new_auditor.v1",
            {
                "kind": "audit_opt_out",
                "action": "deleted",
                "declaration_date": _iso_date(match.group("date")),
                "new_auditor": match.group("name").strip(),
                "new_auditor_uid": match.group("uid"),
                "new_auditor_place": match.group("place").strip(),
            },
        ))

    match = _DE_PERSON_CORRECTION_INCOMPLETE_INFO_TR_TEXT.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.correction_incomplete_info_tr_text.v1",
            match.group("name"),
            place=match.group("place"), signing=match.group("signing"),
            extra={
                "action": "correction_completed",
                "origin": match.group("origin").strip(),
                "previous_role": match.group("previous_role").strip(),
                "previous_signing": match.group("previous_signing").strip(),
                "previous_place": match.group("previous_place").strip(),
                "source_notice": f"SHAB Nr. {match.group('issue')}",
                "notice_date": _iso_date(match.group("notice_date")),
                "tr_text_entry": match.group("entry"),
            },
        ))

    match = _FR_IDENTITY_ERROR_BANKRUPTCY_NULLIFIED_HOMONYM_RESTORED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.identity_error_bankruptcy_nullified_homonym_restored.v1",
            {
                "kind": "bankruptcy_nullified",
                "scope": "repudiated_estate",
                "action": "nullified_identity_error",
                "reason": "homonym",
                "registry_entry_restored": True,
                "previous_notice_date": _iso_date(match.group("notice_date")),
                "previous_notice_id": match.group("notice_id"),
            },
        ))

    match = _FR_TWO_MEMBERS_APPOINTED_CONTINUE_COLLECTIVE_SIGNING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_members_appointed_continue_collective_signing.v1"
        for key in ("name1", "name2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(key),
                role="membre du conseil d'administration",
                signing="collectivement à deux",
                extra={"action": "appointed", "signing_continues": True},
            ))

    return events, re.sub(r"\s+", " ", leftover).strip(" .,;")
