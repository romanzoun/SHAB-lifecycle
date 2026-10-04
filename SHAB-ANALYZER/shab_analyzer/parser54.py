from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_SHARE_TRANSFER_RESTRICTION_REMOVED = re.compile(
    r"Les\s+(?P<count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+ne sont\s+(?:désormais\s+)?plus restreintes quant à "
    r"(?:la|leur) transmissibilité\s*(?:selon\s+l['’]art\.\s*685a,\s*al\.\s*3\s*CO|"
    r"\(art\.\s*685a,\s*al\.\s*3\s*CO\))\.?,?",
    re.I,
)
_DE_ART_934_SHAB_CANTONAL_DELETION_BLOCKED = re.compile(
    r"Auf die durch das Handelsregisteramt gestützt auf Art\.\s*934 Abs\.\s*2 OR "
    r"sowie Art\.\s*152 Abs\.\s*1 HRegV veranlassten und im SHAB mit "
    r"Meldungsnummern\s+(?P<issues>.+?)\s+publizierten Aufforderungen haben sich "
    r"keine weiteren Betroffenen gemeldet\.\s*Das amtliche Verfahren zur Löschung "
    r"der Rechtseinheit ist damit abgeschlossen\.\s*Sie kann mangels Zustimmung "
    r"(?:des|der) kantonalen Steueramtes(?:\s+jedoch)?\s+noch nicht gelöscht werden\.?,?",
    re.I | re.DOTALL,
)
_FR_PERSON_NAME_CHANGED_NOW = re.compile(
    r"(?P<old_name>[A-ZÀ-Ÿ][\wÀ-ÿ'’\-]+(?:\s+[\wÀ-ÿ'’\-]+){1,7})\s+"
    r"se nomme maintenant\s+"
    r"(?P<name>[A-ZÀ-Ÿ][\wÀ-ÿ'’\-]+(?:\s+[\wÀ-ÿ'’\-]+){0,7})\.?,?",
    re.UNICODE,
)
_DE_NON_REGISTERABLE_REMARK_REMOVED = re.compile(
    r"\[Streichung der Bemerkung, da nicht zum Eintragungstext gehörend\]\s*"
    r"\[gestrichen:\s*(?P<removed>[^\]]+)\]\.?,?",
    re.I | re.DOTALL,
)
_IT_STANDALONE_STATUTES_DATE = re.compile(r"(?P<date>\d{2}\.\d{2}\.\d{4})")
_FR_LEGAL_BEARER_AND_PARTICIPATION_CONVERSION = re.compile(
    r"Le\s+(?P<date>\d{2}\.\d{2}\.\d{4}|\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4}),\s*les actions au porteur et bons de "
    r"participation au porteur ont été convertis de par la loi en actions "
    r"nominatives et bons de participation(?: au porteur)? nominatifs\.\s*"
    r"Les statuts de la société n['’]ont pas encore été adaptés à la conversion,\s*"
    r"mais devront l['’]être lors de la prochaine modification\.\s*"
    r"Capital-actions:\s*CHF\s+(?P<share_total>[\d'.]+),\s*libéré à concurrence "
    r"de CHF\s+(?P<share_paid>[\d'.]+),\s*divisé en\s+"
    r"(?P<share_count1>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<share_nominal1>[\d'.]+),\s*"
    r"(?P<share_rights>avec restrictions quant à la transmissibilité selon statuts),\s*"
    r"et\s+(?P<share_count2>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<share_nominal2>[\d'.]+)\.\s*"
    r"Capital-participation:\s*CHF\s+(?P<participation_total>[\d'.]+),\s*"
    r"libéré à concurrence de CHF\s+(?P<participation_paid>[\d'.]+),\s*"
    r"divisé en\s+(?P<participation_count>[\d']+)\s+bons de participation "
    r"nominatifs de CHF\s+(?P<participation_nominal>[\d'.]+)\.?,?",
    re.I,
)
_FR_SHARE_CAPITAL_STRUCTURE = re.compile(
    r"Capital-actions:\s*CHF\s+(?P<total>[\d'.]+),\s*libéré à concurrence de "
    r"CHF\s+(?P<paid>[\d'.]+),\s*divisé en\s+(?P<count>[\d']+)\s+"
    r"actions nominatives de CHF\s+(?P<nominal>[\d'.]+)\.?,?",
    re.I,
)
_DE_SPIN_OFF_ACQUISITION = re.compile(
    r"Spaltung:\s*Die Gesellschaft übernimmt von der\s+(?P<source>.+?),\s*in\s+"
    r"(?P<source_place>[^()]+?)\s*\((?P<source_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"einen Teil des Vermögens\.\s*Die Gesellschaft übernimmt dabei gemäss "
    r"Spaltungsvertrag vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von "
    r"CHF\s*(?P<assets>[\d'.]+)\s+und Passiven \(Fremdkapital\) von "
    r"CHF\s*(?P<liabilities>[\d'.]+)\.\s*Da die mitgliedschaftliche Kontinuität "
    r"gewahrt ist,\s*findet weder eine Kapitalerhöhung noch eine Zuteilung von "
    r"Aktien statt\.?,?",
    re.I | re.DOTALL,
)
_DE_LEGAL_BEARER_CONVERSION_ADAPTED = re.compile(
    r"Die Inhaberaktien sind am\s+(?P<conversion_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"von Gesetzes wegen in Namenaktien umgewandelt worden\.\s*Mit Beschluss der "
    r"Generalversammlung vom\s+(?P<adaptation_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"wurden die Statuten der Gesellschaft an die Umwandlung angepasst\.?,?",
    re.I,
)
_FR_ASSET_TRANSFER_WITH_NAMED_AGREEMENT = re.compile(
    r"Transfert de patrimoine:\s*selon contrat de transfert de patrimoine du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré certains actifs "
    r"pour CHF\s+(?P<assets>[\d'.]+)\s+et certains passifs envers les tiers pour "
    r"CHF\s+(?P<liabilities>[\d'.]+),\s*soit un actif net de CHF\s+"
    r"(?P<net>[\d'.]+)\s+à la société anonyme\s+(?P<recipient>.+?),\s*à\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*(?P<consideration>.+?)(?=\s*$)",
    re.I | re.DOTALL,
)
_DE_FUSION_WITH_POST_UID_PLACE = re.compile(
    r"Fusion:\s*Übernahme der Aktiven und der Passiven der\s+"
    r"(?P<absorbed_name>.+?)\s*\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"in\s+(?P<absorbed_place>.+?),\s*gemäss Fusionsvertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Bilanz per\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\.\s*Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven \(Fremdkapital\) von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+gehen auf die übernehmende Gesellschaft über\.\s*"
    r"Da die übernehmende Gesellschaft sämtliche (?:Stammanteile|Aktien) der "
    r"übertragenden Gesellschaft hält,\s*findet weder eine Kapitalerhöhung noch "
    r"eine Aktienzuteilung statt\.?,?",
    re.I | re.DOTALL,
)
_FR_SOLE_PROPRIETOR_DELETED_CONTINUED = re.compile(
    r"L['’]entreprise individuelle est radiée,\s*les activités continuant sous "
    r"une autre forme juridique\.?,?",
    re.I,
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


def _fr_date(raw: str) -> str:
    if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", raw):
        return _iso_date(raw)
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
    rule_id: str,
    name: str,
    payload: dict,
) -> Event:
    clean_name = name.strip()
    return Event(
        publication_id=publication_id,
        published_at=published_at,
        event_type="officer_changed",
        rule_id=rule_id,
        org_uid=org_uid,
        person_key=person_key(name=clean_name),
        plz=plz,
        canton=canton,
        payload={"name": clean_name, **payload},
    )


