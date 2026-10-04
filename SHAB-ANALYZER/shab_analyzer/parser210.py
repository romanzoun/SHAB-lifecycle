from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_PARTICIPATION_CAPITAL_COUNT_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le "
    r"capital-participation est divisé en\s+(?P<count>[\d']+)\s+bons de "
    r"participation nominatifs de CHF\s+(?P<nominal>[\d'.]+)\s*"
    r"\(et non de\s+(?P<previous_count>[\d']+)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_DE_BUSINESS_UNIT_ASSET_TRANSFER_CASH = re.compile(
    r'^Vermögensübertragung:\s*Die Aktiengesellschaft überträgt gemäss Vertrag vom\s+'
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+den\s+(?P<division>.+?)\s+"
    r"mit Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+und Passiven\s*"
    r"\(Fremdkapital\)\s*von CHF\s+(?P<liabilities>[\d'.]+)\s+auf die\s+"
    r'["“](?P<recipient>.+?)["”]\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*'
    r"in\s+(?P<place>[^.]+)\.\s*Gegenleistung:\s*CHF\s+"
    r"(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_LIQUIDATION_ADDRESS_TYPO = re.compile(
    r"^Neue\s+Lquidationsadresse:\s*(?P<street>.+?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<place>[^.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUR_SHARE_TRANSFERS = re.compile(
    r"^(?P<seller1>[^,.;]+)\s+cède\s+(?P<transfer1>[\d']+)\s+de ses\s+"
    r"(?P<seller1_before>[\d']+)\s+parts de CHF\s+(?P<nominal1>[\d'.]+)\s+à\s+"
    r"(?P<buyer1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*nouvel associé-gérant avec signature collective "
    r"à deux,\s*titulaire de\s+(?P<buyer1_initial>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal2>[\d'.]+)\.\s*(?P=seller1)\s+cède\s+"
    r"(?P<transfer2>[\d']+)\s+de ses\s+(?P<seller1_intermediate>[\d']+)\s+"
    r"parts de CHF\s+(?P<nominal3>[\d'.]+)\s+à\s+(?P<buyer2>[^,.;]+),\s*"
    r"de\s+(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"nouvel associé sans signature,\s*titulaire de\s+"
    r"(?P<buyer2_initial>[\d']+)\s+parts de CHF\s+(?P<nominal4>[\d'.]+)\.\s*"
    r"(?P<seller2>[^,.;]+)\s+cède\s+(?P<transfer3>[\d']+)\s+de ses\s+"
    r"(?P<seller2_before>[\d']+)\s+parts de CHF\s+(?P<nominal5>[\d'.]+)\s+à "
    r"l['’]associé-gérant\s+(?P<buyer1_again>[^,.;]+),\s*désormais titulaire "
    r"de\s+(?P<buyer1_final>[\d']+)\s+parts de CHF\s+(?P<nominal6>[\d'.]+)\.\s*"
    r"(?P=seller2)\s+cède\s+(?P<transfer4>[\d']+)\s+de ses\s+"
    r"(?P<seller2_intermediate>[\d']+)\s+parts de CHF\s+(?P<nominal7>[\d'.]+)\s+"
    r"à l['’]associé-gérant\s+(?P<buyer2_again>[^,.;]+),\s*désormais titulaire "
    r"de\s+(?P<buyer2_final>[\d']+)\s+parts de CHF\s+(?P<nominal8>[\d'.]+)\.\s*"
    r"(?P<seller1_final_name>[^,.;]+)\s+et\s+(?P<seller2_final_name>[^,.;]+)\s+"
    r"sont désormais titulaires de\s+(?P<seller_final>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal9>[\d'.]+)\s+chacun\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_PRESIDENCY_SUPPLEMENT = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée en ce sens que "
    r"l['’]administrateur\s+(?P<name>[^.]+?)\s+est président du conseil "
    r"d['’]administration\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_NEW_COMMITTEE_MEMBERS = re.compile(
    r"^Nouveaux membres du comité avec signature collective à deux:\s*"
    r"(?P<name1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*(?P<role1>secrétaire),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*de et à\s+(?P<place2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_AGGREGATE_SHARE_TRANSFER = re.compile(
    r"^Jusqu['’]ici titulaires de\s+(?P<before1>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal1>[\d'.]+)\s+et de\s+(?P<before2>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal2>[\d'.]+)\s+respectivement,\s*les associés-gérants\s+"
    r"(?P<seller1>[^,.;]+)\s+et\s+(?P<seller2>[^,.;]+)\s+détiennent "
    r"respectivement\s+(?P<remaining1>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal3>[\d'.]+)\s+et\s+(?P<remaining2>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal4>[\d'.]+)\s+par suite de cession de\s+"
    r"(?P<transferred>[\d']+)\s+parts à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{1,3}),\s*nouvel associé-gérant pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<nominal5>[\d'.]+),\s*"
    r"lequel signe individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_PURPOSE_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le but exact est:\s*"
    r"(?P<purpose>.+?)\s*\(et non pas\s+(?P<incorrect>.+?),\s*comme publié\)\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_WITH_ACQUIRER_OWN_SHARES = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di\s+(?P<absorbed_name>.+?)\s*,\s*"
    r"in\s+(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"secondo il contratto di fusione del\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+e bilancio al\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta attivi per CHF\s+"
    r"(?P<assets>[\d'.]+),\s*nei quali sono comprese\s+"
    r"(?P<share_count>[\d']+)\s+azioni nominative da CHF\s+"
    r"(?P<share_nominal>[\d'.]+)\s+della società assuntrice,\s*e passivi "
    r"verso terzi per CHF\s+(?P<liabilities>[\d'.]+)\.\s*La fusione avviene "
    r"senza aumento di capitale visto che gli azionisti della società trasferente "
    r"a seguito della fusione ricevono le azioni proprie della società assuntrice\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_PETITION_REJECTED_RESIDUE = re.compile(
    r"^und das Konkursbegehren zufolge nachträglicher Zahlung abgewiesen\.\s*"
    r"\[gestrichen:\s*(?P<authority>.+?)\s+hat mit Entscheid vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+der gegen die "
    r"Konkurseröffnung erhobenen Beschwerde aufschiebende Wirkung zuerkannt\]\.?$",
    re.I | re.UNICODE,
)
_FR_AUTHORIZED_AND_CONDITIONAL_CAPITAL_INTRODUCED = re.compile(
    r"^L['’]assemblée générale a introduit une clause statutaire relative à une "
    r"augmentation autorisée du capital par décision du\s+"
    r"(?P<authorized_date>\d{2}\.\d{2}\.\d{4}):\s*pour les détails,\s*voir les "
    r"statuts\.\s*L['’]assemblée générale a introduit une clause statutaire "
    r"relative à une augmentation conditionnelle du capital par décision du\s+"
    r"(?P<conditional_date>\d{2}\.\d{2}\.\d{4}):\s*pour les détails,\s*"
    r"voir les statuts\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_TO_NEW_ASSOCIATE_WITH_ORIGIN = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+détient désormais\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<nominal1>[\d'.]+)\s+par suite "
    r"de cession de\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal2>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<nominal3>[\d'.]+)\s+"
    r"avec signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_NAME_CORRECTED_NO_NOTICE = re.compile(
    r"^L['’]inscription\s+(?:no|n°)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que "
    r"l['’]un des administrateurs se nomme\s+(?P<name>[^()]+?)\s*"
    r"\(et non pas\s+(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_SHAB_CITATION_CORRECTED_REFERENCE = re.compile(
    r"^Mit dem im SHAB-Nr\.\s*(?P<previous_issue>\d+)\s+vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+eingetragenen TR-Eintrag\s+"
    r"(?P<entry>\d+)/(?P<entry_year>\d{4})\s+wurde auf das falsche SHAB-Zitat "
    r"bezug genommen\.\s*Korrekt wäre:\s*SHAB Nr\.\s*(?P<issue>\d+)\s+von\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Publ\.\s*"
    r"(?P<publication_ref>\d+)\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_OPENED_DISSOLUTION = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+über die Gesellschaft mit Wirkung ab dem\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}:\d{2})\s+Uhr,\s*den Konkurs eröffnet,\s*"
    r"womit sie aufgelöst ist\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_AND_TWO_NEW_BOARD_MEMBERS = re.compile(
    r"^Gelöschte Person:\s*(?P<removed_name>[^,.;]+),\s*"
    r"(?P<removed_roles>.+?),\s*(?P<removed_signing>Einzelunterschrift)\.\s*"
    r"Neu eingetragene Personen:\s*(?P<name1>[^,.;]+),\s*"
    r"(?P<nationality1>[^,.;]+),\s*in\s+(?P<place1>[^(),.;]+)\s*"
    r"\((?P<country1>[^)]+)\),\s*(?P<roles1>.+?),\s*"
    r"(?P<signing1>Kollektivunterschrift zu zweien);\s*"
    r"(?P<name2>[^,.;]+),\s*(?P<nationality2>[^,.;]+),\s*in\s+"
    r"(?P<place2>[^(),.;]+)\s*\((?P<country2>[^)]+)\),\s*"
    r"(?P<roles2>.+?),\s*(?P<signing2>Kollektivunterschrift zu zweien)\.?$",
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


def _same_name(left: str, right: str) -> bool:
    return " ".join(left.casefold().split()) == " ".join(right.casefold().split())


def extract_parser210_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 210."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_PARTICIPATION_CAPITAL_COUNT_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.participation_capital_count_corrected.v1", {
                "kind": "participation_capital_structure",
                "action": "publication_corrected",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
                "participation_certificates": _count(match.group("count")),
                "previous_participation_certificates": _count(
                    match.group("previous_count")
                ),
                "participation_kind": "registered",
                "nominal": match.group("nominal"),
                "currency": "CHF",
            },
        )], ""

    match = _DE_BUSINESS_UNIT_ASSET_TRANSFER_CASH.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.business_unit_asset_transfer_cash.v1", {
                "action": "transferred", "source_kind": "stock_corporation",
                "transferred_business_unit": match.group("division").strip(),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital",
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration": match.group("consideration"),
                "consideration_kind": "cash", "currency": "CHF",
            },
        )], ""

    match = _DE_LIQUIDATION_ADDRESS_TYPO.fullmatch(leftover)
    if match:
        street = match.group("street").strip()
        place = match.group("place").strip()
        postal_code = match.group("postal_code")
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "de.text.liquidation_address_typo.v1", {
                "kind": "liquidation_address", "action": "changed",
                "street": street, "postal_code": postal_code, "place": place,
                "address": f"{street}, {postal_code} {place}",
                "source_heading_typo": "Lquidationsadresse",
            },
        )], ""

    match = _FR_FOUR_SHARE_TRANSFERS.fullmatch(leftover)
    if match:
        counts = {key: _count(match.group(key)) for key in (
            "transfer1", "seller1_before", "buyer1_initial", "transfer2",
            "seller1_intermediate", "buyer2_initial", "transfer3",
            "seller2_before", "buyer1_final", "transfer4",
            "seller2_intermediate", "buyer2_final", "seller_final",
        )}
        names_consistent = (
            _same_name(match.group("seller1"), match.group("seller1_final_name"))
            and _same_name(match.group("seller2"), match.group("seller2_final_name"))
            and _same_name(match.group("buyer1"), match.group("buyer1_again"))
        )
        counts_consistent = (
            counts["seller1_before"] - counts["transfer1"]
            == counts["seller1_intermediate"]
            and counts["seller1_intermediate"] - counts["transfer2"]
            == counts["seller_final"]
            and counts["seller2_before"] - counts["transfer3"]
            == counts["seller2_intermediate"]
            and counts["seller2_intermediate"] - counts["transfer4"]
            == counts["seller_final"]
            and counts["buyer1_initial"] + counts["transfer3"]
            == counts["buyer1_final"]
            and counts["buyer2_initial"] + counts["transfer4"]
            == counts["buyer2_final"]
        )
        nominals_consistent = len({
            match.group(f"nominal{index}") for index in range(1, 10)
        }) == 1
        if names_consistent and counts_consistent and nominals_consistent:
            rule_id = "fr.persons.four_share_transfers.v1"
            nominal = match.group("nominal1")
            seller1 = match.group("seller1").strip()
            seller2 = match.group("seller2").strip()
            buyer1 = match.group("buyer1").strip()
            buyer2 = match.group("buyer2").strip()
            common = {"share_nominal": nominal, "currency": "CHF"}
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller1, role="associé", extra={
                        **common, "action": "shares_transferred",
                        "counterparties": [buyer1, buyer2],
                        "shares_before": counts["seller1_before"],
                        "shares_transferred": counts["transfer1"] + counts["transfer2"],
                        "shares_count": counts["seller_final"],
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller2, role="associé", extra={
                        **common, "action": "shares_transferred",
                        "counterparties": [buyer1, buyer2],
                        "shares_before": counts["seller2_before"],
                        "shares_transferred": counts["transfer3"] + counts["transfer4"],
                        "shares_count": counts["seller_final"],
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer1, place=match.group("place1"),
                    role="associé-gérant", signing="Kollektivunterschrift zu zweien",
                    extra={
                        **common, "action": "appointed_and_shares_received",
                        "origin": match.group("origin1").strip(),
                        "counterparties": [seller1, seller2],
                        "shares_received": counts["buyer1_final"],
                        "shares_count": counts["buyer1_final"],
                        "new_associate": True,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer2, place=match.group("place2"),
                    role="associé-gérant", extra={
                        **common, "action": "appointed_and_shares_received",
                        "origin": match.group("origin2").strip(),
                        "counterparties": [seller1, seller2],
                        "shares_received": counts["buyer2_final"],
                        "shares_count": counts["buyer2_final"],
                        "new_associate": True, "without_signature": True,
                        "later_spelling": match.group("buyer2_again").strip(),
                    },
                ),
            ], ""

    match = _FR_ADMINISTRATOR_PRESIDENCY_SUPPLEMENT.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_presidency_supplement.v1",
            match.group("name"), role="administrateur, président du conseil d'administration",
            extra={
                "action": "role_supplemented", "appointed_role": "président",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_TWO_NEW_COMMITTEE_MEMBERS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_new_committee_members.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="membre du comité, secrétaire",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group("origin1").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="membre du comité",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group("place2").strip(),
                },
            ),
        ], ""

    match = _FR_TWO_MANAGERS_AGGREGATE_SHARE_TRANSFER.fullmatch(leftover)
    if match:
        before1 = _count(match.group("before1"))
        before2 = _count(match.group("before2"))
        remaining1 = _count(match.group("remaining1"))
        remaining2 = _count(match.group("remaining2"))
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        if (
            before1 - remaining1 + before2 - remaining2 == transferred
            and transferred == buyer_count
            and len({match.group(f"nominal{index}") for index in range(1, 6)}) == 1
        ):
            rule_id = "fr.persons.two_managers_aggregate_share_transfer.v1"
            buyer = match.group("buyer").strip()
            seller1 = match.group("seller1").strip()
            seller2 = match.group("seller2").strip()
            nominal = match.group("nominal1")
            common = {"share_nominal": nominal, "currency": "CHF"}
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller1, role="associé-gérant", extra={
                        **common, "action": "shares_transferred", "counterparty": buyer,
                        "shares_before": before1,
                        "shares_transferred": before1 - remaining1,
                        "shares_count": remaining1,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller2, role="associé-gérant", extra={
                        **common, "action": "shares_transferred", "counterparty": buyer,
                        "shares_before": before2,
                        "shares_transferred": before2 - remaining2,
                        "shares_count": remaining2,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé-gérant", signing="Einzelunterschrift", extra={
                        **common, "action": "appointed_and_shares_received",
                        "origin": match.group("origin").strip(),
                        "country": match.group("country"),
                        "counterparties": [seller1, seller2],
                        "shares_received": buyer_count, "shares_count": buyer_count,
                        "new_associate": True,
                    },
                ),
            ], ""

    match = _FR_PURPOSE_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "purpose_changed", "fr.text.purpose_corrected.v1", {
                "action": "publication_corrected",
                "purpose": match.group("purpose").strip(),
                "incorrect_published_text": match.group("incorrect").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _IT_MERGER_WITH_ACQUIRER_OWN_SHARES.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "it.text.merger_with_acquirer_own_shares.v1", {
                "kind": "absorption", "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("place").strip(),
                "absorbed_uid": match.group("uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party", "currency": "CHF",
                "acquirer_own_registered_shares": _count(match.group("share_count")),
                "share_nominal": match.group("share_nominal"),
                "capital_increase": False,
                "transferor_shareholders_receive_acquirer_own_shares": True,
            },
        )], ""

    match = _DE_BANKRUPTCY_PETITION_REJECTED_RESIDUE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_petition_rejected_after_payment.v1", {
                "kind": "bankruptcy_petition", "action": "rejected",
                "reason": "subsequent_payment",
                "previous_appeal_suspensive_effect_removed": True,
                "previous_decision_date": _iso_date(
                    match.group("previous_decision_date")
                ),
                "previous_authority": match.group("authority").strip(),
            },
        )], ""

    match = _FR_AUTHORIZED_AND_CONDITIONAL_CAPITAL_INTRODUCED.fullmatch(leftover)
    if match:
        rule_id = "fr.text.authorized_and_conditional_capital_introduced.v1"
        return [
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
                    "kind": "conditional_capital_clause", "action": "introduced",
                    "decision_date": _iso_date(match.group("conditional_date")),
                    "details_in_statutes": True,
                },
            ),
        ], ""

    match = _FR_MANAGER_TRANSFER_TO_NEW_ASSOCIATE_WITH_ORIGIN.fullmatch(leftover)
    if match and (
        _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and len({match.group("nominal1"), match.group("nominal2"), match.group("nominal3")}) == 1
    ):
        rule_id = "fr.persons.manager_transfer_to_new_associate_with_origin.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        remaining = _count(match.group("remaining"))
        transferred = _count(match.group("transferred"))
        common = {"share_nominal": match.group("nominal1"), "currency": "CHF"}
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant", extra={
                    **common, "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": remaining + transferred,
                    "shares_transferred": transferred, "shares_count": remaining,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé", signing="Kollektivunterschrift zu zweien", extra={
                    **common, "action": "appointed_and_shares_received",
                    "origin": match.group("origin").strip(), "counterparty": seller,
                    "shares_received": transferred, "shares_count": transferred,
                    "new_associate": True,
                },
            ),
        ], ""

    match = _FR_ADMINISTRATOR_NAME_CORRECTED_NO_NOTICE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_name_corrected_no_notice.v1",
            match.group("name"), role="administrateur", extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _DE_SHAB_CITATION_CORRECTED_REFERENCE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.shab_citation_corrected_reference.v1", {
                "action": "notice_citation_corrected",
                "entry": match.group("entry"),
                "entry_year": int(match.group("entry_year")),
                "previous_issue": int(match.group("previous_issue")),
                "previous_notice_date": _iso_date(match.group("previous_date")),
                "issue": int(match.group("issue")),
                "notice_date": _iso_date(match.group("notice_date")),
                "publication_ref": match.group("publication_ref"),
            },
        )], ""

    match = _DE_BANKRUPTCY_OPENED_DISSOLUTION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_opened_dissolution.v1", {
                "kind": "bankruptcy", "action": "opened",
                "decision_date": _iso_date(match.group("decision_date")),
                "effective_date": _iso_date(match.group("effective_date")),
                "effective_time": match.group("effective_time"),
                "authority": match.group("authority").strip(),
                "dissolved": True,
            },
        )], ""

    match = _DE_REMOVED_AND_TWO_NEW_BOARD_MEMBERS.fullmatch(leftover)
    if match:
        rule_id = "de.persons.removed_and_two_new_board_members.v1"
        events = [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_removed", rule_id, match.group("removed_name"),
            role=match.group("removed_roles").strip(),
            signing=match.group("removed_signing"), extra={"action": "removed"},
        )]
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role=match.group(f"roles{index}").strip(),
                signing=match.group(f"signing{index}"), extra={
                    "action": "appointed",
                    "nationality": match.group(f"nationality{index}").strip(),
                    "country": match.group(f"country{index}").strip(),
                },
            ))
        return events, ""

    return [], leftover
