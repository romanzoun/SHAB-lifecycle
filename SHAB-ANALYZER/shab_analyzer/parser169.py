from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_BOARD_MEMBER_REELECTED = re.compile(
    r"^\[An der Generalversammlung vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"wurde\s+(?P<name>[^,.;]+),\s*von\s+(?P<origin>[^,.;]+),\s*in\s+"
    r"(?P<place>[^,.;]+),\s*als Mitglied des Verwaltungsrates "
    r"wiedergewählt\.\]$",
    re.I | re.UNICODE,
)
_DE_PREVIOUS_REGISTER_FACTS_REFERENCE_REMOVED = re.compile(
    r"^\[gestrichen:\s*Die vor der Eintragung im Handelsregister des Kantons\s+"
    r"(?P<previous_canton>.+?)\s+gestrichenen Tatsachen,\s*sowie allfällige "
    r"frühere Statutendaten oder Tagebuch- und SHAB-Zitate können im "
    r"Registerauszug des bisherigen Sitzes,\s*welcher bei den abgelegten "
    r"Handelsregisterakten liegt,\s*eingesehen werden\.\]$",
    re.I | re.UNICODE,
)
_DE_FOUNDATION_REPEALED = re.compile(
    r"^Die Stiftung ist gemäss Regierungsratsbeschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+aufgehoben\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_CORPORATE_ASSOCIATES_TRANSFER_TO_NEW_ASSOCIATE = re.compile(
    r"^Par suite de cessions chacune de\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*l['’]associée\s+(?P<seller1>.+?)\s*"
    r"\((?P<uid1>CHE-\d{3}\.\d{3}\.\d{3})\)\s+détient\s+"
    r"(?P<count1>[\d']+)\s+parts de CHF\s+(?P<nominal1>[\d'.]+),\s*"
    r"l['’]associée\s+(?P<seller2>.+?)\s*"
    r"\((?P<uid2>CHE-\d{3}\.\d{3}\.\d{3})\)\s+détient\s+"
    r"(?P<count2>[\d']+)\s+parts de CHF\s+(?P<nominal2>[\d'.]+),\s*et\s+"
    r"l['’]associée\s+(?P<seller3>.+?)\s*"
    r"\((?P<uid3>CHE-\d{3}\.\d{3}\.\d{3})\)\s+détient\s+"
    r"(?P<count3>[\d']+)\s+parts de CHF\s+(?P<nominal3>[\d'.]+)\.\s*"
    r"Cessionnaire et nouvelle associée:\s*(?P<buyer>.+?)\s*"
    r"\((?P<buyer_registry>[^)]+)\),\s*à\s+(?P<buyer_place>[^,.;]+),\s*"
    r"(?P<buyer_country>[A-Z]{2,3}),\s*pour\s+(?P<buyer_count>[\d']+)\s+"
    r"parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ASSOCIATES_TRANSFER_TO_NEW_MANAGER_THREE_SIGNING = re.compile(
    r"^(?P<seller1>[^,.;]+),\s*qui est maintenant à\s+"
    r"(?P<seller1_place>[^,.;]+),\s*et\s+(?P<seller2>[^,.;]+)\s+cèdent chacun\s+"
    r"(?P<transferred>[\d']+)\s+de leurs\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<buyer_origin>[^,.;]+),\s*à\s+"
    r"(?P<buyer_place>[^,.;]+),\s*nouvel associé-gérant à trois,\s*avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"(?P=seller1)\s+et\s+(?P=seller2),\s*qui restent titulaires de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\s+"
    r"chacun,\s*signent désormais collectivement à trois\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_SECRETARY_AND_UNSIGNED_MEMBER = re.compile(
    r"^(?P<secretary>[^,.;]+),\s*membre du conseil de fondation,\s*"
    r"est élue secrétaire\.\s*Nouveau membre du conseil de fondation sans "
    r"signature:\s*(?P<member>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_APPOINTED_PROXY_EXTINGUISHED = re.compile(
    r"^(?P<name>[^,.;]+),\s*dont la procuration collective à deux est "
    r"éteinte,\s*est nommé directeur\.?$",
    re.I | re.UNICODE,
)
_DE_COOPERATIVE_LIABILITY_AND_CONTRIBUTIONS_REMOVED = re.compile(
    r"^Haftung/Nachschusspflicht neu:\s*"
    r"\[Die persönliche Haftung oder Nachschusspflichten gemäss Statuten "
    r"wurden aufgehoben\]\s*\[gestrichen:\s*Persönliche Haftung oder "
    r"Nachschusspflichten:\s*Gemäss Statuten\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_AND_CONDITIONAL_CAPITAL_RESOLUTIONS = re.compile(
    r"^Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+den Beschluss über die "
    r"Ermächtigung einer genehmigten Kapitalerhöhung vom\s+"
    r"(?P<authorization_date>\d{2}\.\d{2}\.\d{4})\s+gemäss näherer "
    r"Umschreibung in den Statuten angepasst\.\s*\[bisher:\s*Die "
    r"Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+den Beschluss über "
    r"die Ermächtigung einer genehmigten Kapitalerhöhung vom\s+"
    r"(?P<previous_authorization_date>\d{2}\.\d{2}\.\d{4})\s+gemäss näherer "
    r"Umschreibung in den Statuten angepasst\.\]\.?\s*Die Generalversammlung "
    r"hat mit Beschluss vom\s+(?P<conditional_decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"die Statutenbestimmung über die bedingte Kapitalerhöhung vom\s+"
    r"(?P<conditional_clause_date>\d{2}\.\d{2}\.\d{4})\s+geändert\.\s*\.?(?:\s*)"
    r"Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<additional_decision_date>\d{2}\.\d{2}\.\d{4})\s+eine weitere "
    r"bedingte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten "
    r"eingeführt\.?$",
    re.I | re.UNICODE,
)
_FR_FORMATION_ASSET_ACQUISITION_CLAUSE_REMOVED = re.compile(
    r"^La clause statutaire relative à la reprise de biens effectuée à la "
    r"constitution est supprimée conformément à l['’]art\.\s*"
    r"(?P<article>628),\s*al\.\s*(?P<paragraph>4),\s*CO\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_AND_PARTICIPATION_CAPITAL_CORRECTED = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée comme suit:\s*Augmentation "
    r"ordinaire du capital-actions porté de CHF\s+(?P<share_from>[\d']+,\s*\d+)\s+"
    r"à CHF\s+(?P<share_to>[\d']+,\s*\d+)\s+par l['’]émission de\s+"
    r"(?P<shares_issued>[\d']+)\s+actions de CHF\s+"
    r"(?P<share_nominal>[\d'.]+),\s*privilégiées quant au produit de "
    r"liquidation,\s*nominatives,\s*dont\s+(?P<shares_compensated>[\d']+)\s+"
    r"actions entièrement libérées par compensation de créances pour CHF\s+"
    r"(?P<share_compensation>[\d'.]+)\s*\(et non pas pour CHF\s+"
    r"(?P<previous_share_compensation>[\d'.]+)\),\s*le solde constituant un "
    r"agio\.\s*Augmentation ordinaire du capital-participations porté de CHF\s+"
    r"(?P<participation_from>[\d'.]+)\s+à CHF\s+"
    r"(?P<participation_to>[\d']+,\s*\d+)\s+par l['’]émission de\s+"
    r"(?P<participations_issued>[\d']+)\s+bons de participations de CHF\s+"
    r"(?P<participation_nominal>[\d'.]+),\s*privilégiés quant au produit de "
    r"liquidation,\s*nominatifs,\s*entièrement libérées par compensation de "
    r"créances pour CHF\s+(?P<participation_compensation>[\d'.]+)\s*"
    r"\(et non pas pour CHF\s+(?P<previous_participation_compensation>[\d'.]+)\),\s*"
    r"le solde constituant un agio\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_ASSET_TRANSFER_SHARES_AND_CREDIT = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft\s*überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\((?P<liabilities_kind>Fremdkapital)\)\s+"
    r"von CHF\s+(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*"
    r"in\s+(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<share_count>[\d'.]+)\s+Namenaktien zu CHF\s+"
    r"(?P<share_nominal>[\d'.]+)\s+der\s+(?P<share_issuer>.+?)\s+sowie eine "
    r"Forderungsgutschrift von CHF\s+(?P<credit>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_AUTHORIZED_REPLACED_AND_CONDITIONAL_CAPITAL_MODIFIED = re.compile(
    r"^Par décision du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"l['’]assemblée générale a supprimé la clause statutaire introduite le\s+"
    r"(?P<authorized_previous_date>\d{2}\.\d{2}\.\d{4})\s+en matière "
    r"d['’]augmentation autorisée du capital-actions et a introduit une nouvelle "
    r"clause statutaire en la matière;\s*pour les détails,\s*voir les statuts\.\s*"
    r"Par décision du\s+(?P<conditional_decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"l['’]assemblée générale a modifié la clause statutaire introduite le\s+"
    r"(?P<conditional_previous_date>\d{2}\.\d{2}\.\d{4})\s+en matière "
    r"d['’]augmentation conditionnelle du capital-actions;\s*pour les détails,\s*"
    r"voir les statuts\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_THREE_COLLECTIVE_SIGNING_CHANGED = re.compile(
    r"^Administration:\s*(?P<name1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,.;]+),\s*(?P<country1>[A-Z]{1,3}),\s*"
    r"(?P<role1>président),\s*(?P<name2>[^,.;]+),\s*de\s+"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*et\s+"
    r"(?P<name3>[^,.;]+),\s*lesquels signent collectivement à deux\.\s*"
    r"Les pouvoirs de\s+(?P=name3)\s+sont modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_LIQUIDATORS_AND_SIGNATURE_REVOKED = re.compile(
    r"^Liquidateurs:\s*(?P<name1>[^,.;]+),\s*(?P<role1>président),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*tous deux gérants,\s*lesquels continuent de signer "
    r"individuellement\.\s*(?P<name3>[^,.;]+),\s*gérant,\s*n['’]exerce plus la "
    r"signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_SEAT_TRANSFER_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que la société a "
    r"transféré son siège à\s+(?P<place>[^()]+?)\s*\(et non à\s+"
    r"(?P<previous_place>.+?)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _decimal(raw: str) -> str:
    return re.sub(r"\s+", "", raw).replace(",", ".")


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


def extract_parser169_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 169."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()
    events: list[Event] = []

    match = _DE_BOARD_MEMBER_REELECTED.fullmatch(leftover)
    if match:
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.board_member_reelected.v1",
            match.group("name"), place=match.group("place"),
            role="Mitglied des Verwaltungsrates", extra={
                "action": "reelected", "origin": match.group("origin").strip(),
                "decision_date": _iso_date(match.group("date")),
                "authority": "Generalversammlung",
            },
        ))
        return events, ""

    match = _DE_PREVIOUS_REGISTER_FACTS_REFERENCE_REMOVED.fullmatch(leftover)
    if match:
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.previous_register_facts_reference_removed.v1", {
                "kind": "previous_register_facts_reference", "action": "removed",
                "previous_register_canton": match.group("previous_canton").strip(),
            },
        ))
        return events, ""

    match = _DE_FOUNDATION_REPEALED.fullmatch(leftover)
    if match:
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.foundation_repealed_by_government.v1", {
                "kind": "dissolution", "action": "foundation_repealed",
                "decision_date": _iso_date(match.group("date")),
                "authority": "Regierungsrat",
            },
        ))
        return events, ""

    match = _FR_THREE_CORPORATE_ASSOCIATES_TRANSFER_TO_NEW_ASSOCIATE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.three_corporate_associates_transfer_to_new_associate.v1"
        transferred = _count(match.group("transferred"))
        for index in (1, 2, 3):
            seller = match.group(f"seller{index}").strip()
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associée",
                uid=match.group(f"uid{index}"), extra={
                    "uid": match.group(f"uid{index}"), "action": "shares_transferred",
                    "counterparty": match.group("buyer").strip(),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group(f"count{index}")),
                    "share_nominal": match.group(f"nominal{index}"), "currency": "CHF",
                },
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("buyer"),
            place=match.group("buyer_place"), role="associée", extra={
                "action": "shares_received", "new_associate": True,
                "registry_id": match.group("buyer_registry"),
                "country": match.group("buyer_country"),
                "shares_received": _count(match.group("buyer_count")),
                "shares_count": _count(match.group("buyer_count")),
                "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
            },
        ))
        return events, ""

    match = _FR_TWO_ASSOCIATES_TRANSFER_TO_NEW_MANAGER_THREE_SIGNING.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_associates_transfer_to_new_manager_three_signing.v1"
        seller_common = {
            "action": "shares_and_signing_changed",
            "counterparty": match.group("buyer").strip(),
            "shares_transferred": _count(match.group("transferred")),
            "shares_before": _count(match.group("before")),
            "shares_count": _count(match.group("remaining")),
            "share_nominal": match.group("remaining_nominal"), "currency": "CHF",
        }
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller1"),
                place=match.group("seller1_place"), role="associé",
                signing="Kollektivunterschrift zu dreien", extra={
                    **seller_common, "domicile_changed": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller2"), role="associé",
                signing="Kollektivunterschrift zu dreien", extra=seller_common,
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"),
                place=match.group("buyer_place"), role="associé-gérant",
                signing="Kollektivunterschrift zu dreien", extra={
                    "action": "appointed_manager_and_shares_received",
                    "new_associate": True, "origin": match.group("buyer_origin").strip(),
                    "shares_received": _count(match.group("buyer_count")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])
        return events, ""

    match = _FR_FOUNDATION_SECRETARY_AND_UNSIGNED_MEMBER.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.foundation_secretary_and_unsigned_member.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("secretary"),
                role="membre du conseil de fondation, secrétaire",
                extra={"action": "appointed_secretary"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                place=match.group("place"), role="membre du conseil de fondation",
                extra={
                    "action": "appointed", "origin": match.group("origin").strip(),
                    "without_signing_authority": True,
                },
            ),
        ])
        return events, ""

    match = _FR_DIRECTOR_APPOINTED_PROXY_EXTINGUISHED.fullmatch(leftover)
    if match:
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.director_appointed_proxy_extinguished.v1",
            match.group("name"), role="directeur", extra={
                "action": "appointed_director_and_proxy_extinguished",
                "previous_signing": "procuration collective à deux",
            },
        ))
        return events, ""

    if _DE_COOPERATIVE_LIABILITY_AND_CONTRIBUTIONS_REMOVED.fullmatch(leftover):
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.liability_and_additional_contributions_removed.v1", {
                "kind": "personal_liability_and_additional_contributions",
                "action": "removed", "previous_basis": "statutes",
            },
        ))
        return events, ""

    match = _DE_AUTHORIZED_AND_CONDITIONAL_CAPITAL_RESOLUTIONS.fullmatch(leftover)
    if match:
        rule_id = "de.text.authorized_and_conditional_capital_resolutions.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause", "action": "modified",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "authorization_date": _iso_date(match.group("authorization_date")),
                    "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                    "previous_authorization_date": _iso_date(match.group("previous_authorization_date")),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "conditional_capital_clause", "action": "modified",
                    "decision_date": _iso_date(match.group("conditional_decision_date")),
                    "clause_date": _iso_date(match.group("conditional_clause_date")),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "conditional_capital_clause", "action": "introduced_additional",
                    "decision_date": _iso_date(match.group("additional_decision_date")),
                },
            ),
        ])
        return events, ""

    match = _FR_FORMATION_ASSET_ACQUISITION_CLAUSE_REMOVED.fullmatch(leftover)
    if match:
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.formation_asset_acquisition_clause_removed.v1", {
                "kind": "formation_asset_acquisition_clause", "action": "removed",
                "legal_basis": f"art. {match.group('article')}, al. {match.group('paragraph')}, CO",
            },
        ))
        return events, ""

    match = _FR_SHARE_AND_PARTICIPATION_CAPITAL_CORRECTED.fullmatch(leftover)
    if match:
        rule_id = "fr.text.share_and_participation_capital_corrected.v1"
        reference = {
            "action": "correction", "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_ref": match.group("notice_ref"), "currency": "CHF",
        }
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    **reference, "kind": "share_capital", "increase_kind": "ordinary",
                    "from_nominal": _decimal(match.group("share_from")),
                    "to_nominal": _decimal(match.group("share_to")),
                    "shares_issued": _count(match.group("shares_issued")),
                    "share_nominal": match.group("share_nominal"),
                    "share_kind": "registered, liquidation-preference",
                    "shares_compensated": _count(match.group("shares_compensated")),
                    "compensation_amount": match.group("share_compensation"),
                    "previous_compensation_amount": match.group("previous_share_compensation"),
                    "balance_as_agio": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    **reference, "kind": "participation_capital", "increase_kind": "ordinary",
                    "from_nominal": _decimal(match.group("participation_from")),
                    "to_nominal": _decimal(match.group("participation_to")),
                    "participation_certificates_issued": _count(match.group("participations_issued")),
                    "participation_nominal": match.group("participation_nominal"),
                    "participation_kind": "registered, liquidation-preference",
                    "compensation_amount": match.group("participation_compensation"),
                    "previous_compensation_amount": match.group("previous_participation_compensation"),
                    "balance_as_agio": True,
                },
            ),
        ])
        return events, ""

    match = _DE_COMPANY_ASSET_TRANSFER_SHARES_AND_CREDIT.fullmatch(leftover)
    if match:
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.company_asset_transfer_shares_and_credit.v1", {
                "date": _iso_date(match.group("date")), "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": match.group("liabilities_kind"), "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration_kind": "registered_shares_and_credit",
                "share_count": match.group("share_count"),
                "share_nominal": match.group("share_nominal"),
                "share_issuer": match.group("share_issuer").strip(),
                "credit": match.group("credit"),
            },
        ))
        return events, ""

    match = _FR_AUTHORIZED_REPLACED_AND_CONDITIONAL_CAPITAL_MODIFIED.fullmatch(leftover)
    if match:
        rule_id = "fr.text.authorized_replaced_and_conditional_capital_modified.v1"
        decision_date = _iso_date(match.group("decision_date"))
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause", "action": "removed",
                    "decision_date": decision_date,
                    "clause_date": _iso_date(match.group("authorized_previous_date")),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause", "action": "introduced",
                    "decision_date": decision_date,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "conditional_capital_clause", "action": "modified",
                    "decision_date": _iso_date(match.group("conditional_decision_date")),
                    "clause_date": _iso_date(match.group("conditional_previous_date")),
                },
            ),
        ])
        return events, ""

    match = _FR_BOARD_THREE_COLLECTIVE_SIGNING_CHANGED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.board_three_collective_signing_changed.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="administrateur, président",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "board_composition_recorded",
                    "origin": match.group("origin1").strip(),
                    "country": match.group("country1"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="administrateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "board_composition_recorded",
                    "origin": match.group("origin2").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name3"),
                role="administrateur", signing="Kollektivunterschrift zu zweien",
                extra={"action": "signing_changed"},
            ),
        ])
        return events, ""

    match = _FR_MANAGER_LIQUIDATORS_AND_SIGNATURE_REVOKED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.manager_liquidators_and_signature_revoked.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role="gérant, liquidateur, président", signing="Einzelunterschrift",
                extra={"action": "appointed_liquidator", "signing_continues": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                role="gérante, liquidatrice", signing="Einzelunterschrift",
                extra={"action": "appointed_liquidator", "signing_continues": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name3"),
                role="gérant", extra={
                    "action": "signing_revoked", "previous_signing": "signature sociale",
                },
            ),
        ])
        return events, ""

    match = _FR_SEAT_TRANSFER_CORRECTED.fullmatch(leftover)
    if match:
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "seat_changed", "fr.text.seat_transfer_corrected.v1", {
                "action": "correction", "from": match.group("previous_place").strip(),
                "to": match.group("place").strip(), "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))
        return events, ""

    return [], text
