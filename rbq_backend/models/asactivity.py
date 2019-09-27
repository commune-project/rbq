from typing import Optional
from django.db import models
from django.contrib.postgres.fields import JSONField, ArrayField, CITextField
from django.contrib.auth.models import AbstractBaseUser, UserManager, PermissionsMixin
from django.conf import settings

from .base_models import ARModel
from .account import Account
from .asobject import ASObject

class ASActivity(ARModel):
    "All ActivityStreams activities goes here."
    data = JSONField()
    domain = CITextField()
    actor = models.ForeignKey(
        Account, on_delete=models.DO_NOTHING, related_name='activities', to_field='ap_id')
    recipients = ArrayField(models.TextField(), null=True)

    @property
    def asobject(self):
        try:
            return ASObject.objects.get(data__id=self.data["object"])
        except KeyError:
            raise ASObject.DoesNotExist

    def __str__(self):
        try:
            return self.data.get("type", "") + ": " + self.data["id"]
        except KeyError:
            return super().__str__()

    class Meta:
        verbose_name_plural = 'ASActivities'
