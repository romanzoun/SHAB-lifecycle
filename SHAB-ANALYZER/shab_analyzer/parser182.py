from __future__ import annotations

import re
from decimal import Decimal

from .keys import person_key
from .models import Event


_FR_NAME_SPLIT_AND_PARTICIPATION_CLAUSES = re.compile(
    r"^Nouvelle raison de commerce:\s*(?P<name>.+?)\.\s*"
    r"Les (?P<from_count>[\d']+) actions nominatives de CHF "
    r"(?P<from_nominal>[\d'.]+),\s*formant l['’]entier du capital-actions,\s*"
    r"sont transformées en (?P<to_count>[\d']+) actions nominatives de CHF "
    r"(?P<to_nominal>[\d'.]+),\s*(?P<restriction>avec restrictions quant à "
    r"la transmissibilité selon statuts\.\s*)?L['’]assemblée générale a introduit une "
    r"clause statutaire relative à la création autorisée d['’]un "
    r"capital-participation par décision du (?P<authorized_date>\d{1,2} "
    r"[A-Za-zÀ-ÿ]+ \d{4})\.\s*Pour les détails,\s*voir les statuts\.\s*"
    r"L['’]assemblée générale a introduit une clause statutaire relative à la "
    r"création conditionnelle d['’]un capital-participation par décision du "
    r"(?P<conditional_date>\d{1,2} [A-Za-zÀ-ÿ]+ \d{4})\.\s*"
    r"Pour les détails,\s*voir les statuts\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_TO_EXISTING_MANAGER = re.compile(
    r"^Jusqu['’]ici titulaire de (?P<before>[\d']+) parts de CHF "
    r"(?P<nominal>[\d'.]+),\s*l['’]associé-gérant (?P<seller>[^,.;]+) "
    r"détient (?P<remaining>[\d']+) parts de CHF "
    r"(?P<remaining_nominal>[\d'.]+) par suite de cession de "
    r"(?P<transferred>[\d']+) parts au gérant (?P<buyer>[^,.;]+),\s*"
    r"nouvel associé (?P<buyer_count>[\d']+) parts de CHF "
    r"(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_ASSET_TRANSFER_CASH = re.compile(
    r'^Vermögensübertragung:\s*Die Aktiengesellschaft überträgt gemäss Vertrag vom '
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4}) Aktiven von CHF "
    r"(?P<assets>[\d'.]+) und Passiven \(Fremdkapital\) von CHF "
    r"(?P<liabilities>[\d'.]+) auf die [\"“](?P<recipient>.+?)[\"”] "
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in (?P<place>[^.]+)\.\s*"
    r"Gegenleistung:\s*CHF (?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_FILING_REPLACED_FALSE_REMOVAL = re.compile(
    r"^Die hiermit in die Belegliste aufgenommene Anmeldung vom "
    r"(?P<replacement_date>\d{2}\.\d{2}\.\d{4}) ersetzt diejenige vom "
    r"(?P<replaced_date>\d{2}\.\d{2}\.\d{4}),\s*da auf letzterer "
    r"unrichtigerweise das Ausscheiden des "
    r"(?P<role>Geschäftsführers und Liquidators) "
    r"(?P<name>[^,.;]+) vermerkt ist\.?$",
    re.I | re.UNICODE,
)
_DE_PROFIT_CERTIFICATES_MAX_REMUNERATION = re.compile(
    r"^Genussscheine neu:\s*(?P<count>[\d']+) Genussscheine,\s*"
    r"gemäss näherer Umschreibung in den Statuten mit möglicher jährlicher "
    r"maximaler Vergütung von CHF (?P<maximum>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SECRETARY_APPOINTED_DIRECTOR = re.compile(
    r"^Signature (?P<sign>collective à deux|individuelle) de "
    r"(?P<name>[^,.;]+),\s*maintenant domicilié(?:e)? à (?P<place>[^,.;]+),\s*"
    r"jusqu['’]ici (?P<previous_role>[^,.;]+),\s*nommé(?:e)? "
    r"(?P<role>directeur|directrice)\.?$",
    re.I | re.UNICODE,
)
_DE_AUDITOR_LEGACY_REGISTRY_ID_ADDED = re.compile(
    r"^Mit dem im SHAB Nr\.\s*(?P<issue>\d+) vom "
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}) publizierten TR-Nr\.\s*"
    r"(?P<entry>[\d']+) vom (?P<entry_date>\d{2}\.\d{2}\.\d{4}) wurde die "
    r"alte Firmennummer (?P<legacy_id>CH-[\d.]+-\d) nicht erfasst,\s*"
    r"korrekt wäre:\s*(?P<name>.+?) "
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in (?P<place>[^,.;]+),\s*"
    r"(?P<role>Revisionsstelle) \[bisher:\s*(?P<previous_name>.+?) "
    r"\((?P<previous_id>CH-[\d.]+-\d)\),\s*in (?P<previous_place>[^,.;]+),\s*"
    r"(?P<previous_role>Revisionsstelle)\]\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_SIGNING_GRANTED = re.compile(
    r"^(?P<name>[^,.;]+) engage désormais la fondation par sa signature "
    r"(?P<sign>collective à deux)\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_TWO_INDIVIDUAL_MANAGERS = re.compile(
    r"^L['’]associé (?P<seller>[^,.;]+) a cédé "
    r"(?P<transferred>[\d']+) de ses (?P<before>[\d']+) parts sociales de CHF "
    r"(?P<nominal>[\d'.]+) à (?P<buyer>[^,.;]+),\s*de et à "
    r"(?P<place>[^,.;]+),\s*nouvelle associée\.\s*Gérants:\s*"
    r"(?P=seller),\s*nommé président,\s*et (?P=buyer),\s*lesquels signent "
    r"individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_NAME_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+) du "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) \(FOSC du "
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\) est rectifiée en ce sens que "
    r"l['’]administrateur se nomme (?P<name>.+?) "
    r"\(et non (?P<previous_name>.+?) comme publié\)\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDATION_ASSET_TRANSFER_CONTRACT_RANGE = re.compile(
    r"^Vermögensübertragung:\s*Die Stiftung überträgt gemäss Vertrag vom "
    r"(?P<agreement_date1>\d{2}\.\d{2}\.\d{4})\s*/\s*"
    r"(?P<agreement_date2>\d{2}\.\d{2}\.\d{4}) und Verfügung der "
    r"Aufsichtsbehörde vom (?P<approval_date>\d{2}\.\d{2}\.\d{4}) Aktiven "
    r"von CHF (?P<assets>[\d'.]+) auf die (?P<recipient>.+?),\s*in "
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>Keine)\.?$",
    re.I | re.UNICODE,
)
_DE_CAPITAL_REDUCTION_REINCREASE_SETOFF = re.compile(
    r"^Bei der Kapitalherabsetzung vom (?P<reduction_date>\d{2}\.\d{2}\.\d{4}) "
    r"werden (?P<destroyed>[\d']+) (?P<share_kind>Namenaktien) zu CHF "
    r"(?P<destroyed_nominal>[\d'.]+) vernichtet\.\s*Gleichzeitig werden bei "
    r"der ordentlichen Kapitalerhöhung vom "
    r"(?P<increase_date>\d{2}\.\d{2}\.\d{4}) Forderungen in der der Höhe von "
    r"CHF (?P<setoff>[\d'.]+) verrechnet,\s*wofür (?P<issued>[\d']+) "
    r"voll liberierte (?P<issued_kind>Namenaktien) zu CHF "
    r"(?P<issued_nominal>[\d'.]+) ausgegeben werden\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGER_SHARE_TRANSFER = re.compile(
    r"^(?P<seller>[^,.;]+),\s*(?P<seller_role>associé-gérant),\s*cède "
    r"(?P<transferred>[\d']+) de ses (?P<before>[\d']+) parts de CHF "
    r"(?P<nominal>[\d'.]+) à (?P<buyer>[^,.;]+),\s*de "
    r"(?P<origin>[^,.;]+),\s*à (?P<place>[^,.;]+),\s*nouvelle associée avec "
    r"(?P<buyer_count>[\d']+) parts de CHF (?P<buyer_nominal>[\d'.]+),\s*"
    r"avec signature (?P<sign>collective à deux|individuelle)\.\s*"
    r"(?P=seller) reste titulaire de (?P<remaining>[\d']+) parts de CHF "
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BEARER_PROFIT_CERTIFICATES_REMOVED = re.compile(
    r"^Genussscheine neu:\s*\[Die (?P<count>[\d']+) Inhabergenussscheine "
    r"sind aufgehoben worden\.\]\s*\[gestrichen:\s*Es bestehen (?P=count) "
    r"Inhabergenusscheine,\s*(?P<rights>[^\]]+?)\]\.?\s*"
    r"\[Änderung weiterer nicht publikationspflichtiger Tatsachen\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_PAIR_RESTRICTED_SIGNING = re.compile(
    r"^(?P<name1>[^,.;]+),\s*de (?P<origin1>[^,.;]+),\s*à "
    r"(?P<place1>[^,.;]+) et (?P<name2>[^,.;]+),\s*de "
    r"(?P<origin2>[^,.;]+),\s*à (?P<place2>[^,.;]+),\s*sont membres du "
    r"conseil,\s*tous deux avec signature collective à deux avec "
    r"(?P<with1>[^,.;]+) ou (?P<with2>[^,.;]+)\.?$",
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


def _fr_date(raw: str) -> str | None:
    day, month, year = raw.lower().split()
    month_number = _FR_MONTHS.get(month)
    if month_number is None:
        return None
    return f"{int(year):04d}-{month_number:02d}-{int(day):02d}"


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


def _share_payload(
    *,
    action: str,
    counterparty: str,
    before: int,
    transferred: int,
    count: int,
    nominal: str,
) -> dict:
    return {
        "action": action,
        "counterparty": counterparty,
        "shares_before": before,
        "shares_transferred": transferred,
        "shares_count": count,
        "share_nominal": nominal,
        "currency": "CHF",
    }


def extract_parser182_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 182."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_NAME_SPLIT_AND_PARTICIPATION_CLAUSES.fullmatch(leftover)
    if match:
        authorized_date = _fr_date(match.group("authorized_date"))
        conditional_date = _fr_date(match.group("conditional_date"))
        before_total = _count(match.group("from_count")) * _amount(
            match.group("from_nominal")
        )
        after_total = _count(match.group("to_count")) * _amount(
            match.group("to_nominal")
        )
        if authorized_date and authorized_date == conditional_date and before_total == after_total:
            rule_id = "fr.text.name_split_participation_clauses.v1"
            return [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "company_name_changed", rule_id, {
                        "name": match.group("name").strip(),
                        "action": "changed",
                    },
                ),
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "capital_changed", rule_id, {
                        "kind": "registered_share_split",
                        "from_count": _count(match.group("from_count")),
                        "from_nominal": match.group("from_nominal"),
                        "to_count": _count(match.group("to_count")),
                        "to_nominal": match.group("to_nominal"),
                        "currency": "CHF", "capital_total": str(before_total),
                        "transfer_restricted": bool(match.group("restriction")),
                    },
                ),
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "capital_changed", rule_id, {
                        "kind": "authorized_participation_capital_clause",
                        "action": "created", "decision_date": authorized_date,
                        "details_in_statutes": True,
                    },
                ),
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "capital_changed", rule_id, {
                        "kind": "conditional_participation_capital_clause",
                        "action": "created", "decision_date": conditional_date,
                        "details_in_statutes": True,
                    },
                ),
            ], ""

    match = _FR_MANAGER_TRANSFER_TO_EXISTING_MANAGER.fullmatch(leftover)
    if match and (
        _count(match.group("before"))
        == _count(match.group("remaining")) + _count(match.group("transferred"))
        and _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and len({
            match.group("nominal"), match.group("remaining_nominal"),
            match.group("buyer_nominal"),
        }) == 1
    ):
        rule_id = "fr.persons.manager_transfer_to_existing_manager.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant",
                extra=_share_payload(
                    action="shares_transferred", counterparty=buyer,
                    before=_count(match.group("before")), transferred=transferred,
                    count=_count(match.group("remaining")), nominal=match.group("nominal"),
                ),
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, role="associé-gérant",
                extra={
                    **_share_payload(
                        action="shares_received", counterparty=seller, before=0,
                        transferred=transferred, count=_count(match.group("buyer_count")),
                        nominal=match.group("buyer_nominal"),
                    ),
                    "new_associate": True, "manager_continues": True,
                },
            ),
        ], ""

    match = _DE_COMPANY_ASSET_TRANSFER_CASH.fullmatch(leftover)
    if match and (
        _amount(match.group("assets")) - _amount(match.group("liabilities"))
        == _amount(match.group("consideration"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.company_asset_transfer_cash.v1", {
                "source_kind": "stock_corporation",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital",
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration": match.group("consideration"), "currency": "CHF",
                "consideration_kind": "cash",
            },
        )], ""

    match = _DE_FILING_REPLACED_FALSE_REMOVAL.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.filing_replacement_false_removal.v1", {
                "action": "filing_replaced",
                "replacement_date": _iso_date(match.group("replacement_date")),
                "replaced_date": _iso_date(match.group("replaced_date")),
                "incorrect_change": "officer_removal",
                "officer_name": match.group("name").strip(),
                "officer_role": match.group("role").strip(),
                "removal_retracted": True,
            },
        )], ""

    match = _DE_PROFIT_CERTIFICATES_MAX_REMUNERATION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed",
            "de.text.profit_participation_certificates_max_remuneration.v1", {
                "kind": "profit_participation_certificates", "action": "added",
                "count": _count(match.group("count")),
                "maximum_annual_remuneration": match.group("maximum"),
                "currency": "CHF", "details_in_statutes": True,
            },
        )], ""

    match = _FR_SECRETARY_APPOINTED_DIRECTOR.fullmatch(leftover)
    if match:
        signing = (
            "Kollektivunterschrift zu zweien"
            if match.group("sign").lower().startswith("collective")
            else "Einzelunterschrift"
        )
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.secretary_appointed_director.v1",
            match.group("name"), place=match.group("place"),
            role=match.group("role").lower(), signing=signing, extra={
                "action": "role_changed",
                "previous_role": match.group("previous_role").strip(),
                "domicile_changed": True,
            },
        )], ""

    match = _DE_AUDITOR_LEGACY_REGISTRY_ID_ADDED.fullmatch(leftover)
    if match and (
        match.group("name").strip() == match.group("previous_name").strip()
        and match.group("legacy_id") == match.group("previous_id")
        and match.group("place").strip() == match.group("previous_place").strip()
        and match.group("role").lower() == match.group("previous_role").lower()
    ):
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.auditor_legacy_registry_id_added.v1",
            match.group("name"), place=match.group("place"),
            role=match.group("role"), extra={
                "action": "registry_identifier_supplemented",
                "uid": match.group("uid"), "legacy_registry_id": match.group("legacy_id"),
                "issue": match.group("issue"),
                "notice_date": _iso_date(match.group("notice_date")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_FOUNDATION_SIGNING_GRANTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.foundation_signing_granted.v1",
            match.group("name"), signing="Kollektivunterschrift zu zweien", extra={
                "action": "signing_granted", "organization_kind": "foundation",
            },
        )], ""

    match = _FR_SHARE_TRANSFER_TWO_INDIVIDUAL_MANAGERS.fullmatch(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        before = _count(match.group("before"))
        if 0 < transferred <= before:
            rule_id = "fr.persons.share_transfer_two_individual_managers.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller,
                    role="associé-gérant et président", signing="Einzelunterschrift",
                    extra=_share_payload(
                        action="shares_transferred_and_appointed_president",
                        counterparty=buyer, before=before, transferred=transferred,
                        count=before - transferred, nominal=match.group("nominal"),
                    ),
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associée-gérante", signing="Einzelunterschrift", extra={
                        **_share_payload(
                            action="shares_received_and_appointed_manager",
                            counterparty=seller, before=0, transferred=transferred,
                            count=transferred, nominal=match.group("nominal"),
                        ),
                        "origin": match.group("place").strip(), "new_associate": True,
                    },
                ),
            ], ""

    match = _FR_ADMINISTRATOR_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_name_corrected.v1",
            match.group("name"), role="administrateur", extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _DE_FOUNDATION_ASSET_TRANSFER_CONTRACT_RANGE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.foundation_asset_transfer_contract_range.v1", {
                "source_kind": "foundation",
                "agreement_dates": [
                    _iso_date(match.group("agreement_date1")),
                    _iso_date(match.group("agreement_date2")),
                ],
                "approval_date": _iso_date(match.group("approval_date")),
                "assets": match.group("assets"), "liabilities": None,
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration_kind": "none", "gratuitous": True, "currency": "CHF",
            },
        )], ""

    match = _DE_CAPITAL_REDUCTION_REINCREASE_SETOFF.fullmatch(leftover)
    if match and (
        match.group("reduction_date") == match.group("increase_date")
        and _count(match.group("destroyed")) == _count(match.group("issued"))
        and match.group("destroyed_nominal") == match.group("issued_nominal")
        and match.group("share_kind").lower() == match.group("issued_kind").lower()
        and _count(match.group("issued")) * _amount(match.group("issued_nominal"))
        == _amount(match.group("setoff"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.capital_reduction_reincrease_setoff.v1", {
                "kind": "capital_reduction_and_increase",
                "date": _iso_date(match.group("reduction_date")),
                "destroyed_shares_count": _count(match.group("destroyed")),
                "destroyed_share_kind": match.group("share_kind"),
                "destroyed_share_nominal": match.group("destroyed_nominal"),
                "issued_shares_count": _count(match.group("issued")),
                "issued_share_kind": match.group("issued_kind"),
                "issued_share_nominal": match.group("issued_nominal"),
                "issued_fully_paid": True,
                "setoff_amount": match.group("setoff"), "currency": "CHF",
                "nominal_capital_unchanged": True,
            },
        )], ""

    match = _FR_ASSOCIATE_MANAGER_SHARE_TRANSFER.fullmatch(leftover)
    if match and (
        _count(match.group("before"))
        == _count(match.group("remaining")) + _count(match.group("transferred"))
        and _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and len({
            match.group("nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }) == 1
    ):
        rule_id = "fr.persons.associate_manager_share_transfer.v2"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        buyer_signing = (
            "Kollektivunterschrift zu zweien"
            if match.group("sign").lower().startswith("collective")
            else "Einzelunterschrift"
        )
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role=match.group("seller_role"),
                extra=_share_payload(
                    action="shares_transferred", counterparty=buyer,
                    before=_count(match.group("before")), transferred=transferred,
                    count=_count(match.group("remaining")), nominal=match.group("nominal"),
                ),
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée", signing=buyer_signing, extra={
                    **_share_payload(
                        action="shares_received", counterparty=seller, before=0,
                        transferred=transferred, count=_count(match.group("buyer_count")),
                        nominal=match.group("buyer_nominal"),
                    ),
                    "origin": match.group("origin").strip(), "new_associate": True,
                },
            ),
        ], ""

    match = _DE_BEARER_PROFIT_CERTIFICATES_REMOVED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.bearer_profit_certificates_removed.v1", {
                "kind": "bearer_profit_participation_certificates",
                "action": "removed", "count": _count(match.group("count")),
                "previous_rights": match.group("rights").strip(),
                "other_non_public_facts_changed": True,
            },
        )], ""

    match = _FR_BOARD_PAIR_RESTRICTED_SIGNING.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.board_pair_restricted_collective_signing.v1"
        signing_with = [match.group("with1").strip(), match.group("with2").strip()]
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="membre du conseil",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group(f"origin{index}").strip(),
                    "signing_with_any_of": signing_with,
                },
            )
            for index in (1, 2)
        ], ""

    return [], text
