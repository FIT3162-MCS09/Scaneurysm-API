from rest_framework import serializers

class ShapAnalysisRequestSerializer(serializers.Serializer):
    image_url = serializers.URLField(required=True)

class ShapAnalysisResponseSerializer(serializers.Serializer):
    prediction = serializers.DictField()
    analysis = serializers.DictField()
    metadata = serializers.DictField()
    visualization = serializers.DictField()