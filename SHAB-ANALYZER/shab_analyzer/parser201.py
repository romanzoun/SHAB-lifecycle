from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_FR_SIGNING_CONTINUES_WITH_NAMED_PERSON = re.compile(
    r"^(?P<name>[^,.;]+)\s+continue à signer collectivement à deux,\s*"
    r"toutefois désormais avec\s+(?P<with_person>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_CAPITAL_SUPPLEMENT_QUOTED = re.compile(
    r"^L['’]inscription\s+N[°º]\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})"
    r"(?:\s*\(FOSC du\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"p\.\s*(?P<notice_ref>[\d/]+)\))?\s+est complétée comme suit\s*:\s*"
    r"[\"“]Capital\s*:\s*CHF\s+(?P<capital>[\d'.]+)[\"”]\.?$",
    re.I | re.UNICODE,
)
_DE_LEGAL_FORM_SUFFIX_CORRECTED = re.compile(
    r'^Berichtigung des Rechtsformzusatzes,\s*da irrtümlich\s*["“]'
    r'(?P<previous>[^"”]+)["”]\s+statt\s*["“](?P<correct>[^"”]+)["”]\s+'
    r"erfasst und nicht bemerkt wurde,\s*da\s+(?P<reason>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_CAPITAL_SUPPLEMENT_CORRECTED = re.compile(
    r"^L['’]inscription\s+N[°º]\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée comme suit\s*:\s*"
    r"Capital-actions\s*:\s*CHF\s+(?P<total>[\d'.]+),\s*entièrement libéré,\s*"
    r"divisé en\s+(?P<count>[\d']+)\s+actions de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*(?P<share_kind>nominatives),\s*"
    r"(?P<restriction>liées selon statuts)\s*"
    r"\(et non pas seulement\s+(?P<previous>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_GIVEN_NAME_CORRECTED_WITH_SURNAME = re.compile(
    r"^Rectificatif\s*:\s*l['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le prénom "
    r"exact de l['’](?P<role>[^,.;]+?)\s+(?P<title>M\.)\s*"
    r"(?P<surname>[^,.;]+?)\s+est\s+(?P<given>[^()]+?)\s*"
    r"\(et non\s+(?P<previous_given>[^,;)]+),\s*comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_PROXY_REVOKED_APPOINTED_DIRECTOR_FEMININE = re.compile(
    r"^(?P<name>[^,.;]+),\s*dont la procuration est éteinte,\s*"
    r"est nommée\s+(?P<role>directrice)\s+et engage désormais la société par "
    r"sa signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_REOPENED_WITH_EFFECTIVE_TIME = re.compile(
    r"^Gemäss Verfügung des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wird die Verfügung vom\s+"
    r"(?P<suspension_date>\d{2}\.\d{2}\.\d{4}),\s*mit der das "
    r"Konkursverfahren mangels Aktiven eingestellt worden ist,\s*widerrufen "
    r"und das Konkursverfahren gemäss Verfügung vom\s+"
    r"(?P<reopening_date>\d{2}\.\d{2}\.\d{4}),\s*mit Wirkung ab dem\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}[.:]\d{2})\s+Uhr,\s*wiedereröffnet\.\s*"
    r"\[bisher:\s*(?P<previous>.+?)\]\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_AND_EXECUTIVE_MEMBERS = re.compile(
    r"^Nouveaux membres du conseil de fondation sans signature\s*:\s*"
    r"(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;()]+)\s*"
    r"\((?P<country1>[^)]+)\),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;()]+)\s*"
    r"\((?P<country2>[^)]+)\)\.\s*"
    r"Nouveau membre du comité exécutif\s+avec\s+"
    r"(?P<signing>signature collective à deux)\s*:\s*"
    r"(?P<name3>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_ASSOCIATE_TRANSFERS_WITHOUT_SIGNING = re.compile(
    r"^(?P<seller>[^,.;]+)\s+a cédé\s+(?P<count1>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal1>[\d'.]+)\s+à\s+(?P<buyer1>[^,.;]+),\s*de\s+"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*nouvel associé "
    r"pour\s+(?P<buyer_count1>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal1>[\d'.]+),\s*"
    r"(?P<count2>[\d']+)\s+parts de CHF\s+(?P<nominal2>[\d'.]+)\s+à\s+"
    r"(?P<buyer2>[^,.;]+),\s*de\s+(?P<origin2>.+?),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*nouvel associé pour\s+"
    r"(?P<buyer_count2>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal2>[\d'.]+),\s*et\s+"
    r"(?P<count3>[\d']+)\s+parts de CHF\s+(?P<nominal3>[\d'.]+)\s+à\s+"
    r"(?P<buyer3>[^,.;]+),\s*d['’](?P<origin3>[^,.;]+),\s*à\s+"
    r"(?P<place3>[^,.;]+),\s*(?P<country3>[A-Z]{2,3}),\s*nouvel associé "
    r"pour\s+(?P<buyer_count3>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal3>[\d'.]+);\s*ils n['’]exercent pas la signature "
    r"sociale;\s*par conséquent\s+(?P=seller)\s+est maintenant associé pour\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_REINSTATED_WITH_LIQUIDATOR_AND_ADDRESS = re.compile(
    r"^Die am\s+(?P<deletion_date>\d{2}\.\d{2}\.\d{4})\s+gelöschte "
    r"Gesellschaft wird auf Grund des Entscheids des\s+(?P<authority>.+?)\s+"
    r"vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+zum Zwecke der "
    r"Liquidation wieder in das Handelsregister eingetragen und besteht "
    r"entsprechend den früheren Eintragungen weiter\.\s*\[Liquidatorin\s*:\s*"
    r"(?P<surname>[^,;\]]+),\s*(?P<given>[^,;\]]+),\s*von\s+"
    r"(?P<origin>[^,;\]]+),\s*in\s+(?P<place>.+?)\.\s*"
    r"Liquidationsadresse\s*:\s*(?P<address>[^\]]+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_NAME_LIQUIDATION_CORRECTED = re.compile(
    r"^Rectification de l['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\)\s*:\s*Raison sociale correcte\s*:\s*"
    r"(?P<name>.+?)\s*\(et non pas\s+(?P<previous_name>.+?)\)\.?$",
    re.I | re.UNICODE,
)
_DE_BUSINESS_UNIT_ASSET_TRANSFER_LONG_TERM_LOAN = re.compile(
    r'^Vermögensübertragung:\s*Die Aktiengesellschaft überträgt gemäss '
    r'Vermögensübertragungsvertrag vom\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+'
    r'den Betriebsteil\s+["“](?P<business_unit>[^"”]+)["”]\s+mit Aktiven von '
    r"CHF\s+(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+[\"“](?P<recipient>[^\"”]+)[\"”]\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+(?P<place>[^.]+)\.\s*"
    r"Gegenleistung\s*:\s*Ein langfristiges Darlehen über CHF\s+"
    r"(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_TO_NEW_MANAGER_PRESIDENT = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé-gérant "
    r"et président\s+avec\s+(?P<signing>signature individuelle)\.\s*"
    r"(?P=seller)\s+reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_BOARD_MEMBERS_COLLECTIVE = re.compile(
    r"^(?P<name1>[^,.;]+),\s*d['’](?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+),\s*de\s+"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*sont membres du "
    r"conseil et signent collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_MANAGER = re.compile(
    r"^Nouvelle gérante\s+avec\s+(?P<signing>signature individuelle)\s*:\s*"
    r"(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _money(raw: str) -> Decimal:
    return Decimal(raw.rstrip(".").replace("'", ""))


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


def extract_parser201_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 201."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_SIGNING_CONTINUES_WITH_NAMED_PERSON.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed",
            "fr.persons.signing_continues_with_named_person.v1",
            match.group("name"), signing="Kollektivunterschrift zu zweien", extra={
                "action": "restriction_changed", "signing_continues": True,
                "with": match.group("with_person").strip(),
            },
        )], ""

    match = _FR_CAPITAL_SUPPLEMENT_QUOTED.fullmatch(leftover)
    if match:
        payload = {
            "kind": "share_capital", "action": "publication_supplemented",
            "currency": "CHF", "total": match.group("capital"),
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
        }
        if match.group("notice_date"):
            payload.update({
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            })
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.capital_supplement_quoted.v1", payload,
        )], ""

    match = _DE_LEGAL_FORM_SUFFIX_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "legal_form_changed", "de.text.legal_form_suffix_corrected.v1", {
                "kind": "legal_form_suffix", "action": "publication_corrected",
                "from": match.group("previous"), "to": match.group("correct"),
                "reason": match.group("reason").strip(),
            },
        )], ""

    match = _FR_SHARE_CAPITAL_SUPPLEMENT_CORRECTED.fullmatch(leftover)
    if match and (
        _money(match.group("total"))
        == _count(match.group("count")) * _money(match.group("nominal"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.share_capital_supplement_corrected.v1", {
                "kind": "share_structure", "action": "publication_supplemented",
                "currency": "CHF", "total": match.group("total"),
                "fully_paid": True, "shares_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"),
                "share_kind": match.group("share_kind").lower(),
                "transfer_restricted": True,
                "previous_incomplete_description": match.group("previous").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_GIVEN_NAME_CORRECTED_WITH_SURNAME.fullmatch(leftover)
    if match:
        surname = match.group("surname").strip()
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.given_name_corrected_with_surname.v1",
            f"{surname} {match.group('given').strip()}", role=match.group("role"), extra={
                "action": "name_corrected",
                "previous_name": f"{surname} {match.group('previous_given').strip()}",
                "title": match.group("title"), "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_PROXY_REVOKED_APPOINTED_DIRECTOR_FEMININE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.proxy_revoked_appointed_director_feminine.v1",
            match.group("name"), role=match.group("role"),
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "appointed_and_signing_changed",
                "previous_signing": "procuration", "previous_signing_revoked": True,
            },
        )], ""

    match = _DE_BANKRUPTCY_REOPENED_WITH_EFFECTIVE_TIME.fullmatch(leftover)
    if match and match.group("decision_date") == match.group("reopening_date"):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_reopened_with_effective_time.v1", {
                "kind": "bankruptcy", "action": "reopened",
                "decision_date": _iso_date(match.group("decision_date")),
                "effective_date": _iso_date(match.group("effective_date")),
                "effective_time": match.group("effective_time").replace(".", ":"),
                "authority": match.group("authority").strip(),
                "previous_action": "suspended_for_lack_of_assets",
                "previous_decision_date": _iso_date(match.group("suspension_date")),
                "previous": match.group("previous").strip(),
            },
        )], ""

    match = _FR_FOUNDATION_AND_EXECUTIVE_MEMBERS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.foundation_and_executive_members.v1"
        events = []
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role="membre du conseil de fondation", extra={
                    "action": "appointed", "origin": match.group(f"origin{index}").strip(),
                    "country": match.group(f"country{index}").strip(),
                    "without_signature": True,
                },
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("name3"),
            place=match.group("place3"), role="membre du comité exécutif",
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "appointed", "origin": match.group("origin3").strip(),
            },
        ))
        return events, ""

    match = _FR_THREE_ASSOCIATE_TRANSFERS_WITHOUT_SIGNING.fullmatch(leftover)
    if match:
        counts = [_count(match.group(f"count{index}")) for index in (1, 2, 3)]
        buyer_counts = [
            _count(match.group(f"buyer_count{index}")) for index in (1, 2, 3)
        ]
        nominals = {
            *(match.group(f"nominal{index}") for index in (1, 2, 3)),
            *(match.group(f"buyer_nominal{index}") for index in (1, 2, 3)),
            match.group("seller_nominal"),
        }
        if counts == buyer_counts and len(nominals) == 1:
            rule_id = "fr.persons.three_associate_transfers_without_signing.v1"
            seller = match.group("seller").strip()
            buyers = [match.group(f"buyer{index}").strip() for index in (1, 2, 3)]
            common = {"share_nominal": match.group("seller_nominal"), "currency": "CHF"}
            events = [_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé", extra={
                    "action": "shares_transferred", "counterparties": buyers,
                    "shares_before": _count(match.group("seller_count")) + sum(counts),
                    "shares_transferred": sum(counts),
                    "shares_count": _count(match.group("seller_count")), **common,
                },
            )]
            for index in (1, 2, 3):
                extra = {
                    "action": "appointed_and_shares_received", "counterparty": seller,
                    "shares_received": counts[index - 1],
                    "shares_count": buyer_counts[index - 1],
                    "origin": match.group(f"origin{index}").strip(),
                    "without_signature": True, **common,
                }
                if index == 3:
                    extra["country"] = match.group("country3")
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"buyer{index}"),
                    place=match.group(f"place{index}"), role="associé", extra=extra,
                ))
            return events, ""

    match = _DE_COMPANY_REINSTATED_WITH_LIQUIDATOR_AND_ADDRESS.fullmatch(leftover)
    if match:
        rule_id = "de.text.company_reinstated_with_liquidator_and_address.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "registration_reinstated", "action": "reinstated",
                    "reason": "liquidation", "liquidation_only": True,
                    "company_continues": True,
                    "deletion_date": _iso_date(match.group("deletion_date")),
                    "decision_date": _iso_date(match.group("decision_date")),
                    "authority": match.group("authority").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id,
                f"{match.group('surname').strip()}, {match.group('given').strip()}",
                place=match.group("place"), role="Liquidatorin", extra={
                    "action": "recorded", "origin": match.group("origin").strip(),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", rule_id, {
                    "kind": "liquidation_address", "action": "recorded",
                    "to": match.group("address").strip(),
                },
            ),
        ], ""

    match = _FR_COMPANY_NAME_LIQUIDATION_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_name_changed", "fr.text.company_name_liquidation_corrected.v1", {
                "action": "publication_corrected", "from": match.group("previous_name").strip(),
                "to": match.group("name").strip(), "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        )], ""

    transfer_parts = [
        part.strip()
        for part in re.split(r"(?=Vermögensübertragung:)", leftover)
        if part.strip()
    ]
    if len(transfer_parts) == 2:
        transfer_matches = [
            _DE_BUSINESS_UNIT_ASSET_TRANSFER_LONG_TERM_LOAN.fullmatch(part)
            for part in transfer_parts
        ]
        if all(transfer_matches) and all(
            _money(match.group("assets")) - _money(match.group("liabilities"))
            == _money(match.group("consideration"))
            for match in transfer_matches
            if match is not None
        ):
            rule_id = "de.text.two_business_unit_asset_transfers_long_term_loans.v1"
            return [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "assets_transferred", rule_id, {
                        "source_kind": "corporation", "scope": "business_unit",
                        "business_unit": match.group("business_unit"),
                        "agreement_date": _iso_date(match.group("agreement_date")),
                        "assets": match.group("assets"),
                        "liabilities": match.group("liabilities"),
                        "liabilities_kind": "third_party_capital", "currency": "CHF",
                        "recipient": match.group("recipient"),
                        "recipient_uid": match.group("uid"),
                        "recipient_place": match.group("place").strip(),
                        "consideration_kind": "long_term_loan",
                        "consideration_amount": match.group("consideration").rstrip("."),
                    },
                )
                for match in transfer_matches
                if match is not None
            ], ""

    match = _FR_MANAGER_TRANSFER_TO_NEW_MANAGER_PRESIDENT.fullmatch(leftover)
    if match and (
        match.group("nominal") == match.group("remaining_nominal")
        and _count(match.group("before"))
        == _count(match.group("transferred")) + _count(match.group("remaining"))
    ):
        rule_id = "fr.persons.manager_transfer_to_new_manager_president.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant", extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")), **common,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé-gérant et président", signing="Einzelunterschrift", extra={
                    "action": "appointed_and_shares_received", "counterparty": seller,
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("transferred")),
                    "origin": match.group("origin").strip(), **common,
                },
            ),
        ], ""

    match = _FR_TWO_BOARD_MEMBERS_COLLECTIVE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_board_members_collective.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="membre du conseil",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group(f"origin{index}").strip(),
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_NEW_MANAGER.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.new_manager.v1", match.group("name"),
            place=match.group("place"), role="gérante",
            signing="Einzelunterschrift", extra={
                "action": "appointed", "origin": match.group("origin").strip(),
            },
        )], ""

    return [], leftover
