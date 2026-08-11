from django.contrib.auth.models import AbstractUser
from django.db import models
from .managers import UserManager

class User(AbstractUser):
    '''Стандартная модель пользователя.'''
    username = None

    email = models.EmailField(
        verbose_name='Email-адрес', 
        unique=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email