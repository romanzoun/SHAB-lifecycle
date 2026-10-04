from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_INSTITUTION_ASSET_TRANSFER = re.compile(
    r"^Vermögensübertragung:\s*Die\s+(?P<source_kind>Anstalt|Gesellschaft|Stiftung|Genossenschaft)\s+"
    r"überträgt gemäss (?:Vermögensübertragungs)?Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+und Inventar per\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven \(Fremdkapital\) von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>.+?)\.?$",
    re.I | re.UNICODE,
)
_DE_ART_934_AOR_SHAB_DELETION_BLOCKED = re.compile(
    r"^Auf die durch das Handelsregisteramt gestützt auf\s+"
    r"(?P<legal_basis>Art\.\s*934 Abs\.\s*2 aOR sowie Art\.\s*152 Abs\.\s*1 HRegV)\s+"
    r"veranlassten und im SHAB mit Meldungsnummern\s+(?P<issues>.+?)\s+publizierten "
    r"Aufforderungen haben sich keine weiteren Betroffenen gemeldet\.\s*Das amtliche "
    r"Verfahren zur Löschung der Rechtseinheit ist damit abgeschlossen\.\s*Sie kann "
    r"mangels Zustimmungen der Eidgenössischen Steuerverwaltung und des kantonalen "
    r"Steueramtes jedoch noch nicht gelöscht werden\.?$",
    re.I | re.UNICODE,
)
_DE_ADDITIONAL_STATUTES_DATES = re.compile(
    r"^(?P<date1>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"(?P<date2>\d{2}\.\d{2}\.\d{4})\.?$",
    re.UNICODE,
)
_FR_THREE_ASSOCIATE_MANAGERS_TRANSFER = re.compile(
    r"^Les associés-gérants\s+(?P<seller1>[^,.;]+),\s*"
    r"(?P<seller2>[^,.;]+),\s*et\s+(?P<seller3>[^,.;]+),\s*"
    r"cèdent chacun\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+de leurs\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<before_nominal>[\d'.]+),\s*à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+?)(?:\s*\((?P<place_canton>[A-Z]{2})\))?,\s*"
    r"nouvel associé sans signature avec\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*(?P=seller1),\s*(?P=seller2),\s*et\s*"
    r"(?P=seller3) restent chacun titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_SHAB_CITATION_CORRECTION = re.compile(
    r"^In TR-Nr\.\s*(?P<entry>[\d']+) vom\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"publiziert im SHAB Nr\.\s*(?P<previous_issue>\d+) vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4}) wurde das SHAB-Zitat irrtümlich falsch "
    r"publiziert\.\s*Es sollte heissen:\s*\(SHAB Nr\.\s*(?P<issue>\d+) vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*Publ\.\s*(?P<reference>\d+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_NAME_LIQUIDATION_COMPLETION = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) est complétée en ce sens que la raison "
    r"sociale devient:\s*(?P<name>.+?en liquidation)\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_ADMINISTRATORS_WITHOUT_SIGNATURE = re.compile(
    r"^Nouveaux administrateurs sans signature:\s*"
    r"(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,.;]+?)(?:\s*\((?P<canton1>[A-Z]{2})\))?,\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*"
    r"à\s+(?P<place2>[^,.;]+?)(?:\s*\((?P<canton2>[A-Z]{2})\))?\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_NAME_AND_SIGNING_CORRECTION = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) est rectifiée comme suit:\s*"
    r"signature individuelle de\s+(?P<name>.+?)\s+\(et non\s+(?P<previous_given>[^)]+)\),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<role>directeur|directrice)\.?$",
    re.I | re.UNICODE,
)
_FR_HEAD_OFFICE_DISSOLUTION_AND_BRANCH_NAME = re.compile(
    r"^La société a été dissoute au siège principal par décision de l['’]assemblée "
    r"générale du\s+(?P<date>\d{1,2}(?:er)?\s+(?:janvier|février|mars|avril|mai|juin|"
    r"juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})\.\s*"
    r"Nouvelle raison de commerce de la succursale:\s*(?P<name>.+?)\.?$",
    re.I | re.UNICODE,
)
_DE_STATUTES_DATE_CORRECTION = re.compile(
    r"^Die Statuten datieren vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+und nicht vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_NEW_SHARES_ONLY = re.compile(
    r"^Aktien neu:\s*(?P<count>[\d']+)\s+(?P<kind>Namenaktien) zu\s+"
    r"(?P<currency>[A-Z]{3})\s+(?P<nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNATURES_REPLACING_PROXY = re.compile(
    r"^Signature individuelle a été conférée à\s+(?P<name1>[^;]+);\s*sa procuration "
    r"est radiée\.\s*Signature collective à deux a été conférée à\s+"
    r"(?P<name2>[^,;]+)\s+et\s+(?P<name3>[^,;]+);\s*leur procuration est radiée\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_APPEAL_GRANTED = re.compile(
    r"^In Gutheissung des Rekurses hat\s+(?P<authority>.+?)\s+mit Entscheid vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}) den Entscheid des\s+"
    r"(?P<bankruptcy_court>.+?) vom\s+(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"mit dem über die Gesellschaft der Konkurs eröffnet wurde,\s*aufgehoben\.\s*"
    r"\[bisher:\s*(?P<previous>.+)\]\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_FR_SIGNING_PAIR_WITH_RESTRICTIONS = re.compile(
    r"^Signature collective à deux,\s*toutefois pas entre eux,\s*ni avec\s+"
    r"(?P<excluded>.+?),\s*est conférée à\s+(?P<name1>[^,;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,;]+),\s*à\s+(?P<place1>[^,;]+),\s*"
    r"et\s+(?P<name2>[^,;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,;]+),\s*"
    r"à\s+(?P<place2>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_FOUNDATION_MEMBERS_WITHOUT_SIGNATURE = re.compile(
    r"^Nouveaux membres du conseil de fondation sans signature:\s*"
    r"(?P<name1>[^,;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,;]+),\s*"
    r"à\s+(?P<place1>[^,;]+?)(?:\s*\((?P<country1>[^)]+)\))?,\s*et\s*"
    r"(?P<name2>[^,;]+),\s*de et à\s+(?P<place2>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_CONTINUATION_LIST = re.compile(
    r"^(?:[^(),.;]+\s*\(CHE-\d{3}\.\d{3}\.\d{3}\),\s*)+"
    r"(?:et\s+)?[^(),.;]+\s*\(CHE-\d{3}\.\d{3}\.\d{3}\)\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_CONTINUATION_ITEM = re.compile(
    r"(?:^|,\s*(?:et\s+)?)(?P<place>[^(),.;]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)",
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
    day, month, year = re.sub(r"(?<=\d)er\b", "", raw.strip().lower()).split()
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


def extract_parser73_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 73."""
    del language  # Historical records can contain a different language in this field.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_INSTITUTION_ASSET_TRANSFER.search(leftover)
    if match:
        consume(match)
        consideration = match.group("consideration").strip()
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.institution_asset_transfer.v1",
                {
                    "source_kind": match.group("source_kind").lower(),
                    "date": _iso_date(match.group("date")),
                    "inventory_date": _iso_date(match.group("inventory_date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "recipient": match.group("recipient").strip().strip('"“”'),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration": consideration,
                    "gratuitous": consideration.lower() == "keine",
                },
            )
        )

    match = _DE_ART_934_AOR_SHAB_DELETION_BLOCKED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.art_934_aor_shab_deletion_blocked.v1",
                {
                    "kind": "deletion_blocked",
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")).strip(),
                    "procedure_completed": True,
                    "issues": re.findall(r"[A-Z]{2}\d{2}-\d+", match.group("issues")),
                    "affected_parties_responded": False,
                    "tax_authority_consent_missing": True,
                    "missing_consents": ["federal_tax_authority", "cantonal_tax_authority"],
                },
            )
        )

    match = _DE_ADDITIONAL_STATUTES_DATES.search(leftover)
    if match:
        consume(match)
        for group in ("date1", "date2"):
            events.append(
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "statutes_changed", "de.text.additional_statutes_date.v1",
                    {"date": _iso_date(match.group(group))},
                )
            )

    match = _FR_THREE_ASSOCIATE_MANAGERS_TRANSFER.search(leftover)
    if match:
        consume(match)
        sellers = [match.group(f"seller{index}").strip() for index in (1, 2, 3)]
        buyer = match.group("buyer").strip()
        rule_id = "fr.persons.three_associate_managers_transfer.v1"
        for seller in sellers:
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé-gérant",
                    extra={
                        "action": "shares_transferred",
                        "counterparty": buyer,
                        "shares_before": _count(match.group("before")),
                        "shares_transferred": _count(match.group("transferred")),
                        "shares_count": _count(match.group("remaining")),
                        "shares_nominal": match.group("remaining_nominal"),
                    },
                )
            )
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé",
                extra={
                    "action": "shares_received",
                    "heimat": match.group("origin").strip(),
                    "place_canton": match.group("place_canton"),
                    "counterparties": sellers,
                    "shares_received": _count(match.group("buyer_count")),
                    "shares_count": _count(match.group("buyer_count")),
                    "shares_nominal": match.group("buyer_nominal"),
                    "without_signature": True,
                },
            )
        )

    match = _DE_SHAB_CITATION_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", "de.text.shab_citation_corrected.v1",
                {
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "previous_issue": match.group("previous_issue"),
                    "previous_date": _iso_date(match.group("previous_date")),
                    "issue": match.group("issue"),
                    "date": _iso_date(match.group("date")),
                    "publication_reference": match.group("reference"),
                },
            )
        )

    match = _FR_COMPANY_NAME_LIQUIDATION_COMPLETION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", "fr.text.company_name_liquidation_completion.v1",
                {
                    "action": "entry_supplemented",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "company_name": match.group("name").strip(),
                    "liquidation_designation": True,
                },
            )
        )

    match = _FR_NEW_ADMINISTRATORS_WITHOUT_SIGNATURE.search(leftover)
    if match:
        consume(match)
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.administrators_without_signature.v1",
                    match.group(f"name{index}"), place=match.group(f"place{index}"),
                    role="administrateur",
                    extra={
                        "action": "appointed",
                        "heimat": match.group(f"origin{index}").strip(),
                        "place_canton": match.group(f"canton{index}"),
                        "without_signature": True,
                    },
                )
            )

    match = _FR_PERSON_NAME_AND_SIGNING_CORRECTION.search(leftover)
    if match:
        consume(match)
        name = match.group("name").strip()
        family_name = name.rsplit(" ", 1)[0]
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", "fr.persons.name_and_signing_corrected.v1",
                name, place=match.group("place"), role=match.group("role"),
                signing="Einzelunterschrift",
                extra={
                    "action": "corrected",
                    "previous_name": f"{family_name} {match.group('previous_given').strip()}",
                    "heimat": match.group("origin").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                },
            )
        )

    match = _FR_HEAD_OFFICE_DISSOLUTION_AND_BRANCH_NAME.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.head_office_dissolution_branch_name.v1"
        events.extend(
            [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "status_changed", rule_id,
                    {
                        "kind": "dissolution",
                        "scope": "head_office",
                        "date": _french_date(match.group("date")),
                        "authority": "assemblée générale",
                    },
                ),
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "company_name_changed", rule_id,
                    {"scope": "branch", "to": match.group("name").strip()},
                ),
            ]
        )

    match = _DE_STATUTES_DATE_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "de.text.statutes_date_corrected.v1",
                {
                    "action": "date_corrected",
                    "date": _iso_date(match.group("date")),
                    "previous_date": _iso_date(match.group("previous_date")),
                },
            )
        )

    match = _DE_NEW_SHARES_ONLY.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.new_shares_only.v1",
                {
                    "kind": "share_structure",
                    "currency": match.group("currency"),
                    "shares_count": _count(match.group("count")),
                    "share_kind": match.group("kind"),
                    "nominal": match.group("nominal"),
                },
            )
        )

    match = _FR_SIGNATURES_REPLACING_PROXY.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.signing_replaced_proxy_revoked.v1"
        for group, signing in (
            ("name1", "Einzelunterschrift"),
            ("name2", "Kollektivunterschrift zu zweien"),
            ("name3", "Kollektivunterschrift zu zweien"),
        ):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", rule_id, match.group(group),
                    signing=signing,
                    extra={
                        "action": "signing_replaced",
                        "previous_signing": "procuration",
                        "previous_signing_revoked": True,
                    },
                )
            )

    match = _DE_BANKRUPTCY_APPEAL_GRANTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.bankruptcy_appeal_granted.v1",
                {
                    "kind": "bankruptcy_revoked",
                    "appeal_outcome": "granted",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                    "authority": match.group("authority").strip(),
                    "bankruptcy_court": match.group("bankruptcy_court").strip(),
                    "previous_status_restored": True,
                    "previous": re.sub(r"\s+", " ", match.group("previous")).strip(),
                },
            )
        )

    match = _FR_SIGNING_PAIR_WITH_RESTRICTIONS.search(leftover)
    if match:
        consume(match)
        excluded = [
            name.strip()
            for name in re.split(r",\s*|\s+et\s+", match.group("excluded"))
            if name.strip()
        ]
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", "fr.persons.signing_pair_restricted.v1",
                    match.group(f"name{index}"), place=match.group(f"place{index}"),
                    signing="Kollektivunterschrift zu zweien",
                    extra={
                        "action": "granted",
                        "heimat": match.group(f"origin{index}").strip(),
                        "not_between_appointees": True,
                        "excluded_cosigners": excluded,
                    },
                )
            )

    match = _FR_NEW_FOUNDATION_MEMBERS_WITHOUT_SIGNATURE.search(leftover)
    if match:
        consume(match)
        people = (
            (match.group("name1"), match.group("origin1"), match.group("place1"), match.group("country1")),
            (match.group("name2"), match.group("place2"), match.group("place2"), None),
        )
        for name, origin, place, country in people:
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.foundation_members_without_signature.v1",
                    name, place=place, role="membre du conseil de fondation",
                    extra={
                        "action": "appointed",
                        "heimat": origin.strip(),
                        "country": country,
                        "without_signature": True,
                    },
                )
            )

    match = _FR_BRANCH_CONTINUATION_LIST.search(leftover)
    if match:
        consume(match)
        for item in _FR_BRANCH_CONTINUATION_ITEM.finditer(match.group(0).rstrip(".")):
            events.append(
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "branch_changed", "fr.text.branch_added_continuation.v1",
                    {
                        "action": "added",
                        "place": item.group("place").strip(),
                        "branch_uid": item.group("uid"),
                    },
                )
            )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
