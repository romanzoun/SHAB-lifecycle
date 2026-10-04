from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_MANAGER_TRANSFER_AND_NEW_MANAGER = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+),\s*maintenant président,\s*"
    r"détient\s+(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\s+par suite de cession de\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<transfer_nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]),\s*nouvel associé-gérant pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*avec signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_DE_PROVISIONAL_MORATORIUM_EXTENDED_MONTHS = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+die gewährte provisorische Nachlassstundung um\s+"
    r"(?P<duration>\w+)\s+Monate bis zum\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\s+verlängert\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ADMINISTRATORS_SWAP_ROLES = re.compile(
    r"^les administrateurs\s+(?P<name1>[^,.;]+)\s+jusqu['’]ici\s+"
    r"(?P<previous_role1>secrétaire),\s*nommé\s+(?P<role1>président)\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*jusqu['’]ici\s+(?P<previous_role2>président),\s*"
    r"nommé\s+(?P<role2>secrétaire),\s*continuent à signer individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_COMPANY_REINSTATED_AND_PROCEEDINGS_REOPENED = re.compile(
    r"^Diese Gesellschaft,\s*welche am\s+"
    r"(?P<deletion_date>\d{2}\.\d{2}\.\d{4})\s+infolge Konkurses im Sinne von\s+"
    r"(?P<legal_basis>Art\.\s*159\s+HRegV)\s+gelöscht wurde,\s*wird gemäss "
    r"Entscheid des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wieder als durch Konkurs "
    r"aufgelöst in das Handelsregister eingetragen\.\s*Das mit Entscheid vom\s+"
    r"(?P<suspension_date>\d{2}\.\d{2}\.\d{4})\s+mangels Aktiven eingestellte "
    r"Verfahren wird wieder eröffnet\.\s*Datum der Konkurseröffnung:\s*"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<bankruptcy_time>\d{1,2}[.:]\d{2})\s+Uhr\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_CLASS_NOMINAL_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que la valeur "
    r"nominale des\s+(?P<count>[\d']+)\s+actions nominatives de type\s+"
    r"(?P<share_class>[^,.;]+)\s+est de CHF\s+(?P<nominal>[\d'.]+)\s*"
    r"\(et non de CHF\s+(?P<previous_nominal>[\d'.]+)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_SOCIAL_SHARES_SPLIT_TWO_ASSOCIATES = re.compile(
    r"^Les\s+(?P<from_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<from_nominal>[\d'.]+)\s+ont été divisées en\s+"
    r"(?P<to_count>[\d']+)\s+parts de CHF\s+(?P<to_nominal>[\d'.]+);\s*"
    r"par conséquent l['’]associé\s+(?P<name1>[^,.;]+)\s+est maintenant "
    r"associé pour\s+(?P<count1>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal1>[\d'.]+)\s+et l['’]associé\s+(?P<name2>[^,.;]+)\s+pour\s+"
    r"(?P<count2>[\d']+)\s+parts de CHF\s+(?P<nominal2>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_SINGLE_REMOVED_OFFICER = re.compile(
    r"^Gelöschte Person:\s*(?P<name>[^,.;]+),\s*(?P<role>[^,.;]+),\s*"
    r"(?P<signing>Kollektivunterschrift zu zweien|Einzelunterschrift|"
    r"Kollektivprokura zu zweien)\.?$",
    re.I | re.UNICODE,
)
_DE_PROPERTY_AND_MUNICIPALITY_TYPOS_CORRECTED = re.compile(
    r"^Die Berichtigung erfolgt wegen zwei Schreibversehen:\s*Korrektur der "
    r"Grundstück Nr\.\s*(?P<property_number>\d+)\s*\(statt\s*"
    r"(?P<previous_property_number>\d+)\)\s+des Grundbuchs\s+"
    r"(?P<land_register>[^,.;]+)\s+und der Gemeinde\s+"
    r"(?P<municipality>[^()]+?)\s*\(statt\s*(?P<previous_municipality>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_SOCIAL_SHARE_SPLIT_TRANSFER_TWO_MANAGERS = re.compile(
    r"^Division de la part sociale de CHF\s+(?P<from_nominal>[\d'.]+)\s+de\s+"
    r"(?P<seller>[^,.;]+)\s+en\s+(?P<split_count>[\d']+)\s+parts sociales de "
    r"CHF\s+(?P<split_nominal>[\d'.]+)\.\s*Prestations accessoires,\s*droits "
    r"de préférence,\s*de préemption ou d['’]emption:\s*selon statuts\.\s*"
    r"(?P=seller)\s+a cédé\s+(?P<transferred>[\d']+)\s+des? ses\s+"
    r"(?P<before>[\d']+)\s+parts sociales de CHF\s+"
    r"(?P<transfer_nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé\.\s*"
    r"Gérants:\s*(?P=seller),\s*nommé président,\s*et\s+(?P=buyer),\s*"
    r"lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_FEDERAL_APPEAL_INADMISSIBLE = re.compile(
    r"^Par arrêt de\s+(?P<authority>la IIe Cour de droit civil du Tribunal "
    r"fédéral)\s+du\s+(?P<decision_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"le recours est irrecevable\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ADMINISTRATORS_ROLE_CHANGES = re.compile(
    r"^L['’]administrateur\s+(?P<name1>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<previous_role1>directeur général),\s*nommé\s+"
    r"(?P<role1>président et directeur)\s+et l['’]administrateur\s+"
    r"(?P<name2>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<previous_role2>président et délégué directeur),\s*"
    r"continuent à signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_PUBLICATION_SUPPLEMENT_HEADING_NO_ID_DOT = re.compile(
    r"^Complément:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\)\s+est complétée dans ce sens:\s*$",
    re.I | re.UNICODE,
)
_FR_PERSON_ORIGIN_CORRECTED_AS_PUBLISHED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+est de\s+(?P<origin>.+?)\s*\(et non de\s+"
    r"(?P<previous_origin>[^,()]+),\s*comme publié\)\.?$",
    re.I | re.UNICODE,
)
_DE_COOPERATIVE_LIABILITY_AND_BANK_STATUS = re.compile(
    r"^Haftung/Nachschusspflicht neu:\s*"
    r"\[Streichung des Eintrags aufgrund geänderter Eintragungsvorschriften\.\]\s*"
    r"\[gestrichen:\s*Haftung:\s*(?P<previous>Ohne persönliche Haftung)\.\]\.\s*"
    r"Bankgenossenschaft mit Beteiligungsscheinen gemäss\s+"
    r"(?P<legal_basis>Art\.\s*11\s+Abs\.\s*2bis,\s*Art\.\s*14,\s*"
    r"Art\.\s*14a\s+und\s+Art\.\s*14b\s+des Bundesgesetzes über die Banken "
    r"und Sparkassen)\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_RESTRICTION_CLAUSE_REPEALED = re.compile(
    r"^La clause statutaire relative à la restriction de transmissibilité des "
    r"actions est abrogée\.?$",
    re.I | re.UNICODE,
)
_FR_REGISTRATION_CONTINUED_LEGAL_BASIS_LET = re.compile(
    r"^\((?P<legal_basis>art\.\s*159a\s+al\.\s*2\s+let\.\s*b\s+ORC)\)\.?$",
    re.I | re.UNICODE,
)


_DE_NUMBERS = {
    "ein": 1,
    "eine": 1,
    "einen": 1,
    "zwei": 2,
    "drei": 3,
    "vier": 4,
    "fünf": 5,
    "sechs": 6,
}
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
    return int(raw.replace("'", ""))


def _duration(raw: str) -> int:
    normalized = raw.lower()
    return int(normalized) if normalized.isdigit() else _DE_NUMBERS[normalized]


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
        payload={
            "name": clean_name,
            "place": clean_place,
            **(extra or {}),
        },
    )


