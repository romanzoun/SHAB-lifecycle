from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_AUTHORIZED_CAPITAL_MODIFIED = re.compile(
    r"Mit Beschluss der Generalversammlung vom (?P<date>\d{2}\.\d{2}\.\d{4}) "
    r"wird die Statutenbestimmung über die mit Ermächtigungsbeschluss vom "
    r"(?P<original_date>\d{2}\.\d{2}\.\d{4}) beschlossene genehmigte "
    r"Kapitalerhöhung geändert\.?,?",
    re.I,
)
_DE_LEGAL_BEARER_CONVERSION_ADAPTED = re.compile(
    r"Durch Beschluss der Generalversammlung vom (?P<adaptation_date>\d{2}\.\d{2}\.\d{4}) "
    r"wurden die Statuten der Gesellschaft an die gesetzliche Umwandlung der "
    r"Inhaberaktien auf Namensaktien per (?P<conversion_date>\d{2}\.\d{2}\.\d{4}) "
    r"angepasst\.?,?",
    re.I,
)
_IT_LEGAL_BEARER_CONVERSION_TWO_CLASSES = re.compile(
    r"Nuove azioni:\s*(?P<to_count1>[\d']+) azioni (?P<to_kind1>nominative) da "
    r"CHF (?P<to_nominal1>[\d'.]+) e (?P<to_count2>[\d']+) azioni "
    r"(?P<to_kind2>nominative) da CHF (?P<to_nominal2>[\d'.]+)\s*"
    r"\[finora:\s*(?P<from_count1>[\d']+) azioni (?P<from_kind1>al portatore) da "
    r"CHF (?P<from_nominal1>[\d'.]+) e (?P<from_count2>[\d']+) azioni "
    r"(?P<from_kind2>al portatore) da CHF (?P<from_nominal2>[\d'.]+)\]\.\s*"
    r"In data (?P<date>\d{2}\.\d{2}\.\d{4}) le azioni al portatore sono state "
    r"convertite per legge in azioni nominative\.\s*Gli statuti della società non "
    r"sono ancora stati adeguati;\s*l['’]adeguamento deve avvenire in occasione "
    r"della prossima modifica statutaria\.?,?",
    re.I,
)
_FR_ADAPTED_BEARER_CONVERSION_NUMERIC = re.compile(
    r"Par décision de l['’]assemblée générale du "
    r"(?P<adaptation_date>\d{2}\.\d{2}\.\d{4}),\s*les statuts de la société ont "
    r"été adaptés à la conversion du (?P<conversion_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"Capital-actions:\s*CHF (?P<total>[\d'.]+),\s*libéré à concurrence de CHF "
    r"(?P<paid>[\d'.]+),\s*divisé en (?P<count>[\d']+) actions de CHF "
    r"(?P<nominal>[\d'.]+),\s*(?P<kind>nominatives)(?:,?\s*"
    r"(?P<restriction>liées selon statuts))?\.?,?",
    re.I,
)
_FR_BOARD_MEMBERS_WITHOUT_SIGNATURE_PAIR = re.compile(
    r"(?P<name1>[A-ZÀ-Ÿ][^,.;]+),\s*(?:du|de la|des|de)\s+(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,.;]+),\s*et\s*(?P<name2>[A-ZÀ-Ÿ][^,.;]+),\s*"
    r"(?:du|de la|des|de)\s+(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"sont membres? du conseil,? sans signature\.?,?",
    re.I | re.UNICODE,
)
_FR_LIQUIDATOR_APPOINTED = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,.;]+?)\s+est nommé(?:e)?\s+"
    r"(?P<role>liquidateur|liquidatrice)\.?,?",
    re.I | re.UNICODE,
)
_FR_SIMPLE_BEARER_CONVERSION_CAPITAL = re.compile(
    r"Conversion des actions au porteur en actions nominatives\.\s*"
    r"Capital-actions:\s*CHF (?P<total>[\d'.]+),\s*libéré à concurrence de CHF "
    r"(?P<paid>[\d'.]+),\s*divisé en (?P<count>[\d']+) actions de CHF "
    r"(?P<nominal>[\d'.]+),\s*(?P<kind>nominatives)(?:\s*"
    r"(?P<restriction>liées selon statuts))?\.?"
    r"(?:\s*Nouveau statuts du (?P<statutes_date>\d{2}\.\d{2}\.\d{4})\.?)?",
    re.I,
)
_IT_NON_REGISTERABLE_REMARK_REMOVED = re.compile(
    r"\[La seguente indicazione è radiata in quanto non prevista quale iscrizione "
    r"nel registro di commercio delle società anonime secondo l['’]art\. 45 ORC\.\]\s*"
    r"\[radiati:\s*(?P<removed>Statuti modificati su punti non soggetti a "
    r"pubblicazione\.)\]\.?,?",
    re.I,
)
_DE_AUTHORIZED_CAPITAL_EXPIRED = re.compile(
    r"\[Streichung der Statutenbestimmung über die genehmigte Kapitalerhöhung "
    r"infolge Ablaufs der zeitlichen Befristung\.\]\s*"
    r"\[gestrichen:\s*Die Generalversammlung hat mit Beschluss vom "
    r"(?P<date>\d{2}\.\d{2}\.\d{4}) eine genehmigte Kapitalerhöhung gemäss "
    r"näherer Umschreibung in den Statuten beschlossen\.\]\.?,?",
    re.I,
)
_FR_ERRONEOUS_REGISTRATION_CANCELLED = re.compile(
    r"L['’]inscription no\s*(?P<entry>[\d']+) du "
    r"(?P<date>\d{2}\.\d{2}\.\d{4}) ayant été opérée à tort elle est annulée\.?,?",
    re.I,
)
_DE_LEGAL_BEARER_AND_PARTICIPATION_CONVERSION = re.compile(
    r"Aktien neu:\s*(?P<share_to_count>[\d']+) (?P<share_to_kind>Namenaktien) zu "
    r"CHF (?P<share_to_nominal>[\d'.]+)\s*\[bisher:\s*"
    r"(?P<share_from_count>[\d']+) (?P<share_from_kind>Inhaberaktien) zu CHF "
    r"(?P<share_from_nominal>[\d'.]+)\]\.\s*Partizipationsscheine neu:\s*"
    r"(?P<pc_to_count>[\d']+) (?P<pc_to_kind>Namen-Partizipationsscheine) zu CHF "
    r"(?P<pc_to_nominal>[\d'.]+)\s*\[bisher:\s*(?P<pc_from_count>[\d']+) "
    r"(?P<pc_from_kind>Inhaber-Partizipationsscheine) zu CHF "
    r"(?P<pc_from_nominal>[\d'.]+)\]\.\s*Die Inhaberaktien und "
    r"Inhaber-Partizipationsscheine sind am (?P<date>\d{2}\.\d{2}\.\d{4}) von "
    r"Gesetzes wegen in Namenaktien und Namen-Partizipationsscheine umgewandelt "
    r"worden\.?,?",
    re.I,
)
_DE_LEGAL_BEARER_PARTICIPATION_CONVERSION = re.compile(
    r"Partizipationsscheine neu:\s*(?P<to_count>[\d']+) "
    r"(?P<to_kind>Namen-Partizipationsscheine) zu CHF (?P<to_nominal>[\d'.]+)\s*"
    r"\[bisher:\s*(?P<from_count>[\d']+) "
    r"(?P<from_kind>Inhaber-Partizipationsscheine) zu CHF "
    r"(?P<from_nominal>[\d'.]+)\]\.\s*Die Inhaber-Partizipationsscheine sind am "
    r"(?P<date>\d{2}\.\d{2}\.\d{4}|\d{1,2}\.\s*"
    r"(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+\d{4}) "
    r"von Gesetzes wegen in Namen-Partizipationsscheine umgewandelt worden\.\s*"
    r"Die Statuten der Gesellschaft sind noch nicht an die Umwandlung angepasst "
    r"worden;\s*die Anpassung muss anlässlich der nächsten Statutenänderung "
    r"erfolgen\.?,?",
    re.I,
)
_FR_LEGAL_BEARER_CONVERSION_CAPITAL = re.compile(
    r"Le\s+(?P<date>\d{2}\.\d{2}\.\d{4}|\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}),\s*"
    r"les\s+(?:(?P<from_count>[\d']+)\s+)?actions au porteur ont été converties "
    r"de par la loi en actions nominatives\.\s*Les statuts de la société n['’]ont "
    r"pas encore été adaptés à la conversion,\s*mais devront l['’]être lors de la "
    r"prochaine(?: modification)?\.\s*Capital-actions:\s*CHF (?P<total>[\d'.]+),\s*"
    r"(?:(?P<fully_paid>entièrement libéré)|libéré à concurrence de CHF "
    r"(?P<paid>[\d'.]+)),\s*divisé en\s+(?P<classes>.+?)(?=\.(?:\s|$)|$)",
    re.I,
)
_FR_PREVIOUS_BEARER_FRAGMENT = re.compile(
    r"\(jusqu['’]ici:?\s*(?P<count>[\d']+) actions de CHF "
    r"(?P<nominal>[\d'.]+),\s*au porteur\)\.?,?",
    re.I,
)
_FR_POSTFIX_SHARE_CLASS = re.compile(
    r"(?P<count>[\d']+) actions de CHF (?P<nominal>[\d'.]+),\s*"
    r"(?P<kind>nominatives)(?:,\s*(?P<rights>.+))?",
    re.I,
)
_FR_PREVIOUS_INLINE = re.compile(
    r"\s*\(jusqu['’]ici:?\s*(?P<count>[\d']+) actions de CHF "
    r"(?P<nominal>[\d'.]+),\s*(?P<kind>au porteur)\)\s*$",
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
_DE_MONTHS = {
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
    return f"{year}-{month}-{day}"


def _date(raw: str, months: dict[str, int]) -> str:
    if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", raw):
        return _iso_date(raw)
    day, month, year = re.sub(r"(?<=\d)er\b", "", raw.strip().lower()).split()
    return f"{int(year):04d}-{months[month]:02d}-{int(day.rstrip('.')):02d}"


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
    *,
    place: str | None = None,
    role: str | None = None,
    extra: dict | None = None,
) -> Event:
    clean_name = name.strip()
    clean_place = place.strip() if place else None
    return Event(
        publication_id=publication_id,
        published_at=published_at,
        event_type="officer_changed",
        rule_id=rule_id,
        org_uid=org_uid,
        person_key=person_key(name=clean_name, place=clean_place),
        plz=plz,
        canton=canton,
        role=role,
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def _fr_share_classes(raw: str) -> tuple[list[dict], dict | None]:
    previous = None
    previous_match = _FR_PREVIOUS_INLINE.search(raw)
    if previous_match:
        previous = {
            "count": _count(previous_match.group("count")),
            "nominal": previous_match.group("nominal"),
            "kind": previous_match.group("kind").lower(),
        }
        raw = raw[: previous_match.start()].strip()

    classes = []
    for chunk in re.split(r"\s+et\s+(?=[\d'])", raw, flags=re.I):
        match = _FR_POSTFIX_SHARE_CLASS.fullmatch(chunk.strip())
        if not match:
            return [], previous
        item = {
            "count": _count(match.group("count")),
            "nominal": match.group("nominal"),
            "kind": match.group("kind").lower(),
        }
        if match.group("rights"):
            item["rights"] = match.group("rights").strip()
        classes.append(item)
    return classes, previous


def extract_parser53_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 53."""
    events: list[Event] = []
    leftover = text

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_AUTHORIZED_CAPITAL_MODIFIED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.authorized_capital_modified.v2",
                {
                    "kind": "authorized_capital_clause_modified",
                    "action": "modified",
                    "decision_date": _iso_date(match.group("date")),
                    "authorization_date": _iso_date(match.group("original_date")),
                },
            )
        )

    match = _DE_LEGAL_BEARER_CONVERSION_ADAPTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.legal_bearer_conversion_adapted.v2",
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

    match = _IT_LEGAL_BEARER_CONVERSION_TWO_CLASSES.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "it.text.legal_bearer_conversion.v2",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _iso_date(match.group("date")),
                    "from_kind": "azioni al portatore",
                    "to_kind": "azioni nominative",
                    "share_classes": [
                        {
                            "from_count": _count(match.group(f"from_count{index}")),
                            "from_nominal": match.group(f"from_nominal{index}"),
                            "from_kind": match.group(f"from_kind{index}").lower(),
                            "to_count": _count(match.group(f"to_count{index}")),
                            "to_nominal": match.group(f"to_nominal{index}"),
                            "to_kind": match.group(f"to_kind{index}").lower(),
                        }
                        for index in (1, 2)
                    ],
                    "statutes_adapted": False,
                },
            )
        )

    match = _FR_ADAPTED_BEARER_CONVERSION_NUMERIC.search(leftover)
    if match:
        consume(match)
        paid = match.group("paid")
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.legal_bearer_conversion_adapted.v7",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _iso_date(match.group("conversion_date")),
                    "adaptation_date": _iso_date(match.group("adaptation_date")),
                    "capital_total": match.group("total"),
                    "paid": paid,
                    "paid_in_full": paid == match.group("total"),
                    "from_kind": "au porteur",
                    "to_kind": match.group("kind").lower(),
                    "to_count": _count(match.group("count")),
                    "to_nominal": match.group("nominal"),
                    "restriction": match.group("restriction"),
                    "statutes_adapted": True,
                },
            )
        )

    match = _FR_BOARD_MEMBERS_WITHOUT_SIGNATURE_PAIR.search(leftover)
    if match:
        consume(match)
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "fr.persons.board_members_without_signature.v2",
                    match.group(f"name{index}"), place=match.group(f"place{index}"),
                    role="membre du conseil",
                    extra={
                        "heimat": match.group(f"origin{index}").strip(),
                        "without_signature": True,
                    },
                )
            )

    match = _FR_LIQUIDATOR_APPOINTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "fr.persons.liquidator_appointed.v2", match.group("name"),
                role=match.group("role").lower(),
            )
        )

    match = _FR_ERRONEOUS_REGISTRATION_CANCELLED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", "fr.text.erroneous_registration_cancelled.v1",
                {
                    "kind": "registration_cancelled",
                    "reason": "entered_in_error",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("date")),
                },
            )
        )

    match = _FR_SIMPLE_BEARER_CONVERSION_CAPITAL.search(leftover)
    if match:
        consume(match)
        paid = match.group("paid")
        statutes_date = match.group("statutes_date")
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.bearer_conversion_capital.v2",
                {
                    "kind": "bearer_to_registered_conversion",
                    "capital_total": match.group("total"),
                    "paid": paid,
                    "paid_in_full": paid == match.group("total"),
                    "from_kind": "au porteur",
                    "to_kind": match.group("kind").lower(),
                    "to_count": _count(match.group("count")),
                    "to_nominal": match.group("nominal"),
                    "restriction": match.group("restriction"),
                    "statutes_adapted": bool(statutes_date),
                    "adaptation_date": _iso_date(statutes_date) if statutes_date else None,
                },
            )
        )
        if statutes_date:
            events.append(
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "statutes_changed", "fr.text.statutes_typo.v1",
                    {"date": _iso_date(statutes_date), "raw": match.group(0).split(". ")[-1]},
                )
            )

    match = _IT_NON_REGISTERABLE_REMARK_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", "it.text.non_registerable_remark_removed.v1",
                {
                    "kind": "registry_remark",
                    "action": "removed",
                    "legal_basis": "art. 45 ORC",
                    "removed_fact": match.group("removed"),
                },
            )
        )

    match = _DE_AUTHORIZED_CAPITAL_EXPIRED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.authorized_capital_expired.v2",
                {
                    "kind": "authorized_capital_clause",
                    "action": "removed",
                    "reason": "time_limit_expired",
                    "authorization_date": _iso_date(match.group("date")),
                },
            )
        )

    match = _DE_LEGAL_BEARER_AND_PARTICIPATION_CONVERSION.search(leftover)
    if match:
        consume(match)
        instruments = []
        for prefix, instrument in (("share", "shares"), ("pc", "participation_certificates")):
            instruments.append(
                {
                    "instrument": instrument,
                    "from_count": _count(match.group(f"{prefix}_from_count")),
                    "from_nominal": match.group(f"{prefix}_from_nominal"),
                    "from_kind": match.group(f"{prefix}_from_kind"),
                    "to_count": _count(match.group(f"{prefix}_to_count")),
                    "to_nominal": match.group(f"{prefix}_to_nominal"),
                    "to_kind": match.group(f"{prefix}_to_kind"),
                }
            )
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.legal_bearer_combined_conversion.v1",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _iso_date(match.group("date")),
                    "instruments": instruments,
                },
            )
        )

    match = _DE_LEGAL_BEARER_PARTICIPATION_CONVERSION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.legal_bearer_participation_conversion.v1",
                {
                    "kind": "bearer_to_registered_conversion",
                    "instrument": "participation_certificates",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _date(match.group("date"), _DE_MONTHS),
                    "from_count": _count(match.group("from_count")),
                    "from_nominal": match.group("from_nominal"),
                    "from_kind": match.group("from_kind"),
                    "to_count": _count(match.group("to_count")),
                    "to_nominal": match.group("to_nominal"),
                    "to_kind": match.group("to_kind"),
                    "statutes_adapted": False,
                },
            )
        )

    match = _FR_LEGAL_BEARER_CONVERSION_CAPITAL.search(leftover)
    if match:
        share_classes, previous = _fr_share_classes(match.group("classes"))
        if share_classes:
            consume(match)
            raw_date = match.group("date")
            paid = match.group("paid") or match.group("total")
            explicit_from_count = match.group("from_count")
            payload = {
                "kind": "bearer_to_registered_conversion",
                "legal_basis": "by_operation_of_law",
                "conversion_date": _date(raw_date, _FR_MONTHS),
                "capital_total": match.group("total"),
                "paid": paid,
                "paid_in_full": bool(match.group("fully_paid")) or paid == match.group("total"),
                "from_kind": "au porteur",
                "to_kind": "nominatives",
                "to_count": sum(item["count"] for item in share_classes),
                "share_classes": share_classes,
                "statutes_adapted": False,
            }
            if explicit_from_count:
                payload["from_count"] = _count(explicit_from_count)
            if previous:
                payload.update(
                    {
                        "from_count": previous["count"],
                        "from_nominal": previous["nominal"],
                    }
                )
            events.append(
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "capital_changed", "fr.text.legal_bearer_conversion.v8", payload,
                )
            )

    # Parser 30 already structures this former-capital parenthesis. Some notices
    # use no colon after "jusqu'ici", leaving only the duplicate fragment behind.
    match = _FR_PREVIOUS_BEARER_FRAGMENT.fullmatch(leftover.strip(" .;"))
    if match:
        leftover = ""

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
