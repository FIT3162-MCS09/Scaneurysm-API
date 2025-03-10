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
        """
        try:
            s3 = boto3.client('s3')
            file_key = f"{user_id}/{file.name}"
            s3.upload_fileobj(file, constants.main_bucket, file_key)
            
            # Generate the file URL
            file_url = s3.generate_presigned_url('get_object', Params={'Bucket': constants.main_bucket, 'Key': file_key}, ExpiresIn=3600)
            
            # Create the File record in the database
            user = User.objects.get(id=user_id)
            File.objects.create(user=user, file_url=file_url)
            
            return True
        except Exception as e:
            logging.error(f"Failed to upload file: {str(e)}")
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
