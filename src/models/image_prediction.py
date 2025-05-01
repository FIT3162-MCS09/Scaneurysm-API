from django.db import models
from django.contrib.auth import get_user_model

class ImagePrediction(models.Model):
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='image_predictions'
    )
    image_url = models.URLField()
    prediction = models.JSONField(null=True)
    shap_explanation = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    
    class Meta:
        ordering = ['-created_at']
        db_table = 'image_prediction'

    def __str__(self):
        return f"Prediction for {self.user.username} at {self.created_at}"
        
    def save(self, *args, **kwargs):
        if not self.created_by:
            self.created_by = self.user.username
        super().save(*args, **kwargs)