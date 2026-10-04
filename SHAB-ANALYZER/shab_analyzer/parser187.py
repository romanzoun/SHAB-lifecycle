from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_AUDITOR_RENAMED = re.compile(
    r"^L['’]organe de révision\s+(?P<previous_name>.+?)\s+a modifié sa raison "
    r"de commerce en\s+(?P<name>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_MANAGER_INDIVIDUAL_FRAGMENT = re.compile(
    r"^Nouveau gérant avec signature individuelle\s*:\s*(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s*"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_INCOMING_SPIN_OFF_TWO_RECIPIENTS = re.compile(
    r"^Aufspaltung:\s*Die Gesellschaft und die\s+(?P<co_recipient>.+?),\s*"
    r"in\s+(?P<co_recipient_place>[^()]+?)\s*"
    r"\((?P<co_recipient_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+übernehmen von der\s+"
    r"(?P<source>.+?),\s*in\s+(?P<source_place>[^()]+?)\s*"
    r"\((?P<source_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+je einen Teil des "
    r"Vermögens\.\s*Die Gesellschaft übernimmt dabei gemäss Spaltungsvertrag "
    r"vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\.\s*Da dieselben Aktionäre sämtliche Aktien der "
    r"an der Aufspaltung beteiligten Gesellschaften halten,\s*findet weder eine "
    r"Kapitalerhöhung noch eine Aktienzuteilung statt\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_SHARE_TRANSFER_WITH_RESTRICTED_SIGNING_FRAGMENT = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s*"
    r"(?P<place>[^,.;]+),\s*nouvel associé avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"gérant avec signature collective à deux,\s*toutefois avec un gérant\.\s*"
    r"(?P=seller)\s+reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_FOUR_CONTINUE_COLLECTIVE = re.compile(
    r"^Administration:\s*(?P<name1>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<previous_role1>[^,.;]+),\s*nommé\s+(?P<role1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*nommé\s+(?P<role2>[^,.;]+),\s*"
    r"(?P<name3>[^,.;]+),\s*jusqu['’]ici\s+(?P<previous_role3>[^,.;]+),\s*et\s*"
    r"(?P<name4>[^,.;]+),\s*lesquels continuent de signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_APPOINTMENTS_CANCELLED = re.compile(
    r"^L['’]inscription\s+(?:n[o°]|No)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est annulée en ce sens que\s+"
    r"(?P<name1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+)\s+ne sont pas nommé(?:s)?\s+"
    r"fondés de pouvoirs\.?$",
    re.I | re.UNICODE,
)
_DE_NAMED_ASSET_TRANSFER_WITH_INVENTORY = re.compile(
    r"^Vermögensübertragung:\s*(?P<transferor>.+?)\s+überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Inventar per\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_COMMITTEE_ROLE_CHANGES_AND_TWO_MEMBERS_FRAGMENT = re.compile(
    r"^(?P<name1>[^,.;]+),\s*jusqu['’]ici\s+(?P<previous_role1>[^,.;]+),\s*"
    r"nommée\s+(?P<role1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*jusqu['’]ici\s+(?P<previous_role2>[^,.;]+),\s*"
    r"nommée\s+(?P<role2>[^,.;]+),\s*"
    r"(?P<name3>[^,.;]+),\s*jusqu['’]ici\s+(?P<previous_role3>[^,.;]+),\s*"
    r"nommé\s+(?P<role3>[^,.;]+),\s*"
    r"(?P<name4>[^,.;]+),\s*nommé\s+(?P<role4>[^,.;]+),\s*et\s*"
    r"(?P<name5>[^,.;]+),\s*jusqu['’]ici\s+(?P<previous_role5>[^,.;]+),\s*"
    r"membres du comité,\s*continuent de signer collectivement à deux\.\s*"
    r"(?P<name6>[^,.;]+),\s*de\s+(?P<origin6>[^,.;]+),\s*à\s+"
    r"(?P<place6>[^,.;]+),\s*et\s*(?P<name7>[^,.;]+),\s*de et à\s+"
    r"(?P<place7>[^,.;]+),\s*sont membres du comité avec signature collective "
    r"à deux\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_SURNAME_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le patronyme exact "
    r"d['’]une administratrice est\s+(?P<name>.+?)\s*\(et non\s+"
    r"(?P<previous_name>.+?)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSET_TRANSFER_CLAIM_CONSIDERATION = re.compile(
    r'^Transfert de patrimoine:\s*selon contrat du\s+'
    r'(?P<agreement_date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré des '
    r'actifs pour CHF\s+(?P<assets>[\d\'.]+)\s+et des passifs envers les tiers '
    r'pour CHF\s+(?P<liabilities>[\d\'.]+)\s+à la société\s+["“]'
    r'(?P<recipient>.+?)["”]\s+à\s+(?P<place>[^()]+?)\s*'
    r'\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*Contre-prestation:\s*créance '
    r'de CHF\s+(?P<consideration>[\d\'.]+)\s+à l[\'’]encontre de la société\s+'
    r'["“](?P=recipient)["”]\s+à\s+(?P=place)\s*\((?P=uid)\)\.?$',
    re.I | re.UNICODE,
)
_DE_CONDITIONAL_AND_AUTHORIZED_CAPITAL_HISTORY = re.compile(
    r"^Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<conditional_date>\d{2}\.\d{2}\.\d{4})\s+die Statutenbestimmung über "
    r"die bedingte Kapitalerhöhung vom\s+"
    r"(?P<conditional_introduction_date>\d{2}\.\d{2}\.\d{4})\s+gemäss näherer "
    r"Umschreibung in den Statuten angepasst\.\s*\[bisher:\s*Die "
    r"Generalversammlung hat mit Beschluss vom\s+"
    r"(?P=conditional_introduction_date)\s+eine bedingte Kapitalerhöhung gemäss "
    r"näherer Umschreibung in den Statuten eingeführt\.\]\.\s*Die "
    r"Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<authorized_date>\d{2}\.\d{2}\.\d{4})\s+den Beschluss über die "
    r"Ermächtigung einer genehmigten Kapitalerhöhung vom\s+"
    r"(?P<authorized_previous_date>\d{2}\.\d{2}\.\d{4})\s+gemäss näherer "
    r"Umschreibung in den Statuten angepasst\.\s*\[bisher:\s*Die "
    r"Generalversammlung hat mit Beschluss vom\s+(?P=authorized_previous_date)\s+"
    r"den Beschluss über die Ermächtigung einer genehmigten Kapitalerhöhung vom\s+"
    r"(?P<authorized_introduction_date>\d{2}\.\d{2}\.\d{4})\s+gemäss näherer "
    r"Umschreibung in den Statuten angepasst\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_ROLES_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<president>[^,.;]+)\s+est élu gérant président et\s+"
    r"(?P<manager>[^,.;]+)\s+est gérant\s*\(et non gérant président comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_THREE_SIGNING_FRAGMENT = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*président,\s*"
    r"(?P<secretary>[^,.;]+),\s*nommée secrétaire et\s*"
    r"(?P<member>[^,.;]+),\s*de et à\s+(?P<place>[^,.;]+),\s*tous trois avec "
    r"signature collective à deux\s*;\s*"
    r"les pouvoirs de\s+(?P=president)\s+sont modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_FR_SUPPLEMENT_AUDIT_WAIVER_HEADER = re.compile(
    r"^Complément:\s*l['’]inscription no\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*page\s+"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée en ce sens que\.?$",
    re.I | re.UNICODE,
)
_FR_SUPPLEMENT_ADMINISTRATOR_PRESIDENT = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(publication FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+page\s+"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée en ce sens que "
    r"l['’]administrateur\s+(?P<name>[^,.;]+)\s+est également président\.?$",
    re.I | re.UNICODE,
)
_FR_NOMINATIVE_SHARES_RESTRICTED = re.compile(
    r"^Les\s+(?P<shares>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+sont désormais restreintes quant à la "
    r"transmissibilité selon les statuts\.?$",
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


def extract_parser187_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 187."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_AUDITOR_RENAMED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.auditor_renamed.v1", match.group("name"),
            role="organe de révision", extra={
                "action": "name_changed",
                "previous_name": match.group("previous_name").strip(),
            },
        )], ""

    match = _FR_NEW_MANAGER_INDIVIDUAL_FRAGMENT.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.new_manager_individual_fragment.v1",
            match.group("name"), place=match.group("place"), role="gérant",
            signing="Einzelunterschrift", extra={
                "action": "appointed", "origin": match.group("origin").strip(),
            },
        )], ""

    match = _DE_INCOMING_SPIN_OFF_TWO_RECIPIENTS.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.incoming_spin_off_two_recipients.v1", {
                "kind": "spin_off_acquisition", "scope": "part_of_assets_and_liabilities",
                "date": _iso_date(match.group("date")), "document": "spaltungsvertrag",
                "source": match.group("source").strip(),
                "source_place": match.group("source_place").strip(),
                "source_uid": match.group("source_uid"),
                "co_recipient": match.group("co_recipient").strip(),
                "co_recipient_place": match.group("co_recipient_place").strip(),
                "co_recipient_uid": match.group("co_recipient_uid"),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "currency": "CHF", "same_shareholders": True,
                "capital_increase": False, "share_allocation": False,
            },
        )], ""

    match = _FR_MANAGER_SHARE_TRANSFER_WITH_RESTRICTED_SIGNING_FRAGMENT.fullmatch(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        before = _count(match.group("before"))
        buyer_count = _count(match.group("buyer_count"))
        remaining = _count(match.group("remaining"))
        if (
            before - transferred == remaining
            and transferred == buyer_count
            and len({
                match.group("nominal"), match.group("buyer_nominal"),
                match.group("remaining_nominal"),
            }) == 1
        ):
            rule_id = "fr.persons.manager_share_transfer_restricted_signing_fragment.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé-gérant", extra={
                        "action": "shares_transferred", "counterparty": buyer,
                        "shares_before": before, "shares_transferred": transferred,
                        "shares_count": remaining, "share_nominal": match.group("nominal"),
                        "currency": "CHF",
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé-gérant", signing="Kollektivunterschrift zu zweien",
                    extra={
                        "action": "appointed_and_shares_received", "new_associate": True,
                        "origin": match.group("origin").strip(), "counterparty": seller,
                        "shares_received": transferred, "shares_count": buyer_count,
                        "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                        "signing_restriction": "with_a_manager",
                    },
                ),
            ], ""

    match = _FR_ADMINISTRATION_FOUR_CONTINUE_COLLECTIVE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administration_four_continue_collective.v1"
        people = (
            ("name1", match.group("role1"), match.group("previous_role1"), "role_changed"),
            ("name2", match.group("role2"), None, "appointed_role"),
            ("name3", "administrateur", match.group("previous_role3"), "role_changed"),
            ("name4", "administrateur", None, "continued"),
        )
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(name_key), role=role.strip(),
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": action, "continued_signing": True,
                    **({"previous_role": previous.strip()} if previous else {}),
                },
            )
            for name_key, role, previous, action in people
        ], ""

    match = _FR_APPOINTMENTS_CANCELLED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.authorized_representative_appointments_cancelled.v1"
        common = {
            "action": "appointment_cancelled", "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group(group),
                role="fondé de pouvoirs", extra=common,
            )
            for group in ("name1", "name2")
        ], ""

    match = _DE_NAMED_ASSET_TRANSFER_WITH_INVENTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.named_asset_transfer_with_inventory.v1", {
                "kind": "asset_transfer", "transferor": match.group("transferor").strip(),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "inventory_date": _iso_date(match.group("inventory_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"),
                "consideration_kind": "cash", "currency": "CHF",
            },
        )], ""

    match = _FR_COMMITTEE_ROLE_CHANGES_AND_TWO_MEMBERS_FRAGMENT.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.committee_role_changes_and_two_members.v1"
        events = []
        for index in range(1, 6):
            role = match.group(f"role{index}") if index <= 4 else "membre du comité"
            previous = match.groupdict().get(f"previous_role{index}")
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role=role.strip(), signing="Kollektivunterschrift zu zweien", extra={
                    "action": "role_changed" if previous else "appointed_role",
                    "continued_signing": True,
                    **({"previous_role": previous.strip()} if previous else {}),
                },
            ))
        for index, origin in ((6, match.group("origin6")), (7, match.group("place7"))):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="membre du comité",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": origin.strip(),
                },
            ))
        return events, ""

    match = _FR_ADMINISTRATOR_SURNAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_surname_corrected.v1",
            match.group("name"), role="administratrice", extra={
                "action": "name_corrected", "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_ASSET_TRANSFER_CLAIM_CONSIDERATION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.asset_transfer_claim_consideration.v1", {
                "kind": "asset_transfer",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"),
                "consideration_kind": "claim_against_recipient", "currency": "CHF",
            },
        )], ""

    match = _DE_CONDITIONAL_AND_AUTHORIZED_CAPITAL_HISTORY.fullmatch(leftover)
    if match and match.group("conditional_date") == match.group("authorized_date"):
        rule_id = "de.text.conditional_and_authorized_capital_history.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "conditional_capital_clause", "action": "modified",
                    "decision_date": _iso_date(match.group("conditional_date")),
                    "introduction_date": _iso_date(match.group("conditional_introduction_date")),
                    "details_in_statutes": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause", "action": "modified",
                    "decision_date": _iso_date(match.group("authorized_date")),
                    "previous_decision_date": _iso_date(match.group("authorized_previous_date")),
                    "introduction_date": _iso_date(match.group("authorized_introduction_date")),
                    "details_in_statutes": True,
                },
            ),
        ], ""

    match = _FR_MANAGER_ROLES_CORRECTED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.manager_roles_corrected.v1"
        common = {
            "action": "role_corrected", "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_ref": match.group("notice_ref"),
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="gérant président", extra={**common, "previous_role": "gérant"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("manager"), role="gérant",
                extra={**common, "previous_role": "gérant président"},
            ),
        ], ""

    match = _FR_ADMINISTRATION_THREE_SIGNING_FRAGMENT.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administration_three_collective_fragment.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("president"),
                role="président", signing="Kollektivunterschrift zu zweien",
                extra={"action": "signing_changed"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("secretary"), role="secrétaire",
                signing="Kollektivunterschrift zu zweien", extra={"action": "appointed_role"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                place=match.group("place"), role="administrateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group("place").strip(),
                },
            ),
        ], ""

    match = _FR_SUPPLEMENT_AUDIT_WAIVER_HEADER.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.supplement_audit_waiver_header.v1", {
                "kind": "audit_waiver", "action": "supplemented",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_SUPPLEMENT_ADMINISTRATOR_PRESIDENT.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.supplement_administrator_president.v1",
            match.group("name"), role="administrateur, président", extra={
                "action": "role_supplemented", "previous_role": "administrateur",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_NOMINATIVE_SHARES_RESTRICTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.nominative_shares_restricted.v1", {
                "kind": "share_transfer_restriction", "action": "introduced",
                "share_kind": "actions nominatives", "shares_count": _count(match.group("shares")),
                "nominal": match.group("nominal"), "currency": "CHF", "basis": "statutes",
            },
        )], ""

    return [], text
