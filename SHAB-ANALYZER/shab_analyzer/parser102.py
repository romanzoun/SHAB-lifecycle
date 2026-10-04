from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_COMMITTEE_ROLE_CHANGES = re.compile(
    r"^Les membres du comité\s+(?P<name1>[^,.;]+),\s*nommé\s+"
    r"(?P<role1>[^,.;]+),\s*et\s+(?P<name2>[^,.;]+),\s*nommée\s+"
    r"(?P<role2>[^,.;]+),\s*continuent à signer individuellement\.\s*"
    r"(?P<name3>[^,.;]+),\s*membre du comité,\s*a été nommée\s+"
    r"(?P<role3>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_RESTRICTION_REMOVED_SUPPLEMENT = re.compile(
    r"^Complément:\s*L['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*(?P<notice_ref>[\d/]+)\)\s+"
    r"est complétée en ce sens que les\s+(?P<count>[\d']+)\s+actions nominatives "
    r"de CHF\s+(?P<nominal>[\d'.]+)\s+ne sont désormais plus restreintes quant "
    r"à leur transmissibilité\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_THREE_ROLE_BASED_SIGNING = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+(?:\s*\([^)]*\))?),\s*"
    r"nommé président,\s*(?P<vice>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<vice_origin>[^,.;]+),\s*à\s+(?P<vice_place>[^,.;]+),\s*"
    r"(?P<vice_country>[^,.;]+),\s*vice-président,\s*et\s*"
    r"(?P<secretary>[^,.;]+),\s*de et à\s+(?P<secretary_place>[^,.;]+),\s*"
    r"secrétaire\.\s*Signature individuelle du président ou du vice-président,\s*"
    r"ou collective à deux du secrétaire du conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_SUPPLEMENT_AND_NEW_MEMBERS = re.compile(
    r"^Complément:\s*l['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*(?P<notice_ref>[\d/]+)\)\s+"
    r"est complétée en ce sens que le commissaire\s+(?P<president>[^.;]+?)\s+"
    r"est également président de la fondation\.\s*Nouveaux membres du conseil "
    r"de fondation sans signature:\s*(?P<name1>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*à\s*"
    r"(?P<place1>[^,.;]+),\s*et\s*(?P<name2>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*à\s*"
    r"(?P<place2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATES_APPOINTED_MANAGERS = re.compile(
    r"^Les associés\s+(?P<name1>[^,.;]+),\s*maintenant domiciliée? à\s*"
    r"(?P<place1>[^,.;]+),\s*(?P<country1>[A-Z]{1,3}),\s*"
    r"(?P<name2>[^,.;]+)\s+et\s+(?P<name3>[^,.;]+)\s+sont nommés gérants\.?$",
    re.I | re.UNICODE,
)
_DE_OUTGOING_SPIN_OFF_SINGLE_RECIPIENT_NO_COMMA = re.compile(
    r"^Abspaltung:\s*Ein Teil der Aktiven und Passiven geht gemäss\s+"
    r"(?P<plan>Spaltungsplan|Spaltungsvertrag)\s+vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+auf die\s+"
    r"(?P<newly_founded>neu gegründete\s+)?(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+über\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_REMOVED_AND_ADMINISTRATION_PAIR = re.compile(
    r"^(?P<removed1>.+?)\s+et\s+(?P<removed2>.+?)\s+"
    r"ne sont plus administrateurs;\s*leurs pouvoirs sont radiés\.\s*"
    r"Administration:\s*(?P<president>[^,.;]+),\s*de et à\s*"
    r"(?P<president_place>[^,.;]+),\s*président\s+et\s*"
    r"(?P<member>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<member_origin>[^,.;]+),\s*à\s*(?P<member_place>[^,.;]+),\s*"
    r"tous deux\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_ADMINISTRATOR_RESTRICTED_PAIR = re.compile(
    r"^Nouvelle administratrice avec\s+(?P<with1>[^,.;]+)\s+ou\s+"
    r"(?P<with2>[^:.;]+):\s*(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s*"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_EXACT_GIVEN_NAME_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*(?P<notice_ref>[\d/]+)\)\s+"
    r"est rectifiée en ce sens que le prénom exact de l['’](?P<role>[^,.;]+?)\s+"
    r"est\s+(?P<name>[^()]+?)\s*\(et non\s+(?P<previous_name>[^,;)]+),\s*"
    r"comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_PRESIDENCY_CHANGED_ADMINISTRATORS = re.compile(
    r"^Les administrateurs\s+(?P<new_president>[^,.;]+),\s*nommée? présidente?\s+"
    r"et\s+(?P<old_president>[^,.;]+),\s*jusqu['’]ici président,\s*"
    r"continuent à signer individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_SUSPENSION_REVOKED = re.compile(
    r"^Die\s+(?P<authority>.+?)\s+hat mit Entscheid vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+die am\s+"
    r"(?P<suspension_date>\d{2}\.\d{2}\.\d{4})\s+angeordnete Einstellung "
    r"des Konkursverfahrens aufgehoben und die Durchführung des\s+"
    r"(?P<procedure>summarischen Konkursverfahrens)\s+angeordnet\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_THREE_INDIVIDUAL = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé président,\s*"
    r"(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s*(?P<place1>[^,.;]+),\s*"
    r"(?P<country1>[A-Z]{1,3}),\s*et\s*(?P<name2>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*à\s*"
    r"(?P<place2>[^,.;]+),\s*(?P<country2>[A-Z]{1,3}),\s*"
    r"lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_APPOINTED_LIQUIDATOR_WITH_TRANSLATION = re.compile(
    r"^\((?P<translation>[^()]+?\s+in Liquidation)\)\.\s*"
    r"L['’]associé\s+(?P<name>[^,.;]+),\s*maintenant à\s*"
    r"(?P<place>[^,.;]+),\s*dont la signature est radiée,\s*"
    r"lequel reste gérant,\s*est élu liquidateur\.?$",
    re.I | re.UNICODE,
)
_FR_DOMICILE_CORRECTED_WITH_NOTICE = re.compile(
    r"^L['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+p\.\s*(?P<notice_ref>[\d/]+)\)\s+"
    r"est rectifiée en ce sens que l['’](?P<role>[^,.;]+?)\s+"
    r"(?P<name>[^,.;]+)\s+est domiciliée? à\s+(?P<place>[^()]+?)\s*"
    r"\(et non à\s+(?P<previous_place>.+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_APPEAL_REJECTED = re.compile(
    r"^Mit Entscheid des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde eine gegen die "
    r"Konkurseröffnung erhobene Beschwerde abgewiesen und über die Gesellschaft "
    r"mit Wirkung ab\s+(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}[.:]\d{2})\s+Uhr,\s*der Konkurs eröffnet\.\s*"
    r"\[bisher:\s*Mit Entscheid vom\s+(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"hat der\s+(?P<previous_authority>.+?)\s+über die Gesellschaft mit Wirkung "
    r"ab dem\s+(?P<previous_effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<previous_effective_time>\d{1,2}[.:]\d{2})\s+Uhr,\s*den Konkurs eröffnet;\s*"
    r"demnach ist die Gesellschaft aufgelöst\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_COMPANY_REINSTATED_DATE_ONLY = re.compile(
    r"^Diese Gesellschaft, welche am\s+(?P<deleted_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"infolge Konkurses im Sinne von\s+(?P<legal_basis>Art\.\s*159 HRegV)\s+"
    r"gelöscht wurde, wird gemäss Entscheid des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wieder als durch Konkurs "
    r"aufgelöst in das Handelsregister eingetragen\.\s*Datum der "
    r"Konkurseröffnung:\s*(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.?$",
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


def extract_parser102_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 102."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_COMMITTEE_ROLE_CHANGES.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.committee_role_changes_individual.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role=match.group(f"role{index}"), signing="Einzelunterschrift",
                extra={"action": "role_changed", "committee_member": True},
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("name3"),
            role=match.group("role3"),
            extra={"action": "appointed", "committee_member": True},
        ))

    match = _FR_SHARE_RESTRICTION_REMOVED_SUPPLEMENT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.share_restriction_removed_supplement.v1",
            {
                "kind": "share_transfer_restriction",
                "action": "removed",
                "shares_count": _count(match.group("count")),
                "share_kind": "actions nominatives",
                "share_nominal": match.group("nominal"),
                "currency": "CHF",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
                "supplement": True,
            },
        ))

    match = _FR_ADMINISTRATION_THREE_ROLE_BASED_SIGNING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_three_role_based_signing.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président du conseil d'administration",
                signing="Einzelunterschrift", extra={"action": "appointed"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("vice"),
                place=match.group("vice_place"), role="vice-président du conseil d'administration",
                signing="Einzelunterschrift",
                extra={
                    "action": "appointed",
                    "heimat": match.group("vice_origin").strip(),
                    "country": match.group("vice_country").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("secretary"),
                place=match.group("secretary_place"), role="secrétaire du conseil d'administration",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed", "heimat": match.group("secretary_place").strip()},
            ),
        ])

    match = _FR_FOUNDATION_SUPPLEMENT_AND_NEW_MEMBERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.foundation_supplement_and_new_members.v1"
        reference = {
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_ref": match.group("notice_ref"),
        }
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("president"),
            role="président de la fondation",
            extra={"action": "appointed_president", "previous_role": "commissaire", **reference},
        ))
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="membre du conseil de fondation",
                extra={
                    "action": "appointed",
                    "heimat": match.group(f"origin{index}").strip(),
                    "without_signature": True,
                },
            ))

    match = _FR_ASSOCIATES_APPOINTED_MANAGERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.associates_appointed_managers.v1"
        for index in (1, 2, 3):
            extra = {"action": "appointed", "associate": True}
            if index == 1:
                extra.update({"domicile_changed": True, "country": match.group("country1")})
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group("place1") if index == 1 else None,
                role="gérant", signing="Kollektivunterschrift zu zweien", extra=extra,
            ))

    match = _DE_OUTGOING_SPIN_OFF_SINGLE_RECIPIENT_NO_COMMA.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.outgoing_spin_off_single_recipient_no_comma.v1",
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
        ))

    match = _FR_BOARD_REMOVED_AND_ADMINISTRATION_PAIR.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.board_removed_and_administration_pair.v1"
        for key in ("removed1", "removed2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group(key), role="administrateur",
                extra={"action": "removed", "signing_revoked": True},
            ))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                place=match.group("president_place"), role="président du conseil d'administration",
                signing="Einzelunterschrift",
                extra={"action": "appointed", "heimat": match.group("president_place").strip()},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                place=match.group("member_place"), role="administrateur",
                signing="Einzelunterschrift",
                extra={"action": "appointed", "heimat": match.group("member_origin").strip()},
            ),
        ])

    match = _FR_NEW_ADMINISTRATOR_RESTRICTED_PAIR.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.new_administrator_restricted_pair.v1",
            match.group("name"), place=match.group("place"), role="administratrice",
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "appointed",
                "heimat": match.group("origin").strip(),
                "signing_with_any_of": [match.group("with1").strip(), match.group("with2").strip()],
            },
        ))

    match = _FR_EXACT_GIVEN_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.exact_given_name_corrected.v1",
            match.group("name"), role=match.group("role"),
            extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_PRESIDENCY_CHANGED_ADMINISTRATORS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.presidency_changed_administrators.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("new_president"),
                role="présidente", signing="Einzelunterschrift",
                extra={"action": "appointed_president"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("old_president"),
                role="administrateur", signing="Einzelunterschrift",
                extra={"action": "presidency_ended", "previous_role": "président"},
            ),
        ])

    match = _DE_BANKRUPTCY_SUSPENSION_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_suspension_revoked.v1",
            {
                "kind": "bankruptcy",
                "action": "proceeding_resumed",
                "decision_date": _iso_date(match.group("decision_date")),
                "suspension_date": _iso_date(match.group("suspension_date")),
                "authority": match.group("authority").strip(),
                "procedure": match.group("procedure").strip(),
            },
        ))

    match = _FR_ADMINISTRATION_THREE_INDIVIDUAL.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_three_individual.v1"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("president"), role="président",
            signing="Einzelunterschrift", extra={"action": "appointed"},
        ))
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="administrateur",
                signing="Einzelunterschrift",
                extra={
                    "action": "appointed",
                    "heimat": match.group(f"origin{index}").strip(),
                    "country": match.group(f"country{index}"),
                },
            ))

    match = _FR_MANAGER_APPOINTED_LIQUIDATOR_WITH_TRANSLATION.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.manager_appointed_liquidator_translation.v1",
            match.group("name"), place=match.group("place"), role="gérant et liquidateur",
            signing="Einzelunterschrift",
            extra={
                "action": "appointed_liquidator",
                "domicile_changed": True,
                "previous_signing_revoked": True,
                "translated_liquidation_name": match.group("translation").strip(),
            },
        ))

    match = _FR_DOMICILE_CORRECTED_WITH_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.domicile_corrected_with_notice.v1",
            match.group("name"), place=match.group("place"), role=match.group("role"),
            extra={
                "action": "domicile_corrected",
                "previous_place": match.group("previous_place").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _DE_BANKRUPTCY_APPEAL_REJECTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_appeal_rejected.v1",
            {
                "kind": "bankruptcy",
                "action": "appeal_rejected",
                "authority": match.group("authority").strip(),
                "decision_date": _iso_date(match.group("decision_date")),
                "effective_date": _iso_date(match.group("effective_date")),
                "effective_time": match.group("effective_time").replace(".", ":"),
                "previous_authority": match.group("previous_authority").strip(),
                "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                "previous_effective_date": _iso_date(match.group("previous_effective_date")),
                "previous_effective_time": match.group("previous_effective_time").replace(".", ":"),
                "dissolved_by_bankruptcy": True,
            },
        ))

    match = _DE_BANKRUPTCY_COMPANY_REINSTATED_DATE_ONLY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_company_reinstated_date_only.v1",
            {
                "kind": "bankruptcy_company_reinstated",
                "deleted_date": _iso_date(match.group("deleted_date")),
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "dissolved_by_bankruptcy": True,
                "registry_reinstated": True,
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
