from rest_framework import serializers
from rbq_backend.models import ASObject, ASActivity
from rbq_cs.serializers.mastodon.account_serializer import AccountSerializer
#from rbq_cs.serializers.mastodon.mention_serializer import MentionSerializer

class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        if not value:
            return None
        serializer = self.parent.__class__(value, context=self.context)
        return serializer.data

class StatusSerializer(serializers.ModelSerializer):
    id = serializers.CharField()
    uri = serializers.URLField(source='asobject__data__id')
    url = serializers.URLField(source='asobject__data__url')
    account = AccountSerializer(source="actor")
    in_reply_to_id = serializers.CharField(
        source='asobject__in_reply_to__asactivity__id')
    in_reply_to_account_id = serializers.CharField(
        source='asobject__in_reply_to__asactivity__actor__id')
    created_at = serializers.DateTimeField(source="asobject__data__published")
    sensitive = serializers.BooleanField(source='asobject__data__sensitive')
    spoiler_text = serializers.CharField(source='asobject__data__summary')
#    visibility = serializers.CharField(source='visibility')
    language = serializers.CharField(source='asobject__language')

    content = serializers.CharField(source='asobject__data__content')
#    reblog = RecursiveField(source="reblog_of")
#    mentions = MentionSerializer(many=True)

    favourites_count = serializers.SerializerMethodField()

    def get_favourites_count(self, asa: ASActivity) -> int:
        return ASActivity.objects.filter(
            data__object=asa.data["id"],
            data__type="Like",
            data__rbqInternal__status="normal").count()

    reblogs_count = serializers.SerializerMethodField()

    def get_reblogs_count(self, asa: ASActivity) -> int:
        return ASActivity.objects.filter(
            data__object=asa.data["id"],
            data__type="Announce",
            data__rbqInternal__status="normal").count()

    class Meta:
        model = ASActivity
        fields = ('id', 'in_reply_to_id', 'in_reply_to_account_id',
                  'created_at', 'sensitive', 'spoiler_text',
                  'visibility', 'language', 'uri', 'url', 'content',
                  #'reblog',
                  'account',# 'mentions',
                  #'reblogs_count',
                  'favourites_count')
