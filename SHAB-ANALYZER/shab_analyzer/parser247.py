from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_DE_DEFINITIVE_MORATORIUM_HEAD_OFFICE_COMMISSIONER = re.compile(
    r"^Bemerkungen zum Hauptsitz neu:\s*Mit Entscheid des\s+"
    r"(?P<authority>.+?)\s+vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"wurde eine definitive Nachlassstundung von\s+(?P<duration>\w+)\s+"
    r"Monaten bis\s+(?P<until>\d{2}\.\d{2}\.\d{4})\s+bewilligt\.\s*"
    r"Als Sachwalterin wird die\s+(?P<commissioner>[^,.;]+),\s*Herr\s+"
    r"(?P<contact>[^,.;]+),\s*(?P<street>[^,.;]+),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<place>[^,.;]+),\s*ernannt\.?$",
    re.I | re.UNICODE,
)
_DE_OUTGOING_PERSON_INDIVIDUAL_SIGNATURE = re.compile(
    r"^Ausgeschiedene Personen und erloschene Unterschriften:\s*"
    r"(?P<last>[^,.;]+),\s*(?P<first>[^,.;]+),\s*von\s+"
    r"(?P<origin>[^,.;]+),\s*in\s+(?P<place>[^,.;]+),\s*mit\s+"
    r"(?P<signing>Einzelunterschrift)\.?$",
    re.I | re.UNICODE,
)
_FR_TRANSFER_RESULTING_HOLDINGS = re.compile(
    r"^(?P<seller>[^,.;]+)\s+détient désormais\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+"
    r"par suite de cession de\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<transfer_nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"associé-gérant désormais pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_IT_BANKRUPTCY_REOPENED_AFTER_APPEAL_REJECTED = re.compile(
    r"^Nuova ditta:\s*(?P<name>.+?\s+in liquidazione)\.\s*"
    r"Con decisione del\s+(?P<appeal_date>\d{2}\.\d{2}\.\d{4})\s+la\s+"
    r"(?P<appeal_authority>.+?)\s+ha respinto il reclamo contro la decisione "
    r"di apertura del fallimento della\s+(?P<bankruptcy_authority>.+?)\s+del\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.\s*Il fallimento è quindi "
    r"stato riaperto con effetto a partire dal\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4})\s+alle ore\s+"
    r"(?P<effective_time>\d{2}:\d{2})\.\s*La società è pertanto sciolta\.\s*"
    r"\[radiati:\s*Con decreto del\s+"
    r"(?P<suspension_date>\d{2}\.\d{2}\.\d{4})\s+la\s+"
    r"(?P<previous_appeal_authority>.+?)\s+ha accordato effetto sospensivo al "
    r"reclamo inoltrato contro la decisione di apertura del fallimento della\s+"
    r"(?P<previous_bankruptcy_authority>.+?)\s+del\s+"
    r"(?P<previous_bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"L['’]iscrizione nel registro di commercio relativa allo scioglimento "
    r"della società a seguito di fallimento viene pertanto cancellata\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_BOARD_REPLACEMENT = re.compile(
    r"^(?P<removed1>[^,;]+),\s*(?P<removed2>[^,;]+),\s*et\s+"
    r"(?P<removed3>[^,;]+)\s+ne sont plus membres du conseil de fondation;\s*"
    r"leur signature est radiée\.\s*(?P<vice_president>[^,.;]+)\s+est nommée "
    r"vice-présidente\.\s*Nouveaux membres du conseil de fondation avec "
    r"signature collective à deux\s*:\s*"
    r"(?P<added1>[^,.;]+),\s*de et à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<added2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*et\s+(?P<added3>[^,.;]+),\s*de\s+"
    r"(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_IT_DEFINITIVE_COMPOSITION_MORATORIUM = re.compile(
    r"^Con decreto della\s+(?P<authority>.+?)\s+del\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*alla fondazione è stata "
    r"concessa una moratoria definitiva a scopo di concordato di\s+"
    r"(?P<duration>\d+)\s+mesi\.?$",
    re.I | re.UNICODE,
)
_FR_MALFORMED_STATUTES_SHARE_SPLIT = re.compile(
    r"^Les statuts contiennent désormais l['’]\s+Les\s+"
    r"(?P<before_count>[\d']+|deux)\s+parts de CHF\s+"
    r"(?P<before_nominal>[\d'.]+)\s+ont été divisées en\s+"
    r"(?P<after_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<after_nominal>[\d'.]+)\s+qui se répartiront de la manière suivante:\s*"
    r"les associés\s+(?P<associate1>[^,.;]+),\s*maintenant à\s+"
    r"(?P<place1>[^,.;]+),\s*et\s+(?P<associate2>[^,.;]+),\s*tous deux pour\s+"
    r"(?P<each_count>[\d']+)\s+parts de CHF\s+(?P<each_nominal>[\d'.]+)\.\s*"
    r"La clause statutaire relative à l['’]apport en nature et la reprise de "
    r"biens effectuée à la constitution est abrogée conformément à\s+"
    r"(?P<legal_basis>l['’]article 628 al\. 4 CO \(par renvoi de l['’]art\. 777c CO\))\.\s*"
    r"Gérants:\s*(?P<manager1>[^,.;]+),\s*président,\s*et\s+"
    r"(?P<manager2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_TRANSFER_TO_ORGANIZATION = re.compile(
    r"^(?P<seller>[^,.;]+)\s+a cédé\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>.+?)\s*"
    r"\((?P<buyer_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<buyer_place>[^,.;]+),\s*nouvelle associée pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"par conséquent\s+(?P=seller)\s+est maintenant associé pour\s+"
    r"(?P<seller_count>1)\s+part de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_ADMINISTRATOR_ROLE_AND_DOMICILE = re.compile(
    r"^(?P<name>[^,.;]+),\s*maintenant domicilié à\s+"
    r"(?P<place>[^,.;]+),\s*jusqu['’]ici\s+(?P<previous_role>président),\s*"
    r"désormais\s+(?P<role>administrateur unique),\s*continue de signer "
    r"individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_BOARD_MEMBERS_WITHOUT_SIGNATURE = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:de|du|des|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<country1>[A-Z]{2,3}),\s*et\s+(?P<name2>[^,.;]+),\s*"
    r"(?:de|du|des|d['’])\s*(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*(?P<country2>[A-Z]{2,3}),\s*"
    r"sont membres du conseil d['’]administration,\s*tous deux sans signature\.?$",
    re.I | re.UNICODE,
)
_FR_NOTICE_TWO_ADMINISTRATOR_CHANGES = re.compile(
    r"^L['’]inscription no\.\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(publication FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+page\s+"
    r"(?P<notice_ref>[\d/]+)\)\s+est complété comme suit:\s*"
    r"nouvel administrateur:\s*(?P<new_name>[^,.;]+),\s*de\s+"
    r"(?P<new_origin>[^,.;]+),\s*à\s+(?P<new_place>[^,.;]+),\s*"
    r"avec signature individuelle\.\s*"
    r"L['’]administratrice\s+(?P<president>[^,.;]+)\s+est désormais "
    r"présidente des gérants et continue de signer individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGERS_TRANSFER = re.compile(
    r"^(?P<seller>[^,.;]+),\s*associé-gérant,\s*cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*associée-gérante et "
    r"présidente,\s*laquelle est désormais titulaire de\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_NOMINATIVE_SHARE_SPLIT = re.compile(
    r"^Division des\s+(?P<before_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<before_nominal>[\d'.]+),\s*nominatives,\s*jusqu['’]ici\s+"
    r"liées selon statuts,\s*en\s+"
    r"(?P<after_count>[\d']+)\s+actions de CHF\s+(?P<after_nominal>[\d'.]+)\.\s*"
    r"Capital-actions:\s*CHF\s+(?P<capital>[\d'.]+),\s*entièrement libéré,\s*"
    r"divisé en\s+(?P<capital_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<capital_nominal>[\d'.]+),\s*nominatives\.?$",
    re.I | re.UNICODE,
)
_FR_TRANSFER_TO_NEW_ASSOCIATE_MANAGER = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:de|du|des|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;()]+?)\s*"
    r"\((?P<country>[^)]+)\),\s*nouvel associé-gérant avec signature "
    r"individuelle,\s*avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_EXHAUSTED = re.compile(
    r"^Streichung der Statutenbestimmung über die mit Ermächtigungsbeschluss "
    r"vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+eingeführte genehmigte "
    r"Kapitalerhöhung infolge Ausschöpfung des Erhöhungsbetrages\.?$",
    re.I | re.UNICODE,
)
_DE_ASSOCIATE_REGISTRY_ID_CORRECTED = re.compile(
    r"^Mit dem im SHAB Nr\.\s*(?P<issue>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten TR-Nr\.\s*"
    r"(?P<entry>[\d']+)\s+vom\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"wurde versehentlich die alte CH-Nr\. im bisher Text nicht erfasst,\s*"
    r"jedoch korrekt ist:\s*(?P<name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+"
    r"(?P<place>[^,.;]+),\s*(?P<role>Gesellschafterin),\s*mit einem "
    r"Stammanteil von CHF\s+(?P<nominal>[\d'.]+)\s*\[bisher:\s*"
    r"(?P<previous_name>.+?),\s*(?P<previous_registry_id>CH-[\d.]+-\d)\]\.?$",
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
    "deux": 2,
}


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _count(raw: str) -> int:
    normalized = raw.casefold()
    return (
        int(normalized.replace("'", ""))
        if normalized.replace("'", "").isdigit()
        else _NUMBER_WORDS[normalized]
    )


