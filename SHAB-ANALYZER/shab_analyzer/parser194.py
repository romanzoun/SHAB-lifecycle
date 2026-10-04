from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_DE_DELETION_BLOCKED_TWO_TAX_AUTHORITIES_DATED_NOTICE = re.compile(
    r"^Auf die durch das Handelsregisteramt gestützt auf (?P<legal_basis>Art\.\s*934 "
    r"Abs\.\s*2 OR sowie Art\.\s*152 Abs\.\s*1 HRegV) veranlasste und im SHAB "
    r"mit Meldungsnummer (?P<issue>[A-Z0-9-]+) vom "
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}) publizierten Aufforderung haben sich "
    r"keine weiteren Betroffenen gemeldet\.\s*Das amtliche Verfahren zur Löschung "
    r"der Rechtseinheit ist damit abgeschlossen\.\s*Sie kann mangels Zustimmungen "
    r"der Eidgenössischen Steuerverwaltung und des kantonalen Steueramtes jedoch "
    r"noch nicht gelöscht werden\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_SHARES_AND_CLAIM = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Inventar per\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven von CHF\s+(?P<liabilities>[\d'.]+)\s+"
    r"\(Fremdkapital\)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:?\s*(?P<share_count>[\d']+)\s+Namenaktien zu CHF\s+"
    r"(?P<share_nominal>[\d'.]+)\s+und eine Forderung über CHF\s+"
    r"(?P<claim>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_APPEAL_UPHELD_COMPANY_CONTINUES = re.compile(
    r"^Mit Entscheid vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+wurde die Beschwerde "
    r"geschützt und das Konkursdekret über diese Gesellschaft aufgehoben\.\s*"
    r"Die Gesellschaft besteht gemäss den früheren Eintragungen weiter\.?$",
    re.I | re.UNICODE,
)
_DE_COOPERATIVE_CORRECTION_STATUTES_AUDITOR_WAIVER = re.compile(
    r"^Der Eintrag Nr\.\s*(?P<entry>[\d']+) vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(SHAB vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+(?P<notice_id>\d+)\)\s+"
    r"ist wie folgt berichtigt:\s*Mitteilung an die Genossenschafter:\s*"
    r"(?P<communication>.+?)\s*\(und nicht\s+(?P<previous_communication>[^)]+)\)\.\s*"
    r"Statuten geändert am\s+(?P<statutes_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"(?P<auditor>.+?)\s*\((?P<auditor_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+"
    r"ist nicht mehr Revisionsstelle\.\s*Gemäss Erklärung des Vorstandes vom\s+"
    r"(?P<waiver_date>\d{2}\.\d{2}\.\d{4})\s+untersteht die Gesellschaft keiner "
    r"ordentlichen Revision und verzichtet auf eine eingeschränkte Revision\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_BRANCH_SIGNATORIES = re.compile(
    r"^Signature collective à deux,\s*limitée au affaires de la succursale a été "
    r"conférée à\s+(?P<name1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*(?P<name2>[^,.;]+),\s*de\s+"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_PREVIOUS_DOMICILE_OMITTED_CORRECTION = re.compile(
    r"^Bei der letzten Publikation wurde der bisherige Wohnort nicht als "
    r"Bishereintrag aufgeführt:\s*(?P<name>[^,.;]+,\s*[^,.;]+),\s*von\s+"
    r"(?P<origin>[^,.;]+),\s*in\s+(?P<place>[^,.;]+),\s*"
    r"(?P<role>Gesellschafter und Geschäftsführer),\s*mit\s+"
    r"(?P<signing>Einzelunterschrift),\s*mit\s+(?P<count>[\d']+)\s+"
    r"Stammanteilen zu je CHF\s+(?P<nominal>[\d'.]+)\s*\[bisher:\s*in\s+"
    r"(?P<previous_place>[^,.;]+),\s*(?P<previous_role>[^,;\]]+),\s*mit\s+"
    r"(?P<previous_signing>Einzelunterschrift),\s*mit\s+"
    r"(?P<previous_count>[\d']+)\s+Stammanteilen zu je CHF\s+"
    r"(?P<previous_nominal>[\d'.]+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_SECRETARY_SIGNING_CHANGED = re.compile(
    r"^Le membre du conseil d['’]administration\s+(?P<new_secretary>[^,.;]+),\s*"
    r"nommé secrétaire,\s*signe désormais collectivement à deux\.\s*Le membre "
    r"du conseil d['’]administration\s+(?P<previous_secretary>[^,.;]+),\s*"
    r"jusqu['’]ici secrétaire,\s*n['’]exerce plus la signature\.?$",
    re.I | re.UNICODE,
)
_IT_BANKRUPTCY_APPEAL_MOOT_WITH_HISTORY = re.compile(
    r"^Con decisione del\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+la\s+"
    r"(?P<authority>.+?)\s+ha dichiarato senza oggetto il reclamo contro la "
    r"decisione di apertura del fallimento della\s+(?P<bankruptcy_authority>.+?)\s+"
    r"del\s+(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.\s*\[finora:\s*"
    r"Con decreto del\s+(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+la\s+"
    r"(?P=authority)\s+ha accordato effetto sospensivo al reclamo inoltrato contro "
    r"la decisione di apertura del fallimento della\s+(?P=bankruptcy_authority)\s+"
    r"del\s+(?P=bankruptcy_date)\.\s*L['’]iscrizione nel registro di commercio "
    r"relativa allo scioglimento della società a seguito di fallimento viene "
    r"pertanto cancellata\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_CONDITIONAL_PARTICIPATION_CAPITAL_TEXTUAL_DATES = re.compile(
    r"^Augmentation conditionnelle du capital[ -]participation fondée sur la "
    r"décision relative à l['’]octroi de droits du\s+"
    r"(?P<rights_date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.\s*"
    r"Nouveau capital-participation entièrement libéré:\s*CHF\s+"
    r"(?P<total>[\d'.]+),\s*divisé en\s+(?P<count>[\d']+)\s+bons de "
    r"participation nominatifs de CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"(?:avec restrictions quant à la transmissibilité selon statuts\.\s*)?"
    r"Le conseil d['’]administration a modifié une clause statutaire relative à "
    r"une augmentation conditionnelle du capital-participation\s*"
    r"\(selon décision relative à l['’]octroi de droits de l['’]assemblée "
    r"générale du\s+(?P<clause_date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4})\),\s*"
    r"par décision du\s+(?P<change_date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"pour le détail cf\. statuts\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_WITH_ACQUIRER_OWN_SHARES = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di\s+(?P<absorbed_name>.+?),\s*"
    r"in\s+(?P<absorbed_place>[^()]+?)\s*\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"secondo il contratto di fusione del\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"e bilancio al\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta "
    r"attivi per CHF\s+(?P<assets>[\d'.]+),\s*nei quali sono comprese tutte le "
    r"azioni della società assuntrice,\s*e passivi verso terzi per CHF\s+"
    r"(?P<liabilities>[\d'.]+)\.\s*La fusione avviene senza aumento di capitale "
    r"in quanto i soci della società trasferente,\s*a seguito della fusione,\s*"
    r"ricevono le azioni proprie della società assuntrice\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_DISSOLUTION_SIX_LIQUIDATORS = re.compile(
    r"^Selon décision de l['’](?P<authority>.+?)\s+du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*la fondation est dissoute\.\s*"
    r"Liquidateurs:\s*(?P<a1>[^,.;]+),\s*(?P<a2>[^,.;]+)\s+et\s+"
    r"(?P<a3>[^,.;]+),\s*lesquels continuent à signer collectivement à deux avec\s+"
    r"(?P<b1>[^,.;]+)\s+ou\s+(?P<b2>[^,.;]+)\s+ou\s+(?P<b3>[^,.;]+),\s*et\s+"
    r"(?P=b1),\s*(?P=b2)\s+et\s+(?P=b3),\s*lesquels continuent à signer "
    r"collectivemen(?:t)? à deux avec\s+(?P=a1)\s+ou\s+(?P=a2)\s+ou\s+(?P=a3)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_SIGNING_EXCLUSIONS_FRAGMENT = re.compile(
    r"^Nouveau membre du conseil de fondation\s+"
    r"(?:avec signature collective à deux,\s*)?toutefois pas\s+"
    r"(?P<excluded1>[^,.;]+)\s+et\s+(?P<excluded2>[^,.;]+):\s*"
    r"(?P<name>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_NAME_AND_ORGANIZATION_SEAT_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le nom exact "
    r"d['’]un associé est\s+(?P<name>[^()]+?)\s*\(et non\s+"
    r"(?P<previous_name>[^,;)]+),\s*comme publié\),\s*et que le siège exact de\s+"
    r"(?P<organization>.+?)\s*\((?P<registry_id>[^)]+)\)\s+est à\s+"
    r"(?P<seat>[^()]+?)\s*\((?P<country>[^)]+)\)\s*\(et non au\s+"
    r"(?P<previous_seat>[^()]+?)\s*\((?P<previous_country>[^)]+)\),\s*"
    r"comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_EXISTENCE_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en sens que la mention de "
    r"l['’]existence d['’]une succursale à\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s*\(et non à\s+"
    r"(?P<previous_place>[^)]+?)\s+comme publié\)\s+est inscrite\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_PRESIDENCY_FRAGMENT = re.compile(
    r"^L['’]associée-gérante\s+(?P<seller>[^,.;]+),\s*qui est élue présidente,\s*"
    r"cède\s+(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"gérant(?:\s+avec signature individuelle\.)?\s+(?P=seller)\s+reste "
    r"titulaire de\s+(?P<remaining>[\d']+)\s+"
    r"parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_NAME_CORRECTED_NO_NOTICE = re.compile(
    r"^Le nom exact d['’]un\s+(?P<role>directeur) est\s+(?P<name>[^()]+?)\s*"
    r"\(et non pas\s+(?P<previous_name>[^)]+)\)\.?$",
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
    day, month, year = raw.casefold().replace("1er", "1", 1).split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _amount(raw: str) -> Decimal:
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


def extract_parser194_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 194."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_DELETION_BLOCKED_TWO_TAX_AUTHORITIES_DATED_NOTICE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.deletion_blocked_two_tax_authorities_dated_notice.v1", {
                "kind": "deletion_blocked", "procedure_completed": True,
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "issues": [match.group("issue")],
                "notice_date": _iso_date(match.group("notice_date")),
                "affected_parties_responded": False,
                "tax_authority_consent_missing": True,
                "missing_consents": ["federal_tax_authority", "cantonal_tax_authority"],
            },
        )], ""

    match = _DE_ASSET_TRANSFER_SHARES_AND_CLAIM.fullmatch(leftover)
    if match and (
        _amount(match.group("assets")) - _amount(match.group("liabilities"))
        == _count(match.group("share_count")) * _amount(match.group("share_nominal"))
        + _amount(match.group("claim"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_shares_and_claim.v1", {
                "source_kind": "company",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "inventory_date": _iso_date(match.group("inventory_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration_kind": "registered_shares_and_claim",
                "consideration_share_count": _count(match.group("share_count")),
                "consideration_share_kind": "Namenaktien",
                "consideration_share_nominal": match.group("share_nominal"),
                "consideration_claim": match.group("claim"),
            },
        )], ""

    match = _DE_BANKRUPTCY_APPEAL_UPHELD_COMPANY_CONTINUES.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_appeal_upheld_company_continues.v1", {
                "kind": "bankruptcy_revoked", "action": "appeal_upheld",
                "decision_date": _iso_date(match.group("date")),
                "bankruptcy_decree_revoked": True, "company_continues": True,
            },
        )], ""

    match = _DE_COOPERATIVE_CORRECTION_STATUTES_AUDITOR_WAIVER.fullmatch(leftover)
    if match:
        rule_id = "de.text.cooperative_correction_statutes_auditor_waiver.v1"
        notice = {
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_id": match.group("notice_id"),
        }
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", rule_id, {
                    **notice, "kind": "member_communication", "action": "corrected",
                    "to": match.group("communication").strip(),
                    "from": match.group("previous_communication").strip(),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id,
                {"date": _iso_date(match.group("statutes_date"))},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group("auditor"),
                uid=match.group("auditor_uid"), role="Revisionsstelle",
                extra={"action": "removed", "uid": match.group("auditor_uid")},
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "audit_requirement_changed", rule_id, {
                    "kind": "limited_audit_waiver", "action": "declared",
                    "date": _iso_date(match.group("waiver_date")),
                    "declarant": "Vorstand", "ordinary_audit_required": False,
                    "limited_audit_waived": True,
                },
            ),
        ], ""

    match = _FR_TWO_BRANCH_SIGNATORIES.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_branch_signatories_collective.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "granted", "origin": match.group(f"origin{index}").strip(),
                    "scope": "branch", "limited_to_branch_affairs": True,
                    "source_wording": "au affaires",
                },
            )
            for index in (1, 2)
        ], ""

    match = _DE_PREVIOUS_DOMICILE_OMITTED_CORRECTION.fullmatch(leftover)
    if match and match.group("nominal") == match.group("previous_nominal"):
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.previous_domicile_omitted_correction.v1",
            match.group("name"), place=match.group("place"), role=match.group("role"),
            signing="Einzelunterschrift", extra={
                "action": "previous_domicile_supplemented",
                "origin": match.group("origin").strip(),
                "previous_place": match.group("previous_place").strip(),
                "previous_role": match.group("previous_role").strip(),
                "shares_count": _count(match.group("count")),
                "previous_shares_count": _count(match.group("previous_count")),
                "share_nominal": match.group("nominal"), "currency": "CHF",
            },
        )], ""

    match = _FR_SECRETARY_SIGNING_CHANGED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.board_secretary_and_signing_changed.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("new_secretary"),
                role="membre du conseil d'administration et secrétaire",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed_secretary_and_signing_changed"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("previous_secretary"),
                role="membre du conseil d'administration",
                signing="ohne Zeichnungsberechtigung", extra={
                    "action": "secretary_role_and_signing_removed",
                    "previous_role": "secrétaire", "signing_revoked": True,
                },
            ),
        ], ""

    match = _IT_BANKRUPTCY_APPEAL_MOOT_WITH_HISTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.bankruptcy_appeal_moot_with_history.v1", {
                "kind": "bankruptcy_appeal", "action": "declared_moot",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "bankruptcy_authority": match.group("bankruptcy_authority").strip(),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "previous_decision_date": _iso_date(match.group("previous_date")),
                "previous_suspensive_effect": True,
                "previous_dissolution_entry_cancelled": True,
            },
        )], ""

    match = _FR_CONDITIONAL_PARTICIPATION_CAPITAL_TEXTUAL_DATES.fullmatch(leftover)
    if match and (
        _amount(match.group("total"))
        == _count(match.group("count")) * _amount(match.group("nominal"))
        and _french_date(match.group("rights_date"))
        == _french_date(match.group("clause_date"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.conditional_participation_capital_textual_dates.v1", {
                "kind": "conditional_participation_capital", "action": "increased",
                "total": match.group("total"), "paid": match.group("total"),
                "fully_paid": True, "currency": "CHF",
                "participation_count": _count(match.group("count")),
                "participation_kind": "bons de participation nominatifs",
                "participation_nominal": match.group("nominal"),
                "transfer_restricted": True, "restriction_basis": "statutes",
                "rights_date": _french_date(match.group("rights_date")),
                "clause_action": "modified",
                "clause_change_date": _french_date(match.group("change_date")),
                "details_in_statutes": True,
            },
        )], ""

    match = _IT_MERGER_WITH_ACQUIRER_OWN_SHARES.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "it.text.merger_with_acquirer_own_shares.v1", {
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities", "currency": "CHF",
                "absorbed_assets_include_all_acquirer_shares": True,
                "capital_increase": False,
                "consideration_kind": "acquirer_own_shares",
            },
        )], ""

    match = _FR_FOUNDATION_DISSOLUTION_SIX_LIQUIDATORS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.foundation_dissolution_six_liquidators.v1"
        first_group = [match.group(f"a{index}").strip() for index in (1, 2, 3)]
        second_group = [match.group(f"b{index}").strip() for index in (1, 2, 3)]
        events = [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", rule_id, {
                "kind": "dissolution", "action": "dissolved", "scope": "foundation",
                "decision_date": _iso_date(match.group("date")),
                "authority": match.group("authority").strip(),
            },
        )]
        for name in first_group:
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, name, role="liquidateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_liquidator", "signing_continues": True,
                    "must_sign_with": second_group,
                },
            ))
        for name in second_group:
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, name, role="liquidateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_liquidator", "signing_continues": True,
                    "must_sign_with": first_group,
                },
            ))
        return events, ""

    match = _FR_FOUNDATION_MEMBER_SIGNING_EXCLUSIONS_FRAGMENT.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.foundation_member_signing_exclusions_fragment.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil de fondation",
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "appointed", "origin": match.group("origin").strip(),
                "cannot_sign_with": [
                    match.group("excluded1").strip(), match.group("excluded2").strip()
                ],
            },
        )], ""

    match = _FR_ASSOCIATE_NAME_AND_ORGANIZATION_SEAT_CORRECTED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.associate_name_and_organization_seat_corrected.v1"
        notice = {
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_ref": match.group("notice_ref"),
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"), role="associé",
                extra={
                    **notice, "action": "name_corrected",
                    "previous_name": match.group("previous_name").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("organization"),
                place=match.group("seat"), role="associée", extra={
                    **notice, "action": "seat_corrected",
                    "foreign_registry_id": match.group("registry_id").strip(),
                    "country": match.group("country").strip(),
                    "previous_seat": match.group("previous_seat").strip(),
                    "previous_country": match.group("previous_country").strip(),
                },
            ),
        ], ""

    match = _FR_BRANCH_EXISTENCE_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "fr.text.branch_existence_corrected.v1", {
                "action": "added_by_correction", "place": match.group("place").strip(),
                "branch_uid": match.group("uid"),
                "previous_place": match.group("previous_place").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_MANAGER_TRANSFER_PRESIDENCY_FRAGMENT.fullmatch(leftover)
    if match and (
        _count(match.group("before")) - _count(match.group("transferred"))
        == _count(match.group("remaining"))
        and _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and len({
            match.group("nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }) == 1
    ):
        rule_id = "fr.persons.manager_transfer_presidency_fragment.v2"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller,
                role="associée-gérante présidente", extra={
                    **common, "action": "appointed_president_and_shares_transferred",
                    "counterparty": buyer, "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé-gérant", signing="Einzelunterschrift", extra={
                    **common, "action": "appointed_and_shares_received",
                    "counterparty": seller, "origin": match.group("origin").strip(),
                    "new_associate": True, "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                },
            ),
        ], ""

    match = _FR_DIRECTOR_NAME_CORRECTED_NO_NOTICE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.director_name_corrected_no_notice.v1",
            match.group("name"), role=match.group("role"), extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
            },
        )], ""

    return [], leftover
