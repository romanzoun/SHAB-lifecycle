import pytest

from shab_harvester.discovery import (
    DiscoveryError,
    collect_day_from_api,
    merge_result_items,
    publication_from_api_item,
    publications_api_url,
)


def test_merge_result_items_keeps_first_sighting_and_skips_blanks():
    seen = {}
    added = merge_result_items(
        seen,
        [
            {"publication_id": "a", "title": "first"},
            {"publication_id": None, "title": "skip"},
            {"publication_id": "b", "title": "bee"},
        ],
    )
    assert added == 2
    added_again = merge_result_items(
        seen,
        [
            {"publication_id": "a", "title": "later"},
            {"publication_id": "c", "title": "cee"},
        ],
    )
    assert added_again == 1
    assert seen["a"]["title"] == "first"
    assert set(seen) == {"a", "b", "c"}


def _api_item(publication_id: str, number: str, language: str = "fr") -> dict:
    return {
        "meta": {
            "id": publication_id,
            "publicationNumber": number,
            "publicationDate": "2026-09-22T00:00:00.000Z",
            "language": language,
            "rubric": "HR",
            "subRubric": "HR02",
            "title": {
                "de": f"DE {number}",
                "fr": f"FR {number}",
            },
        }
    }


def test_publication_from_api_item_uses_publication_language_title():
    mapped = publication_from_api_item(_api_item("abc", "HR02-100"), "2026-09-22")
    assert mapped is not None
    assert mapped["publication_id"] == "abc"
    assert mapped["publication_number"] == "HR02-100"
    assert mapped["publication_date"] == "2026-09-22"
    assert mapped["title"] == "FR HR02-100"
    assert mapped["list_info"] == "22.09.2026 - HR02-100 - HR02"
    assert mapped["detail_url"].endswith("/abc")


def test_collect_day_from_api_pages_until_total(monkeypatch):
    pages = {
        0: {"total": 3, "content": [_api_item("a", "HR02-1"), _api_item("b", "HR02-2")]},
        1: {"total": 3, "content": [_api_item("a", "HR02-1"), _api_item("c", "HR02-3")]},
    }

    def fake_fetch(publication_date: str, page_index: int) -> dict:
        assert publication_date == "2026-09-22"
        return pages[page_index]

    monkeypatch.setattr("shab_harvester.discovery.fetch_publications_page", fake_fetch)
    monkeypatch.setattr("shab_harvester.discovery.time.sleep", lambda _seconds: None)
    total, items = collect_day_from_api("2026-09-22")
    assert total == 3
    assert {item["publication_id"] for item in items} == {"a", "b", "c"}


def test_collect_day_from_api_rejects_unfiltered_total(monkeypatch):
    monkeypatch.setattr(
        "shab_harvester.discovery.fetch_publications_page",
        lambda _date, _page: {"total": 2_000_000, "content": []},
    )
    with pytest.raises(DiscoveryError):
        collect_day_from_api("2026-09-22")


def test_publications_api_url_sorts_by_publication_number():
    url = publications_api_url("2026-09-22", 3)
    assert "pageRequest.page=3" in url
    assert "pageRequest.sortOrders=column%3APUBLICATION_NUMBER%7Cdirection%3AASC" in url
    assert "publicationDate.start=2026-09-22" in url
