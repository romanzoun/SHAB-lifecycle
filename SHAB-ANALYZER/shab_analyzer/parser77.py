from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_FEDERAL_SUSPENSIVE_EFFECT = re.compile(
    r"^Par ordonnance du\s+(?P<date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>la IIe Cour de droit civil du Tribunal fédéral) a décidé "
    r"d['’]admettre la requête d['’]effet suspensif,\s*et de maintenir les choses "
    r"en l['’]état pendant la procédure fédérale;\s*les mesures conservatoires déjà "
    r"exécutées par l['’]Office en vertu des\s+(?P<legal_basis>art\.\s*.+?\s+LP) "
    r"demeurent en vigueur\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_AND_CHANGED_ASSOCIATES = re.compile(
    r"^Gelöschte Person:\s*(?P<removed>[^,.;]+),\s*Gesellschafter mit\s+"
    r"(?P<removed_count>[\d']+) Stammanteilen zu CHF\s+(?P<removed_nominal>[\d'.]+)\.\s*"
    r"Eingetragene Person geändert:\s*(?P<changed>[^,.;]+),\s*Gesellschafter mit\s+"
    r"(?P<before_count>[\d']+) Stammanteilen zu CHF\s+(?P<before_nominal>[\d'.]+),\s*"
    r"Geschäftsführer,\s*Einzelunterschrift,\s*neu Gesellschafter mit\s+"
    r"(?P<count>[\d']+) Stammanteilen zu CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"Geschäftsführer,\s*Einzelunterschrift,\s*neu in\s+(?P<place>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_NAME_RESTORED = re.compile(
    r"^La raison de commerce redevient:?[ \t]+(?P<name>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_NAME_CORRECTION_AND_MANAGER_SIGNING = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\) est rectifiée en ce sens que\s+"
    r"(?P<name>.+?)\s+\(et non pas\s+(?P<incorrect_name>.+?)\) est associé avec\s+"
    r"(?P<count>[\d']+) parts sociales de CHF\s+(?P<nominal>[\d'.]+)\.\s*"
    r"L['’]associé\s+(?P<manager>[^,.;]+),\s*nommé gérant et président,\s*"
    r"exerce désormais la signature sociale,\s*individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_WAY_SHARE_TRANSFER = re.compile(
    r"^(?P<seller>[^,.;]+) cède\s+(?P<transferred>[\d']+) de ses\s+"
    r"(?P<before>[\d']+) parts de CHF\s+(?P<nominal>[\d'.]+) par\s+"
    r"(?P<buyer1_received>[\d']+) parts à\s+(?P<buyer1>[^,.;]+) et par\s+"
    r"(?P<buyer2_received>[\d']+) parts à\s+(?P<buyer2>[^,.;]+),\s*désormais "
    r"titulaires de respectivement\s+(?P<buyer1_count>[\d']+) et\s+"
    r"(?P<buyer2_count>[\d']+) parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"(?P=seller) a désormais\s+(?P<seller_count>[\d']+) parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_IT_CREDIT_SET_OFF_CLAUSE_REPEALED = re.compile(
    r"^Fatti particolari:\s*\[La disposizione statutaria relativa alla "
    r"compensazione di credito è abrogata\.?\]\.?$",
    re.I | re.UNICODE,
)
_DE_OWNER_BANKRUPTCY_APPEAL_SUSPENDED = re.compile(
    r"^(?P<authority>Der Abteilungspräsident der II\. Beschwerdeabteilung des "
    r"Obergerichts des Kantons Zug) hat mit Entscheid vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}) der gegen die Konkurseröffnung "
    r"erhobenen Beschwerde aufschiebende Wirkung zuerkannt\s*\[bisher:\s*"
    r"Über die Inhaberin dieses Einzelunternehmens ist mit Entscheid des\s+"
    r"(?P<bankruptcy_court>.+?) vom\s+(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<bankruptcy_time>\d{2}[.:]\d{2}) Uhr,\s*der Konkurs eröffnet worden\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_MIXED_PERSON_SECTIONS = re.compile(
    r"^Gelöschte Personen:\s*(?P<removed1>[^,.;]+),\s*"
    r"(?P<signing1>Kollektivunterschrift zu zweien);\s*"
    r"(?P<removed2>[^,.;]+),\s*(?P<signing2>Kollektivprokura zu zweien)\.\s*"
    r"Neu eingetragene Person:\s*(?P<added>[^,.;]+),\s*von\s+"
    r"(?P<origin>[^,.;]+),\s*in\s+(?P<place>[^,.;]+),\s*"
    r"(?P<signing3>Kollektivprokura zu zweien)\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_UID_BEFORE_PLACE = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}) Aktiven von CHF\s+(?P<assets>[\d'.]+) und "
    r"Passiven\s*\(Fremdkapital\)\s*von CHF\s+(?P<liabilities>[\d'.]+) auf die\s+"
    r"(?P<recipient>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+"
    r"(?P<place>[^.]+)\.\s*Gegenleistung:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_APPOINTED_ADMINISTRATOR = re.compile(
    r"^Le directeur\s+(?P<name>[^,.;]+) est nommé administrateur et "
    r"conti(?:nue|ne) à signer individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_PROXY_GRANTED = re.compile(
    r"^Procuration individuelle a été conférée à l['’](?P<role>associé|associée)\s+"
    r"(?P<name>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_ASSET_TRANSFER_SUPERVISORY = re.compile(
    r"^Transfert de patrimoine:\s*Selon contrat du\s+(?P<date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4}) et selon décision de l['’]autorité de "
    r"surveillance du\s+(?P<approval_date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4}),\s*la fondation a transféré des actifs de CHF\s+"
    r"(?P<assets>[\d'.]+) et des passifs envers les tiers de CHF\s+"
    r"(?P<liabilities>[\d'.]+),\s*à\s+(?P<recipient>.+?)\s+à\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\s*\)\.\s*"
    r"Contre-prestation:\s*(?P<consideration>aucune)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUR_BOARD_MEMBERS = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé président,\s*"
    r"(?P<vice_president>[^,.;]+),\s*de\s+(?P<vice_origin>[^,.;]+),\s*"
    r"vice-président,\s*(?P<secretary>[^,.;]+),\s*de\s+(?P<secretary_origin>[^,.;]+),\s*"
    r"secrétaire,\s*tous les deux à\s+(?P<shared_place>[^,.;]+),\s*et\s*"
    r"(?P<member>[^,.;]+),\s*de\s+(?P<member_origin>[^,.;]+),\s*à\s*"
    r"(?P<member_place>[^,.;]+),\s*(?P<member_country>[A-Z]{2,3})\.\s*"
    r"Signature individuelle du président ou collective à deux des autres membres "
    r"du conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_DIRECTOR_SIGNATURE = re.compile(
    r"^Signature individuelle a été conférée à l['’](?P<role>associé|associée)\s+"
    r"(?P<name>[^,.;]+),\s*nommé(?:e)? (?P<director>directeur|directrice)\.?$",
    re.I | re.UNICODE,
)
_DE_STATUTES_NO_PUBLIC_FACTS = re.compile(
    r"^\[Statutenänderung ohne publikationspflichtige Tatsachen\.?\]\.?$",
    re.I | re.UNICODE,
)
_DE_ASSOCIATION_DELETION_BLOCKED = re.compile(
    r"^Der Verein kann mangels Zustimmung des\s+"
    r"(?P<tax_authority>kantonalen Steueramtes) noch nicht gelöscht werden\.?$",
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
    return f"{year}-{month}-{day}"


def _french_date(raw: str) -> str:
    day, month, year = raw.strip().lower().split()
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


def extract_parser77_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 77."""
    del language  # Historical records can contain a different language in this field.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_FEDERAL_SUSPENSIVE_EFFECT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "fr.text.federal_suspensive_effect.v1",
                {
                    "kind": "federal_proceedings_suspensive_effect",
                    "decision_date": _iso_date(match.group("date")),
                    "authority": match.group("authority"),
                    "proceedings_state_maintained": True,
                    "protective_measures_remain_in_force": True,
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                },
            )
        )

    match = _DE_REMOVED_AND_CHANGED_ASSOCIATES.search(leftover)
    if match:
        consume(match)
        rule_id = "de.persons.removed_and_changed_associates.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", rule_id, match.group("removed"),
                    role="Gesellschafter",
                    extra={
                        "action": "removed",
                        "shares_count": _count(match.group("removed_count")),
                        "shares_nominal": match.group("removed_nominal"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("changed"),
                    place=match.group("place"), role="Gesellschafter und Geschäftsführer",
                    signing="Einzelunterschrift",
                    extra={
                        "action": "shares_and_domicile_changed",
                        "shares_before": _count(match.group("before_count")),
                        "shares_transferred": _count(match.group("count"))
                        - _count(match.group("before_count")),
                        "shares_count": _count(match.group("count")),
                        "shares_nominal": match.group("nominal"),
                    },
                ),
            ]
        )

    match = _FR_COMPANY_NAME_RESTORED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_name_changed", "fr.text.company_name_restored.v1",
                {"action": "restored", "name": match.group("name").strip()},
            )
        )

    match = _FR_ASSOCIATE_NAME_CORRECTION_AND_MANAGER_SIGNING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.associate_correction_and_manager_signing.v1"
        common = {
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
        }
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("name"), role="associé",
                    extra={
                        "action": "corrected",
                        "previous_name": match.group("incorrect_name").strip(),
                        "shares_count": _count(match.group("count")),
                        "shares_nominal": match.group("nominal"),
                        **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("manager"),
                    role="associé-gérant et président", signing="Einzelunterschrift",
                    extra={"action": "appointed_and_signing_granted", **common},
                ),
            ]
        )

    match = _FR_THREE_WAY_SHARE_TRANSFER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.three_way_share_transfer.v1"
        seller = match.group("seller").strip()
        buyer1 = match.group("buyer1").strip()
        buyer2 = match.group("buyer2").strip()
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé",
                extra={
                    "action": "shares_transferred",
                    "counterparties": [buyer1, buyer2],
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("seller_count")),
                    "shares_nominal": match.group("seller_nominal"),
                },
            )
        )
        for index, buyer in ((1, buyer1), (2, buyer2)):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, role="associé",
                    extra={
                        "action": "shares_received",
                        "counterparty": seller,
                        "shares_received": _count(match.group(f"buyer{index}_received")),
                        "shares_count": _count(match.group(f"buyer{index}_count")),
                        "shares_nominal": match.group("buyer_nominal"),
                    },
                )
            )

    match = _IT_CREDIT_SET_OFF_CLAUSE_REPEALED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "it.text.credit_setoff_clause_repealed.v1",
                {"kind": "credit_setoff_clause", "action": "repealed"},
            )
        )

    match = _DE_OWNER_BANKRUPTCY_APPEAL_SUSPENDED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.owner_bankruptcy_appeal_suspended.v1",
                {
                    "kind": "bankruptcy_effect_suspended",
                    "scope": "sole_proprietor_owner",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "authority": match.group("authority"),
                    "bankruptcy_court": match.group("bankruptcy_court").strip(),
                    "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                    "bankruptcy_time": match.group("bankruptcy_time").replace(".", ":"),
                },
            )
        )

    match = _DE_MIXED_PERSON_SECTIONS.search(leftover)
    if match:
        consume(match)
        rule_id = "de.persons.mixed_removed_and_added.v1"
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", rule_id, match.group(f"removed{index}"),
                    signing=match.group(f"signing{index}"), extra={"action": "removed"},
                )
            )
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("added"),
                place=match.group("place"), signing=match.group("signing3"),
                extra={"action": "appointed", "heimat": match.group("origin")},
            )
        )

    match = _DE_ASSET_TRANSFER_UID_BEFORE_PLACE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.asset_transfer_uid_before_place.v1",
                {
                    "date": _iso_date(match.group("date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "currency": "CHF",
                    "liabilities_kind": "third_party_capital",
                    "recipient": match.group("recipient").strip(),
                    "recipient_uid": match.group("uid"),
                    "recipient_place": match.group("place").strip(),
                    "consideration": f"CHF {match.group('consideration')}",
                    "consideration_kind": "cash",
                    "consideration_amount": match.group("consideration"),
                },
            )
        )

    match = _FR_DIRECTOR_APPOINTED_ADMINISTRATOR.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.director_appointed_administrator.v1",
                match.group("name"), role="administrateur", signing="Einzelunterschrift",
                extra={
                    "action": "appointed",
                    "previous_role": "directeur",
                    "signing_continues": True,
                },
            )
        )

    match = _FR_ASSOCIATE_PROXY_GRANTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", "fr.persons.associate_proxy_granted.v1",
                match.group("name"), role=match.group("role").lower(),
                signing="Einzelprokura", extra={"action": "granted"},
            )
        )

    match = _FR_FOUNDATION_ASSET_TRANSFER_SUPERVISORY.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "fr.text.foundation_asset_transfer_supervisory.v1",
                {
                    "date": _french_date(match.group("date")),
                    "supervisory_approval_date": _french_date(match.group("approval_date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "currency": "CHF",
                    "liabilities_kind": "third_party_liabilities",
                    "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration": match.group("consideration").lower(),
                    "gratuitous": True,
                },
            )
        )

    match = _FR_FOUR_BOARD_MEMBERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.four_board_members.v1"
        people = (
            (match.group("president"), None, "président", "Einzelunterschrift", {}),
            (
                match.group("vice_president"), match.group("shared_place"),
                "vice-président", "Kollektivunterschrift zu zweien",
                {"heimat": match.group("vice_origin")},
            ),
            (
                match.group("secretary"), match.group("shared_place"),
                "secrétaire", "Kollektivunterschrift zu zweien",
                {"heimat": match.group("secretary_origin")},
            ),
            (
                match.group("member"), match.group("member_place"),
                "membre du conseil d'administration", "Kollektivunterschrift zu zweien",
                {
                    "heimat": match.group("member_origin"),
                    "country": match.group("member_country"),
                },
            ),
        )
        for name, place, role, signing, extra in people:
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, name, place=place, role=role,
                    signing=signing, extra={"action": "appointed", **extra},
                )
            )

    match = _FR_ASSOCIATE_DIRECTOR_SIGNATURE.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.associate_director_signature.v1",
                match.group("name"),
                role=f"{match.group('role').lower()}-{match.group('director').lower()}",
                signing="Einzelunterschrift",
                extra={"action": "appointed_and_signing_granted"},
            )
        )

    match = _DE_STATUTES_NO_PUBLIC_FACTS.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "de.text.statutes_no_public_facts.v1",
                {"kind": "non_public_facts", "publishable_facts_changed": False},
            )
        )

    match = _DE_ASSOCIATION_DELETION_BLOCKED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.association_deletion_blocked.v1",
                {
                    "kind": "deletion_blocked",
                    "entity": "association",
                    "tax_authority": match.group("tax_authority"),
                    "tax_authority_consent_missing": True,
                },
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
