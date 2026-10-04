from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_FIVE_ASSOCIATES_TRANSFER_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_dates>\d{2}\.\d{2}\.\d{4}(?:\s+\d{2}\.\d{2}\.\d{4})?),\s*"
    r"p\.\s*(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<sellers>.+?)\s+cèdent chacun\s+(?P<transferred>[\d']+)\s+de leurs\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+chacun à\s+"
    r"(?P<buyer>[^()]+?)\s*\(et non\s+(?P<previous_published>[\d']+)\s+"
    r"comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_AUTHORIZED_CAPITAL_CLAUSE_REPLACED = re.compile(
    r"^Radiation de la mention relative à l['’]introduction de la clause statutaire "
    r"d['’]augmentation autorisée décidée le\s+"
    r"(?P<removed_date>\d{2}\.\d{2}\.\d{4})\.\s*Par décision du\s+"
    r"(?P<introduced_date>\d{2}\.\d{2}\.\d{4}),\s*l['’]assemblée générale a "
    r"introduit une clause statutaire relative à une augmentation autorisée du "
    r"capital-actions\.\s*Pour les détails,\s*voir les statuts\.?$",
    re.I | re.UNICODE,
)
_FR_MERGER_SAME_SHAREHOLDER_SOCIAL_SHARES = re.compile(
    r"^Fusion:\s*reprise des actifs de CHF\s+(?P<assets>[\d'.]+)\s+et des "
    r"passifs envers les tiers de CHF\s+(?P<liabilities>[\d'.]+)\s+de la "
    r"(?P<absorbed_legal_form>société anonyme)\s+(?P<absorbed_name>.+?),\s*à\s+"
    r"(?P<absorbed_place>[^()]+?)\s*\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"selon contrat de fusion du\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+et "
    r"bilan(?: intermédiaire)? au\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"La société reprenante détenant l['’]ensemble des actions de la société "
    r"transférante,\s*la fusion ne donne pas lieu à une augmentation du capital,\s*"
    r"ni à une attribution de parts sociales\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_EFFECT_SUSPENDED_WITH_SOURCE_DATE = re.compile(
    r"^(?P<authority>La présidente du Tribunal de l['’]arrondissement de .+?)\s+"
    r"a prononcé le\s+(?P<decision_date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4})\s+l['’]effet suspensif de la faillite rendue le\s+"
    r"(?P<bankruptcy_date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_DEBT_OFFSET_CAPITAL_INCREASE = re.compile(
    r"^Bei der ordentlichen Kapitalerhöhung vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+wird eine Forderung in der Höhe von "
    r"CHF\s+(?P<claim>[\d'.]+)\s+verrechnet,\s*wofür\s+"
    r"(?P<count>[\d']+)\s+(?P<share_kind>Namenaktien) zu CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+ausgegeben werden\.?$",
    re.I | re.UNICODE,
)
_FR_MULTI_CLASS_REGISTERED_SHARE_SPLIT = re.compile(
    r"^Division des\s+(?P<from_count>[\d']+)\s+actions ordinaires de CHF\s+"
    r"(?P<from_nominal>[\d'.]+),\s*nominatives,\s*,?\s*en\s+"
    r"(?P<count1>[\d']+)\s+actions de CHF\s+(?P<nominal1>[\d'.]+)\s+ordinaires,\s*"
    r"(?P<count2>[\d']+)\s+actions de CHF\s+(?P<nominal2>[\d'.]+),\s*"
    r"privilégiées quant au droit préférentiel de souscription et au droit de vote\s+et\s+"
    r"(?P<count3>[\d']+)\s+actions de CHF\s+(?P<nominal3>[\d'.]+),\s*"
    r"privilégiées quant au produit de liquidation,\s*toutes nominatives,\s*"
    r"liées selon statuts\.\s*Capital-actions:\s*CHF\s+(?P<total>[\d'.]+),\s*"
    r"libéré à concurrence de CHF\s+(?P<paid>[\d'.]+),\s*divisé en\s+"
    r"(?P<capital_count1>[\d']+)\s+actions de CHF\s+(?P<capital_nominal1>[\d'.]+)\s+"
    r"ordinaires,\s*(?P<capital_count2>[\d']+)\s+actions de CHF\s+"
    r"(?P<capital_nominal2>[\d'.]+),\s*privilégiées quant au droit préférentiel de "
    r"souscription et au droit de vote,\s*et\s+(?P<capital_count3>[\d']+)\s+actions "
    r"de CHF\s+(?P<capital_nominal3>[\d'.]+),\s*privilégiées quant au produit de "
    r"liquidation,\s*toutes nominatives,\s*liées selon statuts\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_GENDER_CORRECTED = re.compile(
    r"^L['’]inscription no\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name>.+?)\s+est\s+(?P<role>directrice)\s*\(et non pas\s+"
    r"(?P<previous_role>directeur)\)\.?$",
    re.I | re.UNICODE,
)
_FR_INDIVIDUAL_SIGNING_SAME_ORIGIN_AND_PLACE = re.compile(
    r"^Signature individuelle est conférée à\s+(?P<name>[^,.;]+),\s*"
    r"du et au\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_PERSON_ORIGIN_CORRECTED_WITH_NOTICE = re.compile(
    r"^Berichtigung der Eintragung Nr\.\s*(?P<entry>[\d']+)\s+vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(SHAB vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\):\s*(?P<name>[^,.;]+),\s*"
    r"(?P<role1>Gesellschafter)\s+und\s+(?P<role2>Geschäftsführer),\s*"
    r"(?P<signing>Einzelunterschrift),\s*von\s+(?P<origin>[^()]+?)\s*"
    r"\(und nicht von\s+(?P<previous_origin>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_IT_ENDOWMENT_CAPITAL_PAID_INCREASED = re.compile(
    r"^Nuovo capitale liberato:\s*CHF\s+(?P<to_paid>[\d'.]+)\s*"
    r"\[finora:\s*CHF\s+(?P<from_paid>[\d'.]+)\]\.\s*Con risoluzioni del "
    r"Consiglio di Stato del\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+è stato "
    r"autorizzato l['’]aumento del capitale di dotazione a CHF\s+"
    r"(?P<authorized_total>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGER_EXACT_NAME_CORRECTED = re.compile(
    r"^L['’]inscription no\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que l['’]associé "
    r"gérant porte le nom exact\s+(?P<name>[^()]+?)\s*\(et non pas\s+"
    r"(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ADMINISTRATOR_ORIGINS_CORRECTED = re.compile(
    r"^Rectification de l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\)\s+est rectifiée dans ce sens que\s+"
    r"(?P<name1>[^,.;]+),\s*(?P<role1>administrateur président),\s*est originaire "
    r"(?:de\s+|d['’])(?P<origin1>[^()]+?)\s*\(et non pas (?:de\s+|d['’])"
    r"(?P<previous_origin1>[^)]+)\)\s+et\s+(?P<name2>[^,.;]+),\s*"
    r"(?P<role2>administrateur),\s*est originaire (?:de\s+|d['’])"
    r"(?P<origin2>[^()]+?)\s*\(et non pas (?:de\s+|d['’])"
    r"(?P<previous_origin2>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_JUDGMENT_SET_ASIDE = re.compile(
    r"^Par décision du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>.+?)\s+a prononcé une restitution du défaut qui a eu pour "
    r"effet de mettre à néant le jugement de faillite\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_ADDRESS_SUPPLEMENTED = re.compile(
    r"^Complément:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée en ce sens que l['’]adresse de la "
    r"société est:\s*(?P<street>.+?),\s*(?P<postal_code>\d{4})\s+"
    r"(?P<locality>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_APPEAL_SUSPENSIVE_BY_ORDER = re.compile(
    r"^Mit Verfügung des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+ist der Beschwerde gegen die "
    r"Verfügung des\s+(?P<court>.+?)\s+vom\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+aufschiebende Wirkung "
    r"zuerkannt worden\.\s*Demnach wird die Eintragung betreffend Auflösung der "
    r"Gesellschaft infolge Konkurses im Handelsregister gestrichen\.\s*"
    r"\[bisher:\s*Mit Verfügung vom\s+(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"hat der\s+(?P<previous_court>.+?)\s+über die Gesellschaft mit Wirkung ab dem\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}[.:]\d{2})\s+Uhr,\s*den Konkurs eröffnet;\s*"
    r"die Gesellschaft ist aufgelöst\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_ADDITIONAL_ADDRESS_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que l['’]autre adresse "
    r"est\s+(?P<address>.+?)\s*\(et non\s+(?P<previous_address>.+?)\s+comme publié\)\.?$",
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


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _french_date(raw: str) -> str:
    day, month, year = raw.lower().replace("1er", "1", 1).split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _amount(raw: str) -> str:
    integer, separator, decimal = raw.rpartition(".")
    if separator and len(decimal) == 2:
        normalized_integer = integer.replace("'", "").replace(".", "")
        return f"{normalized_integer}.{decimal}"
    return raw.replace("'", "").replace(".", "")


