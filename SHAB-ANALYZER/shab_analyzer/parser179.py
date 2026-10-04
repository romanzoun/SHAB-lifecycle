from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_SHARE_TRANSFER_NEW_MANAGER_AND_SELLER_PRESIDENT = re.compile(
    r"^(?P<seller>[^,.;]+) a cédé (?P<transferred>[\d']+) parts de CHF "
    r"(?P<nominal>[\d'.]+) à (?P<buyer>[^,.;]+),\s*de (?P<origin>[^,.;]+),\s*"
    r"à (?P<place>[^,.;]+),\s*(?P<country>[A-Z]),\s*nouvel associé pour "
    r"(?P<buyer_count>[\d']+) parts de CHF (?P<buyer_nominal>[\d'.]+);\s*"
    r"lequel est en outre nommé gérant avec signature collective à deux\.\s*"
    r"(?P=seller),\s*nommé président,\s*est désormais associé pour "
    r"(?P<seller_count>[\d']+) parts de CHF (?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_OWNER_BANKRUPTCY_APPEAL_GRANTED = re.compile(
    r"^In Gutheissung des Rekurses hat (?P<authority>.+?) mit Entscheid vom "
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}) den Entscheid des "
    r"(?P<bankruptcy_court>.+?) vom (?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"mit dem über den Inhaber der Konkurs eröffnet wurde,\s*aufgehoben\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_OWN_SHARES_DISTRIBUTED = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di (?P<absorbed_name>.+?),\s*"
    r"in (?P<absorbed_place>[^()]+?)\s*"
    r"\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*secondo il contratto "
    r"di fusione del (?P<agreement_date>\d{2}\.\d{2}\.\d{4}) e bilancio al "
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta attivi per CHF "
    r"(?P<assets>[\d'.]+)\s*,\s*nei quali sono comprese tutte le azioni della "
    r"società assuntrice,\s*e passivi verso terzi per CHF "
    r"(?P<liabilities>[\d'.]+)\s*\.\s*La fusione avviene senza aumento di "
    r"capitale visto che gli azionisti della società trasferente a seguito della "
    r"fusione ricevono le azioni proprie della società assuntrice\.?$",
    re.I | re.UNICODE,
)
_FR_GIVEN_NAME_CORRECTED_DIRECT = re.compile(
    r"^L['’]inscription (?:n°|no)\s*(?P<entry>[\d']+) est rectifiée en ce sens "
    r"que (?P<family_name>.+?)\s+(?P<previous_given>[^\s.]+) se prénomme en "
    r"réalité (?P<given_names>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUR_ADMINISTRATORS_ROLE_BASED_SIGNING = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé président,\s*"
    r"(?P<member1>[^,.;]+),\s*de (?P<origin1>[^,.;]+),\s*à "
    r"(?P<place1>[^,.;]+),\s*(?P<member2>[^,.;]+) et "
    r"(?P<member3>[^,.;]+),\s*tous deux de et à (?P<shared_place>[^.;]+)\.\s*"
    r"Signature individuelle du président ou collective à trois des autres "
    r"membres du conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_DE_MERGER_DEFICIT_COVERED = re.compile(
    r"^Fusion:\s*Übernahme der Aktiven und Passiven der "
    r"(?P<absorbed_name>.+?),\s*in (?P<absorbed_place>[^()]+?)\s*"
    r"\((?P<absorbed_uid>CHE-\s*\d{3}\.\d{3}\.?\d{3})\)\s*,?\s*gemäss "
    r"Fusionsvertrag vom (?P<agreement_date>\d{2}\.\d{2}\.\d{4}) und Bilanz per "
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\.\s*Aktiven von CHF "
    r"(?P<assets>[\d'.]+) und Passiven \(Fremdkapital\) von CHF "
    r"(?P<liabilities>[\d'.]+) gehen auf die übernehmende Gesellschaft über\.\s*"
    r"(?:(?P<free_equity>Die übernehmende Gesellschaft weist gemäss Bestätigung "
    r"der zugelassenen Revisionsexpertin frei verwendbare Eigenmittel im Umfang "
    r"der Unterdeckung und der Überschuldung auf)|"
    r"(?P<subordinated>Gemäss Bestätigung des zugelassenen Revisionsexperten "
    r"liegen Rangrücktrittserklärungen im Umfang der Unterdeckung und der "
    r"Überschuldung vor))\.\s*Da die übernehmende Gesellschaft sämtliche Aktien "
    r"der übertragenden Gesellschaft hält,\s*findet weder eine Kapitalerhöhung "
    r"noch eine Aktienzuteilung statt\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_MODIFIED_WITH_HISTORY = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom "
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}) die mit Beschluss vom "
    r"(?P<introduction_date>\d{2}\.\d{2}\.\d{4}) eingeführte und mit Beschlüssen "
    r"vom (?P<amendment_dates>[\d., und]+) geänderte genehmigte Kapitalerhöhung "
    r"erneut abgeändert gemäss näherer Umschreibung in den Statuten\.\s*"
    r"\[bisher:\s*Die Generalversammlung hat mit Beschluss vom "
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4}) die mit Beschluss vom "
    r"(?P=introduction_date) eingeführte und mit Beschlüssen vom "
    r"(?P<previous_amendment_dates>[\d., und]+) geänderte genehmigte "
    r"Kapitalerhöhung erneut abgeändert gemäss näherer Umschreibung in den "
    r"Statuten\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_GRANTED_WITH_HISTORY = re.compile(
    r"^Mit Entscheid vom (?P<decision_date>\d{2}\.\d{2}\.\d{4}) hat "
    r"(?P<authority>.+?) die definitive Nachlassstundung bis "
    r"(?P<until>\d{2}\.\d{2}\.\d{4}) bewilligt\.\s*"
    r"\[bisher:\s*Mit Entscheid vom "
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4}) hat (?P=authority) die am "
    r"(?P<grant_date>\d{2}\.\d{2}\.\d{4}) gewährte provisorische "
    r"Nachlassstundung bis am\s*(?P<previous_until>\d{2}\.\d{2}\.\d{4}) "
    r"verlängert\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_RESOURCES_AND_ORGANIZATION_UPDATED = re.compile(
    r"^Ressources modifiées:\s*(?P<resources>.+?)\.\s*Radiation de la rubrique "
    r"relative à l['’]organisation,\s*plus soumise à inscription\.\s*Selon le "
    r"changement de terminologie,\s*les membres du bureau sont actuellement "
    r"membres du comité\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_NAME_SUPPLEMENT_TWO_TRANSLATIONS = re.compile(
    r"^Complément:\s*l['’]inscription n°\s*(?P<entry>[\d']+) du "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du "
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\) est complétée en ce sens que la raison de "
    r"commerce exacte est:\s*(?P<name>[^()]+?)\s*\((?P<english>[^()]+)\)\s*"
    r"\((?P<german>[^()]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_SHARE_TRANSFER_NEW_MANAGER_PRESIDENT = re.compile(
    r"^L['’]associée-gérante (?P<seller>[^,.;]+) cède "
    r"(?P<transferred>[\d']+) de ses (?P<before>[\d']+) parts de CHF "
    r"(?P<nominal>[\d'.]+) à (?P<buyer>[^,.;]+),\s*du (?P<origin>[^,.;]+),\s*"
    r"à (?P<place>[^,.;]+),\s*nouvel associé avec (?P<buyer_count>[\d']+) parts "
    r"de CHF (?P<buyer_nominal>[\d'.]+),\s*gérant avec signature individuelle,\s*"
    r"président\.\s*(?P=seller) reste titulaire de (?P<seller_count>[\d']+) "
    r"parts de CHF (?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_PARTNERSHIP_CONTINUED_BY_FEMALE_OWNER = re.compile(
    r"^Die Gesellschaft hat sich infolge Ausscheidens des Gesellschafters "
    r"(?P<departed>.+?) aufgelöst\.\s*Die Firma ist erloschen\.\s*Die "
    r"Gesellschafterin (?P<continuing>.+?) führt das Geschäft gemäss "
    r"(?P<legal_basis>Art\.\s*579 OR) als Einzelunternehmen fort\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_APPOINTED_TYPO = re.compile(
    r"^Radiation de la mention relative à la renonciation à un contrôle "
    r"restreint\.\s*Orgn?e de révision:\s*(?P<name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à (?P<place>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_FREE_EQUITY_ALL_SHARES = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di (?P<absorbed_name>.+?),\s*"
    r"in (?P<absorbed_place>[^()]+?)\s*"
    r"\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*secondo contratto di "
    r"fusione del (?P<agreement_date>\d{2}\.\d{2}\.\d{4}) e bilancio al "
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta attivi per CHF "
    r"(?P<assets>[\d'.]+),\s*e passivi verso terzi per CHF "
    r"(?P<liabilities>[\d'.]+)\.\s*Conformemente all['’]attestazione di un "
    r"perito revisore abilitato,\s*la società assuntrice dispone di fondi propri "
    r"liberamente disponibili equivalenti almeno all['’]ammontare dello scoperto "
    r"e del sovraindebitamento\.\s*La società assuntrice detiene tutte le azioni "
    r"della società trasferente,\s*per cui la fusione avviene senza aumento di "
    r"capitale e senza attribuzione di azioni\.?$",
    re.I | re.UNICODE,
)
_DE_CONDITIONAL_CAPITAL_INCREASE = re.compile(
    r"^Kapitalerhöhung aus bedingtem Aktienkapital\.?$", re.I | re.UNICODE
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _dates(raw: str) -> list[str]:
    return [_iso_date(value) for value in re.findall(r"\d{2}\.\d{2}\.\d{4}", raw)]


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


def extract_parser179_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 179."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_SHARE_TRANSFER_NEW_MANAGER_AND_SELLER_PRESIDENT.fullmatch(leftover)
    if match and len({
        match.group("nominal"),
        match.group("buyer_nominal"),
        match.group("seller_nominal"),
    }) == 1 and _count(match.group("transferred")) == _count(match.group("buyer_count")):
        rule_id = "fr.persons.share_transfer_new_manager_seller_president.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant président",
                extra={
                    "action": "shares_transferred_and_appointed_president",
                    "counterparty": buyer,
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé-gérant", signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed_and_shares_received",
                    "origin": match.group("origin").strip(),
                    "country": match.group("country"), "counterparty": seller,
                    "shares_received": _count(match.group("buyer_count")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
        ], ""

    match = _DE_OWNER_BANKRUPTCY_APPEAL_GRANTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.owner_bankruptcy_appeal_granted.v1", {
                "kind": "bankruptcy_revoked", "scope": "owner",
                "appeal_outcome": "granted",
                "decision_date": _iso_date(match.group("decision_date")),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "authority": match.group("authority").strip(),
                "bankruptcy_court": match.group("bankruptcy_court").strip(),
                "previous_status_restored": True,
            },
        )], ""

    match = _IT_MERGER_OWN_SHARES_DISTRIBUTED.fullmatch(leftover)
    if match:
        return [_merger_event(
            match, publication_id, published_at, org_uid, plz, canton,
            "it.text.merger_own_shares_distributed.v1", {
                "acquirer_shares_in_transferred_assets": True,
                "own_shares_distributed_to_transferor_shareholders": True,
                "capital_increase": False,
            },
        )], ""

    match = _FR_GIVEN_NAME_CORRECTED_DIRECT.fullmatch(leftover)
    if match:
        family_name = match.group("family_name").strip()
        given_names = match.group("given_names").strip()
        previous_given = match.group("previous_given").strip()
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.given_name_corrected_direct.v1",
            f"{family_name} {given_names}", extra={
                "action": "given_name_corrected", "family_name": family_name,
                "given_names": given_names,
                "previous_name": f"{family_name} {previous_given}",
                "previous_given_names": previous_given,
                "entry": match.group("entry"),
            },
        )], ""

    match = _FR_FOUR_ADMINISTRATORS_ROLE_BASED_SIGNING.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.four_administrators_role_based_signing.v1"
        events = [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("president"),
            role="président", signing="Einzelunterschrift",
            extra={"action": "appointed_president"},
        )]
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("member1"),
            place=match.group("place1"), role="administrateur",
            signing="Kollektivunterschrift zu dreien", extra={
                "action": "appointed", "origin": match.group("origin1").strip(),
            },
        ))
        for group in ("member2", "member3"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(group),
                place=match.group("shared_place"), role="administrateur",
                signing="Kollektivunterschrift zu dreien", extra={
                    "action": "appointed",
                    "origin": match.group("shared_place").strip(),
                },
            ))
        return events, ""

    match = _DE_MERGER_DEFICIT_COVERED.fullmatch(leftover)
    if match:
        coverage = "freely_available_equity" if match.group("free_equity") else "subordinated_claims"
        return [_merger_event(
            match, publication_id, published_at, org_uid, plz, canton,
            "de.text.merger_deficit_covered_all_shares.v1", {
                "absorbed_uid": re.sub(r"\s+", "", match.group("absorbed_uid")),
                "deficit_coverage": coverage,
                "deficit_coverage_confirmed_by_auditor": True,
                "acquirer_owns_all_shares": True,
                "capital_increase": False, "share_allocation": False,
            },
        )], ""

    match = _DE_AUTHORIZED_CAPITAL_MODIFIED_WITH_HISTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_modified_history.v1", {
                "kind": "authorized_capital_clause", "action": "modified",
                "decision_date": _iso_date(match.group("decision_date")),
                "introduction_date": _iso_date(match.group("introduction_date")),
                "amendment_dates": _dates(match.group("amendment_dates")),
                "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                "previous_amendment_dates": _dates(match.group("previous_amendment_dates")),
                "details_in_statutes": True,
            },
        )], ""

    match = _DE_DEFINITIVE_MORATORIUM_GRANTED_WITH_HISTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.definitive_moratorium_granted_history.v1", {
                "kind": "composition_moratorium_granted", "action": "granted",
                "moratorium_type": "definitive",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "until": _iso_date(match.group("until")),
                "previous_moratorium_type": "provisional",
                "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                "provisional_grant_date": _iso_date(match.group("grant_date")),
                "previous_until": _iso_date(match.group("previous_until")),
            },
        )], ""

    match = _FR_RESOURCES_AND_ORGANIZATION_UPDATED.fullmatch(leftover)
    if match:
        rule_id = "fr.text.resources_and_organization_updated.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id, {
                    "kind": "resources", "action": "modified",
                    "resources": [
                        value.strip()
                        for value in match.group("resources").split(",")
                    ],
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id, {
                    "kind": "governance_terminology", "action": "updated",
                    "organization_register_section_removed": True,
                    "previous_body": "bureau", "body": "comité",
                },
            ),
        ], ""

    match = _FR_COMPANY_NAME_SUPPLEMENT_TWO_TRANSLATIONS.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_name_changed", "fr.text.company_name_supplement_two_translations.v1", {
                "action": "supplemented", "name": match.group("name").strip(),
                "translations": {
                    "en": match.group("english").strip(),
                    "de": match.group("german").strip(),
                },
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_MANAGER_SHARE_TRANSFER_NEW_MANAGER_PRESIDENT.fullmatch(leftover)
    if match and len({
        match.group("nominal"),
        match.group("buyer_nominal"),
        match.group("seller_nominal"),
    }) == 1 and _count(match.group("before")) == (
        _count(match.group("transferred")) + _count(match.group("seller_count"))
    ):
        rule_id = "fr.persons.manager_share_transfer_new_manager_president.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associée-gérante",
                extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé-gérant président", signing="Einzelunterschrift",
                extra={
                    "action": "appointed_and_shares_received",
                    "origin": match.group("origin").strip(), "counterparty": seller,
                    "shares_received": _count(match.group("buyer_count")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
        ], ""

    match = _DE_PARTNERSHIP_CONTINUED_BY_FEMALE_OWNER.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_deleted", "de.text.partnership_continued_by_female_owner.v1", {
                "reason": "partner_exit", "dissolved": True,
                "departed_partner": match.group("departed").strip(),
                "company_extinguished": True, "business_continued": True,
                "continuing_owner": match.group("continuing").strip(),
                "successor_legal_form": "sole_proprietorship",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
            },
        )], ""

    match = _FR_AUDITOR_APPOINTED_TYPO.fullmatch(leftover)
    if match:
        rule_id = "fr.text.auditor_appointed_waiver_revoked_typo.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "audit_requirement_changed", rule_id, {
                    "kind": "limited_audit_waiver", "action": "revoked",
                    "limited_audit_waived": False,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), uid=match.group("uid"),
                role="organe de révision", extra={"action": "appointed"},
            ),
        ], ""

    match = _IT_MERGER_FREE_EQUITY_ALL_SHARES.fullmatch(leftover)
    if match:
        return [_merger_event(
            match, publication_id, published_at, org_uid, plz, canton,
            "it.text.merger_free_equity_all_shares.v1", {
                "deficit_coverage": "freely_available_equity",
                "deficit_coverage_confirmed_by_auditor": True,
                "acquirer_owns_all_shares": True,
                "capital_increase": False, "share_allocation": False,
            },
        )], ""

    if _DE_CONDITIONAL_CAPITAL_INCREASE.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.conditional_capital_increase.v1", {
                "kind": "conditional_capital", "action": "increased",
                "source": "conditional_capital",
            },
        )], ""

    return [], text


def _merger_event(
    match: re.Match[str],
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
    rule_id: str,
    extra: dict,
) -> Event:
    payload = {
        "kind": "absorption",
        "absorbed_name": match.group("absorbed_name").strip(),
        "absorbed_place": match.group("absorbed_place").strip(),
        "absorbed_uid": match.group("absorbed_uid"),
        "agreement_date": _iso_date(match.group("agreement_date")),
        "balance_date": _iso_date(match.group("balance_date")),
        "assets": match.group("assets"),
        "liabilities": match.group("liabilities"),
        "liabilities_kind": "third_party_liabilities",
        "currency": "CHF",
        **extra,
    }
    return _event(
        publication_id, published_at, org_uid, plz, canton,
        "company_merged", rule_id, payload,
    )
