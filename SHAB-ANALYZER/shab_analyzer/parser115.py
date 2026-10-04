from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_STANDALONE_STATUTES_CHANGED = re.compile(
    r"^Statuten geändert am\s+(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_ASSET_TRANSFER_INVENTORY_NO_CONSIDERATION = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+et inventaire au\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré "
    r"des actifs pour CHF\s+(?P<assets>[\d'.]+)\s+et des passifs envers les "
    r"tiers pour CHF\s+(?P<liabilities>[\d'.]+)\s+à la société\s+"
    r"[\"'“](?P<recipient>.+?)[\"'”],\s*à\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*(?P<consideration>aucune)\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_RENAMED_AND_MOVED = re.compile(
    r"^(?P<previous_name>[^,.;]+),\s*laquelle se nomme maintenant\s+"
    r"(?P<name>[^,.;]+),\s*est désormais à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_ASSOCIATE_WITH_ORIGIN = re.compile(
    r"^Nouvel associé\s*:\s*(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"(?:à|au|aux)\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_DEFICIT_FREE_EQUITY = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di\s+(?P<absorbed_name>.+?),\s*"
    r"in\s+(?P<absorbed_place>[^()]+?)\s*"
    r"\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"secondo (?:il\s+)?contratto di fusione del\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+e bilancio al\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta attivi per CHF\s+"
    r"(?P<assets>[\d'.]+),?\s+e passivi verso terzi per CHF\s+"
    r"(?P<liabilities>[\d'.]+),\s*con un['’]eccedenza passiva di CHF\s+"
    r"(?P<deficit>[\d'.]+)\.\s*Conformemente all['’]attestazione di un perito "
    r"revisore abilitato,\s*la società assuntrice dispone di fondi propri "
    r"liberamente disponibili equivalenti almeno all['’]ammontare dello scoperto "
    r"e del sovraindebitamento\.\s*La società assuntrice detiene tutte le azioni "
    r"della società trasferente,\s*per cui la fusione avviene senza aumento di "
    r"capitale e senza attribuzione di azioni\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_SIGNATURE_GRANTED_WITH_ROLE = re.compile(
    r"^Signature\s+(?P<signing>collective à deux),\s*limitée aux affaire(?:s)? "
    r"de la succursale a été conférée à\s+(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"(?:à|au|aux)\s+(?P<place>[^,.;]+),\s*"
    r"(?P<role>directeur de la succursale)\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_NAME_SUPPLEMENT = re.compile(
    r"^Complément:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée en ce sens que la raison de "
    r"commerce de la succursale exacte est:\s*(?P<name>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PAIR_INDIVIDUAL_ORIGIN = re.compile(
    r"^Administration\s*:\s*(?P<president>[^,.;]+),\s*nommé président\s+et\s+"
    r"(?P<member>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*(?:à|au|aux)\s+(?P<place>[^,.;]+),\s*"
    r"lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PAIR_INDIVIDUAL_SAME_PLACE = re.compile(
    r"^Administration\s*:\s*(?P<president>[^,.;]+),\s*nommé président\s+et\s+"
    r"(?P<member>[^,.;]+),\s*de et à\s+(?P<place>[^,.;]+),\s*"
    r"lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_ASSET_TRANSFER_AUTHENTIC_NO_CONSIDERATION = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat et acte authentique du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+et selon décision de l['’]autorité de "
    r"surveillance du\s+(?P<approval_date>\d{2}\.\d{2}\.\d{4}),\s*la fondation "
    r"a transféré une partie des actifs de CHF\s+(?P<assets>[\d'.]+)\s+et des "
    r"passifs envers les tiers de CHF\s+(?P<liabilities>[\d'.]+)\s+à la société\s+"
    r"[\"“](?P<recipient>.+?)[\"”]\s+à\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*(?P<consideration>aucune)\.?$",
    re.I | re.UNICODE,
)
_FR_CAPITAL_RECAPITALIZATION_CORRECTED = re.compile(
    r"^\[non:\s*En assemblée générale du\s+(?P<previous_date>\d{1,2}\.\d{2}\.\d{4}),\s*"
    r"la société a réduit son capital-actions de CHF\s+(?P<previous_from>[\d'.-]+)\s+"
    r"à CHF\s+(?P<previous_reduced_to>[\d'.-]+)\s+par annulation des\s+"
    r"(?P<previous_cancelled_count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<previous_cancelled_nominal>[\d'.-]+)\s+chacune,\s*en application de "
    r"l['’]article\s+(?P<previous_article>\d+)\s+CO,\s*puis le capital-actions a été "
    r"porté à CHF\s+(?P<previous_total>[\d'.-]+)\s+par l['’]émission de\s+"
    r"(?P<previous_count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<previous_nominal>[\d'.-]+)\]\.?\s*"
    r"En assemblée générale du\s+(?P<date>\d{1,2}\.\d{2}\.\d{4}),\s*"
    r"la société a réduit son capital-actions de CHF\s+(?P<from_total>[\d'.-]+)\s+"
    r"à CHF\s+(?P<reduced_to>[\d'.-]+)\s+par annulation des\s+"
    r"(?P<cancelled_count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<cancelled_nominal>[\d'.-]+)\s+chacune,\s*en application de "
    r"l['’]article\s+(?P<article>\d+)\s+CO,\s*puis le capital-actions a été porté "
    r"à CHF\s+(?P<total>[\d'.-]+)\s+par l['’]émission de\s+"
    r"(?P<count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<nominal>[\d'.-]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MERGER_SAME_ASSOCIATES = re.compile(
    r"^Fusion:\s*reprise des actifs de CHF\s+(?P<assets>[\d'.]+)\s+et des "
    r"passifs envers les tiers de CHF\s+(?P<liabilities>[\d'.]+)\s+de la société "
    r"à responsabilité limitée\s+[\"“]?(?P<absorbed_name>.+?)[\"”]?\s+à\s+"
    r"(?P<absorbed_place>[^()]+?)\s*"
    r"\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*selon contrat de fusion "
    r"du\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+et bilan au\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\.\s*La totalité du capital social "
    r"des deux sociétés étant détenue par les mêmes associées,\s*la fusion ne "
    r"donne pas lieu à une augmentation du capital,\s*ni à une attribution de "
    r"parts sociales\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_BEARER_SHARES_CORRECTED = re.compile(
    r"^Nouvelles actions:\s*(?P<count>[\d']+)\s+actions\s+"
    r"(?P<kind>au porteur)\s+de CHF\s+(?P<nominal>[\d'.]+)\s*"
    r"\[non:\s*(?P<previous_count>[\d']+)\s+actions\s+"
    r"(?P<previous_kind>nominatives)\s+de CHF\s+"
    r"(?P<previous_nominal>[\d'.]+)(?:\s*\(chacune\))?\]\.?$",
    re.I | re.UNICODE,
)
_DE_OWNER_BANKRUPTCY_APPEAL_SUSPENDED = re.compile(
    r"^Mit Verfügung vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+der Beschwerde gegen die Konkurseröffnung vom\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+die aufschiebende Wirkung "
    r"erteilt\.\s*\[bisher:\s*Mit Verfügung vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<previous_time>\d{1,2})\s*h,\s*hat\s+(?P<court>.+?)\s+über das Vermögen "
    r"des Inhabers den Konkurs eröffnet\.\]\.?$",
    re.I | re.UNICODE,
)
_IT_ACTIVITY_AREA_CHANGED = re.compile(
    r"^Il raggio di attività comprende\s+(?P<repeated_previous>.+?)\.\s*"
    r"\[radiati:\s*Il raggio di attività comprende\s+(?P<previous>.+?)\.\]\.?\s*"
    r"Il raggio di attività comprende\s+(?P<current>.+?)\.?$",
    re.I | re.UNICODE,
)
_DE_MERGER_ALL_INTERESTS_HELD = re.compile(
    r"^Fusion:\s*Übernahme der Aktiven und Passiven der\s+"
    r"(?P<absorbed_name>.+?),\s*in\s+(?P<absorbed_place>[^()]+?)\s*"
    r"\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\s*\),\s*"
    r"gemäss Fusionsvertrag vom\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"und Bilanz per\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4})\.\s*Aktiven von "
    r"CHF\s+(?P<assets>[\d'.]+)\s+und Passiven \(Fremdkapital\) von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+gehen auf die übernehmende Gesellschaft über\.\s*"
    r"Da die übernehmende Gesellschaft sämtliche Stammanteile der übertragenden "
    r"Gesellschaft hält,\s*findet weder eine Kapitalerhöhung noch eine "
    r"Aktienzuteilung statt\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _money(raw: str) -> str:
    return re.sub(r"\.--$", "", raw)


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


