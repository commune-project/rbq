from typing import Iterable, List, Dict, Any, Union, Optional

from rbq_backend.models import ASActivity, ASObject, Account
from rbq_backend.components import asobject_component
from rbq_ap.components import account_component, fetcher_component, asactivity_component
from django_q.tasks import async_task, result
from django.db import IntegrityError
from urllib.parse import urlparse


def get_recipients(data: dict) -> List[str]:
    to = data.get("to", [])
    cc = data.get("cc", [])
    bcc = data.get("bcc", [])
    actor = data.get("actor", [])
    try:
        aso = ASObject.objects.get(data__id=data["object"])
        return list(set(to + cc + bcc + [actor]+ get_recipients(aso.data)))
    except (KeyError, ASObject.DoesNotExist):
        return list(set(to + cc + bcc + [actor]))

def get_id(data: Union[str, Dict[str, str]]) -> Optional[str]:
    """
    Get object id.
    
    The object id of a str is itself
    """
    if isinstance(data, dict):
        if "id" in data.keys():
            return data["id"]
    if isinstance(data, str):
        return data
    else:
        return None


class ActorNotMatchException(Exception):
    pass

class InvalidFormException(Exception):
    pass

class DomainNotMatchException(Exception):
    pass

class ObjectNotFoundException(Exception):
    pass

def is_domain_equal(url1: str, url2: str) -> bool:
    "Don't allow activities with their objects from other domains."
    result1, result2 = urlparse(url1), urlparse(url2)
    return result1.hostname == result2.hostname

class Inbox:
    """
    Handle all ActivityStreams Activities POSTed
    to /inbox or /users/<username>/inbox.
    """
    def __init__(self, request=None):
        self.request = request
    # Only supported
    ACTIVITY_TYPES = ['Create', 'Follow', 'Undo']
    def handler(self, data: dict):
        """
        Do the side-effects of any Activity;
        the actual function to call is determined
        by data["type"].

        data -- the Activity dict parsed by DRF.
        """
        try:
            if ASActivity.objects.filter(data__id=data["id"]).count() == 0:
                self.check_actor(data)
                if data["type"] in self.ACTIVITY_TYPES:
                    data = getattr(self, '%s_handler' % data["type"].lower())(data)
                    ASActivity.objects.create(data=data, actor=self.request.user, recipients=get_recipients(data))
                else:
                    print(data)
        except KeyError:
            raise InvalidFormException(data)
        except ActorNotMatchException:
            pass
        except Exception as e:
            print(e)

    def create_handler(self, data: dict) -> Optional[Dict[str, Any]]:
        try:
            if isinstance(data["object"], dict):
                data = self.normalize_object(data)
                asobject_component.save_asobject(data["object"])
                data["object"] = data["object"]["id"]
            elif isinstance(data["object"], str):
                if not is_domain_equal(data["object"], data["id"]):
                    raise DomainNotMatchException(data)
                asobject_component.get_asobject({"id": data["object"]})
            else:
                raise ObjectNotFoundException(data)
            return data
        except KeyError:
            raise InvalidFormException(data)
        except IntegrityError:
            # NOTE: Don't create twice.
            return None

    def follow_handler(self, data: dict) -> dict:
        try:
            if isinstance(data["object"], dict):
                data["object"] = data["object"]["id"]
            followee = account_component.get_or_fetch_user(data["object"])
            if followee.is_local:
                if not followee.is_locked:
                    self.request.user.following.add(followee)
                    asactivity_component.send_activity(data={
                        "@context": "https://www.w3.org/ns/activitystreams",
                        "id": "%s#accepts/follows/%s" % (followee.ap_id, data["id"]),
                        "type": "Accept",
                        "actor": followee.ap_id,
                        "object": data
                    }, recipients=[followee.ap_id, self.request.user.ap_id], task_name="send_follow_accept")
        except KeyError:
            raise InvalidFormException(data)
        return data

    def undo_handler(self, data: dict) -> dict:
        obj_id = get_id(data["object"])
        obj_data = None
        try:
            aso = ASObject.objects.get(data__id=obj_id)
            obj_data = aso.data
        except ASObject.DoesNotExist:
            obj_data = ASActivity.objects.get(data__id=obj_id).data
        if obj_data["type"] == "Follow":
            follower = Account.objects.get(ap_id=get_id(obj_data["actor"]))
            followee = Account.objects.get(ap_id=get_id(obj_data["object"]))
            print("%s unfollows %s" % (follower, followee))
            follower.following.remove(followee)
        return data

    def check_actor(self, data: dict):
        "Check against HTTP Signatures"
        try:
            actor_id = data["actor"]
            if isinstance(data["actor"], dict):
                actor_id = data["actor"]["id"]
                data["actor"] = actor_id
            if self.request.user.ap_id != actor_id:
                raise ActorNotMatchException()
        except:
            raise ActorNotMatchException()

    def normalize_object(self, data: dict) -> dict:
        try:
            if not is_domain_equal(data["object"]["id"], data["id"]):
                raise DomainNotMatchException(data)
        except:
            raise DomainNotMatchException(data)
        return data
