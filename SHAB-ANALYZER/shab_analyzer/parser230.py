from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_LIMITED_AUDIT_WAIVED_EFFECTIVE_FISCAL_YEAR = re.compile(
    r"^Die Gesellschaft verzichtet ab dem Geschäftsjahr,\s*das am\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4})\s+beginnt,\s*"
    r"auf eine eingeschränkte Revision\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_NAME_TRANSLATIONS_ADDED_PAIR = re.compile(
    r"^Nouvelle traduction de la raison:\s*\((?P<german>[^()]+)\)\s*"
    r"\((?P<english>[^()]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_REMOVED_DIRECTOR_TYPO = re.compile(
    r"^Perosnne radiée:\s*(?P<name>[^,.;]+),\s*"
    r"(?P<role>directrice),\s*(?P<signing>signature collective à deux)\s+"
    r"avec un administrateur\.?$",
    re.I | re.UNICODE,
)
_DE_NEVER_BOARD_MEMBER_ENTRY_DELETED = re.compile(
    r"^Berichtigung der Eintragung Nr\.\s*(?P<entry>[\d']+)\s+vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(SHAB vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\):\s*(?P<name>[^,.;]+)\s+war nie Mitglied des "
    r"Verwaltungsrats,\s*sein Eintrag ist gelöscht\.?$",
    re.I | re.UNICODE,
)
_FR_DOMICILE_CHANGED_BARE = re.compile(
    r"^(?P<name>[^,.;]+?)\s+est à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SHAREHOLDER_COMMUNICATIONS_SUPPLEMENTED = re.compile(
    r"^Complément:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée en ce sens que les "
    r"communications aux actionnaires s['’]opèrent désormais par\s+"
    r"(?P<mode>.+?)\.?$",
    re.I | re.UNICODE,
)
_DE_SOLE_PROPRIETOR_DELETED_BUSINESS_CEASED = re.compile(
    r"^Der Geschäftsbetrieb hat aufgehört\.\s*Das Einzelunternehmen wird "
    r"gemäss\s+(?P<legal_basis>Art\.\s*159 Abs\.\s*5 lit\.\s*a HRegV)\s+"
    r"von Amtes wegen gelöscht\.?$",
    re.I | re.UNICODE,
)
_FR_FOUR_LIQUIDATORS_TWO_RESTRICTED_PAIRS = re.compile(
    r"^(?P<name1>[^,.;]+?)\s+et\s+(?P<name2>[^,.;]+?)\s+sont nommés "
    r"liquidateurs\s+(?:avec signature collective à deux,\s*)?"
    r"toutefois pas entre eux\.\s*"
    r"(?P<name3>[^,.;]+?)\s+et\s+(?P<name4>[^,.;]+?)\s+sont nommés "
    r"liquidateurs avec signature collective à deux,\s*"
    r"toutefois pas entre eux\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_CORRECTED_COLLECTIVE_FROM_INDIVIDUAL = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\)\s+est rectifiée en ce sens "
    r"que\s+(?P<name>[^,.;]+?)\s+signe collectivement à deux\s*"
    r"\(et non individuellement\)\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_BANKRUPTCY_REVOKED = re.compile(
    r"^Par décision du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>.+?)\s+a annulé la faillite de la société prononcée le\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4});\s*l['’]inscription est "
    r"rétablie comme ci-devant\s*\(FOSC No\s+(?P<notice_number>\d+)\s+du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*page\s+"
    r"(?P<notice_page>\d+),\s*publ\.\s+(?P<notice_id>[\d']+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_MEMBER_SIGNING_PAIR_CHANGED = re.compile(
    r"^La membre\s+(?P<name1>[^,.;]+),\s*(?P<role1>présidente)\s+a désormais "
    r"la signature individuelle;\s*ses pouvoirs sont modifiés dans ce sens\.\s*"
    r"La membre\s+(?P<name2>[^,.;]+)\s+n['’]exerce plus la signature sociale;\s*"
    r"ses pouvoirs sont radiés\.?$",
    re.I | re.UNICODE,
)
_DE_ERRONEOUS_DELETION_REVOKED_NOTICE = re.compile(
    r"^Die Gesellschaft wurde irrtümlich mit Tagesregistereintrag vom\s+"
    r"(?P<deletion_entry_date>\d{2}\.\d{2}\.\d{4})\s+gelöscht\.\s*"
    r"Die Eintragung der Gesellschaft bleibt bestehen und die Publikation im "
    r"SHAB Nr\.\s*(?P<notice_number>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+wird in allen Teilen widerrufen\.\s*"
    r"\[bisher:\s*(?P<previous>.+)\]\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_FR_PROCURATION_NAME_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que la procuration "
    r"collective à deux est conférée à\s+(?P<name>[^()]+?)\s*"
    r"\(et non\s+(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_ADMINISTRATOR_CONTINUES_NO_DOMICILE = re.compile(
    r"^(?P<name>[^,.;]+),\s*jusqu['’]ici président,\s*reste seul "
    r"administrateur et continue à signer individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_DISSOLUTION_ADDRESS_PERSON_NAME_CORRECTED = re.compile(
    r"^Korrekte Adresse:\s*(?P<street>[^,.;]+),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<locality>[^.;]+)\.\s*"
    r"Die Gesellschaft wird gemäss Beschluss der Gesellschafterversammlung vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+aufgelöst\.\s*"
    r"Die Liquidation wird unter der Firma:\s*(?P<liquidation_name>.+? in Liquidation)\s+"
    r"durchgeführt\.\s*Eingetragene Person geändert:\s*"
    r"(?P<previous_name>[^,.;]+),\s*korrekterweise\s+(?P<name>[^,.;]+),\s*"
    r"von\s+(?P<origin>[^,.;]+),\s*Gesellschafter,\s*"
    r"(?P<shares>[\d']+)\s+Stammanteil(?:e)? zu CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*Geschäftsführer,\s*Einzelunterschrift,\s*"
    r"neu Gesellschafter,\s*(?P=shares)\s+Stammanteil(?:e)? zu CHF\s+"
    r"(?P=nominal),\s*Geschäftsführer,\s*Liquidator,\s*Einzelunterschrift\.?$",
    re.I | re.UNICODE,
)
_FR_PROCURATION_REVOKED_CROSS_LANGUAGE = re.compile(
    r"^La procuration de\s+(?P<name>[^,.;]+?)\s+est radiée\.?$",
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


def extract_parser230_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 230."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_LIMITED_AUDIT_WAIVED_EFFECTIVE_FISCAL_YEAR.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "audit_requirement_changed",
            "de.text.limited_audit_waived_effective_fiscal_year.v1", {
                "kind": "limited_audit_waiver", "action": "declared",
                "effective_fiscal_year_start": _iso_date(match.group("effective_date")),
                "limited_audit_waived": True,
            },
        )], ""

    match = _FR_COMPANY_NAME_TRANSLATIONS_ADDED_PAIR.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_name_changed", "fr.text.company_name_translations_added_pair.v1", {
                "kind": "company_name_translations", "action": "translations_added",
                "translations": [
                    match.group("german").strip(), match.group("english").strip()
                ],
            },
        )], ""

    match = _FR_REMOVED_DIRECTOR_TYPO.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_removed", "fr.persons.removed_director_typo_perosnne.v1",
            match.group("name"), role=match.group("role"),
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "removed", "signing_revoked": True,
                "signing_restriction": "avec un administrateur",
                "source_heading_typo": "Perosnne radiée",
            },
        )], ""

    match = _DE_NEVER_BOARD_MEMBER_ENTRY_DELETED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_removed", "de.persons.never_board_member_entry_deleted.v1",
            match.group("name"), role="Mitglied des Verwaltungsrats", extra={
                "action": "erroneous_entry_removed", "never_held_role": True,
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        )], ""

    match = _FR_DOMICILE_CHANGED_BARE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.domicile_changed_bare.v1",
            match.group("name"), place=match.group("place"),
            extra={"action": "domicile_changed"},
        )], ""

    match = _FR_SHAREHOLDER_COMMUNICATIONS_SUPPLEMENTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "fr.text.shareholder_communications_supplemented.v1", {
                "kind": "communications", "action": "supplemented",
                "audience": "shareholders", "to": match.group("mode").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _DE_SOLE_PROPRIETOR_DELETED_BUSINESS_CEASED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_deleted", "de.text.sole_proprietor_deleted_business_ceased_art159.v1", {
                "reason": "business_operations_ceased", "scope": "sole_proprietor",
                "action": "deleted_ex_officio",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
            },
        )], ""

    match = _FR_FOUR_LIQUIDATORS_TWO_RESTRICTED_PAIRS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.four_liquidators_two_restricted_pairs.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="liquidateur", signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_liquidator",
                    "signing_group": "group_1" if index <= 2 else "group_2",
                    "cannot_sign_with": match.group(
                        f"name{2 if index == 1 else 1 if index == 2 else 4 if index == 3 else 3}"
                    ).strip(),
                },
            )
            for index in range(1, 5)
        ], ""

    match = _FR_SIGNING_CORRECTED_COLLECTIVE_FROM_INDIVIDUAL.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed",
            "fr.persons.signing_corrected_collective_from_individual.v1",
            match.group("name"), signing="Kollektivunterschrift zu zweien", extra={
                "action": "publication_corrected",
                "previous_signing": "Einzelunterschrift",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
            },
        )], ""

    match = _FR_COMPANY_BANKRUPTCY_REVOKED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.company_bankruptcy_revoked_registry_restored.v1", {
                "kind": "bankruptcy_revoked", "action": "judgment_set_aside",
                "scope": "company", "registry_entry_restored": True,
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "previous_notice_number": match.group("notice_number"),
                "previous_notice_date": _iso_date(match.group("notice_date")),
                "previous_notice_page": int(match.group("notice_page")),
                "previous_notice_id": match.group("notice_id").replace("'", ""),
            },
        )], ""

    match = _FR_MEMBER_SIGNING_PAIR_CHANGED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.member_signing_pair_changed.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name1"),
                role="membre, présidente", signing="Einzelunterschrift", extra={
                    "action": "signing_changed", "powers_modified": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name2"),
                role="membre", extra={
                    "action": "revoked", "signing_authority": False,
                    "powers_revoked": True,
                },
            ),
        ], ""

    match = _DE_ERRONEOUS_DELETION_REVOKED_NOTICE.fullmatch(leftover)
    if match:
        rule_id = "de.text.erroneous_deletion_revoked_notice.v1"
        reference = {
            "deletion_entry_date": _iso_date(match.group("deletion_entry_date")),
            "notice_number": match.group("notice_number"),
            "notice_date": _iso_date(match.group("notice_date")),
        }
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "registration_reinstated", "action": "reinstated",
                    "reason": "erroneous_deletion", "registry_entry_remains": True,
                    "previous_deleted_text": match.group("previous").strip(),
                    **reference,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", rule_id, {
                    "kind": "erroneous_deletion", "action": "notice_revoked",
                    **reference,
                },
            ),
        ], ""

    match = _FR_PROCURATION_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.procuration_name_corrected.v1",
            match.group("name"), role="fondé de procuration",
            signing="Kollektivprokura zu zweien", extra={
                "action": "name_corrected_and_procuration_granted",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_SOLE_ADMINISTRATOR_CONTINUES_NO_DOMICILE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.sole_administrator_continues_no_domicile.v1",
            match.group("name"), role="seul administrateur",
            signing="Einzelunterschrift", extra={
                "action": "role_changed", "previous_role": "président",
                "signing_continues": True,
            },
        )], ""

    match = _DE_DISSOLUTION_ADDRESS_PERSON_NAME_CORRECTED.fullmatch(leftover)
    if match:
        rule_id = "de.text.dissolution_address_person_name_corrected.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", rule_id, {
                    "action": "corrected", "street": match.group("street").strip(),
                    "postal_code": match.group("postal_code"),
                    "locality": match.group("locality").strip(),
                    "full_address": (
                        f"{match.group('street').strip()}, "
                        f"{match.group('postal_code')} {match.group('locality').strip()}"
                    ),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "dissolution", "action": "dissolved",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "decision_body": "shareholders_meeting",
                    "liquidation_name": match.group("liquidation_name").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                role="Gesellschafter, Geschäftsführer, Liquidator",
                signing="Einzelunterschrift", extra={
                    "action": "name_corrected_and_appointed_liquidator",
                    "previous_name": match.group("previous_name").strip(),
                    "origin": match.group("origin").strip(),
                    "shares_count": _count(match.group("shares")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                    "previous_roles": ["Gesellschafter", "Geschäftsführer"],
                },
            ),
        ], ""

    match = _FR_PROCURATION_REVOKED_CROSS_LANGUAGE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed",
            "fr.persons.procuration_revoked_cross_language.v1",
            match.group("name"), role="fondé de procuration", extra={
                "action": "revoked", "previous_signing": "procuration",
                "procuration_revoked": True,
            },
        )], ""

    return [], leftover
