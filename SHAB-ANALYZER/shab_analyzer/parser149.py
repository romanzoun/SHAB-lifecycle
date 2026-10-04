from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_DE_SOLE_PROPRIETOR_ASSET_TRANSFER_BY_CONTRACT = re.compile(
    r"^Vermögensübertragung:\s*Der Geschäftsinhaber überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>.+?)\.?$",
    re.I | re.UNICODE,
)
_DE_HEAD_OFFICE_PROVISIONAL_MORATORIUM = re.compile(
    r"^Bemerkungen zum Hauptsitz neu:\s*Mit Entscheid vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+(?P<authority>.+?)\s+"
    r"eine provisorische Nachlassstundung von\s+"
    r"(?P<duration>\d+|ein(?:e|en)?|zwei|drei|vier|fünf|sechs)\s+Monaten?\s+"
    r"bis\s+(?P<until>\d{2}\.\d{2}\.\d{4})\s+gewährt\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDATION_PERSON_REPLACED = re.compile(
    r"^Gelöschte Person:\s*(?P<removed>[^,.;]+),\s*"
    r"(?P<removed_roles>.+?),\s*"
    r"(?P<removed_sign>Kollektivunterschrift zu zweien|Einzelunterschrift)\.\s*"
    r"Neu eingetragene Person:\s*(?P<added>[^,.;]+),\s*von\s+"
    r"(?P<origin>[^,.;]+),\s*in\s+(?P<place>[^,.;]+),\s*"
    r"(?P<added_roles>.+?),\s*"
    r"(?P<added_sign>Kollektivunterschrift zu zweien(?:\s+mit\s+.+)?|"
    r"Einzelunterschrift)\.?$",
    re.I | re.UNICODE,
)
_DE_ARBITRATION_CLAUSE_ARTICLE = re.compile(
    r"^Schiedsklausel gemäss näherer Umschreibung in(?:\s+Art\.\s*"
    r"(?P<article>[\w.]+)\s+der)?\s+Statuten\.?$",
    re.I | re.UNICODE,
)
_FR_CORPORATE_NEW_ASSOCIATE_SHARE_TRANSFER = re.compile(
    r"^(?P<seller>[^,.;]+)\s+a cédé\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>.+?)\s*"
    r"\((?P<registry_id>[^()]+)\),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{2,3}),\s*nouvelle associée pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"Par conséquent,\s*(?P=seller)\s+est maintenant associé pour\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_COMMITTEE_ROLE_CORRECTION = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<names>.+?)\s+sont membres du comité de direction\s*"
    r"\(et non membres du comité exécutif,\s*comme publié\)\.?$",
    re.I | re.UNICODE,
)
_DE_PREVIOUS_DOMICILE_OMITTED = re.compile(
    r"^In dem im SHAB Nr\.\s*(?P<notice_number>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten TR-Eintrag Nr\.\s*"
    r"(?P<entry>[\d']+)\s+vom\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"wurde der bisherige Wohnsitz von\s+(?P<name>.+?)\s+"
    r"\[bisher:\s*in\s+(?P<previous_place>[^\]]+)\]\s+nicht publiziert\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_REPLACED_WITH_TWO_WITHOUT_SIGNATURE = re.compile(
    r"^(?P<removed>.+?)\s+ne sont plus membres du conseil\.\s*"
    r"(?P<name1>[^,.;]+),\s*(?:de\s+|d['’])(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,.;]+),\s*(?P<country1>[A-Z]{2,3}),\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*(?:de\s+|d['’])(?P<origin2>[^,.;]+),\s*"
    r"à\s+(?P<place2>[^,.;]+),\s*(?P<country2>[A-Z]{2,3}),\s*"
    r"sont membres du conseil sans signature\.?$",
    re.I | re.UNICODE,
)
_IT_OWNER_BANKRUPTCY_SUSPENSIVE_EFFECT_RADIATI = re.compile(
    r"^Con decisione del\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"(?P<authority>.+?)\s+ha accordato effetto sospensivo al reclamo inoltrato "
    r"contro la decisione di fallimento aperto nei confronti del titolare il\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.\s*\[radiati:\s*"
    r"Il titolare è stato dichiarato in fallimento con decreto della\s+"
    r"(?P<court>.+?)\s+del\s+(?P<previous_bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"a far tempo dal\s+(?P<effective_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"alle ore\s+(?P<effective_time>\d{1,2}:\d{2})\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_ASSOCIATE_SHARE_TRANSFER = re.compile(
    r"^(?P<seller>[^,.;]+)\s+a cédé\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:de\s+|d['’])(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{2,3}),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"par conséquent\s+(?P=seller)\s+est maintenant associé pour\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_SOLE_PROPRIETOR_DELETED_AFTER_CLOSURE = re.compile(
    r"^Das Einzelunternehmen wird infolge Geschäftsaufgabe gelöscht\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_ADMINISTRATOR_NO_COLON = re.compile(
    r"^Nouvel administrateur\s+(?P<name>[^,.;]+),\s*"
    r"(?:de\s+|d['’])(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_REGISTERED_SHARES_TRANSFORMED = re.compile(
    r"^Les\s+(?P<from_count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<from_nominal>[\d'.]+),\s*formant l['’]entier du capital-actions,\s*"
    r"sont transformées en\s+(?P<to_count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<to_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_PURPOSE_MENTION_REMOVED = re.compile(
    r"^La mention relative au but de la succursale est radiée,\s*"
    r"celle-ci n['’]étant pas obligatoire\s*\((?P<legal_basis>"
    r"art\.\s*110 al\.\s*1 let\.\s*d ORC)\)\.?$",
    re.I | re.UNICODE,
)
_FR_DOMICILE_CORRECTION_WITH_NOTICE = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<name>.+?)\s+est domicilié(?:e)? à\s+(?P<place>[^()]+?)\s*"
    r"\(et non pas à\s+(?P<previous_place>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_VOTING_PREFERRED_SPLIT_WITH_CAPITAL = re.compile(
    r"^Division de\s+(?P<from_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<from_nominal>[\d'.]+)\s+en\s+(?P<preferred_count>[\d']+)\s+actions "
    r"de CHF\s+(?P<preferred_nominal>[\d'.]+)\s+privilégiées quant au droit de "
    r"vote\.\s*Capital-actions:\s*CHF\s+(?P<total>[\d'.]+),\s*entièrement "
    r"libéré,\s*divisé en\s+(?P<ordinary_count>[\d']+)\s+actions ordinaires de "
    r"CHF\s+(?P<ordinary_nominal>[\d'.]+)\s+et en\s+"
    r"(?P<capital_preferred_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<capital_preferred_nominal>[\d'.]+),\s*privilégiées quant au droit de "
    r"vote,\s*toutes nominatives\.?$",
    re.I | re.UNICODE,
)


