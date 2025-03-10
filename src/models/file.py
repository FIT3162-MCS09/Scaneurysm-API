# File: src/models/file.py
from django.db import models
from django.conf import settings

from .user import User


class FileManager(models.Manager):
    def create_file(self, user, file_url):
        file = self.model(user=user, file_url=file_url)
        file.save(using=self._db)
        return file


class File(models.Model):
    # Use settings.AUTH_USER_MODEL instead of direct import
    user =models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    file_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = FileManager()

    def __str__(self):
        return f"{self.user.username} - {self.file_url}"

    class Meta:
        db_table = 'files'