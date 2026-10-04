from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_FR_COUNCIL_COMPOSITION_MENTION_REMOVED_SHORT = re.compile(
    r"^Radiation de la mention relative à la composition du conseil\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_PRIVILEGES_REMOVED = re.compile(
    r"^Les\s+(?P<preferred_count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<preferred_nominal>[\d'.]+)\s+ne sont désormais plus privilégiées "
    r"quant au dividende et au produit de liquidation\.\s*Le capital-actions "
    r"de CHF\s+(?P<total>[\d'.]+),\s*entièrement libéré,\s*est maintenant "
    r"divisé en\s+(?P<count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<nominal>[\d'.]+)"
    r"(?:,\s*avec restrictions quant à la transmissibilité selon statuts)?\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_SIGNING_CHANGED = re.compile(
    r"^L['’]associé\s+(?P<name>[^,.;]+),\s*signe désormais "
    r"collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_IT_SOLE_OWNER_ACTIVITY_CONTINUES = re.compile(
    r"^Il titolare continua la sua attività,\s*l['’]iscrizione sussiste\.?$",
    re.I | re.UNICODE,
)
_DE_ASSOCIATE_NAME_SHARES_ORIGIN_AND_NEW_ASSOCIATE = re.compile(
    r"^Eingetragene Person geändert:\s*(?P<previous_name>[^,.;]+),\s*"
    r"korrekterweise\s+(?P<name>[^,.;]+),\s*Gesellschafterin,\s*"
    r"(?P<previous_count>[\d']+)\s+Stammanteile zu CHF\s+"
    r"(?P<previous_nominal>[\d'.]+),\s*Geschäftsführerin,\s*"
    r"Einzelunterschrift,\s*neu Gesellschafterin,\s*"
    r"(?P<count>[\d']+)\s+Stammanteile zu CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"Geschäftsführerin,\s*Einzelunterschrift,\s*nun von\s+"
    r"(?P<origin>.+?)\.\s*Neu eingetragene Person:\s*"
    r"(?P<new_name>[^,.;]+),\s*(?P<nationality>[^,.;]+),\s*in\s+"
    r"(?P<place>[^,.;]+),\s*Gesellschafterin,\s*"
    r"(?P<new_count>[\d']+)\s+Stammanteile zu CHF\s+"
    r"(?P<new_nominal>[\d'.]+),\s*ohne Unterschrift\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFERS_TO_EXISTING_MANAGER = re.compile(
    r"^L['’]associé-gérant et président\s+(?P<seller>[^,.;]+)\s+détient "
    r"désormais\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+par suite de cession de\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<transfer_nominal>[\d'.]+)\s+au gérant\s+(?P<buyer>[^,.;]+),\s*"
    r"désormais associé pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\s+et qui continue de signer "
    r"collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_LIQUIDATION_WITH_LIQUIDATOR_AND_MANAGER_REMOVED = re.compile(
    r"^La liquidation est opérée sous la raison de commerce:\s*"
    r"(?P<company_name>.+? en liquidation),\s*par\s+"
    r"(?P<liquidator>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*élue liquidatrice"
    r"(?P<liquidator_signing>\s+avec signature individuelle\.)?\s*"
    r"L['’]associé\s+"
    r"(?P<removed>[^,.;]+)\s+[mn]['’]est plus gérant;\s*sa signature est "
    r"radiée\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_APPOINTMENTS_AND_SIGNING = re.compile(
    r"^L['’]administrateur\s+(?P<president>[^,.;]+)\s+est élu président\.\s*"
    r"Nouvel administrateur avec(?: signature collective à deux avec)? le "
    r"président ou un directeur:\s*"
    r"(?P<administrator>[^,.;]+),\s*de\s+(?P<administrator_origin>[^,.;]+),\s*"
    r"à\s+(?P<administrator_place>[^,.;]+)\.\s*Signature collective à deux "
    r"avec le président ou le vice-président est conférée à\s+"
    r"(?P<director1>[^,.;]+),\s*à\s+(?P<director1_place>[^,.;]+),\s*"
    r"(?P<director1_role>directeur général adjoint),\s*et\s+"
    r"(?P<director2>[^,.;]+),\s*à\s+(?P<director2_place>[^,.;]+),\s*"
    r"(?P<director2_role>directeur général),\s*tous deux de\s+"
    r"(?P<directors_origin>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED = re.compile(
    r"^Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+die Statutenbestimmung über "
    r"die bedingte Kapitalerhöhung vom\s+"
    r"(?P<authorization_date>\d{2}\.\d{2}\.\d{4})\s+geändert\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_FULLY_OWNED_WITH_CAPITAL_LOSS_CONFIRMATION = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di\s+(?P<absorbed_name>.+?),\s*"
    r"in\s+(?P<absorbed_place>[^()]+?)\s*"
    r"\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*secondo il contratto "
    r"di fusione del\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+e bilancio "
    r"al\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta attivi per "
    r"CHF\s+(?P<assets>[\d'.]+)\s+e passivi verso terzi per CHF\s+"
    r"(?P<liabilities>[\d'.]+)\.\s*La società assuntrice detiene tutte le "
    r"azioni della società trasferente,\s*per cui la fusione avviene senza "
    r"aumento di capitale e senza attribuzione di azioni\.\s*Conformemente "
    r"all['’]attestazione di un perito revisore abilitato,\s*la società "
    r"assuntrice dispone di fondi propri liberamente disponibili equivalenti "
    r"almeno all['’]ammontare della perdita di capitale della società "
    r"trasferente\.?$",
    re.I | re.UNICODE,
)
_DE_LIMITED_PARTNERSHIP_CAPITAL_NEW = re.compile(
    r"^Kommanditsumme neu:\s*CHF\s+(?P<total>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_CONTRIBUTION_AGREEMENT_REPLACED_NOTARY_JURISDICTION = re.compile(
    r"^Infolge örtlicher Unzuständigkeit der Urkundsperson wird der "
    r"öffentlich-beurkundete Sacheinlage- und Sachübernahmevertrag vom\s+"
    r"(?P<previous_date>\d{1,2}\.\s+[A-Za-zÄÖÜäöü]+\s+\d{4})\s+über den "
    r"gleichen Sacheinlagegegenstand durch den öffentlich-beurkundeten "
    r"Sacheinlage- und Sachübernahmevertrag vom\s+"
    r"(?P<date>\d{1,2}\.\s+[A-Za-zÄÖÜäöü]+\s+\d{4})\s+ersetzt\.?$",
    re.I | re.UNICODE,
)
_DE_FEMALE_OWNER_BANKRUPTCY_APPEAL_SUSPENDED_HISTORY = re.compile(
    r"^Mit Verfügung vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+der Beschwerde der Inhaberin gegen das "
    r"erstinstanzliche Konkurserkenntnis die aufschiebende Wirkung erteilt\.\s*"
    r"\[gestrichen:\s*Mit Entscheid des\s+(?P<previous_authority>.+?)\s+vom\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+wurde über die Inhaberin "
    r"dieses Einzelunternehmens mit Wirkung ab dem\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}[:.]\d{2})\s+Uhr,\s*der Konkurs eröffnet\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_AUDITOR_REGISTRY_ID_LAST_MUTATION_SUPPLEMENT = re.compile(
    r"^Bei der letzten Mutation wurde die bisherige Firmennummer nicht "
    r"publiziert\.\s*Deshalb erfolgt folgender Nachtrag:\s*(?P<name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+"
    r"(?P<place>[^,.;]+),\s*(?P<role>Revisionsstelle)\s*"
    r"\[bisher:\s*(?P<previous_name>.+?)\s*"
    r"\((?P<previous_registry_id>CH-[\d.]+-\d)\)\]\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_ASSET_TRANSFER_NO_CONSIDERATION = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4}),\s*la fondation a transféré "
    r"des actifs de CHF\s+(?P<assets>[\d'.]+)\s+et des passifs envers les "
    r"tiers de CHF\s+(?P<liabilities>[\d'.]+),\s*à\s+(?P<recipient>.+?),\s*"
    r"à\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*sans contre-prestation\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDING_MEETING_AUTHORIZED_CAPITAL = re.compile(
    r"^Die Gründungsversammlung hat mit Beschluss vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+eine genehmigte "
    r"Kapitalerhöhung gemäss näherer Umschreibung in den Statuten "
    r"beschlossen\.?$",
    re.I | re.UNICODE,
)


