from __future__ import annotations

import re
from decimal import Decimal

from .keys import person_key
from .models import Event


_FR_MANAGER_SHARE_TRANSFER_AND_PRESIDENCY = re.compile(
    r"^Jusqu['’]ici titulaire de (?P<before>[\d']+) parts de CHF "
    r"(?P<nominal>[\d'.]+),\s*l['’]associé-gérant (?P<seller>[^,.;]+),\s*"
    r"nommé (?P<seller_role>président),\s*détient (?P<remaining>[\d']+) parts "
    r"de CHF (?P<remaining_nominal>[\d'.]+) par suite de cession de "
    r"(?P<transferred>[\d']+) parts à (?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à "
    r"(?P<place>[^,.;]+),\s*nouvelle associée-gérante pour "
    r"(?P<buyer_count>[\d']+) parts de CHF (?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_ASSET_TRANSFER_NEW_COMPANY_SHARES_CLAIM = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du "
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré "
    r"des actifs pour CHF (?P<assets>[\d'.]+) et des passifs envers les tiers "
    r"pour CHF (?P<liabilities>[\d'.]+),\s*à (?P<recipient>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*nouvelle société à "
    r"(?P<place>[^.]+)\.\s*Contre-prestation:\s*(?P<share_count>[\d']+) "
    r"(?P<share_kind>actions) de CHF (?P<share_nominal>[\d'.]+) et une "
    r"créance de CHF (?P<claim>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_IT_PARTIAL_BANKRUPTCY_SUSPENSION_AND_DELETION = re.compile(
    r"^Con decisione del (?P<decision_date>\d{2}\.\d{2}\.\d{4}) la "
    r"(?P<authority>.+?) ha accordato effetto sospensivo parziale al reclamo "
    r"inoltrato contro la decisione di fallimento aperto nei confronti del "
    r"(?P<subject>[^.]+?) il (?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"L['’]iscrizione nel registro di commercio relativa al fallimento del "
    r"(?P=subject) viene pertanto cancellata\.\s*\[finora:\s*Il (?P=subject) "
    r"è stato dichiarato in fallimento con decreto della (?P<previous_authority>.+?) "
    r"del (?P<previous_decision_date>\d{2}\.\d{2}\.\d{4}) a far tempo dal "
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}) alle ore "
    r"(?P<effective_time>\d{1,2}:\d{2})\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_ADMIN_SIGNING_AND_THREE_BOARD_MEMBERS = re.compile(
    r"^L['’]administrateur (?P<administrator>.+?) signe désormais "
    r"collectivement à deux\.\s*(?P<name1>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*à "
    r"(?P<place1>[^,.;]+),\s*(?P<country1>[A-Z]{2,3}),\s*"
    r"(?P<role1>président),\s*(?P<name2>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*à "
    r"(?P<place2>[^,.;]+),\s*(?P<country2>[A-Z]{2,3}),\s*et "
    r"(?P<name3>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin3>[^,.;]+),\s*à (?P<place3>[^,.;]+),\s*avec signature "
    r"individuelle sont membres du conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_DE_CONDITIONAL_AND_AUTHORIZED_CAPITAL_CHANGED = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom (?P<conditional_date>\d{2}\.\d{2}\.\d{4}) "
    r"eine Erhöhung des bedingten Kapitals gemäss näherer Umschreibung in den "
    r"Statuten beschlossen\.\s*\[bisher:\s*Die Gesellschaft hat mit Beschluss vom "
    r"(?P<previous_conditional_date>\d{2}\.\d{2}\.\d{4}) eine Änderung der "
    r"bedingten Kapitalerhöhung gemäss näherer Umschreibung in den Statuten "
    r"beschlossen\.\]\.?\s*Die Gesellschaft hat mit Beschluss vom "
    r"(?P<authorized_date>\d{2}\.\d{2}\.\d{4}) eine Anpassung des genehmigten "
    r"Kapitals gemäss näherer Umschreibung in den Statuten beschlossen\.?$",
    re.I | re.UNICODE,
)
_DE_PARTNERSHIP_CONTINUED_AS_SOLE_PROPRIETORSHIP = re.compile(
    r"^Die Gesellschaft hat sich infolge Ausscheidens des Gesellschafters "
    r"(?P<departed>.+?) aufgelöst\.\s*Die Firma ist erloschen\.\s*Der "
    r"Gesellschafter (?P<continuing>.+?) führt das Geschäft gemäss "
    r"(?P<legal_basis>Art\.\s*579 OR) als Einzelunternehmen fort\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_ACQUIRER_OWNS_ALL_SHARES = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di (?P<absorbed_name>.+?),\s*"
    r"in (?P<absorbed_place>[^()]+?)\s*"
    r"\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*secondo il contratto "
    r"di fusione del (?P<agreement_date>\d{2}\.\d{2}\.\d{4}) e bilancio al "
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta attivi per CHF "
    r"(?P<assets>[\d'.]+) e passivi verso terzi per CHF "
    r"(?P<liabilities>[\d'.]+)\.\s*La società assuntrice detiene tutte le "
    r"azioni della società trasferente,\s*per cui la fusione avviene senza "
    r"aumento di capitale e senza attribuzione di azioni\.\s*"
    r"\[(?P<correction>Data corretta del bilancio di fusione e del contratto di "
    r"fusione)\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_REINSTATED_FOR_ASSIGNED_CLAIMS = re.compile(
    r"^Die am (?P<deletion_date>\d{2}\.\d{2}\.\d{4}) gelöschte Gesellschaft "
    r"wird auf Grund des Urteils des (?P<authority>.+?) vom "
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}) nur zum Zwecke der Geltendmachung "
    r"von abgetretenen Ansprüchen nach (?P<legal_basis>Art\.\s*260 SchKG) wieder "
    r"in das Handelsregister eingetragen und besteht entsprechend den früheren "
    r"Eintragungen weiter\.\s*\[bisher:\s*Das Konkursverfahren wurde mit Urteil "
    r"des (?P<previous_authority>.+?) vom "
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4}) als geschlossen erklärt\.\s*"
    r"Die Gesellschaft wird von Amtes wegen gelöscht\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_ASSET_TRANSFER_NO_CONSIDERATION = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du "
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4}) et selon décision de "
    r"l['’]autorité de surveillance du "
    r"(?P<approval_date>\d{2}\.\d{2}\.\d{4}),\s*la fondation a transféré des "
    r"actifs de CHF (?P<assets>[\d'.]+) et des passifs envers les tiers de CHF "
    r"(?P<liabilities>[\d'.]+) à (?P<recipient>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à (?P<place>[^.]+)\.\s*"
    r"Contre-prestation:\s*aucune\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_PRESIDENT_NAME_CORRECTED_WITH_NOTICE = re.compile(
    r"^L['’]inscription (?:no|n°)\s*(?P<entry>[\d']+) du "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du "
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}) p\.\s*(?P<notice_ref>[\d/]+)\) "
    r"est rectifiée en ce sens que l['’](?P<role>administratrice présidente) "
    r"se nomme (?P<name>[^()]+?)\s*\(et non (?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_COLLECTIVE_SIGNING = re.compile(
    r"^L['’]associé (?P<name>[^,.;]+) a désormais la signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_FR_AUTHORIZED_AND_CONDITIONAL_CAPITAL_CLAUSES_MODIFIED = re.compile(
    r"^L['’]assemblée générale a modifié une clause statutaire relative à une "
    r"augmentation autorisée du capital \(selon décision du "
    r"(?P<authorized_date>\d{1,2}(?:er)?\s+[a-zéûôîàèùç]+\s+\d{4}),\s*modifiée "
    r"en dernier lieu le (?P<last_modified_date>\d{1,2}(?:er)?\s+"
    r"[a-zéûôîàèùç]+\s+\d{4})\) par décision du "
    r"(?P<decision_date>\d{1,2}(?:er)?\s+[a-zéûôîàèùç]+\s+\d{4})\.\s*"
    r"Pour les détails,\s*voir les statuts\.\s*L['’]assemblée générale a modifié "
    r"une clause statutaire relative à une augmentation conditionnelle du capital "
    r"\(selon décision du (?P<conditional_date>\d{1,2}(?:er)?\s+"
    r"[a-zéûôîàèùç]+\s+\d{4})\) par décision du "
    r"(?P<conditional_decision_date>\d{1,2}(?:er)?\s+"
    r"[a-zéûôîàèùç]+\s+\d{4})\.\s*Pour les détails,\s*voir les statuts\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ASSOCIATES_TRANSFER_EQUAL_SHARES = re.compile(
    r"^Les associés (?P<seller1>[^,.;]+?) et (?P<seller2>[^,.;]+?) cèdent "
    r"chacun (?P<transferred>[\d']+) parts de CHF (?P<nominal>[\d'.]+) à "
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à (?P<place>[^(),.;]+)\s*"
    r"\((?P<country>[^)]+)\),\s*nouvel associé avec "
    r"(?P<buyer_count>[\d']+) parts de CHF (?P<buyer_nominal>[\d'.]+),\s*"
    r"sans signature\.\s*(?P=seller1) reste titulaire de "
    r"(?P<remaining1>[\d']+) parts de CHF (?P<remaining_nominal1>[\d'.]+),\s*"
    r"et (?P=seller2),\s*de (?P<remaining2>[\d']+) parts de CHF "
    r"(?P<remaining_nominal2>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_REMOVED_PERSONS_MISSPELLED = re.compile(
    r"^Personnes radi(?:é|ée|eé)s:\s*(?P<persons>.+)\.?$",
    re.I | re.UNICODE,
)
_FR_REMOVED_PERSON_ITEM = re.compile(
    r"^(?P<name>[^,;]+),\s*(?:(?P<role>[^,;]+),\s*)?"
    r"(?P<signing>signature individuelle|procuration individuelle)$",
    re.I | re.UNICODE,
)
_DE_BRANCH_PURPOSE_CHANGED = re.compile(
    r"^Angaben zur Zweigniederlassung neu:\s*Zweck der Zweigniederlassung ist "
    r"(?P<purpose>.+?)\.\s*\[bisher:\s*Zweck der Zweigniederlassung ist "
    r"(?P<previous_purpose>.+?)\.?\]\.?$",
    re.I | re.UNICODE,
)
_FR_ORGANIZATION_TRANSFER_TO_NEW_ASSOCIATE = re.compile(
    r"^L['’]associée (?P<seller>.+?)\s*"
    r"\((?P<seller_uid>CHE-\d{3}\.\d{3}\.\d{3})\) cède "
    r"(?P<transferred>[\d']+) de ses (?P<before>[\d']+) parts de CHF "
    r"(?P<nominal>[\d'.]+) à (?P<buyer>[^,.;]+),\s*de et à "
    r"(?P<place>[^,.;]+),\s*nouvelle associée avec (?P<buyer_count>[\d']+) "
    r"parts de CHF (?P<buyer_nominal>[\d'.]+),\s*sans signature\.\s*"
    r"(?P=seller)\s*\((?P=seller_uid)\) reste titulaire de "
    r"(?P<remaining>[\d']+) parts de CHF (?P<remaining_nominal>[\d'.]+)\.?$",
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
    day, month, year = raw.casefold().replace("1er", "1").split()
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


def extract_parser174_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 174."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_MANAGER_SHARE_TRANSFER_AND_PRESIDENCY.fullmatch(leftover)
    if match and (
        _count(match.group("before")) - _count(match.group("transferred"))
        == _count(match.group("remaining"))
        and _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and len({
            match.group("nominal"), match.group("remaining_nominal"),
            match.group("buyer_nominal"),
        }) == 1
    ):
        rule_id = "fr.persons.manager_share_transfer_and_presidency.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller,
                role="associé-gérant président", extra={
                    **common, "action": "appointed_president_and_shares_transferred",
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée-gérante", extra={
                    **common, "action": "appointed_and_shares_received",
                    "origin": match.group("origin").strip(), "counterparty": seller,
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "new_associate": True,
                },
            ),
        ], ""

    match = _FR_COMPANY_ASSET_TRANSFER_NEW_COMPANY_SHARES_CLAIM.fullmatch(leftover)
    if match and (
        _amount(match.group("assets")) - _amount(match.group("liabilities"))
        == _count(match.group("share_count")) * _amount(match.group("share_nominal"))
        + _amount(match.group("claim"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.company_asset_transfer_new_company_shares_claim.v1",
            {
                "source_kind": "company",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "recipient_new_company": True,
                "consideration_kind": "shares_and_claim",
                "consideration_shares_count": _count(match.group("share_count")),
                "consideration_share_kind": match.group("share_kind").lower(),
                "consideration_share_nominal": match.group("share_nominal"),
                "consideration_claim": match.group("claim"),
            },
        )], ""

    match = _IT_PARTIAL_BANKRUPTCY_SUSPENSION_AND_DELETION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.partial_bankruptcy_suspension_and_deletion.v1",
            {
                "kind": "bankruptcy", "action": "partial_suspensive_effect_granted",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "subject": match.group("subject").strip(),
                "bankruptcy_decision_date": _iso_date(match.group("bankruptcy_date")),
                "bankruptcy_registration_deleted": True,
                "previous_authority": match.group("previous_authority").strip(),
                "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                "previous_effective_date": _iso_date(match.group("effective_date")),
                "previous_effective_time": match.group("effective_time"),
            },
        )], ""

    match = _FR_ADMIN_SIGNING_AND_THREE_BOARD_MEMBERS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administrator_signing_and_three_board_members.v1"
        events = [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", rule_id, match.group("administrator"),
            role="administrateur", signing="Kollektivunterschrift zu zweien",
            extra={"action": "signing_changed"},
        )]
        for index in (1, 2, 3):
            extra = {
                "action": "appointed", "origin": match.group(f"origin{index}").strip(),
            }
            country = match.groupdict().get(f"country{index}")
            if country:
                extra["country"] = country
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role=("président du conseil d'administration" if index == 1
                      else "membre du conseil d'administration"),
                signing="Einzelunterschrift",
                extra=extra,
            ))
        return events, ""

    match = _DE_CONDITIONAL_AND_AUTHORIZED_CAPITAL_CHANGED.fullmatch(leftover)
    if match:
        rule_id = "de.text.conditional_and_authorized_capital_changed.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "conditional_capital", "action": "increased",
                    "decision_date": _iso_date(match.group("conditional_date")),
                    "previous_decision_date": _iso_date(
                        match.group("previous_conditional_date")
                    ),
                    "details_in_statutes": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital", "action": "adjusted",
                    "decision_date": _iso_date(match.group("authorized_date")),
                    "details_in_statutes": True,
                },
            ),
        ], ""

    match = _DE_PARTNERSHIP_CONTINUED_AS_SOLE_PROPRIETORSHIP.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_deleted", "de.text.partnership_continued_as_sole_proprietorship_order.v1",
            {
                "reason": "partner_exit", "dissolved": True,
                "departed_partner": match.group("departed").strip(),
                "company_extinguished": True, "business_continued": True,
                "continuing_owner": match.group("continuing").strip(),
                "successor_legal_form": "sole_proprietorship",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
            },
        )], ""

    match = _IT_MERGER_ACQUIRER_OWNS_ALL_SHARES.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "it.text.merger_acquirer_owns_all_shares.v1", {
                "kind": "absorption", "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities", "currency": "CHF",
                "acquirer_owns_all_shares": True,
                "capital_increase": False, "share_allocation": False,
                "dates_explicitly_corrected": True,
            },
        )], ""

    match = _DE_COMPANY_REINSTATED_FOR_ASSIGNED_CLAIMS.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.company_reinstated_for_assigned_claims.v1", {
                "kind": "registration_reinstated", "action": "reinstated",
                "deletion_date": _iso_date(match.group("deletion_date")),
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "purpose": "assertion_of_assigned_claims",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "continues_under_previous_entries": True,
                "previous_action": "bankruptcy_closed_and_company_deleted",
                "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                "previous_authority": match.group("previous_authority").strip(),
            },
        )], ""

    match = _FR_FOUNDATION_ASSET_TRANSFER_NO_CONSIDERATION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.foundation_asset_transfer_no_consideration.v1", {
                "source_kind": "foundation",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "supervisory_approval_date": _iso_date(match.group("approval_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration_kind": "none",
            },
        )], ""

    match = _FR_ADMINISTRATOR_PRESIDENT_NAME_CORRECTED_WITH_NOTICE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_president_name_corrected_notice.v1",
            match.group("name"), role=match.group("role").lower(), extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_ASSOCIATE_COLLECTIVE_SIGNING.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.associate_collective_signing.v1",
            match.group("name"), role="associé",
            signing="Kollektivunterschrift zu zweien",
            extra={"action": "signing_changed"},
        )], ""

    match = _FR_AUTHORIZED_AND_CONDITIONAL_CAPITAL_CLAUSES_MODIFIED.fullmatch(leftover)
    if match:
        rule_id = "fr.text.authorized_and_conditional_capital_clauses_modified.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause", "action": "modified",
                    "authorization_date": _french_date(match.group("authorized_date")),
                    "previous_modification_date": _french_date(
                        match.group("last_modified_date")
                    ),
                    "decision_date": _french_date(match.group("decision_date")),
                    "details_in_statutes": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "conditional_capital_clause", "action": "modified",
                    "authorization_date": _french_date(match.group("conditional_date")),
                    "decision_date": _french_date(match.group("conditional_decision_date")),
                    "details_in_statutes": True,
                },
            ),
        ], ""

    match = _FR_TWO_ASSOCIATES_TRANSFER_EQUAL_SHARES.fullmatch(leftover)
    if match and (
        _count(match.group("buyer_count")) == 2 * _count(match.group("transferred"))
        and len({
            match.group("nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal1"), match.group("remaining_nominal2"),
        }) == 1
    ):
        rule_id = "fr.persons.two_associates_transfer_equal_shares.v1"
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events = []
        for index in (1, 2):
            remaining = _count(match.group(f"remaining{index}"))
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"seller{index}"),
                role="associé", extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": remaining + transferred,
                    "shares_transferred": transferred, "shares_count": remaining,
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, buyer, place=match.group("place"),
            role="associé", extra={
                "action": "shares_received", "new_associate": True,
                "origin": match.group("origin").strip(),
                "country": match.group("country").strip(),
                "counterparties": [
                    match.group("seller1").strip(), match.group("seller2").strip()
                ],
                "shares_received": 2 * transferred,
                "shares_count": _count(match.group("buyer_count")),
                "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                "without_signature": True,
            },
        ))
        return events, ""

    match = _FR_REMOVED_PERSONS_MISSPELLED.fullmatch(leftover)
    if match:
        parsed = []
        for raw_item in match.group("persons").split(";"):
            item = _FR_REMOVED_PERSON_ITEM.fullmatch(raw_item.strip())
            if not item:
                return [], text
            parsed.append(item)
        rule_id = "fr.persons.removed_list_misspelled_heading.v1"
        events = []
        for item in parsed:
            raw_signing = item.group("signing").casefold()
            is_proxy = raw_signing.startswith("procuration")
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, item.group("name"),
                role=(item.group("role") or ("fondé de procuration" if is_proxy else None)),
                signing=("Einzelprokura" if is_proxy else "Einzelunterschrift"),
                extra={"action": "removed"},
            ))
        return events, ""

    match = _DE_BRANCH_PURPOSE_CHANGED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "purpose_changed", "de.text.branch_purpose_is_changed.v1", {
                "scope": "branch", "action": "changed",
                "from": match.group("previous_purpose").strip(),
                "to": match.group("purpose").strip(),
            },
        )], ""

    match = _FR_ORGANIZATION_TRANSFER_TO_NEW_ASSOCIATE.fullmatch(leftover)
    if match and (
        _count(match.group("before")) - _count(match.group("transferred"))
        == _count(match.group("remaining"))
        and _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and len({
            match.group("nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }) == 1
    ):
        rule_id = "fr.persons.organization_transfer_to_new_associate.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, uid=match.group("seller_uid"),
                role="associée", extra={
                    "action": "shares_transferred", "organization": True,
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée", extra={
                    "action": "shares_received", "new_associate": True,
                    "origin": match.group("place").strip(),
                    "origin_same_as_place": True, "counterparty": seller,
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                    "without_signature": True,
                },
            ),
        ], ""

    return [], text
