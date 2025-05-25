from dataclasses import dataclass
from .gen_ai_service import GenAiService
from .prediction_service import PredictionService
from models.user import User
from models.image_prediction import ImagePrediction


@dataclass
class ReportService:
    gen_ai_service: GenAiService
    prediction_service: PredictionService

    def get_latest_ai_analysis_by_user_id(self, user_id):
        user = User.objects.get(id=user_id)
        report = ImagePrediction.objects.filter(user=user).order_by('-created_at').first()
        if not report:
            return None
            
        # Convert ImagePrediction instance to dictionary
        prediction_data = {
            'id': report.id,
            'prediction': report.prediction,
            'shap_explanation': report.shap_explanation,
            'created_at': report.created_at.isoformat() if report.created_at else None,
            'image_url': report.image_url,
            'request_id': report.request_id,
        }
        
        analysis = self.gen_ai_service.generate_analysis(prediction_data)
        if not analysis:
            return None
        analysis['source'] = 'gen_ai'
        return analysis