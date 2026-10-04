from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_DE_TWO_OFFICERS_REMOVED = re.compile(
    r"^Ausgeschiedene Personen und erloschene Unterschriften:\s*"
    r"(?P<surname1>[^,;]+),\s*(?P<given1>[^,;]+),\s*von\s+"
    r"(?P<origin1>[^,;]+),\s*in\s+(?P<place1>[^,;]+),\s*mit\s+"
    r"(?P<signing1>Kollektivunterschrift zu zweien);\s*"
    r"(?P<surname2>[^,;]+),\s*(?P<given2>[^,;]+),\s*genannt\s+"
    r"(?P<alias2>[^,;]+),\s*von\s+(?P<origin2>[^,;]+),\s*in\s+"
    r"(?P<place2>[^,;]+),\s*mit\s+"
    r"(?P<signing2>Kollektivunterschrift zu zweien)\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_NEW_ASSOCIATES_MIXED_SIGNING = re.compile(
    r"^Nouveaux associés:\s*(?P<name1>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*avec signature individuelle,\s*"
    r"(?P<name2>[^,.;]+),\s*de et à\s+(?P<place2>[^,.;]+)\s+et\s+"
    r"(?P<name3>[^,.;]+),\s*de\s+(?P<origin3>[^,.;]+),\s*à\s+"
    r"(?P<place3>[^,();]+)\s*\((?P<country3>[^)]+)\),\s*"
    r"tous deux sans signature\.?$",
    re.I | re.UNICODE,
)
_DE_DOCUMENT_LIST_SUPPLEMENT = re.compile(
    r"^Nachtrag Liste der Belege\.?$", re.I | re.UNICODE
)
_FR_ADMINISTRATION_THREE_ROLE_CHANGES = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<president_previous_role>[^,.;]+),\s*nommé président,\s*"
    r"(?P<previous_president>[^,.;]+),\s*jusqu['’]ici président,\s*et\s+"
    r"(?P<member>[^,.;]+),\s*de\s+(?P<member_origin>[^,.;]+),\s*à\s+"
    r"(?P<member_place>[^,.;]+),\s*lesquels signent collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_DE_CAPITAL_REDUCTION_AND_RESTORATION = re.compile(
    r"^Bei der Kapitalherabsetzung vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"wird das Aktienkapital von CHF\s+(?P<from_total>[\d'.]+)\s+durch "
    r"Vernichtung von\s+(?P<destroyed>[\d']+)\s+Namenaktien zu CHF\s+"
    r"(?P<destroyed_nominal>[\d'.]+)\s+um CHF\s+(?P<reduction>[\d'.]+)\s+"
    r"auf CHF\s+(?P<reduced_total>[\d'.]+)\s+herabgesetzt\.\s*"
    r"Gleichzeitig wird das Aktienkapital um CHF\s+(?P<increase>[\d'.]+)\s+"
    r"auf CHF\s+(?P<to_total>[\d'.]+)\s+durch Ausgabe von\s+"
    r"(?P<issued>[\d']+)\s+Namenaktien zu CHF\s+"
    r"(?P<issued_nominal>[\d'.]+)\s+ordentlich erhöht\.?$",
    re.I | re.UNICODE,
)
_FR_LIQUIDATOR_AND_TRANSFER_RESTRICTION_REMOVED = re.compile(
    r"^L['’]administratrice\s+(?P<name>[^,.;]+),\s*désormais à\s+"
    r"(?P<place>[^,.;]+),\s*est nommé(?:e)? liquidatrice\s+avec signature "
    r"individuelle\.\s*Les\s+(?P<count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+formant l['’]entier du capital-actions ne sont "
    r"plus restreintes quant à la transmissibilité\s*"
    r"\((?P<legal_basis>art\.\s*685a,\s*al\.\s*3 CO)\)\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_GENERAL_PARTNER_DE_ET_A = re.compile(
    r"^Nouvel associé indéfiniment responsable\s*:\s*"
    r"(?P<name>[^,.;]+),\s*de et à\s+(?P<place>[^,.;]+),\s*"
    r"avec signature individuelle\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_TRANSFER_TO_SAME_MANAGER = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller1>[^,.;]+)\s+détient\s+"
    r"(?P<remaining1>[\d']+)\s+parts de CHF\s+(?P<nominal1>[\d'.]+)\s+"
    r"par suite de cessions de\s+(?P<transferred1>[\d']+)\s+parts de CHF\s+"
    r"(?P<transfer_nominal1>[\d'.]+)\s+à l['’]associé-gérant\s+"
    r"(?P<buyer>[^,.;]+)\.\s*L['’]associé-gérant\s+"
    r"(?P<seller2>[^,.;]+)\s+détient\s+(?P<remaining2>[\d']+)\s+parts de "
    r"CHF\s+(?P<nominal2>[\d'.]+)\s+par suite de cessions de\s+"
    r"(?P<transferred2>[\d']+)\s+parts de CHF\s+"
    r"(?P<transfer_nominal2>[\d'.]+)\s+à l['’]associé-gérant\s+"
    r"(?P=buyer)\.\s*Ce dernier possède désormais\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_IT_STATUTES_DATE_CORRECTED_VERBOSE = re.compile(
    r"^Data corretta dello statuto:\s*(?P<date>\d{2}\.\d{2}\.\d{4})\s*"
    r"\[non come erroneamente indicato:\s*"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\]\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_CLAUSE_EXPIRED_WITH_HISTORY = re.compile(
    r"^\[Streichung der Statutenbestimmung über die mit Ermächtigungsbeschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+eingeführte genehmigte "
    r"Kapitalerhöhung infolge Zeitablaufs\.\]\s*"
    r"\[gestrichen:\s*(?P<previous>Die Gesellschaft hat bei der Gründung vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+eine genehmigte "
    r"Kapitalerhöhung gemäss näherer Umschreibung in den Statuten beschlossen\.)\]\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_CORRECTED_WITH_NOTICE_TYPO = re.compile(
    r"^L['’]inscription\s+(?:n[o°]\s*)?(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est réctifiée en ce sens qu['’]"
    r"(?P<name>[^,.;]+)\s+signe collectivement à deux\s*"
    r"\(et non pas individuellement\)\.?$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_REPLACED = re.compile(
    r"^\[gestrichen:\s*Mit Entscheid vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<previous_authority>.+?)\s+die mit Entscheid vom\s+"
    r"(?P<grant_date>\d{2}\.\d{2}\.\d{4})\s+gewährte definitive "
    r"Nachlassstundung bis\s+(?P<previous_until>\d{2}\.\d{2}\.\d{4})\s+"
    r"verlängert\.\]\.?\s*Mit Entscheid vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+die mit Entscheid vom\s+"
    r"(?P<current_grant_date>\d{2}\.\d{2}\.\d{4})\s+gewährte definitive "
    r"Nachlassstundung bis\s+(?P<until>\d{2}\.\d{2}\.\d{4})\s+verlängert\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_NEW_EXECUTIVE_COMMITTEE_MEMBERS = re.compile(
    r"^Nouveaux membres du comité directeur avec signature collective à deux:\s*"
    r"(?P<name1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*et\s+(?P<name2>[^,.;]+),\s*de\s+"
    r"(?P<origin2>[^,.;]+),\s*au\s+(?P<place2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_DISSOLUTION_LIQUIDATOR_AND_ADDRESS_VARIANT = re.compile(
    r"^Die Gesellschaft ist laut Beschluss der Generalversammlung vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+aufgelöst\.\s*Die Liquidation wird "
    r"unter der Firma:\s*(?P<liquidation_name>.+?)\s+aufgelöst\.\s*"
    r"Eingetragene Person geändert:\s*(?P<name>[^,.;]+),\s*"
    r"(?P<previous_role>Verwaltungsratsmitglied,\s*Präsident),\s*"
    r"(?P<previous_signing>Einzelunterschrift),\s*neu\s+"
    r"(?P<role>Verwaltungsratsmitglied,\s*Präsident,\s*Liquidator),\s*"
    r"(?P<signing>Einzelunterschrift),\s*von\s+(?P<origin>[^.;]+)\.\s*"
    r"Liquidationsadresse:\s*(?P<address>.+?)\.?$",
    re.I | re.UNICODE,
)
_DE_DELETION_PROCEDURE_BLOCKED_FEDERAL_TAX_DATE_NOTICE = re.compile(
    r"^Auf die durch das Handelsregisteramt gestützt auf\s+"
    r"(?P<legal_basis>Art\.\s*934 Abs\.\s*2 OR sowie Art\.\s*152 Abs\.\s*1 HRegV)\s+"
    r"veranlasste und im SHAB mit Meldungsnummer\s+"
    r"(?P<notice>\d{2}\.\d{2}\.\d{4})\s+publizierte Aufforderung haben sich "
    r"keine weiteren Betroffenen gemeldet\.\s*Das amtliche Verfahren zur "
    r"Löschung der Rechtseinheit ist damit abgeschlossen\.\s*Sie kann mangels "
    r"Zustimmung der Eidgenössischen Steuerverwaltung jedoch noch nicht gelöscht "
    r"werden\.?$",
    re.I | re.UNICODE,
)


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


def extract_parser199_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 199."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_TWO_OFFICERS_REMOVED.fullmatch(leftover)
    if match:
        rule_id = "de.persons.two_officers_removed_with_alias.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id,
                f"{match.group('surname1')}, {match.group('given1')}",
                place=match.group("place1"), signing=match.group("signing1"),
                extra={"action": "removed", "origin": match.group("origin1").strip()},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id,
                f"{match.group('surname2')}, {match.group('given2')}",
                place=match.group("place2"), signing=match.group("signing2"),
                extra={
                    "action": "removed", "origin": match.group("origin2").strip(),
                    "alias": match.group("alias2").strip(),
                },
            ),
        ], ""

    match = _FR_THREE_NEW_ASSOCIATES_MIXED_SIGNING.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.three_new_associates_mixed_signing.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="associé",
                signing="Einzelunterschrift", extra={
                    "action": "appointed", "origin": match.group("origin1").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="associé", extra={
                    "action": "appointed", "origin": match.group("place2").strip(),
                    "without_signature": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name3"),
                place=match.group("place3"), role="associé", extra={
                    "action": "appointed", "origin": match.group("origin3").strip(),
                    "country": match.group("country3").strip(),
                    "without_signature": True,
                },
            ),
        ], ""

    match = _DE_DOCUMENT_LIST_SUPPLEMENT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.document_list_supplement_short.v1",
            {"kind": "documents_updated", "action": "supplemented"},
        )], ""

    match = _FR_ADMINISTRATION_THREE_ROLE_CHANGES.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administration_three_role_changes.v1"
        signing = "Kollektivunterschrift zu zweien"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président", signing=signing, extra={
                    "action": "appointed_president",
                    "previous_role": match.group("president_previous_role").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("previous_president"),
                signing=signing, extra={
                    "action": "presidency_ended", "previous_role": "président",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                place=match.group("member_place"),
                role="membre du conseil d'administration", signing=signing,
                extra={
                    "action": "appointed",
                    "origin": match.group("member_origin").strip(),
                },
            ),
        ], ""

    match = _DE_CAPITAL_REDUCTION_AND_RESTORATION.fullmatch(leftover)
    if match:
        from_total = _amount(match.group("from_total"))
        reduction = _amount(match.group("reduction"))
        reduced_total = _amount(match.group("reduced_total"))
        increase = _amount(match.group("increase"))
        to_total = _amount(match.group("to_total"))
        destroyed_value = _count(match.group("destroyed")) * _amount(
            match.group("destroyed_nominal")
        )
        issued_value = _count(match.group("issued")) * _amount(
            match.group("issued_nominal")
        )
        if (
            from_total - reduction == reduced_total
            and reduced_total + increase == to_total
            and destroyed_value == reduction
            and issued_value == increase
        ):
            return [_event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.capital_reduction_and_restoration.v1",
                {
                    "kind": "reduction_and_ordinary_increase",
                    "date": _iso_date(match.group("date")), "currency": "CHF",
                    "from": match.group("from_total"),
                    "reduced_to": match.group("reduced_total"),
                    "to": match.group("to_total"),
                    "reduction": match.group("reduction"),
                    "increase": match.group("increase"),
                    "destroyed_count": _count(match.group("destroyed")),
                    "destroyed_nominal": match.group("destroyed_nominal"),
                    "issued_count": _count(match.group("issued")),
                    "issued_nominal": match.group("issued_nominal"),
                    "share_kind": "Namenaktien",
                },
            )], ""

    match = _FR_LIQUIDATOR_AND_TRANSFER_RESTRICTION_REMOVED.fullmatch(leftover)
    if match:
        rule_id = "fr.text.liquidator_and_transfer_restriction_removed.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), role="administratrice, liquidatrice",
                signing="Einzelunterschrift", extra={
                    "action": "appointed_liquidator",
                    "previous_role": "administratrice",
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "share_transfer_restriction", "action": "removed",
                    "shares_count": _count(match.group("count")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                    "share_kind": "actions nominatives",
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                },
            ),
        ], ""

    match = _FR_NEW_GENERAL_PARTNER_DE_ET_A.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.general_partner_de_et_a.v1",
            match.group("name"), place=match.group("place"),
            role="associé indéfiniment responsable", signing="Einzelunterschrift",
            extra={
                "action": "appointed", "origin": match.group("place").strip(),
            },
        )], ""

    match = _FR_TWO_MANAGERS_TRANSFER_TO_SAME_MANAGER.fullmatch(leftover)
    if match:
        nominals = {
            match.group("nominal1"), match.group("transfer_nominal1"),
            match.group("nominal2"), match.group("transfer_nominal2"),
            match.group("buyer_nominal"),
        }
        transferred1 = _count(match.group("transferred1"))
        transferred2 = _count(match.group("transferred2"))
        buyer_count = _count(match.group("buyer_count"))
        if len(nominals) == 1 and buyer_count >= transferred1 + transferred2:
            rule_id = "fr.persons.two_managers_transfer_to_same_manager.v1"
            common = {
                "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
            }
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("seller1"),
                    role="associé-gérant", extra={
                        "action": "shares_transferred",
                        "shares_transferred": transferred1,
                        "shares_count": _count(match.group("remaining1")),
                        "counterparty": match.group("buyer").strip(), **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("seller2"),
                    role="associé-gérant", extra={
                        "action": "shares_transferred",
                        "shares_transferred": transferred2,
                        "shares_count": _count(match.group("remaining2")),
                        "counterparty": match.group("buyer").strip(), **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("buyer"),
                    role="associé-gérant", extra={
                        "action": "shares_received",
                        "shares_received": transferred1 + transferred2,
                        "shares_before": buyer_count - transferred1 - transferred2,
                        "shares_count": buyer_count, **common,
                    },
                ),
            ], ""

    match = _IT_STATUTES_DATE_CORRECTED_VERBOSE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "it.text.statutes_date_corrected_verbose.v1",
            {
                "kind": "statutes_date", "action": "corrected",
                "date": _iso_date(match.group("date")),
                "previous_published_date": _iso_date(match.group("previous_date")),
            },
        )], ""

    match = _DE_AUTHORIZED_CAPITAL_CLAUSE_EXPIRED_WITH_HISTORY.fullmatch(leftover)
    if match and match.group("date") == match.group("previous_date"):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_clause_expired_history.v1",
            {
                "kind": "authorized_capital_clause", "action": "removed",
                "authorization_date": _iso_date(match.group("date")),
                "reason": "authorization_period_elapsed",
                "previous": match.group("previous").strip(),
            },
        )], ""

    match = _FR_SIGNING_CORRECTED_WITH_NOTICE_TYPO.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.signing_corrected_notice_typo.v1",
            match.group("name"), signing="Kollektivunterschrift zu zweien", extra={
                "action": "signing_corrected",
                "previous_signing": "Einzelunterschrift",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
                "source_wording": "réctifiée",
            },
        )], ""

    match = _DE_DEFINITIVE_MORATORIUM_REPLACED.fullmatch(leftover)
    if match and (
        match.group("previous_authority").strip().casefold()
        == match.group("authority").strip().casefold()
        and match.group("grant_date") == match.group("current_grant_date")
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.definitive_moratorium_replaced.v1", {
                "kind": "definitive_moratorium_extended",
                "decision_date": _iso_date(match.group("decision_date")),
                "until": _iso_date(match.group("until")),
                "authority": match.group("authority").strip(),
                "grant_date": _iso_date(match.group("grant_date")),
                "previous_decision_date": _iso_date(
                    match.group("previous_decision_date")
                ),
                "previous_until": _iso_date(match.group("previous_until")),
                "previous_entry_removed": True,
            },
        )], ""

    match = _FR_TWO_NEW_EXECUTIVE_COMMITTEE_MEMBERS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_new_executive_committee_members.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role="membre du comité directeur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed",
                    "origin": match.group(f"origin{index}").strip(),
                },
            )
            for index in (1, 2)
        ], ""

    match = _DE_DISSOLUTION_LIQUIDATOR_AND_ADDRESS_VARIANT.fullmatch(leftover)
    if match:
        rule_id = "de.text.dissolution_liquidator_address_variant.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "dissolution", "action": "dissolved",
                    "authority": "Generalversammlung",
                    "decision_date": _iso_date(match.group("date")),
                    "liquidation_name": match.group("liquidation_name").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                role=re.sub(r"\s*,\s*", ", ", match.group("role")),
                signing=match.group("signing"), extra={
                    "action": "appointed_liquidator",
                    "previous_role": re.sub(
                        r"\s*,\s*", ", ", match.group("previous_role")
                    ),
                    "previous_signing": match.group("previous_signing"),
                    "origin": match.group("origin").strip(),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", rule_id, {
                    "kind": "liquidation_address", "action": "changed",
                    "to": match.group("address").strip(),
                },
            ),
        ], ""

    match = _DE_DELETION_PROCEDURE_BLOCKED_FEDERAL_TAX_DATE_NOTICE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.deletion_blocked_federal_tax_date_notice.v1",
            {
                "kind": "deletion_procedure_completed",
                "action": "deletion_blocked",
                "reason": "federal_tax_authority_consent_missing",
                "notice": match.group("notice"),
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
            },
        )], ""

    return [], leftover
