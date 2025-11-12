from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import BaseUserManager


import uuid
from datetime import datetime, timezone

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
# from django.db import models

from common.models import BaseModel
from django.contrib.auth.models import User


from .manager import CustomUserManager


class TokenType(models.TextChoices):
    PASSWORD_RESET = ("PASSWORD_RESET", "PASSWORD_RESET")


# class User(BaseModel, AbstractBaseUser, PermissionsMixin):
#     email = models.EmailField(unique=True)
#     password = models.CharField(max_length=255)
#     USERNAME_FIELD = "email"
#     REQUIRED_FIELDS = []
#     is_active = models.BooleanField(default=True)
#     is_staff = models.BooleanField(default=False)

#     objects = CustomUserManager()

class User(BaseModel, AbstractBaseUser, PermissionsMixin): 
    username = models.CharField(max_length=150)
    email = models.EmailField(max_length=355, unique=True, blank=False, null=False)
    mobile_number = models.CharField(max_length=15, unique=True, blank=False, null=False)
    password = models.CharField(max_length=255, default=False, null=False)
    is_email_verified = models.BooleanField(default=False)
    is_mobile_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  
    email_otp = models.CharField(max_length=6, blank=True, null=True)
    mobile_otp = models.CharField(max_length=6, blank=True, null=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['mobile_number']

    objects = CustomUserManager() 

    def __str__(self):
        return self.email


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None,**extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(
            email=email,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, mobile_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, mobile_number, password, **extra_fields)




class PendingUser(BaseModel):
    email = models.EmailField()
    password = models.CharField(max_length=255)
    verification_code = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self) -> bool:
        lifespan_in_seconds = 20 * 60
        now = datetime.now(timezone.utc)
        timediff = now - self.created_at
        timediff = timediff.total_seconds()
        if timediff > lifespan_in_seconds:
            return False
        return True


class Token(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255)
    token_type = models.CharField(max_length=100, choices=TokenType.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user}  {self.token}"

    def is_valid(self) -> bool:
        lifespan_in_seconds = 20 * 60  # 20 mins
        now = datetime.now(timezone.utc)
        timediff = now - self.created_at
        timediff = timediff.total_seconds()
        if timediff > lifespan_in_seconds:
            return False
        return True

    def reset_user_password(self, raw_password: str):
        self.user: User
        self.user.set_password(raw_password)
        self.user.save()


