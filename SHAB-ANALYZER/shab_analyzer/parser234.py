from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_ASSOCIATE_SHARE_NOMINAL_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+?)\s+est associé pour\s+(?P<count>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s*\(et non de CHF\s+"
    r"(?P<previous_nominal>[\d'.]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_TRANSFER_TO_UNSIGNED_ASSOCIATE = re.compile(
    r"^Les associés-gérants\s+(?P<seller1>[^,.;]+?)\s+et\s+"
    r"(?P<seller2>[^,.;]+?)\s+cèdent chacun\s+"
    r"(?P<transferred>[\d']+)\s+parts de leurs\s+(?P<before>[\d']+)\s+"
    r"parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"de et à\s+(?P<place>[^,.;]+),\s*nouvel associé avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*sans signature\.\s*"
    r"(?P=seller1)\s+et\s+(?P=seller2)\s+restent titulaires de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\s+chacun\.?$",
    re.I | re.UNICODE,
)
_FR_PRESIDENCY_CHANGED_NEW_FIRST = re.compile(
    r"^Les administrateurs\s+(?P<new_president>[^,.;]+),\s*nommé président\s+et\s+"
    r"(?P<old_president>[^,.;]+),\s*jusqu['’]ici président,\s*continuent à signer\s+"
    r"collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_TYPO_MOVED_PRESIDENT = re.compile(
    r"^Adminisration:\s*(?P<president>[^,.;]+),\s*maintenant domicilié à\s+"
    r"(?P<president_place>[^,.;]+),\s*(?P<president_country>[^,.;]+),\s*"
    r"nommé président\s+et\s+(?P<member>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<member_place>[^,.;]+),\s*"
    r"lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_APPOINTED_MANAGER_PRESIDENT = re.compile(
    r"^L['’]associé\s+(?P<name>[^,.;]+?)\s+a été nommé\s+"
    r"gérant(?:[- ]président| président)"
    r"(?:\s+avec signature individuelle)?\.?$",
    re.I | re.UNICODE,
)
_DE_AUDITOR_LEGACY_REGISTRY_ID_OMITTED = re.compile(
    r"^Unter der TR-Nr\.\s*(?P<entry>[\d']+)\s+vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+im SHAB Nr\.\s*"
    r"(?P<issue>\d+)\s+vom\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"wurde bei der Revisionsstelle die bisherige Firmennummer\s+"
    r"(?P<legacy_id>CH-[\d.]+-\d)\s+nicht aufgeführt\.?$",
    re.I | re.UNICODE,
)
_FR_ASSET_TRANSFER_CONSIDERATION_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que la "
    r"contre-prestation du transfert de patrimoine s['’]élève à CHF\s+"
    r"(?P<consideration>[\d'.]+)\s*\(et non à CHF\s+"
    r"(?P<previous_consideration>[\d'.]+)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_SIGNATURE_GRANTED = re.compile(
    r"^Signature collective à deux limitée à la succursale est conférée à\s+"
    r"(?P<name>[^,.;]+),\s*de et à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_PUBLIC_INSTITUTION_TRANSFORMED_TO_FOUNDATION = re.compile(
    r"^Urkunde neu:\s*(?P<deed_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"Umwandlung:\s*Das\s+(?P<previous_form>Institut des öffentlichen Rechts)\s+"
    r"wird gemäss\s+(?P<legal_basis>.+?)\s+vom\s+"
    r"(?P<legal_basis_date>\d{2}\.\d{2}\.\d{4}),\s*Beschluss des\s+"
    r"(?P<decision_body>Gemeinderates)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*Umwandlungsplan vom\s+"
    r"(?P<plan_date>\d{2}\.\d{2}\.\d{4})\s+inkl\.\s+Korrigendum vom\s+"
    r"(?P<corrigendum_date>\d{2}\.\d{2}\.\d{4})\s+und Inventar per\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4}),\s*Urnenabstimmung vom\s+"
    r"(?P<vote_date>\d{2}\.\d{2}\.\d{4})\s+und Genehmigung des "
    r"Regierungsrates vom\s+(?P<approval_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"mit Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+und Passiven\s*"
    r"\(Fremdkapital\)\s+von CHF\s+(?P<liabilities>[\d'.]+)\s+in eine\s+"
    r"(?P<new_form>privatrechtliche Stiftung)\s+gleichen Namens umgewandelt\.\s*"
    r"Rechtsform neu:\s*(?P<legal_form>Stiftung)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_SIGNATORIES_NOW_WITH_PERSON = re.compile(
    r"^(?P<name1>[^,.;]+?)\s+et\s+(?P<name2>[^,.;]+?)\s+continuent à signer "
    r"collectivement à deux,\s*toutefois désormais avec\s+"
    r"(?P<with_person>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_SIGNING_RESTRICTIONS_REMOVED = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?P<role1>secrétaire hors conseil),\s*et\s+"
    r"(?P<name2>[^,.;]+)\s+continuent de signer collectivement à deux,\s*"
    r"mais désormais sans autre restriction\.?$",
    re.I | re.UNICODE,
)
_DE_LEGACY_CONTRIBUTION_FRAGMENT = re.compile(
    r'^eingetragenen Einzelfirma\s+["“](?P<business>.+?)["”],\s*in\s+'
    r"(?P<place>[^,.;]+),\s*gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Übernahmebilanz per\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\s+mit Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven von CHF\s+"
    r"(?P<liabilities>[\d'.]+),\s*wofür CHF\s+(?P<credited>[\d'.]+)\s+"
    r"auf das Stammkapital angerechnet und CHF\s+(?P<receivable>[\d'.]+)\s+"
    r"als Forderung gutgeschrieben werden\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_RENAMED_AND_TWO_PEOPLE_MOVED = re.compile(
    r"^(?P<previous_name>[^,.;]+),\s*laquelle se nomme maintenant\s+"
    r"(?P<name>.+?),\s*et\s+(?P<name2>[^,.;]+)\s+sont désormais à\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_AND_OTHER_APPOINTED_LIQUIDATORS = re.compile(
    r"^Liquidateurs:\s*l['’]administrateur\s+(?P<administrator>[^,.;]+?)\s+et\s+"
    r"(?P<liquidator>[^,.;]+),\s*lesquels continuent à signer "
    r"individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_JUDGMENT_NOT_EXECUTED = re.compile(
    r"^Par courrier du\s+(?P<letter_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"l['’](?P<authority>Office cantonal des faillites)\s+a refusé d['’]exécuter "
    r"le jugement déclaratif de faillite rendu le\s+"
    r"(?P<judgment_date>\d{2}\.\d{2}\.\d{4})\.\s*De ce fait,\s*"
    r"l['’]inscription\s+No\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est annulée\.?$",
    re.I | re.UNICODE,
)
_DE_COMPOSITION_AGREEMENT_WITH_LIQUIDATOR_AND_COMMITTEE = re.compile(
    r"^Mit Entscheid des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wird der gerichtliche "
    r"Nachlassvertrag mit Vermögensabtretung vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+in Verbindung mit den "
    r"Zustimmungserklärungen der Gläubiger bestätigt und für sämtliche Gläubiger "
    r"als verbindlich erklärt\.\s*Es wird festgehalten,\s*dass die "
    r"Gläubigerversammlung vom\s+(?P<meeting_date>\d{2}\.\d{2}\.\d{4})\s+als "
    r"Liquidatorin\s+(?P<liquidator>.+?),\s*handelnd durch\s+"
    r"(?P<representative>[^,.;]+),\s*(?P<profession>[^,.;]+),\s*"
    r"(?P<street>[^,.;]+),\s*(?P<postal_code>\d{4})\s+"
    r"(?P<place>[^,.;]+)\s+und in den Gläubigerausschuss die Herren\s+"
    r"(?P<member1>[^,.;]+),\s*(?P<member2>[^,.;]+)\s+und\s+"
    r"(?P<member3>[^,.;]+)\s+gewählt hat\.\s*\[bisher:\s*Mit Entscheid vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+hat der\s+"
    r"(?P<previous_authority>.+?)\s+die definitive Nachlassstundung bis\s+"
    r"(?P<previous_until>\d{2}\.\d{2}\.\d{4})\s+bewilligt\.\]\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", "").replace(".", ""))


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


