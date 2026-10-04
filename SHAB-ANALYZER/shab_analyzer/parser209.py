from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_PARTICIPATION_CAPITAL_CREATED = re.compile(
    r"^Création d['’]un capital-participation:\s*CHF\s+(?P<total>[\d'.]+),\s*"
    r"entièrement libéré,\s*divisé en\s+(?P<count>[\d']+)\s+bons de "
    r"participation au porteur de CHF\s+(?P<nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_DISSOLUTION_NEW_LIQUIDATOR_AND_ADDRESS = re.compile(
    r"^Die Gesellschaft ist laut Beschluss der Generalversammlung vom\s+"
    r"(?P<date>\d{1,2}\.\d{1,2}\.\d{4})\s+aufgelöst\.\s*"
    r"Die Liquidation wird unter der Firma:\s*(?P<liquidation_name>.+?)\s+"
    r"durchgeführt\.\s*Neu eingetragene Person:\s*(?P<name>[^,.;]+),\s*"
    r"von\s+(?P<origin>[^,.;]+),\s*in\s+(?P<place>[^,.;]+),\s*"
    r"(?P<role>Liquidator),\s*(?P<signing>Einzelunterschrift)\.\s*"
    r"Liquidationsadresse:\s*(?P<address>.+?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<locality>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_REPLACED_QUOTED_WITH_UID = re.compile(
    r"^[\"“](?P<previous_name>.+?)[\"”]\s+n['’]est plus organe de révision\.\s*"
    r"Nouvel organe de révision:\s*(?P<name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_FOUNDATION_MEMBERS_COLLECTIVE = re.compile(
    r"^Nouveaux membres du conseil de fondation avec signature collective à "
    r"deux\s*:\s*(?P<name1>[^,.;]+),\s*de et à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*des\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*et\s+(?P<name3>[^,.;]+),\s*du\s+"
    r"(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;()]+)\s*"
    r"\((?P<country3>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_CLASSES_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{1,2}\.\d{1,2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{1,2}\.\d{1,2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le capital est "
    r"divisé en\s+(?P<ordinary_count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<ordinary_nominal>[\d'.]+),\s*et\s+(?P<preferred_count>[\d']+)\s+"
    r"actions nominatives de CHF\s+(?P<preferred_nominal>[\d'.]+),\s*"
    r"privilégiées quant au dividende et au produit de liquidation,\s*toutes "
    r"avec restrictions quant à la transmissibilité selon statuts\.?$",
    re.I | re.UNICODE,
)
_FR_SOCIAL_CAPITAL_AND_HOLDERS_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{1,2}\.\d{1,2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{1,2}\.\d{1,2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le capital "
    r"social est désormais divisé en\s+(?P<count1>[\d']+)\s+part de CHF\s+"
    r"(?P<nominal1>[\d'.]+)\s+et\s+(?P<count2>[\d']+)\s+part de CHF\s+"
    r"(?P<nominal2>[\d'.]+)\s+et que\s+(?P<holder1>.+?)\s*"
    r"\((?P<registry1>[^)]+)\)\s+est titulaire d['’](?P<holder_count1>[\d']+)\s+"
    r"part de CHF\s+(?P<holder_nominal1>[\d'.]+)\s+et\s+(?P<holder2>.+?)\s*"
    r"\((?P<registry2>[^)]+)\)\s+d['’](?P<holder_count2>[\d']+)\s+part de CHF\s+"
    r"(?P<holder_nominal2>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_WITH_COMMISSIONER = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{1,2}\.\d{1,2}\.\d{4})\s+wurde "
    r"eine definitive Nachlassstundung für\s+(?P<duration>\w+)\s+Monate bis\s+"
    r"(?P<until>\d{1,2}\.\d{1,2}\.\d{4})\s+bewilligt\.\s*Als Sachwalterin "
    r"wird die\s+(?P<commissioner>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*Mandatsleitung durch\s+"
    r"(?P<mandate_lead>[^,.;]+),\s*(?P<street>.+?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<locality>[^,;]+?),\s*eingesetzt\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_AND_CONDITIONAL_CAPITAL_HISTORY = re.compile(
    r"^Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<authorized_decision_date>\d{1,2}\.\d{1,2}\.\d{4})\s+den Beschluss "
    r"über die Ermächtigung einer genehmigten Kapitalerhöhung vom\s+"
    r"(?P<authorized_date>\d{1,2}\.\d{1,2}\.\d{4})\s+gemäss näherer "
    r"Umschreibung in den Statuten angepasst\.\s*\[bisher:\s*Die "
    r"Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<previous_authorized_decision_date>\d{1,2}\.\d{1,2}\.\d{4})\s+den "
    r"Beschluss über die Ermächtigung einer genehmigten Kapitalerhöhung vom\s+"
    r"(?P<previous_authorized_date>\d{1,2}\.\d{1,2}\.\d{4})\s+gemäss näherer "
    r"Umschreibung in den Statuten angepasst\.\]\.?\s*Die Generalversammlung "
    r"hat mit Beschluss vom\s+"
    r"(?P<conditional_decision_date>\d{1,2}\.\d{1,2}\.\d{4})\s+die "
    r"Statutenbestimmung über die bedingte Kapitalerhöhung vom\s+"
    r"(?P<conditional_date>\d{1,2}\.\d{1,2}\.\d{4})\s+geändert\.\s*"
    r"\[bisher:\s*Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<previous_conditional_decision_date>\d{1,2}\.\d{1,2}\.\d{4})\s+die "
    r"Statutenbestimmung über die bedingte Kapitalerhöhung vom\s+"
    r"(?P<previous_conditional_date>\d{1,2}\.\d{1,2}\.\d{4})\s+geändert\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_EXCLUSIONS_AND_NEW_ADMINISTRATOR = re.compile(
    r"^(?P<existing>[^,.;]+)\s+continue à signer collectivement à deux,\s*"
    r"désormais pas avec\s+(?P<existing_excluded1>[^,.;]+),\s*"
    r"(?P<existing_excluded2>[^,.;]+)\.\s*Nouvel administrateur avec signature "
    r"collective à deux,\s*toutefois pas avec\s+(?P<new_excluded1>[^,.;]+),\s*"
    r"ni\s+(?P<new_excluded2>[^:.;]+):\s*(?P<new_name>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_ORGANIZATION_ARTICLE_REMOVED = re.compile(
    r"^Organisation neu:\s*\[Löschung aufgrund geänderter "
    r"Eintragungsvorschriften gemäss\s+(?P<legal_basis>Art\.\s*92 lit\.\s*j "
    r"HRegV)\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_ASSET_TRANSFER_CASH_FRENCH_DATE = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<agreement_date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*la société "
    r"a transféré des actifs pour CHF\s+(?P<assets>[\d'.]+)\s+et des passifs "
    r"envers les tiers pour CHF\s+(?P<liabilities>[\d'.]+)\s+à\s+"
    r"(?P<recipient>.+?),\s*à\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*Contre-prestation:\s*"
    r"CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_EXTENDED_WITH_HISTORY = re.compile(
    r"^Mit Entscheid des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{1,2}\.\d{1,2}\.\d{4})\s+wurde die definitive "
    r"Nachlassstundung um weitere\s+(?P<duration>\w+)\s+Monate,\s*d\.h\.\s*bis "
    r"zum\s+(?P<until>\d{1,2}\.\d{1,2}\.\d{4})\s+verlängert\.\s*\[bisher:\s*"
    r"Mit Entscheid des\s+(?P<previous_authority>.+?)\s+vom\s+"
    r"(?P<previous_decision_date>\d{1,2}\.\d{1,2}\.\d{4})\s+wurde die "
    r"definitive Nachlassstundung um\s+(?P<previous_duration>\w+)\s+Monate,\s*"
    r"d\.h\.\s*bis zum\s+(?P<previous_until>\d{1,2}\.\d{1,2}\.\d{4})\s+"
    r"verlängert\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_PERSON_PUBLICATION_CORRECTED = re.compile(
    r"^Mit dem im SHAB Nr\.\s*(?P<issue>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{1,2}\.\d{1,2}\.\d{4})\s+publizierten TR-Nr\.\s*"
    r"(?P<entry>\d+)\s+vom\s+(?P<entry_date>\d{1,2}\.\d{1,2}\.\d{4})\s+wurde "
    r"der bisherige Text nicht richtig publiziert\.\s*Korrekt wäre:\s*"
    r"(?P<name>.+?),\s*von\s+(?P<origin>[^,.;]+),\s*in\s+"
    r"(?P<place>[^,.;]+),\s*(?P<role>[^,.;]+),\s*mit\s+"
    r"(?P<signing>Kollektivunterschrift zu zweien)\s*\[bisher:\s*in\s+"
    r"(?P<previous_place>[^\]]+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGER_USAGE_NAME_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription\s+(?:no|n°)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{1,2}\.\d{1,2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{1,2}\.\d{1,2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que l['’]"
    r"(?P<role>associée-gérante) se nomme\s+(?P<name>.+?)\s*"
    r"\(et non\s+(?P<previous_name>.+?)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_ASSET_TRANSFER_SUPERVISORY_DECISION = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat des\s+"
    r"(?P<agreement_date1>\d{1,2})\s+et\s+"
    r"(?P<agreement_date2>\d{1,2}\.\d{1,2}\.\d{4})\s+et selon décision de "
    r"l['’]autorité de surveillance du\s+"
    r"(?P<decision_date>\d{1,2}\.\d{1,2}\.\d{4}),\s*la fondation a transféré "
    r"des actifs de CHF\s+(?P<assets>[\d'.]+)\s+et des passifs envers les tiers "
    r"de CHF\s+(?P<liabilities>[\d'.]+)\s+à\s+(?P<recipient>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<place>[^,.;]+)\.\s*Contre-prestation:\s*(?P<consideration>aucune)\.?$",
    re.I | re.UNICODE,
)
_DE_ORGANIZATION_REMOVED_WITH_PREVIOUS = re.compile(
    r"^Organisation neu:\s*gestrichen,\s*da nicht mehr eintragungspflichtig\s*"
    r"\[bisher:\s*(?P<previous>[^\]]+)\]\.?$",
    re.I | re.UNICODE,
)


_FR_MONTHS = {
    "janvier": 1,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
}
_NUMBER_WORDS = {
    "ein": 1,
    "eine": 1,
    "einen": 1,
    "zwei": 2,
    "drei": 3,
    "vier": 4,
    "fünf": 5,
    "sechs": 6,
}


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _french_date(raw: str) -> str:
    day, month, year = raw.lower().replace("1er", "1").split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _number(raw: str) -> int:
    return int(raw) if raw.isdigit() else _NUMBER_WORDS[raw.casefold()]


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
    uid: str | None = None,
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
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser209_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 209."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_PARTICIPATION_CAPITAL_CREATED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.participation_capital_created.v1", {
                "kind": "participation_capital", "action": "created",
                "total": match.group("total"), "currency": "CHF",
                "fully_paid": True,
                "participation_certificates": _count(match.group("count")),
                "participation_nominal": match.group("nominal"),
                "participation_kind": "bearer",
            },
        )], ""

    match = _DE_DISSOLUTION_NEW_LIQUIDATOR_AND_ADDRESS.fullmatch(leftover)
    if match:
        rule_id = "de.text.dissolution_new_liquidator_and_address.v1"
        address = f"{match.group('address').strip()}, {match.group('postal_code')} {match.group('locality').strip()}"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "dissolution", "action": "opened",
                    "date": _iso_date(match.group("date")),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_name_changed", rule_id, {
                    "action": "liquidation_name",
                    "name": match.group("liquidation_name").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), role=match.group("role"),
                signing="Einzelunterschrift", extra={
                    "action": "appointed", "origin": match.group("origin").strip(),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", rule_id, {
                    "kind": "liquidation_address", "action": "changed",
                    "address": address,
                    "postal_code": match.group("postal_code"),
                    "locality": match.group("locality").strip(),
                },
            ),
        ], ""

    match = _FR_AUDITOR_REPLACED_QUOTED_WITH_UID.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.auditor_replaced_quoted_with_uid.v1"
        uid = match.group("uid")
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group("previous_name"),
                role="organe de révision", extra={"action": "removed"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), role="organe de révision", uid=uid,
                extra={"action": "appointed", "uid": uid},
            ),
        ], ""

    match = _FR_THREE_FOUNDATION_MEMBERS_COLLECTIVE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.three_foundation_members_collective.v1"
        people = (
            ("name1", "place1", "place1", None),
            ("name2", "place2", "origin2", None),
            ("name3", "place3", "origin3", "country3"),
        )
        events = []
        for name_key, place_key, origin_key, country_key in people:
            extra = {
                "action": "appointed",
                "origin": match.group(origin_key).strip(),
            }
            if country_key:
                extra["country"] = match.group(country_key).strip()
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(name_key),
                place=match.group(place_key),
                role="membre du conseil de fondation",
                signing="Kollektivunterschrift zu zweien", extra=extra,
            ))
        return events, ""

    match = _FR_SHARE_CLASSES_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.share_classes_corrected.v1", {
                "kind": "share_capital_structure", "action": "publication_corrected",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"), "currency": "CHF",
                "share_classes": [
                    {
                        "count": _count(match.group("ordinary_count")),
                        "nominal": match.group("ordinary_nominal"),
                        "kind": "registered",
                    },
                    {
                        "count": _count(match.group("preferred_count")),
                        "nominal": match.group("preferred_nominal"),
                        "kind": "registered",
                        "dividend_preference": True,
                        "liquidation_preference": True,
                    },
                ],
                "transfer_restricted_by_statutes": True,
            },
        )], ""

    match = _FR_SOCIAL_CAPITAL_AND_HOLDERS_CORRECTED.fullmatch(leftover)
    if match:
        rule_id = "fr.text.social_capital_and_holders_corrected.v1"
        reference = {
            "action": "publication_corrected", "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_ref": match.group("notice_ref"), "currency": "CHF",
        }
        events = [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", rule_id, {
                **reference, "kind": "social_capital_structure",
                "shares": [
                    {"count": _count(match.group("count1")), "nominal": match.group("nominal1")},
                    {"count": _count(match.group("count2")), "nominal": match.group("nominal2")},
                ],
            },
        )]
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"holder{index}"),
                role="associée", extra={
                    **reference,
                    "registry_id": match.group(f"registry{index}"),
                    "shares_count": _count(match.group(f"holder_count{index}")),
                    "share_nominal": match.group(f"holder_nominal{index}"),
                },
            ))
        return events, ""

    match = _DE_DEFINITIVE_MORATORIUM_WITH_COMMISSIONER.fullmatch(leftover)
    if match:
        rule_id = "de.text.definitive_moratorium_with_commissioner.v1"
        uid = match.group("uid")
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "definitive_moratorium", "action": "granted",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "duration_months": _number(match.group("duration")),
                    "until": _iso_date(match.group("until")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("commissioner"),
                place=match.group("locality"), role="Sachwalterin", uid=uid,
                extra={
                    "action": "appointed", "uid": uid,
                    "mandate_lead": match.group("mandate_lead").strip(),
                    "street": match.group("street").strip(),
                    "postal_code": match.group("postal_code"),
                },
            ),
        ], ""

    match = _DE_AUTHORIZED_AND_CONDITIONAL_CAPITAL_HISTORY.fullmatch(leftover)
    if match:
        rule_id = "de.text.authorized_and_conditional_capital_history.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause", "action": "modified",
                    "decision_date": _iso_date(match.group("authorized_decision_date")),
                    "authorization_date": _iso_date(match.group("authorized_date")),
                    "previous_decision_date": _iso_date(match.group("previous_authorized_decision_date")),
                    "previous_authorization_date": _iso_date(match.group("previous_authorized_date")),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "conditional_capital_clause", "action": "modified",
                    "decision_date": _iso_date(match.group("conditional_decision_date")),
                    "clause_date": _iso_date(match.group("conditional_date")),
                    "previous_decision_date": _iso_date(match.group("previous_conditional_decision_date")),
                    "previous_clause_date": _iso_date(match.group("previous_conditional_date")),
                },
            ),
        ], ""

    match = _FR_SIGNING_EXCLUSIONS_AND_NEW_ADMINISTRATOR.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.signing_exclusions_and_new_administrator.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("existing"),
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "restriction_changed",
                    "excluded_with": [
                        match.group("existing_excluded1").strip(),
                        match.group("existing_excluded2").strip(),
                    ],
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("new_name"),
                place=match.group("place"), role="administrateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group("origin").strip(),
                    "excluded_with": [
                        match.group("new_excluded1").strip(),
                        match.group("new_excluded2").strip(),
                    ],
                },
            ),
        ], ""

    match = _DE_ORGANIZATION_ARTICLE_REMOVED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.organization_article_removed.v1", {
                "kind": "organization_clause", "action": "removed",
                "reason": "changed_registration_rules",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
            },
        )], ""

    match = _FR_ASSET_TRANSFER_CASH_FRENCH_DATE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.asset_transfer_cash_french_date.v1", {
                "action": "transferred", "transferor_kind": "company",
                "agreement_date": _french_date(match.group("agreement_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"), "currency": "CHF",
            },
        )], ""

    match = _DE_DEFINITIVE_MORATORIUM_EXTENDED_WITH_HISTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.definitive_moratorium_extended_with_history.v1", {
                "kind": "definitive_moratorium", "action": "extended",
                "authority": match.group("authority").strip(),
                "decision_date": _iso_date(match.group("decision_date")),
                "duration_months": _number(match.group("duration")),
                "until": _iso_date(match.group("until")),
                "previous_authority": match.group("previous_authority").strip(),
                "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                "previous_duration_months": _number(match.group("previous_duration")),
                "previous_until": _iso_date(match.group("previous_until")),
            },
        )], ""

    match = _DE_PERSON_PUBLICATION_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.publication_corrected_place.v1",
            match.group("name"), place=match.group("place"),
            role=match.group("role"), signing=match.group("signing"), extra={
                "action": "publication_corrected",
                "origin": match.group("origin").strip(),
                "previous_place": match.group("previous_place").strip(),
                "issue": match.group("issue"),
                "notice_date": _iso_date(match.group("notice_date")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_ASSOCIATE_MANAGER_USAGE_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_manager_usage_name_corrected.v1",
            match.group("name"), role=match.group("role"), extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_FOUNDATION_ASSET_TRANSFER_SUPERVISORY_DECISION.fullmatch(leftover)
    if match:
        second_date = _iso_date(match.group("agreement_date2"))
        year, month, _ = second_date.split("-")
        first_date = f"{year}-{month}-{int(match.group('agreement_date1')):02d}"
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred",
            "fr.text.foundation_asset_transfer_supervisory_decision.v1", {
                "action": "transferred", "transferor_kind": "foundation",
                "agreement_dates": [first_date, second_date],
                "supervisory_decision_date": _iso_date(match.group("decision_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration": None, "currency": "CHF",
            },
        )], ""

    match = _DE_ORGANIZATION_REMOVED_WITH_PREVIOUS.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.organization_removed_with_previous.v1", {
                "kind": "organization_clause", "action": "removed",
                "reason": "no_longer_registration_required",
                "previous": match.group("previous").strip(),
            },
        )], ""

    return [], leftover
