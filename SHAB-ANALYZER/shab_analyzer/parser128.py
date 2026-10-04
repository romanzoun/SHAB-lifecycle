from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_PRESIDENT_AND_THREE_BOARD_MEMBERS = re.compile(
    r"^L['’]administrateur\s+(?P<president>[^,.;]+),\s*nommé président,\s*"
    r"lequel continue à signer individuellement\.\s*"
    r"(?P<name1>[^,.;]+),\s*de et à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*de et à\s+(?P<place2>[^,.;]+),\s*et\s*"
    r"(?P<name3>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+),\s*"
    r"sont membres du conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBER_COUNTRY = re.compile(
    r"^(?P<name>[^,;]+?),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{2,3}),\s*est membre du conseil\.?$",
    re.I | re.UNICODE,
)
_FR_CORRECTED_PRIVILEGED_SHARES_TO_ORGANIZATION = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le gérant\s+"
    r"(?P<seller>[^,.;]+)\s+a cédé ses\s+(?P<count>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+privilégiées quant au droit de vote à\s+"
    r"(?P<buyer>.+?)\s*\((?P<buyer_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvelle associée\s*\(et non à\s+"
    r"(?P<previous_buyer>.+?)\s*\((?P<previous_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+"
    r"comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_PRESIDENT_AND_PREVIOUS_PRESIDENT = re.compile(
    r"^(?P<name1>[^,.;]+),\s*nommée? présidente?,\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*jusqu['’]ici président,\s*"
    r"membres du conseil d['’]administration,\s*continuent de signer "
    r"collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_WITH_ANOTHER_MEMBER = re.compile(
    r"^Nouveau membre du conseil de fondation avec un autre membre du conseil "
    r"de fondation:\s*(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SUPERVISORY_AUDIT_WAIVER_MENTION_REMOVED = re.compile(
    r"^La mention relative à la renonc(?:i)?ation au contrôle restreint(?:e)? "
    r"est radiée par décision de l['’](?P<authority>.+?)\s+du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ASSOCIATES_TRANSFER_TO_NEW_MANAGER = re.compile(
    r"^(?P<seller1>[^,.;]+)\s+et\s+(?P<seller2>[^,.;]+)\s+ont cédé\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"lequel associé est en outre nommé gérant\s*Par conséquent,\s*"
    r"(?P=seller1)\s+et\s+(?P=seller2)\s+sont désormais titulaires de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\s+"
    r"chacun\.?$",
    re.I | re.UNICODE,
)
_DE_NOMINAL_REDUCTION_TO_COVER_DEFICIT = re.compile(
    r"^Bei der Kapitalherabsetzung vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"wird der Nennwert der\s+(?P<count>[\d']+)\s+(?P<share_kind>Namenaktien)\s+"
    r"zu CHF\s+(?P<from_nominal>[\d'.]+)\s+zur Beseitigung einer Unterbilanz "
    r"auf CHF\s+(?P<to_nominal>[\d'.]+)\s+herabgesetzt\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_GENERAL_PARTNERS = re.compile(
    r"^Nouveaux associés indéfiniment responsables:\s*"
    r"(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_FOUNDATION_MEMBERS_WITHOUT_SIGNATURE = re.compile(
    r"^Nouveaux membres du conseil de fondation sans signature:\s*"
    r"(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*tous deux à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_ERRONEOUS_REMOVAL_CORRECTED = re.compile(
    r"^L['’]inscription\s+N°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée comme suit:\s*"
    r"(?P<name>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{2,3}),\s*reste\s+(?P<role>gérant-président)\s*"
    r"\(sa radiation était erronée\)\.?$",
    re.I | re.UNICODE,
)
_FR_OWNER_BANKRUPTCY_REVOKED = re.compile(
    r"^Par décision du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>.+?)\s+a annulé la faillite du titulaire de l['’]entreprise "
    r"prononcée le\s+(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4});\s*"
    r"l['’]inscription est rétablie comme ci-devant\s*\(FOSC no\s+"
    r"(?P<notice_number>\d+)\s+du\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"publ\.\s+(?P<notice_id>[\d']+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_ANCILLARY_OBLIGATIONS_MENTION_REMOVED = re.compile(
    r"^Radiation de la mention relative aux obligations de fournir des prestations "
    r"accessoires,\s*droits de préférence,\s*de préemption ou d['’]emption\.?$",
    re.I | re.UNICODE,
)
_IT_BRANCH_IDENTIFIER_CHANGED = re.compile(
    r"^Modifica succursale:\s*(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s*\[finora:\s*"
    r"(?P=place)\s*\((?P<previous_id>CH-[\d.\-]+)\)\]\.?$",
    re.I | re.UNICODE,
)
_DE_PARTNERSHIP_TO_CORPORATION_TRANSFORMATION = re.compile(
    r"^Umwandlung:\s*Die Kollektivgesellschaft wird gemäss Umwandlungsplan vom\s+"
    r"(?P<plan_date>\d{2}\.\d{2}\.\d{4})\s+und Bilanz per\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\s+mit Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven \(Fremdkapital\) von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+in eine Aktiengesellschaft umgewandelt\.\s*"
    r"Die Gesellschafter erhalten\s+(?P<shares>[\d']+)\s+Aktien zu CHF\s+"
    r"(?P<share_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_REGISTERED_TO_BEARER_SHARES_SUPPLEMENT = re.compile(
    r"^Complément:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée en ce sens que les\s+"
    r"(?P<from_count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<from_nominal>[\d'.]+)\s+avec restrictions quant à la transmissibilité,\s*"
    r"formant l['’]entier du capital-actions,\s*sont converties en\s+"
    r"(?P<to_count>[\d']+)\s+actions au porteur de CHF\s+"
    r"(?P<to_nominal>[\d'.]+)\.?$",
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
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser128_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 128."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_PRESIDENT_AND_THREE_BOARD_MEMBERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.president_and_three_board_members.v1"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("president"),
            role="président", signing="Einzelunterschrift",
            extra={"action": "appointed_president", "signing_continues": True},
        ))
        for index in (1, 2):
            place = match.group(f"place{index}")
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=place, role="membre du conseil d'administration",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed", "heimat": place.strip()},
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("name3"),
            place=match.group("place3"), role="membre du conseil d'administration",
            signing="Kollektivunterschrift zu zweien",
            extra={"action": "appointed", "heimat": match.group("origin3").strip()},
        ))

    match = _FR_BOARD_MEMBER_COUNTRY.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.board_member_country.v1",
            match.group("name"), place=match.group("place"), role="membre du conseil",
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "appointed", "heimat": match.group("origin").strip(),
                "country": match.group("country").upper(),
            },
        ))

    match = _FR_CORRECTED_PRIVILEGED_SHARES_TO_ORGANIZATION.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.corrected_privileged_shares_to_organization.v1"
        count = _count(match.group("count"))
        reference = {
            "correction": True, "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_ref": match.group("notice_ref"),
            "previously_published_counterparty": match.group("previous_buyer").strip(),
            "previously_published_counterparty_uid": match.group("previous_uid"),
        }
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller"), role="gérant",
                extra={
                    **reference, "action": "shares_transferred",
                    "counterparty": match.group("buyer").strip(),
                    "counterparty_uid": match.group("buyer_uid"),
                    "shares_transferred": count,
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                    "voting_rights_privileged": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"),
                place=match.group("place"), uid=match.group("buyer_uid"), role="associée",
                extra={
                    **reference, "uid": match.group("buyer_uid"),
                    "action": "shares_received", "counterparty": match.group("seller").strip(),
                    "new_associate": True, "shares_received": count, "shares_count": count,
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                    "voting_rights_privileged": True,
                },
            ),
        ])

    match = _FR_PRESIDENT_AND_PREVIOUS_PRESIDENT.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.president_and_previous_president.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"), role="présidente",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed_president", "signing_continues": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                role="membre du conseil d'administration",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "role_changed", "previous_role": "président",
                    "signing_continues": True,
                },
            ),
        ])

    match = _FR_FOUNDATION_MEMBER_WITH_ANOTHER_MEMBER.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.foundation_member_with_another_member.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil de fondation",
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "appointed", "heimat": match.group("origin").strip(),
                "required_with": "un autre membre du conseil de fondation",
            },
        ))

    match = _FR_SUPERVISORY_AUDIT_WAIVER_MENTION_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "audit_requirement_changed",
            "fr.text.supervisory_audit_waiver_mention_removed.v1",
            {
                "kind": "limited_audit_waiver", "action": "revoked",
                "waiver_mention_removed": True,
                "authority": match.group("authority").strip(),
                "decision_date": _iso_date(match.group("date")),
            },
        ))

    match = _FR_TWO_ASSOCIATES_TRANSFER_TO_NEW_MANAGER.search(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        remaining = _count(match.group("remaining"))
        if (
            transferred % 2 == 0
            and match.group("nominal") == match.group("buyer_nominal")
            and match.group("nominal") == match.group("remaining_nominal")
            and transferred == _count(match.group("buyer_count"))
        ):
            consume(match)
            rule_id = "fr.persons.two_associates_transfer_to_new_manager.v1"
            per_seller = transferred // 2
            sellers = [match.group("seller1").strip(), match.group("seller2").strip()]
            for seller in sellers:
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé",
                    extra={
                        "action": "shares_transferred", "counterparty": match.group("buyer").strip(),
                        "previous_shares_count": remaining + per_seller,
                        "shares_transferred": per_seller, "shares_count": remaining,
                        "share_nominal": match.group("nominal"), "currency": "CHF",
                    },
                ))
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"),
                place=match.group("place"), role="associé-gérant",
                signing="Einzelunterschrift",
                extra={
                    "action": "appointed_manager_and_shares_received",
                    "counterparties": sellers, "heimat": match.group("origin").strip(),
                    "new_associate": True, "shares_received": transferred,
                    "shares_count": transferred, "share_nominal": match.group("buyer_nominal"),
                    "currency": "CHF",
                },
            ))

    match = _DE_NOMINAL_REDUCTION_TO_COVER_DEFICIT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.nominal_reduction_to_cover_deficit.v1",
            {
                "kind": "share_capital_reduction", "action": "reduced",
                "date": _iso_date(match.group("date")),
                "shares_count": _count(match.group("count")),
                "share_kind": match.group("share_kind"),
                "from_share_nominal": match.group("from_nominal"),
                "to_share_nominal": match.group("to_nominal"),
                "currency": "CHF", "reason": "cover_deficit", "correction": True,
            },
        ))

    match = _FR_TWO_GENERAL_PARTNERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_general_partners_collective.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role="associé indéfiniment responsable",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed", "new_partner": True,
                    "heimat": match.group(f"origin{index}").strip(),
                },
            ))

    match = _FR_TWO_FOUNDATION_MEMBERS_WITHOUT_SIGNATURE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_foundation_members_without_signature.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group("place"), role="membre du conseil de fondation",
                signing="ohne Zeichnungsberechtigung",
                extra={
                    "action": "appointed", "without_signature": True,
                    "heimat": match.group(f"origin{index}").strip(),
                },
            ))

    match = _FR_MANAGER_ERRONEOUS_REMOVAL_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.manager_erroneous_removal_corrected.v1",
            match.group("name"), place=match.group("place"), role=match.group("role"),
            signing="Einzelunterschrift",
            extra={
                "action": "erroneous_removal_corrected", "remains_registered": True,
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "heimat": match.group("origin").strip(),
                "country": match.group("country").upper(),
            },
        ))

    match = _FR_OWNER_BANKRUPTCY_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.owner_bankruptcy_revoked.v1",
            {
                "kind": "bankruptcy_revoked", "scope": "owner",
                "action": "judgment_set_aside", "registry_entry_restored": True,
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "previous_notice_number": match.group("notice_number"),
                "previous_notice_date": _iso_date(match.group("notice_date")),
                "previous_notice_id": match.group("notice_id").replace("'", ""),
            },
        ))

    match = _FR_ANCILLARY_OBLIGATIONS_MENTION_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.ancillary_obligations_mention_removed.v1",
            {
                "kind": "ancillary_obligations", "action": "removed",
                "mention_removed": True,
                "rights_removed": ["preference", "preemption", "emption"],
            },
        ))

    match = _IT_BRANCH_IDENTIFIER_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "it.text.branch_identifier_changed.v1",
            {
                "action": "identifier_replaced", "place": match.group("place").strip(),
                "branch_uid": match.group("uid"),
                "previous_branch_id": match.group("previous_id"),
            },
        ))

    match = _DE_PARTNERSHIP_TO_CORPORATION_TRANSFORMATION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "legal_form_changed",
            "de.text.partnership_to_corporation_transformation.v1",
            {
                "action": "transformed", "from_legal_form": "Kollektivgesellschaft",
                "to_legal_form": "Aktiengesellschaft",
                "transformation_plan_date": _iso_date(match.group("plan_date")),
                "balance_sheet_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "currency": "CHF", "shares_issued": _count(match.group("shares")),
                "share_kind": "Aktien", "share_nominal": match.group("share_nominal"),
                "correction": True,
            },
        ))

    match = _FR_REGISTERED_TO_BEARER_SHARES_SUPPLEMENT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.registered_to_bearer_shares_supplement.v1",
            {
                "kind": "share_class_conversion", "action": "converted",
                "supplement": True, "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"), "currency": "CHF",
                "from_share_structure": {
                    "count": _count(match.group("from_count")),
                    "nominal": match.group("from_nominal"),
                    "kind": "actions nominatives", "transfer_restricted": True,
                },
                "to_share_structure": {
                    "count": _count(match.group("to_count")),
                    "nominal": match.group("to_nominal"), "kind": "actions au porteur",
                },
                "entire_share_capital": True,
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
