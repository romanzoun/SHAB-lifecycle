from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_SHARE_RESTRICTION_TAIL_AND_BANKRUPTCY_DISSOLUTION = re.compile(
    r"^(?P<legal_basis>685a Abs\. 3 OR) aufgehoben\.\s*"
    r"Auflösung der Gesellschaft durch Konkurs gemäss Entscheid der\s+"
    r"(?P<authority>.+?)\s+vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"mit Wirkung ab dem\s+(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}[.:]\d{2})\s+Uhr$",
    re.I | re.UNICODE,
)
_DE_COMPANY_REINSTATED_TO_FINISH_BANKRUPTCY = re.compile(
    r"^Die am\s+(?P<deletion_date>\d{2}\.\d{2}\.\d{4})\s+gelöschte Gesellschaft "
    r"wird auf Grund des Entscheids des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+zum Zwecke der Beendigung des "
    r"Konkursverfahrens wieder in das Handelsregister eingetragen\.\s*"
    r"\[bisher:\s*(?P<previous>.+)\]$",
    re.I | re.UNICODE,
)
_FR_INTENDED_ASSET_ACQUISITION_COMPLETED_NO_HEADING = re.compile(
    r"^La reprise de bien envisagée à la constitution a été réalisée les\s+"
    r"(?P<date1>\d{2}\.\d{2}\.\d{4})\s+et\s+"
    r"(?P<date2>\d{2}\.\d{2}\.\d{4})\s+pour le prix de CHF\s+"
    r"(?P<price>[\d'.]+)$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_PRESIDENT_NAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que le nom "
    r"de l['’]administrateur président est\s+(?P<name>[^()]+?)\s*"
    r"\(et non pas\s+(?P<previous_name>[^)]+)\)$",
    re.I | re.UNICODE,
)
_FR_OLD_HEAD_OFFICE_HEADING_RESIDUE = re.compile(r"^Ancien$", re.I | re.UNICODE)
_DE_LIQUIDATION_NAME_RESIDUE = re.compile(
    r"^Name neu:\s*(?P<name>.+? in Liquidation)$", re.I | re.UNICODE
)
_FR_TWO_BOARD_MEMBERS_WITH_PRESIDENT = re.compile(
    r"^(?P<name1>[^,.;]+),\s*de et à\s+(?P<place1>[^,.;]+),\s*"
    r"présidente,\s*et\s+(?P<name2>[^,.;]+),\s*de et à\s+"
    r"(?P<place2>[^,.;]+),\s*sont membres du conseil d['’]administration$",
    re.I | re.UNICODE,
)
_FR_TWO_LIMITED_PARTNERS_CONTRIBUTIONS_PASS = re.compile(
    r"^La commandite de\s+(?P<name1>[^,.;]+)\s+passe de CHF\s+"
    r"(?P<from1>[\d'.]+)\s+à CHF\s+(?P<to1>[\d'.]+)\.\s*"
    r"La commandite de\s+(?P<name2>[^,.;]+)\s+passe de CHF\s+"
    r"(?P<from2>[\d'.]+)\s+à CHF\s+(?P<to2>[\d'.]+)$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_TO_NEW_MANAGER_PRESIDENT = re.compile(
    r"^(?P<seller>[^,.;]+),\s*qui est maintenant de\s+"
    r"(?P<seller_origin>[^,.;]+),\s*cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*de\s+(?P<buyer_origin>[^,.;]+),\s*au\s+"
    r"(?P<buyer_place>[^,.;]+),\s*nouvelle associée-gérante présidente avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)$",
    re.I | re.UNICODE,
)
_DE_CROSS_BORDER_MERGER_FOREIGN_LLC = re.compile(
    r"^Grenzüberschreitende Fusion gemäss\s+(?P<legal_basis>Art\.\s*163a IPRG):\s*"
    r"Übernahme der Aktiven und Passiven der\s+(?P<absorbed_name>.+?),\s*in\s+"
    r"(?P<absorbed_place>[^(),]+)\s*\((?P<absorbed_country>[A-Z]{2});\s*"
    r"(?P<absorbed_registry_id>[^)]+)\),\s*"
    r"(?P<absorbed_legal_form>Gesellschaft mit beschränkter Haftung) nach dem Recht "
    r"des Staates\s+(?P<absorbed_jurisdiction>[^,.;]+),\s*gemäss Fusionsvertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Bilanz per\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von\s+"
    r"(?P<currency>[A-Z]{3})\s+(?P<assets>[\d'.]+)\s+und Fremdkapital von\s+"
    r"(?P=currency)\s+(?P<liabilities>[\d'.]+)\s+gehen auf die übernehmende "
    r"Gesellschaft über\.\s*Da dieselbe Gesellschaft sämtliche Aktien/Anteile der "
    r"an der Fusion beteiligten Gesellschaften hält,\s*findet weder eine "
    r"Kapitalerhöhung noch eine Aktienzuteilung statt$",
    re.I | re.UNICODE,
)
_FR_ONE_COLLECTIVE_SIGNATORY_NOT_TOGETHER = re.compile(
    r"^Signature collective à deux,\s*sauf entre eux a été conférée à\s+"
    r"(?P<name>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{1,3})$",
    re.I | re.UNICODE,
)
_FR_LIMITED_PARTNERS_BECOME_UNLIMITED_AND_NEW_LIMITED = re.compile(
    r"^(?P<name1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+),\s*jusqu['’]ici associés "
    r"commanditaires,\s*ont été nommés associés indéfiniment responsables\s+"
    r"Nouvel associé commanditaire:\s*(?P<new_name>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*avec une commandite de "
    r"CHF\s+(?P<contribution>[\d'.]+)$",
    re.I | re.UNICODE,
)
_FR_FOUNDING_ASSET_ACQUISITION_CLAUSE_REMOVED = re.compile(
    r"^La clause statutaire relative à la reprise de biens à la constitution est "
    r"supprimée conformément à\s+(?P<legal_basis>l['’]art\.\s*628,\s*al\.\s*4 CO)$",
    re.I | re.UNICODE,
)
_FR_NEW_COMPANY_NAME_WITH_TRANSLATION = re.compile(
    r"Nouvelle raison de commerce:\s*(?P<name>[^().]+?)\s*"
    r"\((?P<translation>[^)]+)\)\.",
    re.I | re.UNICODE,
)
_FR_VOTING_PREFERRED_SHARES_TRANSFORMED = re.compile(
    r"Les\s+(?P<preferred_count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<preferred_nominal>[\d'.]+),\s*privilégiées quant au droit de vote, "
    r"dividende et produit de liquidation et les\s+(?P<ordinary_count>[\d']+)\s+"
    r"actions nominatives de CHF\s+(?P<ordinary_nominal>[\d'.]+),\s*formant la "
    r"totalité du capital-actions,\s*sont transformées en\s+"
    r"(?P<new_count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<new_nominal>[\d'.]+),",
    re.I | re.UNICODE,
)
_FR_CONDITIONAL_CAPITAL_CLAUSE_EMBEDDED = re.compile(
    r"L['’]assemblée générale a introduit une clause statutaire relative à une "
    r"augmentation conditionnelle du capital par décision du\s+"
    r"(?P<date>\d{1,2}(?:er)?\s+(?:janvier|février|mars|avril|mai|juin|juillet|"
    r"août|septembre|octobre|novembre|décembre)\s+\d{4})\.\s*"
    r"Pour les détails,\s*voir les statuts$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_TO_ORGANIZATION_AND_TWO_MANAGERS = re.compile(
    r"^(?P<seller>[^,.;]+)\s+détient désormais\s+(?P<remaining>[\d']+)\s+parts "
    r"de CHF\s+(?P<nominal>[\d'.]+)\s+par suite de cession de\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<transfer_nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>.+?)\s*\((?P<buyer_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<buyer_place>[^,.;]+),\s*nouvelle associée pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"Nouveaux gérants:\s*(?P<manager1>[^,.;]+),\s*de\s+"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<country1>[A-Z]{1,3}),\s*président et\s+(?P<manager2>[^,.;]+),\s*de\s+"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"(?P<country2>[A-Z]{1,3}),\s*tous deux$",
    re.I | re.UNICODE,
)
_FR_TWO_ASSOCIATE_MANAGERS_ROLE_AND_SIGNING_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que les associés\s+"
    r"(?P<name1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+)\s+sont gérants\s*"
    r"\(et non avec signature individuelle,\s*comme publié\)$",
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
    day, month, year = raw.lower().replace("1er", "1").split()
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
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser124_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 124."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_SHARE_RESTRICTION_TAIL_AND_BANKRUPTCY_DISSOLUTION.search(leftover)
    if match:
        consume(match)
        common_rule = "de.text.share_restriction_tail_and_bankruptcy_dissolution.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", common_rule,
                {
                    "kind": "share_transfer_restriction", "action": "removed",
                    "legal_basis": f"Art. {match.group('legal_basis')}",
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", common_rule,
                {
                    "kind": "dissolution", "reason": "bankruptcy",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "effective_date": _iso_date(match.group("effective_date")),
                    "effective_time": match.group("effective_time").replace(".", ":"),
                    "authority": match.group("authority").strip(),
                },
            ),
        ])

    match = _DE_COMPANY_REINSTATED_TO_FINISH_BANKRUPTCY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.company_reinstated_to_finish_bankruptcy.v1",
            {
                "kind": "registration_reinstated", "action": "reinstated",
                "reason": "finish_bankruptcy_proceedings",
                "deletion_date": _iso_date(match.group("deletion_date")),
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "previous": match.group("previous").strip(),
            },
        ))

    match = _FR_INTENDED_ASSET_ACQUISITION_COMPLETED_NO_HEADING.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.intended_asset_acquisition_completed_no_heading.v1",
            {
                "kind": "intended_asset_acquisition", "action": "completed",
                "completion_dates": [
                    _iso_date(match.group("date1")), _iso_date(match.group("date2")),
                ],
                "price": match.group("price"), "currency": "CHF",
            },
        ))

    match = _FR_ADMINISTRATOR_PRESIDENT_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_president_name_corrected.v1",
            match.group("name"), role="administrateur président",
            extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _FR_OLD_HEAD_OFFICE_HEADING_RESIDUE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "fr.text.old_head_office_heading_residue.v1",
            {"kind": "head_office", "scope": "previous_head_office"},
        ))

    match = _DE_LIQUIDATION_NAME_RESIDUE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.liquidation_name_residue.v1",
            {
                "kind": "dissolution", "action": "liquidation_name_added",
                "company_name": match.group("name").strip(),
            },
        ))

    match = _FR_TWO_BOARD_MEMBERS_WITH_PRESIDENT.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_board_members_with_president.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="présidente du conseil d'administration",
                extra={"action": "appointed", "origin": match.group("place1").strip()},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="membre du conseil d'administration",
                extra={"action": "appointed", "origin": match.group("place2").strip()},
            ),
        ])

    match = _FR_TWO_LIMITED_PARTNERS_CONTRIBUTIONS_PASS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_limited_partnership_contributions_reduced.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="associé commanditaire",
                extra={
                    "action": "limited_partnership_contribution_changed",
                    "previous_limited_partnership_contribution": match.group(f"from{index}"),
                    "limited_partnership_contribution": match.group(f"to{index}"),
                    "currency": "CHF",
                },
            ))

    match = _FR_ASSOCIATE_TRANSFER_TO_NEW_MANAGER_PRESIDENT.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.associate_transfer_to_new_manager_president.v1"
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller"),
                role="associé", extra={
                    **common, "action": "shares_transferred_and_origin_changed",
                    "origin": match.group("seller_origin").strip(),
                    "previous_shares_count": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"),
                place=match.group("buyer_place"), role="associée-gérante présidente",
                signing="Einzelunterschrift", extra={
                    **common, "action": "appointed_and_shares_received",
                    "origin": match.group("buyer_origin").strip(),
                    "shares_received": _count(match.group("buyer_count")),
                    "shares_count": _count(match.group("buyer_count")),
                },
            ),
        ])

    match = _DE_CROSS_BORDER_MERGER_FOREIGN_LLC.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "de.text.cross_border_merger_foreign_llc.v1",
            {
                "kind": "cross_border_merger",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_country": match.group("absorbed_country"),
                "absorbed_registry_id": match.group("absorbed_registry_id").strip(),
                "absorbed_legal_form": match.group("absorbed_legal_form"),
                "absorbed_jurisdiction": match.group("absorbed_jurisdiction").strip(),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "currency": match.group("currency").upper(),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "same_shareholder": True, "capital_increase": False,
                "share_allocation": False,
            },
        ))

    match = _FR_ONE_COLLECTIVE_SIGNATORY_NOT_TOGETHER.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.one_collective_signatory_not_together.v1",
            match.group("name"), place=match.group("place"),
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "granted", "origin": match.group("origin").strip(),
                "country": match.group("country"), "not_with_group": True,
            },
        ))

    match = _FR_LIMITED_PARTNERS_BECOME_UNLIMITED_AND_NEW_LIMITED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.limited_partners_become_unlimited_and_new_limited.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="associé indéfiniment responsable",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "role_changed", "previous_role": "associé commanditaire"},
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("new_name"),
            place=match.group("place"), role="associé commanditaire", extra={
                "action": "appointed", "origin": match.group("origin").strip(),
                "limited_partnership_contribution": match.group("contribution"),
                "currency": "CHF",
            },
        ))

    match = _FR_FOUNDING_ASSET_ACQUISITION_CLAUSE_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.founding_asset_acquisition_clause_removed.v1",
            {
                "kind": "founding_asset_acquisition_clause", "action": "removed",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
            },
        ))

    match = _FR_NEW_COMPANY_NAME_WITH_TRANSLATION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_name_changed", "fr.text.company_name_with_translation_changed.v1",
            {
                "to": match.group("name").strip(),
                "translation": match.group("translation").strip(),
            },
        ))

    match = _FR_VOTING_PREFERRED_SHARES_TRANSFORMED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.voting_preferred_shares_transformed.v1",
            {
                "kind": "share_classes_transformed", "currency": "CHF",
                "previous_share_classes": [
                    {
                        "count": _count(match.group("preferred_count")),
                        "nominal": match.group("preferred_nominal"),
                        "registered": True, "voting_preferred": True,
                        "dividend_preferred": True, "liquidation_preferred": True,
                    },
                    {
                        "count": _count(match.group("ordinary_count")),
                        "nominal": match.group("ordinary_nominal"), "registered": True,
                    },
                ],
                "new_share_class": {
                    "count": _count(match.group("new_count")),
                    "nominal": match.group("new_nominal"), "registered": True,
                },
            },
        ))

    match = _FR_CONDITIONAL_CAPITAL_CLAUSE_EMBEDDED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.conditional_capital_clause_embedded.v1",
            {
                "kind": "conditional_capital_clause", "action": "introduced",
                "date": _french_date(match.group("date")), "details_in_statutes": True,
            },
        ))

    match = _FR_SHARE_TRANSFER_TO_ORGANIZATION_AND_TWO_MANAGERS.search(leftover)
    if match:
        consume(match)
        transfer_rule = "fr.persons.share_transfer_to_organization_and_two_managers.v1"
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", transfer_rule, match.group("seller"),
                role="associé", extra={
                    **common, "action": "shares_transferred",
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", transfer_rule, match.group("buyer"),
                place=match.group("buyer_place"), uid=match.group("buyer_uid"),
                role="associée", extra={
                    **common, "action": "appointed_and_shares_received",
                    "uid": match.group("buyer_uid"),
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                },
            ),
        ])
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", transfer_rule, match.group(f"manager{index}"),
                place=match.group(f"place{index}"),
                role="gérant président" if index == 1 else "gérant",
                signing="Einzelunterschrift", extra={
                    "action": "appointed", "origin": match.group(f"origin{index}").strip(),
                    "country": match.group(f"country{index}"),
                },
            ))

    match = _FR_TWO_ASSOCIATE_MANAGERS_ROLE_AND_SIGNING_CORRECTED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_associate_managers_role_signing_corrected.v1"
        reference = {
            "action": "role_and_signing_corrected", "previous_signing": "Einzelunterschrift",
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_ref": match.group("notice_ref"),
        }
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="associé-gérant", signing="Kollektivunterschrift zu zweien",
                extra=reference,
            ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
