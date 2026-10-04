from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_ADMINISTRATOR_DIRECTOR_PROXIES_AND_MANAGEMENT = re.compile(
    r"^L['’]administrateur\s+(?P<administrator>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<previous_role>[^,.;]+),\s*lequel continue à signer collectivement à deux\.\s*"
    r"Signature collective à deux de\s+(?P<director>[^,.;]+),\s*maintenant "
    r"domicilié(?:e)? à\s+(?P<director_place>[^,.;]+),\s*nommé(?:e)? directeur;\s*"
    r"sa procuration est radiée\.\s*Signature collective à deux de\s+"
    r"(?P<signer>[^,.;]+);\s*sa procuration est radiée\.\s*"
    r"(?P<member1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*et\s+(?P<member2>[^,.;]+),\s*de\s+"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"sont membres de la direction\.?$",
    re.I | re.UNICODE,
)
_DE_BUSINESS_UNIT_ASSET_TRANSFER_ZERO_CONSIDERATION = re.compile(
    r'^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+'
    r'(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+den Bereich\s+"'
    r'(?P<business_unit>[^"]+)"\s+mit Aktiven von CHF\s+'
    r"(?P<assets>[\d'.]+)\s+und Passiven von CHF\s+(?P<liabilities>[\d'.]+)\s*"
    r"\(Fremdkapital\)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:?\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_MANAGERS_MIXED_SIGNING = re.compile(
    r"^Gérants:\s*(?P<president>[^,.;]+),\s*maintenant originaire de\s+"
    r"(?P<president_origin>[^,.;]+),\s*nommé(?:e)? président(?:e)?,\s*"
    r"(?P<manager1>[^,.;]+),\s*de et à\s+(?P<manager1_place>[^,.;]+),\s*"
    r"et\s+(?P<manager2>[^,.;]+),\s*de\s+(?P<manager2_origin>[^,.;]+),\s*"
    r"à\s+(?P<manager2_place>[^,.;]+)\.\s*Signature individuelle du président "
    r"ou collective à deux des deux autres gérants\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_DEFICIT_SUBORDINATED_CLAIMS = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di\s+(?P<absorbed_name>.+?),\s*"
    r"in\s+(?P<absorbed_place>[^()]+?)\s*"
    r"\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*secondo "
    r"contratto di fusione del\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"e bilancio al\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta "
    r"attivi per CHF\s+(?P<assets>[\d'.]+),?\s+e passivi verso terzi per CHF\s+"
    r"(?P<liabilities>[\d'.]+),\s*con un['’]eccedenza passiva di CHF\s+"
    r"(?P<deficit>[\d'.]+)\.\s*Conformemente all['’]attestazione di un perito "
    r"revisore abilitato,\s*dei crediti per un ammontare almeno equivalente al "
    r"sovraindebitamento della società assuntrice e della società trasferente "
    r"sono stati postergati\.\s*La fusione avviene senza aumento di capitale e "
    r"senza attribuzione di azioni,\s*poiché un aumento di capitale non è "
    r"necessario alla salvaguardia dei diritti dei soci della società trasferente\.?$",
    re.I | re.UNICODE,
)
_FR_PRESIDENT_SHARE_TRANSFER_TO_MANAGER = re.compile(
    r"^L['’]associé-gérant président\s+(?P<seller>[^,.;]+)\s+détient désormais\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+par "
    r"suite de cession de\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<transfer_nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*désormais "
    r"associé-gérant pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_STATUTES_DATES = re.compile(
    r"^Statuts modifiés les\s+(?P<date1>\d{2}\.\d{2}\.\d{4})\s+et\s+"
    r"(?P<date2>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_REGISTERED_SHARE_CLASSES_TRANSFORMATION = re.compile(
    r"^Transformation des\s+(?P<from_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<from_nominal>[\d'.]+)\s+en\s+(?P<ordinary_count>[\d']+)\s+actions "
    r"ordinaires de CHF\s+(?P<ordinary_nominal>[\d'.]+)\s+et en\s+"
    r"(?P<preferred_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<preferred_nominal>[\d'.]+),\s*privilégiées quant au droit de vote,\s*"
    r"toutes nominatives\.\s*Capital-actions:\s*CHF\s+(?P<total>[\d'.]+),\s*"
    r"entièrement libéré,\s*divisé en\s+(?P=ordinary_count)\s+actions ordinaires "
    r"de CHF\s+(?P=ordinary_nominal)\s+et en\s+(?P=preferred_count)\s+actions de "
    r"CHF\s+(?P=preferred_nominal),\s*privilégiées quant au droit de vote,\s*"
    r"toutes nominatives\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_PROVISION_MODIFIED = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+die mit Beschluss vom\s+"
    r"(?P<original_date>\d{2}\.\d{2}\.\d{4})\s+eingeführte Bestimmung "
    r"betreffend genehmigte Kapitalerhöhung gemäss näherer Umschreibung in den "
    r"Statuten geändert\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_SIGNERS_RESTRICTED_TO_DIRECTOR = re.compile(
    r"^Signature collective à deux,\s*toutefois avec un directeur,\s*est "
    r"conférée à\s+(?P<name1>[^,.;]+),\s*à\s+(?P<place1>[^()]+?)\s*"
    r"\((?P<country1>[^)]+)\),\s*et\s+(?P<name2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^()]+?)\s*\((?P<country2>[^)]+)\),\s*tous deux de\s+"
    r"(?P<origin>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_HEAD_OFFICE_REGISTER_IDENTIFIER = re.compile(
    r"^Etablissement principal inscrit au registre du commerce du canton de\s+"
    r"(?P<register_canton>[^,.;]+)\s+sous le numéro d['’]identification\s*"
    r"\(IDE/UID\)\s*(?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_NAME_CORRECTED_FOUR_LANGUAGES = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que la raison de "
    r"commerce exacte est:\s*(?P<name>[^()]+?)\s*\((?P<german>[^()]+)\)\s*"
    r"\((?P<italian>[^()]+)\)\s*\((?P<english>[^()]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_PROVISIONAL_MORATORIUM_EXTENDED_MONTHS = re.compile(
    r"^Par décision du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+prononcée "
    r"par le\s+(?P<authority>.+?),\s*le sursis concordataire provisoire "
    r"d['’]une durée de\s+(?P<previous_duration>trois)\s+mois est prolongé "
    r"d['’]un mois,\s*soit jusqu['’]au\s+(?P<until>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_TWO_ASSET_TRANSFERS_NO_CONSIDERATION = re.compile(
    r"^Vermögensübertragung:\s*(?P<transferor1>.+?)\s+überträgt gemäss Vertrag "
    r"vom\s+(?P<agreement_date1>\d{2}\.\d{2}\.\d{4})\s+und Inventar per\s+"
    r"(?P<inventory_date1>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets1>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities1>[\d'.]+)\s+auf die\s+(?P<recipient1>.+?),\s*in\s+"
    r"(?P<place1>[^()]+?)\s*\((?P<uid1>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*keine\.\s*\.\s*Vermögensübertragung:\s*"
    r"(?P<transferor2>.+?)\s+überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date2>\d{2}\.\d{2}\.\d{4})\s+und Inventar per\s+"
    r"(?P<inventory_date2>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets2>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities2>[\d'.]+)\s+auf die\s+(?P<recipient2>.+?),\s*in\s+"
    r"(?P<place2>[^()]+?)\s*\((?P<uid2>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*keine\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_CHANGES_PROXIES_REVOKED_NO_SIGNING = re.compile(
    r"^(?P<president>[^,.;]+),\s*président et directeur,\s*et\s+"
    r"(?P<former_vice>[^,.;]+),\s*jusqu['’]ici vice-président,\s*tous deux "
    r"membres du conseil d['’]administration,\s*continuent de signer "
    r"collectivement à deux,\s*mais désormais sauf entre eux\.\s*"
    r"(?P<member1>[^,.;]+),\s*maintenant domicilié(?:e)? à\s+"
    r"(?P<member1_place>[^,.;]+?)(?:\s*\((?P<member1_canton>[A-Z]{2})\))?,\s*"
    r"(?P<member2>[^,.;]+),\s*(?P<member3>[^,.;]+),\s*"
    r"(?P<member4>[^,.;]+),\s*sont membres du conseil d['’]administrationb?\s*;\s*"
    r"leurs procurations sont radiées\.\s*(?P<unsigned1>[^,.;]+),\s*de\s+"
    r"(?P<unsigned1_origin>[^,.;]+),\s*(?P<unsigned2>[^,.;]+),\s*de\s+"
    r"(?P<unsigned2_origin>[^,.;]+),\s*tous deux à\s+"
    r"(?P<unsigned12_place>[^,.;]+),\s*et\s+(?P<unsigned3>[^,.;]+),\s*de\s+"
    r"(?P<unsigned3_origin>[^,.;]+),\s*à\s+(?P<unsigned3_place>[^,.;]+),\s*"
    r"sont membres du conseil d['’]administration;\s*ils n['’]exercent pas la "
    r"signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_PRESIDENCY_CHANGED = re.compile(
    r"^Les membres du conseil de fondation\s+(?P<president>[^,.;]+),\s*nommé(?:e)? "
    r"président(?:e)?\s+et\s+(?P<former_president>[^,.;]+),\s*jusqu['’]ici "
    r"président(?:e)?,\s*continuent à signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_EMPTY_QUALIFIED_FACTS_HEADING = re.compile(
    r"^Nouveaux faits qualifiés:\s*$", re.I | re.UNICODE
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


def extract_parser178_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 178."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_ADMINISTRATOR_DIRECTOR_PROXIES_AND_MANAGEMENT.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administrator_director_proxies_and_management.v1"
        events = [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("administrator"),
                role="administrateur", signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "role_changed", "previous_role": match.group("previous_role"),
                    "signing_continues": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("director"),
                place=match.group("director_place"), role="directeur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_and_signing_changed", "domicile_changed": True,
                    "previous_signing": "procuration", "procuration_revoked": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("signer"),
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "signing_changed", "previous_signing": "procuration",
                    "procuration_revoked": True,
                },
            ),
        ]
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"member{index}"),
                place=match.group(f"place{index}"), role="membre de la direction",
                extra={
                    "action": "appointed",
                    "origin": match.group(f"origin{index}").strip(),
                },
            ))
        return events, ""

    match = _DE_BUSINESS_UNIT_ASSET_TRANSFER_ZERO_CONSIDERATION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.business_unit_asset_transfer_zero_consideration.v1", {
                "source_kind": "company", "business_unit": match.group("business_unit"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"), "gratuitous": True,
            },
        )], ""

    match = _FR_THREE_MANAGERS_MIXED_SIGNING.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.three_managers_mixed_signing.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="gérant-président", signing="Einzelunterschrift", extra={
                    "action": "appointed_president_and_origin_changed",
                    "origin": match.group("president_origin").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("manager1"),
                place=match.group("manager1_place"), role="gérant",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group("manager1_place").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("manager2"),
                place=match.group("manager2_place"), role="gérant",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group("manager2_origin").strip(),
                },
            ),
        ], ""

    match = _IT_MERGER_DEFICIT_SUBORDINATED_CLAIMS.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "it.text.merger_deficit_subordinated_claims.v1", {
                "kind": "absorption", "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "deficit": match.group("deficit"), "currency": "CHF",
                "liabilities_kind": "third_party_liabilities",
                "deficit_coverage": "subordinated_claims",
                "deficit_coverage_confirmed_by_auditor": True,
                "acquirer_and_transferor_claims_subordinated": True,
                "capital_increase": False, "share_allocation": False,
                "shareholder_rights_preserved": True,
            },
        )], ""

    match = _FR_PRESIDENT_SHARE_TRANSFER_TO_MANAGER.fullmatch(leftover)
    if match and (
        match.group("nominal") == match.group("transfer_nominal")
        == match.group("buyer_nominal")
        and _count(match.group("transferred")) == _count(match.group("buyer_count"))
    ):
        rule_id = "fr.persons.president_share_transfer_to_manager.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant président",
                extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, role="associé-gérant", extra={
                    "action": "appointed_and_shares_received", "counterparty": seller,
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
        ], ""

    match = _FR_TWO_STATUTES_DATES.fullmatch(leftover)
    if match:
        rule_id = "fr.text.two_statutes_change_dates.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id, {
                    "date": _iso_date(match.group(f"date{index}")),
                    "sequence": index,
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_REGISTERED_SHARE_CLASSES_TRANSFORMATION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.registered_share_classes_transformation.v1", {
                "kind": "share_classes_transformed", "currency": "CHF",
                "from_count": _count(match.group("from_count")),
                "from_nominal": match.group("from_nominal"),
                "total": match.group("total"), "fully_paid": True, "registered": True,
                "classes": [
                    {
                        "count": _count(match.group("ordinary_count")),
                        "nominal": match.group("ordinary_nominal"), "class": "ordinary",
                    },
                    {
                        "count": _count(match.group("preferred_count")),
                        "nominal": match.group("preferred_nominal"),
                        "class": "voting_preference",
                        "rights": "privilégiées quant au droit de vote",
                    },
                ],
            },
        )], ""

    match = _DE_AUTHORIZED_CAPITAL_PROVISION_MODIFIED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_provision_modified.v1", {
                "kind": "authorized_capital_clause", "action": "modified",
                "decision_date": _iso_date(match.group("decision_date")),
                "original_decision_date": _iso_date(match.group("original_date")),
                "details_in_statutes": True,
            },
        )], ""

    match = _FR_TWO_SIGNERS_RESTRICTED_TO_DIRECTOR.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_signers_restricted_to_director.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "signing_granted", "required_with": "directeur",
                    "origin": match.group("origin").strip(),
                    "country": match.group(f"country{index}").strip(),
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_HEAD_OFFICE_REGISTER_IDENTIFIER.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "fr.text.head_office_register_identifier.v1", {
                "scope": "head_office", "action": "identifier_recorded",
                "head_office_uid": match.group("uid"),
                "register_canton": match.group("register_canton").strip(),
            },
        )], ""

    match = _FR_COMPANY_NAME_CORRECTED_FOUR_LANGUAGES.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_name_changed", "fr.text.company_name_corrected_four_languages.v1", {
                "action": "corrected", "name": match.group("name").strip(),
                "translations": {
                    "de": match.group("german").strip(),
                    "it": match.group("italian").strip(),
                    "en": match.group("english").strip(),
                },
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_PROVISIONAL_MORATORIUM_EXTENDED_MONTHS.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.provisional_moratorium_extended_one_month.v1", {
                "kind": "composition_moratorium_extended", "action": "extended",
                "moratorium_type": "provisional",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "previous_duration_months": 3, "extension_months": 1,
                "until": _iso_date(match.group("until")),
            },
        )], ""

    match = _DE_TWO_ASSET_TRANSFERS_NO_CONSIDERATION.fullmatch(leftover)
    if match and match.group("transferor1") == match.group("transferor2"):
        rule_id = "de.text.two_asset_transfers_no_consideration.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", rule_id, {
                    "transferor": match.group(f"transferor{index}").strip(),
                    "agreement_date": _iso_date(match.group(f"agreement_date{index}")),
                    "inventory_date": _iso_date(match.group(f"inventory_date{index}")),
                    "assets": match.group(f"assets{index}"),
                    "liabilities": match.group(f"liabilities{index}"),
                    "liabilities_kind": "third_party_capital", "currency": "CHF",
                    "recipient": match.group(f"recipient{index}").strip(),
                    "recipient_place": match.group(f"place{index}").strip(),
                    "recipient_uid": match.group(f"uid{index}"),
                    "consideration": "keine", "gratuitous": True,
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_BOARD_CHANGES_PROXIES_REVOKED_NO_SIGNING.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.board_changes_proxies_revoked_no_signing.v1"
        events = [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président et directeur", signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "signing_restriction_changed", "signing_continues": True,
                    "excluded_co_signers": [match.group("former_vice").strip()],
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("former_vice"),
                role="membre du conseil d'administration",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "role_and_signing_restriction_changed",
                    "previous_role": "vice-président", "signing_continues": True,
                    "excluded_co_signers": [match.group("president").strip()],
                },
            ),
        ]
        for index in (1, 2, 3, 4):
            extra = {
                "action": "appointed_and_procuration_revoked",
                "previous_signing": "procuration", "procuration_revoked": True,
            }
            place = None
            if index == 1:
                place = match.group("member1_place")
                extra["domicile_changed"] = True
                if match.group("member1_canton"):
                    extra["place_canton"] = match.group("member1_canton")
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"member{index}"),
                place=place, role="membre du conseil d'administration", extra=extra,
            ))
        for index in (1, 2, 3):
            place = (
                match.group("unsigned12_place") if index in (1, 2)
                else match.group("unsigned3_place")
            )
            origin = match.group(f"unsigned{index}_origin")
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"unsigned{index}"),
                place=place, role="membre du conseil d'administration", extra={
                    "action": "appointed", "origin": origin.strip(),
                    "without_signature": True,
                },
            ))
        return events, ""

    match = _FR_FOUNDATION_PRESIDENCY_CHANGED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.foundation_presidency_changed.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président du conseil de fondation",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_president", "signing_continues": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("former_president"),
                role="membre du conseil de fondation",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "presidency_ended", "previous_role": "président",
                    "signing_continues": True,
                },
            ),
        ], ""

    # This label remains after its following qualified fact was already parsed by
    # text_extras. Consuming the exact, content-free heading does not invent an event.
    if _FR_EMPTY_QUALIFIED_FACTS_HEADING.fullmatch(leftover):
        return [], ""

    return [], text
