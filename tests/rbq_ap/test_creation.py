import json
from rest_framework.test import APITestCase
import requests_mock
from rbq_backend.models import Account, ASObject
from tests import helpers

MIME_AP = "application/activity+json"

class CreationTestCase(APITestCase):
    create_data = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": "https://misskey.localdomain/activities/create",
        "type": "Create",
        "actor": "https://misskey.localdomain/users/ai",
        "object": "https://misskey.localdomain/objects/1",
        "cc": [
            "https://misskey.localdomain/users/ai/followers"
            "https://www.w3.org/ns/activitystreams#Public"
        ]
    }

    note_data = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": "https://misskey.localdomain/objects/1",
        "type": "Note",
        "content": "Alerta, alerta antifascista!"
    }

    def setUp(self):
        Account.objects.create_user(username="chuukaku_may@rbq.localdomain")
        self.user = Account.objects.get(
            username="chuukaku_may@rbq.localdomain")
        self.remote_user, self.actor_data = helpers.create_remote_user("ai", "misskey.localdomain")

    def test_000_note_creates(self):
        "Test whether can create Notes."
        with requests_mock.Mocker() as remote:
            remote.get("https://misskey.localdomain/objects/1",
                       text=json.dumps(self.note_data))
            # pragma pylint: disable=no-member
            self.client.force_authenticate(user=self.remote_user)
            response = self.client.post(
                "/inbox",
                data=json.dumps(self.create_data),
                content_type=MIME_AP,
                HTTP_HOST="rbq.localdomain",
                secure=True)
            # pragma pylint: disable=no-member
            self.client.force_authenticate(user=None)
            self.assertEqual(response.status_code, 200)
            aso = ASObject.objects.get(data__id=self.note_data["id"])
            obj = aso.data
            self.assertEqual(self.note_data["type"], obj["type"])
            self.assertEqual(self.note_data["content"], obj["content"])
            self.assertEqual(aso.actor, self.remote_user)
