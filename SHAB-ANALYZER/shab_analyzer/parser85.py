from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_LIQUIDATOR_APPOINTED_AFTER_MOVE = re.compile(
    r"^(?P<name>[^,.;]+),\s*maintenant à\s+(?P<place>[^,.;]+),\s*"
    r"est nommé(?:e)?\s+(?P<role>liquidateur|liquidatrice)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_APPOINTED_PROXY_REVOKED = re.compile(
    r"^(?P<name>[^,.;]+)\s+a été nommé(?:e)?\s+(?P<role>gérant|gérante)\s*;\s*"
    r"sa procuration est radiée\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_NON_MEMBERS_CORRECTION = re.compile(
    r"^L['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s*"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+)\s+ne sont pas membres du "
    r"conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_OPENED_FOR_DISSOLVED_COMPANY = re.compile(
    r"^Eröffnung des Konkurses gemäss Konkurserkenntnis des\s+"
    r"(?P<authority>.+?)\s+vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"mit Wirkung ab dem\s+(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}[.:]\d{2})\s+Uhr,\s*"
    r"über bereits aufgelöste Gesellschaft\.?$",
    re.I | re.UNICODE,
)
_FR_FULLY_PAID_REGISTERED_SHARE_SPLIT_AND_CLAUSE_REMOVAL = re.compile(
    r"^Division des\s+(?P<from_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<from_nominal>[\d'.]+),\s*nominatives,\s*en\s+"
    r"(?P<to_count>[\d']+)\s+actions de CHF\s+(?P<to_nominal>[\d'.]+)\.\s*"
    r"Capital-actions:\s*CHF\s+(?P<capital>[\d'.]+),\s*entièrement libéré,\s*"
    r"divisé en\s+(?P<capital_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<capital_nominal>[\d'.]+),\s*nominatives\.\s*"
    r"Suppression de la clause statutaire relative à l['’]augmentation autorisée "
    r"du capital-actions,\s*fondée sur la décision d['’]autorisation du\s*"
    r"(?P<authorization_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_AUTHORIZED_CAPITAL_CLAUSE_MODIFIED = re.compile(
    r"^Par décision du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"l['’]assemblée générale a modifié la clause statutaire du\s+"
    r"(?P<authorization_date>\d{2}\.\d{2}\.\d{4})\s+relative à une "
    r"augmentation autorisée du capital-actions selon statuts\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PRESIDENT_AND_TWO_MEMBERS = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé(?:e)? président(?:e)?,\s*"
    r"(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s*(?P<place1>[^,.;]+),\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s*(?P<place2>[^,.;]+),\s*"
    r"du président et collective à deux pour les autres membres du conseil "
    r"d['’]administration\.?$",
    re.I | re.UNICODE,
)
_IT_COMPANY_BANKRUPTCY_SUSPENDED_SAGL_FRAGMENT = re.compile(
    r"^(?P<name_fragment>.+?\bsagl)\.\s*Con decreto del\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+(?P<authority>.+?)\s+"
    r"ha accordato effetto sospensivo al reclamo inoltrato contro la decisione di "
    r"apertura del fallimento della\s+(?P<court>.+?)\s+del\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.\s*L['’]iscrizione nel registro "
    r"di commercio relativa allo scioglimento della società a seguito di fallimento "
    r"viene pertanto cancellata\.\s*\[radiati:\s*La società è sciolta in seguito a "
    r"fallimento pronunciato con decreto della\s+(?P<previous_court>.+?)\s+del\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+a far tempo dal\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4})\s+alle ore\s+"
    r"(?P<effective_time>\d{2}:\d{2})\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_LEGACY_PREVIOUS_BRANCH = re.compile(
    r"^\[bisher:\s*(?P<place>[^()]+?)\s*"
    r"\((?P<registry_id>CH-[\d. ]+-\d)\)\]\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_HEAD_OFFICE_CORRECTION = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s*"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s*"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<page>\d+)/(?P<notice_id>\d+)\)\s+est rectifiée en ce sens que par "
    r"suite de restructuration au siège principal\s*\(fusion\),\s*la nouvelle "
    r"raison de commerce du siège principal est\s+(?P<name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s*\(et non\s*"
    r"\((?P<previous_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s*comme publié\)\.?$",
    re.I | re.UNICODE,
)
_DE_PARTNERSHIP_CONTINUED_AS_NAMED_SOLE_PROPRIETORSHIP = re.compile(
    r"^(?:Diese Kollektivgesellschaft|Die Gesellschaft) hat sich infolge "
    r"Ausscheidens (?:des Gesellschafters|der Gesellschafterin)\s+"
    r"(?P<departed>.+?),\s*(?:dessen|deren) Unterschrift erloschen ist,\s*"
    r"aufgelöst\.\s*(?:Die Gesellschaft|Die Firma) ist erloschen\.\s*"
    r"Der Gesellschafter\s+(?P<continuing>.+?)"
    r"(?:,\s*in\s+(?P<continuing_place>[^,.;]+),)?\s+führt im Sinne von\s+"
    r"(?P<legal_basis>Art\.\s*579 OR)\s+das Geschäft als Einzelunternehmen "
    r"unter der Firma\s+[\"“]?(?P<successor_name>.+?)[\"”]?,\s*in\s+"
    r"(?P<successor_place>[^,.;]+),\s*fort\.?$",
    re.I | re.UNICODE,
)
_DE_DOCUMENT_LIST_SUPPLEMENTED = re.compile(
    r"^Ergänzung\s+(?:der\s+)?Liste der Belege\.?$",
    re.I | re.UNICODE,
)
_FR_BEARER_TO_REGISTERED_CAPITAL_CORRECTION = re.compile(
    r"^Rectification de la publication dans la FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+(?P<notice_id>\d+):\s*"
    r"Transformation des\s+(?P<count>[\d']+)\s+actions de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*au porteur,\s*en\s+(?P=count)\s+actions de CHF\s+"
    r"(?P=nominal),\s*nominatives\s*\(et non pas transformation des\s+"
    r"(?P<previous_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<previous_nominal>[\d'.]+),\s*au porteur,\s*en\s+"
    r"(?P=previous_count)\s+actions de CHF\s+(?P=previous_nominal),\s*"
    r"nominatives\)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_SIGNING_GRANTED = re.compile(
    r"^Signature\s+(?P<sign>individuelle)\s+a été conférée à l['’]"
    r"(?P<role>associé|associée)\s+(?P<name>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_LIMITED_SIGNING_PAIR = re.compile(
    r"^(?P<name1>[^,.;]+),\s*qui est maintenant de\s+(?P<origin1>[^,.;]+),\s*"
    r"continue à engager la succursale par une\s+"
    r"(?P<sign1>procuration collective à deux),\s*toutefois désormais limitée à "
    r"la succursale\.\s*(?P<name2>[^,.;]+)\s+continue à signer\s+"
    r"(?P<sign2>collectivement à deux),\s*toutefois désormais limité(?:e)? à la "
    r"succursale\.?$",
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


def extract_parser85_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 85."""
    del language  # Historical publications can mix languages.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_LIQUIDATOR_APPOINTED_AFTER_MOVE.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.liquidator_appointed_after_move.v1",
                match.group("name"), place=match.group("place"),
                role=match.group("role").lower(),
                extra={"action": "appointed", "domicile_changed": True},
            )
        )

    match = _FR_MANAGER_APPOINTED_PROXY_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.manager_appointed_proxy_revoked.v1",
                match.group("name"), role=match.group("role").lower(),
                extra={"action": "appointed", "procuration_revoked": True},
            )
        )

    match = _FR_BOARD_NON_MEMBERS_CORRECTION.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.board_non_members_correction.v1"
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    role="membre du conseil d'administration",
                    extra={
                        "action": "membership_corrected",
                        "never_member": True,
                        "entry": match.group("entry"),
                        "entry_date": _iso_date(match.group("entry_date")),
                    },
                )
            )

    match = _DE_BANKRUPTCY_OPENED_FOR_DISSOLVED_COMPANY.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.bankruptcy_opened_for_dissolved_company.v1",
                {
                    "kind": "bankruptcy_opened",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "effective_date": _iso_date(match.group("effective_date")),
                    "effective_time": match.group("effective_time").replace(".", ":"),
                    "authority": match.group("authority").strip(),
                    "already_dissolved": True,
                },
            )
        )

    match = _FR_FULLY_PAID_REGISTERED_SHARE_SPLIT_AND_CLAUSE_REMOVAL.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.fully_paid_registered_share_split_and_clause_removal.v1"
        events.extend(
            [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "capital_changed", rule_id,
                    {
                        "kind": "share_split",
                        "currency": "CHF",
                        "from_count": _count(match.group("from_count")),
                        "from_nominal": match.group("from_nominal"),
                        "to_count": _count(match.group("to_count")),
                        "to_nominal": match.group("to_nominal"),
                        "capital": match.group("capital"),
                        "paid_in": match.group("capital"),
                        "fully_paid": True,
                        "capital_count": _count(match.group("capital_count")),
                        "capital_nominal": match.group("capital_nominal"),
                        "registered": True,
                    },
                ),
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "capital_changed", rule_id,
                    {
                        "kind": "authorized_capital_clause",
                        "action": "removed",
                        "authorization_date": _iso_date(
                            match.group("authorization_date")
                        ),
                        "reason": "authorization_period_elapsed",
                    },
                ),
            ]
        )

    match = _FR_AUTHORIZED_CAPITAL_CLAUSE_MODIFIED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.authorized_capital_clause_modified.v2",
                {
                    "kind": "authorized_capital_clause_modified",
                    "action": "modified",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "authorization_date": _iso_date(
                        match.group("authorization_date")
                    ),
                    "details_in_statutes": True,
                },
            )
        )

    match = _FR_ADMINISTRATION_PRESIDENT_AND_TWO_MEMBERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.president_and_two_board_members.v1"
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président du conseil d'administration",
                signing="Einzelunterschrift", extra={"action": "appointed"},
            )
        )
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    place=match.group(f"place{index}"),
                    role="membre du conseil d'administration",
                    signing="Kollektivunterschrift zu zweien",
                    extra={
                        "action": "appointed",
                        "heimat": match.group(f"origin{index}").strip(),
                    },
                )
            )

    match = _IT_COMPANY_BANKRUPTCY_SUSPENDED_SAGL_FRAGMENT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "it.text.company_bankruptcy_suspended_sagl_fragment.v1",
                {
                    "kind": "bankruptcy_effect_suspended",
                    "scope": "company",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "authority": match.group("authority").strip(),
                    "bankruptcy_court": match.group("court").strip(),
                    "bankruptcy_decision_date": _iso_date(
                        match.group("bankruptcy_date")
                    ),
                    "bankruptcy_effective_date": _iso_date(
                        match.group("effective_date")
                    ),
                    "bankruptcy_effective_time": match.group("effective_time"),
                    "dissolution_entry_removed": True,
                    "legacy_name_fragment": match.group("name_fragment").strip(),
                },
            )
        )

    match = _DE_LEGACY_PREVIOUS_BRANCH.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", "de.text.legacy_previous_branch_reference.v1",
                {
                    "action": "previous_branch_reference",
                    "previous_place": match.group("place").strip(),
                    "previous_branch_registry_id": re.sub(
                        r"\s+", "", match.group("registry_id")
                    ),
                },
            )
        )

    match = _FR_BRANCH_HEAD_OFFICE_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", "fr.text.branch_head_office_correction.v1",
                {
                    "action": "head_office_corrected",
                    "reason": "head_office_merger",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_page": match.group("page"),
                    "notice_id": match.group("notice_id"),
                    "head_office_name": match.group("name").strip(),
                    "head_office_uid": match.group("uid"),
                    "previous_head_office_uid": match.group("previous_uid"),
                },
            )
        )

    match = _DE_PARTNERSHIP_CONTINUED_AS_NAMED_SOLE_PROPRIETORSHIP.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_deleted",
                "de.text.partnership_continued_as_named_sole_proprietorship.v1",
                {
                    "reason": "partner_exit",
                    "departed_partner": match.group("departed").strip(),
                    "departed_partner_signing_extinguished": True,
                    "company_extinguished": True,
                    "business_continued": True,
                    "continuing_owner": match.group("continuing").strip(),
                    "continuing_owner_place": (
                        match.group("continuing_place").strip()
                        if match.group("continuing_place") else None
                    ),
                    "successor_legal_form": "sole_proprietorship",
                    "successor_name": match.group("successor_name").strip(),
                    "successor_place": match.group("successor_place").strip(),
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                },
            )
        )

    match = _DE_DOCUMENT_LIST_SUPPLEMENTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.documents_supplemented.v1",
                {"kind": "documents_updated", "action": "supplemented"},
            )
        )

    match = _FR_BEARER_TO_REGISTERED_CAPITAL_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.bearer_to_registered_capital_correction.v1",
                {
                    "kind": "bearer_to_registered_conversion",
                    "action": "corrected",
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_id": match.group("notice_id"),
                    "currency": "CHF",
                    "shares_count": _count(match.group("count")),
                    "nominal": match.group("nominal"),
                    "from_kind": "bearer",
                    "to_kind": "registered",
                    "previously_published_shares_count": _count(
                        match.group("previous_count")
                    ),
                    "previously_published_nominal": match.group("previous_nominal"),
                },
            )
        )

    match = _FR_ASSOCIATE_SIGNING_GRANTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", "fr.persons.associate_signing_granted.v1",
                match.group("name"), role=match.group("role").lower(),
                signing="Einzelunterschrift", extra={"action": "granted"},
            )
        )

    match = _FR_BRANCH_LIMITED_SIGNING_PAIR.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.branch_limited_signing_pair.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", rule_id, match.group("name1"),
                    signing="Kollektivprokura zu zweien",
                    extra={
                        "action": "restricted",
                        "scope": "branch",
                        "continues_signing": True,
                        "heimat": match.group("origin1").strip(),
                        "origin_changed": True,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", rule_id, match.group("name2"),
                    signing="Kollektivunterschrift zu zweien",
                    extra={
                        "action": "restricted",
                        "scope": "branch",
                        "continues_signing": True,
                    },
                ),
            ]
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
