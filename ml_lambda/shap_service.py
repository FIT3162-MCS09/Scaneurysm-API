import shap
import numpy as np
import torch
from torchvision import transforms
import requests
import cv2
from datetime import datetime
from PIL import Image
import io
import matplotlib.pyplot as plt
import seaborn as sns
import boto3
from botocore.exceptions import ClientError
import os
from skimage.segmentation import slic, mark_boundaries
from skimage.color import rgb2gray


# Set matplotlib to use /tmp directory
os.environ['MPLCONFIGDIR'] = '/tmp'
# Set other temp directories
os.environ['TMPDIR'] = '/tmp'
os.environ['HOME'] = '/tmp'

from model_service import CNNModel

class ShapAnalysisService:
    def __init__(self):
        import matplotlib
        matplotlib.use('Agg')
        # Force CPU for Lambda
        self.device = torch.device('cpu')
        self.model = CNNModel().to(self.device)
        
        # Initialize S3 client
        self.s3_client = boto3.client('s3')
        self.model_bucket = 'pytorch-model-mcs09'
        self.output_bucket = 'mcs09-bucket'
        
        # Download model from S3 to Lambda's temporary storage
        model_path = '/tmp/model.pth'
        self.s3_client.download_file(
            self.model_bucket, 
            'model.pth', 
            model_path
        )
        
        # Load the model state
        state_dict = torch.load(model_path, map_location=self.device)
        
        # Handle different state dict formats
        if isinstance(state_dict, dict):
            if 'model_state_dict' in state_dict:
                state_dict = state_dict['model_state_dict']
            elif 'state_dict' in state_dict:
                state_dict = state_dict['state_dict']
        
        self.model.load_state_dict(state_dict, strict=False)
        self.model.eval()
        
        # Clean up temporary file
        if os.path.exists(model_path):
            os.remove(model_path)

    def save_to_s3(self, image_data, user_id, image_name, request_id=None):
        """
        Save image to S3 bucket under the request path structure
        
        Args:
            image_data: The image data to save
            user_id: The user's ID
            image_name: Name of the image file
            request_id: Optional request ID for organizing files
        """
        try:
            # If request_id is provided, use the requests path structure
            if request_id:
                key = f'requests/{user_id}/{request_id}/images/{image_name}'
            else:
                # Fallback to original path if no request_id
                key = f'explain/{user_id}/{image_name}'

            self.s3_client.put_object(
                Bucket=self.output_bucket,
                Key=key,
                Body=image_data,
                ContentType='image/png'
            )
            return f"https://{self.output_bucket}.s3.amazonaws.com/{key}"
        except ClientError as e:
            print(f"Error saving to S3: {str(e)}")
            return None

    def analyze_image(self, image_url, user_id, request_id):
        try:
            start_time = datetime.utcnow()
            print(f"Analysis started at {start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            print(f"Analysis requested by: krooldonutz")
            
            # Image loading and preprocessing
            response = requests.get(image_url)
            if response.status_code != 200:
                raise Exception("Could not download image from URL")

            image_pil = Image.open(io.BytesIO(response.content))
            image = np.array(image_pil)

            is_grayscale = len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1)
            if is_grayscale:
                if len(image.shape) == 3:
                    image = image.squeeze(-1)
                image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            else:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image_rgb = cv2.resize(image_rgb, (224, 224))
            image_normalized = (image_rgb - np.min(image_rgb)) / (np.max(image_rgb) - np.min(image_rgb) + 1e-7)
            image_normalized = image_normalized.astype(np.float32)
            # image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            # image = cv2.resize(image, (224, 224))
            # image = (image - np.min(image)) / (np.max(image) - np.min(image) + 1e-7)
            # image = image.astype(np.float32)

            # Prepare grayscale image for superpixel segmentation
            if is_grayscale:
                image_gray = cv2.resize(image, (224, 224))
                image_gray = (image_gray - np.min(image_gray)) / (np.max(image_gray) - np.min(image_gray) + 1e-7)
            else:
                image_gray = rgb2gray(image_normalized)

            # SHAP analysis
            masker = shap.maskers.Image("inpaint_telea", (224, 224, 3))

            def model_pipeline(x):
                x = torch.Tensor(x).permute(0, 3, 1, 2)
                normalize = transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
                x = torch.stack([normalize(img) for img in x])
                with torch.no_grad():
                    x = x.to(next(self.model.parameters()).device)
                    output = self.model(x)
                    probs = torch.nn.functional.softmax(output, dim=1)
                return probs.cpu().numpy()

            print("Analyzing the image with SHAP...")
            explainer = shap.Explainer(model=model_pipeline, masker=masker)
            shap_values = explainer(
                np.expand_dims(image, 0),
                max_evals=70,
                batch_size=5,
                outputs=shap.Explanation.argsort.flip[:1]
            )

            # Model prediction
            transform = transforms.Compose([
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])
            
            image_tensor = transform(Image.fromarray((image * 255).astype(np.uint8)))
            image_tensor = image_tensor.unsqueeze(0).to(next(self.model.parameters()).device)

            with torch.no_grad():
                output = self.model(image_tensor)
                probs = torch.nn.functional.softmax(output, dim=1)
                pred = torch.argmax(probs, dim=1).item()
                conf = probs[0][pred].item()

            # Analysis calculations
            shap_abs = np.abs(shap_values.values)
            mean_shap = np.mean(shap_abs, axis=(0, -1))
            if len(mean_shap.shape) > 2:
                mean_shap = np.mean(mean_shap, axis=-1)

            labels = slic(image_gray, n_segments=20, compactness=20, sigma=1, start_label=0, channel_axis=None)
            num_superpixels = np.max(labels) + 1
            shap_vals_aneurysm = shap_values.values[0, :, :, :, 0].mean(axis=2)  # Use class 0 or 1 based on pred
            shap_per_superpixel = np.zeros(num_superpixels)
            for sp in range(num_superpixels):
                mask = labels == sp
                if mask.sum() > 0:
                    shap_per_superpixel[sp] = shap_vals_aneurysm[mask].mean()
            top_indices = np.argsort(shap_per_superpixel)[-5:][::-1]
            top_shap_scores = shap_per_superpixel[top_indices].tolist()

            # Generate visualizations
            plt.figure(figsize=(20, 5))
            
            # Original image
            plt.subplot(1, 4, 1)
            plt.imshow(image_rgb)
            plt.title("Original Image")
            plt.axis('off')
            
            # SHAP heatmap
            plt.subplot(1, 4, 2)
            sns.heatmap(mean_shap, cmap='RdBu_r', center=0)
            plt.title("SHAP Importance Heatmap")
            plt.axis('off')
            
            # Overlay
            plt.subplot(1, 4, 3)
            plt.imshow(image_rgb)
            plt.imshow(mean_shap, cmap='RdBu_r', alpha=0.6)
            plt.title("Overlay of Image and SHAP Values")
            plt.axis('off')
            
            # Superpixel highlight plot
            plt.subplot(1, 4, 4)
            boundary_img = mark_boundaries(image_rgb / 255.0, labels, color=(1, 0, 0))
            plt.imshow(boundary_img)
            for idx, sp in enumerate(top_indices):
                mask = labels == sp
                y, x = np.where(mask)
                if len(x) > 0 and len(y) > 0:
                    centroid = (int(np.mean(x)), int(np.mean(y)))
                    plt.text(centroid[0], centroid[1], str(idx + 1), color='white', fontsize=12,
                             bbox=dict(facecolor='red', alpha=0.5))
            plt.title("Top Superpixels for Aneurysm")
            plt.axis('off')

            # Save plot to s3
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)

            # Generate unique filename using timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            image_name = f'shap_analysis_{timestamp}.png'
            
            # Save to S3 and get URL
            s3_url = self.save_to_s3(buf, user_id, image_name, request_id)
            plt.close()

            # Quadrant analysis
            h, w = mean_shap.shape
            quadrants = {
                'upper_left': mean_shap[:h//2, :w//2],
                'upper_right': mean_shap[:h//2, w//2:],
                'lower_left': mean_shap[h//2:, :w//2],
                'lower_right': mean_shap[h//2:, w//2:]
            }
            
            quadrant_scores = {k: float(np.mean(v)) for k, v in quadrants.items()}
            most_important_quadrant = max(quadrant_scores.items(), key=lambda x: x[1])[0]

            # Calculate relative importances
            total_importance = float(np.sum(np.abs(mean_shap)))
            relative_importances = {k: float(np.sum(np.abs(v)))/total_importance 
                                  for k, v in quadrants.items()}

            end_time = datetime.utcnow()
            analysis_duration = (end_time - start_time).total_seconds()

            return {
            'prediction': {
                'result': 'aneurysm detected' if pred == 1 else 'no aneurysm detected',
                'confidence': float(conf),
                'confidence_level': "high" if conf > 0.8 else "moderate" if conf > 0.6 else "low"
            },
            'analysis': {
                'most_important_quadrant': most_important_quadrant,
                'quadrant_scores': quadrant_scores,
                'relative_importances': relative_importances,
                'stability_score': float(1 - (np.std(mean_shap) / (np.mean(mean_shap) + 1e-7))),
                'importance_score': float(np.mean(np.abs(mean_shap))),
                'superpixel_analysis': {
                        'num_superpixels': int(num_superpixels),
                        'top_superpixels': [int(idx) for idx in top_indices],
                        'top_shap_scores': top_shap_scores
                }
            },
            'metadata': {
                'analysis_duration': analysis_duration,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            },
            'visualization': {
                'url': s3_url
            },
            'request_id': request_id
        }

        except Exception as e:
            return {
                'error': str(e),
                'status': 'failed'
            }