_NUMBER_WORDS = {
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


def _count(raw: str) -> int:
    return int(raw.replace("'", "").replace(".", ""))


def _amount(raw: str) -> Decimal:
    return Decimal(raw.replace("'", ""))


def _signing(raw: str) -> str:
    return (
        "Einzelunterschrift"
        if "einzel" in raw.casefold()
        else "Kollektivunterschrift zu zweien"
    )


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


def _split_names(raw: str) -> list[str]:
    return [name.strip() for name in re.split(r",\s*|\s+et\s+", raw) if name.strip()]


def extract_parser149_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 149."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_SOLE_PROPRIETOR_ASSET_TRANSFER_BY_CONTRACT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.sole_proprietor_asset_transfer_contract.v1",
            {
                "source_kind": "sole_proprietor",
                "agreement_date": _iso_date(match.group("date")),
                "currency": "CHF", "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration").strip(),
            },
        ))

    match = _DE_HEAD_OFFICE_PROVISIONAL_MORATORIUM.search(leftover)
    if match:
        consume(match)
        raw_duration = match.group("duration").casefold()
        duration_months = int(raw_duration) if raw_duration.isdigit() else _NUMBER_WORDS[raw_duration]
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.head_office_provisional_moratorium.v1",
            {
                "kind": "composition_moratorium_granted",
                "scope": "head_office", "moratorium_type": "provisional",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "duration_months": duration_months,
                "until": _iso_date(match.group("until")),
            },
        ))

    match = _DE_FOUNDATION_PERSON_REPLACED.search(leftover)
    if match:
        consume(match)
        rule_id = "de.persons.foundation_member_replaced.v1"
        removed_sign = match.group("removed_sign").strip()
        added_sign = match.group("added_sign").strip()
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group("removed"),
                role=match.group("removed_roles").strip(), signing=_signing(removed_sign),
                extra={"action": "removed", "signing_text": removed_sign},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("added"),
                place=match.group("place"), role=match.group("added_roles").strip(),
                signing=_signing(added_sign),
                extra={
                    "action": "appointed", "heimat": match.group("origin").strip(),
                    "signing_text": added_sign,
                    "signing_restriction": (
                        added_sign.split(" mit ", 1)[1] if " mit " in added_sign else None
                    ),
                },
            ),
        ])

    match = _DE_ARBITRATION_CLAUSE_ARTICLE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.arbitration_clause.v1",
            {
                "kind": "arbitration_clause", "present": True,
                "details_in_statutes": True, "article": match.group("article"),
            },
        ))

    match = _FR_CORPORATE_NEW_ASSOCIATE_SHARE_TRANSFER.search(leftover)
    if match and (
        match.group("nominal") == match.group("buyer_nominal")
        == match.group("remaining_nominal")
        and _count(match.group("transferred")) == _count(match.group("buyer_count"))
    ):
        consume(match)
        rule_id = "fr.persons.corporate_new_associate_share_transfer.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        remaining = _count(match.group("remaining"))
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé",
                extra={
                    **common, "action": "shares_transferred", "counterparty": buyer,
                    "shares_transferred": transferred,
                    "previous_shares_count": transferred + remaining,
                    "shares_count": remaining,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée",
                extra={
                    **common, "action": "appointed_and_shares_received",
                    "counterparty": seller, "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "registry_id": match.group("registry_id").strip(),
                    "country": match.group("country").upper(),
                },
            ),
        ])

    match = _FR_COMMITTEE_ROLE_CORRECTION.search(leftover)
    if match:
        names = _split_names(match.group("names"))
        if len(names) >= 2:
            consume(match)
            rule_id = "fr.persons.committee_role_correction.v1"
            reference = {
                "action": "role_corrected",
                "previous_role": "membre du comité exécutif",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            }
            events.extend(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, name,
                    role="membre du comité de direction", extra=reference,
                )
                for name in names
            )

    match = _DE_PREVIOUS_DOMICILE_OMITTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.previous_domicile_omitted.v1",
            match.group("name"),
            extra={
                "action": "previous_domicile_supplemented",
                "previous_place": match.group("previous_place").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_number": match.group("notice_number"),
                "notice_date": _iso_date(match.group("notice_date")),
            },
        ))

    match = _FR_BOARD_REPLACED_WITH_TWO_WITHOUT_SIGNATURE.search(leftover)
    if match:
        removed_names = _split_names(match.group("removed"))
        if removed_names:
            consume(match)
            rule_id = "fr.persons.board_replaced_two_without_signature.v1"
            events.extend(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", rule_id, name, role="membre du conseil",
                    extra={"action": "removed"},
                )
                for name in removed_names
            )
            for index in (1, 2):
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    place=match.group(f"place{index}"), role="membre du conseil",
                    extra={
                        "action": "appointed", "without_signature": True,
                        "origin": match.group(f"origin{index}").strip(),
                        "country": match.group(f"country{index}").upper(),
                    },
                ))

    match = _IT_OWNER_BANKRUPTCY_SUSPENSIVE_EFFECT_RADIATI.search(leftover)
    if match and match.group("bankruptcy_date") == match.group("previous_bankruptcy_date"):
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.owner_bankruptcy_suspensive_effect_radiati.v1",
            {
                "kind": "bankruptcy_effect_suspended", "scope": "owner",
                "action": "suspended_on_appeal",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "bankruptcy_court": match.group("court").strip(),
                "bankruptcy_decision_date": _iso_date(match.group("bankruptcy_date")),
                "bankruptcy_effective_date": _iso_date(match.group("effective_date")),
                "bankruptcy_effective_time": match.group("effective_time"),
                "previous_bankruptcy_entry_removed": True,
            },
        ))

    match = _FR_NEW_ASSOCIATE_SHARE_TRANSFER.search(leftover)
    if match and (
        match.group("nominal") == match.group("buyer_nominal")
        == match.group("remaining_nominal")
        and _count(match.group("transferred")) == _count(match.group("buyer_count"))
    ):
        consume(match)
        rule_id = "fr.persons.new_associate_share_transfer.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        remaining = _count(match.group("remaining"))
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé",
                extra={
                    **common, "action": "shares_transferred", "counterparty": buyer,
                    "shares_transferred": transferred,
                    "previous_shares_count": transferred + remaining,
                    "shares_count": remaining,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé",
                extra={
                    **common, "action": "appointed_and_shares_received",
                    "counterparty": seller, "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "origin": match.group("origin").strip(),
                    "country": match.group("country").upper(),
                },
            ),
        ])

    match = _DE_SOLE_PROPRIETOR_DELETED_AFTER_CLOSURE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_deleted", "de.text.sole_proprietor_deleted_after_closure.v1",
            {"reason": "business_operations_ceased", "scope": "sole_proprietor"},
        ))

    match = _FR_NEW_ADMINISTRATOR_NO_COLON.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.new_administrator_no_colon.v1",
            match.group("name"), place=match.group("place"), role="administrateur",
            extra={"action": "appointed", "origin": match.group("origin").strip()},
        ))

    match = _FR_REGISTERED_SHARES_TRANSFORMED.search(leftover)
    if match and (
        _count(match.group("from_count")) * _amount(match.group("from_nominal"))
        == _count(match.group("to_count")) * _amount(match.group("to_nominal"))
    ):
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.registered_shares_transformed.v1",
            {
                "kind": "share_split", "currency": "CHF", "registered": True,
                "capital_unchanged": True,
                "from_count": _count(match.group("from_count")),
                "from_nominal": match.group("from_nominal"),
                "to_count": _count(match.group("to_count")),
                "to_nominal": match.group("to_nominal"),
            },
        ))

    match = _FR_BRANCH_PURPOSE_MENTION_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "fr.text.branch_purpose_mention_removed.v1",
            {
                "action": "purpose_mention_removed", "scope": "branch",
                "reason": "not_mandatory",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
            },
        ))

    match = _FR_DOMICILE_CORRECTION_WITH_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.domicile_correction_with_notice.v1",
            match.group("name"), place=match.group("place"),
            extra={
                "action": "domicile_corrected", "domicile_changed": True,
                "previous_place": match.group("previous_place").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_VOTING_PREFERRED_SPLIT_WITH_CAPITAL.search(leftover)
    if match and (
        _count(match.group("from_count")) * _amount(match.group("from_nominal"))
        == _count(match.group("preferred_count"))
        * _amount(match.group("preferred_nominal"))
        and match.group("preferred_count") == match.group("capital_preferred_count")
        and match.group("preferred_nominal") == match.group("capital_preferred_nominal")
        and _amount(match.group("total"))
        == _count(match.group("ordinary_count")) * _amount(match.group("ordinary_nominal"))
        + _count(match.group("preferred_count")) * _amount(match.group("preferred_nominal"))
    ):
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.voting_preferred_split_with_capital.v1",
            {
                "kind": "share_split_and_classes", "currency": "CHF",
                "total": match.group("total"), "fully_paid": True,
                "registered": True,
                "split_from": {
                    "count": _count(match.group("from_count")),
                    "nominal": match.group("from_nominal"),
                },
                "split_to": {
                    "count": _count(match.group("preferred_count")),
                    "nominal": match.group("preferred_nominal"),
                    "kind": "voting_preferred",
                },
                "classes": [
                    {
                        "kind": "ordinary",
                        "count": _count(match.group("ordinary_count")),
                        "nominal": match.group("ordinary_nominal"),
                    },
                    {
                        "kind": "voting_preferred",
                        "count": _count(match.group("preferred_count")),
                        "nominal": match.group("preferred_nominal"),
                    },
                ],
            },
        ))

    return events, re.sub(r"\s+", " ", leftover).strip(" .,;")
