from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_DEFINITIVE_MORATORIUM_EXTENDED_WITH_HISTORY = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat das\s+"
    r"(?P<authority>.+?)\s+die gewährte definitive Nachlassstundung um\s+"
    r"(?P<duration>\w+)\s+Monate bis\s+(?P<until>\d{2}\.\d{2}\.\d{4})\s+"
    r"verlängert\.\s*\[bisher:\s*Mit Entscheid vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+hat das\s+"
    r"(?P<previous_authority>.+?)\s+eine definitive Nachlassstundung von\s+"
    r"(?P<previous_duration>\w+)\s+Monaten bis\s+"
    r"(?P<previous_until>\d{2}\.\d{2}\.\d{4})\s+gewährt\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_EARLY_DELETION_POSTPONED_FEDERAL = re.compile(
    r"^Vorzeitige Löschung mit Bestätigung des zugelassenen Revisionsexperten vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+aufgeschoben mangels Zustimmung der\s+"
    r"eidg\.\s+Steuerverwaltung\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_RESTRICTED_SIGNING_POSTFIX = re.compile(
    r"^Nouveau membre du conseil de fondation:\s*(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*au?\s+"
    r"(?P<place>[^,.;]+),\s*avec le président ou le vice-président\.?$",
    re.I | re.UNICODE,
)
_FR_FIVE_CORPORATE_ASSOCIATES_SHARE_TRANSFER = re.compile(
    r"^L['’]associée\s+(?P<seller>.+?)\s*"
    r"\((?P<seller_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+cède\s+"
    r"(?P<count1>[\d']+)\s+part de CHF\s+(?P<nominal1>[\d'.]+)\s+à\s+"
    r"(?P<buyer1>.+?)\s*\((?P<uid1>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*(?P<count2>[\d']+)\s+part de CHF\s+"
    r"(?P<nominal2>[\d'.]+)\s+à\s+(?P<buyer2>.+?)\s*"
    r"\((?P<uid2>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*(?P<count3>[\d']+)\s+part de CHF\s+"
    r"(?P<nominal3>[\d'.]+)\s+à\s+(?P<buyer3>.+?),\s*à\s+"
    r"(?P<place3>[^,.;]+),\s*(?P<count4>[\d']+)\s+part de CHF\s+"
    r"(?P<nominal4>[\d'.]+)\s+à\s+(?P<buyer4>.+?),\s*à\s+"
    r"(?P<place4>[^,.;]+),\s*et\s+(?P<count5>[\d']+)\s+part de CHF\s+"
    r"(?P<nominal5>[\d'.]+)\s+à\s+(?P<buyer5>.+?)\s*"
    r"\((?P<uid5>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<place5>[^,.;]+(?:\s*\([A-Z]{2}\))?),\s*nouvelles associées avec\s+"
    r"(?P<buyer_count>[\d']+)\s+part de CHF\s+(?P<buyer_nominal>[\d'.]+)\s+"
    r"chacune\.\s*(?P=seller)\s*\((?P=seller_uid)\)\s+reste titulaire de\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_WITHOUT_SIGNATURE_LONG_PLACE = re.compile(
    r"^(?P<name>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>.+?),\s*est membre du conseil de "
    r"fondation;\s*elle n['’]exerce pas la signature\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_SEAT_AND_TWO_STATUTES_DATES = re.compile(
    r"^Nouveau siège:\s*(?P<seat>[^.;]+)\.\s*Statuts modifiés les\s+"
    r"(?P<date1>\d{2}\.\d{2}\.\d{4})\s+et\s+"
    r"(?P<date2>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_MULTI_CURRENCY_DEBT_OFFSET_CAPITAL_INCREASE = re.compile(
    r"^Bei der ordentlichen Kapitalerhöhung vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+werden Forderungen in der Höhe von\s+"
    r"CHF\s+(?P<claim_chf>[\d'.]+)\s+und USD\s+(?P<claim_usd>[\d'.]+)\s+"
    r"verrechnet,\s*wofür\s+(?P<count>[\d']+)\s+"
    r"(?P<share_kind>Namenaktien) zu CHF\s+(?P<nominal>[\d'.]+)\s+"
    r"ausgegeben werden\.?$",
    re.I | re.UNICODE,
)
_DE_TWO_LEGACY_BRANCHES_REMOVED = re.compile(
    r"^Zweigniederlassung neu:\s*\[gestrichen:\s*"
    r"(?P<place1>[^()\]]+)\s*\((?P<registry_id1>CH-[\d.]+-\d)\)\]\.?\s*"
    r"\[gestrichen:\s*(?P<place2>[^()\]]+)\s*"
    r"\((?P<registry_id2>CH-[\d.]+-\d)\)\]\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ASSOCIATE_SHARE_COUNTS_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que l['’]associé\s+"
    r"(?P<name1>[^,.;]+)\s+est titulaire de\s+(?P<count1>[\d']+)\s+parts de "
    r"CHF\s+(?P<nominal1>[\d'.]+)\s*\(et non\s+"
    r"(?P<previous_count1>[\d']+)\s+parts de CHF\s+"
    r"(?P<previous_nominal1>[\d'.]+)\s+comme publié\)\s+et l['’]associé,?\s+"
    r"(?P<name2>[^,.;]+)\s+de\s+(?P<count2>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal2>[\d'.]+)\s*\(et non\s+(?P<previous_count2>[\d']+)\s+"
    r"parts de CHF\s+(?P<previous_nominal2>[\d'.]+)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_DE_LIQUIDATION_ADDRESS_REMOVED = re.compile(
    r"^\[gestrichen:\s*Liquidationsadresse:\s*(?P<address>.+?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<locality>[^\].]+)\.?\]\.?$",
    re.I | re.UNICODE,
)
_DE_HEAD_OFFICE_IDENTIFIER_HISTORY_FRAGMENT = re.compile(
    r"^\)\s*\[bisher:\s*Identifikationsnummer Hauptsitz:\s*"
    r"(?P<previous_id>CH-[\d.]+-\d)\]\.?$",
    re.I | re.UNICODE,
)
_FR_AUDIT_WAIVER_MENTION_REMOVED_NO_NOTICE = re.compile(
    r"^L['’]inscription No\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est complétée en ce sens que la "
    r"mention relative à la renonciation à un contrôle restreint est radiée\.?$",
    re.I | re.UNICODE,
)
_DE_MERGER_DISCLOSURE_CORRECTED_PREFIX = re.compile(
    r"^Mit Bestätigung der zugelassenen Revisionsexpertin vom\s+"
    r"(?P<confirmation_date>\d{2}\.\d{2}\.\d{4})\s+wird das Handelsregister "
    r"über die Überschuldung der übernehmenden Gesellschaft,\s*der\s+"
    r"(?P<acquirer>.+?)\s*\(bisher:\s*(?P<previous_name>[^)]+)\),\s*in\s+"
    r"(?P<acquirer_place>.+?)\s*\((?P<acquirer_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+"
    r"gemäss Bilanz per\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4})\s+informiert\.\s*"
    r"Damit ergänzt die Gesellschaft nachträglich ihre Fusionsunterlagen mit "
    r"dieser bisher nicht offengelegten Bestätigung\.\s*Folglich wird der "
    r"Handelsregistereintrag vom\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"\(TR-Nr\.\s*(?P<entry>\d+)\),\s*wie folgt,\s*geändert:\s*Übernahme der "
    r"Aktiven und des Fremdkapitals der\s+(?P<absorbed>.+?),\s*in\s+"
    r"(?P<absorbed_place>[^()]+?)\s*\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"gemäss Fusionsvertrag vom\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"und Bilanz per\s+(?P<merger_balance_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+und Fremdkapital von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+gehen auf die übernehmende Gesellschaft über\.\s*"
    r"Die übertragende Gesellschaft weist gemäss Bestätigung der zugelassenen "
    r"Revisionsexpertin frei verwendbares Eigenkapital im Umfang des "
    r"Kapitalverlustes und der Überschuldung auf\.\s*Da derselbe Aktionär "
    r"sämtliche Aktien der an der Fusion beteiligten Gesellschaften hält,\s*"
    r"findet weder eine Kapitalerhöhung noch eine Aktienzuteilung statt\.\s*"
    r"\[bisher:$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_DOMICILE_CORRECTED = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\)\s+est rectifiée dans ce sens:\s*"
    r"(?P<name>[^,.;]+),\s*(?P<role>administrateur),\s*"
    r"(?P<signing>signature collective à deux),\s*à\s+(?P<place>[^()]+?)\s*"
    r"\(et non pas à\s+(?P<previous_place>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_CONDITIONAL_CAPITAL_RESOLVED_WITH_ARTICLE = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+eine bedingte Kapitalerhöhung gemäss "
    r"näherer Umschreibung in\s+(?P<article>Art\.\s*[^.]+)\s+der Statuten "
    r"beschlossen\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_SIGNATURE_REVOKED = re.compile(
    r"^L['’]administrateur\s+(?P<name>[^,.;]+)\s+n['’]exerce plus la signature "
    r"sociale\.?$",
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
        payload={
            "name": clean_name,
            "place": clean_place,
            **({"uid": uid} if uid else {}),
            **(extra or {}),
        },
    )


