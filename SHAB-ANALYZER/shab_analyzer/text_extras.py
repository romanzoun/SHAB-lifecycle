from __future__ import annotations

import re

from .models import Event

_DE_STATUTES = re.compile(
    r"(?:Statutenänderung|Urkundenänderung):\s*(?P<date>\d{2}\.\d{2}\.\d{4})",
    re.I,
)
_FR_STATUTES = re.compile(
    r"(?:Statuts modifiés le|Nouveaux statuts du|Modification des statuts:|"
    r"Modification de l'acte de fondation:|Acte de fondation modifié le)\s*"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}|\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})"
    r"(?:\s+et validés par décision de l'autorité de surveillance le "
    r"(?P<approval_date>\d{2}\.\d{2}\.\d{4}))?"
    r"(?:\s+et le\s+(?P<additional_date>\d{2}\.\d{2}\.\d{4}))?"
    r"(?:,?\s+(?:y compris\s+)?sur des points non soumis à publication)?\.?,?",
    re.I,
)
_FR_STATUTES_MULTIPLE = re.compile(
    r"Statuts modifiés les\s+(?P<dates>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}"
    r"(?:,\s*\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})*"
    r"\s+et\s+\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})\.?",
    re.I,
)
_FR_ADDITIONAL_NON_PUBLIC_STATUTES = re.compile(
    r"Statuts également modifiés sur des points non soumis à publication\.?",
    re.I,
)
_IT_STATUTES = re.compile(
    r"(?:Modifica(?: dello)? statuto|Modifica statutaria|Statuti modificati|"
    r"Atto pubblico modificato)[:\s]+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})",
    re.I,
)
_IT_FOUNDATION_DEED_SUPERVISORY_APPROVAL = re.compile(
    r"Atto di fondazione modificato con decisione della (?P<authority>.+?) "
    r"\((?P<authority_uid>CHE-\d{3}\.\d{3}\.\d{3})\) in (?P<authority_place>.+?) "
    r"in data (?P<date>\d{2}\.\d{2}\.\d{4}) su punti non soggetti a pubblicazione\.?,?",
    re.I,
)
_IT_NEW_SHARES = re.compile(
    r"Nuove azioni:\s*(?P<to_count>[\d']+)\s+azioni\s+(?P<to_kind>[^.]+?)\s+da\s+"
    r"CHF\s+(?P<to_nominal>[\d'.]+)\s*"
    r"\[(?:finora|no):\s*(?P<from_count>[\d']+)\s+azioni\s+(?P<from_kind>[^.]+?)\s+da\s+"
    r"CHF\s+(?P<from_nominal>[\d'.]+)\]\.?",
    re.I,
)
_FR_SHARE_CONVERSION = re.compile(
    r"Conversion des\s+(?P<count>[\d']+)\s+actions de CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"jusqu'ici au porteur,\s*en actions\s+(?P<to_kind>nominatives(?:,\s*liées selon statuts)?)\.?",
    re.I,
)
_FR_NEW_SHARES = re.compile(
    r"Nouvelles actions:\s*(?P<to_count>[\d']+)\s+actions\s+(?P<to_kind>.+?)\s+de\s+"
    r"CHF\s+(?P<to_nominal>[\d'.]+)(?:\s*\(chacune\))?"
    r"(?:\s+(?P<restriction>[^\[]+?))?\s*"
    r"\[précédemment:\s*(?P<from_count>[\d']+)\s+actions\s+(?P<from_kind>.+?)\s+de\s+"
    r"CHF\s+(?P<from_nominal>[\d'.]+)(?:\s*\(chacune\))?\]\.?,?",
    re.I,
)
_FR_BEARER_CONVERSION = re.compile(
    r"Les\s+(?P<from_count>[\d']+)\s+actions\s+(?P<from_kind>au porteur)\s+de\s+"
    r"CHF\s+(?P<from_nominal>[\d'.]+),\s*formant l'entier du capital-actions,\s*"
    r"sont converties en\s+(?P<to_count>[\d']+)\s+actions\s+(?P<to_kind>nominatives)\s+de\s+"
    r"CHF\s+(?P<to_nominal>[\d'.]+)(?:,\s*(?P<restriction>[^.]+))?\.?,?",
    re.I,
)
_DE_LEGAL_BEARER_CONVERSION_SHARES_FIRST = re.compile(
    r"Aktien neu:\s*(?P<to_count>[\d']+)\s+(?P<to_kind>Namenaktien)\s+zu\s+"
    r"CHF\s+(?P<to_nominal>[\d'.]+)\s*"
    r"\[bisher:\s*(?P<from_count>[\d']+)\s+(?P<from_kind>Inhaberaktien)\s+zu\s+"
    r"CHF\s+(?P<from_nominal>[\d'.]+)\]\.\s*"
    r"Die Inhaberaktien sind am (?P<date>\d{2}\.\d{2}\.\d{4}|\d{1,2}\.\s+"
    r"(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+\d{4}) "
    r"von Gesetzes wegen in Namenaktien umgewandelt worden\.\s*"
    r"Die Statuten der Gesellschaft sind noch nicht an die Umwandlung angepasst(?: worden)?;\s*"
    r"die Anpassung muss anlässlich der nächsten Statutenänderung erfolgen\.?,?",
    re.I,
)
_DE_LEGAL_BEARER_CONVERSION_CAPITAL_LAST = re.compile(
    r"Die Inhaberaktien sind am (?P<date>\d{2}\.\d{2}\.\d{4}|\d{1,2}\.\s+"
    r"(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+\d{4}) "
    r"von Gesetzes wegen in Namenaktien umgewandelt worden\.\s*"
    r"Die Statuten der Gesellschaft sind noch nicht an die Umwandlung angepasst worden;\s*"
    r"die Anpassung muss anlässlich der nächsten Statutenänderung erfolgen\.\s*"
    r"Aktienkapital neu:\s*CHF\s+(?P<total>[\d'.]+),\s*"
    r"(?P<paid>vollständig|vollstänfig|voll) liberiert,\s*eingeteilt in\s*"
    r"(?P<to_count>[\d']+)\s+(?P<to_kind>Namenaktien)\s+zu\s+CHF\s+"
    r"(?P<to_nominal>[\d'.]+)\s*\((?:bisher|bischer):?\s*(?P<from_count>[\d']+)\s+"
    r"(?P<from_kind>Inhaberaktien)\s+zu\s+CHF\s+(?P<from_nominal>[\d'.]+)\)\.?,?",
    re.I,
)
_DE_LEGAL_BEARER_CONVERSION_MULTIPLE_CLASSES = re.compile(
    r"Die Inhaberaktien sind am (?P<date>\d{2}\.\d{2}\.\d{4}) "
    r"von Gesetzes wegen in Namenaktien umgewandelt worden\.\s*"
    r"Die Statuten der Gesellschaft sind noch nicht an die Umwandlung angepasst worden;\s*"
    r"die Anpassung muss anlässlich der nächsten Statutenänderung erfolgen\.\s*"
    r"Aktienkapital neu:\s*CHF\s+(?P<total>[\d'.]+),\s*"
    r"(?P<paid>vollständig|vollstänfig|voll) liberiert,\s*eingeteilt in\s*"
    r"(?P<count1>[\d']+) Namenaktien zu CHF\s+(?P<nominal1>[\d'.]+)\s*"
    r"\((?P<class1>[^)]+)\);\s*"
    r"(?P<count2>[\d']+) Namenaktien zu CHF\s+(?P<nominal2>[\d'.]+)\s*"
    r"\(bisher\s+(?P<from_count1>[\d']+) Namenaktien zu CHF\s+"
    r"(?P<from_nominal1>[\d'.]+)\s*\((?P<from_class1>[^)]+)\);\s*"
    r"(?P<from_count2>[\d']+) Inhaberaktien zu CHF\s+"
    r"(?P<from_nominal2>[\d'.]+)\)\.?,?",
    re.I,
)
_DE_LEGAL_BEARER_CONVERSION_MULTIPLE_CLASSES_SIMPLE = re.compile(
    r"Die Inhaberaktien sind am (?P<date>\d{2}\.\d{2}\.\d{4}) "
    r"von Gesetzes wegen in Namenaktien umgewandelt worden\.\s*"
    r"Die Statuten der Gesellschaft sind noch nicht an die Umwandlung angepasst worden;\s*"
    r"die Anpassung muss anlässlich der nächsten Statutenänderung erfolgen\.\s*"
    r"Aktienkapital neu:\s*CHF\s+(?P<total>[\d'.]+),\s*"
    r"(?P<paid>vollständig|vollstänfig|voll) liberiert,\s*eingeteilt in\s*"
    r"(?P<to_count1>[\d']+) Namenaktien zu CHF\s+(?P<to_nominal1>[\d'.]+)\s+und\s+"
    r"(?P<to_count2>[\d']+) Namenaktien zu CHF\s+(?P<to_nominal2>[\d'.]+)\s*"
    r"\(bisher:\s*(?P<from_count1>[\d']+) Inhaberaktien zu CHF\s+"
    r"(?P<from_nominal1>[\d'.]+)\s+und\s+(?P<from_count2>[\d']+) Namenaktien "
    r"zu CHF\s+(?P<from_nominal2>[\d'.]+)\)\.?,?",
    re.I,
)
_DE_LEGAL_BEARER_CONVERSION_MULTIPLE_CLASSES_SHARES_FIRST = re.compile(
    r"Aktien neu:\s*(?P<to_count1>[\d']+) Namenaktien zu CHF\s+"
    r"(?P<to_nominal1>[\d'.]+)\s+und\s+(?P<to_count2>[\d']+) Namenaktien zu CHF\s+"
    r"(?P<to_nominal2>[\d'.]+)\s*\((?P<class2>[^)]+)\)\s*"
    r"\[bisher:\s*(?P<from_count1>[\d']+) Inhaberaktien zu CHF\s+"
    r"(?P<from_nominal1>[\d'.]+)\s+und\s+(?P<from_count2>[\d']+) Namenaktien zu CHF\s+"
    r"(?P<from_nominal2>[\d'.]+)\s*\((?P<from_class2>[^)]+)\)\]\.\s*"
    r"Die Inhaberaktien sind am (?P<date>\d{2}\.\d{2}\.\d{4}) "
    r"von Gesetzes wegen in Namenaktien umgewandelt worden\.\s*"
    r"Die Statuten der Gesellschaft sind noch nicht an die Umwandlung angepasst worden;\s*"
    r"die Anpassung muss anlässlich der nächsten Statutenänderung erfolgen\.?,?",
    re.I,
)
_DE_LEGAL_BEARER_CONVERSION_PARTIAL_PAID = re.compile(
    r"Die Inhaberaktien sind am (?P<date>\d{2}\.\d{2}\.\d{4}) "
    r"von Gesetzes wegen in Namenaktien umgewandelt worden\.\s*"
    r"Die Statuten der Gesellschaft sind noch nicht an die Umwandlung angepasst worden;\s*"
    r"die Anpassung muss anlässlich der nächsten Statutenänderung erfolgen\.\s*"
    r"Aktienkapital:\s*CHF\s+(?P<total>[\d'.]+),\s*liberiert mit CHF\s+"
    r"(?P<paid>[\d'.]+),\s*eingeteilt in\s*(?P<to_count>[\d']+)\s+"
    r"(?P<to_kind>Namenaktien) zu CHF\s+(?P<to_nominal>[\d'.]+)\s*"
    r"\(bisher:\s*(?P<from_count>[\d']+)\s+(?P<from_kind>Inhaberaktien) "
    r"zu CHF\s+(?P<from_nominal>[\d'.]+)\)\.?,?",
    re.I,
)
_DE_LEGAL_BEARER_CONVERSION_NOTICE_REMOVED = re.compile(
    r"\[gestrichen:\s*Die Inhaberaktien sind am (?P<date>\d{2}\.\d{2}\.\d{4}|\d{1,2}\.\s+"
    r"(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+\d{4}) "
    r"von Gesetzes wegen in Namenaktien umgewandelt worden\.\s*"
    r"Die Statuten der Gesellschaft sind noch nicht an die Umwandlung angepasst worden;\s*"
    r"die Anpassung muss anlässlich der nächsten Statutenänderung erfolgen\.\]\.?,?",
    re.I,
)
_DE_LEGAL_BEARER_CONVERSION_NOTICE = re.compile(
    r"Die Inhaberaktien sind am (?P<date>\d{2}\.\d{2}\.\d{4}|\d{1,2}\.\s+"
    r"(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+\d{4}) "
    r"von Gesetzes wegen in Namenaktien umgewandelt worden\.\s*"
    r"Die Statuten der Gesellschaft sind noch nicht an die Umwandlung angepasst(?: worden)?;\s*"
    r"die Anpassung muss anlässlich der nächsten Statutenänderung erfolgen\.?,?",
    re.I,
)
_FR_LEGAL_BEARER_CONVERSION = re.compile(
    r"Le\s+(?P<date>\d{2}\.\d{2}\.\d{4}|\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}),\s*"
    r"les actions au porteur ont été converties de par la loi en actions nominatives\.\s*"
    r"Les statuts de la société n['’]ont pas encore été adaptés à la conversion,?\s*"
    r"mais devront l['’]être lors de la prochaine modification\.\s*"
    r"Capital-actions(?P<new> nouveau)?:\s*CHF\s+(?:CHF\s+)?(?P<total>[\d'.]+),\s*"
    r"(?:(?P<fully_paid>entièrement libéré)|libéré à (?:concurrence|hauteur) de CHF\s+(?:CHF\s+)?(?P<paid>[\d'.]+)),\s*"
    r"(?:divisé en\s+)?(?P<to_count>[\d']+)\s+actions?\s+"
    r"(?:(?P<kind_before>(?:au\s+)?nominatives|noinatives)\s+de|de)\s+CHF\s+(?P<to_nominal>[\d'.]+)"
    r"(?:,\s*(?P<kind_after>nominatives?|au\s+porteur))?"
    r"(?:\s*\(jusqu['’]ici:\s*(?P<from_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<from_nominal>[\d'.]+),\s*(?P<from_kind>au porteur)\))?\.?,?",
    re.I,
)
_FR_ADAPTED_BEARER_CONVERSION = re.compile(
    r"Par décision de l['’]assemblée générale du (?P<adaptation_date>\d{2}\.\d{2}\.\d{4}),?\s*"
    r"les statuts de la société ont été adaptés à la conversion de par la loi des "
    r"actions au porteur en actions nominatives du (?P<conversion_date>\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})\.\s*"
    r"(?:\.\s*)?(?:Nouveau capital-actions|Capital-actions):\s*CHF\s+(?P<total>[\d'.]+),\s*"
    r"(?:(?P<fully_paid>entièrement libéré)|libéré à concurrence de CHF\s+(?P<paid>[\d'.]+)),\s*"
    r"divisé en\s+"
    r"(?P<count>[\d']+)\s+actions nominatives de CHF\s+(?P<nominal>[\d'.]+)"
    r"(?:,\s*(?P<restriction>avec restrictions quant à la transmissibilité selon statuts))?\.?,?",
    re.I,
)
_FR_ADAPTED_BEARER_CONVERSION_NOTICE_ALT = re.compile(
    r"Par décision de l['’]assemblée générale du "
    r"(?P<adaptation_date>\d{2}\.\d{2}\.\d{4}),?\s*"
    r"les statuts de la société ont été adaptés à la conversion de par la loi "
    r"des actions au porteur en actions nominatives du (?P<conversion_date>\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})\.?,?",
    re.I,
)
_FR_ADAPTED_BEARER_CONVERSION_NOTICE_AT_DATE = re.compile(
    r"Par décision de l['’]assemblée générale du "
    r"(?P<adaptation_date>\d{2}\.\d{2}\.\d{4}),?\s*"
    r"les statuts de la société ont été adaptés à la conversion de par la loi "
    r"des actions au porteur en actions nominatives au (?P<conversion_date>\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})\.?,?",
    re.I,
)
_FR_ADAPTED_BEARER_CONVERSION_NOTICE_NO_DATE = re.compile(
    r"Par décision de l['’]assemblée générale du "
    r"(?P<adaptation_date>\d{2}\.\d{2}\.\d{4}),?\s*"
    r"les statuts de la société ont été adaptés à la conversion de par la loi "
    r"des actions au porteur en actions nominatives\.?,?",
    re.I,
)
_FR_LEGAL_BEARER_CONVERSION_ADAPTED_CAPITAL = re.compile(
    r"Le\s+(?P<conversion_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"les actions au porteur ont été converties de par la loi en actions nominatives;\s*"
    r"par décision de l['’]assemblée générale du "
    r"(?P<adaptation_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?:déposée au registre du commerce ultérieurement,\s*)?"
    r"les statuts de la société ont été adaptés à la conversion\.\s*"
    r"(?:Les actions(?: nominatives)? sont (?:désormais )?liées selon statuts\.\s*)?"
    r"Capital-actions:\s*CHF\s+(?P<total>[\d'.]+),\s*"
    r"(?:(?P<fully_paid>entièrement libéré)|libéré à concurrence de CHF\s+(?P<paid>[\d'.]+)),\s*"
    r"divisé en\s+(?P<count>[\d']+)\s+actions de CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"nominatives(?:,?\s*(?:désormais\s+)?(?P<restriction>liées selon statuts))?\.?,?",
    re.I,
)
_FR_BEARER_CONVERSION_WITH_CAPITAL = re.compile(
    r"Conversion des actions au porteur en actions nominatives\.\s*"
    r"Capital-actions:\s*CHF\s+(?P<total>[\d'.]+),\s*"
    r"(?:(?P<fully_paid>entièrement libéré)|libéré à concurrence de CHF\s+(?P<paid>[\d'.]+)),\s*"
    r"divisé en\s+(?P<count>[\d']+)\s+actions de CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"(?P<restriction>liées selon statuts)\.?,?",
    re.I,
)
_FR_LEGAL_BEARER_CONVERSION_NOTICE = re.compile(
    r"Le\s+(?P<date>\d{2}\.\d{2}\.\d{4}|\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}),\s*"
    r"les actions au porteur ont été converties de par la loi en actions nominatives\.\s*"
    r"Les statuts de la société n['’]ont pas encore été adaptés à la conversion,?\s*"
    r"mais devront l['’]être lors de la prochaine modification\.?,?",
    re.I,
)
_FR_LEGAL_BEARER_CONVERSION_NOTICE_REMOVED = re.compile(
    r"\[biffé:\s*Le\s+(?P<date>\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}),\s*"
    r"les actions au porteur ont été converties de par la loi en actions nominatives\.\s*"
    r"Les statuts de la société n['’]ont pas encore été adaptés à la conversion,?\s*"
    r"mais devront l['’]être lors de la prochaine modification\.\]\.?,?",
    re.I,
)
_IT_LEGAL_BEARER_CONVERSION_ADAPTED = re.compile(
    r"\[Con deliberazione dell['’]assemblea generale del (?P<adaptation_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"gli statuti della società sono stati adeguati alla conversione per legge delle azioni "
    r"al portatore in azioni nominative avvenuta in data (?P<conversion_date>\d{2}\.\d{2}\.\d{4})\.\]\s*"
    r"\[radiati:\s*In data (?P<removed_date>\d{2}\.\d{2}\.\d{4}) le azioni al portatore "
    r"sono state convertite per legge in azioni nominative\.\s*"
    r"(?:Gli statuti della società non sono ancora stati adeguati;\s*"
    r"l['’]adeguamento deve avvenire in occasione della prossima modifica statutaria\.)?\]\.?,?",
    re.I,
)
_FR_LEGAL_BEARER_CONVERSION_MULTIPLE_CLASSES = re.compile(
    r"Le\s+(?P<date>\d{2}\.\d{2}\.\d{4}|\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}),\s*"
    r"les actions au porteur ont été converties de par la loi en actions nominatives\.\s*"
    r"Les statuts de la société n['’]ont pas encore été adaptés à la conversion,?\s*"
    r"mais devront l['’]être lors de la prochaine modification\.\s*"
    r"Capital-actions(?: nouveau)?:\s*CHF\s+(?P<total>[\d'.]+),\s*"
    r"(?:entièrement libéré|libéré à concurrence de CHF\s+(?P<paid>[\d'.]+)),\s*"
    r"divisé en\s+(?P<count1>[\d']+) actions nominatives de CHF\s+"
    r"(?P<nominal1>[\d'.]+),\s*(?P<rights1>[^,]+),\s*et\s*"
    r"(?P<count2>[\d']+) actions (?:au )?nominatives de CHF\s+"
    r"(?P<nominal2>[\d'.]+)\.?,?",
    re.I,
)
_FR_LEGAL_BEARER_CONVERSION_MULTIPLE_CLASSES_POSTFIX_KIND = re.compile(
    r"Le\s+(?P<date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"les\s+(?P<from_count>[\d']+)\s+actions au porteur ont été converties de par la loi "
    r"en actions nominatives\.\s*"
    r"Les statuts de la société n['’]ont pas encore été adaptés à la conversion,?\s*"
    r"mais devront l['’]être lors de la prochaine modification\.\s*"
    r"Capital-actions:\s*CHF\s+(?P<total>[\d'.]+),\s*"
    r"libéré à (?:concurrence|hauteur) de CHF\s+(?P<paid>[\d'.]+),\s*"
    r"divisé en\s+(?P<count1>[\d']+)\s+actions de CHF\s+(?P<nominal1>[\d'.]+),\s*"
    r"nominatives,\s*(?P<rights1>.+?),\s*et\s*"
    r"(?P<count2>[\d']+)\s+actions de CHF\s+(?P<nominal2>[\d'.]+),\s*"
    r"nominatives\.?",
    re.I,
)
_FR_LEGAL_BEARER_CONVERSION_SHARES_LAST = re.compile(
    r"Le\s+(?P<date>\d{2}\.\d{2}\.\d{4}|\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}),\s*"
    r"les actions au porteur ont été converties de par la loi en actions nominatives\.\s*"
    r"Les statuts de la société n['’]ont pas encore été adaptés à la conversion,\s*"
    r"mais devront l['’]être lors de la prochaine modification\.\s*"
    r"Les\s+(?P<from_count>[\d']+)\s+actions\s+(?P<from_kind>au porteur)\s+de CHF\s+"
    r"(?P<from_nominal>[\d'.]+)\s+sont converties en\s+"
    r"(?P<to_count>[\d']+)\s+actions\s+(?P<to_kind>nominatives)\s+de CHF\s+"
    r"(?P<to_nominal>[\d'.]+)\.?,?",
    re.I,
)
_FR_LEGAL_BEARER_CONVERSION_CLASSES = re.compile(
    r"Le\s+(?P<date>\d{2}\.\d{2}\.\d{4}|\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}),\s*"
    r"les (?:[\d']+\s+)?actions au porteur ont été converties de par la loi en actions nominatives\.\s*"
    r"Les statuts de la société n['’]ont pas encore été adaptés à la conversion,\s*"
    r"mais devront l['’]être lors de la prochaine modification\.\s*"
    r"Capital-actions(?P<new> nouveau)?:\s*CHF\s+(?P<total>[\d'.]+),\s*"
    r"(?:entièrement libéré|libéré à concurrence de CHF\s+(?P<paid>[\d'.]+)),\s*"
    r"divisé en\s+(?P<count1>[\d']+)\s+actions\s+(?:nominatives\s+)?"
    r"(?P<class1>[^.\s,]+)\s+de CHF\s+(?P<nominal1>[\d'.]+)"
    r"(?:,\s*nominatives)?\s*,?\s*et\s+"
    r"(?P<count2>[\d']+)\s+actions\s+(?:nominatives\s+)?"
    r"(?P<class2>[^.\s,]+)\s+de CHF\s+(?P<nominal2>[\d'.]+)"
    r"(?:,\s*nominatives)?(?:,\s*(?P<rights>[^.]+))?\.?,?",
    re.I,
)
_FR_LEGAL_BEARER_CONVERSION_ADAPTED_NOTICE = re.compile(
    r"Par décision de l['’]assemblée générale du (?P<adaptation_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"les statuts de la société ont été adaptés à la conversion des actions au porteur "
    r"en actions nominatives de par la loi du (?P<conversion_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"après la conversion d['’]office inscrite le (?P<registration_date>\d{2}\.\d{2}\.\d{4})\.?,?",
    re.I,
)
_FR_LEGAL_BEARER_CONVERSION_CORRECTED = re.compile(
    r"\[biffé:\s*Le\s+\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4},\s*"
    r"les actions au porteur ont été converties de par la loi en actions nominatives\.\s*"
    r"Les statuts de la société n['’]ont pas encore été adaptés à la conversion,\s*"
    r"mais devront l['’]être lors de la prochaine modification\.\]\.?\s*"
    r"La conversion d['’]office a eu lieu à tort,\s*la société ayant converti ses actions "
    r"au porteur en actions nominatives par décision de l['’]assemblée générale du "
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.?,?",
    re.I,
)
_FR_PUBLICATION_ORGAN = re.compile(
    r"Nouvel organe de publication:\s*(?P<to>[^.]+)\.?,?",
    re.I,
)
_DE_PUBLICATION_ORGAN = re.compile(
    r"Publikationsorgan neu:\s*(?P<to>[^.]+)\.?,?",
    re.I,
)
_IT_PUBLICATION_ORGAN = re.compile(
    r"Nuovo organo di pubblicazione:\s*(?P<to>[^.]+)\.?,?",
    re.I,
)
_DE_SIMULTANEOUS_CAPITAL_CHANGE = re.compile(
    r"Bei der Kapitalherabsetzung vom (?P<decrease_date>\d{2}\.\d{2}\.\d{4}) "
    r"werden (?P<decrease_count>[\d']+) (?P<decrease_kind>[^.]+?) zu CHF "
    r"(?P<decrease_nominal>[\d'.]+) vernichtet\.\s*Gleichzeitig werden bei der "
    r"ordentlichen Kapitalerhöhung vom (?P<increase_date>\d{2}\.\d{2}\.\d{4}) "
    r"(?P<increase_count>[\d']+) (?P<increase_paid>voll liberierte )?"
    r"(?P<increase_kind>[^.]+?) zu CHF (?P<increase_nominal>[\d'.]+) ausgegeben\.?",
    re.I,
)
_DE_SIMULTANEOUS_CAPITAL_RECAPITALIZATION = re.compile(
    r"Bei der Kapitalherabsetzung vom (?P<date>\d{2}\.\d{2}\.\d{4}) werden "
    r"(?P<decrease_count>[\d']+) (?P<decrease_kind>[^.]+?) zu CHF "
    r"(?P<decrease_nominal>[\d'.]+) vernichtet zwecks (?P<purpose>[^.]+)\.\s*"
    r"Gleichzeitig wird das Aktienkapital auf CHF (?P<capital_total>[\d'.]+) mittels "
    r"ordentlicher Kapitalerhöhung erhöht und es werden (?P<increase_count>[\d']+) "
    r"(?P<increase_paid>voll liberierte )?(?P<increase_kind>[^.]+?) zu CHF "
    r"(?P<increase_nominal>[\d'.]+) ausgegeben\.?,?",
    re.I,
)
_FR_BEARER_SHARES_AUTHORIZED = re.compile(
    r"La société ayant des titres de participation cotés en bourse,\s*"
    r"elle est autorisée à avoir des actions au porteur\.?,?",
    re.I,
)
_DE_BEARER_SHARES_AUTHORIZED = re.compile(
    r"(?:Da die Gesellschaft Beteiligungsrechte an einer Börse kotiert hat,\s*"
    r"ist sie befugt, Inhaber(?:aktien|-Partizipationsscheine) zu halten|"
    r"Die Gesellschaft hat Beteiligungsrechte an einer Börse kotiert und ist daher befugt,\s*"
    r"Inhaber(?:aktien|-Partizipationsscheine) zu halten)\.?",
    re.I,
)
_FR_BEARER_SHARES_AS_INTERMEDIATED_SECURITIES = re.compile(
    r"La société est autorisée à avoir des actions au porteur car elles sont toutes "
    r"émises sous forme de titres intermédiés au sens de la loi fédérale sur les "
    r"titres intermédiés\.?,?",
    re.I,
)
_DE_BEARER_SHARES_AS_INTERMEDIATED_SECURITIES = re.compile(
    r"Da die Gesellschaft sämtliche Inhaberaktien als Bucheffekten im Sinne des "
    r"Bucheffektengesetzes ausgestaltet hat,\s*ist sie befugt,\s*sie zu halten\.?",
    re.I,
)
_DE_PARTICIPATION_CERTIFICATES_ADDED = re.compile(
    r"Genussscheine neu:\s*(?P<count>[\d']+) Genussscheine,\s*"
    r"mit Rechten auf (?P<rights>[^.]+)\.?,?",
    re.I,
)
_DE_PREFERENCE_SHARE_RIGHTS = re.compile(
    r"Statutarische Vorrechte neu:\s*Die Vorzugsaktien gewähren Vorrechte "
    r"bezüglich (?P<rights>[^.]+)\.?,?\s*"
    r"(?:\[bisher:\s*Die Vorzugsaktien gewähren Vorrechte bezüglich "
    r"(?P<previous_rights>[^\]]+?)\.?\]\.?\s*)?",
    re.I,
)
_FR_CAPITAL_RECAP = re.compile(r"Capital-actions:\s*[^.]+\.?", re.I)
_FR_SIMULTANEOUS_CAPITAL_RECAPITALIZATION = re.compile(
    r"Nouveaux faits qualifiés:\s*Capital-actions réduit de CHF\s+"
    r"(?P<from_total>[\d'.]+)\s+à CHF\s+(?P<reduced_total>[\d'.]+)\s+"
    r"par suite de (?P<reason>pertes) et destruction de\s+(?P<decrease_count>[\d']+)\s+"
    r"actions (?P<decrease_kind>au porteur|nominatives) de CHF\s+"
    r"(?P<decrease_nominal>[\d'.]+)\.\s*Capital-actions reporté simultanément à CHF\s+"
    r"(?P<to_total>[\d'.]+)\s+par l['’]émission de\s+(?P<increase_count>[\d']+)\s+"
    r"actions (?P<increase_kind>au porteur|nominatives) de CHF\s+"
    r"(?P<increase_nominal>[\d'.]+),\s*entièrement libérées par compensation d['’]une "
    r"créance de CHF\s+(?P<compensation>[\d'.]+)\.?,?",
    re.I,
)
_FR_SHAREHOLDER_NOTICE = re.compile(r"Communication aux actionnaires:\s*.+", re.I)
_FR_COMMUNICATIONS_CLAUSE_REMOVED = re.compile(
    r"Les statuts ne prévoient plus de clause particulière relative aux "
    r"communications aux actionnaires\.?,?",
    re.I,
)
_FR_COMMUNICATIONS = re.compile(
    r"(?:Convocations et\s+)?(?:Nouvelles communications:\s*)?"
    r"(?:Nouvelles communications|Nouveau mode de communication|Communications?) "
    r"aux (?:actionnaires|associés|sociétaires):\s*"
    r"(?P<to>[^.]+)\.?",
    re.I,
)
_DELETION_NOTES = [
    re.compile(r"La società è cancellata[^.]*", re.I),
    re.compile(r"Die Gesellschaft ist (?:gelöscht|erloschen)[^.]*", re.I),
    re.compile(r"Die Liquidation ist durchgeführt[^.]*", re.I),
    re.compile(r"Die Zustimmungen der Steuerverwaltungen liegen vor[^.]*", re.I),
    re.compile(r"La société est radiée[^.]*", re.I),
]
_BANKRUPTCY_NOTE = re.compile(r"Das Konkursverfahren[^.]+", re.I)
_DE_DISSOLVED = re.compile(
    r"Die Gesellschaft ist mit Beschluss(?: der [^.]{0,80}?)? vom (?P<date>\d{2}\.\d{2}\.\d{4}) aufgelöst\.?",
    re.I,
)
_DE_BANKRUPTCY_EFFECT_SUSPENDED = re.compile(
    r"Mit Verfügung des (?P<authority>.+?) vom (?P<decision_date>\d{2}\.\d{2}\.\d{4}) "
    r"ist der Beschwerde gegen (?:das Urteil|die Verfügung) .+? vom "
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4}) betreffend Konkurseröffnung "
    r"aufschiebende Wirkung zuerkannt worden\.\s*Demnach wird die Eintragung betreffend "
    r"(?:Auflösung der Gesellschaft infolge )?Konkurs(?:es)? im Handelsregister gestrichen\.?"
    r"(?:\s*\[bisher:.*?\])?",
    re.I | re.DOTALL,
)
_DE_BANKRUPTCY_EFFECT_SUSPENDED_BY_COURT = re.compile(
    r"(?P<authority>Das Kantonsgericht .+?) hat der Beschwerde gegen die Verfügung "
    r"des (?P<court>.+?) vom (?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4}) "
    r"betreffend Konkurseröffnung aufschiebende Wirkung zuerkannt\.\s*"
    r"Demnach wird die Eintragung betreffend "
    r"(?:Auflösung der Gesellschaft infolge )?Konkurs im Handelsregister gestrichen\."
    r"(?:\s*\[bisher:.*?\])?\.?",
    re.I | re.DOTALL,
)
_DE_BANKRUPTCY_EFFECT_SUSPENDED_DECISION = re.compile(
    r"Mit Verfügung des (?P<authority>.+?) vom (?P<decision_date>\d{2}\.\d{2}\.\d{4}) "
    r"ist der Beschwerde gegen den Entscheid des (?P<court>.+?) vom "
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4}) betreffend Konkurseröffnung "
    r"aufschiebende Wirkung zuerkannt worden\.?,?",
    re.I,
)
_DE_APPEAL_EFFECT_SUSPENDED = re.compile(
    r"Mit Entscheid vom (?P<decision_date>\d{2}\.\d{2}\.\d{4}) ist der Beschwerde "
    r"aufschiebende Wirkung zuerkannt worden\.?,?",
    re.I,
)
_DE_OWNER_BANKRUPTCY_EFFECT_SUSPENDED = re.compile(
    r"Mit (?P<document>Verfügung|Mitteilung) des (?P<authority>.+?) vom "
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}) ist (?:der Beschwerde|dem Rekurs) gegen "
    r"(?:die Verfügung|den Entscheid) (?:des|der) (?P<court>.+?) vom "
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4}) betreffend Konkurseröffnung "
    r"aufschiebende Wirkung zuerkannt worden\.\s*Demnach (?P<outcome>"
    r"besteht das Einzelunternehmen entsprechend den früheren Eintragungen weiter|"
    r"wird die Eintragung betreffend Konkurseröffnung über den Inhaber im Handelsregister gestrichen)\."
    r"(?:\s*\[bisher:.*?\])?",
    re.I | re.DOTALL,
)
_DE_OWNER_BANKRUPTCY_EFFECT_SUSPENDED_DIRECT = re.compile(
    r"Mit Verfügung vom (?P<decision_date>\d{2}\.\d{2}\.\d{4}) hat die "
    r"(?P<authority>.+?) der Beschwerde des Inhabers gegen das erstinstanzliche "
    r"Konkurserkenntnis die aufschiebende Wirkung erteilt\.\s*"
    r"\[gestrichen:\s*Mit Entscheid des (?P<court>.+?) vom "
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4}) wurde über den Inhaber dieses "
    r"Einzelunternehmens mit Wirkung ab dem "
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<time>\d{1,2}:\d{2}) Uhr,\s*der Konkurs eröffnet\.\]\.?",
    re.I,
)
_DE_APPEAL_DECISION_REVOKED = re.compile(
    r"In Gutheissung der Beschwerde hat (?P<authority>.+?) mit Entscheid vom "
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}) die Ziff\.\s*1 des Entscheids des "
    r"(?P<court>.+?) vom (?P<original_date>\d{2}\.\d{2}\.\d{4}) aufgehoben\.?,?",
    re.I,
)
_DE_BANKRUPTCY_PROCEEDINGS_SUSPENDED_NO_ASSETS = re.compile(
    r"Einstellung(?: des)? Konkursverfahren(?:s)? mangels Aktiven gemäss Verfügung vom "
    r"(?P<date>\d{2}\.\d{2}\.\d{4}) des (?P<authority>[^.]+)\.?",
    re.I,
)
_DE_BANKRUPTCY_DISSOLUTION = re.compile(
    r"Auflösung der Rechtseinheit durch Konkurs gemäss Konkurserkenntnis des "
    r"(?P<authority>.+?) vom (?P<decision_date>\d{2}\.\d{2}\.\d{4}) "
    r"mit Wirkung ab dem (?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<time>\d{1,2}[.:]\d{2}) Uhr\.?,?",
    re.I,
)
_DE_BANKRUPTCY_CLOSED_BY_DECISION = re.compile(
    r"Das Konkursverfahren ist mit Entscheid des (?P<authority>.+?) vom "
    r"(?P<date>\d{2}\.\d{2}\.\d{4}) als geschlossen erklärt worden\.?,?",
    re.I,
)
_DE_REMOVED_BANKRUPTCY_SUSPENSION = re.compile(
    r"\[gestrichen:\s*Das Konkursverfahren ist mit Verfügung des (?P<authority>.+?) "
    r"vom (?P<date>\d{2}\.\d{2}\.\d{4}) mangels Aktiven eingestellt worden\.\]\.?,?",
    re.I,
)
_DE_REMOVED_OWNER_BANKRUPTCY = re.compile(
    r"\[gestrichen:\s*Über den Inhaber dieses Einzelunternehmens ist mit Entscheid des "
    r"(?P<authority>.+?) vom (?P<decision_date>\d{2}\.\d{2}\.\d{4}) "
    r"mit Wirkung ab dem (?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<time>\d{1,2}:\d{2}) Uhr,\s*der Konkurs eröffnet worden\.\]\.?,?",
    re.I,
)
_DE_COMPOSITION_MORATORIUM_EXTENDED = re.compile(
    r"Mit Verfügung vom (?P<decision_date>\d{2}\.\d{2}\.\d{4}) des "
    r"(?P<authority>.+?) wurde eine Verlängerung der Nachlassstundung bis zum "
    r"(?P<until>\d{2}\.\d{2}\.\d{4}) gewährt\.?",
    re.I,
)
_DE_COMPOSITION_MORATORIUM_EXTENDED_ACTIVE = re.compile(
    r"Mit Verfügung vom (?P<decision_date>\d{2}\.\d{2}\.\d{4}) hat (?:der|die) "
    r"(?P<authority>.+?) die definitive Nachlassstundung um "
    r"(?P<duration>\d+|einen|sechs) Monate bis "
    r"(?P<until>\d{2}\.\d{2}\.\d{4}) verlängert\.?",
    re.I,
)
_DE_COMPOSITION_MORATORIUM_EXTENDED_UNTIL = re.compile(
    r"Mit Verfügung vom (?P<decision_date>\d{2}\.\d{2}\.\d{4}) hat (?:der|die) "
    r"(?P<authority>.+?) die definitive Nachlassstundung bis zum "
    r"(?P<until>\d{2}\.\d{2}\.\d{4}) verlängert\.?",
    re.I,
)
_DE_BANKRUPTCY_OPENED = re.compile(
    r"Mit Entscheid (?:der|des) (?P<authority>.+?) vom "
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}) ist über (?:diese|die) "
    r"(?P<entity>Gesellschaft|Rechtseinheit) der Konkurs mit Wirkung ab dem "
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<time>\d{1,2}[.:]\d{2}) Uhr,\s*eröffnet worden\.?",
    re.I,
)
_DE_COMPOSITION_MORATORIUM_GRANTED = re.compile(
    r"Mit Entscheid vom (?P<decision_date>\d{2}\.\d{2}\.\d{4}) wird der Gesellschaft "
    r"ab (?P<start_date>\d{2}\.\d{2}\.\d{4}) die definitive Nachlassstundung für die "
    r"Dauer von (?P<duration>\d+|einem|sechs) Monaten bis "
    r"(?P<until>\d{2}\.\d{2}\.\d{4}) gewährt und (?P<commissioner>.+?),\s*"
    r"c/o (?P<commissioner_org>.+?),\s*in (?P<commissioner_place>.+?),\s*"
    r"wird als definitiver Sachwalter bestätigt\.?",
    re.I,
)
_FR_COMPOSITION_MORATORIUM_EXTENDED = re.compile(
    r"Par prononcé rendu le (?P<decision_date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}),\s*"
    r"(?P<authority>.+?) a prolongé le sursis concordataire accordé à la société de "
    r"(?P<months>\d+) mois,\s*soit jusqu'au (?P<until>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})\.?",
    re.I,
)
_FR_COMPOSITION_MORATORIUM_GRANTED = re.compile(
    r"Selon jugement du (?P<authority>.+?) du "
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*octroi d['’]un sursis concordataire "
    r"jusqu['’]au (?P<until>\d{2}\.\d{2}\.\d{4})\.?",
    re.I,
)
_FR_COVID_MORATORIUM = re.compile(
    r"Par jugement du (?P<decision_date>\d{2}\.\d{2}\.\d{4}) du (?P<authority>.+?),\s*"
    r"un sursis COVID-19 pour une durée de (?P<months>\d+) mois,\s*soit jusqu'au "
    r"(?P<until>\d{2}\.\d{2}\.\d{4}) a été octroyé\.?",
    re.I,
)
_DE_COMPANY_EXTINGUISHED_AFTER_TAX_APPROVAL = re.compile(
    r"Die Zustimmungen der Steuerverwaltungen liegen vor\.\s*"
    r"Die Gesellschaft ist erloschen\.?",
    re.I,
)
_FR_DISSOLVED = re.compile(
    r"(?:La société est dissoute.{0,160}?\d{2}\.\d{2}\.\d{4}|"
    r"(?:Selon décision[^,]*,\s*)?la société a prononcé sa dissolution).?\.?",
    re.I,
)
_FR_FOUNDATION_DISSOLUTION = re.compile(
    r"L['’](?P<authority>Autorité de surveillance .+?) a constaté la dissolution "
    r"de la fondation par décision du (?P<date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})\.?,?",
    re.I,
)
_FR_DISSOLVED_LIQUIDATED_AND_DELETED = re.compile(
    r"(?:La société est dissoute\.\s*La liquidation étant terminée,\s*"
    r"la raison de commerce est radiée|"
    r"La liquidation de la société étant terminée,\s*"
    r"cette entité juridique est radiée)\.?,?",
    re.I,
)
_FR_FUSION = re.compile(
    r"Fusion:\s*reprise des actifs et(?: des)? passifs (?:de la société )?"
    r"(?P<name>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)(?P<rest>.+)",
    re.I | re.DOTALL,
)
_FR_ADDR_RADIEES = re.compile(
    r"(?:L'adresse|L'autre adresse|Les autres adresses):?\s*"
    r"(?P<addr>.+?)(?:,\s*)?(?:est|sont) radiée(?:s)?\.?",
    re.I,
)
_FR_PUBLICATION_ADDRESS_CORRECTION = re.compile(
    r"L['’]inscription no\s+(?P<number>\d+)\s+du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+est complétée dans le sens que "
    r"l['’]adresse suivante est aussi radiée:\s*(?P<address>[^.]+)\.?,?",
    re.I,
)
_FR_BANKRUPTCY_SCOPE_CORRECTION = re.compile(
    r"Rectificatif:\s*l['’]inscription n[°o]\s*(?P<number>[\d']+) du "
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s*"
    r"\(FOSC du (?P<publication_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"p\.\s*(?P<publication_page>\d+)\) est rectifiée en ce sens que "
    r"l['’]effet suspensif ne se rapporte qu['’]aux mesures d['’]exécution "
    r"et ne doit de ce fait pas être inscrit\.\s*La faillite subsiste comme "
    r"ci-devant \(FOSC du (?P<bankruptcy_publication_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"p\.\s*(?P<bankruptcy_page>\d+)/(?P<bankruptcy_reference>\d+)\)\.?,?",
    re.I,
)
_FR_NO_ADDRESS = re.compile(
    r"(?:(?:Nouvelle )?Adresse:\s*)?(?:La société\s+|L['’](?:entreprise(?: individuelle)?|association)\s+|il\s+)?n['’](?:y a|a) plus "
    r"(?:d'adresse|de domicile légal)"
    r"(?: (?:à son|au) siège(?: statutaire)?)?\.?",
    re.I,
)
_FR_ADDITIONAL_ADDRESS_REMOVED = re.compile(
    r"Autre adresse radiée:\s*(?P<address>[^.]+)\.?",
    re.I,
)
_FR_ADDITIONAL_ADDRESSES = re.compile(
    r"(?<!Les )(?:Nouvelles autres adresses|Autres adresses):\s*"
    r"(?P<addresses>[^.]+)\.?",
    re.I,
)
_FR_ADDRESS_REMOVED = re.compile(r"Nouvelle adresse:\s*\[biffé\]\.?", re.I)
_FR_NEW_ADDRESS = re.compile(
    r"Nouvelle adresse:(?!\s*\[biffé\])\s*(?P<address>[^.]+)\.?,?",
    re.I,
)
_DE_INHABER_CONTINUES = re.compile(
    r"(?:(?:(?:Der Inhaber führt sein|Die Inhaberin führt (?:ihr|sein)) Geschäft weiter|"
    r"Der Geschäftsbetrieb wird fortgeführt)[;,]\s*"
    r"die Eintragung bleibt bestehen|"
    r"Da (?:der Inhaber|die Inhaberin) (?:sein|ihr) Einzelunternehmen weiterführt,\s*"
    r"bleibt die Eintragung bestehen|"
    r"Da (?:der Inhaber|die Inhaberin) den Geschäftsbetrieb weiterführt,\s*"
    r"sind die Voraussetzungen für eine Löschung.{0,250}?nicht erfüllt\.\s*"
    r"Die Eintragung bleibt (?:folgede[n]?ssen\s+)?bestehen)"
    r"(?:\s*\(159a Abs\.\s*2 lit\.\s*b HRegV\))?\.?(?:\s*\[bisher:[^\]]+\])?",
    re.I | re.DOTALL,
)
_IT_OWNER_CONTINUES = re.compile(
    r"Il titolare continua la propria attività aziendale,\s*l['’]iscrizione sussiste\.?,?",
    re.I,
)
_FR_TITULAIRE_CONTINUES = re.compile(
    r"(?:Le titulaire continuant son activité,\s*l'inscription subsiste|"
    r"Le titulaire continue l'exploitation de son commerce\.\s*"
    r"L'inscription subsiste(?:\s*\(art\.\s*159\s+al\.\s*5\s+ORC\))?|"
    r"L'entreprise individuelle poursuit ses activités\.\s*L'inscription est maintenue)\.?",
    re.I | re.DOTALL,
)
_FR_BUSINESS_CEASED_DELETION = re.compile(
    r"(?:L'inscription|L'entreprise individuelle) est radiée par suite de "
    r"cessation (?:de l'exploitation|d['’]activité)\.?",
    re.I,
)
_FR_SUPERVISOR = re.compile(
    r"(?:Nouvelle autorité de surveillance|Nouvelle dénomination de l'autorité de surveillance|"
    r"Autorité de surveillance):\s*(?P<to>.+)",
    re.I,
)
_IT_SUPERVISOR = re.compile(
    r"Nuova autorità di vigilanza:\s*(?P<to>.+)",
    re.I,
)
_DE_QUALIFIED = re.compile(
    r"Qualifizierte Tatbestände neu:.+?(?=Mitteilungen neu:|Gemäss Erklärung|Ausgeschiedene|Eingetragene|$)",
    re.I | re.DOTALL,
)
_FR_CAPITAL_CLAUSE_INTRODUCED = re.compile(
    r"(?:Nouveaux faits qualifiés:\s*)?L['’]assemblée générale a introduit une clause statutaire "
    r"relative à une augmentation (?P<kind>autorisée|conditionnelle) du capital(?:-actions)? "
    r"par décision du (?P<date>\d{2}\.\d{2}\.\d{4})[.;]\s*"
    r"[Pp]our les détails,\s*voir les statuts\.?",
    re.I,
)
_FR_CAPITAL_CLAUSE_REMOVED = re.compile(
    r"(?:Nouveaux faits qualifiés:\s*)?Suppression de la clause statutaire "
    r"relative à l['’]augmentation (?P<kind>autorisée|conditionnelle) "
    r"du capital(?:-actions)?\s*\(fondée sur la décision d['’]autorisation du "
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\)\.?\s*"
    r"(?:\[précédemment:\s*.*?\]\.?\s*)?",
    re.I | re.DOTALL,
)
_FR_CONDITIONAL_PARTICIPATION_CAPITAL_CLAUSE_INTRODUCED = re.compile(
    r"L['’]assemblée générale a introduit une clause statutaire relative à la "
    r"création,\s*sous forme d['’]augmentation conditionnelle,\s*d['’]un "
    r"capital-participations par décision du (?P<date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"pour les détails,\s*voir les statuts\.?,?",
    re.I,
)
_DE_VINKULIERUNG = re.compile(
    r"Vinkulierung neu:\s*(?:\[[^\]]+\]|[^.]+)\.?",
    re.I,
)
_DE_DELETION_BLOCKED = re.compile(
    r"(?:Die (?:Gesellschaft|Genossenschaft) kann mangels Zustimmung(?:en)? "
    r"(?:der Eidgenössischen Steuerverwaltung(?: und des Kantonalen Steueramtes)?|"
    r"des Kantonalen Steueramtes|"
    r"der (?:kantonalen(?: und (?:der )?eidgenössischen)?|"
    r"eidgenössischen(?: und (?:der )?kantonalen)?) "
    r"Steuerverwaltung(?:en)?) noch nicht gelöscht werden|"
    r"Löschung aufgeschoben mangels Zustimmung(?:en)? der "
    r"(?:(?:eidg\.|kant\.)|eidg\.\s+und (?:der )?kant\.) Steuerverwaltung(?:en)?)\.?",
    re.I,
)
_DE_ART_934_INACTIVE_DELETION_BLOCKED = re.compile(
    r"Das Verfahren gemäss Art\.\s*934 OR wurde durchgeführt,\s*weil die "
    r"(?P<entity>Gesellschaft|Genossenschaft) keine Geschäftstätigkeit mehr aufweist"
    r"(?:,\s*|\s+und\s+)keine verwertbaren Aktiven mehr hat"
    r"(?:\s+und kein Interesse an der Aufrechterhaltung "
    r"der Eintragung innert angesetzter Frist geltend gemacht wurde|\.\s*Es wurde kein "
    r"Interesse an der Aufrechterhaltung der Eintragung innert angesetzter Frist geltend gemacht)\.\s*"
    r"Die (?P=entity) kann mangels Zustimmung(?:en)? der "
    r"(?:kantonalen(?: und (?:der )?eidgenössischen)?|"
    r"eidgenössischen(?: und (?:der )?kantonalen)?) "
    r"Steuerverwaltung(?:en)? noch nicht gelöscht werden\.?",
    re.I,
)
_DE_ART_934_CALLS_DELETION_BLOCKED = re.compile(
    r"Auf die durch das Handelsregisteramt gestützt auf Art\.\s*934 Abs\.\s*2 OR "
    r"sowie Art\.\s*152 Abs\.\s*1 HRegV veranlassten und im Schweiz\.\s*"
    r"Handelsamtsblatt Nrn?\.\s*(?P<issues>.+?) publizierten Aufforderungen haben sich "
    r"keine weiteren Betroffenen gemeldet\.\s*Das amtliche Verfahren zur Löschung "
    r"der Rechtseinheit ist damit abgeschlossen\.\s*Sie kann mangels Zustimmung(?:en)? "
    r"(?:der (?:Eidgenössischen Steuerverwaltung|Eidgenössischen und kantonalen Steuerverwaltung(?:en)?|kantonalen und (?:der )?eidgenössischen "
    r"Steuerverwaltung(?:en)?)|des kantonalen Steueramtes) (?:jedoch )?noch nicht gelöscht werden\.?",
    re.I | re.DOTALL,
)
_DE_ART_934_SHAB_NOTICE_DELETION_BLOCKED = re.compile(
    r"Auf die durch das Handelsregisteramt gestützt auf Art\.\s*934 Abs\.\s*2 OR "
    r"sowie Art\.\s*152 Abs\.\s*1 HRegV veranlassten und im SHAB mit Meldungsnummern "
    r"(?P<issues>.+?) publizierten Aufforderungen haben sich keine weiteren Betroffenen "
    r"gemeldet\.\s*Das amtliche Verfahren zur Löschung der Rechtseinheit ist damit "
    r"abgeschlossen\.\s*Sie kann mangels Zustimmung(?:en)? der Eidgenössischen "
    r"Steuerverwaltung(?: und des kantonalen Steueramtes)? jedoch noch nicht gelöscht werden\.?",
    re.I | re.DOTALL,
)
_DE_ART_934_OFFICIAL_PROCEDURE_DELETION_BLOCKED = re.compile(
    r"Das amtliche Verfahren zur Löschung der Rechtseinheit gemäss Art\.\s*934 OR "
    r"i\.V\.m\. Art\.\s*153 HRegV ist gemäss rechtskräftiger Verfügung vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}|\d{1,2}\.\s+"
    r"(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+\d{4}) "
    r"abgeschlossen\.\s*Die Rechtseinheit kann mangels Zustimmung der "
    r"eidgenössischen und kantonalen Steuerverwaltungen noch nicht gelöscht werden\.?",
    re.I,
)
_DE_ART_155_DELETION_BLOCKED = re.compile(
    r"Die Gesellschaft weist keine Geschäftstätigkeit mehr auf und hat keine verwertbaren Aktiven mehr\.\s*"
    r"Das Verfahren gemäss Art\. 155 HRegV wurde durchgeführt und es wurde kein Interesse an der "
    r"Aufrechterhaltung der Eintragung innert angesetzter Frist geltend gemacht\.\s*"
    r"Die Gesellschaft kann(?: aber)? mangels Zustimmung(?:en)? der "
    r"(?:kantonalen(?: und (?:der )?eidgenössischen)?|"
    r"eidgenössischen(?: und (?:der )?kantonalen)?) "
    r"Steuerverwaltung(?:en)? noch nicht gelöscht werden\.?",
    re.I,
)
_DE_ART_155_CALLS_COMPLETED = re.compile(
    r"Auf die durch das Handelsregisteramt gestützt auf Art\.\s*155 HRegV "
    r"(?:\([^)]*\)\s*)?veranlassten und im Schweiz\.\s*Handelsamtsblatt Nr\.\s*"
    r"(?P<issues>.+?) publizierten Rechnungsrufe haben sich keine "
    r"Gesellschafter/innen und Gläubiger/innen gemeldet\.\s*"
    r"Das amtliche Verfahren zur Löschung der Gesellschaft ist damit abgeschlossen\.?",
    re.I | re.DOTALL,
)
_DE_ART_155_CALLS_DELETION_BLOCKED = re.compile(
    r"Auf die durch das Handelsregisteramt gestützt auf Art\.\s*155 HRegV veranlassten und "
    r"Schweiz\.\s*Handelsamtsblatt \(SHAB\) vom .+? publizierten Rechnungsrufe wurde kein "
    r"Interesse an der Aufrechterhaltung der Eintragung geltend gemacht\.\s*"
    r"Das amtliche Verfahren zur Löschung der Gesellschaft ist damit abgeschlossen, weil die "
    r"Gesellschaft keine Geschäftstätigkeit mehr aufweist und keine verwertbaren Aktiven mehr hat\.\s*"
    r"Die Gesellschaft kann mangels Zustimmung der kant\.\s*Steuerverwaltung noch nicht gelöscht werden\.?",
    re.I | re.DOTALL,
)
_DE_ART_155_DATED_CALLS_DELETION_BLOCKED = re.compile(
    r"Auf die durch das Handelsregisteramt gestützt auf Art\.\s*155 HRegV veranlassten und "
    r"im Schweiz\.\s*Handelsamtsblatt \(SHAB\) vom (?P<dates>.+?) publizierten "
    r"Rechnungsrufe wurde kein Interesse an der Aufrechterhaltung der Eintragung geltend gemacht\.\s*"
    r"Das amtliche Verfahren zur Löschung der Gesellschaft ist damit abgeschlossen, weil die "
    r"Gesellschaft keine Geschäftstätigkeit mehr aufweist und keine verwertbaren Aktiven mehr hat\.\s*"
    r"Die Gesellschaft kann mangels Zustimmung der (?P<tax_authority>eidg\.|kant\.)\s*"
    r"Steuerverwaltung noch nicht gelöscht werden\.?",
    re.I | re.DOTALL,
)
_DE_ART_155_NUMBERED_CALLS_DELETION_BLOCKED = re.compile(
    r"Auf die durch das Handelsregisteramt gestützt auf Art\.\s*155 HRegV veranlassten und "
    r"im Schweiz\.\s*Handelsamtsblatt Nr\.\s*(?P<issues>[\d, und]+) publizierten "
    r"Rechnungsrufe haben sich keine Gesellschafter/innen und Gläubiger/innen gemeldet\.\s*"
    r"Das amtliche Verfahren zur Löschung der Gesellschaft ist damit abgeschlossen\.\s*"
    r"Die Gesellschaft kann mangels Zustimmung(?:en)? der .+? "
    r"Steuerverwaltung(?:en)? noch nicht gelöscht werden\.?",
    re.I | re.DOTALL,
)
_IT_DELETION_BLOCKED = re.compile(
    r"La società/la succursale deve essere cancellata a seguito della procedura di cui all'art\. 155 ORC\."
    r"\s*La cancellazione non può tuttavia essere effettuata mancando il consenso delle autorità fiscali"
    r" federali e cantonali\.?",
    re.I,
)
_IT_ART_155_DELETION_BLOCKED = re.compile(
    r"L'associazione deve essere cancellata a seguito della procedura di cui all'art\. 155 ORC\.\s*"
    r"La cancellazione non può tuttavia essere effettuata mancando il consenso delle autorità fiscali"
    r" federali e cantonali\.?",
    re.I,
)
_IT_OFFICE_DELETION_BLOCKED = re.compile(
    r"(?:L'associazione deve essere cancellata d'ufficio conformemente all'art\. 155 cpv\. 3 ORC,\s*"
    r"in quanto priva di attività economica e di attivi realizzabili\.\s*"
    r"La cancellazione non può tuttavia essere effettuata,?\s*mancando il consenso delle autorità "
    r"fiscali federali e cantonali|"
    r"In base l'applicazione dell'art\. 155 ORC.+?"
    r"La procedura di cancellazione d'ufficio della società è terminata,\s*ma la cancellazione "
    r"d'ufficio ai sensi dell'art\. 155 ORC della società non può ancora essere effettuata "
    r"mancando il consenso dell['’]\s*autorità fiscale federale)\.?",
    re.I | re.DOTALL,
)
_IT_ART_934_DELETION_BLOCKED = re.compile(
    r"L'associazione deve essere cancellata d'ufficio conformemente all'art\.\s*934 CO,\s*"
    r"in quanto priva di attività commerciale e di attivi\.\s*"
    r"La cancellazione non può tuttavia essere effettuata,?\s*mancando il consenso "
    r"delle autorità fiscali federali e cantonali\.?",
    re.I,
)
_IT_ART_155_CALLS_DELETION_BLOCKED = re.compile(
    r"In base l'applicazione dell'art\. 155 ORC.+?nessun interesse al mantenimento "
    r"dell'iscrizione della società è stato notificato\.\s*"
    r"La procedura di cancellazione d'ufficio della società è terminata,\s*"
    r"ma la cancellazione della società non può essere effettuata mancando il consenso "
    r"delle autorità fiscali federali e cantonali\.?",
    re.I | re.DOTALL,
)
_IT_SUPPRESSED_DELETION_BLOCKED = re.compile(
    r"La fondazione è dichiarata soppressa.+?ma la cancellazione non può essere effettuata "
    r"mancando il consenso (?:dell'autorità fiscale cantonale|delle autorità fiscali federali e cantonali)\.?",
    re.I | re.DOTALL,
)
_IT_FOUNDATION_SUPPRESSED_DELETION_BLOCKED = re.compile(
    r"Mediante decisione della (?P<authority>.+?),\s*"
    r"(?P<authority_place>[^,(]+)\s*\((?P<authority_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"del (?P<date>\d{2}\.\d{2}\.\d{4}),\s*la fondazione è stata soppressa\.\s*"
    r"La cancellazione non può tuttavia essere effettuata mancando il consenso "
    r"delle autorità fiscali federali e cantonali\.?,?",
    re.I,
)
_IT_ART_748_DELETION_BLOCKED = re.compile(
    r"Le prescrizioni (?:(?:secondo il previgente art\. 748 CO sono state ottemperate,\s*"
    r"i creditori sono stati tacitati o garantiti,\s*ma la)|(?:dell['’]art\. 748 CO diritto "
    r"previgente sono ottemperate\.\s*La)) cancellazione non può essere effettuata "
    r"mancando il consenso delle autorità fiscali federali e cantonali\.?",
    re.I,
)
_IT_BRANCH_DELETION_BLOCKED = re.compile(
    r"(?:,\s*)?Sede principale a:\s*(?:Sede principale:\s*)?(?P<head_office>[^.]+)\.\s*"
    r"(?:Nuove osservazioni della sede principale|Nuove disposizioni per la succursale):\s*"
    r"(?:(?:La società|Lo stabilimento principale) ha deciso la soppressione della succursale|"
    r"La succursale è soppressa a seguito della radiazione dello stabilimento principale "
    r"e trasferimento dello stesso in Svizzera),?\s*"
    r"ma la cancellazione non può essere effettuata "
    r"mancando il consenso delle autorità fiscali federali e cantonali\.?",
    re.I,
)
_IT_NO_DOMICILE = re.compile(
    r"Nuovo recapito:\s*La società (?:è priva di|non ha più un) domicilio legale\.?",
    re.I,
)
_DE_ADDITIONAL_ADDRESS = re.compile(
    r"(?<!gestrichen: )(?<!bisher: )Weitere Adresse(?:n)?:\s*"
    r"(?P<address>[^.]+(?:\.(?=-)[^.]+)*)\.?",
    re.I,
)
_DE_ADDITIONAL_ADDRESS_REMOVED = re.compile(
    r"(?<!Zweigniederlassung neu: )"
    r"\[gestrichen:\s*Weitere Adresse:\s*(?P<address>[^\]]+?)\.?\]\.?,?",
    re.I,
)
_DE_BRANCH_REMOVED = re.compile(
    r"(?:Angaben zur )?Zweigniederlassung neu:\s*"
    r"(?:\[Folgende Zweigniederlassungen sind aufgehoben worden:\]\s*)?"
    r"\[gestrichen:\s*(?P<place>[^\](]+?)"
    r"(?:\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\))?"
    r"(?:,\s*\(HR\s+(?P<register_canton>[A-Z]{2})\))?\]\.?",
    re.I,
)
_DE_BRANCH_REMOVED_CONTINUATION = re.compile(
    r"\[gestrichen:\s*(?P<place>[^\](]+?)"
    r"(?:\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\))?"
    r"(?:,?\s*\(HR\s+(?P<register_canton>[A-Z]{2})\))?\]\.?",
    re.I,
)
_DE_BRANCH_REPLACED_LEGACY = re.compile(
    r"Zweigniederlassung neu:\s*\[gestrichen:\s*(?P<from_place>[^\](]+?)\s*"
    r"\((?P<from_registry_id>CH-[\d.]+-\d)\)\]\.\s*"
    r"(?P<to_place>[^(.]+?)\s*\((?P<to_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?,?",
    re.I,
)
_DE_BRANCH_ADDED = re.compile(
    r"Zweigniederlassung neu:"
    r"(?!\s*\[Folgende Zweigniederlassungen sind aufgehoben worden:\])\s*"
    r"(?:\[Sitz\]\s*)?(?P<place>.+?)\s*"
    r"(?:\((?P<place_canton>[A-Z]{2})\)\s*)?"
    r"(?:\(HR\s+(?P<leading_register_canton>[A-Z]{2})\)\s*)?"
    r"\(+(?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)"
    r"(?:\s*,?\s*\(?HR\s+(?P<register_canton>Basel-Stadt|Basel-Landschaft|[A-Z]{2})\)?)?\.?",
    re.I,
)
_DE_BRANCH_ADDED_CONTINUATION = re.compile(
    r"^\s*(?P<place>(?:St\.\s*)?[^(.]+?)\s*(?:\((?P<place_canton>[A-Z]{2})\)\s*)?"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?,?",
    re.I,
)
_DE_BRANCH_ADDED_AFTER_REMOVAL = re.compile(
    r"(?:^|\.\s*)(?P<place>[^(.]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?,?",
    re.I,
)
_DE_BRANCH_SEAT_CHANGED = re.compile(
    r"Zweigniederlassung neu:\s*(?:\[Sitz neu:\]\s*)?(?P<to>[^()]+?)\s*"
    r"(?:\((?P<place_canton>[A-Z]{2})\)\s*)?"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)"
    r"(?:\s*\(?HR\s+(?P<register_canton>[A-Z]{2})"
    r"(?:\s+(?P<register_section>[^\[\]()]+?))?\)?)?\s*"
    r"\[bisher:\s*(?P<from>[^()]+?)\s*"
    r"\((?P<previous_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s*,?\s*"
    r"\(?HR\s+(?P<previous_register_canton>[A-Z]{2})"
    r"(?:\s+(?P<previous_register_section>[^\]()]+?))?\)?\]\.?",
    re.I,
)
_DE_BRANCH_SIMPLE_SEAT_CHANGED = re.compile(
    r"Zweigniederlassung neu:\s*(?P<to>(?:St\.\s*)?[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s*"
    r"\[bisher:\s*(?P<from>(?:St\.\s*)?[^()]+?)\s*"
    r"\((?P<previous_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\]\.?",
    re.I,
)
_DE_BRANCH_TRANSFERRED_BY_MERGER = re.compile(
    r"Angaben zur Zweigniederlassung neu:\s*Übergang dieser Zweigniederlassung "
    r"infolge Fusion gemäss Art\.\s*112 HRegV\.?,?",
    re.I,
)
_IT_BRANCH_REMOVED = re.compile(
    r"Nuova succursale:\s*\[radiati:\s*(?P<place>[^\]]+)\]\.?",
    re.I,
)
_IT_BRANCH_ADDED = re.compile(
    r"Nuova succursale:\s*(?P<place>(?:St\.\s*)?[^(.]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?,?",
    re.I,
)
_FR_BRANCH_REMOVED = re.compile(
    r"La succursale de\s+(?P<place>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+est radiée\.?",
    re.I,
)
_FR_BRANCH_REMOVED_LEGACY = re.compile(
    r"Nouvelle succursale:\s*\[biffé:\s*(?P<place>[^\]]+)\]\.?,?",
    re.I,
)
_DE_BELEGE = re.compile(
    r"(?:Berichtigte Liste der Belege|Nachtrag der Liste der Belege|"
    r"(?:Die )?Liste der (?:Eintragungs)?belege wurde "
    r"(?:berichtigt|ergänzt|nachgetragen|nachgeführt|korrigiert|bereinigt))\.?",
    re.I,
)
_DE_PARTICIPATION_CERTIFICATES_REMOVED = re.compile(
    r"Genussscheine neu:\s*\[Die Genussscheine sind aufgehoben worden\.\]\s*"
    r"\[gestrichen:\s*(?P<count>[\d']+) Genussscheine,\s*"
    r"(?P<rights>[^\]]+)\]\.?,?",
    re.I,
)
_DE_BANKRUPTCY_ADMINISTRATION_REPLACED = re.compile(
    r"(?P<authority>Der Einzelrichter .+?) hat mit Entscheid vom "
    r"(?P<date>\d{2}\.\d{2}\.\d{4}) die (?P<from_name>.+?) als "
    r"ausseramtliche Konkursverwaltung abgesetzt\.\s*Als neue ausseramtliche "
    r"Konkursverwalterin wird die (?P<to_name>.+?) "
    r"\((?P<to_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"(?P<to_address>[^.]+),\s*eingesetzt\.?,?",
    re.I,
)
_DE_ANCILLARY_RIGHTS = re.compile(
    r"(?<!nicht: )(?:Nebenleistungspflichten(?:,\s*Vorhand-,\s*Vorkaufs- oder Kauf(?:s)?rechte)?|Nachschusspflichten)"
    r"\s*:?\s*gemäss näherer Umschreibung in den Statuten\.?",
    re.I,
)
_FR_ANCILLARY_OBLIGATIONS = re.compile(
    r"Obligation de fournir des prestations(?: accessoires,\s*droits de préférence,\s*"
    r"de préemption ou d['’]emption:\s*pour les détails,\s*voir les statuts|"
    r"\s*\(pour les détails, voir les statuts\))\.?",
    re.I,
)
_FR_ANCILLARY_OBLIGATIONS_NEGATED = re.compile(
    r"\[non:\s*Obligations?:\s*Obligations? de fournir des prestations accessoires,\s*"
    r"droits de préférence,\s*de préemption ou d['’]emption:\s*"
    r"pour les détails,\s*voir les statuts\.\]",
    re.I,
)
_FR_ANCILLARY_OBLIGATIONS_REMOVED = re.compile(
    r"\[biffé:\s*Obligations? de fournir des prestations accessoires,\s*"
    r"droits de préférence,\s*de préemption ou d['’]emption:\s*"
    r"pour les détails,\s*voir les statuts\]\.?",
    re.I,
)
_FR_CONTRIBUTION_RULES_REMOVED = re.compile(
    r"La clause statutaire relative à "
    r"(?:l['’]apport en nature(?: et à la reprise de biens)?(?: effectué)?|"
    r"la reprise de biens envisagée) à la constitution est (?:supprimée|abrogée) "
    r"conformément à l['’]art\.\s*628,?\s*al\.\s*4,?\s*CO\.?",
    re.I,
)
_DE_ANCILLARY_RIGHTS_REMOVED = re.compile(
    r"\[Die Bestimmung über die Nebenleistungspflichten ist aufgehoben\.\]"
    r"(?:\s*\[nicht:\s*Pflichten:[^\]]*\])?",
    re.I,
)
_IT_ANCILLARY_OBLIGATIONS = re.compile(
    r"(?:Prestazioni accessorie a norma di statuto|"
    r"Obblighi di fornire prestazioni accessorie,\s*diritti preferenziali,\s*"
    r"di prelazione o di compera:\s*per i dettagli si rinvia allo statuto)\.?",
    re.I,
)
_DE_FALSE_DISSOLUTION = re.compile(
    r"\[nicht:\s*Die Gesellschaft ist mit Beschluss der "
    r"(?:Generalversammlung|Gesellschafterversammlung) vom aufgelöst\.\]",
    re.I,
)
_DE_TRANSLATIONS = re.compile(
    r"Uebersetzungen (?:der Firma|des Namens) neu:\s*"
    r"(?:(?:\([^)]*\)|\[[^\]]+\])\s*)+\.?,?",
    re.I,
)
_IT_TRANSLATIONS_REMOVAL_ANNOUNCED = re.compile(
    r"Nuove traduzioni della ditta:\s*"
    r"\[Le traduzioni saranno radiate dal Registro di commercio\]\.?,?",
    re.I,
)
_DE_FORMER_TRANSLATIONS_REMOVED = re.compile(
    r"Die Übersetzungen der ehemaligen Firma wurden anlässlich der "
    r"Firmaänderung aufgehoben\.?,?",
    re.I,
)
_DE_HEAD_OFFICE_NAME = re.compile(
    r"Firma Hauptsitz neu:\s*(?P<to>.+?)\s*"
    r"\[bisher:\s*(?:Firma Hauptsitz:\s*)?(?P<from>[^\]]+)\]\.?,?",
    re.I,
)
_DE_HEAD_OFFICE_NAME_DIRECT = re.compile(
    r"Neue Firma des Hauptsitzes:\s*(?P<to>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?,?",
    re.I,
)
_DE_HEAD_OFFICE_LEGAL_FORM = re.compile(
    r"Rechtsform Hauptsitz neu:\s*(?P<to>.+?)\s*"
    r"\[bisher:\s*(?:Rechtsform Hauptsitz:\s*)?(?P<from>[^\]]+)\]\.?,?",
    re.I,
)
_DE_HEAD_OFFICE_LEGAL_FORM_DIRECT = re.compile(
    r"Rechtsform Hauptsitz neu:\s*(?P<to>[^.\[]+)\.?,?",
    re.I,
)
_DE_HEAD_OFFICE_CONTEXT = re.compile(
    r"(?:,\s*)?Hauptsitz in:\s*"
    r"(?P<seat>(?:St\.\s*[^.]+|[^.]+?-St\.\s*[^.]+|[^.]+))\.?",
    re.I,
)
_DE_HEAD_OFFICE_CAPITAL = re.compile(
    r"Kapital Hauptsitz neu:\s*(?P<currency>[A-Z]{3})\s+(?P<to>[\d'.]+),\s*"
    r"(?P<to_paid>voll liberiert)\s*\[bisher:\s*Kapital Hauptsitz:\s*"
    r"(?P<from_currency>[A-Z]{3})\s+(?P<from>[\d'.]+),\s*"
    r"(?P<from_paid>voll liberiert)\]\.?",
    re.I,
)
_DE_HEAD_OFFICE_BANKRUPTCY_SUSPENDED = re.compile(
    r"Bemerkungen zum Hauptsitz neu:\s*Das Konkursverfahren ist mit Entscheid "
    r"des zuständigen Einzelgerichts vom (?P<date>\d{2}\.\d{2}\.\d{4}) "
    r"mangels Aktiven eingestellt worden\.?",
    re.I,
)
_DE_BRANCH_CLOSED_PENDING = re.compile(
    r"Angaben zur Zweigniederlassung neu:\s*Die Zweigniederlassung ist aufgehoben\.\s*"
    r"\[Die Löschung erfolgt sobald die Zustimmungen? der Steuerverwaltung vorliegen\.\]\.?",
    re.I,
)
_DE_HEAD_OFFICE_REGISTRATION = re.compile(
    r"Registrierung Hauptsitz neu:\s*(?P<to>[^.]+)\.?,?",
    re.I,
)
_DE_NEW_HEAD_OFFICE = re.compile(
    r"Neuer Hauptsitz:\s*(?P<to>[^.]+)\.?,?",
    re.I,
)
_DE_STATUTE_EXTRAS = [
    re.compile(
        r"Mitteilungen neu:.+?(?=Gemäss Erklärung|(?:Ausgeschiedene|Eingetragene) Personen|$)",
        re.I | re.DOTALL,
    ),
    re.compile(r"Gemäss Erklärung vom \d{2}\.\d{2}\.\d{4} erfüllt die Gesellschaft die Voraussetzungen für den Verzicht auf die eingeschränkte Revision\.?", re.I),
    re.compile(r"\[Mit Statutenänderung vom \d{2}\.\d{2}\.\d{4}[^\]]*\]", re.I),
    _DE_TRANSLATIONS,
]
_IT_NO_AUDITOR = re.compile(
    r"\[la società è attualmente priva di un organo di revisione[^\]]*\]",
    re.I,
)
_FR_LIQ_OPEREE = re.compile(
    r"(?:Sa|La) liquidation est opérée sous (?:la raison (?:sociale|de commerce)|le nom):?\s*"
    r".+?,?\s+en liquidation(?:\s+\[[^\]]+\])*\.?(?=\s|$)",
    re.I,
)
_DE_LIQ_ENDED = re.compile(
    r"(?<!gestrichen: )(?:Liquidation beendet|Die Liquidation ist (?:beendet|durchgeführt))\.?"
    r"(?:\s+Die Bestätigung.+?liegt vor\.)?"
    r"(?:\s+\[[^\]]+\])?",
    re.I | re.DOTALL,
)
_IT_LIQ_ENDED = re.compile(
    r"(?:Secondo gli interessati la liquidazione è terminata|La liquidazione è terminata(?:\.|,)\s*"
    r"[Mm]a la cancellazione(?: della società)? non può(?: ancora)? essere effettuata(?:\s+mancando il consenso dell['’])?|"
    r"La società deve essere cancellata).*?"
    r"autorità fiscal[ei](?: federali e cantonali| federale e cantonale| federale| cantonale)?\.?",
    re.I | re.DOTALL,
)
_DE_FUSION = re.compile(
    r"Fusion:\s*(?:Die Gesellschaft übernimmt|Übernahme der Aktiven und "
    r"(?:Passiven|des Fremdkapitals) der)\s+"
    r"(?P<name>.+?)"
    r"(?:,\s*in\s+(?P<place>[^(]+))?"
    r"\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)(?P<rest>.+)",
    re.I | re.DOTALL,
)
_IT_CROSS_BORDER_FUSION = re.compile(
    r"Fusione transfrontaliera secondo gli articoli (?P<legal_basis>[^:]+):\s*"
    r"ripresa di attivi e passivi della società a responsabilità limitata di diritto italiano "
    r"[\"“](?P<name>.+?)[\"”],\s*in (?P<place>[^()]+)\s*\((?P<country>[A-Z]{2})\)\s*"
    r"\(Nr\.\s*(?P<registry_id>[^)]+)\),\s*secondo il contratto di fusione del "
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4}) e bilancio al "
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta attivi per "
    r"(?P<currency>[A-Z]{3})\s+(?P<assets>[\d'.]+),.+?passivi verso terzi per "
    r"(?P=currency)\s+(?P<liabilities>[\d'.]+)\.\s*La fusione avviene senza aumento "
    r"di capitale.+?(?:\s*\[non come erroneamente indicato:\s*[^\]]+\])?\.?(?=\s*$)",
    re.I | re.DOTALL,
)
_DE_PARTNERSHIP_AGREEMENT_CHANGED = re.compile(
    r"Änderung Gesellschaftsvertrag:\s*(?P<date>\d{2}\.\d{2}\.\d{4})\.?,?",
    re.I,
)
_DE_AUTH_CAPITAL = re.compile(
    r"(?:Die Gesellschaft hat|Die Generalversammlung hat) mit Beschluss vom "
    r"(?P<date>\d{2}\.\d{2}\.\d{4}) eine genehmigte Kapitalerhöhung"
    r"(?:[^.]|Art\.)*?(?:beschlossen|eingeführt)\.?(?:\s+\[bisher:[^\]]+\])?",
    re.I,
)
_DE_AUTHORIZED_CAPITAL_CLAUSE_EXPIRED = re.compile(
    r"\[Streichung der Statutenbestimmung über die mit Ermächtigungsbeschluss vom "
    r"(?P<date>\d{2}\.\d{2}\.\d{4}) eingeführte genehmigte Kapitalerhöhung "
    r"infolge der zeitlichen Befristung\]"
    r"(?:\s*\[gestrichen:\s*Die Gesellschaft hat mit Beschluss vom "
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4}) eine genehmigte Kapitalerhöhung "
    r"gemäss näherer Umschreibung in den Statuten beschlossen\.\])?\.?,?",
    re.I,
)
_IT_CONDITIONAL_CAPITAL_CLAUSE_INTRODUCED = re.compile(
    r"L['’]assemblea generale ha introdotto una disposizione statutaria relativa "
    r"all['’]aumento condizionale del capitale azionario mediante decisione del "
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.\s*Per i dettagli vedi statuti\.?",
    re.I,
)
_DE_AUTH_CAPITAL_MODIFIED = re.compile(
    r"Die Gesellschaft hat mit Beschluss vom (?P<date>\d{2}\.\d{2}\.\d{4}) die mit "
    r"Ermächtigungsbeschluss vom (?P<original_date>\d{2}\.\d{2}\.\d{4}) eingeführte "
    r"genehmigte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten geändert\."
    r"(?:\s*\[bisher:\s*(?P<previous>[^\]]+)\])?\.?,?",
    re.I,
)
_DE_CONDITIONAL_CAPITAL = re.compile(
    r"Die (?:Generalversammlung|Gesellschaft) hat mit Beschluss vom "
    r"(?P<date>\d{2}\.\d{2}\.\d{4}) eine bedingte Kapitalerhöhung gemäss näherer "
    r"Umschreibung in den Statuten (?:eingeführt|beschlossen)\.?",
    re.I,
)
_DE_CONDITIONAL_CAPITAL_MODIFIED = re.compile(
    r"Die Gesellschaft hat mit Beschluss vom (?P<date>\d{2}\.\d{2}\.\d{4}) die mit "
    r"Beschluss vom (?P<original_date>\d{2}\.\d{2}\.\d{4}) eingeführte Bestimmung "
    r"betreffend bedingter Kapitalerhöhung gemäss näherer Umschreibung in den Statuten "
    r"geändert\.\s*\[bisher:\s*(?P<previous>[^\]]+)\]\.?",
    re.I,
)
_DE_HEAD_OFFICE_STATUTES = re.compile(
    r"Statuten Hauptsitz neu:\s*(?P<date>\d{2}\.\d{2}\.\d{4})\.?",
    re.I,
)
_HAUPTSITZ = re.compile(
    r"(?:,\s*)?Hauptsitz in:\s*(?P<old>[^.]+?)\.\s*Hauptsitz neu:\s*(?P<to>[^\[]+)"
    r"(?:\s*\[bisher:\s*(?P<from>[^\]]+)\])?\.?",
    re.I,
)
_HAUPTSITZ_NEU = re.compile(
    r"(?<!Firma )(?<!Rechtsform )(?<!Registrierung )(?<!Kapital )(?<!Statuten )(?<!zum )"
    r"(?<!Tatbestände )Hauptsitz neu:\s*(?P<to>[^\[]+)"
    r"(?:\s*\[bisher:\s*(?P<from>[^\]]+)\])?\.?,?",
    re.I,
)
_HAUPTSITZ_IDENTIFIER = re.compile(
    r"(?:,\s*)?Hauptsitz in:\s*(?P<seat>[^.]+)\.\s*"
    r"Neue Identifikationsnummer Hauptsitz:\s*(?P<to>CHE-\d{3}\.\d{3}\.\d{3})\s*"
    r"\[bisher:\s*Identifikationsnummer Hauptsitz:\s*(?P<from>CH-[\d.]+-\d)\]\. ?",
    re.I,
)
_HAUPTSITZ_IDENTIFIER_ONLY = re.compile(
    r"Neue Identifikationsnummer Hauptsitz:\s*(?P<to>CHE-\d{3}\.\d{3}\.\d{3})"
    r"(?:\s*\[bisher:\s*(?:Identifikationsnummer Hauptsitz:\s*)?"
    r"(?P<from>CH-[\d.]+-\d|CHE-\d{3}\.\d{3}\.\d{3})\])?\.?",
    re.I,
)
_DE_COMPANY_IDENTIFIER = re.compile(
    r"UID neu:\s*(?P<to>CHE-\d{3}\.\d{3}\.\d{3})\s*"
    r"\[bisher:\s*(?P<from>CHE-\d{3}\.\d{3}\.\d{3})\]\.?",
    re.I,
)
_DE_HEAD_OFFICE_MUNICIPALITY_NOTE = re.compile(
    r"Bemerkungen zum Hauptsitz neu:\s*\[Sitzänderung des Hauptsitzes von Amtes wegen "
    r"infolge Gemeindefusion\.\]\.?",
    re.I,
)
_DE_HEAD_OFFICE_BRANCH_CONTINUED_AFTER_SPINOFF = re.compile(
    r"Bemerkungen zum Hauptsitz neu:\s*Die Zweigniederlassung wird infolge Abspaltung "
    r"der (?P<previous_head_office>.+?)\s*\(neu:\s*(?P<renamed_head_office>.+?)\) "
    r"als Zweigniederlassung der neu gegründeten (?P<new_head_office>.+?) weitergeführt\.?,?",
    re.I,
)
_DE_HEAD_OFFICE_BRANCH_CONTINUED_AFTER_MERGER = re.compile(
    r"Bemerkungen zum Hauptsitz neu:\s*Infolge Fusion der "
    r"(?P<previous_head_office>.+?),\s*in\s+(?P<previous_place>[^()]+)\s*"
    r"\((?P<previous_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*mit der "
    r"(?P<absorbing_head_office>.+?)\s*\(neu:\s*(?P<head_office>.+?)\),\s*"
    r"in\s+(?P<head_office_place>[^()]+)\s*"
    r"\((?P<head_office_uid>CHE-\d{3}\.\d{3}\.\d{3})\) wird die Zweigniederlassung "
    r"gemäss Art\.\s*112 HRegV als Zweigniederlassung der "
    r"(?P<continued_as>.+?) weitergeführt\.?,?",
    re.I,
)
_DE_HEAD_OFFICE_BRANCH_CONTINUED_AFTER_ASSET_TRANSFER = re.compile(
    r"Qualifizierte Tatbestände Hauptsitz neu:\s*Die Firma des Hauptsitzes hat auf "
    r"(?P<renamed_head_office>.+?) umfirmiert und infolge Vermögensübertragung auf die "
    r"neu gegründete (?P<new_head_office>.+?),\s*in\s+(?P<head_office_place>[^()]+)\s*"
    r"\((?P<head_office_uid>CHE-\d{3}\.\d{3}\.\d{3})\) wird die Zweigniederlassung "
    r"gemäss Art\.\s*112 HRegV als Zweigniederlassung der neuen "
    r"(?P<continued_as>.+?) weitergeführt\.?",
    re.I,
)
_FR_HEAD_OFFICE_IDENTIFIER = re.compile(
    r"(?:,\s*)?Siège principal à:\s*(?P<seat>[^.]+)\.\s*"
    r"Nouveau numéro d'identification du siège principal:\s*"
    r"(?P<to>CHE-\d{3}\.\d{3}\.\d{3})\s*"
    r"\[précédemment:\s*Numéro d'identification du siège principal:\s*"
    r"(?P<from>CH-[\d.]+-\d)\]\.?,?",
    re.I,
)
_FR_HEAD_OFFICE_IDENTIFIER_ONLY = re.compile(
    r"Nouveau numéro d'identification du siège principal:\s*"
    r"(?P<to>CHE-\d{3}\.\d{3}\.\d{3})\s*"
    r"\[précédemment:\s*Numéro d'identification du siège principal:\s*"
    r"\(?(?P<from>CH-[\d.]+-\d)\)?\]\.?,?",
    re.I,
)
_FR_HEAD_OFFICE_SEAT_REGISTERED = re.compile(
    r"Nouveau siège de l'établissement principal inscrit au registre du commerce "
    r"du canton de (?P<register_canton>[^:]+?) sous le numéro d'identification "
    r"\(IDE/UID\)\s*(?P<uid>CHE-\d{3}\.\d{3}\.\d{3}):\s*"
    r"(?P<to>[^.]+)\.?,?",
    re.I,
)
_FR_HEAD_OFFICE_SEAT = re.compile(
    r"Nouveau siège de l'établissement principal:\s*(?P<to>[^.]+)\.?",
    re.I,
)
_IT_COMPANY_IDENTIFIER = re.compile(
    r"Nuova IDE:\s*(?P<to>CHE-\d{3}\.\d{3}\.\d{3})\s*"
    r"\[finora:\s*(?P<from>CHE-\d{3}\.\d{3}\.\d{3})\]\.?,?",
    re.I,
)
_FR_COMPANY_IDENTIFIER_CORRECTED = re.compile(
    r"Le numéro IDE/UID (?P<from>CHE-\d{3}\.\d{3}\.\d{3}) étant erroné,\s*"
    r"(?:il\s+)?est remplacé par le numéro IDE/UID "
    r"(?P<to>CHE-\d{3}\.\d{3}\.\d{3})\.?,?",
    re.I,
)
_LIQ_ADDRESS = re.compile(
    r"(?:Nouvelle\s+)?adresse de liquidation:\s*"
    r"(?P<addr>(?:(?:Lic\.iur|\b[A-Z]\.)|[^.])+)\.?",
    re.I,
)
_DE_SUPERVISOR = re.compile(r"Aufsichtsbehörde(?: neu)?:\s*(?P<to>.+)", re.I)
_DOMIZIL_NEU = re.compile(r"Domizil neu:\s*(?P<to>[^.]+)\.?", re.I)
_DE_ORGANIZATION_REMOVED = re.compile(
    r"Organisation neu:\s*\[(?:(?:Löschung|Gestrichene Angaben (?:über die|zur) Organisation) "
    r"aufgrund geänderter Eintragungsvorschriften gemäss Art\. 95(?: Abs\. 1)? HRegV\.?|"
    r"Organisation gestrichen gemäss Art\. 95 Abs\. 1 lit\. h\. HRegV|"
    r"gestrichen aufgrund geänderter Eintragungsvorschriften|"
    r"Die bisher im Handelsregister eingetragene Bemerkung über die Organisation wird gelöscht\.)\]\.?",
    re.I,
)
_DE_ASSOCIATION_ORGANIZATION_REMOVED = re.compile(
    r"Organisation neu:\s*\[Organisation gestrichen gemäss "
    r"(?P<law>Art\.\s*92 lit\.\s*j\.\s*HRegV)\]\.?",
    re.I,
)
_DE_LIABILITY_CLAUSE_REMOVED = re.compile(
    r"Haftung/Nachschusspflicht neu:\s*"
    r"\[Streichung des Eintrags aufgrund geänderter Eintragungsvorschriften\.\]\s*"
    r"\[gestrichen:\s*Haftung/Nachschusspflicht:\s*(?P<previous>[^\]]+)\]\.?",
    re.I,
)
_IT_ORGANIZATION_REMOVED = re.compile(
    r"Nuova organizzazione:\s*\[L'indicazione relativa all'organizzazione è cancellata "
    r"a seguito dell'abrogazione della disposizione di cui all'art\.\s*95 cpv\.\s*1 "
    r"lett\.\s*h ORC\.\]\.?",
    re.I,
)
_IT_OBSOLETE_CORPORATION_INDICATIONS_REMOVED = re.compile(
    r"\[La seguente indicazione è radiata in quanto non prevista quale iscrizione nel "
    r"registro di commercio delle società anonime secondo l'art\.\s*45 ORC\.\]\s*"
    r"\[radiati:\s*Statuti adattati al nuovo diritto azionario\.\]\.?,?",
    re.I,
)
_FR_BOARD_COMPOSITION_REMOVED = re.compile(
    r"La mention relative à la composition du conseil n'étant plus soumise à inscription,\s*"
    r"elle est radiée d'office\.?",
    re.I,
)
_FR_ORGANIZATION_REMOVED = re.compile(
    r"(?:Radiation de la mention relative à l['’]organisation"
    r"(?:,\s*plus soumise à inscription)?|"
    r"La mention relative à l['’]organisation de la fondation est radiée,\s*"
    r"celle-ci n['’]étant plus obligatoire)\.?,?",
    re.I,
)
_DE_CORRECTION_HEADER = re.compile(
    r"^(?:Nachtrag zum|Berichtigung des) im SHAB (?P<issue>.+?) publizierten TR-Eintrag(?:s)? Nr\.\s*"
    r"(?P<entry>[\d']+) vom (?P<date>\d{2}\.\d{2}\.\d{4})\.?\s*",
    re.I,
)
_DE_CORRECTION_HEADER_ALT = re.compile(
    r"^Berichtigung des im SHAB vom (?P<issue>\d{2}\.\d{2}\.\d{4}),\s*"
    r"Meldungs Nr\. [\d']+,\s*publizierten Tagesregistereintrages Nr\.\s*"
    r"(?P<entry>[\d']+) vom (?P<date>\d{2}\.\d{2}\.\d{4})\.?\s*",
    re.I,
)
_DE_NEGATED_FUSION_CORRECTION = re.compile(
    r"\[nicht:\s*Fusion:.*?\]\.?",
    re.I | re.DOTALL,
)
_IT_CORRECTION_HEADER = re.compile(
    r"^(?:Rettifica|Complemento) (?:dell|all)['’]iscrizione del registro giornaliero no\.\s*"
    r"(?P<entry>[\d']+) del (?P<date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"pubblicat[oa] (?:sul|nel) FUSC (?P<issue>no\.\s*\d+(?:\s+del)?\s+\d{2}\.\d{2}\.\d{4})\.?\s*",
    re.I,
)
_DE_AUDIT_WAIVER_REVOKED = re.compile(
    r"\[(?:Der Verzicht auf eine eingeschränkte Revision wurde aufgehoben|"
    r"Streichung der Bemerkung betreffend Verzicht auf eine eingeschränkte Revision "
    r"infolge Wahl einer Revisionsstelle)\.\]",
    re.I,
)
_DE_AUDIT_WAIVER_CORRECTED = re.compile(
    r"\[Die Gesellschaft hat keinen Verzicht auf eine eingeschränkte Revision erklärt\.\s*"
    r"Der entsprechende Eintrag erfolgte irrtümlich\.\]",
    re.I,
)
_DE_AUDIT_WAIVER = re.compile(
    r"(?<!nicht: )(?:(?:Die Gesellschaft hat )?Mit|Gemäss) (?:Geschäftsführungs)?Erklärung(?: des Verwaltungsrates)? vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+(?:"
    r"(?:wurde )?auf die eingeschränkte Revision verzichtet|"
    r"untersteht die Gesellschaft keiner ordentlichen Revision und verzichtet auf eine "
    r"eingeschränkte Revision)\.?",
    re.I,
)
_FR_TRANSLATIONS_REMOVED = re.compile(
    r"Traduction de la raison:\s*\[Les traductions sont radiées dans le registre du commerce\]\.?,?",
    re.I,
)
_FR_COOPERATIVE_SHARE_RANGE = re.compile(
    r"Parts sociales:\s*CHF\s+(?P<minimum>[\d'.]+)\s+au minimum et CHF\s+"
    r"(?P<maximum>[\d'.]+)\s+au maximum\.?",
    re.I,
)
_FR_AUDIT_WAIVER = re.compile(
    r"Selon déclaration du\s+(?P<date>\d{2}\.\d{2}\.\d{4}|\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}),\s*"
    r"(?:la société n'est pas soumise à (?:un contrôle|une révision) ordinaire et (?:renonce|a renoncé)|"
    r"(?:il\s+)?est renoncé) à (?:un contrôle restreint|une révision restreinte)\.?,?",
    re.I,
)
_IT_AUDIT_WAIVER = re.compile(
    r"Secondo dichiarazione del (?P<date>\d{2}\.\d{2}\.\d{4}) la società "
    r"non è soggetta alla revisione ordinaria e rinuncia a una revisione limitata\.?,?",
    re.I,
)
_FR_COMPANY_REINSTATED = re.compile(
    r"La société est réinscrite au registre du commerce conformément à la décision "
    r"(?P<authority>.+?) du (?P<date>\d{1,2}\s+[a-zéû]+\s+\d{4})"
    r"(?:\.\s*Les\s+|\s*\[les\s+)faits inscrits relatifs "
    r"(?:au liquidateur et )?à l'adresse de liquidation demeurent valables\.?(?:\])?\.?,?",
    re.I,
)
_FR_SOLE_PROPRIETOR_OFFICIAL_REGISTRATION = re.compile(
    r"Entreprise individuelle inscrite d'office selon l'art\.\s*"
    r"(?P<article>152 ORC)\.?,?",
    re.I,
)
_FR_COMPANY_REINSTATEMENT_ORDERED = re.compile(
    r"La réinscription de la société(?: en l'état)? a été ordonnée par décision du "
    r"(?P<authority>.+?) du (?P<date>\d{2}\.\d{2}\.\d{4})"
    r"(?:(?:\.\s*)?Les faits inscrits au moment de la radiation demeurent valables)?\.?,?",
    re.I,
)
_FR_ERRONEOUS_DISSOLUTION_REVERSED = re.compile(
    r"L'inscription de la dissolution ayant eu lieu à la suite d'une communication "
    r"erronée du Tribunal,\s*la situation est rétablie comme précédemment\s*"
    r"\(FOSC du (?P<date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*(?P<page>\d+)/(?P<reference>\d+)\)\.?,?",
    re.I,
)
_DE_COMPANY_REINSTATED_BANKRUPTCY_REOPENED = re.compile(
    r"Mit Entscheid des (?P<authority>.+?) vom (?P<date>\d{2}\.\d{2}\.\d{4}) ist die "
    r"Gesellschaft wieder ins Handelsregister einzutragen\.\s*Das mangels Aktiven "
    r"eingestellte Konkursverfahren wird wiedereröffnet und das summarische Verfahren "
    r"angeordnet\.\s*\[bisher:\s*(?P<previous>[^\]]+)\]\.?,?",
    re.I,
)
_FR_SOLE_PROPRIETOR_REINSTATED_CORRECTION = re.compile(
    r"Rectificatif:\s*l'entreprise individuelle ayant été radiée par erreur,\s*"
    r"elle est réinscrite comme ci-devant\s*"
    r"\(FOSC du (?P<reference_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"p\.\s*(?P<page>\d+)/(?P<reference>\d+)\)\.?,?",
    re.I,
)
_DE_SOLE_PROPRIETOR_REINSTATED = re.compile(
    r"(?:Die Löschung des Einzelunternehmens erfolgte versehentlich|"
    r"Die Eintragung der Löschung des Einzelunternehmens erfolgte irrtümlich auf Antrag "
    r"des Inhabers und wird von ihm widerrufen)\.\s*"
    r"Da der Geschäftsbetrieb nicht aufgehört hat,\s*besteht der ursprüngliche Eintrag "
    r"mit den eingetragenen Tatsachen,\s*wie sie vor der Löschung registriert waren,\s*"
    r"unverändert weiter\.\s*"
    r"\[(?:gestrichen|bisher):\s*(?P<removed>(?:Das Einzelunternehmen ist infolge "
    r"Geschäftsaufgabe erloschen|Löschung infolge Geschäftsaufgabe)\.)\]\.?,?",
    re.I,
)
_IT_COMPANY_REINSTATED_IN_LIQUIDATION = re.compile(
    r"Con decreto della (?P<authority>.+?) del (?P<date>\d{2}\.\d{2}\.\d{4}) "
    r"la società è reiscritta come società in liquidazione giusta "
    r"(?P<law>l'art\.\s*164 cpv\.\s*1 lett\.\s*a ORC)\.\s*"
    r"I fatti iscritti relativi al liquidatore e all'indirizzo della liquidazione restano validi\.?",
    re.I,
)
_FR_COMPANY_REINSTATED_BANKRUPTCY = re.compile(
    r"La société est réinscrite au registre du commerce conformément à la décision "
    r"(?P<authority>.+?) du (?P<decision_date>\d{1,2}\s+[a-zéû]+\s+\d{4}),\s*"
    r"prononçant la réouverture de la faillite le "
    r"(?P<bankruptcy_date>\d{1,2}\s+[a-zéû]+\s+\d{4}),\s*à\s*"
    r"(?P<time>\d{1,2}h\d{2})\.?",
    re.I,
)
_FR_BANKRUPTCY_CLOSED = re.compile(
    r"La procédure de faillite,\s*suspendue faute d'actif,\s*a été clôturée le\s+"
    r"(?P<date>\d{1,2}\s+[a-zéû]+\s+\d{4})\.?,?",
    re.I,
)
_FR_BANKRUPTCY_EFFECT_SUSPENDED = re.compile(
    r"Par (?:arrêt|décision) du (?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>.+?) a accordé (?:l'effet suspensif au recours"
    r"(?: interjeté le (?P<appeal_date>\d{2}\.\d{2}\.\d{4}))? contre la décision|"
    r"la suspension de l'effet exécutoire attaché au jugement) de faillite du "
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.?",
    re.I,
)
_FR_BANKRUPTCY_PROCEEDINGS_SUSPENDED = re.compile(
    r"(?P<authority>L(?:e président|a présidente) du Tribunal de l'arrondissement .+?) a prononcé "
    r"l'effet suspensif de la procédure de faillite le\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}|\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})\.?",
    re.I,
)
_FR_BANKRUPTCY_EFFECT_SUSPENDED_WRITTEN = re.compile(
    r"(?P<authority>Le président du Tribunal de l'arrondissement .+?) a prononcé le "
    r"(?P<decision_date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}) "
    r"l'effet suspensif de la faillite rendue le (?P<bankruptcy_date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})\.?",
    re.I,
)
_FR_BANKRUPTCY_ENFORCEMENT_SUSPENDED = re.compile(
    r"Par décision présidentielle du\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+du\s+"
    r"(?P<authority>Tribunal Fédéral),\s*l'effet suspensif est attribué au recours "
    r"en ce sens que le prononcé de la faillite reste en force mais qu'aucun acte "
    r"d'exécution de la décision attaquée ne doit être entrepris,\s*"
    r"les éventuelles mesures conservatoires .+? demeurant toutefois en vigueur\.?",
    re.I | re.DOTALL,
)
_FR_BANKRUPTCY_MAINTAINED = re.compile(
    r"Par arrêt du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>le Tribunal fédéral) a rejeté le recours contre le jugement du\s+"
    r"(?P<judgment_date>\d{2}\.\d{2}\.\d{4});\s*par conséquent,\s*la faillite "
    r"prononcée avec effet à partir du\s+(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4}) "
    r"est maintenue\.?",
    re.I,
)
_FR_BANKRUPTCY_APPEAL_REJECTED = re.compile(
    r"Par décision du\s+(?P<decision_date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}),\s*"
    r"(?P<authority>.+?) a rejeté le recours,\s*confirmé la décision et dit que la "
    r"faillite prend effet le\s+(?P<bankruptcy_date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}),\s*"
    r"à\s*(?P<time>\d{1,2}h\d{2})\.?,?",
    re.I,
)
_FR_COURT_DISSOLUTION = re.compile(
    r"Par arrêt de\s+(?P<authority>.+?)\s+du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*la société a été dissoute\.?",
    re.I,
)
_FR_JUDICIAL_DISSOLUTION = re.compile(
    r"La société n'ayant pas rétabli sa situation légale dans le délai imparti,\s*"
    r"(?P<authority>la présidente du Tribunal de l'arrondissement .+?) a prononcé "
    r"sa dissolution judiciaire le\s+"
    r"(?P<date>\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})\.?",
    re.I,
)
_FR_DISSOLUTION_WITH_BANKRUPTCY_LIQUIDATION = re.compile(
    r"Par décision du\s+"
    r"(?P<date>\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}),\s*"
    r"(?P<authority>.+?) a constaté la dissolution de la société;\s*"
    r"sa liquidation a été ordonnée selon les dispositions applicables à la faillite\.?",
    re.I,
)
_FR_ASSOCIATION_DISSOLUTION_WITH_BANKRUPTCY_LIQUIDATION = re.compile(
    r"Par décision du (?P<authority>.+?) du\s+"
    r"(?P<date>\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}),\s*"
    r"l['’]association a été déclarée dissoute conformément "
    r"(?:à l['’]article|aux articles)\s+(?P<law>154 ORC(?: et 69c CC)?);\s*"
    r"sa liquidation a été ordonnée selon les dispositions "
    r"applicables à la faillite\.?,?",
    re.I,
)
_FR_ASSET_TRANSFER = re.compile(
    r"Transfert de patrimoine:\s*Selon contrat du (?P<date>\d{2}\.\d{2}\.\d{4}) "
    r"la société a transféré certains actifs pour CHF (?P<assets>[\d'.]+) et certains passifs "
    r"envers les tiers pour CHF (?P<liabilities>[\d'.]+),\s*soit un actif net de CHF "
    r"(?P<net>[\d'.]+) à (?:la société anonyme\s+)?[\"“](?P<recipient>.+?)[\"”],\s*"
    r"à (?P<place>[^()]+)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*(?P<consideration>.+?)\.?$",
    re.I | re.DOTALL,
)
_FR_SPIN_OFF_TRANSFER = re.compile(
    r"Séparation:\s*selon contrat de scission du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré une partie de "
    r"ses actifs et de ses passifs à\s+(?P<recipient>.+?),\s*à\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?",
    re.I | re.DOTALL,
)
_FR_FOUNDATION_ASSET_TRANSFER = re.compile(
    r"Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<date>\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|"
    r"septembre|octobre|novembre|décembre)\s+\d{4})\s+et selon décision de "
    r"l['’]autorité de surveillance du\s+"
    r"(?P<approval_date>\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|"
    r"septembre|octobre|novembre|décembre)\s+\d{4}),\s*la fondation a transféré "
    r"des actifs de CHF\s+(?P<assets>[\d'.]+) et des passifs envers les tiers de "
    r"CHF\s+(?P<liabilities>[\d'.]+),\s*à\s+(?P<recipient>.+?)\s+à\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*(?P<consideration>[^.]+)\.?",
    re.I | re.DOTALL,
)
_FR_SOLE_PROPRIETOR_ASSET_TRANSFER = re.compile(
    r"Transfert de patrimoine:\s*Selon contrat du (?P<date>\d{2}\.\d{2}\.\d{4}) "
    r"(?P<amendments>et avenants? du .+?),\s*le titulaire a transféré des actifs pour "
    r"CHF\s+(?P<assets>[\d'.]+) et des passifs envers les tiers pour CHF\s+"
    r"(?P<liabilities>[\d'.]+),\s*soit un actif net de CHF\s+(?P<net>[\d'.]+) à "
    r"(?P<recipient>.+?)\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<place>[^.]+)\.\s*Contre-prestation:\s*(?P<consideration>.+?)\.?$",
    re.I | re.DOTALL,
)
_DE_COOPERATIVE_LIABILITY_AND_OBLIGATIONS = re.compile(
    r"Haftung/Nachschusspflicht neu:\s*"
    r"\[Streichung des Eintrags aufgrund geänderter Eintragungsvorschriften\.\]\s*"
    r"\[gestrichen:\s*(?P<previous_liability>Haftung:\s*[^\]]+)\]\.\s*"
    r"Pflichten neu:\s*(?P<obligations>.+?)\.\s*"
    r"\[bisher:\s*Pflichten:\s*(?P<previous_obligations>[^\]]+)\]\.\s*"
    r"\[Nachtrag aufgrund geänderter Eintragungsvorschriften\.\]\.?,?",
    re.I | re.DOTALL,
)
_DE_ASSET_TRANSFER = re.compile(
    r"Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom "
    r"(?P<date>\d{2}\.\d{2}\.\d{4})(?P<agreements>.*?)\s+Aktiven von CHF "
    r"(?P<assets>[\d'.]+) und Passiven \(Fremdkapital\) von CHF "
    r"(?P<liabilities>[\d'.]+) auf (?:die )?(?P<recipient>.+?),\s*in "
    r"(?P<place>[^()]+)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>.+?)\.?$",
    re.I | re.DOTALL,
)
_DE_ASSET_TRANSFER_WITH_INVENTORY = re.compile(
    r"Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss "
    r"Vermögensübertragungsvertrag vom (?P<date>\d{2}\.\d{2}\.\d{4}) und Inventar per "
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4}) Aktiven von CHF "
    r"(?P<assets>[\d'.]+) und Passiven \(Fremdkapital\) von CHF "
    r"(?P<liabilities>[\d'.]+) auf (?:die )?(?P<recipient>.+?),\s*in "
    r"(?P<place>[^()]+)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>.+?)\.?$",
    re.I | re.DOTALL,
)
_DE_BUSINESS_UNIT_ASSET_TRANSFER = re.compile(
    r"Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss "
    r"Vermögensübertragungsvertrag vom (?P<date>\d{2}\.\d{2}\.\d{4}) und Inventar per "
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4}) den Geschäftsteil "
    r"[\"“](?P<business_unit>.+?)[\"”] mit Aktiven von CHF "
    r"(?P<assets>[\d'.]+) und Passiven \(Fremdkapital\) von CHF "
    r"(?P<liabilities>[\d'.]+) auf (?:die )?(?P<recipient>.+?),\s*in "
    r"(?P<place>[^()]+)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>.+?)\.?$",
    re.I | re.DOTALL,
)
_DE_SPIN_OFF_ACQUISITION = re.compile(
    r"Abspaltung:\s*Die Gesellschaft übernimmt von der (?P<source>.+?),\s*in "
    r"(?P<source_place>[^()]+)\s*\((?P<source_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"einen Teil des Vermögens\.\s*Die Gesellschaft übernimmt dabei gemäss "
    r"Spaltungsvertrag vom (?P<date>\d{2}\.\d{2}\.\d{4}) Aktiven von CHF\s*"
    r"(?P<assets>[\d'.]+)\s*und Passiven \(Fremdkapital\) von CHF\s*"
    r"(?P<liabilities>[\d'.]+)\.\s*Da derselbe Aktionär sämtliche Aktien der an "
    r"der Spaltung beteiligten Gesellschaften hält,\s*findet weder eine Kapitalerhöhung "
    r"noch eine Zuteilung von Aktien statt\.?,?",
    re.I,
)
_FR_AUTHORIZED_CAPITAL_CLAUSE = re.compile(
    r"L'assemblée générale a modifié une clause statutaire relative à une "
    r"augmentation autorisée du capital \(selon décision du (?P<original_date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})\) "
    r"par décision du (?P<date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})\.\s*"
    r"Pour les détails,\s*voir les statuts\.?",
    re.I,
)
_FR_CONDITIONAL_CAPITAL_CLAUSE = re.compile(
    r"L['’]assemblée générale a modifié une clause statutaire relative à une "
    r"augmentation conditionnelle du capital \(selon décision relative à l['’]octroi "
    r"de droits de l['’]assemblée générale du (?P<original_date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})\),?\s*"
    r"par décision du (?P<date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}),?\s*"
    r"pour le détail cf\.\s*statuts\.?",
    re.I,
)
_FR_CONDITIONAL_PARTICIPATION_CAPITAL_CLAUSE = re.compile(
    r"L'assemblée générale a modifié une clause statutaire relative à une "
    r"augmentation conditionnelle du capital-participation \(selon décision du "
    r"(?P<original_date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})\) "
    r"par décision du (?P<date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})\.\s*"
    r"Pour les détails,\s*voir les statuts\.?",
    re.I,
)
_FR_SOCIAL_CAPITAL_COMPOSITION = re.compile(
    r"Le capital social de CHF\s+(?P<total>[\d']+(?:\.\d+)?) "
    r"(?:se compose désormais de|est (?:maintenant|désormais) divisé en) "
    r"(?P<count>[\d']+) parts sociales de CHF\s+(?P<nominal>[\d']+(?:\.\d+)?)"
    r"(?:,\s*dont\s+(?P<holder>[^.]+?)\s+est titulaire)?\.?,?",
    re.I,
)
_FR_SHARE_TRANSFER_RESTRICTION = re.compile(
    r"Les\s+(?P<count>[\d']+)\s+actions nominatives de CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"formant l'entier du capital-actions,\s*sont désormais restreintes quant à la "
    r"transmissibilité selon statuts\.?",
    re.I,
)
_FR_SHARE_TRANSFER_RESTRICTION_WITH_CAPITAL = re.compile(
    r"Les\s+(?P<count>[\d']+)\s+actions de CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"nominatives,\s*sont désormais liées selon statuts\.\s*"
    r"Capital-actions:\s*CHF\s+(?P<total>[\d'.]+),\s*entièrement libéré,\s*"
    r"divisé en\s+(?P<capital_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<capital_nominal>[\d'.]+),\s*nominatives,\s*liées selon statuts\.?,?",
    re.I,
)
_FR_SHARE_TRANSFER_RESTRICTION_REMOVED_WITH_CAPITAL = re.compile(
    r"Les\s+(?P<count>[\d']+)\s+actions de CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"nominatives,\s*ne sont plus liées selon statuts\.\s*"
    r"Capital-actions:\s*CHF\s+(?P<total>[\d'.]+),\s*entièrement libéré,\s*"
    r"divisé en\s+(?P<capital_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<capital_nominal>[\d'.]+),\s*nominatives\.?,?",
    re.I,
)
_FR_SHARE_TRANSFER_RESTRICTION_CAPITAL_GENERIC = re.compile(
    r"Les actions sont désormais liées selon statuts\.\s*"
    r"Capital-actions:\s*CHF\s+(?P<total>[\d'.]+),\s*"
    r"libéré à concurrence de CHF\s+(?P<paid>[\d'.]+),\s*"
    r"divisé en\s+(?P<count>[\d']+)\s+actions de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*nominatives,\s*liées selon statuts\.?,?",
    re.I,
)
_FR_SHARE_TRANSFER_RESTRICTION_GENERIC = re.compile(
    r"(?:Nouvelle restriction à la transmissibilité:\s*)?"
    r"(?:Restriction (?:de|à la) transmissibilité "
    r"(?:des actions|des actions nominatives:)\s*selon statuts)\.?,?",
    re.I,
)
_FR_QUOTA_TRANSFER_STATUTE = re.compile(
    r"Les modalités de transfert des parts sociales dérogent à la loi selon les statuts\.?,?",
    re.I,
)
_FR_PURPOSE_NON_PUBLIC = re.compile(
    r"But modifié(?:\s+sur (?:un point|des points) non soumis à publication)?\.?",
    re.I,
)
_FR_HEAD_OFFICE = re.compile(
    r"Nouveau siège principal:\s*"
    r"(?P<to>(?:St\.\s*)?[^\[.]+(?:\.\d{3}\.\d{3}\))?)"
    r"(?:\s*\[précédemment:\s*(?P<from>[^\]]+)\])?\.?",
    re.I,
)
_FR_SEAT_BECAME = re.compile(r"Siège devenu\s+(?P<to>[^.]+)\.?,?", re.I)
_FR_HEAD_OFFICE_CHANGE = re.compile(
    r"(?<!Nouveau )(?<!du )Siège principal:\s*(?P<to>[^\[.]+?)\s*"
    r"\[précédemment:\s*(?P<from>[^\]]+)\]\.?",
    re.I,
)
_FR_HEAD_OFFICE_REFERENCE = re.compile(
    r"avec siège principal à\s+(?P<seat>[^.]+)\.?",
    re.I,
)
_FR_HEAD_OFFICE_PURPOSE_NOT_PUBLISHED = re.compile(
    r"Le but a été modifié au siège principal;\s*le nouveau but n'est pas mentionné pour "
    r"la succursale,\s*conformément à l'article 110,\s*al\.\s*1,\s*let\.\s*d ORC\.?",
    re.I,
)
_FR_HEAD_OFFICE_CONTEXT = re.compile(
    r"(?<!Nouveau )(?<!du )(?:,\s*)?Siège principal(?: à)?:\s*"
    r"(?P<seat>(?:St\.\s*[^.]+|[^.]+))\.?",
    re.I,
)
_DE_MUNICIPALITY_SEAT_CHANGE = re.compile(
    r"Sitz neu:\s*(?P<to>[^.\[]+)\.\s*"
    r"\[(?P<reason>(?:Anpassung des Sitzes|Sitzänderung von Amtes wegen) "
    r"infolge Namensänderung der Gemeinde)\]\.?",
    re.I,
)
_FR_BRANCH_MENTION_REMOVED = re.compile(
    r"Radiation de la mention de l'existence d'une succursale à "
    r"(?P<place>[^.(]+?)"
    r"(?:\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)|(?=\.|$))\.?",
    re.I,
)
_FR_BRANCH_MENTION_ADDED = re.compile(
    r"Inscription de la mention de l'existence d'une succursale à "
    r"(?P<place>.+?)\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?,?",
    re.I,
)
_FR_HEAD_OFFICE_NAME = re.compile(
    r"Nouvelle raison (?:sociale|de commerce) (?:du siège|de l'établissement) principal:\s*"
    r"(?P<to>.+?)(?:\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\))?"
    r"(?=\s*\[précédemment:|\.\s|$)"
    r"(?:\s*\[précédemment:\s*(?:Raison de commerce du siège principal:\s*)?"
    r"(?P<from>[^\]]+)\])?\.?",
    re.I,
)
_FR_REPUDIATED_ESTATE_LIQUIDATION = re.compile(
    r"(?P<authority>Le président du Tribunal d'arrondissement de .+?) a ordonné "
    r"la liquidation de la succession répudiée du titulaire de cette entreprise "
    r"individuelle par l'Office des faillites le (?P<date>\d{2}\.\d{2}\.\d{4}|\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})\.?",
    re.I,
)
_DE_PURPOSE_RESERVATION_REMOVED = re.compile(
    r"\[gestrichen:\s*Es besteht ein Zweckänderungsvorbehalt zugunsten des Stifters "
    r"gemäss ZGB 86a\.\]",
    re.I,
)
_DE_PURPOSE_RESERVATION = re.compile(
    r"Es besteht ein Zweckänderungsvorbehalt gemäss Art\.\s*86a ZGB\.?",
    re.I,
)
_FR_PURPOSE_RESERVATION = re.compile(
    r"Les fondateurs se réservent expressément la possibilité de faire modifier le but "
    r"par l['’]autorité de surveillance,\s*en application de l['’]article 86a CC\.?",
    re.I,
)
_IT_ADDITIONAL_ADDRESS_REMOVED = re.compile(
    r"Altri indirizzi:\s*\[no:\s*(?P<address>[^\]]+)\]\.?",
    re.I,
)
_IT_ADDITIONAL_ADDRESS = re.compile(
    r"Altri indirizzi:\s*(?!\[(?:no|radiati):)(?P<address>[^.]+)\.?",
    re.I,
)
_EMPTY_NEGATION_MARKER = re.compile(r"\[(?:no|nicht):\s*\]", re.I)
_NEGATION_MARKER = re.compile(
    r"\[(?:no|nicht):(?!\s*Intenzione di assunzione beni:)[^\]]*\]", re.I
)
_IT_SHARE_TRANSFER_RESTRICTION = re.compile(
    r"Nuova limitazione della trasferibilità:\s*"
    r"La trasferibilità dell(?:e|a) azioni nominative è limitata dallo statuto\.?",
    re.I,
)
_IT_SHARE_TRANSFER_RESTRICTION_REMOVED = re.compile(
    r"Nuova limitazione della trasferibilità:\s*"
    r"\[La restrizione della trasferibilità delle azioni nominative è cancellata "
    r"\(art\.\s*685a cpv\.\s*3 CO\)\.\]\.?,?",
    re.I,
)
_DE_TRADE_NAME_ESTABLISHMENT_REMOVED = re.compile(
    r"\[gestrichen:\s*Die Gesellschaft führt in (?P<place>[^,]+),\s*"
    r"(?P<address>[^,\]]+),\s*ein Geschäft unter der Enseigne "
    r"[\"“](?P<trade_name>.+?)[\"”]\.\]\.?,?",
    re.I,
)
_SUPPLEMENT_MARKER = re.compile(r"\[Nachtrag\]\.?,?", re.I)
_IT_QUOTA_TRANSFER_STATUTE = re.compile(
    r"Lo statuto deroga alla legge per le modalità di trasferimento delle quote sociali;\s*"
    r"per i dettagli si rinvia allo statuto\.?",
    re.I,
)
_IT_HEAD_OFFICE_CONTEXT = re.compile(
    r"(?:,\s*)?Sede principale a:\s*(?P<seat>[^.]+)\.?\s*$",
    re.I,
)
_IT_HEAD_OFFICE_CHANGE = re.compile(
    r"(?:,\s*)?Sede principale a:\s*(?P<old>[^.]+)\.\s*"
    r"Nuova sede principale:\s*(?P<to>[^\[]+?)\s*"
    r"\[finora:\s*(?P<from>[^\]]+)\]\.?",
    re.I,
)
_IT_AUTHORIZED_CAPITAL_CLAUSE_REPLACED = re.compile(
    r"\[Abrogazione della disposizione statutaria relativa all['’]aumento autorizzato del capitale "
    r"basata sulla deliberazione dell['’]assemblea generale del (?P<expired_date>\d{2}\.\d{2}\.\d{4}), "
    r"il termine per l['’]aumento del capitale è scaduto\.\]\.?\s*"
    r"\[radiati:\s*Con delibera del (?P<removed_date>\d{2}\.\d{2}\.\d{4}) l['’]assemblea generale "
    r"ha introdotto una clausola statutaria relativa ad un aumento autorizzato del capitale azionario\. "
    r"Per i dettagli vedi statuto\.\]\.?\s*"
    r"Con delibera del (?P<introduced_date>\d{2}\.\d{2}\.\d{4}) l['’]assemblea generale "
    r"ha introdotto una clausola statutaria relativa ad un aumento autorizzato del capitale azionario\. "
    r"Per i dettagli vedi statuto\.?,?",
    re.I,
)
_IT_CONTRIBUTION_RULES_REMOVED = re.compile(
    r"(?:Fatti particolari:\s*\[Le disposizioni statutarie relative ai conferimenti in natura "
    r"e all'assunzione di beni sono abrogate\]|"
    r"Fatti particolari:\s*(?:\[La disposizione statutaria relativa al conferimento in natura "
    r"e all'assunzione di beni è stata abrogata,\s*in quanto sono trascorsi più di 10 anni "
    r"dalla sua introduzione\](?:\s*\[radiati:\s*.*?\])?\.?(?:\s*|$))+)",
    re.I | re.DOTALL,
)
_FR_ADDITIONAL_ADDRESS = re.compile(
    r"(?:Nouvelle\s+)?Autre adresse:\s*(?P<address>[^.]+)\.?",
    re.I,
)
_FR_SHARE_TRANSFER_RESTRICTION_REMOVED = re.compile(
    r"(?:Radiation de la mention relative à la restriction de la transmissibilité "
    r"des actions nominatives|"
    r"Radiation de la restriction statutaire de transmissibilité des\s+"
    r"(?P<count_alt>[\d']+) actions de CHF\s+(?P<nominal_alt>[\d'.]+),\s*nominatives|"
    r"Les\s+(?P<count>[\d']+)\s+actions nominatives de CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"formant l'entier du capital-actions,\s*ne sont désormais plus restreintes quant à "
    r"la transmissibilité)\s*\(art\.\s*685a,\s*al\.\s*3\s*CO\)\.?",
    re.I,
)
_DE_NON_PUBLIC_STATUTES = re.compile(
    r"Statuten (?:geändert über|\u00fcber) nicht publikationspflichtige Tatsachen "
    r"(?:geändert )?am\s*"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.?,?",
    re.I,
)
_IT_NEW_ADDRESS = re.compile(
    r"Nuovo recapito:(?!\s*La società (?:è priva di|non ha più un) domicilio legale)\s*"
    r"(?P<address>.+?)(?:\s*\[(?P<reason>decisione[^\]]+)\])?\.?$",
    re.I,
)
_FR_DELETION_OPPOSED = re.compile(
    r"(?:Une opposition(?: motivée)? (?:à la radiation a été formée|a été présentée contre la radiation "
    r"de cette entité juridique|à la radiation de l'entité juridique,\s*au sens de l'article "
    r"159 al\.\s*5 let\.\s*a ORC,\s*a été présentée)|"
    r"En raison d['’]une opposition motivée à la radiation,\s*la société reste "
    r"inscrite conformément à l['’]art\.\s*159 al\.\s*5 let\.\s*a ORC)\.?",
    re.I,
)
_FR_DOMICILIARY_ADDRESS = re.compile(
    r"Nouvelle raison sociale du domiciliataire:\s*(?P<address>[^.]+)\.?",
    re.I,
)
_EMPTY_HISTORY_MARKER = re.compile(
    r"\[(?:gestrichen|bisher|biffé|précédemment|finora):\s*\]", re.I
)
_DE_COMMUNICATIONS = re.compile(
    r"Mitteilungen neu:\s*(?P<to>.+?)(?=\s+\[|\s+(?:Gemäss Erklärung|Ausgeschiedene|Eingetragene)\b|$)",
    re.I | re.DOTALL,
)
_IT_COMMUNICATIONS = re.compile(
    r"Nuove comunicazioni:\s*(?P<to>.+?)(?=\s+(?:Secondo dichiarazione|Persone)\b|$)",
    re.I | re.DOTALL,
)
_BOILERPLATE = [
    re.compile(r"\[Neue\]", re.I),
    re.compile(r"\[gestrichen\]", re.I),
    re.compile(
        r"\[Statuts modifiés le \d{2}\.\d{2}\.\d{4} sur (?:un point|des points) "
        r"non soumis à publication\.\]",
        re.I,
    ),
    re.compile(r"\[Die publikationspflichtigen Tatsachen haben keine Änderung erfahren\.\]", re.I),
    re.compile(r"\[Die publikationspflichtigen Tatsachen haben keine Änderungen erfahren\.\]", re.I),
    re.compile(r"Die publikationspflichtigen Tatsachen haben keine Änderung erfahren\.?", re.I),
    re.compile(r"\[Bei der Statutenänderung haben die publikationspflichtigen Tatsachen keine Änderung erfahren\.\]", re.I),
    re.compile(r"\[Ferner Änderung nicht publikationspflichtiger Tatsachen\]\.?", re.I),
    re.compile(r"\[Ferner Änderung einer nicht publikationspflichtigen Tatsache\.\]", re.I),
    re.compile(r"\[Änderung einer nicht publikationspflichtigen Tatsache\.\]", re.I),
    re.compile(r"\[Änderung nicht publikationspflichtiger Tatsachen\]", re.I),
    re.compile(r"\[Änderung nicht publikationspflichtiger Tatsachen\.\]", re.I),
    re.compile(r"\[Weitere Änderungen berühren keine publikationspflichtigen Tatsachen\.\]", re.I),
    re.compile(r"\[Modification des statuts sur (?:un point|des points) non soumis à publication\]", re.I),
    re.compile(r"\[Modification des statuts\s*\]", re.I),
    re.compile(r"Änderung nicht publikationspflichtiger Tatsachen\.?", re.I),
    re.compile(r"Statuts modifiés sur (?:un point|des points) non soumis à publication\.?", re.I),
    re.compile(r";?\s*les faits (?:déjà )?publiés ne sont pas modifiés\.?", re.I),
    re.compile(r"\[Behördliche Umadressierung\]\.?", re.I),
    re.compile(r"(?:ainsi que\s+)?sur (?:un point|des points) non soumis à publication", re.I),
    re.compile(r"Nicht publikationspflichtige weitere Statutenänderungen\.?", re.I),
    re.compile(r"\[Weitere Statutenänderungen nicht publikationspflichtiger Tatsachen\]\.?", re.I),
    re.compile(r"\[Weitere Statutenänderungen sind nicht publikationspflichtig\.\]", re.I),
    re.compile(r"\[Streichung mangels Publikationspflicht:\]", re.I),
    re.compile(
        r"\[gestrichen:\s*Streichung der statutarisch festgesetzten Anzahl der "
        r"Verwaltungsratsmitglieder,\s*da nicht zur Eintragung gehörend\.\]\.?,?",
        re.I,
    ),
    re.compile(r"\[Statuto modificato su punti non soggetti a pubblicazione\.\]", re.I),
]
_HEADER = re.compile(
    r"^.+?CHE-\d{3}\.\d{3}\.\d{3}"
    r"(?:.*?\([^)]*(?:SHAB|FOSC|FUSC|Publ\.?)[^)]*\))?"
    r"[.\s]*",
    re.I | re.DOTALL,
)

