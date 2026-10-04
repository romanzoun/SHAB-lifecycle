from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_COOPERATIVE_ERRONEOUS_DELETION_REVOKED = re.compile(
    r"^Die (?P<entity>Genossenschaft) wurde vom (?P<authority>.+?) mittels "
    r"TR-Eintrag Nr\.\s*(?P<entry>\d+) vom "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}),\s*publiziert im SHAB Nr\.\s*"
    r"(?P<notice>\d+) vom (?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"irrtümlich gelöscht\.\s*Der genannte Löschungseintrag wird deshalb "
    r"hiermit widerrufen\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_PRESIDENT_SHARE_TRANSFER = re.compile(
    r"^L['’]associée-gérante (?P<seller>[^,.;]+),\s*maintenant présidente,\s*"
    r"détient désormais (?P<remaining>[\d']+) parts de CHF "
    r"(?P<remaining_nominal>[\d'.]+) par suite de cession de "
    r"(?P<transferred>[\d']+) parts de CHF (?P<nominal>[\d'.]+) à "
    r"(?P<buyer>[^,.;]+),\s*de (?P<origin>[^,.;]+) à "
    r"(?P<place>[^,.;]+),\s*nouvel associé-gérant pour "
    r"(?P<buyer_count>[\d']+) parts de CHF (?P<buyer_nominal>[\d'.]+)"
    r"(?: avec (?P<buyer_signing>signature individuelle))?\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATORS_APPOINTED_DIRECTORS = re.compile(
    r"^Les administrateurs (?P<name1>[^,.;]+),\s*président et "
    r"(?P<name2>[^,.;]+),\s*secrétaire,\s*nommés directeurs,\s*"
    r"continuent à signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_NAME_CORRECTED_WITH_NOTICE = re.compile(
    r"^L['’]inscription (?P<entry>[\d']+) du "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(publication FOSC du "
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}) page "
    r"(?P<notice_ref>[\d/]+)\) est rectifiée en ce sens que "
    r"l['’](?P<role>associée gérante) se nomme (?P<name>[^()]+?)\s*"
    r"\(et non:\s*(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_CAPITAL_MENTION_COMPLETED = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+) du "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du "
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\) est complétée par la mention "
    r"du captial social\.\s*Capital social:\s*(?P<currency>[A-Z]{3})\s+"
    r"(?P<capital>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_PROVISIONAL_MORATORIUM_EXTENDED = re.compile(
    r"^Mit Verfügung vom (?P<decision_date>\d{2}\.\d{2}\.\d{4}) hat "
    r"(?P<authority>.+?) die gewährte provisorische Nachlassstundung um "
    r"(?P<duration>.+?) bis zum (?P<until>\d{2}\.\d{2}\.\d{4}) "
    r"verlängert\.?$",
    re.I | re.UNICODE,
)
_FR_ORGANIZATION_ASSOCIATE_SHARE_TRANSFER = re.compile(
    r"^L['’]associée (?P<seller>.+?)\s*"
    r"\((?P<seller_uid>CHE-\d{3}\.\d{3}\.\d{3})\) cède "
    r"(?P<transferred>[\d']+) de ses (?P<before>[\d']+) parts de CHF "
    r"(?P<nominal>[\d'.]+) à l['’]associée (?P<buyer>.+?)\s*"
    r"\((?P<buyer_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*désormais titulaire de "
    r"(?P<buyer_count>[\d']+) parts de CHF (?P<buyer_nominal>[\d'.]+);\s*"
    r"(?P<seller_statement>.+?)\s*\((?P<seller_statement_uid>CHE-\d{3}\.\d{3}\.\d{3})\) "
    r"reste titulaire de (?P<remaining>[\d']+) parts de CHF "
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_ROLE_CORRECTED = re.compile(
    r"^L['’]inscription (?P<entry>[\d']+) du "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) est rectifiée en ce sens que "
    r"(?P<name>[^,.;]+) est (?P<role>associé-gérant,\s*président);\s*"
    r"ses pouvoirs sont modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_PRESIDENT_AND_TWO_MEMBERS = re.compile(
    r"^(?P<changed>[^,.;]+),\s*membre du conseil d['’]administration,\s*"
    r"jusqu['’]ici président,\s*continue de signer individuellement\.\s*"
    r"(?P<president>[^,.;]+),\s*de (?P<president_origin>[^,.;]+),\s*à "
    r"(?P<president_place>[^,.;]+),\s*(?P<president_country>[A-Z]{1,3}),\s*"
    r"président,\s*et (?P<member>[^,.;]+),\s*de "
    r"(?P<member_origin>[^,.;]+),\s*à (?P<member_place>[^,.;]+),\s*"
    r"(?P<member_country>[A-Z]{1,3}),\s*sont membres du conseil "
    r"d['’]administration(?: avec (?P<new_signing>signature individuelle))?\.?$",
    re.I | re.UNICODE,
)
_DE_DELETION_ENTRY_PARTLY_REVOKED = re.compile(
    r"^\[Bezüglich der Löschung der Gesellschaft erfolgte der im SHAB Nr\.\s*"
    r"(?P<notice>\d+) vom (?P<notice_date>\d{2}\.\d{2}\.\d{4}) publizierte "
    r"TR-Eintrag Nr\.\s*(?P<entry>\d+) vom "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) irrtümlich\.\s*Der Eintrag wird "
    r"somit in diesem Teil widerrufen und die Gesellschaft wieder vollumfänglich "
    r"im Handelsregister eingetragen\.\s*Betreffend der Personalmutation "
    r"erfolgte der Eintrag jedoch korrekt und bleibt somit in diesem Teil bestehen\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_COMPANY_REINSTATED_AFTER_REOPENING = re.compile(
    r"^Diese infolge Konkurses im Sinne von (?P<legal_basis>Art\.\s*159 Abs\.\s*5 HRegV) "
    r"am (?P<deletion_date>\d{2}\.\d{2}\.\d{4}) von Amtes wegen gelöschte "
    r"Gesellschaft wird wieder als durch Konkurs aufgelöst in das Handelsregister "
    r"eingetragen,\s*nachdem (?P<authority>.+?) mit Entscheid vom "
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}) die Wiedereröffnung des "
    r"Konkursverfahrens angeordnet hat\.\s*\[gestrichen:\s*(?P<previous>.+)\]\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_DE_COMPANY_REINSTATED_FOR_LIQUIDATION = re.compile(
    r"^Die am (?P<deletion_date>\d{2}\.\d{2}\.\d{4}) gelöschte Gesellschaft "
    r"wird auf Grund des Entscheids des (?P<authority>.+?) vom "
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}) zum Zwecke der Liquidation wieder "
    r"in das Handelsregister eingetragen und besteht entsprechend den früheren "
    r"Eintragungen weiter\.\s*\[bisher:\s*(?P<previous>.+)\]\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_FR_BRANCH_DELETED = re.compile(
    r"^La succursale de (?P<place>.+?)\s*\((?P<canton>[A-Z]{2})\) est radiée\.?$",
    re.I | re.UNICODE,
)
_DE_ADDRESS_AND_TWO_PERSONS_CHANGED = re.compile(
    r"^Vollständige Adresse:\s*(?P<street>.+?)\s+(?P<house>\d+[A-Za-z]?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<town>[^.]+)\.\s*"
    r"Eingetragene Personen geändert:\s*(?P<name1>[^,;]+),\s*"
    r"(?P<role1a>[^,;]+),\s*(?P<count1>[\d']+) Stammeinlage(?:n)? von CHF "
    r"(?P<nominal1>[\d'.]+),\s*(?P<role1b>[^,;]+),\s*"
    r"(?P<sign1>Einzelunterschrift),\s*neu in (?P<place1>[^,;]+),\s*nun "
    r"(?P<new_role1a>[^,;]+),\s*(?P<new_role1b>[^,;]+),\s*"
    r"(?P<new_sign1>Einzelunterschrift);\s*"
    r"(?P<name2>[^,;]+),\s*(?P<role2a>[^,;]+),\s*"
    r"(?P<count2>[\d']+) Stammeinlage(?:n)? von CHF (?P<nominal2>[\d'.]+),\s*"
    r"(?P<role2b>[^,;]+),\s*(?P<sign2>Einzelunterschrift),\s*neu von "
    r"(?P<origin2>.+?)\s*\((?P<origin_note>Gemeindefusion)\),\s*neu in "
    r"(?P<place2>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_LIQUIDATOR_TYPO = re.compile(
    r"^Liquidatrie:\s*l['’]administratrice (?P<name>[^,.;]+),\s*"
    r"laquelle continue à signer individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_MISSING_REGISTRY_ID_CORRECTED = re.compile(
    r"^Im SHAB Nr\.\s*(?P<notice>\d+) vom "
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}) publizierten TR[ -]Eintrag "
    r"(?P<entry>\d+) vom (?P<entry_date>\d{2}\.\d{2}\.\d{4}) wurde "
    r"irrtümlich die CH-Nummer weggelassen:\s*Richtig ist:\s*"
    r"\[bisher (?P<name>.+?)\s*\((?P<registry_id>CH-[\d.]+-\d)\)\]\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _duration_months(raw: str) -> int | None:
    token = raw.strip().split()[0].lower()
    words = {"ein": 1, "eine": 1, "einen": 1, "zwei": 2, "drei": 3}
    return int(token) if token.isdigit() else words.get(token)


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
        role=role.strip() if role else None,
        signing=signing.strip() if signing else None,
        payload={
            "name": clean_name,
            "place": clean_place,
            **({"uid": uid} if uid else {}),
            **(extra or {}),
        },
    )


