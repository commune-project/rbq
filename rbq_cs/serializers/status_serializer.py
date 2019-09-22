from rest_framework import serializers
from rbq_backend.models import Status

class StatusSerializer(serializers.ModelSerializer):
    uri = serializers.CharField(source='ap_id')
    content = serializers.CharField(source='text')

    class Meta:
        model = Status
        fields = ('id', 'in_reply_to_id', 'in_reply_to_account_id',
                  'created_at', 'sensitive', 'spoiler_text', 'visibility', 'language', 'uri', 'url', 'content')
