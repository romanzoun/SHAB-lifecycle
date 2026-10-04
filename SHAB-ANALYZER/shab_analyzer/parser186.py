from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_APPEAL_SUSPENSIVE_EFFECT_ORC = re.compile(
    r"^Par arrêt du\s+(?P<order_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>.+?)\s+a accordé l['’]effet suspensif au recours "
    r"interjeté le\s+(?P<appeal_date>\d{2}\.\d{2}\.\d{4})\s+contre la "
    r"décision du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s*"
    r"\((?P<legal_basis>art\.\s*159,\s*al\.\s*2\s+ORC)\)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PRESIDENT_AND_FOREIGN_MEMBER = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé président\s+et\s+"
    r"(?P<member>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]),\s*tous deux avec signature individuelle\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_NAME_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens qu['’]un associé "
    r"se nomme\s+(?P<name>[^()]+?)\s*\(et non\s+"
    r"(?P<previous_name>[^,()]+),\s*comme publié\)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_AND_CONDITIONAL_CAPITAL_ARTICLES = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<authorized_date>\d{2}\.\d{2}\.\d{4})\s+die mit Beschluss vom\s+"
    r"(?P<introduction_date>\d{2}\.\d{2}\.\d{4})\s+eingeführte genehmigte "
    r"Kapitalerhöhung gemäss näherer Umschreibung in Art\.\s*"
    r"(?P<authorized_article>[\d.]+)\s+der Statuten geändert\.\s*\.\s*"
    r"Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<conditional_date>\d{2}\.\d{2}\.\d{4})\s+eine bedingte "
    r"Kapitalerhöhung gemäss näherer Umschreibung in Art\.\s*"
    r"(?P<conditional_article>[\d.]+)\s+der Statuten beschlossen\.?$",
    re.I | re.UNICODE,
)
_FR_ENTRY_SUPPLEMENTED_BOARD_VICE_PRESIDENT = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est complétée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+est vice-présidente du conseil\.?$",
    re.I | re.UNICODE,
)
_DE_REAL_ESTATE_ASSET_TRANSFER_TWO_DATES = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date1>\d{2}\.\d{2}\.\d{4})\s+und\s+"
    r"(?P<agreement_date2>\d{2}\.\d{2}\.\d{4})\s+die\s+"
    r"(?P<count_word>drei)\s+Grundstücke\s+(?P<properties>.+?)\s+auf die\s+"
    r"(?P<recipient>.+?),\s*in\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung\s+CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_CONDITIONAL_CAPITAL_MULTI_HISTORY = re.compile(
    r"^\[gestrichen:\s*Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+die mit Beschluss vom\s+"
    r"(?P<introduction_date>\d{2}\.\d{2}\.\d{4})\s+eingeführte und mit "
    r"Beschluss vom\s+(?P<previous_change_date1>\d{2}\.\d{2}\.\d{4})\s+und\s+"
    r"(?P<previous_change_date2>\d{2}\.\d{2}\.\d{4})\s+geänderte Bestimmung "
    r"betreffend bedingter Kapitalerhöhung gemäss näherer Umschreibung in den "
    r"Statuten geändert\.\]\.?\s*Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+die mit Beschluss vom\s+"
    r"(?P=introduction_date)\s+eingeführte und mit Beschlüssen vom\s+"
    r"(?P=previous_change_date1),\s*(?P=previous_change_date2)\s+und\s+"
    r"(?P=previous_decision_date)\s+geänderte Bestimmung betreffend bedingter "
    r"Kapitalerhöhung gemäss näherer Umschreibung in den Statuten geändert\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_SAME_OWNER_NO_PARTICIPATION_SHARES = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di\s+(?P<absorbed_name>.+?),\s*"
    r"in\s+(?P<absorbed_place>[^()]+?)\s*"
    r"\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*secondo contratto "
    r"di fusione del\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+e bilancio "
    r"al\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta attivi per "
    r"CHF\s+(?P<assets>[\d'.]+),?\s+e passivi verso terzi per CHF\s+"
    r"(?P<liabilities>[\d'.]+)\.\s*La totalità del capitale delle due società "
    r"è detenuta dalla stessa persona,\s*la fusione avviene dunque senza "
    r"aumento di capitale e senza attribuzione di quote di partecipazione\.?$",
    re.I | re.UNICODE,
)
_DE_CONDITIONAL_CAPITAL_INCREASED = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+eine Erhöhung des bedingten "
    r"Kapitals gemäss näherer Umschreibung in den Statuten beschlossen\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ASSOCIATES_TRANSFER_TO_NEW_MANAGER = re.compile(
    r"^(?P<seller1>[^,.;]+)\s+et\s+(?P<seller2>[^,.;]+)\s+ont chacun cédé\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvelle associée "
    r"pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*nommée en outre gérante"
    r"(?:\s+(?P<repeated_given_name>[^,.;\s]+))?\s+avec signature collective "
    r"à deux\s*;\s*par conséquent,\s*"
    r"(?P=seller1)\s+et\s+(?P=seller2)\s+sont maintenant chacun associé "
    r"pour\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_REMOVED_PERSON_MISSPELLED = re.compile(
    r"^Personne raidée:\s*(?P<name>[^,.;]+),\s*(?P<role>[^,.;]+),\s*"
    r"signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_ADMINISTRATOR_COLLECTIVE_THREE_FRAGMENT = re.compile(
    r"^Nouvel administrateur avec signature collective à trois:\s*"
    r"(?P<name>[^,.;]+),\s*"
    r"de et à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_UNPUBLISHED_STATUTES_POINT_MISSPELLED = re.compile(
    r"^surt un point non soumis à publication\.?$", re.I | re.UNICODE
)
_DE_DOCUMENT_LIST_CORRECTED_MISSPELLED = re.compile(
    r"^Die Lister der Belege wurde berichtigt\.?$", re.I | re.UNICODE
)
_FR_TWO_MANAGERS_SIGN_INDIVIDUALLY = re.compile(
    r"^(?P<manager>[^,.;]+)\s+et\s+(?P<president>[^,.;]+),\s*président,\s*"
    r"tous deux gérants,\s*signent désormais individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_ENTERPRISE_DELETED_CONTINUED = re.compile(
    r"^L['’]entreprise est radiée,\s*les activités continuant sous une autre "
    r"forme juridique\.?$",
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


def extract_parser186_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 186."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_APPEAL_SUSPENSIVE_EFFECT_ORC.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.appeal_suspensive_effect_orc.v1", {
                "kind": "appeal_suspensive_effect", "action": "granted",
                "order_date": _iso_date(match.group("order_date")),
                "authority": match.group("authority").strip(),
                "appeal_date": _iso_date(match.group("appeal_date")),
                "challenged_decision_date": _iso_date(match.group("decision_date")),
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "suspensive_effect": True,
            },
        )], ""

    match = _FR_ADMINISTRATION_PRESIDENT_AND_FOREIGN_MEMBER.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administration_president_foreign_member_individual.v1"
        signing = "Einzelunterschrift"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président", signing=signing, extra={"action": "appointed"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                place=match.group("place"), role="administrateur", signing=signing,
                extra={
                    "action": "appointed", "origin": match.group("origin").strip(),
                    "country": match.group("country").upper(),
                },
            ),
        ], ""

    match = _FR_ASSOCIATE_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_name_corrected.v1",
            match.group("name"), role="associé", extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _DE_AUTHORIZED_AND_CONDITIONAL_CAPITAL_ARTICLES.fullmatch(leftover)
    if match and match.group("authorized_date") == match.group("conditional_date"):
        rule_id = "de.text.authorized_and_conditional_capital_articles.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause", "action": "modified",
                    "decision_date": _iso_date(match.group("authorized_date")),
                    "introduction_date": _iso_date(match.group("introduction_date")),
                    "statutes_article": match.group("authorized_article"),
                    "details_in_statutes": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "conditional_capital_clause", "action": "created",
                    "decision_date": _iso_date(match.group("conditional_date")),
                    "statutes_article": match.group("conditional_article"),
                    "details_in_statutes": True,
                },
            ),
        ], ""

    match = _FR_ENTRY_SUPPLEMENTED_BOARD_VICE_PRESIDENT.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.entry_supplemented_board_vice_president.v1",
            match.group("name"), role="vice-présidente du conseil", extra={
                "action": "entry_supplemented", "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _DE_REAL_ESTATE_ASSET_TRANSFER_TWO_DATES.fullmatch(leftover)
    if match:
        properties = [item.strip() for item in re.split(r",\s*|\s+und\s+", match.group("properties"))]
        if len(properties) == 3:
            return [_event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.real_estate_asset_transfer_two_dates.v1", {
                    "source_kind": "company", "asset_kind": "real_property",
                    "agreement_dates": [
                        _iso_date(match.group("agreement_date1")),
                        _iso_date(match.group("agreement_date2")),
                    ],
                    "properties": properties,
                    "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration": match.group("consideration"),
                    "consideration_kind": "cash", "currency": "CHF",
                },
            )], ""

    match = _DE_CONDITIONAL_CAPITAL_MULTI_HISTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.conditional_capital_multi_history.v1", {
                "kind": "conditional_capital_clause", "action": "modified",
                "decision_date": _iso_date(match.group("decision_date")),
                "introduction_date": _iso_date(match.group("introduction_date")),
                "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                "previous_change_dates": [
                    _iso_date(match.group("previous_change_date1")),
                    _iso_date(match.group("previous_change_date2")),
                    _iso_date(match.group("previous_decision_date")),
                ],
                "details_in_statutes": True,
            },
        )], ""

    match = _IT_MERGER_SAME_OWNER_NO_PARTICIPATION_SHARES.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "it.text.merger_same_owner_no_participation_shares.v1", {
                "kind": "absorption",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities", "currency": "CHF",
                "same_owner": True, "capital_increase": False,
                "share_allocation": False, "share_kind": "quote di partecipazione",
            },
        )], ""

    match = _DE_CONDITIONAL_CAPITAL_INCREASED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.conditional_capital_increased.v1", {
                "kind": "conditional_capital", "action": "increased",
                "decision_date": _iso_date(match.group("decision_date")),
                "details_in_statutes": True,
            },
        )], ""

    match = _FR_TWO_ASSOCIATES_TRANSFER_TO_NEW_MANAGER.fullmatch(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        remaining = _count(match.group("remaining"))
        repeated_name = match.group("repeated_given_name")
        repeated_name_valid = (
            not repeated_name
            or repeated_name.casefold() == match.group("buyer").split()[-1].casefold()
        )
        if (
            buyer_count == 2 * transferred
            and len({
                match.group("nominal"), match.group("buyer_nominal"),
                match.group("remaining_nominal"),
            }) == 1
            and repeated_name_valid
        ):
            rule_id = "fr.persons.two_associates_transfer_to_new_manager.v1"
            buyer = match.group("buyer").strip()
            events = [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(group), role="associé",
                    extra={
                        "action": "shares_transferred", "counterparty": buyer,
                        "shares_before": remaining + transferred,
                        "shares_transferred": transferred, "shares_count": remaining,
                        "share_nominal": match.group("nominal"), "currency": "CHF",
                    },
                )
                for group in ("seller1", "seller2")
            ]
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée-gérante", signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed_and_shares_received", "new_associate": True,
                    "origin": match.group("origin").strip(),
                    "counterparties": [
                        match.group("seller1").strip(), match.group("seller2").strip(),
                    ],
                    "shares_received": buyer_count, "shares_count": buyer_count,
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                    **({"source_repeated_given_name": repeated_name} if repeated_name else {}),
                },
            ))
            return events, ""

    match = _FR_REMOVED_PERSON_MISSPELLED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_removed", "fr.persons.removed_person_raidée_typo.v1",
            match.group("name"), role=match.group("role").strip(),
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "removed", "source_format_issue": "raidée_for_radiée",
            },
        )], ""

    match = _FR_NEW_ADMINISTRATOR_COLLECTIVE_THREE_FRAGMENT.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.new_administrator_collective_three.v1",
            match.group("name"), place=match.group("place"), role="administrateur",
            signing="Kollektivunterschrift zu dreien", extra={
                "action": "appointed", "origin": match.group("place").strip(),
            },
        )], ""

    if _FR_UNPUBLISHED_STATUTES_POINT_MISSPELLED.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.unpublished_statutes_point_surt_typo.v1", {
                "kind": "unpublished_statutes_change", "action": "modified",
                "scope": "non_public", "source_format_issue": "surt_for_sur",
            },
        )], ""

    if _DE_DOCUMENT_LIST_CORRECTED_MISSPELLED.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.document_list_corrected_lister_typo.v1", {
                "kind": "supporting_document_list", "action": "corrected",
                "source_format_issue": "Lister_for_Liste",
            },
        )], ""

    match = _FR_TWO_MANAGERS_SIGN_INDIVIDUALLY.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_managers_sign_individually.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("manager"),
                role="gérant", signing="Einzelunterschrift",
                extra={"action": "signing_changed"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("president"),
                role="gérant, président", signing="Einzelunterschrift",
                extra={"action": "signing_changed"},
            ),
        ], ""

    if _FR_ENTERPRISE_DELETED_CONTINUED.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_deleted", "fr.text.enterprise_deleted_continued.v1", {
                "reason": "continued_under_other_legal_form",
                "scope": "organization", "business_continues": True,
            },
        )], ""

    return [], text
