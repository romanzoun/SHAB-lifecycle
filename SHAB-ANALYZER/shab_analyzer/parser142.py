from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_COUNCIL_MEMBER_APPOINTED_PRESIDENT = re.compile(
    r"^(?P<name>[^,.;]+),\s*membre du conseil,\s*a été nommé président\.?$",
    re.I | re.UNICODE,
)
_FR_COURT_DISSOLUTION_BANKRUPTCY_LIQUIDATION = re.compile(
    r"^Par décision du\s+(?P<date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"(?P<authority>.+?)\s+a prononcé la dissolution de la société,\s*et "
    r"ordonné sa liquidation selon les dispositions applicables à la faillite\.?$",
    re.I | re.UNICODE,
)
_FR_ROLE_NAME_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que l['’]"
    r"(?P<role>associé-gérant président|administateur)\s+se nomme\s+"
    r"(?P<name>[^()]+?)\s*\(et non\s+(?P<previous>[^,)]+),?\s*comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_NAME_CORRECTED_PUBLICATION = re.compile(
    r"^L['’]inscription no\.?\s*(?P<entry>[\d']+)\s*"
    r"\(publication FOSC du\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"page\s+(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le "
    r"directeur porte le nom de\s+(?P<name>[^()]+?)\s*"
    r"\(et non\s+(?P<previous>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_IT_STATUTES_DATE_CORRECTED_SHORT = re.compile(
    r"^Data statuti corretta:\s*(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_EXTENDED_PREVIOUS_PROVISIONAL = re.compile(
    r"^Mit Entscheid des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde die definitive "
    r"Nachlassstundung um\s+(?P<duration>\d+|ein(?:e|en)?|zwei|drei|vier|fünf|sechs)\s+"
    r"Monate,\s*d\.h\.\s*bis zum\s+(?P<until>\d{2}\.\d{2}\.\d{4})\s+verlängert\.\s*"
    r"\[bisher:\s*Mit Entscheid des\s+(?P<previous_authority>.+?)\s+vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde eine provisorische "
    r"Nachlassstundung für die Dauer von\s+"
    r"(?P<previous_duration>\d+|ein(?:e|en)?|zwei|drei|vier|fünf|sechs)\s+Monaten,\s*"
    r"d\.h\.\s*bis zum\s+(?P<previous_until>\d{2}\.\d{2}\.\d{4})\s+gewährt\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_ASSOCIATE_ORIGIN_PLACE = re.compile(
    r"^Nouvelle associée:\s*(?P<name>[^,.;]+),\s*du\s+(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_PARTIAL_TRANSFER_NEW_ASSOCIATE = re.compile(
    r"^Jusqu['’]ici titulaire de\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*l['’]associé-gérant\s+(?P<seller>[^,.;]+),\s*"
    r"maintenant domicilié à\s+(?P<seller_place>[^,.;]+),\s*détient\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\s+"
    r"par suite de cession de\s+(?P<transferred>[\d']+)\s+parts à\s+"
    r"(?P<buyer>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<buyer_place>[^,.;]+),\s*nouvelle associée pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_RENAMED_AND_MOVED_SAME_UID = re.compile(
    r"^Organe de révision inscrit modifié:\s*(?P<previous_name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+se nomme désormais\s+"
    r"(?P<name>.+?)\s*\((?P<new_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"désormais domicilié à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_COMMON_OWNER_SHARE_AND_SOCIAL_CAPITAL = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di\s+(?P<absorbed_name>.+?),\s*"
    r"in\s+(?P<absorbed_place>[^()]+?)\s*"
    r"\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"secondo il contratto di fusione del\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+e bilancio al\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta attivi per CHF\s+"
    r"(?P<assets>[\d'.]+)\s+e passivi verso terzi per CHF\s+"
    r"(?P<liabilities>[\d'.]+)\.\s*La totalità del capitale azionario e del "
    r"capitale sociale delle due società è detenuta dalla stessa persona,\s*"
    r"la fusione avviene dunque senza aumento di capitale e senza attribuzione "
    r"di azioni\.?$",
    re.I | re.UNICODE,
)
_DE_SUMMARY_BANKRUPTCY_ORDERED_AFTER_ADVANCE = re.compile(
    r"^Nachdem nachträglich ein Kostenvorschuss geleistet wurde,\s*hat\s+"
    r"(?P<authority>.+?)\s+mit Entscheid vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+das summarische Verfahren "
    r"angeordnet\.?$",
    re.I | re.UNICODE,
)
_IT_ASSOCIATION_ART155_DELETION_BLOCKED_TYPO = re.compile(
    r"^L['’]Associzione deve essere cancellata a seguito della procedura di cui "
    r"all['’]art\.\s*155\s+ORC\.\s*La cancellazione non può tuttavia essere "
    r"effettuata mancando il consenso delle autorità fiscali federali e cantonali\.?$",
    re.I | re.UNICODE,
)
_FR_HOLDER_NAME_CORRECTED_NOTICE = re.compile(
    r"^Rectificatif:\s*l['’]inscription no\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que la titulaire "
    r"se nomme\s+(?P<name>.+?)\s+et non\s+(?P<previous>.+?),\s*comme publié\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_RESTRICTION_THEIR_SHARES = re.compile(
    r"^Les\s+(?P<count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*formant l['’]entier du capital-actions,\s*"
    r"sont désormais restreintes quant à leur transmissibilité selon statuts\.?$",
    re.I | re.UNICODE,
)
_FR_DOMICILE_CORRECTED_NOTICE_PARENTHETICAL = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^()]+?)\s+est à\s+(?P<place>[^()]+?)\s*"
    r"\(et non à\s+(?P<previous_place>[^)]+?)\s+comme publié\)\.?$",
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
_DE_NUMBERS = {
    "ein": 1,
    "eine": 1,
    "einen": 1,
    "zwei": 2,
    "drei": 3,
    "vier": 4,
    "fünf": 5,
    "sechs": 6,
}


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _french_date(raw: str) -> str:
    day, month, year = raw.lower().replace("1er", "1", 1).split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _duration(raw: str) -> int:
    normalized = raw.lower()
    return int(normalized) if normalized.isdigit() else _DE_NUMBERS[normalized]


