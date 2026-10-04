from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_DISSOLUTION_CORPORATE_LIQUIDATOR = re.compile(
    r"^Die Gesellschaft ist laut Beschluss der Generalversammlung vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+aufgelöst\.\s*"
    r"Neu eingetragene Person:\s*(?P<name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+"
    r"(?P<place>[^,.;]+),\s*(?P<role>Liquidatorin)\.\s*"
    r"Liquidationsadresse:\s*(?P<address>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_NAME_CORRECTED_NOTICE = re.compile(
    r"^L['’]inscription\s+(?:no|n°)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens qu['’]un "
    r"administrateur porte le nom de\s+(?P<name>[^()]+?)\s*"
    r"\(et non pas\s+(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_APPEAL_SUSPENSIVE_EFFECT = re.compile(
    r"^Par arrêt du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>.+?)\s+a accordé l['’]effet suspensif au recours interjeté le\s+"
    r"(?P<appeal_date>\d{2}\.\d{2}\.\d{4})\s+contre la décision de faillite "
    r"prononcée le\s+(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_EXCEPT_LIST_SAME_ORIGIN = re.compile(
    r"^Nouveau membre du conseil de fondation toutefois pas avec\s+"
    r"(?P<excluded>.+?)\s*:\s*(?P<name>[^,.;]+),\s*de et à\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_CORPORATE_ASSOCIATE_NEW_NAME = re.compile(
    r"^Nouvelle raison sociale de l['’]associée:\s*(?P<name>.+?)\s*"
    r"\((?P<registry_id>RSIN\s+\d+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_AUTHORIZED_CAPITAL_CLAUSE_REPLACED = re.compile(
    r"^Suppression de la clause statutaire relative à l['’]augmentation "
    r"autorisée du capital\s*\(fondée sur la décision d['’]autorisation du\s+"
    r"(?P<previous_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\)\s*\.\s*"
    r"L['’]assemblée générale a introduit une clause statutaire relative à "
    r"une augmentation autorisée du capital par décision du\s+"
    r"(?P<decision_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.\s*"
    r"Pour les détails,\s*voir les statuts\.?$",
    re.I | re.UNICODE,
)
_DE_PERSON_NAME_SIGNING_AND_DOMICILE_CORRECTED = re.compile(
    r"^Eingetragene Person geändert:\s*(?P<previous_name>[^,.;]+),\s*"
    r"korrekterweise\s+(?P<name>[^,.;]+),\s*"
    r"(?P<previous_role1>Gesellschafterin),\s*(?P<previous_count>[\d']+)\s+"
    r"Stammanteile zu CHF\s+(?P<previous_nominal>[\d'.]+),\s*"
    r"(?P<previous_role2>Geschäftsführerin),\s*"
    r"(?P<previous_signing>Einzelunterschrift),\s*neu\s+"
    r"(?P<role>Gesellschafterin),\s*(?P<count>[\d']+)\s+Stammanteile zu CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*(?P<signing>ohne Unterschrift),\s*"
    r"nun in\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_NEW_BRANCH = re.compile(
    r"^Zweigniederlassung neu:\s*(?P<place>[^,.;]+?)\s+"
    r"(?P<branch_canton>[A-Z]{2})\.?$",
    re.I | re.UNICODE,
)
_DE_AUDITOR_REGISTRY_ID_SUPPLEMENT = re.compile(
    r"^Bei der nachfolgenden Mutation wurde die bisherige Firmennummer nicht "
    r"publiziert\.\s*Deshalb erfolgt folgender Nachtrag:\s*(?P<name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+"
    r"(?P<place>[^,.;]+),\s*(?P<role>Revisionsstelle)\s*"
    r"\[bisher:\s*(?P<previous_name>.+?)\s*"
    r"\((?P<previous_registry_id>CH-[\d.]+-\d)\)\]\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_CLAUSE_REPLACED = re.compile(
    r"^\[gestrichen:\s*Mit Beschluss der Generalversammlung vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+wird die "
    r"Statutenbestimmung über die mit Ermächtigungsbeschluss vom\s+"
    r"(?P<previous_authorization_date>\d{2}\.\d{2}\.\d{4})\s+beschlossene "
    r"genehmigte Kapitalerhöhung angepasst\.\]\.?\s*Die Gesellschaft hat mit "
    r"Beschluss vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+eine genehmigte "
    r"Kapitalerhöhung gemäss näherer Umschreibung in den Statuten beschlossen\.?$",
    re.I | re.UNICODE,
)
_IT_SOLE_PROPRIETOR_ASSET_TRANSFER_NO_CONSIDERATION = re.compile(
    r"^Trasferimento di patrimonio:\s*secondo contratto del\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+la società ha trasferito alla "
    r"ditta individuale\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"attivi per CHF\s+(?P<assets>[\d'.]+)\s+e passivi verso terzi per CHF\s+"
    r"(?P<liabilities>[\d'.]+)\.\s*Controprestazione:\s*(?P<consideration>nessuna)\.?$",
    re.I | re.UNICODE,
)
_FR_OWNER_BANKRUPTCY_APPEAL_SUSPENSIVE_HISTORY = re.compile(
    r"^La titulaire a interjeté appel contre le jugement de faillite du\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.\s*Par ordonnance du\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*(?P<authority>.+?)\s+a accordé "
    r"l['’]effet suspensif à l['’]appel\.\s*\[précédemment:\s*Par décision du\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<previous_authority>.+?)\s+a prononcé la faillite de la titulaire de "
    r"l['’]entreprise individuelle avec effet au\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*à\s+"
    r"(?P<effective_time>\d{1,2}[.:]\d{2})\s+heures\.\]\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_ALL_QUOTAS = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di\s+(?P<absorbed_name>.+?),\s*"
    r"in\s+(?P<absorbed_place>[^()]+?)\s*"
    r"\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*secondo il contratto "
    r"di fusione del\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+e bilancio al\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta attivi per CHF\s+"
    r"(?P<assets>[\d'.]+)\s+e passivi verso terzi per CHF\s+"
    r"(?P<liabilities>[\d'.]+)\.\s*La società assuntrice detiene tutte le quote "
    r"della società trasferente,\s*per cui la fusione avviene senza aumento di "
    r"capitale e senza attribuzione di quote\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATORS_PRESIDENCY_CHANGED = re.compile(
    r"^Les administrateurs\s+(?P<name1>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<previous_role1>vice-président),\s*nommé\s+(?P<role1>président),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*jusqu['’]ici\s+(?P<previous_role2>président),\s*"
    r"continuent à signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_TO_NEW_MANAGER_PRESIDENT = re.compile(
    r"^(?P<seller>[^,.;]+)\s+a cédé\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*du\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"lequel associé est en outre nommé\s+(?P<role>gérant-président)\.?$",
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
    day, month, year = raw.casefold().replace("1er", "1").split()
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


def extract_parser177_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 177."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_DISSOLUTION_CORPORATE_LIQUIDATOR.fullmatch(leftover)
    if match:
        rule_id = "de.text.dissolution_corporate_liquidator_address.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "dissolution", "action": "dissolved",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "deciding_body": "Generalversammlung",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), uid=match.group("uid"),
                role=match.group("role"), extra={"action": "appointed"},
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", rule_id, {
                    "kind": "liquidation_address", "action": "changed",
                    "to": match.group("address").strip(),
                },
            ),
        ], ""

    match = _FR_ADMINISTRATOR_NAME_CORRECTED_NOTICE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_name_corrected_notice.v1",
            match.group("name"), role="administrateur", extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_BANKRUPTCY_APPEAL_SUSPENSIVE_EFFECT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.bankruptcy_appeal_suspensive_effect_simple.v1", {
                "kind": "bankruptcy_effect_suspended",
                "action": "suspended_on_appeal",
                "decision_date": _iso_date(match.group("decision_date")),
                "appeal_date": _iso_date(match.group("appeal_date")),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "authority": match.group("authority").strip(),
            },
        )], ""

    match = _FR_FOUNDATION_MEMBER_EXCEPT_LIST_SAME_ORIGIN.fullmatch(leftover)
    if match:
        excluded = [
            value.strip()
            for value in re.split(r"\s*,\s*(?:ni\s+)?|\s+et\s+", match.group("excluded"))
            if value.strip()
        ]
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.foundation_member_except_list_same_origin.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil de fondation",
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "appointed", "origin": match.group("place").strip(),
                "excluded_co_signers": excluded,
            },
        )], ""

    match = _FR_CORPORATE_ASSOCIATE_NEW_NAME.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "fr.text.corporate_associate_new_name.v1", {
                "kind": "corporate_associate", "action": "name_changed",
                "name": match.group("name").strip(),
                "registry_id": match.group("registry_id").strip(),
            },
        )], ""

    match = _FR_AUTHORIZED_CAPITAL_CLAUSE_REPLACED.fullmatch(leftover)
    if match:
        rule_id = "fr.text.authorized_capital_clause_replaced_with_dates.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause", "action": "removed",
                    "authorization_date": _french_date(match.group("previous_date")),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause", "action": "introduced",
                    "decision_date": _french_date(match.group("decision_date")),
                    "details_in_statutes": True,
                },
            ),
        ], ""

    match = _DE_PERSON_NAME_SIGNING_AND_DOMICILE_CORRECTED.fullmatch(leftover)
    if match and (
        _count(match.group("previous_count")) == _count(match.group("count"))
        and match.group("previous_nominal") == match.group("nominal")
    ):
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.name_signing_domicile_corrected.v1",
            match.group("name"), place=match.group("place"),
            role=match.group("role"), extra={
                "action": "name_signing_and_domicile_changed",
                "previous_name": match.group("previous_name").strip(),
                "previous_roles": [
                    match.group("previous_role1"), match.group("previous_role2")
                ],
                "previous_signing": match.group("previous_signing"),
                "without_signature": True,
                "shares_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"), "currency": "CHF",
            },
        )], ""

    match = _DE_NEW_BRANCH.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.new_branch_place_canton.v1", {
                "action": "added", "place": match.group("place").strip(),
                "branch_canton": match.group("branch_canton"),
            },
        )], ""

    match = _DE_AUDITOR_REGISTRY_ID_SUPPLEMENT.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.auditor_registry_id_supplement.v1",
            match.group("name"), place=match.group("place"), uid=match.group("uid"),
            role=match.group("role"), extra={
                "action": "registry_id_supplemented",
                "previous_name": match.group("previous_name").strip(),
                "previous_registry_id": match.group("previous_registry_id"),
            },
        )], ""

    match = _DE_AUTHORIZED_CAPITAL_CLAUSE_REPLACED.fullmatch(leftover)
    if match:
        rule_id = "de.text.authorized_capital_clause_replaced.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause", "action": "previous_entry_removed",
                    "previous_decision_date": _iso_date(
                        match.group("previous_decision_date")
                    ),
                    "previous_authorization_date": _iso_date(
                        match.group("previous_authorization_date")
                    ),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause", "action": "introduced",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "details_in_statutes": True,
                },
            ),
        ], ""

    match = _IT_SOLE_PROPRIETOR_ASSET_TRANSFER_NO_CONSIDERATION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "it.text.sole_proprietor_asset_transfer_no_consideration.v1", {
                "source_kind": "company",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities", "currency": "CHF",
                "recipient_kind": "sole_proprietor",
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration_kind": "none", "gratuitous": True,
            },
        )], ""

    match = _FR_OWNER_BANKRUPTCY_APPEAL_SUSPENSIVE_HISTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.owner_bankruptcy_appeal_suspensive_history.v1", {
                "kind": "bankruptcy_effect_suspended", "scope": "owner",
                "action": "suspended_on_appeal",
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "previous_decision_date": _iso_date(
                    match.group("previous_decision_date")
                ),
                "previous_authority": match.group("previous_authority").strip(),
                "effective_date": _iso_date(match.group("effective_date")),
                "effective_time": match.group("effective_time").replace(".", ":"),
                "previous_entry_removed": True,
            },
        )], ""

    match = _IT_MERGER_ALL_QUOTAS.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "it.text.merger_acquirer_owns_all_quotas.v1", {
                "kind": "absorption",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities", "currency": "CHF",
                "acquirer_owns_all_quotas": True,
                "capital_increase": False, "quota_allocation": False,
            },
        )], ""

    match = _FR_ADMINISTRATORS_PRESIDENCY_CHANGED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administrators_presidency_changed.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role=match.group("role1"),
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "role_changed", "previous_role": match.group("previous_role1"),
                    "signing_continues": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                role="administrateur", signing="Kollektivunterschrift zu zweien", extra={
                    "action": "presidency_ended", "previous_role": match.group("previous_role2"),
                    "signing_continues": True,
                },
            ),
        ], ""

    match = _FR_SHARE_TRANSFER_TO_NEW_MANAGER_PRESIDENT.fullmatch(leftover)
    if match and (
        _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and match.group("nominal") == match.group("buyer_nominal")
    ):
        rule_id = "fr.persons.share_transfer_new_manager_president_simple.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {
            "shares_count": _count(match.group("buyer_count")),
            "share_nominal": match.group("nominal"), "currency": "CHF",
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé", extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_transferred": _count(match.group("transferred")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role=match.group("role"), extra={
                    **common, "action": "appointed_and_shares_received",
                    "counterparty": seller, "origin": match.group("origin").strip(),
                    "new_associate": True,
                },
            ),
        ], ""

    return [], text
