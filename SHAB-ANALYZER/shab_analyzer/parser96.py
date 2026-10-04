from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_CAPITAL_BAND_RECEIVABLE_OFFSET = re.compile(
    r"^Bei der ordentlichen Kapitalerhöhung innerhalb des Kapitalbandes vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+werden Forderungen in der Höhe von\s+"
    r"(?P<currency>[A-Z]{3})\s+(?P<receivables>[\d'.]+)\s+verrechnet,\s*wofür\s+"
    r"(?P<count>[\d']+)\s+(?P<share_kind>.+?)\s+zu\s+"
    r"(?P<nominal_currency>[A-Z]{3})\s+(?P<nominal>[\d'.]+)\s+ausgegeben werden\.?$",
    re.I | re.UNICODE,
)
_DE_OFFICER_CORRECTION = re.compile(
    r"^Mit dem im SHAB Nr\.\s*(?P<issue>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten TR-Nr\.\s*"
    r"(?P<entry>[\d']+)\s+vom\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"wurde der bisherige Text bei\s+(?P<subject>.+?)\s+unvollständig publiziert\.\s*"
    r"Korrekt wäre:\s*(?P<name>[^,.;]+,\s*[^,.;]+),\s*"
    r"(?P<nationality>[^,.;]+),\s*"
    r"in\s+(?P<place>[^,.;]+),\s*(?P<role>[^,.;]+),\s*mit\s+"
    r"(?P<sign>Kollektivunterschrift zu zweien|Einzelunterschrift)\s*"
    r"\[bisher:\s*(?P<previous_role>[^,;\]]+),\s*in\s+"
    r"(?P<previous_place>[^\]]+)\]\.?$",
    re.I | re.UNICODE,
)
_DE_FEDERAL_COURT_CONFIRMATION = re.compile(
    r"^Mit Verfügung vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+hat das\s+"
    r"(?P<authority>Bundesgericht)\s+den Entscheid vom\s+"
    r"(?P<confirmed_date>\d{2}\.\d{2}\.\d{4})\s+für die weitere Dauer des\s+"
    r"(?P<proceeding>bundesgerichtlichen Verfahrens)\s+bestätigt\.\s*"
    r"\[bisher:\s*(?P<previous>.+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_HEAD_OFFICE_NAME_SUPPLEMENT = re.compile(
    r"^L['’]inscription no\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+p\.\s*"
    r"(?P<notice_page>[\d/]+)\)\s+est complétée en ce sens que la nouvelle "
    r"raison sociale du siège principale est:\s*(?P<name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_SPLIT_SIGNING = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé président,\s*et\s+"
    r"(?P<vice>[^,.;]+),\s*de et à\s+(?P<place>[^,.;]+)\s*"
    r"\((?P<canton>[^)]+)\),\s*vice-président\.\s*Signature individuelle du "
    r"président ou collective à deux du vice-président\.?$",
    re.I | re.UNICODE,
)
_DE_STATUTES_DATE_BRACKET_CORRECTION = re.compile(
    r"^Statutenänderung:\s*\[Statutendatum vom\s+"
    r"(?P<entered_date>\d{2}\.\d{2}\.\d{4})\s+wurde irrtümlich eingetragen\s*"
    r"\(nicht:\s*(?P<not_date>\d{2}\.\d{2}\.\d{4})\)\]\.?$",
    re.I | re.UNICODE,
)
_FR_PROCURATION_MISSING_A = re.compile(
    r"^Procuration\s+(?P<sign>collective à deux),\s*"
    r"(?P<constraint>sauf avec un fondé de pouvoir),\s*(?:a\s+)?été conférée à\s+"
    r"(?P<name>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{1,3})\.?$",
    re.I | re.UNICODE,
)
_DE_DOCUMENT_DATE_CORRECTION = re.compile(
    r"^\[Berichtigung des irrtümlich falsch eingetragenen\s+"
    r"(?P<kind>Urkundendatums)\s+vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\]\.?$",
    re.I | re.UNICODE,
)
_DE_REINSTATEMENT_AND_CORRECTION = re.compile(
    r"^\[Die Verfügung vom\s+(?P<order_date>\d{2}\.\d{2}\.\d{4})\s+wird "
    r"widerrufen und die Gesellschaft wieder in das Handelsregister eingetragen\.\]\s*"
    r"\[gestrichen:\s*(?P<removed>.+?)\]\.?\s*"
    r"\[Berichtigung des im SHAB vom\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"Meldungs Nr\.\s*(?P<notice_id>\d+),\s*publizierten Tagesregistereintrages "
    r"Nr\.\s*(?P<entry>[\d']+)\s+vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\]\.?$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_EXTENDED = re.compile(
    r"^Mit Entscheid vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+die definitive Nachlassstundung bis\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\s+verlängert\.?$",
    re.I | re.UNICODE,
)
_FR_GENERAL_PARTNER_WITH_INITIALS = re.compile(
    r"^Nouvel associé indéfiniment responsable:\s*(?P<name>.+?),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_CONSOLIDATION = re.compile(
    r"^L['’]inscription no\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}-\d{2}-\d{4}),\s*p\.\s*"
    r"(?P<notice_page>[\d/]+)\)\s+est complétée en ce sens que les\s+"
    r"(?P<from_count>[\d']+)\s+actions de CHF\s+(?P<from_nominal>[\d'.]+),\s*"
    r"(?P<kind>nominatives),\s*,\s*ont été regroupées en\s+"
    r"(?P<to_count>[\d']+)\s+actions de CHF\s+(?P<to_nominal>[\d'.]+)\.\s*"
    r"Capital-actions:\s*CHF\s+(?P<total>[\d'.]+),\s*entièrement libéré,\s*"
    r"divisé en\s+(?P<capital_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<capital_nominal>[\d'.]+),\s*nominatives(?:,\s*liées selon statuts)?\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_WITH_SIGNING_CONSTRAINT = re.compile(
    r"^Nouvel administrateur\s+(?P<constraint>toutefois avec\s+[^:]+):\s*"
    r"(?P<name>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_PURPOSE_CHANGED = re.compile(
    r"^Angaben zur Zweigniederlassung neu:\s*Zweck der Zweigniederlassung:\s*"
    r"(?P<purpose>.+?)\s*\[bisher:\s*Zweck der Zweigniederlassung:\s*"
    r"(?P<previous>.+?)\]\.?$",
    re.I | re.UNICODE,
)
_DE_PROVISIONAL_MORATORIUM_EXTENDED_WITH_COMMISSIONER = re.compile(
    r"^Mit Entscheid\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+wurde die am\s+"
    r"(?P<granted_date>\d{2}\.\d{2}\.\d{4})\s+bewilligte provisorische "
    r"Nachlassstundung verlängert bis zum\s+(?P<until>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"Sachwalterin ist die\s+(?P<commissioner>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_MANAGERS = re.compile(
    r"^Nouveaux gérants:\s*(?P<name1>[^,.;]+),\s*de\s+"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<country1>[A-Z]{1,3}),\s*(?P<name2>[^,.;]+),\s*de\s+"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"(?P<country2>[A-Z]{1,3}),\s*et\s+(?P<name3>[^,.;]+),\s*de\s+"
    r"(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+),\s*"
    r"(?P<country3>[A-Z]{1,3})\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = re.split(r"[.-]", raw)
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


def extract_parser96_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 96."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_CAPITAL_BAND_RECEIVABLE_OFFSET.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.capital_band_receivable_offset.v1",
            {
                "kind": "ordinary_capital_increase_within_capital_band",
                "date": _iso_date(match.group("date")),
                "receivables_offset": match.group("receivables"),
                "currency": match.group("currency"),
                "shares_issued": _count(match.group("count")),
                "share_kind": match.group("share_kind").strip(),
                "share_nominal": match.group("nominal"),
                "share_nominal_currency": match.group("nominal_currency"),
            },
        ))

    match = _DE_OFFICER_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.officer_text_completed.v1",
            match.group("name"), place=match.group("place"),
            role=match.group("role"), signing=match.group("sign"),
            extra={
                "action": "publication_completed",
                "nationality": match.group("nationality").strip(),
                "previous_role": match.group("previous_role").strip(),
                "previous_place": match.group("previous_place").strip(),
                "subject": match.group("subject").strip(),
                "reference": {
                    "issue": match.group("issue"),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                },
            },
        ))

    match = _DE_FEDERAL_COURT_CONFIRMATION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.federal_court_interim_decision_confirmed.v1",
            {
                "kind": "court_decision_confirmed",
                "decision_date": _iso_date(match.group("date")),
                "confirmed_decision_date": _iso_date(match.group("confirmed_date")),
                "authority": match.group("authority"),
                "duration": match.group("proceeding"),
                "previous_text": match.group("previous").strip(),
            },
        ))

    match = _FR_HEAD_OFFICE_NAME_SUPPLEMENT.search(leftover)
    if match:
        consume(match)
        raw_name = match.group("name").strip()
        primary_name = raw_name.split(" (", 1)[0].strip()
        translations = [name.strip() for name in re.findall(r"\(([^()]+)\)", raw_name)]
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_name_changed", "fr.text.head_office_name_supplement.v1",
            {
                "scope": "head_office",
                "action": "registration_supplemented",
                "to": primary_name,
                "translations": translations,
                "head_office_uid": match.group("uid"),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_page": match.group("notice_page"),
            },
        ))

    match = _FR_ADMINISTRATION_SPLIT_SIGNING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_split_signing.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président", signing="Einzelunterschrift",
                extra={"action": "appointed"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("vice"),
                place=match.group("place"), role="vice-président",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed",
                    "heimat": match.group("place").strip(),
                    "place_canton": match.group("canton").strip(),
                },
            ),
        ])

    match = _DE_STATUTES_DATE_BRACKET_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.statutes_date_bracket_correction.v1",
            {
                "kind": "statutes_date",
                "action": "incorrect_entry_noted",
                "entered_date": _iso_date(match.group("entered_date")),
                "excluded_date": _iso_date(match.group("not_date")),
            },
        ))

    match = _FR_PROCURATION_MISSING_A.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.procuration_except_proxy.v1",
            match.group("name"), place=match.group("place"),
            signing="Kollektivprokura zu zweien",
            extra={
                "action": "appointed",
                "heimat": match.group("origin").strip(),
                "country_code": match.group("country"),
                "signing_constraint": match.group("constraint"),
            },
        ))

    match = _DE_DOCUMENT_DATE_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.document_date_correction_note.v1",
            {
                "kind": "document_date",
                "document": match.group("kind"),
                "incorrect_date": _iso_date(match.group("date")),
            },
        ))

    match = _DE_REINSTATEMENT_AND_CORRECTION.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.registry_reinstatement_order_revoked.v1"
        common = {
            "order_date": _iso_date(match.group("order_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_id": match.group("notice_id"),
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "previous_text": match.group("removed").strip(),
        }
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id,
                {"kind": "registry_reinstatement", "action": "reinstated", **common},
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", rule_id,
                {"kind": "registry_entry", "action": "corrected", **common},
            ),
        ])

    match = _DE_DEFINITIVE_MORATORIUM_EXTENDED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.definitive_moratorium_extended_direct.v1",
            {
                "kind": "composition_moratorium_extended",
                "moratorium_type": "definitive",
                "decision_date": _iso_date(match.group("date")),
                "authority": match.group("authority").strip(" ,"),
                "until": _iso_date(match.group("until")),
            },
        ))

    match = _FR_GENERAL_PARTNER_WITH_INITIALS.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.general_partner_initials.v1",
            match.group("name"), place=match.group("place"),
            role="associé indéfiniment responsable",
            extra={"action": "appointed", "heimat": match.group("origin").strip()},
        ))

    match = _FR_SHARE_CONSOLIDATION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.share_consolidation_supplement.v1",
            {
                "kind": "share_consolidation",
                "from_count": _count(match.group("from_count")),
                "from_nominal": match.group("from_nominal"),
                "to_count": _count(match.group("to_count")),
                "to_nominal": match.group("to_nominal"),
                "share_kind": match.group("kind"),
                "capital_total": match.group("total"),
                "capital_count": _count(match.group("capital_count")),
                "capital_nominal": match.group("capital_nominal"),
                "currency": "CHF",
                "paid_in_full": True,
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_page": match.group("notice_page"),
            },
        ))

    match = _FR_ADMINISTRATOR_WITH_SIGNING_CONSTRAINT.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_named_signing_constraint.v1",
            match.group("name"), place=match.group("place"), role="administrateur",
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "appointed",
                "heimat": match.group("origin").strip(),
                "signing_constraint": match.group("constraint").strip(),
            },
        ))

    match = _DE_BRANCH_PURPOSE_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "purpose_changed", "de.text.branch_purpose_changed.v1",
            {
                "scope": "branch",
                "from": match.group("previous").strip(),
                "to": match.group("purpose").strip(),
            },
        ))

    match = _DE_PROVISIONAL_MORATORIUM_EXTENDED_WITH_COMMISSIONER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.provisional_moratorium_extended_commissioner.v1",
            {
                "kind": "composition_moratorium_extended",
                "moratorium_type": "provisional",
                "decision_date": _iso_date(match.group("date")),
                "granted_date": _iso_date(match.group("granted_date")),
                "until": _iso_date(match.group("until")),
                "authority": match.group("authority").strip(" ,"),
                "commissioner": match.group("commissioner").strip(),
                "commissioner_place": match.group("place").strip(),
                "commissioner_uid": match.group("uid"),
            },
        ))

    match = _FR_THREE_MANAGERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.three_managers.v1"
        for index in (1, 2, 3):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="gérant",
                extra={
                    "action": "appointed",
                    "heimat": match.group(f"origin{index}").strip(),
                    "country_code": match.group(f"country{index}"),
                },
            ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
