from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_UNPUBLISHED_STATUTES_POINT = re.compile(
    r"^sur un point non soumis à la publication\.?$", re.I | re.UNICODE
)
_FR_MANAGER_LIQUIDATORS = re.compile(
    r"^Liquidatrices:\s*les gérantes\s+(?P<name1>.+?)\s+et\s+(?P<name2>.+?),\s*"
    r"lesquelles continuent à signer\s+(?P<sign>individuellement)\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_REINSTATED_AND_LIQUIDATORS = re.compile(
    r"^Rectificatif:\s*la société ayant été radiée par erreur,\s*elle est "
    r"réinscrite comme ci-devant\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<page>\d+)/(?P<reference>\d+)\)\.\s*Les associés\s+"
    r"(?P<name1>.+?)\s+et\s+(?P<name2>.+?)\s+sont nommés liquidateurs avec "
    r"signature\s+(?P<sign>indi\w+)\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_SIGNING_GRANTED_PROXY_REVOKED = re.compile(
    r"^Signature\s+(?P<sign>individuelle)\s+a été conférée\s+"
    r"(?P<name>[^,.;]+),\s*nommé\s+(?P<role>directeur);\s*"
    r"sa procuration est radiée\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBERS_ABROAD = re.compile(
    r"^Nouveaux membres du conseil de fondation\s*:\s*"
    r"(?P<name1>[^,.;]+),\s*à\s*(?P<place1>[^(),.;]+)\s*"
    r"\((?P<country1>[^)]+)\),\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*à\s*(?P<place2>[^(),.;]+)\s*"
    r"\((?P<country2>[^)]+)\),\s*toutes deux du\s+"
    r"(?P<nationality>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_LIQUIDATION_TRANSLATIONS_AND_SIGNING_TYPO = re.compile(
    r"^\((?P<de>[^()]+ GmbH in Liquidation)\)\s*"
    r"\((?P<en>[^()]+ LLC in liquidation)\)\.\s*avec signature\s+"
    r"(?P<sign>indi\w+)\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBERS_PAIR = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s*(?P<place1>[^,.;]+),\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s*(?P<place2>[^,.;]+),\s*"
    r"sont membres du conseil\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_EXPIRED_AND_AMENDED = re.compile(
    r"^Streichung der Statutenbestimmung über die genehmigte Kapitalerhöhung "
    r"infolge Ablaufs der zeitlichen Befristung\.\s*\[bisher:\s*Gemäss Beschluss "
    r"der Generalversammlung vom\s+(?P<expired_authorization_date>\d{1,2}\.\d{1,2}\.\d{4})\s+"
    r"besteht ein genehmigtes Aktienkapital gemäss Umschreibung in den Statuten\.\]\.?\s*"
    r"Die Gesellschaft hat mit Beschluss vom\s+(?P<decision_date>\d{1,2}\.\d{1,2}\.\d{4})\s+"
    r"die mit Beschluss vom\s+(?P<introduction_date>\d{1,2}\.\d{1,2}\.\d{4})\s+"
    r"eingeführte und mit Beschlüssen vom\s+(?P<amendment_date1>\d{1,2}\.\d{1,2}\.\d{4})\s+"
    r"und\s+(?P<amendment_date2>\d{1,2}\.\d{1,2}\.\d{4})\s+geänderte genehmigte "
    r"Kapitalerhöhung gemäss näherer Umschreibung in den Statuten geändert\s*"
    r"\[bisher:\s*(?P<previous>.+)\]\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_AUTHORIZATION_ADAPTED = re.compile(
    r"^Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<decision_date>\d{1,2}\.\d{1,2}\.\d{4})\s+den Beschluss über die "
    r"Ermächtigung einer genehmigten Kapitalerhöhung vom\s+"
    r"(?P<authorization_date>\d{1,2}\.\d{1,2}\.\d{4})\s+gemäss näherer "
    r"Umschreibung in den Statuten angepasst\.\s*\[bisher:\s*Die Generalversammlung "
    r"hat mit Beschluss vom\s+(?P<previous_decision_date>\d{1,2}\.\d{1,2}\.\d{4})\s+"
    r"den Beschluss über die Ermächtigung einer genehmigten Kapitalerhöhung vom\s+"
    r"(?P<previous_authorization_date>\d{1,2}\.\d{1,2}\.\d{4})\s+gemäss näherer "
    r"Umschreibung in den Statuten angepasst\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_GIVEN_NAMES_CORRECTED = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+) du\s*"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s*"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\) est rectifiée en ce sens que "
    r"Madame\s+(?P<surname>[^,.;]+),\s*(?P<roles>[^,.;]+),\s*porte les prénoms\s+"
    r"(?P<given_names>[^()]+?)\s*\(et non pas\s+(?P<previous_given_names>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_IT_COMPANY_BANKRUPTCY_EFFECT_SUSPENDED = re.compile(
    r"^Con decreto del\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"(?P<authority>.+?)\s+ha accordato effetto sospensivo al reclamo inoltrato "
    r"contro la decisione di apertura del fallimento della\s+"
    r"(?P<bankruptcy_court>.+?)\s+dell['’](?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"L['’]iscrizione nel registro di commercio relativa allo scioglimento della società "
    r"a seguito di fallimento viene pertanto cancellata\.\s*\[finora:\s*"
    r"(?P<previous>La società è sciolta in seguito a fallimento pronunciato con decreto "
    r".+? a far tempo dal\s+(?P<effective_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"alle ore\s+(?P<effective_time>\d{1,2}:\d{2})\.)\]\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_TO_NEW_UNSIGNED_ASSOCIATE = re.compile(
    r"^L['’]associé\s+(?P<seller>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred>[\d']+) de ses\s+(?P<before>[\d']+) parts sociales de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s*"
    r"(?P<place>[^,.;]+),\s*nouvel associé,\s*lequel n['’]exerce pas la "
    r"signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_SELLER_TRANSFERS_TO_NEW_MANAGER = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller1>[^,.;]+)\s+cède\s+"
    r"(?P<transferred1>[\d']+) de ses\s+(?P<before1>[\d']+) parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s*"
    r"(?P<place>[^,.;]+),\s*nouvel associé-gérant\s+L['’]associée\s+"
    r"(?P<seller2>.+?)\s*\((?P<seller2_uid>CHE-[\d.]+)\)\s+cède\s+"
    r"(?P<transferred2>[\d']+) de ses\s+(?P<before2>[\d']+) parts de CHF\s+"
    r"(?P<nominal2>[\d'.]+)\s+à l['’]associé-gérant\s+(?P=buyer),\s*"
    r"désormais titulaire de\s+(?P<buyer_count>[\d']+) parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*L['’]associé-gérant\s+(?P=seller1)\s+et "
    r"l['’]associée\s+(?P=seller2)\s*\((?P=seller2_uid)\)\s+restent chacun titulaire "
    r"de\s+(?P<seller_count>[\d']+) parts de CHF\s+(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_PROCEEDINGS_SUSPENDED_TWO_DATES = re.compile(
    r"^(?P<authority>Le président du Tribunal de l['’]arrondissement de .+?)\s+"
    r"a prononcé le\s+(?P<decision_date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4})\s+l['’]effet suspensif de la procédure de "
    r"faillite le\s+(?P<bankruptcy_date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_LIQUIDATORS_DIRECTOR_AND_MEMBER = re.compile(
    r"^Liquidateurs:\s*le directeur de\s+(?P<name1>.+?)\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s*(?P<place2>[^,.;]+),\s*"
    r"(?P<country2>[A-Z]{1,3}),\s*tous deux\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_APPOINTED_AND_WAIVER_REVOKED = re.compile(
    r"^Nouvel organe de révision:\s*(?P<name>.+?)\s*"
    r"\((?P<uid>CHE-[\d.-]+)\),\s*à\s*(?P<place>[^.;]+)\.\s*"
    r"La déclaration du\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+de renonciation "
    r"à un contrôle restreint est abrogée\.?$",
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
    day, month, year = raw.lower().split()
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


def extract_parser84_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 84."""
    del language  # Historical publications can mix languages.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_UNPUBLISHED_STATUTES_POINT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "fr.text.unpublished_statutes_point_with_article.v1",
                {"kind": "non_public_changes"},
            )
        )

    match = _FR_MANAGER_LIQUIDATORS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_liquidators_continue_signing.v1"
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    role="gérante-liquidatrice", signing="Einzelunterschrift",
                    extra={"action": "appointed", "continues_signing": True},
                )
            )

    match = _FR_COMPANY_REINSTATED_AND_LIQUIDATORS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.reinstated_company_associate_liquidators.v1"
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "fr.text.company_reinstated_correction.v1",
                {
                    "kind": "registration_reinstated",
                    "reason": "erroneous_deletion",
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_page": match.group("page"),
                    "notice_reference": match.group("reference"),
                },
            )
        )
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    role="associé-liquidateur", signing="Einzelunterschrift",
                    extra={"action": "appointed"},
                )
            )

    match = _FR_DIRECTOR_SIGNING_GRANTED_PROXY_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.director_signing_granted_proxy_revoked.v1",
                match.group("name"), role=match.group("role").lower(),
                signing="Einzelunterschrift",
                extra={"action": "appointed", "procuration_revoked": True},
            )
        )

    match = _FR_FOUNDATION_MEMBERS_ABROAD.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.foundation_members_abroad_pair.v1"
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    place=match.group(f"place{index}"), role="membre du conseil de fondation",
                    signing="Kollektivunterschrift zu zweien",
                    extra={
                        "action": "appointed",
                        "country": match.group(f"country{index}").strip(),
                        "nationality": match.group("nationality").strip(),
                    },
                )
            )

    match = _FR_LIQUIDATION_TRANSLATIONS_AND_SIGNING_TYPO.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.liquidation_translations_and_signing_typo.v1"
        events.extend(
            [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "company_name_changed", rule_id,
                    {
                        "action": "translations_added",
                        "translations": {
                            "de": match.group("de").strip(),
                            "en": match.group("en").strip(),
                        },
                    },
                ),
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", rule_id,
                    {"scope": "previously_named_liquidator", "signing": "Einzelunterschrift"},
                ),
            ]
        )

    match = _FR_BOARD_MEMBERS_PAIR.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.board_members_pair_collective.v1"
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    place=match.group(f"place{index}"), role="membre du conseil",
                    signing="Kollektivunterschrift zu zweien",
                    extra={"action": "appointed", "heimat": match.group(f"origin{index}").strip()},
                )
            )

    match = _DE_AUTHORIZED_CAPITAL_EXPIRED_AND_AMENDED.search(leftover)
    if match:
        consume(match)
        events.extend(
            [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "capital_changed", "de.text.authorized_capital_expired_and_amended.v1",
                    {
                        "kind": "authorized_capital_clause",
                        "action": "removed",
                        "reason": "time_limit_expired",
                        "authorization_date": _iso_date(match.group("expired_authorization_date")),
                    },
                ),
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "capital_changed", "de.text.authorized_capital_expired_and_amended.v1",
                    {
                        "kind": "authorized_capital_clause_modified",
                        "action": "modified",
                        "decision_date": _iso_date(match.group("decision_date")),
                        "introduction_date": _iso_date(match.group("introduction_date")),
                        "previous_amendment_dates": [
                            _iso_date(match.group("amendment_date1")),
                            _iso_date(match.group("amendment_date2")),
                        ],
                        "previous": match.group("previous").strip(),
                    },
                ),
            ]
        )

    match = _DE_AUTHORIZED_CAPITAL_AUTHORIZATION_ADAPTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.authorized_capital_authorization_adapted.v1",
                {
                    "kind": "authorized_capital_clause_modified",
                    "action": "modified",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "authorization_date": _iso_date(match.group("authorization_date")),
                    "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                    "previous_authorization_date": _iso_date(
                        match.group("previous_authorization_date")
                    ),
                },
            )
        )

    match = _FR_FOUNDATION_GIVEN_NAMES_CORRECTED.search(leftover)
    if match:
        consume(match)
        name = f"{match.group('surname').strip()} {match.group('given_names').strip()}"
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.foundation_given_names_corrected.v1", name,
                role=match.group("roles").strip(),
                extra={
                    "action": "first_names_corrected",
                    "surname": match.group("surname").strip(),
                    "given_names": match.group("given_names").strip(),
                    "previous_given_names": match.group("previous_given_names").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                },
            )
        )

    match = _IT_COMPANY_BANKRUPTCY_EFFECT_SUSPENDED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "it.text.company_bankruptcy_effect_suspended_final.v1",
                {
                    "kind": "bankruptcy_effect_suspended",
                    "scope": "company",
                    "provisional": False,
                    "decision_date": _iso_date(match.group("decision_date")),
                    "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                    "bankruptcy_effective_date": _iso_date(match.group("effective_date")),
                    "bankruptcy_effective_time": match.group("effective_time"),
                    "authority": match.group("authority").strip(),
                    "bankruptcy_court": match.group("bankruptcy_court").strip(),
                    "dissolution_entry_removed": True,
                    "previous": match.group("previous").strip(),
                },
            )
        )

    match = _FR_ASSOCIATE_TRANSFER_TO_NEW_UNSIGNED_ASSOCIATE.search(leftover)
    if match:
        consume(match)
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        before = _count(match.group("before"))
        rule_id = "fr.persons.associate_transfer_to_new_unsigned_associate.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé",
                    extra={
                        "action": "shares_transferred",
                        "counterparty": buyer,
                        "shares_before": before,
                        "shares_transferred": transferred,
                        "shares_count": before - transferred,
                        "shares_nominal": match.group("nominal"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"), role="associé",
                    extra={
                        "action": "shares_received",
                        "heimat": match.group("origin").strip(),
                        "counterparty": seller,
                        "shares_received": transferred,
                        "shares_count": transferred,
                        "shares_nominal": match.group("nominal"),
                        "new_associate": True,
                        "without_signature": True,
                    },
                ),
            ]
        )

    match = _FR_TWO_SELLER_TRANSFERS_TO_NEW_MANAGER.search(leftover)
    if match:
        consume(match)
        seller1 = match.group("seller1").strip()
        seller2 = match.group("seller2").strip()
        buyer = match.group("buyer").strip()
        transferred1 = _count(match.group("transferred1"))
        transferred2 = _count(match.group("transferred2"))
        rule_id = "fr.persons.two_seller_transfers_to_new_manager.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller1, role="associé-gérant",
                    extra={
                        "action": "shares_transferred",
                        "counterparty": buyer,
                        "shares_before": _count(match.group("before1")),
                        "shares_transferred": transferred1,
                        "shares_count": _count(match.group("seller_count")),
                        "shares_nominal": match.group("seller_nominal"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller2, uid=match.group("seller2_uid"),
                    role="associée",
                    extra={
                        "action": "shares_transferred",
                        "counterparty": buyer,
                        "shares_before": _count(match.group("before2")),
                        "shares_transferred": transferred2,
                        "shares_count": _count(match.group("seller_count")),
                        "shares_nominal": match.group("seller_nominal"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé-gérant", signing="Kollektivunterschrift zu zweien",
                    extra={
                        "action": "shares_received_and_appointed",
                        "heimat": match.group("origin").strip(),
                        "counterparties": [seller1, seller2],
                        "shares_received": transferred1 + transferred2,
                        "shares_count": _count(match.group("buyer_count")),
                        "shares_nominal": match.group("buyer_nominal"),
                        "new_associate": True,
                    },
                ),
            ]
        )

    match = _FR_BANKRUPTCY_PROCEEDINGS_SUSPENDED_TWO_DATES.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "fr.text.bankruptcy_proceedings_suspended_two_dates.v1",
                {
                    "kind": "bankruptcy_effect_suspended",
                    "decision_date": _french_date(match.group("decision_date")),
                    "bankruptcy_date": _french_date(match.group("bankruptcy_date")),
                    "authority": match.group("authority").strip(),
                },
            )
        )

    match = _FR_LIQUIDATORS_DIRECTOR_AND_MEMBER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.liquidators_director_and_member.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("name1"),
                    role="directeur-liquidateur", signing="Einzelunterschrift",
                    extra={"action": "appointed"},
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("name2"),
                    place=match.group("place2"), role="liquidateur",
                    signing="Einzelunterschrift",
                    extra={
                        "action": "appointed",
                        "heimat": match.group("origin2").strip(),
                        "country": match.group("country2"),
                    },
                ),
            ]
        )

    match = _FR_AUDITOR_APPOINTED_AND_WAIVER_REVOKED.search(leftover)
    if match:
        consume(match)
        reported_uid = match.group("uid")
        normalized_uid = f"CHE-{reported_uid.removeprefix('CHE-').replace('-', '.')}"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.auditor_appointed_waiver_revoked.v1",
                    match.group("name"), place=match.group("place"), uid=normalized_uid,
                    role="organe de révision",
                    extra={"action": "appointed", "reported_uid": reported_uid},
                ),
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "audit_requirement_changed", "fr.text.audit_waiver_revoked.v1",
                    {
                        "kind": "limited_audit_waiver",
                        "action": "revoked",
                        "declaration_date": _iso_date(match.group("date")),
                    },
                ),
            ]
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
