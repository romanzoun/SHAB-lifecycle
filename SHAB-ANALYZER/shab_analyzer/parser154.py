from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_BOARD_MEMBER_FOREIGN_ORIGIN = re.compile(
    r"^(?P<name>[^,;]+),\s*(?:de|du|des|de la|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>.+?),\s*est membre du conseil "
    r"d['’]administration\.?$",
    re.I | re.UNICODE,
)
_DE_FULL_ADDRESS_AND_PERSON_CHANGES = re.compile(
    r"^Vollständige Adresse:\s*(?P<street>.+?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<locality>[^.]+)\.\s*"
    r"Eingetragene Person geändert:\s*(?P<previous_name>[^,.;]+),\s*"
    r"korrekterweise\s+(?P<correct_name>[^,.;]+),\s*"
    r"(?P<roles>.+?),\s*(?P<signing>Kollektivunterschrift zu zweien),\s*"
    r"neu\s+(?P<new_signing>Kollektivunterschrift zu zweien),\s*"
    r"in\s+(?P<correct_place>[^;]+);\s*"
    r"(?P<moved_name>[^,.;]+),\s*"
    r"(?P<moved_signing>Kollektivprokura zu zweien),\s*neu in\s*"
    r"(?P<moved_place>[^.]+)\.\s*Neu eingetragene Person:\s*"
    r"(?P<new_name>[^,.;]+),\s*von\s+(?P<new_origin>[^,.;]+),\s*"
    r"in\s+(?P<new_place>[^,.;]+),\s*"
    r"(?P<new_person_signing>Kollektivprokura zu zweien)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_TWO_MANAGERS = re.compile(
    r"^(?P<seller>[^,.;]+)\s+a cédé\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^.]+)\.\s*Associés-gérants:\s*"
    r"(?P=seller),\s*nommé président,\s*pour\s+(?P<seller_count>[\d']+)\s+"
    r"parts de CHF\s+(?P<seller_nominal>[\d'.]+)\s+et\s+(?P=buyer)\s+pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"tous deux\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBER_WITHOUT_SIGNATURE = re.compile(
    r"^(?P<name>[^,.;]+),\s*(?:de|du|des|de la|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>.+?),\s*"
    r"est membre du conseil,\s*sans signature\.?$",
    re.I | re.UNICODE,
)
_FR_NON_EXECUTORY_JUDGMENT_RESTORES_ASSOCIATE_MANAGER = re.compile(
    r"^Le jugement sur la base duquel l['’]inscription n°\s*"
    r"(?P<entry>[\d']+)\s+du\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"a été opérée n['’]étant pas exécutoire,\s*l['’]inscription est rétablie "
    r"dans sa situation antérieure en ce sens que\s+(?P<restored>[^,.;]+),\s*"
    r"de et à\s+(?P<place>.+?)\s+est associée avec\s+"
    r"(?P<count>[\d']+)\s+parts sociales de CHF\s+(?P<nominal>[\d'.]+)\s+"
    r"et gérante\s+L['’]inscription de\s+(?P<removed>[^,.;]+)\s+en tant "
    r"qu['’]associé et gérant est radiée\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_INDIVIDUAL_SIGNING_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que signature "
    r"individuelle est conférée à l['’]associé\s+(?P<name>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_EXISTENCE_SUPPLEMENTED = re.compile(
    r"^Complément:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée en ce sens que la mention de "
    r"l['’]existence d['’]une succursale à\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+est inscrite\.?$",
    re.I | re.UNICODE,
)
_FR_CONDITIONAL_CAPITAL_DECISION_DATE_CORRECTED = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que "
    r"par décision du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s*"
    r"\(et non pas du\s+(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\)\s*"
    r"l['’]assemblée générale a introduit une clause statutaire relative à une "
    r"augmentation conditionnelle du capital-actions\.\s*Pour les détails,\s*"
    r"voir les statuts\.?$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_EXTENDED_SHORT = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat das "
    r"(?P<authority>.+?)\s+die gewährte definitive Nachlassstundung bis und mit "
    r"dem\s+(?P<until>\d{2}\.\d{2}\.\d{4})\s+verlängert\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_ORGANIZATIONS_TRANSFER_TO_MANAGER = re.compile(
    r"^(?P<seller1>.+?)\s*\(N°(?P<registry1>[\d ]+)\),\s*"
    r"(?P<seller2>.+?)\s*\(N°(?P<registry2>[\d ]+)\)\s+et\s+"
    r"(?P<seller3>.+?)\s*\(N°(?P<registry3>[\d ]+)\)\s+ne sont plus associées;\s*"
    r"leurs\s+(?P<transferred>[\d']+)\s+parts respectives de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+ont été cédées au gérant\s+"
    r"(?P<buyer>[^,.;]+),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PRESIDENT_AND_MOVED_DIRECTOR = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé président,\s*et\s*"
    r"(?P<director>[^,.;]+),\s*maintenant domicilié à\s+"
    r"(?P<place>[^,.;]+),\s*jusqu['’]ici directeur,\s*lesquels continuent à "
    r"signer individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_STATUTES_AND_ORGANIZATION_ENTRY_REMOVED = re.compile(
    r"^Statuten neu:\s*(?P<statutes_date>\d{2}\.\d{2}\.\d{4})\s*"
    r"\(Änderung über nicht publikationspflichtige Tatsachen\)\.\s*Der Eintrag "
    r"betreffend die Organisation ist gestützt auf\s+(?P<legal_basis>Art\.\s*95\s*"
    r"Bst\.\s*h\s+HRegV)\s+überflüssig und wird daher gelöscht\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_MISSING_SPACES_NO_CONSIDERATION = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s*und\s+Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s*auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*keine\.?$",
    re.I | re.UNICODE,
)
_FR_SINGLE_SHARE_TRANSFER_NEW_ASSOCIATE = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*de et à\s+(?P<place>[^,.;]+),\s*nouvel associé "
    r"sans signature,\s*avec\s+(?P<buyer_count>[\d']+)\s+part(?:s)? de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+);\s*(?P=seller)\s+reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ORIGIN_CORRECTED_WITH_NOTICE = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+est originaire de\s+(?P<origin>.+?)\s*"
    r"\(et non de\s+(?P<previous_origin>.+?),\s*comme publié\)\.?$",
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


