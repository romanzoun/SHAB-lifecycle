from __future__ import annotations

import re

from .keys import person_key
from .models import Event

_UID_RE = re.compile(r"CHE-\d{3}\.\d{3}\.\d{3}")
_REG_RE = re.compile(r"CH-[\d.-]+-\d")


def _che_uid(raw: str | None) -> str | None:
    if raw and _UID_RE.fullmatch(raw.strip()):
        return raw.strip()
    return None


_DE_SIGN = (
    r"Einzelunterschrift|Kollektivunterschrift(?:\s+zu\s+zweien)?|Unterschrift\s+zu\s+zweien"
    r"|Kollketivunterschrift(?:\s+zu\s+zweien)?|Einzelprokura|Kollektivprokura(?:\s+zu\s+zweien)?"
)
# "Heck, Ralph Karl-Heinz, von Muri bei Bern, in Muri bei Bern, Geschäftsführer, mit Einzelunterschrift"
# "Ludwig, Wilfried, von Obersiggenthal, in Kirchdorf AG, mit Kollektivprokura zu zweien"
_DE_PERSON = re.compile(
    r"(?P<last>[A-ZÄÖÜ][\wÀ-ÿ'\-]+),\s*"
    r"(?P<first>[^,]+?),\s*"
    r"(?:von\s+(?P<heimat>[^,]+)|(?P<nationality>[^,]+)),\s*"
    r"(?:(?P<unknown>unbekannten Aufenthaltes)|(?:in\s+)?(?P<place>[^,]+))"
    r"(?:,\s*(?P<role>(?!mit\s)(?!ohne\s).+?))?"
    r",\s*(?:mit\s+(?P<sign>" + _DE_SIGN + r")|ohne Zeichnungsberechtigung)",
    re.UNICODE,
)
_DE_MUTATED = re.compile(
    r"(?P<name>[A-ZÄÖÜ][\wÀ-ÿ'\-]+(?:\s+[A-ZÄÖÜa-zäöüéèêëàâçîïôùûÿ'\-]+)+),\s*"
    r"(?P<role>.+?),\s*(?P<sign>" + _DE_SIGN + r")"
    r"(?:,\s*neu\s+(?P<role_new>.+?),\s*(?P<sign_new>" + _DE_SIGN + r"))?"
    r"(?:,\s*nun in\s+(?P<place>[^;,]+))?",
    re.UNICODE,
)
_DE_SIGN_IN_CHUNK = re.compile(r"mit\s+(" + _DE_SIGN + r")")
_DE_SIGN_ONLY = re.compile(
    r"(?P<name>[A-ZÄÖÜ][\wÀ-ÿ'\-]+(?:\s+[A-ZÄÖÜa-zäöüéèêëàâçîïôùûÿ'\-]+)+),\s*"
    r"(?P<sign>" + _DE_SIGN + r")",
    re.UNICODE,
)
_DE_ORG = re.compile(
    r"(?P<name>[^;]+?)\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3}|CH-[\d.-]+-\d)\)"
    r"(?:\s*\[\s*(?P<registry_id>CH-[\d.-]+-\d)\s*\])?"
    r"(?:,\s*in\s+(?P<place>[^,]+))?,\s*"
    r"(?P<role>[^,]+)",
    re.UNICODE,
)
_DE_ORG_PLAIN = re.compile(
    r"(?P<name>[^;]+?),\s*in\s+(?P<place>[^,]+),\s*"
    r"(?P<role>(?!mit\s)[^,]+)",
    re.UNICODE,
)
_DE_SHARES = re.compile(
    r"mit\s+(?P<count>\d+)\s+Stammanteilen?\s+zu\s+je\s+CHF\s+(?P<nominal>[\d'.]+)",
    re.I,
)
_DE_BISHER = re.compile(r"\[bisher:\s*(?P<bisher>[^\]]+)\]", re.I)
_DE_SECTION_START = re.compile(
    r"(?P<label>Eingetragene Personen[^:]*|Ausgeschiedene Personen[^:]*|"
    r"Gelöschte Person(?:en)?[^:]*|Neu eingetragene Person):",
    re.I,
)
_DE_NAMED_PERSON = re.compile(
    r"(?P<name>[A-ZÄÖÜ][\wÀ-ÿ'’\-]+(?:\s+[\wÀ-ÿ'’\-]+)+),\s*"
    r"von\s+(?P<heimat>[^,]+),\s*in\s+(?P<place>[^,]+),\s*"
    r"(?P<role>[^,]+),\s*(?P<sign>" + _DE_SIGN + r")",
    re.UNICODE,
)
_DE_WITHOUT_SIGNATURE = re.compile(
    r"(?P<name>[A-ZÄÖÜ][^,]+),\s*(?P<role>[^,]+),\s*ohne Unterschrift",
    re.I | re.UNICODE,
)
_DE_COMPACT_PERSON_CHANGED = re.compile(
    r"Eingetragene Person geändert:\s*(?P<name>[^,]+),\s*"
    r"(?P<role>[^,]+),\s*(?P<sign>" + _DE_SIGN + r"),\s*"
    r"(?:nun|neu) in\s+(?P<place>[^.]+)\.?,?",
    re.I | re.UNICODE,
)

