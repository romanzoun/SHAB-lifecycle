from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_FR_PERSON_DOMICILE_CHANGED_WITH_COUNTRY = re.compile(
    r"^(?P<name>[^,.;]+?)\s+est désormais domiciliée? à\s+"
    r"(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{2,3})\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_NAME_CHANGED = re.compile(
    r"^(?!Par suite de changement d['’]état civil\b)(?![^,.;]*\busage\b)"
    r"(?P<previous_name>[^,.;]+?)\s+porte désormais le nom de\s+"
    r"(?P<name>[^,.;]+?)\.?$",
    re.I | re.UNICODE,
)
_DE_REGISTERED_PERSON_NAME_CHANGED = re.compile(
    r"^Eingetragene Person geändert:\s*(?P<previous_name>[^,.;]+),\s*"
    r"(?P<role>[^,.;]+),\s*(?P<signing>[^,.;]+),\s*neuer Name\s+"
    r"(?P<name>[^,.;]+?)\.?$",
    re.I | re.UNICODE,
)
_FR_ORDINARY_AND_PREFERRED_SHARES_TRANSFORMED = re.compile(
    r"^Division des\s+(?P<ordinary_before_count>[\d']+)\s+actions ordinaires de\s+"
    r"(?P<currency>[A-Z]{3})\s+(?P<before_nominal>[\d'.]+)\s+en\s+"
    r"(?P<ordinary_after_count>[\d']+)\s+actions de\s+(?P=currency)\s+"
    r"(?P<after_nominal>[\d'.]+)\s+et transformation des\s+"
    r"(?P<preferred_before_count>[\d']+)\s+actions,\s*jusqu['’]ici privilégiées "
    r"quant au dividende,\s*en\s+(?P<preferred_after_count>[\d']+)\s+actions "
    r"ordinaires de\s+(?P=currency)\s+(?P<preferred_after_nominal>[\d'.]+),\s*"
    r"toutes nominatives\.\s*Capital-actions:\s*(?P=currency)\s+"
    r"(?P<capital>[\d'.]+),\s*libéré à concurrence de\s+(?P=currency)\s+"
    r"(?P<paid>[\d'.]+),\s*divisé en\s+(?P<total_count>[\d']+)\s+actions de\s+"
    r"(?P=currency)\s+(?P<total_nominal>[\d'.]+),\s*nominatives\.?$",
    re.I | re.UNICODE,
)
_DE_ART_155_DELETION_PROCEDURE_COMPLETED = re.compile(
    r"^Auf die durch das Handelsregisteramt gestützt auf\s+"
    r"(?P<legal_basis>Art\.\s*155 HRegV)\s+veranlassten und im Schweiz\.\s*"
    r"Handelsamtsblatt vom\s+(?P<date1>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<date2>\d{2}\.\d{2}\.\d{4})\s+und\s+"
    r"(?P<date3>\d{2}\.\d{2}\.\d{4})\s+publizierten Rechnungsrufe wurde kein "
    r"Interesse an der Aufrechterhaltung der Eintragung geltend gemacht\.\s*"
    r"Das amtliche Verfahren zur Löschung der Gesellschaft ist damit "
    r"abgeschlossen,\s*weil die Gesellschaft keine Geschäftstätigkeit mehr "
    r"aufweist und keine verwertbaren Aktiven mehr hat\.?$",
    re.I | re.UNICODE,
)
_FR_FEMALE_MANAGER_TRANSFER_AND_PRESIDENCY = re.compile(
    r"^L['’]associée-gérante\s+(?P<seller>.+?),\s*qui est nommée présidente,\s*"
    r"cède\s+(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de\s+"
    r"(?P<currency>[A-Z]{3})\s+(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>.+?),\s*"
    r"de\s+(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de\s+(?P=currency)\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*gérant avec signature individuelle\.\s*"
    r"(?P=seller)\s+reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de\s+(?P=currency)\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_GRANTED_MORATORIUM_EXTENDED = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+die gewährte Nachlassstundung bis zum\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\s+verlängert\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ASSOCIATES_TRANSFER_TO_TWO_MANAGERS = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller1>.+?)\s+détient\s+"
    r"(?P<remaining1>[\d']+)\s+parts de\s+(?P<currency>[A-Z]{3})\s+"
    r"(?P<nominal>[\d'.]+)\s+et l['’]associé\s+(?P<seller2>.+?)\s+détient\s+"
    r"(?P<remaining2>[\d']+)\s+parts de\s+(?P=currency)\s+"
    r"(?P<nominal2>[\d'.]+)\s+par suite de cession de\s+"
    r"(?P<transferred1>[\d']+)\s+parts pour l['’]un et de\s+"
    r"(?P<transferred2>[\d']+)\s+parts pour l['’]autre\.\s*"
    r"Cessionnaires et nouveaux associés-gérants:\s*(?P<buyer1>.+?),\s*"
    r"d['’](?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*et\s+"
    r"(?P<buyer2>.+?),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*chacun pour\s+(?P<buyer_count>[\d']+)\s+parts de\s+"
    r"(?P=currency)\s+(?P<buyer_nominal>[\d'.]+)\.\s*Le nouvel associé-gérant\s+"
    r"(?P=buyer1),\s*nommé président,\s*signe collectivement à deux\.\s*"
    r"L['’]associé-gérant\s+(?P=seller1),\s*jusqu['’]ici avec signature "
    r"individuelle,\s*l['’]associé\s+(?P=seller2),\s*jusqu['’]ici avec "
    r"signature collective à deux sans autre "
    r"restriction,\s*et le nouvel associé-gérant\s+(?P=buyer2)\s+signent "
    r"collectivement à deux,\s*sauf entre eux\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_TO_TWO_NEW_MANAGERS = re.compile(
    r"^(?P<seller>.+?)\s+maintenant associé-gérant,\s*président,\s*pour\s+"
    r"(?P<remaining>[\d']+)\s+parts de\s+(?P<currency>[A-Z]{3})\s+"
    r"(?P<nominal>[\d'.]+),\s*par suite de cession de\s+"
    r"(?P<transferred>[\d']+)\s+parts de\s+(?P=currency)\s+"
    r"(?P<transferred_nominal>[\d'.]+)\s+aux nouveaux associés-gérants\s+"
    r"(?P<buyer1>.+?),\s*de et à\s+(?P<place1>[^,.;]+),\s*pour\s+"
    r"(?P<count1>[\d']+)\s+parts de\s+(?P=currency)\s+"
    r"(?P<nominal1>[\d'.]+)\s+et\s+(?P<buyer2>.+?),\s*de\s+"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*pour\s+"
    r"(?P<count2>[\d']+)\s+parts de\s+(?P=currency)\s+"
    r"(?P<nominal2>[\d'.]+),\s*tous deux avec signature individuelle\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTORS_SIGNING_RESTRICTIONS_CHANGED = re.compile(
    r"^Le directeur général\s+(?P<name1>.+?)\s+et le directeur\s+"
    r"(?P<name2>.+?)\s+continuent à signer collectivement à deux désormais sans "
    r"restriction\.\s*Signature collective à deux toutefois pas entre eux est "
    r"conférée à\s+(?P<name3>.+?),\s*de\s+(?P<origin3>[^,.;]+),\s*et\s+"
    r"(?P<name4>.+?),\s*de\s+(?P<origin4>[^,.;]+),\s*tous deux au\s+"
    r"(?P<place>[^,.;]+),\s*directeurs\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_REMOVED_HYPHENATED_LEGACY_ID = re.compile(
    r"^Zweigniederlassung neu:\s*"
    r"\[Folgende Zweigniederlassungen sind aufgehoben worden:\]\s*"
    r"\[gestrichen:\s*(?P<place>[^()\]]+?)\s*"
    r"\((?P<branch_canton>[A-Z]{2})\)\s*"
    r"\((?P<registry_id>CH-[\d.-]+-\d)\)\]\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_PROXIES_WITH_MUTUAL_EXCLUSION = re.compile(
    r"^Procuration collective à deux,\s*toutefois pas entre elles,\s*est "
    r"conférée à\s+(?P<name1>.+?),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*et\s+(?P<name2>.+?),\s*de\s+"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_DISSOLUTION_DATE_CORRECTED = re.compile(
    r"^L['’]inscription\s+n[°o]\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que la "
    r"société a été dissoute par décision de son assemblée générale du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s*\(et non pas du\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\)\.?$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_EXTENDED_SIMPLE_HISTORY = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat der\s+"
    r"(?P<authority>.+?)\s+die definitive Nachlassstundung bis\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\s+verlängert\.\s*"
    r"\[bisher:\s*Mit Entscheid vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+hat der\s+"
    r"(?P=authority)\s+die definitive Nachlassstundung bis\s+"
    r"(?P<previous_until>\d{2}\.\d{2}\.\d{4})\s+bewilligt\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_LIQUIDATION_WITH_FOUR_ADMINISTRATORS = re.compile(
    r"^Sa liquidation est opérée sous la raison sociale:\s*"
    r"(?P<liquidation_name>.+?)\.\s*Liquidateurs:\s*les administrateurs\s+"
    r"(?P<president>[^,.;]+),\s*président,\s*(?P<vice_president>[^,.;]+),\s*"
    r"vice-président,\s*(?P<delegate>[^,.;]+),\s*délégué,\s*et\s+"
    r"(?P<member>[^,.;]+)\.\s*Signature collective à deux de\s+"
    r"(?P=president)\s+et de\s+(?P=delegate)\s+avec\s+(?P=member)\s+ou\s+"
    r"(?P=vice_president)\.\s*Signature collective à deux de\s+"
    r"(?P=member)\s+et de\s+(?P=vice_president)\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_NAME_TRANSLATIONS_REMOVAL_OMITTED = re.compile(
    r"^Die Streichung der Übersetzungen der bisherigen Firma sind irrtümlich "
    r"vergessen gegangen\.?$",
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


def extract_parser225_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 225."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_PERSON_DOMICILE_CHANGED_WITH_COUNTRY.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.domicile_changed_with_country.v1",
            match.group("name"), place=match.group("place"), extra={
                "action": "domicile_changed",
                "country": match.group("country").upper(),
            },
        )], ""

    match = _FR_PERSON_NAME_CHANGED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.name_changed.v1",
            match.group("name"), extra={
                "action": "name_changed",
                "previous_name": match.group("previous_name").strip(),
            },
        )], ""

    match = _DE_REGISTERED_PERSON_NAME_CHANGED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.registered_person_name_changed.v1",
            match.group("name"), role=match.group("role"),
            signing=match.group("signing").strip(), extra={
                "action": "name_changed",
                "previous_name": match.group("previous_name").strip(),
            },
        )], ""

    match = _FR_ORDINARY_AND_PREFERRED_SHARES_TRANSFORMED.fullmatch(leftover)
    if match:
        ordinary_before = _count(match.group("ordinary_before_count"))
        ordinary_after = _count(match.group("ordinary_after_count"))
        preferred_before = _count(match.group("preferred_before_count"))
        preferred_after = _count(match.group("preferred_after_count"))
        total_count = _count(match.group("total_count"))
        before_nominal = _money(match.group("before_nominal"))
        after_nominal = _money(match.group("after_nominal"))
        preferred_after_nominal = _money(match.group("preferred_after_nominal"))
        total_nominal = _money(match.group("total_nominal"))
        capital = _money(match.group("capital"))
        if (
            ordinary_before * before_nominal == ordinary_after * after_nominal
            and preferred_before * before_nominal
            == preferred_after * preferred_after_nominal
            and ordinary_after + preferred_after == total_count
            and total_count * total_nominal == capital
            and _money(match.group("paid")) == capital
            and after_nominal == preferred_after_nominal == total_nominal
        ):
            return [_event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed",
                "fr.text.ordinary_and_preferred_shares_transformed.v1", {
                    "kind": "share_split_and_class_transformation",
                    "currency": match.group("currency").upper(),
                    "capital": match.group("capital"),
                    "paid": match.group("paid"),
                    "fully_paid": True,
                    "shares_count": total_count,
                    "share_nominal": match.group("total_nominal"),
                    "share_kind": "registered_ordinary",
                    "ordinary_before_count": ordinary_before,
                    "preferred_before_count": preferred_before,
                    "ordinary_after_split_count": ordinary_after,
                    "preferred_transformed_count": preferred_after,
                    "previous_share_nominal": match.group("before_nominal"),
                },
            )], ""

    match = _DE_ART_155_DELETION_PROCEDURE_COMPLETED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.art_155_deletion_procedure_completed.v1", {
                "kind": "deletion_procedure", "action": "completed",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "creditor_call_dates": [
                    _iso_date(match.group(f"date{index}")) for index in (1, 2, 3)
                ],
                "continued_registration_interest": False,
                "business_activity": False,
                "realisable_assets": False,
            },
        )], ""

    match = _FR_FEMALE_MANAGER_TRANSFER_AND_PRESIDENCY.fullmatch(leftover)
    if match:
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        remaining = _count(match.group("remaining"))
        buyer_count = _count(match.group("buyer_count"))
        if (
            before - transferred == remaining
            and transferred == buyer_count
            and len({
                match.group("nominal"), match.group("buyer_nominal"),
                match.group("remaining_nominal"),
            }) == 1
        ):
            rule_id = "fr.persons.female_manager_transfer_and_presidency.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            common = {
                "currency": match.group("currency").upper(),
                "share_nominal": match.group("nominal"),
            }
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller,
                    role="associée-gérante et présidente", extra={
                        "action": "appointed_president_and_shares_transferred",
                        "counterparty": buyer, "shares_before": before,
                        "shares_transferred": transferred,
                        "shares_count": remaining, **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé-gérant", signing="Einzelunterschrift", extra={
                        "action": "appointed_and_shares_received",
                        "counterparty": seller, "origin": match.group("origin").strip(),
                        "shares_received": buyer_count, "shares_count": buyer_count,
                        **common,
                    },
                ),
            ], ""

    match = _DE_GRANTED_MORATORIUM_EXTENDED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.granted_moratorium_extended.v1", {
                "kind": "composition_moratorium", "action": "extended",
                "decision_date": _iso_date(match.group("decision_date")),
                "until": _iso_date(match.group("until")),
                "authority": match.group("authority").strip(),
            },
        )], ""

    match = _FR_TWO_ASSOCIATES_TRANSFER_TO_TWO_MANAGERS.fullmatch(leftover)
    if match:
        transferred = [_count(match.group(f"transferred{index}")) for index in (1, 2)]
        remaining = [_count(match.group(f"remaining{index}")) for index in (1, 2)]
        buyer_count = _count(match.group("buyer_count"))
        if (
            sum(transferred) == buyer_count * 2
            and match.group("nominal") == match.group("nominal2")
            == match.group("buyer_nominal")
        ):
            rule_id = "fr.persons.two_associates_transfer_to_two_managers.v1"
            sellers = [match.group(f"seller{index}").strip() for index in (1, 2)]
            buyers = [match.group(f"buyer{index}").strip() for index in (1, 2)]
            common = {
                "currency": match.group("currency").upper(),
                "share_nominal": match.group("nominal"),
            }
            events = [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, sellers[index - 1],
                    role="associé-gérant", signing="Kollektivunterschrift zu zweien",
                    extra={
                        "action": "shares_transferred_and_signing_changed",
                        "shares_before": remaining[index - 1] + transferred[index - 1],
                        "shares_transferred": transferred[index - 1],
                        "shares_count": remaining[index - 1],
                        "signing_exclusion": "between_named_group",
                        **({"previous_role": "associé"} if index == 2 else {}),
                        **common,
                    },
                )
                for index in (1, 2)
            ]
            for index in (1, 2):
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyers[index - 1],
                    place=match.group(f"place{index}"),
                    role=("associé-gérant et président" if index == 1 else "associé-gérant"),
                    signing="Kollektivunterschrift zu zweien", extra={
                        "action": "appointed_and_shares_received",
                        "origin": match.group(f"origin{index}").strip(),
                        "shares_received": buyer_count, "shares_count": buyer_count,
                        "signing_exclusion": "between_named_group" if index == 2 else None,
                        **common,
                    },
                ))
            return events, ""

    match = _FR_MANAGER_TRANSFER_TO_TWO_NEW_MANAGERS.fullmatch(leftover)
    if match:
        remaining = _count(match.group("remaining"))
        transferred = _count(match.group("transferred"))
        counts = [_count(match.group(f"count{index}")) for index in (1, 2)]
        if (
            transferred == sum(counts)
            and len({
                match.group("nominal"), match.group("transferred_nominal"),
                match.group("nominal1"), match.group("nominal2"),
            }) == 1
        ):
            rule_id = "fr.persons.manager_transfer_to_two_new_managers.v1"
            seller = match.group("seller").strip()
            common = {
                "currency": match.group("currency").upper(),
                "share_nominal": match.group("nominal"),
            }
            events = [_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller,
                role="associé-gérant et président", extra={
                    "action": "appointed_manager_president_and_shares_transferred",
                    "shares_before": remaining + transferred,
                    "shares_transferred": transferred, "shares_count": remaining,
                    **common,
                },
            )]
            for index in (1, 2):
                origin = (
                    match.group("place1") if index == 1 else match.group("origin2")
                )
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"buyer{index}"),
                    place=match.group(f"place{index}"), role="associé-gérant",
                    signing="Einzelunterschrift", extra={
                        "action": "appointed_and_shares_received", "origin": origin.strip(),
                        "shares_received": counts[index - 1],
                        "shares_count": counts[index - 1], "counterparty": seller,
                        **common,
                    },
                ))
            return events, ""

    match = _FR_DIRECTORS_SIGNING_RESTRICTIONS_CHANGED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.directors_signing_restrictions_changed.v1"
        events = [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name1"),
                role="directeur général", signing="Kollektivunterschrift zu zweien",
                extra={"action": "restriction_removed", "signing_restricted": False},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name2"),
                role="directeur", signing="Kollektivunterschrift zu zweien",
                extra={"action": "restriction_removed", "signing_restricted": False},
            ),
        ]
        for index, other_index in ((3, 4), (4, 3)):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                place=match.group("place"), role="directeur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "signing_granted",
                    "origin": match.group(f"origin{index}").strip(),
                    "signing_excluded_with": match.group(f"name{other_index}").strip(),
                },
            ))
        return events, ""

    match = _DE_BRANCH_REMOVED_HYPHENATED_LEGACY_ID.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_removed", "de.text.branch_removed_hyphenated_legacy_id.v1", {
                "action": "removed", "place": match.group("place").strip(),
                "registry_id": match.group("registry_id"),
                "branch_canton": match.group("branch_canton").upper(),
            },
        )], ""

    match = _FR_TWO_PROXIES_WITH_MUTUAL_EXCLUSION.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_proxies_with_mutual_exclusion.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="fondé de procuration",
                signing="Kollektivprokura zu zweien", extra={
                    "action": "procuration_granted",
                    "origin": match.group(f"origin{index}").strip(),
                    "signing_excluded_with": match.group(
                        f"name{2 if index == 1 else 1}"
                    ).strip(),
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_DISSOLUTION_DATE_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.dissolution_date_corrected.v1", {
                "kind": "dissolution", "action": "publication_corrected",
                "decision_maker": "assemblée générale",
                "date": _iso_date(match.group("date")),
                "previous_date": _iso_date(match.group("previous_date")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _DE_DEFINITIVE_MORATORIUM_EXTENDED_SIMPLE_HISTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed",
            "de.text.definitive_moratorium_extended_simple_history.v1", {
                "kind": "composition_moratorium", "action": "extended",
                "moratorium_kind": "definitive",
                "decision_date": _iso_date(match.group("decision_date")),
                "until": _iso_date(match.group("until")),
                "authority": match.group("authority").strip(),
                "previous_decision_date": _iso_date(
                    match.group("previous_decision_date")
                ),
                "previous_until": _iso_date(match.group("previous_until")),
            },
        )], ""

    match = _FR_LIQUIDATION_WITH_FOUR_ADMINISTRATORS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.four_administrators_appointed_liquidators.v1"
        people = [
            (
                "president",
                "administrateur président et liquidateur",
                ["member", "vice_president"],
            ),
            (
                "vice_president",
                "administrateur vice-président et liquidateur",
                ["president", "delegate", "member"],
            ),
            (
                "delegate",
                "administrateur délégué et liquidateur",
                ["member", "vice_president"],
            ),
            (
                "member",
                "administrateur et liquidateur",
                ["president", "delegate", "vice_president"],
            ),
        ]
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(group),
                role=role,
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_liquidator",
                    "signing_with": [match.group(other).strip() for other in signing_with],
                    "liquidation_name": match.group("liquidation_name").strip(),
                },
            )
            for group, role, signing_with in people
        ], ""

    if _DE_COMPANY_NAME_TRANSLATIONS_REMOVAL_OMITTED.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected",
            "de.text.company_name_translations_removal_omitted.v1", {
                "kind": "company_name_translations",
                "action": "removal_omission_corrected",
                "translations_removed": True,
            },
        )], ""

    return [], leftover
