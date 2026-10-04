from __future__ import annotations

import re
from decimal import Decimal

from .keys import person_key
from .models import Event


_DE_ASSET_TRANSFER_FIXED_VARIABLE_CONSIDERATION = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\??\s*"
    r"Gegenleistung:\s*CHF\s+(?P<fixed>[\d'.]+)\s+fixe Gegenleistung sowie "
    r"weitere maximal CHF\s+(?P<variable>[\d'.]+)\s+gemäss vertraglicher "
    r"Preisanpassungsklausel\s*\(variable Gegenleistung\)\.?$",
    re.I | re.UNICODE,
)
_IT_SUPPLEMENT_REFERENCE = re.compile(
    r"^\[Complemento all['’]iscrizione no\.\s*(?P<entry>[\d']+)\s+del\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+pubblicata sul FUSC no\.\s*"
    r"(?P<issue>\d+)\s+del\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4})\.\]$",
    re.I | re.UNICODE,
)
_FR_NO_ANCILLARY_OBLIGATIONS_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(publication FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+page\s+"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que les statuts "
    r"de la société ne prévoient aucune prestation accessoire\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_TO_MANAGER_PRESIDENT = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*d['’]"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé-gérant "
    r"et président avec signature individuelle\.\s*(?P=seller)\s+reste "
    r"titulaire de\s+(?P<remaining>[\d']+)\s+part(?:s)? de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_NEW_MANAGERS_INDIVIDUAL = re.compile(
    r"^Nouveaux gérants:\s*(?P<name1>[^,.;]+),\s*de\s+"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*avec signature individuelle\.?$",
    re.I | re.UNICODE,
)
_DE_EX_OFFICIO_DELETION_ENTRY_REMOVED = re.compile(
    r"^\[gestrichen:\s*Nachdem kein begründeter Einspruch gegen die Löschung "
    r"erhoben wurde,\s*wird die Gesellschaft im Sinne von\s+"
    r"(?P<legal_basis>Art\.\s*159 Abs\.\s*5 lit\.\s*a HRegV)\s+von Amtes "
    r"wegen gelöscht\.\]$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_NAME_CORRECTED_NOTICE = re.compile(
    r"^Rectificatif:\s*l['’]inscription\s+(?:no|n°)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s*,?\s*p?\.?\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le directeur "
    r"se nomme\s+(?P<name>[^()]+?)\s*\(et non\s+"
    r"(?P<previous_name>[^)]+?)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATION_BANKRUPTCY_OPENED = re.compile(
    r"^La faillite de l['’]association a été prononcée par jugement du\s+"
    r"(?P<authority>.+?)\s+du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"avec effet à partir du\s+(?P<effective_date>\d{2}\.\d{2}\.\d{4})\s+à\s+"
    r"(?P<time>\d{1,2}:\d{2})\.\s*Par conséquent,\s*son nom devient:\s*"
    r"(?P<name>.+?,\s*en liquidation)\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_FOUNDATION_MEMBER_CONTINUES = re.compile(
    r"^(?P<name>[^,.;]+),\s*jusqu['’]ici président,\s*reste seul membre du "
    r"conseil de fondation et continue de signer individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_REGISTERED_SHARE_COUNT_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que le "
    r"nouveau capital-actions de CHF\s+(?P<total>[\d']+,\s*\d+)\s+est formé de\s+"
    r"(?P<count>[\d']+)\s+actions de CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"nominatives\s*\(et non de\s+(?P<previous_count>[\d']+)\s+actions\)\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_ADDED_AFTER_REMOVED_FRAGMENT = re.compile(
    r"^\]\.?\s*(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s*"
    r"\(HR\s+(?P<register_canton>[A-Z]{2})\)\.?$",
    re.I | re.UNICODE,
)
_FR_MOVED_MANAGER_TRANSFER_TO_MANAGER_PRESIDENT = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+),\s*lequel est désormais à\s+"
    r"(?P<seller_place>[^,.;]+),\s*cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<buyer_place>[^,.;]+),\s*nouvel associé "
    r"avec\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*gérant président avec signature "
    r"individuelle;\s*(?P=seller)\s+reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_REMAINS_WITH_SIGNING_EXCLUSION = re.compile(
    r"^Rectificatif:\s*l['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+),\s*d['’](?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+(?:\s*\([^)]+\))?),\s*reste adminsitrateur avec "
    r"signature collective à deux,\s*toutefois pas avec\s+"
    r"(?P<excluded>[^()]+?)\s*\(\s*n['’]est pas radié à l['’]instar de son "
    r"droit de signature,\s*contrairement au texte publié\)\.?$",
    re.I | re.UNICODE,
)
_DE_DEBT_OFFSET_CAPITAL_INCREASE = re.compile(
    r"^Bei der ordentlichen Kapitalerhöhung vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+werden Forderungen in der Höhe von CHF\s+"
    r"(?P<claim>[\d'.]+)\s+verrechnet,\s*wofür\s+(?P<count>[\d']+)\s+"
    r"(?P<share_kind>Namenaktien) zu CHF\s+(?P<nominal>[\d'.]+)\s+"
    r"ausgegeben werden\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_BOARD_ROLES_CORRECTED_CONTINUE_SIGNING = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*jusqu['’]ici président,\s*nommé secrétaire,\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*(?P<country2>[A-Z]{2,3}),\s*jusqu['’]ici "
    r"secrétaire,\s*sont toujours membres du conseil d['’]administration et "
    r"continuent à signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_BOARD_MEMBERS_RESTRICTED_SIGNING = re.compile(
    r"^(?P<name1>[^,.;]+),\s*de et à\s+(?P<place1>[^,.;]+)\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*sont membres du conseil d['’]administration,\s*"
    r"avec signature collective à deux,\s*avec le président ou le "
    r"vice-président\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _money(raw: str) -> Decimal:
    return Decimal(raw.replace("'", "").replace(" ", "").replace(",", "."))


def _normalized_money(raw: str) -> str:
    return raw.replace(" ", "").replace(",", ".")


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


def extract_parser204_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 204."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_ASSET_TRANSFER_FIXED_VARIABLE_CONSIDERATION.fullmatch(leftover)
    if match and _money(match.group("fixed")) + _money(match.group("variable")) == _money(
        match.group("assets")
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_fixed_variable_consideration.v1", {
                "source_kind": "company", "agreement_date": _iso_date(match.group("date")),
                "assets": match.group("assets"), "liabilities": None, "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration_kind": "fixed_and_variable_cash",
                "fixed_consideration": match.group("fixed"),
                "maximum_variable_consideration": match.group("variable"),
                "variable_consideration_basis": "contractual_price_adjustment_clause",
            },
        )], ""

    match = _IT_SUPPLEMENT_REFERENCE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "it.text.supplement_reference.v1", {
                "action": "supplemented", "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "issue": match.group("issue"),
                "notice_date": _iso_date(match.group("notice_date")),
            },
        )], ""

    match = _FR_NO_ANCILLARY_OBLIGATIONS_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.no_ancillary_obligations_corrected.v1", {
                "kind": "ancillary_obligations", "action": "publication_corrected",
                "ancillary_obligations": False, "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_MANAGER_TRANSFER_TO_MANAGER_PRESIDENT.fullmatch(leftover)
    if match and (
        _count(match.group("before")) - _count(match.group("transferred"))
        == _count(match.group("remaining"))
        and match.group("nominal") == match.group("remaining_nominal")
    ):
        rule_id = "fr.persons.manager_transfer_to_manager_president.v2"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant", extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")), **common,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé-gérant et président", signing="Einzelunterschrift", extra={
                    "action": "appointed_and_shares_received", "counterparty": seller,
                    "heimat": match.group("origin").strip(),
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("transferred")), **common,
                },
            ),
        ], ""

    match = _FR_TWO_NEW_MANAGERS_INDIVIDUAL.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_new_managers_individual.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="gérant",
                signing="Einzelunterschrift", extra={
                    "action": "appointed", "heimat": match.group(f"origin{index}").strip(),
                },
            )
            for index in (1, 2)
        ], ""

    match = _DE_EX_OFFICIO_DELETION_ENTRY_REMOVED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.ex_officio_deletion_entry_removed.v1", {
                "kind": "deletion_entry", "action": "historical_entry_removed",
                "ex_officio": True, "legal_basis": match.group("legal_basis"),
            },
        )], ""

    match = _FR_DIRECTOR_NAME_CORRECTED_NOTICE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.director_name_corrected_notice.v2",
            match.group("name"), role="directeur", extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_ASSOCIATION_BANKRUPTCY_OPENED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.association_bankruptcy_opened.v1", {
                "kind": "bankruptcy_opened", "entity": "association",
                "decision_date": _iso_date(match.group("decision_date")),
                "effective_date": _iso_date(match.group("effective_date")),
                "effective_time": match.group("time"),
                "authority": match.group("authority").strip(),
                "company_name": match.group("name").strip(), "in_liquidation": True,
            },
        )], ""

    match = _FR_SOLE_FOUNDATION_MEMBER_CONTINUES.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.sole_foundation_member_continues.v1",
            match.group("name"), role="seul membre du conseil de fondation",
            signing="Einzelunterschrift", extra={
                "action": "role_changed", "previous_role": "président",
                "signing_continues": True,
            },
        )], ""

    match = _FR_REGISTERED_SHARE_COUNT_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.registered_share_count_corrected.v1", {
                "kind": "share_structure", "action": "corrected",
                "total": _normalized_money(match.group("total")), "currency": "CHF",
                "shares_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"),
                "share_kind": "actions nominatives",
                "previous_published_shares_count": _count(match.group("previous_count")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _DE_BRANCH_ADDED_AFTER_REMOVED_FRAGMENT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_added_after_removed_fragment.v1", {
                "action": "added", "place": match.group("place").strip(),
                "branch_uid": match.group("uid"),
                "register_canton": match.group("register_canton").upper(),
            },
        )], ""

    match = _FR_MOVED_MANAGER_TRANSFER_TO_MANAGER_PRESIDENT.fullmatch(leftover)
    if match and (
        _count(match.group("before")) - _count(match.group("transferred"))
        == _count(match.group("remaining"))
        and _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and len({
            match.group("nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }) == 1
    ):
        rule_id = "fr.persons.moved_manager_transfer_to_manager_president.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, place=match.group("seller_place"),
                role="associé-gérant", extra={
                    "action": "domicile_changed_and_shares_transferred",
                    "counterparty": buyer, "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")), **common,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("buyer_place"),
                role="associé-gérant et président", signing="Einzelunterschrift", extra={
                    "action": "appointed_and_shares_received", "counterparty": seller,
                    "heimat": match.group("origin").strip(),
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")), **common,
                },
            ),
        ], ""

    match = _FR_ADMINISTRATOR_REMAINS_WITH_SIGNING_EXCLUSION.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_remains_signing_exclusion.v1",
            match.group("name"), place=match.group("place"), role="administrateur",
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "erroneous_removal_corrected",
                "heimat": match.group("origin").strip(),
                "signing_excluded_with": match.group("excluded").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _DE_DEBT_OFFSET_CAPITAL_INCREASE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.debt_offset_capital_increase.v1", {
                "kind": "ordinary_capital_increase", "action": "shares_issued",
                "date": _iso_date(match.group("date")),
                "contribution_kind": "debt_offset",
                "claim": match.group("claim"), "currency": "CHF",
                "issued_shares": [{
                    "count": _count(match.group("count")),
                    "nominal": match.group("nominal"), "currency": "CHF",
                    "kind": match.group("share_kind"),
                }],
            },
        )], ""

    match = _FR_TWO_BOARD_ROLES_CORRECTED_CONTINUE_SIGNING.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_board_roles_corrected_continue_signing.v1"
        reference = {
            "action": "role_corrected", "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "signing_continues": True,
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"),
                role="secrétaire et membre du conseil d'administration",
                signing="Kollektivunterschrift zu zweien", extra={
                    **reference, "previous_role": "président",
                    "heimat": match.group("origin1").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="membre du conseil d'administration",
                signing="Kollektivunterschrift zu zweien", extra={
                    **reference, "previous_role": "secrétaire",
                    "heimat": match.group("origin2").strip(),
                    "country": match.group("country2"),
                },
            ),
        ], ""

    match = _FR_TWO_BOARD_MEMBERS_RESTRICTED_SIGNING.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_board_members_restricted_signing.v1"
        people = (
            (match.group("name1"), match.group("place1"), match.group("place1")),
            (match.group("name2"), match.group("place2"), match.group("origin2")),
        )
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, name, place=place,
                role="membre du conseil d'administration",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "heimat": origin.strip(),
                    "signing_with": "président ou vice-président",
                },
            )
            for name, place, origin in people
        ], ""

    return [], leftover
