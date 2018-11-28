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
    
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(default=timezone.now)
    enabled = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        """
        Always update the last modified timestamp!
        
        """
        self.updated = timezone.now()
        super().save(*args, **kwargs)

class Application(BaseModel):
    pass

class Token(BaseModel):
    owner = models.ForeignKey('User', on_delete=models.PROTECT)
    application = models.ForeignKey('Application', on_delete=models.PROTECT)
    expires = models.DateTimeField(default=timezone.now)
    
    value = models.CharField(max_length=255, default=uuid4, db_index=True)
    
    def generate(self):
        return uuid4()
    
    def renew(self):
        self.expires = get_expiration()
        self.save()

class User(BaseModel, AbstractUser):
    pass