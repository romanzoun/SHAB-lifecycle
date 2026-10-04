from shab_harvester import utils


def test_to_ddmmyyyy():
    assert utils.to_ddmmyyyy("2018-09-03") == "03.09.2018"


def test_daterange_inclusive():
    days = list(utils.daterange("2018-09-02", "2018-09-05"))
    assert days == ["2018-09-02", "2018-09-03", "2018-09-04", "2018-09-05"]


def test_daterange_single_day():
    assert list(utils.daterange("2018-09-02", "2018-09-02")) == ["2018-09-02"]


def test_daterange_rejects_inverted_range():
    try:
        list(utils.daterange("2018-09-05", "2018-09-02"))
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for from > to")


def test_year_month():
    assert utils.year_month("2018-09-03") == ("2018", "09")


def test_content_hash_is_deterministic():
    a = utils.content_hash("foo", "bar")
    b = utils.content_hash("foo", "bar")
    c = utils.content_hash("foo", "baz")
    assert a == b
    assert a != c


def test_extract_publication_number():
    assert utils.extract_publication_number("03.09.2018 - HR01-0004447088 - SOGC") == "HR01-0004447088"
    assert utils.extract_publication_number(None) is None
    assert utils.extract_publication_number("no number here") is None


def test_extract_date_from_list_info():
    assert utils.extract_date_from_list_info("03.09.2018 - HR01-0004447088") == "2018-09-03"
    assert utils.extract_date_from_list_info(None) is None


def test_extract_uid():
    assert utils.extract_uid("some text CHE-108.472.828 more text") == "CHE-108.472.828"
    assert utils.extract_uid(None, "href without uid", "CHE-999.999.999") == "CHE-999.999.999"
    assert utils.extract_uid("no uid here") is None
