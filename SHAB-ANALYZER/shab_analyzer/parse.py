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
from .parser271 import extract_parser271_leftovers
from .parser290 import extract_parser290_leftovers
from .parser291 import extract_parser291_leftovers
from .parser292 import extract_parser292_leftovers
from .parser293 import extract_parser293_leftovers
from .parser298 import extract_parser298_leftovers
from .parser311 import extract_parser311_leftovers
from .parser321 import extract_parser321_leftovers
from .parser322 import extract_parser322_leftovers
from .parser323 import extract_parser323_leftovers
from .parser324 import extract_parser324_leftovers
from .parser325 import extract_parser325_leftovers
from .parser326 import extract_parser326_leftovers
from .parser327 import extract_parser327_leftovers
from .parser328 import extract_parser328_leftovers
from .parser329 import extract_parser329_leftovers
from .parser330 import extract_parser330_leftovers
from .parser331 import extract_parser331_leftovers
from .parser332 import extract_parser332_leftovers
from .parser333 import extract_parser333_leftovers
from .parser334 import extract_parser334_leftovers
from .parser335 import extract_parser335_leftovers
from .parser336 import extract_parser336_leftovers
from .parser337 import extract_parser337_leftovers
from .parser338 import extract_parser338_leftovers
from .parser339 import extract_parser339_leftovers
from .parser340 import extract_parser340_leftovers
from .parser341 import extract_parser341_leftovers
from .parser342 import extract_parser342_leftovers
from .parser343 import extract_parser343_leftovers
from .parser344 import extract_parser344_leftovers
from .parser345 import extract_parser345_leftovers
from .parser346 import extract_parser346_leftovers
from .parser347 import extract_parser347_leftovers
from .parser348 import extract_parser348_leftovers
from .parser349 import extract_parser349_leftovers
from .parser350 import extract_parser350_leftovers
from .parser351 import extract_parser351_leftovers
from .parser352 import extract_parser352_leftovers
from .parser353 import extract_parser353_leftovers
from .parser354 import extract_parser354_leftovers
from .parser355 import extract_parser355_leftovers
from .parser356 import extract_parser356_leftovers
from .parser357 import extract_parser357_leftovers
from .parser358 import extract_parser358_leftovers
from .parser359 import extract_parser359_leftovers
from .parser360 import extract_parser360_leftovers
from .parser361 import extract_parser361_leftovers
from .parser362 import extract_parser362_leftovers
from .parser363 import extract_parser363_leftovers
from .parser364 import extract_parser364_leftovers
from .parser365 import extract_parser365_leftovers
from .parser366 import extract_parser366_leftovers
from .parser367 import extract_parser367_leftovers
from .parser368 import extract_parser368_leftovers
from .parser369 import extract_parser369_leftovers
from .parser370 import extract_parser370_leftovers
from .parser371 import extract_parser371_leftovers
from .parser372 import extract_parser372_leftovers
from .parser373 import extract_parser373_leftovers
from .parser374 import extract_parser374_leftovers
from .parser375 import extract_parser375_leftovers
from .parser376 import extract_parser376_leftovers
from .parser377 import extract_parser377_leftovers
from .parser378 import extract_parser378_leftovers
from .parser379 import extract_parser379_leftovers
from .parser380 import extract_parser380_leftovers
from .parser381 import extract_parser381_leftovers
from .parser382 import extract_parser382_leftovers
from .parser383 import extract_parser383_leftovers
from .parser384 import extract_parser384_leftovers
from .parser385 import extract_parser385_leftovers
from .parser386 import extract_parser386_leftovers
from .parser387 import extract_parser387_leftovers
from .parser388 import extract_parser388_leftovers
from .parser389 import extract_parser389_leftovers
from .parser390 import extract_parser390_leftovers
from .parser391 import extract_parser391_leftovers
from .parser392 import extract_parser392_leftovers
from .parser393 import extract_parser393_leftovers
from .parser394 import extract_parser394_leftovers
from .parser395 import extract_parser395_leftovers
from .parser396 import extract_parser396_leftovers
from .parser397 import extract_parser397_leftovers
from .parser398 import extract_parser398_leftovers
from .parser399 import extract_parser399_leftovers
from .parser400 import extract_parser400_leftovers
from .parser401 import extract_parser401_leftovers
from .parser402 import extract_parser402_leftovers
from .parser403 import extract_parser403_leftovers
from .parser404 import extract_parser404_leftovers
from .parser405 import extract_parser405_leftovers
from .parser406 import extract_parser406_leftovers
from .parser407 import extract_parser407_leftovers
from .parser408 import extract_parser408_leftovers
from .parser409 import extract_parser409_leftovers
from .parser410 import extract_parser410_leftovers
from .parser411 import extract_parser411_leftovers
from .parser412 import extract_parser412_leftovers
from .parser413 import extract_parser413_leftovers
from .parser414 import extract_parser414_leftovers
from .parser415 import extract_parser415_leftovers
from .parser416 import extract_parser416_leftovers
from .parser417 import extract_parser417_leftovers
from .parser418 import extract_parser418_leftovers
from .parser419 import extract_parser419_leftovers
from .parser320 import extract_parser320_leftovers
from .parser319 import extract_parser319_leftovers
from .parser318 import extract_parser318_leftovers
from .parser317 import extract_parser317_leftovers
from .parser316 import extract_parser316_leftovers
from .parser315 import extract_parser315_leftovers
from .parser314 import extract_parser314_leftovers
from .parser313 import extract_parser313_leftovers
from .parser312 import extract_parser312_leftovers
from .parser310 import extract_parser310_leftovers
from .parser309 import extract_parser309_leftovers
from .parser308 import extract_parser308_leftovers
from .parser307 import extract_parser307_leftovers
from .parser306 import extract_parser306_leftovers
from .parser305 import extract_parser305_leftovers
from .parser304 import extract_parser304_leftovers
from .parser303 import extract_parser303_leftovers
from .parser302 import extract_parser302_leftovers
from .parser301 import extract_parser301_leftovers
from .parser300 import extract_parser300_leftovers
from .parser299 import extract_parser299_leftovers
from .parser297 import extract_parser297_leftovers
from .parser296 import extract_parser296_leftovers
from .parser295 import extract_parser295_leftovers
from .parser294 import extract_parser294_leftovers
from .parser289 import extract_parser289_leftovers
from .parser288 import extract_parser288_leftovers
from .parser287 import extract_parser287_leftovers
from .parser286 import extract_parser286_leftovers
from .parser285 import extract_parser285_leftovers
from .parser284 import extract_parser284_leftovers
from .parser283 import extract_parser283_leftovers
from .parser282 import extract_parser282_leftovers
from .parser281 import extract_parser281_leftovers
from .parser280 import extract_parser280_leftovers
from .parser279 import extract_parser279_leftovers
from .parser278 import extract_parser278_leftovers
from .parser277 import extract_parser277_leftovers
from .parser276 import extract_parser276_leftovers
from .parser275 import extract_parser275_leftovers
from .parser274 import extract_parser274_leftovers
from .parser273 import extract_parser273_leftovers
from .parser272 import extract_parser272_leftovers
from .parser270 import extract_parser270_leftovers
from .parser269 import extract_parser269_leftovers
from .parser268 import extract_parser268_leftovers
from .parser267 import extract_parser267_leftovers
from .parser266 import extract_parser266_leftovers
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
    parser320_events, leftover = extract_parser320_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser319_events, leftover = extract_parser319_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser318_events, leftover = extract_parser318_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser317_events, leftover = extract_parser317_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser316_events, leftover = extract_parser316_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser315_events, leftover = extract_parser315_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser314_events, leftover = extract_parser314_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser313_events, leftover = extract_parser313_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser312_events, leftover = extract_parser312_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser311_events, leftover = extract_parser311_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser310_events, leftover = extract_parser310_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser309_events, leftover = extract_parser309_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    if any(e.rule_id == "it.text.auditor_erroneous_entry_corrected.v1" for e in parser309_events):
        extra_events = [e for e in extra_events if e.rule_id != "it.text.audit_waiver.v1"]
    parser308_events, leftover = extract_parser308_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser307_events, leftover = extract_parser307_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser306_events, leftover = extract_parser306_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser305_events, leftover = extract_parser305_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser304_events, leftover = extract_parser304_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser303_events, leftover = extract_parser303_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser302_events, leftover = extract_parser302_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser301_events, leftover = extract_parser301_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser300_events, leftover = extract_parser300_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser299_events, leftover = extract_parser299_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser298_events, leftover = extract_parser298_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser297_events, leftover = extract_parser297_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser296_events, leftover = extract_parser296_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser295_events, leftover = extract_parser295_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser294_events, leftover = extract_parser294_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser293_events, leftover = extract_parser293_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser292_events, leftover = extract_parser292_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser291_events, leftover = extract_parser291_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser290_events, leftover = extract_parser290_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser289_events, leftover = extract_parser289_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser288_events, leftover = extract_parser288_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser287_events, leftover = extract_parser287_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser286_events, leftover = extract_parser286_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser285_events, leftover = extract_parser285_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser284_events, leftover = extract_parser284_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser283_events, leftover = extract_parser283_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser282_events, leftover = extract_parser282_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser281_events, leftover = extract_parser281_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser280_events, leftover = extract_parser280_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser279_events, leftover = extract_parser279_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser278_events, leftover = extract_parser278_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser277_events, leftover = extract_parser277_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser276_events, leftover = extract_parser276_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser275_events, leftover = extract_parser275_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser274_events, leftover = extract_parser274_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser273_events, leftover = extract_parser273_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser272_events, leftover = extract_parser272_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser271_events, leftover = extract_parser271_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser270_events, leftover = extract_parser270_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    if any(e.rule_id == "fr.persons.liquidator_shared_relocation.v1" for e in parser270_events):
        person_events = [e for e in person_events if not (
            e.rule_id == "fr.persons.liquidator_appointed.v2" and e.payload.get("name") == "lequel"
        )]
    if any(e.rule_id == "de.text.void_statutes_audit_restored.v1" for e in parser270_events):
        extra_events = [e for e in extra_events if e.rule_id != "de.text.statutes.v1"]
    parser269_events, leftover = extract_parser269_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    if any(e.rule_id == "fr.text.shareholder_communications_corrected.v1" for e in parser269_events):
        extra_events = [e for e in extra_events if e.rule_id != "fr.text.communications.v1"]
    parser268_events, leftover = extract_parser268_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser267_events, leftover = extract_parser267_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser266_events, leftover = extract_parser266_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
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
    parser321_events, leftover = extract_parser321_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser322_events, leftover = extract_parser322_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"),
    )
    parser323_events, leftover = extract_parser323_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser324_events, leftover = extract_parser324_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser325_events, leftover = extract_parser325_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser326_events, leftover = extract_parser326_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser327_events, leftover = extract_parser327_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser328_events, leftover = extract_parser328_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser329_events, leftover = extract_parser329_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser330_events, leftover = extract_parser330_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser331_events, leftover = extract_parser331_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser332_events, leftover = extract_parser332_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser333_events, leftover = extract_parser333_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser334_events, leftover = extract_parser334_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser335_events, leftover = extract_parser335_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser336_events, leftover = extract_parser336_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser337_events, leftover = extract_parser337_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser338_events, leftover = extract_parser338_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser339_events, leftover = extract_parser339_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser340_events, leftover = extract_parser340_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser341_events, leftover = extract_parser341_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser342_events, leftover = extract_parser342_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser343_events, leftover = extract_parser343_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser344_events, leftover = extract_parser344_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser345_events, leftover = extract_parser345_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser346_events, leftover = extract_parser346_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser347_events, leftover = extract_parser347_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser348_events, leftover = extract_parser348_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser349_events, leftover = extract_parser349_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser350_events, leftover = extract_parser350_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser351_events, leftover = extract_parser351_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser352_events, leftover = extract_parser352_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser353_events, leftover = extract_parser353_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser354_events, leftover = extract_parser354_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser355_events, leftover = extract_parser355_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser356_events, leftover = extract_parser356_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser357_events, leftover = extract_parser357_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser358_events, leftover = extract_parser358_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser359_events, leftover = extract_parser359_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser360_events, leftover = extract_parser360_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser361_events, leftover = extract_parser361_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser362_events, leftover = extract_parser362_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser363_events, leftover = extract_parser363_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser364_events, leftover = extract_parser364_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser365_events, leftover = extract_parser365_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser366_events, leftover = extract_parser366_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser367_events, leftover = extract_parser367_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser368_events, leftover = extract_parser368_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser369_events, leftover = extract_parser369_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser370_events, leftover = extract_parser370_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser371_events, leftover = extract_parser371_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser372_events, leftover = extract_parser372_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser373_events, leftover = extract_parser373_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser374_events, leftover = extract_parser374_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser375_events, leftover = extract_parser375_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser376_events, leftover = extract_parser376_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser377_events, leftover = extract_parser377_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser378_events, leftover = extract_parser378_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser379_events, leftover = extract_parser379_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser380_events, leftover = extract_parser380_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser381_events, leftover = extract_parser381_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser382_events, leftover = extract_parser382_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser383_events, leftover = extract_parser383_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser384_events, leftover = extract_parser384_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser385_events, leftover = extract_parser385_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser386_events, leftover = extract_parser386_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser387_events, leftover = extract_parser387_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser388_events, leftover = extract_parser388_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser389_events, leftover = extract_parser389_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser390_events, leftover = extract_parser390_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser391_events, leftover = extract_parser391_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser392_events, leftover = extract_parser392_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser393_events, leftover = extract_parser393_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser394_events, leftover = extract_parser394_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser395_events, leftover = extract_parser395_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser396_events, leftover = extract_parser396_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser397_events, leftover = extract_parser397_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser398_events, leftover = extract_parser398_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser399_events, leftover = extract_parser399_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser400_events, leftover = extract_parser400_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser401_events, leftover = extract_parser401_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser402_events, leftover = extract_parser402_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser403_events, leftover = extract_parser403_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser404_events, leftover = extract_parser404_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser405_events, leftover = extract_parser405_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser406_events, leftover = extract_parser406_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser407_events, leftover = extract_parser407_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser408_events, leftover = extract_parser408_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser409_events, leftover = extract_parser409_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser410_events, leftover = extract_parser410_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser411_events, leftover = extract_parser411_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser412_events, leftover = extract_parser412_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser413_events, leftover = extract_parser413_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser414_events, leftover = extract_parser414_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser415_events, leftover = extract_parser415_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser416_events, leftover = extract_parser416_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser417_events, leftover = extract_parser417_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser418_events, leftover = extract_parser418_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
    parser419_events, leftover = extract_parser419_leftovers(
        leftover, meta.get("language"), pub_id, meta.get("published_at") or "",
        meta.get("org_uid"), meta.get("plz"), meta.get("canton"), source_text=text,
    )
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
        + parser321_events
        + parser322_events
        + parser323_events
        + parser324_events
        + parser325_events
        + parser326_events
        + parser327_events
        + parser328_events
        + parser329_events
        + parser330_events
        + parser331_events
        + parser332_events
        + parser333_events
        + parser334_events
        + parser335_events
        + parser336_events
        + parser337_events
        + parser338_events
        + parser339_events
        + parser340_events
        + parser341_events
        + parser342_events
        + parser343_events
        + parser344_events
        + parser345_events
        + parser346_events
        + parser347_events
        + parser348_events
        + parser349_events
        + parser350_events
        + parser351_events
        + parser352_events
        + parser353_events
        + parser354_events
        + parser355_events
        + parser356_events
        + parser357_events
        + parser358_events
        + parser359_events
        + parser360_events
        + parser361_events
        + parser362_events
        + parser363_events
        + parser364_events
        + parser365_events
        + parser366_events
        + parser367_events
        + parser368_events
        + parser369_events
        + parser370_events
        + parser371_events
        + parser372_events
        + parser373_events
        + parser374_events
        + parser375_events
        + parser376_events
        + parser377_events
        + parser378_events
        + parser379_events
        + parser380_events
        + parser381_events
        + parser382_events
        + parser383_events
        + parser384_events
        + parser385_events
        + parser386_events
        + parser387_events
        + parser388_events
        + parser389_events
        + parser390_events
        + parser391_events
        + parser392_events
        + parser393_events
        + parser394_events
        + parser395_events
        + parser396_events
        + parser397_events
        + parser398_events
        + parser399_events
        + parser400_events
        + parser401_events
        + parser402_events
        + parser403_events
        + parser404_events
        + parser405_events
        + parser406_events
        + parser407_events
        + parser408_events
        + parser409_events
        + parser410_events
        + parser411_events
        + parser412_events
        + parser413_events
        + parser414_events
        + parser415_events
        + parser416_events
        + parser417_events
        + parser418_events
        + parser419_events
        + parser320_events
        + parser319_events
        + parser318_events
        + parser317_events
        + parser316_events
        + parser315_events
        + parser314_events
        + parser313_events
        + parser312_events
        + parser311_events
        + parser310_events
        + parser309_events
        + parser308_events
        + parser307_events
        + parser306_events
        + parser305_events
        + parser304_events
        + parser303_events
        + parser302_events
        + parser301_events
        + parser300_events
        + parser299_events
        + parser298_events
        + parser297_events
        + parser296_events
        + parser295_events
        + parser294_events
        + parser293_events
        + parser292_events
        + parser291_events
        + parser290_events
        + parser289_events
        + parser288_events
        + parser287_events
        + parser286_events
        + parser285_events
        + parser284_events
        + parser283_events
        + parser282_events
        + parser281_events
        + parser280_events
        + parser279_events
        + parser278_events
        + parser277_events
        + parser276_events
        + parser275_events
        + parser274_events
        + parser273_events
        + parser272_events
        + parser271_events
        + parser270_events
        + parser269_events
        + parser268_events
        + parser267_events
        + parser266_events
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
    if any(e.signing for e in parser320_events + parser319_events + parser318_events + parser317_events + parser316_events + parser315_events + parser314_events + parser313_events + parser312_events + parser311_events + parser310_events + parser309_events + parser308_events + parser307_events + parser306_events + parser305_events + parser304_events + parser303_events + parser302_events + parser301_events + parser300_events + parser299_events + parser298_events + parser297_events + parser296_events + parser295_events + parser294_events + parser293_events + parser292_events + parser291_events + parser290_events + parser289_events + parser288_events + parser287_events + parser286_events + parser285_events + parser284_events + parser283_events + parser282_events + parser281_events + parser280_events + parser279_events + parser278_events + parser277_events + parser276_events + parser275_events + parser274_events + parser273_events + parser272_events + parser271_events + parser270_events + parser269_events + parser268_events + parser267_events + parser266_events + parser265_events + parser264_events + parser263_events + parser262_events + parser261_events + parser261_followup_events):
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
