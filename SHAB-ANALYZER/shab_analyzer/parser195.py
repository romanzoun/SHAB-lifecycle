from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_FR_HEAD_OFFICE_UID_FORMAT_CORRECTED = re.compile(
    r"^Nouveau numéro d['’]identification du siège principal:\s*"
    r"(?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\s*"
    r"\[précédemment:\s*Numéro d['’]identification du siège principal:\s*"
    r"\(?(?P<previous_uid>CHE-\d{3}\.\d{3}\.\d{3})\)?\]\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_NAME_CORRECTED_TYPO = re.compile(
    r"^L['’]inscription\s+(?:no|n°)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\)\s+est r[ée]ctifiée dans ce sens que la nouvelle "
    r"raison sociale est:\s*(?P<name>[^()]+?)\s*"
    r"\((?P<translation>[^()]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_NEW_MANAGERS_INDIVIDUAL = re.compile(
    r"^Nouveaux gérants:\s*(?P<name1>[^,.;]+),\s*"
    r"d['’](?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<country1>[A-Z]{2,3}),\s*président\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*tous deux"
    r"(?:\s+avec signature individuelle)?\.?$",
    re.I | re.UNICODE,
)
_FR_AUTHORIZED_CAPITAL_CLAUSE_REPLACED_NUMERIC_DATES = re.compile(
    r"^Suppression de la clause statutaire relative à l['’]augmentation "
    r"autorisée du capital fondée sur la décision d['’]autorisation du\s+"
    r"(?P<authorization_date>\d{2}\.\d{2}\.\d{4})"
    r"(?:\s*,\s*le délai étant écoulé|\s*)\.\s*"
    r"Par décision du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"l['’]assemblée générale a introduit une clause statutaire relative à "
    r"une augmentation autorisée du capital-actions\.\s*"
    r"Pour les détails,\s*voir les statuts\.?$",
    re.I | re.UNICODE,
)
_DE_AUDITOR_REGISTRY_ID_CORRECTED = re.compile(
    r"^Beim TR\s+(?P<entry>[\d']+)\s+vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+wurde die bisherige "
    r"Firmennummer der Revisionsstelle nicht publiziert\.\s*Korrekt wäre:\s*"
    r"(?P<name>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+"
    r"(?P<place>[^,.;]+),\s*(?P<role>Revisionsstelle)\s*"
    r"\[bisher:\s*(?P<previous_name>.+?)\s*"
    r"\((?P<previous_registry_id>CH-[\d.-]+)\)\]\.?$",
    re.I | re.UNICODE,
)
_DE_AUDITOR_PREVIOUS_ID_SUPPLEMENT = re.compile(
    r"^Nachtrag zu SHAB Nr\.\s*(?P<issue_number>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{1,2}\.\d{1,2}\.\d{4})\s+publizierten "
    r"TR-Nr\.\s*(?P<entry>[\d']+)\s+vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}),\s*bei Revisionsstelle fehlt "
    r"folgender Text\s*\[bisher:\s*"
    r"(?P<previous_registry_id>CH-[\d.]+-\d)\]\.?$",
    re.I | re.UNICODE,
)
_DE_STATUTES_APPROVED_BY_THREE_AUTHORITIES = re.compile(
    r"^Statuten:\s*Die Statuten wurden am\s+"
    r"(?P<date1>\d{2}\.\d{2}\.\d{4})\s+durch die\s+"
    r"(?P<authority1>Gemeindeversammlung\s+[^,.;]+),\s*am\s+"
    r"(?P<date2>\d{2}\.\d{2}\.\d{4})\s+durch die\s+"
    r"(?P<authority2>Gemeindeversammlung\s+[^,.;]+)\s+und am\s+"
    r"(?P<date3>\d{2}\.\d{2}\.\d{4})\s+durch den\s+"
    r"(?P<authority3>Regierungsrat des Kantons\s+[^,.;]+)\s+genehmigt\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_SIGNING_WITH_ADMINISTRATOR_PROXY_REVOKED = re.compile(
    r"^Signature collective à deux,\s*avec un administrateur a été conférée à\s+"
    r"(?P<name>[^,.;]+),\s*maintenant domicilié à\s+(?P<place>[^,.;]+),\s*"
    r"nommé\s+(?P<role>directeur);\s*sa procuration est radiée\.?$",
    re.I | re.UNICODE,
)
_FR_CAPITAL_NOMINAL_REDUCTION_AND_RESTORATION = re.compile(
    r"^Capital-actions réduit d['’]un montant de CHF\s+(?P<reduction>[\d'.]+),\s*"
    r"par réduction de la valeur nominale des\s+(?P<count>[\d']+)\s+actions,\s*"
    r"nominatives,\s*de CHF\s+(?P<from_nominal>[\d'.]+)\s+à CHF\s+"
    r"(?P<reduced_nominal>[\d'.]+),\s*et simultanément augmenté d['’]un "
    r"montant de CHF\s+(?P<increase>[\d'.]+),\s*par augmentation de la valeur "
    r"nominale des\s+(?P<increase_count>[\d']+)\s+actions,\s*nominatives,\s*"
    r"de CHF\s+(?P<increase_from_nominal>[\d'.]+)\s+à CHF\s+"
    r"(?P<to_nominal>[\d'.]+)\.\s*Capital-actions:\s*CHF\s+"
    r"(?P<total>[\d'.]+),\s*entièrement libéré,\s*divisé en\s+"
    r"(?P<final_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<final_nominal>[\d'.]+)(?:,\s*nominatives)?\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ASSOCIATES_TRANSFER_TO_ORGANIZATION_NO_SEPARATOR = re.compile(
    r"^(?P<seller1>[^\s,.;]+(?:\s+[^\s,.;]+){2})\s+"
    r"(?P<seller2>[^\s,.;]+(?:\s+[^\s,.;]+){2})\s+ne sont plus associés "
    r"par suite de cession de leurs\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>.+?)\s*"
    r"\((?P<buyer_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvelle associée pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_COMMITTEE_MEMBERS_WITH_PRESIDENT = re.compile(
    r"^Nouveaux membres du comité (?:avec signature collective à deux,\s*)?"
    r"avec le président ou le vice-président:\s*"
    r"(?P<name1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*trésorier,\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFERS_TO_TWO_UNSIGNED_ASSOCIATES = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+détient désormais\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+"
    r"par suite de cession de\s+(?P<transferred1>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal1>[\d'.]+)\s+à\s+(?P<buyer1>[^,.;]+),\s*de\s+"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*nouvel associé "
    r"pour\s+(?P<buyer_count1>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal1>[\d'.]+)\s+sans signature sociale,\s*et de\s+"
    r"(?P<transferred2>[\d']+)\s+parts de CHF\s+(?P<nominal2>[\d'.]+)\s+"
    r"à\s+(?P<buyer2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*(?P<country2>[A-Z]{1,3}),\s*nouvel associé "
    r"pour\s+(?P<buyer_count2>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal2>[\d'.]+)\s+sans signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_APPOINTED_VICE_PRESIDENT = re.compile(
    r"^(?P<name>[^,.;]+)\s+est nommé administrateur vice-président;\s*"
    r"(?:il\s+)?continue de signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_EXTENDED_TWO_HISTORY = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+die definitive Nachlassstundung bis\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\s+verlängert\.\s*"
    r"\[gestrichen:\s*Mit Entscheid vom\s+"
    r"(?P<previous_decision_date1>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P=authority)\s+die definitive Nachlassstundung bis\s+"
    r"(?P<previous_until1>\d{2}\.\d{2}\.\d{4})\s+verlängert\.\]\.?\s*"
    r"\[gestrichen:\s*Mit Entscheid vom\s+"
    r"(?P<previous_decision_date2>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P=authority)\s+die definitive Nachlassstundung bis\s+"
    r"(?P<previous_until2>\d{2}\.\d{2}\.\d{4})\s+verlängert\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_ASSET_TRANSFER_CASH_CONSIDERATION = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré "
    r"des actifs pour CHF\s+(?P<assets>[\d'.]+)\s+et des passifs envers les "
    r"tiers pour CHF\s+(?P<liabilities>[\d'.]+),\s*à la société\s+"
    r"(?P<recipient>.+?)\s+à\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_PROCEEDINGS_SUSPENDED_ORDINAL_DATE = re.compile(
    r"^(?P<authority>Le président du Tribunal de l['’]arrondissement .+?)\s+"
    r"a prononcé l['’]effet suspensif de la procédure de faillite le\s+"
    r"(?P<date>\d{1,2}(?:er)?\s+(?:janvier|février|mars|avril|mai|juin|"
    r"juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})\.?$",
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


def _amount(raw: str) -> Decimal:
    return Decimal(raw.replace("'", ""))


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


def extract_parser195_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 195."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_HEAD_OFFICE_UID_FORMAT_CORRECTED.fullmatch(leftover)
    if match and match.group("uid") == match.group("previous_uid"):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_identifier_changed", "fr.text.head_office_uid_format_corrected.v1", {
                "scope": "head_office", "action": "format_corrected",
                "from": match.group("previous_uid"), "to": match.group("uid"),
                "identifier_unchanged": True,
            },
        )], ""

    match = _FR_COMPANY_NAME_CORRECTED_TYPO.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_name_changed", "fr.text.company_name_corrected_typo.v1", {
                "action": "corrected", "to": match.group("name").strip(),
                "translation": match.group("translation").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
                "source_wording": "réctifiée",
            },
        )], ""

    match = _FR_TWO_NEW_MANAGERS_INDIVIDUAL.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_new_managers_individual_fragment.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="gérant président",
                signing="Einzelunterschrift", extra={
                    "action": "appointed", "origin": match.group("origin1").strip(),
                    "country": match.group("country1"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="gérant",
                signing="Einzelunterschrift", extra={
                    "action": "appointed", "origin": match.group("origin2").strip(),
                },
            ),
        ], ""

    match = _FR_AUTHORIZED_CAPITAL_CLAUSE_REPLACED_NUMERIC_DATES.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.authorized_capital_clause_replaced_numeric_dates.v1", {
                "kind": "authorized_capital_clause", "action": "introduced",
                "previous_clause_removed": True,
                "previous_authorization_date": _iso_date(
                    match.group("authorization_date")
                ),
                "decision_date": _iso_date(match.group("decision_date")),
                "details_in_statutes": True,
            },
        )], ""

    match = _DE_AUDITOR_REGISTRY_ID_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.auditor_registry_id_corrected.v1",
            match.group("name"), place=match.group("place"), uid=match.group("uid"),
            role=match.group("role"), extra={
                "action": "identifier_corrected",
                "previous_name": match.group("previous_name").strip(),
                "previous_registry_id": match.group("previous_registry_id"),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _DE_AUDITOR_PREVIOUS_ID_SUPPLEMENT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.auditor_previous_id_supplement.v1", {
                "kind": "auditor_previous_identifier", "action": "supplemented",
                "previous_registry_id": match.group("previous_registry_id"),
                "issue_number": match.group("issue_number"),
                "notice_date": _iso_date(match.group("notice_date")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _DE_STATUTES_APPROVED_BY_THREE_AUTHORITIES.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.statutes_approved_by_three_authorities.v1", {
                "kind": "statutes_approved", "action": "approved",
                "approvals": [
                    {
                        "date": _iso_date(match.group(f"date{index}")),
                        "authority": match.group(f"authority{index}").strip(),
                    }
                    for index in (1, 2, 3)
                ],
            },
        )], ""

    match = _FR_DIRECTOR_SIGNING_WITH_ADMINISTRATOR_PROXY_REVOKED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.director_signing_with_administrator_proxy_revoked.v1",
            match.group("name"), place=match.group("place"), role=match.group("role"),
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "appointed_and_signing_changed",
                "co_signs_with": "administrateur", "previous_signing": "procuration",
                "procuration_revoked": True,
            },
        )], ""

    match = _FR_CAPITAL_NOMINAL_REDUCTION_AND_RESTORATION.fullmatch(leftover)
    if match:
        count = _count(match.group("count"))
        reduction = _amount(match.group("reduction"))
        increase = _amount(match.group("increase"))
        from_nominal = _amount(match.group("from_nominal"))
        reduced_nominal = _amount(match.group("reduced_nominal"))
        if (
            reduction == increase
            and abs(reduction - count * (from_nominal - reduced_nominal))
            <= Decimal("0.01")
            and count == _count(match.group("increase_count"))
            and count == _count(match.group("final_count"))
            and reduced_nominal == _amount(match.group("increase_from_nominal"))
            and from_nominal == _amount(match.group("to_nominal"))
            and from_nominal == _amount(match.group("final_nominal"))
            and _amount(match.group("total")) == count * from_nominal
        ):
            return [_event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.capital_nominal_reduction_and_restoration.v1", {
                    "kind": "nominal_reduction_and_simultaneous_increase",
                    "currency": "CHF", "amount": match.group("reduction"),
                    "shares_count": count,
                    "from_nominal": match.group("from_nominal"),
                    "reduced_nominal": match.group("reduced_nominal"),
                    "to_nominal": match.group("to_nominal"),
                    "total": match.group("total"), "fully_paid": True,
                    "share_kind": "actions nominatives",
                },
            )], ""

    match = _FR_TWO_ASSOCIATES_TRANSFER_TO_ORGANIZATION_NO_SEPARATOR.fullmatch(leftover)
    if match and (
        _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and match.group("nominal") == match.group("buyer_nominal")
    ):
        rule_id = "fr.persons.two_associates_transfer_to_organization_no_separator.v1"
        sellers = [match.group("seller1").strip(), match.group("seller2").strip()]
        common = {
            "action": "removed_after_share_transfer",
            "counterparty": match.group("buyer").strip(),
            "aggregate_shares_transferred": _count(match.group("transferred")),
            "share_nominal": match.group("nominal"), "currency": "CHF",
        }
        return [
            *[
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", rule_id, seller, role="associé", extra=common,
                )
                for seller in sellers
            ],
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"),
                place=match.group("place"), uid=match.group("buyer_uid"),
                role="associée", extra={
                    "action": "shares_received", "new_associate": True,
                    "counterparties": sellers,
                    "shares_received": _count(match.group("buyer_count")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ], ""

    match = _FR_TWO_COMMITTEE_MEMBERS_WITH_PRESIDENT.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_committee_members_with_president_or_vice_president.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="membre du comité, trésorier",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group("origin1").strip(),
                    "co_signs_with": "président ou vice-président",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="membre du comité",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group("origin2").strip(),
                    "co_signs_with": "président ou vice-président",
                },
            ),
        ], ""

    match = _FR_MANAGER_TRANSFERS_TO_TWO_UNSIGNED_ASSOCIATES.fullmatch(leftover)
    if match:
        remaining = _count(match.group("remaining"))
        transfer1 = _count(match.group("transferred1"))
        transfer2 = _count(match.group("transferred2"))
        if (
            transfer1 == _count(match.group("buyer_count1"))
            and transfer2 == _count(match.group("buyer_count2"))
            and len({
                match.group("nominal"), match.group("nominal1"),
                match.group("nominal2"), match.group("buyer_nominal1"),
                match.group("buyer_nominal2"),
            }) == 1
        ):
            rule_id = "fr.persons.manager_transfers_to_two_unsigned_associates.v1"
            seller = match.group("seller").strip()
            buyers = [match.group("buyer1").strip(), match.group("buyer2").strip()]
            common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé-gérant", extra={
                        **common, "action": "shares_transferred",
                        "counterparties": buyers,
                        "shares_before": remaining + transfer1 + transfer2,
                        "shares_transferred": transfer1 + transfer2,
                        "shares_count": remaining,
                    },
                ),
                *[
                    _person_event(
                        publication_id, published_at, org_uid, plz, canton,
                        "officer_changed", rule_id, match.group(f"buyer{index}"),
                        place=match.group(f"place{index}"), role="associé", extra={
                            **common, "action": "shares_received",
                            "counterparty": seller, "new_associate": True,
                            "origin": match.group(f"origin{index}").strip(),
                            "shares_received": _count(match.group(f"buyer_count{index}")),
                            "shares_count": _count(match.group(f"buyer_count{index}")),
                            "without_signature": True,
                            **(
                                {"country": match.group("country2")}
                                if index == 2 else {}
                            ),
                        },
                    )
                    for index in (1, 2)
                ],
            ], ""

    match = _FR_ADMINISTRATOR_APPOINTED_VICE_PRESIDENT.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_appointed_vice_president.v1",
            match.group("name"), role="administrateur vice-président",
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "appointed_vice_president", "signing_continues": True,
            },
        )], ""

    match = _DE_DEFINITIVE_MORATORIUM_EXTENDED_TWO_HISTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.definitive_moratorium_extended_two_history.v1", {
                "kind": "composition_moratorium_extended",
                "moratorium_type": "definitive",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "until": _iso_date(match.group("until")),
                "previous_extensions": [
                    {
                        "decision_date": _iso_date(
                            match.group(f"previous_decision_date{index}")
                        ),
                        "until": _iso_date(match.group(f"previous_until{index}")),
                    }
                    for index in (1, 2)
                ],
            },
        )], ""

    match = _FR_COMPANY_ASSET_TRANSFER_CASH_CONSIDERATION.fullmatch(leftover)
    if match and (
        _amount(match.group("assets")) - _amount(match.group("liabilities"))
        == _amount(match.group("consideration"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.company_asset_transfer_cash_consideration.v1", {
                "source_kind": "company",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration_kind": "cash",
                "consideration": match.group("consideration"),
            },
        )], ""

    match = _FR_BANKRUPTCY_PROCEEDINGS_SUSPENDED_ORDINAL_DATE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.bankruptcy_proceedings_suspended_ordinal_date.v1", {
                "kind": "bankruptcy_effect_suspended", "action": "suspended",
                "date": _french_date(match.group("date")),
                "authority": match.group("authority").strip(),
            },
        )], ""

    return [], leftover
