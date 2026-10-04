from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_SHAB_CITATION_CORRECTED = re.compile(
    r"^Mit dem im SHAB-Nr\.\s*(?P<wrong_issue>\d+) vom "
    r"(?P<wrong_date>\d{2}\.\d{2}\.\d{4}) publizierten TR-Eintrag "
    r"(?P<entry>\d+)/(?P<entry_year>\d{4}) wurde das falsche SHAB-Zitat "
    r"publiziert\.\s*Korrekt wäre:\s*\(SHAB Nr\.\s*(?P<issue>\d+) vom "
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Publ\.\s*"
    r"(?P<publication_ref>\d+)\)\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_NO_CAPITAL_SAFEGUARD = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di (?P<absorbed_name>.+?),\s*"
    r"in (?P<absorbed_place>[^()]+?)\s*\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"secondo il contratto di fusione del (?P<agreement_date>\d{2}\.\d{2}\.\d{4}) "
    r"e bilancio al (?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta "
    r"attivi per CHF (?P<assets>[\d'.]+) e passivi verso terzi per CHF "
    r"(?P<liabilities>[\d'.]+)\s*\.\s*La fusione avviene senza aumento di "
    r"capitale e senza attribuzione di azioni,\s*poiché un aumento di capitale "
    r"non è necessario alla salvaguardia dei diritti dei soci della società "
    r"trasferente\.?$",
    re.I | re.UNICODE,
)
_DE_QUALIFIED_FACT_HEADING_CORRECTED = re.compile(
    r'^Fälschlicherweise wurde im Tagesregistertext der Tatbestand der '
    r'beabsichtigten Sachübernahme unter dem Titel ["“](?P<wrong_heading>Genusscheine)["”] '
    r'publiziert,\s*statt unter den Titel ["“](?P<heading>qualifizierte Tatbestände)["”]\.\s*'
    r'Der Handelsregisterauszug bleibt unverändert korrekt\.?$',
    re.I | re.UNICODE,
)
_DE_REMOVED_BRANCH_REGISTER_RESIDUE = re.compile(
    r"^\(HR\s+(?P<register_canton>[A-Z]{2})\)\]$",
    re.I | re.UNICODE,
)
_DE_ASSOCIATION_DISSOLVED_BOARD_IMPOSSIBLE = re.compile(
    r"^Name neu:\s*(?P<name>.+? in Liquidation)\.\s*Eintragung von Amtes wegen\.\s*"
    r"Der Verein ist gemäss (?P<legal_basis>Art\.\s*77 ZGB) von Gesetztes wegen "
    r"aufgelöst,\s*weil der Vorstand nicht mehr statutengemäss bestellt werden kann\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_TRANSFER_TO_NEW_MANAGER = re.compile(
    r"^Les associés-gérants (?P<seller1>[^,.;]+?) et (?P<seller2>[^,.;]+?) "
    r"cèdent chacun (?P<transferred>[\d']+) de leur (?P<before>[\d']+) parts de CHF "
    r"(?P<nominal>[\d'.]+) à (?P<buyer>[^,.;]+),\s*d['’](?P<origin>[^,.;]+),\s*"
    r"à (?P<place>[^,.;]+),\s*nouvel associé avec (?P<buyer_count>[\d']+) parts "
    r"de CHF (?P<buyer_nominal>[\d'.]+),\s*gérant avec signature "
    r"(?P<signing>collective à deux|individuelle)\.\s*(?P=seller1) et "
    r"(?P=seller2) restent titulaires de (?P<remaining>[\d']+) parts de CHF "
    r"(?P<remaining_nominal>[\d'.]+) chacun\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_GIVEN_NAME_CORRECTED = re.compile(
    r"^Rectificatif:\s*L['’]inscription n°\s*(?P<entry>[\d']+) du "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) \(FOSC du "
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\) est rectifiée en ce sens que le prénom exact du "
    r"(?P<role>directeur) (?P<previous_name>[^.;]+?) est (?P<name>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_ADDRESS_AUDITOR_WAIVER_REVOKED = re.compile(
    r"^Vollständige Adresse:\s*(?P<street>.+?)\s+(?P<house>\d+[A-Za-z]?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<place>[^.]+)\.\s*Die Erklärung vom "
    r"(?P<waiver_date>\d{2}\.\d{2}\.\d{4}) über den Verzicht auf die "
    r"eingeschränkte Revision ist gelöscht worden\.\s*Neue Revisionsstelle:\s*"
    r"(?P<auditor>.+?)\s*\((?P<auditor_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"in (?P<auditor_place>[^.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_STATUTES_DATE_CAPITAL_CORRECTED = re.compile(
    r"^Irrtümlich wurde Statutendatum (?P<previous_date>\d{2}\.\d{2}\.\d{4}) "
    r"publiziert\.\s*Richtig ist:\s*(?P<date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"Bei der ordentlichen Kapitalerhöhung vom (?P<capital_date>\d{2}\.\d{2}\.\d{4}) "
    r"wird frei verwendbares Eigenkapital in der Höhe von CHF "
    r"(?P<amount>[\d'.]+) umgewandelt\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_TO_MANAGER = re.compile(
    r"^L['’]associée (?P<seller>[^,.;]+) cède (?P<transferred>[\d']+) de ses "
    r"(?P<before>[\d']+) parts de CHF (?P<nominal>[\d'.]+) à l['’]associé-gérant "
    r"(?P<buyer>[^,.;]+),\s*désormais titulaire (?P<buyer_count>[\d']+) parts de CHF "
    r"(?P<buyer_nominal>[\d'.]+);\s*(?P=seller) reste titulaire de "
    r"(?P<remaining>[\d']+) parts de CHF (?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_SPLIT_TRANSFER_TWO_ASSOCIATES = re.compile(
    r"^L['’]associée-gérante (?P<seller>[^,.;]+) cède (?P<transferred>[\d']+) de ses "
    r"(?P<before>[\d']+) parts de CHF (?P<nominal>[\d'.]+),\s*par "
    r"(?P<count1>[\d']+) parts à (?P<buyer1>[^,.;]+),\s*de (?P<origin1>[^,.;]+),\s*"
    r"à (?P<place1>[^,.;]+),\s*et par (?P<count2>[\d']+) parts à "
    r"(?P<buyer2>[^,.;]+),\s*d['’](?P<origin2>[^,.;]+),\s*à (?P<place2>[^,.;]+),\s*"
    r"nouveaux associés avec (?P<buyer_count>[\d']+) parts de CHF "
    r"(?P<buyer_nominal>[\d'.]+) chacun,\s*tous deux avec signature "
    r"(?P<signing>collective à deux|individuelle)\.\s*(?P=seller) est désormais "
    r"titulaire de (?P<remaining>[\d']+) parts de CHF "
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_CONDITIONAL_CAPITAL_ADJUSTED_AND_CREATED = re.compile(
    r"^Die Generalversammlung hat mit Beschluss vom "
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}) die Statutenbestimmung über die "
    r"bedingte Kapitalerhöhung vom (?P<original_date>\d{2}\.\d{2}\.\d{4}) "
    r"angepasst\.\s*\.\s*Die Generalversammlung hat mit Beschluss vom "
    r"(?P<created_date>\d{2}\.\d{2}\.\d{4}) eine bedingte Kapitalerhöhung "
    r"gemäss näherer Umschreibung in den Statuten eingeführt\.?$",
    re.I | re.UNICODE,
)
_DE_LIABILITY_HEADING_RESIDUE = re.compile(
    r"^Haftung/Nachschusspflicht neu:$",
    re.I | re.UNICODE,
)
_FR_MANAGER_DOMICILE_CORRECTED = re.compile(
    r"^L['’]inscription (?P<entry>[\d']+) du "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) \(publication FOSC du "
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}) page (?P<notice_ref>[\d/]+)\) "
    r"est rectifiée en ce sens que l['’](?P<role>associé-gérant) "
    r"(?P<name>[^,.;]+) est domicilié à (?P<place>[^()]+?)\s*"
    r"\(et non à (?P<previous_place>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_COMMITTEE_MEMBERS_WITHOUT_SIGNATURE = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*"
    r"à (?P<place1>[^,.;]+),\s*(?P<country1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*"
    r"à (?P<place2>[^,.;]+),\s*(?P<country2>[^,.;]+),\s*et "
    r"(?P<name3>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin3>[^,.;]+),\s*"
    r"à (?P<place3>[^,.;]+),\s*(?P<country3>[^,.;]+),\s*sont membres du comité "
    r"et ils n['’]exercent pas la signature sociale\.?$",
    re.I | re.UNICODE,
)
_DE_NO_STATUTES_CHANGE_CORRECTION = re.compile(
    r"^Im Tagesregistereintrag (?P<entry>[\d']+) vom "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) wurde irrtümlich publiziert,\s*"
    r"obwohl keine Statutenänderung erfolgte\.?$",
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
        payload={
            "name": clean_name,
            "place": clean_place,
            **({"uid": uid} if uid else {}),
            **(extra or {}),
        },
    )


