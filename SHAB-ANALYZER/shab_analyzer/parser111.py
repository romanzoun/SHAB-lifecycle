from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_ASSET_TAKEOVER_AND_PROFIT_CERTIFICATES_REMOVED = re.compile(
    r"^La disposition statutaire relative à la reprise de biens est abrogée "
    r"conformément à l['’]article\s+(?P<legal_basis>628 al\.\s*4 CO)\.\s*"
    r"Suppression des\s+(?P<count>[\d']+)\s+bons de jouissance donnant droit à "
    r"(?P<rights>une part du bénéfice net et du produit de liquidation),\s*"
    r"les détenteurs ayant été désintéressés\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_THREE_MIXED_SIGNING = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé président,\s*"
    r"(?P<member1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*et\s*"
    r"(?P<member2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+)\.\s*"
    r"Signature individuelle du président ou collective à deux des autres "
    r"membres du conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_FR_AUTHORIZED_CAPITAL_CLAUSE_REMOVED_WITH_DATE = re.compile(
    r"^(?P<date>\d{2}\.\d{2}\.\d{4})\.\s*Suppression de la clause statutaire "
    r"relative à l['’]augmentation autorisée du capital fondée sur la décision "
    r"d['’]autorisation du\s+(?P<authorization_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_APPOINTED_WAIVER_REVOKED = re.compile(
    r"^Radiation de la mention relative à la renonciation à un contrôle "
    r"restreint\.\s*Organe de révision:\s*(?P<name>.+?)\s+"
    r"(?P<uid>CHE-\d{3}\.\d{3}\.\d{3}),\s*à\s+(?P<place>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_TWO_ASSOCIATES = re.compile(
    r"^Par suite de cession de\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*l['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+"
    r"détient\s+(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\s+et l['’]associé\s+(?P<buyer>[^,.;]+)\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_LIQUIDATOR_MANAGERS_CONTINUE_INDIVIDUAL = re.compile(
    r"^Liquidateurs:\s*(?P<president>[^,.;]+),\s*président,\s*et\s*"
    r"(?P<member>[^,.;]+),\s*gérants,\s*lesquels continuent de signer "
    r"individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_PROPRIETOR_MORATORIUM_EXTENDED = re.compile(
    r"^Par décision du\s+(?P<decision_date>\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4}),\s*(?P<authority>.+?)\s+a prolongé le "
    r"sursis concordataire accordé au titulaire jusqu['’]au\s+"
    r"(?P<until>\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_DOMICILES_CORRECTED_WITH_NOTICE = re.compile(
    r"^Rectification:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s*est rectifiée dans le sens que le domicile "
    r"correct de\s+(?P<name1>[^,.;]+)\s+est à\s+(?P<place1>[^,.;]+)\s+"
    r"et non pas à\s+(?P<previous_place1>[^,.;]+)\s+et le domicile correct de\s+"
    r"(?P<name2>[^,.;]+)\s+est à\s+(?P<place2>[^,.;]+)\s+et non pas à\s+"
    r"(?P<previous_place2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSET_TRANSFER_NO_LIABILITIES_CASH = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré des actifs "
    r"pour CHF\s+(?P<assets>[\d'.]+)\s+et aucun passif envers les tiers,\s*à\s+"
    r"(?P<recipient>.+?),\s*à\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*Contre-prestation:\s*"
    r"CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_LIABILITY_FUNDS_ORGANIZATION_UPDATED = re.compile(
    r"^Haftung/Nachschusspflicht neu:\s*\[(?P<liability_reason>Löschung infolge "
    r"geänderter Eintragungsvorschriften gemäss\s+"
    r"(?P<liability_basis>Art\.\s*92 lit\.\s*i HRegV))\.\]\s*"
    r"\[gestrichen:\s*(?P<previous_liability>[^\]]+)\]\.\s*"
    r"Mittel neu:\s*(?P<funds>.+?)\.\s*\[bisher:\s*Mittel:\s*"
    r"(?P<previous_funds>[^\]]+)\]\.\s*Organisation neu:\s*"
    r"\[(?P<organization_reason>Löschung infolge geänderter "
    r"Eintragungsvorschriften gemäss\s+"
    r"(?P<organization_basis>Art\.\s*92 lit\.\s*j der HRegV))\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_HEAD_OFFICE_PROXY_PAIR = re.compile(
    r"^Procuration collective à deux,\s*limitée au siège principal,\s*pas avec "
    r"un autre fondé de procuration,\s*est conférée à\s+"
    r"(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_ASSOCIATE_SEAT_CHANGED = re.compile(
    r"^Nouveau siège de l['’]associée\s+[\"“](?P<name>.+?)[\"”]\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\):\s*(?P<place>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_PAIR_ORIGIN_CORRECTED_WITH_NOTICE = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<name1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+)\s+sont de\s+"
    r"(?P<origin>[^()]+?)\s*\(et non de\s+(?P<previous_origin>.+?)\s+comme "
    r"publié\)\.?$",
    re.I | re.UNICODE,
)
_DE_ASSOCIATION_DISSOLVED_BOARD_IMPOSSIBLE = re.compile(
    r"^Name neu:\s*(?P<name>.+? in Liquidation)\.\s*Der Verein ist von "
    r"Gesetzes wegen aufgelöst wegen Unmöglichkeit der Bestellung eines "
    r"statutengemässen Vorstands\s*\((?P<legal_basis>Art\.\s*77 ZGB)\)\.\s*"
    r"Die Eintragung erfolgt von Amtes gemäss\s*"
    r"(?P<registration_basis>Art\.\s*152 HRegV)\.?$",
    re.I | re.UNICODE,
)
_FR_CROSS_BORDER_MERGER_BERMUDA = re.compile(
    r"^Fusion transfrontalière:\s*reprise des actifs et passifs,\s*au sens de\s*"
    r"l['’](?P<legal_basis>art\.\s*163a LDIP),\s*de\s+"
    r"(?P<absorbed_name>.+?),\s*à\s+(?P<absorbed_place>[^,.;]+),\s*"
    r"(?P<absorbed_country>[A-Z]{3}),\s*société de droit des\s+"
    r"(?P<governing_law>[^,.;]+),\s*inscrite au registrar of companies sous le "
    r"n°\s*(?P<registry_id>[^,.;]+),\s*selon contrat de fusion du\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+et bilan au\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\s+présentant des actifs de CHF\s+"
    r"(?P<assets>[\d'.]+)\s+et aucun passif envers les tiers\.\s*La société "
    r"reprenante détenant l['’]ensemble des actions de la société transférante,\s*"
    r"la fusion ne donne pas lieu à une augmentation du capital,\s*ni à une "
    r"attribution d['’]actions\.?$",
    re.I | re.UNICODE,
)
_FR_CAPITAL_REDUCTION_SPLIT_SIMULTANEOUS_INCREASE = re.compile(
    r"^Réduction du capital-actions de CHF\s+(?P<initial_total>[\d'.]+)\s+à CHF\s+"
    r"(?P<reduced_total>[\d'.]+),\s*par réduction de la valeur nominale des\s+"
    r"(?P<initial_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<initial_nominal>[\d'.]+)\s+à CHF\s+(?P<reduced_nominal>[\d'.]+),\s*"
    r"par affectation du montant de la réduction à la réserve légale issue "
    r"d['’]apports de capital\.\s*Les\s+(?P<split_from_count>[\d']+)\s+actions "
    r"nominatives de CHF\s+(?P<split_from_nominal>[\d'.]+),\s*formant l['’]entier "
    r"du capital-actions,\s*sont transformées en\s+(?P<split_to_count>[\d']+)\s+"
    r"actions nominatives de CHF\s+(?P<split_to_nominal>[\d'.]+)\.\s*"
    r"Augmentation simultanée du capital-actions par conversion de fonds propres "
    r"dont la société peut librement disposer\.\s*Nouveau capital-actions "
    r"entièrement libéré:\s*CHF\s+(?P<final_total>[\d'.]+),\s*divisé en\s+"
    r"(?P<final_count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<final_nominal>[\d'.]+)[,.]?$",
    re.I | re.UNICODE,
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


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _french_date(raw: str) -> str:
    day, month, year = raw.lower().replace("1er", "1").split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


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
        payload={
            "name": clean_name,
            "place": clean_place,
            **({"uid": uid} if uid else {}),
            **(extra or {}),
        },
    )


