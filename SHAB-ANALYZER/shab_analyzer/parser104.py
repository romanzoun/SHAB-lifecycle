from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_PARTICIPATION_CAPITAL_CONDITIONAL_INCREASE = re.compile(
    r"^Augmentation conditionnelle du capital-participation,\s*fondée sur la "
    r"décision relative à l['’]octroi de droits du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.\s*Nouveau capital-participation:\s*"
    r"CHF\s+(?P<total>[\d'.]+),\s*entièrement libéré,\s*divisé en\s+"
    r"(?P<count>[\d']+)\s+bons de participation de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*nominatifs,\s*liés selon statuts\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_EXISTING_BUYER = re.compile(
    r"^L['’]associé\s+(?P<seller>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts sociales "
    r"de CHF\s+(?P<nominal>[\d'.]+)\s+à l['’]associé\s+(?P<buyer>[^,.;]+),\s*"
    r"lequel devient ainsi titulaire de\s+(?P<buyer_count>[\d']+)\s+parts "
    r"sociales de CHF\s+(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ANCILLARY_OBLIGATIONS_REMOVED_WITH_NOTICE = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(publication FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+page\s+"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée en ce sens qu['’]a a été "
    r"supprimée l['’]obligation de fournir des prestations accessoires,\s*"
    r"droits de préférence,\s*de préemption ou d['’]emption\.?$",
    re.I | re.UNICODE,
)
_DE_AUDITOR_PREVIOUS_ENTRY_NOT_REMOVED = re.compile(
    r"^\[Im Zuge des Eintrages einer Revisionsstelle wurde der bisherige "
    r"Eintrag versehentlich nicht gestrichen\]\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_UID_BEFORE_PLACE_NO_CONSIDERATION = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+auf die\s+(?P<recipient>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+"
    r"(?P<place>[^.]+)\.\s*Gegenleistung:\s*(?P<consideration>keine)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_SIGNINGS_CORRECTED = re.compile(
    r"^L['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée comme suit:\s*"
    r"(?P<name1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*(?P<role1>président)\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*d['’](?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*(?P<country2>[A-Z]{2,3}),\s*signent "
    r"collectivement à deux et non individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_AUTHORIZED_CAPITAL_INTRODUCED_INVALID_YEAR = re.compile(
    r"^L['’]assemblée générale a introduit une clause statutaire relative à une "
    r"augmentation autorisée du capital par décision du\s+"
    r"(?P<day>\d{1,2})\s+(?P<month>janvier|février|mars|avril|mai|juin|juillet|"
    r"août|septembre|octobre|novembre|décembre)\s+(?P<year>\d{3})\.\s*"
    r"Pour les détails,\s*voir les statuts\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_ADMINISTRATORS_DE_ET_A = re.compile(
    r"^Nouveaux administrateurs sans signature:\s*"
    r"(?P<name1>[^,.;]+),\s*de et à\s+(?P<place1>[^,.;]+),\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ANCILLARY_MENTION_REMOVED_SUPPLEMENT = re.compile(
    r"^L['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est complétée sur les points "
    r"suivants:\s*radiation de la mention relative aux prestations accessoires,\s*"
    r"droits de préférence,\s*de préemption ou d['’]emption selon statuts est "
    r"radiée\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_NEW_UNSIGNED_ASSOCIATE = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé sans "
    r"signature\.\s*(?P=seller)\s+reste titulaire de\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_TWO_PERSON_CHANGES_WITH_NAME_CORRECTION = re.compile(
    r"^Eingetragene Personen geändert:\s*(?P<previous_name1>[^,.;]+),\s*"
    r"(?P<previous_role1>[^,.;]+),\s*"
    r"(?P<previous_sign1>Kollektivunterschrift zu zweien),\s*neu\s+"
    r"(?P<role1>[^,.;]+),\s*(?P<sign1>Einzelunterschrift),\s*korrekterweise\s+"
    r"(?P<name1>[^;]+);\s*(?P<name2>[^,.;]+),\s*"
    r"(?P<previous_sign2>Kollektivprokura zu zweien),\s*mit\s+"
    r"(?P<previous_with>.+?),\s*neu\s+(?P<sign2>Kollektivprokura zu zweien)\s+"
    r"mit\s+(?P<with>.+?),\s*nun in\s+(?P<place>[^()]+?)\s*"
    r"\((?P<place_reason>Gemeindefusion)\)\.?$",
    re.I | re.UNICODE,
)
_FR_PROXY_REVOKED_APPOINTED_DIRECTOR = re.compile(
    r"^(?P<name>[^,.;]+),\s*dont la procuration est éteinte,\s*est "
    r"nommé(?:e)?\s+(?P<role>directeur|directrice)\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_GRANTED_DEPUTY_DIRECTOR = re.compile(
    r"^Signature collective à deux,\s*avec l['’]administrateur ou le directeur,\s*"
    r"a été conférée à\s+(?P<name>[^,.;]+),\s*nommé(?:e)?\s+"
    r"(?P<role>sous-directeur|sous-directrice);\s*sa procuration est radiée\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_NEW_ASSOCIATE_SEMICOLON = re.compile(
    r"^(?P<seller>[^,.;]+)\s+a cédé\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{1,3}),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"sans signature sociale;\s*par conséquent\s+(?P=seller)\s+est maintenant "
    r"associé pour\s+(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_DOMICILES_CORRECTED = re.compile(
    r"^L['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name1>[^,.;]+)\s+est domicilié(?:e)? à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<country1>[A-Z]{2,3}),\s*et\s+(?P<name2>[^,.;]+)\s+est "
    r"domicilié(?:e)? à\s+(?P<place2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_REGISTERED_SHARE_RESTRICTION_REMOVED_TYPO = re.compile(
    r"^Les\s+(?P<count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+ne sont désormais plus retreintes quant à la "
    r"transmissibilité\.?$",
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
        role=role,
        signing=signing,
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def _share_transfer_events(
    match: re.Match[str],
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
    rule_id: str,
    *,
    seller_role: str = "associé",
    buyer_place: str | None = None,
    buyer_extra: dict | None = None,
) -> list[Event]:
    transferred = _count(match.group("transferred"))
    groups = match.groupdict()
    seller_count = groups.get("seller_count")
    buyer_count = groups.get("buyer_count")
    return [
        _person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("seller"), role=seller_role,
            extra={
                "action": "shares_transferred",
                "counterparty": match.group("buyer").strip(),
                **(
                    {"shares_before": _count(match.group("before"))}
                    if groups.get("before") else {}
                ),
                "shares_transferred": transferred,
                **({"shares_count": _count(seller_count)} if seller_count else {}),
                "share_nominal": (
                    groups.get("seller_nominal") or match.group("nominal")
                ),
                "currency": "CHF",
            },
        ),
        _person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("buyer"), place=buyer_place,
            role="associé",
            extra={
                "action": "shares_received",
                "counterparty": match.group("seller").strip(),
                "shares_received": transferred,
                "shares_count": _count(buyer_count) if buyer_count else transferred,
                "share_nominal": groups.get("buyer_nominal") or match.group("nominal"),
                "currency": "CHF",
                **(buyer_extra or {}),
            },
        ),
    ]


