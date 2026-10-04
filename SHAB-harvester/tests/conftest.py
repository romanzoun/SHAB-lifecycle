import pytest

from shab_harvester import db


@pytest.fixture
def conn(tmp_path):
    db_path = tmp_path / "test.sqlite"
    db.init_db(db_path)
    connection = db.get_connection(db_path)
    yield connection
    connection.close()
