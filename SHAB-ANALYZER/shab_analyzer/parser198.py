from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_FR_DIRECTOR_SIGNING_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que la\s+"
    r"(?P<role>directrice)\s+(?P<name>[^,.;]+?)\s+signe\s+"
    r"(?P<signing>individuellement)\s*\(et non\s+"
    r"(?P<previous_signing>collectivement à deux)\)\.?$",
    re.I | re.UNICODE,
)
_DE_NEW_LIQUIDATION_ADDRESS = re.compile(
    r"^Neue Liquidationsadresse:\s*(?P<street>.+?),\s*"
    r"(?P<care_of>c/o\s+.+?),\s*(?P<postal_code>\d{4})\s+"
    r"(?P<locality>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_CAPITAL_CLAUSE_CHANGES = re.compile(
    r"^Suppression de la clause statutaire d['’]augmentation autorisée adoptée "
    r"par l['’]assemblée générale du\s+(?P<removed_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"L['’]assemblée générale du\s+(?P<authorized_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"a décidé de créer une augmentation autorisée du capital-actions;\s*"
    r"pour les détails voir les statuts\.\s*La clause d['’]augmentation "
    r"conditionnelle du capital-actions,\s*décidée par l['’]assemblée générale du\s+"
    r"(?P<conditional_original_date>\d{2}\.\d{2}\.\d{4}),\s*a été modifiée le\s+"
    r"(?P<conditional_changed_date>\d{2}\.\d{2}\.\d{4});\s*"
    r"pour les détails voir les statuts\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_DEFICIT_FREE_EQUITY = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di\s+(?P<absorbed_name>.+?),\s*"
    r"in\s+(?P<absorbed_place>[^()]+?)\s*"
    r"\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*secondo "
    r"contratto di fusione del\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"e bilancio al\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta "
    r"attivi per CHF\s+(?P<assets>[\d'.]+),?\s+e passivi verso terzi per CHF\s+"
    r"(?P<liabilities>[\d'.]+),\s*con un['’]eccedenza passiva di CHF\s+"
    r"(?P<deficit>[\d'.]+)\.\s*Conformemente all['’]attestazione di un perito "
    r"revisore abilitato,\s*la società assuntrice dispone di fondi propri "
    r"liberamente disponibili equivalenti almeno all['’]ammontare dello scoperto "
    r"e del sovraindebitamento\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_BOARD_SIGNING_RESTRICTIONS = re.compile(
    r"^Le membre du conseil de fondation et vice-président du comité de direction\s+"
    r"(?P<vice>[^,.;]+)\s+continue de signer collectivement à deux,\s*désormais "
    r"pas avec\s+(?P<excluded>[^.;]+)\.\s*Les membres du conseil de fondation "
    r"et du comité de direction\s+(?P<member1>[^,.;]+)\s+et\s+"
    r"(?P<member2>[^,.;]+)\s+continuent de signer collectivement à deux,\s*"
    r"désormais avec le/la président/e ou le/la vice-président/e\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_NEW_ASSOCIATES_SHARE_TRANSFER = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+par\s+"
    r"(?P<buyer1_count>[\d']+)\s+parts à\s+(?P<buyer1>[^,.;]+),\s*de\s+"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,;]+),\s*et par\s+"
    r"(?P<buyer2_count>[\d']+)\s+parts à\s+(?P<buyer2>[^,.;]+),\s*de\s+"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,;]+),\s*nouveaux associés "
    r"sans signature,\s*avec respectivement\s+(?P<result1>[\d']+)\s+et\s+"
    r"(?P<result2>[\d']+)\s+parts de CHF\s+(?P<result_nominal>[\d'.]+);\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_LIQUIDATION_OPERATED_BY_LIQUIDATOR = re.compile(
    r"^La liquidation est opérée sous la raison de commerce:\s*"
    r"(?P<company>.+?),\s*par\s+(?P<name>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+)\s+"
    r"nommé(?:e)?\s+(?P<role>liquidateur|liquidatrice)"
    r"(?:\s+avec\s+(?P<signing>signature individuelle))?\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_PERSON_CORRECTIONS = re.compile(
    r"^L['’]inscription\s+(?:n°|no)?\s*(?P<entry1>[\d']+)\s+du\s+"
    r"(?P<entry_date1>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date1>\d{2}\.\d{2}\.\d{4})\s+p\.\s*"
    r"(?P<notice_ref1>[\d/]+)\)\s+est rectif[éi]e en ce sens que\s+"
    r"(?P<previous_name>[^.]+?)\s+se prénomme en réalité\s+(?P<name>[^.]+)\.\s*"
    r"L['’]inscription\s+(?:n°|no)?\s*(?P<entry2>[\d']+)\s+du\s+"
    r"(?P<entry_date2>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date2>\d{2}\.\d{2}\.\d{4})\s+p\.\s*"
    r"(?P<notice_ref2>[\d/]+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<role_name>[^.]+?)\s+est nommé\s+(?P<role>[^.]+?)\s+et non pas\s+"
    r"(?P<previous_role>[^.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_AUTHORIZED_CAPITAL_CLAUSE_REPLACED = re.compile(
    r"^Suppression de la clause statutaire relative à l['’]augmentation "
    r"autorisée du capital décidée le\s+"
    r"(?P<removed_date>\d{2}\.\d{2}\.\d{4})"
    r"(?P<expired>,\s*le délai étant écoulé)?\s*\.\s*Par décision du\s+"
    r"(?P<introduced_date>\d{2}\.\d{2}\.\d{4}),\s*l['’]assemblée générale a "
    r"introduit une clause statutaire relative à une augmentation autorisée du "
    r"capital-actions\.\s*Pour les détails,\s*voir les statuts\.?$",
    re.I | re.UNICODE,
)
_FR_DOMICILE_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:n°|no)?\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+est domicilié(?:e)? à\s+(?P<place>[^()]+?)\s*"
    r"\(et non pas\s+(?!à\b)(?P<previous_place>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_PRESIDENCY_CHANGES = re.compile(
    r"^Les membres du conseil\s+(?P<president>[^,.;]+),\s*maintenant "
    r"originaire de\s+(?P<origin>[^,.;]+),\s*nommé président,\s*et\s+"
    r"(?P<previous_president>[^,.;]+),\s*jusqu['’]ici président,\s*"
    r"continuent à signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_ASSET_TRANSFER_CASH_FRENCH_DATE = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<agreement_date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"la société a transféré des actifs pour CHF\s+(?P<assets>[\d'.]+)\s+"
    r"et des passifs envers les tiers pour CHF\s+(?P<liabilities>[\d'.]+)\s+"
    r"à\s+(?P<recipient>.+?),\s*à\s+(?P<place>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_FOUR_MIXED_SIGNING = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé président,\s*"
    r"(?P<member1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,;]+),\s*(?P<member2>[^,.;]+),\s*de\s+"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,;]+),\s*et\s+"
    r"(?P<member3>[^,.;]+),\s*de\s+(?P<origin3>[^,.;]+),\s*à\s+"
    r"(?P<place3>[^.;]+)\.\s*Signature individuelle du président ou "
    r"collective à deux des autres membres du conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_FR_OUTGOING_SPIN_OFF_NEW_COMPANY = re.compile(
    r"^Séparation:\s*selon projet de scission du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré une partie de "
    r"ses actifs et de ses passifs à la nouvelle société\s+(?P<recipient>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<place>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_AUDIT_WAIVER_REVOCATION_SUPPLEMENT = re.compile(
    r"^Complément à l['’]inscription\s+(?:n°|no)?\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\):\s*La déclaration du\s+"
    r"(?P<declaration_date>\d{2}\.\d{2}\.\d{4})\s+de renonciation à un "
    r"contrôle restreint est abrogée\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_DOMICILE_CORRECTED_WITH_NOTICE = re.compile(
    r"^L['’]inscription\s+(?:n°|no)?\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(publication FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+page\s+"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que l['’]associé\s+"
    r"(?P<name>[^,.;]+)\s+est domicilié à\s+(?P<place>[^,()]+),\s*"
    r"(?P<country>[A-Z]{2,3})\s*\(et non à\s+(?P<previous_place>[^)]+)\)\.?$",
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


def extract_parser198_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 198."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_DIRECTOR_SIGNING_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.director_signing_corrected.v1",
            match.group("name"), role=match.group("role").lower(),
            signing="Einzelunterschrift", extra={
                "action": "signing_corrected",
                "previous_signing": "Kollektivunterschrift zu zweien",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _DE_NEW_LIQUIDATION_ADDRESS.fullmatch(leftover)
    if match:
        address = (
            f"{match.group('street').strip()}, {match.group('care_of').strip()}, "
            f"{match.group('postal_code')} {match.group('locality').strip()}"
        )
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "de.text.new_liquidation_address.v1", {
                "kind": "liquidation_address", "action": "changed", "to": address,
                "street": match.group("street").strip(),
                "care_of": match.group("care_of").strip(),
                "postal_code": match.group("postal_code"),
                "locality": match.group("locality").strip(),
            },
        )], ""

    match = _FR_THREE_CAPITAL_CLAUSE_CHANGES.fullmatch(leftover)
    if match:
        rule_id = "fr.text.three_capital_clause_changes.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause", "action": "removed",
                    "authorization_date": _iso_date(match.group("removed_date")),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause", "action": "introduced",
                    "decision_date": _iso_date(match.group("authorized_date")),
                    "details_in_statutes": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "conditional_capital_clause", "action": "modified",
                    "original_decision_date": _iso_date(
                        match.group("conditional_original_date")
                    ),
                    "decision_date": _iso_date(match.group("conditional_changed_date")),
                    "details_in_statutes": True,
                },
            ),
        ], ""

    match = _IT_MERGER_DEFICIT_FREE_EQUITY.fullmatch(leftover)
    if match and (
        _amount(match.group("liabilities")) - _amount(match.group("assets"))
        == _amount(match.group("deficit"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "it.text.merger_deficit_free_equity_short.v1", {
                "kind": "absorption",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities",
                "deficit": match.group("deficit"), "currency": "CHF",
                "deficit_coverage": "freely_available_equity",
                "deficit_coverage_confirmed_by_auditor": True,
            },
        )], ""

    match = _FR_FOUNDATION_BOARD_SIGNING_RESTRICTIONS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.foundation_board_signing_restrictions.v1"
        common = {"action": "signing_restriction_changed", "continued": True}
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("vice"),
                role="membre du conseil de fondation et vice-président du comité de direction",
                signing="Kollektivunterschrift zu zweien", extra={
                    **common, "cannot_sign_with": match.group("excluded").strip(),
                },
            ),
            *[
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", rule_id, match.group(group),
                    role="membre du conseil de fondation et du comité de direction",
                    signing="Kollektivunterschrift zu zweien", extra={
                        **common, "co_signs_with": "président/e ou vice-président/e",
                    },
                )
                for group in ("member1", "member2")
            ],
        ], ""

    match = _FR_TWO_NEW_ASSOCIATES_SHARE_TRANSFER.fullmatch(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        before = _count(match.group("before"))
        remaining = _count(match.group("remaining"))
        buyer_counts = [
            _count(match.group("buyer1_count")),
            _count(match.group("buyer2_count")),
        ]
        results = [_count(match.group("result1")), _count(match.group("result2"))]
        if (
            transferred == sum(buyer_counts)
            and before - transferred == remaining
            and buyer_counts == results
            and match.group("nominal") == match.group("result_nominal")
            == match.group("remaining_nominal")
        ):
            rule_id = "fr.persons.two_new_associates_share_transfer.v1"
            seller = match.group("seller").strip()
            common = {
                "share_nominal": match.group("nominal"), "currency": "CHF",
            }
            events = [_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé", extra={
                    "action": "shares_transferred", "shares_before": before,
                    "shares_transferred": transferred, "shares_count": remaining,
                    **common,
                },
            )]
            for index in (1, 2):
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"buyer{index}"),
                    place=match.group(f"place{index}"), role="associé", extra={
                        "action": "appointed_and_shares_received",
                        "counterparty": seller,
                        "origin": match.group(f"origin{index}").strip(),
                        "shares_received": buyer_counts[index - 1],
                        "shares_count": buyer_counts[index - 1],
                        "without_signature": True, **common,
                    },
                ))
            return events, ""

    match = _FR_LIQUIDATION_OPERATED_BY_LIQUIDATOR.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.liquidation_operated_by_liquidator.v1",
            match.group("name"), place=match.group("place"),
            role=match.group("role").lower(),
            signing="Einzelunterschrift" if match.group("signing") else None,
            extra={
                "action": "appointed_liquidator",
                "origin": match.group("origin").strip(),
                "liquidation_company_name": match.group("company").strip(),
            },
        )], ""

    match = _FR_TWO_PERSON_CORRECTIONS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_person_corrections.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"), extra={
                    "action": "given_name_corrected",
                    "previous_name": match.group("previous_name").strip(),
                    "entry": match.group("entry1"),
                    "entry_date": _iso_date(match.group("entry_date1")),
                    "notice_date": _iso_date(match.group("notice_date1")),
                    "notice_ref": match.group("notice_ref1"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("role_name"),
                role=match.group("role").strip(), extra={
                    "action": "role_corrected",
                    "previous_role": match.group("previous_role").strip(),
                    "entry": match.group("entry2"),
                    "entry_date": _iso_date(match.group("entry_date2")),
                    "notice_date": _iso_date(match.group("notice_date2")),
                    "notice_ref": match.group("notice_ref2"),
                },
            ),
        ], ""

    match = _FR_AUTHORIZED_CAPITAL_CLAUSE_REPLACED.fullmatch(leftover)
    if match:
        rule_id = "fr.text.authorized_capital_clause_replaced.v2"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause", "action": "removed",
                    "decision_date": _iso_date(match.group("removed_date")),
                    "reason": "authorization_period_elapsed"
                    if match.group("expired") else None,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause", "action": "introduced",
                    "decision_date": _iso_date(match.group("introduced_date")),
                    "details_in_statutes": True,
                },
            ),
        ], ""

    match = _FR_DOMICILE_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.domicile_corrected.v2",
            match.group("name"), place=match.group("place"), extra={
                "action": "domicile_corrected",
                "previous_place": match.group("previous_place").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_BOARD_PRESIDENCY_CHANGES.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.board_presidency_changes.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président", signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_president_and_origin_changed",
                    "origin": match.group("origin").strip(),
                    "signing_continues": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("previous_president"),
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "presidency_ended", "previous_role": "président",
                    "signing_continues": True,
                },
            ),
        ], ""

    match = _FR_ASSET_TRANSFER_CASH_FRENCH_DATE.fullmatch(leftover)
    if match and (
        _amount(match.group("assets")) - _amount(match.group("liabilities"))
        == _amount(match.group("consideration"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.asset_transfer_cash_french_date.v1", {
                "agreement_date": _french_date(match.group("agreement_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities",
                "currency": "CHF", "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"),
                "consideration_kind": "cash",
            },
        )], ""

    match = _FR_ADMINISTRATION_FOUR_MIXED_SIGNING.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administration_four_mixed_signing.v1"
        events = [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("president"),
            role="président", signing="Einzelunterschrift",
            extra={"action": "appointed_president"},
        )]
        for index in range(1, 4):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"member{index}"),
                place=match.group(f"place{index}"),
                role="membre du conseil d'administration",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed",
                    "origin": match.group(f"origin{index}").strip(),
                },
            ))
        return events, ""

    match = _FR_OUTGOING_SPIN_OFF_NEW_COMPANY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.outgoing_spin_off_new_company.v1", {
                "kind": "spin_off_distribution",
                "date": _iso_date(match.group("date")),
                "document": "projet de scission",
                "scope": "part_of_assets_and_liabilities",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_newly_founded": True,
            },
        )], ""

    match = _FR_AUDIT_WAIVER_REVOCATION_SUPPLEMENT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "audit_requirement_changed",
            "fr.text.audit_waiver_revocation_supplement.v1", {
                "kind": "limited_audit_waiver", "action": "revoked",
                "limited_audit_waived": False,
                "declaration_date": _iso_date(match.group("declaration_date")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
                "publication_supplemented": True,
            },
        )], ""

    match = _FR_ASSOCIATE_DOMICILE_CORRECTED_WITH_NOTICE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_domicile_corrected_notice.v1",
            match.group("name"), place=match.group("place"), role="associé", extra={
                "action": "domicile_corrected",
                "country": match.group("country").upper(),
                "previous_place": match.group("previous_place").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    return [], leftover
