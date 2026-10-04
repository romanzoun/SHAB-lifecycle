from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_STATUTES_DATE_ENTERED_INCORRECTLY = re.compile(
    r"^Als Statutendatum wurde irrtümlich\s+(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"anstelle von\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+eingetragen\.?$",
    re.I | re.UNICODE,
)
_IT_CONTRIBUTION_IN_KIND_REMOVED = re.compile(
    r"^\[radiati:\s*Alla società sono stati apportati beni per un valore di CHF\s+"
    r"(?P<value>[\d'.-]+),\s*di cui CHF\s+(?P<credited>[\d'.-]+)\s+computati sul "
    r"capitale azionario\.\s*Data dell['’]apporto:\s*"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_AT_FOUNDING = re.compile(
    r"^Die Gesellschaft hat bei der Gründung vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+eine genehmigte Kapitalerhöhung "
    r"gemäss näherer Umschreibung in den Statuten beschlossen\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_NAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+n[°o]\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que le "
    r"nom exact de l['’](?P<role>administrateur|administratrice) est\s+"
    r"(?P<name>.+?)\s+et non pas\s+(?P<previous_name>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_PRESIDENCY_CHANGED_OLD_FIRST = re.compile(
    r"^Les administrateurs\s+(?P<old_president>[^,.;]+),\s*jusqu['’]ici président,\s*"
    r"et\s+(?P<new_president>[^,.;]+),\s*nommé président,\s*continuent à signer\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?$",
    re.I | re.UNICODE,
)
_FR_COMMITTEE_COMPOSITION_SECTION_REMOVED = re.compile(
    r"^L['’]inscription\s+N[°o]\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_page>\d+)\)\s+est complétée comme suit\s*:\s*"
    r"radiation de la rubrique concernant la composition du comité\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGER_TRANSFER_TO_NEW_UNSIGNED = re.compile(
    r"^L['’]associée-gérante\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts? de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de et à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé avec\s+(?P<buyer_count>[\d']+)\s+"
    r"parts? de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*sans signature\.\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<seller_count>[\d']+)\s+parts? de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_OUTGOING_SPIN_OFF_SINGLE_RECIPIENT = re.compile(
    r"^Abspaltung:\s*Ein Teil der Aktiven und Passiven geht gemäss\s+"
    r"(?P<plan>Spaltungsplan|Spaltungsvertrag)\s+vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+auf die\s+"
    r"(?P<newly_founded>neu gegründete\s+)?(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*über\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_NAME_CORRECTED_WITH_NOTICE = re.compile(
    r"^Rectification:\s*l['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\)\s+est rectifiée dans le sens que le nom exact est\s+"
    r"(?P<name>.+?)\s+et non pas\s+(?P<previous_name>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_LIQUIDATORS_ONE_MOVED = re.compile(
    r"^(?P<name1>[^,.;]+),\s*maintenant à\s+(?P<place>[^,.;]+),\s*et\s+"
    r"(?P<name2>[^,.;]+)\s+sont nommées liquidatrices\.?$",
    re.I | re.UNICODE,
)
_FR_ORGANIZATION_TRANSFER_TO_EXISTING_MANAGER = re.compile(
    r"^L['’]associée\s+(?P<seller>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+parts? de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"l['’]associé-gérant\s+(?P<buyer>[^,.;]+),\s*maintenant domicilié à\s+"
    r"(?P<place>[^,.;]+),\s*qui possède désormais\s+"
    r"(?P<buyer_count>[\d']+)\s+parts? de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"Par conséquent,\s*(?P=seller)\s+est maintenant associée pour\s+"
    r"(?P<seller_count>[\d']+)\s+parts? de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_ENDOWMENT_CAPITAL_INCREASED = re.compile(
    r"^Kapital neu:\s*CHF\s+(?P<capital>[\d'.]+)\s*"
    r"\[bisher:\s*CHF\s+(?P<previous_capital>[\d'.]+)\]\.\s*"
    r"Liberierung Kapital neu:\s*CHF\s+(?P<paid>[\d'.]+)\s*"
    r"\[bisher:\s*CHF\s+(?P<previous_paid>[\d'.]+)\]\.\s*"
    r"Erhöhung des Dotationskapitals gemäss Beschluss des\s+"
    r"(?P<authority>.+?)\s+vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"(?P<reason>.+?)\s+um CHF\s+(?P<increase>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_USAGE_NAME_CHANGED = re.compile(
    r"^(?P<previous_name>.+?\s+usage\s+.+?)\s+porte désormais le nom de\s+"
    r"(?P<name>.+?)\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_AND_CHANGED_PERSON = re.compile(
    r"^Gelöschte Person:\s*(?P<removed>[^,.;]+),\s*"
    r"(?P<removed_roles>.+?),\s*"
    r"(?P<removed_sign>Einzelunterschrift|Kollektivunterschrift(?:\s+zu\s+zweien)?)\.\s*"
    r"Eingetragene Person geändert:\s*(?P<changed>[^,.;]+),\s*"
    r"(?P<previous_roles>.+?),\s*"
    r"(?P<previous_sign>Einzelunterschrift|Kollektivunterschrift(?:\s+zu\s+zweien)?),\s*"
    r"neu\s+(?P<roles>.+?),\s*"
    r"(?P<sign>Einzelunterschrift|Kollektivunterschrift(?:\s+zu\s+zweien)?)\.?$",
    re.I | re.UNICODE,
)
_IT_COMPANY_BANKRUPTCY_EFFECT_SUSPENDED = re.compile(
    r"^Con decreto del\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"(?P<authority>.+?)\s+ha accordato effetto sospensivo al reclamo inoltrato "
    r"contro la decisione di apertura del fallimento della\s+"
    r"(?P<court>.+?)\s+del\s+(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"L['’]iscrizione nel registro di commercio relativa allo scioglimento della "
    r"società a seguito di fallimento viene pertanto cancellata\."
    r"(?:\s*\[radiati:\s*La società è sciolta in seguito a fallimento pronunciato "
    r"con decreto della\s+(?P<previous_court>.+?)\s+del\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+a far tempo dal\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4})\s+alle ore\s+"
    r"(?P<effective_time>\d{1,2}:\d{2})\.\])?\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_TRANSLATIONS_COMPLETED = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est complétée en ce sens que la "
    r"raison sociale,\s*assortie de ses traductions,\s*a pour teneur\s*:\s*"
    r"(?P<name>.+?)\s*\[(?P<german>[^\]]+)\]\s*\[(?P<english>[^\]]+)\]\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _signing(raw: str) -> str:
    return (
        "Einzelunterschrift"
        if "individ" in raw.lower() or "einzel" in raw.lower()
        else "Kollektivunterschrift zu zweien"
    )


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


def extract_parser90_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 90."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_STATUTES_DATE_ENTERED_INCORRECTLY.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", "de.text.statutes_date_entered_incorrectly.v1",
                {
                    "kind": "statutes_date",
                    "action": "corrected",
                    "date": _iso_date(match.group("date")),
                    "previous_date": _iso_date(match.group("previous_date")),
                },
            )
        )

    match = _IT_CONTRIBUTION_IN_KIND_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "it.text.contribution_in_kind_removed_legacy.v1",
                {
                    "kind": "contribution_in_kind",
                    "action": "removed",
                    "currency": "CHF",
                    "value": match.group("value"),
                    "credited_to_share_capital": match.group("credited"),
                    "date": _iso_date(match.group("date")),
                },
            )
        )

    match = _DE_AUTHORIZED_CAPITAL_AT_FOUNDING.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.authorized_capital_at_foundation.v1",
                {
                    "kind": "authorized_capital",
                    "action": "introduced",
                    "foundation_date": _iso_date(match.group("date")),
                    "details_in_statutes": True,
                },
            )
        )

    match = _FR_ADMINISTRATOR_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.administrator_name_corrected.v1",
                match.group("name"), role=match.group("role"),
                extra={
                    "action": "name_corrected",
                    "previous_name": match.group("previous_name").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                },
            )
        )

    match = _FR_PRESIDENCY_CHANGED_OLD_FIRST.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.presidency_changed_old_first.v1"
        signing = _signing(match.group("sign"))
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("old_president"),
                    role="administrateur", signing=signing,
                    extra={"action": "presidency_ended", "previous_role": "président"},
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("new_president"),
                    role="président", signing=signing,
                    extra={"action": "appointed_president"},
                ),
            ]
        )

    match = _FR_COMMITTEE_COMPOSITION_SECTION_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", "fr.text.committee_composition_section_removed.v1",
                {
                    "kind": "committee_composition_section",
                    "action": "removed",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_page": match.group("notice_page"),
                },
            )
        )

    match = _FR_ASSOCIATE_MANAGER_TRANSFER_TO_NEW_UNSIGNED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.associate_manager_transfer_new_unsigned.v1"
        transferred = _count(match.group("transferred"))
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("seller"),
                    role="associée-gérante",
                    extra={
                        "action": "shares_transferred",
                        "shares_before": _count(match.group("before")),
                        "shares_transferred": transferred,
                        "shares_count": _count(match.group("seller_count")),
                        "share_nominal": match.group("seller_nominal"),
                        "currency": "CHF",
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("buyer"),
                    place=match.group("place"), role="associé",
                    extra={
                        "action": "appointed",
                        "shares_received": transferred,
                        "shares_count": _count(match.group("buyer_count")),
                        "share_nominal": match.group("buyer_nominal"),
                        "currency": "CHF",
                        "new_associate": True,
                        "without_signature": True,
                        "heimat": match.group("place").strip(),
                    },
                ),
            ]
        )

    match = _DE_OUTGOING_SPIN_OFF_SINGLE_RECIPIENT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.outgoing_spin_off_single_recipient.v1",
                {
                    "kind": "spin_off_distribution",
                    "date": _iso_date(match.group("date")),
                    "document": match.group("plan").lower(),
                    "scope": "part_of_assets_and_liabilities",
                    "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "recipient_newly_founded": bool(match.group("newly_founded")),
                },
            )
        )

    match = _FR_PERSON_NAME_CORRECTED_WITH_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.name_corrected_with_notice.v1",
                match.group("name"),
                extra={
                    "action": "name_corrected",
                    "previous_name": match.group("previous_name").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_id": match.group("notice_id"),
                },
            )
        )

    match = _FR_TWO_LIQUIDATORS_ONE_MOVED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_liquidators_one_moved.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("name1"),
                    place=match.group("place"), role="liquidatrice",
                    extra={"action": "appointed_liquidator", "domicile_changed": True},
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("name2"),
                    role="liquidatrice", extra={"action": "appointed_liquidator"},
                ),
            ]
        )

    match = _FR_ORGANIZATION_TRANSFER_TO_EXISTING_MANAGER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.organization_transfer_existing_manager_moved.v1"
        transferred = _count(match.group("transferred"))
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("seller"), role="associée",
                    extra={
                        "action": "shares_transferred",
                        "shares_transferred": transferred,
                        "shares_count": _count(match.group("seller_count")),
                        "share_nominal": match.group("seller_nominal"),
                        "currency": "CHF",
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("buyer"),
                    place=match.group("place"), role="associé-gérant",
                    extra={
                        "action": "shares_received",
                        "shares_received": transferred,
                        "shares_count": _count(match.group("buyer_count")),
                        "share_nominal": match.group("buyer_nominal"),
                        "currency": "CHF",
                        "domicile_changed": True,
                    },
                ),
            ]
        )

    match = _DE_ENDOWMENT_CAPITAL_INCREASED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.endowment_capital_increased.v1",
                {
                    "kind": "endowment_capital_increase",
                    "currency": "CHF",
                    "from_nominal": match.group("previous_capital"),
                    "to_nominal": match.group("capital"),
                    "from_paid": match.group("previous_paid"),
                    "to_paid": match.group("paid"),
                    "increase": match.group("increase"),
                    "decision_date": _iso_date(match.group("date")),
                    "authority": match.group("authority").strip(),
                    "reason": match.group("reason").strip(),
                },
            )
        )

    match = _FR_USAGE_NAME_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.usage_name_changed.v1",
                match.group("name"),
                extra={
                    "action": "name_changed",
                    "previous_name": match.group("previous_name").strip(),
                },
            )
        )

    match = _DE_REMOVED_AND_CHANGED_PERSON.search(leftover)
    if match:
        consume(match)
        rule_id = "de.persons.removed_and_role_changed.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", rule_id, match.group("removed"),
                    role=match.group("removed_roles").strip(),
                    signing=_signing(match.group("removed_sign")),
                    extra={"action": "removed"},
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("changed"),
                    role=match.group("roles").strip(),
                    signing=_signing(match.group("sign")),
                    extra={
                        "action": "role_changed",
                        "previous_role": match.group("previous_roles").strip(),
                        "previous_signing": _signing(match.group("previous_sign")),
                    },
                ),
            ]
        )

    match = _IT_COMPANY_BANKRUPTCY_EFFECT_SUSPENDED.search(leftover)
    if match:
        consume(match)
        payload = {
            "kind": "bankruptcy_effect_suspended",
            "action": "suspended_on_appeal",
            "decision_date": _iso_date(match.group("decision_date")),
            "authority": match.group("authority").strip(),
            "bankruptcy_court": match.group("court").strip(),
            "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
            "dissolution_entry_removed": True,
        }
        if match.group("effective_date"):
            payload.update(
                {
                    "effective_date": _iso_date(match.group("effective_date")),
                    "effective_time": match.group("effective_time"),
                }
            )
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "it.text.company_bankruptcy_effect_suspended.v2",
                payload,
            )
        )

    match = _FR_COMPANY_TRANSLATIONS_COMPLETED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_name_changed", "fr.text.company_translations_completed.v1",
                {
                    "action": "translations_added",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "name": match.group("name").strip(),
                    "translations": {
                        "de": match.group("german").strip(),
                        "en": match.group("english").strip(),
                    },
                },
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
