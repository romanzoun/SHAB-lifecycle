from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_FR_CONDITIONAL_PARTICIPATION_CAPITAL_TYPO = re.compile(
    r"^Augmentation conditionnelle du capital-participation fondée sur la décision "
    r"relative à l['’]octroi de droits du\s+(?P<rights_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"Nouveau capital-participation entièrement libéré:\s*CHF\s+"
    r"(?P<total_whole>[\d']+),\s*(?P<total_cents>\d{2}),\s*divisé en\s+"
    r"(?P<count>[\d']+)\s+bons(?: de participation)? nominatifs de CHF\s+"
    r"(?P<nominal>[\d'.]+)\.\s*Le conseil d['’]administration a modifié une "
    r"clause statutaire relative à une augmentation conditionnelle du "
    r"capital-participation\s*\(selon décision relative à l['’]octroi de droits de "
    r"l['’]assemblée générale du\s+(?P<clause_rights_date>\d{2}\.\d{2}\.\d{4})\),\s*"
    r"par décision du\s+(?P<change_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"pour le détail cf\. statuts\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_BOARD_MEMBERS_PRESIDENT = re.compile(
    r"^(?P<name1>[^,.;]+),\s*de et à\s+(?P<place1>[^,.;]+),\s*"
    r"président,\s*et\s+(?P<name2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*"
    r"à\s+(?P<place2>[^,.;]+),\s*sont membres du conseil d['’]administration"
    r"(?P<collective_signing> avec signature collective à deux)?\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_TWO_INDIVIDUAL_TYPO = re.compile(
    r"^Administration:\s*(?P<name1>[^,.;]+),\s*maintenant domicilié à\s+"
    r"(?P<place1>[^,.;]+),\s*(?P<country1>[A-Z]{1,3}),\s*nommé président et\s+"
    r"(?P<name2>[^,.;]+),\s*de et à\s+(?P<place2>[^,.;]+),\s*"
    r"lesqu(?:els|es) signent individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_FOREIGN_COMPANY_SHARE_TRANSFER = re.compile(
    r"^Jusqu['’]ici titulaire de\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*l['’]associée\s+(?P<seller>.+?)\s*"
    r"\((?P<seller_registry>[^)]+)\)\s+détient\s+(?P<remaining>[\d']+)\s+"
    r"parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\s+par suite de cession de\s+"
    r"(?P<transferred>[\d']+)\s+parts à\s+(?P<buyer>.+?)\s*"
    r"\((?P<buyer_registry>[^)]+)\),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{1,3}),\s*nouvelle associée pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_INHERITANCE_COMMUNITY_MEMBERS = re.compile(
    r"^Die Erbengemeinschaft\s+(?P<decedent>.+?)\s+besteht aus\s+"
    r"(?P<name1>[^,.;]+),\s*von\s+(?P<origin1>[^,(]+)\s*"
    r"\((?P<origin_canton1>[A-Z]{2})\),\s*in\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*(?P<nationality2>[^,.;]+ Staatsangehöriger),\s*"
    r"in\s+(?P<place2>[^()]+?)\s*\((?P<country2>[A-Z]{2})\)\s+und\s+"
    r"(?P<name3>[^,.;]+),\s*(?P<nationality3>[^,.;]+ Staatsangehöriger),\s*"
    r"in\s+(?P<place3>[^()]+?)\s*\((?P<country3>[A-Z]{2})\)\.?$",
    re.I | re.UNICODE,
)
_FR_ORGANIZATION_SHARE_TRANSFER_NOW_REMAINING = re.compile(
    r"^(?P<seller>.+?)\s*\((?P<seller_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+"
    r"maintenant associée pour\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*par suite de cession de\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<transfer_nominal>[\d'.]+)\s+"
    r"à\s+(?P<buyer>.+?)\s*\((?P<buyer_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*nouvelle associée pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_OFFICER_CORRECTION_INCOMPLETE_ENTRY = re.compile(
    r"^Mit dem im SHAB-Nr\.\s*(?P<notice_number>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten TR-Eintrag Nr\.\s*"
    r"(?P<entry>[\d']+)\s+vom\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+wurde "
    r"nicht der vollständige bisherige Text publiziert\.\s*Korrekt wäre:\s*"
    r"(?P<name>.+?),\s*von\s+(?P<origin>[^,.;]+),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<country>[A-Z]{2})\),\s*"
    r"(?P<role>[^,.;]+),\s*mit Einzelunterschrift\s*"
    r"\[bisher:\s*in\s+(?P<previous_place>[^,;\]]+),\s*"
    r"(?P<previous_role>[^,;\]]+),\s*mit Einzelunterschrift\]\.?$",
    re.I | re.UNICODE,
)
_FR_LIQUIDATION_NAME_CORPORATE_LIQUIDATOR = re.compile(
    r"^La liquidation est opérée sous la raison de commerce:\s*"
    r"(?P<liquidation_name>.+? en liquidation),\s*par\s+(?P<name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nommée liquidatrice\.?$",
    re.I | re.UNICODE,
)
_DE_DOMESTIC_MERGER_DEFICIT_FREE_EQUITY = re.compile(
    r"^Fusion:\s*Übernahme der Aktiven und des Fremdkapitals der\s+"
    r"(?P<absorbed_name>.+?),\s*in\s+(?P<absorbed_place>[^()]+?)\s*"
    r"\((?P<registry_id>[^)]+)\)\s*,\s*gemäss Fusionsvertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Bilanz per\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\.\s*Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Fremdkapital von CHF\s+(?P<liabilities>[\d'.]+),\s*"
    r"d\.h\.\s*ein Passivenüberschuss von CHF\s+(?P<deficit>[\d'.]+)\s+gehen "
    r"auf die übernehmende Gesellschaft über\.\s*Die Gesellschaft weist gemäss "
    r"Bestätigung des zugelassenen Revisionsexperten über frei verwendbares "
    r"Eigenkapital im Umfang der Unterdeckung und der Überschuldung auf\.\s*"
    r"Da derselbe Aktionär sämtliche Aktien der an der Fusion beteiligten "
    r"Gesellschaften hält,\s*findet weder eine Kapitalerhöhung noch eine "
    r"Aktienzuteilung statt\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_CLAUSE_EXPIRED = re.compile(
    r"^Streichung der Statutenbestimmung über die mit Ermächtigungsbeschluss vom\s+"
    r"(?P<authorization_date>\d{2}\.\d{2}\.\d{4})\s+eingeführte genehmigte "
    r"Kapitalerhöhung infolge Ablaufs der zeitlichen Befristung\.?$",
    re.I | re.UNICODE,
)
_DE_ASSOCIATE_MANAGER_CORRECTION_INCOMPLETE_ENTRY = re.compile(
    r"^Mit dem im SHAB-Nr\.\s*(?P<notice_number>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten TR-Text\s+"
    r"(?P<entry>[\d/]+)\s+wurden nicht die vollständigen Angaben aufgeführt\.\s*"
    r"Korrekt wäre:\s*(?P<name>.+?),\s*"
    r"(?P<nationality>[^,.;]+ Staatsangehöriger),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<country>[A-Z]{2})\),\s*"
    r"(?P<role>Gesellschafter und Vorsitzender der Geschäftsführung),\s*"
    r"mit Einzelunterschrift,\s*mit\s+(?P<shares>[\d']+)\s+Stammanteilen zu je "
    r"CHF\s+(?P<nominal>[\d'.]+)\s*\[bisher:\s*in\s+"
    r"(?P<previous_place>[^,;\]]+),\s*(?P<previous_role>[^,;\]]+),\s*"
    r"mit Einzelunterschrift\]\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_LIQUIDATORS_COLLECTIVE = re.compile(
    r"^Liquidateurs:\s*(?P<name1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^()]+?)\s*\((?P<canton1>[A-Z]{2})\)\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*lesquels signent collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_TWO_NEW_ASSOCIATES = re.compile(
    r"^(?P<seller>[^,.;]+),\s*lequel est maintenant de\s+(?P<seller_origin>[^,.;]+),\s*"
    r"cède\s+(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*par\s+(?P<count1>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal1>[\d'.]+)\s+à\s+(?P<buyer1>[^,.;]+),\s*nouvel associé"
    r"(?P<buyer1_signing> avec signature individuelle)?,\s*et par\s+"
    r"(?P<count2>[\d']+)\s+parts de CHF\s+(?P<nominal2>[\d'.]+)\s+à\s+"
    r"(?P<buyer2>[^,.;]+),\s*nouvel associé sans signature,\s*tous deux de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*titulaires respectivement "
    r"de\s+(?P<buyer_total1>[\d']+)\s+et\s+(?P<buyer_total2>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*(?P=seller)\s+reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_EARLY_DELETION_EXPERT_CONFIRMATION = re.compile(
    r"^Die Bestätigung des zugelassenen Revisionsexperten vom\s+"
    r"(?P<confirmation_date>\d{2}\.\d{2}\.\d{4})\s+zur Löschung vor Ablauf des "
    r"Sperrjahres liegt vor\.\s*\[Die Löschung der Gesellschaft erfolgt,\s*sobald "
    r"die Zustimmung der Steuerverwaltung vorliegt\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_BUYER_APPOINTED_SELLER_PRESIDENT = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à l['’]associé\s+(?P<buyer>[^,.;]+),\s*"
    r"désormais à\s+(?P<place>[^,.;]+),\s*lequel est élu gérant"
    r"(?P<buyer_signing> avec signature individuelle)?,\s*maintenant "
    r"titulaire de\s+(?P<buyer_after>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*(?P=seller),\s*qui est élu président des "
    r"gérants et continue à signer individuellement,\s*reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_NAME_SPELLING_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que le nom "
    r"de\s+(?P<previous_name>.+?)\s+s['’]orthographie en réalité\s+"
    r"(?P<name>.+?)\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


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
        role=role.strip() if role else None,
        signing=signing,
        payload={
            "name": clean_name,
            "place": clean_place,
            **({"uid": uid} if uid else {}),
            **(extra or {}),
        },
    )


def extract_parser227_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 227."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_CONDITIONAL_PARTICIPATION_CAPITAL_TYPO.fullmatch(leftover)
    if match:
        total = f"{match.group('total_whole')}.{match.group('total_cents')}"
        count = _count(match.group("count"))
        if (
            match.group("rights_date") == match.group("clause_rights_date")
            and _amount(total) == count * _amount(match.group("nominal"))
        ):
            rule_id = "fr.text.conditional_participation_capital_comma_typo.v1"
            return [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "capital_changed", rule_id, {
                        "kind": "conditional_participation_capital_increase",
                        "rights_decision_date": _iso_date(match.group("rights_date")),
                        "currency": "CHF", "total": total, "fully_paid": True,
                        "participation_certificates_count": count,
                        "participation_certificate_nominal": match.group("nominal"),
                        "registered": True, "source_decimal_separator_corrected": True,
                    },
                ),
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "statutes_changed", rule_id, {
                        "kind": "conditional_participation_capital_clause",
                        "action": "changed",
                        "rights_decision_date": _iso_date(match.group("clause_rights_date")),
                        "decision_date": _iso_date(match.group("change_date")),
                        "details_in_statutes": True,
                    },
                ),
            ], ""

    match = _FR_TWO_BOARD_MEMBERS_PRESIDENT.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_board_members_president.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="président du conseil d'administration",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed", "origin": match.group("place1").strip()},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="membre du conseil d'administration",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed", "origin": match.group("origin2").strip()},
            ),
        ], ""

    match = _FR_ADMINISTRATION_TWO_INDIVIDUAL_TYPO.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administration_two_individual_lesques_typo.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="président du conseil d'administration",
                signing="Einzelunterschrift", extra={
                    "action": "appointed_president_and_domicile_changed",
                    "country": match.group("country1"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="membre du conseil d'administration",
                signing="Einzelunterschrift", extra={
                    "action": "appointed", "origin": match.group("place2").strip(),
                    "source_wording": "lesques",
                },
            ),
        ], ""

    match = _FR_FOREIGN_COMPANY_SHARE_TRANSFER.fullmatch(leftover)
    if match:
        before = _count(match.group("before"))
        remaining = _count(match.group("remaining"))
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        if (
            before == remaining + transferred
            and transferred == buyer_count
            and len({match.group("nominal"), match.group("remaining_nominal"), match.group("buyer_nominal")}) == 1
        ):
            rule_id = "fr.persons.foreign_company_share_transfer.v1"
            common = {"currency": "CHF", "share_nominal": match.group("nominal")}
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("seller"),
                    role="associée", extra={
                        "action": "shares_transferred", "shares_before": before,
                        "shares_transferred": transferred, "shares_count": remaining,
                        "registry_id": match.group("seller_registry").strip(),
                        "counterparty": match.group("buyer").strip(), **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("buyer"),
                    place=match.group("place"), role="associée", extra={
                        "action": "appointed_and_shares_received",
                        "shares_received": transferred, "shares_count": buyer_count,
                        "registry_id": match.group("buyer_registry").strip(),
                        "country": match.group("country"),
                        "counterparty": match.group("seller").strip(), **common,
                    },
                ),
            ], ""

    match = _DE_INHERITANCE_COMMUNITY_MEMBERS.fullmatch(leftover)
    if match:
        members = [
            {
                "name": match.group("name1").strip(),
                "origin": match.group("origin1").strip(),
                "origin_canton": match.group("origin_canton1"),
                "place": match.group("place1").strip(),
            },
            {
                "name": match.group("name2").strip(),
                "nationality": match.group("nationality2").strip(),
                "place": match.group("place2").strip(),
                "country": match.group("country2"),
            },
            {
                "name": match.group("name3").strip(),
                "nationality": match.group("nationality3").strip(),
                "place": match.group("place3").strip(),
                "country": match.group("country3"),
            },
        ]
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.inheritance_community_members.v1", {
                "kind": "inheritance_community", "action": "members_recorded",
                "decedent": match.group("decedent").strip(), "members": members,
            },
        )], ""

    match = _FR_ORGANIZATION_SHARE_TRANSFER_NOW_REMAINING.fullmatch(leftover)
    if match:
        remaining = _count(match.group("remaining"))
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        if transferred == buyer_count and len({
            match.group("nominal"), match.group("transfer_nominal"), match.group("buyer_nominal")
        }) == 1:
            rule_id = "fr.persons.organization_share_transfer_now_remaining.v1"
            common = {"currency": "CHF", "share_nominal": match.group("nominal")}
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("seller"),
                    uid=match.group("seller_uid"), role="associée", extra={
                        "action": "shares_transferred", "shares_transferred": transferred,
                        "shares_count": remaining, "shares_before": remaining + transferred,
                        "counterparty_uid": match.group("buyer_uid"), **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("buyer"),
                    place=match.group("place"), uid=match.group("buyer_uid"),
                    role="associée", extra={
                        "action": "appointed_and_shares_received",
                        "shares_received": transferred, "shares_count": buyer_count,
                        "counterparty_uid": match.group("seller_uid"), **common,
                    },
                ),
            ], ""

    match = _DE_OFFICER_CORRECTION_INCOMPLETE_ENTRY.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.incomplete_entry_officer_corrected.v1",
            match.group("name"), place=match.group("place"), role=match.group("role"),
            signing="Einzelunterschrift", extra={
                "action": "entry_completed_and_corrected", "correction": True,
                "origin": match.group("origin").strip(), "country": match.group("country"),
                "previous_place": match.group("previous_place").strip(),
                "previous_role": match.group("previous_role").strip(),
                "notice_number": match.group("notice_number"),
                "notice_date": _iso_date(match.group("notice_date")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_LIQUIDATION_NAME_CORPORATE_LIQUIDATOR.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.corporate_liquidator_with_liquidation_name.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_name_changed", rule_id, {
                    "kind": "liquidation_name", "action": "changed_for_liquidation",
                    "name": match.group("liquidation_name").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), uid=match.group("uid"), role="liquidatrice",
                extra={"action": "appointed_liquidator"},
            ),
        ], ""

    match = _DE_DOMESTIC_MERGER_DEFICIT_FREE_EQUITY.fullmatch(leftover)
    if match and (
        _amount(match.group("liabilities")) - _amount(match.group("assets"))
        == _amount(match.group("deficit"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "de.text.domestic_merger_deficit_free_equity.v1", {
                "kind": "absorption", "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_registry_id": match.group("registry_id").strip(),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "deficit": match.group("deficit"), "currency": "CHF",
                "deficit_covered_by_free_equity": True, "same_shareholder": True,
                "capital_increase": False, "share_allocation": False,
            },
        )], ""

    match = _DE_AUTHORIZED_CAPITAL_CLAUSE_EXPIRED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_clause_expired.v1", {
                "kind": "authorized_capital_clause", "action": "removed",
                "authorization_date": _iso_date(match.group("authorization_date")),
                "reason": "authorization_expired", "basis": "statutes",
            },
        )], ""

    match = _DE_ASSOCIATE_MANAGER_CORRECTION_INCOMPLETE_ENTRY.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.incomplete_entry_associate_manager_corrected.v1",
            match.group("name"), place=match.group("place"), role=match.group("role"),
            signing="Einzelunterschrift", extra={
                "action": "entry_completed_and_corrected", "correction": True,
                "nationality": match.group("nationality").strip(),
                "country": match.group("country"),
                "shares_count": _count(match.group("shares")),
                "share_nominal": match.group("nominal"), "currency": "CHF",
                "previous_place": match.group("previous_place").strip(),
                "previous_role": match.group("previous_role").strip(),
                "notice_number": match.group("notice_number"),
                "notice_date": _iso_date(match.group("notice_date")),
                "entry": match.group("entry"),
            },
        )], ""

    match = _FR_TWO_LIQUIDATORS_COLLECTIVE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_liquidators_collective.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="liquidateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_liquidator", "origin": match.group("origin1").strip(),
                    "place_canton": match.group("canton1"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="liquidateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_liquidator", "origin": match.group("origin2").strip(),
                },
            ),
        ], ""

    match = _FR_SHARE_TRANSFER_TWO_NEW_ASSOCIATES.fullmatch(leftover)
    if match:
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        count1 = _count(match.group("count1"))
        count2 = _count(match.group("count2"))
        remaining = _count(match.group("remaining"))
        if (
            transferred == count1 + count2
            and before == remaining + transferred
            and count1 == _count(match.group("buyer_total1"))
            and count2 == _count(match.group("buyer_total2"))
            and len({
                match.group("nominal"), match.group("nominal1"), match.group("nominal2"),
                match.group("buyer_nominal"), match.group("remaining_nominal"),
            }) == 1
        ):
            rule_id = "fr.persons.share_transfer_two_new_associates_respective.v1"
            common = {"currency": "CHF", "share_nominal": match.group("nominal")}
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("seller"), role="associé",
                    extra={
                        "action": "shares_transferred_and_origin_changed",
                        "origin": match.group("seller_origin").strip(),
                        "shares_before": before, "shares_transferred": transferred,
                        "shares_count": remaining, **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("buyer1"),
                    place=match.group("place"), role="associé",
                    signing="Einzelunterschrift", extra={
                        "action": "appointed_and_shares_received",
                        "origin": match.group("origin").strip(),
                        "shares_received": count1, "shares_count": count1, **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("buyer2"),
                    place=match.group("place"), role="associé", extra={
                        "action": "appointed_and_shares_received",
                        "origin": match.group("origin").strip(),
                        "shares_received": count2, "shares_count": count2,
                        "signing_authority": False, **common,
                    },
                ),
            ], ""

    match = _DE_EARLY_DELETION_EXPERT_CONFIRMATION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.early_deletion_expert_confirmation.v1", {
                "kind": "deletion", "action": "early_deletion_clearance_confirmed",
                "confirmation_date": _iso_date(match.group("confirmation_date")),
                "waiting_period_expired": False, "tax_authority_consent_pending": True,
            },
        )], ""

    match = _FR_MANAGER_TRANSFER_BUYER_APPOINTED_SELLER_PRESIDENT.fullmatch(leftover)
    if match:
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        remaining = _count(match.group("remaining"))
        buyer_after = _count(match.group("buyer_after"))
        if (
            before == remaining + transferred
            and buyer_after >= transferred
            and len({match.group("nominal"), match.group("buyer_nominal"), match.group("remaining_nominal")}) == 1
        ):
            rule_id = "fr.persons.manager_transfer_buyer_manager_seller_president.v1"
            common = {"currency": "CHF", "share_nominal": match.group("nominal")}
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("seller"),
                    role="associé-gérant président", signing="Einzelunterschrift", extra={
                        "action": "appointed_president_and_shares_transferred",
                        "shares_before": before, "shares_transferred": transferred,
                        "shares_count": remaining, "counterparty": match.group("buyer").strip(),
                        **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("buyer"),
                    place=match.group("place"), role="associé-gérant",
                    signing="Einzelunterschrift", extra={
                        "action": "appointed_manager_and_shares_received",
                        "shares_before": buyer_after - transferred,
                        "shares_received": transferred, "shares_count": buyer_after,
                        "counterparty": match.group("seller").strip(), **common,
                    },
                ),
            ], ""

    match = _FR_PERSON_NAME_SPELLING_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.persons.name_spelling_corrected.v1",
            match.group("name"), extra={
                "action": "name_spelling_corrected", "correction": True,
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    return [], leftover
