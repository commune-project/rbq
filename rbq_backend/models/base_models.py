from django.db import models

class ARModel(models.Model):
    "Basic model with common fields."
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True