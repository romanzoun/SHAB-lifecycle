from __future__ import annotations

import re

from .keys import address_key, person_key
from .models import Event


_DE_CHANGED_SHAREHOLDER_AND_NEW_MANAGER = re.compile(
    r"^Eingetragene Personen geändert:\s*(?P<shareholder>[^,.;]+),\s*"
    r"Gesellschafter,\s*(?P<shares>[\d']+) Stammanteile zu CHF\s*"
    r"(?P<nominal>[\d'.]+),\s*Geschäftsführer,\s*Einzelunterschrift,\s*"
    r"neu Gesellschafter,\s*(?P<new_shares>[\d']+) Stammanteile zu CHF\s*"
    r"(?P<new_nominal>[\d'.]+),\s*ohne Unterschrift\.\s*"
    r"Neu eingetragene Person:\s*(?P<manager>[^,.;]+),\s*von\s*"
    r"(?P<origin>[^,.;]+),\s*in\s*(?P<place>[^,.;]+),\s*"
    r"Geschäftsführer,\s*Einzelunterschrift\.?$",
    re.I | re.UNICODE,
)
_FR_SUPPLEMENT_REFERENCE = re.compile(
    r"^Complément:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_LIQUIDATORS_AND_TRANSFER_RESTRICTION_REMOVED = re.compile(
    r"^Liquidateurs:\s*(?P<president>[^,.;]+),\s*président,\s*et\s*"
    r"(?P<member>[^,.;]+),\s*membres du conseil d['’]administration,\s*"
    r"lesquels continuent de signer collectivement à deux\.\s*"
    r"Les restrictions statutaires à la transmissibilité des actions(?:\s+actions)?\s+"
    r"sont levées de par la loi\.?$",
    re.I | re.UNICODE,
)
_FR_PRESIDENT_AND_TREASURER_SIGNING_CHANGED = re.compile(
    r"^(?P<president>[^,.;]+),\s*nommée présidente,\s*signe désormais "
    r"collective à deux,\s*sans autre restriction\.\s*"
    r"(?P<treasurer>[^,.;]+),\s*trésorier,\s*jusqu['’]ici président,\s*"
    r"signe désormais collective à deux,\s*avec la présidente ou le "
    r"vice-président\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_ELECTED_LIQUIDATOR = re.compile(
    r"^(?P<name>[^,.;]+)\s+est élu liquidateur\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_TRANSFER_WITH_LIABILITIES_NO_CONSIDERATION = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré des actifs "
    r"pour CHF\s*(?P<assets>[\d'.]+)\s+et des passifs envers les tiers pour "
    r"CHF\s*(?P<liabilities>[\d'.]+)\s+à la société\s+(?P<recipient>.+?),\s*"
    r"à\s+(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*aucune\.?$",
    re.I | re.UNICODE,
)
_FR_CURRENT_LIQUIDATION_ADDRESS = re.compile(
    r"^Adresse de liquidation actuelle:\s*(?P<street>.+?)\s+"
    r"(?P<house>\d+[A-Za-z]?),\s*c/o\s+(?P<co>.+?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<town>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_PARTIAL_TRANSFER_WITHOUT_LIABILITIES = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat des\s+"
    r"(?P<date1>\d{2}\.\d{2}\.\d{4})\s+et\s+"
    r"(?P<date2>\d{2}\.\d{2}\.\d{4})\s+et décision de l['’]autorité de "
    r"surveillance du\s+(?P<approval_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"la fondation a transféré une partie des actifs de CHF\s*"
    r"(?P<assets>[\d'.]+)\s+sans passifs envers les tiers à la société\s+"
    r"(?P<recipient>.+?)\s+à\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*aucune\.?$",
    re.I | re.UNICODE,
)
_FR_FIVE_BOARD_MEMBERS_WITH_TWO_SIGNING_GROUPS = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*président,\s*"
    r"(?P<secretary>[^,.;]+),\s*secrétaire,\s*(?P<member>[^,.;]+),\s*"
    r"(?P<previous_president>[^,.;]+),\s*jusqu['’]ici président,\s*et\s*"
    r"(?P<previous_secretary>[^,.;]+),\s*jusqu['’]ici secrétaire\.\s*"
    r"Signature collective à deux de\s+(?P=president),\s*(?P=secretary)\s+"
    r"ou\s+(?P=member),\s*ou signature collective à deux sauf entre eux de\s+"
    r"(?P=previous_president)\s+ou\s+(?P=previous_secretary)\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_BOARD_MEMBERS_SIGN_WITH_ADMINISTRATOR = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*président,\s*"
    r"(?P<vice>[^,.;]+),\s*nommé vice-président,\s*et\s*"
    r"(?P<foreign_vice>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s*"
    r"(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{1,3}),\s*vice-président,\s*"
    r"lesquels signent collectivement à deux,\s*avec un administrateur\.?$",
    re.I | re.UNICODE,
)
_FR_EQUAL_TRANSFERS_TO_TWO_EXISTING_ASSOCIATES = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+par\s+"
    r"(?P<each>[\d']+)\s+parts chacun à\s+(?P<buyer1>[^,.;]+)\s+et\s+"
    r"(?P<buyer2>[^,.;]+),\s*désormais titulaires de\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\s+"
    r"chacun\.\s*(?P=seller)\s+a désormais\s+(?P<remaining>[\d']+)\s+"
    r"parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_STATUTES_DATE_CORRECTED = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que "
    r"les statuts sont du\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+et non pas du\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_IT_ASSET_ACQUISITION_PRICE_CORRECTED = re.compile(
    r"^Fatti particolari:\s*Intenzione di assunzione beni:\s*la società intende "
    r"assumere la quota di nominali\s+(?P<currency>[A-Z]{3})\s+"
    r"(?P<nominal>[\d'.]+)\s+rappresentante l['’]intero capitale sociale di\s+"
    r"(?P<company>.+?)\s*\(nr\.\s*(?P<registration_number>[^)]+)\),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<country>[A-Z]{2})\)\s+per il prezzo di\s+"
    r"(?P=currency)\s+(?P<price>[\d'.]+)\.\s*La società intende inoltre "
    r"assumere un credito di nominali\s+(?P=currency)\s+"
    r"(?P<credit_nominal>[\d'.]+)\s+per il prezzo di\s+(?P=currency)\s+"
    r"(?P<credit_price>[\d'.]+)\.\s*\[no:\s*Intenzione di assunzione beni:\s*"
    r"la società intende assumere la quota di nominali\s+(?P=currency)\s+"
    r"(?P=nominal)\s+rappresentante l['’]intero capitale sociale di\s+"
    r"(?P=company)\s*\(nr\.\s*(?P=registration_number)\),\s*in\s+"
    r"(?P=place)\s*\((?P=country)\)\s+per il prezzo di\s+(?P=currency)\s+"
    r"(?P<previous_price>[\d'.]+)\.\s*La società intende inoltre assumere "
    r"un credito di nominali\s+(?P=currency)\s+(?P=credit_nominal)\s+per il "
    r"prezzo di\s+(?P=currency)\s+(?P=credit_price)\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_TRANSFER_WITHOUT_LIABILITIES_OR_CONSIDERATION = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré des actifs "
    r"pour CHF\s*(?P<assets>[\d'.]+)\s+et aucun passif envers les tiers à\s+"
    r"(?P<recipient>.+?),\s*à\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*sans contre-prestation\.?$",
    re.I | re.UNICODE,
)
_FR_FIVE_BOARD_MEMBERS_SIGN_WITH_DELEGATE = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé président et "
    r"délégué,\s*lequel continue à signer individuellement,\s*"
    r"(?P<vice>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*vice-président,\s*(?P<member3>[^,.;]+),\s*"
    r"de\s+(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+),\s*"
    r"(?P<member4>[^,.;]+),\s*de\s+(?P<origin4>[^,.;]+),\s*à\s+"
    r"(?P<place4>[^,.;]+),\s*(?P<country4>[A-Z]{1,3}),\s*et\s+"
    r"(?P<member5>[^,.;]+),\s*de\s+(?P<origin5>[^,.;]+),\s*à\s+"
    r"(?P<place5>[^,.;]+),\s*lesquels signent collectivement à deux,\s*"
    r"avec\s+(?P=president)\.?$",
    re.I | re.UNICODE,
)
_DE_ERRONEOUS_DELETION_CORRECTED_TO_MUTATION = re.compile(
    r"^Der Eintrag von\s+(?P<surname>[^,.;]+),\s*(?P<given>[^,.;]+),\s*"
    r"von\s+(?P<origin>.+?),\s*in\s+(?P<place>[^,.;]+),\s*"
    r"(?P<previous_role>Präsident des Verwaltungsrates)\s+wurde irrtümlich "
    r"gelöscht anstelle mutiert\.\s*Die Eintragung lautet nun wie folgt:\s*"
    r"(?P=surname),\s*(?P=given),\s*von\s+(?P=origin),\s*in\s+(?P=place),\s*"
    r"(?P<role>Mitglied des Verwaltungsrates),\s*mit\s+"
    r"(?P<signing>Kollektivunterschrift zu zweien),\s*bisher:\s*"
    r"(?P=previous_role)\s+mit\s+(?P=signing)\.?$",
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


def extract_parser171_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 171."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_CHANGED_SHAREHOLDER_AND_NEW_MANAGER.fullmatch(leftover)
    if match and match.group("shares") == match.group("new_shares") and match.group(
        "nominal"
    ) == match.group("new_nominal"):
        rule_id = "de.persons.shareholder_signing_removed_and_manager_added.v1"
        shares = _count(match.group("new_shares"))
        nominal = match.group("new_nominal")
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("shareholder"),
                role="Gesellschafter", extra={
                    "action": "management_role_and_signing_removed",
                    "previous_role": "Geschäftsführer",
                    "previous_signing": "Einzelunterschrift",
                    "without_signing_authority": True,
                    "shares_count": shares, "share_nominal": nominal,
                    "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("manager"),
                place=match.group("place"), role="Geschäftsführer",
                signing="Einzelunterschrift", extra={
                    "action": "appointed", "origin": match.group("origin").strip(),
                },
            ),
        ], ""

    match = _FR_SUPPLEMENT_REFERENCE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.supplement_reference.v1", {
                "action": "entry_supplemented", "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_BOARD_LIQUIDATORS_AND_TRANSFER_RESTRICTION_REMOVED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.board_liquidators_and_transfer_restriction_removed.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="administrateur, président, liquidateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_liquidator", "signing_continues": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                role="administrateur, liquidateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_liquidator", "signing_continues": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id, {
                    "kind": "share_transfer_restrictions", "action": "removed",
                    "removed_by_law": True, "share_kind": "actions",
                },
            ),
        ], ""

    match = _FR_PRESIDENT_AND_TREASURER_SIGNING_CHANGED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.president_and_treasurer_signing_changed.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="présidente", signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed_president_and_signing_changed",
                       "restriction_removed": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("treasurer"),
                role="trésorier", signing="Kollektivunterschrift zu zweien",
                extra={"action": "presidency_ended_and_signing_changed",
                       "previous_role": "président",
                       "co_signs_with_roles": ["présidente", "vice-président"]},
            ),
        ], ""

    match = _FR_PERSON_ELECTED_LIQUIDATOR.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.person_elected_liquidator.v1",
            match.group("name"), role="liquidateur", extra={
                "action": "appointed_liquidator",
            },
        )], ""

    match = _FR_COMPANY_TRANSFER_WITH_LIABILITIES_NO_CONSIDERATION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred",
            "fr.text.company_transfer_with_liabilities_no_consideration.v1", {
                "source_kind": "company", "agreement_date": _iso_date(match.group("date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"), "consideration_kind": "none",
            },
        )], ""

    match = _FR_CURRENT_LIQUIDATION_ADDRESS.fullmatch(leftover)
    if match:
        address = {
            "street": match.group("street").strip(), "house": match.group("house"),
            "co": match.group("co").strip(), "plz": match.group("postal_code"),
            "town": match.group("town").strip(),
        }
        address_text = (
            f"{address['street']} {address['house']}, c/o {address['co']}, "
            f"{address['plz']} {address['town']}"
        )
        return [Event(
            publication_id=publication_id, published_at=published_at,
            event_type="address_changed",
            rule_id="fr.text.current_liquidation_address.v1", org_uid=org_uid,
            plz=plz, canton=canton,
            payload={"kind": "liquidation_address", "action": "changed",
                     "to": address_text, "address": address,
                     "address_key": address_key(**address)},
        )], ""

    match = _FR_FOUNDATION_PARTIAL_TRANSFER_WITHOUT_LIABILITIES.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred",
            "fr.text.foundation_partial_transfer_without_liabilities.v1", {
                "source_kind": "foundation", "partial_transfer": True,
                "agreement_dates": [_iso_date(match.group("date1")),
                                    _iso_date(match.group("date2"))],
                "supervisory_approval_date": _iso_date(match.group("approval_date")),
                "assets": match.group("assets"), "liabilities": "0",
                "liabilities_kind": "third_party_liabilities", "currency": "CHF",
                "recipient": match.group("recipient").strip().strip('"'),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"), "consideration_kind": "none",
            },
        )], ""

    match = _FR_FIVE_BOARD_MEMBERS_WITH_TWO_SIGNING_GROUPS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.five_board_members_two_signing_groups.v1"
        specs = [
            ("president", "président", "board_composition_recorded", None),
            ("secretary", "secrétaire", "board_composition_recorded", None),
            ("member", "administrateur", "board_composition_recorded", None),
            ("previous_president", "administrateur", "presidency_ended", "président"),
            ("previous_secretary", "administrateur", "secretary_role_ended", "secrétaire"),
        ]
        events = []
        for group, role, action, previous_role in specs:
            extra = {"action": action}
            if previous_role:
                extra["previous_role"] = previous_role
                extra["cannot_sign_with"] = (
                    match.group("previous_secretary") if group == "previous_president"
                    else match.group("previous_president")
                )
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(group), role=role,
                signing="Kollektivunterschrift zu zweien", extra=extra,
            ))
        return events, ""

    match = _FR_THREE_BOARD_MEMBERS_SIGN_WITH_ADMINISTRATOR.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.three_board_members_sign_with_administrator.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="administrateur, président", signing="Kollektivunterschrift zu zweien",
                extra={"action": "board_composition_recorded",
                       "co_signs_with_role": "administrateur"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("vice"),
                role="administrateur, vice-président",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_vice_president",
                    "co_signs_with_role": "administrateur",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("foreign_vice"),
                place=match.group("place"), role="administrateur, vice-président",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group("origin").strip(),
                    "country": match.group("country"),
                    "co_signs_with_role": "administrateur",
                },
            ),
        ], ""

    match = _FR_EQUAL_TRANSFERS_TO_TWO_EXISTING_ASSOCIATES.fullmatch(leftover)
    if match and len({match.group("nominal"), match.group("buyer_nominal"),
                      match.group("remaining_nominal")}) == 1:
        rule_id = "fr.persons.equal_transfers_to_two_existing_associates.v1"
        seller = match.group("seller").strip()
        each = _count(match.group("each"))
        buyers = [match.group("buyer1").strip(), match.group("buyer2").strip()]
        events = [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, seller, role="associé", extra={
                "action": "shares_transferred", "counterparties": buyers,
                "shares_before": _count(match.group("before")),
                "shares_transferred": _count(match.group("transferred")),
                "shares_transferred_each": each,
                "shares_count": _count(match.group("remaining")),
                "share_nominal": match.group("nominal"), "currency": "CHF",
            },
        )]
        for buyer in buyers:
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, role="associé", extra={
                    "action": "shares_received", "counterparty": seller,
                    "shares_received": each,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ))
        return events, ""

    match = _FR_STATUTES_DATE_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.statutes_date_corrected.v1", {
                "action": "date_corrected", "date": _iso_date(match.group("date")),
                "previous_incorrect_date": _iso_date(match.group("previous_date")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _IT_ASSET_ACQUISITION_PRICE_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "it.text.asset_acquisition_price_corrected.v1", {
                "kind": "asset_acquisition_intention_clause", "action": "price_corrected",
                "currency": match.group("currency").upper(),
                "shareholding_nominal": match.group("nominal"),
                "target": match.group("company").strip(),
                "target_registration_number": match.group("registration_number"),
                "target_place": match.group("place").strip(),
                "target_country": match.group("country"),
                "price": match.group("price"),
                "previous_incorrect_price": match.group("previous_price"),
                "credit_nominal": match.group("credit_nominal"),
                "credit_price": match.group("credit_price"),
            },
        )], ""

    match = _FR_COMPANY_TRANSFER_WITHOUT_LIABILITIES_OR_CONSIDERATION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred",
            "fr.text.company_transfer_without_liabilities_or_consideration.v1", {
                "source_kind": "company", "agreement_date": _iso_date(match.group("date")),
                "assets": match.group("assets"), "liabilities": "0",
                "liabilities_kind": "third_party_liabilities", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"), "consideration_kind": "none",
            },
        )], ""

    match = _FR_FIVE_BOARD_MEMBERS_SIGN_WITH_DELEGATE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.five_board_members_sign_with_delegate.v1"
        events = [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("president"),
            role="administrateur, président, délégué", signing="Einzelunterschrift",
            extra={"action": "appointed_president_and_delegate",
                   "signing_continues": True},
        )]
        specs = [
            ("vice", "origin2", "place2", "administrateur, vice-président", None),
            ("member3", "origin3", "place3", "administrateur", None),
            ("member4", "origin4", "place4", "administrateur", match.group("country4")),
            ("member5", "origin5", "place5", "administrateur", None),
        ]
        for name_group, origin_group, place_group, role, country in specs:
            extra = {
                "action": "board_composition_recorded",
                "origin": match.group(origin_group).strip(),
                "co_signs_with": match.group("president").strip(),
            }
            if country:
                extra["country"] = country
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(name_group),
                place=match.group(place_group), role=role,
                signing="Kollektivunterschrift zu zweien", extra=extra,
            ))
        return events, ""

    match = _DE_ERRONEOUS_DELETION_CORRECTED_TO_MUTATION.fullmatch(leftover)
    if match:
        name = f"{match.group('surname')}, {match.group('given')}"
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.erroneous_deletion_corrected_to_mutation.v1",
            name, place=match.group("place"), role=match.group("role"),
            signing=match.group("signing"), extra={
                "action": "erroneous_deletion_corrected_to_mutation",
                "origin": match.group("origin").strip(),
                "previous_role": match.group("previous_role"),
                "previous_signing": match.group("signing"),
            },
        )], ""

    return [], text