def extract_parser54_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 54."""
    events: list[Event] = []
    leftover = text

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_SHARE_TRANSFER_RESTRICTION_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "fr.text.share_transfer_restriction_removed.v4",
                {
                    "kind": "share_transfer_restriction",
                    "action": "removed",
                    "shares_count": _count(match.group("count")),
                    "nominal": match.group("nominal"),
                    "legal_basis": "art. 685a al. 3 CO",
                },
            )
        )

    match = _DE_ART_934_SHAB_CANTONAL_DELETION_BLOCKED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.art_934_deletion_blocked.v3",
                {
                    "kind": "deletion_blocked",
                    "legal_basis": "Art. 934 OR / Art. 152 Abs. 1 HRegV",
                    "procedure_completed": True,
                    "issues": match.group("issues").strip(),
                    "affected_parties_responded": False,
                    "tax_authority": "cantonal",
                    "tax_authority_consent_missing": True,
                },
            )
        )

    match = _FR_PERSON_NAME_CHANGED_NOW.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "fr.persons.civil_name.v3", match.group("name"),
                {
                    "action": "name_changed",
                    "previous": match.group("old_name").strip(),
                },
            )
        )

    match = _DE_NON_REGISTERABLE_REMARK_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", "de.text.non_registerable_remark_removed.v1",
                {
                    "kind": "registry_remark",
                    "action": "removed",
                    "reason": "not_part_of_registration_text",
                    "removed_fact": match.group("removed").strip(),
                },
            )
        )

    match = _FR_LEGAL_BEARER_AND_PARTICIPATION_CONVERSION.search(leftover)
    if match:
        consume(match)
        share_total = match.group("share_total")
        share_paid = match.group("share_paid")
        participation_total = match.group("participation_total")
        participation_paid = match.group("participation_paid")
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.legal_bearer_combined_conversion.v1",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _fr_date(match.group("date")),
                    "statutes_adapted": False,
                    "instruments": [
                        {
                            "instrument": "shares",
                            "from_kind": "actions au porteur",
                            "to_kind": "actions nominatives",
                            "capital_total": share_total,
                            "paid": share_paid,
                            "paid_in_full": share_paid == share_total,
                            "share_classes": [
                                {
                                    "count": _count(match.group("share_count1")),
                                    "nominal": match.group("share_nominal1"),
                                    "rights": match.group("share_rights"),
                                },
                                {
                                    "count": _count(match.group("share_count2")),
                                    "nominal": match.group("share_nominal2"),
                                },
                            ],
                        },
                        {
                            "instrument": "participation_certificates",
                            "from_kind": "bons de participation au porteur",
                            "to_kind": "bons de participation nominatifs",
                            "capital_total": participation_total,
                            "paid": participation_paid,
                            "paid_in_full": participation_paid == participation_total,
                            "count": _count(match.group("participation_count")),
                            "nominal": match.group("participation_nominal"),
                        },
                    ],
                },
            )
        )

    match = _FR_SHARE_CAPITAL_STRUCTURE.search(leftover)
    if match:
        consume(match)
        paid = match.group("paid")
        total = match.group("total")
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.share_capital_structure.v1",
                {
                    "kind": "share_structure",
                    "currency": "CHF",
                    "capital_total": total,
                    "paid": paid,
                    "paid_in_full": paid == total,
                    "shares_count": _count(match.group("count")),
                    "nominal": match.group("nominal"),
                    "share_kind": "actions nominatives",
                },
            )
        )

    match = _DE_SPIN_OFF_ACQUISITION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.spin_off_acquisition.v2",
                {
                    "kind": "spin_off_acquisition",
                    "date": _iso_date(match.group("date")),
                    "source": match.group("source").strip(),
                    "source_place": match.group("source_place").strip(),
                    "source_uid": match.group("source_uid"),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "membership_continuity": True,
                    "capital_increase": False,
                    "share_allocation": False,
                },
            )
        )

    match = _DE_LEGAL_BEARER_CONVERSION_ADAPTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.legal_bearer_conversion_adapted.v3",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _iso_date(match.group("conversion_date")),
                    "adaptation_date": _iso_date(match.group("adaptation_date")),
                    "from_kind": "Inhaberaktien",
                    "to_kind": "Namenaktien",
                    "statutes_adapted": True,
                },
            )
        )

    match = _FR_ASSET_TRANSFER_WITH_NAMED_AGREEMENT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "fr.text.asset_transfer.v3",
                {
                    "date": _iso_date(match.group("date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "net_assets": match.group("net"),
                    "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration": match.group("consideration").strip().rstrip("."),
                },
            )
        )

    match = _DE_FUSION_WITH_POST_UID_PLACE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_merged", "de.text.fusion.v2",
                {
                    "kind": "absorption",
                    "absorbed_name": match.group("absorbed_name").strip(),
                    "absorbed_uid": match.group("absorbed_uid"),
                    "absorbed_place": match.group("absorbed_place").strip(),
                    "agreement_date": _iso_date(match.group("agreement_date")),
                    "balance_date": _iso_date(match.group("balance_date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "capital_increase": False,
                    "share_allocation": False,
                },
            )
        )

    match = _FR_SOLE_PROPRIETOR_DELETED_CONTINUED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_deleted", "fr.text.sole_proprietor_deleted_continued.v1",
                {
                    "reason": "continued_under_other_legal_form",
                    "scope": "sole_proprietor",
                    "business_continues": True,
                },
            )
        )

    stripped = leftover.strip(" .;")
    date_match = _IT_STANDALONE_STATUTES_DATE.fullmatch(stripped)
    if language == "it" and date_match:
        leftover = ""
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "it.text.statutes_additional_date.v1",
                {
                    "kind": "additional_statutes_date",
                    "date": _iso_date(date_match.group("date")),
                },
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