def extract_parser115_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 115."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_STANDALONE_STATUTES_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.standalone_statutes_changed.v1",
            {"date": _iso_date(match.group("date")), "raw": match.group(0)},
        ))

    match = _FR_ASSET_TRANSFER_INVENTORY_NO_CONSIDERATION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.asset_transfer_inventory_no_consideration.v1",
            {
                "date": _iso_date(match.group("date")),
                "inventory_date": _iso_date(match.group("inventory_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "currency": "CHF", "liabilities_kind": "third_party_liabilities",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration").lower(),
                "gratuitous": True,
            },
        ))

    match = _FR_PERSON_RENAMED_AND_MOVED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.renamed_and_moved.v1",
            match.group("name"), place=match.group("place"),
            extra={
                "action": "name_and_domicile_changed",
                "previous_name": match.group("previous_name").strip(),
                "domicile_changed": True,
            },
        ))

    match = _FR_NEW_ASSOCIATE_WITH_ORIGIN.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.new_associate_with_origin.v1",
            match.group("name"), place=match.group("place"), role="associé",
            extra={"action": "appointed", "heimat": match.group("origin").strip()},
        ))

    match = _IT_MERGER_DEFICIT_FREE_EQUITY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "it.text.merger_deficit_free_equity.v1",
            {
                "kind": "absorption",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "deficit": match.group("deficit"), "currency": "CHF",
                "deficit_coverage": "freely_available_equity",
                "deficit_coverage_confirmed_by_auditor": True,
                "all_shares_held_by_acquirer": True,
                "capital_increase": False, "share_allocation": False,
            },
        ))

    match = _FR_BRANCH_SIGNATURE_GRANTED_WITH_ROLE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.branch_signing_with_role.v1",
            match.group("name"), place=match.group("place"),
            role=match.group("role"), signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "granted", "scope": "branch",
                "heimat": match.group("origin").strip(),
            },
        ))

    match = _FR_BRANCH_NAME_SUPPLEMENT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_name_changed", "fr.text.branch_name_supplement.v1",
            {
                "scope": "branch", "action": "corrected",
                "to": match.group("name").strip(), "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_ADMINISTRATION_PAIR_INDIVIDUAL_ORIGIN.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_pair_individual_origin.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président", signing="Einzelunterschrift",
                extra={"action": "appointed_president"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                place=match.group("place"), role="membre de l'administration",
                signing="Einzelunterschrift",
                extra={"action": "appointed", "heimat": match.group("origin").strip()},
            ),
        ])

    match = _FR_ADMINISTRATION_PAIR_INDIVIDUAL_SAME_PLACE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_pair_individual_same_place.v1"
        place = match.group("place").strip()
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président", signing="Einzelunterschrift",
                extra={"action": "appointed_president"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"), place=place,
                role="membre de l'administration", signing="Einzelunterschrift",
                extra={"action": "appointed", "heimat": place},
            ),
        ])

    match = _FR_FOUNDATION_ASSET_TRANSFER_AUTHENTIC_NO_CONSIDERATION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred",
            "fr.text.foundation_asset_transfer_authentic_no_consideration.v1",
            {
                "source_kind": "foundation", "date": _iso_date(match.group("date")),
                "supervisory_approval_date": _iso_date(match.group("approval_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "currency": "CHF", "liabilities_kind": "third_party_liabilities",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration").lower(),
                "gratuitous": True,
            },
        ))

    match = _FR_CAPITAL_RECAPITALIZATION_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.capital_recapitalization_corrected.v1",
            {
                "kind": "recapitalization_after_full_reduction",
                "action": "corrected", "date": _iso_date(match.group("date")),
                "from_total": _money(match.group("from_total")),
                "reduced_to": _money(match.group("reduced_to")),
                "cancelled_share_count": _count(match.group("cancelled_count")),
                "cancelled_share_nominal": _money(match.group("cancelled_nominal")),
                "legal_basis": f"article {match.group('article')} CO",
                "total": _money(match.group("total")),
                "share_count": _count(match.group("count")),
                "share_nominal": _money(match.group("nominal")),
                "share_kind": "nominatives", "currency": "CHF",
                "previous_published_share_count": _count(match.group("previous_count")),
                "previous_published_share_nominal": _money(match.group("previous_nominal")),
            },
        ))

    match = _FR_MERGER_SAME_ASSOCIATES.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "fr.text.merger_same_associates.v1",
            {
                "kind": "absorption",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "currency": "CHF", "same_owners": True,
                "capital_increase": False, "share_allocation": False,
                "share_kind": "parts sociales",
            },
        ))

    match = _FR_NEW_BEARER_SHARES_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.new_bearer_shares_corrected.v1",
            {
                "kind": "share_structure", "action": "corrected",
                "count": _count(match.group("count")),
                "nominal": match.group("nominal"), "share_kind": match.group("kind"),
                "previous_published_count": _count(match.group("previous_count")),
                "previous_published_nominal": match.group("previous_nominal"),
                "previous_published_kind": match.group("previous_kind"),
                "currency": "CHF",
            },
        ))

    match = _DE_OWNER_BANKRUPTCY_APPEAL_SUSPENDED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.owner_bankruptcy_appeal_suspended.v1",
            {
                "kind": "bankruptcy_effect_suspended", "scope": "owner",
                "decision_date": _iso_date(match.group("decision_date")),
                "bankruptcy_decision_date": _iso_date(match.group("bankruptcy_date")),
                "bankruptcy_effective_time": f"{int(match.group('previous_time')):02d}:00",
                "authority": match.group("authority").strip(),
                "bankruptcy_court": match.group("court").strip(),
            },
        ))

    match = _IT_ACTIVITY_AREA_CHANGED.search(leftover)
    if match:
        if match.group("repeated_previous").strip() == match.group("previous").strip():
            consume(match)
            events.append(_event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", "it.text.activity_area_changed.v1",
                {
                    "kind": "activity_area", "action": "changed",
                    "previous": match.group("previous").strip(),
                    "current": match.group("current").strip(),
                },
            ))

    match = _DE_MERGER_ALL_INTERESTS_HELD.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "de.text.merger_all_interests_held.v1",
            {
                "kind": "absorption",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "currency": "CHF", "liabilities_kind": "third_party_capital",
                "all_interests_held_by_acquirer": True,
                "capital_increase": False, "share_allocation": False,
                "transferred_interest_kind": "Stammanteile",
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