def extract_parser220_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 220."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_COOPERATIVE_ERRONEOUS_DELETION_REVOKED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.cooperative_erroneous_deletion_revoked.v1", {
                "kind": "registry_deletion", "action": "revoked_as_erroneous",
                "organization_kind": match.group("entity"),
                "authority": match.group("authority").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice": match.group("notice"),
                "notice_date": _iso_date(match.group("notice_date")),
            },
        )], ""

    match = _FR_MANAGER_PRESIDENT_SHARE_TRANSFER.fullmatch(leftover)
    if match:
        remaining = _count(match.group("remaining"))
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        if transferred == buyer_count:
            rule_id = "fr.persons.manager_president_share_transfer.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller,
                    role="associée-gérante et présidente", extra={
                        "action": "appointed_president_and_shares_transferred",
                        "counterparty": buyer,
                        "shares_before": remaining + transferred,
                        "shares_transferred": transferred,
                        "shares_count": remaining,
                        "share_nominal": match.group("remaining_nominal"),
                        "currency": "CHF",
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer,
                    place=match.group("place"), role="associé-gérant",
                    signing=(
                        "Einzelunterschrift"
                        if match.group("buyer_signing") else None
                    ), extra={
                        "action": "appointed_and_shares_received",
                        "new_associate": True, "counterparty": seller,
                        "heimat": match.group("origin").strip(),
                        "shares_received": transferred,
                        "shares_count": buyer_count,
                        "share_nominal": match.group("buyer_nominal"),
                        "currency": "CHF",
                    },
                ),
            ], ""

    match = _FR_ADMINISTRATORS_APPOINTED_DIRECTORS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administrators_appointed_directors.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role="administrateur et directeur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_director", "previous_role": "président",
                    "signing_continues": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                role="administrateur et directeur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_director", "previous_role": "secrétaire",
                    "signing_continues": True,
                },
            ),
        ], ""

    match = _FR_MANAGER_NAME_CORRECTED_WITH_NOTICE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.manager_name_corrected_with_notice.v1",
            match.group("name"), role=match.group("role"), extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_CAPITAL_MENTION_COMPLETED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.capital_mention_completed.v1", {
                "action": "entry_completed", "field": "capital_social",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "currency": match.group("currency").upper(),
                "capital": match.group("capital"),
            },
        )], ""

    match = _DE_PROVISIONAL_MORATORIUM_EXTENDED.fullmatch(leftover)
    if match:
        duration = match.group("duration").strip()
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.provisional_moratorium_extended.v1", {
                "kind": "provisional_composition_moratorium",
                "action": "extended",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "duration": duration,
                "duration_months": _duration_months(duration),
                "until": _iso_date(match.group("until")),
            },
        )], ""

    match = _FR_ORGANIZATION_ASSOCIATE_SHARE_TRANSFER.fullmatch(leftover)
    if match:
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        remaining = _count(match.group("remaining"))
        if (
            before - transferred == remaining
            and match.group("seller_uid") == match.group("seller_statement_uid")
        ):
            rule_id = "fr.persons.organization_associate_share_transfer.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associée",
                    uid=match.group("seller_uid"), extra={
                        "action": "shares_transferred", "counterparty": buyer,
                        "shares_before": before, "shares_transferred": transferred,
                        "shares_count": remaining,
                        "share_nominal": match.group("remaining_nominal"),
                        "currency": "CHF",
                        "statement_name": match.group("seller_statement").strip(),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, role="associée",
                    uid=match.group("buyer_uid"), extra={
                        "action": "shares_received", "counterparty": seller,
                        "shares_received": transferred,
                        "shares_count": _count(match.group("buyer_count")),
                        "share_nominal": match.group("buyer_nominal"),
                        "currency": "CHF",
                    },
                ),
            ], ""

    match = _FR_PERSON_ROLE_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.role_and_powers_corrected.v1",
            match.group("name"), role=match.group("role"), extra={
                "action": "role_and_powers_corrected",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_BOARD_PRESIDENT_AND_TWO_MEMBERS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.board_president_and_two_members.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("changed"),
                role="membre du conseil d'administration",
                signing="Einzelunterschrift", extra={
                    "action": "presidency_ended", "previous_role": "président",
                    "signing_continues": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                place=match.group("president_place"),
                role="président du conseil d'administration",
                signing=(
                    "Einzelunterschrift" if match.group("new_signing") else None
                ), extra={
                    "action": "appointed", "heimat": match.group("president_origin").strip(),
                    "country": match.group("president_country"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                place=match.group("member_place"),
                role="membre du conseil d'administration",
                signing=(
                    "Einzelunterschrift" if match.group("new_signing") else None
                ), extra={
                    "action": "appointed", "heimat": match.group("member_origin").strip(),
                    "country": match.group("member_country"),
                },
            ),
        ], ""

    match = _DE_DELETION_ENTRY_PARTLY_REVOKED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.deletion_entry_partly_revoked.v1", {
                "kind": "registry_deletion", "action": "revoked_as_erroneous",
                "company_reinstated": True, "personnel_mutation_remains": True,
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice": match.group("notice"),
                "notice_date": _iso_date(match.group("notice_date")),
            },
        )], ""

    match = _DE_BANKRUPTCY_COMPANY_REINSTATED_AFTER_REOPENING.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_company_reinstated_after_reopening.v1", {
                "kind": "bankruptcy", "action": "reopened_and_reinstated",
                "deletion_date": _iso_date(match.group("deletion_date")),
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "legal_basis": match.group("legal_basis"),
                "previous": match.group("previous").strip(),
            },
        )], ""

    match = _DE_COMPANY_REINSTATED_FOR_LIQUIDATION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.company_reinstated_for_liquidation.v1", {
                "kind": "liquidation", "action": "reinstated_for_liquidation",
                "deletion_date": _iso_date(match.group("deletion_date")),
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "previous_registration_continues": True,
                "previous": match.group("previous").strip(),
            },
        )], ""

    match = _FR_BRANCH_DELETED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "fr.text.branch_deleted_with_place.v1", {
                "action": "deleted", "place": match.group("place").strip(),
                "branch_canton": match.group("canton").upper(),
            },
        )], ""

    match = _DE_ADDRESS_AND_TWO_PERSONS_CHANGED.fullmatch(leftover)
    if match:
        rule_id = "de.text.address_and_two_persons_changed.v1"
        address = (
            f"{match.group('street').strip()} {match.group('house')}, "
            f"{match.group('postal_code')} {match.group('town').strip()}"
        )
        common = {
            "share_kind": "Stammeinlage", "currency": "CHF",
        }
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", rule_id, {
                    "action": "complete_address_recorded", "address": address,
                    "street": match.group("street").strip(),
                    "house_number": match.group("house"),
                    "postal_code": match.group("postal_code"),
                    "town": match.group("town").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"),
                role=f"{match.group('new_role1a').strip()}, {match.group('new_role1b').strip()}",
                signing=match.group("new_sign1"), extra={
                    "action": "domicile_and_role_changed",
                    "previous_role": f"{match.group('role1a').strip()}, {match.group('role1b').strip()}",
                    "shares_count": _count(match.group("count1")),
                    "share_nominal": match.group("nominal1"), **common,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"),
                role=f"{match.group('role2a').strip()}, {match.group('role2b').strip()}",
                signing=match.group("sign2"), extra={
                    "action": "origin_and_domicile_changed",
                    "heimat": match.group("origin2").strip(),
                    "origin_change_reason": match.group("origin_note"),
                    "shares_count": _count(match.group("count2")),
                    "share_nominal": match.group("nominal2"), **common,
                },
            ),
        ], ""

    match = _FR_LIQUIDATOR_TYPO.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_liquidator_typo.v1",
            match.group("name"), role="administratrice et liquidatrice",
            signing="Einzelunterschrift", extra={
                "action": "appointed_liquidator", "signing_continues": True,
            },
        )], ""

    match = _DE_MISSING_REGISTRY_ID_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.missing_registry_id_corrected.v1", {
                "action": "registry_identifier_completed",
                "name": match.group("name").strip(),
                "registry_id": match.group("registry_id"),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice": match.group("notice"),
                "notice_date": _iso_date(match.group("notice_date")),
            },
        )], ""

    return [], leftover
