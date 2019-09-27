from django import db
from rbq_backend.models import ASActivity
from rbq_backend.components.asobject_component import ASDict
from rbq_ap.components import account_component, asactivity_component


class Inbox(asactivity_component.CreateHandlerMixin,
            asactivity_component.LikeHandler,
            asactivity_component.AnnounceHandler,
            asactivity_component.UndoHandlerMixin,
            asactivity_component.FollowHandlerMixin,
            asactivity_component.AcceptHandlerMixin,
            asactivity_component.SaveASActivityMixin):
    """
    Handle all ActivityStreams Activities POSTed
    to /inbox or /users/<username>/inbox.
    """

    def __init__(self, request=None):
        self.request = request
    # Only supported
    ACTIVITY_TYPES = ['Create', 'Follow', 'Accept', 'Undo', 'Like']

    def handler(self, data: ASDict):
        """
        Do the side-effects of any Activity;
        the actual function to call is determined
        by data["type"].

        data -- the Activity dict parsed by DRF.
        """
        self.original_activity = data
        try:
            if ASActivity.objects.filter(data__id=data["id"]).count() == 0:
                self.check_actor(data)
                if data["type"] in self.ACTIVITY_TYPES:
                    data = getattr(self, '%s_handler' %
                                   data["type"].lower())(data)
                    if data:
                        self.save(data, self.request.user,
                                  asactivity_component.get_recipients(data))
                else:
                    print(data)
        except KeyError:
            raise asactivity_component.InvalidFormException(data)

    def check_actor(self, data: ASDict):
        """
        Check against HTTP Signatures.

        data -- Can be an Activity or an Object dict.
        """
        try:
            actor_id = data["actor"]
            if isinstance(data["actor"], dict):
                actor_id = data["actor"]["id"]
                data["actor"] = actor_id
            if self.request.user is None:
                raise asactivity_component.ActorNotMatchException(
                    actor_id=actor_id,
                    account_id=None)
            if self.request.user.ap_id != actor_id:
                raise asactivity_component.ActorNotMatchException(
                    actor_id=actor_id,
                    account_id=self.request.user.ap_id)
        except asactivity_component.ActorNotMatchException as exception:
            raise exception
        except:
            raise asactivity_component.ActorNotMatchException()
