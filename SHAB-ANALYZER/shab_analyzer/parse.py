from __future__ import annotations

from pathlib import Path

from .models import Event, ParseResult
from .parser50 import extract_parser50_leftovers
from .parser51 import extract_parser51_leftovers
from .parser52 import extract_parser52_leftovers
from .parser53 import extract_parser53_leftovers
from .parser54 import extract_parser54_leftovers
from .parser55 import extract_parser55_leftovers
from .parser56 import extract_parser56_leftovers
from .parser57 import extract_parser57_leftovers
from .parser58 import extract_parser58_leftovers
from .parser59 import extract_parser59_leftovers
from .parser60 import extract_parser60_leftovers
from .parser61 import extract_parser61_leftovers
from .parser62 import extract_parser62_leftovers
from .parser63 import extract_parser63_leftovers
from .parser64 import extract_parser64_leftovers
from .parser65 import extract_parser65_leftovers
from .parser66 import extract_parser66_leftovers
from .parser67 import extract_parser67_leftovers
from .parser68 import extract_parser68_leftovers
from .parser69 import extract_parser69_leftovers
from .parser70 import extract_parser70_leftovers
from .parser71 import extract_parser71_leftovers
from .parser72 import extract_parser72_leftovers
from .parser73 import extract_parser73_leftovers
from .parser74 import extract_parser74_leftovers
from .parser75 import extract_parser75_leftovers
from .parser76 import extract_parser76_leftovers
from .parser77 import extract_parser77_leftovers
from .parser78 import extract_parser78_leftovers
from .parser79 import extract_parser79_leftovers
from .parser80 import extract_parser80_leftovers
from .parser81 import extract_parser81_leftovers
from .parser82 import extract_parser82_leftovers
from .parser83 import extract_parser83_leftovers
from .parser84 import extract_parser84_leftovers
from .parser85 import extract_parser85_leftovers
from .parser86 import extract_parser86_leftovers
from .parser87 import extract_parser87_leftovers
from .parser88 import extract_parser88_leftovers
from .parser89 import extract_parser89_leftovers
from .parser90 import extract_parser90_leftovers
from .parser91 import extract_parser91_leftovers
from .parser92 import extract_parser92_leftovers
from .parser93 import extract_parser93_leftovers
from .parser94 import extract_parser94_leftovers
from .parser95 import extract_parser95_leftovers
from .parser96 import extract_parser96_leftovers
from .parser97 import extract_parser97_leftovers
from .parser98 import extract_parser98_leftovers
from .parser99 import extract_parser99_leftovers
from .parser100 import extract_parser100_leftovers
from .parser101 import extract_parser101_leftovers
from .parser102 import extract_parser102_leftovers
from .parser103 import extract_parser103_leftovers
from .parser104 import extract_parser104_leftovers
from .parser105 import extract_parser105_leftovers
from .parser106 import extract_parser106_leftovers
from .parser107 import extract_parser107_leftovers
from .parser108 import extract_parser108_leftovers
from .parser109 import extract_parser109_leftovers
from .parser110 import extract_parser110_leftovers
from .parser111 import extract_parser111_leftovers
from .parser112 import extract_parser112_leftovers
from .parser113 import extract_parser113_leftovers
from .parser114 import extract_parser114_leftovers
from .parser115 import extract_parser115_leftovers
from .parser116 import extract_parser116_leftovers
from .parser117 import extract_parser117_leftovers
from .parser118 import extract_parser118_leftovers
from .parser119 import extract_parser119_leftovers
from .parser120 import extract_parser120_leftovers
from .parser121 import extract_parser121_leftovers
from .parser122 import extract_parser122_leftovers
from .parser123 import extract_parser123_leftovers
from .parser124 import extract_parser124_leftovers
from .parser125 import extract_parser125_leftovers
from .parser126 import extract_parser126_leftovers
from .parser127 import extract_parser127_leftovers
from .parser128 import extract_parser128_leftovers
from .parser129 import extract_parser129_leftovers
from .parser130 import extract_parser130_leftovers
from .parser131 import extract_parser131_leftovers
from .parser132 import extract_parser132_leftovers
from .parser133 import extract_parser133_leftovers
from .parser134 import extract_parser134_leftovers
from .parser135 import extract_parser135_leftovers
from .parser136 import extract_parser136_leftovers
from .parser137 import extract_parser137_leftovers
from .parser138 import extract_parser138_leftovers
from .parser139 import extract_parser139_leftovers
from .parser140 import extract_parser140_leftovers
from .parser141 import extract_parser141_leftovers
from .parser142 import extract_parser142_leftovers
from .parser143 import extract_parser143_leftovers
from .parser144 import extract_parser144_leftovers
from .parser145 import extract_parser145_leftovers
from .parser146 import extract_parser146_leftovers
from .parser147 import extract_parser147_leftovers
from .parser148 import extract_parser148_leftovers
from .parser149 import extract_parser149_leftovers
from .parser150 import extract_parser150_leftovers
from .parser151 import extract_parser151_leftovers
from .parser152 import extract_parser152_leftovers
from .parser153 import extract_parser153_leftovers
from .parser154 import extract_parser154_leftovers
from .parser155 import extract_parser155_leftovers
from .parser156 import extract_parser156_leftovers
from .parser157 import extract_parser157_leftovers
from .parser158 import extract_parser158_leftovers
from .parser159 import extract_parser159_leftovers
from .parser160 import extract_parser160_leftovers
from .parser161 import extract_parser161_leftovers
from .parser162 import extract_parser162_leftovers
from .parser163 import extract_parser163_leftovers
from .parser164 import extract_parser164_leftovers
from .parser165 import extract_parser165_leftovers
from .parser166 import extract_parser166_leftovers
from .parser167 import extract_parser167_leftovers
from .parser168 import extract_parser168_leftovers
from .parser169 import extract_parser169_leftovers
from .parser170 import extract_parser170_leftovers
from .parser171 import extract_parser171_leftovers
from .parser172 import extract_parser172_leftovers
from .parser173 import extract_parser173_leftovers
from .parser174 import extract_parser174_leftovers
from .parser175 import extract_parser175_leftovers
from .parser176 import extract_parser176_leftovers
from .parser177 import extract_parser177_leftovers
from .parser178 import extract_parser178_leftovers
from .parser179 import extract_parser179_leftovers
from .parser180 import extract_parser180_leftovers
from .parser181 import extract_parser181_leftovers
from .parser182 import extract_parser182_leftovers
from .parser183 import extract_parser183_leftovers
from .parser184 import extract_parser184_leftovers
from .parser185 import extract_parser185_leftovers
from .parser186 import extract_parser186_leftovers
from .parser187 import extract_parser187_leftovers
from .parser188 import extract_parser188_leftovers
from .parser189 import extract_parser189_leftovers
from .parser190 import extract_parser190_leftovers
from .parser191 import extract_parser191_leftovers
from .parser192 import extract_parser192_leftovers
from .parser193 import extract_parser193_leftovers
from .parser194 import extract_parser194_leftovers
from .parser195 import extract_parser195_leftovers
from .parser196 import extract_parser196_leftovers
from .parser197 import extract_parser197_leftovers
from .parser198 import extract_parser198_leftovers
from .parser199 import extract_parser199_leftovers
from .parser200 import extract_parser200_leftovers
from .parser201 import extract_parser201_leftovers
from .parser202 import extract_parser202_leftovers
from .parser203 import extract_parser203_leftovers
from .parser204 import extract_parser204_leftovers
from .parser205 import extract_parser205_leftovers
from .parser206 import extract_parser206_leftovers
from .parser207 import extract_parser207_leftovers
from .parser208 import extract_parser208_leftovers
from .parser209 import extract_parser209_leftovers
from .parser210 import extract_parser210_leftovers
from .parser211 import extract_parser211_leftovers
from .parser212 import extract_parser212_leftovers
from .parser213 import extract_parser213_leftovers
from .parser214 import extract_parser214_leftovers
from .parser215 import extract_parser215_leftovers
from .parser216 import extract_parser216_leftovers
from .parser217 import extract_parser217_leftovers
from .parser218 import extract_parser218_leftovers
from .parser219 import extract_parser219_leftovers
from .parser220 import extract_parser220_leftovers
from .parser221 import extract_parser221_leftovers
from .parser222 import extract_parser222_leftovers
from .parser223 import extract_parser223_leftovers
from .parser224 import extract_parser224_leftovers
from .parser225 import extract_parser225_leftovers
from .parser226 import extract_parser226_leftovers
from .parser227 import extract_parser227_leftovers
from .parser228 import extract_parser228_leftovers
from .parser229 import extract_parser229_leftovers
from .parser230 import extract_parser230_leftovers
from .parser231 import extract_parser231_leftovers
from .parser232 import extract_parser232_leftovers
from .parser233 import extract_parser233_leftovers
from .parser234 import extract_parser234_leftovers
from .parser235 import extract_parser235_leftovers
from .parser236 import extract_parser236_leftovers
from .parser237 import extract_parser237_leftovers
from .parser238 import extract_parser238_leftovers
from .parser239 import extract_parser239_leftovers
from .parser240 import extract_parser240_leftovers
from .parser241 import extract_parser241_leftovers
from .parser242 import extract_parser242_leftovers
from .parser243 import extract_parser243_leftovers
from .parser244 import extract_parser244_leftovers
from .parser245 import extract_parser245_leftovers
from .parser246 import extract_parser246_leftovers
from .parser247 import extract_parser247_leftovers
from .parser248 import extract_parser248_leftovers
from .parser249 import extract_parser249_leftovers
from .parser250 import extract_parser250_leftovers
from .parser251 import extract_parser251_leftovers
from .parser252 import extract_parser252_leftovers
from .parser253 import extract_parser253_leftovers
from .parser254 import extract_parser254_leftovers
from .parser255 import extract_parser255_leftovers
from .parser256 import extract_parser256_leftovers
from .parser257 import extract_parser257_leftovers
from .parser258 import extract_parser258_leftovers
from .parser259 import extract_parser259_leftovers
from .parser260 import extract_parser260_leftovers
from .parser261 import extract_parser261_leftovers
from .parser265 import extract_parser265_leftovers
from .parser264 import extract_parser264_leftovers
from .parser263 import extract_parser263_leftovers
from .parser262 import extract_parser262_leftovers
from .persons import extract_persons
from .text_extras import extract_text_extras
from .xml_map import map_hr_xml


