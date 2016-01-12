def setup():
    from .test_models import wait_until_db_is_ready
    wait_until_db_is_ready()
