import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.app import activities, app


class UnregisterTests(unittest.TestCase):
    def test_unregister_removes_only_the_selected_participant(self):
        activity = {"participants": ["student@example.com", "other@example.com", "student@example.com"]}
        with patch.dict(activities, {"Test Activity": activity}):
            client = TestClient(app)
            url = "/activities/Test%20Activity/signup"
            response = client.delete(url, params={"email": "student@example.com"})

            self.assertEqual(response.status_code, 200)
            self.assertEqual(activity["participants"], ["other@example.com"])
            self.assertEqual(client.get("/activities").json()["Test Activity"]["participants"], ["other@example.com"])
            self.assertEqual(client.delete(url, params={"email": "student@example.com"}).status_code, 404)

    def test_unregister_missing_activity(self):
        client = TestClient(app)
        response = client.delete("/activities/Not%20An%20Activity/signup", params={"email": "student@example.com"})
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
