from rbq_backend.models import Account
from rbq_ap.serializers.actor import ActorSerializer


def create_remote_user(preferred_username: str, domain: str) -> (Account, dict):
    "Create a fake remote user in database."

    class MockRequest:
        def __init__(self, host):
            self.host = host

        def get_host(self):
            return self.host

    remote_user = Account(
        username="%s@%s" % (preferred_username, domain),
        ap_id="https://%s/users/%s" % (domain, preferred_username))
    Account.objects.initialize(remote_user)
    remote_user.save()
    actor_data = ActorSerializer(
        instance=remote_user,
        context={
            "request": MockRequest(domain)
        }).data
    return remote_user, actor_data
