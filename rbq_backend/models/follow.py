from django.db import models
from .base_models import ARModel

class Follow(ARModel):
    followee = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='+')
    follower = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='+')
    class Meta:
        ordering = ['created_at']