def _share_payload(
    *,
    action: str,
    counterparty: str | None = None,
    counterparties: list[str] | None = None,
    before: int,
    transferred: int,
    count: int,
    nominal: str,
) -> dict:
    return {
        "action": action,
        **({"counterparty": counterparty} if counterparty else {}),
        **({"counterparties": counterparties} if counterparties else {}),
        "shares_before": before,
        "shares_transferred": transferred,
        "shares_count": count,
        "share_nominal": nominal,
        "currency": "CHF",
    }


def extract_parser183_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 183."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_SHAB_CITATION_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.shab_citation_corrected.v1", {
                "action": "notice_citation_corrected",
                "entry": match.group("entry"),
                "entry_year": int(match.group("entry_year")),
                "previous_issue": int(match.group("wrong_issue")),
                "previous_notice_date": _iso_date(match.group("wrong_date")),
                "issue": int(match.group("issue")),
                "notice_date": _iso_date(match.group("notice_date")),
                "publication_ref": match.group("publication_ref"),
            },
        )], ""

    match = _IT_MERGER_NO_CAPITAL_SAFEGUARD.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "it.text.merger_no_capital_safeguard.v1", {
                "kind": "absorption",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party",
                "currency": "CHF",
                "capital_increase": False,
                "shares_allocated": False,
                "transferor_members_rights_safeguarded": True,
            },
        )], ""

    match = _DE_QUALIFIED_FACT_HEADING_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.qualified_fact_heading_corrected.v1", {
                "action": "heading_corrected",
                "fact_kind": "intended_asset_acquisition",
                "previous_heading": match.group("wrong_heading"),
                "heading": match.group("heading"),
                "registry_extract_unchanged": True,
            },
        )], ""

    match = _DE_REMOVED_BRANCH_REGISTER_RESIDUE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.removed_branch_register_residue.v1", {
                "action": "removed",
                "register_canton": match.group("register_canton").upper(),
                "kind": "removed_branch_register_suffix",
            },
        )], ""

    match = _DE_ASSOCIATION_DISSOLVED_BOARD_IMPOSSIBLE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.association_dissolved_board_impossible.v2", {
                "kind": "dissolution",
                "scope": "association",
                "action": "dissolved",
                "company_name": match.group("name").strip(),
                "legal_basis": match.group("legal_basis"),
                "reason": "statutory_board_cannot_be_appointed",
                "by_operation_of_law": True,
                "registered_ex_officio": True,
            },
        )], ""

    match = _FR_TWO_MANAGERS_TRANSFER_TO_NEW_MANAGER.fullmatch(leftover)
    if match and (
        _count(match.group("before"))
        == _count(match.group("remaining")) + _count(match.group("transferred"))
        and _count(match.group("buyer_count")) == 2 * _count(match.group("transferred"))
        and len({
            match.group("nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }) == 1
    ):
        rule_id = "fr.persons.two_managers_transfer_to_new_manager.v1"
        sellers = [match.group("seller1").strip(), match.group("seller2").strip()]
        transferred = _count(match.group("transferred"))
        events = [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant",
                extra=_share_payload(
                    action="shares_transferred", counterparty=match.group("buyer").strip(),
                    before=_count(match.group("before")), transferred=transferred,
                    count=_count(match.group("remaining")), nominal=match.group("nominal"),
                ),
            )
            for seller in sellers
        ]
        signing = (
            "Kollektivunterschrift zu zweien"
            if match.group("signing").lower().startswith("collective")
            else "Einzelunterschrift"
        )
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("buyer"), place=match.group("place"),
            role="associé-gérant", signing=signing, extra={
                **_share_payload(
                    action="shares_received_and_appointed_manager", counterparties=sellers,
                    before=0, transferred=_count(match.group("buyer_count")),
                    count=_count(match.group("buyer_count")),
                    nominal=match.group("buyer_nominal"),
                ),
                "origin": match.group("origin").strip(), "new_associate": True,
            },
        ))
        return events, ""

    match = _FR_DIRECTOR_GIVEN_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.director_given_name_corrected.v1",
            match.group("name"), role=match.group("role"), extra={
                "action": "given_name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _DE_ADDRESS_AUDITOR_WAIVER_REVOKED.fullmatch(leftover)
    if match:
        rule_id = "de.text.address_auditor_waiver_revoked.v1"
        address = " ".join((match.group("street"), match.group("house")))
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", rule_id, {
                    "action": "full_address_recorded", "street": address,
                    "postal_code": match.group("postal_code"),
                    "place": match.group("place").strip(),
                    "address": f"{address}, {match.group('postal_code')} {match.group('place').strip()}",
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "audit_requirement_changed", rule_id, {
                    "kind": "limited_audit_waiver", "action": "removed",
                    "declaration_date": _iso_date(match.group("waiver_date")),
                    "limited_audit_waived": False,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("auditor"),
                place=match.group("auditor_place"), uid=match.group("auditor_uid"),
                role="Revisionsstelle", extra={"action": "appointed"},
            ),
        ], ""

    match = _DE_STATUTES_DATE_CAPITAL_CORRECTED.fullmatch(leftover)
    if match and match.group("date") == match.group("capital_date"):
        rule_id = "de.text.statutes_date_capital_corrected.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", rule_id, {
                    "action": "statutes_date_corrected",
                    "previous_date": _iso_date(match.group("previous_date")),
                    "date": _iso_date(match.group("date")),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "ordinary_capital_increase",
                    "date": _iso_date(match.group("capital_date")),
                    "source": "freely_available_equity",
                    "amount": match.group("amount"), "currency": "CHF",
                },
            ),
        ], ""

    match = _FR_ASSOCIATE_TRANSFER_TO_MANAGER.fullmatch(leftover)
    if match and (
        _count(match.group("before"))
        == _count(match.group("remaining")) + _count(match.group("transferred"))
        and _count(match.group("buyer_count")) >= _count(match.group("transferred"))
        and len({
            match.group("nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }) == 1
    ):
        rule_id = "fr.persons.associate_transfer_to_manager.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associée",
                extra=_share_payload(
                    action="shares_transferred", counterparty=buyer,
                    before=_count(match.group("before")), transferred=transferred,
                    count=_count(match.group("remaining")), nominal=match.group("nominal"),
                ),
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, role="associé-gérant",
                extra=_share_payload(
                    action="shares_received", counterparty=seller,
                    before=buyer_count - transferred, transferred=transferred,
                    count=buyer_count, nominal=match.group("buyer_nominal"),
                ),
            ),
        ], ""

    match = _FR_MANAGER_SPLIT_TRANSFER_TWO_ASSOCIATES.fullmatch(leftover)
    if match and (
        _count(match.group("transferred"))
        == _count(match.group("count1")) + _count(match.group("count2"))
        and _count(match.group("before"))
        == _count(match.group("remaining")) + _count(match.group("transferred"))
        and _count(match.group("count1")) == _count(match.group("buyer_count"))
        and _count(match.group("count2")) == _count(match.group("buyer_count"))
        and len({
            match.group("nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }) == 1
    ):
        rule_id = "fr.persons.manager_split_transfer_two_associates.v1"
        seller = match.group("seller").strip()
        buyers = [match.group("buyer1").strip(), match.group("buyer2").strip()]
        signing = (
            "Kollektivunterschrift zu zweien"
            if match.group("signing").lower().startswith("collective")
            else "Einzelunterschrift"
        )
        events = [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, seller, role="associée-gérante",
            extra=_share_payload(
                action="shares_transferred", counterparties=buyers,
                before=_count(match.group("before")),
                transferred=_count(match.group("transferred")),
                count=_count(match.group("remaining")), nominal=match.group("nominal"),
            ),
        )]
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"buyer{index}"),
                place=match.group(f"place{index}"), role="associé", signing=signing,
                extra={
                    **_share_payload(
                        action="shares_received", counterparty=seller, before=0,
                        transferred=_count(match.group(f"count{index}")),
                        count=_count(match.group("buyer_count")),
                        nominal=match.group("buyer_nominal"),
                    ),
                    "origin": match.group(f"origin{index}").strip(),
                    "new_associate": True,
                },
            ))
        return events, ""

    match = _DE_CONDITIONAL_CAPITAL_ADJUSTED_AND_CREATED.fullmatch(leftover)
    if match and match.group("decision_date") == match.group("created_date"):
        rule_id = "de.text.conditional_capital_adjusted_and_created.v1"
        decision_date = _iso_date(match.group("decision_date"))
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "conditional_capital_clause", "action": "adjusted",
                    "decision_date": decision_date,
                    "original_decision_date": _iso_date(match.group("original_date")),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "conditional_capital_clause", "action": "created",
                    "decision_date": decision_date, "details_in_statutes": True,
                },
            ),
        ], ""

    if _DE_LIABILITY_HEADING_RESIDUE.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "liability_changed", "de.text.liability_supplement_heading_residue.v1", {
                "kind": "member_personal_liability", "action": "removed",
                "personal_liability": False, "supplement": True,
                "heading": "Haftung/Nachschusspflicht neu",
            },
        )], ""

    match = _FR_MANAGER_DOMICILE_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.manager_domicile_corrected.v1",
            match.group("name"), place=match.group("place"), role=match.group("role"),
            extra={
                "action": "domicile_corrected",
                "previous_place": match.group("previous_place").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_THREE_COMMITTEE_MEMBERS_WITHOUT_SIGNATURE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.three_committee_members_without_signature.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="membre du comité",
                extra={
                    "action": "appointed", "origin": match.group(f"origin{index}").strip(),
                    "country": match.group(f"country{index}").strip(),
                    "without_signature": True,
                },
            )
            for index in (1, 2, 3)
        ], ""

    match = _DE_NO_STATUTES_CHANGE_CORRECTION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.no_statutes_change_correction.v1", {
                "action": "erroneous_no_change_notice_removed",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "statutes_changed": False,
            },
        )], ""

    return [], text
