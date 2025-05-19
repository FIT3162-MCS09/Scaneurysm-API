from django.db import models
from .user import User
class Report(models.Model):
    user = models.ForeignKey(
                    User,
                    on_delete=models.CASCADE,  # or CASCADE, PROTECT, etc. depending on your needs
                    null=False,
                    blank=False,  # if having a primary doctor is optional
                    related_name='reports'  # to access patient list from doctor instance
                )
    aneurysm_detected = models.BooleanField(null=False)
    confidence_score = models.IntegerField()
    approximate_size = models.IntegerField()

    def __str__(self):
        return f"{self.user.username} - {self.id}"
    
    class Meta:
        db_table = 'reports'