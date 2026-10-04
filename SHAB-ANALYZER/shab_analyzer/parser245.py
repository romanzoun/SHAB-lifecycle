from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_FR_SIGNATURE_REVOKED_AND_DIRECTOR_APPOINTED = re.compile(
    r"^La signature de\s+(?P<removed>[^.;]+?)\s+est radiée\.\s*"
    r"Signature collective à deux est conférée à\s+(?P<name>[^,.;]+),\s*"
    r"(?:de|du|des|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*(?P<role>directeur),\s*"
    r"(?P<additional_role>membre de la direction générale)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUR_SIGNINGS_SUPPLEMENTED = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est complétée en ce sens que\s+"
    r"(?P<name1>[^,.;]+),\s*(?P<name2>[^,.;]+),\s*"
    r"(?P<name3>[^,.;]+),\s*(?:et\s+)?(?P<name4>[^,.;]+),\s*"
    r"signent collectivement à deux avec un administrateur ou un directeur\.?$",
    re.I | re.UNICODE,
)
_DE_PROVISIONAL_MORATORIUM_LAST_EXTENSION = re.compile(
    r"^Mit Verfügung vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+im summarischen Verfahren letz(?:t|)mals eine "
    r"Verlängerung der provisorischen Nachlassstundung bis zum\s+"
    r"(?P<until>\d{1,2}\.\s+(?:Januar|Februar|März|April|Mai|Juni|Juli|"
    r"August|September|Oktober|November|Dezember)\s+\d{4})\s+gewährt\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_CORRECTION_SAME_VALUE = re.compile(
    r"^\[non:\s*(?P<previous_place>[^()]+?)\s*"
    r"\((?P<previous_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\]\.?\s*"
    r"Nouvelle succursale:\s*(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_FR_PROXY_REVOKED_DEPUTY_DIRECTOR_APPOINTED = re.compile(
    r"^(?P<name>[^,.;]+),\s*dont la procuration est éteinte,\s*est "
    r"nommé(?:e)?\s+(?P<role>directeur adjoint|directrice adjointe)"
    r"(?:\s+avec\s+(?P<signing>signature collective à deux))?\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PRESIDENT_SECRETARY_COLLECTIVE = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*"
    r"(?:de|du|des|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*(?P<president_role>président(?:e)?)\s+et\s+"
    r"(?P<secretary>[^,.;]+),\s*nommé(?:e)?\s+"
    r"(?P<secretary_role>secrétaire),\s*lesquels signent collectivement à deux;\s*"
    r"les pouvoirs de la seconde sont modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_MANAGER_PRESIDENT_NAME_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le nouveau "
    r"gérant président se nomme\s+(?P<name>[^()]+?)\s*"
    r"\(et non\s+(?P<previous_name>[^()]+?)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_ALREADY_CHANGED_FACTS_UNCHANGED = re.compile(
    r"^;?\s*les faits déjà modifiés ne sont pas modifiés\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_ORIGIN_CORRECTED = re.compile(
    r"^L['’]inscription au journal n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que "
    r"l['’](?P<role>administrateur|administratrice)\s+(?P<name>[^,.;]+?)\s+"
    r"est originaire de\s+(?P<origin>.+?)\s+et non pas de\s+"
    r"(?P<previous_origin>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_STATUTES_DATE_SUPPLEMENTED = re.compile(
    r"^L['’]inscription no\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\)\s+est complétée en ce sens "
    r"que les statuts ont été modifiés le\s+"
    r"(?P<statutes_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNATURE_REVOKED_ROLE_CONTINUES = re.compile(
    r"^(?P<name>[^,;]+?),\s*dont la signature est radiée,\s*reste\s+"
    r"(?P<role>membre du conseil de fondation)\.?$",
    re.I | re.UNICODE,
)
_FR_PROXY_GRANTED_DU_ET_AU = re.compile(
    r"^Procuration collective à deux a été conférée à\s+(?P<name>[^,.;]+),\s*"
    r"du et au\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BUSINESS_UNIT_TRANSFER_TWO_DATES_CASH = re.compile(
    r'^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+'
    r'(?P<date1>\d{2}\.\d{2}\.\d{4})/(?P<date2>\d{2}\.\d{2}\.\d{4})\s+'
    r'den Geschäftsbereich\s+["“](?P<business_unit>[^"”]+)["”]\s+mit Aktiven '
    r'von CHF\s+(?P<assets>[\d\'.]+)\s+und Passiven von CHF\s+'
    r'(?P<liabilities>[\d\'.]+)\s*\(Fremdkapital\)\s+auf die\s+'
    r'(?P<recipient>.+?),\s*in\s+(?P<place>[^()]+?)\s*'
    r'\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*Gegenleistung\s*:?\s*CHF\s+'
    r'(?P<consideration>[\d\'.]+)\.?$',
    re.I | re.UNICODE,
)
_FR_INDIVIDUAL_SIGNING_TYPO = re.compile(
    r"^(?P<name>[^,.;]+)\s+signe\s+désromais\s+individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_CAPITAL_REDUCTION_REPLACEMENT_SHARES = re.compile(
    r"^Bei der Kapitalherabsetzung vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"werden\s+(?P<destroyed_count>[\d']+)\s+Stammanteile zu CHF\s+"
    r"(?P<destroyed_nominal>[\d'.]+)\s+vernichtet\.\s*Gleichzeitig werden\s+"
    r"(?P<issued_count>[\d']+)\s+voll liberierte Stammanteile zu CHF\s+"
    r"(?P<issued_nominal>[\d'.]+)\s+ausgegeben\.?$",
    re.I | re.UNICODE,
)
_FR_LIMITED_AUDIT_WAIVED_EFFECTIVE_FISCAL_YEAR = re.compile(
    r"^La société renonce à un contrôle restreint à partir de l['’]exercice "
    r"débutant le\s+(?P<effective_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)

_GERMAN_MONTHS = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _german_date(raw: str) -> str:
    day, month, year = raw.replace(".", "", 1).split()
    return f"{int(year):04d}-{_GERMAN_MONTHS[month.casefold()]:02d}-{int(day):02d}"


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
        role=role.strip() if role else None,
        signing=signing,
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser245_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 245."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_SIGNATURE_REVOKED_AND_DIRECTOR_APPOINTED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.signature_revoked_director_appointed.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("removed"),
                extra={"action": "revoked"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), role=match.group("role"),
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group("origin").strip(),
                    "additional_role": match.group("additional_role").lower(),
                },
            ),
        ], ""

    match = _FR_FOUR_SIGNINGS_SUPPLEMENTED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.four_signings_supplemented.v1"
        reference = {
            "action": "signing_supplemented", "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "with": "un administrateur ou un directeur",
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                signing="Kollektivunterschrift zu zweien", extra=reference,
            )
            for index in (1, 2, 3, 4)
        ], ""

    match = _DE_PROVISIONAL_MORATORIUM_LAST_EXTENSION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.provisional_moratorium_last_extension.v1", {
                "kind": "composition_moratorium_extended", "action": "extended",
                "moratorium_type": "provisional", "last_extension": True,
                "decision_date": _iso_date(match.group("decision_date")),
                "until": _german_date(match.group("until")),
                "authority": match.group("authority").strip(),
                "procedure": "summary",
            },
        )], ""

    match = _FR_BRANCH_CORRECTION_SAME_VALUE.fullmatch(leftover)
    if match and (
        match.group("place").casefold() == match.group("previous_place").casefold()
        and match.group("uid") == match.group("previous_uid")
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.branch_correction_same_value.v1", {
                "kind": "branch", "action": "confirmed_unchanged",
                "place": match.group("place").strip(), "uid": match.group("uid"),
            },
        )], ""

    match = _FR_PROXY_REVOKED_DEPUTY_DIRECTOR_APPOINTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.proxy_revoked_deputy_director_appointed.v1",
            match.group("name"), role=match.group("role").lower(),
            signing=(
                "Kollektivunterschrift zu zweien" if match.group("signing") else None
            ), extra={
                "action": "appointed", "previous_signing": "Kollektivprokura",
                "previous_signing_revoked": True,
            },
        )], ""

    match = _FR_ADMINISTRATION_PRESIDENT_SECRETARY_COLLECTIVE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administration_president_secretary_collective.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                place=match.group("place"), role=match.group("president_role").lower(),
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group("origin").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("secretary"),
                role=match.group("secretary_role").lower(),
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "powers_modified": True,
                },
            ),
        ], ""

    match = _FR_NEW_MANAGER_PRESIDENT_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.persons.manager_president_name_corrected.v1",
            match.group("name"), role="gérant président", extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    if _FR_ALREADY_CHANGED_FACTS_UNCHANGED.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.already_changed_facts_unchanged.v1", {
                "kind": "registry_facts", "action": "confirmed_unchanged",
                "facts_already_changed": True,
            },
        )], ""

    match = _FR_ADMINISTRATOR_ORIGIN_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.persons.administrator_origin_corrected.v1",
            match.group("name"), role=match.group("role").lower(), extra={
                "action": "origin_corrected", "origin": match.group("origin").strip(),
                "previous_origin": match.group("previous_origin").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_STATUTES_DATE_SUPPLEMENTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.statutes_date_supplemented.v1", {
                "kind": "statutes_date", "action": "supplemented",
                "date": _iso_date(match.group("statutes_date")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
            },
        )], ""

    match = _FR_SIGNATURE_REVOKED_ROLE_CONTINUES.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.signature_revoked_role_continues.v1",
            match.group("name"), role=match.group("role").lower(), extra={
                "action": "revoked", "role_continues": True,
            },
        )], ""

    match = _FR_PROXY_GRANTED_DU_ET_AU.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.proxy_granted_du_et_au.v1",
            match.group("name"), place=match.group("place"),
            signing="Kollektivprokura zu zweien", extra={
                "action": "granted", "origin": match.group("place").strip(),
            },
        )], ""

    match = _DE_BUSINESS_UNIT_TRANSFER_TWO_DATES_CASH.fullmatch(leftover)
    if match and _amount(match.group("assets")) == _amount(match.group("consideration")):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.business_unit_transfer_two_dates_cash.v1", {
                "agreement_dates": [
                    _iso_date(match.group("date1")), _iso_date(match.group("date2"))
                ],
                "business_unit": match.group("business_unit").strip(),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital",
                "liabilities_transferred": True, "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"),
                "consideration_kind": "cash",
            },
        )], ""

    match = _FR_INDIVIDUAL_SIGNING_TYPO.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.individual_signing_typo_desromais.v1",
            match.group("name"), signing="Einzelunterschrift",
            extra={"action": "changed", "source_typo": "désromais"},
        )], ""

    match = _DE_CAPITAL_REDUCTION_REPLACEMENT_SHARES.fullmatch(leftover)
    if match and (
        _count(match.group("destroyed_count")) == _count(match.group("issued_count"))
        and _amount(match.group("destroyed_nominal"))
        == _amount(match.group("issued_nominal"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.capital_reduction_replacement_shares.v1", {
                "kind": "capital_reduction_and_replacement", "currency": "CHF",
                "date": _iso_date(match.group("date")),
                "destroyed_shares_count": _count(match.group("destroyed_count")),
                "destroyed_share_kind": "Stammanteile",
                "destroyed_share_nominal": match.group("destroyed_nominal"),
                "issued_shares_count": _count(match.group("issued_count")),
                "issued_share_kind": "Stammanteile",
                "issued_share_nominal": match.group("issued_nominal"),
                "issued_fully_paid": True,
            },
        )], ""

    match = _FR_LIMITED_AUDIT_WAIVED_EFFECTIVE_FISCAL_YEAR.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "audit_requirement_changed",
            "fr.text.limited_audit_waived_effective_fiscal_year.v1", {
                "kind": "limited_audit_waiver", "action": "declared",
                "effective_fiscal_year_start": _iso_date(match.group("effective_date")),
                "limited_audit_waived": True,
            },
        )], ""

    return [], leftover