def parse_publication_xml(path: Path, publication_id: str | None = None) -> ParseResult:
    path = Path(path)
    meta, xml_events, text = map_hr_xml(path, publication_id=publication_id)
    pub_id = meta.get("publication_id") or path.stem
    person_events, leftover = extract_persons(
        text,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    extra_events, leftover = extract_text_extras(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
        {e.event_type for e in xml_events + person_events},
    )
    parser265_events, leftover = extract_parser265_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser264_events, leftover = extract_parser264_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    if any(e.rule_id == "it.text.audit_opt_out_date_corrected.v1" for e in parser265_events):
        extra_events = [e for e in extra_events if e.rule_id != "it.text.audit_waiver.v1"]
    superseded264 = {
        "de.text.branch_uid_replaced_and_branch_added.v1": "de.text.branch_added.v1",
        "de.text.cooperative_share_nominal_changed.v1": "de.text.cooperative_share_certificate.v1",
    }
    obsolete264 = {superseded264[e.rule_id] for e in parser264_events if e.rule_id in superseded264}
    extra_events = [e for e in extra_events if e.rule_id not in obsolete264]
    parser263_events, leftover = extract_parser263_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    if any(e.rule_id == "de.text.branch_places_replaced_uid.v1" for e in parser263_events):
        extra_events = [e for e in extra_events if e.rule_id != "de.text.branch_added.v1"]
    if any(e.rule_id == "it.text.registration_maintained_deletion_clause_removed.v1" for e in parser263_events):
        extra_events = [e for e in extra_events if e.rule_id != "it.text.liquidation_ended.v1"]
    if any(e.rule_id == "fr.persons.partial_share_transfer_president_communications.v1" for e in parser263_events):
        extra_events = [e for e in extra_events if e.rule_id != "fr.text.communications.v1"]
    parser262_events, leftover = extract_parser262_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser261_events, leftover = extract_parser261_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    if any(e.signing for e in parser261_events):
        person_events = [e for e in person_events if e.rule_id != "fr.persons.group_signing.v1"]
    if any(e.rule_id == "de.text.branches_deleted_added_corrected.v1" for e in parser261_events):
        extra_events = [e for e in extra_events if e.rule_id != "de.text.branch_added.v1"]
    parser260_events, leftover = extract_parser260_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    if any(e.signing for e in parser260_events):
        person_events = [e for e in person_events if e.rule_id != "fr.persons.group_signing.v1"]
    if any(e.rule_id == "de.text.additional_address_abbreviated_place.v1" for e in parser260_events):
        extra_events = [e for e in extra_events if e.rule_id != "de.text.additional_address.v1"]
    if any(e.rule_id == "fr.text.authorized_capital_expired_clause_deleted.v1" for e in parser260_events):
        extra_events = [e for e in extra_events if e.rule_id != "fr.text.capital_clause_expired.v1"]
    parser259_events, leftover = extract_parser259_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    if any(e.signing for e in parser259_events):
        person_events = [e for e in person_events if e.rule_id != "fr.persons.group_signing.v1"]
    parser258_events, leftover = extract_parser258_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    if any(e.signing for e in parser258_events):
        person_events = [e for e in person_events if e.rule_id != "fr.persons.group_signing.v1"]
    if any(e.rule_id == "fr.persons.given_names_corrected_notice_typo.v1" for e in parser258_events):
        person_events = [e for e in person_events if e.rule_id != "fr.persons.first_name_changed_direct.v1"]
    if any(e.rule_id == "de.text.authorized_capital_expired.v1" for e in parser258_events):
        extra_events = [e for e in extra_events if e.rule_id != "de.text.authorized_capital.v1"]
    parser257_events, leftover = extract_parser257_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    if any(e.signing for e in parser257_events):
        person_events = [e for e in person_events if e.rule_id != "fr.persons.group_signing.v1"]
    parser256_events, leftover = extract_parser256_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"),
    )
    if any(e.signing for e in parser256_events):
        person_events = [e for e in person_events if e.rule_id != "fr.persons.group_signing.v1"]
    parser255_events, leftover = extract_parser255_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    if any(e.signing for e in parser255_events):
        person_events = [e for e in person_events if e.rule_id != "fr.persons.group_signing.v1"]
    # Parsers 179-260 contain complete families that broad historical search rules
    # would otherwise consume only in fragments.
    parser254_events, leftover = extract_parser254_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    # The historical extras rule reads the negated published reservation as added.
    # A complete parser254 correction supersedes that event for this family only.
    if any(
        e.rule_id == "de.text.foundation_deed_date_purpose_reservation_corrected.v1"
        for e in parser254_events
    ):
        extra_events = [
            e for e in extra_events if e.rule_id != "de.text.purpose_reservation.v1"
        ]
    parser253_events, leftover = extract_parser253_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser252_events, leftover = extract_parser252_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser251_events, leftover = extract_parser251_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser250_events, leftover = extract_parser250_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser249_events, leftover = extract_parser249_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser248_events, leftover = extract_parser248_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser247_events, leftover = extract_parser247_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser246_events, leftover = extract_parser246_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser245_events, leftover = extract_parser245_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser244_events, leftover = extract_parser244_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser243_events, leftover = extract_parser243_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser242_events, leftover = extract_parser242_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser241_events, leftover = extract_parser241_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser240_events, leftover = extract_parser240_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser239_events, leftover = extract_parser239_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser238_events, leftover = extract_parser238_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser237_events, leftover = extract_parser237_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser236_events, leftover = extract_parser236_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    # Parser 236 can deliberately return a person-change tail after consuming a
    # compound dissolution sentence; give parser 237 that bounded tail once.
    parser237_followup_events, leftover = extract_parser237_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser235_events, leftover = extract_parser235_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser234_events, leftover = extract_parser234_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser233_events, leftover = extract_parser233_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser232_events, leftover = extract_parser232_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser231_events, leftover = extract_parser231_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser230_events, leftover = extract_parser230_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser229_events, leftover = extract_parser229_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser228_events, leftover = extract_parser228_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser227_events, leftover = extract_parser227_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser226_events, leftover = extract_parser226_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser225_events, leftover = extract_parser225_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser224_events, leftover = extract_parser224_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser223_events, leftover = extract_parser223_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser222_events, leftover = extract_parser222_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser221_events, leftover = extract_parser221_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser220_events, leftover = extract_parser220_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser219_events, leftover = extract_parser219_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser218_events, leftover = extract_parser218_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser217_events, leftover = extract_parser217_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser216_events, leftover = extract_parser216_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser215_events, leftover = extract_parser215_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser214_events, leftover = extract_parser214_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser213_events, leftover = extract_parser213_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser212_events, leftover = extract_parser212_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser211_events, leftover = extract_parser211_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser210_events, leftover = extract_parser210_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser209_events, leftover = extract_parser209_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser208_events, leftover = extract_parser208_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser207_events, leftover = extract_parser207_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser206_events, leftover = extract_parser206_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser205_events, leftover = extract_parser205_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser204_events, leftover = extract_parser204_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser203_events, leftover = extract_parser203_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser202_events, leftover = extract_parser202_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser201_events, leftover = extract_parser201_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser200_events, leftover = extract_parser200_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser199_events, leftover = extract_parser199_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser198_events, leftover = extract_parser198_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser197_events, leftover = extract_parser197_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser196_events, leftover = extract_parser196_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser195_events, leftover = extract_parser195_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser194_events, leftover = extract_parser194_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser193_events, leftover = extract_parser193_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
        prior_events=xml_events + person_events + extra_events,
    )
    parser192_events, leftover = extract_parser192_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser191_events, leftover = extract_parser191_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser190_events, leftover = extract_parser190_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser189_events, leftover = extract_parser189_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser188_events, leftover = extract_parser188_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser187_events, leftover = extract_parser187_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser186_events, leftover = extract_parser186_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser185_events, leftover = extract_parser185_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser184_events, leftover = extract_parser184_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser183_events, leftover = extract_parser183_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser182_events, leftover = extract_parser182_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser181_events, leftover = extract_parser181_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser180_events, leftover = extract_parser180_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser179_events, leftover = extract_parser179_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    # Parser 164 contains a few complete correction notices whose suffixes are
    # otherwise consumed by older, deliberately broad fallback rules.
    parser164_events, leftover = extract_parser164_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser50_events, leftover = extract_parser50_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser51_events, leftover = extract_parser51_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser52_events, leftover = extract_parser52_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser53_events, leftover = extract_parser53_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser54_events, leftover = extract_parser54_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser55_events, leftover = extract_parser55_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser56_events, leftover = extract_parser56_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser57_events, leftover = extract_parser57_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser58_events, leftover = extract_parser58_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser59_events, leftover = extract_parser59_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser60_events, leftover = extract_parser60_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser61_events, leftover = extract_parser61_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser62_events, leftover = extract_parser62_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser63_events, leftover = extract_parser63_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser64_events, leftover = extract_parser64_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser65_events, leftover = extract_parser65_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser66_events, leftover = extract_parser66_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser67_events, leftover = extract_parser67_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser68_events, leftover = extract_parser68_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser69_events, leftover = extract_parser69_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser70_events, leftover = extract_parser70_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser71_events, leftover = extract_parser71_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser72_events, leftover = extract_parser72_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser73_events, leftover = extract_parser73_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser74_events, leftover = extract_parser74_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser75_events, leftover = extract_parser75_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser76_events, leftover = extract_parser76_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser77_events, leftover = extract_parser77_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser78_events, leftover = extract_parser78_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser79_events, leftover = extract_parser79_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser80_events, leftover = extract_parser80_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser81_events, leftover = extract_parser81_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser82_events, leftover = extract_parser82_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser83_events, leftover = extract_parser83_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser84_events, leftover = extract_parser84_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser85_events, leftover = extract_parser85_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser86_events, leftover = extract_parser86_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser87_events, leftover = extract_parser87_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser88_events, leftover = extract_parser88_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser89_events, leftover = extract_parser89_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser90_events, leftover = extract_parser90_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser91_events, leftover = extract_parser91_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser92_events, leftover = extract_parser92_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser93_events, leftover = extract_parser93_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser94_events, leftover = extract_parser94_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser95_events, leftover = extract_parser95_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser96_events, leftover = extract_parser96_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser97_events, leftover = extract_parser97_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser98_events, leftover = extract_parser98_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser99_events, leftover = extract_parser99_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser100_events, leftover = extract_parser100_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser101_events, leftover = extract_parser101_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser102_events, leftover = extract_parser102_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser103_events, leftover = extract_parser103_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser104_events, leftover = extract_parser104_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser105_events, leftover = extract_parser105_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser106_events, leftover = extract_parser106_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser107_events, leftover = extract_parser107_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser108_events, leftover = extract_parser108_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser109_events, leftover = extract_parser109_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser110_events, leftover = extract_parser110_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser111_events, leftover = extract_parser111_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser112_events, leftover = extract_parser112_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser113_events, leftover = extract_parser113_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser114_events, leftover = extract_parser114_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser115_events, leftover = extract_parser115_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser116_events, leftover = extract_parser116_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser117_events, leftover = extract_parser117_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser118_events, leftover = extract_parser118_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser119_events, leftover = extract_parser119_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser120_events, leftover = extract_parser120_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser121_events, leftover = extract_parser121_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser122_events, leftover = extract_parser122_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser123_events, leftover = extract_parser123_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser124_events, leftover = extract_parser124_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser125_events, leftover = extract_parser125_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser126_events, leftover = extract_parser126_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser127_events, leftover = extract_parser127_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser128_events, leftover = extract_parser128_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser129_events, leftover = extract_parser129_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser130_events, leftover = extract_parser130_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser131_events, leftover = extract_parser131_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser132_events, leftover = extract_parser132_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser133_events, leftover = extract_parser133_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser134_events, leftover = extract_parser134_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser135_events, leftover = extract_parser135_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser136_events, leftover = extract_parser136_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser137_events, leftover = extract_parser137_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser138_events, leftover = extract_parser138_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser139_events, leftover = extract_parser139_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser140_events, leftover = extract_parser140_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser141_events, leftover = extract_parser141_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser142_events, leftover = extract_parser142_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser143_events, leftover = extract_parser143_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser144_events, leftover = extract_parser144_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser145_events, leftover = extract_parser145_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser146_events, leftover = extract_parser146_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser147_events, leftover = extract_parser147_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser148_events, leftover = extract_parser148_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser149_events, leftover = extract_parser149_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser150_events, leftover = extract_parser150_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser151_events, leftover = extract_parser151_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser152_events, leftover = extract_parser152_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser153_events, leftover = extract_parser153_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser154_events, leftover = extract_parser154_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser155_events, leftover = extract_parser155_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser156_events, leftover = extract_parser156_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser157_events, leftover = extract_parser157_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser158_events, leftover = extract_parser158_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser159_events, leftover = extract_parser159_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser160_events, leftover = extract_parser160_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser161_events, leftover = extract_parser161_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser162_events, leftover = extract_parser162_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser163_events, leftover = extract_parser163_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser165_events, leftover = extract_parser165_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser166_events, leftover = extract_parser166_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser167_events, leftover = extract_parser167_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser168_events, leftover = extract_parser168_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser169_events, leftover = extract_parser169_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser170_events, leftover = extract_parser170_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser171_events, leftover = extract_parser171_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser172_events, leftover = extract_parser172_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser173_events, leftover = extract_parser173_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser174_events, leftover = extract_parser174_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser175_events, leftover = extract_parser175_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser176_events, leftover = extract_parser176_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser177_events, leftover = extract_parser177_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser178_events, leftover = extract_parser178_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    # Some broad legacy rules remove an adjacent clause before a bounded
    # parser-249/250 family becomes a full match.
    parser250_followup_events, leftover = extract_parser250_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser249_followup_events, leftover = extract_parser249_leftovers(
        leftover,
        meta.get("language"),
        pub_id,
        meta.get("published_at") or "",
        meta.get("org_uid"),
        meta.get("plz"),
        meta.get("canton"),
    )
    parser261_followup_events, leftover = extract_parser261_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    if any(e.signing for e in parser261_followup_events):
        person_events = [e for e in person_events if e.rule_id != "fr.persons.group_signing.v1"]
    events = (
        xml_events
        + person_events
        + extra_events
        + parser50_events
        + parser51_events
        + parser52_events
        + parser53_events
        + parser54_events
        + parser55_events
        + parser56_events
        + parser57_events
        + parser58_events
        + parser59_events
        + parser60_events
        + parser61_events
        + parser62_events
        + parser63_events
        + parser64_events
        + parser65_events
        + parser66_events
        + parser67_events
        + parser68_events
        + parser69_events
        + parser70_events
        + parser71_events
        + parser72_events
        + parser73_events
        + parser74_events
        + parser75_events
        + parser76_events
        + parser77_events
        + parser78_events
        + parser79_events
        + parser80_events
        + parser81_events
        + parser82_events
        + parser83_events
        + parser84_events
        + parser85_events
        + parser86_events
        + parser87_events
        + parser88_events
        + parser89_events
        + parser90_events
        + parser91_events
        + parser92_events
        + parser93_events
        + parser94_events
        + parser95_events
        + parser96_events
        + parser97_events
        + parser98_events
        + parser99_events
        + parser100_events
        + parser101_events
        + parser102_events
        + parser103_events
        + parser104_events
        + parser105_events
        + parser106_events
        + parser107_events
        + parser108_events
        + parser109_events
        + parser110_events
        + parser111_events
        + parser112_events
        + parser113_events
        + parser114_events
        + parser115_events
        + parser116_events
        + parser117_events
        + parser118_events
        + parser119_events
        + parser120_events
        + parser121_events
        + parser122_events
        + parser123_events
        + parser124_events
        + parser125_events
        + parser126_events
        + parser127_events
        + parser128_events
        + parser129_events
        + parser130_events
        + parser131_events
        + parser132_events
        + parser133_events
        + parser134_events
        + parser135_events
        + parser136_events
        + parser137_events
        + parser138_events
        + parser139_events
        + parser140_events
        + parser141_events
        + parser142_events
        + parser143_events
        + parser144_events
        + parser145_events
        + parser146_events
        + parser147_events
        + parser148_events
        + parser149_events
        + parser150_events
        + parser151_events
        + parser152_events
        + parser153_events
        + parser154_events
        + parser155_events
        + parser156_events
        + parser157_events
        + parser158_events
        + parser159_events
        + parser160_events
        + parser161_events
        + parser162_events
        + parser163_events
        + parser164_events
        + parser165_events
        + parser166_events
        + parser167_events
        + parser168_events
        + parser169_events
        + parser170_events
        + parser171_events
        + parser172_events
        + parser173_events
        + parser174_events
        + parser175_events
        + parser176_events
        + parser177_events
        + parser178_events
        + parser179_events
        + parser180_events
        + parser181_events
        + parser182_events
        + parser183_events
        + parser184_events
        + parser185_events
        + parser186_events
        + parser187_events
        + parser188_events
        + parser189_events
        + parser190_events
        + parser191_events
        + parser192_events
        + parser193_events
        + parser194_events
        + parser195_events
        + parser196_events
        + parser197_events
        + parser198_events
        + parser199_events
        + parser200_events
        + parser201_events
        + parser202_events
        + parser203_events
        + parser204_events
        + parser205_events
        + parser206_events
        + parser207_events
        + parser208_events
        + parser209_events
        + parser210_events
        + parser211_events
        + parser212_events
        + parser213_events
        + parser214_events
        + parser215_events
        + parser216_events
        + parser217_events
        + parser218_events
        + parser219_events
        + parser220_events
        + parser221_events
        + parser222_events
        + parser223_events
        + parser224_events
        + parser225_events
        + parser226_events
        + parser227_events
        + parser228_events
        + parser229_events
        + parser230_events
        + parser231_events
        + parser232_events
        + parser233_events
        + parser234_events
        + parser235_events
        + parser236_events
        + parser237_events
        + parser237_followup_events
        + parser238_events
        + parser239_events
        + parser240_events
        + parser241_events
        + parser242_events
        + parser243_events
        + parser244_events
        + parser245_events
        + parser246_events
        + parser247_events
        + parser248_events
        + parser249_events
        + parser249_followup_events
        + parser250_events
        + parser250_followup_events
        + parser251_events
        + parser252_events
        + parser265_events
        + parser264_events
        + parser263_events
        + parser262_events
        + parser261_events
        + parser261_followup_events
        + parser260_events
        + parser259_events
        + parser258_events
        + parser257_events
        + parser256_events
        + parser255_events
        + parser254_events
        + parser253_events
    )
    if any(e.signing for e in parser265_events + parser264_events + parser263_events + parser262_events + parser261_events + parser261_followup_events):
        events = [e for e in events if e.rule_id != "fr.persons.group_signing.v1"]
    others = bool(meta.get("others"))
    leftover = leftover.strip(" .")
    if not events and others and not leftover:
        events.append(
            Event(
                publication_id=pub_id,
                published_at=meta.get("published_at") or "",
                event_type="organization_changed",
                rule_id="xml.hr02.other_unspecified.v1",
                org_uid=meta.get("org_uid"),
                plz=meta.get("plz"),
                canton=meta.get("canton"),
                payload={
                    "kind": "other_mutation",
                    "detail": "not_specified_in_publication_text",
                    "company_name": meta.get("company_name"),
                },
            )
        )
    if not events:
        status = "PARTIALLY_PARSED"
    elif leftover and others and not person_events:
        status = "PARTIALLY_PARSED"
    else:
        status = "FULLY_PARSED"
    return ParseResult(
        publication_id=pub_id,
        published_at=meta.get("published_at") or "",
        language=meta.get("language"),
        sub_rubric=meta.get("sub_rubric"),
        org_uid=meta.get("org_uid"),
        canton=meta.get("canton"),
        plz=meta.get("plz"),
        events=events,
        leftover_text=leftover,
        status=status,
    )
