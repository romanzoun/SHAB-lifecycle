from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_ANCILLARY_AND_TRANSFER_CLAUSES = re.compile(
    r"^La clause statutaire relative à l['’]obligation de fournir des prestations "
    r"accessoires,\s*droits de préférence,\s*de préemption ou d['’]emption est "
    r"abrogée\.\s*Les statuts dérogent à la loi quant aux modalités du transfert "
    r"des parts sociales:\s*pour les détails,\s*voir les statuts\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ADMINISTRATORS_SIGNING_CORRECTED = re.compile(
    r"^L['’]inscription (?:no|n°)\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) est rectifiée en ce sens que les "
    r"administrateurs\s+(?P<name1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+)\s+"
    r"signent individuellement\s*\(et non pas collectivement à deux\)\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_WITH_LIABILITIES_NO_CONSIDERATION = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven von CHF\s+(?P<liabilities>[\d'.]+)\s+"
    r"auf die\s+(?P<recipient>.+?),\s*in\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{2,3})\)\.\s*"
    r"Gegenleistung:\s*keine\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_MOVE_AND_SECRETARY = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*maintenant domiciliée? à\s*"
    r"(?P<president_place>[^,.;]+),\s*nommée?\s+(?P<president_role>présidente?),\s*"
    r"et\s+(?P<secretary>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<secretary_origin>[^,.;]+),\s*à\s*(?P<secretary_place>[^,.;]+),\s*"
    r"(?P<secretary_role>secrétaire),\s*lesquelles signent individuellement\.?$",
    re.I | re.UNICODE,
)
_IT_OWNER_BANKRUPTCY_SUSPENDED_AND_REMOVED = re.compile(
    r"^\[radiati:\s*Il titolare è stato dichiarato in fallimento con decreto della\s+"
    r"(?P<court>.+?)\s+del\s+(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"a far tempo dal\s+(?P<effective_date>\d{2}\.\d{2}\.\d{4})\s+alle ore\s+"
    r"(?P<effective_time>\d{2}:\d{2})\.\]\.?\s*Con decisione del\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+(?P<authority>.+?)\s+"
    r"ha accordato effetto sospensivo al reclamo inoltrato contro la decisione di "
    r"fallimento aperto nei confronti del titolare il\s+"
    r"(?P<appealed_date>\d{2}\.\d{2}\.\d{4})\.\s*L['’]iscrizione nel registro di "
    r"commercio relativa al fallimento del titolare viene pertanto cancellata\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_RENAMED_AND_UID_CHANGED = re.compile(
    r"^Nouvelle raison sociale et numéro d['’]identification des entreprises\s*"
    r"\(IDE/UID\) de l['’]organe de révision\s+[\"“](?P<old_name>.+?)[\"”]\s*"
    r"\((?P<old_registry_id>CH-[\d-]+)\):\s*[\"“](?P<name>.+?)[\"”]\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_FR_REGISTERED_SHARE_SPLIT = re.compile(
    r"^Division des\s+(?P<from_count>[\d']+) actions de CHF\s+"
    r"(?P<from_nominal>[\d'.]+),\s*nominatives,\s*en\s+"
    r"(?P<to_count>[\d']+) actions de CHF\s+(?P<to_nominal>[\d'.]+)\.\s*"
    r"Capital-actions:\s*CHF\s+(?P<total>[\d'.]+),\s*libéré à concurrence de CHF\s+"
    r"(?P<paid>[\d'.]+),\s*divisé en\s+(?P<capital_count>[\d']+) actions de CHF\s+"
    r"(?P<capital_nominal>[\d'.]+),\s*nominatives\.?$",
    re.I | re.UNICODE,
)
_FR_ORGANIZATION_SHARE_TRANSFER = re.compile(
    r"^(?P<seller>.+?)\s+a cédé\s+(?P<transferred>[\d']+) parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*maintenant associé pour\s+"
    r"(?P<buyer_count>[\d']+) parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"par conséquent\s+(?P=seller)\s+est maintenant associée pour\s+"
    r"(?P<seller_count>[\d']+) parts de CHF\s+(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_AND_TWO_MANAGERS = re.compile(
    r"^(?P<seller>[^,.;]+)\s+a cédé\s+(?P<transferred>[\d']+) parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s*"
    r"(?P<place>[^,.;]+),\s*nouvel associé pour\s+(?P<buyer_count>[\d']+) parts "
    r"de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*Par conséquent,\s*"
    r"(?P=seller)\s+est désormais titulaire de\s+(?P<seller_count>[\d']+) parts "
    r"de CHF\s+(?P<seller_nominal>[\d'.]+)\.\s*Gérants:\s*(?P=seller),\s*"
    r"nommé président et\s+(?P=buyer),\s*tous deux\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGERS_SHARE_TRANSFER = re.compile(
    r"^(?P<seller>[^,.;]+),\s*(?P<seller_role>associé-gérant),\s*cède\s+"
    r"(?P<transferred>[\d']+) de ses\s+(?P<before>[\d']+) parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?P<buyer_role>associée-gérante et présidente),\s*désormais titulaire de\s+"
    r"(?P<buyer_count>[\d']+) parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<seller_count>[\d']+) parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_PROPRIETOR_REINSTATED_PLAIN = re.compile(
    r"^L['’]entreprise individuelle a été radiée par erreur\.\s*"
    r"Elle est réinscrite et continue son activité comme auparavant\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_BOARD_MEMBERS_PAIR = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s*(?P<place1>[^,.;]+),\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s*(?P<place2>[^,.;]+),\s*"
    r"sont membres du conseil de fondation\.?$",
    re.I | re.UNICODE,
)
_IT_COMPANY_BANKRUPTCY_SUSPENDED_WITH_NAME_FRAGMENT = re.compile(
    r"^(?:(?P<name_fragment>.+?\bSA)\.\s*)?Con decreto del\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+(?P<authority>.+?)\s+"
    r"ha accordato effetto sospensivo al reclamo inoltrato contro la decisione di "
    r"apertura del fallimento della\s+(?P<court>.+?)\s+del\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.\s*L['’]iscrizione nel registro "
    r"di commercio relativa allo scioglimento della società a seguito di fallimento "
    r"viene pertanto cancellata\.\s*\[finora:\s*La società è sciolta in seguito a "
    r"fallimento pronunciato con decreto della\s+(?P<previous_court>.+?)\s+del\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+a far tempo dall['’]"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4})\s+alle ore\s+"
    r"(?P<effective_time>\d{2}:\d{2})\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_ASSET_TRANSFER_WITH_LIABILITIES = re.compile(
    r"^Transfert de patrimoine:\s*Selon contrat du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré des actifs pour CHF\s+"
    r"(?P<assets>[\d'.]+)\s+et des passifs envers les tiers pour CHF\s+"
    r"(?P<liabilities>[\d'.]+),\s*à\s+(?P<recipient>.+?),\s*à\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_REPLACED_AFTER_EXPIRY = re.compile(
    r"^\[Streichung der Statutenbestimmung über die mit Ermächtigungsbeschluss vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+eingeführte genehmigte "
    r"Kapitalerhöhung infolge Zeitablaufs\.\]\s*\.?\s*Die Gesellschaft hat mit "
    r"Beschluss vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+eine genehmigte "
    r"Kapitalerhöhung gemäss näherer Umschreibung in den Statuten beschlossen\.?$",
    re.I | re.UNICODE,
)
_IT_FUSION_WITH_DEFICIT_COVERAGE = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di\s+(?P<absorbed_name>.+?),\s*"
    r"in\s+(?P<absorbed_place>[^()]+?)\s*\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"secondo il contratto di fusione del\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"e bilancio al\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta "
    r"attivi per CHF\s+(?P<assets>[\d'.]+)\s+e passivi verso terzi per CHF\s+"
    r"(?P<liabilities>[\d'.]+)\.\s*La società assuntrice detiene tutte le azioni "
    r"della società trasferente,\s*per cui la fusione avviene senza aumento del "
    r"capitale e senza attribuzione di azioni\.\s*Come risulta dall['’]attestazione "
    r"di un perito revisore abilitato,\s*la società assuntrice dispone di fondi "
    r"propri liberamente disponibili equivalenti almeno all['’]ammontare dello "
    r"scoperto e del sovraindebitamento della società trasferente\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{year}-{month}-{day}"


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


