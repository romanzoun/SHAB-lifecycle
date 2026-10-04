from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ImportDay:
    publication_date: str
    status: str = "pending"
    result_count: int | None = None
    discovered_count: int = 0
    scraped_count: int = 0
    attempt_count: int = 0
    last_error: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class PublicationQueueItem:
    publication_id: str
    publication_date: str
    publication_number: str | None = None
    title: str | None = None
    list_info: str | None = None
    detail_url: str | None = None
    status: str = "pending"
    attempt_count: int = 0
    http_status: int | None = None
    last_error: str | None = None
    discovered_at: str | None = None
    scraped_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class ShabPublicationRaw:
    publication_id: str
    publication_number: str | None = None
    publication_date: str | None = None
    status: str | None = None
    category: str | None = None
    subcategory: str | None = None
    language: str | None = None
    canton: str | None = None
    title: str | None = None
    company_name_raw: str | None = None
    uid: str | None = None
    company_block_text: str | None = None
    body_text: str | None = None
    journal_number: str | None = None
    journal_date: str | None = None
    previous_sogc_number: str | None = None
    previous_sogc_date: str | None = None
    previous_publication_number: str | None = None
    contact_point: str | None = None
    detail_url: str | None = None
    xml_url: str | None = None
    pdf_url: str | None = None
    zefix_url: str | None = None
    raw_metadata_json: str | None = None
    raw_links_json: str | None = None
    raw_content_json: str | None = None
    raw_content_html: str | None = None
    raw_page_html_path: str | None = None
    raw_xml_path: str | None = None
    content_hash: str | None = None
    scraped_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
