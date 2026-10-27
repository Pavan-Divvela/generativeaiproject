import sys
from pathlib import Path
import unittest

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import create_app
from knowledge_base.retriever import retrieve_context

class TestChatbot(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_vector_retriever(self):
        chunks = retrieve_context("How do I link PAN with Aadhaar?", top_k=3)
        self.assertGreater(len(chunks), 0)
        top_titles = [c.get("title", "").lower() for c in chunks]
        self.assertTrue(any("pan" in t or "linking" in t for t in top_titles))

    def test_chat_api_endpoint(self):
        payload = {"message": "What is the fee for Tatkaal passport?"}
        response = self.client.post('/api/chat', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("3,500", data["data"]["answer"])
        self.assertGreater(len(data["data"]["suggestions"]), 0)

    def test_empty_chat_message(self):
        response = self.client.post('/api/chat', json={"message": ""})
        self.assertEqual(response.status_code, 400)

    def test_chat_suggestions_endpoint(self):
        response = self.client.get('/api/chat/suggestions')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertGreater(len(data["suggestions"]), 3)

if __name__ == '__main__':
    unittest.main()
