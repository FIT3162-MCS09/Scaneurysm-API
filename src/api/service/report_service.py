from dataclasses import dataclass
from .gen_ai_service import GenAiService
from .prediction_service import PredictionService
from models.user import User
from models.image_prediction import ImagePrediction
from models.ai_analysis import AIAnalysis


@dataclass
class ReportService:
    gen_ai_service: GenAiService
    prediction_service: PredictionService

    def get_latest_ai_analysis_by_user_id(self, user_id):
        user = User.objects.get(id=user_id)
        
        # Check if user is whitelisted for Gen AI features
        if not user.gen_ai_whitelist:
            return None
            
        report = ImagePrediction.objects.filter(user=user).order_by('-created_at').first()
        if not report:
            return None

        # Check if analysis already exists for this report
        existing_analysis = AIAnalysis.objects.filter(user=user, image_prediction=report).first()
        if existing_analysis:
            return {
                'generated_insight': existing_analysis.generated_insight,
                'model_used': existing_analysis.model_used,
                'source': existing_analysis.source,
                'metadata': existing_analysis.metadata,
                'already_exists': True
            }
            
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

        # Save the analysis to database
        AIAnalysis.objects.create(
            user=user,
            image_prediction=report,
            generated_insight=analysis.get('generated_insight', ''),
            model_used=analysis.get('model_used', ''),
            source=analysis.get('source', 'gen_ai'),
            metadata={
                'prompt_tokens': analysis.get('metadata', {}).get('prompt_tokens'),
                'completion_tokens': analysis.get('metadata', {}).get('completion_tokens'),
                'total_tokens': analysis.get('metadata', {}).get('total_tokens'),
                'timestamp': analysis.get('timestamp')
            }
        )
        
        analysis['already_exists'] = False
        return analysis