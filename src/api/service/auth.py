import logging
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from models.user import User

logger = logging.getLogger(__name__)

class AuthService:
    @staticmethod
    def authenticate(username, password):
        """
        Retrieve a user by their username.
        Returns the user object if found, otherwise returns None.
        """
        try:
            user = User.objects.get(username=username)
            logging.debug(f'User found: {user}')
            if user is None:
                return None
            if check_password(password, user.hashed_password):
                return user
            else:
                return None
        except:
            return None