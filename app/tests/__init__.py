from .test_models import (wait_until_db_is_ready,
                          db_test_request_context,
                          create_tables,
                          drop_tables)

def setup():
    wait_until_db_is_ready()
    with db_test_request_context():
        create_tables()

def teardown():
    with db_test_request_context():
        drop_tables()