_CONSUME = {
    "address_changed": [
        re.compile(r"Domizil neu:[^.]*\.?", re.I),
        re.compile(r"Nouvelle adresse:[^.]*\.?", re.I),
        re.compile(r"Nuovo indirizzo:[^.]*\.?", re.I),
        re.compile(r"\[Die weitere Adresse wird im Handelsregister gelöscht\]", re.I),
        re.compile(r"Die weitere Adresse wurde aufgehoben\.?", re.I),
    ],
    "seat_changed": [
        re.compile(r"(?<!Haupt)Sitz neu:[^.]*\.?", re.I),
        re.compile(r"Siège transféré[^.]*\.?", re.I),
        re.compile(r"Trasferimento di sede[^.]*\.?", re.I),
    ],
    "purpose_changed": [
        re.compile(r"Zweck neu:[^.]*\.?", re.I),
        re.compile(r"Nouveau but:[^.]*\.?", re.I),
        re.compile(r"Nuovo scopo:[^.]*\.?", re.I),
    ],
    "company_name_changed": [
        re.compile(r"Firma neu:[^.]*\.?", re.I),
        re.compile(r"Neue Geschäftsfirma:[^.]*\.?", re.I),
        re.compile(r"Nouvelle raison de commerce:[^.]*\.?", re.I),
        re.compile(
            r"La raison de commerce devient:.+?"
            r"(?=\.\s+(?-i:[A-ZÀ-Ÿ][a-zà-ÿ])|\.$|$)",
            re.I,
        ),
        re.compile(r"La raison de commerce redevient:.+?(?=\.\s+[A-ZÀ-Ÿ]|$)", re.I),
        re.compile(r"Nuova ragione sociale:[^.]*\.?", re.I),
    ],
}


