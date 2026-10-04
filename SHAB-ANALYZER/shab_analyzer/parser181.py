from __future__ import annotations

import re
from decimal import Decimal

from .keys import person_key
from .models import Event


_FR_MANAGER_SHARE_TRANSFER_TO_UNSIGNED_ASSOCIATE = re.compile(
    r"^Jusqu['’]ici titulaire de (?P<before>[\d']+) parts de CHF "
    r"(?P<nominal>[\d'.]+),\s*l['’]associé-gérant (?P<seller>[^,.;]+) "
    r"détient (?P<remaining>[\d']+) parts de CHF "
    r"(?P<remaining_nominal>[\d'.]+) par suite de cession de "
    r"(?P<transferred>[\d']+) parts à (?P<buyer>[^,.;]+),\s*de "
    r"(?P<origin>[^,.;]+),\s*à (?P<place>[^,.;]+),\s*(?P<country>[A-Z]),\s*"
    r"nouvelle associée pour (?P<buyer_count>[\d']+) parts de CHF "
    r"(?P<buyer_nominal>[\d'.]+),\s*laquelle n['’]exerce pas la signature "
    r"sociale\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDATION_ASSET_TRANSFER_WITH_APPROVAL = re.compile(
    r"^Vermögensübertragung:\s*Die Stiftung überträgt gemäss Vertrag vom "
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4}) und Verfügung der "
    r"Aufsichtsbehörde vom (?P<approval_date>\d{2}\.\d{2}\.\d{4}) Aktiven "
    r"von CHF (?P<assets>[\d'.]+) und Fremdkapital von CHF "
    r"(?P<liabilities>[\d'.]+) auf die (?P<recipient>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in (?P<place>[^.]+)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>keine)\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_DURATION_CHANGED = re.compile(
    r"^Dauer der Gesellschaft neu:\s*Bis (?P<until_year>\d{4}) mit "
    r"unbeschränkter Verlängerungsmöglichkeit um jeweils höchstens "
    r"(?P<extension_years>\w+) Jahre\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_PROXIES_APPOINTED_ADMINISTRATORS = re.compile(
    r"^(?P<name1>[^,.;]+) et (?P<name2>[^,.;]+),\s*dont la procuration est "
    r"éteinte,\s*sont élus administrateurs et engagent désormais la société "
    r"par leur signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_CLASS_SHARE_SPLIT = re.compile(
    r"^Division de (?P<from_count1>[\d']+) actions de CHF "
    r"(?P<from_nominal1>[\d'.]+),\s*nominatives,\s*en "
    r"(?P<to_count1>[\d']+) actions de CHF (?P<to_nominal1>[\d'.]+),\s*"
    r"désormais privilégiées quant au droit de vote et au dividende,\s*et de "
    r"(?P<from_count2>[\d']+) actions de CHF (?P<from_nominal2>[\d'.]+),\s*"
    r"nominatives,\s*en (?P<to_count2>[\d']+) actions ordinaires de CHF "
    r"(?P<to_nominal2>[\d'.]+)\.\s*Capital-actions:\s*CHF "
    r"(?P<total>[\d'.]+),\s*entièrement libéré,\s*divisé en "
    r"(?P<capital_count1>[\d']+) actions de CHF "
    r"(?P<capital_nominal1>[\d'.]+),\s*privilégiées quant au droit de vote et "
    r"au dividende,\s*et (?P<capital_count2>[\d']+) actions ordinaires de CHF "
    r"(?P<capital_nominal2>[\d'.]+),\s*toutes nominatives\.?$",
    re.I | re.UNICODE,
)
_DE_MERGER_TWO_AGREEMENT_DATES_SAME_SHAREHOLDER = re.compile(
    r"^Fusion:\s*Übernahme der Aktiven und Passiven der "
    r"(?P<absorbed_name>.+?),\s*in (?P<absorbed_place>[^()]+?)\s*"
    r"\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\s*\),\s*gemäss "
    r"Fusionsvertrag vom (?P<agreement_date1>\d{2}\.\d{2}\.) bzw\. "
    r"(?P<agreement_date2>\d{2}\.\d{2}\.\d{4}) und Bilanz per "
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\.\s*Aktiven von CHF "
    r"(?P<assets>[\d'.]+) und Passiven \(Fremdkapital\) von CHF "
    r"(?P<liabilities>[\d'.]+) gehen auf die übernehmende Gesellschaft über\.\s*"
    r"Da dieselbe Aktionärin sämtliche Aktien der an der Fusion beteiligten "
    r"Gesellschaften hält,\s*findet weder eine Kapitalerhöhung noch eine "
    r"Aktienzuteilung statt\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_ADJUSTED_WITH_FOUNDING_HISTORY = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom "
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}) Anpassung der genehmigten "
    r"Kapitalerhöhung gemäss näherer Umschreibung in den Statuten beschlossen\.\s*"
    r"\[bisher:\s*Die Gesellschaft hat bei der Gründung vom "
    r"(?P<founding_date>\d{2}\.\d{2}\.\d{4}) eine genehmigte Kapitalerhöhung "
    r"gemäss näherer Umschreibung in den Statuten beschlossen\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_NAME_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+) du "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) \(FOSC du "
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\) est rectifiée en ce sens que le nom exact du "
    r"membre du conseil de fondation (?P<previous_name>[^,.;]+) est "
    r"(?P<name>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_CONDITIONAL_CAPITAL_CREATED = re.compile(
    r"^Die Generalversammlung hat mit Beschluss vom "
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}) ein bedingtes Aktienkapital "
    r"geschaffen gemäss näherer Umschreibung in den Statuten\.?$",
    re.I | re.UNICODE,
)
_FR_CAPITAL_AND_THREE_CLAUSES_MODIFIED = re.compile(
    r"^Capital-actions nouveau:\s*CHF (?P<total>[\d'.]+),\s*libéré à "
    r"concurrence de CHF (?P<paid>[\d'.]+),\s*désormais divisé en "
    r"(?P<count>[\d']+) actions de CHF (?P<nominal>[\d'.]+) "
    r"\(jusqu['’]ici:\s*(?P<previous_count>[\d']+) actions de CHF "
    r"(?P<previous_nominal>[\d'.]+)\),\s*nominatives et "
    r"(?P<restriction>liées selon statuts)\.\s*"
    r"(?P<details>Les clauses statutaires concernant les apports en nature .+"
    r"Pour les détails,\s*voir les statuts)\.?$",
    re.I | re.UNICODE,
)
_DE_TWO_NEW_PERSONS_INDIVIDUAL_SIGNING = re.compile(
    r"^Neu eingetragene Personen:\s*(?P<name1>[^,;]+),\s*von und in "
    r"(?P<place1>[^,;]+),\s*Einzelunterschrift;\s*(?P<name2>[^,;]+),\s*"
    r"(?P<nationality2>[^,;]+?) Staatsangehöriger,\s*in (?P<place2>[^,;]+),\s*"
    r"Einzelunterschrift\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_APPEAL_SUSPENDED_DISSOLVED_COMPANY = re.compile(
    r"^Mit Verfügung des (?P<authority>.+?) vom "
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}) ist der Beschwerde gegen das "
    r"Urteil des (?P<bankruptcy_court>.+?) vom "
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4}) betreffend Konkurseröffnung "
    r"aufschiebende Wirkung zuerkannt worden\.\s*Demnach wird die Eintragung "
    r"betreffend Eröffnung des Konkurses im Handelsregister gestrichen\.\s*"
    r"\[bisher:\s*Mit Urteil vom (?P=bankruptcy_date) hat der "
    r"(?P<previous_bankruptcy_court>.+?) mit Wirkung ab dem "
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}[.:]\d{2}) Uhr,\s*über die bereits aufgelöste "
    r"Gesellschaft den Konkurs eröffnet\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_LATE_FULL_PAYMENT_AFTER_FOUNDER_DEFAULT = re.compile(
    r"^Der Gründer hat,\s*wie sich nachträglich herausgestellt hat,\s*seine "
    r"anlässlich der Gründung vom (?P<founding_date>\d{2}\.\d{2}\.\d{4}) "
    r"bedingungslos versprochene Leistung der Einlagen auf die von ihm "
    r"gezeichneten Aktien nicht erfüllt\.\s*Bei der Nachliberierung vom "
    r"(?P<payment_date>\d{2}\.\d{2}\.\d{4}) wurden alle "
    r"(?P<count>[\d']+) bisher nicht liberierten (?P<share_kind>Inhaberaktien) "
    r"zu CHF (?P<nominal>[\d'.]+) statutengemäss voll liberiert\.?$",
    re.I | re.UNICODE,
)
_DE_OWNER_BANKRUPTCY_APPEAL_SUSPENDED_FEMININE_HISTORY = re.compile(
    r"^Mit Verfügung vom (?P<decision_date>\d{2}\.\d{2}\.\d{4}) hat "
    r"(?P<authority>.+?) der Beschwerde des Inhabers gegen das erstinstanzliche "
    r"Konkurserkenntnis die aufschiebende Wirkung erteilt\.\s*"
    r"\[gestrichen:\s*Mit Entscheid des (?P<previous_authority>.+?) vom "
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4}) wurde über die Inhaberin "
    r"dieses Einzelunternehmens mit Wirkung ab dem "
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}:\d{2}) Uhr,\s*der Konkurs eröffnet\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_CONTINUING_SIGNING_AND_UNSIGNED_MEMBER = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé président,\s*"
    r"(?P<secretary>[^,.;]+),\s*nommée secrétaire,\s*lesquels continuent à "
    r"signer individuellement et (?P<member>[^,.;]+),\s*de "
    r"(?P<origin>[^,.;]+),\s*à (?P<place>[^,.;]+),\s*sans signature sociale\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_BALANCE_DATE_CORRECTED_FREE_EQUITY = re.compile(
    r"^\[data corretta del bilancio di fusione\]\s*Fusione:\s*ripresa di "
    r"attivi e passivi di (?P<absorbed_name>.+?),\s*in "
    r"(?P<absorbed_place>[^()]+?)\s*\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"secondo contratto di fusione del "
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4}) e bilancio al "
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta attivi per CHF "
    r"(?P<assets>[\d'.]+),\s*e passivi verso terzi per CHF "
    r"(?P<liabilities>[\d'.]+)\.\s*Conformemente all['’]attestazione di un "
    r"perito revisore abilitato,\s*la società assuntrice dispone di fondi propri "
    r"liberamente disponibili equivalenti almeno all['’]ammontare dello "
    r"scoperto\.\s*La società assuntrice detiene tutte le azioni della società "
    r"trasferente,\s*per cui la fusione avviene senza aumento di capitale e "
    r"senza attribuzione di azioni\.\s*\[non:\s*data del bilancio "
    r"(?P<previous_balance_date>\d{2}\.\d{2}\.\d{4})\]\.?$",
    re.I | re.UNICODE,
)