def extract_parser163_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 163."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_DEFINITIVE_MORATORIUM_EXTENDED_WITH_HISTORY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.definitive_moratorium_extended_with_history.v2",
            {
                "kind": "composition_moratorium", "action": "extended",
                "moratorium_kind": "definitive",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "duration": match.group("duration").lower(),
                "until": _iso_date(match.group("until")),
                "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                "previous_duration": match.group("previous_duration").lower(),
                "previous_until": _iso_date(match.group("previous_until")),
            },
        ))

    match = _DE_EARLY_DELETION_POSTPONED_FEDERAL.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.early_deletion_postponed_federal.v1",
            {
                "kind": "deletion_postponed", "requested_early": True,
                "audit_expert_confirmation_date": _iso_date(match.group("date")),
                "tax_authority_consent_missing": True,
                "authorities": ["federal_tax_authority"],
            },
        ))

    match = _FR_FOUNDATION_MEMBER_RESTRICTED_SIGNING_POSTFIX.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.foundation_member_restricted_signing_postfix.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil de fondation",
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "appointed", "origin": match.group("origin").strip(),
                "co_signs_with": "président ou vice-président",
            },
        ))

    match = _FR_FIVE_CORPORATE_ASSOCIATES_SHARE_TRANSFER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.five_corporate_associates_share_transfer.v1"
        seller = match.group("seller").strip()
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, seller, uid=match.group("seller_uid"),
            role="associée",
            extra={
                "action": "shares_transferred", "shares_transferred": sum(
                    _count(match.group(f"count{index}")) for index in range(1, 6)
                ),
                "shares_count": _count(match.group("seller_count")),
                "share_nominal": match.group("seller_nominal"), "currency": "CHF",
            },
        ))
        for index in range(1, 6):
            uid = match.group(f"uid{index}") if index in (1, 2, 5) else None
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"buyer{index}"),
                place=match.group(f"place{index}"), uid=uid, role="associée",
                extra={
                    "action": "shares_received", "counterparty": seller,
                    "counterparty_uid": match.group("seller_uid"),
                    "new_associate": True,
                    "shares_received": _count(match.group(f"count{index}")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ))

    match = _FR_FOUNDATION_MEMBER_WITHOUT_SIGNATURE_LONG_PLACE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.foundation_member_without_signature_long_place.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil de fondation",
            signing="ohne Zeichnungsberechtigung",
            extra={
                "action": "appointed", "origin": match.group("origin").strip(),
                "without_signature": True,
            },
        ))

    match = _FR_NEW_SEAT_AND_TWO_STATUTES_DATES.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.new_seat_and_two_statutes_dates.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "seat_changed", rule_id,
                {"action": "changed", "seat": match.group("seat").strip()},
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id,
                {
                    "action": "modified",
                    "dates": [
                        _iso_date(match.group("date1")),
                        _iso_date(match.group("date2")),
                    ],
                },
            ),
        ])

    match = _DE_MULTI_CURRENCY_DEBT_OFFSET_CAPITAL_INCREASE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.multi_currency_debt_offset_capital_increase.v1",
            {
                "kind": "ordinary_capital_increase",
                "date": _iso_date(match.group("date")),
                "contribution_kind": "debt_offset",
                "claims": [
                    {"amount": match.group("claim_chf"), "currency": "CHF"},
                    {"amount": match.group("claim_usd"), "currency": "USD"},
                ],
                "issued_shares": [{
                    "count": _count(match.group("count")),
                    "nominal": match.group("nominal"),
                    "currency": "CHF", "kind": match.group("share_kind"),
                }],
            },
        ))

    match = _DE_TWO_LEGACY_BRANCHES_REMOVED.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.two_legacy_branches_removed.v1"
        for index in (1, 2):
            events.append(_event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id,
                {
                    "action": "removed", "place": match.group(f"place{index}").strip(),
                    "registry_id": match.group(f"registry_id{index}"),
                },
            ))

    match = _FR_TWO_ASSOCIATE_SHARE_COUNTS_CORRECTED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_associate_share_counts_corrected.v1"
        reference = {
            "action": "share_count_corrected", "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_ref": match.group("notice_ref"), "currency": "CHF",
        }
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="associé",
                extra={
                    **reference,
                    "shares_count": _count(match.group(f"count{index}")),
                    "share_nominal": match.group(f"nominal{index}"),
                    "previous_shares_count": _count(match.group(f"previous_count{index}")),
                    "previous_share_nominal": match.group(f"previous_nominal{index}"),
                },
            ))

    match = _DE_LIQUIDATION_ADDRESS_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "de.text.liquidation_address_removed.v1",
            {
                "kind": "liquidation_address", "action": "removed",
                "address": f"{match.group('address').strip()}, {match.group('postal_code')} {match.group('locality').strip()}",
                "postal_code": match.group("postal_code"),
                "locality": match.group("locality").strip(),
            },
        ))

    match = _DE_HEAD_OFFICE_IDENTIFIER_HISTORY_FRAGMENT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.head_office_identifier_history_fragment.v1",
            {
                "kind": "head_office_identifier", "action": "corrected",
                "previous_identifier": match.group("previous_id"),
            },
        ))

    match = _FR_AUDIT_WAIVER_MENTION_REMOVED_NO_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "audit_requirement_changed", "fr.text.audit_waiver_mention_removed_no_notice.v1",
            {
                "kind": "limited_audit_waiver", "action": "revoked",
                "waiver_mention_removed": True, "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _DE_MERGER_DISCLOSURE_CORRECTED_PREFIX.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.merger_disclosure_corrected_prefix.v1",
            {
                "kind": "merger_disclosure", "action": "supplemented_and_corrected",
                "confirmation_date": _iso_date(match.group("confirmation_date")),
                "acquirer": match.group("acquirer").strip(),
                "acquirer_previous_name": match.group("previous_name").strip(),
                "acquirer_place": match.group("acquirer_place").strip(),
                "acquirer_uid": match.group("acquirer_uid"),
                "overindebtedness_balance_date": _iso_date(match.group("balance_date")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "absorbed_company": match.group("absorbed").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("merger_balance_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "currency": "CHF", "same_shareholder": True,
                "capital_increase": False, "shares_allocated": False,
                "capital_loss_and_overindebtedness_covered": True,
            },
        ))

    match = _FR_ADMINISTRATOR_DOMICILE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_domicile_corrected.v1",
            match.group("name"), place=match.group("place"), role=match.group("role"),
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "domicile_corrected",
                "previous_place": match.group("previous_place").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        ))

    match = _DE_CONDITIONAL_CAPITAL_RESOLVED_WITH_ARTICLE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.conditional_capital_resolved_with_article.v1",
            {
                "kind": "conditional_capital", "action": "resolved",
                "decision_date": _iso_date(match.group("date")),
                "statutes_article": match.group("article").strip(),
                "details_in_statutes": True,
            },
        ))

    match = _FR_ADMINISTRATOR_SIGNATURE_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.administrator_signature_revoked.v1",
            match.group("name"), role="administrateur",
            extra={"action": "revoked"},
        ))

    return events, re.sub(r"\s+", " ", leftover).strip(" .,;")