def extract_parser213_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 213."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_MANAGER_TRANSFER_AND_NEW_MANAGER.fullmatch(leftover)
    if match and len({
        match.group("seller_nominal"),
        match.group("transfer_nominal"),
        match.group("buyer_nominal"),
    }) == 1:
        rule_id = "fr.persons.manager_transfer_and_new_manager.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        seller_count = _count(match.group("seller_count"))
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        if transferred == buyer_count:
            common = {
                "share_nominal": match.group("seller_nominal"),
                "currency": "CHF",
            }
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller,
                    role="associé-gérant président", extra={
                        **common, "action": "role_changed_and_shares_transferred",
                        "previous_role": "associé-gérant", "counterparty": buyer,
                        "shares_before": seller_count + transferred,
                        "shares_transferred": transferred,
                        "shares_count": seller_count,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer,
                    place=match.group("place"), role="associé-gérant",
                    signing="Kollektivunterschrift zu zweien", extra={
                        **common, "action": "appointed_and_shares_received",
                        "counterparty": seller, "shares_received": transferred,
                        "shares_count": buyer_count, "new_associate": True,
                        "origin": match.group("origin").strip(),
                        "country": match.group("country").upper(),
                    },
                ),
            ], ""

    match = _DE_PROVISIONAL_MORATORIUM_EXTENDED_MONTHS.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.provisional_moratorium_extended_months.v1", {
                "kind": "composition_moratorium_extended", "action": "extended",
                "moratorium_type": "provisional",
                "decision_date": _iso_date(match.group("decision_date")),
                "duration_months": _duration(match.group("duration")),
                "until": _iso_date(match.group("until")),
                "authority": match.group("authority").strip(),
            },
        )], ""

    match = _FR_TWO_ADMINISTRATORS_SWAP_ROLES.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_administrators_swap_roles.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role=match.group(f"role{index}").lower(),
                signing="Einzelunterschrift", extra={
                    "action": "role_changed",
                    "previous_role": match.group(f"previous_role{index}").lower(),
                    "signing_continues": True,
                },
            )
            for index in (1, 2)
        ], ""

    match = _DE_BANKRUPTCY_COMPANY_REINSTATED_AND_PROCEEDINGS_REOPENED.fullmatch(
        leftover
    )
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed",
            "de.text.bankruptcy_company_reinstated_proceedings_reopened.v1", {
                "kind": "bankruptcy", "action": "reinstated_and_reopened",
                "deletion_date": _iso_date(match.group("deletion_date")),
                "deletion_legal_basis": match.group("legal_basis"),
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "dissolved_by_bankruptcy": True,
                "proceedings_suspension_date": _iso_date(
                    match.group("suspension_date")
                ),
                "proceedings_suspension_reason": "lack_of_assets",
                "proceedings_reopened": True,
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "bankruptcy_time": match.group("bankruptcy_time").replace(".", ":"),
            },
        )], ""

    match = _FR_SHARE_CLASS_NOMINAL_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.share_class_nominal_corrected.v1", {
                "kind": "share_structure_correction", "action": "corrected",
                "currency": "CHF", "shares_count": _count(match.group("count")),
                "share_kind": "actions nominatives",
                "share_class": match.group("share_class").strip(),
                "nominal": match.group("nominal"),
                "previous_nominal": match.group("previous_nominal"),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_SOCIAL_SHARES_SPLIT_TWO_ASSOCIATES.fullmatch(leftover)
    if match:
        from_count = _count(match.group("from_count"))
        to_count = _count(match.group("to_count"))
        count1 = _count(match.group("count1"))
        count2 = _count(match.group("count2"))
        if (
            from_count * _count(match.group("from_nominal"))
            == to_count * _count(match.group("to_nominal"))
            and count1 + count2 == to_count
            and len({
                match.group("to_nominal"),
                match.group("nominal1"),
                match.group("nominal2"),
            }) == 1
        ):
            rule_id = "fr.text.social_shares_split_two_associates.v1"
            events = [_event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "social_share_split", "action": "split",
                    "currency": "CHF",
                    "split_from": {
                        "count": from_count,
                        "nominal": match.group("from_nominal"),
                    },
                    "split_to": {
                        "count": to_count,
                        "nominal": match.group("to_nominal"),
                    },
                },
            )]
            for index, count in ((1, count1), (2, count2)):
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    role="associé", extra={
                        "action": "shares_reallocated", "shares_count": count,
                        "share_nominal": match.group(f"nominal{index}"),
                        "currency": "CHF",
                    },
                ))
            return events, ""

    match = _DE_SINGLE_REMOVED_OFFICER.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_removed", "de.persons.single_removed_officer.v1",
            match.group("name"), role=match.group("role").strip(),
            signing=match.group("signing"), extra={"action": "removed"},
        )], ""

    match = _DE_PROPERTY_AND_MUNICIPALITY_TYPOS_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected",
            "de.text.property_and_municipality_typos_corrected.v1", {
                "kind": "qualified_fact", "action": "typos_corrected",
                "corrections": [
                    {
                        "field": "property_number",
                        "value": match.group("property_number"),
                        "previous_value": match.group("previous_property_number"),
                        "land_register": match.group("land_register").strip(),
                    },
                    {
                        "field": "municipality",
                        "value": match.group("municipality").strip(),
                        "previous_value": match.group(
                            "previous_municipality"
                        ).strip(),
                    },
                ],
            },
        )], ""

    match = _FR_SOCIAL_SHARE_SPLIT_TRANSFER_TWO_MANAGERS.fullmatch(leftover)
    if match:
        split_count = _count(match.group("split_count"))
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        if (
            _count(match.group("from_nominal"))
            == split_count * _count(match.group("split_nominal"))
            and split_count == before
            and transferred <= before
            and match.group("split_nominal") == match.group("transfer_nominal")
        ):
            rule_id = "fr.persons.social_share_split_transfer_two_managers.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            nominal = match.group("split_nominal")
            return [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "capital_changed", rule_id, {
                        "kind": "social_share_split", "action": "split",
                        "currency": "CHF",
                        "split_from": {
                            "count": 1, "nominal": match.group("from_nominal")
                        },
                        "split_to": {"count": split_count, "nominal": nominal},
                    },
                ),
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "statutes_changed", rule_id, {
                        "kind": "ancillary_obligations_and_share_rights",
                        "action": "governed_by_statutes",
                        "rights": ["preference", "preemption", "emption"],
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller,
                    role="associé-gérant président", signing="Einzelunterschrift",
                    extra={
                        "action": "appointed_president_and_shares_transferred",
                        "counterparty": buyer, "shares_before": before,
                        "shares_transferred": transferred,
                        "shares_count": before - transferred,
                        "share_nominal": nominal, "currency": "CHF",
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer,
                    place=match.group("place"), role="associé-gérant",
                    signing="Einzelunterschrift", extra={
                        "action": "appointed_and_shares_received",
                        "counterparty": seller, "new_associate": True,
                        "shares_received": transferred,
                        "shares_count": transferred, "share_nominal": nominal,
                        "currency": "CHF", "origin": match.group("origin").strip(),
                    },
                ),
            ], ""

    match = _FR_FEDERAL_APPEAL_INADMISSIBLE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.federal_appeal_inadmissible.v1", {
                "kind": "bankruptcy_appeal", "action": "inadmissible",
                "authority": match.group("authority"),
                "decision_date": _french_date(match.group("decision_date")),
            },
        )], ""

    match = _FR_TWO_ADMINISTRATORS_ROLE_CHANGES.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_administrators_role_changes.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role=match.group("role1").lower(),
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "role_changed",
                    "previous_role": match.group("previous_role1").lower(),
                    "signing_continues": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                role="administrateur", signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "role_changed",
                    "previous_role": match.group("previous_role2").lower(),
                    "signing_continues": True,
                },
            ),
        ], ""

    match = _FR_PUBLICATION_SUPPLEMENT_HEADING_NO_ID_DOT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected",
            "fr.text.publication_supplement_heading_no_id_dot.v1", {
                "kind": "statutes_date", "action": "publication_supplemented",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        )], ""

    match = _FR_PERSON_ORIGIN_CORRECTED_AS_PUBLISHED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.origin_corrected_as_published.v1",
            match.group("name"), extra={
                "action": "origin_corrected",
                "origin": match.group("origin").strip(),
                "previous_origin": match.group("previous_origin").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _DE_COOPERATIVE_LIABILITY_AND_BANK_STATUS.fullmatch(leftover)
    if match:
        rule_id = "de.text.cooperative_liability_and_bank_status.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "liability_changed", rule_id, {
                    "kind": "member_personal_liability", "action": "entry_removed",
                    "personal_liability": False,
                    "previous": match.group("previous"),
                    "reason": "changed_registration_rules",
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id, {
                    "kind": "bank_cooperative", "action": "status_recorded",
                    "participation_certificates": True,
                    "legal_basis": re.sub(
                        r"\s+", " ", match.group("legal_basis")
                    ),
                },
            ),
        ], ""

    match = _FR_SHARE_TRANSFER_RESTRICTION_CLAUSE_REPEALED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed",
            "fr.text.share_transfer_restriction_clause_repealed.v1", {
                "kind": "share_transfer_restriction", "action": "removed",
                "share_kind": "actions",
            },
        )], ""

    match = _FR_REGISTRATION_CONTINUED_LEGAL_BASIS_LET.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.registration_continued_legal_basis_let.v1", {
                "kind": "registration_continued", "action": "legal_basis_recorded",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
            },
        )], ""

    return [], leftover