def _split_fr_names(raw: str) -> list[str]:
    return [
        name.strip()
        for name in re.split(r",\s*|\s+et\s+", raw)
        if name.strip()
    ]


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


def extract_parser126_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 126."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_FIVE_ASSOCIATES_TRANSFER_CORRECTED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.five_associates_transfer_corrected.v1"
        sellers = _split_fr_names(match.group("sellers"))
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        reference = {
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_dates": [
                _iso_date(value) for value in match.group("notice_dates").split()
            ],
            "notice_ref": match.group("notice_ref"),
            "correction": True,
        }
        for seller in sellers:
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé",
                extra={
                    **reference,
                    "action": "shares_transferred",
                    "counterparty": match.group("buyer").strip(),
                    "previous_shares_count": before,
                    "previously_published_shares_count": _count(
                        match.group("previous_published")
                    ),
                    "shares_transferred": transferred,
                    "shares_count": before - transferred,
                    "share_nominal": match.group("nominal"),
                    "currency": "CHF",
                },
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("buyer"), role="associé",
            extra={
                **reference,
                "action": "shares_received",
                "counterparties": sellers,
                "shares_received": transferred * len(sellers),
                "share_nominal": match.group("nominal"),
                "currency": "CHF",
            },
        ))

    match = _FR_AUTHORIZED_CAPITAL_CLAUSE_REPLACED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.authorized_capital_clause_replaced.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "kind": "authorized_capital_clause", "action": "removed",
                    "decision_date": _iso_date(match.group("removed_date")),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "kind": "authorized_capital_clause", "action": "introduced",
                    "decision_date": _iso_date(match.group("introduced_date")),
                    "capital_kind": "capital-actions", "details_in_statutes": True,
                },
            ),
        ])

    match = _FR_MERGER_SAME_SHAREHOLDER_SOCIAL_SHARES.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "fr.text.merger_same_shareholder_social_shares.v1",
            {
                "kind": "absorption", "assets": match.group("assets"),
                "liabilities": match.group("liabilities"), "currency": "CHF",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_legal_form": match.group("absorbed_legal_form"),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "same_shareholder": True, "capital_increase": False,
                "share_allocation": False, "share_kind": "parts sociales",
            },
        ))

    match = _FR_BANKRUPTCY_EFFECT_SUSPENDED_WITH_SOURCE_DATE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.bankruptcy_effect_suspended_with_source_date.v1",
            {
                "kind": "bankruptcy_effect_suspended",
                "action": "suspended_on_appeal",
                "decision_date": _french_date(match.group("decision_date")),
                "bankruptcy_date": _french_date(match.group("bankruptcy_date")),
                "authority": match.group("authority").strip(),
            },
        ))

    match = _DE_DEBT_OFFSET_CAPITAL_INCREASE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.debt_offset_capital_increase.v1",
            {
                "kind": "ordinary_capital_increase",
                "date": _iso_date(match.group("date")),
                "contribution_kind": "debt_offset", "claim": match.group("claim"),
                "currency": "CHF",
                "issued_shares": [{
                    "count": _count(match.group("count")),
                    "nominal": match.group("nominal"),
                    "kind": match.group("share_kind"),
                }],
            },
        ))

    match = _FR_MULTI_CLASS_REGISTERED_SHARE_SPLIT.search(leftover)
    if match:
        split_classes = [
            {
                "count": _count(match.group("count1")),
                "nominal": match.group("nominal1"),
                "class": "ordinaire",
            },
            {
                "count": _count(match.group("count2")),
                "nominal": match.group("nominal2"),
                "class": "privilégiée",
                "preferences": [
                    "droit préférentiel de souscription", "droit de vote",
                ],
            },
            {
                "count": _count(match.group("count3")),
                "nominal": match.group("nominal3"),
                "class": "privilégiée",
                "preferences": ["produit de liquidation"],
            },
        ]
        capital_classes = [
            (_count(match.group(f"capital_count{index}")),
             match.group(f"capital_nominal{index}"))
            for index in (1, 2, 3)
        ]
        if capital_classes == [
            (item["count"], item["nominal"]) for item in split_classes
        ]:
            consume(match)
            events.append(_event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.multi_class_registered_share_split.v1",
                {
                    "kind": "share_split_and_classes", "currency": "CHF",
                    "split_from": {
                        "count": _count(match.group("from_count")),
                        "nominal": match.group("from_nominal"),
                        "class": "ordinaire", "registered": True,
                    },
                    "split_to": split_classes,
                    "capital_total": match.group("total"),
                    "paid": match.group("paid"),
                    "paid_in_full": match.group("paid") == match.group("total"),
                    "registered": True, "transfer_restricted": True,
                },
            ))

    match = _FR_DIRECTOR_GENDER_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.director_gender_corrected.v1",
            match.group("name"), role=match.group("role"),
            extra={
                "action": "role_label_corrected",
                "previous_role": match.group("previous_role"),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _FR_INDIVIDUAL_SIGNING_SAME_ORIGIN_AND_PLACE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed",
            "fr.persons.individual_signing_same_origin_and_place.v1",
            match.group("name"), place=match.group("place"),
            signing="Einzelunterschrift",
            extra={
                "action": "signing_granted", "heimat": match.group("place").strip(),
            },
        ))

    match = _DE_PERSON_ORIGIN_CORRECTED_WITH_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.origin_corrected_with_notice.v1",
            match.group("name"),
            role=f"{match.group('role1')}; {match.group('role2')}",
            signing=match.group("signing"),
            extra={
                "action": "origin_corrected", "heimat": match.group("origin").strip(),
                "previous_heimat": match.group("previous_origin").strip(),
                "roles": [match.group("role1"), match.group("role2")],
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        ))

    match = _IT_ENDOWMENT_CAPITAL_PAID_INCREASED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "it.text.endowment_capital_paid_increased.v1",
            {
                "kind": "endowment_capital_increase",
                "action": "authorized_and_paid_increased",
                "from_paid": _amount(match.group("from_paid")),
                "to_paid": _amount(match.group("to_paid")),
                "authorized_total": _amount(match.group("authorized_total")),
                "currency": "CHF", "date": _iso_date(match.group("date")),
                "authority": "Consiglio di Stato",
            },
        ))

    match = _FR_ASSOCIATE_MANAGER_EXACT_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_manager_exact_name_corrected.v1",
            match.group("name"), role="associé-gérant",
            extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_TWO_ADMINISTRATOR_ORIGINS_CORRECTED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_administrator_origins_corrected.v1"
        reference = {
            "action": "origin_corrected", "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_id": match.group("notice_id"),
        }
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role=match.group(f"role{index}"),
                extra={
                    **reference,
                    "heimat": match.group(f"origin{index}").strip(),
                    "previous_heimat": match.group(f"previous_origin{index}").strip(),
                },
            ))

    match = _FR_BANKRUPTCY_JUDGMENT_SET_ASIDE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.bankruptcy_judgment_set_aside.v1",
            {
                "kind": "bankruptcy_revoked", "action": "judgment_set_aside",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "reason": "restitution_du_defaut", "previous_status_restored": True,
            },
        ))

    match = _FR_COMPANY_ADDRESS_SUPPLEMENTED.search(leftover)
    if match:
        consume(match)
        street = match.group("street").strip()
        postal_code = match.group("postal_code")
        locality = match.group("locality").strip()
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.company_address_supplemented.v1",
            {
                "kind": "company_address", "action": "supplemented",
                "address": f"{street}, {postal_code} {locality}",
                "street": street, "postal_code": postal_code, "locality": locality,
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _DE_BANKRUPTCY_APPEAL_SUSPENSIVE_BY_ORDER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_appeal_suspensive_by_order.v1",
            {
                "kind": "bankruptcy", "action": "suspended_on_appeal",
                "dissolution_entry_removed": True,
                "decision_date": _iso_date(match.group("decision_date")),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "effective_date": _iso_date(match.group("effective_date")),
                "effective_time": match.group("effective_time").replace(".", ":"),
                "authority": match.group("authority").strip(),
                "court": match.group("court").strip(),
                "previous_court": match.group("previous_court").strip(),
                "previous_decision_date": _iso_date(match.group("previous_date")),
            },
        ))

    match = _FR_ADDITIONAL_ADDRESS_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.additional_address_corrected.v1",
            {
                "kind": "additional_address", "action": "corrected",
                "address": match.group("address").strip(),
                "previous_address": match.group("previous_address").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
