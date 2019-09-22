from rest_framework import serializers
from rbq_backend.models import Account

class AccountSerializer(serializers.ModelSerializer):
    bot = serializers.BooleanField(source='is_bot')
    locked = serializers.BooleanField(source='is_locked')
    acct = serializers.CharField(source="username")
    note = serializers.CharField(source="summary")
    avatar = serializers.CharField(read_only=True)
    header = serializers.CharField(read_only=True)
    username = serializers.CharField(source='preferred_username')
    display_name = serializers.CharField(source='name')
    followers_count = serializers.IntegerField()
    following_count = serializers.IntegerField()
    statuses_count = serializers.IntegerField(source="posts_count")
    url = serializers.URLField()
    class Meta:
        model = Account
        fields = (
            'id', 'username', 'acct', 'display_name', 'locked',
            'created_at', 'note', 'bot', 'url', 'avatar', 'header',
            'followers_count', 'following_count', 'statuses_count',
        )
