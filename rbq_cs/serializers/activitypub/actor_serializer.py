from rest_framework import serializers
from django.conf import settings
from misaca_federation.models import Account
from misaca_federation.helpers.urls.activitypub import *

class EndpointsSerializer(serializers.Serializer):
    sharedInbox = serializers.SerializerMethodField()
    def get_sharedInbox(self, obj):
        return 'https://%s/inbox' % (settings.MISACA_FEDERATION_DOMAIN,)

class ActorSerializer(serializers.ModelSerializer):
    """
    Serializer for local Actor (Account) objects.
    No need to serialize remote Actors.
    """
    id = serializers.URLField(source='ap_id')
    type = serializers.SerializerMethodField()
    preferredUsername = serializers.CharField(source='username')
    name = serializers.CharField(source='display_name')

    inbox = serializers.URLField(source='ap_inbox_uri')
    outbox = serializers.URLField(source='ap_outbox_uri')
    following = serializers.URLField(source='ap_following_uri')
    followers = serializers.URLField(source='ap_followers_uri')

    url = serializers.URLField(source='ap_url')
    manuallyApprovesFollowers = serializers.BooleanField(source='locked')
    endpoints = EndpointsSerializer(source='*')
    class Meta:
        model = Account
        fields = (
            'id', 'type', 'preferredUsername', 'name', 'url',
            'manuallyApprovesFollowers', 'inbox', 'outbox',
            'followers', 'following', 'endpoints'
        )

    def get_type(self, obj):
        if obj.actor_type and obj.actor_type!='':
            return obj.actor_type
        else:
            return ("Service" if obj.is_bot else "Person")
