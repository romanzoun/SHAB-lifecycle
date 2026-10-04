from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_DE_DELETION_BLOCKED_TAX_CONSENTS_TYPO = re.compile(
    r"^Die Gesellschaft kann mangels Zustimmung der kantonalen und der "
    r"eidgenössischen Steuerverwaltungen noch nicht gel+öscht werden\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATIVE_COMMITTEE_MEMBER_WITHOUT_SIGNATURE = re.compile(
    r"^(?P<name>[^,;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,;]+),\s*à\s+(?P<place>[^,;]+),\s*est membre du comité "
    r"administratif;\s*(?:il\s+)?n['’]exerce pas la signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_CROSS_BORDER_MERGER_LUXEMBOURG = re.compile(
    r"^Fusion transfrontalière:\s*reprise des actifs et passifs,\s*au sens de "
    r"l['’](?P<legal_basis>art\.\s*163a LDIP),\s*de\s+"
    r"(?P<absorbed_name>.+?),\s*à\s+(?P<absorbed_place>[^(),]+)\s*"
    r"\((?P<absorbed_country>[^)]+)\)\s*\((?P<registry_id>[^)]+)\),\s*"
    r"selon contrat de fusion du\s+(?P<agreement_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\s+"
    r"et bilan au\s+(?P<balance_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"présentant des actifs de\s+(?P<currency>[A-Z]{3})\s+(?P<assets>[\d'.]+),\s*"
    r"des passifs envers les tiers de\s+(?P=currency)\s+(?P<liabilities>[\d'.]+),\s*"
    r"soit un actif net de\s+(?P=currency)\s+(?P<net_assets>[\d'.]+)\.\s*"
    r"Conformément à l['’]attestation d['’]un expert-réviseur agréé,\s*la société "
    r"reprenante dispose de fonds propres librement disponibles équivalant au "
    r"moins au montant du découvert de la société transférante\.\s*La société "
    r"reprenante détenant l['’]ensemble des actions de la société transférante,\s*"
    r"la fusion ne donne pas lieu à une augmentation du capital,\s*ni à une "
    r"attribution d['’]actions\.?$",
    re.I | re.UNICODE,
)
_DE_PERSON_PREVIOUS_TEXT_COMPLETED = re.compile(
    r"^Bei den Eingetragenen Personen neu oder mutierend wurde bei\s+"
    r"(?P<name>.+?)\s+der bisher Text nicht vollständig aufgeführt\.\s*"
    r"Korrekt sollte die Eintragung lauten:\s*\[bisher:\s*in\s+"
    r"(?P<place>[^,\]]+),\s*(?P<role>[^,\]]+),\s*mit\s+"
    r"(?P<signing>[^,\]]+),\s*mit\s+(?P<count>[\d']+)\s+Stammanteilen "
    r"zu je CHF\s+(?P<nominal>[\d'.]+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_FOUR_FOUNDATION_MEMBERS_WITHOUT_SIGNATURE = re.compile(
    r"^Nouveaux membres du conseil de fondation sans signature:\s*"
    r"(?P<name1>[^,;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,;]+),\s*"
    r"à\s+(?P<place1>[^,;()]+)(?:\s*\((?P<country1>[^)]+)\))?,\s*"
    r"(?P<name2>[^,;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,;]+),\s*"
    r"à\s+(?P<place2>[^,;()]+)(?:\s*\((?P<country2>[^)]+)\))?,\s*"
    r"(?P<name3>[^,;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin3>[^,;]+),\s*"
    r"à\s+(?P<place3>[^,;()]+)(?:\s*\((?P<country3>[^)]+)\))?,\s*et\s*"
    r"(?P<name4>[^,;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin4>[^,;]+),\s*"
    r"à\s+(?P<place4>[^,;()]+)(?:\s*\((?P<country4>[^)]+)\))?\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_PRONOUNCED_WITH_EFFECTIVE_TIME = re.compile(
    r"^La faillite de la société a été prononcée par décision du\s+"
    r"(?P<authority>.+?)\s+du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"avec effet à partir du\s+(?P<effective_date>\d{2}\.\d{2}\.\d{4})\s+à\s+"
    r"(?P<effective_time>\d{1,2}:\d{2})\.\s*Par conséquent,\s*sa raison sociale "
    r"devient:\s*(?P<name>.+? en liquidation)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGERS_LIQUIDATORS_COLLECTIVE = re.compile(
    r"^Liquidateurs:\s*les associés gérants\s+(?P<name1>[^,;]+?)\s+et\s+"
    r"(?P<name2>[^,;]+?),\s*lesquels continuent à signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_PUBLICATION_SUPPLEMENT_HEADING = re.compile(
    r"^Complément:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\.\s*"
    r"(?P<notice_id>\d+)\)\s+est complétée dans ce sens:\s*$",
    re.I | re.UNICODE,
)
_DE_ERASED_SOLE_PROPRIETOR_ASSETS_LIABILITIES_ASSUMED = re.compile(
    r"^Übernimmt Aktiven und Passiven des erloschenen Einzelunternehmens\s+"
    r"(?P<source>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_SIGNATURE_CORRECTED = re.compile(
    r"^L['’]inscription\s+N[°º]\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée comme suit:\s*"
    r"le gérant\s+(?P<name>[^,.;]+)\s+possède une signature collective à deux\s*"
    r"\(et non individuelle\)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_THREE_DIRECT_SIGNINGS = re.compile(
    r"^Administration:\s*(?P<president>[^,;]+),\s*nommé président,\s*"
    r"avec signature individuelle,\s*(?P<name1>[^,;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,;]+),\s*à\s+"
    r"(?P<place1>[^,;]+),?\s+et\s+(?P<name2>[^,;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,;]+),\s*à\s+"
    r"(?P<place2>[^,;]+),\s*tous deux avec signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_DE_HEAD_OFFICE_MERGER_BRANCH_CONTINUES = re.compile(
    r"^Bemerkungen zum Hauptsitz neu:\s*Die bisherige Hauptniederlassung\s+"
    r"(?P<absorbed>.+?)\s+geht infolge Fusion mit der\s+(?P<survivor>.+?)\s*"
    r"\(Firma neu:\s*(?P<new_name>.+?)\)\s+unter\.\s*Die Zweigniederlassung "
    r"der untergehenden Gesellschaft wird neu als Zweigniederlassung der "
    r"übernehmenden Gesellschaft weitergeführt\.?$",
    re.I | re.UNICODE,
)
_FR_GIVEN_NAME_CORRECTED_DIRECT = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<surname>[^,.;]+?)\s+(?P<previous_given>[^,.;\s]+)\s+se prénomme "
    r"en réalité\s+(?P<given>[^,.;\s]+)\.?$",
    re.I | re.UNICODE,
)
_DE_DEED_DATE_CORRECTED = re.compile(
    r"^Das Urkundendatum datiert vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s*"
    r"\[nicht vom\s+(?P<previous_date>\d{2}\.\d{2}\.\d{4})\]\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_APPOINTED_DIRECTOR_INDIVIDUAL = re.compile(
    r"^L['’]administratrice\s+(?P<name>[^,.;]+),\s*nommée directrice,\s*"
    r"signe désormais individuellement;\s*ses pouvoirs sont modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_DE_THREE_REGISTERED_PERSON_CHANGES = re.compile(
    r"^Eingetragene Personen geändert:\s*(?P<items>.+)$",
    re.I | re.UNICODE,
)
_DE_REGISTERED_PERSON_CHANGE_ITEM = re.compile(
    r"^(?P<name>.+?),?\s+Gesellschafter,\s*"
    r"(?P<old_count>[\d']+)\s+Stammanteile zu CHF\s+(?P<old_nominal>[\d'.]+),\s*"
    r"(?P<old_role>(?:vorsitzender\s+)?Geschäftsführer),\s*"
    r"(?P<old_signing>Kollektivunterschrift zu zweien|ohne Unterschrift),\s*"
    r"neu Gesellschafter,\s*(?P<new_count>[\d']+)\s+Stammanteile zu CHF\s+"
    r"(?P<new_nominal>[\d'.]+),\s*(?:(?P<new_role>(?:vorsitzdender|vorsitzender)\s+"
    r"Geschäftsführer),\s*)?(?P<new_signing>Kollektivunterschrift zu zweien|"
    r"ohne Unterschrift)\.?$",
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
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _money(raw: str) -> Decimal:
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


def extract_parser208_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 208."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    if _DE_DELETION_BLOCKED_TAX_CONSENTS_TYPO.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.deletion_blocked_tax_consents_typo.v1", {
                "kind": "deletion_blocked", "action": "pending",
                "reason": "missing_tax_authority_consents",
                "tax_authorities": ["cantonal", "federal"],
                "tax_authority_consent_missing": True,
            },
        )], ""

    match = _FR_ADMINISTRATIVE_COMMITTEE_MEMBER_WITHOUT_SIGNATURE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed",
            "fr.persons.administrative_committee_member_without_signature.v1",
            match.group("name"), place=match.group("place"),
            role="membre du comité administratif", extra={
                "action": "appointed", "origin": match.group("origin").strip(),
                "without_signature": True,
            },
        )], ""

    match = _FR_CROSS_BORDER_MERGER_LUXEMBOURG.fullmatch(leftover)
    if match and (
        _money(match.group("assets")) - _money(match.group("liabilities"))
        == _money(match.group("net_assets"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "fr.text.cross_border_merger_luxembourg.v1", {
                "kind": "cross_border_merger", "direction": "inbound",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_country": match.group("absorbed_country").strip(),
                "absorbed_registry_id": match.group("registry_id").strip(),
                "agreement_date": _french_date(match.group("agreement_date")),
                "balance_date": _french_date(match.group("balance_date")),
                "currency": match.group("currency").upper(),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "net_assets": match.group("net_assets"),
                "expert_confirmation": True, "same_shareholder": True,
                "capital_increase": False, "share_allocation": False,
            },
        )], ""

    match = _DE_PERSON_PREVIOUS_TEXT_COMPLETED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.previous_text_completed_shares.v1",
            match.group("name"), role=match.group("role").strip(),
            signing=match.group("signing").strip(), extra={
                "action": "previous_text_completed",
                "previous_place": match.group("place").strip(),
                "shares_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"), "currency": "CHF",
            },
        )], ""

    match = _FR_FOUR_FOUNDATION_MEMBERS_WITHOUT_SIGNATURE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.four_foundation_members_without_signature.v1"
        events = []
        for index in range(1, 5):
            extra = {
                "action": "appointed",
                "origin": match.group(f"origin{index}").strip(),
                "without_signature": True,
            }
            country = match.group(f"country{index}")
            if country:
                extra["country"] = country.strip()
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role="membre du conseil de fondation", extra=extra,
            ))
        return events, ""

    match = _FR_BANKRUPTCY_PRONOUNCED_WITH_EFFECTIVE_TIME.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.bankruptcy_pronounced_effective_time.v1", {
                "kind": "bankruptcy", "action": "opened",
                "authority": match.group("authority").strip(),
                "decision_date": _iso_date(match.group("decision_date")),
                "effective_date": _iso_date(match.group("effective_date")),
                "effective_time": match.group("effective_time"),
                "new_name": match.group("name").strip(),
            },
        )], ""

    match = _FR_ASSOCIATE_MANAGERS_LIQUIDATORS_COLLECTIVE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.associate_managers_liquidators_collective.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="associé-gérant et liquidateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_liquidator", "signing_continues": True,
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_PUBLICATION_SUPPLEMENT_HEADING.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.publication_supplement_heading.v1", {
                "kind": "publication_supplement", "action": "supplemented",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        )], ""

    match = _DE_ERASED_SOLE_PROPRIETOR_ASSETS_LIABILITIES_ASSUMED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred",
            "de.text.erased_sole_proprietor_assets_liabilities_assumed.v1", {
                "action": "assumed", "source_kind": "sole_proprietor",
                "source": match.group("source").strip(),
                "source_uid": match.group("uid"),
                "source_place": match.group("place").strip(),
                "source_erased": True, "assets_transferred": True,
                "liabilities_transferred": True, "amounts_omitted_in_source": True,
            },
        )], ""

    match = _FR_MANAGER_SIGNATURE_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.manager_signature_corrected.v1",
            match.group("name"), role="gérant",
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "publication_corrected",
                "previous_signing": "Einzelunterschrift",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_ADMINISTRATION_THREE_DIRECT_SIGNINGS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administration_three_direct_signings.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président", signing="Einzelunterschrift",
                extra={"action": "appointed_president"},
            ),
            *[
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    place=match.group(f"place{index}"), role="administrateur",
                    signing="Kollektivunterschrift zu zweien", extra={
                        "action": "appointed",
                        "origin": match.group(f"origin{index}").strip(),
                    },
                )
                for index in (1, 2)
            ],
        ], ""

    match = _DE_HEAD_OFFICE_MERGER_BRANCH_CONTINUES.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.head_office_merger_branch_continues.v1", {
                "action": "continued_after_head_office_merger",
                "absorbed_head_office": match.group("absorbed").strip(),
                "surviving_company_previous_name": match.group("survivor").strip(),
                "surviving_company_name": match.group("new_name").strip(),
                "branch_continues": True,
            },
        )], ""

    match = _FR_GIVEN_NAME_CORRECTED_DIRECT.fullmatch(leftover)
    if match:
        surname = match.group("surname").strip()
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.given_name_corrected_direct.v2",
            f"{surname} {match.group('given')}", extra={
                "action": "first_name_corrected",
                "previous_name": f"{surname} {match.group('previous_given')}",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _DE_DEED_DATE_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.deed_date_corrected.v1", {
                "kind": "deed_date", "action": "corrected",
                "date": _iso_date(match.group("date")),
                "previous_date": _iso_date(match.group("previous_date")),
            },
        )], ""

    match = _FR_ADMINISTRATOR_APPOINTED_DIRECTOR_INDIVIDUAL.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed",
            "fr.persons.administrator_appointed_director_individual.v1",
            match.group("name"), role="administratrice et directrice",
            signing="Einzelunterschrift", extra={
                "action": "appointed_director_and_signing_changed",
                "powers_modified": True,
            },
        )], ""

    match = _DE_THREE_REGISTERED_PERSON_CHANGES.fullmatch(leftover)
    if match:
        items = [item.strip() for item in match.group("items").split(";")]
        item_matches = [_DE_REGISTERED_PERSON_CHANGE_ITEM.fullmatch(item) for item in items]
        if len(item_matches) == 3 and all(item_matches):
            rule_id = "de.persons.three_registered_person_changes.v1"
            events = []
            for item_match in item_matches:
                assert item_match is not None
                new_role = item_match.group("new_role")
                if new_role:
                    new_role = re.sub(
                        r"^vorsitzdender", "vorsitzender", new_role, flags=re.I
                    )
                new_signing = item_match.group("new_signing")
                signing = (
                    "Kollektivunterschrift zu zweien"
                    if new_signing.lower().startswith("kollektiv") else None
                )
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, item_match.group("name"),
                    role=(
                        f"Gesellschafter und {new_role}"
                        if new_role else "Gesellschafter"
                    ),
                    signing=signing, extra={
                        "action": "role_and_signing_changed",
                        "shares_count": _count(item_match.group("new_count")),
                        "share_nominal": item_match.group("new_nominal"),
                        "currency": "CHF",
                        "previous_role": (
                            "Gesellschafter und "
                            f"{item_match.group('old_role').strip()}"
                        ),
                        "previous_signing": item_match.group("old_signing"),
                        "without_signature": signing is None,
                    },
                ))
            return events, ""

    return [], leftover
