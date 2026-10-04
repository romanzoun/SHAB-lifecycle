from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_CORPORATE_ASSOCIATE_SHARE_TRANSFER = re.compile(
    r"^(?P<seller>.+?)\s*\((?P<seller_registry>[^)]+)\)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>.+?)\s*\((?P<buyer_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<buyer_place>[^,.;]+),\s*nouvelle associée pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"Par conséquent,\s*(?P=seller)\s*\((?P=seller_registry)\)\s+est maintenant "
    r"titulaire de\s+(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_EXPIRED_AND_REINTRODUCED = re.compile(
    r"^\[Streichung der Statutenbestimmung über die mit Ermächtigungsbeschluss vom\s+"
    r"(?P<authorization_date>\d{2}\.\d{2}\.\d{4})\s+eingeführte genehmigte "
    r"Kapitalerhöhung infolge Ablaufs der zeitlichen Befristung\.\]\s*\.\s*"
    r"Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+eine genehmigte Kapitalerhöhung "
    r"gemäss näherer Umschreibung in den Statuten beschlossen\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_APPOINTED_PROXY_REVOKED = re.compile(
    r"^Signature collective à deux a été conférée à\s+(?P<name>[^,.;]+),\s*"
    r"nommé directeur,\s*sa procuration est radiée\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_FOREIGN_MANAGERS = re.compile(
    r"^Nouveaux gérants:\s*(?P<name1>[^,.;]+),\s*des\s+(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,.;]+),\s*(?P<country1>[A-Z]{2,3})\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*des\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*(?P<country2>[A-Z]{2,3})\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_EXECUTIVE_COMMITTEE_PRESIDENT = re.compile(
    r"^Nouvelle membre du comité exécutif\s*:\s*(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*présidente\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_NAME_CORRECTION_AND_PAIR = re.compile(
    r"^L['’]inscription\s+n[o°]\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\)\s+est rectifiée en ce sens que "
    r"l['’]associée et gérante porte le nom\s+(?P<surname>[^,.;]+)\s+et le prénom\s+"
    r"(?P<first_name>[^,.;]+)\.\s*Gérants:\s*(?P<corrected_name>[^,.;]+),\s*"
    r"nommée présidente,\s*et\s+(?P<manager>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_ASSET_TRANSFER_CLAIM_EXTINGUISHED = re.compile(
    r"^Transfert de patrimoine:\s*Selon contrat du\s+"
    r"(?P<date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*la société a transféré des "
    r"actifs pour CHF\s+(?P<assets>[\d'.]+)\s+et des passifs envers les tiers "
    r"pour CHF\s+(?P<liabilities>[\d'.]+),\s*à\s+(?P<recipient>.+?)\s+à\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*extinction de la créance de CHF\s+"
    r"(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_PRESIDENT_NAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+n[o°]\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que la "
    r"nouvelle présidente est\s+(?P<name>[^()]+?)\s*\(et non pas\s+"
    r"(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_SECRETARY_AND_DOMICILE_SIGNING_CHANGED = re.compile(
    r"^(?P<secretary>[^,.;]+),\s*qui est nommé secrétaire,\s*et\s+"
    r"(?P<moved>[^,.;]+),\s*qui est maintenant à\s+(?P<place>[^,.;]+),\s*"
    r"signent désormais individuellement\.?$",
    re.I | re.UNICODE,
)
_IT_CONTRIBUTION_IN_KIND_FOREIGN_INTERESTS = re.compile(
    r"^Fatti particolari:\s*\.\s*Conferimenti in natura:\s*apporto\s+"
    r"(?P<shares1>[\d']+)\s+azioni nominative da CHF\s+"
    r"(?P<nominal1>[\d'.]+)\s+della\s+(?P<source1>.+?)\s+"
    r"\((?P<uid1>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+(?P<place1>[^,.;]+)\s+e di\s+"
    r"(?P<shares2>[\d']+)\s+quota di nominali EUR\s+(?P<nominal2>[\d'.]+)\s+di\s+"
    r"(?P<source2>.+?)\s+\(nr\.\s*(?P<registry2>[^)]+)\),\s*in\s+"
    r"(?P<place2>[^()]+?)\s*\((?P<country2>[A-Z]{2})\)\s+per il valore complessivo "
    r"di CHF\s+(?P<total>[\d'.]+),\s*accettato dalla società per CHF\s+"
    r"(?P<accepted>[\d'.]+),\s*interamente computati sul capitale azionario,\s*"
    r"contro rimessa di\s+(?P<issued>[\d']+)\s+azioni nominative da CHF\s+"
    r"(?P<issued_nominal>[\d'.]+)\.\s*Contratto:\s*"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_MANAGER_PRESIDENT = re.compile(
    r"^Nouveau gérant président:\s*(?P<name>[^,.;]+),\s*de et à\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATION_DISSOLVED_COMMITTEE_LIQUIDATORS = re.compile(
    r"^L['’]association est dissoute par décision de l['’]assemblée générale du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.\s*Liquidateurs:\s*les membres du comité\s+"
    r"(?P<name1>[^,.;]+?)\s+et\s+(?P<name2>[^,.;]+),\s*lesquels continuent à "
    r"signer individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_PAIR_COMPLEX_ROLES_INDIVIDUAL = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?P<role1>président),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*(?P<roles2>vice-présidente,\s*secrétaire et directrice),\s*"
    r"membres du conseil d['’]administration,\s*signent désormais "
    r"individuellement\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_SAME_SHAREHOLDER_CAPITAL_LOSS_COVERED = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di\s+(?P<absorbed_name>.+?),\s*"
    r"in\s+(?P<absorbed_place>[^()]+?)\s*"
    r"\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*secondo contratto di "
    r"fusione del\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+e bilancio al\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta attivi per CHF\s+"
    r"(?P<assets>[\d'.]+),?\s+e passivi verso terzi per CHF\s+"
    r"(?P<liabilities>[\d'.]+)\.\s*La totalità del capitale azionario delle due "
    r"società è detenuta dallo stesso azionista,\s*la fusione avviene dunque senza "
    r"aumento di capitale e senza attribuzione di azioni\.\s*Secondo "
    r"l['’]attestazione di un perito revisore abilitato,\s*la società assuntrice "
    r"dispone di fondi propri liberamente disponibili equivalenti almeno "
    r"all['’]ammontare della perdita di capitale della società trasferente\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_LIQUIDATORS_NAME_CHANGED = re.compile(
    r"^Liquidateurs:\s*l['’]associé gérant\s+(?P<name1>[^,.;]+)\s+et la gérante\s+"
    r"(?P<previous_name>.+?)\s+qui porte désormais le nom de\s+"
    r"(?P<name2>[^,.;]+),\s*lesquels continuent à signer individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_EMPTY_OBLIGATIONS_REMOVED = re.compile(
    r"^\[gestrichen:\s*Pflichten:\s*\]\.?$",
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
    uid: str | None = None,
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
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser168_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 168."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()
    events: list[Event] = []

    match = _FR_CORPORATE_ASSOCIATE_SHARE_TRANSFER.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.corporate_associate_share_transfer.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associée",
                extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "registry_id": match.group("seller_registry"),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("seller_nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("buyer_place"),
                role="associée", uid=match.group("buyer_uid"), extra={
                    "uid": match.group("buyer_uid"), "action": "shares_received",
                    "counterparty": seller, "new_associate": True,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])
        return events, ""

    match = _DE_AUTHORIZED_CAPITAL_EXPIRED_AND_REINTRODUCED.fullmatch(leftover)
    if match:
        rule_id = "de.text.authorized_capital_expired_and_reintroduced.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause", "action": "removed",
                    "authorization_date": _iso_date(match.group("authorization_date")),
                    "reason": "authorization_expired",
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause", "action": "introduced",
                    "decision_date": _iso_date(match.group("decision_date")),
                },
            ),
        ])
        return events, ""

    match = _FR_DIRECTOR_APPOINTED_PROXY_REVOKED.fullmatch(leftover)
    if match:
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.director_appointed_proxy_revoked.v1",
            match.group("name"), role="directeur",
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "appointed_director_and_proxy_revoked",
                "previous_signing": "procuration",
            },
        ))
        return events, ""

    match = _FR_NEW_FOREIGN_MANAGERS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.new_foreign_managers.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="gérant", extra={
                    "action": "appointed", "origin": match.group(f"origin{index}"),
                    "country": match.group(f"country{index}"),
                },
            ))
        return events, ""

    match = _FR_NEW_EXECUTIVE_COMMITTEE_PRESIDENT.fullmatch(leftover)
    if match:
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.executive_committee_president_added.v1",
            match.group("name"), place=match.group("place"),
            role="membre du comité exécutif, présidente", extra={
                "action": "appointed", "origin": match.group("origin").strip(),
            },
        ))
        return events, ""

    match = _FR_MANAGER_NAME_CORRECTION_AND_PAIR.fullmatch(leftover)
    if match and match.group("corrected_name").strip() == (
        f"{match.group('surname').strip()} {match.group('first_name').strip()}"
    ):
        rule_id = "fr.persons.manager_name_correction_and_pair.v1"
        reference = {
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
        }
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("corrected_name"),
                role="associée-gérante, présidente", signing="Einzelunterschrift",
                extra={
                    **reference, "action": "name_corrected_and_appointed_president",
                    "surname": match.group("surname").strip(),
                    "first_name": match.group("first_name").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("manager"),
                place=match.group("place"), role="gérant",
                signing="Einzelunterschrift", extra={
                    **reference, "action": "appointed",
                    "origin": match.group("origin").strip(),
                },
            ),
        ])
        return events, ""

    match = _FR_ASSET_TRANSFER_CLAIM_EXTINGUISHED.fullmatch(leftover)
    if match:
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.asset_transfer_claim_extinguished.v1", {
                "date": _french_date(match.group("date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"), "currency": "CHF",
                "consideration_kind": "claim_extinguished",
                "consideration": match.group("consideration"),
            },
        ))
        return events, ""

    match = _FR_PRESIDENT_NAME_CORRECTED.fullmatch(leftover)
    if match:
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.president_name_corrected.v1",
            match.group("name"), role="présidente", extra={
                "action": "name_corrected", "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))
        return events, ""

    match = _FR_SECRETARY_AND_DOMICILE_SIGNING_CHANGED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.secretary_and_domicile_individual_signing.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("secretary"),
                role="secrétaire", signing="Einzelunterschrift", extra={
                    "action": "appointed_secretary_and_signing_changed",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("moved"),
                place=match.group("place"), signing="Einzelunterschrift", extra={
                    "action": "domicile_and_signing_changed", "domicile_changed": True,
                },
            ),
        ])
        return events, ""

    match = _IT_CONTRIBUTION_IN_KIND_FOREIGN_INTERESTS.fullmatch(leftover)
    if match:
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "it.text.contribution_in_kind_foreign_interests.v1", {
                "kind": "contribution_in_kind", "action": "shares_issued",
                "contributions": [
                    {
                        "source": match.group("source1").strip(),
                        "source_uid": match.group("uid1"),
                        "source_place": match.group("place1").strip(),
                        "interest_count": _count(match.group("shares1")),
                        "interest_kind": "azioni nominative", "currency": "CHF",
                        "interest_nominal": match.group("nominal1"),
                    },
                    {
                        "source": match.group("source2").strip(),
                        "source_registry_id": match.group("registry2"),
                        "source_place": match.group("place2").strip(),
                        "source_country": match.group("country2"),
                        "interest_count": _count(match.group("shares2")),
                        "interest_kind": "quota", "currency": "EUR",
                        "interest_nominal": match.group("nominal2"),
                    },
                ],
                "total_value": match.group("total"),
                "accepted_value": match.group("accepted"), "value_currency": "CHF",
                "credited_to_share_capital": True,
                "shares_issued": _count(match.group("issued")),
                "share_kind": "azioni nominative",
                "share_nominal": match.group("issued_nominal"),
                "agreement_date": _iso_date(match.group("agreement_date")),
            },
        ))
        return events, ""

    match = _FR_NEW_MANAGER_PRESIDENT.fullmatch(leftover)
    if match:
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.new_manager_president_same_origin_place.v1",
            match.group("name"), place=match.group("place"),
            role="gérant président", extra={
                "action": "appointed", "origin": match.group("place").strip(),
            },
        ))
        return events, ""

    match = _FR_ASSOCIATION_DISSOLVED_COMMITTEE_LIQUIDATORS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.association_dissolved_committee_liquidators.v1"
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", rule_id, {
                "kind": "dissolution", "action": "dissolved",
                "decision_date": _iso_date(match.group("date")),
                "authority": "assemblée générale",
            },
        ))
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="membre du comité, liquidateur",
                signing="Einzelunterschrift", extra={
                    "action": "appointed_liquidator", "signing_continues": True,
                },
            ))
        return events, ""

    match = _FR_BOARD_PAIR_COMPLEX_ROLES_INDIVIDUAL.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.board_pair_complex_roles_individual_signing.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name1"),
                role="membre du conseil d'administration, président",
                signing="Einzelunterschrift", extra={"action": "signing_changed"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name2"),
                role=("membre du conseil d'administration, " + match.group("roles2")),
                signing="Einzelunterschrift", extra={"action": "signing_changed"},
            ),
        ])
        return events, ""

    match = _IT_MERGER_SAME_SHAREHOLDER_CAPITAL_LOSS_COVERED.fullmatch(leftover)
    if match:
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "it.text.merger_same_shareholder_capital_loss_covered.v1", {
                "kind": "absorption",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "currency": "CHF", "same_shareholder": True,
                "capital_increase": False, "share_allocation": False,
                "capital_loss_covered_by_acquirer_free_equity": True,
                "coverage_confirmed_by_auditor": True,
            },
        ))
        return events, ""

    match = _FR_MANAGER_LIQUIDATORS_NAME_CHANGED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.manager_liquidators_name_changed.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role="associé-gérant, liquidateur", signing="Einzelunterschrift",
                extra={"action": "appointed_liquidator", "signing_continues": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                role="gérante, liquidatrice", signing="Einzelunterschrift", extra={
                    "action": "name_changed_and_appointed_liquidator",
                    "previous_name": match.group("previous_name").strip(),
                    "signing_continues": True,
                },
            ),
        ])
        return events, ""

    if _DE_EMPTY_OBLIGATIONS_REMOVED.fullmatch(leftover):
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.empty_obligations_entry_removed.v1", {
                "kind": "obligations", "action": "removed",
                "previous_detail_available": False,
            },
        ))
        return events, ""

    return [], text
