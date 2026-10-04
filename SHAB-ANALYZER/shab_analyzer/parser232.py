from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_MANAGERS_SIGNING_REVOKED_AND_LIQUIDATOR = re.compile(
    r"^Les associés\s+(?P<manager1>[^,.;]+?)\s+et\s+"
    r"(?P<manager2>[^,.;]+?),\s*dont la signature est radiée,\s*"
    r"restent gérants\.\s*La gérante\s+(?P<liquidator>[^,.;]+?)\s+"
    r"est élue liquidatrice(?:\s+avec signature individuelle)?\.?$",
    re.I | re.UNICODE,
)
_DE_PROVISIONAL_MORATORIUM_EXTENSION_NATURAL_DATE = re.compile(
    r"^Mit Verfügung vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+im summarischen Verfahren eine Verlängerung der "
    r"provisorischen Nachlassstundung bis zum\s+"
    r"(?P<until>\d{1,2}\.\s+[A-Za-zÀ-ÿ]+\s+\d{4})\s+gewährt\.?$",
    re.I | re.UNICODE,
)
_IT_NEW_COMPANY_NAME_RESIDUE = re.compile(
    r"^Nuova ditta:\s*(?P<name>(?![^.;]*\bin liquidazione\b)[^.;]+?)\.?$",
    re.I | re.UNICODE,
)
_DE_SHAREHOLDER_NOTICE_AND_STATUTES_CROSS_LANGUAGE = re.compile(
    r"^Mitteilung an die Aktionäre neu:\s*(?P<methods>.+?)\.\s*"
    r"Statuten geändert am\s+(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_OTHER_ADDRESS_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription no\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que l['’]autre "
    r"adresse exacte est:\s*(?P<street>[^,]+),\s*"
    r"(?P<post_office_box>Case Postale\s+\d+),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_PROCURATION_EXTINGUISHED = re.compile(
    r"^La procuration de\s+(?P<name>[^,.;]+?)\s+est éteinte\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_DOMICILE_SHARE_TRANSFER_NEW_PRESIDENT = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+),\s*désormais de\s+"
    r"(?P<seller_origin>.+?)\s+à\s+(?P<seller_place>[^,.;]+),\s*cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<buyer_origin>[^,.;]+),\s*à\s+"
    r"(?P<buyer_place>[^,.;]+),\s*nouvel associé avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*gérant président"
    r"(?:\s+avec signature individuelle)?\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_PROXY_REVOKED_COLLECTIVE_SIGNING = re.compile(
    r"^(?P<name>[^,.;]+),\s*lequel est maintenant à\s+"
    r"(?P<place>[^,.;]+)\s+et dont la procuration collective à deux est "
    r"éteinte,\s*engage désormais la succursale par une signature "
    r"collective à deux\.?$",
    re.I | re.UNICODE,
)
_DE_SEAT_TRANSFER_OMISSION_SUPPLEMENT = re.compile(
    r"^Anlässlich der Sitzverlegung wurde der folgende Eintrag nicht "
    r"übertragen,\s*weshalb nun ein Nachtrag erfolgt\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_BOARD_MEMBERS = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<country1>[A-Z]{1,3}),\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+)\s+et\s+"
    r"(?P<name3>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+),\s*"
    r"sont membres du conseil d['’]administration"
    r"(?:,\s*avec signature collective à deux)?\.?$",
    re.I | re.UNICODE,
)
_FR_COMMITTEE_MEMBER_SAME_ORIGIN_AND_PLACE = re.compile(
    r"^(?P<name>[^,.;]+),\s*de et à\s+(?P<place>[^,.;]+),\s*"
    r"est membre du comité(?:\s+avec signature collective à deux)?\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_PRESIDENT_APPOINTED_LIQUIDATOR = re.compile(
    r"^(?P<name>[^,.;]+),\s*gérante et présidente,\s*"
    r"est nommée liquidatrice(?:\s+avec signature individuelle)?\.?$",
    re.I | re.UNICODE,
)
_FR_HEAD_OFFICE_AFTER_MERGER = re.compile(
    r"^Nouvel établissement principal par suite de fusion:\s*"
    r"(?P<name>.+?)\s*\((?P<registry_id>CR No\.\s*[\d.]+)\),\s*à\s+"
    r"(?P<place>[^()]+?)\s*\((?P<country>[^()]+)\)\.\s*"
    r"Enregistrement de l['’]établissement principal:\s*"
    r"(?P<registration>.+?)\.\s*Nature juridique nouvelle de "
    r"l['’]établissement principal:\s*(?P<legal_form>.+?)\.\s*"
    r"Capital nouveau de l['’]établissement principal:\s*"
    r"(?P<currency>[A-Z]{3})\s+(?P<capital>[\d'.]+),\s*entièrement "
    r"libéré\.\s*Radiation d['’]office selon l['’]art\.\s*110 ORC de "
    r"la mention\s+[\"“](?P<removed_mention>.+?)[\"”]\.?$",
    re.I | re.UNICODE,
)
_FR_ORGANIZATION_SHARE_TRANSFER_AND_THREE_MANAGERS = re.compile(
    r"^L['’]associé\s+(?P<seller>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts sociales "
    r"de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+[\"“](?P<buyer>.+?)[\"”]\s*"
    r"\((?P<buyer_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<buyer_place>[^,.;]+),\s*nouvelle associée\.\s*Gérants:\s*"
    r"(?P=seller),\s*nommé président,\s*"
    r"(?P<manager1>[^,.;]+),\s*à\s+(?P<manager1_place>[^,.;]+),\s*"
    r"secrétaire,\s*et\s+(?P<manager2>[^,.;]+),\s*à\s+"
    r"(?P<manager2_place>[^,.;]+),\s*tous deux de\s+"
    r"(?P<manager_origin>[^,.;]+),\s*lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_ADJUSTED_AND_OLD_CLAUSE_REMOVED = re.compile(
    r"^Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+den Beschluss über die "
    r"Ermächtigung einer genehmigten Kapitalerhöhung vom\s+"
    r"(?P<authorization_date>\d{2}\.\d{2}\.\d{4})\s+gemäss näherer "
    r"Umschreibung in den Statuten angepasst\.\s*\.\s*\[Die statutarische "
    r"Bestimmung über die Ermächtigung einer genehmigten Kapitalerhöhung "
    r"vom\s+(?P<removed_date>\d{2}\.\d{2}\.\d{4})\s+wurde gestrichen\.\]\s*"
    r"\[gestrichen:\s*Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P=removed_date)\s+eine genehmigte Kapitalerhöhung gemäss näherer "
    r"Umschreibung in den Statuten eingeführt\.\s*\]\.?$",
    re.I | re.UNICODE,
)
_DE_INCOMING_SPIN_OFF_CURRENCY_DUPLICATED = re.compile(
    r"^Abspaltung:\s*Die Gesellschaft übernimmt von der\s+(?P<source>.+?),\s*"
    r"in\s+(?P<source_place>[^()]+?)\s*"
    r"\((?P<source_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*einen Teil des "
    r"Vermögens\.\s*Die Gesellschaft übernimmt dabei gemäss Spaltungsvertrag "
    r"vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von\s+"
    r"(?P<prefix_currency>[A-Z]{3})\s+(?P<currency>[A-Z]{3})\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von\s+"
    r"(?P=prefix_currency)\s+(?P=currency)\s+(?P<liabilities>[\d'.]+)\.\s*"
    r"Da die Alleinaktionärin der übertragenden mit der Alleinaktionärin der "
    r"übernehmenden Gesellschaft identisch ist,\s*erfolgt weder eine "
    r"Kapitalerhöhung noch eine Zuteilung von Aktien\.?$",
    re.I | re.UNICODE,
)


