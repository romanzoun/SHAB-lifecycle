from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_FR_FOUNDATION_ORGANIZATION_MENTION_REMOVED_RESIDUE = re.compile(
    r"^de la fondation,\s*celle-ci n['’]étant plus obligatoire\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_DIRECTORS_APPOINTED_ADMINISTRATORS = re.compile(
    r"^(?P<name1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+),\s*jusqu['’]ici "
    r"directeurs,\s*nommés administrateurs,\s*continuent à signer "
    r"collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_INDIVIDUAL_SIGNING = re.compile(
    r"^Signature individuelle est conférée à\s+(?P<name1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*(?P<role1>présidente),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*toutes deux "
    r"de\s+(?P<origin>[^,.;]+),\s*(?P<role2>gérantes)\.?$",
    re.I | re.UNICODE,
)
_FR_POSTAL_ROUTING_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:no|n°|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que "
    r"le numéro postal d['’]acheminement est\s+(?P<postal_code>\d{4})\s+"
    r"(?P<place>.+?)\s*\(et non pas\s+(?P<previous_postal_code>\d{4})\s+"
    r"(?P<previous_place>.+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_ORIGIN_CHANGED_APPOINTED_LIQUIDATOR = re.compile(
    r"^(?P<name>[^,.;]+),\s*qui est maintenant de\s+(?P<origin>[^,.;]+),\s*"
    r"est nommée liquidatrice(?:\s+avec signature individuelle)?\.?$",
    re.I | re.UNICODE,
)
_FR_PARTNERS_DISSOLVED_FIVE_LIQUIDATORS = re.compile(
    r"^Selon décision des associés du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"la société est dissoute\.\s*Liquidateurs:\s*les associés\s+"
    r"(?P<names>.+?),\s*lesquels continuent à signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_SIGNING_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:No|no|n°|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que le "
    r"membre du conseil de fondation\s+(?P<name>[^()]+?)\s+signe "
    r"individuellement\s*\(et non pas collectivement à deux\)\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_COMPANY_REINSTATED_SOURCE_TYPO = re.compile(
    r"^Diese Gesellschaft,\s*welche am\s+(?P<deleted_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"infolge Konkurses im Sinne von\s+(?P<legal_basis>Art\.\s*159 HRegV)\s+"
    r"gelöscht wurde,\s*wird gemäss Entscheid des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wieder als durch Konkurs "
    r"aufgelöst in das Handelsregister eingetragen\.\s*Datum der "
    r"(?P<label>Konkuseröffnung):\s*"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<bankruptcy_time>\d{1,2}[.:]\d{2})\s+Uhr\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_ALL_INTERESTS_OWNED = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di\s+(?P<absorbed_name>.+?),\s*"
    r"in\s+(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"secondo il contratto di fusione del\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+e bilancio al\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta attivi per\s+"
    r"(?P<currency>[A-Z]{3})\s+(?P<assets>[\d'.]+)\s+e passivi verso terzi per\s+"
    r"(?P=currency)\s+(?P<liabilities>[\d'.]+)\.\s*La società assuntrice "
    r"detiene tutte le quote della società trasferente,\s*per cui la fusione "
    r"avviene senza aumento di capitale e senza attribuzione di azioni\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDATION_AUDIT_EXEMPTION_REVOKED = re.compile(
    r"^Mit Verfügung vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat die "
    r"Aufsichtsbehörde ihre Verfügung vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4}),\s*mit welcher die "
    r"Stiftung von der Pflicht zur Bezeichnung einer Revisionsstelle befreit "
    r"worden ist,\s*widerrufen\.\s*\[bisher:\s*Die Stiftung wurde mit "
    r"Verfügung vom\s+(?P<previous_text_date>\d{2}\.\d{2}\.\d{4})\s+der "
    r"Aufsichtsbehörde von der Pflicht befreit,\s*eine Revisionsstelle zu "
    r"bezeichnen\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_PRESIDENT_AND_TWO_MEMBERS = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé président,\s*lequel "
    r"continue à signer individuellement,\s*(?P<member1>[^,.;]+),\s*de et à\s*"
    r"(?P<place1>[^,.;]+),\s*et\s*(?P<member2>[^,.;]+),\s*d['’]"
    r"(?P<origin2>[^,.;]+),\s*à\s*(?P<place2>[^,.;]+),\s*avec signature "
    r"collective à deux\.?$",
    re.I | re.UNICODE,
)
_FR_LIMITED_AUDIT_WAIVED = re.compile(
    r"^Selon déclaration du\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s*,\s*"
    r"(?:il\s+)?est renoncé à un contrôle restreint\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_ASSOCIATES_TRANSFER_TO_ONE = re.compile(
    r"^(?P<seller1>[^,.;]+),\s*(?P<seller2>[^,.;]+)\s+et\s+"
    r"(?P<seller3>[^,.;]+)\s+cèdent chacun\s+(?P<transferred>[\d']+)\s+de "
    r"leur\s+(?P<before>[\d']+)\s+parts de\s+(?P<currency>[A-Z]{3})\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de\s+(?P=currency)\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*avec signature collective à deux\.\s*"
    r"(?P<statement1>[^,.;]+),\s*"
    r"(?P<statement2>[^,.;]+)\s+et\s+(?P<statement3>[^,.;]+)\s+restent "
    r"titulaires de\s+(?P<remaining>[\d']+)\s+parts de\s+(?P=currency)\s+"
    r"(?P<remaining_nominal>[\d'.]+)\s+chacun\.?$",
    re.I | re.UNICODE,
)
_FR_DELEGATED_ADMINISTRATOR_NOW_PROXY = re.compile(
    r"^(?P<name>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<previous_role>administrateur délégué),\s*signe désormais par "
    r"procuration collective à deux;\s*ses pouvoirs sont modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_CAPITAL_STRUCTURE_RESIDUE = re.compile(
    r"^Les\s+(?P<count>[\d']+)\s+actions de\s+(?P<currency>[A-Z]{3})\s+"
    r"(?P<nominal>[\d'.]+)\s+sont désormais liées selon statuts\.\s*"
    r"Capital-actions:\s*"
    r"(?P=currency)\s+(?P<capital>[\d'.]+),\s*entièrement libéré,\s*divisé en\s+"
    r"(?P<capital_count>[\d']+)\s+actions de\s+(?P=currency)\s+"
    r"(?P<capital_nominal>[\d'.]+),\s*nominatives,\s*liées selon statuts\.?$",
    re.I | re.UNICODE,
)
_DE_UID_ASSIGNMENT_CORRECTED_NOTE = re.compile(
    r"^\[Bei der Sitzverlegung wurde irrtümlicherweise die falsche UID-Nummer\s+"
    r"(?P<previous_uid>CHE-\d{3}\.\d{3}\.\d{3})\s+zugeordnet\.\s*Die "
    r"korrekte UID-Nummer lautet\s+(?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\.\s*"
    r"Der Eintrag wird hiermit berichtigt\.\]\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _money(raw: str) -> Decimal:
    return Decimal(raw.replace("'", ""))


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
        role=role.strip() if role else None,
        signing=signing,
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def _split_french_names(raw: str) -> list[str]:
    return [
        name.strip()
        for name in re.split(r"\s*,\s*|\s+et\s+", raw, flags=re.I | re.UNICODE)
        if name.strip()
    ]


def extract_parser224_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 224."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    if _FR_FOUNDATION_ORGANIZATION_MENTION_REMOVED_RESIDUE.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed",
            "fr.text.foundation_organization_mention_removed_residue.v1", {
                "kind": "foundation_organization",
                "action": "mention_removed",
                "reason": "no_longer_required",
                "source_fragment": True,
            },
        )], ""

    match = _FR_TWO_DIRECTORS_APPOINTED_ADMINISTRATORS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_directors_appointed_administrators.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(name),
                role="administrateur", signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed_administrator",
                    "previous_role": "directeur",
                    "signing_continues": True,
                },
            )
            for name in ("name1", "name2")
        ], ""

    match = _FR_TWO_MANAGERS_INDIVIDUAL_SIGNING.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_managers_individual_signing.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="présidente et gérante",
                signing="Einzelunterschrift", extra={
                    "action": "signing_granted", "origin": match.group("origin").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="gérante",
                signing="Einzelunterschrift", extra={
                    "action": "signing_granted", "origin": match.group("origin").strip(),
                },
            ),
        ], ""

    match = _FR_POSTAL_ROUTING_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.postal_routing_corrected.v1", {
                "kind": "postal_routing", "action": "publication_corrected",
                "postal_code": match.group("postal_code"),
                "place": match.group("place").strip(),
                "previous_postal_code": match.group("previous_postal_code"),
                "previous_place": match.group("previous_place").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_ORIGIN_CHANGED_APPOINTED_LIQUIDATOR.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.origin_changed_appointed_liquidator.v1",
            match.group("name"), role="liquidatrice", extra={
                "action": "origin_changed_and_appointed_liquidator",
                "origin": match.group("origin").strip(),
            }, signing="Einzelunterschrift",
        )], ""

    match = _FR_PARTNERS_DISSOLVED_FIVE_LIQUIDATORS.fullmatch(leftover)
    if match:
        names = _split_french_names(match.group("names"))
        if len(names) >= 2:
            rule_id = "fr.text.partners_dissolved_multiple_liquidators.v1"
            events = [_event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "dissolution", "action": "dissolved",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "decision_maker": "associés",
                },
            )]
            events.extend(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, name,
                    role="associé et liquidateur",
                    signing="Kollektivunterschrift zu zweien", extra={
                        "action": "appointed_liquidator", "signing_continues": True,
                    },
                )
                for name in names
            )
            return events, ""

    match = _FR_FOUNDATION_MEMBER_SIGNING_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed",
            "fr.persons.foundation_member_signing_corrected.v1",
            match.group("name"), role="membre du conseil de fondation",
            signing="Einzelunterschrift", extra={
                "action": "signing_corrected",
                "previous_signing": "Kollektivunterschrift zu zweien",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _DE_BANKRUPTCY_COMPANY_REINSTATED_SOURCE_TYPO.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_company_reinstated_source_typo.v1", {
                "kind": "bankruptcy", "action": "reinstated_as_dissolved",
                "deleted_date": _iso_date(match.group("deleted_date")),
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "bankruptcy_time": match.group("bankruptcy_time").replace(".", ":"),
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "registry_reinstated": True, "dissolved_by_bankruptcy": True,
                "source_typo": match.group("label"),
            },
        )], ""

    match = _IT_MERGER_ALL_INTERESTS_OWNED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "it.text.merger_all_interests_owned.v1", {
                "kind": "absorption", "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("place").strip(),
                "absorbed_uid": match.group("uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party",
                "currency": match.group("currency").upper(),
                "acquirer_owns_all_transferor_interests": True,
                "capital_increase": False, "shares_allocated": False,
            },
        )], ""

    match = _DE_FOUNDATION_AUDIT_EXEMPTION_REVOKED.fullmatch(leftover)
    if match and match.group("previous_decision_date") == match.group("previous_text_date"):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "audit_requirement_changed",
            "de.text.foundation_audit_exemption_revoked.v1", {
                "kind": "auditor_appointment_exemption", "action": "revoked",
                "entity": "foundation",
                "decision_date": _iso_date(match.group("decision_date")),
                "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                "authority": "Aufsichtsbehörde", "auditor_required": True,
            },
        )], ""

    match = _FR_BOARD_PRESIDENT_AND_TWO_MEMBERS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.board_president_and_two_members.v2"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président du conseil d'administration",
                signing="Einzelunterschrift", extra={
                    "action": "appointed_president", "signing_continues": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member1"),
                place=match.group("place1"), role="membre du conseil d'administration",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group("place1").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member2"),
                place=match.group("place2"), role="membre du conseil d'administration",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group("origin2").strip(),
                },
            ),
        ], ""

    match = _FR_LIMITED_AUDIT_WAIVED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "audit_requirement_changed", "fr.text.limited_audit_waived.v1", {
                "kind": "limited_audit_waiver", "action": "declared",
                "declaration_date": _iso_date(match.group("date")),
                "limited_audit_waived": True,
            },
        )], ""

    match = _FR_THREE_ASSOCIATES_TRANSFER_TO_ONE.fullmatch(leftover)
    if match:
        sellers = [match.group(f"seller{index}").strip() for index in (1, 2, 3)]
        statements = [match.group(f"statement{index}").strip() for index in (1, 2, 3)]
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        remaining = _count(match.group("remaining"))
        buyer_count = _count(match.group("buyer_count"))
        if (
            [name.casefold() for name in sellers] == [name.casefold() for name in statements]
            and before - transferred == remaining
            and buyer_count == transferred * len(sellers)
            and len({
                match.group("nominal"),
                match.group("buyer_nominal"),
                match.group("remaining_nominal"),
            }) == 1
        ):
            rule_id = "fr.persons.three_associates_transfer_to_one.v1"
            buyer = match.group("buyer").strip()
            common = {
                "currency": match.group("currency").upper(),
                "share_nominal": match.group("nominal"),
            }
            events = [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé", extra={
                        "action": "shares_transferred", "counterparty": buyer,
                        "shares_before": before, "shares_transferred": transferred,
                        "shares_count": remaining, **common,
                    },
                )
                for seller in sellers
            ]
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé", signing="Kollektivunterschrift zu zweien", extra={
                    "action": "shares_received", "counterparties": sellers,
                    "origin": match.group("origin").strip(), "new_associate": True,
                    "shares_received": buyer_count, "shares_count": buyer_count, **common,
                },
            ))
            return events, ""

    match = _FR_DELEGATED_ADMINISTRATOR_NOW_PROXY.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed",
            "fr.persons.delegated_administrator_now_proxy.v1",
            match.group("name"), signing="Kollektivprokura zu zweien", extra={
                "action": "role_and_signing_changed",
                "previous_role": match.group("previous_role"),
                "powers_modified": True,
            },
        )], ""

    match = _FR_SHARE_CAPITAL_STRUCTURE_RESIDUE.fullmatch(leftover)
    if match:
        count = _count(match.group("count"))
        capital_count = _count(match.group("capital_count"))
        if (
            count == capital_count
            and match.group("nominal") == match.group("capital_nominal")
            and _money(match.group("capital"))
            == capital_count * _money(match.group("capital_nominal"))
        ):
            return [_event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.share_capital_structure_residue.v1", {
                    "kind": "share_structure", "action": "recorded",
                    "currency": match.group("currency").upper(),
                    "capital": match.group("capital"), "fully_paid": True,
                    "shares_count": capital_count,
                    "share_nominal": match.group("capital_nominal"),
                    "share_kind": "registered", "transfer_restricted": True,
                },
            )], ""

    match = _DE_UID_ASSIGNMENT_CORRECTED_NOTE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.uid_assignment_corrected_note.v1", {
                "kind": "company_identifier", "action": "assignment_corrected",
                "context": "seat_transfer",
                "previous_uid": match.group("previous_uid"),
                "uid": match.group("uid"),
            },
        )], ""

    return [], leftover
