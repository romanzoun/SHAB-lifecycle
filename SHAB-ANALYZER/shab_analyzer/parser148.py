from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_DIRECTORS_CONTINUE_COLLECTIVE = re.compile(
    r"^(?P<name1>[^,.;]+),\s*jusqu['’]ici\s+(?P<role1>directeur),\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*jusqu['’]ici\s+(?P<role2>directrice),\s*"
    r"continuent à signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_DE_LIMITED_PARTNERSHIP_CAPITAL_CURRENCY_PREFIX = re.compile(
    r"^Kommanditsumme neu:\s*CHF\s+(?P<to>[\d'.]+)\s*"
    r"\[bisher:\s*CHF\s+(?P<from>[\d'.]+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_FEMALE_OWNER_BANKRUPTCY_REVOKED = re.compile(
    r"^Par décision du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>.+?)\s+a annulé la faillite de la titulaire de l['’]entreprise "
    r"prononcée le\s+(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4});\s*"
    r"l['’]inscription est rétablie comme ci-devant\s*\(FOSC No\s+"
    r"(?P<notice_number>\d+)\s+du\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"publ\.\s+(?P<notice_id>[\d']+)\)\.?$",
    re.I | re.UNICODE,
)
_IT_BRANCH_HEAD_OFFICE_NAME_IDENTIFIER = re.compile(
    r"^Sede principale a:\s*(?P<head_office>[^.]+)\.\s*"
    r"Nuova ditta o ragione sociale della succursale:\s*(?P<branch_name>[^.]+)\.\s*"
    r"Nuovo numero di identificazione della sede principale:\s*"
    r"(?P<head_office_uid>CHE-\d{3}\.\d{3}\.\d{3})\s*"
    r"\[finora:\s*Numero di identificazione della sede principale:\s*"
    r"(?P<previous_registry_id>CH-[\d.-]+)\]\.\s*"
    r"Nuovo nome della ditta della sede principale:\s*(?P<head_office_name>[^\[]+?)\s*"
    r"\[finora:\s*Ditta della sede principale:\s*"
    r"(?P<previous_head_office_name>[^\]]+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_ROLE_CORPORATE_ASSOCIATE_CORRECTION = re.compile(
    r"^L['’]inscription\s+no\.\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(publication FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+page\s+"
    r"(?P<notice_id>\d+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<manager>[^,.;]+)\s+n['’]est pas\s+(?P<previous_role>associé),\s*"
    r"mais\s+(?P<role>gérant président)\s+Associée:\s*"
    r"(?P<associate>.+?)\s*\((?P<associate_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"à\s+(?P<place>[^()]+?)\s*\((?P<place_canton>[A-Z]{2})\),\s*pour\s+"
    r"(?P<count>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_AND_NAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\)\s+est rectifiée en ce sens "
    r"qu['’]une signature collective à deux a été conférée à\s+"
    r"(?P<name>[^()]+?)\s*\(et non pas\s+(?P<previous_name>[^)]+)\),\s*"
    r"(?P<role>directeur)\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_IDENTIFIER_AND_NAME_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le numéro "
    r"d['’]identification des entreprises de\s+(?P<previous_name>.+?)\s+est le\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s*\(et non le\s*"
    r"\((?P<incorrect_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"L['’]organe de révision\s+(?P=previous_name)\s+a modifié sa raison de "
    r"commerce en\s+(?P<name>.+?)\s*\((?P=uid)\)\.?$",
    re.I | re.UNICODE,
)
_IT_BANKRUPTCY_APPEAL_UPHELD = re.compile(
    r"^Con decisione del\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"(?P<authority>.+?)\s+ha accolto il reclamo e ha di conseguenza annullato "
    r"la decisione di apertura del fallimento della\s+(?P<court>.+?)\s+del\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.\s*\[radiati:\s*"
    r"Con decreto del\s+(?P<suspension_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"(?P=authority)\s+ha accordato effetto sospensivo al reclamo inoltrato "
    r"contro la decisione di apertura del fallimento della\s+(?P=court)\s+del\s+"
    r"(?P=bankruptcy_date)\.\s*L['’]iscrizione nel registro di commercio "
    r"relativa allo scioglimento della società a seguito di fallimento viene "
    r"pertanto cancellata\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_PAIR_DOMICILE_CHANGED_COUNTRY = re.compile(
    r"^(?P<name1>[^,.;]+?)\s+et\s+(?P<name2>[^,.;]+?)\s+sont maintenant "
    r"domiciliés à\s+(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{2,3})\.?$",
    re.I | re.UNICODE,
)
_FR_CIVIL_STATUS_NAME_CHANGED = re.compile(
    r"^Par suite de changement d['’]état civil,\s*(?P<previous_name>[^,.;]+?)\s+"
    r"porte désormais le nom de\s+(?P<name>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_REVOKED_WITH_HISTORY = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+die mit Beschluss vom\s+"
    r"(?P<introduced_date>\d{2}\.\d{2}\.\d{4})\s+eingeführte und am\s+"
    r"(?P<amended_date>\d{2}\.\d{2}\.\d{4})\s+geänderte genehmigte "
    r"Kapitalerhöhung widerrufen\.\s*\[gestrichen:\s*Die Gesellschaft hat mit "
    r"Beschluss vom\s+(?P=amended_date)\s+die anlässlich der Generalversammlung "
    r"vom\s+(?P=introduced_date)\s+eingeführte genehmigte Kapitalerhöhung gemäss "
    r"näherer Umschreibung in den Statuten geändert\]\.?$",
    re.I | re.UNICODE,
)
_FR_ORIGIN_TYPO_CORRECTED = re.compile(
    r"^L['’]inscription\s+no\.\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(publication FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+page\s+"
    r"(?P<notice_id>\d+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+est originaire de\s+(?P<origin>[^()]+?)\s*"
    r"\(et non de\s+(?P<previous_origin>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_DIRECTORS_SIGNING_SHARED_ORIGIN = re.compile(
    r"^Signature collective à deux a été conférée à\s+"
    r"(?P<name1>[^,.;]+),\s*(?P<name2>[^,.;]+)\s+et\s+"
    r"(?P<name3>[^,.;]+),\s*tous trois de et à\s+(?P<place>[^,.;]+),\s*"
    r"directeurs\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_CLASS_CONDITIONAL_PARTICIPATION_CAPITAL = re.compile(
    r"^Augmentation conditionnelle du capital-participation fondée sur la "
    r"décision relative à l['’]octroi de droits du\s+"
    r"(?P<rights_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.\s*"
    r"Nouveau capital-participation:\s*CHF\s+(?P<total>[\d'.]+),\s*libéré à "
    r"concurrence de CHF\s+(?P<paid>[\d'.]+),\s*divisé en\s+"
    r"(?P<count_a>[\d']+)\s+bons de participation nominatifs\s+[\"“]A[\"”]\s+"
    r"de CHF\s+(?P<nominal_a>[\d'.]+),\s*et\s+(?P<count_b>[\d']+)\s+bons de "
    r"participation nominatifs\s+[\"“]B[\"”]\s+de CHF\s+"
    r"(?P<nominal_b>[\d'.]+),\s*tous(?: avec restrictions quant à la "
    r"transmissibilité selon statuts\.)?\s*Le conseil d['’]administration a "
    r"modifié une clause statutaire relative à une augmentation conditionnelle "
    r"du capital-participation\s*\(selon décision relative à l['’]octroi de "
    r"droits de l['’]assemblée générale du\s+(?P<clause_rights_date>"
    r"\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\),\s*par décision du\s+"
    r"(?P<decision_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*pour le détail "
    r"cf\. statuts\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_BOARD_REMOVED_THREE_APPOINTED = re.compile(
    r"^(?P<removed1>[^,.;]+),\s*(?P<removed2>[^,.;]+),\s*"
    r"(?P<removed3>[^,.;]+),\s*inscrits sans signature,\s*ne sont plus "
    r"administrateurs\.\s*Nouveaux administrateurs sans signature:\s*"
    r"(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*et\s*"
    r"(?P<name3>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_DEPUTY_DIRECTOR_ROLE_CORRECTED = re.compile(
    r"^L['’]inscription\s+No\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce que\s+"
    r"(?P<name>[^,.;]+)\s+est en réalité\s+(?P<role>directeur adjoint)\s+"
    r"et non pas\s+(?P<previous_role>délégué)\.?$",
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
    day, month, year = raw.lower().split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", "").replace(".", ""))


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


def extract_parser148_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 148."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_DIRECTORS_CONTINUE_COLLECTIVE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.directors_continue_collective.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role=match.group(f"role{index}").lower(),
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "signing_continues", "role_unchanged": True},
            ))

    match = _DE_LIMITED_PARTNERSHIP_CAPITAL_CURRENCY_PREFIX.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.limited_partnership_capital_currency_prefix.v1",
            {
                "kind": "limited_partnership_capital", "currency": "CHF",
                "from": match.group("from"), "to": match.group("to"),
            },
        ))

    match = _FR_FEMALE_OWNER_BANKRUPTCY_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.female_owner_bankruptcy_revoked.v1",
            {
                "kind": "bankruptcy_revoked", "scope": "owner",
                "action": "judgment_set_aside", "registry_entry_restored": True,
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "previous_notice_number": match.group("notice_number"),
                "previous_notice_date": _iso_date(match.group("notice_date")),
                "previous_notice_id": match.group("notice_id").replace("'", ""),
            },
        ))

    match = _IT_BRANCH_HEAD_OFFICE_NAME_IDENTIFIER.search(leftover)
    if match:
        consume(match)
        rule_id = "it.text.branch_head_office_name_identifier.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_identifier_changed", rule_id,
                {
                    "scope": "head_office", "action": "changed",
                    "from": match.group("previous_registry_id"),
                    "to": match.group("head_office_uid"),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id,
                {
                    "action": "head_office_details_changed",
                    "head_office": match.group("head_office").strip(),
                    "head_office_uid": match.group("head_office_uid"),
                    "branch_name": match.group("branch_name").strip(),
                    "head_office_name": match.group("head_office_name").strip(),
                    "previous_head_office_name": (
                        match.group("previous_head_office_name").strip()
                    ),
                },
            ),
        ])

    match = _FR_MANAGER_ROLE_CORPORATE_ASSOCIATE_CORRECTION.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_role_corporate_associate_correction.v1"
        reference = {
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_id": match.group("notice_id"),
        }
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("manager"),
                role=match.group("role").lower(),
                extra={
                    "action": "role_corrected",
                    "previous_role": match.group("previous_role").lower(),
                    **reference,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("associate"),
                place=match.group("place"), uid=match.group("associate_uid"),
                role="associée",
                extra={
                    "action": "associate_corrected",
                    "shares_count": _count(match.group("count")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                    "place_canton": match.group("place_canton"), **reference,
                },
            ),
        ])

    match = _FR_SIGNING_AND_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.signing_and_name_corrected.v1",
            match.group("name"), role=match.group("role").lower(),
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "signing_granted_and_name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
            },
        ))

    match = _FR_AUDITOR_IDENTIFIER_AND_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.auditor_identifier_and_name_corrected.v1"
        reference = {
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_ref": match.group("notice_ref"),
        }
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", rule_id,
                {
                    "kind": "auditor_identifier", "action": "corrected",
                    "auditor_name": match.group("previous_name").strip(),
                    "from": match.group("incorrect_uid"), "to": match.group("uid"),
                    **reference,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                uid=match.group("uid"), role="organe de révision",
                extra={
                    "action": "trade_name_changed",
                    "previous_name": match.group("previous_name").strip(),
                    **reference,
                },
            ),
        ])

    match = _IT_BANKRUPTCY_APPEAL_UPHELD.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.bankruptcy_appeal_upheld.v1",
            {
                "kind": "bankruptcy_revoked", "action": "appeal_upheld",
                "decision_date": _iso_date(match.group("decision_date")),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "suspensive_effect_date": _iso_date(match.group("suspension_date")),
                "authority": match.group("authority").strip(),
                "bankruptcy_court": match.group("court").strip(),
                "dissolution_entry_cancelled": True,
            },
        ))

    match = _FR_PAIR_DOMICILE_CHANGED_COUNTRY.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.pair_domicile_changed_country.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group("place"),
                extra={
                    "action": "domicile_changed", "domicile_changed": True,
                    "country": match.group("country").upper(),
                },
            ))

    match = _FR_CIVIL_STATUS_NAME_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.civil_status_name_changed.v1",
            match.group("name"),
            extra={
                "action": "name_changed",
                "reason": "civil_status",
                "previous_name": match.group("previous_name").strip(),
            },
        ))

    match = _DE_AUTHORIZED_CAPITAL_REVOKED_WITH_HISTORY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_revoked_with_history.v1",
            {
                "kind": "authorized_increase", "action": "revoked",
                "decision_date": _iso_date(match.group("decision_date")),
                "introduced_date": _iso_date(match.group("introduced_date")),
                "amended_date": _iso_date(match.group("amended_date")),
                "previous_clause_removed": True, "details_in_statutes": True,
            },
        ))

    match = _FR_ORIGIN_TYPO_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.origin_typo_corrected.v1",
            match.group("name"),
            extra={
                "action": "origin_corrected",
                "heimat": match.group("origin").strip(),
                "previous_origin": match.group("previous_origin").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        ))

    match = _FR_THREE_DIRECTORS_SIGNING_SHARED_ORIGIN.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.three_directors_signing_shared_origin.v1"
        for index in (1, 2, 3):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                place=match.group("place"), role="directeur",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "signing_granted",
                    "heimat": match.group("place").strip(),
                },
            ))

    match = _FR_TWO_CLASS_CONDITIONAL_PARTICIPATION_CAPITAL.search(leftover)
    if match and (
        match.group("rights_date").casefold()
        == match.group("clause_rights_date").casefold()
        and _count(match.group("total")) == _count(match.group("paid"))
        and _count(match.group("total"))
        == _count(match.group("count_a")) * _count(match.group("nominal_a"))
        + _count(match.group("count_b")) * _count(match.group("nominal_b"))
    ):
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.two_class_conditional_participation_capital.v1",
            {
                "kind": "conditional_participation_capital_increase",
                "currency": "CHF", "total": match.group("total"),
                "paid": match.group("paid"), "fully_paid": True,
                "rights_date": _french_date(match.group("rights_date")),
                "clause_decision_date": _french_date(match.group("decision_date")),
                "registered": True, "transfer_restricted": True,
                "classes": [
                    {
                        "class": "A", "count": _count(match.group("count_a")),
                        "nominal": match.group("nominal_a"),
                    },
                    {
                        "class": "B", "count": _count(match.group("count_b")),
                        "nominal": match.group("nominal_b"),
                    },
                ],
                "details_in_statutes": True,
            },
        ))

    match = _FR_THREE_BOARD_REMOVED_THREE_APPOINTED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.three_board_removed_three_appointed.v1"
        for index in (1, 2, 3):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group(f"removed{index}"),
                role="administrateur",
                extra={"action": "removed", "without_signature": True},
            ))
        for index in (1, 2, 3):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="administrateur",
                extra={
                    "action": "appointed", "without_signature": True,
                    "heimat": match.group(f"origin{index}").strip(),
                },
            ))

    match = _FR_DEPUTY_DIRECTOR_ROLE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.deputy_director_role_corrected.v1",
            match.group("name"), role=match.group("role").lower(),
            extra={
                "action": "role_corrected",
                "previous_role": match.group("previous_role").lower(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    return events, re.sub(r"\s+", " ", leftover).strip(" .,;")
