from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from uuid import uuid4


def get_expiration(days=365):
    """
    Calculates expiration date n days in the future.
    
    Returns:
        expiration (DateTime): DateTime object representing a future timestamp.
        
    """
    return timezone.now() + timedelta(days=days)
    

# Create your models here.
class AbstractBaseModelManager(models.Manager):
    def enabled(self):
        return self.get_queryset().filter(enabled=True)


class AbstractBaseModel(models.Model):
    """
    Base model that defines common fields and attributes across all child objects.
    
    """
    class Meta:
        abstract = True
    
    # Use bigints for primary keys
    id = models.BigAutoField(primary_key=True)
    
    created = models.DateTimeField(default=timezone.now, help_text="Date and time of object creation.")
    updated = models.DateTimeField(default=timezone.now, help_text="Date and time of last object modification.")
    enabled = models.BooleanField(default=True, help_text="Whether or not this object should be enabled.")
    
    # Custom object handler
    objects = AbstractBaseModelManager()
    
    def save(self, *args, **kwargs):
        # Updates the last modified timestamp
        self.updated = timezone.now()
        super().save(*args, **kwargs)


class Host(AbstractBaseModel):
    
    class Meta:
        unique_together = ('hostname', 'domain')
    
    hostname = models.CharField(max_length=255, help_text="Name of a specific computer or host on the network.")
    domain = models.CharField(max_length=255, help_text="The domain name a specific computer, or host, on the network is associated with.")
    
    @property
    def fqdn(self):
        return '.'.join((self.hostname, self.domain))
        
    @fqdn.setter
    def fqdn(self, val):
        hostname, domain = val.strip().lower().split('.', 1)
        self.hostname = hostname.strip()
        self.domain = domain.strip()
        
    def __str__(self):
        return self.fqdn
        
    def save(self, *args, **kwargs):
        # Forces storage as lowercase
        self.hostname = self.hostname.strip().lower()
        self.domain = self.domain.strip().lower()
        super().save(*args, **kwargs)


class Token(AbstractBaseModel):
    """
    A unique string associated with a user or set of users that permits them to
    furnish logs for ingestion.
    
    """
    users = models.ManyToManyField('User', help_text="What user(s) are responsible for the logs submitted using this token?")
    hosts = models.ManyToManyField('Host', help_text="What hostnames to expect logs from using this token.")
    expires = models.DateTimeField(default=get_expiration, help_text="Date and time of token expiration.")
    
    value = models.CharField(max_length=255, default=uuid4, unique=True, help_text="Token string, as UUID4.")
    
    @property
    def expired(self):
        if timezone.now() > self.expires:
            return True
        return False
    
    def __str__(self):
        return self.value
    
    @classmethod
    def generate(cls):
        return uuid4()
    
    def renew(self):
        self.expires = get_expiration()
        self.save()
        
        
class Pulse(AbstractBaseModel):
    
    token = models.ForeignKey('Token', on_delete=models.CASCADE)
    app = models.CharField(max_length=8)
    count = models.PositiveIntegerField()
    bytes = models.PositiveIntegerField()
    

class User(AbstractUser, AbstractBaseModel):
    
    email = models.EmailField(unique=True)
    
    @property
    def tokens(self):
        return Token.objects.filter(enabled=True, users__in=[self]).order_by('-expires')