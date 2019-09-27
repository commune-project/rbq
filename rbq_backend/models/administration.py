from django.db import models

class Administration(models.Model):
    ADMIN_TYPE = (
        ("owner", "Owns"),
        ("moderator", "Moderates"),
        ("poster", "Able to post on"),
    )
    bourgeoisie = models.ForeignKey('Account', related_name="exploits", on_delete=models.CASCADE)
    proletariat = models.ForeignKey('Account', related_name="exploited_by", on_delete=models.CASCADE)
    admin_type = models.CharField(choices=ADMIN_TYPE, max_length=50)
    def __str__(self) -> str:
        return "%s %s %s." % (self.bourgeoisie, dict(self.ADMIN_TYPE)[self.admin_type], self.proletariat)
