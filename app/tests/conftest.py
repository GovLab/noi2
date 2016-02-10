import pytest

from .test_models import (wait_until_db_is_ready,
                          db_test_request_context,
                          create_tables,
                          drop_tables)

@pytest.fixture(scope="session", autouse=True)
def create_db_tables(request):
    wait_until_db_is_ready()
    with db_test_request_context():
        create_tables()

    def teardown():
        with db_test_request_context():
            drop_tables()

    request.addfinalizer(teardown)