def _amount(raw: str) -> Decimal:
    return Decimal(raw.replace("'", ""))


def _duration_months(raw: str) -> int | None:
    normalized = raw.casefold()
    return int(normalized) if normalized.isdigit() else _NUMBER_WORDS.get(normalized)


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
        signing=signing,
        payload={
            "name": clean_name,
            "place": clean_place,
            **({"uid": uid} if uid else {}),
            **(extra or {}),
        },
    )


def extract_parser247_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 247."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_DEFINITIVE_MORATORIUM_HEAD_OFFICE_COMMISSIONER.fullmatch(leftover)
    if match:
        return [
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.definitive_moratorium_head_office_commissioner.v1",
                {
                    "kind": "definitive_moratorium",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "authority": match.group("authority").strip(),
                    "duration_months": _duration_months(match.group("duration")),
                    "until": _iso_date(match.group("until")),
                    "commissioner": match.group("commissioner").strip(),
                    "commissioner_contact": match.group("contact").strip(),
                    "commissioner_address": {
                        "street": match.group("street").strip(),
                        "postal_code": match.group("postal_code"),
                        "place": match.group("place").strip(),
                    },
                    "head_office_note": True,
                },
            )
        ], ""

    match = _DE_OUTGOING_PERSON_INDIVIDUAL_SIGNATURE.fullmatch(leftover)
    if match:
        return [
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_removed",
                "de.persons.outgoing_individual_signature.v1",
                f"{match.group('last')} {match.group('first')}",
                place=match.group("place"),
                signing="Einzelunterschrift erloschen",
                extra={
                    "action": "removed",
                    "origin": match.group("origin").strip(),
                    "previous_signing": match.group("signing"),
                },
            )
        ], ""

    match = _FR_TRANSFER_RESULTING_HOLDINGS.fullmatch(leftover)
    if match and len(
        {
            match.group("nominal"),
            match.group("transfer_nominal"),
            match.group("buyer_nominal"),
        }
    ) == 1:
        rule_id = "fr.persons.share_transfer_resulting_holdings.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        seller_count = _count(match.group("seller_count"))
        buyer_count = _count(match.group("buyer_count"))
        if buyer_count < transferred:
            return [], leftover
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                seller,
                role="associé",
                extra={
                    **common,
                    "action": "shares_transferred",
                    "counterparty": buyer,
                    "shares_before": seller_count + transferred,
                    "shares_transferred": transferred,
                    "shares_count": seller_count,
                },
            ),
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                buyer,
                role="associé-gérant",
                extra={
                    **common,
                    "action": "shares_received",
                    "counterparty": seller,
                    "shares_before": buyer_count - transferred,
                    "shares_received": transferred,
                    "shares_count": buyer_count,
                },
            ),
        ], ""

    match = _IT_BANKRUPTCY_REOPENED_AFTER_APPEAL_REJECTED.fullmatch(leftover)
    if match and (
        match.group("appeal_authority") == match.group("previous_appeal_authority")
        and match.group("bankruptcy_authority")
        == match.group("previous_bankruptcy_authority")
        and match.group("bankruptcy_date")
        == match.group("previous_bankruptcy_date")
    ):
        return [
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "it.text.bankruptcy_reopened_after_appeal_rejected.v1",
                {
                    "kind": "bankruptcy_reopened",
                    "company_name": match.group("name").strip(),
                    "appeal_decision_date": _iso_date(match.group("appeal_date")),
                    "appeal_authority": match.group("appeal_authority").strip(),
                    "appeal_result": "rejected",
                    "bankruptcy_authority": match.group(
                        "bankruptcy_authority"
                    ).strip(),
                    "bankruptcy_decision_date": _iso_date(
                        match.group("bankruptcy_date")
                    ),
                    "effective_date": _iso_date(match.group("effective_date")),
                    "effective_time": match.group("effective_time"),
                    "dissolved": True,
                    "previous_suspension_date": _iso_date(
                        match.group("suspension_date")
                    ),
                    "previous_suspension_removed": True,
                },
            )
        ], ""

    match = _FR_FOUNDATION_BOARD_REPLACEMENT.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.foundation_board_replacement.v1"
        events = [
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_removed",
                rule_id,
                match.group(f"removed{index}"),
                role="membre du conseil de fondation",
                signing="Unterschrift erloschen",
                extra={"action": "removed", "signing_revoked": True},
            )
            for index in (1, 2, 3)
        ]
        events.append(
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                match.group("vice_president"),
                role="vice-présidente",
                extra={"action": "appointed_vice_president"},
            )
        )
        for index in (1, 2, 3):
            origin = (
                match.group("place1")
                if index == 1
                else match.group(f"origin{index}")
            )
            events.append(
                _person_event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    rule_id,
                    match.group(f"added{index}"),
                    place=match.group(f"place{index}"),
                    role="membre du conseil de fondation",
                    signing="Kollektivunterschrift zu zweien",
                    extra={"action": "appointed", "origin": origin.strip()},
                )
            )
        return events, ""

    match = _IT_DEFINITIVE_COMPOSITION_MORATORIUM.fullmatch(leftover)
    if match:
        return [
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "it.text.definitive_composition_moratorium.v1",
                {
                    "kind": "definitive_moratorium",
                    "purpose": "composition",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "authority": match.group("authority").strip(),
                    "duration_months": int(match.group("duration")),
                    "subject_kind": "foundation",
                },
            )
        ], ""

    match = _FR_MALFORMED_STATUTES_SHARE_SPLIT.fullmatch(leftover)
    if match:
        before_count = _count(match.group("before_count"))
        after_count = _count(match.group("after_count"))
        each_count = _count(match.group("each_count"))
        if not (
            _amount(match.group("before_nominal")) * before_count
            == _amount(match.group("after_nominal")) * after_count
            and match.group("after_nominal") == match.group("each_nominal")
            and each_count * 2 == after_count
            and match.group("associate1") == match.group("manager1")
            and match.group("associate2") == match.group("manager2")
        ):
            return [], leftover
        rule_id = "fr.text.malformed_statutes_share_split.v1"
        common = {
            "shares_count": each_count,
            "share_nominal": match.group("each_nominal"),
            "currency": "CHF",
        }
        return [
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                rule_id,
                {
                    "kind": "share_split",
                    "before_count": before_count,
                    "before_nominal": match.group("before_nominal"),
                    "after_count": after_count,
                    "after_nominal": match.group("after_nominal"),
                    "currency": "CHF",
                    "source_intro_malformed": True,
                },
            ),
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                rule_id,
                {
                    "kind": "contribution_in_kind_clause",
                    "action": "removed",
                    "legal_basis": match.group("legal_basis"),
                },
            ),
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                match.group("associate1"),
                place=match.group("place1"),
                role="associé-gérant président",
                extra={**common, "action": "holding_and_management_confirmed"},
            ),
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                match.group("associate2"),
                role="associé-gérant",
                extra={**common, "action": "holding_and_management_confirmed"},
            ),
        ], ""

    match = _FR_PERSON_TRANSFER_TO_ORGANIZATION.fullmatch(leftover)
    if match and (
        _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and len(
            {
                match.group("nominal"),
                match.group("buyer_nominal"),
                match.group("seller_nominal"),
            }
        )
        == 1
    ):
        rule_id = "fr.persons.person_transfer_to_organization.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        seller_count = _count(match.group("seller_count"))
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                seller,
                role="associé",
                extra={
                    **common,
                    "action": "shares_transferred",
                    "counterparty": buyer,
                    "counterparty_uid": match.group("buyer_uid"),
                    "shares_before": seller_count + transferred,
                    "shares_transferred": transferred,
                    "shares_count": seller_count,
                },
            ),
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                buyer,
                place=match.group("buyer_place"),
                role="associée",
                uid=match.group("buyer_uid"),
                extra={
                    **common,
                    "action": "appointed_associate_and_shares_received",
                    "counterparty": seller,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                },
            ),
        ], ""

    match = _FR_SOLE_ADMINISTRATOR_ROLE_AND_DOMICILE.fullmatch(leftover)
    if match:
        return [
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.sole_administrator_role_and_domicile.v1",
                match.group("name"),
                place=match.group("place"),
                role=match.group("role"),
                signing="Einzelunterschrift",
                extra={
                    "action": "domicile_and_role_changed",
                    "previous_role": match.group("previous_role"),
                    "signing_continues": True,
                },
            )
        ], ""

    match = _FR_TWO_BOARD_MEMBERS_WITHOUT_SIGNATURE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_board_members_without_signature.v1"
        return [
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role="membre du conseil d'administration",
                signing="ohne Unterschrift",
                extra={
                    "action": "appointed",
                    "origin": match.group(f"origin{index}").strip(),
                    "country": match.group(f"country{index}"),
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_NOTICE_TWO_ADMINISTRATOR_CHANGES.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.notice_two_administrator_changes.v1"
        notice = {
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_ref": match.group("notice_ref"),
        }
        return [
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                match.group("new_name"),
                place=match.group("new_place"),
                role="administrateur",
                signing="Einzelunterschrift",
                extra={
                    **notice,
                    "action": "appointed",
                    "origin": match.group("new_origin").strip(),
                },
            ),
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                match.group("president"),
                role="présidente des gérants",
                signing="Einzelunterschrift",
                extra={
                    **notice,
                    "action": "appointed_president",
                    "signing_continues": True,
                },
            ),
        ], ""

    match = _FR_ASSOCIATE_MANAGERS_TRANSFER.fullmatch(leftover)
    if match and (
        _count(match.group("before")) - _count(match.group("transferred"))
        == _count(match.group("remaining"))
        and len(
            {
                match.group("nominal"),
                match.group("buyer_nominal"),
                match.group("remaining_nominal"),
            }
        )
        == 1
    ):
        rule_id = "fr.persons.associate_managers_transfer.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        if buyer_count < transferred:
            return [], leftover
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                seller,
                role="associé-gérant",
                extra={
                    **common,
                    "action": "shares_transferred",
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                },
            ),
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                buyer,
                role="associée-gérante et présidente",
                extra={
                    **common,
                    "action": "shares_received",
                    "counterparty": seller,
                    "shares_before": buyer_count - transferred,
                    "shares_received": transferred,
                    "shares_count": buyer_count,
                },
            ),
        ], ""

    match = _FR_NOMINATIVE_SHARE_SPLIT.fullmatch(leftover)
    if match:
        before_count = _count(match.group("before_count"))
        after_count = _count(match.group("after_count"))
        capital_count = _count(match.group("capital_count"))
        capital = _amount(match.group("capital"))
        if not (
            _amount(match.group("before_nominal")) * before_count == capital
            and _amount(match.group("after_nominal")) * after_count == capital
            and _amount(match.group("capital_nominal")) * capital_count == capital
            and after_count == capital_count
            and match.group("after_nominal") == match.group("capital_nominal")
        ):
            return [], leftover
        return [
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.nominative_share_split.v1",
                {
                    "kind": "share_split",
                    "capital": match.group("capital"),
                    "currency": "CHF",
                    "fully_paid": True,
                    "share_kind": "nominative",
                    "before_count": before_count,
                    "before_nominal": match.group("before_nominal"),
                    "after_count": after_count,
                    "after_nominal": match.group("after_nominal"),
                },
            )
        ], ""

    match = _FR_TRANSFER_TO_NEW_ASSOCIATE_MANAGER.fullmatch(leftover)
    if match and (
        _count(match.group("before")) - _count(match.group("transferred"))
        == _count(match.group("remaining"))
        and _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and len(
            {
                match.group("nominal"),
                match.group("buyer_nominal"),
                match.group("remaining_nominal"),
            }
        )
        == 1
    ):
        rule_id = "fr.persons.transfer_to_new_associate_manager.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                seller,
                role="associé",
                extra={
                    **common,
                    "action": "shares_transferred",
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                },
            ),
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                buyer,
                place=match.group("place"),
                role="associé-gérant",
                signing="Einzelunterschrift",
                extra={
                    **common,
                    "action": "appointed_associate_manager_and_shares_received",
                    "origin": match.group("origin").strip(),
                    "country": match.group("country").strip(),
                    "counterparty": seller,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                },
            ),
        ], ""

    match = _DE_AUTHORIZED_CAPITAL_EXHAUSTED.fullmatch(leftover)
    if match:
        return [
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "de.text.authorized_capital_exhausted.v1",
                {
                    "kind": "authorized_capital_clause",
                    "action": "removed_after_exhaustion",
                    "authorization_date": _iso_date(match.group("date")),
                    "reason": "increase_amount_exhausted",
                },
            )
        ], ""

    match = _DE_ASSOCIATE_REGISTRY_ID_CORRECTED.fullmatch(leftover)
    if match and match.group("name") == match.group("previous_name"):
        return [
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "de.persons.associate_registry_id_corrected.v1",
                match.group("name"),
                place=match.group("place"),
                role=match.group("role"),
                uid=match.group("uid"),
                extra={
                    "action": "uid_supplemented",
                    "shares_count": 1,
                    "share_nominal": match.group("nominal"),
                    "currency": "CHF",
                    "previous_registry_id": match.group("previous_registry_id"),
                    "issue": int(match.group("issue")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                },
            )
        ], ""

    return [], leftover