_FR_N_EST_PLUS = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^;]+?)\s+n'est plus\s+(?P<role_off>[^;]+)",
    re.I,
)
_FR_DEMEURE = re.compile(
    r"demeure\s+(?P<role_on>[^;.]+)",
    re.I,
)
_FR_SIGN = re.compile(
    r"signer\s+(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)",
    re.I,
)
_FR_SIGN_RADIEE = re.compile(
    r"La signature d(?:e\s+|['’])(?P<name>.+?)\s+est radiée",
    re.I,
)
_FR_POUVOIRS_RADIES = re.compile(
    r"Les pouvoirs de\s+(?P<name>.+?)\s+sont radiés",
    re.I,
)
_FR_ORIGIN = r"(?:du |de la |de l'|des |de |d')"
_FR_CONFEREE = re.compile(
    r"(?P<what>Signature|Procuration)\s+(?P<kind>individuelle|collective(?:\s+à\s+deux)?)"
    r"(?:,?\s+limitée (?:aux affaires de la succursale|à l'établissement principal))?"
    r"(?:,?\s+(?:toutefois\s+)?(?:(?P<except_with>pas|sauf)\s+)?avec\s+"
    r"(?P<with>.+?))?"
    r",?\s*(?:est|a été) conférée à\s+(?P<name>[^,]+),\s*"
    r"(?:de et à\s+(?P<place_same>[^,]+)|"
    + _FR_ORIGIN
    + r"(?P<heimat>[^,]+),\s*(?:à|au|aux)\s+(?P<place>[^,]+))"
    r"(?:,\s*(?P<role>[^.]+))?",
    re.I,
)
_FR_CONFEREE_TWO = re.compile(
    r"(?P<what>Signature|Procuration)\s+(?P<kind>individuelle|collective(?:\s+à\s+deux)?)"
    r"(?:,?\s+(?:toutefois\s+)?avec\s+(?P<with>[^.,]+))?"
    r",?\s*(?:est|a été) conférée à\s+"
    r"(?P<name1>[^,]+),\s*" + _FR_ORIGIN + r"(?P<heimat1>[^,]+),\s*"
    r"et\s+(?P<name2>[^,]+),\s*" + _FR_ORIGIN + r"(?P<heimat2>[^,]+),\s*"
    r"(?:tous|toutes|les) deux à\s+(?P<place>[^,]+)(?:,\s*(?P<role>[^.]+))?",
    re.I,
)
_FR_CONFEREE_THREE = re.compile(
    r"Signature\s+(?P<kind>individuelle|collective(?:\s+à\s+deux)?)\s+"
    r"(?:est|a été) conférée à\s+"
    r"(?P<name1>[^,]+),\s*" + _FR_ORIGIN + r"(?P<heimat1>[^,]+),\s*"
    r"(?P<name2>[^,]+),\s*" + _FR_ORIGIN + r"(?P<heimat2>[^,]+),\s*"
    r"tous deux à\s+(?P<place12>[^,]+),\s*(?P<role12>[^,]+),\s*et\s*"
    r"(?P<name3>[^,]+),\s*" + _FR_ORIGIN + r"(?P<heimat3>[^,]+),\s*"
    r"à\s+(?P<place3>[^,]+),\s*(?P<role3>[^.]+)\.?",
    re.I | re.UNICODE,
)
_FR_CONFEREE_THREE_SHARED_ORIGIN = re.compile(
    r"Signature\s+(?P<kind>individuelle|collective(?:\s+à\s+deux)?)\s+"
    r"(?:est|a été) conférée à\s+"
    r"(?P<name1>[^,]+),\s*(?P<name2>[^,]+)\s+et\s+(?P<name3>[^,]+),\s*"
    r"les trois de\s+(?P<heimat>[^,]+),\s*à\s+(?P<place>[^.]+)\.?,?",
    re.I | re.UNICODE,
)
_FR_NOMME_LIQUIDATEUR = re.compile(
    r"(?:par )?(?:l'associé |l'associée )(?P<name>[A-ZÀ-Ÿ][^,]+),\s*"
    r"lequel est nommé liquidateur(?: avec (?P<sign>signature individuelle|signature collective(?:\s+à\s+deux)?))?",
    re.UNICODE,
)
_FR_NOMME_GERANT_LIQ = re.compile(
    r"(?:L'associé-gérant |L'associée-gérante |Le gérant |La gérante )"
    r"(?P<name>[A-ZÀ-Ÿ].+?) est nommé(?:e)? liquidateur(?:trice)?"
    r"(?: avec (?P<sign>signature individuelle|signature collective(?:\s+à\s+deux)?))?",
    re.UNICODE,
)
_FR_APPOINTED_LIQUIDATOR_SIMPLE = re.compile(
    r"(?<![\wÀ-ÿ])(?P<name>(?!(?:lequel|laquelle|qui)\b)[A-ZÀ-Ÿ][^,.;]+) "
    r"est nommé(?:e)? "
    r"(?P<role>liquidateur|liquidatrice) avec "
    r"(?P<sign>signature individuelle|signature collective(?:\s+à\s+deux)?)\.?,?",
    re.I | re.UNICODE,
)
_FR_APPOINTED_LIQUIDATOR_WITH_PREVIOUS_ROLE = re.compile(
    r"(?<![\wÀ-ÿ])(?P<name>[A-ZÀ-Ÿ][^,.;]+),\s*"
    r"(?P<previous_role>associé(?:e)?-gérant(?:e)?|gérant(?:e)?|administrat(?:eur|rice)),\s*"
    r"est nommé(?:e)? (?P<role>liquidateur|liquidatrice) avec "
    r"(?P<sign>signature individuelle|signature collective(?:\s+à\s+deux)?)\.?,?",
    re.I | re.UNICODE,
)
_FR_AUDITOR_RENAME = re.compile(
    r"Nouvelle raison (?:sociale|de commerce) (?:de l'organe de révision|du réviseur):\s*(?P<name>.+?)\s+"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?",
    re.I,
)
_FR_AUDITOR_RENAME_AND_SEAT = re.compile(
    r"Nouvelle raison sociale et nouveau siège du réviseur:\s*(?P<name>.+?)\s+"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+(?P<place>[^.]+)\.?",
    re.I,
)
_FR_AUDITOR_IDENTIFIER_AND_SEAT = re.compile(
    r"Nouveau numéro d['’]identification et nouveau siège du réviseur:\s*"
    r"(?P<name>.+?)\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"à\s+(?P<place>[^.]+)\.?,?",
    re.I,
)
_FR_AUDITOR_RENAME_QUOTED = re.compile(
    r"Nouvelle raison sociale (?:de l'organe de révision|du réviseur)\s+"
    r"[\"“](?P<old_name>.+?)[\"”]\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s*:\s*"
    r"[\"“](?P<name>.+?)[\"”]\.?",
    re.I,
)
_FR_AUDITOR_RENAME_QUOTED_AFTER_COLON = re.compile(
    r"Nouvelle raison sociale de l'organe de révision\s*"
    r"[\"“](?P<old_name>.+?)[\"”]:\s*[\"“](?P<name>.+?)[\"”]"
    r"(?:\s*\((?P<uid_direct>CHE-\d{3}\.\d{3}\.\d{3})\)|"
    r",\s*dont le numéro d'identification(?: des entreprises)?(?: \(IDE/UID\))?\s+"
    r"(?:(?P<old_registry>CH-[\d.-]+-\d) est remplacé par le numéro d'identification "
    r"des entreprises \(IDE/UID\)\s+)?(?:est\s+)?"
    r"(?P<uid_clause>CHE-\d{3}\.\d{3}\.\d{3}))\. ?",
    re.I,
)
_FR_AUDITOR_RENAME_QUOTED_LEGACY = re.compile(
    r"Nouvelle raison sociale de l'organe de révision:\s*"
    r"[\"“](?P<old_name>.+?)[\"”]\s+\((?P<registry_id>CH-[\d.-]+-\d)\),\s*"
    r"à\s+(?P<place>[^:]+):\s*[\"“](?P<name>.+?)[\"”],\s*"
    r"dont le numéro IDE/UID est\s+(?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\.?",
    re.I,
)
_FR_AUDITOR_RENAME_FEDERAL_NUMBER = re.compile(
    r"Nouvelle raison sociale de l'organe de révision\s+"
    r"[\"“](?P<old_name>.+?)[\"”],\s*dont le numéro fédéral\s+"
    r"(?P<registry_id>CH-[\d.-]+-\d)\s+est remplacé par le numéro "
    r"IDE\s*/?\s*UID\s+(?P<uid>CHE-\d{3}\.\d{3}\.\d{3}):\s*"
    r"[\"“](?P<name>.+?)[\"”]\.?,?",
    re.I,
)
_FR_NEW_AUDITOR = re.compile(
    r"(?:Nouvel\s+)?Organe de révision:\s*(?P<name>.+?)\s+"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)(?:,\s*à\s+(?P<place>[^.]+))?\.?",
    re.I,
)
_FR_SIGN_ONLY = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,]+),\s*"
    r"(?P<kind>signature|procuration)\s+(?P<sign>individuelle|collective(?:\s+à\s+deux)?)",
    re.I | re.UNICODE,
)
_FR_DOMICILE_NOW = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,]+?)(?:\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)|\s+est) "
    r"maintenant domicilié(?:e)? "
    r"(?:(?:à|au|aux) )?(?P<place>[^,;.]+(?:,\s*[A-Z]{2,3})?)",
    re.UNICODE,
)
_FR_NATURAL = re.compile(
    r"(?P<last>[A-ZÀ-Ÿ][\wÀ-ÿ'\-]+(?:\s+[\wÀ-ÿ'\-]+)*)\s*,\s*"
    r"(?P<first>[^,]+?),\s*"
    r"(?:de\s+(?P<heimat>[^,]+)|(?P<nationality>(?:ressortissant\s+)?[^,]+)),\s*"
    r"à\s+(?P<place>[^,]+)"
    r"(?:,\s+(?!avec\s)(?P<role>[^,]+))?"
    r"(?:,\s+avec\s+(?P<sign>signature individuelle|signature collective(?:\s+à\s+deux)?"
    r"|procuration individuelle|procuration collective(?:\s+à\s+deux)?))?",
    re.UNICODE,
)
_FR_PROCURATION_OFF = re.compile(
    r"La procuration (?:de\s+|d['’])(?P<name>.+?)\s+est (?:éteinte|radiée)",
    re.I,
)
_FR_LIQUIDATEUR = re.compile(
    r"Liquidat(?:eur|rice):\s+(?:l'|le |la )?(?:associé gérant |associée gérante |"
    r"administrateur |administratrice |gérant |gérante |associé |associée )?"
    r"(?:secrétaire |président |présidente )?(?P<name>[A-ZÀ-Ÿ][^,;]+)"
    r"(?:,\s*maintenant originaire de (?P<heimat>[^,.;]+))?"
    r"(?:,\s*(?:lequel|laquelle) continue à signer "
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?))?",
    re.I | re.UNICODE,
)
_FR_AUDITOR_NOW = re.compile(
    r"L'organe de révision inscrit\s+(?P<old_name>.+?)\s+\([^)]+\),?\s*"
    r"se nomme désormais\s+(?P<name>.+?)\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?",
    re.I,
)
_FR_BOARD_MEMBER = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,.]+),\s*"
    r"(?:de et à\s+(?P<place_same>[^,.]+(?:,\s*[A-Z]{1,3})?)|"
    + _FR_ORIGIN
    + r"(?P<heimat>[^,]+),\s*à\s+(?P<place>[^,.]+(?:,\s*[A-Z]{1,3})?)),\s*"
    r"est membre(?:(?: et)? (?P<office>président(?:e)?|secrétaire|directeur(?:trice)?))? "
    r"du (?P<board>conse(?:il)?(?: d'administration)?)"
    r"(?: avec (?P<sign>signature (?:individuelle|collective(?:\s+à\s+deux)?)))?\.?",
    re.I | re.UNICODE,
)
_FR_NEW_BOARD_MEMBER = re.compile(
    r"Nouveau membre du conse(?:il)? d'administration avec "
    r"(?P<sign>signature (?:individuelle|collective(?:\s+à\s+deux)?)):\s*"
    r"(?P<name>[A-ZÀ-Ÿ][^,.]+),\s*"
    r"(?:de et à\s+(?P<place_same>[^,.]+)|"
    + _FR_ORIGIN
    + r"(?P<heimat>[^,]+),\s*à\s+(?P<place>[^,.]+))\.?",
    re.I | re.UNICODE,
)
_FR_NEW_ADMINISTRATOR = re.compile(
    r"Nouvel(?:le)? (?:administrateur|administratrice) "
    r"(?:avec (?P<sign>signature (?:individuelle|collective(?:\s+à\s+deux)?))|sans signature):\s*"
    r"(?P<name>[A-ZÀ-Ÿ][^,.]+),\s*"
    r"(?:de et à\s+(?P<place_same>[^,.]+)|"
    + _FR_ORIGIN
    + r"(?P<heimat>[^,]+),\s*à\s+(?P<place>[^,.]+))\.?",
    re.I | re.UNICODE,
)
_FR_SIGN_NOW = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,.]+)\s+signe désormais\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?",
    re.I | re.UNICODE,
)
_FR_GROUP_SIGN_NOW_SIMPLE = re.compile(
    r"Les (?P<role>administrateurs?|gérants?|directeurs?)\s+"
    r"(?P<name1>[A-ZÀ-Ÿ][^,.;]+?)\s+et\s+(?P<name2>[A-ZÀ-Ÿ][^,.;]+?)\s+"
    r"signent désormais\s+(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?",
    re.I | re.UNICODE,
)
_FR_PAIR_SIGN_NOW = re.compile(
    r"(?P<name1>[A-ZÀ-Ÿ][^,.;]+?)\s+et\s+(?P<name2>[A-ZÀ-Ÿ][^,.;]+?)\s+"
    r"signent désormais\s+(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATORS_SIGN_NOW_WITH_FIRST_ROLE = re.compile(
    r"Les administrateurs\s+(?P<name1>[A-ZÀ-Ÿ][^,.;]+),\s*"
    r"(?P<role1>président(?:e)?)\s+et\s+(?P<name2>[A-ZÀ-Ÿ][^,.;]+)\s+"
    r"signent désormais\s+(?P<sign>individuelle(?:ment)?|collectivement(?:\s+à\s+deux)?);\s*"
    r"leurs pouvoirs sont modifiés en ce sens\.?,?",
    re.I | re.UNICODE,
)
_FR_GROUP_SIGN_NOW = re.compile(
    r"Les (?P<role>administrateurs?|gérants?|directeurs?)\s+(?P<names>.+?),\s*"
    r"jusqu'ici avec (?P<previous>signature individuelle|signature collective(?:\s+à\s+deux)?),\s*"
    r"signent désormais (?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?",
    re.I | re.UNICODE,
)
_FR_NAMED_OFFICER = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,.]+),\s*"
    r"(?:de et à\s+(?P<place_same>[^,.]+(?:,\s*[A-Z]{1,3})?)|"
    + _FR_ORIGIN
    + r"(?P<heimat>[^,]+),\s*à\s+(?P<place>[^,.]+(?:,\s*[A-Z]{1,3})?)),\s*"
    r"est nommé(?:e)? (?P<role>[^,.]+?)(?=\s+avec signature|\.|$)"
    r"(?: avec (?P<sign>signature (?:individuelle|collective(?:\s+à\s+deux)?)))?\.?",
    re.I | re.UNICODE,
)
_FR_CIVIL_NAME = re.compile(
    r"(?:Par suite de changement d'état civil,\s*)?(?P<old_name>[A-ZÀ-Ÿ][^.;]+?)\s+"
    r"porte maintenant le nom de\s+(?P<name>[^.]+)\.?",
    re.I,
)
_FR_CIVIL_NAME_SIMPLE = re.compile(
    r"(?P<old_name>[A-ZÀ-Ÿ][\wÀ-ÿ'’\-]+"
    r"(?:\s+[A-ZÀ-Ÿ][\wÀ-ÿ'’\-]+){1,3})\s+se nomme désormais\s+"
    r"(?P<name>[A-ZÀ-Ÿ][\wÀ-ÿ'’\-]+"
    r"(?:\s+[A-ZÀ-Ÿ][\wÀ-ÿ'’\-]+){0,3})\.?",
    re.UNICODE,
)
_FR_CIVIL_NAME_AND_DOMICILE = re.compile(
    r"(?P<old_name>[A-ZÀ-Ÿ][^,.;]+?)(?:\s+porte maintenant le nom(?: de)?|,\s*qui se nomme désormais)\s+"
    r"(?P<name>[^,.;]+),\s*(?:et\s+)?est maintenant (?:domicilié(?:e)?\s+)?à\s+(?P<place>[^.]+)\.?",
    re.I | re.UNICODE,
)
_FR_ORIGIN_DOM = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,]+?),?\s*(?:est\s+)?maintenant originaire de (?P<heimat>.+?) "
    r"et (?:maintenant )?domicilié(?:e)? à (?P<place>[^.]+)",
    re.UNICODE,
)
_FR_ORIGIN_AND_DOM_NOW = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,.;]+?) est maintenant de et à (?P<place>[^.]+)\.?",
    re.UNICODE,
)
_FR_ORIGIN_ONLY = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,.;]+?) est (?:maintenant|désormais) (?:originaire )?"
    r"(?:du |de la |de l['’]|des |de |d['’])"
    r"(?P<heimat>[^.]+)\.?",
    re.UNICODE,
)
_FR_BRANCH_DIR = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,]+),\s*" + _FR_ORIGIN + r"(?P<heimat>[^,]+),\s*"
    r"à\s+(?P<place>[^,]+)(?:,\s*F)?,\s*est directeur(?:trice)? de la succursale"
    r"(?: avec (?P<sign>signature individuelle|signature collective(?:\s+à\s+deux)?))?",
    re.I | re.UNICODE,
)
_FR_NE_SONT_PLUS = re.compile(
    r"(?P<names>[A-ZÀ-Ÿ][^.;]+?\s+et\s+[A-ZÀ-Ÿ][^.;]+?)\s+ne sont plus\s+(?P<role_off>[^;.]+)",
    re.I,
)
_FR_RESTE = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][\wÀ-ÿ' \-]+),\s*jusqu'ici\s+(?P<role_old>[^,]+),\s*reste\s+(?P<role_on>.+?)"
    r"\s+et signe désormais\s+(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)",
    re.UNICODE,
)
_FR_NOUVEAUX = re.compile(
    r"Nouveaux administrateurs(?: avec signature (?P<kind>individuelle|collective(?:\s+à\s+deux)?))?:\s*(?P<body>[^.]+)",
    re.I,
)
_FR_NOUVEAU_ONE = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,]+),\s*(?:du |de la |de l'|de |d')(?P<heimat>[^,]+),\s*à\s+(?P<place>.+)",
    re.I,
)
_FR_GROUPED_PLACE = re.compile(
    r"tous\s+(?:deux|trois|quatre|cinq|six)\s+à\s+(?P<place>[^,]+)",
    re.I,
)
_FR_GROUPED_LAST = re.compile(
    r"(?:^|,\s*)(?:et\s+)?(?P<name>[A-ZÀ-Ÿ][\wÀ-ÿ'’\-]+(?:\s+[A-ZÀ-Ÿ][\wÀ-ÿ'’\-]+)+),\s*"
    r"à\s+(?P<place>.+)$",
    re.UNICODE,
)
_FR_GROUPED_NAME = re.compile(
    r"(?:^|,\s*)(?:et\s+)?(?P<name>[A-ZÀ-Ÿ][\wÀ-ÿ'’\-]+(?:\s+[A-ZÀ-Ÿ][\wÀ-ÿ'’\-]+)+)"
    r"(?=,|$)",
    re.UNICODE,
)
_FR_SECTION_START = re.compile(
    r"(?P<label>Inscription ou modification de personne\(s\)[^:]*|"
    r"Nouvelles? personnes? inscrites?[^:]*|"
    r"Personne\(s\) et signature\(s\) radiée\(s\)|"
    r"Personnes? inscrites?[^:]*|"
    r"Personnes? radiée(?:s)?[^:]*):",
    re.I,
)
_FR_ORG = re.compile(
    r"(?P<name>[^;]+?)\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3}|CH-[\d.-]+-\d)\)"
    r"(?:,\s*à\s+(?P<place>[^,]+))?,\s*"
    r"(?P<role>[^,]+)",
    re.UNICODE,
)
_FR_FOREIGN_ORG = re.compile(
    r"(?P<name>[^;]+?)\s+\((?P<registry_id>(?:No d['’]entreprise|HRB)\s+[^)]+)\)"
    r"(?:,\s*à\s+(?P<place>[^,]+))?,\s*(?P<role>[^,]+)",
    re.I | re.UNICODE,
)
_FR_ORG_PLAIN = re.compile(
    r"^(?P<name>.+?\b(?:SA|S\.A\.|Sàrl|S\.à\s*r\.l\.|AG|GmbH|fondation|association)"
    r"(?:\s+succursale\s+de\s+[^,]+)?),\s*"
    r"à\s+(?P<place>[^,]+),\s*(?P<role>[^,.]+)",
    re.I | re.UNICODE,
)
_FR_SECTION_TRAILING_AUDIT = re.compile(
    r"(?P<tail>Selon déclaration du \d{2}\.\d{2}\.\d{4},[^.]+contrôle restreint\.?)$",
    re.I,
)
_FR_LIST_PERSON = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,]+?),\s*"
    r"(?P<role>(?![Ss]ignature)[^,]+),\s*"
    r"(?i:signature)\s+(?P<sign>individuelle|collec(?:t|vt)ive(?:\s+à\s+deux)?)"
    r"(?:(?:,\s*)?\s*(?i:désormais|maintenant)\s+(?P<role_new>[^,]+),\s*"
    r"(?i:signature)\s+(?P<sign_new>individuelle|collective(?:\s+à\s+deux)?))?",
    re.UNICODE,
)
_FR_LIST_WITHOUT_SIGN = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,]+?),\s*(?P<role>[^,]+),\s*sans signature",
    re.I | re.UNICODE,
)
_FR_LIST_ROLE_CHANGED = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,]+?),\s*(?P<role>[^,]+),\s*"
    r"maintenant\s+(?P<role_new>[^,.;]+)",
    re.I | re.UNICODE,
)
_FR_NEW_INSCRIT = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,]+?),\s*(?:du |de la |de l'|de |d')(?P<heimat>[^,]+),\s*"
    r"à\s+(?P<place>[^,]+)"
    r"(?:,\s*(?P<role>(?![Ss]ignature)(?!sans\s)[^,]+))?"
    r",\s*(?:(?i:signature)\s+(?P<sign>individuelle|collective(?:\s+à\s+deux)?)|sans signature)",
    re.UNICODE,
)
_FR_NEW_INSCRIT_WITH = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,]+?),\s*(?:du |de la |de l'|de |d')(?P<heimat>[^,]+),\s*"
    r"à\s+(?P<place>[^,]+),\s*(?P<role>[^,]+?)\s+avec\s+"
    r"(?i:signature)\s+(?P<sign>individuelle|collective(?:\s+à\s+deux)?)",
    re.UNICODE,
)
_FR_AUDITOR_RAISON = re.compile(
    r"L'organe de révision\s+(?P<old>.+?)\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)"
    r"\s+a modifié sa raison de commerce en\s+(?P<name>.+?)\s+"
    r"\((?P<uid2>CHE-\d{3}\.\d{3}\.\d{3})\)\.?",
    re.I,
)
_FR_AUDITOR_LEGACY_REASON = re.compile(
    r"L'organe de révision(?:\s+inscrit)?\s*:?\s*(?P<old>.+?)\s+"
    r"\((?P<old_registry>CH-[\d.-]+-\d)\)\s+"
    r"(?:désormais avec la raison sociale|a modifié sa raison de commerce en)\s+"
    r"(?P<name>.+?)\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?",
    re.I,
)
_FR_MIXED_LANGUAGE_AUDITOR_CHANGED = re.compile(
    r"Personnes inscrites modifiées:\s*(?P<old_name>.+?)\s+"
    r"\((?P<old_registry>CH-[\d.-]+-\d)\),\s*"
    r"(?P<role>organe de révision),\s*nouvelle raison sociale\s+"
    r"(?P<name>.+?)\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"maintenant à\s+(?P<place>[^.]+)\.?,?",
    re.I | re.UNICODE,
)
_FR_AUDITOR_RAISON_WITH_ID = re.compile(
    r"L'organe de révision\s+(?P<old>.+?)"
    r"(?:\s+\((?P<old_registry>CH-[\d.-]+-\d)\))?,\s*"
    r"dont le numéro d'identification(?: des entreprises)?(?: \(IDE/UID\))? est(?: désormais)?(?: le)?\s+"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"a modifié sa raison de commerce en\s+(?P<name>.*?\S)"
    r"(?:\s+\((?P<uid2>CHE-\d{3}\.\d{3}\.\d{3})\))?(?:\.|$)",
    re.I,
)
_FR_ASSOCIATE_UPDATED = re.compile(
    r"L'associée?\s+(?P<old_name>.+?)\s+\((?P<registry_id>CH-[\d.-]+-\d)\),\s*"
    r"qui a modifié sa raison de commerce en\s+(?P<name>.+?)\s+et dont le numéro "
    r"d'identification des entreprises est désormais\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"a transféré son siège à\s+(?P<place>[^.]+)\.?,?",
    re.I,
)
_FR_ASSOCIATE_UPDATED_UID = re.compile(
    r"L['’]associée?\s+(?P<old_name>.+?)\s+"
    r"\((?P<old_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"dont la raison de commerce est désormais\s+(?P<name>.+?)\s+"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"a transféré son siège à\s+(?P<place>[^.]+)\.?,?",
    re.I,
)
_FR_OFFICER_CONTINUES = re.compile(
    r"L'(?P<old_role>administrateur|administratrice)\s+(?P<name>[^,]+),\s*"
    r"nommé(?:e)?\s+(?P<role>[^,]+),\s*continue à signer\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?,?",
    re.I | re.UNICODE,
)
_FR_OFFICER_FORMER_ROLE_CONTINUES = re.compile(
    r"L'(?P<role>administrateur|administratrice)\s+(?P<name>[^,]+),\s*"
    r"jusqu'ici\s+(?P<old_role>[^,]+),\s*continue \u00e0 signer\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+\u00e0\s+deux)?)\.?,?",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBER_CONTINUES_SIMPLE = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,.;]+) est membre(?: et (?P<office>président(?:e)?))? "
    r"du conseil d'administration,\s*(?:il\s+)?continue \u00e0 signer\s+"
    r"(?P<sign>collectivement|collcetivement|collecvtivement)(?:\s+\u00e0\s+deux)?\.?,?",
    re.I | re.UNICODE,
)
_FR_BOARD_ROLES_SIGN_NOW_PAIR = re.compile(
    r"(?P<name1>[A-ZÀ-Ÿ][^,.;]+),\s*(?P<role1>président(?:e)?),\s*et\s*"
    r"(?P<name2>[A-ZÀ-Ÿ][^,.;]+),\s*(?P<role2>membres?) du conseil "
    r"d'administration,\s*signent désormais\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+\u00e0\s+deux)?)\.?,?",
    re.I | re.UNICODE,
)
_FR_ROLE_CONTINUES_SIGNING = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,.;]+?)\s*,?\s+jusqu'ici\s+(?P<role>[^,.;]+),\s*"
    r"continue (?:de|à) signer\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?",
    re.I | re.UNICODE,
)
_FR_OFFICER_REMAINS_SOLE = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,.;]+),\s*jusqu['’]ici\s+(?P<old_role>[^,.;]+),\s*"
    r"reste\s+(?P<role>seul administrateur|seule administratrice)\s+et\s+"
    r"continue de signer\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?,?",
    re.I | re.UNICODE,
)
_FR_NEW_GENERAL_PARTNER = re.compile(
    r"Nouvel associé indéfiniment responsable:\s*(?P<name>[^,]+),\s*"
    + _FR_ORIGIN
    + r"(?P<heimat>[^,]+),\s*à\s+(?P<place>[^,]+),\s*avec\s+"
    r"(?P<sign>signature\s+(?:individuelle|collective(?:\s+à\s+deux)?))\.?,?",
    re.I | re.UNICODE,
)
_FR_NAMED_OFFICER_CONTINUES = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,.;]+?),?\s+"
    r"(?:jusqu'ici\s+(?P<old_role>[^,]+),\s*)?"
    r"(?:est\s+)?nommé(?:e)?\s+(?P<role>[^,.;]+?)(?:,\s*|\s+et\s+)"
    r"continue (?:de|à) signer\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_SIGNING_REVOKED = re.compile(
    r"L['’]associé(?:e)?\s+(?P<name>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<old_role>gérant(?:e)?),\s*n['’]exerce plus la signature sociale\.?",
    re.I | re.UNICODE,
)
_FR_ROLES_CHANGED_PAIR = re.compile(
    r"(?P<name1>[A-ZÀ-Ÿ][^,.;]+?)\s+et\s+(?P<name2>[A-ZÀ-Ÿ][^,.;]+?)\s+"
    r"jusqu['’]ici\s+(?P<old_role>directeurs?|directrices?),\s*"
    r"nommé(?:e)?s?\s+(?P<role>administrateurs?|administratrices?),\s*"
    r"continuent (?:à|de) signer\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?",
    re.I | re.UNICODE,
)
_FR_APPOINTED_SIGNING_PROCURATION_REVOKED = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,.;]+),\s*nommé(?:e)?\s+(?P<role>[^,;]+),\s*"
    r"signe désormais\s+(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)"
    r"(?:\s+avec\s+(?P<with>[^;.]+))?;\s*sa procuration est radiée\.?",
    re.I | re.UNICODE,
)
_FR_BRANCH_SIGNATURE_WITH_PROCURATION_REVOKED = re.compile(
    r"Signature (?P<kind>individuelle|collective(?:\s+à\s+deux)?) "
    r"limitée aux affaires de la succursale a été conférée à "
    r"(?P<name>[^;]+);\s*sa procuration est radiée\.?",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_RENAMED = re.compile(
    r"Nouvelle raison sociale de l'associée? (?P<old_name>.+?) "
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\):\s*(?P<name>[^.]+)\.?",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFORMED = re.compile(
    r"L['’]associée?\s+(?P<old_name>.+?)\s+"
    r"\((?P<old_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+est devenue?\s+"
    r"(?P<name>.+?)\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+"
    r"par suite de transformation\.?,?",
    re.I | re.UNICODE,
)
_FR_MEMBER_CONTINUES_SIGNING = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,.;]+),\s*(?P<role>membre du conseil d'administration),\s*"
    r"jusqu'ici (?P<old_role>[^,]+),\s*continue de signer "
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)"
    r"(?: avec (?P<with>[^.]+))?\.?",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBERS_PAIR = re.compile(
    r"(?P<name1>[A-ZÀ-Ÿ][\wÀ-ÿ'’\-.]+(?:\s+[A-ZÀ-Ÿ][\wÀ-ÿ'’\-.]+)+),\s*"
    + _FR_ORIGIN + r"(?P<heimat1>[^,]+),\s*"
    r"à\s+(?P<place1>.+?),\s*et\s*"
    r"(?P<name2>[A-ZÀ-Ÿ][\wÀ-ÿ'’\-.]+(?:\s+[A-ZÀ-Ÿ][\wÀ-ÿ'’\-.]+)+),\s*"
    + _FR_ORIGIN + r"(?P<heimat2>[^,]+),\s*"
    r"à\s+(?P<place2>.+?)(?:,\s*(?P<role2>délégué))?,\s*"
    r"sont membres du conseil d'administration,?\s*(?:tous deux )?avec "
    r"(?P<sign>signature (?:individuelle|collective(?:\s+à\s+deux)?))"
    r"(?: avec (?P<with>[^.]+))?\.?",
    re.I | re.UNICODE,
)
_FR_NEW_FOUNDATION_MEMBER = re.compile(
    r"Nouveau membre du conseil de fondation avec "
    r"(?P<sign>signature (?:individuelle|collective(?:\s+à\s+deux)?))"
    r"(?:,\s*avec (?P<with>[^:]+))?:\s*(?P<name>[A-ZÀ-Ÿ][^,]+),\s*"
    + _FR_ORIGIN
    + r"(?P<heimat>[^,]+),\s*à\s+(?P<place>[^.]+)\.?",
    re.I | re.UNICODE,
)
_FR_NEW_FOUNDATION_MEMBER_POSTFIX = re.compile(
    r"Nouveau membre du conseil de fondation:\s*"
    r"(?P<name>[A-ZÀ-Ÿ][^,]+),\s*"
    + _FR_ORIGIN
    + r"(?P<heimat>[^,]+),\s*à\s+(?P<place>[^,]+),\s*avec "
    r"(?P<sign>signature (?:individuelle|collective(?:\s+à\s+deux)?)),\s*"
    r"pas avec (?P<not_with>[^.]+)\.?",
    re.I | re.UNICODE,
)
_FR_REMOVED_MEMBERS_AND_POWERS = re.compile(
    r"(?P<name1>[A-ZÀ-Ÿ][\wÀ-ÿ'’\-.]+(?:\s+[A-ZÀ-Ÿ][\wÀ-ÿ'’\-.]+)+)\s+et\s+"
    r"(?P<name2>[A-ZÀ-Ÿ][\wÀ-ÿ'’\-.]+(?:\s+[A-ZÀ-Ÿ][\wÀ-ÿ'’\-.]+)+) "
    r"ne sont plus (?P<role>membres du conseil d'administration);\s*"
    r"leurs pouvoirs,\s*de même que ceux de (?P<name3>[^,.;]+),\s*sont radiés\.?",
    re.I | re.UNICODE,
)
_FR_SIGN_NOW_WITH_ROLE = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,.;]+),(?!\s*nommé(?:e)?\s)\s*(?P<role>[^,.;]+),\s*signe désormais "
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?",
    re.I | re.UNICODE,
)
_FR_ROLE_SIGN_NOW = re.compile(
    r"L['’](?P<role>administrateur(?:\s+président)?|administratrice(?:\s+présidente)?)\s+"
    r"(?P<name>[^,.;]+),\s*signe désormais\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?);\s*"
    r"ses pouvoirs sont modifiés en ce sens\.?,?",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_DIRECTOR_PAIR = re.compile(
    r"Administration:\s*(?P<name1>[^,]+),\s*" + _FR_ORIGIN + r"(?P<heimat1>[^,]+),\s*"
    r"à\s+(?P<place1>.+?),\s*(?P<role1>président(?:e)?),\s*et\s*"
    r"(?P<name2>[^,]+),\s*" + _FR_ORIGIN + r"(?P<heimat2>[^,]+),\s*"
    r"à\s+(?P<place2>.+?),\s*(?P<role2>secrétaire),\s*"
    r"tous deux nommés en outre (?P<additional_role>[^,]+),\s*lesquels signent "
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_CONTINUES_PAIR = re.compile(
    r"Administration:\s*(?P<name1>[^,]+),\s*nommé(?:e)?\s+(?P<role1>[^,]+?)\s*,?\s*et\s*"
    r"(?P<name2>[^,]+),\s*(?:(?P<old_marker>jusqu'ici)\s+)?(?P<role2>[^,]+),\s*"
    r"lesquels continuent (?:à|de) signer\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?,?",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_MIXED_PAIR = re.compile(
    r"Administration:\s*(?P<name1>[^,]+),\s*nommé(?:e)?\s+(?P<role1>[^,]+),\s*"
    r"lequel continue à signer\s+(?P<sign1>individuellement|collectivement(?:\s+à\s+deux)?),\s*et\s*"
    r"(?P<name2>[^,]+),\s*" + _FR_ORIGIN + r"(?P<heimat2>[^,]+),\s*"
    r"à\s+(?P<place2>[^,]+)(?:,\s*(?P<country2>[A-Z]{2,3}))?,\s*avec\s+"
    r"(?P<sign2>signature individuelle|signature collective(?:\s+à\s+deux)?)\.?",
    re.I | re.UNICODE,
)
_FR_MANAGERS_PAIR = re.compile(
    r"(?P<name1>[^,.;]+),\s*" + _FR_ORIGIN + r"(?P<heimat1>[^,]+),\s*"
    r"à\s+(?P<place1>[^,]+)\s+et\s+(?P<name2>[^,.;]+),\s*"
    + _FR_ORIGIN + r"(?P<heimat2>[^,]+),\s*à\s+(?P<place2>[^,]+),\s*"
    r"sont\s+(?P<role>gérants?)\s+et\s+signent\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)"
    r"(?:,\s*avec\s+(?P<with>[^.]+))?\.?",
    re.I | re.UNICODE,
)
_FR_APPOINTED_PAIR_PROCURATION_REVOKED = re.compile(
    r"(?P<name1>[^,.;]+),\s*dont la procuration est (?P<revoked1>éteinte|radiée),\s*"
    r"est nommé(?:e)?\s+(?P<role1>[^;]+);\s*"
    r"(?P<name2>[^,.;]+),\s*dont la procuration est (?P<revoked2>éteinte|radiée),\s*"
    r"est nommé(?:e)?\s+(?P<role2>[^;]+);\s*"
    r"toutes deux engagent désormais la société par leur\s+"
    r"(?P<sign>signature individuelle|signature collective(?:\s+à\s+deux)?)\.?",
    re.I | re.UNICODE,
)
_FR_BUREAU_GROUP = re.compile(
    r"(?P<name1>[^,.;]+),\s*jusqu['’]ici\s+(?P<old_role1>[^,]+),\s*"
    r"nommé(?:e)?\s+(?P<role1>[^,]+),\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*nommé(?:e)?\s+(?P<role2>[^,]+),\s*"
    r"signent désormais\s+(?P<sign1>individuellement|collectivement(?:\s+à\s+deux)?),\s*"
    r"sans autre restriction\.\s*Les membres du conseil\s+"
    r"(?P<name3>[^,.;]+)\s+et\s+(?P<name4>[^,.;]+),\s*"
    r"nommés? en outre\s+(?P<role34>[^,]+),\s*continuent à signer\s+"
    r"(?P<sign2>individuellement|collectivement(?:\s+à\s+deux)?)\.?",
    re.I | re.UNICODE,
)
_FR_PROCURATION_REVOKED_SIGNING_NOW = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,.;]+),\s*dont la procuration est "
    r"(?P<revoked>éteinte|radiée),\s*engage désormais la société par sa "
    r"(?P<sign>signature individuelle|signature collective(?:\s+à\s+deux)?)\.?",
    re.I | re.UNICODE,
)
_FR_CONFEREE_TWO_PLACES = re.compile(
    r"Signature\s+(?P<kind>individuelle|collective(?:\s+à\s+deux)?)\s+"
    r"(?:est|a été) conférée à\s+(?P<name1>[^,]+),\s*à\s+(?P<place1>[^,]+),\s*"
    r"et\s+(?P<name2>[^,]+),\s*à\s+(?P<place2>[^,]+),\s*"
    r"tous deux de\s+(?P<heimat>[^,]+)(?:,\s*(?P<role>[^.]+))?\.?,?",
    re.I | re.UNICODE,
)
_FR_CONFEREE_TWO_DISTINCT_PLACES = re.compile(
    r"Signature\s+(?P<kind>individuelle|collective(?:\s+à\s+deux)?)"
    r"(?:,\s*limitée à l'établissement principal)?"
    r"(?:,\s*avec\s+(?P<with>.+?))?\s+(?:est|a été) conférée à\s+"
    r"(?P<name1>[^,]+),\s*" + _FR_ORIGIN + r"(?P<heimat1>[^,]+),\s*"
    r"à\s+(?P<place1>[^,]+),\s*et\s*"
    r"(?P<name2>[^,]+),\s*" + _FR_ORIGIN + r"(?P<heimat2>[^,]+),\s*"
    r"à\s+(?P<place2>[^,]+(?:,\s*[A-Z]{1,3})?),\s*(?P<role>[^.]+)\.?",
    re.I | re.UNICODE,
)
_FR_IS_OFFICER = re.compile(
    r"(?P<name>(?-i:[A-ZÀ-Ÿ][\wÀ-ÿ'’\-]+(?:\s+[A-ZÀ-Ÿ][\wÀ-ÿ'’\-]+)+)),\s*"
    + _FR_ORIGIN + r"(?P<heimat>[^,]+),\s*"
    r"à\s+(?P<place>.+?),\s*est\s+"
    r"(?!nommé(?:e)?\b)(?P<role>[^.]+?)\s+avec\s+"
    r"(?P<sign>signature\s+(?:individuelle|collective(?:\s+à\s+deux)?))\.?",
    re.I | re.UNICODE,
)
_FR_IS_OFFICER_SAME_PLACE = re.compile(
    r"(?P<name>(?-i:[A-ZÀ-Ÿ][\wÀ-ÿ'’\-]+(?:\s+[A-ZÀ-Ÿ][\wÀ-ÿ'’\-]+)+)),\s*"
    r"de et à\s+(?P<place>[^,.]+(?:,\s*[A-Z]{1,3})?),\s*est\s+(?!membre\b)"
    r"(?P<role>[^.]+?)\s+avec\s+"
    r"(?P<sign>signature\s+(?:individuelle|collective(?:\s+à\s+deux)?))\.?",
    re.I | re.UNICODE,
)
_FR_IS_OFFICER_BARE_ORIGIN = re.compile(
    r"(?P<name>(?-i:[A-ZÀ-Ÿ][\wÀ-ÿ'’\-]+(?:\s+[A-ZÀ-Ÿ][\wÀ-ÿ'’\-]+)+)),\s*"
    r"(?P<heimat>(?!de\s|du\s|des\s|d['’]|de la\s|de l['’])[^,]+),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*est\s+(?!nommé(?:e)?\b)"
    r"(?P<role>[^.]+?)\s+avec\s+"
    r"(?P<sign>signature\s+(?:individuelle|collective(?:\s+à\s+deux)?))\.?,?",
    re.I | re.UNICODE,
)
_FR_PROCURATION_FOUR_GROUPED = re.compile(
    r"Procuration\s+(?P<kind>individuelle|collective(?:\s+à\s+deux)?),\s*"
    r"toutefois avec (?P<with>.+?),\s*est conférée à\s*"
    r"(?P<name1>[^,]+),\s*de et à\s+(?P<place1>[^,]+),\s*"
    r"(?P<name2>[^,]+),\s*d['’](?P<heimat2>[^,]+),\s*"
    r"(?P<name3>[^,]+),\s*de\s+(?P<heimat3>[^,]+),\s*tous deux à\s+(?P<place23>[^,]+),\s*"
    r"et\s+(?P<name4>[^,]+),\s*de\s+(?P<heimat4>[^,]+),\s*à\s+(?P<place4>[^.]+)\.?,?",
    re.I | re.UNICODE,
)
_FR_PROCURATION_FIVE_GROUPED = re.compile(
    r"Procuration\s+(?P<kind>individuelle|collective(?:\s+à\s+deux)?),\s*"
    r"toutefois avec (?P<with>.+?),\s*est conférée à\s*"
    r"(?P<name1>[^,]+),\s*d['’](?P<heimat1>[^,]+),\s*à\s+(?P<place1>[^,]+),\s*"
    r"(?P<name2>[^,]+),\s*d['’](?P<heimat2>[^,]+),\s*à\s+(?P<place2>[^,]+),\s*"
    r"(?P<name3>[^,]+),\s*de\s+(?P<heimat3>[^,]+),\s*à\s+(?P<place3>[^,]+),\s*"
    r"(?P<name4>[^,]+),\s*de\s+(?P<heimat4>[^,]+),\s*à\s+(?P<place4>[^,]+),\s*"
    r"et\s+(?P<name5>[^,]+),\s*de et à\s+(?P<place5>[^.]+)\.?,?",
    re.I | re.UNICODE,
)
_FR_ELECTED_OFFICER = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,.;]+),\s*(?P<previous>[^,.;]+),\s*"
    r"est élu(?:e)?\s+(?P<role>président(?:e)?)\s*(?:\.|$)",
    re.I | re.UNICODE,
)
_FR_APPOINTED_OFFICER_SIMPLE = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,.;]+)\s+est nommé(?:e)?\s+"
    r"(?P<role>administrateur|administratrice|gérant|gérante|directeur|directrice|"
    r"président|présidente)\s*(?:\.|$)",
    re.I | re.UNICODE,
)
_FR_NEW_MANAGER = re.compile(
    r"Nouve(?:au (?P<role_m>gérant)|lle (?P<role_f>gérante)):\s*"
    r"(?P<name>[A-ZÀ-Ÿ][^,]+),\s*"
    r"(?:de et à\s+(?P<place_same>[^,.;]+)|"
    + _FR_ORIGIN
    + r"(?P<heimat>[^,]+),\s*à\s+(?P<place>[^,]+))"
    r"(?:,\s*(?P<country>[A-Z]{1,3}))?"
    r"(?:,\s*(?P<office>président))?\s*,?\s*avec\s+"
    r"(?P<sign>signature individuelle|signature collective(?:\s+à\s+deux)?)\.?",
    re.I | re.UNICODE,
)
_FR_LIQUIDATOR_NAME = re.compile(
    r"Nouvelle raison sociale de la liquidatrice:\s*"
    r"(?P<name>.+?)\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?",
    re.I,
)
_FR_ASSOCIATE_TRANSFER = re.compile(
    r"Par suite de restructuration,\s*les\s+(?P<count>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+) de (?P<old_name>.+?)\s+"
    r"\((?P<old_uid>CHE-\d{3}\.\d{3}\.\d{3})\) sont transférées à\s+"
    r"(?P<name>.+?)\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"à\s+(?P<place>[^,]+),\s*nouvelle associée avec\s+"
    r"(?P<new_count>[\d']+)\s+parts de CHF\s+(?P<new_nominal>[\d'.]+)\.?",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_PAIR = re.compile(
    r"(?P<seller1>[^.;]+?) a cédé (?P<sold1>[\d']+) parts de CHF\s+"
    r"(?P<nominal>[\d'.]+) et (?P<seller2>[^.;]+?) (?P<sold2>[\d']+) parts "
    r"de CHF\s+(?P<nominal2>[\d'.]+) à (?P<buyer>[^,;]+),\s*"
    + _FR_ORIGIN
    + r"(?P<heimat>[^,]+),\s*à\s+(?P<place>[^,;]+),\s*nouvel associé pour "
    r"(?P<buyer_count>[\d']+) parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"par conséquent (?P=seller1) est maintenant associé pour "
    r"(?P<seller1_count>[\d']+) parts de CHF\s+(?P<seller1_nominal>[\d'.]+) et "
    r"(?P=seller2) pour (?P<seller2_count>[\d']+) parts de CHF\s+"
    r"(?P<seller2_nominal>[\d'.]+)\.\s*L'associé (?P=buyer) est nommé gérant "
    r"avec (?P<sign>signature individuelle|signature collective(?:\s+à\s+deux)?)\.?,?",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_TRIPLE = re.compile(
    r"(?P<seller1>[^,.;]+),\s*(?P<seller2>[^,.;]+)\s+et\s+"
    r"(?P<seller3>[^,.;]+) cèdent respectivement\s+"
    r"(?P<sold1>[\d']+),\s*(?P<sold2>[\d']+)\s+et\s+(?P<sold3>[\d']+) "
    r"de leurs\s+(?P<before1>[\d']+),\s*(?P<before2>[\d']+)\s+et\s+"
    r"(?P<before3>[\d']+) parts de CHF\s+(?P<nominal>[\d'.]+) \u00e0\s+"
    r"(?P<buyer>[^,;]+),\s*de\s+(?P<heimat>[^,;]+),\s*\u00e0\s+"
    r"(?P<place>[^,;]+),\s*nouvel associé sans signature,\s*avec\s+"
    r"(?P<buyer_count>[\d']+) parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"(?P=seller1),\s*(?P=seller2)\s+et\s+(?P=seller3) restent titulaires "
    r"de respectivement\s+(?P<count1>[\d']+),\s*(?P<count2>[\d']+)\s+et\s+"
    r"(?P<count3>[\d']+) parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?,?",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGER_TRANSFER = re.compile(
    r"L['’](?P<seller_role>associé-gérant(?: et président)?)\s+"
    r"(?P<seller>[^,.;]+?)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à la\s+"
    r"(?P<buyer_role>gérante)\s+(?P<buyer>[^,.;]+),\s*nouvelle associée,\s*"
    r"laquelle continue à signer\s+(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.\s*"
    r"(?P=seller) reste titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_AND_MANAGERS = re.compile(
    r"L['’]associée?\s+(?P<seller>[^,.;]+),\s*maintenant domiciliée? à\s+"
    r"(?P<seller_place>[^,.;]+),\s*a cédé\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts sociales de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*de\s+(?P<heimat>[^,.;]+),\s*à\s+"
    r"(?P<buyer_place>[^,.;]+),\s*nouvel associé\.\s*Gérants:\s*"
    r"(?P=buyer),\s*(?P<buyer_office>président),\s*et\s*(?P=seller),\s*"
    r"lesquels signent\s+(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.\s*"
    r"Les pouvoirs de\s+(?P=seller)\s+sont modifiés en ce sens\.?,?",
    re.I | re.UNICODE,
)
_FR_SHAREHOLDERS_NOW_PAIR = re.compile(
    r"(?P<name1>[A-ZÀ-Ÿ][^,.;]+?) est désormais titulaire de\s+"
    r"(?P<count1>[\d']+) parts de CHF\s+(?P<nominal1>[\d'.]+)\s+et\s+"
    r"(?P<name2>[A-ZÀ-Ÿ][^,.;]+?) de\s+(?P<count2>[\d']+) "
    r"parts? de CHF\s+(?P<nominal2>[\d'.]+)\.?,?",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_SHARES_NOW = re.compile(
    r"L['’](?P<role>associé-gérant|associée-gérante)\s+(?P<name>.+?)\s+"
    r"détient maintenant\s+(?P<count>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d']+(?:\.\d+)?)\.?",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_NAMED_PAIR = re.compile(
    r"Administration:\s*(?P<name1>[^,]+),\s*nommé(?:e)?\s+(?P<role1>[^,]+?)\s*,?\s*et\s*"
    r"(?P<name2>[^,]+),\s*" + _FR_ORIGIN + r"(?P<heimat2>[^,]+),\s*"
    r"à\s+(?P<place2>[^,]+),\s*tous deux avec\s+"
    r"(?P<sign>signature\s+(?:individuelle|collective(?:\s+à\s+deux)?))"
    r"(?:,\s*les pouvoirs de\s+(?P<changed>[^,]+?)\s+étant modifiés en ce sens)?\.?",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_NAMED_ROLE_PAIR = re.compile(
    r"Administration:\s*(?P<name1>[^,]+),\s*nommé(?:e)?\s+(?P<role1>[^,]+?)\s*,?\s*et\s*"
    r"(?P<name2>[^,]+),\s*de et à\s+(?P<place2>[^,]+),\s*(?P<role2>[^,]+),\s*"
    r"tous deux avec\s+(?P<sign>signature\s+(?:individuelle|collective(?:\s+à\s+deux)?))\.?,?",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_DOMICILE_PAIR = re.compile(
    r"Administration:\s*(?P<name1>[^,]+),\s*nommé(?:e)?\s+(?P<role1>[^,]+),\s*et\s*"
    r"(?P<name2>[^,]+),\s*maintenant domicilié(?:e)? à\s+(?P<place2>[^,]+),\s*"
    r"lesquels signent\s+(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_SIGN_PAIR = re.compile(
    r"Administration:\s*(?P<name1>[^,]+),\s*nommé(?:e)?\s+(?P<role1>[^,]+?)\s+et\s*"
    r"(?P<name2>[^,]+),\s*" + _FR_ORIGIN + r"(?P<heimat2>[^,]+),\s*"
    r"à\s+(?P<place2>[^,]+),\s*lesquels signent\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_FIRST_DOMICILE_PAIR = re.compile(
    r"Administration:\s*(?P<name1>[^,]+),\s*maintenant domicilié(?:e)? à\s*"
    r"(?P<place1>.+?),\s*nommé(?:e)?\s+(?P<role1>[^,]+?),?\s+et\s*"
    r"(?P<name2>[^,]+),\s*" + _FR_ORIGIN + r"(?P<heimat2>[^,]+),\s*"
    r"à\s+(?P<place2>[^,]+),\s*(?:tous deux avec|lesquels signent)\s+"
    r"(?P<sign>(?:signature\s+)?(?:individuelle(?:ment)?|collective(?:ment)?(?:\s+à\s+deux)?))\.?",
    re.I | re.UNICODE,
)
_FR_SIGNATURE_GRANTED_THREE_MIXED = re.compile(
    r"Signature\s+(?P<kind>individuelle|collective(?:\s+à\s+deux)?),\s*"
    r"toutefois avec\s+(?P<with>[^,]+),\s*(?:est|a été) conférée à\s+"
    r"(?P<name1>[^,]+),\s*à\s+(?P<place1>[^,]+),\s*"
    r"(?P<name2>[^,]+),\s*à\s+(?P<place2>.+?),\s*"
    r"tous deux de\s+(?P<heimat12>[^,]+),\s*et\s+"
    r"(?P<name3>[^,]+),\s*" + _FR_ORIGIN + r"(?P<heimat3>[^,]+),\s*"
    r"à\s+(?P<place3>[^.]+)\.?",
    re.I | re.UNICODE,
)
_FR_COMPOSITION_COMMISSIONER = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,.;]+),\s*" + _FR_ORIGIN + r"(?P<heimat>[^,]+),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*est commissaire au sursis\.?",
    re.I | re.UNICODE,
)
_FR_ORG_NAME_CHANGED = re.compile(
    r"(?P<old_name>.+?)\s+\((?P<old_registry>B\s*\d+)\),\s*"
    r"(?P<role>[^,]+),\s*nouvelle raison sociale\s+"
    r"(?P<name>.+?)\s+\((?P<registry>B\s*\d+)\)$",
    re.I,
)
_FR_AUDITOR_UPDATED = re.compile(
    r"Personnes inscrites modifiées:\s*(?P<name>.+?)\s+"
    r"\((?P<old_id>CHE-\d{3}\.\d{3}\.\d{3}|CH-[\d.-]+-\d)\),\s*"
    r"organe de révision,\s*maintenant à\s+(?P<place>.+?)"
    r"(?:\s+et avec le numéro IDE\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\))?\.?$",
    re.I,
)
_FR_AUDITOR_LEGACY_RENAMED_AND_MOVED = re.compile(
    r"(?:^|(?<=\.\s))(?P<old_name>[^.]+?)\s+"
    r"\((?P<registry_id>CH-[\d.-]+-\d)\),\s*organe de révision,\s*"
    r"nouvelle raison sociale\s+(?P<name>.+?)\s+"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"maintenant à\s+(?P<place>[^.]+)\.?",
    re.I,
)
_FR_NOW_AT = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,]+?) est (?:maintenant|désormais) (?:à|au|aux) (?P<place>[^.]+)",
    re.UNICODE,
)
_FR_AUDITOR_SEAT_NOW = re.compile(
    r"L'organe de révision\s+[\"“]?(?P<name>.+?)[\"”]?\s+"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+a maintenant son siège à\s+"
    r"(?P<place>[^.]+)\. ?",
    re.I,
)
_FR_AUDITOR_RAISON_AND_SEAT = re.compile(
    r"L'organe de révision\s+(?P<old>.+?)\s+a modifié sa raison de commerce en\s+"
    r"(?P<name>.+?)\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"et a transféré son siège à\s+(?P<place>[^.]+)\.?",
    re.I,
)
_FR_AUDITOR_STANDALONE_RENAMED_AND_MOVED = re.compile(
    r"(?P<old>[^.]+?)\s+\((?P<old_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"qui a modifié sa raison de commerce en\s+(?P<name>.+?)\s+"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*est maintenant à\s+"
    r"(?P<place>[^.]+)\.?",
    re.I,
)
_FR_ADMINISTRATORS_CONTINUE_SIGNING = re.compile(
    r"Les administrateurs\s+(?P<name1>[^,]+),\s*nommé\s+(?P<role1>[^,]+),\s*et\s*"
    r"(?P<name2>[^,]+),\s*jusqu'ici\s+(?P<previous_role2>[^,]+),\s*"
    r"continuent à signer\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATORS_ROLES_CHANGED_PAIR = re.compile(
    r"Les administrateurs\s+(?P<name1>[^,]+),\s*jusqu['’]ici\s+"
    r"(?P<old_role1>[^,]+),\s*nommé\s+(?P<role1>[^,]+),\s*et\s*"
    r"(?P<name2>[^,]+),\s*jusqu['’]ici\s+(?P<old_role2>[^,]+),\s*"
    r"nommé\s+(?P<role2>[^,]+),\s*continuent à signer\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?,?",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBERS_CONTINUE_SIGNING = re.compile(
    r"Les membres du conseil\s+(?P<name1>[^,]+),\s*nommé(?:e)?\s+"
    r"(?P<role1>[^,]+),\s*et\s*(?P<name2>[^,]+),\s*jusqu'ici\s+"
    r"(?P<previous_role2>[^,]+),\s*continuent (?:à|de) signer\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?",
    re.I | re.UNICODE,
)
_FR_TWO_DOMICILES_NOW = re.compile(
    r"(?P<name1>[A-ZÀ-Ÿ][^,.;]+?)\s+et\s+"
    r"(?P<name2>[A-ZÀ-Ÿ][^,.;]+?)\s+sont maintenant\s+"
    r"(?:à|au|aux)\s+(?P<place>[^.]+)\.?",
    re.UNICODE,
)
_FR_LIQUIDATEURS = re.compile(
    r"Liquidateurs:\s*les\s+(?P<old_role>administrateurs?)\s+"
    r"(?P<name1>[^,]+?)\s+et\s+(?P<name2>[^,]+?),\s*lesquels continuent à signer\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?",
    re.I | re.UNICODE,
)
_FR_LIQUIDATEURS_WITH_ROLES = re.compile(
    r"Liquidateurs:\s*(?P<name1>[^,]+),\s*(?P<role1>président(?:e)?),\s*et\s*"
    r"(?P<name2>[^,]+),\s*(?P<role2>secrétaire),\s*"
    r"tous deux membres du conseil d['’]administration,\s*lesquels continuent de signer\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?,?",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_LIQUIDATORS = re.compile(
    r"Les membres du conseil de fondation\s+(?P<name1>[^,]+),\s*"
    r"(?P<name2>[^,]+),?\s*et\s+(?P<name3>[^,]+)\s+sont nommés "
    r"liquidateurs avec\s+(?P<sign>signature\s+collective(?:\s+à\s+deux)?|"
    r"signature\s+individuelle)\.?,?",
    re.I | re.UNICODE,
)
_FR_ORG_LIQUIDATOR = re.compile(
    r"Liquidat(?:eur|rice):\s*(?P<name>.+?)\s+"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"à\s+(?P<place>[^.]+)\.?",
    re.I,
)
_FR_ORG_ELECTED_LIQUIDATOR = re.compile(
    r"(?:La liquidation est opérée .+?\s+)?par\s+(?P<name>.+?)\s+"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*élue\s+liquidatrice\.?",
    re.I | re.UNICODE,
)
_FR_ELECTED_LIQUIDATOR = re.compile(
    r"L['’](?P<old_role>administrateur|administratrice)\s+"
    r"(?P<name>[A-ZÀ-Ÿ][^,.;]+),\s*maintenant de\s+(?P<heimat>[^.;]+?)\s+"
    r"est élu(?:e)?\s+(?P<role>liquidateur|liquidatrice)\s+avec\s+"
    r"(?P<sign>signature individuelle|signature collective(?:\s+à\s+deux)?)\.?",
    re.I | re.UNICODE,
)
_FR_CIVIL_NAME_ORIGIN_DOMICILE = re.compile(
    r"(?P<old_name>[A-ZÀ-Ÿ][^,.;]+),\s*qui se nomme désormais\s+"
    r"(?P<name>[^,.;]+),\s*et maintenant de et à\s+(?P<place>[^.]+)\.?",
    re.I | re.UNICODE,
)
_FR_CIVIL_NAME_ORIGIN = re.compile(
    r"(?:L['’](?P<role>associé(?:e)?-gérant(?:e)?)\s+)?"
    r"(?P<old_name>[A-ZÀ-Ÿ][^,.;]+),\s*qui se nomme (?:désormais|maintenant)\s+"
    r"(?P<name>[^,.;]+),\s*est (?:maintenant|désormais)\s+"
    r"(?:du |de la |de l['’]|des |de |d['’])(?P<heimat>[^.]+)\.?",
    re.I | re.UNICODE,
)
_FR_FIRST_NAME_AND_DOMICILE = re.compile(
    r"(?P<surname>[A-ZÀ-Ÿ][\wÀ-ÿ'’\-]+)\s+"
    r"(?P<old_first>[A-ZÀ-Ÿ][\wÀ-ÿ'’\-]+),\s*"
    r"qui se prénomme désormais\s+(?P<first>[A-ZÀ-Ÿ][\wÀ-ÿ'’\-]+),\s*"
    r"est maintenant à\s+(?P<place>[^.]+)\.?",
    re.I | re.UNICODE,
)
_FR_STANDALONE_ORG_RENAMED = re.compile(
    r"(?:^|(?<=\.\s))(?!L['’]organe de révision\b)"
    r"(?P<old_name>[A-ZÀ-Ÿ][^()]+?)\s+\("
    r"(?:(?P<old_registry>CH-[\d.-]+-\d)|(?P<old_uid>CHE-\d{3}\.\d{3}\.\d{3}))\)"
    r"(?:,\s*dont le numéro d'identification des entreprises \(IDE/UID\) "
    r"est le \((?P<assigned_uid>CHE-\d{3}\.\d{3}\.\d{3})\))?,?\s*"
    r"a modifié sa raison de commerce en\s+(?P<name>.+?)\s+"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?",
    re.I | re.UNICODE,
)
_FR_HEAD_OFFICE_REPRESENTATIVES_REMOVED = re.compile(
    r"En application de l'art\.\s*110,\s*al\.\s*1,\s*lit\.\s*e ORC,\s*"
    r"les personnes disposant d'un pouvoir de représentation selon l'inscription "
    r"de l'établissement principal sont radiées,\s*ainsi,\s*les fonctions et signatures de\s*"
    r"(?P<names>.+?)\s+sont radiées\.?",
    re.I | re.UNICODE,
)
_FR_HEAD_OFFICE_REPRESENTATIVES_REMOVED_RIGHT_CHANGE = re.compile(
    r"Les informations relatives aux personnes disposant d'un pouvoir de représentation "
    r"pour toute l'entreprise sont radiées conformément à l'art\.\s*110,\s*al\.\s*1,\s*"
    r"let\.\s*e ORC,\s*suite à la modification du droit du registre du commerce\.\s*"
    r"(?:Est concerné|Sont concernés):\s*(?P<names>[^.]+)\.?",
    re.I | re.UNICODE,
)
_DE_AUDITOR_FIRMA = re.compile(
    r"Die eingetragene Revisionsstelle\s+(?P<old>.+?)\s+\([^)]+\)\s+"
    r"firmiert neu\s+(?P<name>.+?)\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?",
    re.I,
)
_DE_AUDITOR_PERSON_RENAMED = re.compile(
    r"Eingetragene Person geändert:\s*(?P<old_name>.+?)\s+"
    r"\((?P<old_id>CHE-\d{3}\.\d{3}\.\d{3}|CH-[\d.-]+-\d)\),\s*"
    r"(?P<role>Revisionsorgan|Revisionsstelle),\s*firmiert neu\s+"
    r"(?P<name>.+?)"
    r"(?:\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\))?\.?$",
    re.I,
)
_DE_AUDITOR_REMOVED = re.compile(
    r"(?:^|(?<=\.\s))(?P<name>[A-ZÄÖÜ][\wÀ-ÿ'’&.,\- ]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+"
    r"ist nicht mehr\s+(?P<role>Revisionsorgan|Revisionsstelle)\.?",
    re.I | re.UNICODE,
)
_DE_AUDITOR_MOVED = re.compile(
    r"Eingetragene Person geändert:\s*(?P<name>.+?)\s+"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"(?P<role>Revisionsorgan|Revisionsstelle),\s*neu in\s+(?P<place>[^.]+)\.?",
    re.I,
)
_DE_AUDITOR_REPLACED = re.compile(
    r"(?:^|(?<=\.\s))(?P<old_name>[^.]+?)\s+"
    r"\((?P<old_registry>CH-[\d.-]+-\d)\)\s+"
    r"ist nicht mehr Revisionsstelle\.\s*Neue Revisionsstelle:\s*"
    r"(?P<name>.+?)\s+\(\s*(?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\s*\)"
    r"(?:,\s*in\s+(?P<place>[^.]+))?\.?",
    re.I,
)
_FR_PERSONNE_RADIEE = re.compile(
    r"Personne radiée:\s*(?P<name>[^,]+),\s*(?P<role>.+?),\s*"
    r"(?P<sign>signature\s+(?:individuelle|collective(?:\s+à\s+deux)?))\.?",
    re.I | re.UNICODE,
)
_DE_COURT_SIGNING_AND_NAME_CORRECTION = re.compile(
    r"Mit Entscheid vom (?P<decision_date>\d{2}\.\d{2}\.\d{4}) hat (?P<authority>.+?) "
    r"die mit Entscheid vom (?P<original_date>\d{2}\.\d{2}\.\d{4}) verhängte "
    r"Entziehung der Vertretungsbefugnis von (?P<removed>.+?) für die Kollektivgesellschaft "
    r"und die Übertragung der alleinigen Vertretung an (?P<granted>.+?) bestätigt\.\s*"
    r"Die Publikation im SHAB vom (?P<publication_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"Id (?P<publication_id>\d+),\s*wird dahingehend berichtigt,\s*dass die Gesellschafterin "
    r"richtigerweise (?P<correct_name>.+?) \(und nicht (?P<wrong_name>.+?)\) heisst\.?",
    re.I | re.UNICODE,
)


def _event(
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
    event_type: str,
    rule_id: str,
    *,
    name: str,
    place: str | None = None,
    uid: str | None = None,
    role: str | None = None,
    signing: str | None = None,
    extra: dict | None = None,
) -> Event:
    payload = {"name": name, "place": place, **(extra or {})}
    return Event(
        publication_id=publication_id,
        published_at=published_at,
        event_type=event_type,
        rule_id=rule_id,
        org_uid=org_uid,
        person_key=person_key(name=name, place=place, uid=uid),
        plz=plz,
        canton=canton,
        role=role,
        signing=signing,
        payload=payload,
    )


def _de_signing(raw: str | None) -> str | None:
    if raw and raw.lower() in {
        "unterschrift zu zweien",
        "kollketivunterschrift zu zweien",
    }:
        return "Kollektivunterschrift zu zweien"
    return raw


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{year}-{month}-{day}"


def extract_persons(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Return person events and leftover publicationText (sections consumed)."""
    lang = (language or "de").lower()
    updated_auditor = _FR_AUDITOR_UPDATED.search(text)
    prefix_events: list[Event] = []
    if updated_auditor:
        old_id = updated_auditor.group("old_id")
        uid = updated_auditor.group("uid") or _che_uid(old_id)
        extra = {"previous_registry_id": old_id} if old_id.startswith("CH-") else None
        prefix_events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.auditor_updated.v1",
                name=updated_auditor.group("name").strip(),
                place=updated_auditor.group("place").strip(),
                uid=uid,
                role="organe de révision",
                extra=extra,
            )
        )
        text = text.replace(updated_auditor.group(0), " ")
    mixed_language_auditor = _FR_MIXED_LANGUAGE_AUDITOR_CHANGED.search(text)
    if mixed_language_auditor:
        prefix_events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.auditor_renamed.v7",
                name=mixed_language_auditor.group("name").strip(),
                place=mixed_language_auditor.group("place").strip(),
                uid=mixed_language_auditor.group("uid"),
                role=mixed_language_auditor.group("role").strip(),
                extra={
                    "action": "name_and_seat_changed",
                    "previous": mixed_language_auditor.group("old_name").strip(),
                    "previous_registry_id": mixed_language_auditor.group(
                        "old_registry"
                    ),
                },
            )
        )
        text = text.replace(mixed_language_auditor.group(0), " ")
    personne_radiee = _FR_PERSONNE_RADIEE.search(text)
    if personne_radiee:
        prefix_events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_removed",
                "fr.persons.removed.v1",
                name=personne_radiee.group("name").strip(),
                role=personne_radiee.group("role").strip(),
                signing=_fr_signing(personne_radiee.group("sign")),
            )
        )
        text = text.replace(personne_radiee.group(0), " ")
    compact_changed = _DE_COMPACT_PERSON_CHANGED.search(text)
    if compact_changed:
        name = re.sub(r"\s+", " ", compact_changed.group("name")).strip()
        role = compact_changed.group("role").strip()
        place = compact_changed.group("place").strip()
        signing = _de_signing(compact_changed.group("sign"))
        prefix_events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "de.persons.compact_changed.v1",
                name=name,
                place=place,
                role=role,
                signing=signing,
                extra={"action": "domicile_changed"},
            )
        )
        prefix_events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "de.persons.signing.v1",
                name=name,
                place=place,
                role=role,
                signing=signing,
            )
        )
        text = text.replace(compact_changed.group(0), " ")
    if lang != "fr" and _FR_SECTION_START.search(text):
        mixed_events, text = _extract_fr_sections(
            text, publication_id, published_at, org_uid, plz, canton
        )
        prefix_events.extend(mixed_events)
    if lang == "de":
        events, leftover = _extract_de(text, publication_id, published_at, org_uid, plz, canton)
        return prefix_events + events, leftover
    if lang == "fr":
        events, leftover = _extract_fr(text, publication_id, published_at, org_uid, plz, canton)
        return prefix_events + events, leftover
    if lang == "it":
        events, leftover = _extract_it(text, publication_id, published_at, org_uid, plz, canton)
        return prefix_events + events, leftover
    return prefix_events, text


def _extract_de(
    text: str,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    events: list[Event] = []
    starts = list(_DE_SECTION_START.finditer(text))
    leftover = text
    if starts:
        leftover = text[: starts[0].start()].strip()
        for index, match in enumerate(starts):
            label = match.group("label")
            body_start = match.end()
            body_end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
            body = text[body_start:body_end].strip().rstrip(".")
            action = (
                "officer_removed"
                if re.search(r"Ausgeschiedene|Gelöschte", label, re.I)
                else "officer_changed"
            )
            for chunk in body.split(";"):
                chunk = chunk.strip()
                if not chunk:
                    continue
                _append_de_chunk(
                    events,
                    chunk,
                    action,
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                )
    court_signing = _DE_COURT_SIGNING_AND_NAME_CORRECTION.search(leftover)
    if court_signing:
        common = {
            "decision_date": _iso_date(court_signing.group("decision_date")),
            "original_decision_date": _iso_date(court_signing.group("original_date")),
            "authority": court_signing.group("authority").strip(),
        }
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "de.persons.court_signing.v1",
                name=court_signing.group("removed").strip(),
                extra={"action": "revoked", **common},
            )
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "de.persons.court_signing.v1",
                name=court_signing.group("granted").strip(),
                signing="Einzelunterschrift",
                extra={"action": "granted", **common},
            )
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "de.persons.name_correction.v1",
                name=court_signing.group("correct_name").strip(),
                role="Gesellschafterin",
                extra={
                    "action": "name_corrected",
                    "previous": court_signing.group("wrong_name").strip(),
                    "corrected_publication_date": _iso_date(
                        court_signing.group("publication_date")
                    ),
                    "corrected_publication_id": court_signing.group("publication_id"),
                },
            )
        )
        leftover = leftover.replace(court_signing.group(0), " ")
    auditor_person_renamed = _DE_AUDITOR_PERSON_RENAMED.search(leftover)
    if auditor_person_renamed:
        old_id = auditor_person_renamed.group("old_id")
        uid = auditor_person_renamed.group("uid") or _che_uid(old_id)
        extra = {
            "action": "name_changed",
            "previous": auditor_person_renamed.group("old_name").strip(),
        }
        if old_id.startswith("CH-"):
            extra["previous_registry_id"] = old_id
        else:
            extra["previous_uid"] = old_id
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "de.persons.auditor_renamed.v2",
                name=auditor_person_renamed.group("name").strip(),
                uid=uid,
                role=auditor_person_renamed.group("role").strip(),
                extra=extra,
            )
        )
        leftover = leftover.replace(auditor_person_renamed.group(0), " ")
        leftover = re.sub(r"\s+", " ", leftover).strip(" .")
    auditor_removed = _DE_AUDITOR_REMOVED.search(leftover)
    if auditor_removed:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_removed",
                "de.persons.auditor_removed.v1",
                name=auditor_removed.group("name").strip(),
                uid=auditor_removed.group("uid"),
                role=auditor_removed.group("role").strip(),
                extra={"action": "removed"},
            )
        )
        leftover = leftover.replace(auditor_removed.group(0), " ")
        leftover = re.sub(r"\s+", " ", leftover).strip(" .")
    auditor_firma = _DE_AUDITOR_FIRMA.search(leftover)
    if auditor_firma:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "de.persons.auditor_renamed.v1",
                name=auditor_firma.group("name").strip(),
                uid=auditor_firma.group("uid"),
                role="Revisionsstelle",
                extra={"previous": auditor_firma.group("old").strip()},
            )
        )
        leftover = leftover.replace(auditor_firma.group(0), " ")
        leftover = re.sub(r"\s+", " ", leftover).strip(" .")
    auditor_moved = _DE_AUDITOR_MOVED.search(leftover)
    if auditor_moved:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "de.persons.auditor_moved.v1",
                name=auditor_moved.group("name").strip(),
                place=auditor_moved.group("place").strip(),
                uid=auditor_moved.group("uid"),
                role=auditor_moved.group("role").strip(),
                extra={"action": "seat_changed"},
            )
        )
        leftover = leftover.replace(auditor_moved.group(0), " ")
        leftover = re.sub(r"\s+", " ", leftover).strip(" .")
    auditor_replaced = _DE_AUDITOR_REPLACED.search(leftover)
    if auditor_replaced:
        common = {
            "replacement": auditor_replaced.group("name").strip(),
            "replacement_uid": auditor_replaced.group("uid"),
        }
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_removed",
                "de.persons.auditor_replaced.v1",
                name=auditor_replaced.group("old_name").strip(),
                role="Revisionsstelle",
                extra={
                    "action": "replaced",
                    "registry_id": auditor_replaced.group("old_registry"),
                    **common,
                },
            )
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "de.persons.auditor_replaced.v1",
                name=auditor_replaced.group("name").strip(),
                place=(auditor_replaced.group("place") or "").strip() or None,
                uid=auditor_replaced.group("uid"),
                role="Revisionsstelle",
                extra={
                    "action": "appointed",
                    "previous": auditor_replaced.group("old_name").strip(),
                    "previous_registry_id": auditor_replaced.group("old_registry"),
                },
            )
        )
        leftover = leftover.replace(auditor_replaced.group(0), " ")
        leftover = re.sub(r"\s+", " ", leftover).strip(" .")
    return events, leftover


_IT_CANCELLED = re.compile(r"La società è cancellata[^.]*\.?", re.I)
_IT_SECTION_START = re.compile(
    r"(?P<label>Nuove persone iscritte[^:]*|Persone dimissionarie[^:]*|"
    r"Persone iscritte[^:]*|Persone cancellate[^:]*):",
    re.I,
)
_IT_PERSON = re.compile(
    r"(?P<last>[A-ZÀ-Ÿ][\wÀ-ÿ'\-]+),\s*"
    r"(?P<first>[^,]+?),\s*"
    r"(?:(?:da|di)\s+(?P<heimat>[^,]+)|(?P<nationality>[^,]+)),\s*"
    r"(?:in|a)\s+(?P<place>[^,]+)"
    r"(?:,\s*(?P<role>(?!con\s)[^,]+))?"
    r"(?:,\s*con\s+(?P<sign>(?:firma|procura) individuale|(?:firma|procura) collettiva(?:\s+a\s+due)?)"
    r"(?P<sign_note>[^;]*))?",
    re.I | re.UNICODE,
)
_IT_ORG = re.compile(
    r"(?P<name>[^;]+?)\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3}|CH-[\d.-]+-\d)\)"
    r"(?:,\s*in\s+(?P<place>[^,]+))?,\s*"
    r"(?P<role>[^,]+)",
    re.UNICODE,
)
_IT_ORG_PLAIN = re.compile(
    r"(?P<name>[^;]+?),\s*in\s+(?P<place>[^,]+),\s*"
    r"(?P<role>(?!con\s)[^,.]+)",
    re.UNICODE,
)


def _it_signing(raw: str) -> str:
    lower = raw.lower()
    if "procura" in lower:
        return "Einzelprokura" if "individuale" in lower else "Kollektivprokura zu zweien"
    if "individuale" in lower:
        return "Einzelunterschrift"
    if "collettiva" in lower:
        return "Kollektivunterschrift zu zweien"
    return raw


def _extract_it(
    text: str,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    events: list[Event] = []
    starts = list(_IT_SECTION_START.finditer(text))
    leftover = text
    if starts:
        leftover = text[: starts[0].start()].strip()
        for index, match in enumerate(starts):
            label = match.group("label")
            body_start = match.end()
            body_end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
            body = text[body_start:body_end].strip().rstrip(".")
            action = (
                "officer_removed"
                if re.search(r"dimissionarie|cancellate", label, re.I)
                else "officer_changed"
            )
            for chunk in body.split(";"):
                chunk = chunk.strip()
                if not chunk:
                    continue
                _append_it_chunk(
                    events,
                    chunk,
                    action,
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                )
    cancel = _IT_CANCELLED.search(leftover)
    if cancel:
        leftover = leftover.replace(cancel.group(0), " ")
        leftover = re.sub(r"\s+", " ", leftover).strip(" .")
    return events, leftover


def _append_it_chunk(
    events: list[Event],
    chunk: str,
    action: str,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> None:
    org = _IT_ORG.search(chunk)
    person = _IT_PERSON.search(chunk)
    if org and (not person or org.start() < person.start()):
        extra = {}
        uid = _che_uid(org.group("uid"))
        if not uid and org.group("uid"):
            extra["registry_id"] = org.group("uid")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                action,
                "it.persons.org.v1",
                name=org.group("name").strip(),
                place=org.group("place"),
                uid=uid,
                role=org.group("role").strip(),
                extra=extra or None,
            )
        )
        return
    plain = _IT_ORG_PLAIN.search(chunk)
    if plain and (not person or plain.start() < person.start()):
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                action,
                "it.persons.org.v1",
                name=plain.group("name").strip(),
                place=plain.group("place"),
                role=plain.group("role").strip(),
            )
        )
        return
    if not person:
        return
    name = f"{person.group('last')}, {person.group('first').strip()}"
    raw_sign = person.group("sign")
    signing = _it_signing(raw_sign) if raw_sign else None
    role = (person.group("role") or "").strip() or None
    extra = {
        "heimat": person.group("heimat"),
        "nationality": person.group("nationality"),
    }
    note = (person.group("sign_note") or "").strip()
    if note:
        extra["signing_note"] = note
    events.append(
        _event(
            publication_id,
            published_at,
            org_uid,
            plz,
            canton,
            action,
            "it.persons.natural.v1",
            name=name,
            place=person.group("place"),
            role=role,
            signing=signing,
            extra=extra,
        )
    )
    if signing:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "it.persons.signing.v1",
                name=name,
                place=person.group("place"),
                role=role,
                signing=signing,
            )
        )


def _fr_signing(raw: str | None) -> str | None:
    if not raw:
        return None
    lower = raw.lower()
    if "procuration" in lower:
        return "Einzelprokura" if "individuelle" in lower else "Kollektivprokura zu zweien"
    if "individuelle" in lower:
        return "Einzelunterschrift"
    if "collective" in lower or "collecvtive" in lower or "collcetive" in lower:
        return "Kollektivunterschrift zu zweien"
    return raw


def _append_fr_chunk(
    events: list[Event],
    chunk: str,
    action: str,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> None:
    renamed_org = _FR_ORG_NAME_CHANGED.search(chunk)
    if renamed_org:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                action,
                "fr.persons.org_name_changed.v1",
                name=renamed_org.group("name").strip(),
                role=renamed_org.group("role").strip(),
                extra={
                    "action": "name_changed",
                    "previous": renamed_org.group("old_name").strip(),
                    "previous_registry_id": renamed_org.group("old_registry").replace(" ", ""),
                    "registry_id": renamed_org.group("registry").replace(" ", ""),
                },
            )
        )
        return
    foreign_org = _FR_FOREIGN_ORG.search(chunk)
    if foreign_org:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                action,
                "fr.persons.foreign_org.v1",
                name=foreign_org.group("name").strip(),
                place=(foreign_org.group("place") or "").strip() or None,
                role=foreign_org.group("role").strip(),
                extra={"registry_id": foreign_org.group("registry_id").strip()},
            )
        )
        return
    org = _FR_ORG.search(chunk)
    newbie = _FR_NEW_INSCRIT_WITH.search(chunk) or _FR_NEW_INSCRIT.search(chunk)
    person = _FR_LIST_PERSON.search(chunk)
    if org and (not person or org.start() < person.start()) and (not newbie or org.start() < newbie.start()):
        extra = {}
        uid = _che_uid(org.group("uid"))
        if not uid and org.group("uid"):
            extra["registry_id"] = org.group("uid")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                action,
                "fr.persons.org.v1",
                name=org.group("name").strip(),
                place=org.group("place"),
                uid=uid,
                role=org.group("role").strip(),
                extra=extra or None,
            )
        )
        return
    plain_org = _FR_ORG_PLAIN.search(chunk)
    if plain_org and (not person or plain_org.start() < person.start()) and (
        not newbie or plain_org.start() < newbie.start()
    ):
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                action,
                "fr.persons.org.v1",
                name=plain_org.group("name").strip(),
                place=plain_org.group("place").strip(),
                role=plain_org.group("role").strip(),
            )
        )
        return
    if newbie and (not person or newbie.start() <= person.start()):
        name = re.sub(r"\s+", " ", newbie.group("name")).strip()
        signing = _fr_signing(newbie.group("sign"))
        extra = {"heimat": newbie.group("heimat").strip()}
        role = (newbie.group("role") or "").strip() or None
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                action,
                "fr.persons.list.v1",
                name=name,
                place=newbie.group("place").strip(),
                role=role,
                signing=signing,
                extra=extra,
            )
        )
        if signing:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.list_signing.v1",
                    name=name,
                    place=newbie.group("place").strip(),
                    signing=signing,
                )
            )
        return
    natural = _FR_NATURAL.search(chunk)
    if natural and (not person or natural.start() <= person.start()):
        name = f"{natural.group('last')}, {natural.group('first').strip()}"
        signing = _fr_signing(natural.group("sign"))
        extra = {
            "heimat": natural.group("heimat"),
            "nationality": natural.group("nationality"),
        }
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                action,
                "fr.persons.natural.v1",
                name=name,
                place=natural.group("place"),
                role=(natural.group("role") or "").strip() or None,
                signing=signing,
                extra=extra,
            )
        )
        if signing:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.natural_signing.v1",
                    name=name,
                    place=natural.group("place"),
                    role=(natural.group("role") or "").strip() or None,
                    signing=signing,
                )
            )
        return
    sign_only = _FR_SIGN_ONLY.search(chunk)
    if sign_only and (not person or sign_only.start() <= person.start()):
        name = re.sub(r"\s+", " ", sign_only.group("name")).strip()
        signing = _fr_signing(f"{sign_only.group('kind')} {sign_only.group('sign')}")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                action,
                "fr.persons.list.v1",
                name=name,
                signing=signing,
            )
        )
        if signing:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.list_signing.v1",
                    name=name,
                    signing=signing,
                )
            )
        return
    if not person:
        role_changed = _FR_LIST_ROLE_CHANGED.search(chunk)
        if role_changed:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    action,
                    "fr.persons.role_changed.v1",
                    name=re.sub(r"\s+", " ", role_changed.group("name")).strip(),
                    role=role_changed.group("role_new").strip(),
                    extra={"previous": role_changed.group("role").strip()},
                )
            )
            return
        without_sign = _FR_LIST_WITHOUT_SIGN.search(chunk)
        if not without_sign:
            return
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                action,
                "fr.persons.list.v1",
                name=re.sub(r"\s+", " ", without_sign.group("name")).strip(),
                role=without_sign.group("role").strip(),
            )
        )
        return
    name = re.sub(r"\s+", " ", person.group("name")).strip()
    role_new = (person.group("role_new") or "").strip()
    role = role_new or person.group("role").strip()
    signing = _fr_signing(person.group("sign_new") or person.group("sign"))
    extra = {}
    if role_new:
        extra["previous"] = person.group("role").strip()
    events.append(
        _event(
            publication_id,
            published_at,
            org_uid,
            plz,
            canton,
            action,
            "fr.persons.list.v1",
            name=name,
            role=role,
            signing=signing,
            extra=extra or None,
        )
    )
    if signing:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.list_signing.v1",
                name=name,
                role=role,
                signing=signing,
            )
        )


def _extract_fr_sections(
    text: str,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    events: list[Event] = []
    starts = list(_FR_SECTION_START.finditer(text))
    if not starts:
        return events, text
    leftover_parts = [text[: starts[0].start()].strip()]
    for index, match in enumerate(starts):
        label = match.group("label")
        body_start = match.end()
        body_end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        body = text[body_start:body_end].strip().rstrip(".")
        trailing_audit = _FR_SECTION_TRAILING_AUDIT.search(body)
        if trailing_audit:
            leftover_parts.append(trailing_audit.group("tail").strip())
            body = body[: trailing_audit.start()].rstrip(" .")
        action = "officer_removed" if re.search(r"radiée", label, re.I) else "officer_changed"
        for chunk in body.split(";"):
            chunk = chunk.strip()
            if not chunk:
                continue
            _append_fr_chunk(
                events,
                chunk,
                action,
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
            )
    return events, " ".join(part for part in leftover_parts if part)


def _de_chunk_extra(chunk: str) -> dict:
    extra: dict = {}
    shares = _DE_SHARES.search(chunk)
    if shares:
        extra["shares_count"] = int(shares.group("count"))
        extra["shares_nominal"] = shares.group("nominal")
    bisher = _DE_BISHER.search(chunk)
    if bisher:
        extra["previous"] = bisher.group("bisher").strip()
    return extra


def _append_de_chunk(
    events: list[Event],
    chunk: str,
    action: str,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> None:
    org = _DE_ORG.search(chunk)
    person = _DE_PERSON.search(chunk)
    named_person = _DE_NAMED_PERSON.search(chunk)
    sign_match = _DE_SIGN_IN_CHUNK.search(chunk)
    signing = _de_signing(sign_match.group(1)) if sign_match else None
    extra = _de_chunk_extra(chunk)
    if org and (not person or org.start() < person.start()):
        uid = _che_uid(org.group("uid"))
        registry_id = org.group("registry_id") or (None if uid else org.group("uid"))
        if registry_id:
            extra["registry_id"] = registry_id
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                action,
                "de.persons.org.v1",
                name=org.group("name").strip(),
                place=org.group("place"),
                uid=uid,
                role=org.group("role").strip(),
                signing=signing,
                extra=extra or None,
            )
        )
        return
    if person:
        name = f"{person.group('last')}, {person.group('first').strip()}"
        extra = {
            "heimat": person.group("heimat"),
            "nationality": person.group("nationality"),
            **extra,
        }
        if person.group("unknown"):
            extra["domicile"] = "unknown"
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                action,
                "de.persons.natural.v1",
                name=name,
                place=person.group("place"),
                role=(person.group("role") or "").strip() or None,
                signing=_de_signing(person.group("sign")),
                extra=extra,
            )
        )
        if signing:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "de.persons.signing.v1",
                    name=name,
                    place=person.group("place"),
                    role=(person.group("role") or "").strip() or None,
                    signing=signing,
                )
            )
        return

    if named_person:
        name = re.sub(r"\s+", " ", named_person.group("name")).strip()
        role = named_person.group("role").strip()
        signing = _de_signing(named_person.group("sign"))
        place = named_person.group("place").strip()
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                action,
                "de.persons.named_natural.v1",
                name=name,
                place=place,
                role=role,
                signing=signing,
                extra={"heimat": named_person.group("heimat").strip()},
            )
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "de.persons.signing.v1",
                name=name,
                place=place,
                role=role,
                signing=signing,
            )
        )
        return

    without_signature = _DE_WITHOUT_SIGNATURE.search(chunk)
    if without_signature:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                action,
                "de.persons.without_signature.v1",
                name=re.sub(r"\s+", " ", without_signature.group("name")).strip(),
                role=without_signature.group("role").strip(),
            )
        )
        return

    mutated = _DE_MUTATED.search(chunk)
    if mutated:
        name = re.sub(r"\s+", " ", mutated.group("name")).strip()
        role = (mutated.group("role_new") or mutated.group("role") or "").strip()
        signing = mutated.group("sign_new") or mutated.group("sign")
        extra = {}
        if mutated.group("role_new"):
            extra["previous"] = mutated.group("role").strip()
        place = (mutated.group("place") or "").strip() or None
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                action,
                "de.persons.mutated.v1",
                name=name,
                place=place,
                role=role or None,
                signing=signing,
                extra=extra or None,
            )
        )
        if signing:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "de.persons.signing.v1",
                    name=name,
                    place=place,
                    role=role or None,
                    signing=signing,
                )
            )
        return

    sign_only = _DE_SIGN_ONLY.search(chunk)
    if sign_only:
        name = re.sub(r"\s+", " ", sign_only.group("name")).strip()
        signing = _de_signing(sign_only.group("sign"))
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                action,
                "de.persons.sign_only.v1",
                name=name,
                signing=signing,
            )
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "de.persons.signing.v1",
                name=name,
                signing=signing,
            )
        )
        return

    plain = _DE_ORG_PLAIN.search(chunk)
    if plain:
        extra = _de_chunk_extra(chunk)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                action,
                "de.persons.org.v1",
                name=plain.group("name").strip(),
                place=plain.group("place"),
                role=plain.group("role").strip(),
                extra=extra or None,
            )
        )


def _extract_fr(
    text: str,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    events, leftover = _extract_fr_sections(
        text, publication_id, published_at, org_uid, plz, canton
    )
    mixed_administration = _FR_ADMINISTRATION_MIXED_PAIR.search(leftover)
    if mixed_administration:
        people = (
            (
                mixed_administration.group("name1").strip(),
                None,
                mixed_administration.group("role1").strip(),
                _fr_signing(mixed_administration.group("sign1")),
                {"action": "role_changed", "signing_action": "kept"},
            ),
            (
                mixed_administration.group("name2").strip(),
                mixed_administration.group("place2").strip(),
                "administrateur",
                _fr_signing(mixed_administration.group("sign2")),
                {
                    "action": "appointed",
                    "heimat": mixed_administration.group("heimat2").strip(),
                    "country": mixed_administration.group("country2"),
                },
            ),
        )
        for name, place, role, signing, extra in people:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.administration_mixed_pair.v1",
                    name=name,
                    place=place,
                    role=role,
                    signing=signing,
                    extra=extra,
                )
            )
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.administration_mixed_pair_signing.v1",
                    name=name,
                    place=place,
                    role=role,
                    signing=signing,
                    extra={"action": extra["signing_action"] if "signing_action" in extra else "granted"},
                )
            )
        leftover = leftover.replace(mixed_administration.group(0), " ")
    managers = _FR_MANAGERS_PAIR.search(leftover)
    if managers:
        signing = _fr_signing(managers.group("sign"))
        role = managers.group("role").strip().rstrip("s")
        shared = {"with": managers.group("with").strip()} if managers.group("with") else {}
        for index in range(1, 3):
            name = managers.group(f"name{index}").strip()
            place = managers.group(f"place{index}").strip()
            extra = {"heimat": managers.group(f"heimat{index}").strip(), **shared}
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.managers_pair.v1",
                    name=name,
                    place=place,
                    role=role,
                    signing=signing,
                    extra=extra,
                )
            )
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.managers_pair_signing.v1",
                    name=name,
                    place=place,
                    role=role,
                    signing=signing,
                    extra=shared or None,
                )
            )
        leftover = leftover.replace(managers.group(0), " ")
    appointed_pair = _FR_APPOINTED_PAIR_PROCURATION_REVOKED.search(leftover)
    if appointed_pair:
        signing = _fr_signing(appointed_pair.group("sign"))
        for index in range(1, 3):
            name = appointed_pair.group(f"name{index}").strip()
            role = appointed_pair.group(f"role{index}").strip()
            common = {
                "previous_signing": "procuration",
                "procuration_revoked": True,
            }
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.appointed_pair.v1",
                    name=name,
                    role=role,
                    signing=signing,
                    extra={"action": "appointed", **common},
                )
            )
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.appointed_pair_signing.v1",
                    name=name,
                    role=role,
                    signing=signing,
                    extra={"action": "modified", **common},
                )
            )
        leftover = leftover.replace(appointed_pair.group(0), " ")
    bureau_group = _FR_BUREAU_GROUP.search(leftover)
    if bureau_group:
        first_signing = _fr_signing(bureau_group.group("sign1"))
        second_signing = _fr_signing(bureau_group.group("sign2"))
        people = (
            (
                bureau_group.group("name1").strip(),
                bureau_group.group("role1").strip(),
                first_signing,
                {"previous": bureau_group.group("old_role1").strip(), "action": "role_changed"},
            ),
            (
                bureau_group.group("name2").strip(),
                bureau_group.group("role2").strip(),
                first_signing,
                {"action": "role_changed"},
            ),
            (
                bureau_group.group("name3").strip(),
                f"membre du conseil et {bureau_group.group('role34').strip()}",
                second_signing,
                {"action": "additional_role"},
            ),
            (
                bureau_group.group("name4").strip(),
                f"membre du conseil et {bureau_group.group('role34').strip()}",
                second_signing,
                {"action": "additional_role"},
            ),
        )
        for name, role, signing, extra in people:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.bureau_group.v1",
                    name=name,
                    role=role,
                    signing=signing,
                    extra=extra,
                )
            )
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.bureau_group_signing.v1",
                    name=name,
                    role=role,
                    signing=signing,
                    extra={"action": "kept" if extra["action"] == "additional_role" else "modified"},
                )
            )
        leftover = leftover.replace(bureau_group.group(0), " ")
    auditor_federal_number = _FR_AUDITOR_RENAME_FEDERAL_NUMBER.search(leftover)
    if auditor_federal_number:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.auditor_renamed.v8",
                name=auditor_federal_number.group("name").strip(),
                uid=auditor_federal_number.group("uid"),
                role="organe de révision",
                extra={
                    "previous": auditor_federal_number.group("old_name").strip(),
                    "previous_registry_id": auditor_federal_number.group(
                        "registry_id"
                    ),
                },
            )
        )
        leftover = leftover.replace(auditor_federal_number.group(0), " ")
    associate_transfer_triple = _FR_ASSOCIATE_TRANSFER_TRIPLE.search(leftover)
    if associate_transfer_triple:
        nominal = associate_transfer_triple.group("nominal")
        for index in range(1, 4):
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.associate_transfer_triple.v1",
                    name=associate_transfer_triple.group(f"seller{index}").strip(),
                    role="associé",
                    extra={
                        "action": "shareholding_changed",
                        "shares_transferred": int(
                            associate_transfer_triple.group(f"sold{index}").replace("'", "")
                        ),
                        "previous_shares_count": int(
                            associate_transfer_triple.group(f"before{index}").replace("'", "")
                        ),
                        "shares_count": int(
                            associate_transfer_triple.group(f"count{index}").replace("'", "")
                        ),
                        "shares_nominal": nominal,
                    },
                )
            )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.associate_transfer_triple.v1",
                name=associate_transfer_triple.group("buyer").strip(),
                place=associate_transfer_triple.group("place").strip(),
                role="associé",
                extra={
                    "action": "shares_received",
                    "heimat": associate_transfer_triple.group("heimat").strip(),
                    "shares_count": int(
                        associate_transfer_triple.group("buyer_count").replace("'", "")
                    ),
                    "shares_nominal": associate_transfer_triple.group("buyer_nominal"),
                    "without_signature": True,
                },
            )
        )
        leftover = leftover.replace(associate_transfer_triple.group(0), " ")
    associate_transfer_and_managers = _FR_ASSOCIATE_TRANSFER_AND_MANAGERS.search(
        leftover
    )
    if associate_transfer_and_managers:
        seller = associate_transfer_and_managers.group("seller").strip()
        buyer = associate_transfer_and_managers.group("buyer").strip()
        nominal = associate_transfer_and_managers.group("nominal")
        transferred = int(
            associate_transfer_and_managers.group("transferred").replace("'", "")
        )
        before = int(
            associate_transfer_and_managers.group("before").replace("'", "")
        )
        signing = _fr_signing(associate_transfer_and_managers.group("sign"))
        seller_role = "associée, gérante"
        buyer_role = (
            "associé, gérant, "
            + associate_transfer_and_managers.group("buyer_office").strip()
        )
        people = (
            (
                seller,
                associate_transfer_and_managers.group("seller_place").strip(),
                seller_role,
                {
                    "action": "domicile_and_shareholding_changed",
                    "shares_transferred": transferred,
                    "previous_shares_count": before,
                    "shares_count": before - transferred,
                    "shares_nominal": nominal,
                    "signing_action": "modified",
                },
            ),
            (
                buyer,
                associate_transfer_and_managers.group("buyer_place").strip(),
                buyer_role,
                {
                    "action": "appointed_and_shares_received",
                    "heimat": associate_transfer_and_managers.group("heimat").strip(),
                    "shares_count": transferred,
                    "shares_nominal": nominal,
                    "signing_action": "granted",
                },
            ),
        )
        for name, place, role, extra in people:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.associate_transfer_and_managers.v1",
                    name=name,
                    place=place,
                    role=role,
                    signing=signing,
                    extra={key: value for key, value in extra.items() if key != "signing_action"},
                )
            )
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.associate_transfer_and_managers_signing.v1",
                    name=name,
                    place=place,
                    role=role,
                    signing=signing,
                    extra={"action": extra["signing_action"]},
                )
            )
        leftover = leftover.replace(associate_transfer_and_managers.group(0), " ")
    associate_manager_transfer = _FR_ASSOCIATE_MANAGER_TRANSFER.search(leftover)
    if associate_manager_transfer:
        nominal = associate_manager_transfer.group("nominal")
        seller = associate_manager_transfer.group("seller").strip()
        seller_role = associate_manager_transfer.group("seller_role")
        buyer = associate_manager_transfer.group("buyer").strip()
        buyer_role = f"associée, {associate_manager_transfer.group('buyer_role')}"
        signing = _fr_signing(associate_manager_transfer.group("sign"))
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.associate_manager_transfer.v1",
                name=seller,
                role=seller_role,
                extra={
                    "action": "shareholding_changed",
                    "shares_transferred": int(
                        associate_manager_transfer.group("transferred").replace("'", "")
                    ),
                    "previous_shares_count": int(
                        associate_manager_transfer.group("before").replace("'", "")
                    ),
                    "shares_count": int(
                        associate_manager_transfer.group("remaining").replace("'", "")
                    ),
                    "shares_nominal": nominal,
                },
            )
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.associate_manager_transfer.v1",
                name=buyer,
                role=buyer_role,
                signing=signing,
                extra={
                    "action": "shares_received",
                    "shares_count": int(
                        associate_manager_transfer.group("transferred").replace("'", "")
                    ),
                    "shares_nominal": nominal,
                },
            )
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.associate_manager_transfer_signing.v1",
                name=buyer,
                role=associate_manager_transfer.group("buyer_role"),
                signing=signing,
                extra={"action": "kept"},
            )
        )
        leftover = leftover.replace(associate_manager_transfer.group(0), " ")
    shareholders_now = _FR_SHAREHOLDERS_NOW_PAIR.search(leftover)
    if shareholders_now:
        for index in range(1, 3):
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.shareholding_now_pair.v1",
                    name=shareholders_now.group(f"name{index}").strip(),
                    role="associé",
                    extra={
                        "action": "shareholding_changed",
                        "shares_count": int(
                            shareholders_now.group(f"count{index}").replace("'", "")
                        ),
                        "shares_nominal": shareholders_now.group(f"nominal{index}"),
                    },
                )
            )
        leftover = leftover.replace(shareholders_now.group(0), " ")
    former_role_continues = _FR_OFFICER_FORMER_ROLE_CONTINUES.search(leftover)
    if former_role_continues:
        name = former_role_continues.group("name").strip()
        role = former_role_continues.group("role").strip()
        signing = _fr_signing(former_role_continues.group("sign"))
        common = {
            "name": name,
            "role": role,
            "signing": signing,
        }
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.former_role_continues.v1",
                extra={"previous": former_role_continues.group("old_role").strip()},
                **common,
            )
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.former_role_continues_signing.v1",
                extra={"action": "kept"},
                **common,
            )
        )
        leftover = leftover.replace(former_role_continues.group(0), " ")
    board_member_continues = _FR_BOARD_MEMBER_CONTINUES_SIMPLE.search(leftover)
    if board_member_continues:
        name = board_member_continues.group("name").strip()
        office = board_member_continues.group("office")
        role = (
            f"membre et {office.strip()} du conseil d'administration"
            if office
            else "membre du conseil d'administration"
        )
        signing = _fr_signing(board_member_continues.group("sign"))
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.board_member_continues.v1",
                name=name,
                role=role,
                signing=signing,
            )
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.board_member_continues_signing.v1",
                name=name,
                role=role,
                signing=signing,
                extra={"action": "kept"},
            )
        )
        leftover = leftover.replace(board_member_continues.group(0), " ")
    board_roles_pair = _FR_BOARD_ROLES_SIGN_NOW_PAIR.search(leftover)
    if board_roles_pair:
        signing = _fr_signing(board_roles_pair.group("sign"))
        for index in range(1, 3):
            raw_role = board_roles_pair.group(f"role{index}").strip()
            role = (
                "membre du conseil d'administration"
                if raw_role.lower().startswith("membre")
                else raw_role
            )
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.board_roles_signing_now.v1",
                    name=board_roles_pair.group(f"name{index}").strip(),
                    role=role,
                    signing=signing,
                    extra={"action": "modified"},
                )
            )
        leftover = leftover.replace(board_roles_pair.group(0), " ")
    commissioner = _FR_COMPOSITION_COMMISSIONER.search(leftover)
    if commissioner:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.composition_commissioner.v1",
                name=commissioner.group("name").strip(),
                place=commissioner.group("place").strip(),
                role="commissaire au sursis",
                extra={"heimat": commissioner.group("heimat").strip()},
            )
        )
        leftover = leftover.replace(commissioner.group(0), " ")
    grouped_procuration_five = _FR_PROCURATION_FIVE_GROUPED.search(leftover)
    if grouped_procuration_five:
        signing = _fr_signing(f"procuration {grouped_procuration_five.group('kind')}")
        shared = {"with": grouped_procuration_five.group("with").strip()}
        for index in range(1, 6):
            place = grouped_procuration_five.group(f"place{index}").strip()
            heimat = (
                grouped_procuration_five.groupdict().get(f"heimat{index}") or place
            ).strip()
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.procuration_group.v2",
                    name=grouped_procuration_five.group(f"name{index}").strip(),
                    place=place,
                    signing=signing,
                    extra={"heimat": heimat, **shared},
                )
            )
        leftover = leftover.replace(grouped_procuration_five.group(0), " ")
    grouped_procuration = _FR_PROCURATION_FOUR_GROUPED.search(leftover)
    if grouped_procuration:
        signing = _fr_signing(f"procuration {grouped_procuration.group('kind')}")
        shared = {"with": grouped_procuration.group("with").strip()}
        people = (
            (
                grouped_procuration.group("name1").strip(),
                grouped_procuration.group("place1").strip(),
                grouped_procuration.group("place1").strip(),
            ),
            (
                grouped_procuration.group("name2").strip(),
                grouped_procuration.group("place23").strip(),
                grouped_procuration.group("heimat2").strip(),
            ),
            (
                grouped_procuration.group("name3").strip(),
                grouped_procuration.group("place23").strip(),
                grouped_procuration.group("heimat3").strip(),
            ),
            (
                grouped_procuration.group("name4").strip(),
                grouped_procuration.group("place4").strip(),
                grouped_procuration.group("heimat4").strip(),
            ),
        )
        for name, place, heimat in people:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.procuration_group.v1",
                    name=name,
                    place=place,
                    signing=signing,
                    extra={"heimat": heimat, **shared},
                )
            )
        leftover = leftover.replace(grouped_procuration.group(0), " ")
    role_sign_now = _FR_ROLE_SIGN_NOW.search(leftover)
    if role_sign_now:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.signing_now.v3",
                name=role_sign_now.group("name").strip(),
                role=role_sign_now.group("role").strip(),
                signing=_fr_signing(role_sign_now.group("sign")),
                extra={"action": "modified"},
            )
        )
        leftover = leftover.replace(role_sign_now.group(0), " ")
    administrators_sign_now = _FR_ADMINISTRATORS_SIGN_NOW_WITH_FIRST_ROLE.search(
        leftover
    )
    if administrators_sign_now:
        signing = _fr_signing(administrators_sign_now.group("sign"))
        for name, role in (
            (
                administrators_sign_now.group("name1").strip(),
                administrators_sign_now.group("role1").strip(),
            ),
            (administrators_sign_now.group("name2").strip(), "administrateur"),
        ):
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.group_signing_now.v2",
                    name=name,
                    role=role,
                    signing=signing,
                    extra={"action": "modified"},
                )
            )
        leftover = leftover.replace(administrators_sign_now.group(0), " ")
    standalone_org_renamed = _FR_STANDALONE_ORG_RENAMED.search(leftover)
    if standalone_org_renamed:
        extra = {
            "action": "name_changed",
            "previous": standalone_org_renamed.group("old_name").strip(),
        }
        if standalone_org_renamed.group("old_registry"):
            extra["previous_registry_id"] = standalone_org_renamed.group(
                "old_registry"
            )
        previous_uid = (
            standalone_org_renamed.group("assigned_uid")
            or standalone_org_renamed.group("old_uid")
        )
        if previous_uid:
            extra["previous_uid"] = previous_uid
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.organization_renamed.v1",
                name=standalone_org_renamed.group("name").strip(),
                uid=standalone_org_renamed.group("uid"),
                role="organe de révision",
                extra=extra,
            )
        )
        leftover = leftover.replace(standalone_org_renamed.group(0), " ")
    legacy_auditor = _FR_AUDITOR_LEGACY_REASON.search(leftover)
    if legacy_auditor:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.auditor_renamed.v5",
                name=legacy_auditor.group("name").strip(),
                uid=legacy_auditor.group("uid"),
                role="organe de révision",
                extra={
                    "previous": legacy_auditor.group("old").strip(),
                    "previous_registry_id": legacy_auditor.group("old_registry"),
                },
            )
        )
        leftover = leftover.replace(legacy_auditor.group(0), " ")
    associate_transfer_pair = _FR_ASSOCIATE_TRANSFER_PAIR.search(leftover)
    if associate_transfer_pair:
        nominal = associate_transfer_pair.group("nominal")
        for name_group, count_group, sold_group in (
            ("seller1", "seller1_count", "sold1"),
            ("seller2", "seller2_count", "sold2"),
        ):
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.associate_transfer_pair.v1",
                    name=associate_transfer_pair.group(name_group).strip(),
                    role="associé",
                    extra={
                        "action": "shareholding_changed",
                        "shares_transferred": int(
                            associate_transfer_pair.group(sold_group).replace("'", "")
                        ),
                        "shares_count": int(
                            associate_transfer_pair.group(count_group).replace("'", "")
                        ),
                        "shares_nominal": nominal,
                    },
                )
            )
        buyer = associate_transfer_pair.group("buyer").strip()
        buyer_place = associate_transfer_pair.group("place").strip()
        buyer_extra = {
            "action": "shares_received",
            "heimat": associate_transfer_pair.group("heimat").strip(),
            "shares_count": int(
                associate_transfer_pair.group("buyer_count").replace("'", "")
            ),
            "shares_nominal": associate_transfer_pair.group("buyer_nominal"),
        }
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.associate_transfer_pair.v1",
                name=buyer,
                place=buyer_place,
                role="associé, gérant",
                signing=_fr_signing(associate_transfer_pair.group("sign")),
                extra=buyer_extra,
            )
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.associate_transfer_pair_signing.v1",
                name=buyer,
                place=buyer_place,
                role="gérant",
                signing=_fr_signing(associate_transfer_pair.group("sign")),
                extra={"heimat": associate_transfer_pair.group("heimat").strip()},
            )
        )
        leftover = leftover.replace(associate_transfer_pair.group(0), " ")
    associate_transfer = _FR_ASSOCIATE_TRANSFER.search(leftover)
    if associate_transfer:
        shares_count = int(associate_transfer.group("count").replace("'", ""))
        nominal = associate_transfer.group("nominal")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_removed",
                "fr.persons.associate_transfer.v1",
                name=associate_transfer.group("old_name").strip(),
                uid=associate_transfer.group("old_uid"),
                role="associée",
                extra={
                    "action": "shares_transferred",
                    "shares_count": shares_count,
                    "shares_nominal": nominal,
                },
            )
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.associate_transfer.v1",
                name=associate_transfer.group("name").strip(),
                place=associate_transfer.group("place").strip(),
                uid=associate_transfer.group("uid"),
                role="associée",
                extra={
                    "action": "shares_received",
                    "shares_count": int(
                        associate_transfer.group("new_count").replace("'", "")
                    ),
                    "shares_nominal": associate_transfer.group("new_nominal"),
                },
            )
        )
        leftover = leftover.replace(associate_transfer.group(0), " ")
    associate_shares = _FR_ASSOCIATE_SHARES_NOW.search(leftover)
    if associate_shares:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.associate_shares.v1",
                name=associate_shares.group("name").strip(),
                role=associate_shares.group("role").lower(),
                extra={
                    "action": "shareholding_changed",
                    "shares_count": int(
                        associate_shares.group("count").replace("'", "")
                    ),
                    "shares_nominal": associate_shares.group("nominal"),
                },
            )
        )
        leftover = leftover.replace(associate_shares.group(0), " ")
    liquidator_name = _FR_LIQUIDATOR_NAME.search(leftover)
    if liquidator_name:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.liquidator_name.v1",
                name=liquidator_name.group("name").strip(),
                uid=liquidator_name.group("uid"),
                role="liquidatrice",
                extra={"action": "name_changed"},
            )
        )
        leftover = leftover.replace(liquidator_name.group(0), " ")
    new_manager = _FR_NEW_MANAGER.search(leftover)
    if new_manager:
        place = (new_manager.group("place_same") or new_manager.group("place")).strip()
        role = new_manager.group("role_m") or new_manager.group("role_f")
        if new_manager.group("office"):
            role += f" et {new_manager.group('office').strip()}"
        signing = _fr_signing(new_manager.group("sign"))
        extra = {}
        if new_manager.group("heimat"):
            extra["heimat"] = new_manager.group("heimat").strip()
        else:
            extra["heimat"] = place
        if new_manager.group("country"):
            extra["country"] = new_manager.group("country")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.new_manager.v1",
                name=new_manager.group("name").strip(),
                place=place,
                role=role,
                signing=signing,
                extra=extra,
            )
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.new_manager_signing.v1",
                name=new_manager.group("name").strip(),
                place=place,
                role=role,
                signing=signing,
            )
        )
        leftover = leftover.replace(new_manager.group(0), " ")
    for elected in list(_FR_ELECTED_OFFICER.finditer(leftover)):
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.officer_elected.v1",
                name=elected.group("name").strip(),
                role=elected.group("role").strip(),
                extra={"previous": elected.group("previous").strip()},
            )
        )
        leftover = leftover.replace(elected.group(0), " ")
    for appointed in list(_FR_APPOINTED_OFFICER_SIMPLE.finditer(leftover)):
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.officer_appointed.v1",
                name=appointed.group("name").strip(),
                role=appointed.group("role").strip(),
            )
        )
        leftover = leftover.replace(appointed.group(0), " ")
    associate_transformed = _FR_ASSOCIATE_TRANSFORMED.search(leftover)
    if associate_transformed:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.associate_transformed.v1",
                name=associate_transformed.group("name").strip(),
                uid=associate_transformed.group("uid"),
                role="associée",
                extra={
                    "action": "name_changed",
                    "reason": "transformation",
                    "previous": associate_transformed.group("old_name").strip(),
                    "previous_uid": associate_transformed.group("old_uid"),
                },
            )
        )
        leftover = leftover.replace(associate_transformed.group(0), " ")
    associate_renamed = _FR_ASSOCIATE_RENAMED.search(leftover)
    if associate_renamed:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.associate_renamed.v1",
                name=associate_renamed.group("name").strip(),
                uid=associate_renamed.group("uid"),
                role="associée",
                extra={
                    "action": "name_changed",
                    "previous": associate_renamed.group("old_name").strip(),
                },
            )
        )
        leftover = leftover.replace(associate_renamed.group(0), " ")
    branch_signature = _FR_BRANCH_SIGNATURE_WITH_PROCURATION_REVOKED.search(leftover)
    if branch_signature:
        signing = _fr_signing(f"signature {branch_signature.group('kind')}")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.branch_signing_granted.v1",
                name=branch_signature.group("name").strip(),
                signing=signing,
                extra={
                    "scope": "branch",
                    "previous_signing": "procuration",
                    "procuration_revoked": True,
                },
            )
        )
        leftover = leftover.replace(branch_signature.group(0), " ")
    member_continues = _FR_MEMBER_CONTINUES_SIGNING.search(leftover)
    if member_continues:
        name = member_continues.group("name").strip()
        role = member_continues.group("role").strip()
        signing = _fr_signing(member_continues.group("sign"))
        extra = {"previous": member_continues.group("old_role").strip()}
        if member_continues.group("with"):
            extra["with"] = member_continues.group("with").strip()
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.member_continues.v1",
                name=name,
                role=role,
                signing=signing,
                extra=extra,
            )
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.member_continues_signing.v1",
                name=name,
                role=role,
                signing=signing,
                extra={"with": extra["with"]} if "with" in extra else None,
            )
        )
        leftover = leftover.replace(member_continues.group(0), " ")
    board_pair = _FR_BOARD_MEMBERS_PAIR.search(leftover)
    if board_pair:
        signing = _fr_signing(board_pair.group("sign"))
        shared = {}
        if board_pair.group("with"):
            shared["with"] = board_pair.group("with").strip()
        for name_group, heimat_group, place_group, delegated in (
            ("name1", "heimat1", "place1", False),
            ("name2", "heimat2", "place2", bool(board_pair.group("role2"))),
        ):
            name = board_pair.group(name_group).strip()
            place = board_pair.group(place_group).strip()
            role = "membre du conseil d'administration"
            if delegated:
                role += " et délégué"
            extra = {"heimat": board_pair.group(heimat_group).strip(), **shared}
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.board_members_pair.v1",
                    name=name,
                    place=place,
                    role=role,
                    signing=signing,
                    extra=extra,
                )
            )
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.board_members_pair_signing.v1",
                    name=name,
                    place=place,
                    role=role,
                    signing=signing,
                    extra=shared or None,
                )
            )
        leftover = leftover.replace(board_pair.group(0), " ")
    foundation_member = (
        _FR_NEW_FOUNDATION_MEMBER.search(leftover)
        or _FR_NEW_FOUNDATION_MEMBER_POSTFIX.search(leftover)
    )
    if foundation_member:
        name = foundation_member.group("name").strip()
        place = foundation_member.group("place").strip()
        role = "membre du conseil de fondation"
        signing = _fr_signing(foundation_member.group("sign"))
        extra = {"heimat": foundation_member.group("heimat").strip()}
        if foundation_member.groupdict().get("with"):
            extra["with"] = foundation_member.group("with").strip()
        if foundation_member.groupdict().get("not_with"):
            extra["not_with"] = foundation_member.group("not_with").strip()
        for event_type, rule_id in (
            ("officer_changed", "fr.persons.foundation_member.v1"),
            ("signing_authority_changed", "fr.persons.foundation_member_signing.v1"),
        ):
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    event_type,
                    rule_id,
                    name=name,
                    place=place,
                    role=role,
                    signing=signing,
                    extra=extra,
                )
            )
        leftover = leftover.replace(foundation_member.group(0), " ")
    removed_members = _FR_REMOVED_MEMBERS_AND_POWERS.search(leftover)
    if removed_members:
        member_names = [removed_members.group("name1"), removed_members.group("name2")]
        for name in member_names:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_removed",
                    "fr.persons.board_members_removed.v1",
                    name=name.strip(),
                    role="membre du conseil d'administration",
                )
            )
        for name in (*member_names, removed_members.group("name3")):
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.powers_revoked_group.v1",
                    name=name.strip(),
                    extra={"action": "revoked"},
                )
            )
        leftover = leftover.replace(removed_members.group(0), " ")
    sign_now_with_role = _FR_SIGN_NOW_WITH_ROLE.search(leftover)
    if sign_now_with_role:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.signing_now.v2",
                name=sign_now_with_role.group("name").strip(),
                role=sign_now_with_role.group("role").strip(),
                signing=_fr_signing(sign_now_with_role.group("sign")),
            )
        )
        leftover = leftover.replace(sign_now_with_role.group(0), " ")
    administration_directors = _FR_ADMINISTRATION_DIRECTOR_PAIR.search(leftover)
    if administration_directors:
        signing = _fr_signing(administration_directors.group("sign"))
        additional_role = administration_directors.group("additional_role").strip()
        for suffix in ("1", "2"):
            name = administration_directors.group(f"name{suffix}").strip()
            place = administration_directors.group(f"place{suffix}").strip()
            role = f"{administration_directors.group(f'role{suffix}').strip()} et {additional_role}"
            extra = {"heimat": administration_directors.group(f"heimat{suffix}").strip()}
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.administration_directors.v1",
                    name=name,
                    place=place,
                    role=role,
                    signing=signing,
                    extra=extra,
                )
            )
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.administration_directors_signing.v1",
                    name=name,
                    place=place,
                    role=role,
                    signing=signing,
                )
            )
        leftover = leftover.replace(administration_directors.group(0), " ")
    administration_continues = _FR_ADMINISTRATION_CONTINUES_PAIR.search(leftover)
    if administration_continues:
        signing = _fr_signing(administration_continues.group("sign"))
        people = (
            (
                administration_continues.group("name1").strip(),
                administration_continues.group("role1").strip(),
                "role_changed",
            ),
            (
                administration_continues.group("name2").strip(),
                administration_continues.group("role2").strip(),
                "role_and_signing_kept",
            ),
        )
        for name, role, action in people:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.administration_continues.v1",
                    name=name,
                    role=role,
                    signing=signing,
                    extra={"action": action},
                )
            )
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.administration_continues_signing.v1",
                    name=name,
                    role=role,
                    signing=signing,
                    extra={"action": "kept"},
                )
            )
        leftover = leftover.replace(administration_continues.group(0), " ")
    representatives_removed = (
        _FR_HEAD_OFFICE_REPRESENTATIVES_REMOVED.search(leftover)
        or _FR_HEAD_OFFICE_REPRESENTATIVES_REMOVED_RIGHT_CHANGE.search(leftover)
    )
    if representatives_removed:
        for raw_name in re.split(
            r",\s*|\s+et\s+", representatives_removed.group("names")
        ):
            name = re.sub(r"\s+", " ", raw_name).strip()
            if not name:
                continue
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_removed",
                    "fr.persons.head_office_representative_removed.v1",
                    name=name,
                    role="personne disposant d'un pouvoir de représentation",
                    extra={"action": "functions_and_signatures_removed"},
                )
            )
        leftover = leftover.replace(representatives_removed.group(0), " ")
    civil_name_origin = _FR_CIVIL_NAME_ORIGIN_DOMICILE.search(leftover)
    if civil_name_origin:
        place = civil_name_origin.group("place").strip()
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.civil_name_origin_domicile.v1",
                name=civil_name_origin.group("name").strip(),
                place=place,
                extra={
                    "action": "name_origin_and_domicile_changed",
                    "previous": civil_name_origin.group("old_name").strip(),
                    "heimat": place,
                },
            )
        )
        leftover = leftover.replace(civil_name_origin.group(0), " ")
    civil_name_origin_only = _FR_CIVIL_NAME_ORIGIN.search(leftover)
    if civil_name_origin_only:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.civil_name_origin.v1",
                name=civil_name_origin_only.group("name").strip(),
                role=civil_name_origin_only.group("role"),
                extra={
                    "action": "name_and_origin_changed",
                    "previous": civil_name_origin_only.group("old_name").strip(),
                    "heimat": civil_name_origin_only.group("heimat").strip(),
                },
            )
        )
        leftover = leftover.replace(civil_name_origin_only.group(0), " ")
    first_name_and_domicile = _FR_FIRST_NAME_AND_DOMICILE.search(leftover)
    if first_name_and_domicile:
        surname = first_name_and_domicile.group("surname").strip()
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.first_name_domicile.v1",
                name=f"{surname} {first_name_and_domicile.group('first').strip()}",
                place=first_name_and_domicile.group("place").strip(),
                extra={
                    "action": "first_name_and_domicile_changed",
                    "previous": f"{surname} {first_name_and_domicile.group('old_first').strip()}",
                },
            )
        )
        leftover = leftover.replace(first_name_and_domicile.group(0), " ")
    auditor_seat_now = _FR_AUDITOR_SEAT_NOW.search(leftover)
    if auditor_seat_now:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.auditor_moved.v1",
                name=auditor_seat_now.group("name").strip(),
                place=auditor_seat_now.group("place").strip(),
                uid=auditor_seat_now.group("uid"),
                role="organe de révision",
                extra={"action": "seat_changed"},
            )
        )
        leftover = leftover.replace(auditor_seat_now.group(0), " ")
    named_role_pair = _FR_ADMINISTRATION_NAMED_ROLE_PAIR.search(leftover)
    if named_role_pair:
        signing = _fr_signing(named_role_pair.group("sign"))
        for name, place, role, extra in (
            (
                named_role_pair.group("name1").strip(),
                None,
                named_role_pair.group("role1").strip(),
                {"action": "role_changed"},
            ),
            (
                named_role_pair.group("name2").strip(),
                named_role_pair.group("place2").strip(),
                named_role_pair.group("role2").strip(),
                {"heimat": named_role_pair.group("place2").strip()},
            ),
        ):
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.administration_pair.v2",
                    name=name,
                    place=place,
                    role=role,
                    signing=signing,
                    extra=extra,
                )
            )
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.administration_pair_signing.v2",
                    name=name,
                    place=place,
                    role=role,
                    signing=signing,
                )
            )
        leftover = leftover.replace(named_role_pair.group(0), " ")
    for administration in (
        _FR_ADMINISTRATION_FIRST_DOMICILE_PAIR.search(leftover),
        _FR_ADMINISTRATION_NAMED_PAIR.search(leftover),
        _FR_ADMINISTRATION_DOMICILE_PAIR.search(leftover),
        _FR_ADMINISTRATION_SIGN_PAIR.search(leftover),
    ):
        if not administration:
            continue
        signing = _fr_signing(administration.group("sign"))
        name1 = re.sub(r"\s+", " ", administration.group("name1")).strip()
        name2 = re.sub(r"\s+", " ", administration.group("name2")).strip()
        role1 = administration.group("role1").strip()
        place1 = (administration.groupdict().get("place1") or "").strip() or None
        place2 = administration.group("place2").strip()
        second_extra = {"action": "domicile_changed"}
        if administration.groupdict().get("heimat2"):
            second_extra = {"heimat": administration.group("heimat2").strip()}
        first_extra = None
        if place1:
            first_extra = {"action": "domicile_changed"}
        elif administration.groupdict().get("changed"):
            first_extra = {"signing_modified": True}
        for name, place, role, extra in (
            (name1, place1, role1, first_extra),
            (name2, place2, "administrateur", second_extra),
        ):
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.administration_pair.v1",
                    name=name,
                    place=place,
                    role=role,
                    signing=signing,
                    extra=extra,
                )
            )
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.administration_pair_signing.v1",
                    name=name,
                    place=place,
                    role=role,
                    signing=signing,
                )
            )
        leftover = leftover.replace(administration.group(0), " ")
        break
    is_officer = (
        _FR_IS_OFFICER.search(leftover)
        or _FR_IS_OFFICER_SAME_PLACE.search(leftover)
        or _FR_IS_OFFICER_BARE_ORIGIN.search(leftover)
    )
    if is_officer:
        name = re.sub(r"\s+", " ", is_officer.group("name")).strip()
        place = is_officer.group("place").strip()
        role = is_officer.group("role").strip()
        signing = _fr_signing(is_officer.group("sign"))
        heimat = is_officer.groupdict().get("heimat") or place
        extra = {"heimat": heimat.strip()}
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.is_officer.v1",
                name=name,
                place=place,
                role=role,
                signing=signing,
                extra=extra,
            )
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.is_officer_signing.v1",
                name=name,
                place=place,
                role=role,
                signing=signing,
            )
        )
        leftover = leftover.replace(is_officer.group(0), " ")
    mixed_three = _FR_SIGNATURE_GRANTED_THREE_MIXED.search(leftover)
    if mixed_three:
        signing = _fr_signing(f"signature {mixed_three.group('kind')}")
        shared = {"with": mixed_three.group("with").strip()}
        for name_group, place_group, heimat in (
            ("name1", "place1", mixed_three.group("heimat12")),
            ("name2", "place2", mixed_three.group("heimat12")),
            ("name3", "place3", mixed_three.group("heimat3")),
        ):
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.sign_granted_group.v2",
                    name=mixed_three.group(name_group).strip(),
                    place=mixed_three.group(place_group).strip(),
                    signing=signing,
                    extra={"heimat": heimat.strip(), **shared},
                )
            )
        leftover = leftover.replace(mixed_three.group(0), " ")
    three = _FR_CONFEREE_THREE.search(leftover)
    if three:
        signing = _fr_signing(f"signature {three.group('kind')}")
        for name_group, heimat_group, place_group, role_group in (
            ("name1", "heimat1", "place12", "role12"),
            ("name2", "heimat2", "place12", "role12"),
            ("name3", "heimat3", "place3", "role3"),
        ):
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.sign_granted_group.v1",
                    name=three.group(name_group).strip(),
                    place=three.group(place_group).strip(),
                    role=three.group(role_group).strip(),
                    signing=signing,
                    extra={"heimat": three.group(heimat_group).strip()},
                )
            )
        leftover = leftover.replace(three.group(0), " ")
    shared_three = _FR_CONFEREE_THREE_SHARED_ORIGIN.search(leftover)
    if shared_three:
        signing = _fr_signing(f"signature {shared_three.group('kind')}")
        for name_group in ("name1", "name2", "name3"):
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.sign_granted_group.v3",
                    name=shared_three.group(name_group).strip(),
                    place=shared_three.group("place").strip(),
                    signing=signing,
                    extra={"heimat": shared_three.group("heimat").strip()},
                )
            )
        leftover = leftover.replace(shared_three.group(0), " ")
    simple_group = _FR_GROUP_SIGN_NOW_SIMPLE.search(leftover)
    if simple_group:
        signing = _fr_signing(simple_group.group("sign"))
        role = simple_group.group("role").strip()
        for name_group in ("name1", "name2"):
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.group_signing_now.v2",
                    name=simple_group.group(name_group).strip(),
                    role=role,
                    signing=signing,
                )
            )
        leftover = leftover.replace(simple_group.group(0), " ")
    pair_sign_now = _FR_PAIR_SIGN_NOW.search(leftover)
    if pair_sign_now:
        signing = _fr_signing(pair_sign_now.group("sign"))
        for name_group in ("name1", "name2"):
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.pair_signing_now.v1",
                    name=pair_sign_now.group(name_group).strip(),
                    signing=signing,
                    extra={"action": "modified"},
                )
            )
        leftover = leftover.replace(pair_sign_now.group(0), " ")
    civil_with_domicile = _FR_CIVIL_NAME_AND_DOMICILE.search(leftover)
    if civil_with_domicile:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.civil_name_domicile.v1",
                name=civil_with_domicile.group("name").strip(),
                place=civil_with_domicile.group("place").strip(),
                extra={
                    "action": "name_and_domicile_changed",
                    "previous": civil_with_domicile.group("old_name").strip(),
                },
            )
        )
        leftover = leftover.replace(civil_with_domicile.group(0), " ")
    associate_uid = _FR_ASSOCIATE_UPDATED_UID.search(leftover)
    if associate_uid:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.associate_updated.v2",
                name=associate_uid.group("name").strip(),
                place=associate_uid.group("place").strip(),
                uid=associate_uid.group("uid"),
                role="associée",
                extra={
                    "action": "name_and_seat_changed",
                    "previous": associate_uid.group("old_name").strip(),
                    "previous_uid": associate_uid.group("old_uid"),
                },
            )
        )
        leftover = leftover.replace(associate_uid.group(0), " ")
    associate = _FR_ASSOCIATE_UPDATED.search(leftover)
    if associate:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.associate_updated.v1",
                name=associate.group("name").strip(),
                place=associate.group("place").strip(),
                uid=associate.group("uid"),
                role="associée",
                extra={
                    "action": "name_and_seat_changed",
                    "previous": associate.group("old_name").strip(),
                    "previous_registry_id": associate.group("registry_id"),
                },
            )
        )
        leftover = leftover.replace(associate.group(0), " ")
    general_partner = _FR_NEW_GENERAL_PARTNER.search(leftover)
    if general_partner:
        name = general_partner.group("name").strip()
        place = general_partner.group("place").strip()
        role = "associé indéfiniment responsable"
        signing = _fr_signing(general_partner.group("sign"))
        extra = {"heimat": general_partner.group("heimat").strip()}
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.general_partner.v1",
                name=name,
                place=place,
                role=role,
                signing=signing,
                extra=extra,
            )
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.general_partner_signing.v1",
                name=name,
                place=place,
                role=role,
                signing=signing,
            )
        )
        leftover = leftover.replace(general_partner.group(0), " ")
    associate_signing_revoked = _FR_ASSOCIATE_SIGNING_REVOKED.search(leftover)
    if associate_signing_revoked:
        name = associate_signing_revoked.group("name").strip()
        previous_role = associate_signing_revoked.group("old_role").strip()
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.associate_role_changed.v1",
                name=name,
                role="associé",
                extra={"previous": previous_role},
            )
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.associate_signing_revoked.v1",
                name=name,
                extra={"action": "revoked", "previous_role": previous_role},
            )
        )
        leftover = leftover.replace(associate_signing_revoked.group(0), " ")
    roles_changed_pair = _FR_ROLES_CHANGED_PAIR.search(leftover)
    if roles_changed_pair:
        signing = _fr_signing(roles_changed_pair.group("sign"))
        previous_role_raw = roles_changed_pair.group("old_role").strip().lower()
        role_raw = roles_changed_pair.group("role").strip().lower()
        previous_role = {
            "directeurs": "directeur",
            "directrices": "directrice",
        }.get(previous_role_raw, previous_role_raw)
        role = {
            "administrateurs": "administrateur",
            "administratrices": "administratrice",
        }.get(role_raw, role_raw)
        for name_group in ("name1", "name2"):
            name = roles_changed_pair.group(name_group).strip()
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.roles_changed_pair.v1",
                    name=name,
                    role=role,
                    signing=signing,
                    extra={"previous": previous_role},
                )
            )
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.roles_changed_pair_signing.v1",
                    name=name,
                    role=role,
                    signing=signing,
                    extra={"action": "kept"},
                )
            )
        leftover = leftover.replace(roles_changed_pair.group(0), " ")
    continues = _FR_OFFICER_CONTINUES.search(leftover)
    if continues:
        name = re.sub(r"\s+", " ", continues.group("name")).strip()
        signing = _fr_signing(continues.group("sign"))
        role = continues.group("role").strip()
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.officer_continues.v1",
                name=name,
                role=role,
                signing=signing,
                extra={"previous": continues.group("old_role")},
            )
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.officer_continues_signing.v1",
                name=name,
                role=role,
                signing=signing,
            )
        )
        leftover = leftover.replace(continues.group(0), " ")
    remains_sole = _FR_OFFICER_REMAINS_SOLE.search(leftover)
    if remains_sole:
        name = re.sub(r"\s+", " ", remains_sole.group("name")).strip()
        role = remains_sole.group("role").strip()
        signing = _fr_signing(remains_sole.group("sign"))
        extra = {
            "action": "role_changed_signing_kept",
            "previous": remains_sole.group("old_role").strip(),
        }
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.officer_remains_sole.v1",
                name=name,
                role=role,
                signing=signing,
                extra=extra,
            )
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.officer_remains_sole_signing.v1",
                name=name,
                role=role,
                signing=signing,
                extra={"action": "kept"},
            )
        )
        leftover = leftover.replace(remains_sole.group(0), " ")
    role_continues = _FR_ROLE_CONTINUES_SIGNING.search(leftover)
    if role_continues:
        name = re.sub(r"\s+", " ", role_continues.group("name")).strip()
        role = role_continues.group("role").strip()
        signing = _fr_signing(role_continues.group("sign"))
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.role_continues.v1",
                name=name,
                role=role,
                signing=signing,
                extra={"action": "role_and_signing_kept"},
            )
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.role_continues_signing.v1",
                name=name,
                role=role,
                signing=signing,
                extra={"action": "kept"},
            )
        )
        leftover = leftover.replace(role_continues.group(0), " ")
    board_members_continue = _FR_BOARD_MEMBERS_CONTINUE_SIGNING.search(leftover)
    if board_members_continue:
        signing = _fr_signing(board_members_continue.group("sign"))
        people = (
            (
                board_members_continue.group("name1").strip(),
                board_members_continue.group("role1").strip(),
                "membre du conseil",
            ),
            (
                board_members_continue.group("name2").strip(),
                "membre du conseil",
                board_members_continue.group("previous_role2").strip(),
            ),
        )
        for name, role, previous_role in people:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.board_members_continue.v1",
                    name=name,
                    role=role,
                    signing=signing,
                    extra={"previous": previous_role},
                )
            )
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.board_members_continue_signing.v1",
                    name=name,
                    role=role,
                    signing=signing,
                    extra={"action": "kept"},
                )
            )
        leftover = leftover.replace(board_members_continue.group(0), " ")
    administrators_roles_changed = _FR_ADMINISTRATORS_ROLES_CHANGED_PAIR.search(
        leftover
    )
    if administrators_roles_changed:
        signing = _fr_signing(administrators_roles_changed.group("sign"))
        for index in range(1, 3):
            name = administrators_roles_changed.group(f"name{index}").strip()
            role = administrators_roles_changed.group(f"role{index}").strip()
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.administrators_roles_changed.v1",
                    name=name,
                    role=role,
                    signing=signing,
                    extra={
                        "action": "role_changed",
                        "previous": administrators_roles_changed.group(
                            f"old_role{index}"
                        ).strip(),
                    },
                )
            )
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.administrators_roles_changed_signing.v1",
                    name=name,
                    role=role,
                    signing=signing,
                    extra={"action": "kept"},
                )
            )
        leftover = leftover.replace(administrators_roles_changed.group(0), " ")
    administrators_continue = _FR_ADMINISTRATORS_CONTINUE_SIGNING.search(leftover)
    if administrators_continue:
        signing = _fr_signing(administrators_continue.group("sign"))
        people = (
            (
                administrators_continue.group("name1").strip(),
                administrators_continue.group("role1").strip(),
                "administrateur",
            ),
            (
                administrators_continue.group("name2").strip(),
                "administrateur",
                administrators_continue.group("previous_role2").strip(),
            ),
        )
        for name, role, previous_role in people:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.administrators_continue.v1",
                    name=name,
                    role=role,
                    signing=signing,
                    extra={"previous": previous_role},
                )
            )
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.administrators_continue_signing.v1",
                    name=name,
                    role=role,
                    signing=signing,
                    extra={"action": "kept"},
                )
            )
        leftover = leftover.replace(administrators_continue.group(0), " ")
    named_continues = _FR_NAMED_OFFICER_CONTINUES.search(leftover)
    if named_continues:
        name = re.sub(r"\s+", " ", named_continues.group("name")).strip()
        signing = _fr_signing(named_continues.group("sign"))
        role = named_continues.group("role").strip()
        previous = (named_continues.group("old_role") or "").strip()
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.named_officer_continues.v1",
                name=name,
                role=role,
                signing=signing,
                extra={"previous": previous} if previous else None,
            )
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.named_officer_continues_signing.v1",
                name=name,
                role=role,
                signing=signing,
            )
        )
        leftover = leftover.replace(named_continues.group(0), " ")
    two_places = _FR_CONFEREE_TWO_PLACES.search(leftover)
    if two_places:
        signing = _fr_signing(f"signature {two_places.group('kind')}")
        role = (two_places.group("role") or "").strip() or None
        heimat = two_places.group("heimat").strip()
        for name_group, place_group in (("name1", "place1"), ("name2", "place2")):
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.sign_granted.v2",
                    name=two_places.group(name_group).strip(),
                    place=two_places.group(place_group).strip(),
                    role=role,
                    signing=signing,
                    extra={"heimat": heimat},
                )
            )
        leftover = leftover.replace(two_places.group(0), " ")
    distinct_places = _FR_CONFEREE_TWO_DISTINCT_PLACES.search(leftover)
    if distinct_places:
        signing = _fr_signing(f"signature {distinct_places.group('kind')}")
        role = distinct_places.group("role").strip()
        shared = {}
        if distinct_places.group("with"):
            shared["with"] = distinct_places.group("with").strip()
        for name_group, heimat_group, place_group in (
            ("name1", "heimat1", "place1"),
            ("name2", "heimat2", "place2"),
        ):
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.sign_granted_distinct_places.v1",
                    name=distinct_places.group(name_group).strip(),
                    place=distinct_places.group(place_group).strip(),
                    role=role,
                    signing=signing,
                    extra={"heimat": distinct_places.group(heimat_group).strip(), **shared},
                )
            )
        leftover = leftover.replace(distinct_places.group(0), " ")
    n_est = _FR_N_EST_PLUS.search(leftover)
    if n_est:
        name = re.sub(r"\s+", " ", n_est.group("name")).strip()
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.role_off.v1",
                name=name,
                role=n_est.group("role_off").strip(),
                extra={"action": "role_removed"},
            )
        )
    if n_est:
        leftover = leftover.replace(n_est.group(0), " ")
    ne_sont = _FR_NE_SONT_PLUS.search(leftover)
    if ne_sont:
        role_off = ne_sont.group("role_off").strip()
        for raw_name in re.split(r"\s+et\s+", ne_sont.group("names")):
            name = re.sub(r"\s+", " ", raw_name).strip()
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.role_off_plural.v1",
                    name=name,
                    role=role_off,
                    extra={"action": "role_removed"},
                )
            )
        leftover = leftover.replace(ne_sont.group(0), " ")
        revoked = re.search(r"leur(?:s)? (?:signature est radiée|pouvoirs sont radiés)", leftover, re.I)
        if revoked:
            leftover = leftover.replace(revoked.group(0), " ")
    reste = _FR_RESTE.search(leftover)
    if reste:
        name = re.sub(r"\s+", " ", reste.group("name")).strip()
        role_on = reste.group("role_on").strip().rstrip(".")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.role_kept.v1",
                name=name,
                role=role_on,
                extra={"action": "role_kept", "previous": reste.group("role_old").strip()},
            )
        )
        if reste.group("sign"):
            signing = (
                "Einzelunterschrift"
                if "individuel" in reste.group("sign").lower()
                else "Kollektivunterschrift zu zweien"
            )
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.signing.v1",
                    name=name,
                    signing=signing,
                )
            )
        leftover = leftover.replace(reste.group(0), " ")
    nouveaux = _FR_NOUVEAUX.search(leftover)
    if nouveaux:
        kind = (nouveaux.group("kind") or "").lower()
        signing = "Einzelunterschrift" if "individuelle" in kind else "Kollektivunterschrift zu zweien"
        body = nouveaux.group("body")
        events_before = len(events)
        for chunk in re.split(r",\s+et\s+", body):
            one = _FR_NOUVEAU_ONE.search(chunk.strip())
            if not one:
                continue
            name = re.sub(r"\s+", " ", one.group("name")).strip()
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.nouveaux.v1",
                    name=name,
                    place=one.group("place").strip(),
                    role="administrateur",
                    signing=signing,
                    extra={"heimat": one.group("heimat").strip()},
                )
            )
        if len(events) == events_before:
            origin_match = re.search(r",\s*les\s+\w+\s+d'(?P<heimat>[^,]+)$", body, re.I)
            heimat = origin_match.group("heimat").strip() if origin_match else None
            grouped_body = body[: origin_match.start()] if origin_match else body
            cursor = 0
            grouped_people: list[tuple[str, str, str | None]] = []
            for place_match in _FR_GROUPED_PLACE.finditer(grouped_body):
                names_part = grouped_body[cursor : place_match.start()].strip(" ,")
                place = place_match.group("place").strip()
                for name_match in _FR_GROUPED_NAME.finditer(names_part):
                    name = name_match.group("name").strip()
                    role = "secrétaire" if re.search(
                        re.escape(name) + r",\s*secrétaire", names_part, re.I
                    ) else None
                    grouped_people.append((name, place, role))
                cursor = place_match.end()
            tail = grouped_body[cursor:].strip(" ,")
            last = _FR_GROUPED_LAST.search(tail)
            if last:
                grouped_people.append(
                    (last.group("name").strip(), last.group("place").strip(), None)
                )
            seen: set[str] = set()
            for name, place, role in grouped_people:
                if name in seen:
                    continue
                seen.add(name)
                extra = {"heimat": heimat} if heimat else None
                events.append(
                    _event(
                        publication_id,
                        published_at,
                        org_uid,
                        plz,
                        canton,
                        "officer_changed",
                        "fr.persons.nouveaux_grouped.v1",
                        name=name,
                        place=place,
                        role=role or "administrateur",
                        signing=signing,
                        extra=extra,
                    )
                )
        # A title abbreviation such as "Dr." can terminate the generic body
        # match before any complete person was parsed.  Preserve that text for
        # a bounded leftover rule instead of silently discarding it.
        if len(events) > events_before or not re.search(r"\bDr$", body, re.I):
            leftover = leftover.replace(nouveaux.group(0), " ")
    for member_pattern in (_FR_NEW_BOARD_MEMBER, _FR_NEW_ADMINISTRATOR, _FR_BOARD_MEMBER):
        for member in list(member_pattern.finditer(leftover)):
            place = (member.group("place_same") or member.group("place") or "").strip()
            signing = _fr_signing(member.group("sign"))
            office = member.groupdict().get("office")
            if member_pattern is _FR_NEW_ADMINISTRATOR:
                role = "administrateur"
            else:
                board = member.groupdict().get("board") or "conseil d'administration"
                role = f"membre et {office} du {board}" if office else f"membre du {board}"
            extra = {}
            if member.group("heimat"):
                extra["heimat"] = member.group("heimat").strip()
            elif member.group("place_same"):
                extra["heimat"] = place
            name = re.sub(r"\s+", " ", member.group("name")).strip()
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.board_member.v1",
                    name=name,
                    place=place or None,
                    role=role,
                    signing=signing,
                    extra=extra or None,
                )
            )
            if signing:
                events.append(
                    _event(
                        publication_id,
                        published_at,
                        org_uid,
                        plz,
                        canton,
                        "signing_authority_changed",
                        "fr.persons.board_member_signing.v1",
                        name=name,
                        place=place or None,
                        role=role,
                        signing=signing,
                    )
                )
            leftover = leftover.replace(member.group(0), " ")
    for named in list(_FR_NAMED_OFFICER.finditer(leftover)):
        place = (named.group("place_same") or named.group("place") or "").strip()
        signing = _fr_signing(named.group("sign"))
        extra = {}
        if named.group("heimat"):
            extra["heimat"] = named.group("heimat").strip()
        elif named.group("place_same"):
            extra["heimat"] = place
        name = re.sub(r"\s+", " ", named.group("name")).strip()
        role = named.group("role").strip()
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.named_officer.v1",
                name=name,
                place=place or None,
                role=role,
                signing=signing,
                extra=extra or None,
            )
        )
        if signing:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.named_officer_signing.v1",
                    name=name,
                    place=place or None,
                    role=role,
                    signing=signing,
                )
            )
            leftover = leftover.replace(named.group(0), " ")
    appointed = _FR_APPOINTED_SIGNING_PROCURATION_REVOKED.search(leftover)
    if appointed:
        name = re.sub(r"\s+", " ", appointed.group("name")).strip()
        role = appointed.group("role").strip()
        signing = _fr_signing(appointed.group("sign"))
        extra = {"previous_signing": "procuration", "procuration_revoked": True}
        if appointed.group("with"):
            extra["with"] = appointed.group("with").strip()
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.appointed_signing.v1",
                name=name,
                role=role,
                signing=signing,
                extra=extra,
            )
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.appointed_signing.v1",
                name=name,
                role=role,
                signing=signing,
                extra=extra,
            )
        )
        leftover = leftover.replace(appointed.group(0), " ")
    for group_sign in list(_FR_GROUP_SIGN_NOW.finditer(leftover)):
        signing = _fr_signing(group_sign.group("sign"))
        previous_signing = _fr_signing(group_sign.group("previous"))
        role = group_sign.group("role").strip()
        for raw_name in re.split(r",\s*|\s+et\s+", group_sign.group("names")):
            name = re.sub(r"\s+", " ", raw_name).strip()
            if not name:
                continue
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.group_signing_now.v1",
                    name=name,
                    role=role,
                    signing=signing,
                    extra={"previous_signing": previous_signing},
                )
            )
        leftover = leftover.replace(group_sign.group(0), " ")
    for sign_now in list(_FR_SIGN_NOW.finditer(leftover)):
        name = re.sub(r"\s+", " ", sign_now.group("name")).strip()
        signing = _fr_signing(sign_now.group("sign"))
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.signing_now.v1",
                name=name,
                signing=signing,
            )
        )
        leftover = leftover.replace(sign_now.group(0), " ")
    civil_name = _FR_CIVIL_NAME.search(leftover)
    if civil_name:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.civil_name.v1",
                name=civil_name.group("name").strip(),
                extra={
                    "action": "name_changed",
                    "previous": civil_name.group("old_name").strip(),
                },
            )
        )
        leftover = leftover.replace(civil_name.group(0), " ")
    civil_name_simple = _FR_CIVIL_NAME_SIMPLE.search(leftover)
    if civil_name_simple:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.civil_name.v2",
                name=civil_name_simple.group("name").strip(),
                extra={
                    "action": "name_changed",
                    "previous": civil_name_simple.group("old_name").strip(),
                },
            )
        )
        leftover = leftover.replace(civil_name_simple.group(0), " ")
    demeure = _FR_DEMEURE.search(leftover)
    if demeure and n_est:
        name = re.sub(r"\s+", " ", n_est.group("name")).strip()
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.role_on.v1",
                name=name,
                role=demeure.group("role_on").strip(),
                extra={"action": "role_kept"},
            )
        )
    sign = _FR_SIGN.search(leftover)
    if sign and n_est:
        name = re.sub(r"\s+", " ", n_est.group("name")).strip()
        signing = "Einzelunterschrift" if "individuel" in sign.group("sign").lower() else sign.group("sign")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.signing.v1",
                name=name,
                signing=signing,
            )
        )
    revoked_procuration_signing = _FR_PROCURATION_REVOKED_SIGNING_NOW.search(leftover)
    if revoked_procuration_signing:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.procuration_revoked_signing_now.v1",
                name=revoked_procuration_signing.group("name").strip(),
                signing=_fr_signing(revoked_procuration_signing.group("sign")),
                extra={
                    "action": "modified",
                    "previous_signing": "procuration",
                    "procuration_revoked": True,
                },
            )
        )
        leftover = leftover.replace(revoked_procuration_signing.group(0), " ")
    radi = (
        _FR_SIGN_RADIEE.search(leftover)
        or _FR_POUVOIRS_RADIES.search(leftover)
        or _FR_PROCURATION_OFF.search(leftover)
    )
    if radi:
        name = re.sub(r"\s+", " ", radi.group("name")).strip().rstrip(".")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.sign_revoked.v1",
                name=name,
                extra={"action": "revoked"},
            )
        )
        leftover = leftover.replace(radi.group(0), " ")
    legacy_auditor_change = _FR_AUDITOR_LEGACY_RENAMED_AND_MOVED.search(leftover)
    if legacy_auditor_change:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.auditor_renamed_and_moved.v3",
                name=legacy_auditor_change.group("name").strip(),
                place=legacy_auditor_change.group("place").strip(),
                uid=legacy_auditor_change.group("uid"),
                role="organe de révision",
                extra={
                    "action": "name_and_seat_changed",
                    "previous": legacy_auditor_change.group("old_name").strip(),
                    "previous_registry_id": legacy_auditor_change.group("registry_id"),
                },
            )
        )
        leftover = leftover.replace(legacy_auditor_change.group(0), " ")
    auditor_identifier_seat = _FR_AUDITOR_IDENTIFIER_AND_SEAT.search(leftover)
    if auditor_identifier_seat:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.auditor_identifier_and_seat.v1",
                name=auditor_identifier_seat.group("name").strip(),
                place=auditor_identifier_seat.group("place").strip(),
                uid=auditor_identifier_seat.group("uid"),
                role="organe de révision",
                extra={"action": "identifier_and_seat_changed"},
            )
        )
        leftover = leftover.replace(auditor_identifier_seat.group(0), " ")
    auditor = _FR_AUDITOR_RENAME.search(leftover)
    if auditor:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.auditor_renamed.v1",
                name=auditor.group("name").strip(),
                uid=auditor.group("uid"),
                role="organe de révision",
            )
        )
        leftover = leftover.replace(auditor.group(0), " ")
    auditor_seat = _FR_AUDITOR_RENAME_AND_SEAT.search(leftover)
    if auditor_seat:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.auditor_renamed_and_moved.v1",
                name=auditor_seat.group("name").strip(),
                place=auditor_seat.group("place").strip(),
                uid=auditor_seat.group("uid"),
                role="organe de révision",
                extra={"action": "name_and_seat_changed"},
            )
        )
        leftover = leftover.replace(auditor_seat.group(0), " ")
    quoted_auditor = _FR_AUDITOR_RENAME_QUOTED.search(leftover)
    if quoted_auditor:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.auditor_renamed.v2",
                name=quoted_auditor.group("name").strip(),
                uid=quoted_auditor.group("uid"),
                role="organe de révision",
                extra={"previous": quoted_auditor.group("old_name").strip()},
            )
        )
        leftover = leftover.replace(quoted_auditor.group(0), " ")
    quoted_auditor_after_colon = _FR_AUDITOR_RENAME_QUOTED_AFTER_COLON.search(leftover)
    if quoted_auditor_after_colon:
        uid = (
            quoted_auditor_after_colon.group("uid_direct")
            or quoted_auditor_after_colon.group("uid_clause")
        )
        extra = {"previous": quoted_auditor_after_colon.group("old_name").strip()}
        if quoted_auditor_after_colon.group("old_registry"):
            extra["previous_registry_id"] = quoted_auditor_after_colon.group(
                "old_registry"
            )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.auditor_renamed.v6",
                name=quoted_auditor_after_colon.group("name").strip(),
                uid=uid,
                role="organe de révision",
                extra=extra,
            )
        )
        leftover = leftover.replace(quoted_auditor_after_colon.group(0), " ")
    legacy_auditor = _FR_AUDITOR_RENAME_QUOTED_LEGACY.search(leftover)
    if legacy_auditor:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.auditor_renamed.v4",
                name=legacy_auditor.group("name").strip(),
                place=legacy_auditor.group("place").strip(),
                uid=legacy_auditor.group("uid"),
                role="organe de révision",
                extra={
                    "previous": legacy_auditor.group("old_name").strip(),
                    "previous_registry_id": legacy_auditor.group("registry_id"),
                },
            )
        )
        leftover = leftover.replace(legacy_auditor.group(0), " ")
    new_auditor = _FR_NEW_AUDITOR.search(leftover)
    if new_auditor:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.auditor_new.v1",
                name=new_auditor.group("name").strip(),
                place=(new_auditor.group("place") or "").strip() or None,
                uid=new_auditor.group("uid"),
                role="organe de révision",
            )
        )
        leftover = leftover.replace(new_auditor.group(0), " ")
    auditor_now = _FR_AUDITOR_NOW.search(leftover)
    if auditor_now:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.auditor_renamed.v1",
                name=auditor_now.group("name").strip(),
                uid=auditor_now.group("uid"),
                role="organe de révision",
                extra={"previous": auditor_now.group("old_name").strip()},
            )
        )
        leftover = leftover.replace(auditor_now.group(0), " ")
    auditor_raison_and_seat = _FR_AUDITOR_RAISON_AND_SEAT.search(leftover)
    if auditor_raison_and_seat:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.auditor_renamed_and_moved.v2",
                name=auditor_raison_and_seat.group("name").strip(),
                place=auditor_raison_and_seat.group("place").strip(),
                uid=auditor_raison_and_seat.group("uid"),
                role="organe de révision",
                extra={
                    "action": "name_and_seat_changed",
                    "previous": auditor_raison_and_seat.group("old").strip(),
                },
            )
        )
        leftover = leftover.replace(auditor_raison_and_seat.group(0), " ")
    standalone_auditor = _FR_AUDITOR_STANDALONE_RENAMED_AND_MOVED.search(leftover)
    if standalone_auditor:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.auditor_renamed_and_moved.v4",
                name=standalone_auditor.group("name").strip(),
                place=standalone_auditor.group("place").strip(),
                uid=standalone_auditor.group("uid"),
                role="organe de révision",
                extra={
                    "action": "name_and_seat_changed",
                    "previous": standalone_auditor.group("old").strip(),
                    "previous_uid": standalone_auditor.group("old_uid"),
                },
            )
        )
        leftover = leftover.replace(standalone_auditor.group(0), " ")
    auditor_raison_with_id = _FR_AUDITOR_RAISON_WITH_ID.search(leftover)
    if auditor_raison_with_id:
        uid = auditor_raison_with_id.group("uid2") or auditor_raison_with_id.group("uid")
        extra = {"previous": auditor_raison_with_id.group("old").strip()}
        if auditor_raison_with_id.group("old_registry"):
            extra["previous_registry_id"] = auditor_raison_with_id.group("old_registry")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.auditor_renamed.v3",
                name=auditor_raison_with_id.group("name").strip(),
                uid=uid,
                role="organe de révision",
                extra=extra,
            )
        )
        leftover = leftover.replace(auditor_raison_with_id.group(0), " ")
    auditor_raison = _FR_AUDITOR_RAISON.search(leftover)
    if auditor_raison:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.auditor_renamed.v1",
                name=auditor_raison.group("name").strip(),
                uid=auditor_raison.group("uid2"),
                role="organe de révision",
                extra={"previous": auditor_raison.group("old").strip()},
            )
        )
        leftover = leftover.replace(auditor_raison.group(0), " ")
    for two in list(_FR_CONFEREE_TWO.finditer(leftover)):
        kind = two.group("kind").lower()
        what = two.group("what").lower()
        if "procuration" in what:
            signing = "Einzelprokura" if "individuelle" in kind else "Kollektivprokura zu zweien"
        else:
            signing = "Einzelunterschrift" if "individuelle" in kind else "Kollektivunterschrift zu zweien"
        role = (two.group("role") or "").strip() or None
        extra_with = {"with": two.group("with").strip()} if two.group("with") else {}
        place = two.group("place").strip().rstrip(".")
        for name, heimat in (
            (two.group("name1").strip(), two.group("heimat1").strip()),
            (two.group("name2").strip(), two.group("heimat2").strip()),
        ):
            extra = {"heimat": heimat, **extra_with}
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "signing_authority_changed",
                    "fr.persons.sign_granted.v1",
                    name=name,
                    place=place,
                    role=role,
                    signing=signing,
                    extra=extra,
                )
            )
        leftover = leftover.replace(two.group(0), " ")
    for confer in _FR_CONFEREE.finditer(leftover):
        kind = confer.group("kind").lower()
        what = confer.group("what").lower()
        if "procuration" in what:
            signing = "Einzelprokura" if "individuelle" in kind else "Kollektivprokura zu zweien"
        else:
            signing = "Einzelunterschrift" if "individuelle" in kind else "Kollektivunterschrift zu zweien"
        name = confer.group("name").strip()
        place = (confer.group("place_same") or confer.group("place") or "").strip().rstrip(".")
        extra = {}
        if confer.group("heimat"):
            extra["heimat"] = confer.group("heimat").strip()
        elif confer.group("place_same"):
            extra["heimat"] = place
        if confer.group("with"):
            qualifier = "not_with" if confer.group("except_with") else "with"
            extra[qualifier] = confer.group("with").strip()
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.sign_granted.v1",
                name=name,
                place=place or None,
                role=(confer.group("role") or "").strip() or None,
                signing=signing,
                extra=extra or None,
            )
        )
        leftover = leftover.replace(confer.group(0), " ")
    leftover = re.sub(
        r"Entreprise ayant son siège à [^,.]+(?:,\s*F)?\.?",
        " ",
        leftover,
        flags=re.I,
    )
    branch = _FR_BRANCH_DIR.search(leftover)
    if branch:
        signing = _fr_signing(branch.group("sign"))
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.branch_director.v1",
                name=branch.group("name").strip(),
                place=branch.group("place").strip(),
                role="directeur de la succursale",
                signing=signing,
                extra={"heimat": branch.group("heimat").strip()},
            )
        )
        leftover = leftover.replace(branch.group(0), " ")
    org_liquidator = _FR_ORG_LIQUIDATOR.search(leftover)
    if org_liquidator:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.organization_liquidator.v1",
                name=org_liquidator.group("name").strip(),
                place=org_liquidator.group("place").strip(),
                uid=org_liquidator.group("uid"),
                role="Liquidateur",
            )
        )
        leftover = leftover.replace(org_liquidator.group(0), " ")
    elected_org_liquidator = _FR_ORG_ELECTED_LIQUIDATOR.search(leftover)
    if elected_org_liquidator:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.organization_liquidator.v2",
                name=elected_org_liquidator.group("name").strip(),
                place=elected_org_liquidator.group("place").strip(),
                uid=elected_org_liquidator.group("uid"),
                role="Liquidatrice",
                extra={"action": "appointed"},
            )
        )
        leftover = leftover.replace(elected_org_liquidator.group(0), " ")
    elected_liquidator = _FR_ELECTED_LIQUIDATOR.search(leftover)
    if elected_liquidator:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.elected_liquidator.v1",
                name=elected_liquidator.group("name").strip(),
                role="Liquidateur",
                signing=_fr_signing(elected_liquidator.group("sign")),
                extra={
                    "previous": elected_liquidator.group("old_role").strip(),
                    "heimat": elected_liquidator.group("heimat").strip(),
                },
            )
        )
        leftover = leftover.replace(elected_liquidator.group(0), " ")
    liquidateur = _FR_LIQUIDATEUR.search(leftover)
    if liquidateur:
        name = re.sub(r"\s+", " ", liquidateur.group("name")).strip()
        sign = _fr_signing(liquidateur.group("sign"))
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.liquidateur.v1",
                name=name,
                role="Liquidateur",
                signing=sign,
                extra=(
                    {"heimat": liquidateur.group("heimat").strip()}
                    if liquidateur.group("heimat")
                    else None
                ),
            )
        )
        leftover = leftover.replace(liquidateur.group(0), " ")
    liquidateurs_with_roles = _FR_LIQUIDATEURS_WITH_ROLES.search(leftover)
    if liquidateurs_with_roles:
        signing = _fr_signing(liquidateurs_with_roles.group("sign"))
        for name_group, role_group in (("name1", "role1"), ("name2", "role2")):
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.liquidateurs.v2",
                    name=liquidateurs_with_roles.group(name_group).strip(),
                    role=f"Liquidateur, {liquidateurs_with_roles.group(role_group).strip()}",
                    signing=signing,
                    extra={"previous": "membre du conseil d'administration"},
                )
            )
        leftover = leftover.replace(liquidateurs_with_roles.group(0), " ")
    foundation_liquidators = _FR_FOUNDATION_LIQUIDATORS.search(leftover)
    if foundation_liquidators:
        signing = _fr_signing(foundation_liquidators.group("sign"))
        for name_group in ("name1", "name2", "name3"):
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.foundation_liquidators.v1",
                    name=foundation_liquidators.group(name_group).strip(),
                    role="Liquidateur",
                    signing=signing,
                    extra={"previous": "membre du conseil de fondation"},
                )
            )
        leftover = leftover.replace(foundation_liquidators.group(0), " ")
    liquidateurs = _FR_LIQUIDATEURS.search(leftover)
    if liquidateurs:
        signing = _fr_signing(liquidateurs.group("sign"))
        for name_group in ("name1", "name2"):
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.liquidateurs.v1",
                    name=liquidateurs.group(name_group).strip(),
                    role="Liquidateur",
                    signing=signing,
                    extra={"previous": liquidateurs.group("old_role").strip()},
                )
            )
        leftover = leftover.replace(liquidateurs.group(0), " ")
    appointed_with_previous_role = (
        _FR_APPOINTED_LIQUIDATOR_WITH_PREVIOUS_ROLE.search(leftover)
    )
    if appointed_with_previous_role:
        name = re.sub(
            r"\s+", " ", appointed_with_previous_role.group("name")
        ).strip()
        role = appointed_with_previous_role.group("role").capitalize()
        signing = _fr_signing(appointed_with_previous_role.group("sign"))
        previous_role = appointed_with_previous_role.group("previous_role").strip()
        for event_type, rule_id in (
            ("officer_changed", "fr.persons.appointed_liquidator.v2"),
            (
                "signing_authority_changed",
                "fr.persons.appointed_liquidator_signing.v2",
            ),
        ):
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    event_type,
                    rule_id,
                    name=name,
                    role=role,
                    signing=signing,
                    extra={"previous": previous_role},
                )
            )
        leftover = leftover.replace(appointed_with_previous_role.group(0), " ")
    appointed_liquidator = _FR_APPOINTED_LIQUIDATOR_SIMPLE.search(leftover)
    if appointed_liquidator:
        name = re.sub(r"\s+", " ", appointed_liquidator.group("name")).strip()
        signing = _fr_signing(appointed_liquidator.group("sign"))
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.appointed_liquidator.v1",
                name=name,
                role=appointed_liquidator.group("role").capitalize(),
                signing=signing,
            )
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.appointed_liquidator_signing.v1",
                name=name,
                role=appointed_liquidator.group("role").capitalize(),
                signing=signing,
            )
        )
        leftover = leftover.replace(appointed_liquidator.group(0), " ")
    nomme = _FR_NOMME_LIQUIDATEUR.search(leftover)
    if nomme:
        name = re.sub(r"\s+", " ", nomme.group("name")).strip()
        sign = _fr_signing(nomme.group("sign"))
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.liquidateur.v1",
                name=name,
                role="Liquidateur",
                signing=sign,
            )
        )
        leftover = leftover.replace(nomme.group(0), " ")
    gerant_liq = _FR_NOMME_GERANT_LIQ.search(leftover)
    if gerant_liq:
        name = re.sub(r"\s+", " ", gerant_liq.group("name")).strip()
        sign = _fr_signing(gerant_liq.group("sign"))
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.liquidateur.v1",
                name=name,
                role="Liquidateur",
                signing=sign,
            )
        )
        leftover = leftover.replace(gerant_liq.group(0), " ")
    for same_origin_dom in list(_FR_ORIGIN_AND_DOM_NOW.finditer(leftover)):
        name = re.sub(r"\s+", " ", same_origin_dom.group("name")).strip()
        place = same_origin_dom.group("place").strip()
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.origin_domicile.v1",
                name=name,
                place=place,
                extra={
                    "action": "origin_and_domicile_changed",
                    "heimat": place,
                },
            )
        )
        leftover = leftover.replace(same_origin_dom.group(0), " ")
    two_domiciles = _FR_TWO_DOMICILES_NOW.search(leftover)
    if two_domiciles:
        place = two_domiciles.group("place").strip()
        for name_group in ("name1", "name2"):
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.domicile_pair.v1",
                    name=two_domiciles.group(name_group).strip(),
                    place=place,
                    extra={"action": "domicile_changed"},
                )
            )
        leftover = leftover.replace(two_domiciles.group(0), " ")
    for origin_dom in list(_FR_ORIGIN_DOM.finditer(leftover)):
        name = re.sub(r"\s+", " ", origin_dom.group("name")).strip()
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.domicile.v1",
                name=name,
                place=origin_dom.group("place").strip(),
                extra={
                    "action": "domicile_changed",
                    "heimat": origin_dom.group("heimat").strip(),
                },
            )
        )
        leftover = leftover.replace(origin_dom.group(0), " ")
    for origin in list(_FR_ORIGIN_ONLY.finditer(leftover)):
        name = re.sub(r"\s+", " ", origin.group("name")).strip()
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.origin.v1",
                name=name,
                extra={
                    "action": "origin_changed",
                    "heimat": origin.group("heimat").strip(),
                },
            )
        )
        leftover = leftover.replace(origin.group(0), " ")
    for dom in list(_FR_DOMICILE_NOW.finditer(leftover)):
        name = re.sub(r"\s+", " ", dom.group("name")).strip()
        uid = dom.group("uid")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.domicile.v1",
                name=name,
                place=dom.group("place").strip(),
                uid=uid,
                role="organe de révision" if uid else None,
                extra={"action": "domicile_changed"},
            )
        )
        leftover = leftover.replace(dom.group(0), " ")
    for now_at in list(_FR_NOW_AT.finditer(leftover)):
        name = re.sub(r"\s+", " ", now_at.group("name")).strip()
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.domicile.v1",
                name=name,
                place=now_at.group("place").strip(),
                extra={"action": "domicile_changed"},
            )
        )
        leftover = leftover.replace(now_at.group(0), " ")
    leftover = re.sub(r"\s+", " ", leftover).strip(" .")
    leftover = re.sub(r"\bil\s+", " ", leftover, flags=re.I)
    leftover = re.sub(r"\s+", " ", leftover).strip(" .")
    return events, leftover
