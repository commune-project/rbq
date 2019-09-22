from rest_framework import serializers
from rbq_backend.models import Mention

class MentionSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='account.user.username')
    acct = serializers.CharField(source='account.user.username')
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        return obj.account.url

    class Meta:
        model = Mention
        fields = ('username', 'acct', 'id', 'url')