def _share_change_payload(
    *,
    action: str,
    counterparty: str,
    transferred: int,
    count: int,
    nominal: str,
    before: int | None = None,
) -> dict:
    payload = {
        "action": action,
        "counterparty": counterparty.strip(),
        "shares_count": count,
        "shares_nominal": nominal,
    }
    if action == "shares_transferred":
        payload["shares_transferred"] = transferred
    else:
        payload["shares_received"] = transferred
    if before is not None:
        payload["shares_before"] = before
    return payload


def extract_parser79_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 79."""
    del language  # Historical publications can mix languages.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_ANCILLARY_AND_TRANSFER_CLAUSES.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "fr.text.ancillary_and_share_transfer_clauses.v1",
                {
                    "kind": "ancillary_obligations_and_share_transfer_rules",
                    "ancillary_obligations": "removed",
                    "share_transfer_rules": "statutory_derogation",
                    "details_in_statutes": True,
                },
            )
        )

    match = _FR_TWO_ADMINISTRATORS_SIGNING_CORRECTED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_administrators_signing_corrected.v1"
        for name in (match.group("name1"), match.group("name2")):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", rule_id, name,
                    role="administrateur", signing="Einzelunterschrift",
                    extra={
                        "action": "corrected",
                        "previous_signing": "Kollektivunterschrift zu zweien",
                        "entry": match.group("entry"),
                        "entry_date": _iso_date(match.group("entry_date")),
                    },
                )
            )

    match = _DE_ASSET_TRANSFER_WITH_LIABILITIES_NO_CONSIDERATION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.asset_transfer_no_consideration_legacy_uid.v1",
                {
                    "date": _iso_date(match.group("date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "currency": "CHF",
                    "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration": "keine",
                    "consideration_kind": "none",
                },
            )
        )

    match = _FR_ADMINISTRATION_MOVE_AND_SECRETARY.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_move_and_secretary.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("president"),
                    place=match.group("president_place"), role=match.group("president_role"),
                    signing="Einzelunterschrift",
                    extra={"action": "appointed_president", "domicile_changed": True},
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("secretary"),
                    place=match.group("secretary_place"), role=match.group("secretary_role"),
                    signing="Einzelunterschrift",
                    extra={
                        "action": "appointed",
                        "heimat": match.group("secretary_origin").strip(),
                    },
                ),
            ]
        )

    match = _IT_OWNER_BANKRUPTCY_SUSPENDED_AND_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "it.text.owner_bankruptcy_suspended_and_removed.v1",
                {
                    "kind": "bankruptcy_effect_suspended",
                    "scope": "sole_proprietor_owner",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "authority": match.group("authority").strip(),
                    "bankruptcy_court": match.group("court").strip(),
                    "bankruptcy_decision_date": _iso_date(match.group("bankruptcy_date")),
                    "appealed_bankruptcy_date": _iso_date(match.group("appealed_date")),
                    "bankruptcy_effective_date": _iso_date(match.group("effective_date")),
                    "bankruptcy_effective_time": match.group("effective_time"),
                    "bankruptcy_entry_removed": True,
                },
            )
        )

    match = _FR_AUDITOR_RENAMED_AND_UID_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.auditor_renamed_and_uid_changed.v1",
                match.group("name"), uid=match.group("uid"), role="organe de révision",
                extra={
                    "action": "name_and_identifier_changed",
                    "previous": match.group("old_name").strip(),
                    "previous_registry_id": match.group("old_registry_id"),
                },
            )
        )

    match = _FR_REGISTERED_SHARE_SPLIT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.registered_share_split.v1",
                {
                    "kind": "share_split",
                    "currency": "CHF",
                    "from_count": _count(match.group("from_count")),
                    "from_nominal": match.group("from_nominal"),
                    "to_count": _count(match.group("to_count")),
                    "to_nominal": match.group("to_nominal"),
                    "capital": match.group("total"),
                    "paid_in": match.group("paid"),
                    "capital_count": _count(match.group("capital_count")),
                    "capital_nominal": match.group("capital_nominal"),
                    "registered": True,
                },
            )
        )

    match = _FR_ORGANIZATION_SHARE_TRANSFER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.organization_share_transfer.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        seller_count = _count(match.group("seller_count"))
        buyer_count = _count(match.group("buyer_count"))
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associée",
                    extra=_share_change_payload(
                        action="shares_transferred", counterparty=buyer,
                        transferred=transferred, before=seller_count + transferred,
                        count=seller_count, nominal=match.group("seller_nominal"),
                    ),
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, role="associé",
                    extra=_share_change_payload(
                        action="shares_received", counterparty=seller,
                        transferred=transferred, before=buyer_count - transferred,
                        count=buyer_count, nominal=match.group("buyer_nominal"),
                    ),
                ),
            ]
        )

    match = _FR_SHARE_TRANSFER_AND_TWO_MANAGERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.share_transfer_and_two_managers.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        seller_count = _count(match.group("seller_count"))
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé-gérant et président",
                    signing="Kollektivunterschrift zu zweien",
                    extra=_share_change_payload(
                        action="shares_transferred", counterparty=buyer,
                        transferred=transferred, before=seller_count + transferred,
                        count=seller_count, nominal=match.group("seller_nominal"),
                    ),
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé-gérant", signing="Kollektivunterschrift zu zweien",
                    extra={
                        **_share_change_payload(
                            action="shares_received", counterparty=seller,
                            transferred=transferred, before=0,
                            count=_count(match.group("buyer_count")),
                            nominal=match.group("buyer_nominal"),
                        ),
                        "heimat": match.group("origin").strip(),
                        "new_associate": True,
                    },
                ),
            ]
        )

    match = _FR_ASSOCIATE_MANAGERS_SHARE_TRANSFER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.associate_managers_share_transfer.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role=match.group("seller_role"),
                    extra=_share_change_payload(
                        action="shares_transferred", counterparty=buyer,
                        transferred=transferred, before=_count(match.group("before")),
                        count=_count(match.group("seller_count")),
                        nominal=match.group("seller_nominal"),
                    ),
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, role=match.group("buyer_role"),
                    extra=_share_change_payload(
                        action="shares_received", counterparty=seller,
                        transferred=transferred,
                        before=_count(match.group("buyer_count")) - transferred,
                        count=_count(match.group("buyer_count")),
                        nominal=match.group("buyer_nominal"),
                    ),
                ),
            ]
        )

    match = _FR_SOLE_PROPRIETOR_REINSTATED_PLAIN.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "fr.text.sole_proprietor_reinstated_plain.v1",
                {
                    "kind": "registration_reinstated",
                    "entity": "sole_proprietorship",
                    "reason": "erroneous_deletion",
                    "business_continues": True,
                },
            )
        )

    match = _FR_FOUNDATION_BOARD_MEMBERS_PAIR.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.foundation_board_members_pair.v1"
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    place=match.group(f"place{index}"), role="membre du conseil de fondation",
                    signing="Kollektivunterschrift zu zweien",
                    extra={
                        "action": "appointed",
                        "heimat": match.group(f"origin{index}").strip(),
                    },
                )
            )

    match = _IT_COMPANY_BANKRUPTCY_SUSPENDED_WITH_NAME_FRAGMENT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "it.text.company_bankruptcy_suspended_legacy_name_fragment.v1",
                {
                    "kind": "bankruptcy_effect_suspended",
                    "scope": "company",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "authority": match.group("authority").strip(),
                    "bankruptcy_court": match.group("court").strip(),
                    "bankruptcy_decision_date": _iso_date(match.group("bankruptcy_date")),
                    "bankruptcy_effective_date": _iso_date(match.group("effective_date")),
                    "bankruptcy_effective_time": match.group("effective_time"),
                    "dissolution_entry_removed": True,
                    "legacy_name_fragment": (
                        match.group("name_fragment").strip()
                        if match.group("name_fragment") else None
                    ),
                },
            )
        )

    match = _FR_ASSET_TRANSFER_WITH_LIABILITIES.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "fr.text.asset_transfer_with_liabilities.v1",
                {
                    "date": _iso_date(match.group("date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "currency": "CHF",
                    "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration": f"CHF {match.group('consideration')}",
                    "consideration_kind": "cash",
                    "consideration_amount": match.group("consideration"),
                },
            )
        )

    match = _DE_AUTHORIZED_CAPITAL_REPLACED_AFTER_EXPIRY.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.authorized_capital_replaced_after_expiry.v1",
                {
                    "kind": "authorized_capital_clause",
                    "action": "replaced_after_expiry",
                    "previous_decision_date": _iso_date(match.group("previous_date")),
                    "decision_date": _iso_date(match.group("date")),
                    "details_in_statutes": True,
                },
            )
        )

    match = _IT_FUSION_WITH_DEFICIT_COVERAGE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_merged", "it.text.fusion_with_deficit_coverage.v1",
                {
                    "kind": "absorption",
                    "absorbed_name": match.group("absorbed_name").strip(),
                    "absorbed_place": match.group("absorbed_place").strip(),
                    "absorbed_uid": match.group("absorbed_uid"),
                    "agreement_date": _iso_date(match.group("agreement_date")),
                    "balance_date": _iso_date(match.group("balance_date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "currency": "CHF",
                    "all_shares_held_by_acquirer": True,
                    "capital_increase": False,
                    "share_allocation": False,
                    "deficit_coverage_confirmed_by_auditor": True,
                },
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
