from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_IT_COMPANY_REINSTATED_IN_LIQUIDATION_ART_164 = re.compile(
    r"^Con decreto della\s+(?P<authority>.+?)\s+del\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+la società è reiscritta come "
    r"società in liquidazione giusta\s+"
    r"(?P<legal_basis>l['’]art\.\s*164 cpv\.\s*1 lett\.\s*a\)\s*e\s*b\)\s*ORC)\.\s*"
    r"I fatti iscritti relativi al liquidatore e all['’]indirizzo della "
    r"liquidazione restano validi\.\s*\[finora:\s*(?P<previous>.+?)\]\.?$",
    re.I | re.UNICODE,
)
_DE_OUTGOING_SPIN_OFF_ASSETS_ONLY = re.compile(
    r"^Abspaltung:\s*Ein Teil der Aktiven geht gemäss\s+"
    r"(?P<document>Spaltungsplan|Spaltungsvertrag)\s+vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+auf die\s+"
    r"(?P<recipient>.+?),\s*in\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+über\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBERS_WITHOUT_SIGNATURE_TRIPLE = re.compile(
    r"^Nouveaux membres du conseil de fondation sans signature:\s*"
    r"(?P<name1>[^,.;]+),\s*de et à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*d['’](?P<origin2>[^,.;]+),\s*"
    r"à\s+(?P<place2>[^,.;]+),\s*et\s+"
    r"(?P<name3>[^,.;]+),\s*de et à\s+(?P<place3>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_SUSPENSION_REVOKED_AND_REOPENED = re.compile(
    r"^Mit Verfügung des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde die Konkurseinstellung "
    r"vom\s+(?P<suspension_date>\d{2}\.\d{2}\.\d{4})\s+widerrufen\.\s*"
    r"Infolgedessen ist über diese Gesellschaft mit Wirkung ab dem\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}[.:]\d{2})\s+Uhr,\s*der Konkurs "
    r"wiedereröffnet worden\.\s*\[bisher:\s*(?P<previous>.+?)\]\.?$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_EXTENDED_GRANTED_HISTORY = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+die mit Verfügung vom\s+"
    r"(?P<grant_date>\d{2}\.\d{2}\.\d{4})\s+gewährte definitive "
    r"Nachlassstundung bis\s+(?P<until>\d{2}\.\d{2}\.\d{4})\s+verlängert\.\s*"
    r"\[bisher:\s*Mit Entscheid vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<previous_authority>.+?)\s+die mit Verfügung vom\s+"
    r"(?P<previous_grant_date>\d{2}\.\d{2}\.\d{4})\s+gewährte definitive "
    r"Nachlassstundung um weitere\s+(?P<previous_duration>.+?)\s+bis\s+"
    r"(?P<previous_until>\d{2}\.\d{2}\.\d{4})\s+verlängert\.\]\.?$",
    re.I | re.UNICODE,
)
_IT_DEFINITIVE_MORATORIUM_EXTENDED = re.compile(
    r"^Con decreto del\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>.+?)\s+ha prorogato la concessione della moratoria "
    r"definitiva a scopo di concordato fino al\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_PRESIDENT_ADMINISTRATOR = re.compile(
    r"^Nouvelle administratrice présidente\s*:\s*(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_AND_ASSOCIATE_MANAGERS = re.compile(
    r"^(?P<seller>[^,.;]+)\s+a cédé\s+(?P<transferred>[\d']+)\s+parts de "
    r"CHF\s+(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+)\.\s*"
    r"Associés-gérants:\s*(?P=seller),\s*pour\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+(?P<seller_nominal>[\d'.]+),\s*"
    r"nommé président,\s*et\s+(?P=buyer)\s+pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"jusqu['’]ici directrice,\s*tous deux\.?$",
    re.I | re.UNICODE,
)
_IT_BRANCH_ADDITIONAL_ADDRESS_REMOVED = re.compile(
    r"^,?\s*Sede principale a:\s*(?P<head_office>[^.]+)\.\s*"
    r"Nuove disposizioni per la succursale:\s*\[radiati:\s*"
    r"Ulteriore indirizzo:\s*(?P<street>[^,\]]+),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<locality>[^.\]]+)\.\s*\]\.?$",
    re.I | re.UNICODE,
)
_FR_PROXY_REVOKED_DIRECTOR_APPOINTED_AND_SIGNING_CHANGED = re.compile(
    r"^(?P<name>[^,.;]+),\s*maintenant à\s+(?P<place>[^(),.;]+)\s*"
    r"\((?P<country>[^)]+)\),\s*dont la procuration est éteinte,\s*"
    r"est nommé\s+(?P<role>directeur)\s+et engage désormais la société par sa "
    r"signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_FR_CONDITIONAL_CAPITAL_CLAUSES_REPLACED = re.compile(
    r"^L['’]assemblée générale a supprimé une clause statutaire relative à une "
    r"augmentation conditionnelle du capital\s*\(selon décision du\s+"
    r"(?P<share_clause_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\)\s+et une clause "
    r"statutaire relative à une augmentation conditionnelle du capital participation\s*"
    r"\(selon décision du\s+"
    r"(?P<participation_clause_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\)\s+"
    r"par décision du\s+(?P<removal_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.\s*"
    r"L['’]assemblée générale a introduit une clause statutaire relative à une "
    r"augmentation conditionnelle du capital-participation par décision du\s+"
    r"(?P<introduction_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.\s*"
    r"Pour les détails,\s*voir les statuts\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_PROPRIETOR_EQUIPMENT_TRANSFER = re.compile(
    r"^Transfert de patrimoine:\s*Selon contrat du\s+"
    r"(?P<date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*le titulaire a transféré\s+"
    r"(?P<assets_description>.+?),\s*pour CHF\s+(?P<assets>[\d'.]+),\s*à\s+"
    r"(?P<recipient>.+?)\s+à\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*Contre-prestation:\s*"
    r"(?P<shares_count>[\d']+)\s+parts sociales de CHF\s+"
    r"(?P<share_nominal>[\d'.]+)\s+et une créance de CHF\s+"
    r"(?P<claim>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_IT_COMPANY_TRANSLATIONS_REMOVED = re.compile(
    r"^Nuove traduzioni della ragione sociale:\s*\[Le traduzioni saranno "
    r"radiate dal Registro di commercio\]\.?$",
    re.I | re.UNICODE,
)
_DE_CROSS_BORDER_MERGER_LIECHTENSTEIN_LLC = re.compile(
    r"^Grenzüberschreitende Fusion gemäss\s+(?P<legal_basis>Art\.\s*163a IPRG):\s*"
    r"Übernahme der Aktiven und Passiven der\s+(?P<absorbed_name>.+?),\s*in\s+"
    r"(?P<absorbed_place>[^()]+?)\s*\((?P<absorbed_country>[A-Z]{2})\)\s*"
    r"\((?P<absorbed_registry_id>[^)]+)\),\s*einer\s+"
    r"(?P<absorbed_legal_form>.+?)\s+nach\s+(?P<governing_law>.+?)\s+Recht,\s*"
    r"gemäss Fusionsvertrag vom\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"und Bilanz per\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"Aktiven von\s+(?P<currency>[A-Z]{3})\s+(?P<assets>[\d'.]+)\s+und Passiven "
    r"\(Fremdkapital\) von\s+(?P=currency)\s+(?P<liabilities>[\d'.]+)\s+gehen "
    r"auf die übernehmende Gesellschaft über\.\s*Da dieselbe Gesellschafterin "
    r"sämtliche Aktien und den Stammanteil der an der Fusion beteiligten "
    r"Gesellschaften hält,\s*findet weder eine Kapitalerhöhung noch eine "
    r"Zuteilung von Stammanteilen statt\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_LEGACY_CONTRIBUTION_REMAINDER = re.compile(
    r'^eingetragenen Einzelfirma\s+"(?P<source>[^"]+)",\s*in\s+'
    r"(?P<place>[^,.;]+),\s*gemäss Sacheinlagevertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Übernahmebilanz per\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\s+mit Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven von CHF\s+(?P<liabilities>[\d'.]+),\s*"
    r"wofür\s+(?P<count1>[\d']+)\s+Namenaktien zu CHF\s+"
    r"(?P<nominal1>[\d'.-]+)\s+und\s+(?P<count2>[\d']+)\s+Namenaktien zu CHF\s+"
    r"(?P<nominal2>[\d'.-]+)\s+ausgegeben und CHF\s+(?P<claim>[\d'.]+)\s+"
    r"als Forderung gutgeschrieben werden\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_PURPOSE_AND_STATUTES_FRAGMENT_WITH_PAIR_ORIGIN_CHANGED = re.compile(
    r"^But et\s*\.\s*(?P<name1>[^,.;]+?)\s+et\s+(?P<name2>[^,.;]+?)\s+"
    r"sont maintenant originaires d['’](?P<origin>[^,.;]+)\.?$",
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
    day, month, year = raw.lower().replace("1er", "1").split()
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


def extract_parser110_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 110."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _IT_COMPANY_REINSTATED_IN_LIQUIDATION_ART_164.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.company_reinstated_liquidation_art_164_ab.v1",
            {
                "kind": "registration_reinstated",
                "action": "reinstated_in_liquidation",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "liquidator_entry_preserved": True,
                "liquidation_address_preserved": True,
                "previous": match.group("previous").strip(),
            },
        ))

    match = _DE_OUTGOING_SPIN_OFF_ASSETS_ONLY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.outgoing_spin_off_assets_only.v1",
            {
                "kind": "spin_off_distribution",
                "date": _iso_date(match.group("date")),
                "document": match.group("document").lower(),
                "scope": "part_of_assets",
                "liabilities_transferred": False,
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
            },
        ))

    match = _FR_FOUNDATION_MEMBERS_WITHOUT_SIGNATURE_TRIPLE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.foundation_members_without_signature_triple.v1"
        people = (
            (match.group("name1"), match.group("place1"), match.group("place1")),
            (match.group("name2"), match.group("place2"), match.group("origin2")),
            (match.group("name3"), match.group("place3"), match.group("place3")),
        )
        for name, place, origin in people:
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, name, place=place,
                role="membre du conseil de fondation",
                extra={
                    "action": "appointed",
                    "heimat": origin.strip(),
                    "without_signature": True,
                },
            ))

    match = _DE_BANKRUPTCY_SUSPENSION_REVOKED_AND_REOPENED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_suspension_revoked_reopened.v1",
            {
                "kind": "bankruptcy_reopened",
                "action": "reopened_after_suspension_revoked",
                "decision_date": _iso_date(match.group("decision_date")),
                "suspension_date": _iso_date(match.group("suspension_date")),
                "effective_date": _iso_date(match.group("effective_date")),
                "effective_time": match.group("effective_time").replace(".", ":"),
                "authority": match.group("authority").strip(),
                "previous": match.group("previous").strip(),
            },
        ))

    match = _DE_DEFINITIVE_MORATORIUM_EXTENDED_GRANTED_HISTORY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.definitive_moratorium_extended_grant_history.v1",
            {
                "kind": "composition_moratorium_extended",
                "moratorium_type": "definitive",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "grant_date": _iso_date(match.group("grant_date")),
                "until": _iso_date(match.group("until")),
                "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                "previous_until": _iso_date(match.group("previous_until")),
                "previous_duration": match.group("previous_duration").strip(),
            },
        ))

    match = _IT_DEFINITIVE_MORATORIUM_EXTENDED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.definitive_moratorium_extended.v1",
            {
                "kind": "composition_moratorium_extended",
                "moratorium_type": "definitive",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "until": _iso_date(match.group("until")),
            },
        ))

    match = _FR_NEW_PRESIDENT_ADMINISTRATOR.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.new_president_administrator.v1",
            match.group("name"), place=match.group("place"), role="présidente",
            extra={
                "action": "appointed",
                "heimat": match.group("origin").strip(),
                "board_role": "administratrice présidente",
            },
        ))

    match = _FR_SHARE_TRANSFER_AND_ASSOCIATE_MANAGERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.share_transfer_associate_managers.v1"
        transferred = _count(match.group("transferred"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller"),
                role="associé-gérant président",
                extra={
                    "action": "shares_transferred_and_appointed_president",
                    "counterparty": match.group("buyer").strip(),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("seller_nominal"),
                    "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"),
                role="associée-gérante",
                extra={
                    "action": "shares_received_and_appointed_manager",
                    "counterparty": match.group("seller").strip(),
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"),
                    "currency": "CHF",
                    "previous_role": "directrice",
                },
            ),
        ])

    match = _IT_BRANCH_ADDITIONAL_ADDRESS_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "it.text.branch_additional_address_removed.v1",
            {
                "action": "additional_address_removed",
                "head_office": match.group("head_office").strip(),
                "address": (
                    f"{match.group('street').strip()}, "
                    f"{match.group('postal_code')} {match.group('locality').strip()}"
                ),
                "street": match.group("street").strip(),
                "postal_code": match.group("postal_code"),
                "locality": match.group("locality").strip(),
            },
        ))

    match = _FR_PROXY_REVOKED_DIRECTOR_APPOINTED_AND_SIGNING_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.proxy_revoked_director_appointed_signing.v1",
            match.group("name"), place=match.group("place"),
            role=match.group("role").lower(), signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "appointed_and_signing_changed",
                "country": match.group("country").strip(),
                "domicile_changed": True,
                "previous_signing": "procuration",
                "procuration_revoked": True,
            },
        ))

    match = _FR_CONDITIONAL_CAPITAL_CLAUSES_REPLACED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.conditional_capital_clauses_replaced.v1"
        removal_date = _french_date(match.group("removal_date"))
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "kind": "conditional_share_capital_clause",
                    "action": "removed",
                    "original_decision_date": _french_date(match.group("share_clause_date")),
                    "decision_date": removal_date,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "kind": "conditional_participation_capital_clause",
                    "action": "removed",
                    "original_decision_date": _french_date(match.group("participation_clause_date")),
                    "decision_date": removal_date,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "kind": "conditional_participation_capital_clause",
                    "action": "introduced",
                    "decision_date": _french_date(match.group("introduction_date")),
                    "details_in_statutes": True,
                },
            ),
        ])

    match = _FR_SOLE_PROPRIETOR_EQUIPMENT_TRANSFER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.sole_proprietor_equipment_transfer.v1",
            {
                "date": _french_date(match.group("date")),
                "scope": "specified_assets",
                "assets_description": match.group("assets_description").strip(),
                "assets": match.group("assets"),
                "liabilities_transferred": False,
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "currency": "CHF",
                "consideration": {
                    "shares_count": _count(match.group("shares_count")),
                    "share_nominal": match.group("share_nominal"),
                    "claim": match.group("claim"),
                },
            },
        ))

    match = _IT_COMPANY_TRANSLATIONS_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_name_changed", "it.text.company_translations_removed.v1",
            {
                "action": "translations_removed",
                "registry_updated": True,
            },
        ))

    match = _DE_CROSS_BORDER_MERGER_LIECHTENSTEIN_LLC.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "de.text.cross_border_merger_liechtenstein_llc.v1",
            {
                "kind": "cross_border_merger",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_country": match.group("absorbed_country"),
                "absorbed_registry_id": match.group("absorbed_registry_id").strip(),
                "absorbed_legal_form": match.group("absorbed_legal_form").strip(),
                "governing_law": match.group("governing_law").strip(),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "currency": match.group("currency").upper(),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "same_shareholder": True,
                "capital_increase": False,
                "share_allocation": False,
            },
        ))

    match = _DE_REMOVED_LEGACY_CONTRIBUTION_REMAINDER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.removed_legacy_contribution_remainder.v1",
            {
                "kind": "legacy_contribution_in_kind_clause",
                "action": "removed",
                "source": match.group("source").strip(),
                "source_place": match.group("place").strip(),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "currency": "CHF",
                "issued_shares": [
                    {
                        "count": _count(match.group("count1")),
                        "nominal": match.group("nominal1"),
                        "kind": "Namenaktien",
                    },
                    {
                        "count": _count(match.group("count2")),
                        "nominal": match.group("nominal2"),
                        "kind": "Namenaktien",
                    },
                ],
                "claim": match.group("claim"),
            },
        ))

    match = _FR_PURPOSE_AND_STATUTES_FRAGMENT_WITH_PAIR_ORIGIN_CHANGED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.purpose_fragment_pair_origin_changed.v1"
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "purpose_changed", rule_id,
            {
                "action": "changed",
                "details_published": False,
                "statutes_also_changed": True,
            },
        ))
        for name_group in ("name1", "name2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(name_group),
                extra={
                    "action": "origin_changed",
                    "heimat": match.group("origin").strip(),
                    "origin_changed": True,
                },
            ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