def extract_parser104_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 104."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_PARTICIPATION_CAPITAL_CONDITIONAL_INCREASE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.participation_capital_conditional_increase.v1",
            {
                "kind": "conditional_participation_capital_increase",
                "decision_date": _iso_date(match.group("date")),
                "currency": "CHF", "total": match.group("total"),
                "fully_paid": True, "participation_certificates_count": _count(match.group("count")),
                "participation_certificate_nominal": match.group("nominal"),
                "registered": True, "transfer_restricted": True,
            },
        ))

    match = _FR_ASSOCIATE_TRANSFER_EXISTING_BUYER.search(leftover)
    if match:
        consume(match)
        events.extend(_share_transfer_events(
            match, publication_id, published_at, org_uid, plz, canton,
            "fr.persons.associate_transfer_existing_buyer.v1",
        ))

    match = _FR_ANCILLARY_OBLIGATIONS_REMOVED_WITH_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.ancillary_obligations_removed_with_notice.v1",
            {
                "kind": "ancillary_obligations", "action": "removed",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
                "rights_removed": ["preference", "preemption", "emption"],
            },
        ))

    match = _DE_AUDITOR_PREVIOUS_ENTRY_NOT_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.auditor_previous_entry_not_removed.v1",
            {
                "kind": "auditor_entry", "action": "previous_entry_removed",
                "reason": "previous_entry_erroneously_not_removed",
            },
        ))

    match = _DE_ASSET_TRANSFER_UID_BEFORE_PLACE_NO_CONSIDERATION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_uid_before_place_no_consideration.v1",
            {
                "date": _iso_date(match.group("date")), "assets": match.group("assets"),
                "currency": "CHF", "liabilities_transferred": False,
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration": match.group("consideration").lower(),
                "gratuitous": True,
            },
        ))

    match = _FR_TWO_SIGNINGS_CORRECTED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_signings_corrected.v1"
        reference = {
            "action": "signing_corrected", "previous_signing": "Einzelunterschrift",
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
        }
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role=match.group("role1").lower(),
                signing="Kollektivunterschrift zu zweien",
                extra={**reference, "heimat": match.group("origin1").strip()},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name2"),
                place=match.group("place2"), signing="Kollektivunterschrift zu zweien",
                extra={
                    **reference, "heimat": match.group("origin2").strip(),
                    "country": match.group("country2"),
                },
            ),
        ])

    match = _FR_AUTHORIZED_CAPITAL_INTRODUCED_INVALID_YEAR.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.authorized_capital_clause_invalid_source_year.v1",
            {
                "kind": "authorized_capital_clause", "action": "introduced",
                "decision_date_text": (
                    f"{match.group('day')} {match.group('month')} {match.group('year')}"
                ),
                "source_year": int(match.group("year")),
                "source_date_invalid": True, "details_in_statutes": True,
            },
        ))

    match = _FR_NEW_ADMINISTRATORS_DE_ET_A.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administrators_without_signature_de_et_a.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="administrateur",
                extra={
                    "action": "appointed", "heimat": match.group("place1").strip(),
                    "without_signature": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="administrateur",
                extra={
                    "action": "appointed", "heimat": match.group("origin2").strip(),
                    "without_signature": True,
                },
            ),
        ])

    match = _FR_ANCILLARY_MENTION_REMOVED_SUPPLEMENT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.ancillary_mention_removed_supplement.v1",
            {
                "kind": "ancillary_obligations", "action": "mention_removed",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "rights_removed": ["preference", "preemption", "emption"],
            },
        ))

    match = _FR_MANAGER_TRANSFER_NEW_UNSIGNED_ASSOCIATE.search(leftover)
    if match:
        consume(match)
        events.extend(_share_transfer_events(
            match, publication_id, published_at, org_uid, plz, canton,
            "fr.persons.manager_transfer_new_unsigned_associate.v1",
            seller_role="associé-gérant", buyer_place=match.group("place"),
            buyer_extra={
                "heimat": match.group("origin").strip(), "new_associate": True,
                "without_signature": True,
            },
        ))

    match = _DE_TWO_PERSON_CHANGES_WITH_NAME_CORRECTION.search(leftover)
    if match:
        consume(match)
        rule_id = "de.persons.two_changes_name_signing_and_place.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role=match.group("role1").strip(), signing=match.group("sign1"),
                extra={
                    "action": "name_and_signing_corrected",
                    "previous_name": match.group("previous_name1").strip(),
                    "previous_role": match.group("previous_role1").strip(),
                    "previous_signing": match.group("previous_sign1"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place"), signing=match.group("sign2"),
                extra={
                    "action": "signing_restriction_and_domicile_changed",
                    "previous_signing": match.group("previous_sign2"),
                    "previous_signing_with": match.group("previous_with").strip(),
                    "signing_with": match.group("with").strip(),
                    "place_change_reason": match.group("place_reason"),
                },
            ),
        ])

    match = _FR_PROXY_REVOKED_APPOINTED_DIRECTOR.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.proxy_revoked_appointed_director.v1",
            match.group("name"), role=match.group("role").lower(),
            extra={
                "action": "appointed", "previous_signing": "procuration",
                "previous_signing_revoked": True,
            },
        ))

    match = _FR_SIGNING_GRANTED_DEPUTY_DIRECTOR.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.signing_granted_deputy_director.v1",
            match.group("name"), role=match.group("role").lower(),
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "appointed", "previous_signing": "procuration",
                "previous_signing_revoked": True,
                "signing_restriction": "avec l'administrateur ou le directeur",
            },
        ))

    match = _FR_ASSOCIATE_TRANSFER_NEW_ASSOCIATE_SEMICOLON.search(leftover)
    if match:
        consume(match)
        events.extend(_share_transfer_events(
            match, publication_id, published_at, org_uid, plz, canton,
            "fr.persons.associate_transfer_new_associate_semicolon.v1",
            buyer_place=match.group("place"),
            buyer_extra={
                "heimat": match.group("origin").strip(),
                "country": match.group("country"), "new_associate": True,
                "without_signature": True,
            },
        ))

    match = _FR_TWO_DOMICILES_CORRECTED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_domiciles_corrected.v1"
        reference = {
            "action": "domicile_corrected", "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
        }
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"),
                extra={**reference, "country": match.group("country1")},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), extra=reference,
            ),
        ])

    match = _FR_REGISTERED_SHARE_RESTRICTION_REMOVED_TYPO.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.registered_share_restriction_removed_typo.v1",
            {
                "kind": "share_transfer_restriction", "action": "removed",
                "shares_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"), "currency": "CHF",
                "share_kind": "actions nominatives",
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
