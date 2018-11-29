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
    
    # Custom object handler; allows filtering by enabled objects
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
        return '.'.join(self.hostname, self.domain)
        
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


class Application(AbstractBaseModel):
    """
    Object representing a business process or application.
    
    """
    value = models.CharField(max_length=255, help_text="Name of the application or business process.")
    hosts = models.ManyToManyField('Host', help_text="Hostnames or FQDNs identifying this application/process.")


class Token(AbstractBaseModel):
    """
    A unique string associated with a user or set of users that permits them to
    furnish logs for ingestion.
    
    """
    owners = models.ManyToManyField('User', help_text="What user(s) are responsible for the logs submitted using this token?")
    application = models.ForeignKey('Application', on_delete=models.PROTECT, help_text="What business process or application is this token designed to support?")
    expires = models.DateTimeField(default=timezone.now, help_text="Date and time of token expiration.")
    
    value = models.CharField(max_length=255, default=uuid4, unique=True, help_text="Token string, as UUID4.")
    
    def generate(self):
        return uuid4()
    
    def renew(self):
        self.expires = get_expiration()
        self.save()


class User(AbstractBaseModel, AbstractUser):
    pass