def _strip_header(text: str) -> str:
    text = text.strip(" .")
    match = _HEADER.match(text)
    if not match:
        return text
    return text[match.end() :].strip(" .")


def _swiss_date(value: str) -> str:
    day, month, year = value.split(".")
    return f"{year}-{month}-{day}"


def _french_written_date(value: str) -> str:
    months = {
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
    day, month, year = value.lower().split()
    day = re.sub(r"\D+$", "", day)
    return f"{int(year):04d}-{months[month]:02d}-{int(day):02d}"


def _german_written_date(value: str) -> str:
    months = {
        "januar": 1,
        "februar": 2,
        "märz": 3,
        "april": 4,
        "mai": 5,
        "juni": 6,
        "juli": 7,
        "august": 8,
        "september": 9,
        "oktober": 10,
        "november": 11,
        "dezember": 12,
    }
    day, month, year = value.lower().split()
    return f"{int(year):04d}-{months[month]:02d}-{int(day.rstrip('.')):02d}"


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


def extract_text_extras(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
    event_types: set[str],
) -> tuple[list[Event], str]:
    events: list[Event] = []
    leftover = text
    event_types = set(event_types)
    lang = (language or "de").lower()
    correction = (
        _IT_CORRECTION_HEADER.search(leftover)
        if lang == "it"
        else _DE_CORRECTION_HEADER.search(leftover)
        or _DE_CORRECTION_HEADER_ALT.search(leftover)
    )
    if correction:
        correction_lang = "it" if correction.re is _IT_CORRECTION_HEADER else "de"
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "publication_corrected",
                f"{correction_lang}.text.correction.v1",
                {
                    "issue": correction.group("issue").strip(),
                    "entry": correction.group("entry"),
                    "entry_date": _swiss_date(correction.group("date")),
                },
            )
        )
        leftover = leftover.replace(correction.group(0), " ", 1)
    bankruptcy_scope_correction = _FR_BANKRUPTCY_SCOPE_CORRECTION.search(leftover)
    if bankruptcy_scope_correction:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "publication_corrected",
                "fr.text.bankruptcy_scope_correction.v1",
                {
                    "entry": bankruptcy_scope_correction.group("number"),
                    "entry_date": _swiss_date(
                        bankruptcy_scope_correction.group("date")
                    ),
                    "publication_date": _swiss_date(
                        bankruptcy_scope_correction.group("publication_date")
                    ),
                    "publication_page": bankruptcy_scope_correction.group(
                        "publication_page"
                    ),
                    "kind": "bankruptcy_suspensive_effect_scope",
                    "enforcement_only": True,
                    "bankruptcy_remains_in_force": True,
                    "bankruptcy_publication_date": _swiss_date(
                        bankruptcy_scope_correction.group(
                            "bankruptcy_publication_date"
                        )
                    ),
                    "bankruptcy_reference": bankruptcy_scope_correction.group(
                        "bankruptcy_reference"
                    ),
                },
            )
        )
        leftover = leftover.replace(bankruptcy_scope_correction.group(0), " ", 1)
    negated_fusion = _DE_NEGATED_FUSION_CORRECTION.search(leftover)
    if negated_fusion:
        leftover = leftover.replace(negated_fusion.group(0), " ", 1)
    multiple_statutes = _FR_STATUTES_MULTIPLE.search(leftover)
    if multiple_statutes:
        written_dates = re.findall(
            r"\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|"
            r"septembre|octobre|novembre|décembre)\s+\d{4}",
            multiple_statutes.group("dates"),
            re.I,
        )
        parsed_dates = [_french_written_date(value) for value in written_dates]
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "fr.text.statutes_multiple.v1",
                {
                    "date": parsed_dates[-1],
                    "dates": parsed_dates,
                    "raw": multiple_statutes.group(0).strip(),
                },
            )
        )
        leftover = leftover.replace(multiple_statutes.group(0), " ", 1)
        event_types.add("statutes_changed")
    statute_patterns = {
        "de": (_DE_STATUTES, "de.text.statutes.v1"),
        "fr": (_FR_STATUTES, "fr.text.statutes.v1"),
        "it": (_IT_STATUTES, "it.text.statutes.v1"),
    }
    pattern, rule_id = statute_patterns.get(lang, statute_patterns["de"])
    match = pattern.search(leftover)
    if not match:
        for fallback_lang in ("de", "fr", "it"):
            fallback_pattern, fallback_rule_id = statute_patterns[fallback_lang]
            if fallback_pattern is pattern:
                continue
            match = fallback_pattern.search(leftover)
            if match:
                pattern = fallback_pattern
                rule_id = fallback_rule_id
                break
    if match:
        raw_date = match.group("date")
        parsed_date = (
            _swiss_date(raw_date)
            if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", raw_date)
            else _french_written_date(raw_date)
        )
        statutes_payload = {"date": parsed_date, "raw": match.group(0)}
        if re.search(r"points non soumis à publication", match.group(0), re.I):
            statutes_payload["non_public_changes"] = True
        approval_date = match.groupdict().get("approval_date")
        if approval_date:
            statutes_payload["supervisory_approval_date"] = _swiss_date(approval_date)
        additional_date = match.groupdict().get("additional_date")
        if additional_date:
            statutes_payload["additional_date"] = _swiss_date(additional_date)
            statutes_payload["non_public_changes"] = True
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                rule_id,
                statutes_payload,
            )
        )
        leftover = leftover.replace(match.group(0), " ")
        additional_non_public = _FR_ADDITIONAL_NON_PUBLIC_STATUTES.search(leftover)
        if additional_non_public:
            statutes_payload["non_public_changes"] = True
            leftover = leftover.replace(additional_non_public.group(0), " ")
    head_office_statutes = _DE_HEAD_OFFICE_STATUTES.search(leftover)
    if head_office_statutes:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "de.text.head_office_statutes.v1",
                {
                    "date": _swiss_date(head_office_statutes.group("date")),
                    "scope": "head_office",
                    "raw": head_office_statutes.group(0).strip(),
                },
            )
        )
        leftover = leftover.replace(head_office_statutes.group(0), " ")
    foundation_approval = _IT_FOUNDATION_DEED_SUPERVISORY_APPROVAL.search(leftover)
    if foundation_approval:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "it.text.foundation_deed_supervisory_approval.v1",
                {
                    "kind": "foundation_deed_supervisory_approval",
                    "date": _swiss_date(foundation_approval.group("date")),
                    "authority": foundation_approval.group("authority").strip(),
                    "authority_uid": foundation_approval.group("authority_uid"),
                    "authority_place": foundation_approval.group("authority_place").strip(),
                    "non_public_changes": True,
                },
            )
        )
        leftover = leftover.replace(foundation_approval.group(0), " ")
    it_authorized_capital = _IT_AUTHORIZED_CAPITAL_CLAUSE_REPLACED.search(leftover)
    if it_authorized_capital:
        for action, date_group in (
            ("expired", "expired_date"),
            ("introduced", "introduced_date"),
        ):
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "capital_changed",
                    "it.text.authorized_capital_clause.v1",
                    {
                        "kind": "authorized_capital_clause",
                        "action": action,
                        "decision_date": _swiss_date(
                            it_authorized_capital.group(date_group)
                        ),
                    },
                )
            )
        leftover = leftover.replace(it_authorized_capital.group(0), " ")
        event_types.add("capital_changed")
    participation_certificates = _DE_PARTICIPATION_CERTIFICATES_REMOVED.search(leftover)
    if participation_certificates:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "de.text.participation_certificates_removed.v1",
                {
                    "kind": "participation_certificates",
                    "action": "removed",
                    "from_count": int(participation_certificates.group("count").replace("'", "")),
                    "rights": participation_certificates.group("rights").strip(),
                },
            )
        )
        leftover = leftover.replace(participation_certificates.group(0), " ")
        event_types.add("capital_changed")
    added_participation_certificates = _DE_PARTICIPATION_CERTIFICATES_ADDED.search(
        leftover
    )
    if added_participation_certificates:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "de.text.participation_certificates_added.v1",
                {
                    "kind": "participation_certificates",
                    "action": "added",
                    "to_count": int(
                        added_participation_certificates.group("count").replace("'", "")
                    ),
                    "rights": added_participation_certificates.group("rights").strip(),
                },
            )
        )
        leftover = leftover.replace(added_participation_certificates.group(0), " ")
        event_types.add("capital_changed")
    preference_rights = _DE_PREFERENCE_SHARE_RIGHTS.search(leftover)
    if preference_rights:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "de.text.preference_share_rights.v1",
                {
                    "kind": "preference_share_rights",
                    "action": "changed",
                    "rights": preference_rights.group("rights").strip(),
                    **(
                        {
                            "previous_rights": preference_rights.group(
                                "previous_rights"
                            ).strip()
                        }
                        if preference_rights.group("previous_rights")
                        else {}
                    ),
                },
            )
        )
        leftover = leftover.replace(preference_rights.group(0), " ")
        event_types.add("capital_changed")
    new_shares = _IT_NEW_SHARES.search(leftover)
    if new_shares:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "it.text.share_structure.v1",
                {
                    "from_count": int(new_shares.group("from_count").replace("'", "")),
                    "from_nominal": new_shares.group("from_nominal"),
                    "from_kind": new_shares.group("from_kind").strip(),
                    "to_count": int(new_shares.group("to_count").replace("'", "")),
                    "to_nominal": new_shares.group("to_nominal"),
                    "to_kind": new_shares.group("to_kind").strip(),
                },
            )
        )
        leftover = leftover.replace(new_shares.group(0), " ")
        event_types.add("capital_changed")
    de_legal_classes = _DE_LEGAL_BEARER_CONVERSION_MULTIPLE_CLASSES.search(leftover)
    if de_legal_classes:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "de.text.legal_bearer_conversion.v3",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _swiss_date(de_legal_classes.group("date")),
                    "capital_total": de_legal_classes.group("total"),
                    "paid_in_full": True,
                    "from_kind": "Inhaberaktien",
                    "to_kind": "Namenaktien",
                    "from_share_classes": [
                        {
                            "class": de_legal_classes.group("from_class1"),
                            "count": int(de_legal_classes.group("from_count1").replace("'", "")),
                            "nominal": de_legal_classes.group("from_nominal1"),
                            "kind": "Namenaktien",
                        },
                        {
                            "count": int(de_legal_classes.group("from_count2").replace("'", "")),
                            "nominal": de_legal_classes.group("from_nominal2"),
                            "kind": "Inhaberaktien",
                        },
                    ],
                    "to_share_classes": [
                        {
                            "class": de_legal_classes.group("class1"),
                            "count": int(de_legal_classes.group("count1").replace("'", "")),
                            "nominal": de_legal_classes.group("nominal1"),
                            "kind": "Namenaktien",
                        },
                        {
                            "count": int(de_legal_classes.group("count2").replace("'", "")),
                            "nominal": de_legal_classes.group("nominal2"),
                            "kind": "Namenaktien",
                        },
                    ],
                    "statutes_adapted": False,
                },
            )
        )
        leftover = leftover.replace(de_legal_classes.group(0), " ")
        event_types.add("capital_changed")
    de_legal_classes_simple = (
        _DE_LEGAL_BEARER_CONVERSION_MULTIPLE_CLASSES_SIMPLE.search(leftover)
    )
    if de_legal_classes_simple:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "de.text.legal_bearer_conversion.v6",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _swiss_date(
                        de_legal_classes_simple.group("date")
                    ),
                    "capital_total": de_legal_classes_simple.group("total"),
                    "paid_in_full": True,
                    "from_kind": "Inhaberaktien",
                    "to_kind": "Namenaktien",
                    "from_share_classes": [
                        {
                            "count": int(
                                de_legal_classes_simple.group("from_count1").replace("'", "")
                            ),
                            "nominal": de_legal_classes_simple.group("from_nominal1"),
                            "kind": "Inhaberaktien",
                        },
                        {
                            "count": int(
                                de_legal_classes_simple.group("from_count2").replace("'", "")
                            ),
                            "nominal": de_legal_classes_simple.group("from_nominal2"),
                            "kind": "Namenaktien",
                        },
                    ],
                    "to_share_classes": [
                        {
                            "count": int(
                                de_legal_classes_simple.group("to_count1").replace("'", "")
                            ),
                            "nominal": de_legal_classes_simple.group("to_nominal1"),
                            "kind": "Namenaktien",
                        },
                        {
                            "count": int(
                                de_legal_classes_simple.group("to_count2").replace("'", "")
                            ),
                            "nominal": de_legal_classes_simple.group("to_nominal2"),
                            "kind": "Namenaktien",
                        },
                    ],
                    "statutes_adapted": False,
                },
            )
        )
        leftover = leftover.replace(de_legal_classes_simple.group(0), " ")
        event_types.add("capital_changed")
    de_legal_classes_first = (
        _DE_LEGAL_BEARER_CONVERSION_MULTIPLE_CLASSES_SHARES_FIRST.search(leftover)
    )
    if de_legal_classes_first:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "de.text.legal_bearer_conversion.v4",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _swiss_date(de_legal_classes_first.group("date")),
                    "from_kind": "Inhaberaktien",
                    "to_kind": "Namenaktien",
                    "from_share_classes": [
                        {
                            "count": int(de_legal_classes_first.group("from_count1").replace("'", "")),
                            "nominal": de_legal_classes_first.group("from_nominal1"),
                            "kind": "Inhaberaktien",
                        },
                        {
                            "class": de_legal_classes_first.group("from_class2"),
                            "count": int(de_legal_classes_first.group("from_count2").replace("'", "")),
                            "nominal": de_legal_classes_first.group("from_nominal2"),
                            "kind": "Namenaktien",
                        },
                    ],
                    "to_share_classes": [
                        {
                            "count": int(de_legal_classes_first.group("to_count1").replace("'", "")),
                            "nominal": de_legal_classes_first.group("to_nominal1"),
                            "kind": "Namenaktien",
                        },
                        {
                            "class": de_legal_classes_first.group("class2"),
                            "count": int(de_legal_classes_first.group("to_count2").replace("'", "")),
                            "nominal": de_legal_classes_first.group("to_nominal2"),
                            "kind": "Namenaktien",
                        },
                    ],
                    "statutes_adapted": False,
                },
            )
        )
        leftover = leftover.replace(de_legal_classes_first.group(0), " ")
        event_types.add("capital_changed")
    de_legal_partial_paid = _DE_LEGAL_BEARER_CONVERSION_PARTIAL_PAID.search(leftover)
    if de_legal_partial_paid:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "de.text.legal_bearer_conversion.v5",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _swiss_date(de_legal_partial_paid.group("date")),
                    "capital_total": de_legal_partial_paid.group("total"),
                    "paid": de_legal_partial_paid.group("paid"),
                    "paid_in_full": de_legal_partial_paid.group("paid")
                    == de_legal_partial_paid.group("total"),
                    "from_count": int(de_legal_partial_paid.group("from_count").replace("'", "")),
                    "from_nominal": de_legal_partial_paid.group("from_nominal"),
                    "from_kind": de_legal_partial_paid.group("from_kind"),
                    "to_count": int(de_legal_partial_paid.group("to_count").replace("'", "")),
                    "to_nominal": de_legal_partial_paid.group("to_nominal"),
                    "to_kind": de_legal_partial_paid.group("to_kind"),
                    "statutes_adapted": False,
                },
            )
        )
        leftover = leftover.replace(de_legal_partial_paid.group(0), " ")
        event_types.add("capital_changed")
    removed_conversion_notice = _DE_LEGAL_BEARER_CONVERSION_NOTICE_REMOVED.search(leftover)
    if removed_conversion_notice:
        raw_date = removed_conversion_notice.group("date")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "de.text.legal_bearer_conversion_notice_removed.v1",
                {
                    "kind": "bearer_to_registered_conversion_notice",
                    "action": "removed",
                    "conversion_date": (
                        _swiss_date(raw_date)
                        if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", raw_date)
                        else _german_written_date(raw_date)
                    ),
                    "statutes_adapted": True,
                },
            )
        )
        leftover = leftover.replace(removed_conversion_notice.group(0), " ")
        event_types.add("capital_changed")
    it_adapted_conversion = _IT_LEGAL_BEARER_CONVERSION_ADAPTED.search(leftover)
    if it_adapted_conversion:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "it.text.legal_bearer_conversion_adapted.v1",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _swiss_date(
                        it_adapted_conversion.group("conversion_date")
                    ),
                    "adaptation_date": _swiss_date(
                        it_adapted_conversion.group("adaptation_date")
                    ),
                    "from_kind": "azioni al portatore",
                    "to_kind": "azioni nominative",
                    "statutes_adapted": True,
                    "previous_notice_removed": True,
                },
            )
        )
        leftover = leftover.replace(it_adapted_conversion.group(0), " ")
        event_types.add("capital_changed")
    for legal_conversion, legal_rule in (
        (
            _DE_LEGAL_BEARER_CONVERSION_SHARES_FIRST.search(leftover),
            "de.text.legal_bearer_conversion.v1",
        ),
        (
            _DE_LEGAL_BEARER_CONVERSION_CAPITAL_LAST.search(leftover),
            "de.text.legal_bearer_conversion.v2",
        ),
    ):
        if not legal_conversion:
            continue
        raw_date = legal_conversion.group("date")
        payload = {
            "kind": "bearer_to_registered_conversion",
            "legal_basis": "by_operation_of_law",
            "conversion_date": (
                _swiss_date(raw_date)
                if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", raw_date)
                else _german_written_date(raw_date)
            ),
            "from_count": int(legal_conversion.group("from_count").replace("'", "")),
            "from_nominal": legal_conversion.group("from_nominal"),
            "from_kind": legal_conversion.group("from_kind"),
            "to_count": int(legal_conversion.group("to_count").replace("'", "")),
            "to_nominal": legal_conversion.group("to_nominal"),
            "to_kind": legal_conversion.group("to_kind"),
            "statutes_adapted": False,
        }
        if legal_conversion.groupdict().get("total"):
            payload["capital_total"] = legal_conversion.group("total")
            payload["paid_in_full"] = True
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                legal_rule,
                payload,
            )
        )
        leftover = leftover.replace(legal_conversion.group(0), " ")
        event_types.add("capital_changed")
    de_conversion_notice = _DE_LEGAL_BEARER_CONVERSION_NOTICE.search(leftover)
    if de_conversion_notice:
        raw_date = de_conversion_notice.group("date")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "de.text.legal_bearer_conversion_notice.v1",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": (
                        _swiss_date(raw_date)
                        if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", raw_date)
                        else _german_written_date(raw_date)
                    ),
                    "from_kind": "Inhaberaktien",
                    "to_kind": "Namenaktien",
                    "statutes_adapted": False,
                },
            )
        )
        leftover = leftover.replace(de_conversion_notice.group(0), " ")
        event_types.add("capital_changed")
    fr_legal_postfix_classes = (
        _FR_LEGAL_BEARER_CONVERSION_MULTIPLE_CLASSES_POSTFIX_KIND.search(leftover)
    )
    if fr_legal_postfix_classes:
        paid = fr_legal_postfix_classes.group("paid")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.legal_bearer_conversion.v5",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _swiss_date(
                        fr_legal_postfix_classes.group("date")
                    ),
                    "capital_total": fr_legal_postfix_classes.group("total"),
                    "paid": paid,
                    "paid_in_full": paid
                    == fr_legal_postfix_classes.group("total"),
                    "from_count": int(
                        fr_legal_postfix_classes.group("from_count").replace("'", "")
                    ),
                    "from_kind": "au porteur",
                    "to_kind": "nominatives",
                    "share_classes": [
                        {
                            "count": int(
                                fr_legal_postfix_classes.group("count1").replace("'", "")
                            ),
                            "nominal": fr_legal_postfix_classes.group("nominal1"),
                            "kind": "nominatives",
                            "rights": fr_legal_postfix_classes.group("rights1").strip(),
                        },
                        {
                            "count": int(
                                fr_legal_postfix_classes.group("count2").replace("'", "")
                            ),
                            "nominal": fr_legal_postfix_classes.group("nominal2"),
                            "kind": "nominatives",
                        },
                    ],
                    "statutes_adapted": False,
                },
            )
        )
        leftover = leftover.replace(fr_legal_postfix_classes.group(0), " ")
        event_types.add("capital_changed")
    fr_legal_multiple = _FR_LEGAL_BEARER_CONVERSION_MULTIPLE_CLASSES.search(leftover)
    if fr_legal_multiple:
        raw_date = fr_legal_multiple.group("date")
        paid = fr_legal_multiple.group("paid") or fr_legal_multiple.group("total")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.legal_bearer_conversion.v4",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": (
                        _swiss_date(raw_date)
                        if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", raw_date)
                        else _french_written_date(raw_date)
                    ),
                    "capital_total": fr_legal_multiple.group("total"),
                    "paid": paid,
                    "paid_in_full": paid == fr_legal_multiple.group("total"),
                    "from_kind": "au porteur",
                    "to_kind": "nominatives",
                    "share_classes": [
                        {
                            "count": int(fr_legal_multiple.group("count1").replace("'", "")),
                            "nominal": fr_legal_multiple.group("nominal1"),
                            "rights": fr_legal_multiple.group("rights1").strip(),
                        },
                        {
                            "count": int(fr_legal_multiple.group("count2").replace("'", "")),
                            "nominal": fr_legal_multiple.group("nominal2"),
                        },
                    ],
                    "statutes_adapted": False,
                },
            )
        )
        leftover = leftover.replace(fr_legal_multiple.group(0), " ")
        event_types.add("capital_changed")
    fr_legal_classes = _FR_LEGAL_BEARER_CONVERSION_CLASSES.search(leftover)
    if fr_legal_classes:
        raw_date = fr_legal_classes.group("date")
        paid = fr_legal_classes.group("paid") or fr_legal_classes.group("total")
        share_classes = [
            {
                "class": fr_legal_classes.group("class1"),
                "count": int(fr_legal_classes.group("count1").replace("'", "")),
                "nominal": fr_legal_classes.group("nominal1"),
            },
            {
                "class": fr_legal_classes.group("class2"),
                "count": int(fr_legal_classes.group("count2").replace("'", "")),
                "nominal": fr_legal_classes.group("nominal2"),
            },
        ]
        payload = {
            "kind": "bearer_to_registered_conversion",
            "legal_basis": "by_operation_of_law",
            "conversion_date": (
                _swiss_date(raw_date)
                if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", raw_date)
                else _french_written_date(raw_date)
            ),
            "capital_total": fr_legal_classes.group("total"),
            "paid": paid,
            "paid_in_full": paid == fr_legal_classes.group("total"),
            "from_kind": "au porteur",
            "to_kind": "nominatives",
            "share_classes": share_classes,
            "statutes_adapted": False,
        }
        if fr_legal_classes.group("rights"):
            payload["rights"] = fr_legal_classes.group("rights").strip()
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.legal_bearer_conversion.v3",
                payload,
            )
        )
        leftover = leftover.replace(fr_legal_classes.group(0), " ")
        event_types.add("capital_changed")
    fr_legal_conversion = _FR_LEGAL_BEARER_CONVERSION.search(leftover)
    if fr_legal_conversion:
        raw_date = fr_legal_conversion.group("date")
        from_count = fr_legal_conversion.group("from_count")
        from_nominal = fr_legal_conversion.group("from_nominal")
        paid = fr_legal_conversion.group("paid")
        fully_paid = bool(fr_legal_conversion.group("fully_paid")) or (
            paid == fr_legal_conversion.group("total")
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.legal_bearer_conversion.v1",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": (
                        _swiss_date(raw_date)
                        if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", raw_date)
                        else _french_written_date(raw_date)
                    ),
                    "capital_total": fr_legal_conversion.group("total"),
                    "paid": (
                        fr_legal_conversion.group("total")
                        if fully_paid
                        else paid
                    ),
                    "paid_in_full": fully_paid,
                    "from_count": int(
                        (from_count or fr_legal_conversion.group("to_count")).replace("'", "")
                    ),
                    "from_nominal": from_nominal or fr_legal_conversion.group("to_nominal"),
                    "from_kind": fr_legal_conversion.group("from_kind") or "au porteur",
                    "to_count": int(fr_legal_conversion.group("to_count").replace("'", "")),
                    "to_nominal": fr_legal_conversion.group("to_nominal"),
                    "to_kind": "nominatives",
                    "reported_capital_kind": (
                        fr_legal_conversion.group("kind_after")
                        or fr_legal_conversion.group("kind_before")
                    ),
                    "statutes_adapted": False,
                },
            )
        )
        leftover = leftover.replace(fr_legal_conversion.group(0), " ")
        event_types.add("capital_changed")
    fr_legal_shares_last = _FR_LEGAL_BEARER_CONVERSION_SHARES_LAST.search(leftover)
    if fr_legal_shares_last:
        raw_date = fr_legal_shares_last.group("date")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.legal_bearer_conversion.v2",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": (
                        _swiss_date(raw_date)
                        if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", raw_date)
                        else _french_written_date(raw_date)
                    ),
                    "from_count": int(
                        fr_legal_shares_last.group("from_count").replace("'", "")
                    ),
                    "from_nominal": fr_legal_shares_last.group("from_nominal"),
                    "from_kind": fr_legal_shares_last.group("from_kind"),
                    "to_count": int(
                        fr_legal_shares_last.group("to_count").replace("'", "")
                    ),
                    "to_nominal": fr_legal_shares_last.group("to_nominal"),
                    "to_kind": fr_legal_shares_last.group("to_kind"),
                    "statutes_adapted": False,
                },
            )
        )
        leftover = leftover.replace(fr_legal_shares_last.group(0), " ")
        event_types.add("capital_changed")
    corrected_conversion = _FR_LEGAL_BEARER_CONVERSION_CORRECTED.search(leftover)
    if corrected_conversion:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.legal_bearer_conversion_corrected.v1",
                {
                    "kind": "bearer_to_registered_conversion",
                    "action": "corrected",
                    "actual_basis": "shareholders_resolution",
                    "decision_date": _swiss_date(corrected_conversion.group("date")),
                    "automatic_conversion_removed": True,
                },
            )
        )
        leftover = leftover.replace(corrected_conversion.group(0), " ")
        event_types.add("capital_changed")
    adapted_conversion = _FR_ADAPTED_BEARER_CONVERSION.search(leftover)
    if adapted_conversion:
        paid = adapted_conversion.group("paid") or adapted_conversion.group("total")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.legal_bearer_conversion_adapted.v1",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _french_written_date(
                        adapted_conversion.group("conversion_date")
                    ),
                    "adaptation_date": _swiss_date(
                        adapted_conversion.group("adaptation_date")
                    ),
                    "capital_total": adapted_conversion.group("total"),
                    "paid": paid,
                    "paid_in_full": paid == adapted_conversion.group("total"),
                    "from_kind": "au porteur",
                    "to_kind": "nominatives",
                    "to_count": int(adapted_conversion.group("count").replace("'", "")),
                    "to_nominal": adapted_conversion.group("nominal"),
                    "restriction": (adapted_conversion.group("restriction") or "").strip()
                    or None,
                    "statutes_adapted": True,
                },
            )
        )
        leftover = leftover.replace(adapted_conversion.group(0), " ")
        event_types.add("capital_changed")
    adapted_conversion_with_capital = (
        _FR_LEGAL_BEARER_CONVERSION_ADAPTED_CAPITAL.search(leftover)
    )
    if adapted_conversion_with_capital:
        paid = (
            adapted_conversion_with_capital.group("paid")
            or adapted_conversion_with_capital.group("total")
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.legal_bearer_conversion_adapted.v3",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _swiss_date(
                        adapted_conversion_with_capital.group("conversion_date")
                    ),
                    "adaptation_date": _swiss_date(
                        adapted_conversion_with_capital.group("adaptation_date")
                    ),
                    "capital_total": adapted_conversion_with_capital.group("total"),
                    "paid": paid,
                    "paid_in_full": paid
                    == adapted_conversion_with_capital.group("total"),
                    "from_kind": "au porteur",
                    "to_kind": "nominatives",
                    "to_count": int(
                        adapted_conversion_with_capital.group("count").replace("'", "")
                    ),
                    "to_nominal": adapted_conversion_with_capital.group("nominal"),
                    "restriction": (
                        adapted_conversion_with_capital.group("restriction") or ""
                    ).strip()
                    or None,
                    "statutes_adapted": True,
                },
            )
        )
        leftover = leftover.replace(adapted_conversion_with_capital.group(0), " ")
        event_types.add("capital_changed")
    bearer_conversion_with_capital = _FR_BEARER_CONVERSION_WITH_CAPITAL.search(
        leftover
    )
    if bearer_conversion_with_capital:
        paid = (
            bearer_conversion_with_capital.group("paid")
            or bearer_conversion_with_capital.group("total")
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.bearer_conversion_capital.v1",
                {
                    "kind": "bearer_to_registered_conversion",
                    "from_kind": "au porteur",
                    "to_kind": "nominatives",
                    "capital_total": bearer_conversion_with_capital.group("total"),
                    "paid": paid,
                    "paid_in_full": paid
                    == bearer_conversion_with_capital.group("total"),
                    "to_count": int(
                        bearer_conversion_with_capital.group("count").replace("'", "")
                    ),
                    "to_nominal": bearer_conversion_with_capital.group("nominal"),
                    "restriction": bearer_conversion_with_capital.group(
                        "restriction"
                    ).strip(),
                },
            )
        )
        leftover = leftover.replace(bearer_conversion_with_capital.group(0), " ")
        event_types.add("capital_changed")
    adapted_conversion_notice = _FR_LEGAL_BEARER_CONVERSION_ADAPTED_NOTICE.search(
        leftover
    )
    if adapted_conversion_notice:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.legal_bearer_conversion_adapted.v2",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _swiss_date(
                        adapted_conversion_notice.group("conversion_date")
                    ),
                    "adaptation_date": _swiss_date(
                        adapted_conversion_notice.group("adaptation_date")
                    ),
                    "registration_date": _swiss_date(
                        adapted_conversion_notice.group("registration_date")
                    ),
                    "from_kind": "au porteur",
                    "to_kind": "nominatives",
                    "statutes_adapted": True,
                },
            )
        )
        leftover = leftover.replace(adapted_conversion_notice.group(0), " ")
        event_types.add("capital_changed")
    adapted_conversion_notice_alt = (
        _FR_ADAPTED_BEARER_CONVERSION_NOTICE_ALT.search(leftover)
    )
    if adapted_conversion_notice_alt:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.legal_bearer_conversion_adapted.v4",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _french_written_date(
                        adapted_conversion_notice_alt.group("conversion_date")
                    ),
                    "adaptation_date": _swiss_date(
                        adapted_conversion_notice_alt.group("adaptation_date")
                    ),
                    "from_kind": "au porteur",
                    "to_kind": "nominatives",
                    "statutes_adapted": True,
                },
            )
        )
        leftover = leftover.replace(adapted_conversion_notice_alt.group(0), " ")
        event_types.add("capital_changed")
    adapted_conversion_notice_at_date = (
        _FR_ADAPTED_BEARER_CONVERSION_NOTICE_AT_DATE.search(leftover)
    )
    if adapted_conversion_notice_at_date:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.legal_bearer_conversion_adapted.v6",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _french_written_date(
                        adapted_conversion_notice_at_date.group("conversion_date")
                    ),
                    "adaptation_date": _swiss_date(
                        adapted_conversion_notice_at_date.group("adaptation_date")
                    ),
                    "from_kind": "au porteur",
                    "to_kind": "nominatives",
                    "statutes_adapted": True,
                },
            )
        )
        leftover = leftover.replace(adapted_conversion_notice_at_date.group(0), " ")
        event_types.add("capital_changed")
    adapted_conversion_notice_no_date = (
        _FR_ADAPTED_BEARER_CONVERSION_NOTICE_NO_DATE.search(leftover)
    )
    if adapted_conversion_notice_no_date:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.legal_bearer_conversion_adapted.v5",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": None,
                    "adaptation_date": _swiss_date(
                        adapted_conversion_notice_no_date.group("adaptation_date")
                    ),
                    "from_kind": "au porteur",
                    "to_kind": "nominatives",
                    "statutes_adapted": True,
                },
            )
        )
        leftover = leftover.replace(adapted_conversion_notice_no_date.group(0), " ")
        event_types.add("capital_changed")
    for share_change, share_rule in (
        (_FR_NEW_SHARES.search(leftover), "fr.text.share_structure.v1"),
        (_FR_BEARER_CONVERSION.search(leftover), "fr.text.bearer_conversion.v1"),
    ):
        if not share_change:
            continue
        payload = {
            "from_count": int(share_change.group("from_count").replace("'", "")),
            "from_nominal": share_change.group("from_nominal"),
            "from_kind": share_change.group("from_kind").strip(),
            "to_count": int(share_change.group("to_count").replace("'", "")),
            "to_nominal": share_change.group("to_nominal"),
            "to_kind": share_change.group("to_kind").strip(),
        }
        restriction = (share_change.group("restriction") or "").strip()
        if restriction:
            payload["restriction"] = restriction
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                share_rule,
                payload,
            )
        )
        leftover = leftover.replace(share_change.group(0), " ")
        event_types.add("capital_changed")
    removed_fr_conversion_notice = (
        _FR_LEGAL_BEARER_CONVERSION_NOTICE_REMOVED.search(leftover)
    )
    if removed_fr_conversion_notice:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.legal_bearer_conversion_notice_removed.v1",
                {
                    "kind": "bearer_to_registered_conversion_notice",
                    "action": "removed",
                    "conversion_date": _french_written_date(
                        removed_fr_conversion_notice.group("date")
                    ),
                    "statutes_adapted": True,
                },
            )
        )
        leftover = leftover.replace(removed_fr_conversion_notice.group(0), " ")
        event_types.add("capital_changed")
    fr_conversion_notice = _FR_LEGAL_BEARER_CONVERSION_NOTICE.search(leftover)
    if fr_conversion_notice:
        raw_date = fr_conversion_notice.group("date")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.legal_bearer_conversion_notice.v1",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": (
                        _swiss_date(raw_date)
                        if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", raw_date)
                        else _french_written_date(raw_date)
                    ),
                    "from_kind": "au porteur",
                    "to_kind": "nominatives",
                    "statutes_adapted": False,
                },
            )
        )
        leftover = leftover.replace(fr_conversion_notice.group(0), " ")
        event_types.add("capital_changed")
    publication_organ = (
        _IT_PUBLICATION_ORGAN.search(leftover)
        if lang == "it"
        else _FR_PUBLICATION_ORGAN.search(leftover)
        if lang == "fr"
        else _DE_PUBLICATION_ORGAN.search(leftover)
    )
    if publication_organ:
        publication_organ_lang = (
            "it"
            if publication_organ.re is _IT_PUBLICATION_ORGAN
            else "fr"
            if publication_organ.re is _FR_PUBLICATION_ORGAN
            else "de"
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "organization_changed",
                f"{publication_organ_lang}.text.publication_organ.v1",
                {"kind": "publication_organ", "to": publication_organ.group("to").strip()},
            )
        )
        leftover = leftover.replace(publication_organ.group(0), " ")
    simultaneous_capital = _DE_SIMULTANEOUS_CAPITAL_CHANGE.search(leftover)
    if simultaneous_capital:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "de.text.simultaneous_capital_change.v1",
                {
                    "kind": "capital_decrease_and_increase",
                    "decrease_date": _swiss_date(
                        simultaneous_capital.group("decrease_date")
                    ),
                    "decrease_count": int(
                        simultaneous_capital.group("decrease_count").replace("'", "")
                    ),
                    "decrease_kind": simultaneous_capital.group("decrease_kind").strip(),
                    "decrease_nominal": simultaneous_capital.group("decrease_nominal"),
                    "increase_date": _swiss_date(
                        simultaneous_capital.group("increase_date")
                    ),
                    "increase_count": int(
                        simultaneous_capital.group("increase_count").replace("'", "")
                    ),
                    "increase_kind": simultaneous_capital.group("increase_kind").strip(),
                    "increase_nominal": simultaneous_capital.group("increase_nominal"),
                    "increase_paid_in_full": bool(
                        simultaneous_capital.group("increase_paid")
                    ),
                },
            )
        )
        leftover = leftover.replace(simultaneous_capital.group(0), " ")
        event_types.add("capital_changed")
    recapitalization = _DE_SIMULTANEOUS_CAPITAL_RECAPITALIZATION.search(leftover)
    if recapitalization:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "de.text.simultaneous_capital_change.v2",
                {
                    "kind": "capital_decrease_and_increase",
                    "date": _swiss_date(recapitalization.group("date")),
                    "decrease_count": int(
                        recapitalization.group("decrease_count").replace("'", "")
                    ),
                    "decrease_kind": recapitalization.group("decrease_kind").strip(),
                    "decrease_nominal": recapitalization.group("decrease_nominal"),
                    "decrease_purpose": recapitalization.group("purpose").strip(),
                    "capital_total": recapitalization.group("capital_total"),
                    "increase_count": int(
                        recapitalization.group("increase_count").replace("'", "")
                    ),
                    "increase_kind": recapitalization.group("increase_kind").strip(),
                    "increase_nominal": recapitalization.group("increase_nominal"),
                    "increase_paid_in_full": bool(
                        recapitalization.group("increase_paid")
                    ),
                },
            )
        )
        leftover = leftover.replace(recapitalization.group(0), " ")
        event_types.add("capital_changed")
    fr_recapitalization = _FR_SIMULTANEOUS_CAPITAL_RECAPITALIZATION.search(leftover)
    if fr_recapitalization:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.simultaneous_capital_change.v1",
                {
                    "kind": "capital_decrease_and_increase",
                    "qualified_fact": True,
                    "from_total": fr_recapitalization.group("from_total"),
                    "reduced_total": fr_recapitalization.group("reduced_total"),
                    "decrease_reason": fr_recapitalization.group("reason"),
                    "decrease_count": int(
                        fr_recapitalization.group("decrease_count").replace("'", "")
                    ),
                    "decrease_kind": fr_recapitalization.group("decrease_kind"),
                    "decrease_nominal": fr_recapitalization.group("decrease_nominal"),
                    "to_total": fr_recapitalization.group("to_total"),
                    "increase_count": int(
                        fr_recapitalization.group("increase_count").replace("'", "")
                    ),
                    "increase_kind": fr_recapitalization.group("increase_kind"),
                    "increase_nominal": fr_recapitalization.group("increase_nominal"),
                    "increase_paid_in_full": True,
                    "compensation_claim": fr_recapitalization.group("compensation"),
                },
            )
        )
        leftover = leftover.replace(fr_recapitalization.group(0), " ")
        event_types.add("capital_changed")
    bearer_authorized = _FR_BEARER_SHARES_AUTHORIZED.search(leftover)
    if bearer_authorized:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.bearer_shares_authorized.v1",
                {
                    "kind": "bearer_shares_authorized",
                    "reason": "listed_participation_securities",
                },
            )
        )
        leftover = leftover.replace(bearer_authorized.group(0), " ")
        event_types.add("capital_changed")
    de_bearer_authorized = _DE_BEARER_SHARES_AUTHORIZED.search(leftover)
    if de_bearer_authorized:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "de.text.bearer_shares_authorized.v1",
                {
                    "kind": "bearer_shares_authorized",
                    "reason": "listed_participation_securities",
                },
            )
        )
        leftover = leftover.replace(de_bearer_authorized.group(0), " ")
        event_types.add("capital_changed")
    intermediated_bearer_shares = (
        _DE_BEARER_SHARES_AS_INTERMEDIATED_SECURITIES.search(leftover)
    )
    if intermediated_bearer_shares:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "de.text.bearer_shares_authorized.v2",
                {
                    "kind": "bearer_shares_authorized",
                    "reason": "intermediated_securities",
                },
            )
        )
        leftover = leftover.replace(intermediated_bearer_shares.group(0), " ")
        event_types.add("capital_changed")
    fr_intermediated_bearer_shares = (
        _FR_BEARER_SHARES_AS_INTERMEDIATED_SECURITIES.search(leftover)
    )
    if fr_intermediated_bearer_shares:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.bearer_shares_authorized.v2",
                {
                    "kind": "bearer_shares_authorized",
                    "reason": "intermediated_securities",
                },
            )
        )
        leftover = leftover.replace(fr_intermediated_bearer_shares.group(0), " ")
        event_types.add("capital_changed")
    authorized_capital = _FR_AUTHORIZED_CAPITAL_CLAUSE.search(leftover)
    if authorized_capital:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.authorized_capital_clause.v1",
                {
                    "kind": "authorized_capital_clause_modified",
                    "original_decision_date": _french_written_date(
                        authorized_capital.group("original_date")
                    ),
                    "decision_date": _french_written_date(
                        authorized_capital.group("date")
                    ),
                },
            )
        )
        leftover = leftover.replace(authorized_capital.group(0), " ")
        event_types.add("capital_changed")
    conditional_capital_clause = _FR_CONDITIONAL_CAPITAL_CLAUSE.search(leftover)
    if conditional_capital_clause:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.conditional_capital_clause.v2",
                {
                    "kind": "conditional_capital_clause_modified",
                    "action": "modified",
                    "original_decision_date": _french_written_date(
                        conditional_capital_clause.group("original_date")
                    ),
                    "decision_date": _french_written_date(
                        conditional_capital_clause.group("date")
                    ),
                },
            )
        )
        leftover = leftover.replace(conditional_capital_clause.group(0), " ")
        event_types.add("capital_changed")
    conditional_participation_capital = (
        _FR_CONDITIONAL_PARTICIPATION_CAPITAL_CLAUSE.search(leftover)
    )
    if conditional_participation_capital:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.conditional_participation_capital_clause.v1",
                {
                    "kind": "conditional_participation_capital_clause_modified",
                    "original_decision_date": _french_written_date(
                        conditional_participation_capital.group("original_date")
                    ),
                    "decision_date": _french_written_date(
                        conditional_participation_capital.group("date")
                    ),
                },
            )
        )
        leftover = leftover.replace(conditional_participation_capital.group(0), " ")
        event_types.add("capital_changed")
    social_capital = _FR_SOCIAL_CAPITAL_COMPOSITION.search(leftover)
    if social_capital:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.social_capital_composition.v1",
                {
                    "kind": "share_structure",
                    "currency": "CHF",
                    "total": social_capital.group("total"),
                    "shares_count": int(
                        social_capital.group("count").replace("'", "")
                    ),
                    "shares_nominal": social_capital.group("nominal"),
                    **(
                        {"holder": social_capital.group("holder").strip()}
                        if social_capital.group("holder")
                        else {}
                    ),
                },
            )
        )
        leftover = leftover.replace(social_capital.group(0), " ")
        event_types.add("capital_changed")
    share_restriction_removed_with_capital = (
        _FR_SHARE_TRANSFER_RESTRICTION_REMOVED_WITH_CAPITAL.search(leftover)
    )
    if share_restriction_removed_with_capital:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.share_transfer_restriction_removed.v2",
                {
                    "kind": "share_transfer_restriction",
                    "action": "removed",
                    "basis": "statutes",
                    "capital_total": share_restriction_removed_with_capital.group(
                        "total"
                    ),
                    "paid_in_full": True,
                    "shares_count": int(
                        share_restriction_removed_with_capital.group(
                            "capital_count"
                        ).replace("'", "")
                    ),
                    "nominal": share_restriction_removed_with_capital.group(
                        "capital_nominal"
                    ),
                },
            )
        )
        leftover = leftover.replace(
            share_restriction_removed_with_capital.group(0), " "
        )
        event_types.add("capital_changed")
    share_restriction_with_capital = (
        _FR_SHARE_TRANSFER_RESTRICTION_WITH_CAPITAL.search(leftover)
    )
    if share_restriction_with_capital:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.share_transfer_restriction.v3",
                {
                    "kind": "share_transfer_restricted",
                    "action": "added",
                    "basis": "statutes",
                    "capital_total": share_restriction_with_capital.group("total"),
                    "paid_in_full": True,
                    "shares_count": int(
                        share_restriction_with_capital.group("capital_count").replace(
                            "'", ""
                        )
                    ),
                    "nominal": share_restriction_with_capital.group(
                        "capital_nominal"
                    ),
                },
            )
        )
        leftover = leftover.replace(share_restriction_with_capital.group(0), " ")
        event_types.add("capital_changed")
    generic_restriction_with_capital = (
        _FR_SHARE_TRANSFER_RESTRICTION_CAPITAL_GENERIC.search(leftover)
    )
    if generic_restriction_with_capital:
        total = generic_restriction_with_capital.group("total")
        paid = generic_restriction_with_capital.group("paid")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.share_transfer_restriction.v4",
                {
                    "kind": "share_transfer_restricted",
                    "action": "added",
                    "basis": "statutes",
                    "capital_total": total,
                    "paid": paid,
                    "paid_in_full": paid == total,
                    "shares_count": int(
                        generic_restriction_with_capital.group("count").replace(
                            "'", ""
                        )
                    ),
                    "nominal": generic_restriction_with_capital.group("nominal"),
                },
            )
        )
        leftover = leftover.replace(generic_restriction_with_capital.group(0), " ")
        event_types.add("capital_changed")
    share_restriction = _FR_SHARE_TRANSFER_RESTRICTION.search(leftover)
    if share_restriction:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.share_transfer_restriction.v1",
                {
                    "kind": "share_transfer_restricted",
                    "action": "added",
                    "shares_count": int(
                        share_restriction.group("count").replace("'", "")
                    ),
                    "nominal": share_restriction.group("nominal"),
                },
            )
        )
        leftover = leftover.replace(share_restriction.group(0), " ")
        event_types.add("capital_changed")
    generic_share_restriction = _FR_SHARE_TRANSFER_RESTRICTION_GENERIC.search(leftover)
    if generic_share_restriction:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.share_transfer_restriction.v2",
                {
                    "kind": "share_transfer_restricted",
                    "action": "added",
                    "basis": "statutes",
                },
            )
        )
        leftover = leftover.replace(generic_share_restriction.group(0), " ")
        event_types.add("capital_changed")
    quota_transfer_fr = _FR_QUOTA_TRANSFER_STATUTE.search(leftover)
    if quota_transfer_fr:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "fr.text.quota_transfer_rules.v1",
                {
                    "kind": "quota_transfer_rules",
                    "deviates_from_law": True,
                    "raw": quota_transfer_fr.group(0).strip(),
                },
            )
        )
        leftover = leftover.replace(quota_transfer_fr.group(0), " ")
    purpose_non_public = _FR_PURPOSE_NON_PUBLIC.search(leftover)
    if purpose_non_public:
        leftover = leftover.replace(purpose_non_public.group(0), " ")
        if "purpose_changed" not in event_types:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "purpose_changed",
                    "fr.text.purpose_non_public.v1",
                    {"scope": "non_publication_point", "raw": purpose_non_public.group(0).strip()},
                )
            )
            event_types.add("purpose_changed")
    head_office_purpose = _FR_HEAD_OFFICE_PURPOSE_NOT_PUBLISHED.search(leftover)
    if head_office_purpose:
        leftover = leftover.replace(head_office_purpose.group(0), " ")
        if "purpose_changed" not in event_types:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "purpose_changed",
                    "fr.text.head_office_purpose.v1",
                    {
                        "scope": "head_office",
                        "branch_value_published": False,
                        "raw": head_office_purpose.group(0).strip(),
                    },
                )
            )
            event_types.add("purpose_changed")
    it_transfer_restriction_removed = _IT_SHARE_TRANSFER_RESTRICTION_REMOVED.search(
        leftover
    )
    if it_transfer_restriction_removed:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "it.text.share_transfer_restriction_removed.v1",
                {
                    "kind": "share_transfer_restriction",
                    "action": "removed",
                    "legal_basis": "art. 685a cpv. 3 CO",
                },
            )
        )
        leftover = leftover.replace(it_transfer_restriction_removed.group(0), " ")
    transfer_restriction = _IT_SHARE_TRANSFER_RESTRICTION.search(leftover)
    if transfer_restriction:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "it.text.share_transfer_restriction.v1",
                {
                    "kind": "share_transfer_restricted",
                    "raw": transfer_restriction.group(0).strip(),
                },
            )
        )
        leftover = leftover.replace(transfer_restriction.group(0), " ")
    transfer_restriction_removed = _FR_SHARE_TRANSFER_RESTRICTION_REMOVED.search(leftover)
    if transfer_restriction_removed:
        transfer_payload = {
            "kind": "share_transfer_restriction",
            "action": "removed",
            "raw": transfer_restriction_removed.group(0).strip(),
        }
        count = (
            transfer_restriction_removed.group("count")
            or transfer_restriction_removed.group("count_alt")
        )
        nominal = (
            transfer_restriction_removed.group("nominal")
            or transfer_restriction_removed.group("nominal_alt")
        )
        if count:
            transfer_payload["shares_count"] = int(
                count.replace("'", "")
            )
            transfer_payload["nominal"] = nominal
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "fr.text.share_transfer_restriction_removed.v1",
                transfer_payload,
            )
        )
        leftover = leftover.replace(transfer_restriction_removed.group(0), " ")
    quota_transfer = _IT_QUOTA_TRANSFER_STATUTE.search(leftover)
    if quota_transfer:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "it.text.quota_transfer_rules.v1",
                {
                    "kind": "quota_transfer_rules",
                    "raw": quota_transfer.group(0).strip(),
                },
            )
        )
        leftover = leftover.replace(quota_transfer.group(0), " ")
    share_conversion = _FR_SHARE_CONVERSION.search(leftover)
    if share_conversion:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.share_conversion.v1",
                {
                    "count": int(share_conversion.group("count").replace("'", "")),
                    "nominal": share_conversion.group("nominal"),
                    "from_kind": "au porteur",
                    "to_kind": share_conversion.group("to_kind"),
                },
            )
        )
        leftover = leftover.replace(share_conversion.group(0), " ")
        event_types.add("capital_changed")
        leftover = _FR_CAPITAL_RECAP.sub(" ", leftover)
        notice = _FR_SHAREHOLDER_NOTICE.search(leftover)
        if notice:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "statutes_changed",
                    "fr.text.shareholder_notice.v1",
                    {"raw": notice.group(0).strip()},
                )
            )
            leftover = leftover.replace(notice.group(0), " ")
    de_bankruptcy_suspended_by_court = _DE_BANKRUPTCY_EFFECT_SUSPENDED_BY_COURT.search(
        leftover
    )
    if de_bankruptcy_suspended_by_court:
        leftover = leftover.replace(de_bankruptcy_suspended_by_court.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.bankruptcy_effect_suspended.v2",
                {
                    "kind": "bankruptcy_effect_suspended",
                    "bankruptcy_date": _swiss_date(
                        de_bankruptcy_suspended_by_court.group("bankruptcy_date")
                    ),
                    "authority": de_bankruptcy_suspended_by_court.group("authority").strip(),
                    "bankruptcy_court": de_bankruptcy_suspended_by_court.group("court").strip(),
                    "bankruptcy_registration_removed": True,
                },
            )
        )
        event_types.add("status_changed")
    de_bankruptcy_suspended = _DE_BANKRUPTCY_EFFECT_SUSPENDED.search(leftover)
    if de_bankruptcy_suspended:
        leftover = leftover.replace(de_bankruptcy_suspended.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.bankruptcy_effect_suspended.v1",
                {
                    "kind": "bankruptcy_effect_suspended",
                    "decision_date": _swiss_date(
                        de_bankruptcy_suspended.group("decision_date")
                    ),
                    "bankruptcy_date": _swiss_date(
                        de_bankruptcy_suspended.group("bankruptcy_date")
                    ),
                    "authority": de_bankruptcy_suspended.group("authority").strip(),
                    "bankruptcy_registration_removed": True,
                },
            )
        )
        event_types.add("status_changed")
    suspended_decision = _DE_BANKRUPTCY_EFFECT_SUSPENDED_DECISION.search(leftover)
    if suspended_decision:
        leftover = leftover.replace(suspended_decision.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.bankruptcy_effect_suspended.v3",
                {
                    "kind": "bankruptcy_effect_suspended",
                    "decision_date": _swiss_date(
                        suspended_decision.group("decision_date")
                    ),
                    "bankruptcy_date": _swiss_date(
                        suspended_decision.group("bankruptcy_date")
                    ),
                    "authority": suspended_decision.group("authority").strip(),
                    "bankruptcy_court": suspended_decision.group("court").strip(),
                },
            )
        )
        event_types.add("status_changed")
    direct_owner_bankruptcy_suspended = (
        _DE_OWNER_BANKRUPTCY_EFFECT_SUSPENDED_DIRECT.search(leftover)
    )
    if direct_owner_bankruptcy_suspended:
        leftover = leftover.replace(direct_owner_bankruptcy_suspended.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.owner_bankruptcy_effect_suspended.v2",
                {
                    "kind": "bankruptcy_effect_suspended",
                    "scope": "owner",
                    "decision_date": _swiss_date(
                        direct_owner_bankruptcy_suspended.group("decision_date")
                    ),
                    "bankruptcy_decision_date": _swiss_date(
                        direct_owner_bankruptcy_suspended.group("bankruptcy_date")
                    ),
                    "bankruptcy_effective_date": _swiss_date(
                        direct_owner_bankruptcy_suspended.group("effective_date")
                    ),
                    "bankruptcy_effective_time": direct_owner_bankruptcy_suspended.group(
                        "time"
                    ),
                    "authority": direct_owner_bankruptcy_suspended.group(
                        "authority"
                    ).strip(),
                    "bankruptcy_court": direct_owner_bankruptcy_suspended.group(
                        "court"
                    ).strip(),
                    "bankruptcy_registration_removed": True,
                },
            )
        )
        event_types.add("status_changed")
    owner_bankruptcy_suspended = _DE_OWNER_BANKRUPTCY_EFFECT_SUSPENDED.search(leftover)
    if owner_bankruptcy_suspended:
        outcome = owner_bankruptcy_suspended.group("outcome")
        leftover = leftover.replace(owner_bankruptcy_suspended.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.owner_bankruptcy_effect_suspended.v1",
                {
                    "kind": "bankruptcy_effect_suspended",
                    "scope": "owner",
                    "decision_date": _swiss_date(
                        owner_bankruptcy_suspended.group("decision_date")
                    ),
                    "bankruptcy_date": _swiss_date(
                        owner_bankruptcy_suspended.group("bankruptcy_date")
                    ),
                    "authority": owner_bankruptcy_suspended.group("authority").strip(),
                    "bankruptcy_court": owner_bankruptcy_suspended.group("court").strip(),
                    "business_continues": outcome.lower().startswith("besteht"),
                    "bankruptcy_registration_removed": "gestrichen" in outcome.lower(),
                },
            )
        )
        event_types.add("status_changed")
    appeal_suspended = _DE_APPEAL_EFFECT_SUSPENDED.search(leftover)
    if appeal_suspended:
        leftover = leftover.replace(appeal_suspended.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.appeal_effect_suspended.v1",
                {
                    "kind": "appeal_effect_suspended",
                    "decision_date": _swiss_date(
                        appeal_suspended.group("decision_date")
                    ),
                },
            )
        )
        event_types.add("status_changed")
    revoked_decision = _DE_APPEAL_DECISION_REVOKED.search(leftover)
    if revoked_decision:
        leftover = leftover.replace(revoked_decision.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.appeal_decision_revoked.v1",
                {
                    "kind": "court_decision_revoked",
                    "decision_date": _swiss_date(revoked_decision.group("decision_date")),
                    "original_decision_date": _swiss_date(
                        revoked_decision.group("original_date")
                    ),
                    "authority": revoked_decision.group("authority").strip(),
                    "original_court": revoked_decision.group("court").strip(),
                    "section": "1",
                },
            )
        )
        event_types.add("status_changed")
    proceedings_suspended = _DE_BANKRUPTCY_PROCEEDINGS_SUSPENDED_NO_ASSETS.search(leftover)
    if proceedings_suspended:
        leftover = leftover.replace(proceedings_suspended.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.bankruptcy_proceedings_suspended.v1",
                {
                    "kind": "bankruptcy_proceedings_suspended",
                    "reason": "lack_of_assets",
                    "date": _swiss_date(proceedings_suspended.group("date")),
                    "authority": proceedings_suspended.group("authority").strip(),
                },
            )
        )
        event_types.add("status_changed")
    bankruptcy_closed_by_decision = _DE_BANKRUPTCY_CLOSED_BY_DECISION.search(leftover)
    if bankruptcy_closed_by_decision:
        leftover = leftover.replace(bankruptcy_closed_by_decision.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.bankruptcy_closed.v1",
                {
                    "kind": "bankruptcy_closed",
                    "decision_date": _swiss_date(
                        bankruptcy_closed_by_decision.group("date")
                    ),
                    "authority": bankruptcy_closed_by_decision.group(
                        "authority"
                    ).strip(),
                },
            )
        )
        event_types.add("status_changed")
    bankruptcy_dissolution = _DE_BANKRUPTCY_DISSOLUTION.search(leftover)
    if bankruptcy_dissolution:
        leftover = leftover.replace(bankruptcy_dissolution.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.bankruptcy_dissolution.v1",
                {
                    "kind": "bankruptcy_opened",
                    "decision_date": _swiss_date(
                        bankruptcy_dissolution.group("decision_date")
                    ),
                    "effective_date": _swiss_date(
                        bankruptcy_dissolution.group("effective_date")
                    ),
                    "effective_time": bankruptcy_dissolution.group("time").replace(
                        ".", ":"
                    ),
                    "authority": bankruptcy_dissolution.group("authority").strip(),
                    "entity_dissolved": True,
                },
            )
        )
        event_types.add("status_changed")
    removed_bankruptcy_suspension = _DE_REMOVED_BANKRUPTCY_SUSPENSION.search(leftover)
    if removed_bankruptcy_suspension:
        leftover = leftover.replace(removed_bankruptcy_suspension.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.bankruptcy_suspension_removed.v1",
                {
                    "kind": "bankruptcy_proceedings_suspension",
                    "action": "removed",
                    "reason": "lack_of_assets",
                    "date": _swiss_date(removed_bankruptcy_suspension.group("date")),
                    "authority": removed_bankruptcy_suspension.group("authority").strip(),
                },
            )
        )
        event_types.add("status_changed")
    removed_owner_bankruptcy = _DE_REMOVED_OWNER_BANKRUPTCY.search(leftover)
    if removed_owner_bankruptcy:
        leftover = leftover.replace(removed_owner_bankruptcy.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.owner_bankruptcy_removed.v1",
                {
                    "kind": "bankruptcy_opened",
                    "action": "removed",
                    "decision_date": _swiss_date(
                        removed_owner_bankruptcy.group("decision_date")
                    ),
                    "effective_date": _swiss_date(
                        removed_owner_bankruptcy.group("effective_date")
                    ),
                    "effective_time": removed_owner_bankruptcy.group("time"),
                    "authority": removed_owner_bankruptcy.group("authority").strip(),
                    "scope": "sole_proprietor",
                },
            )
        )
        event_types.add("status_changed")
    moratorium_granted = _DE_COMPOSITION_MORATORIUM_GRANTED.search(leftover)
    if moratorium_granted:
        duration_raw = moratorium_granted.group("duration").lower()
        duration_months = {"einem": 1, "sechs": 6}.get(
            duration_raw, int(duration_raw) if duration_raw.isdigit() else None
        )
        leftover = leftover.replace(moratorium_granted.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.composition_moratorium_granted.v1",
                {
                    "kind": "composition_moratorium_granted",
                    "decision_date": _swiss_date(
                        moratorium_granted.group("decision_date")
                    ),
                    "start_date": _swiss_date(moratorium_granted.group("start_date")),
                    "until": _swiss_date(moratorium_granted.group("until")),
                    "duration_months": duration_months,
                    "commissioner": moratorium_granted.group("commissioner").strip(),
                    "commissioner_organization": moratorium_granted.group(
                        "commissioner_org"
                    ).strip(),
                    "commissioner_place": moratorium_granted.group(
                        "commissioner_place"
                    ).strip(),
                    "commissioner_status": "confirmed",
                },
            )
        )
        event_types.add("status_changed")
    fr_moratorium_granted = _FR_COMPOSITION_MORATORIUM_GRANTED.search(leftover)
    if fr_moratorium_granted:
        leftover = leftover.replace(fr_moratorium_granted.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "fr.text.composition_moratorium_granted.v1",
                {
                    "kind": "composition_moratorium_granted",
                    "decision_date": _swiss_date(
                        fr_moratorium_granted.group("decision_date")
                    ),
                    "until": _swiss_date(fr_moratorium_granted.group("until")),
                    "authority": fr_moratorium_granted.group("authority").strip(),
                },
            )
        )
        event_types.add("status_changed")
    moratorium_extended = _DE_COMPOSITION_MORATORIUM_EXTENDED.search(leftover)
    if moratorium_extended:
        leftover = leftover.replace(moratorium_extended.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.composition_moratorium_extended.v1",
                {
                    "kind": "composition_moratorium_extended",
                    "decision_date": _swiss_date(moratorium_extended.group("decision_date")),
                    "until": _swiss_date(moratorium_extended.group("until")),
                    "authority": moratorium_extended.group("authority").strip(),
                },
            )
        )
        event_types.add("status_changed")
    active_moratorium_extended = _DE_COMPOSITION_MORATORIUM_EXTENDED_ACTIVE.search(
        leftover
    )
    if active_moratorium_extended:
        duration_raw = active_moratorium_extended.group("duration").lower()
        duration_months = {"einen": 1, "sechs": 6}.get(
            duration_raw, int(duration_raw) if duration_raw.isdigit() else None
        )
        leftover = leftover.replace(active_moratorium_extended.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.composition_moratorium_extended.v2",
                {
                    "kind": "composition_moratorium_extended",
                    "decision_date": _swiss_date(
                        active_moratorium_extended.group("decision_date")
                    ),
                    "until": _swiss_date(active_moratorium_extended.group("until")),
                    "duration_months": duration_months,
                    "authority": active_moratorium_extended.group(
                        "authority"
                    ).strip(),
                },
            )
        )
        event_types.add("status_changed")
    fr_moratorium_extended = _FR_COMPOSITION_MORATORIUM_EXTENDED.search(leftover)
    if fr_moratorium_extended:
        leftover = leftover.replace(fr_moratorium_extended.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "fr.text.composition_moratorium_extended.v1",
                {
                    "kind": "composition_moratorium_extended",
                    "decision_date": _french_written_date(
                        fr_moratorium_extended.group("decision_date")
                    ),
                    "until": _french_written_date(fr_moratorium_extended.group("until")),
                    "duration_months": int(fr_moratorium_extended.group("months")),
                    "authority": fr_moratorium_extended.group("authority").strip(),
                },
            )
        )
        event_types.add("status_changed")
    covid_moratorium = _FR_COVID_MORATORIUM.search(leftover)
    if covid_moratorium:
        leftover = leftover.replace(covid_moratorium.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "fr.text.covid_moratorium.v1",
                {
                    "kind": "covid19_moratorium_granted",
                    "decision_date": _swiss_date(covid_moratorium.group("decision_date")),
                    "until": _swiss_date(covid_moratorium.group("until")),
                    "duration_months": int(covid_moratorium.group("months")),
                    "authority": covid_moratorium.group("authority").strip(),
                },
            )
        )
        event_types.add("status_changed")
    repudiated_estate = _FR_REPUDIATED_ESTATE_LIQUIDATION.search(leftover)
    if repudiated_estate:
        leftover = leftover.replace(repudiated_estate.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "fr.text.repudiated_estate_liquidation.v1",
                {
                    "kind": "repudiated_estate_liquidation_ordered",
                    "authority": repudiated_estate.group("authority").strip(),
                    "date": (
                        _swiss_date(repudiated_estate.group("date"))
                        if re.fullmatch(
                            r"\d{2}\.\d{2}\.\d{4}",
                            repudiated_estate.group("date"),
                        )
                        else _french_written_date(repudiated_estate.group("date"))
                    ),
                    "procedure": "bankruptcy_office",
                },
            )
        )
        event_types.add("status_changed")
    business_ceased = _FR_BUSINESS_CEASED_DELETION.search(leftover)
    if business_ceased:
        leftover = leftover.replace(business_ceased.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "company_deleted",
                "fr.text.business_ceased_deletion.v1",
                {
                    "reason": "business_operations_ceased",
                    "note": business_ceased.group(0).strip(),
                },
            )
        )
        event_types.add("company_deleted")
    bankruptcy_maintained = _FR_BANKRUPTCY_MAINTAINED.search(leftover)
    if bankruptcy_maintained:
        leftover = leftover.replace(bankruptcy_maintained.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "fr.text.bankruptcy_maintained.v1",
                {
                    "kind": "bankruptcy_maintained",
                    "decision_date": _swiss_date(bankruptcy_maintained.group("decision_date")),
                    "judgment_date": _swiss_date(bankruptcy_maintained.group("judgment_date")),
                    "bankruptcy_date": _swiss_date(bankruptcy_maintained.group("bankruptcy_date")),
                    "authority": bankruptcy_maintained.group("authority").strip(),
                },
            )
        )
        event_types.add("status_changed")
    bankruptcy_appeal_rejected = _FR_BANKRUPTCY_APPEAL_REJECTED.search(leftover)
    if bankruptcy_appeal_rejected:
        leftover = leftover.replace(bankruptcy_appeal_rejected.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "fr.text.bankruptcy_appeal_rejected.v1",
                {
                    "kind": "bankruptcy_confirmed",
                    "appeal_outcome": "rejected",
                    "decision_date": _french_written_date(
                        bankruptcy_appeal_rejected.group("decision_date")
                    ),
                    "bankruptcy_date": _french_written_date(
                        bankruptcy_appeal_rejected.group("bankruptcy_date")
                    ),
                    "bankruptcy_time": bankruptcy_appeal_rejected.group("time"),
                    "authority": bankruptcy_appeal_rejected.group(
                        "authority"
                    ).strip(),
                },
            )
        )
        event_types.add("status_changed")
    bankruptcy_proceedings_suspended = _FR_BANKRUPTCY_PROCEEDINGS_SUSPENDED.search(leftover)
    if bankruptcy_proceedings_suspended:
        leftover = leftover.replace(bankruptcy_proceedings_suspended.group(0), " ")
        raw_date = bankruptcy_proceedings_suspended.group("date")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "fr.text.bankruptcy_proceedings_suspended.v1",
                {
                    "kind": "bankruptcy_effect_suspended",
                    "date": (
                        _swiss_date(raw_date)
                        if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", raw_date)
                        else _french_written_date(raw_date)
                    ),
                    "authority": bankruptcy_proceedings_suspended.group("authority").strip(),
                },
            )
        )
        event_types.add("status_changed")
    bankruptcy_effect_suspended_written = _FR_BANKRUPTCY_EFFECT_SUSPENDED_WRITTEN.search(
        leftover
    )
    if bankruptcy_effect_suspended_written:
        leftover = leftover.replace(bankruptcy_effect_suspended_written.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "fr.text.bankruptcy_effect_suspended.v2",
                {
                    "kind": "bankruptcy_effect_suspended",
                    "decision_date": _french_written_date(
                        bankruptcy_effect_suspended_written.group("decision_date")
                    ),
                    "bankruptcy_date": _french_written_date(
                        bankruptcy_effect_suspended_written.group("bankruptcy_date")
                    ),
                    "authority": bankruptcy_effect_suspended_written.group(
                        "authority"
                    ).strip(),
                },
            )
        )
        event_types.add("status_changed")
    bankruptcy_enforcement_suspended = _FR_BANKRUPTCY_ENFORCEMENT_SUSPENDED.search(leftover)
    if bankruptcy_enforcement_suspended:
        leftover = leftover.replace(bankruptcy_enforcement_suspended.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "fr.text.bankruptcy_enforcement_suspended.v1",
                {
                    "kind": "bankruptcy_enforcement_suspended",
                    "date": _swiss_date(bankruptcy_enforcement_suspended.group("date")),
                    "authority": bankruptcy_enforcement_suspended.group("authority").strip(),
                    "bankruptcy_remains_in_force": True,
                    "conservatory_measures_remain_in_force": True,
                },
            )
        )
        event_types.add("status_changed")
    dissolution_bankruptcy = _FR_DISSOLUTION_WITH_BANKRUPTCY_LIQUIDATION.search(leftover)
    if dissolution_bankruptcy:
        leftover = leftover.replace(dissolution_bankruptcy.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "fr.text.dissolution_bankruptcy_liquidation.v1",
                {
                    "kind": "dissolution",
                    "date": _french_written_date(dissolution_bankruptcy.group("date")),
                    "authority": dissolution_bankruptcy.group("authority").strip(),
                    "liquidation_mode": "bankruptcy",
                },
            )
        )
        event_types.add("status_changed")
    association_dissolution = (
        _FR_ASSOCIATION_DISSOLUTION_WITH_BANKRUPTCY_LIQUIDATION.search(leftover)
    )
    if association_dissolution:
        leftover = leftover.replace(association_dissolution.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "fr.text.association_dissolution_bankruptcy_liquidation.v1",
                {
                    "kind": "dissolution",
                    "date": _french_written_date(association_dissolution.group("date")),
                    "authority": association_dissolution.group("authority").strip(),
                    "legal_basis": association_dissolution.group("law"),
                    "liquidation_mode": "bankruptcy",
                },
            )
        )
        event_types.add("status_changed")
    judicial_dissolution = _FR_JUDICIAL_DISSOLUTION.search(leftover)
    if judicial_dissolution:
        leftover = leftover.replace(judicial_dissolution.group(0), " ")
        if "status_changed" not in event_types:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "status_changed",
                    "fr.text.judicial_dissolution.v1",
                    {
                        "kind": "dissolution",
                        "date": _french_written_date(judicial_dissolution.group("date")),
                        "authority": judicial_dissolution.group("authority").strip(),
                        "reason": "legal_situation_not_restored",
                    },
                )
            )
            event_types.add("status_changed")
    court_dissolution = _FR_COURT_DISSOLUTION.search(leftover)
    if court_dissolution:
        leftover = leftover.replace(court_dissolution.group(0), " ")
        if "status_changed" not in event_types:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "status_changed",
                    "fr.text.court_dissolution.v1",
                    {
                        "kind": "dissolution",
                        "date": _swiss_date(court_dissolution.group("date")),
                        "authority": court_dissolution.group("authority").strip(),
                    },
                )
            )
            event_types.add("status_changed")
    dissolved_liquidated_deleted = _FR_DISSOLVED_LIQUIDATED_AND_DELETED.search(leftover)
    if dissolved_liquidated_deleted:
        leftover = leftover.replace(dissolved_liquidated_deleted.group(0), " ")
        if "status_changed" not in event_types:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "status_changed",
                    "fr.text.dissolution_and_liquidation.v1",
                    {"kind": "liquidation_ended", "was_dissolved": True},
                )
            )
            event_types.add("status_changed")
        if "company_deleted" not in event_types:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "company_deleted",
                    "fr.text.liquidation_deletion.v1",
                    {
                        "reason": "liquidation_completed",
                        "note": dissolved_liquidated_deleted.group(0).strip(),
                    },
                )
            )
            event_types.add("company_deleted")
    foundation_dissolution = _FR_FOUNDATION_DISSOLUTION.search(leftover)
    if foundation_dissolution:
        leftover = leftover.replace(foundation_dissolution.group(0), " ")
        if "status_changed" not in event_types:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "status_changed",
                    "fr.text.foundation_dissolution.v1",
                    {
                        "kind": "dissolution",
                        "date": _french_written_date(
                            foundation_dissolution.group("date")
                        ),
                        "authority": foundation_dissolution.group(
                            "authority"
                        ).strip(),
                    },
                )
            )
            event_types.add("status_changed")
    dissolved = _DE_DISSOLVED.search(leftover) or _FR_DISSOLVED.search(leftover)
    if dissolved:
        payload = {"kind": "dissolution", "raw": dissolved.group(0).strip()}
        if dissolved.re is _DE_DISSOLVED:
            payload["date"] = _swiss_date(dissolved.group("date"))
            rule_id_status = "de.text.dissolution.v1"
        else:
            rule_id_status = "fr.text.dissolution.v1"
        leftover = leftover.replace(dissolved.group(0), " ")
        if "status_changed" not in event_types:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "status_changed",
                    rule_id_status,
                    payload,
                )
            )
            event_types.add("status_changed")
    liq_ended = _DE_LIQ_ENDED.search(leftover)
    if liq_ended:
        leftover = leftover.replace(liq_ended.group(0), " ")
        if "status_changed" not in event_types:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "status_changed",
                    "de.text.liquidation_ended.v1",
                    {"kind": "liquidation_ended", "raw": liq_ended.group(0).strip()},
                )
            )
            event_types.add("status_changed")
    found_liq_name = _FR_LIQ_OPEREE.search(leftover)
    if found_liq_name:
        leftover = leftover.replace(found_liq_name.group(0), " ")
    it_liq = _IT_LIQ_ENDED.search(leftover)
    if it_liq:
        leftover = leftover.replace(it_liq.group(0), " ")
        if "status_changed" not in event_types:
            liquidation_payload = {
                "kind": "liquidation_ended",
                "raw": it_liq.group(0).strip(),
            }
            if re.search(r"non può(?: ancora)? essere effettuata", it_liq.group(0), re.I):
                liquidation_payload.update(
                    {
                        "deletion_blocked": True,
                        "deletion_blocked_reason": "cantonal_tax_authority_consent_missing",
                    }
                )
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "status_changed",
                    "it.text.liquidation_ended.v1",
                    liquidation_payload,
                )
            )
            event_types.add("status_changed")
    extinguished = _DE_COMPANY_EXTINGUISHED_AFTER_TAX_APPROVAL.search(leftover)
    if extinguished:
        leftover = leftover.replace(extinguished.group(0), " ")
        if "company_deleted" not in event_types:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "company_deleted",
                    "de.text.company_extinguished.v1",
                    {
                        "reason": "tax_authority_approvals_received",
                        "note": extinguished.group(0).strip(),
                    },
                )
            )
            event_types.add("company_deleted")
    de_sole_proprietor_reinstated = _DE_SOLE_PROPRIETOR_REINSTATED.search(leftover)
    if de_sole_proprietor_reinstated:
        leftover = leftover.replace(de_sole_proprietor_reinstated.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.sole_proprietor_reinstated.v1",
                {
                    "kind": "registration_reinstated",
                    "reason": "erroneous_deletion",
                    "business_continues": True,
                    "removed_fact": de_sole_proprietor_reinstated.group(
                        "removed"
                    ).strip(),
                },
            )
        )
        event_types.add("status_changed")
    de_reinstated_bankruptcy = _DE_COMPANY_REINSTATED_BANKRUPTCY_REOPENED.search(
        leftover
    )
    if de_reinstated_bankruptcy:
        leftover = leftover.replace(de_reinstated_bankruptcy.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.company_reinstated_bankruptcy.v1",
                {
                    "kind": "registration_reinstated",
                    "reason": "bankruptcy_reopened",
                    "decision_date": _swiss_date(
                        de_reinstated_bankruptcy.group("date")
                    ),
                    "authority": de_reinstated_bankruptcy.group(
                        "authority"
                    ).strip(" ,"),
                    "proceeding": "summary",
                    "previous": de_reinstated_bankruptcy.group("previous").strip(),
                },
            )
        )
        event_types.add("status_changed")
    fr_sole_proprietor_reinstated = (
        _FR_SOLE_PROPRIETOR_REINSTATED_CORRECTION.search(leftover)
    )
    if fr_sole_proprietor_reinstated:
        leftover = leftover.replace(fr_sole_proprietor_reinstated.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "fr.text.sole_proprietor_reinstated.v1",
                {
                    "kind": "registration_reinstated",
                    "reason": "erroneous_deletion",
                    "correction": True,
                    "reference_date": _swiss_date(
                        fr_sole_proprietor_reinstated.group("reference_date")
                    ),
                    "reference": fr_sole_proprietor_reinstated.group("reference"),
                },
            )
        )
        event_types.add("status_changed")
    official_registration = _FR_SOLE_PROPRIETOR_OFFICIAL_REGISTRATION.search(
        leftover
    )
    if official_registration:
        leftover = leftover.replace(official_registration.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "fr.text.sole_proprietor_official_registration.v1",
                {
                    "kind": "official_registration",
                    "legal_basis": official_registration.group("article"),
                    "entity_kind": "sole_proprietorship",
                },
            )
        )
        event_types.add("status_changed")
    reinstated_bankruptcy = _FR_COMPANY_REINSTATED_BANKRUPTCY.search(leftover)
    if reinstated_bankruptcy:
        leftover = leftover.replace(reinstated_bankruptcy.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "fr.text.company_reinstated_bankruptcy.v1",
                {
                    "kind": "registration_reinstated",
                    "reason": "bankruptcy_reopened",
                    "decision_date": _french_written_date(
                        reinstated_bankruptcy.group("decision_date")
                    ),
                    "bankruptcy_date": _french_written_date(
                        reinstated_bankruptcy.group("bankruptcy_date")
                    ),
                    "bankruptcy_time": reinstated_bankruptcy.group("time"),
                    "authority": reinstated_bankruptcy.group("authority").strip(),
                },
            )
        )
        event_types.add("status_changed")
    reinstated = _FR_COMPANY_REINSTATED.search(leftover)
    if reinstated:
        leftover = leftover.replace(reinstated.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "fr.text.company_reinstated.v1",
                {
                    "kind": "registration_reinstated",
                    "date": _french_written_date(reinstated.group("date")),
                    "authority": reinstated.group("authority").strip(),
                    "liquidation_facts_remain_valid": True,
                },
            )
        )
        event_types.add("status_changed")
    reinstatement_ordered = _FR_COMPANY_REINSTATEMENT_ORDERED.search(leftover)
    if reinstatement_ordered:
        leftover = leftover.replace(reinstatement_ordered.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "fr.text.company_reinstatement_ordered.v1",
                {
                    "kind": "registration_reinstated",
                    "date": _swiss_date(reinstatement_ordered.group("date")),
                    "authority": reinstatement_ordered.group("authority").strip(),
                    "action": "ordered",
                },
            )
        )
        event_types.add("status_changed")
    erroneous_dissolution = _FR_ERRONEOUS_DISSOLUTION_REVERSED.search(leftover)
    if erroneous_dissolution:
        leftover = leftover.replace(erroneous_dissolution.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "fr.text.erroneous_dissolution_reversed.v1",
                {
                    "kind": "dissolution_reversed",
                    "reason": "erroneous_court_communication",
                    "restored": True,
                    "reference_date": _swiss_date(
                        erroneous_dissolution.group("date")
                    ),
                    "reference_page": erroneous_dissolution.group("page"),
                    "reference": erroneous_dissolution.group("reference"),
                },
            )
        )
        event_types.add("status_changed")
    it_reinstated = _IT_COMPANY_REINSTATED_IN_LIQUIDATION.search(leftover)
    if it_reinstated:
        leftover = leftover.replace(it_reinstated.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "it.text.company_reinstated_liquidation.v1",
                {
                    "kind": "registration_reinstated",
                    "date": _swiss_date(it_reinstated.group("date")),
                    "authority": it_reinstated.group("authority").strip(),
                    "legal_basis": it_reinstated.group("law"),
                    "liquidation_facts_remain_valid": True,
                },
            )
        )
        event_types.add("status_changed")
    bankruptcy_closed = _FR_BANKRUPTCY_CLOSED.search(leftover)
    if bankruptcy_closed:
        leftover = leftover.replace(bankruptcy_closed.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "fr.text.bankruptcy_closed.v1",
                {
                    "kind": "bankruptcy_closed",
                    "date": _french_written_date(bankruptcy_closed.group("date")),
                    "reason": "suspended_for_lack_of_assets",
                },
            )
        )
        event_types.add("status_changed")
    bankruptcy_suspended = _FR_BANKRUPTCY_EFFECT_SUSPENDED.search(leftover)
    if bankruptcy_suspended:
        leftover = leftover.replace(bankruptcy_suspended.group(0), " ")
        payload = {
            "kind": "bankruptcy_effect_suspended",
            "decision_date": _swiss_date(bankruptcy_suspended.group("decision_date")),
            "bankruptcy_date": _swiss_date(bankruptcy_suspended.group("bankruptcy_date")),
            "authority": bankruptcy_suspended.group("authority").strip(),
        }
        if bankruptcy_suspended.group("appeal_date"):
            payload["appeal_date"] = _swiss_date(bankruptcy_suspended.group("appeal_date"))
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "fr.text.bankruptcy_effect_suspended.v1",
                payload,
            )
        )
        event_types.add("status_changed")
    spin_off = _DE_SPIN_OFF_ACQUISITION.search(leftover)
    if spin_off:
        leftover = leftover.replace(spin_off.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "assets_transferred",
                "de.text.spin_off_acquisition.v1",
                {
                    "kind": "spin_off_acquisition",
                    "date": _swiss_date(spin_off.group("date")),
                    "source": spin_off.group("source").strip(),
                    "source_place": spin_off.group("source_place").strip(),
                    "source_uid": spin_off.group("source_uid"),
                    "assets": spin_off.group("assets"),
                    "liabilities": spin_off.group("liabilities"),
                    "capital_increase": False,
                    "share_allocation": False,
                },
            )
        )
    spin_off_transfer = _FR_SPIN_OFF_TRANSFER.search(leftover)
    if spin_off_transfer:
        leftover = leftover.replace(spin_off_transfer.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "assets_transferred",
                "fr.text.spin_off_transfer.v1",
                {
                    "kind": "spin_off",
                    "date": _swiss_date(spin_off_transfer.group("date")),
                    "scope": "partial_assets_and_liabilities",
                    "recipient": spin_off_transfer.group("recipient").strip(),
                    "recipient_place": spin_off_transfer.group("place").strip(),
                    "recipient_uid": spin_off_transfer.group("uid"),
                },
            )
        )
    foundation_transfer = _FR_FOUNDATION_ASSET_TRANSFER.search(leftover)
    if foundation_transfer:
        leftover = leftover.replace(foundation_transfer.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "assets_transferred",
                "fr.text.foundation_asset_transfer.v1",
                {
                    "date": _french_written_date(foundation_transfer.group("date")),
                    "supervisory_approval_date": _french_written_date(
                        foundation_transfer.group("approval_date")
                    ),
                    "assets": foundation_transfer.group("assets"),
                    "liabilities": foundation_transfer.group("liabilities"),
                    "recipient": foundation_transfer.group("recipient").strip(),
                    "recipient_place": foundation_transfer.group("place").strip(),
                    "recipient_uid": foundation_transfer.group("uid"),
                    "consideration": foundation_transfer.group("consideration").strip(),
                },
            )
        )
    asset_transfer = _FR_ASSET_TRANSFER.search(leftover)
    if asset_transfer:
        leftover = leftover.replace(asset_transfer.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "assets_transferred",
                "fr.text.asset_transfer.v1",
                {
                    "date": _swiss_date(asset_transfer.group("date")),
                    "assets": asset_transfer.group("assets"),
                    "liabilities": asset_transfer.group("liabilities"),
                    "net_assets": asset_transfer.group("net"),
                    "recipient": asset_transfer.group("recipient").strip(),
                    "recipient_place": asset_transfer.group("place").strip(),
                    "recipient_uid": asset_transfer.group("uid"),
                    "consideration": asset_transfer.group("consideration").strip(),
                },
            )
        )
    inventory_asset_transfer = _DE_ASSET_TRANSFER_WITH_INVENTORY.search(leftover)
    if inventory_asset_transfer:
        leftover = leftover.replace(inventory_asset_transfer.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "assets_transferred",
                "de.text.asset_transfer.v3",
                {
                    "date": _swiss_date(inventory_asset_transfer.group("date")),
                    "inventory_date": _swiss_date(
                        inventory_asset_transfer.group("inventory_date")
                    ),
                    "assets": inventory_asset_transfer.group("assets"),
                    "liabilities": inventory_asset_transfer.group("liabilities"),
                    "recipient": inventory_asset_transfer.group("recipient").strip(),
                    "recipient_place": inventory_asset_transfer.group("place").strip(),
                    "recipient_uid": inventory_asset_transfer.group("uid"),
                    "consideration": inventory_asset_transfer.group(
                        "consideration"
                    ).strip(),
                },
            )
        )
    business_asset_transfer = _DE_BUSINESS_UNIT_ASSET_TRANSFER.search(leftover)
    if business_asset_transfer:
        leftover = leftover.replace(business_asset_transfer.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "assets_transferred",
                "de.text.asset_transfer.v2",
                {
                    "date": _swiss_date(business_asset_transfer.group("date")),
                    "inventory_date": _swiss_date(
                        business_asset_transfer.group("inventory_date")
                    ),
                    "business_unit": business_asset_transfer.group("business_unit").strip(),
                    "assets": business_asset_transfer.group("assets"),
                    "liabilities": business_asset_transfer.group("liabilities"),
                    "recipient": business_asset_transfer.group("recipient").strip(),
                    "recipient_place": business_asset_transfer.group("place").strip(),
                    "recipient_uid": business_asset_transfer.group("uid"),
                    "consideration": business_asset_transfer.group("consideration").strip(),
                },
            )
        )
    de_asset_transfer = _DE_ASSET_TRANSFER.search(leftover)
    if de_asset_transfer:
        leftover = leftover.replace(de_asset_transfer.group(0), " ")
        agreements = re.sub(
            r"^\s*mit\s+|\s+$", "", de_asset_transfer.group("agreements"), flags=re.I
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "assets_transferred",
                "de.text.asset_transfer.v1",
                {
                    "date": _swiss_date(de_asset_transfer.group("date")),
                    "agreements": agreements or None,
                    "assets": de_asset_transfer.group("assets"),
                    "liabilities": de_asset_transfer.group("liabilities"),
                    "recipient": de_asset_transfer.group("recipient").strip(),
                    "recipient_place": de_asset_transfer.group("place").strip(),
                    "recipient_uid": de_asset_transfer.group("uid"),
                    "consideration": de_asset_transfer.group("consideration").strip(),
                },
            )
        )
    fusion = _DE_FUSION.search(leftover)
    if fusion:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "company_merged",
                "de.text.fusion.v1",
                {
                    "absorbed_name": fusion.group("name").strip(),
                    "absorbed_uid": fusion.group("uid"),
                    "raw": fusion.group(0).strip()[:500],
                },
            )
        )
        leftover = leftover.replace(fusion.group(0), " ")
    it_fusion = _IT_CROSS_BORDER_FUSION.search(leftover)
    if it_fusion:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "company_merged",
                "it.text.cross_border_fusion.v1",
                {
                    "kind": "cross_border_merger",
                    "legal_basis": it_fusion.group("legal_basis").strip(),
                    "absorbed_name": it_fusion.group("name").strip(),
                    "absorbed_place": it_fusion.group("place").strip(),
                    "absorbed_country": it_fusion.group("country"),
                    "absorbed_registry_id": it_fusion.group("registry_id").strip(),
                    "agreement_date": _swiss_date(it_fusion.group("agreement_date")),
                    "balance_date": _swiss_date(it_fusion.group("balance_date")),
                    "currency": it_fusion.group("currency"),
                    "assets": it_fusion.group("assets"),
                    "liabilities": it_fusion.group("liabilities"),
                    "capital_increase": False,
                },
            )
        )
        leftover = leftover.replace(it_fusion.group(0), " ")
    fr_fusion = _FR_FUSION.search(leftover)
    if fr_fusion:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "company_merged",
                "fr.text.fusion.v1",
                {
                    "absorbed_name": fr_fusion.group("name").strip(" ,"),
                    "absorbed_uid": fr_fusion.group("uid"),
                    "raw": fr_fusion.group(0).strip()[:500],
                },
            )
        )
        leftover = leftover.replace(fr_fusion.group(0), " ")
    partnership_agreement = _DE_PARTNERSHIP_AGREEMENT_CHANGED.search(leftover)
    if partnership_agreement:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "de.text.partnership_agreement.v1",
                {
                    "kind": "partnership_agreement",
                    "date": _swiss_date(partnership_agreement.group("date")),
                },
            )
        )
        leftover = leftover.replace(partnership_agreement.group(0), " ")
    expired_authorized_capital = _DE_AUTHORIZED_CAPITAL_CLAUSE_EXPIRED.search(
        leftover
    )
    if expired_authorized_capital:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "de.text.authorized_capital_expired.v1",
                {
                    "kind": "authorized_increase",
                    "action": "removed",
                    "reason": "authorization_expired",
                    "authorization_date": _swiss_date(
                        expired_authorized_capital.group("date")
                    ),
                },
            )
        )
        leftover = leftover.replace(expired_authorized_capital.group(0), " ")
        event_types.add("capital_changed")
    auth_cap_modified = _DE_AUTH_CAPITAL_MODIFIED.search(leftover)
    if auth_cap_modified:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "de.text.authorized_capital_modified.v1",
                {
                    "kind": "authorized_increase",
                    "action": "modified",
                    "date": _swiss_date(auth_cap_modified.group("date")),
                    "original_authorization_date": _swiss_date(
                        auth_cap_modified.group("original_date")
                    ),
                    "previous": auth_cap_modified.group("previous"),
                },
            )
        )
        leftover = leftover.replace(auth_cap_modified.group(0), " ")
        event_types.add("capital_changed")
    auth_cap = _DE_AUTH_CAPITAL.search(leftover)
    if auth_cap:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "de.text.authorized_capital.v1",
                {
                    "kind": "authorized_increase",
                    "date": _swiss_date(auth_cap.group("date")),
                    "raw": auth_cap.group(0).strip(),
                },
            )
        )
        leftover = leftover.replace(auth_cap.group(0), " ")
    fr_conditional_participation = (
        _FR_CONDITIONAL_PARTICIPATION_CAPITAL_CLAUSE_INTRODUCED.search(leftover)
    )
    if fr_conditional_participation:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.conditional_participation_capital_clause.v2",
                {
                    "kind": "conditional_participation_capital_clause",
                    "action": "introduced",
                    "decision_date": _swiss_date(
                        fr_conditional_participation.group("date")
                    ),
                },
            )
        )
        leftover = leftover.replace(fr_conditional_participation.group(0), " ")
        event_types.add("capital_changed")
    removed_capital_clause = _FR_CAPITAL_CLAUSE_REMOVED.search(leftover)
    if removed_capital_clause:
        clause_kind = removed_capital_clause.group("kind").lower()
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.capital_clause_removed.v1",
                {
                    "kind": (
                        "authorized_capital_clause"
                        if clause_kind == "autorisée"
                        else "conditional_capital_clause"
                    ),
                    "action": "removed",
                    "original_decision_date": _swiss_date(
                        removed_capital_clause.group("date")
                    ),
                },
            )
        )
        leftover = leftover.replace(removed_capital_clause.group(0), " ")
        event_types.add("capital_changed")
    for fr_capital_clause in list(_FR_CAPITAL_CLAUSE_INTRODUCED.finditer(leftover)):
        clause_kind = fr_capital_clause.group("kind").lower()
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                (
                    "fr.text.authorized_capital_clause.v2"
                    if clause_kind == "autorisée"
                    else "fr.text.conditional_capital_clause.v1"
                ),
                {
                    "kind": (
                        "authorized_capital_clause"
                        if clause_kind == "autorisée"
                        else "conditional_capital_clause"
                    ),
                    "action": "introduced",
                    "decision_date": _swiss_date(fr_capital_clause.group("date")),
                    "raw": fr_capital_clause.group(0).strip(),
                },
            )
        )
        leftover = leftover.replace(fr_capital_clause.group(0), " ")
        event_types.add("capital_changed")
    it_conditional_capital = _IT_CONDITIONAL_CAPITAL_CLAUSE_INTRODUCED.search(
        leftover
    )
    if it_conditional_capital:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "it.text.conditional_capital_clause.v1",
                {
                    "kind": "conditional_capital_clause",
                    "action": "introduced",
                    "decision_date": _swiss_date(
                        it_conditional_capital.group("date")
                    ),
                },
            )
        )
        leftover = leftover.replace(it_conditional_capital.group(0), " ")
        event_types.add("capital_changed")
    conditional_capital_modified = _DE_CONDITIONAL_CAPITAL_MODIFIED.search(leftover)
    if conditional_capital_modified:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "de.text.conditional_capital_modified.v1",
                {
                    "kind": "conditional_increase",
                    "action": "modified",
                    "date": _swiss_date(conditional_capital_modified.group("date")),
                    "original_date": _swiss_date(
                        conditional_capital_modified.group("original_date")
                    ),
                    "previous": conditional_capital_modified.group("previous").strip(),
                },
            )
        )
        leftover = leftover.replace(conditional_capital_modified.group(0), " ")
        event_types.add("capital_changed")
    conditional_capital = _DE_CONDITIONAL_CAPITAL.search(leftover)
    if conditional_capital:
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "de.text.conditional_capital.v1",
                {
                    "kind": "conditional_increase",
                    "date": _swiss_date(conditional_capital.group("date")),
                    "raw": conditional_capital.group(0).strip(),
                },
            )
        )
        leftover = leftover.replace(conditional_capital.group(0), " ")
        event_types.add("capital_changed")
    head_office_name = _DE_HEAD_OFFICE_NAME.search(leftover)
    if head_office_name:
        leftover = leftover.replace(head_office_name.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "company_name_changed",
                "de.text.head_office_name.v1",
                {
                    "scope": "head_office",
                    "from": head_office_name.group("from").strip(),
                    "to": head_office_name.group("to").strip(),
                },
            )
        )
        event_types.add("company_name_changed")
    direct_head_office_name = _DE_HEAD_OFFICE_NAME_DIRECT.search(leftover)
    if direct_head_office_name:
        leftover = leftover.replace(direct_head_office_name.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "company_name_changed",
                "de.text.head_office_name_direct.v1",
                {
                    "scope": "head_office",
                    "to": direct_head_office_name.group("to").strip(),
                    "head_office_uid": direct_head_office_name.group("uid"),
                },
            )
        )
        event_types.add("company_name_changed")
    head_office_legal_form = _DE_HEAD_OFFICE_LEGAL_FORM.search(leftover)
    if head_office_legal_form:
        leftover = leftover.replace(head_office_legal_form.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "organization_changed",
                "de.text.head_office_legal_form.v1",
                {
                    "scope": "head_office",
                    "kind": "legal_form",
                    "from": head_office_legal_form.group("from").strip(),
                    "to": head_office_legal_form.group("to").strip(),
                },
            )
        )
    direct_head_office_legal_form = _DE_HEAD_OFFICE_LEGAL_FORM_DIRECT.search(leftover)
    if direct_head_office_legal_form:
        leftover = leftover.replace(direct_head_office_legal_form.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "organization_changed",
                "de.text.head_office_legal_form.v2",
                {
                    "scope": "head_office",
                    "kind": "legal_form",
                    "to": direct_head_office_legal_form.group("to").strip(),
                },
            )
        )
    trans = _DE_TRANSLATIONS.search(leftover)
    if trans:
        leftover = leftover.replace(trans.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "company_name_changed",
                "de.text.translations.v1",
                {"raw": trans.group(0).strip()},
            )
        )
    former_translations = _DE_FORMER_TRANSLATIONS_REMOVED.search(leftover)
    if former_translations:
        leftover = leftover.replace(former_translations.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "company_name_changed",
                "de.text.former_translations_removed.v1",
                {
                    "kind": "translations",
                    "action": "removed",
                    "reason": "company_name_changed",
                    "raw": former_translations.group(0).strip(),
                },
            )
        )
    it_translations = _IT_TRANSLATIONS_REMOVAL_ANNOUNCED.search(leftover)
    if it_translations:
        leftover = leftover.replace(it_translations.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "company_name_changed",
                "it.text.translations_removal_announced.v1",
                {
                    "kind": "translations",
                    "action": "removal_announced",
                    "raw": it_translations.group(0).strip(),
                },
            )
        )
    head_office_bankruptcy = _DE_HEAD_OFFICE_BANKRUPTCY_SUSPENDED.search(leftover)
    if head_office_bankruptcy:
        leftover = leftover.replace(head_office_bankruptcy.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.head_office_bankruptcy_suspended.v1",
                {
                    "kind": "bankruptcy_suspended_for_lack_of_assets",
                    "scope": "head_office",
                    "date": _swiss_date(head_office_bankruptcy.group("date")),
                },
            )
        )
        event_types.add("status_changed")
    head_office_capital = _DE_HEAD_OFFICE_CAPITAL.search(leftover)
    if head_office_capital:
        leftover = leftover.replace(head_office_capital.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "de.text.head_office_capital.v1",
                {
                    "scope": "head_office",
                    "currency": head_office_capital.group("currency").upper(),
                    "from_nominal": head_office_capital.group("from"),
                    "to_nominal": head_office_capital.group("to"),
                    "from_paid": head_office_capital.group("from_paid"),
                    "to_paid": head_office_capital.group("to_paid"),
                },
            )
        )
        event_types.add("capital_changed")
    municipality_seat = _DE_MUNICIPALITY_SEAT_CHANGE.search(leftover)
    if municipality_seat:
        leftover = leftover.replace(municipality_seat.group(0), " ")
        if "seat_changed" not in event_types:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "seat_changed",
                    "de.text.municipality_seat_change.v1",
                    {
                        "to": municipality_seat.group("to").strip(),
                        "reason": "municipality_name_change",
                        "official_change": "von Amtes wegen"
                        in municipality_seat.group("reason"),
                        "raw_reason": municipality_seat.group("reason").strip(),
                    },
                )
            )
            event_types.add("seat_changed")
    hauptsitz = (
        _HAUPTSITZ.search(leftover)
        or _HAUPTSITZ_NEU.search(leftover)
        or _DE_NEW_HEAD_OFFICE.search(leftover)
    )
    if hauptsitz:
        to_seat = hauptsitz.group("to").strip()
        from_seat = (hauptsitz.groupdict().get("from") or hauptsitz.groupdict().get("old") or "").strip() or None
        leftover = leftover.replace(hauptsitz.group(0), " ")
        if "seat_changed" not in event_types:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "seat_changed",
                    "de.text.hauptsitz.v1",
                    {"from": from_seat, "to": to_seat},
                )
            )
            event_types.add("seat_changed")
    hauptsitz_id = _HAUPTSITZ_IDENTIFIER.search(leftover)
    if hauptsitz_id:
        leftover = leftover.replace(hauptsitz_id.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "company_identifier_changed",
                "de.text.head_office_identifier.v1",
                {
                    "scope": "head_office",
                    "seat": hauptsitz_id.group("seat").strip(),
                    "from": hauptsitz_id.group("from"),
                    "to": hauptsitz_id.group("to"),
                },
            )
        )
    hauptsitz_id_only = _HAUPTSITZ_IDENTIFIER_ONLY.search(leftover)
    if hauptsitz_id_only:
        leftover = leftover.replace(hauptsitz_id_only.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "company_identifier_changed",
                "de.text.head_office_identifier.v2",
                {
                    "scope": "head_office",
                    "from": hauptsitz_id_only.group("from"),
                    "to": hauptsitz_id_only.group("to"),
                },
            )
        )
    company_identifier = _DE_COMPANY_IDENTIFIER.search(leftover)
    if company_identifier:
        leftover = leftover.replace(company_identifier.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "company_identifier_changed",
                "de.text.company_identifier.v1",
                {
                    "scope": "organization",
                    "from": company_identifier.group("from"),
                    "to": company_identifier.group("to"),
                },
            )
        )
    it_company_identifier = _IT_COMPANY_IDENTIFIER.search(leftover)
    if it_company_identifier:
        leftover = leftover.replace(it_company_identifier.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "company_identifier_changed",
                "it.text.company_identifier.v1",
                {
                    "scope": "organization",
                    "from": it_company_identifier.group("from"),
                    "to": it_company_identifier.group("to"),
                },
            )
        )
    fr_company_identifier = _FR_COMPANY_IDENTIFIER_CORRECTED.search(leftover)
    if fr_company_identifier:
        leftover = leftover.replace(fr_company_identifier.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "company_identifier_changed",
                "fr.text.company_identifier_corrected.v1",
                {
                    "scope": "organization",
                    "action": "corrected",
                    "from": fr_company_identifier.group("from"),
                    "to": fr_company_identifier.group("to"),
                },
            )
        )
    it_head_office_change = _IT_HEAD_OFFICE_CHANGE.search(leftover)
    if it_head_office_change:
        leftover = leftover.replace(it_head_office_change.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "seat_changed",
                "it.text.head_office.v1",
                {
                    "scope": "head_office",
                    "from": it_head_office_change.group("from").strip(),
                    "to": it_head_office_change.group("to").strip(),
                },
            )
        )
        event_types.add("seat_changed")
    continued_branch = _DE_HEAD_OFFICE_BRANCH_CONTINUED_AFTER_SPINOFF.search(leftover)
    if continued_branch:
        leftover = leftover.replace(continued_branch.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "branch_changed",
                "de.text.branch_continued_after_spinoff.v1",
                {
                    "action": "continued",
                    "reason": "spin_off",
                    "previous_head_office": continued_branch.group(
                        "previous_head_office"
                    ).strip(),
                    "previous_head_office_new_name": continued_branch.group(
                        "renamed_head_office"
                    ).strip(),
                    "head_office": continued_branch.group("new_head_office").strip(),
                },
            )
        )
    asset_transfer_branch = (
        _DE_HEAD_OFFICE_BRANCH_CONTINUED_AFTER_ASSET_TRANSFER.search(leftover)
    )
    if asset_transfer_branch:
        leftover = leftover.replace(asset_transfer_branch.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "branch_changed",
                "de.text.branch_continued_after_asset_transfer.v1",
                {
                    "action": "continued",
                    "reason": "asset_transfer",
                    "legal_basis": "Art. 112 HRegV",
                    "previous_head_office_new_name": asset_transfer_branch.group(
                        "renamed_head_office"
                    ).strip(),
                    "head_office": asset_transfer_branch.group(
                        "new_head_office"
                    ).strip(),
                    "head_office_place": asset_transfer_branch.group(
                        "head_office_place"
                    ).strip(),
                    "head_office_uid": asset_transfer_branch.group(
                        "head_office_uid"
                    ),
                    "continued_as": asset_transfer_branch.group(
                        "continued_as"
                    ).strip(),
                },
            )
        )
    merged_branch = _DE_HEAD_OFFICE_BRANCH_CONTINUED_AFTER_MERGER.search(leftover)
    if merged_branch:
        leftover = leftover.replace(merged_branch.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "branch_changed",
                "de.text.branch_continued_after_merger.v1",
                {
                    "action": "continued",
                    "reason": "merger",
                    "legal_basis": "Art. 112 HRegV",
                    "previous_head_office": merged_branch.group(
                        "previous_head_office"
                    ).strip(),
                    "previous_head_office_uid": merged_branch.group(
                        "previous_uid"
                    ),
                    "absorbing_head_office": merged_branch.group(
                        "absorbing_head_office"
                    ).strip(),
                    "head_office": merged_branch.group("head_office").strip(),
                    "head_office_uid": merged_branch.group("head_office_uid"),
                },
            )
        )
    head_office_note = _DE_HEAD_OFFICE_MUNICIPALITY_NOTE.search(leftover)
    if head_office_note:
        leftover = leftover.replace(head_office_note.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "organization_changed",
                "de.text.head_office_municipality_note.v1",
                {
                    "scope": "head_office",
                    "kind": "seat_change_reason",
                    "reason": "municipality_merger",
                    "official_change": True,
                },
            )
        )
    head_office_context = _DE_HEAD_OFFICE_CONTEXT.search(leftover)
    if head_office_context:
        leftover = leftover.replace(head_office_context.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "organization_changed",
                "de.text.head_office_context.v1",
                {
                    "scope": "head_office",
                    "kind": "seat_reference",
                    "seat": head_office_context.group("seat").strip(),
                },
            )
        )
    it_head_office_context = _IT_HEAD_OFFICE_CONTEXT.search(leftover)
    if it_head_office_context:
        leftover = leftover.replace(it_head_office_context.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "organization_changed",
                "it.text.head_office_context.v1",
                {
                    "scope": "head_office",
                    "kind": "seat_reference",
                    "seat": it_head_office_context.group("seat").strip(),
                },
            )
        )
    fr_head_office_id = _FR_HEAD_OFFICE_IDENTIFIER.search(leftover)
    if fr_head_office_id:
        leftover = leftover.replace(fr_head_office_id.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "company_identifier_changed",
                "fr.text.head_office_identifier.v1",
                {
                    "scope": "head_office",
                    "seat": fr_head_office_id.group("seat").strip(),
                    "from": fr_head_office_id.group("from"),
                    "to": fr_head_office_id.group("to"),
                },
            )
        )
    fr_head_office_id_only = _FR_HEAD_OFFICE_IDENTIFIER_ONLY.search(leftover)
    if fr_head_office_id_only:
        leftover = leftover.replace(fr_head_office_id_only.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "company_identifier_changed",
                "fr.text.head_office_identifier.v2",
                {
                    "scope": "head_office",
                    "from": fr_head_office_id_only.group("from"),
                    "to": fr_head_office_id_only.group("to"),
                },
            )
        )
    fr_head_office_seat = _FR_HEAD_OFFICE_SEAT_REGISTERED.search(leftover)
    if fr_head_office_seat:
        leftover = leftover.replace(fr_head_office_seat.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "seat_changed",
                "fr.text.head_office_registered_seat.v1",
                {
                    "scope": "head_office",
                    "to": fr_head_office_seat.group("to").strip(),
                    "head_office_uid": fr_head_office_seat.group("uid"),
                    "register_canton": fr_head_office_seat.group(
                        "register_canton"
                    ).strip(),
                },
            )
        )
        event_types.add("seat_changed")
    fr_head_office_seat_simple = _FR_HEAD_OFFICE_SEAT.search(leftover)
    if fr_head_office_seat_simple:
        leftover = leftover.replace(fr_head_office_seat_simple.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "seat_changed",
                "fr.text.head_office_seat.v1",
                {
                    "scope": "head_office",
                    "to": fr_head_office_seat_simple.group("to").strip(),
                },
            )
        )
        event_types.add("seat_changed")
    head_office_registration = _DE_HEAD_OFFICE_REGISTRATION.search(leftover)
    if head_office_registration:
        leftover = leftover.replace(head_office_registration.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "organization_changed",
                "de.text.head_office_registration.v1",
                {
                    "scope": "head_office",
                    "kind": "register_office",
                    "to": head_office_registration.group("to").strip(),
                },
            )
        )
    fr_head_office_reference = _FR_HEAD_OFFICE_REFERENCE.search(leftover)
    if fr_head_office_reference:
        leftover = leftover.replace(fr_head_office_reference.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "organization_changed",
                "fr.text.head_office_context.v2",
                {
                    "scope": "head_office",
                    "kind": "seat_reference",
                    "seat": fr_head_office_reference.group("seat").strip(),
                },
            )
        )
    fr_head_office_change = _FR_HEAD_OFFICE_CHANGE.search(leftover)
    if fr_head_office_change:
        leftover = leftover.replace(fr_head_office_change.group(0), " ")
        if "seat_changed" not in event_types:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "seat_changed",
                    "fr.text.head_office.v2",
                    {
                        "scope": "head_office",
                        "from": fr_head_office_change.group("from").strip(),
                        "to": fr_head_office_change.group("to").strip(),
                    },
                )
            )
            event_types.add("seat_changed")
    fr_head_office_context = _FR_HEAD_OFFICE_CONTEXT.search(leftover)
    if fr_head_office_context:
        leftover = leftover.replace(fr_head_office_context.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "organization_changed",
                "fr.text.head_office_context.v1",
                {
                    "scope": "head_office",
                    "kind": "seat_reference",
                    "seat": fr_head_office_context.group("seat").strip(),
                },
            )
        )
    fr_head_office_name = _FR_HEAD_OFFICE_NAME.search(leftover)
    if fr_head_office_name:
        leftover = leftover.replace(fr_head_office_name.group(0), " ")
        head_office_name_payload = {
            "scope": "head_office",
            "to": fr_head_office_name.group("to").strip(),
        }
        if fr_head_office_name.group("uid"):
            head_office_name_payload["head_office_uid"] = fr_head_office_name.group(
                "uid"
            )
        if fr_head_office_name.group("from"):
            head_office_name_payload["from"] = fr_head_office_name.group(
                "from"
            ).strip()
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "company_name_changed",
                "fr.text.head_office_name.v1",
                head_office_name_payload,
            )
        )
        event_types.add("company_name_changed")
    head_office = _FR_HEAD_OFFICE.search(leftover)
    if head_office:
        leftover = leftover.replace(head_office.group(0), " ")
        head_office_payload = {
            "scope": "head_office",
            "to": head_office.group("to").strip(),
        }
        if head_office.group("from"):
            head_office_payload["from"] = head_office.group("from").strip()
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "seat_changed",
                "fr.text.head_office.v1",
                head_office_payload,
            )
        )
        event_types.add("seat_changed")
    seat_became = _FR_SEAT_BECAME.search(leftover)
    if seat_became:
        leftover = leftover.replace(seat_became.group(0), " ")
        if "seat_changed" not in event_types:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "seat_changed",
                    "fr.text.seat_became.v1",
                    {"to": seat_became.group("to").strip()},
                )
            )
            event_types.add("seat_changed")
    publication_address_correction = _FR_PUBLICATION_ADDRESS_CORRECTION.search(
        leftover
    )
    if publication_address_correction:
        leftover = leftover.replace(publication_address_correction.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "address_changed",
                "fr.text.publication_address_correction.v1",
                {
                    "action": "removed",
                    "kind": "publication_correction",
                    "address": publication_address_correction.group("address").strip(),
                    "corrected_registration_number": publication_address_correction.group(
                        "number"
                    ),
                    "corrected_registration_date": _swiss_date(
                        publication_address_correction.group("date")
                    ),
                },
            )
        )
        event_types.add("address_changed")
    domiciliary_address = _FR_DOMICILIARY_ADDRESS.search(leftover)
    if domiciliary_address:
        leftover = leftover.replace(domiciliary_address.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "address_changed",
                "fr.text.domiciliary_address.v1",
                {
                    "kind": "domiciliary_address",
                    "to": domiciliary_address.group("address").strip(),
                },
            )
        )
        event_types.add("address_changed")
    additional_removed = _FR_ADDITIONAL_ADDRESS_REMOVED.search(leftover)
    if additional_removed:
        leftover = leftover.replace(additional_removed.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "address_changed",
                "fr.text.additional_address_removed.v1",
                {
                    "action": "removed",
                    "kind": "additional_address",
                    "address": additional_removed.group("address").strip(),
                },
            )
        )
        event_types.add("address_changed")
    additional_addresses = _FR_ADDITIONAL_ADDRESSES.search(leftover)
    if additional_addresses:
        leftover = leftover.replace(additional_addresses.group(0), " ")
        addresses = re.split(
            r"\s+et\s+(?=[A-ZÀ-Ÿ])", additional_addresses.group("addresses").strip()
        )
        for address in addresses:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "address_changed",
                    "fr.text.additional_addresses.v1",
                    {
                        "action": "added",
                        "kind": "additional_address",
                        "address": address.strip(),
                    },
                )
            )
        event_types.add("address_changed")
    addr_rad = _FR_ADDR_RADIEES.search(leftover)
    if addr_rad:
        leftover = leftover.replace(addr_rad.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "address_changed",
                "fr.text.addresses_removed.v1",
                {"raw": addr_rad.group(0).strip(), "action": "removed"},
            )
        )
        event_types.add("address_changed")
    no_address = _FR_NO_ADDRESS.search(leftover)
    if no_address:
        leftover = leftover.replace(no_address.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "address_changed",
                "fr.text.no_domicile.v1",
                {"kind": "no_legal_domicile", "raw": no_address.group(0).strip()},
            )
        )
        event_types.add("address_changed")
    new_address = _FR_NEW_ADDRESS.search(leftover)
    if new_address:
        leftover = leftover.replace(new_address.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "address_changed",
                "fr.text.address.v1",
                {"action": "changed", "to": new_address.group("address").strip()},
            )
        )
        event_types.add("address_changed")
    additional_address = _FR_ADDITIONAL_ADDRESS.search(leftover)
    if additional_address:
        leftover = leftover.replace(additional_address.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "address_changed",
                "fr.text.additional_address.v1",
                {
                    "action": "added",
                    "kind": "additional_address",
                    "address": additional_address.group("address").strip(),
                },
            )
        )
        event_types.add("address_changed")
    it_new_address = _IT_NEW_ADDRESS.search(leftover)
    if it_new_address:
        payload = {
            "action": "changed",
            "to": it_new_address.group("address").strip(),
        }
        if it_new_address.group("reason"):
            payload["reason"] = it_new_address.group("reason").strip()
        leftover = leftover.replace(it_new_address.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "address_changed",
                "it.text.address.v1",
                payload,
            )
        )
        event_types.add("address_changed")
    address_removed = _FR_ADDRESS_REMOVED.search(leftover)
    if address_removed:
        leftover = leftover.replace(address_removed.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "address_changed",
                "fr.text.address_removed.v1",
                {"action": "removed", "raw": address_removed.group(0).strip()},
            )
        )
        event_types.add("address_changed")
    it_additional_removed = _IT_ADDITIONAL_ADDRESS_REMOVED.search(leftover)
    if it_additional_removed:
        leftover = leftover.replace(it_additional_removed.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "address_changed",
                "it.text.additional_address_removed.v1",
                {
                    "action": "removed",
                    "kind": "additional_address",
                    "address": it_additional_removed.group("address").strip(),
                },
            )
        )
        event_types.add("address_changed")
    it_additional = _IT_ADDITIONAL_ADDRESS.search(leftover)
    if it_additional:
        leftover = leftover.replace(it_additional.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "address_changed",
                "it.text.additional_address.v1",
                {
                    "action": "added",
                    "kind": "additional_address",
                    "address": it_additional.group("address").strip(),
                },
            )
        )
        event_types.add("address_changed")
    liq_addr = _LIQ_ADDRESS.search(leftover)
    if liq_addr:
        leftover = leftover.replace(liq_addr.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "address_changed",
                "fr.text.liquidation_address.v1",
                {"to": liq_addr.group("addr").strip(), "kind": "liquidation_address"},
            )
        )
        event_types.add("address_changed")
    domizil = _DOMIZIL_NEU.search(leftover)
    if domizil:
        leftover = leftover.replace(domizil.group(0), " ")
        if "address_changed" not in event_types:
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "address_changed",
                    "de.text.domizil.v1",
                    {"to": domizil.group("to").strip()},
                )
            )
            event_types.add("address_changed")
    supervisor = (
        _DE_SUPERVISOR.search(leftover)
        or _FR_SUPERVISOR.search(leftover)
        or _IT_SUPERVISOR.search(leftover)
    )
    if supervisor:
        leftover = leftover.replace(supervisor.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "supervisor_changed",
                "text.supervisor.v1",
                {"to": supervisor.group("to").strip().rstrip(".")},
            )
        )
    non_public_statutes = _DE_NON_PUBLIC_STATUTES.search(leftover)
    if non_public_statutes:
        leftover = leftover.replace(non_public_statutes.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "de.text.non_public_statutes.v1",
                {
                    "date": _swiss_date(non_public_statutes.group("date")),
                    "non_public_changes": True,
                },
            )
        )
    qualified = _DE_QUALIFIED.search(leftover)
    if qualified:
        leftover = leftover.replace(qualified.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "de.text.qualified_facts.v1",
                {"raw": re.sub(r"\s+", " ", qualified.group(0)).strip()[:400]},
            )
        )
    vink = _DE_VINKULIERUNG.search(leftover)
    if vink:
        leftover = leftover.replace(vink.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "de.text.vinkulierung.v1",
                {"raw": vink.group(0).strip()},
            )
        )
    ancillary_removed = _DE_ANCILLARY_RIGHTS_REMOVED.search(leftover)
    if ancillary_removed:
        leftover = leftover.replace(ancillary_removed.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "de.text.ancillary_rights_removed.v1",
                {"action": "removed", "raw": ancillary_removed.group(0).strip()},
            )
        )
    ancillary_negated = _FR_ANCILLARY_OBLIGATIONS_NEGATED.search(leftover)
    if ancillary_negated:
        leftover = leftover.replace(ancillary_negated.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "fr.text.ancillary_obligations_negated.v1",
                {
                    "kind": "ancillary_obligations",
                    "action": "correction_negated",
                    "raw": ancillary_negated.group(0).strip(),
                },
            )
        )
    ancillary_fr_removed = _FR_ANCILLARY_OBLIGATIONS_REMOVED.search(leftover)
    if ancillary_fr_removed:
        leftover = leftover.replace(ancillary_fr_removed.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "fr.text.ancillary_obligations_removed.v1",
                {
                    "kind": "ancillary_obligations",
                    "action": "removed",
                    "raw": ancillary_fr_removed.group(0).strip(),
                },
            )
        )
    purpose_reservation_removed = _DE_PURPOSE_RESERVATION_REMOVED.search(leftover)
    if purpose_reservation_removed:
        leftover = leftover.replace(purpose_reservation_removed.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "de.text.purpose_reservation_removed.v1",
                {
                    "kind": "purpose_change_reservation",
                    "action": "removed",
                    "law": "ZGB 86a",
                },
            )
        )
    purpose_reservation = _DE_PURPOSE_RESERVATION.search(leftover)
    if purpose_reservation:
        leftover = leftover.replace(purpose_reservation.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "de.text.purpose_reservation.v1",
                {
                    "kind": "purpose_change_reservation",
                    "action": "added",
                    "law": "ZGB 86a",
                },
            )
        )
    fr_purpose_reservation = _FR_PURPOSE_RESERVATION.search(leftover)
    if fr_purpose_reservation:
        leftover = leftover.replace(fr_purpose_reservation.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "fr.text.purpose_reservation.v1",
                {
                    "kind": "purpose_change_reservation",
                    "action": "added",
                    "law": "CC 86a",
                },
            )
        )
    ancillary = (
        _DE_ANCILLARY_RIGHTS.search(leftover)
        or _FR_ANCILLARY_OBLIGATIONS.search(leftover)
        or _IT_ANCILLARY_OBLIGATIONS.search(leftover)
    )
    if ancillary:
        leftover = leftover.replace(ancillary.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                (
                    "de.text.ancillary_rights.v1"
                    if ancillary.re is _DE_ANCILLARY_RIGHTS
                    else "fr.text.ancillary_obligations.v1"
                    if ancillary.re is _FR_ANCILLARY_OBLIGATIONS
                    else "it.text.ancillary_obligations.v1"
                ),
                {"raw": ancillary.group(0).strip()},
            )
        )
    fr_contribution_rules = _FR_CONTRIBUTION_RULES_REMOVED.search(leftover)
    if fr_contribution_rules:
        leftover = leftover.replace(fr_contribution_rules.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "fr.text.contribution_rules_removed.v1",
                {"action": "removed", "raw": fr_contribution_rules.group(0).strip()},
            )
        )
    contribution_rules = _IT_CONTRIBUTION_RULES_REMOVED.search(leftover)
    if contribution_rules:
        leftover = leftover.replace(contribution_rules.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "it.text.contribution_rules_removed.v1",
                {"action": "removed", "raw": contribution_rules.group(0).strip()},
            )
        )
    calls_completed = _DE_ART_155_CALLS_COMPLETED.search(leftover)
    if calls_completed:
        leftover = leftover.replace(calls_completed.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.art_155_deletion_procedure_completed.v1",
                {
                    "kind": "official_deletion_procedure_completed",
                    "law": "Art. 155 HRegV",
                    "issues": calls_completed.group("issues").strip(),
                    "creditor_responses": False,
                },
            )
        )
        event_types.add("status_changed")
    foundation_suppressed = _IT_FOUNDATION_SUPPRESSED_DELETION_BLOCKED.search(
        leftover
    )
    if foundation_suppressed:
        leftover = leftover.replace(foundation_suppressed.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "it.text.foundation_suppressed_deletion_blocked.v1",
                {
                    "kind": "deletion_blocked",
                    "entity": "foundation",
                    "action": "suppressed",
                    "decision_date": _swiss_date(foundation_suppressed.group("date")),
                    "authority": foundation_suppressed.group("authority").strip(),
                    "authority_place": foundation_suppressed.group(
                        "authority_place"
                    ).strip(),
                    "authority_uid": foundation_suppressed.group("authority_uid"),
                    "tax_authority_consent_missing": True,
                },
            )
        )
        event_types.add("status_changed")
    blocked = (
        _DE_ART_934_INACTIVE_DELETION_BLOCKED.search(leftover)
        or _DE_ART_934_CALLS_DELETION_BLOCKED.search(leftover)
        or _DE_ART_934_OFFICIAL_PROCEDURE_DELETION_BLOCKED.search(leftover)
        or _DE_ART_155_DATED_CALLS_DELETION_BLOCKED.search(leftover)
        or _DE_ART_155_NUMBERED_CALLS_DELETION_BLOCKED.search(leftover)
        or _DE_ART_155_CALLS_DELETION_BLOCKED.search(leftover)
        or _DE_ART_155_DELETION_BLOCKED.search(leftover)
        or _DE_DELETION_BLOCKED.search(leftover)
        or _IT_DELETION_BLOCKED.search(leftover)
        or _IT_ART_155_DELETION_BLOCKED.search(leftover)
        or _IT_OFFICE_DELETION_BLOCKED.search(leftover)
        or _IT_ART_934_DELETION_BLOCKED.search(leftover)
        or _IT_ART_155_CALLS_DELETION_BLOCKED.search(leftover)
        or _IT_SUPPRESSED_DELETION_BLOCKED.search(leftover)
        or _IT_ART_748_DELETION_BLOCKED.search(leftover)
    )
    if blocked:
        leftover = leftover.replace(blocked.group(0), " ")
        is_art_934 = blocked.re in {
            _DE_ART_934_INACTIVE_DELETION_BLOCKED,
            _DE_ART_934_CALLS_DELETION_BLOCKED,
            _DE_ART_934_OFFICIAL_PROCEDURE_DELETION_BLOCKED,
            _IT_ART_934_DELETION_BLOCKED,
        }
        blocked_payload = {"kind": "deletion_blocked", "raw": blocked.group(0).strip()}
        if blocked.re is _DE_ART_155_DATED_CALLS_DELETION_BLOCKED:
            blocked_payload.update(
                {
                    "legal_basis": "Art. 155 HRegV",
                    "procedure_completed": True,
                    "calls_published_at": blocked.group("dates").strip(),
                    "creditor_responses": False,
                    "inactive": True,
                    "assets_available": False,
                    "tax_authority_consent_missing": True,
                    "tax_authority": (
                        "federal"
                        if blocked.group("tax_authority").lower().startswith("eidg")
                        else "cantonal"
                    ),
                }
            )
        if is_art_934:
            blocked_payload["legal_basis"] = (
                "Art. 934 CO"
                if blocked.re is _IT_ART_934_DELETION_BLOCKED
                else "Art. 934 OR"
            )
        if blocked.re in {
            _DE_ART_934_INACTIVE_DELETION_BLOCKED,
            _DE_ART_934_CALLS_DELETION_BLOCKED,
            _DE_ART_934_OFFICIAL_PROCEDURE_DELETION_BLOCKED,
        }:
            blocked_payload["procedure_completed"] = True
        if blocked.re is _DE_ART_934_OFFICIAL_PROCEDURE_DELETION_BLOCKED:
            raw_date = blocked.group("date")
            blocked_payload["procedure_completed_at"] = (
                _swiss_date(raw_date)
                if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", raw_date)
                else _german_written_date(raw_date)
            )
            blocked_payload["tax_authority_consent_missing"] = True
        if blocked.re is _DE_ART_934_CALLS_DELETION_BLOCKED:
            blocked_payload["issues"] = blocked.group("issues").strip()
        if blocked.re is _DE_ART_155_DATED_CALLS_DELETION_BLOCKED:
            blocked_rule_id = "de.text.art_155_deletion_blocked.v2"
        elif blocked.re is _IT_ART_934_DELETION_BLOCKED:
            blocked_rule_id = "it.text.art_934_deletion_blocked.v1"
        elif is_art_934:
            blocked_rule_id = "de.text.art_934_deletion_blocked.v1"
        else:
            blocked_rule_id = "text.deletion_blocked.v1"
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                blocked_rule_id,
                blocked_payload,
            )
        )
    branch_blocked = _IT_BRANCH_DELETION_BLOCKED.search(leftover)
    if branch_blocked:
        leftover = leftover.replace(branch_blocked.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "it.text.branch_deletion_blocked.v1",
                {
                    "kind": "deletion_blocked",
                    "scope": "branch",
                    "head_office": branch_blocked.group("head_office").strip(),
                    "raw": branch_blocked.group(0).strip(),
                },
            )
        )
    additional_address_removed = _DE_ADDITIONAL_ADDRESS_REMOVED.search(leftover)
    if additional_address_removed:
        leftover = leftover.replace(additional_address_removed.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "address_changed",
                "de.text.additional_address_removed.v1",
                {
                    "action": "removed",
                    "kind": "additional_address",
                    "address": additional_address_removed.group("address").strip(),
                },
            )
        )
        event_types.add("address_changed")
    additional_address = _DE_ADDITIONAL_ADDRESS.search(leftover)
    if additional_address:
        leftover = leftover.replace(additional_address.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "address_changed",
                "de.text.additional_address.v1",
                {"action": "added", "address": additional_address.group("address").strip()},
            )
        )
        event_types.add("address_changed")
    replaced_legacy_branch = _DE_BRANCH_REPLACED_LEGACY.search(leftover)
    if replaced_legacy_branch:
        leftover = leftover.replace(replaced_legacy_branch.group(0), " ")
        for action, place_group, id_key, id_group in (
            ("removed", "from_place", "branch_registry_id", "from_registry_id"),
            ("added", "to_place", "branch_uid", "to_uid"),
        ):
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "branch_changed",
                    f"de.text.branch_{action}.v2",
                    {
                        "action": action,
                        "place": replaced_legacy_branch.group(place_group).strip(),
                        id_key: replaced_legacy_branch.group(id_group),
                    },
                )
            )
    branch_removed = _DE_BRANCH_REMOVED.search(leftover)
    if branch_removed:
        leftover = leftover.replace(branch_removed.group(0), " ")
        branch_removed_payload = {
            "action": "removed",
            "place": branch_removed.group("place").strip(),
        }
        if branch_removed.group("uid"):
            branch_removed_payload["branch_uid"] = branch_removed.group("uid")
        if branch_removed.group("register_canton"):
            branch_removed_payload["register_canton"] = branch_removed.group(
                "register_canton"
            ).upper()
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "branch_changed",
                "de.text.branch_removed.v1",
                branch_removed_payload,
            )
        )
        for continued_branch in list(
            _DE_BRANCH_REMOVED_CONTINUATION.finditer(leftover)
        ):
            continued_payload = {
                "action": "removed",
                "place": continued_branch.group("place").strip(),
            }
            if continued_branch.group("uid"):
                continued_payload["branch_uid"] = continued_branch.group("uid")
            if continued_branch.group("register_canton"):
                continued_payload["register_canton"] = continued_branch.group(
                    "register_canton"
                ).upper()
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "branch_changed",
                    "de.text.branch_removed.v1",
                    continued_payload,
                )
            )
            leftover = leftover.replace(continued_branch.group(0), " ", 1)
    branch_seat_changed = _DE_BRANCH_SEAT_CHANGED.search(leftover)
    if branch_seat_changed:
        leftover = leftover.replace(branch_seat_changed.group(0), " ")
        register_canton = (
            branch_seat_changed.group("register_canton")
            or branch_seat_changed.group("previous_register_canton")
        ).upper()
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "branch_changed",
                "de.text.branch_seat_changed.v1",
                {
                    "action": "seat_changed",
                    "from": branch_seat_changed.group("from").strip(),
                    "to": branch_seat_changed.group("to").strip(),
                    "branch_uid": branch_seat_changed.group("uid"),
                    "previous_branch_uid": branch_seat_changed.group("previous_uid"),
                    "register_canton": register_canton,
                    "previous_register_canton": branch_seat_changed.group(
                        "previous_register_canton"
                    ).upper(),
                    **(
                        {
                            "register_section": branch_seat_changed.group(
                                "register_section"
                            ).strip()
                        }
                        if branch_seat_changed.group("register_section")
                        else {}
                    ),
                    **(
                        {
                            "previous_register_section": branch_seat_changed.group(
                                "previous_register_section"
                            ).strip()
                        }
                        if branch_seat_changed.group("previous_register_section")
                        else {}
                    ),
                    **(
                        {
                            "place_canton": branch_seat_changed.group(
                                "place_canton"
                            ).upper()
                        }
                        if branch_seat_changed.group("place_canton")
                        else {}
                    ),
                },
            )
        )
    simple_branch_seat_changed = _DE_BRANCH_SIMPLE_SEAT_CHANGED.search(leftover)
    if simple_branch_seat_changed:
        leftover = leftover.replace(simple_branch_seat_changed.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "branch_changed",
                "de.text.branch_seat_changed.v2",
                {
                    "action": "seat_changed",
                    "from": simple_branch_seat_changed.group("from").strip(),
                    "to": simple_branch_seat_changed.group("to").strip(),
                    "branch_uid": simple_branch_seat_changed.group("uid"),
                    "previous_branch_uid": simple_branch_seat_changed.group(
                        "previous_uid"
                    ),
                },
            )
        )
    branch_added = _DE_BRANCH_ADDED.search(leftover)
    if branch_added:
        continuation = _DE_BRANCH_ADDED_CONTINUATION.match(
            leftover[branch_added.end() :]
        )
        leftover = leftover.replace(branch_added.group(0), " ", 1)
        branch_payload = {
            "action": "added",
            "place": branch_added.group("place").strip(),
            "branch_uid": branch_added.group("uid"),
        }
        if branch_added.group("place_canton"):
            branch_payload["place_canton"] = branch_added.group(
                "place_canton"
            ).upper()
        register_canton = (
            branch_added.group("leading_register_canton")
            or branch_added.group("register_canton")
        )
        if register_canton:
            register_canton = register_canton.upper()
            branch_payload["register_canton"] = {
                "BASEL-STADT": "BS",
                "BASEL-LANDSCHAFT": "BL",
            }.get(register_canton, register_canton)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "branch_changed",
                "de.text.branch_added.v1",
                branch_payload,
            )
        )
        if continuation:
            continuation_text = continuation.group(0)
            continuation_payload = {
                "action": "added",
                "place": continuation.group("place").strip(),
                "branch_uid": continuation.group("uid"),
            }
            if continuation.group("place_canton"):
                continuation_payload["place_canton"] = continuation.group(
                    "place_canton"
                ).upper()
            leftover = leftover.replace(continuation_text, " ", 1)
            events.append(
                _event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "branch_changed",
                    "de.text.branch_added.v1",
                    continuation_payload,
                )
            )
    branch_transferred = _DE_BRANCH_TRANSFERRED_BY_MERGER.search(leftover)
    if branch_transferred:
        leftover = leftover.replace(branch_transferred.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "branch_changed",
                "de.text.branch_transferred_by_merger.v1",
                {
                    "action": "transferred",
                    "reason": "merger",
                    "legal_basis": "Art. 112 HRegV",
                },
            )
        )
    it_branch_removed = _IT_BRANCH_REMOVED.search(leftover)
    if it_branch_removed:
        leftover = leftover.replace(it_branch_removed.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "branch_changed",
                "it.text.branch_removed.v1",
                {
                    "action": "removed",
                    "place": it_branch_removed.group("place").strip(),
                },
            )
        )
    it_branch_added = _IT_BRANCH_ADDED.search(leftover)
    if it_branch_added:
        leftover = leftover.replace(it_branch_added.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "branch_changed",
                "it.text.branch_added.v1",
                {
                    "action": "added",
                    "place": it_branch_added.group("place").strip(),
                    "branch_uid": it_branch_added.group("uid"),
                },
            )
        )
    fr_branch_deleted = _FR_BRANCH_REMOVED.search(leftover)
    if fr_branch_deleted:
        leftover = leftover.replace(fr_branch_deleted.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "branch_changed",
                "fr.text.branch_removed.v1",
                {
                    "action": "removed",
                    "place": fr_branch_deleted.group("place").strip(),
                    "branch_uid": fr_branch_deleted.group("uid"),
                },
            )
        )
    fr_branch_added = _FR_BRANCH_MENTION_ADDED.search(leftover)
    if fr_branch_added:
        leftover = leftover.replace(fr_branch_added.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "branch_changed",
                "fr.text.branch_added.v1",
                {
                    "action": "added",
                    "place": fr_branch_added.group("place").strip(),
                    "branch_uid": fr_branch_added.group("uid"),
                },
            )
        )
    fr_branch_removed = _FR_BRANCH_MENTION_REMOVED.search(leftover)
    if fr_branch_removed:
        leftover = leftover.replace(fr_branch_removed.group(0), " ")
        payload = {
            "action": "removed",
            "place": fr_branch_removed.group("place").strip(),
        }
        if fr_branch_removed.group("uid"):
            payload["branch_uid"] = fr_branch_removed.group("uid")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "branch_changed",
                "fr.text.branch_removed.v1",
                payload,
            )
        )
    legacy_fr_branch_removed = _FR_BRANCH_REMOVED_LEGACY.search(leftover)
    if legacy_fr_branch_removed:
        leftover = leftover.replace(legacy_fr_branch_removed.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "branch_changed",
                "fr.text.branch_removed.v2",
                {
                    "action": "removed",
                    "place": legacy_fr_branch_removed.group("place").strip(),
                },
            )
        )
    branch_closed = _DE_BRANCH_CLOSED_PENDING.search(leftover)
    if branch_closed:
        leftover = leftover.replace(branch_closed.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "branch_changed",
                "de.text.branch_closed_pending_deletion.v1",
                {
                    "action": "closed",
                    "deletion_pending": True,
                    "reason": "tax_authority_approval_pending",
                },
            )
        )
    no_dom = _IT_NO_DOMICILE.search(leftover)
    if no_dom:
        leftover = leftover.replace(no_dom.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "address_changed",
                "it.text.no_domicile.v1",
                {"kind": "no_legal_domicile"},
            )
        )
        event_types.add("address_changed")
    removed_trade_name = _DE_TRADE_NAME_ESTABLISHMENT_REMOVED.search(leftover)
    if removed_trade_name:
        leftover = leftover.replace(removed_trade_name.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "organization_changed",
                "de.text.trade_name_establishment_removed.v1",
                {
                    "kind": "trade_name_establishment",
                    "action": "removed",
                    "trade_name": removed_trade_name.group("trade_name").strip(),
                    "place": removed_trade_name.group("place").strip(),
                    "address": removed_trade_name.group("address").strip(),
                },
            )
        )
    belege = _DE_BELEGE.search(leftover)
    if belege:
        leftover = leftover.replace(belege.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.documents.v1",
                {"kind": "documents_updated"},
            )
        )
    bankruptcy_administration = _DE_BANKRUPTCY_ADMINISTRATION_REPLACED.search(
        leftover
    )
    if bankruptcy_administration:
        leftover = leftover.replace(bankruptcy_administration.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "organization_changed",
                "de.text.bankruptcy_administration_replaced.v1",
                {
                    "kind": "bankruptcy_administration",
                    "action": "replaced",
                    "decision_date": _swiss_date(
                        bankruptcy_administration.group("date")
                    ),
                    "authority": bankruptcy_administration.group("authority").strip(),
                    "from_name": bankruptcy_administration.group(
                        "from_name"
                    ).strip(),
                    "to_name": bankruptcy_administration.group("to_name").strip(),
                    "to_uid": bankruptcy_administration.group("to_uid"),
                    "to_address": bankruptcy_administration.group(
                        "to_address"
                    ).strip(),
                },
            )
        )
    liability_clause_removed = _DE_LIABILITY_CLAUSE_REMOVED.search(leftover)
    if liability_clause_removed:
        leftover = leftover.replace(liability_clause_removed.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "de.text.liability_clause_removed.v1",
                {
                    "kind": "liability_and_additional_contributions",
                    "action": "removed",
                    "reason": "changed_registration_rules",
                    "previous": liability_clause_removed.group("previous").strip(),
                },
            )
        )
    association_organization_removed = _DE_ASSOCIATION_ORGANIZATION_REMOVED.search(
        leftover
    )
    if association_organization_removed:
        leftover = leftover.replace(association_organization_removed.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "organization_changed",
                "de.text.organization_removed.v2",
                {
                    "action": "removed",
                    "reason": "changed_registration_rules",
                    "law": re.sub(
                        r"\s+", " ", association_organization_removed.group("law")
                    ).strip(),
                },
            )
        )
    organization_removed = _DE_ORGANIZATION_REMOVED.search(leftover)
    if organization_removed:
        leftover = leftover.replace(organization_removed.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "organization_changed",
                "de.text.organization_removed.v1",
                {
                    "action": "removed",
                    "reason": "changed_registration_rules",
                    "law": "Art. 95 Abs. 1 HRegV",
                },
            )
        )
    it_organization_removed = _IT_ORGANIZATION_REMOVED.search(leftover)
    if it_organization_removed:
        leftover = leftover.replace(it_organization_removed.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "organization_changed",
                "it.text.organization_removed.v1",
                {
                    "action": "removed",
                    "reason": "changed_registration_rules",
                    "law": "Art. 95 cpv. 1 lett. h ORC",
                },
            )
        )
    obsolete_corporation_indications = (
        _IT_OBSOLETE_CORPORATION_INDICATIONS_REMOVED.search(leftover)
    )
    if obsolete_corporation_indications:
        leftover = leftover.replace(obsolete_corporation_indications.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "organization_changed",
                "it.text.obsolete_corporation_indications_removed.v1",
                {
                    "action": "removed",
                    "reason": "registration_not_required",
                    "law": "Art. 45 ORC",
                    "detail": "statutes_adapted_to_new_corporate_law",
                },
            )
        )
    board_composition_removed = _FR_BOARD_COMPOSITION_REMOVED.search(leftover)
    if board_composition_removed:
        leftover = leftover.replace(board_composition_removed.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "organization_changed",
                "fr.text.board_composition_removed.v1",
                {
                    "kind": "board_composition",
                    "action": "removed",
                    "reason": "registration_not_required",
                },
            )
        )
    fr_organization_removed = _FR_ORGANIZATION_REMOVED.search(leftover)
    if fr_organization_removed:
        leftover = leftover.replace(fr_organization_removed.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "organization_changed",
                "fr.text.organization_removed.v1",
                {
                    "action": "removed",
                    "reason": "registration_not_required",
                },
            )
        )
    audit_waiver_corrected = _DE_AUDIT_WAIVER_CORRECTED.search(leftover)
    if audit_waiver_corrected:
        leftover = leftover.replace(audit_waiver_corrected.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "audit_requirement_changed",
                "de.text.audit_waiver_corrected.v1",
                {
                    "kind": "limited_audit_waiver",
                    "action": "corrected",
                    "waiver_declared": False,
                    "previous_entry_erroneous": True,
                },
            )
        )
    audit_waiver_revoked = _DE_AUDIT_WAIVER_REVOKED.search(leftover)
    if audit_waiver_revoked:
        leftover = leftover.replace(audit_waiver_revoked.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "audit_requirement_changed",
                "de.text.audit_waiver_revoked.v1",
                {
                    "kind": "limited_audit_waiver",
                    "action": "revoked",
                    "raw": audit_waiver_revoked.group(0).strip(),
                },
            )
        )
    de_audit_waiver = _DE_AUDIT_WAIVER.search(leftover)
    if de_audit_waiver:
        leftover = leftover.replace(de_audit_waiver.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "audit_requirement_changed",
                "de.text.audit_waiver.v1",
                {
                    "kind": "limited_audit_waiver",
                    "action": "granted",
                    "date": _swiss_date(de_audit_waiver.group("date")),
                },
            )
        )
    audit_waiver = _FR_AUDIT_WAIVER.search(leftover)
    if audit_waiver:
        leftover = leftover.replace(audit_waiver.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "audit_requirement_changed",
                "fr.text.audit_waiver.v1",
                {
                    "kind": "limited_audit_waiver",
                    "action": "granted",
                    "date": (
                        _swiss_date(audit_waiver.group("date"))
                        if re.fullmatch(
                            r"\d{2}\.\d{2}\.\d{4}", audit_waiver.group("date")
                        )
                        else _french_written_date(audit_waiver.group("date"))
                    ),
                },
            )
        )
    it_audit_waiver = _IT_AUDIT_WAIVER.search(leftover)
    if it_audit_waiver:
        leftover = leftover.replace(it_audit_waiver.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "audit_requirement_changed",
                "it.text.audit_waiver.v1",
                {
                    "kind": "limited_audit_waiver",
                    "action": "granted",
                    "date": _swiss_date(it_audit_waiver.group("date")),
                },
            )
        )
    communications_clause_removed = _FR_COMMUNICATIONS_CLAUSE_REMOVED.search(
        leftover
    )
    if communications_clause_removed:
        leftover = leftover.replace(communications_clause_removed.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "organization_changed",
                "fr.text.communications_clause_removed.v1",
                {
                    "kind": "communications",
                    "action": "special_clause_removed",
                },
            )
        )
    communication_patterns = {
        "de": _DE_COMMUNICATIONS,
        "fr": _FR_COMMUNICATIONS,
        "it": _IT_COMMUNICATIONS,
    }
    communication_pattern = communication_patterns.get(lang, _DE_COMMUNICATIONS)
    communications = communication_pattern.search(leftover)
    if not communications:
        for fallback_pattern in (
            _DE_COMMUNICATIONS,
            _FR_COMMUNICATIONS,
            _IT_COMMUNICATIONS,
        ):
            if fallback_pattern is communication_pattern:
                continue
            communications = fallback_pattern.search(leftover)
            if communications:
                break
    if communications:
        leftover = leftover.replace(communications.group(0), " ")
        communications_lang = (
            "it"
            if communications.re is _IT_COMMUNICATIONS
            else "fr"
            if communications.re is _FR_COMMUNICATIONS
            else "de"
        )
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "organization_changed",
                f"{communications_lang}.text.communications.v1",
                {
                    "kind": "communications",
                    "to": communications.group("to").strip().rstrip("."),
                },
            )
        )
    for extra_pat in _DE_STATUTE_EXTRAS:
        leftover = extra_pat.sub(" ", leftover)
    inhaber = _DE_INHABER_CONTINUES.search(leftover)
    if inhaber:
        leftover = leftover.replace(inhaber.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.owner_continues.v1",
                {"kind": "registration_continued", "raw": inhaber.group(0).strip()},
            )
        )
    titulaire = _FR_TITULAIRE_CONTINUES.search(leftover)
    if titulaire:
        leftover = leftover.replace(titulaire.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "fr.text.owner_continues.v1",
                {"kind": "registration_continued", "raw": titulaire.group(0).strip()},
            )
        )
    it_owner = _IT_OWNER_CONTINUES.search(leftover)
    if it_owner:
        leftover = leftover.replace(it_owner.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "it.text.owner_continues.v1",
                {"kind": "registration_continued", "raw": it_owner.group(0).strip()},
            )
        )
    opposed = _FR_DELETION_OPPOSED.search(leftover)
    if opposed:
        leftover = leftover.replace(opposed.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "fr.text.deletion_opposed.v1",
                {"kind": "deletion_opposed", "raw": opposed.group(0).strip()},
            )
        )
    supplement = _SUPPLEMENT_MARKER.search(leftover)
    if supplement:
        leftover = leftover.replace(supplement.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "publication_corrected",
                "de.text.supplement.v1",
                {"kind": "supplement"},
            )
        )
    found_no_aud = _IT_NO_AUDITOR.search(leftover)
    if found_no_aud:
        leftover = leftover.replace(found_no_aud.group(0), " ")
    shab_deletion_blocked = _DE_ART_934_SHAB_NOTICE_DELETION_BLOCKED.search(leftover)
    if shab_deletion_blocked:
        leftover = leftover.replace(shab_deletion_blocked.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.art_934_deletion_blocked.v2",
                {
                    "kind": "deletion_blocked",
                    "legal_basis": "Art. 934 OR",
                    "procedure_completed": True,
                    "issues": shab_deletion_blocked.group("issues").strip(),
                    "affected_parties_responded": False,
                    "tax_authority_consent_missing": True,
                },
            )
        )
        event_types.add("status_changed")
    moratorium_until = _DE_COMPOSITION_MORATORIUM_EXTENDED_UNTIL.search(leftover)
    if moratorium_until:
        leftover = leftover.replace(moratorium_until.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.composition_moratorium_extended.v3",
                {
                    "kind": "composition_moratorium_extended",
                    "decision_date": _swiss_date(moratorium_until.group("decision_date")),
                    "until": _swiss_date(moratorium_until.group("until")),
                    "authority": moratorium_until.group("authority").strip(),
                },
            )
        )
        event_types.add("status_changed")
    bankruptcy_opened = _DE_BANKRUPTCY_OPENED.search(leftover)
    if bankruptcy_opened:
        leftover = leftover.replace(bankruptcy_opened.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.bankruptcy_opened.v1",
                {
                    "kind": "bankruptcy_opened",
                    "decision_date": _swiss_date(bankruptcy_opened.group("decision_date")),
                    "effective_date": _swiss_date(bankruptcy_opened.group("effective_date")),
                    "effective_time": bankruptcy_opened.group("time").replace(".", ":"),
                    "authority": bankruptcy_opened.group("authority").strip(),
                },
            )
        )
        event_types.add("status_changed")
    sole_proprietor_transfer = _FR_SOLE_PROPRIETOR_ASSET_TRANSFER.search(leftover)
    if sole_proprietor_transfer:
        leftover = leftover.replace(sole_proprietor_transfer.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "assets_transferred",
                "fr.text.asset_transfer.v2",
                {
                    "date": _swiss_date(sole_proprietor_transfer.group("date")),
                    "amendments": sole_proprietor_transfer.group("amendments").strip(),
                    "assets": sole_proprietor_transfer.group("assets"),
                    "liabilities": sole_proprietor_transfer.group("liabilities"),
                    "net_assets": sole_proprietor_transfer.group("net"),
                    "recipient": sole_proprietor_transfer.group("recipient").strip(),
                    "recipient_place": sole_proprietor_transfer.group("place").strip(),
                    "recipient_uid": sole_proprietor_transfer.group("uid"),
                    "consideration": sole_proprietor_transfer.group("consideration").strip(),
                },
            )
        )
    cooperative_share_range = _FR_COOPERATIVE_SHARE_RANGE.search(leftover)
    if cooperative_share_range:
        leftover = leftover.replace(cooperative_share_range.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "fr.text.cooperative_share_range.v1",
                {
                    "kind": "cooperative_share_range",
                    "currency": "CHF",
                    "minimum": cooperative_share_range.group("minimum"),
                    "maximum": cooperative_share_range.group("maximum"),
                },
            )
        )
        event_types.add("capital_changed")
    translations_removed = _FR_TRANSLATIONS_REMOVED.search(leftover)
    if translations_removed:
        leftover = leftover.replace(translations_removed.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "company_name_changed",
                "fr.text.translations_removed.v1",
                {"kind": "translations", "action": "removed"},
            )
        )
        event_types.add("company_name_changed")
    cooperative_obligations = _DE_COOPERATIVE_LIABILITY_AND_OBLIGATIONS.search(leftover)
    if cooperative_obligations:
        leftover = leftover.replace(cooperative_obligations.group(0), " ")
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "de.text.cooperative_obligations.v1",
                {
                    "kind": "liability_and_member_obligations",
                    "action": "changed",
                    "liability_action": "removed",
                    "previous_liability": cooperative_obligations.group("previous_liability").strip(),
                    "obligations": cooperative_obligations.group("obligations").strip(),
                    "previous_obligations": cooperative_obligations.group("previous_obligations").strip(),
                    "reason": "changed_registration_rules",
                },
            )
        )
    branch_after_removal = (
        _DE_BRANCH_ADDED_AFTER_REMOVAL.search(leftover) if branch_removed else None
    )
    if branch_after_removal:
        leftover = leftover.replace(branch_after_removal.group(0), " ", 1)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "branch_changed",
                "de.text.branch_added.v2",
                {
                    "action": "added",
                    "place": branch_after_removal.group("place").strip(),
                    "branch_uid": branch_after_removal.group("uid"),
                },
            )
        )
    for boiler in _BOILERPLATE:
        leftover = boiler.sub(" ", leftover)
    leftover = _EMPTY_NEGATION_MARKER.sub(" ", leftover)
    leftover = _EMPTY_HISTORY_MARKER.sub(" ", leftover)
    leftover = _NEGATION_MARKER.sub(" ", leftover)
    if "company_deleted" in event_types:
        for note in _DELETION_NOTES:
            found = note.search(leftover)
            if found:
                leftover = leftover.replace(found.group(0), " ")
    if "status_changed" in event_types:
        found = _BANKRUPTCY_NOTE.search(leftover)
        if found:
            leftover = leftover.replace(found.group(0), " ")
        leftover = _DE_FALSE_DISSOLUTION.sub(" ", leftover)
    for event_type, phrases in _CONSUME.items():
        if event_type not in event_types:
            continue
        for phrase in phrases:
            leftover = phrase.sub(" ", leftover)
    leftover = re.sub(r"\s+", " ", leftover).strip(" .")
    leftover = _strip_header(leftover)
    leftover = re.sub(r"\s+", " ", leftover).strip(" .")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
