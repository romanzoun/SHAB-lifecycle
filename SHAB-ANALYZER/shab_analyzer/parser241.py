from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_FR_SHARE_TRANSFER_TO_NEW_UNSIGNED_ASSOCIATE = re.compile(
    r"^(?P<seller>[^,.;]+) cède (?P<transferred>[\d']+) de ses "
    r"(?P<before>[\d']+) parts de CHF (?P<nominal>[\d'.]+) à "
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;()]+)\s*"
    r"\((?P<country>[^)]+)\),\s*nouvelle associée sans signature,\s*"
    r"avec (?P<buyer_count>[\d']+) parts de CHF "
    r"(?P<buyer_nominal>[\d'.]+);\s*(?P=seller) reste titulaire de "
    r"(?P<remaining>[\d']+) parts de CHF (?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_CORRECTION_CONTINUES_COLLECTIVE = re.compile(
    r"^L['’]inscription\s+(?:no|n°)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+continue à signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_DEFINITIVE_MORATORIUM_WITHOUT_COMMISSIONER = re.compile(
    r"^Par prononcé rendu le\s+"
    r"(?P<decision_date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"(?P<authority>.+?)\s+a accordé à la société un sursis concordataire "
    r"définitif de\s+(?P<duration>\w+)\s+mois,\s*échéant le\s+"
    r"(?P<until>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.?$",
    re.I | re.UNICODE,
)
_IT_ASSOCIATION_DISSOLVED_BY_LAW = re.compile(
    r"^Nuovo nome:\s*(?P<name>.+? in liquidazione)\.\s*"
    r"L['’]associazione è sciolta per legge ai sensi dell['’]"
    r"(?P<legal_basis>art\.\s*77 CC),\s*in quanto\s+"
    r"(?P<reason>la direzione non può più essere costituita conformemente allo statuto)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_CLAUSE_REMOVED_NOT_EXHAUSTED = re.compile(
    r"^\[Streichung der Statutenbestimmung über die genehmigte Kapitalerhöhung "
    r"infolge Nichtausschöpfung des Erhöhungsbetrages\.\]\s*"
    r"\[gestrichen:\s*Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<authorization_date>\d{2}\.\d{2}\.\d{4})\s+eine genehmigte "
    r"Kapitalerhöhung gemäss näherer Umschreibung in den Statuten beschlossen\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_APPEAL_SUSPENSIVE_EFFECT_WITH_DUPLICATE_HISTORY = re.compile(
    r"^\[bisher:\s*(?P<previous>Über den Inhaber dieses Einzelunternehmens ist "
    r"mit Entscheid des Einzelrichters am Kantonsgericht vom\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<bankruptcy_time>\d{1,2}[.:]\d{2})\s+Uhr,\s*der Konkurs eröffnet "
    r"worden\.)\]\.?\s*"
    r"(?P<authority>Der .+?)\s+hat mit Entscheid vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+der gegen die "
    r"Konkurseröffnung erhobenen Beschwerde aufschiebende Wirkung zuerkannt\s*"
    r"\[bisher:\s*(?P=previous)\]\.?$",
    re.I | re.UNICODE,
)
_DE_OUTGOING_SPIN_OFF_MISSING_AUF = re.compile(
    r"^Abspaltung:\s*Ein Teil der Aktiven und Passiven geht gemäss\s+"
    r"(?P<document>Spaltungsplan|Spaltungsvertrag)\s+vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+die\s+"
    r"(?P<newly_founded>neu gegründete\s+)?(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*über\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_CHANGED_AND_ADDED_PERSON = re.compile(
    r"^Eingetragene Person gelöscht:\s*(?P<removed>[^,.;]+),\s*"
    r"(?P<removed_signing>[^.;]+)\.\s*"
    r"Eingetragene Personen geändert:\s*(?P<changed>[^,.;]+),\s*"
    r"(?P<previous_role>[^,.;]+),\s*(?P<previous_signing>[^,.;]+),\s*neu\s+"
    r"(?P<role1>[^,.;]+),\s*(?P<role2>[^,.;]+),\s*"
    r"(?P<signing>[^.;]+)\.\s*"
    r"Neu eingetragene Person:\s*(?P<added>[^,.;]+),\s*von\s+"
    r"(?P<origin>[^,.;]+),\s*in\s+(?P<place>[^,.;]+),\s*"
    r"(?P<added_role>[^,.;]+),\s*(?P<added_signing>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_ADDITIONAL_ADDRESS_REPLACED = re.compile(
    r"^Zusätzliche Adresse gelöscht:\s*(?P<previous_address>.+?,\s*"
    r"(?P<previous_postal_code>\d{4})\s+(?P<previous_place>[^.]+))\.\s*"
    r"Zusätzliche Adresse neu:\s*(?P<address>.+?,\s*"
    r"(?P<postal_code>\d{4})\s+(?P<place>[^.]+))\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_DELETED_INACTIVE_ART_155 = re.compile(
    r"^Die Gesellschaft wird in Anwendung von\s+"
    r"(?P<legal_basis>Art\.\s*155 HRegV)\s+von Amtes wegen gelöscht,\s*weil "
    r"die Gesellschaft keine Geschäftstätigkeit mehr aufweist,\s*keine "
    r"verwertbaren Aktiven mehr hat und kein Interesse an der Aufrechterhaltung "
    r"der Eintragung innert angesetzter Frist geltend gemacht wurde\.?$",
    re.I | re.UNICODE,
)
_DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_INTRODUCED_HISTORY = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+die mit Beschluss vom\s+"
    r"(?P<authorization_date>\d{2}\.\d{2}\.\d{4})\s+geänderte Bestimmung "
    r"betreffend bedingter Kapitalerhöhung gemäss näherer Umschreibung in den "
    r"Statuten geändert\.\s*\[bisher:\s*Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+die mit Beschluss vom\s+"
    r"(?P<introduction_date>\d{2}\.\d{2}\.\d{4})\s+eingeführte Bestimmung "
    r"betreffend bedingter Kapitalerhöhung gemäss näherer Umschreibung in den "
    r"Statuten geändert\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_MEMBER_OBLIGATIONS_ACCORDING_TO_STATUTES = re.compile(
    r"^Pflichten neu:\s*(?P<obligations>Beitrags- oder Leistungspflichten:\s*"
    r"Gemäss Statuten)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_TRANSFER_TO_THREE_ASSOCIATES = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller1>[^,.;]+)\s+cède\s+"
    r"(?P<transferred1>[\d']+)\s+de ses\s+(?P<before1>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal1>[\d'.]+),\s*par\s+(?P<allocation11>[\d']+)\s+à\s+"
    r"(?P<buyer1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;()]+)\s*\((?P<country1>[^)]+)\),\s*par\s+"
    r"(?P<allocation12>[\d']+)\s+à\s+(?P<buyer2>[^,.;]+),\s*de et à\s+"
    r"(?P<place2>[^,.;]+),\s*et par\s+(?P<allocation13>[\d']+)\s+à\s+"
    r"(?P<buyer3>[^,.;]+),\s*de\s+(?P<origin3>[^,.;]+),\s*à\s+"
    r"(?P<place3>[^,.;]+),\s*tous trois nouveaux associés sans signature\.\s*"
    r"L['’]associé-gérant\s+(?P<seller2>[^,.;]+)\s+cède\s+"
    r"(?P<transferred2>[\d']+)\s+de ses\s+(?P<before2>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal2>[\d'.]+),\s*par\s+(?P<allocation21>[\d']+)\s+à\s+"
    r"(?P=buyer1),\s*par\s+(?P<allocation22>[\d']+)\s+à\s+(?P=buyer2),\s*"
    r"et par\s+(?P<allocation23>[\d']+)\s+à\s+(?P=buyer3),\s*tous trois "
    r"désormais titulaires de\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*(?P=seller1)\s+et\s+(?P=seller2)\s+"
    r"restent chacun titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_COLLECTIVE_PROXIES_MUTUALLY_EXCLUDED = re.compile(
    r"^Procuration collective à deux,\s*toutefois pas entre eux,\s*est conférée à\s+"
    r"(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*et\s+"
    r"(?P<name3>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_CORPORATE_ASSOCIATE_RENAMED_AND_MOVED = re.compile(
    r"^Eingetragene Personen neu oder mutierend:\s*"
    r"(?P<name>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+"
    r"(?P<place>[^,.;]+),\s*(?P<role>Gesellschafterin),\s*mit\s+"
    r"(?P<count>[\d']+)\s+Stammanteilen zu je CHF\s+(?P<nominal>[\d'.]+)\s*"
    r"\[bisher:\s*(?P<previous_name>.+?)\s*\((?P=uid)\),\s*in\s+"
    r"(?P<previous_place>[^\]]+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_TO_NEW_UNSIGNED_ASSOCIATE = re.compile(
    r"^(?P<seller>[^,.;]+)\s+maintenant associé pour\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"par suite de cession de\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<transferred_nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"de\s+(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]),\s*nouvel associé pour\s+(?P<buyer_count>[\d']+)\s+"
    r"parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*sans signature sociale\.?$",
    re.I | re.UNICODE,
)


