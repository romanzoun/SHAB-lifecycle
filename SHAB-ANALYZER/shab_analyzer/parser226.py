from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_DE_ORGANIZATIONAL_DEFICIENCIES_DISSOLUTION = re.compile(
    r"^Über die Rechtseinheit ist mit Entscheid der\s+"
    r"(?P<authority>.+?)\s+vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"infolge Mängel in der Organisation der Rechtseinheit in Anwendung von\s+"
    r"(?P<legal_basis>Art\.\s*939 OR)\s+die Auflösung und die Liquidation nach "
    r"den Vorschriften über den Konkurs angeordnet worden\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_CAPITAL_CURRENCY_CONVERTED = re.compile(
    r"^La monnaie du capital-social de\s+(?P<from_currency>[A-Z]{3})\s+"
    r"(?P<from_total>[\d'.]+),\s*divisé en\s+(?P<from_count>[\d']+)\s+"
    r"parts de\s+(?P=from_currency)\s+(?P<from_nominal>[\d'.]+)\s+a été "
    r"convertie en\s+(?P<to_currency>[A-Z]{3})\s+(?P<to_total>[\d'.]+),\s*"
    r"divisé en\s+(?P<to_count>[\d']+)\s+parts de\s+(?P=to_currency)\s+"
    r"(?P<to_nominal>[\d'.]+)\.\s*Capital-social:\s*(?P=to_currency)\s+"
    r"(?P<stated_total>[\d'.]+),\s*entièrement libéré,\s*divisé en\s+"
    r"(?P<stated_count>[\d']+)\s+parts de\s+(?P=to_currency)\s+"
    r"(?P<stated_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_PRESIDENT_AND_TWO_ADMINISTRATORS = re.compile(
    r"^(?P<president>[^,.;]+),\s*désormais à\s+(?P<president_place>[^,.;]+),\s*"
    r"est nommé président\.\s*(?P<administrator1>[^,.;]+)\s+et\s+"
    r"(?P<administrator2>[^,.;]+)\s+sont nommés administrateurs\.?$",
    re.I | re.UNICODE,
)
_FR_FOREIGN_BOARD_MEMBER_WITHOUT_SIGNATURE = re.compile(
    r"^(?P<name>[^,.;]+),\s*des\s+(?P<origin>[^,.;]+),\s*en\s+"
    r"(?P<region>[^,.;]+),\s*(?P<country>[^,.;]+),\s*est membre du conseil "
    r"d['’]administration,\s*(?:il\s+)?n['’]exerce pas la signature\.?$",
    re.I | re.UNICODE,
)
_FR_HEAD_OFFICE_PROXY_WITH_EXCLUSION = re.compile(
    r"^Procuration collective à deux limitée au siège principal,\s*toutefois "
    r"pas avec un autre fondé de procuration,\s*est conférée à\s+"
    r"(?P<name>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;()]+)"
    r"(?:\s*\((?P<place_canton>[A-Z]{2})\))?\.?$",
    re.I | re.UNICODE,
)
_FR_ADDITIONAL_DIRECTOR_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:n[o°]|no\.)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+est nommé en outre\s+(?P<role>directeur)\.?$",
    re.I | re.UNICODE,
)
_FR_TRANSFER_TO_TWO_NEW_ASSOCIATES_ONE_MANAGER = re.compile(
    r"^(?P<seller>[^,.;]+)\s+a cédé\s+(?P<stated_transfer>[\d']+)\s+parts de\s+"
    r"(?P<currency>[A-Z]{3})\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer1>[^,.;]+)\s+et à\s+(?P<buyer2>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*tous deux nouveaux associés chacun pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de\s+(?P=currency)\s+"
    r"(?P<buyer_nominal>[\d'.]+);\s*par conséquent\s+(?P=seller)\s+est "
    r"maintenant associé pour\s+(?P<remaining>[\d']+)\s+parts de\s+"
    r"(?P=currency)\s+(?P<remaining_nominal>[\d'.]+)\.\s*"
    r"(?P=buyer2)\s+est nommé\s+(?P<manager_role>gérant)"
    r"(?:\s+avec signature individuelle)?\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_WITH_PRESIDENT_OR_VICE_PRESIDENT = re.compile(
    r"^Nouveau membre du conseil de fondation "
    r"(?:avec signature collective à deux )?avec le président ou le "
    r"vice-président:\s*(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_NON_PUBLIC_DEED_CHANGES = re.compile(
    r"^\[Weitere Urkundenänderungen sind nicht publikationspflichtig\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_DEFINITIVE_MORATORIUM_EXTENDED_BY_JUDGMENT = re.compile(
    r"^Par jugement du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>.+?)\s+a prolongé le sursis concordataire définitif à la "
    r"société jusqu['’]au\s+(?P<until>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_CAPITAL_SPLIT_AND_MANAGER_SHARE_TRANSFER = re.compile(
    r"^Le capital social de\s+(?P<currency>[A-Z]{3})\s+"
    r"(?P<capital>[\d'.]+)\s+est désormais composé de\s+"
    r"(?P<total_count>[\d']+)\s+parts sociales de\s+(?P=currency)\s+"
    r"(?P<nominal>[\d'.]+),\s*dont\s+(?P<buyer>[^,.;]+)\s+et\s+"
    r"(?P<seller>[^,.;]+)\s+sont titulaires à hauteur de\s+"
    r"(?P<initial_count>[\d']+)\s+parts de\s+(?P=currency)\s+"
    r"(?P<initial_nominal>[\d'.]+)\s+chacun\.\s*L['’]associé-gérant\s+"
    r"(?P=seller)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<seller_before>[\d']+)\s+parts de\s+(?P=currency)\s+"
    r"(?P<seller_nominal>[\d'.]+)\s+à l['’]associée-gérante\s+"
    r"(?P=buyer),\s*désormais titulaire de\s+(?P<buyer_after>[\d']+)\s+parts "
    r"de\s+(?P=currency)\s+(?P<buyer_nominal>[\d'.]+);\s*(?P=seller)\s+reste "
    r"titulaire de\s+(?P<seller_after>[\d']+)\s+parts de\s+(?P=currency)\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_REMOVED_PERSON_TYPO = re.compile(
    r"^Personne rafiée:\s*(?P<name>[^,.;]+),\s*(?P<role>[^,.;]+),\s*"
    r"(?P<signing>signature individuelle)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_DOMICILES_CORRECTED_TYPO = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce "
    r"d[e]?ns que\s+(?P<name1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+)\s+sont "
    r"domiciliés à\s+(?P<place>[^()]+?)\s*\(et non\s+"
    r"(?P<previous_place>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_DEPUTY_DIRECTOR_INDIVIDUAL_TWO_PROXY_REVOKED = re.compile(
    r"^Signature\s+(?P<raw_signing>individuelle à deux)\s+a été conférée à\s+"
    r"(?P<name>[^,.;]+),\s*nommé\s+(?P<role>directeur adjoint);\s*"
    r"sa procuration est radiée\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATION_DISSOLVED_COLLECTIVE_LIQUIDATORS = re.compile(
    r"^L['’]association est dissoute par décision de l['’]assemblée générale du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.\s*Liquidateurs:\s*les membres du comité\s+"
    r"(?P<name1>[^,.;]+?)\s+et\s+(?P<name2>[^,.;]+),\s*lesquels continuent à "
    r"signer collectivement à deux\.?$",
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


def extract_parser226_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 226."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_ORGANIZATIONAL_DEFICIENCIES_DISSOLUTION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.organizational_deficiencies_dissolution.v1", {
                "kind": "dissolution", "action": "ordered_by_court",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "reason": "organizational_deficiencies",
                "legal_basis": match.group("legal_basis"),
                "liquidation_procedure": "bankruptcy",
            },
        )], ""

    match = _FR_SHARE_CAPITAL_CURRENCY_CONVERTED.fullmatch(leftover)
    if match:
        repeated_values_match = (
            match.group("to_total") == match.group("stated_total")
            and match.group("to_count") == match.group("stated_count")
            and match.group("to_nominal") == match.group("stated_nominal")
        )
        arithmetic_matches = (
            _money(match.group("from_total"))
            == _count(match.group("from_count")) * _money(match.group("from_nominal"))
            and _money(match.group("to_total"))
            == _count(match.group("to_count")) * _money(match.group("to_nominal"))
        )
        if repeated_values_match and arithmetic_matches:
            return [_event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.share_capital_currency_converted.v1", {
                    "action": "currency_converted",
                    "from_currency": match.group("from_currency").upper(),
                    "from_capital": match.group("from_total"),
                    "from_shares_count": _count(match.group("from_count")),
                    "from_share_nominal": match.group("from_nominal"),
                    "to_currency": match.group("to_currency").upper(),
                    "to_capital": match.group("to_total"),
                    "to_shares_count": _count(match.group("to_count")),
                    "to_share_nominal": match.group("to_nominal"),
                    "fully_paid": True,
                },
            )], ""

    match = _FR_BOARD_PRESIDENT_AND_TWO_ADMINISTRATORS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.board_president_and_two_administrators.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                place=match.group("president_place"),
                role="président du conseil d'administration",
                extra={"action": "appointed_president", "domicile_changed": True},
            ),
            *[
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"administrator{index}"),
                    role="administrateur", extra={"action": "appointed"},
                )
                for index in (1, 2)
            ],
        ], ""

    match = _FR_FOREIGN_BOARD_MEMBER_WITHOUT_SIGNATURE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.foreign_board_member_without_signature.v1",
            match.group("name"), place=match.group("region"),
            role="membre du conseil d'administration", extra={
                "action": "appointed", "origin": match.group("origin").strip(),
                "country": match.group("country").strip(),
                "signing_authority": False,
            },
        )], ""

    match = _FR_HEAD_OFFICE_PROXY_WITH_EXCLUSION.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.head_office_proxy_with_exclusion.v1",
            match.group("name"), place=match.group("place"),
            role="fondé de procuration", signing="Kollektivprokura zu zweien", extra={
                "action": "procuration_granted", "origin": match.group("origin").strip(),
                "scope": "head_office", "signing_exclusion": "another_proxy_holder",
                "place_canton": match.group("place_canton"),
            },
        )], ""

    match = _FR_ADDITIONAL_DIRECTOR_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.additional_director_corrected.v1",
            match.group("name"), role=match.group("role"), extra={
                "action": "additional_role_appointed", "correction": True,
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_TRANSFER_TO_TWO_NEW_ASSOCIATES_ONE_MANAGER.fullmatch(leftover)
    if match:
        buyer_count = _count(match.group("buyer_count"))
        remaining = _count(match.group("remaining"))
        stated_transfer = _count(match.group("stated_transfer"))
        if (
            stated_transfer == buyer_count
            and match.group("nominal") == match.group("buyer_nominal")
            == match.group("remaining_nominal")
        ):
            rule_id = "fr.persons.transfer_to_two_new_associates_one_manager.v1"
            common = {
                "currency": match.group("currency").upper(),
                "share_nominal": match.group("nominal"),
            }
            seller = match.group("seller").strip()
            events = [_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé", extra={
                    "action": "shares_transferred", "shares_before": remaining + buyer_count * 2,
                    "shares_transferred": buyer_count * 2, "shares_count": remaining,
                    "stated_transfer_to_each": stated_transfer, **common,
                },
            )]
            for index in (1, 2):
                is_manager = index == 2
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"buyer{index}"),
                    place=match.group("place") if is_manager else None,
                    role="associé-gérant" if is_manager else "associé",
                    signing="Einzelunterschrift" if is_manager else None,
                    extra={
                        "action": "appointed_and_shares_received",
                        "shares_received": buyer_count, "shares_count": buyer_count,
                        "counterparty": seller,
                        **({"origin": match.group("origin").strip()} if is_manager else {}),
                        **common,
                    },
                ))
            return events, ""

    match = _FR_FOUNDATION_MEMBER_WITH_PRESIDENT_OR_VICE_PRESIDENT.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed",
            "fr.persons.foundation_member_with_president_or_vice_president.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil de fondation",
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "appointed", "origin": match.group("origin").strip(),
                "signing_with_roles": ["président", "vice-président"],
            },
        )], ""

    if _DE_NON_PUBLIC_DEED_CHANGES.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.non_public_deed_changes.v1", {
                "kind": "deed_changes", "action": "changed",
                "details_public": False,
            },
        )], ""

    match = _FR_DEFINITIVE_MORATORIUM_EXTENDED_BY_JUDGMENT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.definitive_moratorium_extended_by_judgment.v1", {
                "kind": "composition_moratorium", "action": "extended",
                "moratorium_kind": "definitive",
                "decision_date": _iso_date(match.group("decision_date")),
                "until": _iso_date(match.group("until")),
                "authority": match.group("authority").strip(),
            },
        )], ""

    match = _FR_CAPITAL_SPLIT_AND_MANAGER_SHARE_TRANSFER.fullmatch(leftover)
    if match:
        total_count = _count(match.group("total_count"))
        initial_count = _count(match.group("initial_count"))
        transferred = _count(match.group("transferred"))
        seller_before = _count(match.group("seller_before"))
        seller_after = _count(match.group("seller_after"))
        buyer_after = _count(match.group("buyer_after"))
        nominal_values = {
            match.group("nominal"), match.group("initial_nominal"),
            match.group("seller_nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }
        if (
            len(nominal_values) == 1
            and _money(match.group("capital")) == total_count * _money(match.group("nominal"))
            and total_count == initial_count * 2
            and seller_before == initial_count
            and seller_after == seller_before - transferred
            and buyer_after == initial_count + transferred
        ):
            rule_id = "fr.persons.capital_split_and_manager_share_transfer.v1"
            common = {
                "currency": match.group("currency").upper(),
                "share_nominal": match.group("nominal"),
            }
            return [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "capital_changed", rule_id, {
                        "action": "share_structure_changed",
                        "capital": match.group("capital"),
                        "shares_count": total_count, **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("seller"),
                    role="associé-gérant", extra={
                        "action": "shares_transferred", "shares_before": seller_before,
                        "shares_transferred": transferred, "shares_count": seller_after,
                        "counterparty": match.group("buyer").strip(), **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("buyer"),
                    role="associée-gérante", extra={
                        "action": "shares_received", "shares_before": initial_count,
                        "shares_received": transferred, "shares_count": buyer_after,
                        "counterparty": match.group("seller").strip(), **common,
                    },
                ),
            ], ""

    match = _FR_REMOVED_PERSON_TYPO.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_removed", "fr.persons.removed_person_rafiee_typo.v1",
            match.group("name"), role=match.group("role"),
            signing="Einzelunterschrift", extra={
                "action": "removed", "source_wording": "Personne rafiée",
            },
        )], ""

    match = _FR_TWO_DOMICILES_CORRECTED_TYPO.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_domiciles_corrected_ce_dens_typo.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group("place"), extra={
                    "action": "domicile_corrected", "correction": True,
                    "previous_place": match.group("previous_place").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_DEPUTY_DIRECTOR_INDIVIDUAL_TWO_PROXY_REVOKED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed",
            "fr.persons.deputy_director_individual_two_proxy_revoked.v1",
            match.group("name"), role=match.group("role"),
            signing=match.group("raw_signing"), extra={
                "action": "appointed_and_signing_changed",
                "previous_signing": "procuration", "previous_signing_revoked": True,
                "raw_signing": match.group("raw_signing"),
            },
        )], ""

    match = _FR_ASSOCIATION_DISSOLVED_COLLECTIVE_LIQUIDATORS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.association_dissolved_collective_liquidators.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "dissolution", "action": "dissolved",
                    "decision_maker": "assemblée générale",
                    "date": _iso_date(match.group("date")),
                },
            ),
            *[
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    role="membre du comité et liquidateur",
                    signing="Kollektivunterschrift zu zweien", extra={
                        "action": "appointed_liquidator",
                        "previous_role": "membre du comité",
                    },
                )
                for index in (1, 2)
            ],
        ], ""

    return [], leftover
