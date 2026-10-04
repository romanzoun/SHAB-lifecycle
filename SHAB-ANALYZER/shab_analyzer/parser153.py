from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_BRANCH_PURPOSE_INFORMATION_REMOVED = re.compile(
    r"^(?:(?P<notice_date_fragment>\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\.\s*)?Suite à la modification du droit du "
    r"registre du commerce et en application de l['’]art\.\s*110,\s*al\.\s*1 "
    r"ORC,\s*les informations relatives au but sont radiées\.?$",
    re.I | re.UNICODE,
)
_DE_COMPOSITION_MORATORIUM_GRANTED_SUMMARY = re.compile(
    r"^Mit Verfügung vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat das\s+"
    r"(?P<authority>.+?)\s+im summarischen Verfahren eine Nachlassstundung von\s+"
    r"(?P<duration>\d+)\s+Monaten gewährt\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_SEAT_WITH_ADDRESS = re.compile(
    r"^Nouveau siège:\s*(?P<seat>[^,.;]+),\s*(?P<street>.+?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<locality>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_EXTENDED_WITH_HISTORY = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat der\s+"
    r"(?P<authority>.+?)\s+die mit Entscheid vom\s+"
    r"(?P<grant_date>\d{2}\.\d{2}\.\d{4})\s+gewährte definitive "
    r"Nachlassstundung bis\s+(?P<until>\d{2}\.\d{2}\.\d{4})\s+verlängert\.\s*"
    r"\[bisher:\s*Mit Entscheid vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+hat der\s+"
    r"(?P<previous_authority>.+?)\s+die mit Verfügung vom\s+"
    r"(?P<previous_grant_date>\d{2}\.\d{2}\.\d{4})\s+gewährte definitive "
    r"Nachlassstundung bis\s+(?P<previous_until>\d{2}\.\d{2}\.\d{4})\s+"
    r"verlängert\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_MERGER_MALFORMED_DUPLICATE_UID = re.compile(
    r"^Fusion:\s*Übernahme der Aktiven und Passiven der\s+"
    r"(?P<absorbed_name>.+?),\s*in\s+(?P<absorbed_place>[^,.;]+)\s*"
    r"\(CHE-\s*CHE-(?P<uid_digits>\d{3}\.\d{3}\.\d{3})\?\),\s*"
    r"gemäss Fusionsvertrag vom\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"und Bilanz per\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+und Passiven\s*"
    r"\(Fremdkapital\)\s+von CHF\s+(?P<liabilities>[\d'.]+)\s+gehen auf die "
    r"übernehmende Gesellschaft über\.\s*Da die übernehmende Gesellschaft "
    r"sämtliche Aktien der übertragenden Gesellschaft hält,\s*findet weder eine "
    r"Kapitalerhöhung noch eine Aktienzuteilung statt\.?$",
    re.I | re.UNICODE,
)
_FR_FOUR_MANAGERS_PRESIDENT_COLLECTIVE = re.compile(
    r"^Gérants:\s*(?P<president>[^,.;]+),\s*nommé président,\s*"
    r"(?P<manager2>[^,.;]+),\s*de et à\s+(?P<place2>[^,.;]+),\s*"
    r"(?P<manager3>[^,.;]+),\s*de\s+(?P<origin3>[^,.;]+),\s*à\s+"
    r"(?P<place3>[^,.;]+),\s*(?P<country3>[A-Z])\s+et\s+"
    r"(?P<manager4>[^,.;]+),\s*de\s+(?P<origin4>[^,.;]+),\s*à\s+"
    r"(?P<place4>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_CORPORATE_ASSOCIATE_TRANSFER_AND_TWO_DIRECTORS = re.compile(
    r"^L['’]associée\s+(?P<seller>.+?)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*(?P<country>[A-Z]),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"Ce dernier est nommé directeur(?:\.\s*)?\s*L['’]associée\s+"
    r"(?P<director>[^,.;]+)\s+est nommée directrice,\s*a désormais la "
    r"signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_FR_PROXY_REVOKED_APPOINTED_SUBDIRECTOR = re.compile(
    r"^(?P<name>[^,.;]+),\s*dont la procuration est éteinte,\s*est "
    r"nommé(?:e)?\s+(?P<role>sous-directeur|sous-directrice)\.?$",
    re.I | re.UNICODE,
)
_FR_FEMALE_MANAGER_TRANSFER_TO_NEW_MANAGER_PRESIDENT = re.compile(
    r"^Jusqu['’]ici titulaire de\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*maintenant domiciliée à\s+"
    r"(?P<seller_place>[^,.;]+),\s*l['’]associée-gérante\s+"
    r"(?P<seller>[^,.;]+)\s+détient\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\s+par suite de cession de\s+"
    r"(?P<transferred>[\d']+)\s+parts à\s+(?P<buyer>[^,.;]+),\s*"
    r"d['’](?P<origin>[^,.;]+),\s*à\s+(?P<buyer_place>[^,.;]+),\s*"
    r"nouvel associé-gérant pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*nommé président\.?$",
    re.I | re.UNICODE,
)
_FR_CAPITAL_SUPPLEMENT_PAGE_REFERENCE = re.compile(
    r"^L['’]inscription\s+N°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée comme suit:\s*Capital\s*:\s*"
    r"CHF\s+(?P<capital>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PRESIDENT_MOVED_MEMBER_AND_NEW_MEMBER = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé président,\s*lequel "
    r"continue à signer individuellement,\s*(?P<moved>[^,.;]+),\s*maintenant "
    r"domicilié à\s+(?P<moved_place>[^,.;]+),\s*(?P<moved_country>[A-Z])\s*;\s*"
    r"sa procuration est radiée et\s+(?P<member>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<member_place>[^,.;]+),\s*avec signature "
    r"collective à deux,\s*avec les deux premiers\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_PROXIES_RESTRICTION_REMOVED = re.compile(
    r"^(?P<name1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+),\s*qui est maintenant à\s+"
    r"(?P<place2>[^,.;]+),\s*continuent d['’]engager la société par une "
    r"procuration collective à deux,\s*désormais sans restriction\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MEMBER_ADMINISTRATION_MIXED_SIGNING = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*président,\s*et\s+"
    r"(?P<member>[^.;]+)\.\s*Signature individuelle du président ou "
    r"collective à deux de l['’]autre membre du conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_DE_NEW_ADDITIONAL_STREET_ADDRESS = re.compile(
    r"^Neue zusätzliche Adresse:\s*(?P<street>.+?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<locality>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_TO_NEW_MANAGER_PRESIDENT = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de et à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé-gérant président,\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_OWNER_BANKRUPTCY_APPEAL_SUSPENSIVE_MALE = re.compile(
    r"^Der Abteilungspräsident der\s+(?P<department>.+?)\s+des\s+"
    r"(?P<authority>.+?)\s+hat mit Entscheid vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+der gegen die Konkurseröffnung "
    r"erhobenen Beschwerde aufschiebende Wirkung zuerkannt\s*\[bisher:\s*"
    r"Über den Inhaber dieses Einzelunternehmens ist mit Entscheid des\s+"
    r"(?P<bankruptcy_court>.+?)\s+vom\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<bankruptcy_time>\d{1,2}[.:]\d{2})\s+Uhr,\s*der Konkurs eröffnet "
    r"worden\.\]\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


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


def extract_parser153_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 153."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_BRANCH_PURPOSE_INFORMATION_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "purpose_changed", "fr.text.branch_purpose_information_removed_art110.v1",
            {
                "action": "removed", "scope": "branch",
                "kind": "purpose_information", "legal_basis": "Art. 110 al. 1 ORC",
                "reason": "commercial_register_law_change",
                **(
                    {
                        "notice_date_fragment": match.group("notice_date_fragment"),
                        "notice_ref": match.group("notice_ref"),
                    }
                    if match.group("notice_ref") else {}
                ),
            },
        ))

    match = _DE_COMPOSITION_MORATORIUM_GRANTED_SUMMARY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.composition_moratorium_granted_summary.v1",
            {
                "kind": "composition_moratorium_granted", "action": "granted",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "procedure": "summary", "duration_months": int(match.group("duration")),
            },
        ))

    match = _FR_NEW_SEAT_WITH_ADDRESS.search(leftover)
    if match:
        consume(match)
        address = (
            f"{match.group('street').strip()}, {match.group('postal_code')} "
            f"{match.group('locality').strip()}"
        )
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "seat_changed", "fr.text.new_seat_with_address.v1",
            {
                "action": "changed", "seat": match.group("seat").strip(),
                "address": address, "street": match.group("street").strip(),
                "postal_code": match.group("postal_code"),
                "locality": match.group("locality").strip(),
            },
        ))

    match = _DE_DEFINITIVE_MORATORIUM_EXTENDED_WITH_HISTORY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed",
            "de.text.definitive_moratorium_extended_with_history.v1",
            {
                "kind": "composition_moratorium_extended", "action": "extended",
                "moratorium_type": "definitive",
                "decision_date": _iso_date(match.group("decision_date")),
                "grant_date": _iso_date(match.group("grant_date")),
                "until": _iso_date(match.group("until")),
                "authority": match.group("authority").strip(),
                "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                "previous_grant_date": _iso_date(match.group("previous_grant_date")),
                "previous_until": _iso_date(match.group("previous_until")),
                "previous_authority": match.group("previous_authority").strip(),
            },
        ))

    match = _DE_MERGER_MALFORMED_DUPLICATE_UID.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "de.text.merger_malformed_duplicate_uid.v1",
            {
                "kind": "absorption",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": f"CHE-{match.group('uid_digits')}",
                "source_uid_malformed": True,
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "currency": "CHF", "liabilities_kind": "third_party_capital",
                "all_shares_held_by_acquirer": True,
                "capital_increase": False, "share_allocation": False,
            },
        ))

    match = _FR_FOUR_MANAGERS_PRESIDENT_COLLECTIVE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.four_managers_president_collective.v1"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("president"),
            role="gérant président", signing="Kollektivunterschrift zu zweien",
            extra={"action": "appointed_president"},
        ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("manager2"),
            place=match.group("place2"), role="gérant",
            signing="Kollektivunterschrift zu zweien",
            extra={"action": "recorded", "heimat": match.group("place2").strip()},
        ))
        for index in (3, 4):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"manager{index}"),
                place=match.group(f"place{index}"), role="gérant",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "recorded",
                    "heimat": match.group(f"origin{index}").strip(),
                    **(
                        {"country": match.group("country3")}
                        if index == 3 else {}
                    ),
                },
            ))

    match = _FR_CORPORATE_ASSOCIATE_TRANSFER_AND_TWO_DIRECTORS.search(leftover)
    if match and (
        match.group("nominal") == match.group("buyer_nominal")
        and _count(match.group("transferred")) == _count(match.group("buyer_count"))
    ):
        consume(match)
        rule_id = "fr.persons.corporate_transfer_and_two_directors.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {
            "shares_count": _count(match.group("transferred")),
            "share_nominal": match.group("nominal"), "currency": "CHF",
        }
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associée",
                extra={**common, "action": "shares_transferred", "counterparty": buyer},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé et directeur", signing="Kollektivunterschrift zu zweien",
                extra={
                    **common, "action": "shares_received_and_appointed_director",
                    "counterparty": seller, "new_associate": True,
                    "heimat": match.group("origin").strip(),
                    "country": match.group("country"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("director"),
                role="associée et directrice", signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed_director_and_signing_changed"},
            ),
        ])

    match = _FR_PROXY_REVOKED_APPOINTED_SUBDIRECTOR.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.proxy_revoked_appointed_subdirector.v1",
            match.group("name"), role=match.group("role").lower(),
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "appointed_and_signing_changed",
                "previous_signing": "procuration", "previous_signing_revoked": True,
            },
        ))

    match = _FR_FEMALE_MANAGER_TRANSFER_TO_NEW_MANAGER_PRESIDENT.search(leftover)
    if match and (
        _count(match.group("before"))
        == _count(match.group("remaining")) + _count(match.group("transferred"))
        and _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and len({
            match.group("nominal"), match.group("remaining_nominal"),
            match.group("buyer_nominal"),
        }) == 1
    ):
        consume(match)
        rule_id = "fr.persons.female_manager_transfer_new_manager_president.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, place=match.group("seller_place"),
                role="associée-gérante",
                extra={
                    **common, "action": "domicile_changed_and_shares_transferred",
                    "domicile_changed": True, "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("buyer_place"),
                role="associé-gérant président", signing="Einzelunterschrift",
                extra={
                    **common, "action": "shares_received_and_appointed_president",
                    "counterparty": seller, "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "heimat": match.group("origin").strip(), "new_associate": True,
                },
            ),
        ])

    match = _FR_CAPITAL_SUPPLEMENT_PAGE_REFERENCE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.capital_supplement_page_reference.v1",
            {
                "kind": "share_capital", "action": "publication_supplemented",
                "currency": "CHF", "total": match.group("capital"),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_ADMINISTRATION_PRESIDENT_MOVED_MEMBER_AND_NEW_MEMBER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_president_moved_and_new_member.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président", signing="Einzelunterschrift",
                extra={"action": "appointed_president", "signing_continues": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("moved"),
                place=match.group("moved_place"), role="administrateur",
                signing="Einzelunterschrift",
                extra={
                    "action": "domicile_changed", "domicile_changed": True,
                    "country": match.group("moved_country"),
                    "previous_signing": "procuration", "procuration_revoked": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                place=match.group("member_place"), role="administrateur",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed", "heimat": match.group("origin").strip(),
                    "signing_with": "les deux premiers",
                },
            ),
        ])

    match = _FR_TWO_PROXIES_RESTRICTION_REMOVED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_proxies_restriction_removed.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                place=match.group("place2") if index == 2 else None,
                signing="Kollektivprokura zu zweien",
                extra={
                    "action": "restriction_removed", "signing_continues": True,
                    **(
                        {"domicile_changed": True}
                        if index == 2 else {}
                    ),
                },
            ))

    match = _FR_TWO_MEMBER_ADMINISTRATION_MIXED_SIGNING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_member_administration_mixed_signing.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                place=match.group("place"), role="président",
                signing="Einzelunterschrift",
                extra={"action": "recorded", "heimat": match.group("origin").strip()},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                role="administrateur", signing="Kollektivunterschrift zu zweien",
                extra={"action": "recorded"},
            ),
        ])

    match = _DE_NEW_ADDITIONAL_STREET_ADDRESS.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "de.text.new_additional_street_address.v1",
            {
                "action": "added", "kind": "additional_address",
                "address": (
                    f"{match.group('street').strip()}, {match.group('postal_code')} "
                    f"{match.group('locality').strip()}"
                ),
                "street": match.group("street").strip(),
                "postal_code": match.group("postal_code"),
                "locality": match.group("locality").strip(),
            },
        ))

    match = _FR_MANAGER_TRANSFER_TO_NEW_MANAGER_PRESIDENT.search(leftover)
    if match and (
        _count(match.group("before"))
        == _count(match.group("remaining")) + _count(match.group("transferred"))
        and match.group("nominal") == match.group("remaining_nominal")
    ):
        consume(match)
        rule_id = "fr.persons.manager_transfer_new_manager_president.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant",
                extra={
                    **common, "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé-gérant président", signing="Einzelunterschrift",
                extra={
                    **common, "action": "shares_received_and_appointed_president",
                    "counterparty": seller, "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("transferred")),
                    "heimat": match.group("place").strip(), "new_associate": True,
                },
            ),
        ])

    match = _DE_OWNER_BANKRUPTCY_APPEAL_SUSPENSIVE_MALE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.owner_bankruptcy_appeal_suspensive_male.v1",
            {
                "kind": "bankruptcy_effect_suspended",
                "scope": "sole_proprietor_owner", "action": "suspensive_effect_granted",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "department": match.group("department").strip(),
                "bankruptcy_court": match.group("bankruptcy_court").strip(),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "bankruptcy_time": match.group("bankruptcy_time").replace(".", ":"),
            },
        ))

    return events, re.sub(r"\s+", " ", leftover).strip(" .,;")
