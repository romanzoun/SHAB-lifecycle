from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_FEMALE_MANAGER_SHARE_TRANSFER = re.compile(
    r"^L['’]associée-gérante\s+(?P<seller>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{1,3}),\s*nouvelle associée "
    r"pour\s+(?P<buyer_count>[\d']+)\s+parts(?: de)? CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*Gérantes:\s*les associées\s+"
    r"(?P=seller)\s+et\s+(?P=buyer),\s*nommée présidente,\s*avec "
    r"signature individuelle\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_CLASS_REGISTERED_SHARE_CAPITAL = re.compile(
    r"^Capital-actions nouveau:\s*CHF\s+(?P<total>[\d'.]+),\s*entièrement "
    r"libéré,\s*divisé en\s+(?P<count_a>[\d']+)\s+actions de CHF\s+"
    r"(?P<nominal_a>[\d'.]+),\s*nominatives,\s*de Type\s+"
    r"(?P<class_a>[^,.;]+),\s*(?P<rights_a>ordinaires),\s*et\s+"
    r"(?P<count_b>[\d']+)\s+actions de CHF\s+(?P<nominal_b>[\d'.]+),\s*"
    r"nominatives,\s*de Type\s+(?P<class_b>[^,.;]+),\s*"
    r"(?P<rights_b>privilégiées quant au dividende),\s*toutes avec restriction "
    r"de transmissibilité selon statuts\s*\(jusqu['’]ici:\s*"
    r"(?P<previous_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<previous_nominal>[\d'.]+),\s*nominatives et liées selon statuts\)\.?$",
    re.I | re.UNICODE,
)
_FR_COMMITTEE_MEMBER_WITHOUT_SIGNATURE = re.compile(
    r"^(?P<name>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+(?:\s*\([A-Z]{2}\))?),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*est membre du comité,\s*elle n['’]exerce pas "
    r"la signature\.?$",
    re.I | re.UNICODE,
)
_DE_AUDIT_WAIVER_ERRONEOUSLY_ENTERED = re.compile(
    r"^Mit dem im SHAB Nr\.\s*(?P<issue>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten TR-Eintrag "
    r"Nr\.\s*(?P<entry>[\d']+)\s+vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+wurde irrtümlich unter den "
    r"Bemerkungen der Verzicht auf die eingeschränkte Revision eingetragen\.?$",
    re.I | re.UNICODE,
)
_FR_CONTRIBUTION_CLAUSE_REPEALED = re.compile(
    r"^Faits qualifiés:\s*\[Abrogation de la clause d['’]apport en nature et "
    r"de reprise de biens\]\s*\[biffé:\s*(?P<previous>Apport en nature\s*:\s*"
    r"selon contrat du\s+(?P<date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<contributor>.+?)\s+fait apport des\s+(?P<shares_count>[\d']+)\s+"
    r"actions nominatives liées de CHF\s+(?P<share_nominal>[\d'.-]+)\s+"
    r"constituant le capital-actions de la société\s+[\"“](?P<company>[^\"”]+)"
    r"[\"”]\s+à\s+(?P<place>[^;]+);\s*la valeur de cet apport est de CHF\s+"
    r"(?P<value>[\d'.-]+),\s*accepté pour ce montant et totalement imputé sur "
    r"le capital,\s*en contrepartie,\s*l['’]apportant reçoit la totalité des "
    r"actions)\]\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_CONTINUES_WITH_EITHER = re.compile(
    r"^(?P<name>[^,.;]+)\s+continuent à signer collectivement à deux,\s*"
    r"désormais avec\s+(?P<with1>[^,.;]+)\s+ou\s+(?P<with2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_PRESIDENT_CORRECTION_AND_ADMINISTRATION = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que le "
    r"président du conseil d['’]administration est\s+(?P<president>[^,.;]+)\s+"
    r"et non pas\s+(?P<previous_president>[^,.;]+)\.\s*Administration:\s*"
    r"(?P=president),\s*président,\s*(?P=previous_president)\s+et\s+"
    r"(?P<member>[^,.;]+)\.\s*Signature collective à deux de\s+"
    r"(?P=president)\s+et\s+(?P=previous_president)\.\s*(?P=member)\s+"
    r"n['’]exerce pas la signature sociale\.?$",
    re.I | re.UNICODE,
)
_DE_STATUTES_DATE_BRACKET_CORRECTION = re.compile(
    r"^Die Statuten datieren vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"\[nicht vom\s+(?P<previous_date>\d{2}\.\d{2}\.\d{4})\]\.?$",
    re.I | re.UNICODE,
)
_DE_EXPIRED_AUTHORIZED_CAPITAL_CLAUSE_REMOVED = re.compile(
    r"^\[Streichung der bisherigen Statutenbestimmung betreffend genehmigter "
    r"Kapitalerhöhung infolge Ablauf der zeitlichen Befristung\]\s*"
    r"\[bisher:\s*Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+eine genehmigte Kapitalerhöhung gemäss "
    r"näherer Umschreibung in den Statuten beschlossen\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_BOARD_MEMBERS_WITH_PRESIDENT = re.compile(
    r"^(?P<name1>[^,.;]+),\s*d['’](?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*(?P<country1>[A-Z]{1,3}),\s*président et\s+"
    r"(?P<name2>[^,.;]+),\s*d['’](?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*(?P<country2>[A-Z]{1,3})\s+sont membres du "
    r"conseil d['’]administration avec signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_TO_MANAGER_PRESIDENT = re.compile(
    r"^(?P<seller>[^,.;]+),\s*maintenant à\s+(?P<seller_place>[^,.;]+),\s*"
    r"cède\s+(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts "
    r"de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<buyer_place>[^,.;]+),\s*nouvel associé "
    r"avec\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*gérant avec signature individuelle,\s*"
    r"président\.\s*(?P=seller)\s+"
    r"reste titulaire d['’]une part de CHF\s+(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSET_ACQUISITION_SOURCE_CORRECTED = re.compile(
    r"^Nouveaux faits qualifiés:\s*\[non:\s*La société reprend l['’]actif et "
    r"le passif de la société en nom collectif\s+[\"“](?P<previous_source>[^\"”]+)"
    r"[\"”],\s*à\s+(?P<source_place>[^,.;]+),\s*selon convention de reprise de "
    r"biens du\s+(?P<agreement_date>\d{1,2}\.\d{2}\.\d{4})\s+et bilan au\s+"
    r"(?P<balance_date>\d{1,2}\.\d{2}\.\d{4})\s+accusant un actif de CHF\s+"
    r"(?P<assets>[\d'.]+)\s+\((?P<asset_details>[^)]+)\)\s+et un passif de "
    r"CHF\s+(?P<liabilities>[\d'.]+)\s+\((?P<liability_details>[^)]+)\),\s*"
    r"soit un actif net de CHF\s+(?P<net_assets>[\d'.]+)\.\s*Le dit apport a "
    r"été accepté pour le prix de CHF\s+(?P<accepted>[\d'.]+)\s+dont CHF\s+"
    r"(?P<capital_credit>[\d'.-]+)\s+sont imputés sur le capital et le solde,\s*"
    r"soit CHF\s+(?P<balance>[\d'.]+)\s+constitue deux créances de CHF\s+"
    r"(?P<claim>[\d'.]+)\s+contre la société\]\.\s*La société reprend l['’]actif "
    r"et le passif de la société en nom collectif\s+[\"“](?P<source>[^\"”]+)"
    r"[\"”],\s*à\s+(?P=source_place),\s*selon convention de reprise de biens du\s+"
    r"(?P=agreement_date)\s+et bilan au\s+(?P=balance_date)\s+accusant un actif "
    r"de CHF\s+(?P=assets)\s+\((?P=asset_details)\)\s+et un passif de CHF\s+"
    r"(?P=liabilities)\s+\((?P=liability_details)\),\s*soit un actif net de CHF\s+"
    r"(?P=net_assets)\.\s*Le dit apport a été accepté pour le prix de CHF\s+"
    r"(?P=accepted)\s+dont CHF\s+(?P=capital_credit)\s+sont imputés sur le "
    r"capital et le solde,\s*soit CHF\s+(?P=balance)\s+constitue deux créances "
    r"de CHF\s+(?P=claim)\s+contre la société\.?$",
    re.I | re.UNICODE,
)
_FR_ROLE_CORRECTED_TO_DEPUTY_GENERAL_DIRECTOR = re.compile(
    r"^L['’]inscription No\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est corrigée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+est nommé\s+(?P<role>directeur général adjoint)\s*"
    r"\(et non pas\s+(?P<previous_role>directeur général)\)\.?$",
    re.I | re.UNICODE,
)
_FR_NON_PUBLIC_STATUTES_RESIDUAL = re.compile(
    r"^Modification des statuts\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_TWO_MANAGERS = re.compile(
    r"^(?P<seller>[^,.;]+)\s+a cédé\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{2,3})\.\s*Associés-gérants:\s*(?P=seller),\s*nommé "
    r"président,\s*et\s+(?P=buyer),\s*chacun pour\s+"
    r"(?P<shares_count>[\d']+)\s+parts de CHF\s+(?P<share_nominal>[\d'.]+),\s*"
    r"tous deux avec signature individuelle\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_HOLDING_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+est titulaire de\s+(?P<count>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s*\(et non de\s+(?P<previous_count>[\d']+)\s+parts "
    r"de CHF\s+(?P<previous_nominal>[\d'.]+)\s+comme publié\)\.?$",
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


def extract_parser203_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 203."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_FEMALE_MANAGER_SHARE_TRANSFER.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.female_manager_share_transfer_and_presidency.v1"
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller"),
                role="associée-gérante", signing="Einzelunterschrift", extra={
                    "action": "shares_transferred",
                    "counterparty": match.group("buyer").strip(),
                    "shares_transferred": _count(match.group("transferred")),
                    **common,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"),
                place=match.group("place"), role="associée-gérante et présidente",
                signing="Einzelunterschrift",
                extra={
                    "action": "appointed_and_shares_received",
                    "counterparty": match.group("seller").strip(),
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "heimat": match.group("origin").strip(),
                    "country": match.group("country"),
                    **common,
                },
            ),
        ], ""

    match = _FR_TWO_CLASS_REGISTERED_SHARE_CAPITAL.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.two_class_registered_share_capital.v1", {
                "kind": "share_structure", "action": "changed",
                "total": match.group("total"), "currency": "CHF",
                "fully_paid": True, "transfer_restricted": True,
                "share_classes": [
                    {
                        "class": match.group("class_a").strip(),
                        "count": _count(match.group("count_a")),
                        "nominal": match.group("nominal_a"),
                        "kind": "actions nominatives",
                        "rights": match.group("rights_a"),
                    },
                    {
                        "class": match.group("class_b").strip(),
                        "count": _count(match.group("count_b")),
                        "nominal": match.group("nominal_b"),
                        "kind": "actions nominatives",
                        "rights": match.group("rights_b"),
                    },
                ],
                "previous_shares_count": _count(match.group("previous_count")),
                "previous_share_nominal": match.group("previous_nominal"),
                "previous_share_kind": "actions nominatives liées selon statuts",
            },
        )], ""

    match = _FR_COMMITTEE_MEMBER_WITHOUT_SIGNATURE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.committee_member_without_signature.v1",
            match.group("name"), place=match.group("place"), role="membre du comité",
            extra={
                "action": "appointed", "heimat": match.group("origin").strip(),
                "without_signature": True,
            },
        )], ""

    match = _DE_AUDIT_WAIVER_ERRONEOUSLY_ENTERED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "audit_requirement_changed", "de.text.audit_waiver_erroneously_entered.v1", {
                "action": "erroneous_entry_corrected", "waiver": False,
                "issue": match.group("issue"),
                "notice_date": _iso_date(match.group("notice_date")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_CONTRIBUTION_CLAUSE_REPEALED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.contribution_asset_clause_repealed.v1", {
                "kind": "contribution_and_asset_acquisition_clause",
                "action": "removed", "agreement_date": _iso_date(match.group("date")),
                "contributor": match.group("contributor").strip(),
                "company": match.group("company").strip(),
                "company_place": match.group("place").strip(),
                "shares_count": _count(match.group("shares_count")),
                "share_nominal": match.group("share_nominal").rstrip(".-"),
                "accepted_value": match.group("value").rstrip(".-"),
                "currency": "CHF", "previous": match.group("previous").strip(),
            },
        )], ""

    match = _FR_SIGNING_CONTINUES_WITH_EITHER.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.signing_continues_with_either.v1",
            match.group("name"), signing="Kollektivunterschrift zu zweien", extra={
                "action": "restriction_changed", "signing_continues": True,
                "with_any_of": [match.group("with1").strip(), match.group("with2").strip()],
            },
        )], ""

    match = _FR_BOARD_PRESIDENT_CORRECTION_AND_ADMINISTRATION.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.board_president_correction_and_administration.v1"
        reference = {
            "action": "publication_corrected", "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président du conseil d'administration",
                signing="Kollektivunterschrift zu zweien", extra=reference,
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("previous_president"),
                role="membre du conseil d'administration",
                signing="Kollektivunterschrift zu zweien", extra={
                    **reference, "previous_role": "présidente du conseil d'administration",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                role="membre du conseil d'administration", extra={
                    **reference, "without_signature": True,
                },
            ),
        ], ""

    match = _DE_STATUTES_DATE_BRACKET_CORRECTION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.statutes_date_bracket_correction.v1", {
                "action": "date_corrected", "date": _iso_date(match.group("date")),
                "previous_date": _iso_date(match.group("previous_date")),
            },
        )], ""

    match = _DE_EXPIRED_AUTHORIZED_CAPITAL_CLAUSE_REMOVED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.expired_authorized_capital_clause_removed.v1", {
                "kind": "authorized_capital_clause", "action": "removed",
                "reason": "authorization_expired",
                "authorization_date": _iso_date(match.group("date")),
            },
        )], ""

    match = _FR_TWO_BOARD_MEMBERS_WITH_PRESIDENT.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_board_members_with_president.v1"
        common = {"action": "appointed"}
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"),
                role="président du conseil d'administration",
                signing="Kollektivunterschrift zu zweien", extra={
                    **common, "heimat": match.group("origin1").strip(),
                    "country": match.group("country1"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="membre du conseil d'administration",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    **common, "heimat": match.group("origin2").strip(),
                    "country": match.group("country2"),
                },
            ),
        ], ""

    match = _FR_ASSOCIATE_TRANSFER_TO_MANAGER_PRESIDENT.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.associate_transfer_to_manager_president.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, place=match.group("seller_place"),
                role="associée", extra={
                    "action": "domicile_changed_and_shares_transferred",
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": 1,
                    "share_nominal": match.group("seller_nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("buyer_place"),
                role="associé-gérant et président", signing="Einzelunterschrift", extra={
                    "action": "appointed_and_shares_received", "counterparty": seller,
                    "heimat": match.group("origin").strip(),
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ], ""

    match = _FR_ASSET_ACQUISITION_SOURCE_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.asset_acquisition_source_corrected.v1", {
                "kind": "asset_acquisition", "action": "source_name_corrected",
                "source": match.group("source").strip(),
                "previous_source": match.group("previous_source").strip(),
                "source_place": match.group("source_place").strip(),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "net_assets": match.group("net_assets"),
                "accepted_value": match.group("accepted"),
                "capital_credit": match.group("capital_credit").rstrip(".-"),
                "remaining_credit": match.group("balance"),
                "claim_count": 2, "claim_value": match.group("claim"),
                "currency": "CHF",
            },
        )], ""

    match = _FR_ROLE_CORRECTED_TO_DEPUTY_GENERAL_DIRECTOR.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.role_corrected_to_deputy_general_director.v1",
            match.group("name"), role=match.group("role"), extra={
                "action": "role_corrected", "previous_role": match.group("previous_role"),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_NON_PUBLIC_STATUTES_RESIDUAL.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.non_public_statutes_residual.v1", {
                "action": "non_public_points_changed", "non_public_changes": True,
            },
        )], ""

    match = _FR_SHARE_TRANSFER_TWO_MANAGERS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.share_transfer_two_managers.v1"
        common = {
            "shares_count": _count(match.group("shares_count")),
            "share_nominal": match.group("share_nominal"), "currency": "CHF",
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller"),
                role="associé-gérant et président", signing="Einzelunterschrift", extra={
                    "action": "shares_transferred_and_appointed_president",
                    "counterparty": match.group("buyer").strip(),
                    "shares_transferred": _count(match.group("transferred")), **common,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"),
                place=match.group("place"), role="associé-gérant",
                signing="Einzelunterschrift", extra={
                    "action": "appointed_and_shares_received",
                    "counterparty": match.group("seller").strip(),
                    "shares_received": _count(match.group("transferred")),
                    "heimat": match.group("origin").strip(),
                    "country": match.group("country"), **common,
                },
            ),
        ], ""

    match = _FR_SHARE_HOLDING_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.share_holding_corrected.v1",
            match.group("name"), role="associé", extra={
                "action": "share_holding_corrected",
                "shares_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"),
                "previous_shares_count": _count(match.group("previous_count")),
                "previous_share_nominal": match.group("previous_nominal"),
                "currency": "CHF", "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    return [], leftover