_DE_MONTHS = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _german_date(raw: str) -> str:
    day, month, year = raw.replace(".", "", 1).casefold().split()
    return f"{int(year):04d}-{_DE_MONTHS[month]:02d}-{int(day):02d}"


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


def extract_parser196_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 196."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_COUNCIL_COMPOSITION_MENTION_REMOVED_SHORT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "fr.text.council_composition_mention_removed_short.v1", {
                "kind": "council_composition_mention", "action": "removed",
            },
        )], ""

    match = _FR_SHARE_PRIVILEGES_REMOVED.fullmatch(leftover)
    if match and (
        _count(match.group("count")) * _amount(match.group("nominal"))
        == _amount(match.group("total"))
        and match.group("preferred_nominal") == match.group("nominal")
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.share_privileges_removed.v1", {
                "kind": "share_privileges", "action": "removed",
                "removed_privileges": ["dividend", "liquidation_proceeds"],
                "preferred_shares_count": _count(match.group("preferred_count")),
                "share_kind": "actions nominatives",
                "shares_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"),
                "total": match.group("total"), "currency": "CHF",
                "fully_paid": True,
            },
        )], ""

    match = _FR_ASSOCIATE_SIGNING_CHANGED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.associate_signing_collective.v1",
            match.group("name"), role="associé",
            signing="Kollektivunterschrift zu zweien",
            extra={"action": "signing_changed"},
        )], ""

    match = _IT_SOLE_OWNER_ACTIVITY_CONTINUES.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.sole_owner_activity_registration_continues.v1", {
                "kind": "registration_continues", "scope": "sole_proprietor",
                "action": "continued", "activity_continues": True,
            },
        )], ""

    match = _DE_ASSOCIATE_NAME_SHARES_ORIGIN_AND_NEW_ASSOCIATE.fullmatch(leftover)
    if match and (
        match.group("previous_nominal") == match.group("nominal")
        == match.group("new_nominal")
        and _count(match.group("previous_count"))
        == _count(match.group("count")) + _count(match.group("new_count"))
    ):
        rule_id = "de.persons.associate_name_shares_origin_and_new_associate.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                role="Gesellschafterin, Geschäftsführerin",
                signing="Einzelunterschrift", extra={
                    "action": "name_shares_and_origin_changed",
                    "previous_name": match.group("previous_name").strip(),
                    "previous_shares_count": _count(match.group("previous_count")),
                    "shares_count": _count(match.group("count")),
                    "shares_transferred": _count(match.group("new_count")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                    "origin": match.group("origin").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("new_name"),
                place=match.group("place"), role="Gesellschafterin",
                extra={
                    "action": "appointed_and_shares_received", "new_associate": True,
                    "nationality": match.group("nationality").strip(),
                    "shares_received": _count(match.group("new_count")),
                    "shares_count": _count(match.group("new_count")),
                    "share_nominal": match.group("new_nominal"), "currency": "CHF",
                    "without_signature": True,
                },
            ),
        ], ""

    match = _FR_MANAGER_TRANSFERS_TO_EXISTING_MANAGER.fullmatch(leftover)
    if match and (
        _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and len({
            match.group("nominal"), match.group("transfer_nominal"),
            match.group("buyer_nominal"),
        }) == 1
    ):
        rule_id = "fr.persons.manager_transfers_to_existing_manager.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        remaining = _count(match.group("remaining"))
        transferred = _count(match.group("transferred"))
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller,
                role="associé-gérant et président", extra={
                    **common, "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": remaining + transferred,
                    "shares_transferred": transferred, "shares_count": remaining,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, role="associé-gérant",
                signing="Kollektivunterschrift zu zweien", extra={
                    **common, "action": "shares_received", "counterparty": seller,
                    "became_associate": True, "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "signing_continues": True,
                },
            ),
        ], ""

    match = _FR_LIQUIDATION_WITH_LIQUIDATOR_AND_MANAGER_REMOVED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.liquidator_appointed_manager_removed_fragment.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("liquidator"),
                place=match.group("place"), role="liquidatrice",
                signing=(
                    "Einzelunterschrift"
                    if match.group("liquidator_signing") else None
                ), extra={
                    "action": "appointed", "origin": match.group("origin").strip(),
                    "liquidation_company_name": match.group("company_name").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group("removed"),
                role="associé-gérant", extra={
                    "action": "manager_removed", "signature_revoked": True,
                },
            ),
        ], ""

    match = _FR_BOARD_APPOINTMENTS_AND_SIGNING.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.board_appointments_and_signing_groups.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="administrateur président", extra={"action": "appointed_president"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("administrator"),
                place=match.group("administrator_place"), role="administrateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group("administrator_origin").strip(),
                    "co_signs_with": "président ou directeur",
                },
            ),
            *[
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", rule_id, match.group(f"director{index}"),
                    place=match.group(f"director{index}_place"),
                    role=match.group(f"director{index}_role"),
                    signing="Kollektivunterschrift zu zweien", extra={
                        "action": "signing_granted",
                        "origin": match.group("directors_origin").strip(),
                        "co_signs_with": "président ou vice-président",
                    },
                )
                for index in (1, 2)
            ],
        ], ""

    match = _DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.conditional_capital_clause_changed_dates.v1", {
                "kind": "conditional_capital_clause", "action": "changed",
                "decision_date": _iso_date(match.group("decision_date")),
                "authorization_date": _iso_date(match.group("authorization_date")),
            },
        )], ""

    match = _IT_MERGER_FULLY_OWNED_WITH_CAPITAL_LOSS_CONFIRMATION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "it.text.merger_fully_owned_capital_loss_confirmation.v1", {
                "kind": "absorption", "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "currency": "CHF", "all_shares_held_by_acquirer": True,
                "capital_increase": False, "share_allocation": False,
                "capital_loss_covered_by_free_equity": True,
                "auditor_confirmation": True,
            },
        )], ""

    match = _DE_LIMITED_PARTNERSHIP_CAPITAL_NEW.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.limited_partnership_capital_new.v1", {
                "kind": "limited_partnership_capital", "action": "changed",
                "to": match.group("total"), "currency": "CHF",
            },
        )], ""

    match = _DE_CONTRIBUTION_AGREEMENT_REPLACED_NOTARY_JURISDICTION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected",
            "de.text.contribution_agreement_replaced_notary_jurisdiction.v1", {
                "kind": "contribution_in_kind_and_asset_acquisition_agreement",
                "action": "supporting_document_replaced",
                "previous_agreement_date": _german_date(match.group("previous_date")),
                "agreement_date": _german_date(match.group("date")),
                "same_contribution_asset": True,
                "reason": "notary_lacked_local_jurisdiction",
            },
        )], ""

    match = _DE_FEMALE_OWNER_BANKRUPTCY_APPEAL_SUSPENDED_HISTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.female_owner_bankruptcy_appeal_suspended_history.v1", {
                "kind": "bankruptcy_effect_suspended", "scope": "owner",
                "action": "suspensive_effect_granted",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "previous_authority": match.group("previous_authority").strip(),
                "effective_date": _iso_date(match.group("effective_date")),
                "effective_time": match.group("effective_time").replace(".", ":"),
                "previous_entry_removed": True,
            },
        )], ""

    match = _DE_AUDITOR_REGISTRY_ID_LAST_MUTATION_SUPPLEMENT.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.auditor_registry_id_last_mutation_supplement.v1",
            match.group("name"), place=match.group("place"), uid=match.group("uid"),
            role=match.group("role"), extra={
                "action": "registry_id_supplemented",
                "previous_name": match.group("previous_name").strip(),
                "previous_registry_id": match.group("previous_registry_id"),
            },
        )], ""

    match = _FR_FOUNDATION_ASSET_TRANSFER_NO_CONSIDERATION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.foundation_asset_transfer_no_consideration.v1", {
                "source_kind": "foundation",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration_kind": "none", "gratuitous": True,
            },
        )], ""

    match = _DE_FOUNDING_MEETING_AUTHORIZED_CAPITAL.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.founding_meeting_authorized_capital.v1", {
                "kind": "authorized_capital_clause", "action": "introduced",
                "decision_date": _iso_date(match.group("decision_date")),
                "deciding_body": "Gründungsversammlung", "details_in_statutes": True,
            },
        )], ""

    return [], leftover
