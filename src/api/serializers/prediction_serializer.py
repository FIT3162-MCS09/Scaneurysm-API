from rest_framework import serializers
from models.image_prediction import ImagePrediction
from models.user import User

class ImagePredictionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    include_shap = serializers.BooleanField(default=False, write_only=True)

    class Meta:
        model = ImagePrediction
        fields = ['id', 'user', 'image_url', 'prediction', 'created_at', 'include_shap', 'shap_explanation']
        read_only_fields = ['id', 'prediction', 'created_at', 'shap_explanation']