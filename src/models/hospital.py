from django.db import models
class Hospital(models.Model):
    name = models.CharField(max_length=255, unique=False)

    class Meta:
        db_table = 'hospitals'

    def __str__(self):
        return self.name


