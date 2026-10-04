from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_IT_TWO_OBSOLETE_CORPORATION_INDICATIONS_REMOVED = re.compile(
    r"^\[La seguente indicazione è radiata in quanto non prevista quale "
    r"iscrizione nel registro di commercio delle società anonime secondo "
    r"l['’]art\.\s*45 ORC\.\]\s*"
    r"\[radiati:\s*(?P<board>Consiglio di amministrazione da\s+"
    r"(?P<minimum>\d+)\s+a più membri\.)\]\.?\s*"
    r"\[La seguente indicazione è radiata in quanto non prevista quale "
    r"iscrizione nel registro di commercio delle società anonime secondo "
    r"l['’]art\.\s*45 ORC\.\]\s*"
    r"\[radiati:\s*(?P<statutes>Gli statuti sono stati adeguati al nuovo "
    r"diritto azionario in vigore dal\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4})\.)\]\.?$",
    re.I | re.UNICODE,
)
_FR_SUPPLEMENT_LIQUIDATION_NAME = re.compile(
    r"^Complément à l['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\):\s*Nouvelle raison sociale:\s*"
    r"(?P<name>[^()]+?\s+en liquidation)\s*"
    r"\((?P<german_name>[^()]+?\s+in Liquidation)\)\s*"
    r"\((?P<italian_name>[^()]+?\s+in liquidazione)\)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_NAME_CORRECTED_MISSPELLED_HEADER = re.compile(
    r"^Rectificatf:\s*l['’]inscription\s+(?:no|n°)\s*"
    r"(?P<entry>[\d']+)\s+du\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*"
    r"\(FOSC du\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"p\.\s*(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le "
    r"gérant se nomme\s+(?P<name>[^()]+?)\s*\(et non\s+"
    r"(?P<previous_name>[^)]+?)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATION_ASSET_TRANSFER_NO_CONSIDERATION = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<agreement_date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"l['’]association a transféré des actifs pour CHF\s+"
    r"(?P<assets>[\d'.]+)\s+et des passifs envers les tiers pour CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+à\s+(?P<recipient>.+?),\s*à\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*aucune\.?$",
    re.I | re.UNICODE,
)
_DE_AUDIT_WAIVER_RENEWED = re.compile(
    r"^Gemäss Erklärung vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+wurde der "
    r"Verzicht auf die eingeschränkte Revision erneuert\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_DIRECTORS_INDIVIDUAL_SIGNING = re.compile(
    r"^Signature individuelle est conférée à\s+(?P<name1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*(?P<name2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*tous deux de\s+(?P<origin12>[^,.;]+),\s*"
    r"et\s+(?P<name3>[^,.;]+),\s*de\s+(?P<origin3>[^,.;]+),\s*à\s+"
    r"(?P<place3>[^,.;]+),\s*directeurs\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_PROXIES_RESTRICTION_REMOVED = re.compile(
    r"^(?P<name1>[^,.;]+?)\s+et\s+(?P<name2>[^,.;]+?)\s+continuent à "
    r"engager la société par leur procuration collective à deux,\s*"
    r"toutefois désormais sans restriction\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_UID_OMISSION_SUPPLEMENT = re.compile(
    r"^Unter TR-Nr\.\s*(?P<entry>[\d']+)\s+vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+publiziert im SHAB Nr\.\s*"
    r"(?P<issue>\d+)\s+vom\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"ging die UID Nr\.\s+der Zweigniederlassung\s+(?P<place>[^,.;]+?)\s+"
    r"vergessen deshalb erfolgt untenstehender Nachtrag\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_ORGANIZATION_IDENTITY_AND_SEAT_CHANGED = re.compile(
    r"^L['’]associée\s+(?P<previous_name>.+?)\s*"
    r"\((?P<previous_registry_id>CH-[\d-]+)\),\s*qui a modifié sa raison de "
    r"commerce en\s+(?P<name>.+?)\s+et dont le numéro d['’]identification "
    r"des entreprise(?:s)? est désormais\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*a transféré son siège à\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_ROLES_CORRECTED = re.compile(
    r"^L['’]inscription\s+no\.\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(publication FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+page\s+"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<name1>[^,.;]+)\s+n['’]est pas secrétaire,\s*mais demeure "
    r"administrateur et président avec signature collective à deux,\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*de\s+"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+)\s+est nommé "
    r"administrateur et secrétaire avec signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_BUYER_APPOINTED_MANAGER = re.compile(
    r"^(?P<seller>[^,.;]+)\s+a cédé\s+(?P<transferred>[\d']+)\s+parts de "
    r"CHF\s+(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{1,3}),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"lequel associé est en outre nommé gérant avec signature individuelle\.\s*"
    r"Par conséquent,\s*"
    r"(?P=seller)\s+est maintenant titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_DOMICILE_CORRECTED_MALFORMED_REFERENCE = re.compile(
    r"^Rectificatif:\s*l['’]inscription\s+(?:no|n°)\s*"
    r"(?P<entry>[\d']+)\s+du\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"FOSC du\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"p\.\s*(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que "
    r"l['’]associée-gérante\s+(?P<name>[^,.;]+)\s+est à\s+"
    r"(?P<place>[^()]+?)\s*\(et non à\s+(?P<previous_place>[^)]+?)\s+"
    r"comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_SOCIAL_SHARE_SPLIT_CAPITAL = re.compile(
    r"^Division de la part de CHF\s+(?P<from_nominal>[\d'.]+)\s+de "
    r"l['’]associé-gérant\s+(?P<name>[^,.;]+),\s*formant le capital de même "
    r"montant,\s*en\s+(?P<count>[\d']+)\s+parts de CHF\s+"
    r"(?P<to_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBERSHIP_CORRECTED_NEGATIVE = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\)\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+n['’]est pas membre du conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_FR_VOTING_PRIVILEGE_REMOVED = re.compile(
    r"^Les\s+(?P<count>[\d']+)\s+actions de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+ne sont désormais plus privilégiées quant au "
    r"droit de vote\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_PEOPLE_ORIGIN_CHANGED_SHORT = re.compile(
    r"^(?P<name1>[^,.;]+?)\s+et\s+(?P<name2>[^,.;]+?)\s+sont maintenant "
    r"d['’](?P<origin>[^,.;]+)\.?$",
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
    day, month, year = re.sub(r"(?<=\d)er\b", "", raw.strip().casefold()).split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _amount(raw: str) -> Decimal:
    return Decimal(raw.replace("'", "").replace(" ", "").replace(",", "."))


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


def extract_parser205_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 205."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _IT_TWO_OBSOLETE_CORPORATION_INDICATIONS_REMOVED.fullmatch(leftover)
    if match:
        rule_id = "it.text.two_obsolete_corporation_indications_removed.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id, {
                    "kind": "board_composition_indication", "action": "removed",
                    "reason": "registration_not_required", "law": "Art. 45 ORC",
                    "minimum_members": _count(match.group("minimum")),
                    "previous": match.group("board"),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id, {
                    "kind": "corporate_law_adaptation_indication",
                    "action": "historical_indication_removed",
                    "reason": "registration_not_required", "law": "Art. 45 ORC",
                    "effective_date": _iso_date(match.group("effective_date")),
                    "previous": match.group("statutes"),
                },
            ),
        ], ""

    match = _FR_SUPPLEMENT_LIQUIDATION_NAME.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_name_changed", "fr.text.liquidation_name_supplemented.v1", {
                "action": "supplemented", "to": match.group("name").strip(),
                "translations": [
                    match.group("german_name").strip(),
                    match.group("italian_name").strip(),
                ],
                "in_liquidation": True, "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        )], ""

    match = _FR_MANAGER_NAME_CORRECTED_MISSPELLED_HEADER.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.manager_name_corrected_rectificatf.v1",
            match.group("name"), role="gérant", extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
                "source_wording": "Rectificatf",
            },
        )], ""

    match = _FR_ASSOCIATION_ASSET_TRANSFER_NO_CONSIDERATION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.association_asset_transfer_no_consideration.v1", {
                "source_kind": "association",
                "agreement_date": _french_date(match.group("agreement_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration_kind": "none", "gratuitous": True,
            },
        )], ""

    match = _DE_AUDIT_WAIVER_RENEWED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "audit_requirement_changed", "de.text.audit_waiver_renewed.v1", {
                "kind": "limited_audit_waiver", "action": "renewed",
                "waiver": True, "date": _iso_date(match.group("date")),
            },
        )], ""

    match = _FR_THREE_DIRECTORS_INDIVIDUAL_SIGNING.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.three_directors_individual_signing.v1"
        people = (
            (match.group("name1"), match.group("place1"), match.group("origin12")),
            (match.group("name2"), match.group("place2"), match.group("origin12")),
            (match.group("name3"), match.group("place3"), match.group("origin3")),
        )
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, name, place=place,
                role="directeur", signing="Einzelunterschrift", extra={
                    "action": "signing_granted", "heimat": origin.strip(),
                },
            )
            for name, place, origin in people
        ], ""

    match = _FR_TWO_PROXIES_RESTRICTION_REMOVED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_proxies_restriction_removed.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                signing="Kollektivprokura zu zweien", extra={
                    "action": "restriction_removed", "signing_continues": True,
                },
            )
            for index in (1, 2)
        ], ""

    match = _DE_BRANCH_UID_OMISSION_SUPPLEMENT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.branch_uid_omission_supplement.v1", {
                "kind": "branch_identifier", "action": "supplemented",
                "omitted_field": "uid", "branch_place": match.group("place").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "issue": match.group("issue"),
                "notice_date": _iso_date(match.group("notice_date")),
            },
        )], ""

    match = _FR_ASSOCIATE_ORGANIZATION_IDENTITY_AND_SEAT_CHANGED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_org_identity_and_seat_changed.v1",
            match.group("name"), place=match.group("place"), uid=match.group("uid"),
            role="associée", extra={
                "action": "name_identifier_and_seat_changed",
                "previous_name": match.group("previous_name").strip(),
                "previous_registry_id": match.group("previous_registry_id"),
            },
        )], ""

    match = _FR_BOARD_ROLES_CORRECTED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.board_roles_corrected.v1"
        reference = {
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_ref": match.group("notice_ref"),
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role="administrateur et président",
                signing="Kollektivunterschrift zu zweien", extra={
                    **reference, "action": "role_corrected",
                    "incorrect_role": "secrétaire", "remains_in_roles": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="administrateur et secrétaire",
                signing="Kollektivunterschrift zu zweien", extra={
                    **reference, "action": "appointed",
                    "heimat": match.group("origin2").strip(),
                },
            ),
        ], ""

    match = _FR_SHARE_TRANSFER_BUYER_APPOINTED_MANAGER.fullmatch(leftover)
    if match and (
        _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and len({
            match.group("nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }) == 1
    ):
        rule_id = "fr.persons.share_transfer_buyer_appointed_manager.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        remaining = _count(match.group("remaining"))
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé", extra={
                    **common, "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": transferred + remaining,
                    "shares_transferred": transferred, "shares_count": remaining,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé-gérant", signing="Einzelunterschrift", extra={
                    **common, "action": "appointed_and_shares_received",
                    "counterparty": seller, "origin": match.group("origin").strip(),
                    "country": match.group("country"), "new_associate": True,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                },
            ),
        ], ""

    match = _FR_MANAGER_DOMICILE_CORRECTED_MALFORMED_REFERENCE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.manager_domicile_corrected_malformed_reference.v1",
            match.group("name"), place=match.group("place"), role="associée-gérante",
            extra={
                "action": "domicile_corrected",
                "previous_place": match.group("previous_place").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_MANAGER_SOCIAL_SHARE_SPLIT_CAPITAL.fullmatch(leftover)
    if match and _amount(match.group("from_nominal")) == (
        _count(match.group("count")) * _amount(match.group("to_nominal"))
    ):
        rule_id = "fr.text.manager_social_share_split_capital.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "social_share_split", "action": "split",
                    "capital": match.group("from_nominal"), "currency": "CHF",
                    "from_count": 1, "from_nominal": match.group("from_nominal"),
                    "to_count": _count(match.group("count")),
                    "to_nominal": match.group("to_nominal"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                role="associé-gérant", extra={
                    "action": "share_structure_changed",
                    "shares_count": _count(match.group("count")),
                    "share_nominal": match.group("to_nominal"), "currency": "CHF",
                },
            ),
        ], ""

    match = _FR_BOARD_MEMBERSHIP_CORRECTED_NEGATIVE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.board_membership_corrected_negative.v1",
            match.group("name"), extra={
                "action": "role_corrected",
                "incorrect_role": "membre du conseil d'administration",
                "role_applies": False, "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
            },
        )], ""

    match = _FR_VOTING_PRIVILEGE_REMOVED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.voting_privilege_removed.v1", {
                "kind": "share_privileges", "action": "removed",
                "removed_privileges": ["voting_rights"],
                "shares_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"), "currency": "CHF",
            },
        )], ""

    match = _FR_TWO_PEOPLE_ORIGIN_CHANGED_SHORT.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_people_origin_changed_short.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"), extra={
                    "action": "origin_changed", "origin": match.group("origin").strip(),
                },
            )
            for index in (1, 2)
        ], ""

    return [], leftover