def extract_parser154_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 154."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_BOARD_MEMBER_FOREIGN_ORIGIN.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.board_member_foreign_origin.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil d'administration",
            extra={
                "action": "appointed", "origin": match.group("origin").strip(),
            },
        ))

    match = _DE_FULL_ADDRESS_AND_PERSON_CHANGES.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.full_address_and_person_changes.v1"
        address = (
            f"{match.group('street').strip()}, {match.group('postal_code')} "
            f"{match.group('locality').strip()}"
        )
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", rule_id,
                {
                    "kind": "complete_address", "action": "recorded",
                    "address": address, "street": match.group("street").strip(),
                    "postal_code": match.group("postal_code"),
                    "locality": match.group("locality").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("correct_name"),
                place=match.group("correct_place"), role=match.group("roles").strip(),
                signing=match.group("new_signing"),
                extra={
                    "action": "name_corrected_and_domicile_changed",
                    "previous_name": match.group("previous_name").strip(),
                    "previous_signing": match.group("signing"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("moved_name"),
                place=match.group("moved_place"), signing=match.group("moved_signing"),
                extra={"action": "domicile_changed"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("new_name"),
                place=match.group("new_place"), signing=match.group("new_person_signing"),
                extra={
                    "action": "appointed", "heimat": match.group("new_origin").strip(),
                },
            ),
        ])

    match = _FR_ASSOCIATE_TRANSFER_TWO_MANAGERS.search(leftover)
    if match and (
        match.group("nominal") == match.group("seller_nominal")
        == match.group("buyer_nominal")
        and _count(match.group("transferred")) == _count(match.group("buyer_count"))
    ):
        consume(match)
        rule_id = "fr.persons.associate_transfer_two_managers.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant président",
                extra={
                    **common, "action": "shares_transferred_and_appointed_president",
                    "counterparty": buyer,
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("seller_count")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé-gérant",
                extra={
                    **common, "action": "shares_received_and_appointed_manager",
                    "counterparty": seller,
                    "shares_received": _count(match.group("buyer_count")),
                    "shares_count": _count(match.group("buyer_count")),
                    "heimat": match.group("origin").strip(), "new_associate": True,
                },
            ),
        ])

    match = _FR_BOARD_MEMBER_WITHOUT_SIGNATURE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.board_member_without_signature_short.v1",
            match.group("name"), place=match.group("place"), role="membre du conseil",
            extra={
                "action": "appointed", "origin": match.group("origin").strip(),
                "without_signature": True,
            },
        ))

    match = _FR_NON_EXECUTORY_JUDGMENT_RESTORES_ASSOCIATE_MANAGER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.non_executory_judgment_restores_associate_manager.v1"
        common = {
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "reason": "underlying_judgment_not_enforceable",
        }
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", rule_id,
                {**common, "action": "previous_state_restored"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("restored"),
                place=match.group("place"), role="associée-gérante",
                extra={
                    **common, "action": "restored",
                    "shares_count": _count(match.group("count")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group("removed"),
                role="associé-gérant", extra={**common, "action": "removed"},
            ),
        ])

    match = _FR_ASSOCIATE_INDIVIDUAL_SIGNING_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.associate_individual_signing_corrected.v1",
            match.group("name"), role="associé", signing="Einzelunterschrift",
            extra={
                "action": "signing_granted_by_correction", "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_BRANCH_EXISTENCE_SUPPLEMENTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "fr.text.branch_existence_supplemented.v1",
            {
                "action": "existence_recorded", "place": match.group("place").strip(),
                "uid": match.group("uid"), "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"), "supplement": True,
            },
        ))

    match = _FR_CONDITIONAL_CAPITAL_DECISION_DATE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.conditional_capital_decision_date_corrected.v1",
            {
                "kind": "conditional_share_capital_increase_clause",
                "action": "introduced", "correction": True,
                "decision_date": _iso_date(match.group("decision_date")),
                "previous_incorrect_decision_date": _iso_date(
                    match.group("previous_decision_date")
                ),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "details_in_statutes": True,
            },
        ))

    match = _DE_DEFINITIVE_MORATORIUM_EXTENDED_SHORT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.definitive_moratorium_extended_short_court.v1",
            {
                "kind": "composition_moratorium_extended",
                "moratorium_type": "definitive",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "until": _iso_date(match.group("until")),
            },
        ))

    match = _FR_THREE_ORGANIZATIONS_TRANSFER_TO_MANAGER.search(leftover)
    if match and (
        _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and match.group("nominal") == match.group("buyer_nominal")
    ):
        consume(match)
        rule_id = "fr.persons.three_organizations_transfer_to_manager.v1"
        buyer = match.group("buyer").strip()
        for index in (1, 2, 3):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group(f"seller{index}"), role="associée",
                extra={
                    "action": "removed_after_collective_share_transfer",
                    "foreign_registry_number": match.group(f"registry{index}").strip(),
                    "counterparty": buyer,
                },
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, buyer, role="associé-gérant",
            extra={
                "action": "shares_received", "new_associate": True,
                "shares_received": _count(match.group("buyer_count")),
                "shares_count": _count(match.group("buyer_count")),
                "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                "counterparties": [
                    match.group(f"seller{index}").strip() for index in (1, 2, 3)
                ],
            },
        ))

    match = _FR_ADMINISTRATION_PRESIDENT_AND_MOVED_DIRECTOR.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_president_and_moved_director.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président", signing="Einzelunterschrift",
                extra={"action": "appointed_president", "signing_continues": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("director"),
                place=match.group("place"), role="administrateur",
                signing="Einzelunterschrift",
                extra={
                    "action": "role_and_domicile_changed", "previous_role": "directeur",
                    "domicile_changed": True, "signing_continues": True,
                },
            ),
        ])

    match = _DE_STATUTES_AND_ORGANIZATION_ENTRY_REMOVED.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.statutes_and_organization_entry_removed.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id,
                {
                    "action": "changed",
                    "date": _iso_date(match.group("statutes_date")),
                    "publication_required_facts_changed": False,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id,
                {
                    "action": "entry_removed", "kind": "organization_entry",
                    "reason": "obsolete", "legal_basis": re.sub(
                        r"\s+", " ", match.group("legal_basis").strip()
                    ),
                },
            ),
        ])

    match = _DE_ASSET_TRANSFER_MISSING_SPACES_NO_CONSIDERATION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_missing_spaces_no_consideration.v1",
            {
                "date": _iso_date(match.group("date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "currency": "CHF", "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"), "consideration": "keine",
                "gratuitous": True, "source_spacing_malformed": True,
            },
        ))

    match = _FR_SINGLE_SHARE_TRANSFER_NEW_ASSOCIATE.search(leftover)
    if match and (
        _count(match.group("before"))
        == _count(match.group("remaining")) + _count(match.group("transferred"))
        and _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and len({
            match.group("nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }) == 1
    ):
        consume(match)
        rule_id = "fr.persons.single_share_transfer_new_associate.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé",
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
                role="associé",
                extra={
                    **common, "action": "shares_received", "counterparty": seller,
                    "shares_received": _count(match.group("buyer_count")),
                    "shares_count": _count(match.group("buyer_count")),
                    "heimat": match.group("place").strip(), "new_associate": True,
                    "without_signature": True,
                },
            ),
        ])

    match = _FR_ORIGIN_CORRECTED_WITH_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.origin_corrected_with_notice.v1",
            match.group("name"),
            extra={
                "action": "origin_corrected", "heimat": match.group("origin").strip(),
                "previous_origin": match.group("previous_origin").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    return events, re.sub(r"\s+", " ", leftover).strip(" .,;")
