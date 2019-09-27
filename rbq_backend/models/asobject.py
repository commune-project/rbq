from typing import Dict, Optional, Union, List
from django.db import models, transaction   
from django.contrib.postgres.fields import JSONField, ArrayField, CITextField
from django.contrib.auth.models import AbstractBaseUser, UserManager, PermissionsMixin
from django.conf import settings

from .account import Account
from rbq_ap.components import fetcher_component

ASElement = Union[str, int, float, 'ASDict', List['ASElement']]
ASDict = Dict[str, ASElement]

class ASObjectManager(models.Manager):
    def get_or_fetch(self, obj: ASDict) -> Optional['ASObject']:
        """
        Get an ASObject from DB or fetch it from remote.

        :params obj: a dict contains key "id" that pointed to the object's AP ID.
        :returning: the ASObject fetched from DB or saved to DB.
        """
        try:
            return self.get(data__id=obj["id"])
        except self.model.DoesNotExist:
            result = fetcher_component.get(obj["id"])
            obj = result.json()
            return self.save_asobject(obj)

    def save_asobject(self, obj: ASDict) -> Optional['ASObject']:
        """
        Save an ASObject to DB with some fixes.

        :params obj: the ASDict to save.
        :returning: the created or updated ASObject.
        """
        if "id" not in obj.keys():
            return None
        obj = self.maybe_create_or_find_context(obj)
        try:
            aso = self.get(data__id=obj["id"])
            aso.data = obj
            aso.save()
        except self.model.DoesNotExist:
            aso = self.create(data=obj)
        aso = self.maybe_increase_actor_posts_count(aso)
        return aso

    def maybe_create_or_find_context(self, obj: ASDict, recursion_count: int = 0) -> ASDict:
        """Ensure an ActivityStreams object has its context."""
        context = None
        try:
            context = self.get(data__id=obj["context"])
        except (KeyError, self.model.DoesNotExist):
            if 'inReplyTo' in obj.keys() and recursion_count < 8:
                obj["context"] = self.maybe_create_or_find_context(
                    self.get_or_fetch({"id": obj["inReplyTo"]}),
                    recursion_count=recursion_count+1)
            else:
                with transaction.atomic():
                    context = self.model(data={"type": "Context"})
                    context.save()
                    context.data["id"] = "https://%s/contexts/%s" % (
                        settings.RBQ_LOCAL_DOMAINS[0], context.id)
                    context.save()
                    obj["context"] = context.data["id"]
        return obj

    @staticmethod
    def maybe_increase_actor_posts_count(aso: 'ASObject') -> 'ASObject':
        """
        Increase posts_count of the object's actor if object is of certain types.

        :params aso: -- The ASObject to check its type.
        :returning: aso itself.
        """
        try:
            if aso.data.get("type", None) in ("Article", "Note"):
                actor = aso.actor
                actor.posts_count += 1
                actor.save()
        except Account.DoesNotExist:
            pass
        return aso


class ASObject(models.Model):
    "All ActivityStreams objects goes here."
    data = JSONField()

    @property
    def actor(self):
        if isinstance(self.data.get("actor", None), str):
            return Account.objects.get(ap_id=self.data["actor"])
        return Account.objects.filter(
            activities__data__object=self.data["id"],
            activities__data__type="Create").get()

    def __str__(self):
        try:
            return self.data["id"]
        except KeyError:
            return "ASO: %d" % self.id

    @property
    def asactivity(self):
        from .asactivity import ASActivity
        return ASActivity.objects.get(
            data__object=self.data["id"],
            data__type="Create")

    @property
    def language(self):
        try:
            return self.data["contentMap"].keys()[0]
        except (KeyError, TypeError, IndexError):
            return settings.LANGUAGE_CODE

    @property
    def in_reply_to(self):
        return ASObject.objects.get(data__id=self.data["inReplyTo"])

    @property
    def replies(self):
        return ASObject.objects.filter(data__inReplyTo=self.data["id"])

    @property
    def replies_count(self):
        return self.replies.count()

    objects = ASObjectManager()

    class Meta:
        verbose_name_plural = 'ASObjects'
