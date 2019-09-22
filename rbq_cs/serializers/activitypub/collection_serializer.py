from rest_framework import serializers
from misaca_federation.models import Status
from misaca_federation.helpers.urls.activitypub import *
from django.conf import settings

class CollectionSerializer(serializers.ModelSerializer):
    """
    Serializer for local Actor (Status) objects.
    No need to serialize remote Actors.
    """
    class Meta:
        model = Status
        fields = (
            'id', 'type', 'totalItems', 'next', 'prev'
        )