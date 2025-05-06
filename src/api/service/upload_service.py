import logging
from models.user import User
from models.file import File
import boto3
import utils.mcs09_constants as constants

class UploadService:
    @staticmethod
    def upload_file(file, user_id):
        """
        Upload a file to S3 bucket.
        
        Args:
            file: File object to upload
            user_id: ID of the user uploading the file
            
        Returns:
            str: Presigned URL of the uploaded file
            
        Raises:
            ValueError: If file or user_id is invalid
            boto3.exceptions.S3UploadFailedError: If S3 upload fails
            User.DoesNotExist: If user is not found
        """
        try:
            if not file or not user_id:
                raise ValueError("File and user_id are required")

            s3 = boto3.client('s3')
            file_key = f"{user_id}/{file.name}"
            
            # Upload to S3
            try:
                s3.upload_fileobj(file, constants.main_bucket, file_key)
            except boto3.exceptions.S3UploadFailedError as e:
                logging.error(f"S3 upload failed: {str(e)}")
                raise

            # Generate the file URL
            file_url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': constants.main_bucket, 'Key': file_key},
                ExpiresIn=3600
            )
            
            # Create the File record in the database
            try:
                user = User.objects.get(id=user_id)
                File.objects.create(user=user, file_url=file_url)
            except User.DoesNotExist:
                logging.error(f"User with id {user_id} not found")
                raise
                
            return file_url
            
        except (ValueError, boto3.exceptions.S3UploadFailedError, User.DoesNotExist) as e:
            logging.error(f"Upload failed: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error during upload: {str(e)}")
            return False

    @staticmethod
    def get_user_files(user_id):
        """
        Retrieve all files uploaded by a user and return their URLs from the database.
        """
        try:
            user = User.objects.get(id=user_id)
            files = File.objects.filter(user=user)
            file_urls = [file.file_url for file in files]
            return file_urls
        except Exception as e:
            print(f"Failed to retrieve files: {str(e)}")
            return []
