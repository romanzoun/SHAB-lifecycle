from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_CONTRIBUTION_IN_KIND_CLAUSE_REPEALED_ART_634 = re.compile(
    r"^La clause statutaire relative à l['’]apport en nature effectuée à la "
    r"constitution est abrogée conformément à l['’]art\.\s*634\s+al\.\s*4\s+CO\.?$",
    re.I | re.UNICODE,
)
_DE_CONDITIONAL_CAPITAL_CLAUSE_REPEALED_EXPIRED_RIGHTS = re.compile(
    r"^Aufhebung der Statutenbestimmung über die mit Gewährungsbeschluss vom\s+"
    r"(?P<introduced_date>\d{2}\.\d{2}\.\d{4})\s+eingeführte bedingte "
    r"Kapitalerhöhung infolge Erlöschens der Wandelrechte\.?$",
    re.I | re.UNICODE,
)
_FR_CORRECTION_REFERENCE_PREFIX = re.compile(
    r"^Rectificatif:\s*L['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_PARTIAL_TRANSFER_TO_MANAGER = re.compile(
    r"^(?P<seller>[^,.;]+),\s*associé,\s*cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à l['’]associé-gérant\s+(?P<buyer>[^,.;]+),\s*"
    r"lequel est désormais titulaire de\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*(?P=seller)\s+reste titulaire de\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_IT_LIQUIDATION_ENDED_EARLY_DELETION_BLOCKED = re.compile(
    r"^La liquidazione è terminata\.\s*Ma la cancellazione anticipata con "
    r"conferma di un perito revisore abilitato dell['’]"
    r"(?P<confirmation_date>\d{2}\.\d{2}\.\d{4})\s+non può ancora essere "
    r"effettuata mancando il consenso dell['’]autorità fiscale federale\.?$",
    re.I | re.UNICODE,
)
_FR_AUTHORIZED_CAPITAL_INTRODUCED_AMENDED_DECISION = re.compile(
    r"^Par décision du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+modifiée le\s+"
    r"(?P<amended_date>\d{2}\.\d{2}\.\d{4}),\s*l['’]assemblée générale a "
    r"introduit une clause statutaire relative à une augmentation autorisée du "
    r"capital-actions\.\s*Pour les détails,\s*voir les statuts\.\s*Statuts modifiés "
    r"les\s+(?P<statutes_date1>\d{2}\.\d{2}\.\d{4})\s+et\s+"
    r"(?P<statutes_date2>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_SUPPLEMENT_TRANSACTION_TEXT_HEADER = re.compile(
    r"^Nachtrag zu SHAB Nr\.\s*(?P<notice>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten TR-Nr\.\s*"
    r"(?P<entry>[\d']+)\s+vom\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"folgender TR-Text\.?$",
    re.I | re.UNICODE,
)
_FR_CONDITIONAL_PARTICIPATION_CLAUSE_INTRODUCED = re.compile(
    r"^L['’]assemblée générale a introduit une clause statutaire relative à une "
    r"augmentation conditionnelle du capital-participation par décision du\s+"
    r"(?P<decision_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.\s*"
    r"Pour les détails,\s*voir les statuts\.?$",
    re.I | re.UNICODE,
)
_DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_HISTORY = re.compile(
    r"^Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+die Statutenbestimmung über die "
    r"bedingte Kapitalerhöhung vom\s+(?P<clause_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"geändert\.\s*\[bisher:\s*Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+die Statutenbestimmung "
    r"über die bedingte Kapitalerhöhung vom\s+"
    r"(?P<previous_clause_date>\d{2}\.\d{2}\.\d{4})\s+geändert\.\]\.?$",
    re.I | re.UNICODE,
)
_IT_BRANCH_DELETION_BLOCKED_ART_155 = re.compile(
    r"^,?\s*Sede principale a:\s*(?:Sede principale:\s*)?"
    r"(?P<head_office>[^.]+)\.\s*Nuove disposizioni per la succursale:\s*"
    r"La succursale deve essere cancellata a seguito della procedura di cui "
    r"all['’]art\.\s*155\s+ORC\.\s*La cancellazione non può tuttavia essere "
    r"effettuata mancando il consenso delle autorità fiscali federali e cantonali\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBER_DOMICILE_AND_SIGNING_CHANGED = re.compile(
    r"^(?P<name>[^,.;]+),\s*maintenant domicilié à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{1,3}),\s*membre du conseil d['’]administration,\s*"
    r"signe désormais collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_SINGLE_SHARE_TRANSFER_ASSOCIATE_REMOVED = re.compile(
    r"^La part de CHF\s+(?P<nominal>[\d'.]+)\s+d['’](?P<seller>[^,.;]+),\s*"
    r"qui\s*n['’]est plus associé,\s*est cédée à l['’]associé-gérant\s+"
    r"(?P<buyer>[^,.;]+),\s*désormais titulalire de\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_IT_COMPANY_BANKRUPTCY_EFFECT_SUSPENDED_DEL = re.compile(
    r"^(?P<name_fragment>.+?\bsagl)\.\s*Con decreto del\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+(?P<authority>.+?)\s+"
    r"ha accordato effetto sospensivo al reclamo inoltrato contro la decisione di "
    r"apertura del fallimento del\s+(?P<court>.+?)\s+del\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.\s*L['’]iscrizione nel registro "
    r"di commercio relativa allo scioglimento della società a seguito di fallimento "
    r"viene pertanto cancellata\.\s*\[radiati:\s*La società è sciolta in seguito a "
    r"fallimento pronunciato con decreto del\s+(?P<previous_court>.+?)\s+del\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+a far tempo dal\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4})\s+alle ore\s+"
    r"(?P<effective_time>\d{2}:\d{2})\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_HOLDER_ORIGIN_AND_SHARE_TRANSFER = re.compile(
    r"^détenues par\s+(?P<seller>[^,.;]+),\s*désormais d['’]"
    r"(?P<origin>[^,.;]+)\.\s*(?P=seller)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à la gérante\s+(?P<buyer>[^,.;]+),\s*"
    r"nouvelle associée,\s*avec\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+);\s*(?P=seller)\s+reste titulaire de\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGERS_APPOINTED_LIQUIDATORS = re.compile(
    r"^Liquidateurs:\s*les associés gérants\s+(?P<name1>[^,.;]+?)\s+et\s+"
    r"(?P<name2>[^,.;]+?),\s*lesquels continuent à signer individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_FEDERAL_APPEAL_REJECTED_BANKRUPTCY_EFFECTIVE = re.compile(
    r"^Par arrêt du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>la IIe Cour de droit civil du Tribunal fédéral)\s+a rejeté "
    r"le recours\.\s*La faillite prend effet le\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4})\s+à\s+"
    r"(?P<effective_time>\d{1,2}h\d{2})\.?$",
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


def extract_parser107_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 107."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_CONTRIBUTION_IN_KIND_CLAUSE_REPEALED_ART_634.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.contribution_in_kind_clause_repealed_art_634.v1",
            {
                "kind": "contribution_in_kind", "action": "removed",
                "at_incorporation": True, "legal_basis": "Art. 634 al. 4 CO",
            },
        ))

    match = _DE_CONDITIONAL_CAPITAL_CLAUSE_REPEALED_EXPIRED_RIGHTS.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.conditional_capital_clause_repealed_expired_rights.v1",
            {
                "kind": "conditional_capital_clause", "action": "removed",
                "introduced_date": _iso_date(match.group("introduced_date")),
                "reason": "conversion_rights_expired",
            },
        ))

    match = _FR_CORRECTION_REFERENCE_PREFIX.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.correction_reference_prefix.v1",
            {
                "kind": "person_entry", "action": "corrected",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_ASSOCIATE_PARTIAL_TRANSFER_TO_MANAGER.search(leftover)
    if match and len({
        match.group("nominal"), match.group("buyer_nominal"),
        match.group("seller_nominal"),
    }) == 1:
        consume(match)
        rule_id = "fr.persons.associate_partial_transfer_to_manager.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé",
                extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, role="associé-gérant",
                extra={
                    "action": "shares_received", "counterparty": seller,
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _IT_LIQUIDATION_ENDED_EARLY_DELETION_BLOCKED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.liquidation_ended_early_deletion_blocked.v1",
            {
                "kind": "liquidation_ended", "deletion_blocked": True,
                "requested_early_deletion": True,
                "audit_expert_confirmation_date": _iso_date(match.group("confirmation_date")),
                "deletion_blocked_reason": "federal_tax_authority_consent_missing",
            },
        ))

    match = _FR_AUTHORIZED_CAPITAL_INTRODUCED_AMENDED_DECISION.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.authorized_capital_introduced_amended_decision.v1"
        decision_date = _iso_date(match.group("decision_date"))
        amended_date = _iso_date(match.group("amended_date"))
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "kind": "authorized_capital_clause", "action": "introduced",
                    "decision_date": decision_date, "amended_date": amended_date,
                    "details_in_statutes": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id,
                {
                    "action": "changed",
                    "dates": [
                        _iso_date(match.group("statutes_date1")),
                        _iso_date(match.group("statutes_date2")),
                    ],
                },
            ),
        ])

    match = _DE_SUPPLEMENT_TRANSACTION_TEXT_HEADER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.supplement_transaction_text_header.v1",
            {
                "kind": "transaction_text", "action": "supplemented",
                "notice": match.group("notice"),
                "notice_date": _iso_date(match.group("notice_date")),
                "entry": match.group("entry").replace("'", ""),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _FR_CONDITIONAL_PARTICIPATION_CLAUSE_INTRODUCED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.conditional_participation_clause_introduced.v1",
            {
                "kind": "conditional_participation_capital_clause",
                "action": "introduced",
                "decision_date": _french_date(match.group("decision_date")),
                "details_in_statutes": True,
            },
        ))

    match = _DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_HISTORY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.conditional_capital_clause_changed_history.v1",
            {
                "kind": "conditional_capital_clause", "action": "changed",
                "decision_date": _iso_date(match.group("decision_date")),
                "clause_date": _iso_date(match.group("clause_date")),
                "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                "previous_clause_date": _iso_date(match.group("previous_clause_date")),
            },
        ))

    match = _IT_BRANCH_DELETION_BLOCKED_ART_155.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "it.text.branch_deletion_blocked_art_155.v1",
            {
                "action": "deletion_pending", "head_office": match.group("head_office").strip(),
                "legal_basis": "Art. 155 ORC", "deletion_blocked": True,
                "deletion_blocked_reason": "tax_authority_consent_missing",
                "authorities": ["federal_tax_authority", "cantonal_tax_authority"],
            },
        ))

    match = _FR_BOARD_MEMBER_DOMICILE_AND_SIGNING_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.board_member_domicile_and_signing_changed.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil d'administration",
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "domicile_and_signing_changed",
                "country": match.group("country"), "domicile_changed": True,
            },
        ))

    match = _FR_SINGLE_SHARE_TRANSFER_ASSOCIATE_REMOVED.search(leftover)
    if match and match.group("nominal") == match.group("buyer_nominal"):
        consume(match)
        rule_id = "fr.persons.single_share_transfer_associate_removed.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, seller, role="associé",
                extra={
                    "action": "shares_transferred_and_removed", "counterparty": buyer,
                    "shares_transferred": 1, "shares_count": 0,
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, role="associé-gérant",
                extra={
                    "action": "shares_received", "counterparty": seller,
                    "shares_received": 1, "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _IT_COMPANY_BANKRUPTCY_EFFECT_SUSPENDED_DEL.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.company_bankruptcy_effect_suspended_del.v1",
            {
                "kind": "bankruptcy_effect_suspended", "scope": "company",
                "action": "suspended_on_appeal",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "bankruptcy_court": match.group("court").strip(),
                "bankruptcy_decision_date": _iso_date(match.group("bankruptcy_date")),
                "bankruptcy_effective_date": _iso_date(match.group("effective_date")),
                "bankruptcy_effective_time": match.group("effective_time"),
                "dissolution_entry_removed": True,
                "legacy_name_fragment": match.group("name_fragment").strip(),
            },
        ))

    match = _FR_HOLDER_ORIGIN_AND_SHARE_TRANSFER.search(leftover)
    if match and len({
        match.group("nominal"), match.group("buyer_nominal"),
        match.group("seller_nominal"),
    }) == 1:
        consume(match)
        rule_id = "fr.persons.holder_origin_and_share_transfer.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé",
                extra={
                    "action": "origin_changed_and_shares_transferred",
                    "heimat": match.group("origin").strip(), "origin_changed": True,
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, role="associée-gérante",
                extra={
                    "action": "appointed_and_shares_received", "new_associate": True,
                    "counterparty": seller,
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _FR_ASSOCIATE_MANAGERS_APPOINTED_LIQUIDATORS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.associate_managers_appointed_liquidators.v1"
        for name_group in ("name1", "name2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(name_group),
                role="associé-gérant et liquidateur", signing="Einzelunterschrift",
                extra={"action": "appointed_liquidator", "signing_continues": True},
            ))

    match = _FR_FEDERAL_APPEAL_REJECTED_BANKRUPTCY_EFFECTIVE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.federal_appeal_rejected_bankruptcy_effective.v1",
            {
                "kind": "bankruptcy", "action": "appeal_rejected",
                "authority": match.group("authority"),
                "decision_date": _iso_date(match.group("decision_date")),
                "effective_date": _iso_date(match.group("effective_date")),
                "effective_time": match.group("effective_time").replace("h", ":"),
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
