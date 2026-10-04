from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_ASSET_TRANSFER_WITHOUT_CONSIDERATION = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s*"
    r"(?P<assets>[\d'.]+)\s+auf die\s+(?P<recipient>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+"
    r"(?P<place>[^.]+)\.\s*Gegenleistung:\s*(?:Keine|keine)\.?$",
    re.I | re.UNICODE,
)
_FR_SECRETARY_DIRECTOR_BECOMES_SOLE_ADMINISTRATOR = re.compile(
    r"^(?P<name>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<previous_role>secrétaire directeur),\s*reste seul administrateur "
    r"et continue à signer individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_LIQUIDATOR_NAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:n[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens "
    r"qu['’]un administrateur liquidateur porte le nom de\s+"
    r"(?P<name>[^()]+?)\s*\(et non pas\s+(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_IT_ASSET_ACQUISITION_INTENTION_LIMIT_EXCEEDED = re.compile(
    r"^Fatti particolari:\s*A seguito del superamento dell['’]importo massimo "
    r"dell['’]intenzione di assunzione di beni notificata in occasione "
    r"dell['’]aumento di capitale iscritto nel registro di commercio in data\s+"
    r"(?P<registration_date>\d{2}\.\d{2}\.\d{4}),\s*la società ha modificato "
    r"successivamente il proprio statuto in merito alla clausola "
    r"dell['’]intenzione di assunzione di beni come segue:\s*la società intende "
    r"assumere\s+(?P<details>.+?)\.\s*Controprestazione massima:\s*"
    r"(?P<currency>[A-Z]{3})\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_IT_HEAD_OFFICE_MERGER_BRANCH_DELETION_BLOCKED = re.compile(
    r"^Sede principale a:\s*Sede principale:\s*(?P<head_office>[^()]+?)\s*"
    r"\((?P<country>[A-Z]{2})\)\.\s*Nuove disposizioni per la succursale:\s*"
    r"La succursale deve essere cancellata a seguito della fusione della sede "
    r"principale\.\s*La cancellazione non può tuttavia essere effettuata "
    r"mancando il consenso delle autorità fiscali federali e cantonali\.?$",
    re.I | re.UNICODE,
)
_FR_ROLE_CORRECTED_TO_SUBDIRECTOR = re.compile(
    r"^L['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+est sous-directeur\s*"
    r"\(et non pas directeur\)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFERS_TO_TWO_UNSIGNED_ASSOCIATES = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+détient désormais\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+(?P<seller_nominal>[\d'.]+)\s+"
    r"par suite de cession de\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer1>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*et à\s+(?P<buyer2>.+?)\s*"
    r"\((?P<uid2>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<place2>[^()]+?)\s*\((?P<canton2>[A-Z]{2})\),\s*nouveaux associés,\s*"
    r"chacun pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*sans signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_PAIR_DOMICILE_CHANGED = re.compile(
    r"^(?P<name1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+)\s+sont tous deux "
    r"désormais à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_LIQUIDATORS_RESTRICTION_REMOVED = re.compile(
    r"^(?P<name1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+),\s*membres du conseil "
    r"de fondation et liquidateurs,\s*continuent de signer collectivement à "
    r"deux,\s*d[ée]somais sans autre restriction\.?$",
    re.I | re.UNICODE,
)
_FR_CONTRIBUTION_AND_ASSET_ACQUISITION_CLAUSE_REPEALED = re.compile(
    r"^Nouveaux faits qualifiés:\s*\[Abrogation de la clause d['’]apport en "
    r"nature et de reprise de biens\]\s*\[biffé:\s*apport en nature:\s*selon "
    r"convention du\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+et inventaire,\s*sont "
    r"apportés pour CHF\s+(?P<amount>[\d']+\.?)?-?\s*(?P<details>.+?);\s*"
    r"apport accepté pour ce prix et payé par remise à l['’]apporteur de\s+"
    r"(?P<share_count>[\d']+)\s+actions imputées sur le capital\]\.?$",
    re.I | re.UNICODE,
)
_FR_ERRONEOUS_BANKRUPTCY_REGISTRATION_REMOVED = re.compile(
    r"^L['’]Office cantonal des faillites ayant refusé d['’]exécuter le "
    r"jugement du\s+(?P<date>\d{2}\.\d{2}\.\d{4}),\s*l['’]insciption de la "
    r"faillite,\s*opérée à tort,\s*est radiée\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_APPOINTMENT_AND_PRESIDENCY_SUPPLEMENTED = re.compile(
    r"^L['’]inscription\s+(?:n[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est complétée par "
    r"l['’]inscription de\s+(?P<member>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*en qualité de membre du conseil "
    r"d['’]administration et de la qualité de président de l['’]administrateur\s+"
    r"(?P<president>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_APPEAL_SUSPENSIVE_EFFECT = re.compile(
    r"^Mit Verfügung des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+ist der Beschwerde gegen das "
    r"Urteil des\s+(?P<lower_authority>.+?)\s+vom\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+betreffend Konkurseröffnung "
    r"aufschiebende Wirkung zuerkannt worden\.?$",
    re.I | re.UNICODE,
)
_DE_ASSOCIATION_MERGER_PLACE_WITHOUT_COMMA = re.compile(
    r"^Fusion:\s*Übernahme der Aktiven und Passiven des\s+"
    r"(?P<absorbed_name>.+?)\s+in\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*gemäss Fusionsvertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Bilanz per\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\.\s*Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+gehen auf den übernehmenden Verein über\.\s*"
    r"Die Mitglieder des übertragenden Vereins werden zu Mitgliedern des "
    r"übernehmenden Vereins\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_TO_NEW_MANAGER_PRESIDENT = re.compile(
    r"^L['’]associé\s+(?P<seller>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts sociales "
    r"de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé,\s*lequel est en outre nommé "
    r"gérant et président\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PRESIDENT_AND_VICE_PRESIDENT_DIRECTOR = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé président et\s+"
    r"(?P<vice>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"vice-présidente directrice,\s*tous deux\.?$",
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
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser170_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 170."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_ASSET_TRANSFER_WITHOUT_CONSIDERATION.fullmatch(leftover)
    if match:
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.asset_transfer_without_consideration.v1",
                {
                    "date": _iso_date(match.group("date")),
                    "assets": match.group("assets"), "currency": "CHF",
                    "recipient": match.group("recipient").strip(),
                    "recipient_uid": match.group("uid"),
                    "recipient_place": match.group("place").strip(),
                    "consideration_kind": "none",
                },
            )
        ], ""

    match = _FR_SECRETARY_DIRECTOR_BECOMES_SOLE_ADMINISTRATOR.fullmatch(leftover)
    if match:
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed",
                "fr.persons.secretary_director_becomes_sole_administrator.v1",
                match.group("name"), role="seul administrateur",
                signing="Einzelunterschrift", extra={
                    "action": "role_changed",
                    "previous_role": match.group("previous_role").lower(),
                    "signing_continues": True,
                },
            )
        ], ""

    match = _FR_ADMINISTRATOR_LIQUIDATOR_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed",
                "fr.persons.administrator_liquidator_name_corrected.v1",
                match.group("name"), role="administrateur liquidateur", extra={
                    "action": "name_corrected",
                    "previous_name": match.group("previous_name").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                },
            )
        ], ""

    match = _IT_ASSET_ACQUISITION_INTENTION_LIMIT_EXCEEDED.fullmatch(leftover)
    if match:
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed",
                "it.text.asset_acquisition_intention_limit_exceeded.v1",
                {
                    "kind": "asset_acquisition_intention_clause",
                    "action": "modified_after_maximum_exceeded",
                    "capital_increase_registration_date": _iso_date(
                        match.group("registration_date")
                    ),
                    "acquisition_details": match.group("details").strip(),
                    "maximum_consideration": match.group("consideration"),
                    "currency": match.group("currency").upper(),
                },
            )
        ], ""

    match = _IT_HEAD_OFFICE_MERGER_BRANCH_DELETION_BLOCKED.fullmatch(leftover)
    if match:
        rule_id = "it.text.head_office_merger_branch_deletion_blocked.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "seat_changed", rule_id, {
                    "kind": "head_office",
                    "to": match.group("head_office").strip(),
                    "country": match.group("country").upper(),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "branch_deletion_pending",
                    "reason": "head_office_merger",
                    "deletion_blocked": True,
                    "deletion_blocked_reason": (
                        "federal_and_cantonal_tax_authority_consent_missing"
                    ),
                },
            ),
        ], ""

    match = _FR_ROLE_CORRECTED_TO_SUBDIRECTOR.fullmatch(leftover)
    if match:
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.role_corrected_to_subdirector.v1",
                match.group("name"), role="sous-directeur", extra={
                    "action": "role_corrected", "previous_role": "directeur",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                },
            )
        ], ""

    match = _FR_MANAGER_TRANSFERS_TO_TWO_UNSIGNED_ASSOCIATES.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.manager_transfers_to_two_unsigned_associates.v1"
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        common_buyer = {
            "action": "shares_received", "new_associate": True,
            "shares_received": buyer_count, "shares_count": buyer_count,
            "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
            "without_signing_authority": True,
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller"),
                role="associé-gérant", extra={
                    "action": "shares_transferred",
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("seller_nominal"),
                    "currency": "CHF",
                    "counterparties": [
                        match.group("buyer1").strip(), match.group("buyer2").strip()
                    ],
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer1"),
                place=match.group("place1"), role="associé", extra={
                    **common_buyer, "origin": match.group("origin1").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer2"),
                place=match.group("place2"), uid=match.group("uid2"),
                role="associé", extra={
                    **common_buyer, "uid": match.group("uid2"),
                    "place_canton": match.group("canton2").upper(),
                },
            ),
        ], ""

    match = _FR_PAIR_DOMICILE_CHANGED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.pair_domicile_changed_without_label.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(group),
                place=match.group("place"), extra={
                    "action": "domicile_changed", "domicile_changed": True,
                },
            )
            for group in ("name1", "name2")
        ], ""

    match = _FR_FOUNDATION_LIQUIDATORS_RESTRICTION_REMOVED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.foundation_liquidators_restriction_removed.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(group),
                role="membre du conseil de fondation et liquidateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "restriction_removed", "signing_continues": True,
                },
            )
            for group in ("name1", "name2")
        ], ""

    match = _FR_CONTRIBUTION_AND_ASSET_ACQUISITION_CLAUSE_REPEALED.fullmatch(leftover)
    if match:
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed",
                "fr.text.contribution_and_asset_acquisition_clause_repealed.v1",
                {
                    "kind": "contribution_in_kind_and_asset_acquisition_clause",
                    "action": "removed",
                    "agreement_date": _iso_date(match.group("date")),
                    "previous_contribution_value": (match.group("amount") or "").rstrip("."),
                    "currency": "CHF",
                    "previous_contribution_details": match.group("details").strip(),
                    "previous_shares_issued": _count(match.group("share_count")),
                },
            )
        ], ""

    match = _FR_ERRONEOUS_BANKRUPTCY_REGISTRATION_REMOVED.fullmatch(leftover)
    if match:
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "fr.text.erroneous_bankruptcy_registration_removed.v1",
                {
                    "kind": "bankruptcy_registration_revoked",
                    "action": "registration_removed", "registered_in_error": True,
                    "judgment_date": _iso_date(match.group("date")),
                    "reason": "bankruptcy_office_refused_execution",
                },
            )
        ], ""

    match = _FR_BOARD_APPOINTMENT_AND_PRESIDENCY_SUPPLEMENTED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.board_appointment_and_presidency_supplemented.v1"
        reference = {
            "action": "entry_supplemented", "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                place=match.group("place"), role="membre du conseil d'administration",
                extra={**reference, "origin": match.group("origin").strip(),
                       "appointment_supplemented": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="administrateur, président", extra={
                    **reference, "action": "presidency_supplemented",
                },
            ),
        ], ""

    match = _DE_BANKRUPTCY_APPEAL_SUSPENSIVE_EFFECT.fullmatch(leftover)
    if match:
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.bankruptcy_appeal_suspensive_effect.v1",
                {
                    "kind": "bankruptcy_appeal_suspensive_effect",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "authority": match.group("authority").strip(),
                    "bankruptcy_decision_date": _iso_date(
                        match.group("bankruptcy_date")
                    ),
                    "bankruptcy_authority": match.group("lower_authority").strip(),
                    "suspensive_effect": True,
                },
            )
        ], ""

    match = _DE_ASSOCIATION_MERGER_PLACE_WITHOUT_COMMA.fullmatch(leftover)
    if match:
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_merged", "de.text.association_merger_place_without_comma.v1",
                {
                    "kind": "absorption",
                    "absorbed_name": match.group("absorbed_name").strip(),
                    "absorbed_place": match.group("place").strip(),
                    "absorbed_uid": match.group("uid"),
                    "agreement_date": _iso_date(match.group("agreement_date")),
                    "balance_date": _iso_date(match.group("balance_date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"), "currency": "CHF",
                    "members_became_acquirer_members": True,
                },
            )
        ], ""

    match = _FR_ASSOCIATE_TRANSFER_TO_NEW_MANAGER_PRESIDENT.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.associate_transfer_to_new_manager_president.v1"
        transferred = _count(match.group("transferred"))
        remaining = _count(match.group("before")) - transferred
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller"), role="associé",
                extra={
                    "action": "shares_transferred", "shares_transferred": transferred,
                    "shares_before": _count(match.group("before")),
                    "shares_count": remaining,
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                    "counterparty": match.group("buyer").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"),
                place=match.group("place"), role="associé-gérant, président",
                extra={
                    "action": "appointed_manager_president_and_shares_received",
                    "origin": match.group("origin").strip(), "new_associate": True,
                    "shares_received": transferred, "shares_count": transferred,
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
        ], ""

    match = _FR_ADMINISTRATION_PRESIDENT_AND_VICE_PRESIDENT_DIRECTOR.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.president_and_vice_president_director.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="administrateur, président", extra={"action": "appointed_president"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("vice"),
                place=match.group("place"),
                role="administratrice, vice-présidente, directrice", extra={
                    "action": "appointed_vice_president_director",
                    "origin": match.group("origin").strip(),
                },
            ),
        ], ""

    return [], text
