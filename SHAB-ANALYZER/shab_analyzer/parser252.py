from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_BOARD_MEMBER_SIGNING_GRANTED = re.compile(
    r"^Eingetragene Person geändert:\s*(?P<name>[^,;]+),\s*"
    r"(?P<previous_role>Verwaltungsratsmitglied),\s*"
    r"(?P<previous_signing>ohne Unterschrift),\s*neu\s+"
    r"(?P<role>Verwaltungsratsmitglied),\s*"
    r"(?P<signing>Kollektivunterschrift zu zweien)\.?$",
    re.I | re.UNICODE,
)
_DE_DISSOLUTION_LIQUIDATION_BOARD_MEMBER = re.compile(
    r"^Die Gesellschaft ist laut Beschluss der Generalversammlung vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+aufgelöst\.\s*"
    r"Die Liquidation wird unter der Firma:\s*(?P<liquidation_name>.+? in Liquidation)\s+"
    r"durchgeführt\.\s*Eingetragene Person geändert:\s*"
    r"(?P<name>[^,.;]+),\s*(?P<previous_role1>Verwaltungsratsmitglied),\s*"
    r"(?P<previous_role2>Geschäftsführer),\s*"
    r"(?P<previous_signing>Einzelunterschrift),\s*neu\s+"
    r"(?P<role1>Verwaltungsratsmitglied),\s*(?P<role2>Geschäftsführer),\s*"
    r"(?P<liquidator>Liquidator),\s*(?P<signing>Einzelunterschrift)\.?$",
    re.I | re.UNICODE,
)
_DE_PARTICIPATION_CAPITAL_CLAUSES_TREASURY_RIGHTS = re.compile(
    r"^\[gestrichen:\s*Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<authorization_date>\d{2}\.\d{2}\.\d{4})\s+eine genehmigte Erhöhung "
    r"des Partizipationskapitals gemäss näherer Umschreibung in den Statuten "
    r"beschlossen\.\]\.?\s*Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<conditional_date>\d{2}\.\d{2}\.\d{4})\s+eine bedingte Erhöhung "
    r"des Partizipationskapitals gemäss näherer Umschreibung in den Statuten "
    r"eingeführt\.\s*\.?\s*Da die Gesellschaft Beteiligungsrechte an einer Börse "
    r"kotiert hat,\s*ist sie befugt Inhaber-Partizipationsscheine zu halten\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ASSOCIATE_MANAGERS_SHARE_TRANSFERS = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller1>.+?)\s+cède\s+"
    r"(?P<transferred1>[\d']+)\s+de ses\s+(?P<before1>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal1>[\d'.]+)\s+au gérant\s+(?P<buyer1>[^,.;]+),\s*"
    r"nouvel associé\.\s*L['’]associée-gérante\s+(?P<previous_name>[^,.;]+),\s*"
    r"qui se nomme maintenant\s+(?P<seller2>[^,.;]+),\s*cède\s+"
    r"(?P<transferred2>[\d']+)\s+de ses\s+(?P<before2>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal2>[\d'.]+)\s+à l['’]associé-gérant\s+(?P<buyer2>[^,.;]+),\s*"
    r"désormais titulaire de\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*(?P<seller1_again>.+?)\s+et\s+"
    r"(?P<seller2_again>[^,.;]+)\s+restent chacun titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUR_ADMINISTRATORS_APPOINTED_LIQUIDATORS = re.compile(
    r"^Les administrateurs\s+(?P<name1>[^,.;]+),\s*(?P<name2>[^,.;]+),\s*"
    r"(?P<name3>[^,.;]+)\s+et\s+(?P<name4>[^,.;]+)\s+sont élus liquidateurs"
    r"(?:\s+avec signature collective à deux)?\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_DISSOLUTION_TWO_LIQUIDATORS = re.compile(
    r"^Selon décision de l['’](?P<authority>Autorité cantonale de surveillance "
    r"des fondations et des institutions de prévoyance)\s+du\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*la fondation est dissoute\.\s*"
    r"Liquidateurs:\s*les membres du conseil\s+(?P<name1>[^,.;]+)\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*lesquels continuent à signer "
    r"collectivemnent à deux\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_COMMON_SHAREHOLDER_NO_CAPITAL_INCREASE = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di\s+(?P<absorbed_name>.+?)\s+,\s*"
    r"in\s+(?P<absorbed_place>[^()]+?)\s*\(\s*"
    r"(?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\s+\),\s*"
    r"secondo il contratto di fusione del\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+e bilancio al\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta attivi per CHF\s+"
    r"(?P<assets>[\d'.]+)\s+e passivi verso terzi per CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s*\.\s*La totalità del capitale azionario delle "
    r"due società è detenuta dallo stesso azionista,\s*la fusione avviene dunque "
    r"senza aumento di capitale e senza attribuzione di azioni\.?$",
    re.I | re.UNICODE,
)
_FR_ORGANIZATION_TRANSFER_TO_NEW_MANAGER = re.compile(
    r"^(?P<seller>.+?)\s*\((?P<seller_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de et à\s+"
    r"(?P<place>[^,.;]+),\s*nouvelle associée avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"gérante(?:\s+avec\s+(?P<signing>signature collective à deux))?\.?\s*"
    r"(?P<seller_again>.+?)\s*\("
    r"(?P<seller_uid_again>CHE-\d{3}\.\d{3}\.\d{3})\)\s+reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_LIQUIDATOR_AND_SHARE_RESTRICTION = re.compile(
    r"^par\s+(?P<name>[^,.;]+),\s*d['’](?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nommé liquidateur"
    r"(?:\s+avec\s+(?P<signing>signature individuelle))?\.?(?:\s*"
    r"Les\s+(?P<share_count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<share_nominal>[\d'.]+)\s+ne sont plus restreintes quant à la "
    r"transmissibilité selon l['’](?P<legal_basis>art\.\s*685a,\s*al\.\s*3 CO)"
    r")?\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_REOPENED_COURT_WRITTEN_DATE = re.compile(
    r"^Par décision du\s+(?P<authority>Tribunal d['’]arrondissement .+?)\s+du\s+"
    r"(?P<decision_date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"la faillite de la société a été réouverte le\s+"
    r"(?P<bankruptcy_date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4})\s+"
    r"à\s+(?P<hour>\d{1,2})h(?P<minute>\d{2})\.?$",
    re.I | re.UNICODE,
)
_FR_INDIVIDUAL_PROXY_NAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:no|n°|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens "
    r"qu['’]une procuration individuelle a été conférée à\s+"
    r"(?P<name>[^()]+?)\s*\(et non pas\s+(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_COMMITTEE_PRESIDENT_SECRETARY_SWAP = re.compile(
    r"^Les membres du comité\s+(?P<president>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<previous_role1>trésorière),\s*nommée\s+(?P<role1>présidente),\s*"
    r"et\s+(?P<secretary>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<previous_role2>président),\s*nommé\s+(?P<role2>secrétaire),\s*"
    r"continuent à signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_PLACE_AND_INDIVIDUAL_SIGNING_CHANGED = re.compile(
    r"^(?P<name>[^,.;]+),\s*désormais à\s+(?P<place>[^,.;]+),\s*"
    r"signe maintenant individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_STATUTES_ANCILLARY_CLAUSES_ABSENT_CORRECTION = re.compile(
    r"^L['’]inscription\s+(?:no|n°|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que les "
    r"statuts ne comportent pas de clauses relatives à obligation de fournir "
    r"des prestations accessoires,\s*droits de préférence,\s*de préemption "
    r"ou d['’]emption\.?$",
    re.I | re.UNICODE,
)
_DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_PRIOR_CLAUSE = re.compile(
    r"^Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+die Statutenbestimmung über die bedingte "
    r"Kapitalerhöhung vom\s+(?P<clause_date>\d{2}\.\d{2}\.\d{4})\s+geändert\.\s*"
    r"\[gestrichen:\s*Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+die Statutenbestimmung über die "
    r"bedingte Kapitalerhöhung vom\s+"
    r"(?P<previous_clause_date>\d{2}\.\d{2}\.\d{4})\s+geändert\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_DUPLICATE_DOMICILE_NOTICE_CORRECTED = re.compile(
    r"^Mit dem im SHAB Nr\.\s*(?P<issue>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten TR-Eintrag\s+"
    r"(?P<entry>[\d']+)/(?P<entry_year>\d{4})\s+wurde das Domizil irrtümlich "
    r"doppelt vorgenommen\.?$",
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
    day, month, year = raw.casefold().replace("1er", "1", 1).split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", "").replace(".", ""))


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
        role=role.strip() if role else None,
        signing=signing,
        payload={
            "name": clean_name,
            "place": clean_place,
            **({"uid": uid} if uid else {}),
            **(extra or {}),
        },
    )


