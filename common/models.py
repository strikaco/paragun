from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from uuid import uuid4

def get_expiration():
    return timezone.now() + timedelta(days=365)

# Create your models here.
class BaseModel(models.Model):
    
    class Meta:
        abstract = True
    
    id = models.BigAutoField(primary_key=True)
    
    created = models.DateTimeField(default=timezone.now, help_text="Date and time of object creation.")
    updated = models.DateTimeField(default=timezone.now, help_text="Date and time of last object modification.")
    enabled = models.BooleanField(default=True, help_text="Whether or not this object should be enabled.")
    
    def save(self, *args, **kwargs):
        """
        Always update the last modified timestamp!
        
        """
        self.updated = timezone.now()
        super().save(*args, **kwargs)

class Application(BaseModel):
    pass

class Token(BaseModel):
    owners = models.ManyToManyField('User', help_text="What user(s) are responsible for the logs submitted using this token?")
    application = models.ForeignKey('Application', on_delete=models.PROTECT, help_text="What application is this token designed to support?")
    expires = models.DateTimeField(default=timezone.now, help_text="Date and time of token expiration.")
    
    value = models.CharField(max_length=255, default=uuid4, unique=True, help_text="Token string, as UUID4.")
    
    def generate(self):
        return uuid4()
    
    def renew(self):
        self.expires = get_expiration()
        self.save()

class User(BaseModel, AbstractUser):
    pass