import sys
from pathlib import Path
import unittest

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import create_app
from services.guidance_service import generate_checklist

class TestChecklist(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_generate_passport_tatkaal_checklist(self):
        result = generate_checklist(
            target_service="passport_fresh",
            age_group="adult",
            has_10th=True,
            scheme="tatkaal",
            is_employed_govt=False
        )
        self.assertIn("3,500", result["estimated_fee"])
        self.assertTrue(any("Tatkaal Requirement" in d["type"] for d in result["mandatory_documents"]))
        self.assertTrue(any("Non-ECR" in d["type"] for d in result["mandatory_documents"]))

    def test_generate_instant_epan_checklist(self):
        result = generate_checklist(target_service="pan_instant")
        self.assertEqual(result["estimated_fee"], "Free")
        self.assertTrue(any("Aadhaar Card" in d["name"] for d in result["mandatory_documents"]))

    def test_checklist_api_endpoint(self):
        payload = {
            "target_service": "passport_fresh",
            "age_group": "adult",
            "has_10th": True,
            "scheme": "normal"
        }
        response = self.client.post('/api/checklist/generate', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("mandatory_documents", data["data"])

    def test_get_acceptable_documents(self):
        response = self.client.get('/api/checklist/documents?proof_type=PoI')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertGreater(data.get("count", 0), 0)

if __name__ == '__main__':
    unittest.main()
