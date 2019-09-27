import json
from rest_framework.test import APITestCase
import requests_mock
from rbq_backend.models import Account
from rbq_ap.serializers.actor import ActorSerializer
from tests import helpers

MIME_AP = "application/activity+json"

class ActorTestCase(APITestCase):

    follow_data = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": "https://misskey.localdomain/activities/follow",
        "type": "Follow",
        "actor": "https://misskey.localdomain/users/ai",
        "object": "https://rbq.localdomain/users/chuukaku_may"
    }

    def setUp(self):
        Account.objects.create_user(username="chuukaku_may@rbq.localdomain")
        self.user = Account.objects.get(
            username="chuukaku_may@rbq.localdomain")
        self.remote_user, self.actor_data = helpers.create_remote_user("ai", "misskey.localdomain")

    def test_000_actor_creation(self):
        self.assertEqual(Account.objects.count(), 2)
        self.assertEqual(
            Account.objects.get(username="chuukaku_may@rbq.localdomain").inbox_uri,
            "https://rbq.localdomain/users/chuukaku_may/inbox")
        self.assertEqual(
            Account.objects.filter(
                ap_id__in=["https://misskey.localdomain/users/ai"]).all()[0].preferred_username,
            "ai")

    def test_001_actor_get(self):
        "Test whether can get the Actor."
        response = self.client.get(
            "/users/chuukaku_may",
            HTTP_ACCEPT=MIME_AP,
            HTTP_HOST="rbq.localdomain",
            secure=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["preferredUsername"], "chuukaku_may")

    def test_002_actor_follow(self):
        "Test whether a remote actor can follow a local actor."
        with requests_mock.Mocker() as remote:
            remote.get('https://misskey.localdomain/users/ai', text=json.dumps(self.actor_data))
            remote.post('https://misskey.localdomain/inbox')
            remote.post('https://misskey.localdomain/users/ai/inbox')
            remote.get(
                'https://misskey.localdomain/activities/follow',
                text=json.dumps(self.follow_data))
            # pragma pylint: disable=no-member
            self.client.force_authenticate(user=self.remote_user)
            response = self.client.post(
                "/inbox",
                data=json.dumps(self.follow_data),
                content_type=MIME_AP,
                HTTP_HOST="rbq.localdomain",
                secure=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(self.remote_user, self.user.followers.all())
            # pragma pylint: disable=no-member
            self.client.force_authenticate(user=None)
