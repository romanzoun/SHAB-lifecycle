from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_FR_NON_PUBLIC_STATUTES_TYPO = re.compile(
    r"^sur des points non sousmis à publication\.?$", re.I | re.UNICODE
)
_FR_MANAGER_TRANSFER_TO_UNSIGNED_ASSOCIATE = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s*"
    r"(?P<place>[^,.;]+),\s*nouvel associé avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"sans signature;\s*(?P=seller)\s+reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_RESTRICTION_REMOVED_AND_CAPITAL = re.compile(
    r"^Suppression de la restriction au transfert des\s+"
    r"(?P<count>[\d']+)\s+actions de CHF\s+(?P<nominal>[\d'.]+),\s*nominatives\.\s*"
    r"Capital-actions:\s*CHF\s+(?P<total>[\d'.]+),\s*entièrement libéré,\s*"
    r"divisé en\s+(?P<capital_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<capital_nominal>[\d'.]+),\s*nominatives\.?$",
    re.I | re.UNICODE,
)
_FR_PROXY_AND_NEW_MANAGER_APPOINTED = re.compile(
    r"^(?P<name1>[^,.;]+),\s*jusqu['’]ici avec procuration collective à deux,\s*"
    r"et\s+(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s*(?P<place2>[^,.;]+),\s*"
    r"sont nommés gérants avec signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_NEW_BRANCH_SEAT = re.compile(
    r"^Nouveau siège de l['’]organe de révision:\s*succursale à\s*"
    r"(?P<place>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_SEAT_CHANGED_RESIDUAL = re.compile(
    r"^(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s*"
    r"\[bisher:\s*(?P<previous_place>[^()]+?)\s*"
    r"\((?P<previous_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\]\.?$",
    re.I | re.UNICODE,
)
_FR_INTENDED_ASSET_ACQUISITION_COMPLETED_SINGLE_DATE = re.compile(
    r"^La reprise de bien envisagée à la constitution a été réalisée par contrat du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+pour le prix de CHF\s+"
    r"(?P<price>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_PURPOSE_SUPPLEMENT_TRUNCATED_NOTICE = re.compile(
    r"^,?\s*(?P<notice_month>\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\.\s*L['’]inscription\s+"
    r"(?P<entry>[\d']+)\s+du\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"est complétée en ce sens que le but et objet partculier de la succursale est:\s*"
    r"(?P<purpose>.+)\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBER_APPOINTED_PROXY_REVOKED = re.compile(
    r"^(?P<name>[^,.;]+)\s+est nommé membre du conseil d['’]administration\s+"
    r"avec signature collective à deux;\s*sa procuration est radiée\.?$",
    re.I | re.UNICODE,
)
_DE_INTENDED_ASSET_ACQUISITION_CORRECTED_FRAGMENT = re.compile(
    r"^eingetragenen Einzelunternehmens\s+(?P<source>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"gemäss der Schlussbilanz per\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"mit Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+und Passiven\s*"
    r"\(Fremdkapital\)\s+von CHF\s+(?P<liabilities>[\d'.]+)\s+"
    r"zum Preis von höchstens CHF\s+(?P<price>[\d'.]+)\s+zu übernehmen\.?$",
    re.I | re.UNICODE,
)
_FR_ORIGIN_AND_SHARED_DOMICILE_CHANGED = re.compile(
    r"^(?P<name1>[^,.;]+),\s*désormais de\s+(?P<origin1>[^,.;]+),\s*"
    r"et\s+(?P<name2>[^,.;]+)\s+sont maintenant à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_LIQUIDATION_ADDRESS_SUPPLEMENT_RESIDUAL = re.compile(
    r"^Complément:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée en ce sens:\s*$",
    re.I | re.UNICODE,
)
_FR_FOUR_FOUNDATION_MEMBERS_WITHOUT_SIGNATURE = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s*(?P<place1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s*(?P<place2>[^,.;]+),\s*"
    r"(?P<country2>[A-Z]{1,3}),\s*"
    r"(?P<name3>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin3>[^,.;]+),\s*à\s*(?P<place3>[^,.;]+)\s+et\s+"
    r"(?P<name4>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin4>[^,.;]+),\s*à\s*(?P<place4>[^,.;]+),\s*"
    r"(?P<country4>[A-Z]{1,3}),\s*sont membres du conseil de fondation,\s*"
    r"tous sans signature\.?$",
    re.I | re.UNICODE,
)
_FR_RENAMED_ASSOCIATE_PAIR_AND_TRANSFER = re.compile(
    r"^(?P<previous_name>[^,.;]+),\s*qui se nomme désormais\s+"
    r"(?P<seller>[^,.;]+),\s*et\s+(?P<buyer>[^,.;]+)\s+sont maintenant "
    r"titulaires de\s+(?P<initial_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<initial_nominal>[\d'.]+)\s+chacun et signent désormais "
    r"individuellement\.\s*(?P=seller)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<seller_before>[\d']+)\s+parts "
    r"de CHF\s+(?P<transfer_nominal>[\d'.]+)\s+à\s+(?P=buyer),\s*désormais "
    r"titulaire de\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*(?P=seller)\s+a désormais\s+"
    r"(?P<remaining>[\d']+)\s+part(?:s)? de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_AMOUNT_TYPO_CORRECTED = re.compile(
    r"^Korrektur eines Tippfehlers in der Betragsangabe\.?$", re.I | re.UNICODE
)
_DE_INCOMING_SPIN_OFF_TWO_RECIPIENTS_SPACED_COMMA = re.compile(
    r"^Aufspaltung:\s*Die Gesellschaft und die\s+(?P<co_recipient>.+?)\s*,\s*"
    r"in\s+(?P<co_recipient_place>[^()]+?)\s*"
    r"\((?P<co_recipient_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*übernehmen von der\s+"
    r"(?P<source>.+?),\s*in\s+(?P<source_place>[^()]+?)\s*"
    r"\((?P<source_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*je einen Teil des "
    r"Vermögens\.\s*Die Gesellschaft übernimmt dabei gemäss Spaltungsvertrag "
    r"vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\.\s*Da dieselben Aktionäre sämtliche Aktien der "
    r"an der Aufspaltung beteiligten Gesellschaften halten,\s*findet weder eine "
    r"Kapitalerhöhung noch eine Aktienzuteilung statt\.?$",
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


def extract_parser190_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 190."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    if _FR_NON_PUBLIC_STATUTES_TYPO.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.non_public_statutes_typo_sousmis.v1", {
                "kind": "non_public_statute_changes",
                "publication_relevant_facts": False,
                "source_typo": "sousmis",
            },
        )], ""

    match = _FR_MANAGER_TRANSFER_TO_UNSIGNED_ASSOCIATE.fullmatch(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        before = _count(match.group("before"))
        remaining = _count(match.group("remaining"))
        buyer_count = _count(match.group("buyer_count"))
        if (
            before - transferred == remaining
            and transferred == buyer_count
            and len({
                match.group("nominal"),
                match.group("buyer_nominal"),
                match.group("remaining_nominal"),
            }) == 1
        ):
            rule_id = "fr.persons.manager_transfer_to_unsigned_associate.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            common = {
                "share_nominal": match.group("nominal"), "currency": "CHF",
            }
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé-gérant",
                    extra={
                        **common, "action": "shares_transferred",
                        "counterparty": buyer, "shares_before": before,
                        "shares_transferred": transferred, "shares_count": remaining,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé", extra={
                        **common, "action": "shares_received", "counterparty": seller,
                        "origin": match.group("origin").strip(),
                        "new_associate": True, "without_signature": True,
                        "shares_received": transferred, "shares_count": buyer_count,
                    },
                ),
            ], ""

    match = _FR_SHARE_RESTRICTION_REMOVED_AND_CAPITAL.fullmatch(leftover)
    if match:
        count = _count(match.group("count"))
        capital_count = _count(match.group("capital_count"))
        nominal = _amount(match.group("nominal"))
        capital_nominal = _amount(match.group("capital_nominal"))
        total = _amount(match.group("total"))
        if count == capital_count and nominal == capital_nominal and count * nominal == total:
            rule_id = "fr.text.share_restriction_removed_and_capital.v1"
            return [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "capital_changed", rule_id, {
                        "kind": "share_transfer_restriction", "action": "removed",
                        "shares_count": count, "share_nominal": match.group("nominal"),
                        "share_kind": "actions nominatives", "currency": "CHF",
                    },
                ),
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "capital_changed", rule_id, {
                        "kind": "share_capital", "action": "composition_recorded",
                        "total": match.group("total"), "fully_paid": True,
                        "shares_count": capital_count,
                        "share_nominal": match.group("capital_nominal"),
                        "share_kind": "actions nominatives", "currency": "CHF",
                    },
                ),
            ], ""

    match = _FR_PROXY_AND_NEW_MANAGER_APPOINTED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.proxy_and_new_manager_appointed.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"), role="gérant",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_manager",
                    "previous_signing": "Kollektivprokura zu zweien",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="gérant",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_manager",
                    "origin": match.group("origin2").strip(),
                },
            ),
        ], ""

    match = _FR_AUDITOR_NEW_BRANCH_SEAT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.text.auditor_new_branch_seat.v1", {
                "kind": "auditor_seat", "action": "seat_changed",
                "seat_kind": "branch", "to": match.group("place").strip(),
            },
        )], ""

    match = _DE_BRANCH_SEAT_CHANGED_RESIDUAL.fullmatch(leftover)
    if match and match.group("uid") == match.group("previous_uid"):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_seat_changed_residual.v1", {
                "action": "seat_changed", "from": match.group("previous_place").strip(),
                "to": match.group("place").strip(), "branch_uid": match.group("uid"),
                "previous_branch_uid": match.group("previous_uid"),
            },
        )], ""

    match = _FR_INTENDED_ASSET_ACQUISITION_COMPLETED_SINGLE_DATE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.intended_asset_acquisition_completed_single_date.v1", {
                "kind": "intended_asset_acquisition", "action": "completed",
                "contract_date": _iso_date(match.group("date")),
                "price": match.group("price"), "currency": "CHF",
            },
        )], ""

    match = _FR_BRANCH_PURPOSE_SUPPLEMENT_TRUNCATED_NOTICE.fullmatch(leftover)
    if match:
        month, year = match.group("notice_month").split(".")
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "purpose_changed", "fr.text.branch_purpose_supplement_truncated_notice.v1", {
                "scope": "branch", "action": "supplemented",
                "purpose": match.group("purpose").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_month": f"{int(year):04d}-{int(month):02d}",
                "notice_ref": match.group("notice_ref"),
                "source_typo": "partculier",
            },
        )], ""

    match = _FR_BOARD_MEMBER_APPOINTED_PROXY_REVOKED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.board_member_appointed_proxy_revoked.v1",
            match.group("name"), role="membre du conseil d'administration",
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "appointed", "previous_signing": "procuration",
                "procuration_revoked": True,
            },
        )], ""

    match = _DE_INTENDED_ASSET_ACQUISITION_CORRECTED_FRAGMENT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.intended_asset_acquisition_corrected_fragment.v1", {
                "kind": "intended_asset_acquisition", "action": "publication_corrected",
                "source": match.group("source").strip(),
                "source_place": match.group("place").strip(),
                "source_uid": match.group("uid"),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital",
                "price_limit": "maximum", "price": match.group("price"),
                "currency": "CHF",
            },
        )], ""

    match = _FR_ORIGIN_AND_SHARED_DOMICILE_CHANGED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.origin_and_shared_domicile_changed.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place"), extra={
                    "action": "origin_and_domicile_changed",
                    "origin": match.group("origin1").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place"), extra={"action": "domicile_changed"},
            ),
        ], ""

    match = _FR_LIQUIDATION_ADDRESS_SUPPLEMENT_RESIDUAL.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.liquidation_address_supplement_residual.v1", {
                "kind": "liquidation_address", "action": "supplemented",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_FOUR_FOUNDATION_MEMBERS_WITHOUT_SIGNATURE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.four_foundation_members_without_signature.v1"
        people = (
            (1, None), (2, match.group("country2")),
            (3, None), (4, match.group("country4")),
        )
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role="membre du conseil de fondation", extra={
                    "action": "appointed",
                    "origin": match.group(f"origin{index}").strip(),
                    "without_signature": True,
                    **({"country": country} if country else {}),
                },
            )
            for index, country in people
        ], ""

    match = _FR_RENAMED_ASSOCIATE_PAIR_AND_TRANSFER.fullmatch(leftover)
    if match:
        initial = _count(match.group("initial_count"))
        seller_before = _count(match.group("seller_before"))
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        remaining = _count(match.group("remaining"))
        if (
            initial == seller_before
            and seller_before - transferred == remaining
            and initial + transferred == buyer_count
            and len({
                match.group("initial_nominal"), match.group("transfer_nominal"),
                match.group("buyer_nominal"), match.group("remaining_nominal"),
            }) == 1
        ):
            rule_id = "fr.persons.renamed_associate_pair_and_transfer.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            common = {
                "share_nominal": match.group("initial_nominal"), "currency": "CHF",
            }
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé",
                    signing="Einzelunterschrift", extra={
                        **common, "action": "renamed_and_shares_transferred",
                        "previous_name": match.group("previous_name").strip(),
                        "counterparty": buyer, "shares_before": seller_before,
                        "shares_transferred": transferred, "shares_count": remaining,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, role="associé",
                    signing="Einzelunterschrift", extra={
                        **common, "action": "shares_received_and_signing_changed",
                        "counterparty": seller, "shares_before": initial,
                        "shares_received": transferred, "shares_count": buyer_count,
                    },
                ),
            ], ""

    if _DE_AMOUNT_TYPO_CORRECTED.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.amount_typo_corrected.v1", {
                "kind": "amount", "action": "corrected", "reason": "typographical_error",
            },
        )], ""

    match = _DE_INCOMING_SPIN_OFF_TWO_RECIPIENTS_SPACED_COMMA.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.incoming_spin_off_two_recipients_spaced_comma.v1", {
                "kind": "spin_off_acquisition", "scope": "part_of_assets_and_liabilities",
                "date": _iso_date(match.group("date")), "document": "spaltungsvertrag",
                "source": match.group("source").strip(),
                "source_place": match.group("source_place").strip(),
                "source_uid": match.group("source_uid"),
                "co_recipient": match.group("co_recipient").strip(),
                "co_recipient_place": match.group("co_recipient_place").strip(),
                "co_recipient_uid": match.group("co_recipient_uid"),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "currency": "CHF", "same_shareholders": True,
                "capital_increase": False, "share_allocation": False,
            },
        )], ""

    return [], text
