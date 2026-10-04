from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_PERSON_ORIGIN_RECTIFIED_NO_NOTICE = re.compile(
    r"^L['’]inscription\s+No\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que "
    r"l['’](?P<role>[^,.;]+?)\s+(?P<name>[^,.;]+?)\s+est originaire de\s+"
    r"(?P<origin>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_RELATED_ORGANIZATION_RENAMED = re.compile(
    r"^(?P<previous_name>.+?),\s*dont le numéro d['’]identification des "
    r"entreprises est\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"a modifié sa raison de commerce en\s+(?P<name>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_SHARE_COUNT_SUPPLEMENTED = re.compile(
    r"^L['’]inscription\s+no\.\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(publication FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+page\s+"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée en ce sens que l['’]associé\s+"
    r"(?P<name>[^,.;]+?)\s+l['’]est pour\s+(?P<count>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_HEAD_OFFICE_BANKRUPTCY_OPENING_REVOKED = re.compile(
    r"^Bemerkungen zum Hauptsitz neu:\s*Mit Beschluss vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat das\s+"
    r"(?P<authority>.+?)\s+die Verfügung des\s+(?P<court>.+?)\s+vom\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+betreffend die "
    r"Konkurseröffnung aufgehoben\.\s*Die Gesellschaft besteht entsprechend "
    r"den früheren Eintragungen weiter\.\s*\[bisher:\s*(?P<previous>.+)\]\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_DE_BOARD_ELECTION_RESOLUTIONS_NULLIFIED_NO_CHANGES = re.compile(
    r"^Mit Verfügung des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+werden die Beschlüsse der "
    r"Generalversammlung vom\s+(?P<meeting_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"über die Wahl von\s+(?P<name1>[^,.;]+?)\s+und\s+(?P<name2>[^,.;]+?)\s+"
    r"als Verwaltungsratsmitglieder für nichtig erklärt\.\s*Da die "
    r"Gesellschaft bereits selber Veränderungen angemeldet hatte,\s*führt die "
    r"Verfügung zu keinen neuen Einträgen oder Streichungen\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_SIGNING_CHANGES_WITH_REQUIRED_OFFICERS = re.compile(
    r"^Le directeur général\s+(?P<name1>[^,.;]+),\s*nommé en outre membre du "
    r"conseil d['’]administration,\s*signe désormais collectivement à deux,\s*"
    r"avec le président ou la secrétaire\.\s*La directrice\s+"
    r"(?P<name2>[^,.;]+),\s*signe désormais collectivement à deux,\s*"
    r"avec le président ou la secrétaire\.\s*Signature collective à deux,\s*"
    r"avec le président ou la secrétaire,\s*a été conférée à\s+"
    r"(?P<name3>[^,.;]+);\s*sa procuration est radiée\.?$",
    re.I | re.UNICODE,
)
_DE_SOLE_PROPRIETOR_ASSET_TRANSFER_SHARES_AND_CREDIT = re.compile(
    r"^Vermögensübertragung:\s*(?P<transferor>Der Geschäftsinhaber)\s+"
    r"überträgt gemäss Vertrag vom\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+und Passiven\s*"
    r"\(Fremdkapital\)\s+von CHF\s+(?P<liabilities>[\d'.]+(?:\s+\d+)?)\s+"
    r"auf die\s+(?P<recipient>.+?),\s*in\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*Gegenleistung:\s*"
    r"(?P<share_count>[\d']+)\s+(?P<share_kind>Namenaktien)\s+zu CHF\s+"
    r"(?P<share_nominal>[\d'.]+)\s+und Forderungsgutschrift von CHF\s+"
    r"(?P<credit>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_SUSPENSION_REVOKED = re.compile(
    r"^Gemäss Verfügung des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wird die Verfügung vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4}),\s*mit der das Konkursverfahren "
    r"mangels Aktiven eingestellt worden ist,\s*widerrufen\.\s*"
    r"\[bisher:\s*(?P<previous>.+)\]\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_DE_AUDITOR_REGISTRY_ID_REPLACED_BY_UID = re.compile(
    r"^Die Nr\.\s*(?P<registry_id>CH-[\d-]+)\s+des Revisionsorgans\s+"
    r"(?P<name>.+?)\s+in\s+(?P<place>[^,.;]+)\s+wird durch die UID-Nr\.\s*"
    r"(?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\s+ersetzt\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_WITH_PRESIDENT_OR_VICE_PRESIDENT = re.compile(
    r"^Nouveau membre du conseil de fondation avec le président ou le "
    r"vice-président:\s*(?P<name>[^,.;]+),\s*de et à\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_WITH_NET_CASH_CONSIDERATION = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+"
    r"(?P<place>[^.]+)\.\s*Gegenleistung:\s*CHF\s+"
    r"(?P<consideration>[\d']+,\s*\d+)\.?$",
    re.I | re.UNICODE,
)
_FR_AUTHORIZED_REMOVED_AND_CONDITIONAL_MODIFIED = re.compile(
    r"^Suppression de la clause statutaire d['’]augmentation autorisée du "
    r"capital-actions adoptée par l['’]assemblée générale du\s+"
    r"(?P<authorized_date>\d{2}\.\d{2}\.\d{4})\.\s*La clause d['’]augmentation "
    r"conditionnelle du capital-actions décidée par l['’]assemblée générale du\s+"
    r"(?P<conditional_date>\d{2}\.\d{2}\.\d{4})\s+a été modifiée selon "
    r"décision du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s*"
    r"\(pour les détails voir les statuts\)\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_FEMALE_ASSOCIATE = re.compile(
    r"^Nouvelle associée\s*:\s*(?P<name>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_REAL_ESTATE_ASSET_TRANSFER_NO_CONSIDERATION = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss öffentlich "
    r"beurkundetem Vermögensübertragungsvertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+(?P<property>.+?)\s+mit "
    r"Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+und Passiven\s*"
    r"\(Fremdkapital\)\s+von CHF\s+(?P<liabilities>[\d'.]+)\s+auf die\s+"
    r"(?P<recipient>.+?),\s*in\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*keine\.?$",
    re.I | re.UNICODE,
)
_DE_ERRONEOUS_STATUTES_DATE = re.compile(
    r"^\[Das Statutendatum vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"wurde irrtümlich eingetragen\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_COMPANY_NAME_TRANSLATION = re.compile(
    r"^Nouvelle traduction de la raison:\s*\((?P<translation>[^()]+)\)\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _amount(raw: str) -> str:
    return re.sub(r"(?<=[.,])\s+(?=\d)", "", raw).replace(",", ".")


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


def extract_parser161_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 161."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_PERSON_ORIGIN_RECTIFIED_NO_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.person_origin_rectified_no_notice.v1",
            {
                "kind": "person_origin",
                "action": "origin_corrected",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "name": match.group("name").strip(),
                "role": match.group("role").strip(),
                "origin": match.group("origin").strip(),
            },
        ))

    match = _FR_RELATED_ORGANIZATION_RENAMED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "fr.persons.related_organization_renamed.v1",
            match.group("name"), uid=match.group("uid"),
            extra={
                "action": "name_changed",
                "previous_name": match.group("previous_name").strip(),
            },
        ))

    match = _FR_ASSOCIATE_SHARE_COUNT_SUPPLEMENTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_share_count_supplemented.v1",
            match.group("name"), role="associé",
            extra={
                "action": "share_count_supplemented",
                "shares_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"),
                "currency": "CHF",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _DE_HEAD_OFFICE_BANKRUPTCY_OPENING_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.head_office_bankruptcy_opening_revoked.v1",
            {
                "scope": "head_office",
                "kind": "bankruptcy_opening_revoked",
                "decision_date": _iso_date(match.group("decision_date")),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "authority": match.group("authority").strip(),
                "court": match.group("court").strip(),
                "registration_continued": True,
                "previous": match.group("previous").strip(),
            },
        ))

    match = _DE_BOARD_ELECTION_RESOLUTIONS_NULLIFIED_NO_CHANGES.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed",
            "de.text.board_election_resolutions_nullified_no_changes.v1",
            {
                "kind": "board_election_resolutions",
                "action": "nullified",
                "decision_date": _iso_date(match.group("decision_date")),
                "meeting_date": _iso_date(match.group("meeting_date")),
                "authority": match.group("authority").strip(),
                "persons": [match.group("name1").strip(), match.group("name2").strip()],
                "registry_entries_changed": False,
            },
        ))

    match = _FR_THREE_SIGNING_CHANGES_WITH_REQUIRED_OFFICERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.three_signing_changes_with_required_officers.v1"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("name1"),
            role="directeur général, membre du conseil d'administration",
            signing="Kollektivunterschrift zu zweien",
            extra={"action": "appointed_and_signing_changed", "co_signs_with": "président ou secrétaire"},
        ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", rule_id, match.group("name2"),
            role="directrice", signing="Kollektivunterschrift zu zweien",
            extra={"action": "signing_changed", "co_signs_with": "président ou secrétaire"},
        ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", rule_id, match.group("name3"),
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "signing_changed",
                "co_signs_with": "président ou secrétaire",
                "previous_signing": "procuration",
                "procuration_revoked": True,
            },
        ))

    match = _DE_SOLE_PROPRIETOR_ASSET_TRANSFER_SHARES_AND_CREDIT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred",
            "de.text.sole_proprietor_asset_transfer_shares_and_credit.v1",
            {
                "transferor": match.group("transferor"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"),
                "liabilities": _amount(match.group("liabilities")),
                "liabilities_kind": "third_party_capital",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "currency": "CHF",
                "consideration_share_count": _count(match.group("share_count")),
                "consideration_share_kind": match.group("share_kind"),
                "consideration_share_nominal": match.group("share_nominal"),
                "consideration_credit": match.group("credit"),
            },
        ))

    match = _DE_BANKRUPTCY_SUSPENSION_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_suspension_revoked.v1",
            {
                "kind": "bankruptcy_proceedings_resumed",
                "action": "suspension_revoked",
                "decision_date": _iso_date(match.group("decision_date")),
                "previous_decision_date": _iso_date(match.group("previous_date")),
                "authority": match.group("authority").strip(),
                "previous": match.group("previous").strip(),
            },
        ))

    match = _DE_AUDITOR_REGISTRY_ID_REPLACED_BY_UID.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.auditor_registry_id_replaced_by_uid.v1",
            match.group("name"), place=match.group("place"), uid=match.group("uid"),
            role="Revisionsorgan",
            extra={
                "action": "identifier_changed",
                "previous_registry_id": match.group("registry_id"),
            },
        ))

    match = _FR_FOUNDATION_MEMBER_WITH_PRESIDENT_OR_VICE_PRESIDENT.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed",
            "fr.persons.foundation_member_with_president_or_vice_president.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil de fondation",
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "appointed",
                "origin": match.group("place").strip(),
                "co_signs_with": "président ou vice-président",
            },
        ))

    match = _DE_ASSET_TRANSFER_WITH_NET_CASH_CONSIDERATION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_with_net_cash_consideration.v1",
            {
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": _amount(match.group("consideration")),
                "currency": "CHF",
            },
        ))

    match = _FR_AUTHORIZED_REMOVED_AND_CONDITIONAL_MODIFIED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.authorized_removed_and_conditional_modified.v1"
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", rule_id,
            {
                "kind": "authorized_capital_clause",
                "action": "removed",
                "original_decision_date": _iso_date(match.group("authorized_date")),
            },
        ))
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", rule_id,
            {
                "kind": "conditional_capital_clause",
                "action": "modified",
                "original_decision_date": _iso_date(match.group("conditional_date")),
                "decision_date": _iso_date(match.group("decision_date")),
            },
        ))

    match = _FR_NEW_FEMALE_ASSOCIATE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.new_female_associate.v1",
            match.group("name"), place=match.group("place"), role="associée",
            extra={"action": "appointed", "origin": match.group("origin").strip()},
        ))

    match = _DE_REAL_ESTATE_ASSET_TRANSFER_NO_CONSIDERATION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred",
            "de.text.real_estate_asset_transfer_no_consideration.v1",
            {
                "kind": "real_estate",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "property": match.group("property").strip(),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": "keine",
                "gratuitous": True,
                "currency": "CHF",
            },
        ))

    match = _DE_ERRONEOUS_STATUTES_DATE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.erroneous_statutes_date.v1",
            {
                "kind": "statutes_date",
                "action": "erroneous_entry_noted",
                "erroneous_date": _iso_date(match.group("date")),
            },
        ))

    match = _FR_NEW_COMPANY_NAME_TRANSLATION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_name_changed", "fr.text.new_company_name_translation.v1",
            {
                "kind": "translation",
                "action": "added",
                "translation": match.group("translation").strip(),
            },
        ))

    return events, re.sub(r"\s+", " ", leftover).strip(" .,;")
