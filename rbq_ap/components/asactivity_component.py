from typing import Dict, Iterable, List, Optional, Union
from urllib.parse import urlparse

from django.conf import settings
from django.db import IntegrityError, transaction
from django import db
from django_q.tasks import async_task

from rbq_ap import helpers
from rbq_ap.components import fetcher_component, account_component
from rbq_backend.components import asobject_component
from rbq_backend.components.asobject_component import (
    ASDict, filter_asobject_for_output)
from rbq_backend.models import Account, ASActivity, ASObject


def send_activity(data: ASDict, recipients: Iterable[str], task_name: str = "send_activity"):
    """
    Save a new Activity to database and POST it to recipients' inboxes.

    data -- the ActivityStreams Activity dict.
    recipients -- a list of ActivityPub IDs pointed to recipient Actors.
    task_name -- the name of task in queue to send the activity.
    """
    actor = Account.objects.get(ap_id=helpers.get_id(data["actor"]))
    recipient_actors = list(Account.objects.filter(ap_id__in=recipients).all())
    recipient_actors += Account.objects.filter(followers_uri__in=recipients).all()
    ap_ids = list(set((actor.inbox_uri for actor in recipient_actors)))
    inboxes = set((actor.inbox_uri for actor in recipient_actors))

    asa = ASActivity(data=data, actor=actor, recipients=ap_ids)
    if "id" not in data.keys():
        asa.data["id"] = "https://%s/actvities/%d" % (actor.domain, asa.id)
        data = asa.data
    asa.save()
    for inbox in inboxes:
        if urlparse(inbox).hostname not in settings.RBQ_LOCAL_DOMAINS + ["www.w3.org"]:
            async_task(
                fetcher_component.post,
                inbox,
                account=actor,
                json=filter_asobject_for_output(data),
                q_options={
                    "task_name": task_name
                })


def get_recipients(data: dict) -> List[str]:
    """
    Returns recipients of an Activity.

    dict -- the Activity dict.
    """
    to = data.get("to", [])
    cc = data.get("cc", [])
    bcc = data.get("bcc", [])
    actor = data.get("actor", None)
    try:
        aso = ASObject.objects.get(data__id=helpers.get_id(data["object"]))
        return list(set(to + cc + bcc + [actor] + get_recipients(aso.data)) - set([None]))
    except (KeyError, ASObject.DoesNotExist):
        return list(set(to + cc + bcc + [actor]) - set([None]))


class ActorNotMatchException(Exception):
    "The Actor in Activity dict differs from the Account checked in HTTP Signatures."


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


class ObjectNormalizerMixin:
    "Base class of all Activity handlers."

    original_activity: ASDict
    asobject: ASObject

    def normalize_object(self, data: ASDict) -> ASDict:
        """
        Check if "object" value in an activity is wrong and fix it.

        returns Fixed Activity dict.
        data -- ActivityStreams Activity dict.
        """
        try:
            if not is_domain_equal(helpers.get_id(data["object"]), data["id"]):
                raise DomainNotMatchException(data)
            if isinstance(data["object"], dict):
                self.asobject = asobject_component.save_asobject(
                    data["object"])
                data["object"] = data["object"]["id"]
            elif isinstance(data["object"], str):
                self.asobject = asobject_component.get_asobject(
                    {"id": data["object"]})
            else:
                raise ObjectNotFoundException(data)
        except DomainNotMatchException:
            raise DomainNotMatchException(data)
        except KeyError:
            raise InvalidFormException(data)
        return data


class SaveASActivityMixin:
    def save(self, data: ASDict, actor: Account, recipients: List[str] = None) -> None:
        if not recipients:
            recipients = get_recipients(data)
        ASActivity.objects.create(
            data=data,
            actor=actor,
            recipients=recipients)


class CreateHandlerMixin(ObjectNormalizerMixin):
    "Handle the Create Activity."

    def create_handler(self, data: ASDict) -> Optional[ASDict]:
        """
        Handle the Create Activity.

        returns the proccessed Activity to save in database.
        data -- the incoming Activity dict.
        """
        try:
            return self.normalize_object(data)
        except IntegrityError:
            # NOTE: Don't create twice.
            return None