def _replace_final_name_part(name: str, previous: str) -> str:
    prefix, separator, _ = name.strip().rpartition(" ")
    return f"{prefix}{separator}{previous.strip()}" if separator else previous.strip()


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


def extract_parser142_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 142."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_COUNCIL_MEMBER_APPOINTED_PRESIDENT.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.council_member_appointed_president.v1",
            match.group("name"), role="membre du conseil et président",
            extra={"action": "appointed_president", "previous_role": "membre du conseil"},
        ))

    match = _FR_COURT_DISSOLUTION_BANKRUPTCY_LIQUIDATION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.court_dissolution_bankruptcy_liquidation.v1",
            {
                "kind": "dissolution", "date": _french_date(match.group("date")),
                "authority": match.group("authority").strip(),
                "liquidation_mode": "bankruptcy",
            },
        ))

    match = _FR_ROLE_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        published_role = match.group("role").lower()
        role = "administrateur" if published_role == "administateur" else published_role
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.role_name_corrected_notice.v1",
            match.group("name"), role=role,
            extra={
                "action": "name_corrected", "previous_name": match.group("previous").strip(),
                "entry": match.group("entry"), "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"), "published_role": published_role,
            },
        ))

    match = _FR_DIRECTOR_NAME_CORRECTED_PUBLICATION.search(leftover)
    if match:
        consume(match)
        name = match.group("name").strip()
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.director_name_corrected_publication.v1",
            name, role="directeur",
            extra={
                "action": "name_corrected",
                "previous_name": _replace_final_name_part(name, match.group("previous")),
                "entry": match.group("entry"),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _IT_STATUTES_DATE_CORRECTED_SHORT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "it.text.statutes_date_corrected_short.v2",
            {"kind": "statutes_date", "action": "corrected", "date": _iso_date(match.group("date"))},
        ))

    match = _DE_DEFINITIVE_MORATORIUM_EXTENDED_PREVIOUS_PROVISIONAL.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.definitive_moratorium_extended_previous_provisional.v1",
            {
                "kind": "composition_moratorium_extended", "moratorium_type": "definitive",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "duration_months": _duration(match.group("duration")),
                "until": _iso_date(match.group("until")),
                "previous_moratorium_type": "provisional",
                "previous_authority": match.group("previous_authority").strip(),
                "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                "previous_duration_months": _duration(match.group("previous_duration")),
                "previous_until": _iso_date(match.group("previous_until")),
            },
        ))

    match = _FR_NEW_ASSOCIATE_ORIGIN_PLACE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.new_associate_origin_place.v1",
            match.group("name"), place=match.group("place"), role="associée",
            extra={"action": "appointed", "new_associate": True, "heimat": match.group("origin").strip()},
        ))

    match = _FR_MANAGER_PARTIAL_TRANSFER_NEW_ASSOCIATE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_partial_transfer_new_associate.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, place=match.group("seller_place"),
                role="associé-gérant",
                extra={
                    "action": "domicile_changed_and_shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred, "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("remaining_nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("buyer_place"), role="associée",
                extra={
                    "action": "shares_received", "counterparty": seller, "new_associate": True,
                    "heimat": match.group("origin").strip(), "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _FR_AUDITOR_RENAMED_AND_MOVED_SAME_UID.search(leftover)
    if match and match.group("uid") == match.group("new_uid"):
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.auditor_renamed_and_moved_same_uid.v1",
            match.group("name"), place=match.group("place"), uid=match.group("uid"),
            role="organe de révision",
            extra={
                "action": "name_and_domicile_changed",
                "previous_name": match.group("previous_name").strip(),
                "previous_uid": match.group("uid"),
            },
        ))

    match = _IT_MERGER_COMMON_OWNER_SHARE_AND_SOCIAL_CAPITAL.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "it.text.merger_common_owner_share_and_social_capital.v1",
            {
                "kind": "absorption", "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "currency": "CHF", "common_owner": True,
                "capital_increase": False, "share_allocation": False,
            },
        ))

    match = _DE_SUMMARY_BANKRUPTCY_ORDERED_AFTER_ADVANCE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.summary_bankruptcy_ordered_after_advance.v1",
            {
                "kind": "bankruptcy_proceedings", "action": "summary_procedure_ordered",
                "procedure": "summary", "advance_paid_late": True,
                "authority": match.group("authority").strip(),
                "decision_date": _iso_date(match.group("decision_date")),
            },
        ))

    match = _IT_ASSOCIATION_ART155_DELETION_BLOCKED_TYPO.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.association_art155_deletion_blocked_typo.v1",
            {
                "kind": "deletion_blocked", "entity": "association",
                "legal_basis": "art. 155 ORC", "deletion_blocked": True,
                "deletion_blocked_reason": "tax_authority_consent_missing",
                "missing_consents": ["federal_tax_authority", "cantonal_tax_authority"],
            },
        ))

    match = _FR_HOLDER_NAME_CORRECTED_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.holder_name_corrected_notice.v1",
            match.group("name"), role="titulaire",
            extra={
                "action": "name_corrected", "previous_name": match.group("previous").strip(),
                "entry": match.group("entry"), "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_SHARE_TRANSFER_RESTRICTION_THEIR_SHARES.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.share_transfer_restriction_their_shares.v1",
            {
                "kind": "share_transfer_restricted", "action": "added", "basis": "statutes",
                "shares_count": _count(match.group("count")), "share_kind": "actions nominatives",
                "nominal": match.group("nominal"), "currency": "CHF", "entire_share_capital": True,
            },
        ))

    match = _FR_DOMICILE_CORRECTED_NOTICE_PARENTHETICAL.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.domicile_corrected_notice_parenthetical.v1",
            match.group("name"), place=match.group("place"),
            extra={
                "action": "domicile_corrected", "previous_place": match.group("previous_place").strip(),
                "entry": match.group("entry"), "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