def extract_parser111_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 111."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_ASSET_TAKEOVER_AND_PROFIT_CERTIFICATES_REMOVED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.asset_takeover_and_profit_certificates_removed.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id,
                {
                    "kind": "asset_takeover_clause", "action": "removed",
                    "legal_basis": match.group("legal_basis"),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "kind": "participation_certificates", "action": "removed",
                    "count": _count(match.group("count")),
                    "rights": match.group("rights"),
                    "holders_compensated": True,
                },
            ),
        ])

    match = _FR_ADMINISTRATION_THREE_MIXED_SIGNING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_three_mixed_signing.v1"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("president"),
            role="président", signing="Einzelunterschrift",
            extra={"action": "appointed_president"},
        ))
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"member{index}"),
                place=match.group(f"place{index}"), role="administrateur",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed", "heimat": match.group(f"origin{index}").strip(),
                },
            ))

    match = _FR_AUTHORIZED_CAPITAL_CLAUSE_REMOVED_WITH_DATE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.authorized_capital_clause_removed_with_date.v1",
            {
                "kind": "authorized_capital_clause", "action": "removed",
                "date": _iso_date(match.group("date")),
                "authorization_date": _iso_date(match.group("authorization_date")),
            },
        ))

    match = _FR_AUDITOR_APPOINTED_WAIVER_REVOKED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.auditor_appointed_waiver_revoked.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "audit_requirement_changed", rule_id,
                {"kind": "limited_audit_waiver", "action": "revoked"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), uid=match.group("uid"),
                role="organe de révision", extra={"action": "appointed"},
            ),
        ])

    match = _FR_SHARE_TRANSFER_TWO_ASSOCIATES.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.share_transfer_two_associates.v1"
        common = {
            "shares_transferred": _count(match.group("transferred")),
            "share_nominal": match.group("nominal"),
            "currency": "CHF",
        }
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller"),
                role="associé-gérant",
                extra={
                    **common, "action": "shares_transferred",
                    "counterparty": match.group("buyer").strip(),
                    "shares_count": _count(match.group("seller_count")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"), role="associé",
                extra={
                    **common, "action": "shares_received",
                    "counterparty": match.group("seller").strip(),
                    "shares_count": _count(match.group("buyer_count")),
                },
            ),
        ])

    match = _FR_LIQUIDATOR_MANAGERS_CONTINUE_INDIVIDUAL.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.liquidator_managers_continue_individual.v1"
        for group, role in (("president", "liquidateur président"), ("member", "liquidateur")):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(group), role=role,
                signing="Einzelunterschrift",
                extra={
                    "action": "appointed_liquidator", "previous_role": "gérant",
                    "continues_signing": True,
                },
            ))

    match = _FR_SOLE_PROPRIETOR_MORATORIUM_EXTENDED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.sole_proprietor_moratorium_extended.v1",
            {
                "kind": "composition_moratorium_extended",
                "decision_date": _french_date(match.group("decision_date")),
                "until": _french_date(match.group("until")),
                "authority": match.group("authority").strip(),
                "subject": "sole_proprietor",
            },
        ))

    match = _FR_TWO_DOMICILES_CORRECTED_WITH_NOTICE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_domiciles_corrected_with_notice.v1"
        reference = {
            "action": "domicile_corrected", "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_ref": match.group("notice_ref"),
        }
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                extra={
                    **reference, "previous_place": match.group(f"previous_place{index}").strip(),
                },
            ))

    match = _FR_ASSET_TRANSFER_NO_LIABILITIES_CASH.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.asset_transfer_no_liabilities_cash.v1",
            {
                "date": _iso_date(match.group("date")),
                "assets": match.group("assets"), "liabilities": "0",
                "liabilities_transferred": False, "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"),
                "consideration_kind": "cash",
            },
        ))

    match = _DE_LIABILITY_FUNDS_ORGANIZATION_UPDATED.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.liability_funds_organization_updated.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id,
                {
                    "kind": "member_liability", "action": "removed",
                    "previous": match.group("previous_liability").strip().rstrip("."),
                    "reason": "changed_registration_rules",
                    "legal_basis": re.sub(r"\s+", " ", match.group("liability_basis")),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id,
                {
                    "kind": "funding", "action": "changed",
                    "to": match.group("funds").strip(),
                    "previous": match.group("previous_funds").strip().rstrip("."),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id,
                {
                    "kind": "organization_entry", "action": "removed",
                    "reason": "changed_registration_rules",
                    "legal_basis": re.sub(r"\s+", " ", match.group("organization_basis")),
                },
            ),
        ])

    match = _FR_HEAD_OFFICE_PROXY_PAIR.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.head_office_proxy_pair.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="fondé de procuration",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "granted", "heimat": match.group(f"origin{index}").strip(),
                    "limited_to_head_office": True,
                    "cannot_sign_with_other_proxy_holder": True,
                },
            ))

    match = _FR_COMPANY_ASSOCIATE_SEAT_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.company_associate_seat_changed.v1",
            match.group("name"), place=match.group("place"), uid=match.group("uid"),
            role="associée", extra={"action": "seat_changed"},
        ))

    match = _FR_PAIR_ORIGIN_CORRECTED_WITH_NOTICE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.pair_origin_corrected_with_notice.v1"
        reference = {
            "action": "origin_corrected", "heimat": match.group("origin").strip(),
            "previous_heimat": match.group("previous_origin").strip(),
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_ref": match.group("notice_ref"),
        }
        for group in ("name1", "name2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(group), extra=reference,
            ))

    match = _DE_ASSOCIATION_DISSOLVED_BOARD_IMPOSSIBLE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.association_dissolved_board_impossible.v1",
            {
                "kind": "dissolution", "action": "dissolved_by_law",
                "reason": "statutory_board_cannot_be_appointed",
                "new_name": match.group("name").strip(),
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "registration": "ex_officio",
                "registration_basis": re.sub(
                    r"\s+", " ", match.group("registration_basis")
                ),
            },
        ))

    match = _FR_CROSS_BORDER_MERGER_BERMUDA.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "fr.text.cross_border_merger_bermuda_same_shareholder.v1",
            {
                "kind": "cross_border_merger",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_country": match.group("absorbed_country"),
                "governing_law": match.group("governing_law").strip(),
                "absorbed_registry_id": match.group("registry_id").strip(),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "currency": "CHF", "assets": match.group("assets"),
                "liabilities": "0", "liabilities_to_third_parties": False,
                "same_shareholder": True, "capital_increase": False,
                "share_allocation": False,
            },
        ))

    match = _FR_CAPITAL_REDUCTION_SPLIT_SIMULTANEOUS_INCREASE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.capital_reduction_split_simultaneous_increase.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "kind": "share_capital_reduction", "action": "reduced",
                    "currency": "CHF", "from_total": match.group("initial_total"),
                    "to_total": match.group("reduced_total"),
                    "share_count": _count(match.group("initial_count")),
                    "from_nominal": match.group("initial_nominal"),
                    "to_nominal": match.group("reduced_nominal"),
                    "allocated_to": "legal_capital_contribution_reserve",
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "kind": "registered_share_split", "action": "split",
                    "currency": "CHF",
                    "from_count": _count(match.group("split_from_count")),
                    "from_nominal": match.group("split_from_nominal"),
                    "to_count": _count(match.group("split_to_count")),
                    "to_nominal": match.group("split_to_nominal"),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "kind": "simultaneous_share_capital_increase", "action": "increased",
                    "method": "conversion_of_freely_disposable_equity",
                    "currency": "CHF", "total": match.group("final_total"),
                    "share_count": _count(match.group("final_count")),
                    "share_nominal": match.group("final_nominal"),
                    "share_kind": "actions nominatives", "fully_paid": True,
                },
            ),
        ])

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
