from django.db import models
from django.conf import settings

# Change the User import
from django.contrib.auth import get_user_model

User = get_user_model()

class FileManager(models.Manager):
    def create_file(self, user, file_url):
        file = self.model(user=user, file_url=file_url)
        file.save(using=self._db)
        return file


class File(models.Model):
    id = models.BigAutoField(primary_key=True)
    # Update the User reference to use settings.AUTH_USER_MODEL
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='files'
    )
    file_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = FileManager()

    def __str__(self):
        return f"{self.user.username} - {self.file_url}"

    class Meta:
        db_table = 'files'