import sys
from pathlib import Path
import unittest

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import create_app
from services.guidance_service import analyze_name_discrepancy

class TestServices(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_health_check(self):
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data.get("status"), "healthy")

    def test_get_all_services(self):
        response = self.client.get('/api/services')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertGreater(data.get("count", 0), 5)

    def test_filter_services_by_category(self):
        response = self.client.get('/api/services?category=aadhaar')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(all(s['category'] == 'aadhaar' for s in data.get("data", [])))

    def test_name_mismatch_analysis(self):
        # Case 1: Initial vs expanded
        res = analyze_name_discrepancy(
            name_10th="Kottayam Ramesh",
            name_aadhaar="K. Ramesh",
            name_pan="Kottayam Ramesh"
        )
        self.assertEqual(res["severity"], "High")
        self.assertTrue(any("initial" in i.lower() for i in res["issues"]))

        # Case 2: Exact match
        res_match = analyze_name_discrepancy(
            name_10th="Rahul Kumar Sharma",
            name_aadhaar="Rahul Kumar Sharma",
            name_pan="Rahul Kumar Sharma"
        )
        self.assertTrue(res_match["is_perfect_match"])
        self.assertEqual(res_match["severity"], "None")

    def test_faqs_search(self):
        response = self.client.get('/api/faqs?category=passport')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertGreater(data.get("count", 0), 0)

if __name__ == '__main__':
    unittest.main()