_FRENCH_MONTHS = {
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
    "un": 1,
    "une": 1,
    "deux": 2,
    "trois": 3,
    "quatre": 4,
    "cinq": 5,
    "six": 6,
}


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _french_date(raw: str) -> str:
    day, month, year = raw.casefold().replace("1er", "1", 1).split()
    return f"{int(year):04d}-{_FRENCH_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _amount(raw: str) -> Decimal:
    return Decimal(raw.replace("'", ""))


def _duration_months(raw: str) -> int | None:
    normalized = raw.casefold()
    return int(normalized) if normalized.isdigit() else _NUMBER_WORDS.get(normalized)


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
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser241_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 241."""
    del language  # Historical publications regularly contain another language.
    leftover = text.strip()

    match = _FR_SHARE_TRANSFER_TO_NEW_UNSIGNED_ASSOCIATE.fullmatch(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        before = _count(match.group("before"))
        remaining = _count(match.group("remaining"))
        buyer_count = _count(match.group("buyer_count"))
        amounts = {
            _amount(match.group(group))
            for group in ("nominal", "buyer_nominal", "remaining_nominal")
        }
        if before - transferred != remaining or transferred != buyer_count or len(amounts) != 1:
            return [], leftover
        rule_id = "fr.persons.share_transfer_new_unsigned_associate.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller"), role="associé",
                extra={
                    "action": "shares_transferred", "counterparty": match.group("buyer").strip(),
                    "previous_shares_count": before, "shares_transferred": transferred,
                    "shares_count": remaining, "share_nominal": match.group("nominal"),
                    "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"),
                place=match.group("place"), role="associée", extra={
                    "action": "appointed_and_shares_received",
                    "counterparty": match.group("seller").strip(),
                    "origin": match.group("origin").strip(),
                    "country": match.group("country").strip(),
                    "shares_received": transferred, "shares_count": buyer_count,
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                    "without_signature": True,
                },
            ),
        ], ""

    match = _FR_SIGNING_CORRECTION_CONTINUES_COLLECTIVE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed",
            "fr.persons.signing_correction_continues_collective.v1",
            match.group("name"), signing="Kollektivunterschrift zu zweien", extra={
                "action": "publication_corrected", "signing_continues": True,
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_DEFINITIVE_MORATORIUM_WITHOUT_COMMISSIONER.fullmatch(leftover)
    if match:
        duration = _duration_months(match.group("duration"))
        if duration is None:
            return [], leftover
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.definitive_moratorium_granted.v1", {
                "kind": "composition_moratorium_granted", "action": "granted",
                "moratorium_type": "definitive",
                "authority": match.group("authority").strip(),
                "decision_date": _french_date(match.group("decision_date")),
                "duration_months": duration,
                "until": _french_date(match.group("until")),
            },
        )], ""

    match = _IT_ASSOCIATION_DISSOLVED_BY_LAW.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.association_dissolved_by_law.v1", {
                "kind": "dissolution", "action": "dissolved_by_law",
                "entity_type": "association", "new_name": match.group("name").strip(),
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "reason": "management_cannot_be_constituted_according_to_statutes",
            },
        )], ""

    match = _DE_AUTHORIZED_CAPITAL_CLAUSE_REMOVED_NOT_EXHAUSTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_clause_removed_not_exhausted.v1", {
                "kind": "authorized_capital_clause", "action": "removed",
                "reason": "increase_amount_not_exhausted",
                "authorization_date": _iso_date(match.group("authorization_date")),
                "basis": "statutes",
            },
        )], ""

    match = _DE_BANKRUPTCY_APPEAL_SUSPENSIVE_EFFECT_WITH_DUPLICATE_HISTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.sole_proprietor_bankruptcy_appeal_suspensive_effect.v1", {
                "kind": "bankruptcy_effect_suspended", "action": "suspensive_effect_granted",
                "scope": "sole_proprietor", "authority": match.group("authority").strip(),
                "decision_date": _iso_date(match.group("decision_date")),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "bankruptcy_time": match.group("bankruptcy_time").replace(".", ":"),
                "previous": match.group("previous").strip(),
            },
        )], ""

    match = _DE_OUTGOING_SPIN_OFF_MISSING_AUF.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.outgoing_spin_off_missing_auf.v1", {
                "kind": "spin_off_distribution", "date": _iso_date(match.group("date")),
                "document": match.group("document").lower(),
                "scope": "part_of_assets_and_liabilities",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_newly_founded": bool(match.group("newly_founded")),
            },
        )], ""

    match = _DE_REMOVED_CHANGED_AND_ADDED_PERSON.fullmatch(leftover)
    if match:
        rule_id = "de.persons.removed_changed_and_added.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group("removed"), extra={
                    "action": "removed", "previous_signing": match.group("removed_signing").strip(),
                    "signing_revoked": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("changed"),
                role=f"{match.group('role1').strip()}; {match.group('role2').strip()}",
                signing=match.group("signing").strip(), extra={
                    "action": "role_changed", "previous_role": match.group("previous_role").strip(),
                    "previous_signing": match.group("previous_signing").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("added"), place=match.group("place"),
                role=match.group("added_role").strip(), signing=match.group("added_signing").strip(),
                extra={"action": "appointed", "origin": match.group("origin").strip()},
            ),
        ], ""

    match = _DE_ADDITIONAL_ADDRESS_REPLACED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "de.text.additional_address_replaced.v1", {
                "kind": "additional_address", "action": "changed",
                "from": match.group("previous_address").strip(),
                "previous_postal_code": match.group("previous_postal_code"),
                "previous_place": match.group("previous_place").strip(),
                "to": match.group("address").strip(),
                "postal_code": match.group("postal_code"),
                "place": match.group("place").strip(),
            },
        )], ""

    match = _DE_COMPANY_DELETED_INACTIVE_ART_155.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_deleted", "de.text.company_deleted_inactive_art_155.v1", {
                "action": "deleted_ex_officio", "reason": "inactive_without_assets_or_interest",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "business_activity": False, "realisable_assets": False,
                "maintenance_interest_asserted": False,
            },
        )], ""

    match = _DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_INTRODUCED_HISTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.conditional_capital_clause_changed_introduced_history.v1", {
                "kind": "conditional_capital_clause", "action": "modified",
                "decision_date": _iso_date(match.group("decision_date")),
                "authorization_date": _iso_date(match.group("authorization_date")),
                "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                "introduction_date": _iso_date(match.group("introduction_date")),
                "details_in_statutes": True,
            },
        )], ""

    match = _DE_MEMBER_OBLIGATIONS_ACCORDING_TO_STATUTES.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.member_obligations_according_to_statutes.v1", {
                "kind": "member_obligations", "action": "changed",
                "obligations": match.group("obligations").strip(), "basis": "statutes",
            },
        )], ""

    match = _FR_TWO_MANAGERS_TRANSFER_TO_THREE_ASSOCIATES.fullmatch(leftover)
    if match:
        transfer1 = _count(match.group("transferred1"))
        transfer2 = _count(match.group("transferred2"))
        allocations1 = [_count(match.group(f"allocation1{index}")) for index in (1, 2, 3)]
        allocations2 = [_count(match.group(f"allocation2{index}")) for index in (1, 2, 3)]
        remaining = _count(match.group("remaining"))
        buyer_count = _count(match.group("buyer_count"))
        amounts = {
            _amount(match.group(group))
            for group in ("nominal1", "nominal2", "buyer_nominal", "remaining_nominal")
        }
        valid = (
            transfer1 == sum(allocations1)
            and transfer2 == sum(allocations2)
            and _count(match.group("before1")) - transfer1 == remaining
            and _count(match.group("before2")) - transfer2 == remaining
            and all(allocations1[index] + allocations2[index] == buyer_count for index in range(3))
            and len(amounts) == 1
        )
        if not valid:
            return [], leftover
        rule_id = "fr.persons.two_managers_transfer_to_three_associates.v1"
        sellers = [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"seller{index}"),
                role="associé-gérant", extra={
                    "action": "shares_transferred",
                    "previous_shares_count": _count(match.group(f"before{index}")),
                    "shares_transferred": _count(match.group(f"transferred{index}")),
                    "shares_count": remaining, "share_nominal": match.group(f"nominal{index}"),
                    "currency": "CHF",
                },
            )
            for index in (1, 2)
        ]
        buyers = []
        for index in (1, 2, 3):
            origin = match.group("place2") if index == 2 else match.group(f"origin{index}")
            extra = {
                "action": "appointed_and_shares_received", "origin": origin.strip(),
                "shares_received": allocations1[index - 1] + allocations2[index - 1],
                "shares_count": buyer_count, "share_nominal": match.group("buyer_nominal"),
                "currency": "CHF", "without_signature": True,
            }
            if index == 1:
                extra["country"] = match.group("country1").strip()
            buyers.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"buyer{index}"),
                place=match.group(f"place{index}"), role="associé", extra=extra,
            ))
        return sellers + buyers, ""

    match = _FR_THREE_COLLECTIVE_PROXIES_MUTUALLY_EXCLUDED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.three_collective_proxies_mutually_excluded.v1"
        names = [match.group(f"name{index}").strip() for index in (1, 2, 3)]
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, names[index - 1],
                place=match.group(f"place{index}"), role="fondé de procuration",
                signing="Kollektivprokura zu zweien", extra={
                    "action": "proxy_granted", "origin": match.group(f"origin{index}").strip(),
                    "cannot_sign_with": [name for name in names if name != names[index - 1]],
                },
            )
            for index in (1, 2, 3)
        ], ""

    match = _DE_CORPORATE_ASSOCIATE_RENAMED_AND_MOVED.fullmatch(leftover)
    if match:
        uid = match.group("uid")
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.corporate_associate_renamed_and_moved.v1",
            match.group("name"), place=match.group("place"), uid=uid,
            role=match.group("role"), extra={
                "action": "renamed_moved_and_shares_recorded", "uid": uid,
                "previous_name": match.group("previous_name").strip(),
                "previous_place": match.group("previous_place").strip(),
                "shares_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"), "currency": "CHF",
            },
        )], ""

    match = _FR_ASSOCIATE_TRANSFER_TO_NEW_UNSIGNED_ASSOCIATE.fullmatch(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        amounts = {
            _amount(match.group(group))
            for group in ("nominal", "transferred_nominal", "buyer_nominal")
        }
        if transferred != buyer_count or len(amounts) != 1:
            return [], leftover
        rule_id = "fr.persons.associate_transfer_to_new_unsigned_associate.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller"), role="associé", extra={
                    "action": "shares_transferred", "counterparty": match.group("buyer").strip(),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"), place=match.group("place"),
                role="associé", extra={
                    "action": "appointed_and_shares_received",
                    "counterparty": match.group("seller").strip(),
                    "origin": match.group("origin").strip(), "country": match.group("country"),
                    "shares_received": transferred, "shares_count": buyer_count,
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                    "without_signature": True,
                },
            ),
        ], ""

    return [], leftover
