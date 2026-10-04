from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_ADMINISTRATION_FOUR_INDIVIDUAL = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*maintenant domicilié(?:e)? à\s*"
    r"(?P<president_place>[^,.;]+),\s*(?P<president_country>[A-Z]{1,3}),\s*"
    r"nommé(?:e)? président(?:e)?,\s*(?P<member2>[^,.;]+),\s*de et à\s*"
    r"(?P<place2>[^,.;]+),\s*(?P<member3>[^,.;]+),\s*"
    r"d['’](?P<origin3>[^,.;]+),\s*à\s*(?P<place3>[^,.;]+),\s*"
    r"(?P<country3>[A-Z]{1,3}),\s*et\s*(?P<member4>[^,.;]+),\s*"
    r"d['’](?P<origin4>[^,.;]+),\s*à\s*(?P<place4>[^,.;]+),\s*"
    r"(?P<country4>[A-Z]{1,3}),\s*lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_PROXY_CORRECTED_COLLECTIVE_RESTRICTED = re.compile(
    r"^L['’]inscription\s+(?:N[o°]|n[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),?\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens qu['’]une "
    r"procuration collective à deux,\s*avec un administrateur,\s*un membre du "
    r"comité de direction ou le directeur général a été conférée à\s*"
    r"(?P<name>[^,.;()]+)\s*\(et non pas une procuration individuelle\)\.?$",
    re.I | re.UNICODE,
)
_FR_PAID_CAPITAL_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:N[o°]|n[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*(?:p\.\s*)?"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée comme suit\s*:\s*"
    r"le capital-actions est libéré à concurrence de CHF\s+(?P<paid>[\d'.]+)\s*"
    r"\(et non entièrement libéré\)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGERS_PRESIDENCY_CHANGED_SINGULAR = re.compile(
    r"^L['’]associé-gérant\s+(?P<new_president>[^,.;]+),\s*nommé président et "
    r"l['’]associé-gérant\s+(?P<previous_president>[^,.;]+),\s*"
    r"jusqu['’]ici président,\s*continuent à signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_DE_COMPOSITION_AGREEMENT_CONFIRMED_PASSIVE = re.compile(
    r"^Mit Verfügung des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+wurde der Nachlassvertrag mit\s+"
    r"(?P<agreement_type>Dividendenvergleich)\s+bestätigt\.?$",
    re.I | re.UNICODE,
)
_FR_LIQUIDATION_ADDRESS = re.compile(
    r"^Domicile de liquidation:\s*(?P<street>.+?)\s+"
    r"(?P<street_number>\d+[A-Za-z]?),\s*c/o\s+(?P<care_of>.+?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<locality>[^.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_REINSTATEMENT_BANKRUPTCY_REOPENED_FIRST_DAY = re.compile(
    r"^La société est réinscrite au registre du commerce conformément à la décision "
    r"du\s+(?P<authority>.+?)\s+du\s+"
    r"(?P<decision_date>\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4})\s+prononçant la réouverture de la faillite le\s+"
    r"(?P<bankruptcy_date>\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4}),\s*à\s*(?P<time>\d{1,2}h\d{2})\.?$",
    re.I | re.UNICODE,
)
_MIXED_FULL_ADDRESS_BOARD_CHANGES = re.compile(
    r"^Vollständige Adresse:\s*(?P<street>.+?)\s+(?P<house_number>\d+[A-Za-z]?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<locality>[^.]+)\.\s*Gelöschte Person:\s*"
    r"(?P<removed_name>[^,.;]+),\s*(?P<removed_roles>Verwaltungsratsmitglied,\s*"
    r"Präsident),\s*(?P<removed_signing>Einzelunterschrift)\.\s*"
    r"Eingetragene Person geändert:\s*(?P<changed_name>[^,.;]+),\s*"
    r"(?P<previous_role>Verwaltungsratsmitglied),\s*"
    r"(?P<previous_signing>Einzelunterschrift),\s*neu\s*"
    r"(?P<changed_roles>Verwaltungsratsmitglied,\s*Präsident),\s*"
    r"(?P<changed_signing>Einzelunterschrift),\s*Neu eingetragene Person:\s*"
    r"(?P<new_name>[^,.;]+),\s*von und in\s+(?P<new_place>[^,.;]+),\s*"
    r"(?P<new_roles>Verwaltungsratsmitglied,\s*Sekretär),\s*"
    r"(?P<new_signing>Einzelunterschrift)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ADMINISTRATORS_APPOINTED = re.compile(
    r"^(?P<name1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+)\s+sont nommés "
    r"administrateurs et continuent de signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_EXPIRED_AUTHORIZATION_RESOLUTION = re.compile(
    r"^\[Streichung der Statutenbestimmung über die mit Ermächtigungsbeschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+eingeführte genehmigte Kapitalerhöhung "
    r"infolge Ablaufs der zeitlichen Befristung\.\]\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_FREE_EQUITY_WITHOUT_DEFICIT_AMOUNT = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di\s+(?P<absorbed_name>.+?),\s*"
    r"in\s+(?P<absorbed_place>[^()]+?)\s*"
    r"\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"secondo (?:il\s+)?contratto di fusione del\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+e bilancio al\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta attivi per CHF\s+"
    r"(?P<assets>[\d'.]+),?\s+e passivi verso terzi per CHF\s+"
    r"(?P<liabilities>[\d'.]+)\.\s*Conformemente all['’]attestazione di un "
    r"perito revisore abilitato,\s*la società assuntrice dispone di fondi propri "
    r"liberamente disponibili equivalenti almeno all['’]ammontare dello scoperto "
    r"della società trasferente\.\s*La società assuntrice detiene tutte le azioni "
    r"della società trasferente,\s*per cui la fusione avviene senza aumento di "
    r"capitale e senza attribuzione di azioni\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_NAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:N[o°]|n[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que "
    r"l['’]un des administrateurs porte le nom de\s+(?P<name>[^()]+?)\s*"
    r"\(et non pas\s+(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_SPLIT_TRANSFER_TWO_EXISTING = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+par\s+(?P<buyer1_received>[\d']+)\s+à "
    r"l['’]associé-gérant\s+(?P<buyer1>[^,.;]+),\s*désormais à\s+"
    r"(?P<buyer1_place>[^,.;]+)\s+et titulaire de\s+"
    r"(?P<buyer1_count>[\d']+)\s+parts de CHF\s+(?P<buyer1_nominal>[\d'.]+),\s*"
    r"et par\s+(?P<buyer2_received>[\d']+)\s+à l['’]associé-gérant\s+"
    r"(?P<buyer2>[^,.;]+),\s*désormais titulaire de\s+"
    r"(?P<buyer2_count>[\d']+)\s+parts de CHF\s+(?P<buyer2_nominal>[\d'.]+)\.\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_NAME_CORRECTED_WITH_FOSC_COMMA = re.compile(
    r"^L['’]inscription\s+(?:N[o°]|n[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<previous_name>.+?)\s+porte en réalité le nom de\s+"
    r"(?P<name>[^.]+?)\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_ROLE_CORRECTED_PARENTHESES = re.compile(
    r"^L['’]inscription\s+(?:N[o°]|n[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+est en réalité\s+(?P<role>directeur adjoint)\s*"
    r"\(et non pas\s+(?P<previous_role>directeur)\)\.?$",
    re.I | re.UNICODE,
)
_DE_SHARE_RESTRICTION_TAIL_ORGANIZATIONAL_DISSOLUTION = re.compile(
    r"^(?P<restriction_basis>685a Abs\. 3 OR) aufgehoben\.\s*"
    r"Über die Rechtseinheit ist mit Entscheid der\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+infolge Mängel in der "
    r"Organisation der Rechtseinheit in Anwendung von\s+"
    r"(?P<dissolution_basis>Art\.\s*939 OR)\s+die Auflösung und die Liquidation "
    r"nach den Vorschriften über den Konkurs angeordnet worden\.?$",
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
    day, month, year = raw.lower().split()
    day = re.sub(r"er$", "", day)
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


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


def extract_parser167_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 167."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()
    events: list[Event] = []

    match = _FR_ADMINISTRATION_FOUR_INDIVIDUAL.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administration_four_individual.v1"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("president"),
            place=match.group("president_place"), role="président",
            signing="Einzelunterschrift", extra={
                "action": "appointed_president",
                "country": match.group("president_country"),
                "domicile_changed": True,
            },
        ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("member2"),
            place=match.group("place2"), role="administrateur",
            signing="Einzelunterschrift", extra={
                "action": "appointed", "origin": match.group("place2").strip(),
            },
        ))
        for index in (3, 4):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"member{index}"),
                place=match.group(f"place{index}"), role="administrateur",
                signing="Einzelunterschrift", extra={
                    "action": "appointed",
                    "origin": match.group(f"origin{index}").strip(),
                    "country": match.group(f"country{index}"),
                },
            ))
        return events, ""

    match = _FR_PROXY_CORRECTED_COLLECTIVE_RESTRICTED.fullmatch(leftover)
    if match:
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.restricted_proxy_corrected.v1",
            match.group("name"), role="fondé de procuration",
            signing="Kollektivprokura zu zweien", extra={
                "action": "signing_corrected",
                "previous_signing": "Einzelprokura",
                "co_signs_with_roles": [
                    "administrateur", "membre du comité de direction",
                    "directeur général",
                ],
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))
        return events, ""

    match = _FR_PAID_CAPITAL_CORRECTED.fullmatch(leftover)
    if match:
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.paid_capital_corrected.v1",
            {
                "kind": "paid_capital", "action": "corrected", "currency": "CHF",
                "paid": match.group("paid"), "paid_in_full": False,
                "previous_paid_in_full": True, "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))
        return events, ""

    match = _FR_ASSOCIATE_MANAGERS_PRESIDENCY_CHANGED_SINGULAR.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.associate_managers_presidency_changed.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("new_president"),
                role="associé-gérant président",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_president", "signing_continues": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("previous_president"),
                role="associé-gérant", signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "presidency_ended", "previous_role": "président",
                    "signing_continues": True,
                },
            ),
        ])
        return events, ""

    match = _DE_COMPOSITION_AGREEMENT_CONFIRMED_PASSIVE.fullmatch(leftover)
    if match:
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.composition_agreement_confirmed_passive.v1",
            {
                "kind": "composition_agreement_confirmed",
                "decision_date": _iso_date(match.group("date")),
                "authority": match.group("authority").strip(),
                "agreement_type": match.group("agreement_type"),
            },
        ))
        return events, ""

    match = _FR_LIQUIDATION_ADDRESS.fullmatch(leftover)
    if match:
        address = (
            f"{match.group('street').strip()} {match.group('street_number')}, "
            f"c/o {match.group('care_of').strip()}, "
            f"{match.group('postal_code')} {match.group('locality').strip()}"
        )
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.liquidation_address_standalone.v1",
            {
                "kind": "liquidation_address", "action": "changed", "to": address,
                "street": match.group("street").strip(),
                "street_number": match.group("street_number"),
                "care_of": match.group("care_of").strip(),
                "postal_code": match.group("postal_code"),
                "locality": match.group("locality").strip(),
            },
        ))
        return events, ""

    match = _FR_REINSTATEMENT_BANKRUPTCY_REOPENED_FIRST_DAY.fullmatch(leftover)
    if match:
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.reinstatement_bankruptcy_reopened_first_day.v1",
            {
                "kind": "company_reinstated", "action": "reinstated",
                "reason": "bankruptcy_reopened",
                "authority": match.group("authority").strip(),
                "decision_date": _french_date(match.group("decision_date")),
                "bankruptcy_date": _french_date(match.group("bankruptcy_date")),
                "bankruptcy_time": match.group("time").replace("h", ":"),
            },
        ))
        return events, ""

    match = _MIXED_FULL_ADDRESS_BOARD_CHANGES.fullmatch(leftover)
    if match:
        rule_id = "mixed.persons.full_address_board_changes.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", rule_id,
                {
                    "action": "set", "complete": True,
                    "street": match.group("street").strip(),
                    "house_number": match.group("house_number"),
                    "postal_code": match.group("postal_code"),
                    "locality": match.group("locality").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group("removed_name"),
                role=match.group("removed_roles"),
                signing=match.group("removed_signing"), extra={"action": "removed"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("changed_name"),
                role=match.group("changed_roles"), signing=match.group("changed_signing"),
                extra={
                    "action": "role_changed",
                    "previous_role": match.group("previous_role"),
                    "previous_signing": match.group("previous_signing"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("new_name"),
                place=match.group("new_place"), role=match.group("new_roles"),
                signing=match.group("new_signing"), extra={
                    "action": "appointed", "origin": match.group("new_place").strip(),
                },
            ),
        ])
        return events, ""

    match = _FR_TWO_ADMINISTRATORS_APPOINTED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_administrators_appointed_continuing_signing.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="administrateur", signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed", "signing_continues": True},
            ))
        return events, ""

    match = _DE_AUTHORIZED_CAPITAL_EXPIRED_AUTHORIZATION_RESOLUTION.fullmatch(leftover)
    if match:
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_expired_authorization.v1",
            {
                "kind": "authorized_capital_clause", "action": "removed",
                "authorization_date": _iso_date(match.group("date")),
                "reason": "authorization_expired",
            },
        ))
        return events, ""

    match = _IT_MERGER_FREE_EQUITY_WITHOUT_DEFICIT_AMOUNT.fullmatch(leftover)
    if match:
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "it.text.merger_free_equity_without_deficit_amount.v1",
            {
                "kind": "absorption",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "currency": "CHF", "deficit_coverage": "freely_available_equity",
                "deficit_coverage_confirmed_by_auditor": True,
                "all_shares_held_by_acquirer": True,
                "capital_increase": False, "share_allocation": False,
            },
        ))
        return events, ""

    match = _FR_ADMINISTRATOR_NAME_CORRECTED.fullmatch(leftover)
    if match:
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_name_corrected_one_of.v1",
            match.group("name"), role="administrateur", extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))
        return events, ""

    match = _FR_MANAGER_SPLIT_TRANSFER_TWO_EXISTING.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.manager_split_transfer_two_existing.v1"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("seller"),
            role="associé-gérant", extra={
                "action": "shares_transferred", "currency": "CHF",
                "shares_before": _count(match.group("before")),
                "shares_transferred": _count(match.group("transferred")),
                "shares_count": _count(match.group("seller_count")),
                "share_nominal": match.group("seller_nominal"),
                "counterparties": [
                    match.group("buyer1").strip(), match.group("buyer2").strip(),
                ],
            },
        ))
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"buyer{index}"),
                place=(match.group("buyer1_place") if index == 1 else None),
                role="associé-gérant", extra={
                    "action": "shares_received", "currency": "CHF",
                    "shares_received": _count(match.group(f"buyer{index}_received")),
                    "shares_count": _count(match.group(f"buyer{index}_count")),
                    "share_nominal": match.group(f"buyer{index}_nominal"),
                    "counterparty": match.group("seller").strip(),
                },
            ))
        return events, ""

    match = _FR_PERSON_NAME_CORRECTED_WITH_FOSC_COMMA.fullmatch(leftover)
    if match:
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.name_corrected_fosc_comma.v1",
            match.group("name"), extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))
        return events, ""

    match = _FR_DIRECTOR_ROLE_CORRECTED_PARENTHESES.fullmatch(leftover)
    if match:
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.director_role_corrected_parentheses.v1",
            match.group("name"), role=match.group("role").lower(), extra={
                "action": "role_corrected",
                "previous_role": match.group("previous_role").lower(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))
        return events, ""

    match = _DE_SHARE_RESTRICTION_TAIL_ORGANIZATIONAL_DISSOLUTION.fullmatch(leftover)
    if match:
        rule_id = "de.text.share_restriction_tail_organizational_dissolution.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id,
                {
                    "kind": "share_transfer_restriction", "action": "removed",
                    "legal_basis": f"Art. {match.group('restriction_basis')}",
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id,
                {
                    "kind": "dissolution", "action": "dissolved_and_liquidated",
                    "reason": "organization_deficiencies",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "authority": match.group("authority").strip(),
                    "legal_basis": re.sub(
                        r"\s+", " ", match.group("dissolution_basis")
                    ).strip(),
                    "liquidation_procedure": "bankruptcy",
                },
            ),
        ])
        return events, ""

    return [], text
