from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_ASSOCIATE_TRANSFER_TO_TWO_EXISTING_ASSOCIATES = re.compile(
    r"^L['’]associé\s+(?P<seller>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts sociales "
    r"de CHF\s+(?P<nominal>[\d'.]+),\s*à savoir\s+"
    r"(?P<transferred1>[\d']+)\s+parts? sociale?s? de CHF\s+"
    r"(?P<nominal1>[\d'.]+)\s+à l['’]associé\s+(?P<buyer1>[^,.;]+)\s+et\s+"
    r"(?P<transferred2>[\d']+)\s+parts? sociale?s? de CHF\s+"
    r"(?P<nominal2>[\d'.]+)\s+à l['’]associé\s+(?P<buyer2>[^,.;]+),\s*"
    r"lesquels sont désormais chacun titulaire de\s+"
    r"(?P<buyer_count>[\d']+)\s+parts sociales de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ORIGIN_DOMICILE_AND_LIQUIDATOR = re.compile(
    r"^(?P<name>[^,.;]+),\s*qui est maintenant de\s+(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*est nommée liquidatrice\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_ASSET_TRANSFER_TWO_CONTRACT_DATES = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat des\s+"
    r"(?P<date1>\d{2}\.\d{2}\.\d{4})\s+et\s+"
    r"(?P<date2>\d{2}\.\d{2}\.\d{4}),\s*la fondation a transféré des "
    r"actifs de CHF\s+(?P<assets>[\d'.]+)\s+et des passifs envers les tiers "
    r"de CHF\s+(?P<liabilities>[\d'.]+),\s*à\s+(?P<recipient>.+?),\s*"
    r"à\s+(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"sans contre-prestation\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ASSOCIATES_RESTRICTED_SIGNING = re.compile(
    r"^Signature collective à deux,\s*avec la gérante,\s*a été conférée aux "
    r"associés\s+(?P<name1>[^,.;]+?)\s+et\s+(?P<name2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_MINOR_HEIR_PARENTAL_CUSTODY = re.compile(
    r"^\[gestrichen:\s*Die Erbin\s+(?P<name>[^,.;]+),\s*von\s+"
    r"(?P<origin>[^,.;]+),\s*in\s+(?P<place>[^,.;]+)\s+ist im Zeitpunkt der "
    r"Eintragung minderjährig\.\s*Sie wird durch\s+"
    r"(?P<previous_representative>.+?),\s*in\s+"
    r"(?P<previous_representative_place>[^,.;]+)\s+vertreten\.\]\.?\s*"
    r"Die Erbin\s+(?P=name),\s*von\s+(?P=origin),\s*in\s+(?P=place)\s+ist im "
    r"Zeitpunkt der Eintragung minderjährig und steht gemäss der Verfügung der\s+"
    r"(?P<authority>.+?)\s+vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+unter "
    r"elterlicher Sorge ihrer Mutter,\s*(?P<mother>[^,.;]+),\s*in\s+"
    r"(?P<mother_place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_PROVISIONAL_MORATORIUM_EXTENDED_MISSING_SPACE = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+die am\s+"
    r"(?P<grant_date>\d{2}\.\d{2}\.\d{4})\s+gewährte provisorische "
    r"Nachlassstundung bis\s+am\s*(?P<until>\d{2}\.\d{2}\.\d{4})\s+"
    r"verlängert\.\s*\[bisher:\s*Mit Entscheid vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<previous_authority>.+?)\s+eine provisorische Nachlassstundung bis\s+"
    r"(?P<previous_until>\d{2}\.\d{2}\.\d{4})\s+gewährt\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_PRESIDENT_OR_VICE_PRESIDENTS = re.compile(
    r"^Nouve(?:au|lle) membre du conseil de fondation toutefois avec le "
    r"président ou les? vices?-présidents?\s*:\s*(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_WITH_HISTORY = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+eine Änderung des bedingten Kapitals "
    r"gemäss näherer Umschreibung in den Statuten beschlossen\.\s*"
    r"\[bisher:\s*Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+eine Änderung des bedingten "
    r"Kapitals gemäss näherer Umschreibung in den Statuten beschlossen\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_PROPRIETOR_DELETION_EMPTY_CORRECTION = re.compile(
    r"^\[non:\s*\]\.?\s*L['’]inscription n['’]étant plus obligatoire\s*"
    r"\((?P<legal_basis>art\.\s*36 ORC)\),\s*l['’]entreprise individuelle est "
    r"radiée à la demande de la titulaire\.?$",
    re.I | re.UNICODE,
)
_DE_PERSON_REPLACEMENT_FRENCH_NATIONALITY = re.compile(
    r"^Gelöschte Person:\s*(?P<removed>[^,.;]+),\s*"
    r"(?P<removed_role>[^,.;]+),\s*"
    r"(?P<removed_sign>Einzelunterschrift|Kollektivunterschrift zu zweien)\.\s*"
    r"Neu eingetragene Person:\s*(?P<added>[^,.;]+),\s*"
    r"(?P<nationality>französische Staatsangehörige),\s*in\s+"
    r"(?P<place>[^,.;]+),\s*(?P<added_role>[^,.;]+),\s*"
    r"(?P<added_sign>Einzelunterschrift|Kollektivunterschrift zu zweien)\.?$",
    re.I | re.UNICODE,
)
_DE_NEW_PERSON_MISSPELLED = re.compile(
    r"^Neu eingetranene Person:\s*(?P<name>[^,.;]+),\s*von\s+"
    r"(?P<origin>[^,.;]+),\s*in\s+(?P<place>[^,.;]+),\s*"
    r"(?P<sign>Einzelunterschrift|Kollektivunterschrift zu zweien)\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_NEW_UNSIGNED_ASSOCIATE = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé sans "
    r"signature,\s*titulaire d['’](?P<buyer_count>[\d']+)\s+parts? de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*(?P=seller)\s+a maintenant\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_ENDOWMENT_CAPITAL_CHANGED = re.compile(
    r"^Dotationskapital CHF\s+(?P<capital>[\d'.]+)\.\s*"
    r"\[bisher:\s*Dotationskapital CHF\s+(?P<previous_capital>[\d'.]+)\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_CAPITAL_PREEMPTION_CORRECTION = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\)\s+est rectifiée en ce sens que "
    r"les\s+(?P<count>[\d']+)\s+actions de CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"nominatives,\s*,\s*ne sont pas munies d['’]un droit de préemption "
    r"statutaire\.\s*Capital-actions:\s*CHF\s+(?P<capital>[\d'.]+),\s*"
    r"libéré à concurrence de CHF\s+(?P<paid>[\d'.]+),\s*divisé en\s+"
    r"(?P<capital_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<capital_nominal>[\d'.]+),\s*nominatives,\s*liées selon statuts\.?$",
    re.I | re.UNICODE,
)
_IT_COMPANY_TRANSLATIONS_ADDED_DITTA = re.compile(
    r"^Nuove traduzioni della ditta:\s*\((?P<german>[^()]+)\)\s*"
    r"\((?P<english>[^()]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_TWO_MISSING_SPACES = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft\s*überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+?)\s*und\s+Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>keine)\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _signing(raw: str) -> str:
    return (
        "Einzelunterschrift"
        if "einzel" in raw.casefold()
        else "Kollektivunterschrift zu zweien"
    )


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


def extract_parser157_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 157."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_ASSOCIATE_TRANSFER_TO_TWO_EXISTING_ASSOCIATES.search(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        transferred1 = _count(match.group("transferred1"))
        transferred2 = _count(match.group("transferred2"))
        before = _count(match.group("before"))
        nominals = {
            match.group("nominal"),
            match.group("nominal1"),
            match.group("nominal2"),
            match.group("buyer_nominal"),
        }
        if transferred == transferred1 + transferred2 and before >= transferred and len(nominals) == 1:
            consume(match)
            rule_id = "fr.persons.associate_transfer_to_two_existing_associates.v1"
            seller = match.group("seller").strip()
            buyer_count = _count(match.group("buyer_count"))
            common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé",
                extra={
                    **common, "action": "shares_transferred",
                    "shares_before": before, "shares_transferred": transferred,
                    "shares_count": before - transferred,
                    "counterparties": [
                        match.group("buyer1").strip(), match.group("buyer2").strip()
                    ],
                },
            ))
            for index, received in ((1, transferred1), (2, transferred2)):
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"buyer{index}"),
                    role="associé",
                    extra={
                        **common, "action": "shares_received", "counterparty": seller,
                        "shares_received": received, "shares_count": buyer_count,
                    },
                ))

    match = _FR_ORIGIN_DOMICILE_AND_LIQUIDATOR.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.origin_domicile_appointed_liquidator.v1",
            match.group("name"), place=match.group("place"), role="liquidatrice",
            extra={
                "action": "origin_domicile_and_role_changed",
                "origin": match.group("origin").strip(),
                "domicile_changed": True,
                "appointed_liquidator": True,
            },
        ))

    match = _FR_FOUNDATION_ASSET_TRANSFER_TWO_CONTRACT_DATES.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.foundation_asset_transfer_two_contract_dates.v1",
            {
                "source_kind": "foundation",
                "agreement_dates": [
                    _iso_date(match.group("date1")), _iso_date(match.group("date2"))
                ],
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party",
                "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": "none",
                "gratuitous": True,
            },
        ))

    match = _FR_TWO_ASSOCIATES_RESTRICTED_SIGNING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_associates_signing_with_manager.v1"
        for group in ("name1", "name2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(group),
                role="associé", signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "granted", "required_with": "gérante",
                    "signing_restriction": "avec la gérante",
                },
            ))

    match = _DE_MINOR_HEIR_PARENTAL_CUSTODY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.minor_heir_parental_custody.v1",
            {
                "kind": "minor_heir_representation",
                "action": "representation_changed",
                "heir": match.group("name").strip(),
                "origin": match.group("origin").strip(),
                "place": match.group("place").strip(),
                "minor": True,
                "previous_representative": match.group("previous_representative").strip(),
                "previous_representative_place": match.group(
                    "previous_representative_place"
                ).strip(),
                "representation": "parental_custody",
                "parent": match.group("mother").strip(),
                "parent_place": match.group("mother_place").strip(),
                "authority": match.group("authority").strip(),
                "decision_date": _iso_date(match.group("date")),
            },
        ))

    match = _DE_PROVISIONAL_MORATORIUM_EXTENDED_MISSING_SPACE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.provisional_moratorium_extended_missing_space.v1",
            {
                "kind": "composition_moratorium_extended",
                "action": "extended",
                "moratorium_type": "provisional",
                "decision_date": _iso_date(match.group("decision_date")),
                "grant_date": _iso_date(match.group("grant_date")),
                "until": _iso_date(match.group("until")),
                "authority": match.group("authority").strip(),
                "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                "previous_until": _iso_date(match.group("previous_until")),
                "previous_authority": match.group("previous_authority").strip(),
                "source_spacing_malformed": True,
            },
        ))

    match = _FR_FOUNDATION_MEMBER_PRESIDENT_OR_VICE_PRESIDENTS.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.foundation_member_president_or_vice_presidents.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil de fondation",
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "appointed", "origin": match.group("origin").strip(),
                "required_with": ["président", "vice-président"],
            },
        ))

    match = _DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_WITH_HISTORY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.conditional_capital_clause_changed_history.v1",
            {
                "kind": "conditional_capital_clause",
                "action": "changed",
                "decision_date": _iso_date(match.group("date")),
                "previous_decision_date": _iso_date(match.group("previous_date")),
                "details_in_statutes": True,
            },
        ))

    match = _FR_SOLE_PROPRIETOR_DELETION_EMPTY_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.sole_proprietor_deletion_empty_correction.v1",
            {
                "kind": "sole_proprietor_deletion",
                "action": "empty_negative_marker_ignored",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis").strip()),
                "registration_no_longer_required": True,
                "deletion_requested_by_owner": True,
            },
        ))

    match = _DE_PERSON_REPLACEMENT_FRENCH_NATIONALITY.search(leftover)
    if match:
        consume(match)
        rule_id = "de.persons.replacement_french_nationality.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group("removed"),
                role=match.group("removed_role").strip(),
                signing=_signing(match.group("removed_sign")),
                extra={"action": "removed"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("added"),
                place=match.group("place"), role=match.group("added_role").strip(),
                signing=_signing(match.group("added_sign")),
                extra={"action": "appointed", "nationality": "France"},
            ),
        ])

    match = _DE_NEW_PERSON_MISSPELLED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.new_person_misspelled_eingetranene.v1",
            match.group("name"), place=match.group("place"),
            signing=_signing(match.group("sign")),
            extra={
                "action": "appointed", "origin": match.group("origin").strip(),
                "source_label_misspelled": True,
            },
        ))

    match = _FR_SHARE_TRANSFER_NEW_UNSIGNED_ASSOCIATE.search(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        before = _count(match.group("before"))
        buyer_count = _count(match.group("buyer_count"))
        remaining = _count(match.group("remaining"))
        nominals = {
            match.group("nominal"),
            match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }
        if before == transferred + remaining and buyer_count == transferred and len(nominals) == 1:
            consume(match)
            rule_id = "fr.persons.share_transfer_new_unsigned_associate_titulaire.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
            events.extend([
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé",
                    extra={
                        **common, "action": "shares_transferred", "counterparty": buyer,
                        "shares_before": before, "shares_transferred": transferred,
                        "shares_count": remaining,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé", signing="ohne Zeichnungsberechtigung",
                    extra={
                        **common, "action": "appointed_and_shares_received",
                        "counterparty": seller, "new_associate": True,
                        "origin": match.group("origin").strip(),
                        "shares_received": transferred, "shares_count": buyer_count,
                        "without_signature": True,
                    },
                ),
            ])

    match = _DE_ENDOWMENT_CAPITAL_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.endowment_capital_changed.v1",
            {
                "kind": "endowment_capital",
                "action": "changed",
                "currency": "CHF",
                "from_capital": match.group("previous_capital"),
                "to_capital": match.group("capital"),
            },
        ))

    match = _FR_SHARE_CAPITAL_PREEMPTION_CORRECTION.search(leftover)
    if match and (
        _count(match.group("count")) == _count(match.group("capital_count"))
        and match.group("nominal") == match.group("capital_nominal")
    ):
        consume(match)
        rule_id = "fr.text.share_capital_preemption_correction.v1"
        reference = {
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
        }
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", rule_id,
                {
                    **reference, "kind": "statutory_preemption_right",
                    "action": "corrected", "preemption_right": False,
                    "share_count": _count(match.group("count")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    **reference, "kind": "share_capital_confirmation",
                    "capital": match.group("capital"), "paid_in": match.group("paid"),
                    "currency": "CHF", "share_count": _count(match.group("count")),
                    "share_nominal": match.group("nominal"), "registered": True,
                    "transfer_restricted": True, "preemption_right": False,
                },
            ),
        ])

    match = _IT_COMPANY_TRANSLATIONS_ADDED_DITTA.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_name_changed", "it.text.company_translations_added_ditta.v1",
            {
                "action": "translations_added",
                "translations": {
                    "de": match.group("german").strip(),
                    "en": match.group("english").strip(),
                },
            },
        ))

    match = _DE_ASSET_TRANSFER_TWO_MISSING_SPACES.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_two_missing_spaces.v1",
            {
                "date": _iso_date(match.group("date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital",
                "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration").lower(),
                "gratuitous": True,
                "source_spacing_malformed": True,
            },
        ))

    return events, re.sub(r"\s+", " ", leftover).strip(" .,;")