def extract_parser234_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 234."""
    del language  # Historical publications regularly contain another language.
    leftover = text.strip()

    match = _FR_ASSOCIATE_SHARE_NOMINAL_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_share_nominal_corrected.v1",
            match.group("name"), role="associé", extra={
                "action": "share_nominal_corrected",
                "shares_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"),
                "previous_share_nominal": match.group("previous_nominal"),
                "currency": "CHF", "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_TWO_MANAGERS_TRANSFER_TO_UNSIGNED_ASSOCIATE.fullmatch(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        before = _count(match.group("before"))
        remaining = _count(match.group("remaining"))
        buyer_count = _count(match.group("buyer_count"))
        nominals = {
            match.group("nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }
        if (
            len(nominals) == 1
            and before - transferred == remaining
            and transferred * 2 == buyer_count
        ):
            rule_id = "fr.persons.two_managers_transfer_unsigned_associate.v1"
            buyer = match.group("buyer").strip()
            common = {
                "currency": "CHF", "share_nominal": match.group("nominal"),
                "shares_before": before, "shares_transferred": transferred,
                "shares_count": remaining, "counterparty": buyer,
            }
            events = [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"seller{index}"),
                    role="associé-gérant", extra={
                        **common, "action": "shares_transferred",
                    },
                )
                for index in (1, 2)
            ]
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé", extra={
                    "action": "shares_received", "new_associate": True,
                    "signing_authority": False, "shares_received": buyer_count,
                    "shares_count": buyer_count, "share_nominal": match.group("nominal"),
                    "currency": "CHF",
                    "counterparties": [
                        match.group("seller1").strip(), match.group("seller2").strip(),
                    ],
                },
            ))
            return events, ""

    match = _FR_PRESIDENCY_CHANGED_NEW_FIRST.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.presidency_changed_new_first.v1"
        signing = "Kollektivunterschrift zu zweien"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("new_president"),
                role="administrateur et président", signing=signing, extra={
                    "action": "appointed_president", "signing_continues": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("old_president"),
                role="administrateur", signing=signing, extra={
                    "action": "presidency_ended", "previous_role": "président",
                    "signing_continues": True,
                },
            ),
        ], ""

    match = _FR_ADMINISTRATION_TYPO_MOVED_PRESIDENT.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administration_typo_moved_president.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                place=match.group("president_place"), role="président",
                signing="Einzelunterschrift", extra={
                    "action": "domicile_changed_and_appointed_president",
                    "country": match.group("president_country").strip(),
                    "source_wording": "Adminisration",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                place=match.group("member_place"), role="administrateur",
                signing="Einzelunterschrift", extra={
                    "action": "appointed", "origin": match.group("origin").strip(),
                    "source_wording": "Adminisration",
                },
            ),
        ], ""

    match = _FR_ASSOCIATE_APPOINTED_MANAGER_PRESIDENT.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_appointed_manager_president.v1",
            match.group("name"), role="associé-gérant président",
            signing="Einzelunterschrift", extra={
                "action": "appointed_manager_president", "previous_role": "associé",
            },
        )], ""

    match = _DE_AUDITOR_LEGACY_REGISTRY_ID_OMITTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.auditor_legacy_registry_id_omitted.v1", {
                "kind": "auditor_registry_identifier",
                "action": "omission_corrected", "role": "Revisionsstelle",
                "legacy_registry_id": match.group("legacy_id"),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "issue": match.group("issue"),
                "notice_date": _iso_date(match.group("notice_date")),
            },
        )], ""

    match = _FR_ASSET_TRANSFER_CONSIDERATION_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.asset_transfer_consideration_corrected.v1", {
                "kind": "asset_transfer", "action": "consideration_corrected",
                "currency": "CHF", "consideration": match.group("consideration"),
                "previous_consideration": match.group("previous_consideration"),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_BRANCH_SIGNATURE_GRANTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.branch_signature_granted.v1",
            match.group("name"), place=match.group("place"),
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "signing_granted", "origin": match.group("place").strip(),
                "scope": "branch",
            },
        )], ""

    match = _DE_PUBLIC_INSTITUTION_TRANSFORMED_TO_FOUNDATION.fullmatch(leftover)
    if match:
        rule_id = "de.text.public_institution_transformed_to_foundation.v1"
        common = {
            "action": "transformed",
            "transformation_plan_date": _iso_date(match.group("plan_date")),
            "corrigendum_date": _iso_date(match.group("corrigendum_date")),
            "inventory_date": _iso_date(match.group("inventory_date")),
            "decision_date": _iso_date(match.group("decision_date")),
            "decision_body": match.group("decision_body"),
            "public_vote_date": _iso_date(match.group("vote_date")),
            "approval_date": _iso_date(match.group("approval_date")),
            "legal_basis": match.group("legal_basis").strip(),
            "legal_basis_date": _iso_date(match.group("legal_basis_date")),
            "assets": match.group("assets"),
            "liabilities": match.group("liabilities"), "currency": "CHF",
        }
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id, {
                    "kind": "foundation_deed", "date": _iso_date(match.group("deed_date")),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "legal_form_changed", rule_id, {
                    **common, "from_legal_form": match.group("previous_form"),
                    "to_legal_form": match.group("legal_form"),
                    "foundation_type": match.group("new_form"), "same_name": True,
                },
            ),
        ], ""

    match = _FR_TWO_SIGNATORIES_NOW_WITH_PERSON.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_signatories_now_with_person.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "co_signatory_restriction_changed", "continued": True,
                    "with": match.group("with_person").strip(),
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_TWO_SIGNING_RESTRICTIONS_REMOVED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_signing_restrictions_removed.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name1"),
                role=match.group("role1").lower(),
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "restriction_removed", "continued": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name2"),
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "restriction_removed", "continued": True,
                },
            ),
        ], ""

    match = _DE_LEGACY_CONTRIBUTION_FRAGMENT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.legacy_contribution_fragment.v1", {
                "kind": "contribution_and_asset_acquisition_clause",
                "action": "removed", "business": match.group("business").strip(),
                "business_place": match.group("place").strip(),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_sheet_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "credited_to_share_capital": match.group("credited"),
                "receivable_credited": match.group("receivable"), "currency": "CHF",
            },
        )], ""

    match = _FR_RENAMED_AND_TWO_PEOPLE_MOVED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.renamed_and_two_people_moved.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), extra={
                    "action": "name_and_domicile_changed",
                    "previous_name": match.group("previous_name").strip(),
                    "domicile_changed": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place"), extra={
                    "action": "domicile_changed", "domicile_changed": True,
                },
            ),
        ], ""

    match = _FR_ADMINISTRATOR_AND_OTHER_APPOINTED_LIQUIDATORS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administrator_and_other_appointed_liquidators.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("administrator"),
                role="administrateur et liquidateur", signing="Einzelunterschrift",
                extra={"action": "appointed_liquidator", "signing_continues": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("liquidator"),
                role="liquidateur", signing="Einzelunterschrift", extra={
                    "action": "appointed_liquidator", "signing_continues": True,
                },
            ),
        ], ""

    match = _FR_BANKRUPTCY_JUDGMENT_NOT_EXECUTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.bankruptcy_judgment_not_executed.v1", {
                "kind": "bankruptcy_registration_cancelled",
                "action": "judgment_execution_refused",
                "authority": match.group("authority"),
                "letter_date": _iso_date(match.group("letter_date")),
                "judgment_date": _iso_date(match.group("judgment_date")),
                "cancelled_entry": match.group("entry"),
                "cancelled_entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _DE_COMPOSITION_AGREEMENT_WITH_LIQUIDATOR_AND_COMMITTEE.fullmatch(leftover)
    if match:
        rule_id = "de.text.composition_agreement_liquidator_committee.v1"
        events = [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "composition_agreement_confirmed",
                    "agreement_type": "assignment_of_assets",
                    "action": "confirmed_and_declared_binding",
                    "authority": match.group("authority").strip(),
                    "decision_date": _iso_date(match.group("decision_date")),
                    "agreement_date": _iso_date(match.group("agreement_date")),
                    "creditor_meeting_date": _iso_date(match.group("meeting_date")),
                    "previous_status": "definitive_composition_moratorium",
                    "previous_decision_date": _iso_date(
                        match.group("previous_decision_date")
                    ),
                    "previous_authority": match.group("previous_authority").strip(),
                    "previous_until": _iso_date(match.group("previous_until")),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id, {
                    "kind": "composition_liquidator", "action": "appointed",
                    "name": match.group("liquidator").strip(),
                    "representative": match.group("representative").strip(),
                    "representative_profession": match.group("profession").strip(),
                    "street": match.group("street").strip(),
                    "postal_code": match.group("postal_code"),
                    "place": match.group("place").strip(),
                },
            ),
        ]
        events.extend(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"member{index}"),
                role="Mitglied des Gläubigerausschusses", extra={
                    "action": "appointed", "committee": "Gläubigerausschuss",
                },
            )
            for index in (1, 2, 3)
        )
        return events, ""

    return [], leftover
