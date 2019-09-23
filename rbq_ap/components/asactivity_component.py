from typing import Iterable

from rbq_backend.models import ASActivity, Account
from rbq_ap.components import fetcher_component
from rbq_ap import helpers

from django_q.tasks import async_task
from django.conf import settings
from urllib.parse import urlparse

from rbq_backend.components.asobject_component import ASDict, filter_asobject_for_output


def send_activity(data: ASDict, recipients: Iterable[str], task_name: str = "send_activity"):
    """
    Save a new Activity to database and POST it to recipients' inboxes.

    data -- the ActivityStreams Activity dict.
    recipients -- a list of ActivityPub IDs pointed to recipient Actors.
    task_name -- the name of task in queue to send the activity.
    """
    actor = Account.objects.get(ap_id=helpers.get_id(data["actor"]))
    recipient_actors = Account.objects.filter(ap_id__in=recipients).all()
    ap_ids = list(set((actor.inbox_uri for actor in recipient_actors)))
    inboxes = set((actor.inbox_uri for actor in recipient_actors))

    ASActivity.objects.create(data=data, actor=actor, recipients=ap_ids)
    for inbox in inboxes:
        if urlparse(inbox).hostname not in settings.RBQ_LOCAL_DOMAINS:
            async_task(
                fetcher_component.post,
                inbox,
                account=actor,
                json=filter_asobject_for_output(data),
                q_options={
                    "task_name": task_name
                }
            )
