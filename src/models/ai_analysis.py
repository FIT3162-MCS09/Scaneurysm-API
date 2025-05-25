from django.db import models
from django.contrib.auth import get_user_model
from .image_prediction import ImagePrediction
from .user import User

class AIAnalysis(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image_prediction = models.ForeignKey(ImagePrediction, on_delete=models.CASCADE)
    generated_insight = models.TextField()
    model_used = models.CharField(max_length=550)
    source = models.CharField(max_length=50)  # Can be 'gen_ai', 'api', 'cache'
    metadata = models.JSONField(null=True)  # For prompt_tokens, completion_tokens, total_tokens
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        db_table = 'ai_analysis'
        verbose_name = 'AI Analysis'
        verbose_name_plural = 'AI Analyses'
        # Set composite primary key
        constraints = [
            models.UniqueConstraint(fields=['user', 'image_prediction'], name='ai_analysis_pk')
        ]
        # Add indexes
        indexes = [
            models.Index(fields=['user_id'], name='ai_analysis_user_idx'),
            models.Index(fields=['image_prediction_id'], name='ai_analysis_img_pred_idx'),
            models.Index(fields=['created_at'], name='ai_analysis_created_at_idx')
        ]

    def __str__(self):
        return f"Analysis for {self.user.username}'s prediction at {self.created_at}"
