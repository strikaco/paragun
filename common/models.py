from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import TruncDay, TruncHour
from django.urls import reverse
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
    updated = models.DateTimeField(auto_now=True, help_text="Date and time of last object modification.")
    enabled = models.BooleanField(default=True, help_text="Whether or not this object should be enabled.")
    
    tags = models.CharField(max_length=160, blank=True, default='', help_text="Comma-separated list of any custom tags related to this object.")
    
    # Custom object handler
    objects = AbstractBaseModelManager()
    
    @property
    def tag_list(self):
        terms = (x.strip() for x in self.tags.split(','))
        return tuple(x for x in terms)


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
        
        
class Pulse(AbstractBaseModel):
    
    token = models.ForeignKey('Token', on_delete=models.CASCADE, related_name='metrics')
    host = models.GenericIPAddressField(blank=True, null=True)
    app = models.CharField(max_length=8)
    count = models.PositiveIntegerField()
    bytes = models.PositiveIntegerField()


class Statistics(object):
    
    def __init__(self, obj):
        self.obj = obj
        self.limit = timezone.now() - timedelta(days=7)
        
        self.queryset = self.obj.metrics.filter(created__gte=self.limit)
        
    def daily(self):
        return self.queryset.annotate(ts=TruncDay('created')).values('ts').order_by('ts').annotate(num_events=models.Sum('count'), num_bytes=models.Sum('bytes'))
        
    def hourly(self):
        return self.queryset.annotate(ts=TruncHour('created')).values('ts').order_by('ts').annotate(num_events=models.Sum('count'), num_bytes=models.Sum('bytes'))
        
    def daily_by_app(self):
        return self.queryset.annotate(ts=TruncDay('created')).values('ts', 'app').order_by('ts', 'app').annotate(num_events=models.Sum('count'), num_bytes=models.Sum('bytes'))
    
    def hourly_by_app(self):
        return self.queryset.annotate(ts=TruncHour('created')).values('ts', 'app').order_by('ts', 'app').annotate(num_events=models.Sum('count'), num_bytes=models.Sum('bytes'))
    

class Token(AbstractBaseModel):
    """
    A unique string associated with a user or set of users that permits them to
    furnish logs for ingestion.
    
    """
    id = models.CharField(max_length=255, primary_key=True, default=uuid4, help_text="Token string, as UUID4.")
    
    user = models.ForeignKey('User', on_delete=models.CASCADE, help_text="What user is responsible for the creation of this token?")
    hosts = models.ManyToManyField('Host', help_text="What hostnames to expect logs from using this token.")
    expires = models.DateTimeField(default=get_expiration, help_text="Date and time of token expiration.")
    retain = models.PositiveIntegerField(default=365, help_text="How long (in days) to keep logs submitted under this token.")
    backup_email = models.EmailField(help_text="Email address of a second party or group to send expiration warnings to.", default='', blank=True)
    
    notes = models.CharField(max_length=160, blank=True, null=True, help_text="Any notes about the reason for this token.")
    
    @property
    def expired(self):
        if timezone.now() > self.expires:
            return True
        return False
        
    @property
    def purge_date(self):
        return timezone.now() - timedelta(days=self.retain)
        
    @property
    def value(self):
        return self.id
    
    def __str__(self):
        return self.id
    
    @classmethod
    def generate(cls):
        return uuid4()
        
    def get_absolute_url(self):
        return reverse('token-detail', args=(self.id,))
    
    def renew(self):
        self.expires = get_expiration()
        self.save()
        
    def statistics(self, *args, **kwargs):
        return Statistics(self)
    

class User(AbstractUser, AbstractBaseModel):
    
    email = models.EmailField(unique=True)
    
    @property
    def tokens(self):
        return Token.objects.filter(user=self)