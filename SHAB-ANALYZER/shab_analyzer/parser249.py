from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_TWO_FOUNDATION_MEMBERS_MIXED_ORIGIN = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*sans signature,\s*"
    r"et\s+(?P<name2>[^,.;]+),\s*de et à\s+(?P<place2>[^,.;]+),\s*"
    r"sans signature,\s*sont membres du conseil de fondation\.?$",
    re.I | re.UNICODE,
)
_DE_CAPITAL_BAND_RESTATED = re.compile(
    r"^Kapitalband gemäss näherer Umschreibung in den Statuten\.\s*"
    r"\[bisher:\s*Kapitalband gemäss näherer Umschreibung in den Statuten\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_ORIGIN_CHANGED_DIRECTOR_AND_BOARD_MEMBER = re.compile(
    r"^(?P<name1>[^,.;]+),\s*maintenant originaire de\s+"
    r"(?P<origin1>[^,.;]+),\s*jusqu['’]ici\s+(?P<previous_role1>[^,.;]+)\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"sont membres du conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_DE_PERSON_SIGNING_CHANGED = re.compile(
    r"^Eingetragene Person geändert:\s*(?P<name>[^,.;]+),\s*"
    r"(?P<previous_signing>Kollektivprokura zu zweien),\s*neu\s+"
    r"(?P<signing>Kollektivunterschrift zu zweien)\.?$",
    re.I | re.UNICODE,
)
_FR_NOTICE_TWO_ADMINISTRATORS_SIGNING = re.compile(
    r"^L['’]inscription no\.\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(publication FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+page\s+"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée en ce sens que\s+"
    r"(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+)\s+est administrateur "
    r"avec\s+(?:signature collective à deux avec\s+)?"
    r"(?P<with_person>[^,.;]+),\s*et\s+(?P<name2>[^,.;]+),\s*"
    r"de et à\s+(?P<place2>[^,.;]+)\s+est administrateur avec signature "
    r"collective à deux\.?$",
    re.I | re.UNICODE,
)
_FR_LIQUIDATORS_WITH_MANAGER_ROLES = re.compile(
    r"^Liquidateurs:\s*(?P<name1>[^,.;]+),\s*(?P<role1>gérante et présidente),\s*"
    r"et\s+(?P<name2>[^,.;]+),\s*(?P<role2>gérant),\s*lesquels continuent "
    r"de signer individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_NOMINATIVE_SHARE_SPLIT_UNRESTRICTED = re.compile(
    r"^Division des\s+(?P<before_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<before_nominal>[\d'.]+),\s*nominatives,\s*en\s+"
    r"(?P<after_count>[\d']+)\s+actions de CHF\s+(?P<after_nominal>[\d'.]+),\s*"
    r"nominatives\.\s*Capital-actions:\s*CHF\s+(?P<capital>[\d'.]+),\s*"
    r"entièrement libéré,\s*divisé en\s+(?P<capital_count>[\d']+)\s+actions "
    r"de CHF\s+(?P<capital_nominal>[\d'.]+),\s*nominatives\.?$",
    re.I | re.UNICODE,
)
_FR_AUTHORIZED_PARTICIPATION_CAPITAL_REMOVED = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est complétée en ce que sens "
    r"la clause statutaire relative à l['’]augmentation autorisée du capital "
    r"participation,\s*fondée sur la décision d['’]autorisation du\s+"
    r"(?P<authorization_date>\d{2}\.\d{2}\.\d{4}),\s*est supprimée par "
    r"l['’]assemblée générale du\s+(?P<removal_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_FOREIGN_ASSET_TRANSFER_CASH = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré "
    r"des actifs pour\s+(?P<currency>[A-Z]{3})\s+(?P<assets>[\d'.]+)\s+et "
    r"des passifs envers les tiers pour\s+(?P=currency)\s+"
    r"(?P<liabilities>[\d'.]+)\s+à la société\s+(?P<recipient>.+?)\s*"
    r"\((?P<foreign_id>[^)]+)\),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{1,3})\.\s*Contre-prestation:\s*(?P=currency)\s+"
    r"(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_SUSPENSION_REVOKED = re.compile(
    r"^Gemäss Verfügung des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wird die Verfügung vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4}),\s*mit der das "
    r"Konkursverfahren mangels Aktiven eingestellt worden ist,\s*widerrufen\s*"
    r"\[bisher:\s*Das Konkursverfahren ist mit Verfügung des\s+"
    r"(?P<previous_authority>.+?)\s+vom\s+"
    r"(?P<previous_text_date>\d{2}\.\d{2}\.\d{4})\s+mangels Aktiven "
    r"eingestellt worden\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBER_SIGNING_REVOKED = re.compile(
    r"^Le membre du conseil\s+(?P<name>[^,.;]+)\s+n['’]exerce plus la "
    r"signature social(?:e)?\.?$",
    re.I | re.UNICODE,
)
_DE_PERSON_NAME_CHANGED_WITH_ROLES = re.compile(
    r"^Eingetragene Person geändert:\s*(?P<previous_name>[^,.;]+),\s*"
    r"(?P<role1>[^,.;]+),\s*(?P<role2>[^,.;]+),\s*"
    r"(?P<signing>Kollektivunterschrift zu zweien mit dem Präsidenten oder "
    r"Vizepräsidenten),\s*nun mit dem Namen\s+(?P<name>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_DELETION_UID_CORRECTED = re.compile(
    r"^Die unter TR-Nr\.\s*(?P<entry>[\d']+)\s+vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+und im SHAB-Nr\.\s*"
    r"(?P<issue>\d+)\s+vom\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"publizierte Löschung von\s+(?P<surname>[^,.;]+),\s*"
    r"(?P<given>[^,.;]+),\s*wurde mit der falschen UID-Nr\. publiziert\s*"
    r"\((?P<incorrect_uid>CHE-\d{3}\.\d{3}\.\d{3})\s+anstelle von\s+"
    r"(?P<correct_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+deshalb erfolgt diese "
    r"Berichtigung\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_SELLERS_TRANSFER_TO_NEW_ASSOCIATE = re.compile(
    r"^(?P<seller1>[^,.;]+)\s+et\s+(?P<seller2>[^,.;]+)\s+ont cédé\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{1,3}),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"Signature collective à deux a été conférée à l['’]associé\s+"
    r"(?P<signed_buyer>[^,.;]+)\.\s*Par conséquent,\s*(?P<after_seller1>[^,.;]+)\s+"
    r"et\s+(?P<after_seller2>[^,.;]+)\s+sont désormais titulaires de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\s+"
    r"chacun\.?$",
    re.I | re.UNICODE,
)
_FR_AUDIT_WAIVER_REVOKED = re.compile(
    r"^Par décision du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"l['’]autorité de surveillance a révoqué la dispense de l['’]obligation "
    r"de désigner un organe de révision\.?$",
    re.I | re.UNICODE,
)
_FR_PRESIDENT_AND_TWO_BOARD_MEMBERS = re.compile(
    r"^L['’]administrateur\s+(?P<president>[^,.;]+),\s*nommé président,\s*"
    r"signe désormais collectivement à deux\.\s*"
    r"(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+)\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"(?P<country2>[A-Z]{2,3}),\s*sont membres du conseil "
    r"d['’]administration\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


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


def extract_parser249_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 249."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_TWO_FOUNDATION_MEMBERS_MIXED_ORIGIN.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_foundation_members_mixed_origin.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="membre du conseil de fondation",
                signing="ohne Unterschrift", extra={
                    "action": "appointed", "origin": match.group("origin1").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="membre du conseil de fondation",
                signing="ohne Unterschrift", extra={
                    "action": "appointed", "origin": match.group("place2").strip(),
                },
            ),
        ], ""

    match = _DE_CAPITAL_BAND_RESTATED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.capital_band_restated.v1", {
                "kind": "capital_band", "action": "restated",
                "basis": "statutes", "previous": "capital_band",
            },
        )], ""

    match = _FR_ORIGIN_CHANGED_DIRECTOR_AND_BOARD_MEMBER.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.origin_changed_director_and_board_member.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role="membre du conseil d'administration", extra={
                    "action": "role_and_origin_changed",
                    "origin": match.group("origin1").strip(),
                    "previous_role": match.group("previous_role1").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="membre du conseil d'administration",
                extra={
                    "action": "appointed", "origin": match.group("origin2").strip(),
                },
            ),
        ], ""

    match = _DE_PERSON_SIGNING_CHANGED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "de.persons.signing_changed.v1",
            match.group("name"), signing=match.group("signing"), extra={
                "action": "signing_changed",
                "previous_signing": match.group("previous_signing"),
            },
        )], ""

    match = _FR_NOTICE_TWO_ADMINISTRATORS_SIGNING.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.notice_two_administrators_signing.v1"
        reference = {
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_ref": match.group("notice_ref"),
            "action": "supplemented",
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="administrateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    **reference, "origin": match.group("origin1").strip(),
                    "required_with": match.group("with_person").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="administrateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    **reference, "origin": match.group("place2").strip(),
                },
            ),
        ], ""

    match = _FR_LIQUIDATORS_WITH_MANAGER_ROLES.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.liquidators_with_manager_roles.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role=f"liquidateur, {match.group(f'role{index}')}",
                signing="Einzelunterschrift", extra={
                    "action": "appointed_liquidator", "signing_continues": True,
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_NOMINATIVE_SHARE_SPLIT_UNRESTRICTED.fullmatch(leftover)
    if match:
        before_count = _count(match.group("before_count"))
        after_count = _count(match.group("after_count"))
        capital_count = _count(match.group("capital_count"))
        before_nominal = _count(match.group("before_nominal"))
        after_nominal = _count(match.group("after_nominal"))
        capital = _count(match.group("capital"))
        capital_nominal = _count(match.group("capital_nominal"))
        if (
            before_count * before_nominal == capital
            and after_count == capital_count
            and after_nominal == capital_nominal
            and after_count * after_nominal == capital
        ):
            return [_event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.nominative_share_split_unrestricted.v1", {
                    "action": "shares_split", "currency": "CHF",
                    "capital": match.group("capital"), "paid_in_full": True,
                    "from_share_count": before_count,
                    "from_share_nominal": match.group("before_nominal"),
                    "to_share_count": after_count,
                    "to_share_nominal": match.group("after_nominal"),
                    "share_kind": "nominatives",
                },
            )], ""

    match = _FR_AUTHORIZED_PARTICIPATION_CAPITAL_REMOVED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.authorized_participation_capital_removed.v1", {
                "kind": "authorized_participation_capital_clause",
                "action": "removed", "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "authorization_date": _iso_date(match.group("authorization_date")),
                "removal_date": _iso_date(match.group("removal_date")),
                "deciding_body": "assemblée générale",
            },
        )], ""

    match = _FR_FOREIGN_ASSET_TRANSFER_CASH.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.foreign_asset_transfer_cash.v1", {
                "action": "transferred", "transferor_kind": "company",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party",
                "recipient": match.group("recipient").strip(),
                "recipient_foreign_id": match.group("foreign_id").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_country": match.group("country"),
                "consideration": match.group("consideration"),
                "consideration_kind": "cash", "currency": match.group("currency"),
            },
        )], ""

    match = _DE_BANKRUPTCY_SUSPENSION_REVOKED.fullmatch(leftover)
    if match and match.group("previous_decision_date") == match.group("previous_text_date"):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_suspension_revoked.v1", {
                "kind": "bankruptcy", "action": "suspension_revoked",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "previous_action": "suspended_for_lack_of_assets",
                "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                "previous_authority": match.group("previous_authority").strip(),
            },
        )], ""

    match = _FR_BOARD_MEMBER_SIGNING_REVOKED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.board_member_signing_revoked.v1",
            match.group("name"), role="membre du conseil", extra={
                "action": "signing_revoked", "previous_signing": "signature sociale",
            },
        )], ""

    match = _DE_PERSON_NAME_CHANGED_WITH_ROLES.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.name_changed_with_roles.v1",
            match.group("name"),
            role=f"{match.group('role1')}, {match.group('role2')}",
            signing=match.group("signing"), extra={
                "action": "name_changed",
                "previous_name": match.group("previous_name").strip(),
            },
        )], ""

    match = _DE_DELETION_UID_CORRECTED.fullmatch(leftover)
    if match:
        name = f"{match.group('surname').strip()}, {match.group('given').strip()}"
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.deletion_uid_corrected.v1", name,
            uid=match.group("correct_uid"), extra={
                "action": "deletion_identifier_corrected",
                "incorrect_uid": match.group("incorrect_uid"),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_issue": int(match.group("issue")),
                "notice_date": _iso_date(match.group("notice_date")),
            },
        )], ""

    match = _FR_TWO_SELLERS_TRANSFER_TO_NEW_ASSOCIATE.fullmatch(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        remaining = _count(match.group("remaining"))
        names_match = (
            match.group("buyer").strip() == match.group("signed_buyer").strip()
            and match.group("seller1").strip() == match.group("after_seller1").strip()
            and match.group("seller2").strip() == match.group("after_seller2").strip()
        )
        same_nominal = (
            match.group("nominal") == match.group("buyer_nominal")
            == match.group("remaining_nominal")
        )
        if names_match and same_nominal and transferred == buyer_count and transferred % 2 == 0:
            per_seller = transferred // 2
            rule_id = "fr.persons.two_sellers_transfer_to_new_associate.v1"
            sellers = [match.group("seller1").strip(), match.group("seller2").strip()]
            events = [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé", extra={
                        "action": "shares_transferred", "counterparty": match.group("buyer").strip(),
                        "previous_shares_count": remaining + per_seller,
                        "shares_transferred": per_seller, "shares_count": remaining,
                        "share_nominal": match.group("nominal"), "currency": "CHF",
                    },
                )
                for seller in sellers
            ]
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"),
                place=match.group("place"), role="associé",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_and_shares_received", "counterparties": sellers,
                    "origin": match.group("origin").strip(),
                    "country": match.group("country"), "new_associate": True,
                    "shares_received": transferred, "shares_count": buyer_count,
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ))
            return events, ""

    match = _FR_AUDIT_WAIVER_REVOKED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "audit_requirement_changed", "fr.text.audit_waiver_revoked.v1", {
                "kind": "audit_waiver", "action": "revoked",
                "authority": "autorité de surveillance",
                "decision_date": _iso_date(match.group("decision_date")),
                "audit_body_required": True,
            },
        )], ""

    match = _FR_PRESIDENT_AND_TWO_BOARD_MEMBERS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.president_and_two_board_members.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président du conseil d'administration",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_president_and_signing_changed",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="membre du conseil d'administration",
                extra={
                    "action": "appointed", "origin": match.group("origin1").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="membre du conseil d'administration",
                extra={
                    "action": "appointed", "origin": match.group("origin2").strip(),
                    "country": match.group("country2"),
                },
            ),
        ], ""

    return [], leftover
