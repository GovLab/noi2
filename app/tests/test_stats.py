from .test_models import DbTestCase

from app import stats

class StatsTests(DbTestCase):
    def test_smoke(self):
        stats.generate()
