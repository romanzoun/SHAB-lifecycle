from __future__ import annotations

import re
from decimal import Decimal

from .keys import person_key
from .models import Event


_FR_MANAGER_RECORDED = re.compile(
    r"^(?P<name>[^,.;]+),\s*(?:(?:du|de la|des|de)\s+|d['’])"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+)\s+est\s+"
    r"(?P<role>gérant(?:e)?)\.?$",
    re.I | re.UNICODE,
)
_FR_BANK_OFFICER_PROMOTIONS = re.compile(
    r"^(?P<directors>.+?),\s*jusqu['’]ici directeurs adjoints,\s*nommés "
    r"directeurs,\s*continuent à signer collectivement à deux,\s*avec limitation "
    r"au siège principal\.\s*(?P<deputy_directors>.+?),\s*jusqu['’]ici "
    r"sous-directeurs,\s*nommés directeurs adjoints,\s*continuent à signer "
    r"collectivement à deux,\s*avec limitation au siège principal\.\s*"
    r"Signature collective à deux a été conférée à (?P<signatory>[^,.;]+);\s*"
    r"sa procuration est radiée\.\s*Signature collective à deux limitée à "
    r"l['’]établissement principal a été conférée à (?P<subdirectors>.+?),\s*"
    r"nommés sous-directeurs;\s*leur procuration est radiée\.?$",
    re.I | re.UNICODE,
)
_DE_ASSOCIATION_DISSOLVED_BY_LAW = re.compile(
    r"^Name neu:\s*(?P<name>.+?)\.\s*Der Verein ist gemäss\s+"
    r"(?P<legal_basis>Art\.\s*77 ZGB)\s+von Gesetzes wegen aufgelöst,\s*"
    r"weil der Vorstand nicht mehr statutengemäss bestellt werden kann\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_TO_NEW_CORPORATE_ASSOCIATE = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvelle associée avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*(?P=seller)\s+reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+part(?:s)? de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_SIGNATORIES_NOT_WITH_EACH_OTHER = re.compile(
    r"^Signature collective à deux,\s*toutefois pas entre eux,\s*est conférée à\s+"
    r"(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_COOPERATIVE_NOMINAL_REDUCTION_WITH_HISTORY = re.compile(
    r"^\[bisher:\s*Fr\.\s*(?P<historical>[\d']+)\.--\]\.\s*"
    r"Mit Beschluss der Generalversammlung vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+wird der Nennwert der Anteilscheine "
    r"zu CHF\s+(?P<before>[\d'.]+)\s+im Sinne von\s+"
    r"(?P<legal_basis>Art\.\s*735 i\.V\.m\.\s*Art\.\s*874 Abs\.\s*2 OR)\s+"
    r"auf CHF\s+(?P<after>[\d'.]+)\s+herabgesetzt\.?$",
    re.I | re.UNICODE,
)
_FR_SINGLE_SHARE_TRANSFER_TO_NEW_UNSIGNED_ASSOCIATE = re.compile(
    r"^(?P<seller>[^,.;]+)\s+a cédé une part de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+part(?:s)? de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*lequel n['’]exerce pas la signature "
    r"sociale\.\s*Par conséquent,\s*(?P=seller)\s+est maintenant associé pour\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDER_AUDIT_WAIVER = re.compile(
    r"^Gemäss Erklärung des Gründers vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+untersteht die Gesellschaft keiner "
    r"ordentlichen Revision und verzichtet auf eine eingeschränkte Revision\.?$",
    re.I | re.UNICODE,
)
_DE_TWO_BRANCHES_REMOVED_ONE_ADDED = re.compile(
    r"^\[gestrichen:\s*(?P<removed_place1>[^()\]]+?)\s*"
    r"\((?P<removed_id1>CH-\d{3}\.\d\.\d{3}\.\d{3}-\d)\)\]\.\s*"
    r"\[gestrichen:\s*(?P<removed_place2>[^()\]]+?)\s*"
    r"\((?P<removed_id2>CH-\d{3}\.\d\.\d{3}\.\d{3}-\d)\)\]\.\s*"
    r"(?P<added_place>[^().]+?)\s*"
    r"\((?P<added_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_FR_ORDINARY_PARTICIPATION_CAPITAL_INCREASE = re.compile(
    r"^Augmentation ordinaire du capital-participation de CHF\s+"
    r"(?P<previous_total>[\d'.]+)\s+à CHF\s+(?P<total>[\d'.]+),\s*par "
    r"l['’]émission de\s+(?P<issued>[\d']+)\s+bons de CHF\s+"
    r"(?P<issued_nominal>[\d'.]+),\s*nominatifs,\s*liés selon statuts\.\s*"
    r"Capital-participation:\s*CHF\s+(?P<reported_total>[\d'.]+),\s*"
    r"entièrement libéré,\s*divisé en\s+(?P<count>[\d']+)\s+bons de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*nominatifs,\s*liés selon statuts\.?$",
    re.I | re.UNICODE,
)
_FR_GIVEN_NAME_CORRECTED = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?:Madame\s+)?(?P<family_name>[^,.;]+?)\s+porte le prénom\s+"
    r"(?P<given_name>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FIVE_COUNCIL_MEMBERS = re.compile(
    r"^(?P<name1>[^,.;]+),\s*d['’](?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*(?P<country1>[A-Z]),\s*"
    r"(?P<name2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*(?P<name3>[^,.;]+),\s*du\s+"
    r"(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+),\s*"
    r"(?P<country3>[A-Z]),\s*(?P<name4>[^,.;]+),\s*d['’]"
    r"(?P<origin4>[^,.;]+),\s*à\s+(?P<place4>[^,.;]+),\s*"
    r"(?P<country4>[A-Z]),\s*et\s+(?P<name5>[^,.;]+),\s*de\s+"
    r"(?P<origin5>[^,.;]+),\s*à\s+(?P<place5>[^,.;]+),\s*"
    r"sont membres du conseil\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_ASSOCIATE_WITH_COLLECTIVE_SIGNING = re.compile(
    r"^Nouvelle associée:\s*(?P<name>[^,.;]+),\s*de et à\s+"
    r"(?P<place>[^,.;]+),\s*laquelle signe collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_CORPORATE_ASSOCIATE_RENAMED = re.compile(
    r'^L[\'’]associée\s+["“](?P<previous_name>.+?)["”]\s*'
    r"\((?P<registry_id>[^)]+)\),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]),\s*qui est désormais une\s+"
    r"(?P<legal_form>société par actions simplifiée de droit français),\s*"
    r'porte la nouvelle raison sociale\s+["“](?P<name>.+?)["”]\.?$',
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_RENEWED = re.compile(
    r"^Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+ein genehmigtes Kapital gemäss "
    r"näherer Umschreibung in den Statuten beschlossen\.\s*"
    r"\[bisher:\s*Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+ein genehmigtes Kapital "
    r"gemäss näherer Umschreibung in den Statuten beschlossen\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_UNSIGNED_BOARD_MEMBER_MOVED = re.compile(
    r"^Eingetragene Person geändert:\s*(?P<name>[^,.;]+),\s*"
    r"(?P<role>Verwaltungsratsmitglied),\s*ohne Unterschrift,\s*neu in\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _amount(raw: str) -> Decimal:
    return Decimal(raw.replace("'", ""))


def _names(raw: str) -> list[str]:
    return [name.strip() for name in re.split(r"\s*,\s*|\s+et\s+", raw) if name.strip()]


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
        role=role,
        signing=signing,
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser172_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 172."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_MANAGER_RECORDED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.manager_recorded.v1",
            match.group("name"), place=match.group("place"),
            role=match.group("role").lower(), extra={
                "action": "role_recorded", "origin": match.group("origin").strip(),
            },
        )], ""

    match = _FR_BANK_OFFICER_PROMOTIONS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.bank_officer_promotions_and_signing.v1"
        events: list[Event] = []
        specs = [
            ("directors", "directeur", "directeur adjoint", "head_office"),
            ("deputy_directors", "directeur adjoint", "sous-directeur", "head_office"),
        ]
        for group, role, previous_role, scope in specs:
            for name in _names(match.group(group)):
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, name, role=role,
                    signing="Kollektivunterschrift zu zweien", extra={
                        "action": "promoted", "previous_role": previous_role,
                        "signing_continues": True, "signing_scope": scope,
                    },
                ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", rule_id, match.group("signatory"),
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "collective_signing_granted_and_procuration_revoked",
                "previous_authority": "procuration",
                "previous_authority_revoked": True,
            },
        ))
        for name in _names(match.group("subdirectors")):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, name, role="sous-directeur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_and_procuration_revoked",
                    "previous_authority": "procuration",
                    "previous_authority_revoked": True,
                    "signing_scope": "principal_establishment",
                },
            ))
        return events, ""

    match = _DE_ASSOCIATION_DISSOLVED_BY_LAW.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.association_dissolved_by_law.v1", {
                "kind": "dissolution", "action": "dissolved_by_law",
                "company_name": match.group("name").strip(),
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "reason": "board_cannot_be_appointed_according_to_statutes",
            },
        )], ""

    match = _FR_MANAGER_TRANSFER_TO_NEW_CORPORATE_ASSOCIATE.fullmatch(leftover)
    if match and len({
        match.group("nominal"), match.group("buyer_nominal"),
        match.group("remaining_nominal"),
    }) == 1:
        rule_id = "fr.persons.manager_transfer_to_new_corporate_associate.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant", extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée", uid=match.group("uid"), extra={
                    "action": "appointed_and_shares_received",
                    "counterparty": seller, "uid": match.group("uid"),
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ], ""

    match = _FR_TWO_SIGNATORIES_NOT_WITH_EACH_OTHER.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_signatories_not_with_each_other.v1"
        events = []
        for index, other in ((1, 2), (2, 1)):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "signing_granted",
                    "origin": match.group(f"origin{index}").strip(),
                    "cannot_sign_with": match.group(f"name{other}").strip(),
                },
            ))
        return events, ""

    match = _DE_COOPERATIVE_NOMINAL_REDUCTION_WITH_HISTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed",
            "de.text.cooperative_nominal_reduction_with_history.v1", {
                "kind": "cooperative_share_certificate_nominal_reduction",
                "action": "reduced", "date": _iso_date(match.group("date")),
                "currency": "CHF", "from_nominal": match.group("before"),
                "to_nominal": match.group("after"),
                "previously_reported_nominal": match.group("historical"),
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
            },
        )], ""

    match = _FR_SINGLE_SHARE_TRANSFER_TO_NEW_UNSIGNED_ASSOCIATE.fullmatch(leftover)
    if match and len({
        match.group("nominal"), match.group("buyer_nominal"),
        match.group("remaining_nominal"),
    }) == 1:
        rule_id = "fr.persons.single_share_transfer_to_new_unsigned_associate.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé", extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_transferred": 1,
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé", extra={
                    "action": "appointed_and_shares_received",
                    "counterparty": seller,
                    "origin": match.group("origin").strip(),
                    "shares_received": 1,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                    "without_signing_authority": True,
                },
            ),
        ], ""

    match = _DE_FOUNDER_AUDIT_WAIVER.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "audit_requirement_changed", "de.text.founder_audit_waiver.v1", {
                "kind": "limited_audit_waiver", "action": "declared",
                "date": _iso_date(match.group("date")),
                "limited_audit_waived": True,
                "ordinary_audit_required": False,
                "declarant": "founder",
            },
        )], ""

    match = _DE_TWO_BRANCHES_REMOVED_ONE_ADDED.fullmatch(leftover)
    if match:
        rule_id = "de.text.two_branches_removed_one_added.v1"
        events = []
        for index in (1, 2):
            events.append(_event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id, {
                    "action": "removed",
                    "place": match.group(f"removed_place{index}").strip(),
                    "legacy_registry_id": match.group(f"removed_id{index}"),
                },
            ))
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", rule_id, {
                "action": "added", "place": match.group("added_place").strip(),
                "branch_uid": match.group("added_uid"),
            },
        ))
        return events, ""

    match = _FR_ORDINARY_PARTICIPATION_CAPITAL_INCREASE.fullmatch(leftover)
    if match and (
        _amount(match.group("total")) == _amount(match.group("reported_total"))
        and _amount(match.group("previous_total"))
        + _count(match.group("issued")) * _amount(match.group("issued_nominal"))
        == _amount(match.group("total"))
        and _count(match.group("count")) * _amount(match.group("nominal"))
        == _amount(match.group("total"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.ordinary_participation_capital_increase.v2", {
                "kind": "ordinary_participation_capital_increase",
                "currency": "CHF", "previous_total": match.group("previous_total"),
                "total": match.group("total"),
                "issued_participation_certificates": _count(match.group("issued")),
                "issued_participation_certificate_nominal": match.group("issued_nominal"),
                "participation_certificates_count": _count(match.group("count")),
                "participation_certificate_nominal": match.group("nominal"),
                "registered": True, "transfer_restricted": True, "fully_paid": True,
            },
        )], ""

    match = _FR_GIVEN_NAME_CORRECTED.fullmatch(leftover)
    if match:
        family_name = match.group("family_name").strip()
        given_name = match.group("given_name").strip()
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.given_name_corrected.v1",
            f"{family_name} {given_name}", extra={
                "action": "given_name_corrected", "family_name": family_name,
                "given_name": given_name, "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_FIVE_COUNCIL_MEMBERS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.five_council_members.v1"
        events = []
        for index in range(1, 6):
            extra = {
                "action": "appointed", "origin": match.group(f"origin{index}").strip(),
            }
            country = match.groupdict().get(f"country{index}")
            if country:
                extra["country"] = country
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="membre du conseil",
                extra=extra,
            ))
        return events, ""

    match = _FR_NEW_ASSOCIATE_WITH_COLLECTIVE_SIGNING.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.new_associate_collective_signing.v1",
            match.group("name"), place=match.group("place"), role="associée",
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "appointed", "origin": match.group("place").strip(),
            },
        )], ""

    match = _FR_CORPORATE_ASSOCIATE_RENAMED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "fr.text.corporate_associate_renamed.v1", {
                "kind": "corporate_associate", "action": "name_and_legal_form_changed",
                "name": match.group("name").strip(),
                "previous_name": match.group("previous_name").strip(),
                "registry_id": match.group("registry_id").strip(),
                "place": match.group("place").strip(), "country": match.group("country"),
                "legal_form": match.group("legal_form").strip(),
            },
        )], ""

    match = _DE_AUTHORIZED_CAPITAL_RENEWED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_renewed.v1", {
                "kind": "authorized_capital_clause", "action": "renewed",
                "decision_date": _iso_date(match.group("date")),
                "previous_decision_date": _iso_date(match.group("previous_date")),
                "basis": "statutes",
            },
        )], ""

    match = _DE_UNSIGNED_BOARD_MEMBER_MOVED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.unsigned_board_member_moved.v1",
            match.group("name"), place=match.group("place"),
            role=match.group("role"), extra={
                "action": "domicile_changed", "without_signing_authority": True,
            },
        )], ""

    return [], text