_GERMAN_NUMBERS = {
    "ein": 1,
    "eine": 1,
    "einen": 1,
    "zwei": 2,
    "drei": 3,
    "vier": 4,
    "fünf": 5,
}


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


def extract_parser181_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 181."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_MANAGER_SHARE_TRANSFER_TO_UNSIGNED_ASSOCIATE.fullmatch(leftover)
    if match and (
        _count(match.group("before"))
        == _count(match.group("remaining")) + _count(match.group("transferred"))
        and _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and len({
            match.group("nominal"),
            match.group("remaining_nominal"),
            match.group("buyer_nominal"),
        }) == 1
    ):
        rule_id = "fr.persons.manager_share_transfer_to_unsigned_associate.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant",
                extra={
                    **common, "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée", extra={
                    **common, "action": "shares_received", "counterparty": seller,
                    "origin": match.group("origin").strip(),
                    "country": match.group("country"),
                    "shares_received": _count(match.group("buyer_count")),
                    "shares_count": _count(match.group("buyer_count")),
                    "new_associate": True, "without_signature": True,
                },
            ),
        ], ""

    match = _DE_FOUNDATION_ASSET_TRANSFER_WITH_APPROVAL.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.foundation_asset_transfer_with_approval.v1", {
                "source_kind": "foundation",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "approval_date": _iso_date(match.group("approval_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration_kind": "none", "gratuitous": True,
            },
        )], ""

    match = _DE_COMPANY_DURATION_CHANGED.fullmatch(leftover)
    if match:
        extension_raw = match.group("extension_years").lower()
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.company_duration_changed.v1", {
                "kind": "company_duration", "action": "changed",
                "until_year": int(match.group("until_year")),
                "extension_unlimited": True,
                "maximum_extension_years": _GERMAN_NUMBERS.get(extension_raw),
                "maximum_extension_years_raw": extension_raw,
            },
        )], ""

    match = _FR_TWO_PROXIES_APPOINTED_ADMINISTRATORS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_proxies_appointed_administrators.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(group),
                role="administrateur", signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "proxy_revoked_and_appointed_administrator",
                    "previous_authority": "procuration",
                    "previous_authority_revoked": True,
                },
            )
            for group in ("name1", "name2")
        ], ""

    match = _FR_TWO_CLASS_SHARE_SPLIT.fullmatch(leftover)
    if match:
        before_total = (
            _count(match.group("from_count1")) * _amount(match.group("from_nominal1"))
            + _count(match.group("from_count2")) * _amount(match.group("from_nominal2"))
        )
        after_total = (
            _count(match.group("to_count1")) * _amount(match.group("to_nominal1"))
            + _count(match.group("to_count2")) * _amount(match.group("to_nominal2"))
        )
        capital_matches_split = all(
            match.group(left) == match.group(right)
            for left, right in (
                ("to_count1", "capital_count1"),
                ("to_nominal1", "capital_nominal1"),
                ("to_count2", "capital_count2"),
                ("to_nominal2", "capital_nominal2"),
            )
        )
        if before_total == after_total == _amount(match.group("total")) and capital_matches_split:
            return [_event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.two_class_voting_dividend_share_split.v1", {
                    "kind": "share_split_and_classes", "currency": "CHF",
                    "split_from": [
                        {
                            "count": _count(match.group("from_count1")),
                            "nominal": match.group("from_nominal1"),
                            "registered": True,
                        },
                        {
                            "count": _count(match.group("from_count2")),
                            "nominal": match.group("from_nominal2"),
                            "registered": True,
                        },
                    ],
                    "split_to": [
                        {
                            "count": _count(match.group("to_count1")),
                            "nominal": match.group("to_nominal1"),
                            "class": "voting_and_dividend_preferred",
                        },
                        {
                            "count": _count(match.group("to_count2")),
                            "nominal": match.group("to_nominal2"),
                            "class": "ordinary",
                        },
                    ],
                    "capital_total": match.group("total"),
                    "fully_paid": True, "registered": True,
                },
            )], ""

    match = _DE_MERGER_TWO_AGREEMENT_DATES_SAME_SHAREHOLDER.fullmatch(leftover)
    if match:
        agreement_year = match.group("agreement_date2").rsplit(".", 1)[-1]
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "de.text.merger_two_agreement_dates_same_shareholder.v1", {
                "kind": "absorption",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_dates": [
                    _iso_date(f"{match.group('agreement_date1')}{agreement_year}"),
                    _iso_date(match.group("agreement_date2")),
                ],
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital", "currency": "CHF",
                "same_shareholder": True,
                "capital_increase": False, "share_allocation": False,
            },
        )], ""

    match = _DE_AUTHORIZED_CAPITAL_ADJUSTED_WITH_FOUNDING_HISTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_adjusted_founding_history.v1", {
                "kind": "authorized_capital_clause", "action": "adjusted",
                "decision_date": _iso_date(match.group("decision_date")),
                "introduced_at_founding": True,
                "introduction_date": _iso_date(match.group("founding_date")),
                "details_in_statutes": True,
            },
        )], ""

    match = _FR_FOUNDATION_MEMBER_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.foundation_member_name_corrected.v1",
            match.group("name"), role="membre du conseil de fondation", extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _DE_CONDITIONAL_CAPITAL_CREATED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.conditional_share_capital_created.v1", {
                "kind": "conditional_share_capital", "action": "created",
                "decision_date": _iso_date(match.group("decision_date")),
                "details_in_statutes": True,
            },
        )], ""

    match = _FR_CAPITAL_AND_THREE_CLAUSES_MODIFIED.fullmatch(leftover)
    capital_details = match.group("details") if match else ""
    capital_dates = re.findall(r"\d{2}\.\d{2}\.\d{4}", capital_details)
    capital_details_valid = bool(
        match
        and len(capital_dates) == 12
        and capital_dates[3] == capital_dates[6] == capital_dates[9]
        and capital_details.count("augmentation autorisée du capital") == 1
        and capital_details.count("augmentation conditionnelle du capital") == 2
        and capital_details.count("Pour les détails, voir les statuts") == 3
        and "ainsi que la reprise de biens" in capital_details
        and "sont abrogées" in capital_details
    )
    if match and capital_details_valid and (
        _count(match.group("count")) * _amount(match.group("nominal"))
        == _amount(match.group("total"))
        and _count(match.group("previous_count"))
        * _amount(match.group("previous_nominal"))
        == _amount(match.group("total"))
    ):
        rule_id = "fr.text.capital_and_three_capital_clauses_modified.v1"
        decision_date = _iso_date(capital_dates[3])
        events = [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "share_nominal_reduction", "currency": "CHF",
                    "total": match.group("total"), "paid": match.group("paid"),
                    "paid_in_full": match.group("paid") == match.group("total"),
                    "shares_count": _count(match.group("count")),
                    "share_nominal": match.group("nominal"),
                    "previous_shares_count": _count(match.group("previous_count")),
                    "previous_share_nominal": match.group("previous_nominal"),
                    "registered": True, "transfer_restricted": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "contribution_clauses", "action": "repealed",
                    "contribution_in_kind_dates": [
                        _iso_date(capital_dates[0]),
                        _iso_date(capital_dates[1]),
                    ],
                    "asset_acquisition_date": _iso_date(capital_dates[2]),
                },
            ),
        ]
        for kind, introduced_index, modified_index in (
            ("authorized", 4, 5),
            ("conditional", 7, 8),
            ("conditional", 10, 11),
        ):
            events.append(_event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": f"{kind}_capital_clause", "action": "modified",
                    "decision_date": decision_date,
                    "introduction_date": _iso_date(capital_dates[introduced_index]),
                    "last_modified_date": _iso_date(capital_dates[modified_index]),
                    "details_in_statutes": True,
                },
            ))
        return events, ""

    match = _DE_TWO_NEW_PERSONS_INDIVIDUAL_SIGNING.fullmatch(leftover)
    if match:
        rule_id = "de.persons.two_new_people_individual_signing.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), signing="Einzelunterschrift", extra={
                    "action": "appointed", "origin": match.group("place1").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), signing="Einzelunterschrift", extra={
                    "action": "appointed",
                    "nationality": match.group("nationality2").strip(),
                },
            ),
        ], ""

    match = _DE_BANKRUPTCY_APPEAL_SUSPENDED_DISSOLVED_COMPANY.fullmatch(leftover)
    if match and (
        match.group("bankruptcy_court").replace("Konkursrichters", "Konkursrichter")
        == match.group("previous_bankruptcy_court").strip()
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_appeal_suspended_dissolved_company.v1", {
                "kind": "bankruptcy_suspended", "scope": "company",
                "decision_date": _iso_date(match.group("decision_date")),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "effective_date": _iso_date(match.group("effective_date")),
                "effective_time": match.group("effective_time").replace(".", ":"),
                "authority": match.group("authority").strip(),
                "bankruptcy_court": match.group("bankruptcy_court").strip(),
                "company_previously_dissolved": True,
                "bankruptcy_registration_deleted": True,
                "suspensive_effect": True,
            },
        )], ""

    match = _DE_LATE_FULL_PAYMENT_AFTER_FOUNDER_DEFAULT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.late_full_payment_after_founder_default.v1", {
                "kind": "share_payment", "action": "fully_paid_late",
                "founding_date": _iso_date(match.group("founding_date")),
                "payment_date": _iso_date(match.group("payment_date")),
                "founder_initially_defaulted": True,
                "shares_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"),
                "share_kind": match.group("share_kind"),
                "currency": "CHF", "fully_paid": True,
            },
        )], ""

    match = _DE_OWNER_BANKRUPTCY_APPEAL_SUSPENDED_FEMININE_HISTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.owner_bankruptcy_appeal_suspended_feminine_history.v1", {
                "kind": "bankruptcy_suspended", "scope": "owner",
                "decision_date": _iso_date(match.group("decision_date")),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "effective_date": _iso_date(match.group("effective_date")),
                "effective_time": match.group("effective_time"),
                "authority": match.group("authority").strip(),
                "bankruptcy_court": match.group("previous_authority").strip(),
                "suspensive_effect": True,
            },
        )], ""

    match = _FR_ADMINISTRATION_CONTINUING_SIGNING_AND_UNSIGNED_MEMBER.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administration_continuing_signing_unsigned_member.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président", signing="Einzelunterschrift",
                extra={"action": "appointed_president", "signing_continues": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("secretary"),
                role="secrétaire", signing="Einzelunterschrift",
                extra={"action": "appointed_secretary", "signing_continues": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                place=match.group("place"), role="administrateur", extra={
                    "action": "appointed", "origin": match.group("origin").strip(),
                    "without_signature": True,
                },
            ),
        ], ""

    match = _IT_MERGER_BALANCE_DATE_CORRECTED_FREE_EQUITY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "it.text.merger_balance_date_corrected_free_equity.v1", {
                "kind": "absorption",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "previous_balance_date": _iso_date(
                    match.group("previous_balance_date")
                ),
                "balance_date_corrected": True,
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities", "currency": "CHF",
                "deficit_coverage": "freely_available_equity",
                "deficit_coverage_confirmed_by_auditor": True,
                "acquirer_owns_all_shares": True,
                "capital_increase": False, "share_allocation": False,
            },
        )], ""

    return [], text