_DE_MONTHS = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _german_date(raw: str) -> str:
    day, month, year = raw.casefold().replace(".", "", 1).split()
    return f"{int(year):04d}-{_DE_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", "").replace(".", ""))


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
        role=role.strip() if role else None,
        signing=signing,
        payload={
            "name": clean_name,
            "place": clean_place,
            **({"uid": uid} if uid else {}),
            **(extra or {}),
        },
    )


def extract_parser232_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 232."""
    del language  # Historical publications regularly contain another language.
    leftover = text.strip()

    match = _FR_MANAGERS_SIGNING_REVOKED_AND_LIQUIDATOR.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.managers_signing_revoked_and_liquidator.v1"
        events = [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id,
                match.group(f"manager{index}"), role="gérant", extra={
                    "action": "signing_revoked", "signing_revoked": True,
                    "role_continues": True,
                },
            )
            for index in (1, 2)
        ]
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("liquidator"),
            role="gérante, liquidatrice", signing="Einzelunterschrift",
            extra={"action": "appointed_liquidator", "previous_role": "gérante"},
        ))
        return events, ""

    match = _DE_PROVISIONAL_MORATORIUM_EXTENSION_NATURAL_DATE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.provisional_moratorium_extended_natural_date.v1", {
                "kind": "composition_moratorium_extended", "action": "extended",
                "moratorium_type": "provisional",
                "decision_date": _iso_date(match.group("decision_date")),
                "until": _german_date(match.group("until")),
                "authority": match.group("authority").strip(),
                "procedure": "summarisch",
            },
        )], ""

    match = _IT_NEW_COMPANY_NAME_RESIDUE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_name_changed", "it.text.new_company_name_residue.v1", {
                "kind": "company_name", "action": "changed",
                "to": match.group("name").strip(),
            },
        )], ""

    match = _DE_SHAREHOLDER_NOTICE_AND_STATUTES_CROSS_LANGUAGE.fullmatch(leftover)
    if match:
        rule_id = "de.text.shareholder_notice_and_statutes_cross_language.v1"
        methods = [
            method.strip()
            for method in re.split(r"\s+oder\s+", match.group("methods"), flags=re.I)
        ]
        date = _iso_date(match.group("date"))
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id, {
                    "kind": "communications", "action": "changed",
                    "recipients": "shareholders", "methods": methods,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id, {"date": date},
            ),
        ], ""

    match = _FR_OTHER_ADDRESS_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.other_address_corrected.v1", {
                "kind": "other_address", "action": "corrected",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
                "street": match.group("street").strip(),
                "post_office_box": match.group("post_office_box").strip(),
                "postal_code": match.group("postal_code"),
                "place": match.group("place").strip(),
            },
        )], ""

    match = _FR_PROCURATION_EXTINGUISHED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.procuration_extinguished.v1",
            match.group("name"), extra={
                "action": "procuration_revoked", "previous_signing": "procuration",
                "procuration_revoked": True,
            },
        )], ""

    match = _FR_MANAGER_DOMICILE_SHARE_TRANSFER_NEW_PRESIDENT.fullmatch(leftover)
    if match:
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        if (
            match.group("nominal") == match.group("buyer_nominal")
            and transferred <= before
            and transferred == buyer_count
        ):
            rule_id = "fr.persons.manager_domicile_share_transfer_new_president.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            common = {
                "share_nominal": match.group("nominal"), "currency": "CHF",
                "shares_transferred": transferred,
            }
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller,
                    place=match.group("seller_place"), role="associé-gérant",
                    extra={
                        **common, "action": "shares_transferred_and_domicile_changed",
                        "origin": match.group("seller_origin").strip(),
                        "counterparty": buyer, "shares_before": before,
                        "shares_count": before - transferred,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer,
                    place=match.group("buyer_place"),
                    role="associé-gérant président", signing="Einzelunterschrift",
                    extra={
                        **common, "action": "appointed_and_shares_received",
                        "origin": match.group("buyer_origin").strip(),
                        "counterparty": seller, "shares_received": transferred,
                        "shares_count": buyer_count, "new_associate": True,
                    },
                ),
            ], ""

    match = _FR_BRANCH_PROXY_REVOKED_COLLECTIVE_SIGNING.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.branch_proxy_replaced_by_collective_signing.v1",
            match.group("name"), place=match.group("place"),
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "domicile_and_signing_changed", "scope": "branch",
                "previous_signing": "procuration collective à deux",
                "previous_procuration_revoked": True,
            },
        )], ""

    match = _DE_SEAT_TRANSFER_OMISSION_SUPPLEMENT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.seat_transfer_omission_supplement.v1", {
                "kind": "omitted_entry_supplement", "action": "supplemented",
                "context": "seat_transfer",
            },
        )], ""

    match = _FR_THREE_BOARD_MEMBERS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.three_board_members.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role="membre du conseil d'administration",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group(f"origin{index}").strip(),
                    **(
                        {"country": match.group("country1")}
                        if index == 1 else {}
                    ),
                },
            )
            for index in (1, 2, 3)
        ], ""

    match = _FR_COMMITTEE_MEMBER_SAME_ORIGIN_AND_PLACE.fullmatch(leftover)
    if match:
        place = match.group("place").strip()
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.committee_member_same_origin_place.v1",
            match.group("name"), place=place, role="membre du comité",
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "appointed", "origin": place,
            },
        )], ""

    match = _FR_MANAGER_PRESIDENT_APPOINTED_LIQUIDATOR.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.manager_president_appointed_liquidator.v1",
            match.group("name"), role="gérante, présidente, liquidatrice",
            signing="Einzelunterschrift", extra={
                "action": "appointed_liquidator",
                "previous_roles": ["gérante", "présidente"],
            },
        )], ""

    match = _FR_HEAD_OFFICE_AFTER_MERGER.fullmatch(leftover)
    if match:
        rule_id = "fr.text.head_office_after_merger.v1"
        common = {"scope": "head_office", "name": match.group("name").strip()}
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id, {
                    **common, "kind": "head_office", "action": "changed_after_merger",
                    "registry_id": match.group("registry_id"),
                    "place": match.group("place").strip(),
                    "country": match.group("country"),
                    "registration": match.group("registration").strip(),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id, {
                    **common, "kind": "legal_form", "action": "changed",
                    "legal_form": match.group("legal_form").strip(),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    **common, "kind": "head_office_capital", "action": "changed",
                    "currency": match.group("currency"),
                    "capital": match.group("capital"), "fully_paid": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_name_changed", rule_id, {
                    **common, "kind": "branch_trade_name", "action": "removed",
                    "removed_mention": match.group("removed_mention").strip(),
                    "legal_basis": "Art. 110 ORC", "automatic": True,
                },
            ),
        ], ""

    match = _FR_ORGANIZATION_SHARE_TRANSFER_AND_THREE_MANAGERS.fullmatch(leftover)
    if match:
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        if transferred <= before:
            rule_id = "fr.persons.organization_share_transfer_and_three_managers.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            common = {
                "share_nominal": match.group("nominal"), "currency": "CHF",
                "shares_transferred": transferred,
            }
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller,
                    role="associé-gérant président", signing="Einzelunterschrift",
                    extra={
                        **common, "action": "shares_transferred_and_appointed_president",
                        "counterparty": buyer, "shares_before": before,
                        "shares_count": before - transferred,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer,
                    place=match.group("buyer_place"), uid=match.group("buyer_uid"),
                    role="associée", extra={
                        **common, "action": "shares_received", "counterparty": seller,
                        "shares_received": transferred, "shares_count": transferred,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("manager1"),
                    place=match.group("manager1_place"), role="gérant secrétaire",
                    signing="Einzelunterschrift", extra={
                        "action": "appointed", "origin": match.group("manager_origin").strip(),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("manager2"),
                    place=match.group("manager2_place"), role="gérant",
                    signing="Einzelunterschrift", extra={
                        "action": "appointed", "origin": match.group("manager_origin").strip(),
                    },
                ),
            ], ""

    match = _DE_AUTHORIZED_CAPITAL_ADJUSTED_AND_OLD_CLAUSE_REMOVED.fullmatch(leftover)
    if match:
        rule_id = "de.text.authorized_capital_adjusted_and_old_clause_removed.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_increase", "action": "authorization_adjusted",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "authorization_date": _iso_date(match.group("authorization_date")),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_increase", "action": "authorization_removed",
                    "authorization_date": _iso_date(match.group("removed_date")),
                },
            ),
        ], ""

    match = _DE_INCOMING_SPIN_OFF_CURRENCY_DUPLICATED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.incoming_spin_off_currency_duplicated.v1", {
                "kind": "spin_off_acquisition", "action": "assets_assumed",
                "source": match.group("source").strip(),
                "source_place": match.group("source_place").strip(),
                "source_uid": match.group("source_uid"),
                "agreement_date": _iso_date(match.group("date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "currency": match.group("currency"),
                "source_currency_prefix": match.group("prefix_currency"),
                "same_sole_shareholder": True,
                "capital_increase": False, "share_allocation": False,
            },
        )], ""

    return [], leftover
