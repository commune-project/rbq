from rest_framework import serializers
from django.conf import settings
from rbq_backend.models import Account

from urllib.parse import urlparse

#from rbq_ap.helpers.urls.activitypub import *

class EndpointsSerializer(serializers.Serializer):
    sharedInbox = serializers.SerializerMethodField()
    def get_sharedInbox(self, obj):
        return 'https://%s/inbox' % (self.context['request'].get_host())

class PublicKeySerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    owner = serializers.URLField(source="ap_id", read_only=True)
    publicKeyPem = serializers.CharField(source="public_key")
    def get_id(self, obj):
        return "%s#main-key" % obj.ap_id

class ActorSerializer(serializers.ModelSerializer):
    """
    Serializer for local Actor (Account) objects.
    No need to serialize remote Actors.
    """
    id = serializers.URLField(source='ap_id')
    preferredUsername = serializers.CharField(source='preferred_username')

    inbox = serializers.URLField(source='inbox_uri')
    outbox = serializers.URLField(source='outbox_uri')
    following = serializers.URLField(source='following_uri')
    followers = serializers.URLField(source='followers_uri')

    url = serializers.URLField()
    manuallyApprovesFollowers = serializers.BooleanField(source='is_locked')
    endpoints = EndpointsSerializer(source='*')
    publicKey = PublicKeySerializer(source='*')

    def _set_fullname(self, instance, data):
        try:
            domain = urlparse(data.get("id", instance.ap_id))
            firstname = data.get("preferredUsername", instance.preferred_username)
            instance.username = "%s@%s" % (firstname, domain)
        except:
            pass

    def _set_inbox(self, instance, data):
        try:
            urlparse(data["endpoints"]["sharedInbox"])
            instance.inbox_uri = data["endpoints"]["sharedInbox"]
        except:
            pass

    def _set_public_key(self, instance, data):
        try:
            instance.public_key = data["publicKey"]["publicKeyPem"]
        except:
            pass

    def create(self, data):
        account = super().create(data)
        self._set_fullname(account, data)
        self._set_inbox(account, data)
        self._set_public_key(account, data)
        account.save()
        return account

    def update(self, account, data):
        self._set_fullname(account, data)
        self._set_inbox(account, data)
        self._set_public_key(account, data)
        return super().update(account, data)

    class Meta:
        model = Account
        fields = (
            'id', 'type', 'preferredUsername', 'name', 'summary', 'url',
            'manuallyApprovesFollowers', 'inbox', 'outbox',
            'followers', 'following', 'endpoints', 'publicKey'
        )
        read_only_fields = ('preferredUsername', 'endpoints', 'inbox_uri', 'publicKey')
