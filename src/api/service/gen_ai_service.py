import os
import json
import requests
from datetime import datetime
from django.conf import settings
from django.core.cache import cache
from functools import lru_cache

class GenAiService:
    def __init__(self):
        self.api_key = os.environ.get('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is not set")
            
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        # self.model = "deepseek/deepseek-prover-v2:free"
        self.model = "mistralai/mistral-7b-instruct:free" 
        self.cache_ttl = 60 * 60 * 24  # 24 hours in seconds
        
    def generate_analysis(self, prediction_data):
        """
        Generate medical insights using OpenRouter API based on prediction and SHAP analysis
        """
        try:
            # Check cache first
            cache_key = f"analysis_{prediction_data.get('id')}_{self.model}"
            cached_result = cache.get(cache_key)
            if cached_result:
                cached_result['source'] = 'cache'
                return cached_result

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else "localhost"
            }

            # Prepare the prompt
            prompt = self._create_medical_prompt(prediction_data)

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,  # Lower temperature for more focused medical analysis
                "max_tokens": 500,    # Limit response to roughly one paragraph
                "top_p": 0.9,        # Narrow down the token selection for more focused output
                "frequency_penalty": 0.5  # Reduce repetition
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30  # 30 second timeout
            )

            if response.status_code == 200:
                result = response.json()
                generated_result = {
                    'generated_insight': result['choices'][0]['message']['content'],
                    'model_used': result['model'],
                    'timestamp': datetime.utcnow().isoformat(),
                    'metadata': {
                        'prompt_tokens': result.get('usage', {}).get('prompt_tokens'),
                        'completion_tokens': result.get('usage', {}).get('completion_tokens'),
                        'total_tokens': result.get('usage', {}).get('total_tokens')
                    },
                    'source': 'api'
                }
                # Cache the result
                cache.set(cache_key, generated_result, self.cache_ttl)
                return generated_result
            else:
                error_result = {
                    'error': f"API Error: {response.status_code}",
                    'details': response.text,
                    'timestamp': datetime.utcnow().isoformat()
                }
                # Cache errors briefly to prevent hammering the API
                cache.set(cache_key, error_result, 300)  # Cache errors for 5 minutes
                return error_result

        except requests.exceptions.Timeout:
            return {
                'error': 'API request timed out',
                'timestamp': datetime.utcnow().isoformat()
            }
        except requests.exceptions.RequestException as e:
            return {
                'error': f"Request failed: {str(e)}",
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'error': f"Unexpected error: {str(e)}",
                'timestamp': datetime.utcnow().isoformat()
            }

    @staticmethod
    def _create_medical_prompt(prediction_data):
        """
        Create a prompt for the medical AI model based on prediction data
        """
        prediction = prediction_data.get('prediction', {})
        shap_data = prediction_data.get('shap_explanation', {})
        analysis = shap_data.get('analysis', {})
        
        prompt = f"""You are an AI medical assistant analyzing a brain aneurysm scan result.

Prediction Details:
- Classification: {prediction.get('prediction')}
- Confidence Score: {prediction.get('confidence', 0):.2%}
- Model Metadata: {json.dumps(prediction.get('metadata', {}), indent=2)}

SHAP Analysis Results:
- Stability Score: {analysis.get('stability_score')}
- Most Important Region: {analysis.get('most_important_quadrant')}
- Quadrant Relative Importances:
  {json.dumps(analysis.get('relative_importances', {}), indent=2)}
- Super-pixel Analysis:
  {json.dumps(analysis.get('superpixel_analysis', {}), indent=2)}

Please provide a concise medical analysis including:
1. Clinical interpretation of the prediction and its confidence level
2. Significance of the identified important regions in the context of aneurysm detection
3. Recommendations for follow-up based on these findings
4. Any noteworthy patterns in the SHAP analysis that could be clinically relevant

Focus on being precise, medical professional-focused, and actionable."""

        return prompt