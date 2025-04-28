from rest_framework import serializers
from models.image_prediction import ImagePrediction
from models.user import User

class ImagePredictionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())  # Changed to allow input

    class Meta:
        model = ImagePrediction
        fields = ['id', 'user', 'image_url', 'prediction', 'created_at']
        read_only_fields = ['id', 'prediction', 'created_at']  # Removed user from read_only