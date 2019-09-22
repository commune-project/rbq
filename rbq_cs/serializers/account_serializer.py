from rest_framework import serializers
from misaca_federation.models import Account

class AccountSerializer(serializers.ModelSerializer):
    bot = serializers.BooleanField(source='is_bot')
    avatar = serializers.CharField(source='get_avatar_url')
    class Meta:
        model = Account
        fields = (
            'id', 'username', 'acct', 'display_name', 'locked',
            'created_at', 'note', 'bot', 'url', 'avatar',
            'followers_count', 'following_count', 'statuses_count'
        )