def extract_parser252_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 252."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_BOARD_MEMBER_SIGNING_GRANTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.board_member_signing_granted.v1",
            match.group("name"), role=match.group("role"),
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "signing_changed",
                "previous_role": match.group("previous_role"),
                "previous_signing": "ohne Unterschrift",
            },
        )], ""

    match = _DE_DISSOLUTION_LIQUIDATION_BOARD_MEMBER.fullmatch(leftover)
    if match:
        rule_id = "de.text.dissolution_liquidation_board_member.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "dissolution", "action": "dissolved",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "liquidation_name": match.group("liquidation_name").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                role="Verwaltungsratsmitglied, Geschäftsführer, Liquidator",
                signing="Einzelunterschrift", extra={
                    "action": "appointed_liquidator",
                    "previous_role": "Verwaltungsratsmitglied, Geschäftsführer",
                    "previous_signing": "Einzelunterschrift",
                },
            ),
        ], ""

    match = _DE_PARTICIPATION_CAPITAL_CLAUSES_TREASURY_RIGHTS.fullmatch(leftover)
    if match:
        rule_id = "de.text.participation_capital_clauses_treasury_rights.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_participation_capital",
                    "action": "clause_removed",
                    "authorization_date": _iso_date(match.group("authorization_date")),
                    "details_in_statutes": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "conditional_participation_capital",
                    "action": "introduced",
                    "decision_date": _iso_date(match.group("conditional_date")),
                    "details_in_statutes": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "treasury_participation_certificates",
                    "action": "holding_authorized",
                    "certificate_type": "bearer",
                    "listed_participation_rights": True,
                },
            ),
        ], ""

    match = _FR_TWO_ASSOCIATE_MANAGERS_SHARE_TRANSFERS.fullmatch(leftover)
    if match:
        transferred1 = _count(match.group("transferred1"))
        transferred2 = _count(match.group("transferred2"))
        before1 = _count(match.group("before1"))
        before2 = _count(match.group("before2"))
        remaining = _count(match.group("remaining"))
        buyer_count = _count(match.group("buyer_count"))
        same_people = (
            match.group("buyer1").strip().casefold()
            == match.group("buyer2").strip().casefold()
            and match.group("seller1").strip().casefold()
            == match.group("seller1_again").strip().casefold()
            and match.group("seller2").strip().casefold()
            == match.group("seller2_again").strip().casefold()
        )
        same_nominal = len({
            match.group("nominal1"), match.group("nominal2"),
            match.group("buyer_nominal"), match.group("remaining_nominal"),
        }) == 1
        if (
            same_people and same_nominal
            and before1 - transferred1 == remaining
            and before2 - transferred2 == remaining
            and transferred1 + transferred2 == buyer_count
        ):
            rule_id = "fr.persons.two_associate_managers_share_transfers.v1"
            buyer = match.group("buyer1").strip()
            common = {
                "currency": "CHF", "share_nominal": match.group("nominal1"),
            }
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("seller1"),
                    role="associé-gérant", extra={
                        "action": "shares_transferred", "counterparty": buyer,
                        "shares_before": before1, "shares_transferred": transferred1,
                        "shares_count": remaining, **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("seller2"),
                    role="associée-gérante", extra={
                        "action": "name_changed_and_shares_transferred",
                        "previous_name": match.group("previous_name").strip(),
                        "counterparty": buyer, "shares_before": before2,
                        "shares_transferred": transferred2,
                        "shares_count": remaining, **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, role="associé-gérant",
                    extra={
                        "action": "appointed_and_shares_received",
                        "new_associate": True,
                        "shares_received": transferred1 + transferred2,
                        "shares_count": buyer_count,
                        "counterparties": [
                            match.group("seller1").strip(),
                            match.group("seller2").strip(),
                        ],
                        **common,
                    },
                ),
            ], ""

    match = _FR_FOUR_ADMINISTRATORS_APPOINTED_LIQUIDATORS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.four_administrators_appointed_liquidators.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="liquidateur", extra={
                    "action": "appointed_liquidator",
                    "previous_role": "administrateur", "group_count": 4,
                },
            )
            for index in range(1, 5)
        ], ""

    match = _FR_FOUNDATION_DISSOLUTION_TWO_LIQUIDATORS.fullmatch(leftover)
    if match:
        rule_id = "fr.text.foundation_dissolution_two_liquidators.v1"
        events = [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", rule_id, {
                "kind": "dissolution", "action": "dissolved",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
            },
        )]
        events.extend(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="membre du conseil, liquidateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_liquidator",
                    "previous_role": "membre du conseil",
                    "signing_continues": True,
                },
            )
            for index in (1, 2)
        )
        return events, ""

    match = _IT_MERGER_COMMON_SHAREHOLDER_NO_CAPITAL_INCREASE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "it.text.merger_common_shareholder_no_capital_increase.v1", {
                "kind": "merger",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "currency": "CHF", "same_shareholder": True,
                "capital_increase": False, "share_allocation": False,
            },
        )], ""

    match = _FR_ORGANIZATION_TRANSFER_TO_NEW_MANAGER.fullmatch(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        before = _count(match.group("before"))
        remaining = _count(match.group("remaining"))
        same_seller = (
            match.group("seller").strip().casefold()
            == match.group("seller_again").strip().casefold()
            and match.group("seller_uid") == match.group("seller_uid_again")
        )
        same_nominal = len({
            match.group("nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }) == 1
        if same_seller and same_nominal and before - transferred == remaining:
            rule_id = "fr.persons.organization_transfer_to_new_manager.v1"
            common = {
                "currency": "CHF", "share_nominal": match.group("nominal"),
            }
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("seller"),
                    uid=match.group("seller_uid"), role="associée", extra={
                        "action": "shares_transferred",
                        "counterparty": match.group("buyer").strip(),
                        "shares_before": before, "shares_transferred": transferred,
                        "shares_count": remaining, **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("buyer"),
                    place=match.group("place"), role="associée-gérante",
                    signing=(
                        "Kollektivunterschrift zu zweien"
                        if match.group("signing") else None
                    ), extra={
                        "action": "appointed_and_shares_received",
                        "new_associate": True,
                        "origin": match.group("place").strip(),
                        "shares_received": _count(match.group("buyer_count")),
                        "shares_count": _count(match.group("buyer_count")),
                        "reported_transfer_total": transferred,
                        "counterparty": match.group("seller").strip(), **common,
                    },
                ),
            ], ""

    match = _FR_LIQUIDATOR_AND_SHARE_RESTRICTION.fullmatch(leftover)
    if match:
        rule_id = "fr.text.liquidator_and_share_restriction.v1"
        events = [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id,
            match.group("name"), place=match.group("place"), role="liquidateur",
            signing="Einzelunterschrift" if match.group("signing") else None,
            extra={
                "action": "appointed_liquidator",
                "origin": match.group("origin").strip(),
            },
        )]
        if match.group("share_count"):
            events.append(_event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id, {
                    "kind": "share_transfer_restriction", "action": "removed",
                    "share_count": _count(match.group("share_count")),
                    "share_nominal": match.group("share_nominal"),
                    "currency": "CHF", "registered": True,
                    "transfer_restricted": False,
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                },
            ))
        return events, ""

    match = _FR_BANKRUPTCY_REOPENED_COURT_WRITTEN_DATE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.bankruptcy_reopened_court_written_date.v1", {
                "kind": "bankruptcy", "action": "reopened",
                "authority": match.group("authority").strip(),
                "decision_date": _french_date(match.group("decision_date")),
                "bankruptcy_date": _french_date(match.group("bankruptcy_date")),
                "bankruptcy_time": (
                    f"{int(match.group('hour')):02d}:{int(match.group('minute')):02d}"
                ),
            },
        )], ""

    match = _FR_INDIVIDUAL_PROXY_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.persons.individual_proxy_name_corrected.v1",
            match.group("name"), signing="Einzelprokura", extra={
                "action": "name_corrected_and_proxy_confirmed",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_COMMITTEE_PRESIDENT_SECRETARY_SWAP.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.committee_president_secretary_swap.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="présidente du comité",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "role_changed",
                    "previous_role": match.group("previous_role1"),
                    "signing_continues": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("secretary"),
                role="secrétaire du comité",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "role_changed",
                    "previous_role": match.group("previous_role2"),
                    "signing_continues": True,
                },
            ),
        ], ""

    match = _FR_PLACE_AND_INDIVIDUAL_SIGNING_CHANGED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.place_and_individual_signing_changed.v1",
            match.group("name"), place=match.group("place"),
            signing="Einzelunterschrift", extra={
                "action": "place_and_signing_changed",
            },
        )], ""

    match = _FR_STATUTES_ANCILLARY_CLAUSES_ABSENT_CORRECTION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.statutes_ancillary_clauses_absent_correction.v1", {
                "kind": "ancillary_obligations_and_share_rights",
                "action": "absence_corrected",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "ancillary_obligations": False,
                "rights": {"preference": False, "preemption": False, "emption": False},
            },
        )], ""

    match = _DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_PRIOR_CLAUSE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.conditional_capital_clause_changed_prior_clause.v1", {
                "kind": "conditional_capital_clause", "action": "changed",
                "date": _iso_date(match.group("date")),
                "clause_date": _iso_date(match.group("clause_date")),
                "previous_date": _iso_date(match.group("previous_date")),
                "previous_clause_date": _iso_date(match.group("previous_clause_date")),
                "previous_clause_removed": True,
            },
        )], ""

    match = _DE_DUPLICATE_DOMICILE_NOTICE_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.duplicate_domicile_notice_corrected.v1", {
                "kind": "registered_address", "action": "duplicate_entry_corrected",
                "entry": match.group("entry"),
                "entry_year": int(match.group("entry_year")),
                "notice_issue": int(match.group("issue")),
                "notice_date": _iso_date(match.group("notice_date")),
            },
        )], ""

    return [], leftover
