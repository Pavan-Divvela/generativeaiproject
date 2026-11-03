"""
Tests for authentication service and endpoints.
Run: python -m pytest tests/test_auth.py -v
"""
import sys
import uuid
from pathlib import Path
import unittest

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import create_app


class TestAuth(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_demo_credentials_endpoint(self):
        """GET /api/auth/demo-credentials returns demo credentials."""
        resp = self.client.get('/api/auth/demo-credentials')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["data"]["email"], "demo@example.com")

    def test_demo_user_login_success(self):
        """Demo user can log in with standard demo password."""
        payload = {
            "email": "demo@example.com",
            "password": "Password@123"
        }
        resp = self.client.post('/api/auth/login', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("token", data["data"])
        self.assertEqual(data["data"]["user"]["email"], "demo@example.com")

    def test_login_invalid_password(self):
        """Login with wrong password returns 401."""
        payload = {
            "email": "demo@example.com",
            "password": "WrongPassword999"
        }
        resp = self.client.post('/api/auth/login', json=payload)
        self.assertEqual(resp.status_code, 401)
        data = resp.get_json()
        self.assertEqual(data["status"], "error")

    def test_register_new_user_and_login(self):
        """Can register a new citizen account and log in."""
        unique_email = f"citizen_{uuid.uuid4().hex[:8]}@test.org"
        reg_payload = {
            "email": unique_email,
            "full_name": "Ramesh Kumar",
            "password": "SecretPassword@456"
        }
        reg_resp = self.client.post('/api/auth/register', json=reg_payload)
        self.assertEqual(reg_resp.status_code, 201)
        reg_data = reg_resp.get_json()
        self.assertEqual(reg_data["status"], "success")
        self.assertIn("token", reg_data["data"])
        self.assertEqual(reg_data["data"]["user"]["email"], unique_email)

        # Duplicate registration with same email should fail
        dup_resp = self.client.post('/api/auth/register', json=reg_payload)
        self.assertEqual(dup_resp.status_code, 400)

        # Login with newly registered credentials
        login_resp = self.client.post('/api/auth/login', json={
            "email": unique_email,
            "password": "SecretPassword@456"
        })
        self.assertEqual(login_resp.status_code, 200)

    def test_register_validation(self):
        """Invalid inputs return 400."""
        # Invalid email
        resp1 = self.client.post('/api/auth/register', json={
            "email": "invalid-email-address",
            "full_name": "Test User",
            "password": "ValidPassword123"
        })
        self.assertEqual(resp1.status_code, 400)

        # Short password
        resp2 = self.client.post('/api/auth/register', json={
            "email": "valid@email.com",
            "full_name": "Test User",
            "password": "123"
        })
        self.assertEqual(resp2.status_code, 400)

    def test_protected_me_endpoint(self):
        """GET /api/auth/me requires valid token."""
        # Without token -> 401
        unauth_resp = self.client.get('/api/auth/me')
        self.assertEqual(unauth_resp.status_code, 401)

        # Login first
        login_resp = self.client.post('/api/auth/login', json={
            "email": "demo@example.com",
            "password": "Password@123"
        })
        token = login_resp.get_json()["data"]["token"]

        # With Bearer token -> 200
        auth_resp = self.client.get(
            '/api/auth/me',
            headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(auth_resp.status_code, 200)
        data = auth_resp.get_json()
        self.assertEqual(data["data"]["user"]["email"], "demo@example.com")

    def test_checklist_save_and_retrieve(self):
        """Authenticated user can save and list checklists."""
        login_resp = self.client.post('/api/auth/login', json={
            "email": "demo@example.com",
            "password": "Password@123"
        })
        token = login_resp.get_json()["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Save checklist progress
        save_resp = self.client.post('/api/auth/checklists', json={
            "service_code": "passport_tatkaal",
            "service_title": "Tatkaal Passport Readiness",
            "items_checked": 3,
            "total_items": 5
        }, headers=headers)
        self.assertEqual(save_resp.status_code, 200)

        # List saved checklists
        list_resp = self.client.get('/api/auth/checklists', headers=headers)
        self.assertEqual(list_resp.status_code, 200)
        checklists = list_resp.get_json()["data"]
        self.assertTrue(any(c["service_code"] == "passport_tatkaal" for c in checklists))

    def test_logout_invalidates_session(self):
        """Logging out deletes the session token."""
        login_resp = self.client.post('/api/auth/login', json={
            "email": "demo@example.com",
            "password": "Password@123"
        })
        token = login_resp.get_json()["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Verify token works
        check_before = self.client.get('/api/auth/me', headers=headers)
        self.assertEqual(check_before.status_code, 200)

        # Logout
        logout_resp = self.client.post('/api/auth/logout', headers=headers)
        self.assertEqual(logout_resp.status_code, 200)

        # Verify token no longer works
        check_after = self.client.get('/api/auth/me', headers=headers)
        self.assertEqual(check_after.status_code, 401)


if __name__ == '__main__':
    unittest.main()
