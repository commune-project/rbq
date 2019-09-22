from rest_framework import serializers
from rbq_backend.models import Status
from rbq_cs.serializers.mastodon.account_serializer import AccountSerializer
#from rbq_cs.serializers.mastodon.mention_serializer import MentionSerializer

class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        if not value:
            return None
        serializer = self.parent.__class__(value, context=self.context)
        return serializer.data

class StatusSerializer(serializers.ModelSerializer):
    content = serializers.CharField(source='text')
    visibility = serializers.CharField(source='visibility')
    reblog = RecursiveField(source="reblog_of")
    account = AccountSerializer()
#    mentions = MentionSerializer(many=True)

    class Meta:
        model = Status
        fields = ('id', 'in_reply_to_id', 'in_reply_to_account_id',
                  'created_at', 'sensitive', 'spoiler_text',
                  'visibility', 'language', 'uri', 'url', 'content',
                  'reblog', 'account',# 'mentions',
                  'reblogs_count', 'favourites_count')