def like_or_announce_handler(_self: object, data: ASDict) -> ASDict:
    "Handle Like or Announce Activities."

    try:
        obj_id = helpers.get_id(data["object"])
        asobject = asobject_component.get_asobject({"id": obj_id})
        asobject.save()
        data["rbqInternal"] = data.get("rbqInternal", {})
        data["rbqInternal"]["status"] = "normal"
    except (KeyError, ASObject.DoesNotExist):
        raise ObjectNotFoundException(data)
    return data


class LikeHandler:
    "Handle the Like Activity."

    asobject: ASObject
    like_handler = like_or_announce_handler


class AnnounceHandler:
    "Handle the Like Activity."

    asobject: ASObject
    announce_handler = like_or_announce_handler


class UndoHandlerMixin:
    "Handle all types of Undo Activities."

    def undo_handler(self, data: ASDict) -> ASDict:
        """
        Common entry of Undo Activities.

        returns the proccessed Activity to save in database.
        data -- the incoming Activity dict.
        """
        obj_id = helpers.get_id(data["object"])
        obj_data = None
        try:
            aso = ASObject.objects.get(data__id=obj_id)
            obj_data = aso.data
        except ASObject.DoesNotExist:
            obj_data = ASActivity.objects.get(data__id=obj_id).data
        if obj_data["type"] == "Follow":
            follower = Account.objects.get(
                ap_id=helpers.get_id(obj_data["actor"]))
            followee = Account.objects.get(
                ap_id=helpers.get_id(obj_data["object"]))
            print("%s unfollows %s" % (follower, followee))
            follower.following.remove(followee)
        elif obj_data["type"] == "Like":
            like_asa = ASActivity.objects.get(data__id=obj_id)
            like_asa.data["rbqInternal"] = like_asa.data.get("rbqInternal", {})
            like_asa.data["rbqInternal"]["status"] = "canceled"
            like_asa.save()

        return data


class FollowHandlerMixin(SaveASActivityMixin):
    "Handle Follow Activities, for accounts and subforums."
    def follow_handler(self, data: ASDict) -> ASDict:
        """
        Handle the Follow Activity.

        returns the proccessed Activity to save in database.
        data -- the incoming Activity dict.
        """
        try:
            if isinstance(data["object"], dict):
                data["object"] = data["object"]["id"]
            followee = account_component.get_or_fetch_user(data["object"])
            if followee.is_local:
                if not followee.is_locked:
                    account_component.local_follow_user(
                        self.request.user, followee)
                    send_activity(
                        data={
                            "@context": "https://www.w3.org/ns/activitystreams",
                            "id": "%s#accepts/follows/%s" % (followee.ap_id, data["id"]),
                            "type": "Accept",
                            "actor": followee.ap_id,
                            "object": data
                        },
                        recipients=[
                            followee.ap_id,
                            self.request.user.ap_id
                        ],
                        task_name="send_follow_accept")
                else:
                    data["rbqInternal"] = data.get("rbqInternal", {})
                    data["rbqInternal"]["status"] = "pending"
            self.save(data, self.request.user, recipients=[
                followee.ap_id,
                self.request.user.ap_id
            ])
        except KeyError:
            raise InvalidFormException(data)
        return None

class AcceptHandlerMixin:
    "Handle Follow - Accept Activities, for accounts and subforums."

    def accept_handler(self, data: ASDict) -> None:
        """
        Common entry of Accept Activities.
        Don't save Accept Activities to the database.

        returns the proccessed Activity to save in database.
        data -- the incoming Activity dict.
        """
        followee = account_component.get_or_fetch_user(
            helpers.get_id(data["actor"]))
        follow_request = ASActivity.objects.get(helpers.get_id(data["object"]))
        follower = follow_request.actor
        account_component.local_follow_user(follower, followee)
        follow_request.delete()
