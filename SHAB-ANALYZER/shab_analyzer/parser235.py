from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_RESTRICTED_SIGNATURE_GRANTED_TO_TWO = re.compile(
    r"^Signature collective à deux,\s*pas entre eux,\s*ni avec\s+"
    r"(?P<excluded>.+?),\s*est conférée à\s+(?P<name1>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+?)(?:\s*\((?P<canton1>[A-Z]{2})\))?\s+et à\s+"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_FOREIGN_BOARD_MEMBERS = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<country1>[A-Z]{2,3}),\s*(?P<role1>président)\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"(?P<country2>[A-Z]{2,3}),\s*sont membres du conseil "
    r"d['’]administration(?P<individual_signing> avec signature individuelle)?\.?$",
    re.I | re.UNICODE,
)
_IT_LIQUIDATION_ENDED_DELETION_BLOCKED_BOTH_TAX_AUTHORITIES = re.compile(
    r"^La liquidazione è terminata\.\s*La cancellazione della società non può "
    r"ancora essere effettuata mancando il consenso delle autorità fiscali "
    r"federali e cantonali\.?$",
    re.I | re.UNICODE,
)
_FR_SOCIAL_SHARES_SPLIT_AND_TRANSFER = re.compile(
    r"^Les\s+(?P<from_count>[\d']+)\s+parts sociales de CHF\s+"
    r"(?P<from_nominal>[\d'.]+)\s+ont été divisées en\s+"
    r"(?P<to_count>[\d']+)\s+parts de CHF\s+(?P<to_nominal>[\d'.]+)\s+"
    r"chacune qui se répartissent de la manière suivante\s*:\s*"
    r"l['’]associé\s+(?P<name1>[^,.;]+),\s*pour\s+"
    r"(?P<initial_count1>[\d']+)\s+parts de CHF\s+"
    r"(?P<initial_nominal1>[\d'.]+)\s+et,?\s*l['’]associé\s+"
    r"(?P<name2>[^,.;]+),\s*pour\s+(?P<initial_count2>[\d']+)\s+"
    r"parts de CHF\s+(?:CHF\s+)?(?P<initial_nominal2>[\d'.]+)\.\s*"
    r"Par suite de cession de\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<transfer_nominal>[\d'.]+),\s*(?P<name1_after>.+?)\s+et\s+"
    r"(?P<name2_after>.+?)\s+sont maintenant tous deux associés pour\s+"
    r"(?P<final_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<final_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_INCREASE_DATE_REPLACED = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+eine Erhöhung des genehmigten "
    r"Kapitals gemäss näherer Umschreibung in den Statuten beschlossen\.\s*"
    r"\[bisher:\s*Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+eine Erhöhung des "
    r"genehmigten Kapitals gemäss näherer Umschreibung in den Statuten "
    r"beschlossen\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_CROSS_BORDER_MERGER_BVI_COMPANY = re.compile(
    r"^Grenzüberschreitende Fusion nach den Vorschriften des\s+"
    r"(?P<legal_basis>Art\.\s*163a IPRG):\s*Übernahme der Aktiven und "
    r"Passiven der\s+(?P<absorbed_name>.+?),\s*in\s+"
    r"(?P<absorbed_place>[^()]+?)\s*\((?P<absorbed_country>[^)]+)\),\s*"
    r"einer\s+(?P<absorbed_legal_form>company limited by shares)\s+nach dem "
    r"Recht der\s+(?P<jurisdiction>[^()]+?)\s*\(Company No:\s*"
    r"(?P<company_number>[^)]+)\),\s*gemäss Fusionsvertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Bilanz per\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\.\s*Aktiven von\s+"
    r"(?P<currency>[A-Z]{3})\s+(?P<assets>[\d'.]+)\s+und Passiven\s*"
    r"\(Fremdkapital\)\s+von\s+(?P=currency)\s+"
    r"(?P<liabilities>[\d'.]+)\s+gehen auf die übernehmende Gesellschaft "
    r"(?:über|ueber)\.\s*Da die übernehmende Gesellschaft sämtlich(?:e)? "
    r"Aktien der übertragenden Gesellschaft hält,\s*findet weder eine "
    r"Kapitalerhöhung noch eine Aktienzuteilung statt\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_PRESIDENT_APPOINTED_LIQUIDATOR = re.compile(
    r"^(?:Les\s+(?P<share_count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<share_nominal>[\d'.]+)\s+ne sont plus restreintes quant à la "
    r"transmissibilité\s*\((?P<legal_basis>art\.\s*685a,\s*al\.\s*3 CO)\)\.\s*)?"
    r"(?P<name>[^,.;]+),\s*administratrice présidente,\s*"
    r"est nommée liquidatrice(?P<individual_signing> avec signature individuelle)?\.?$",
    re.I | re.UNICODE,
)
_DE_MUNICIPAL_LEGAL_BASIS_AND_ENDOWMENT_CAPITAL = re.compile(
    r"^Rechtliche Grundlage:\s*(?P<legal_basis1>.+?)\s*;\s*"
    r"(?P<legal_basis2>.+?)\s+vom\s+"
    r"(?P<legal_basis_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"Dotationskapital:\s*CHF\s+(?P<capital>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_SOLE_PROPRIETOR_ASSET_TRANSFER_DEBT_SETTLED = re.compile(
    r'^Vermögensübertragung:\s*Der Geschäftsinhaber überträgt gemäss '
    r"Vertrag vom\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven "
    r"von CHF\s+(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+"
    r'von CHF\s+(?P<liabilities>[\d\'.]+)\s+auf die\s+["\u201c]'
    r'(?P<recipient>.+?)["\u201d]\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*'
    r"in\s+(?P<place>[^.]+)\.\s*Gegenleistung:\s*Eine bestehende Schuld "
    r"in gleicher Höhe wird getilgt\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ADMINISTRATORS_SECRETARY_CHANGE = re.compile(
    r"^Les administrateurs\s+(?P<name1>[^,.;]+),\s*nommé\s+"
    r"(?P<role1>secrétaire)\s+et\s+(?P<name2>[^,.;]+),\s*"
    r"jusqu['’]ici\s+(?P<previous_role2>secrétaire),\s*continuent à "
    r"signer individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_ORGANIZATION_SHARE_TRANSFER_TO_MANAGER = re.compile(
    r"^L['’]associée\s+(?P<seller>.+?)\s*\((?P<foreign_id>[^)]+)\)\s+"
    r"cède\s+(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+"
    r"parts de CHF\s+(?P<nominal>[\d'.]+)\s+à l['’]associé-gérant\s+"
    r"(?P<buyer>.+?),\s*désormais titulaire de\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\s*;\s*(?P=seller)\s*\((?P=foreign_id)\)\s+"
    r"est désormais titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_PRESIDENT_TRANSFER_TO_NEW_MANAGER = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+),\s*maintenant "
    r"président,\s*détient désormais\s+(?P<remaining>[\d']+)\s+parts de "
    r"CHF\s+(?P<nominal>[\d'.]+)\s+par suite de cession d['’]une part de CHF\s+"
    r"(?P<transfer_nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvelle associée-gérante pour une part de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)"
    r"(?P<individual_signing> avec signature individuelle)?\.?$",
    re.I | re.UNICODE,
)
_FR_UNPUBLISHED_STATUTES_POINTS_SOURCE_TYPO = re.compile(
    r"^également sur des points non soumis à modification"
    r"(?:\.\s*Rectification en ce sens que l['’]administrateur se prénomme\s+"
    r"(?P<name>.+?)\s*\(et non\s+(?P<previous_name>[^)]+)\))?\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_COMMITTEE_MEMBER_RESTRICTED_SIGNING = re.compile(
    r"^Nouveau membre du comité(?: avec signature collective à deux,)?\s*"
    r"toutefois avec le président ou le "
    r"vice-président\s*:\s*(?P<name>[^,.;]+),\s*de et à\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_REPRESENTATION_POWERS_REMOVED_ART_110 = re.compile(
    r"^Suite à la modification du droit du registre du commerce,\s*et en "
    r"application de l['’]article\s+(?P<article>110 al\.\s*1 ORC),\s*les "
    r"informations relatives aux personnes disposant d['’]un pouvoir de "
    r"représentation pour toute l['’]entreprise sont radiées\.\s*Par "
    r"conséquent,\s*sont radiés les pouvoirs de\s+(?P<name1>[^,.;]+),\s*"
    r"jusqu['’]ici\s+(?P<role1>président et directeur),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*(?P<role2>membres? du conseil "
    r"d['’]administration)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_FOUNDATION_MEMBERS_UNSIGNED = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"sans signature,\s*et\s+(?P<name2>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*sans signature,\s*sont membres du conseil de "
    r"fondation\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


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


def extract_parser235_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 235."""
    del language  # Historical publications regularly contain another language.
    leftover = text.strip()

    match = _FR_RESTRICTED_SIGNATURE_GRANTED_TO_TWO.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.restricted_signature_granted_to_two.v1"
        excluded = [
            item.strip()
            for item in re.split(r",\s*|\s+et\s+", match.group("excluded"))
            if item.strip()
        ]
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "signing_granted",
                    "origin": match.group(f"origin{index}").strip(),
                    "not_with_each_other": True,
                    "excluded_co_signatories": excluded,
                    **(
                        {"place_canton": match.group("canton1")}
                        if index == 1 and match.group("canton1") else {}
                    ),
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_TWO_FOREIGN_BOARD_MEMBERS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_foreign_board_members.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role=("administrateur et président" if index == 1 else "administrateur"),
                signing=(
                    "Einzelunterschrift" if match.group("individual_signing") else None
                ),
                extra={
                    "action": "appointed",
                    "origin": match.group(f"origin{index}").strip(),
                    "country": match.group(f"country{index}"),
                    "signing_authority": None,
                },
            )
            for index in (1, 2)
        ], ""

    if _IT_LIQUIDATION_ENDED_DELETION_BLOCKED_BOTH_TAX_AUTHORITIES.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed",
            "it.text.liquidation_ended_deletion_blocked_both_tax_authorities.v1", {
                "kind": "liquidation_ended", "deletion_blocked": True,
                "deletion_blocked_reason": "tax_authority_consent_missing",
                "missing_consents": ["federal_tax_authority", "cantonal_tax_authority"],
            },
        )], ""

    match = _FR_SOCIAL_SHARES_SPLIT_AND_TRANSFER.fullmatch(leftover)
    if match:
        from_count = _count(match.group("from_count"))
        to_count = _count(match.group("to_count"))
        initial1 = _count(match.group("initial_count1"))
        initial2 = _count(match.group("initial_count2"))
        transferred = _count(match.group("transferred"))
        final_count = _count(match.group("final_count"))
        nominals = {
            match.group("to_nominal"), match.group("initial_nominal1"),
            match.group("initial_nominal2"), match.group("transfer_nominal"),
            match.group("final_nominal"),
        }
        names_consistent = (
            match.group("name1_after").casefold().startswith(
                match.group("name1").casefold()
            )
            and match.group("name2_after").casefold() == match.group("name2").casefold()
        )
        if (
            from_count * _count(match.group("from_nominal"))
            == to_count * _count(match.group("to_nominal"))
            and initial1 + initial2 == to_count
            and initial1 - transferred == final_count
            and initial2 + transferred == final_count
            and len(nominals) == 1
            and names_consistent
        ):
            rule_id = "fr.persons.social_shares_split_and_transfer.v1"
            common = {
                "share_nominal": match.group("final_nominal"), "currency": "CHF",
            }
            return [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "capital_changed", rule_id, {
                        "kind": "share_split", "action": "split",
                        "split_from": {
                            "count": from_count,
                            "nominal": match.group("from_nominal"),
                        },
                        "split_to": {
                            "count": to_count,
                            "nominal": match.group("to_nominal"),
                        },
                        "currency": "CHF",
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("name1_after"),
                    role="associé", extra={
                        **common, "action": "shares_transferred",
                        "previous_name_wording": match.group("name1").strip(),
                        "counterparty": match.group("name2").strip(),
                        "shares_before": initial1, "shares_transferred": transferred,
                        "shares_count": final_count,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("name2"),
                    role="associé", extra={
                        **common, "action": "shares_received",
                        "counterparty": match.group("name1_after").strip(),
                        "shares_before": initial2, "shares_received": transferred,
                        "shares_count": final_count,
                    },
                ),
            ], ""

    match = _DE_AUTHORIZED_CAPITAL_INCREASE_DATE_REPLACED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_increase_date_replaced.v1", {
                "kind": "authorized_capital_increase", "action": "decision_date_changed",
                "decision_date": _iso_date(match.group("date")),
                "previous_decision_date": _iso_date(match.group("previous_date")),
                "details_in_statutes": True,
            },
        )], ""

    match = _DE_CROSS_BORDER_MERGER_BVI_COMPANY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "de.text.cross_border_merger_bvi_company.v1", {
                "kind": "cross_border_merger", "direction": "inbound",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_country": match.group("absorbed_country").strip(),
                "absorbed_legal_form": match.group("absorbed_legal_form"),
                "absorbed_jurisdiction": match.group("jurisdiction").strip(),
                "absorbed_company_number": match.group("company_number").strip(),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "currency": match.group("currency").upper(),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "same_shareholder": True, "capital_increase": False,
                "share_allocation": False,
            },
        )], ""

    match = _FR_ADMINISTRATOR_PRESIDENT_APPOINTED_LIQUIDATOR.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administrator_president_liquidator.v1"
        events = [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("name"),
            role="administratrice présidente et liquidatrice",
            signing=(
                "Einzelunterschrift" if match.group("individual_signing") else None
            ),
            extra={
                "action": "appointed_liquidator",
                "previous_role": "administratrice présidente",
            },
        )]
        if match.group("share_count"):
            events.insert(0, _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id, {
                    "kind": "share_transfer_restriction", "action": "removed",
                    "share_count": _count(match.group("share_count")),
                    "share_nominal": match.group("share_nominal"),
                    "currency": "CHF",
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                },
            ))
        return events, ""

    match = _DE_MUNICIPAL_LEGAL_BASIS_AND_ENDOWMENT_CAPITAL.fullmatch(leftover)
    if match:
        rule_id = "de.text.municipal_legal_basis_endowment_capital.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id, {
                    "kind": "legal_basis", "action": "recorded",
                    "legal_basis": [
                        match.group("legal_basis1").strip(),
                        match.group("legal_basis2").strip(),
                    ],
                    "legal_basis_date": _iso_date(match.group("legal_basis_date")),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "endowment_capital", "action": "recorded",
                    "capital": match.group("capital"), "currency": "CHF",
                },
            ),
        ], ""

    match = _DE_SOLE_PROPRIETOR_ASSET_TRANSFER_DEBT_SETTLED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.sole_proprietor_asset_transfer_debt_settled.v1", {
                "kind": "asset_transfer", "source_kind": "sole_proprietor",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"), "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration_kind": "existing_debt_settled",
                "consideration_equal_to_assets": True,
            },
        )], ""

    match = _FR_TWO_ADMINISTRATORS_SECRETARY_CHANGE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_administrators_secretary_change.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role="administrateur et secrétaire", signing="Einzelunterschrift",
                extra={"action": "appointed_secretary", "signing_continues": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                role="administrateur", signing="Einzelunterschrift", extra={
                    "action": "secretary_role_ended", "previous_role": "secrétaire",
                    "signing_continues": True,
                },
            ),
        ], ""

    match = _FR_ORGANIZATION_SHARE_TRANSFER_TO_MANAGER.fullmatch(leftover)
    if match:
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        remaining = _count(match.group("remaining"))
        buyer_count = _count(match.group("buyer_count"))
        if (
            before - transferred == remaining
            and len({
                match.group("nominal"), match.group("buyer_nominal"),
                match.group("remaining_nominal"),
            }) == 1
        ):
            rule_id = "fr.persons.organization_share_transfer_to_manager.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associée", extra={
                        "action": "shares_transferred", "foreign_id": match.group("foreign_id"),
                        "counterparty": buyer, "shares_before": before,
                        "shares_transferred": transferred, "shares_count": remaining,
                        "share_nominal": match.group("nominal"), "currency": "CHF",
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, role="associé-gérant", extra={
                        "action": "shares_received", "counterparty": seller,
                        "shares_received": transferred, "shares_count": buyer_count,
                        "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                    },
                ),
            ], ""

    match = _FR_MANAGER_PRESIDENT_TRANSFER_TO_NEW_MANAGER.fullmatch(leftover)
    if match and len({
        match.group("nominal"), match.group("transfer_nominal"),
        match.group("buyer_nominal"),
    }) == 1:
        rule_id = "fr.persons.manager_president_transfer_to_new_manager.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant président",
                extra={
                    "action": "shares_transferred_and_appointed_president",
                    "counterparty": buyer, "shares_transferred": 1,
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée-gérante",
                signing=(
                    "Einzelunterschrift" if match.group("individual_signing") else None
                ), extra={
                    "action": "shares_received_and_appointed_manager",
                    "origin": match.group("origin").strip(), "counterparty": seller,
                    "shares_received": 1, "shares_count": 1,
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ], ""

    match = _FR_UNPUBLISHED_STATUTES_POINTS_SOURCE_TYPO.fullmatch(leftover)
    if match:
        events = [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.unpublished_statutes_points_source_typo.v1", {
                "kind": "additional_unpublished_points", "action": "modified",
                "published_details": False, "source_wording": "modification",
            },
        )]
        if match.group("name"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.text.unpublished_statutes_points_source_typo.v1",
                match.group("name"), role="administrateur", extra={
                    "action": "name_corrected",
                    "previous_name": match.group("previous_name").strip(),
                },
            ))
        return events, ""

    match = _FR_NEW_COMMITTEE_MEMBER_RESTRICTED_SIGNING.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.new_committee_member_restricted_signing.v1",
            match.group("name"), place=match.group("place"), role="membre du comité",
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "appointed", "origin": match.group("place").strip(),
                "with": "président ou vice-président",
            },
        )], ""

    match = _FR_REPRESENTATION_POWERS_REMOVED_ART_110.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.representation_powers_removed_art_110.v1"
        common = {
            "action": "representation_power_removed",
            "reason": "commercial_register_law_change",
            "legal_basis": re.sub(r"\s+", " ", match.group("article")),
            "scope": "entire_company", "signing_revoked": True,
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name1"),
                role=match.group("role1"), extra={**common, "previous_role": match.group("role1")},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name2"),
                role="membre du conseil d'administration", extra=common,
            ),
        ], ""

    match = _FR_TWO_FOUNDATION_MEMBERS_UNSIGNED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_foundation_members_unsigned.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="membre du conseil de fondation",
                extra={
                    "action": "appointed", "origin": match.group(f"origin{index}").strip(),
                    "signing_authority": False,
                },
            )
            for index in (1, 2)
        ], ""

    return [], leftover
