from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.db.models.functions import Coalesce, TruncDay, TruncHour
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
    
    tags = models.CharField(max_length=160, blank=True, null=True, help_text="Comma-separated list of any custom tags related to this object.")
    
    # Custom object handler
    objects = AbstractBaseModelManager()
    
    @property
    def tag_list(self):
        terms = (x.strip() for x in self.tags.split(','))
        return tuple(x for x in terms)
        
    def get_admin_url(self):
        """
        Returns the URI path for the Django Admin page for this object.

        ex. Account#1 = '/admin/accounts/1/change/'

        Returns:
            path (str): URI path to Django Admin page for object.

        """
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (content_type.app_label,
                                               content_type.model), args=(self.id,))
        
        
class Pulse(AbstractBaseModel):
    
    token = models.ForeignKey('Token', on_delete=models.CASCADE, related_name='metrics')
    host = models.GenericIPAddressField(blank=True, null=True)
    app = models.CharField(max_length=8)
    count = models.PositiveIntegerField()
    bytes = models.PositiveIntegerField()


class Statistics(object):
    
    limit_int = 30
    
    def __init__(self, obj):
        self.obj = obj
        self.limit = timezone.now() - timedelta(days=self.limit_int)
        
        self.queryset = self.obj.metrics.filter(created__gte=self.limit)
        
    def daily(self):
        return self.queryset.annotate(ts=TruncDay('created')).values('ts').order_by('ts').annotate(num_events=models.Sum('count'), num_bytes=models.Sum('bytes'))
        
    def by_host(self):
        return self.queryset.values('host').order_by('host').annotate(num_events=models.Sum('count'), num_bytes=models.Sum('bytes'))
        
    def hourly(self):
        return self.queryset.annotate(ts=TruncHour('created')).values('ts').order_by('ts').annotate(num_events=models.Sum('count'), num_bytes=models.Sum('bytes'))
        
    def daily_by_app(self):
        return self.queryset.annotate(ts=TruncDay('created')).values('ts', 'host', 'app').order_by('ts', 'host', 'app').annotate(num_events=models.Sum('count'), num_bytes=models.Sum('bytes'))

    def hourly_by_app(self):
        return self.queryset.annotate(ts=TruncHour('created')).values('ts', 'host', 'app').order_by('ts', 'host', 'app').annotate(num_events=models.Sum('count'), num_bytes=models.Sum('bytes'))
    

class Token(AbstractBaseModel):
    """
    A unique string associated with a user or set of users that permits them to
    furnish logs for ingestion.
    
    """
    id = models.CharField(max_length=255, primary_key=True, default=uuid4, help_text="Token string, as UUID4.")
    
    user = models.ForeignKey('User', on_delete=models.CASCADE, help_text="What user is responsible for the creation of this token?")
    application = models.CharField(max_length=80, default='Unknown', blank=True, help_text="Name of the application (i.e. 'Jenkins') whose logs will be remitted under this token.")
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
        
    def event_count(self, *args, **kwargs):
        return Pulse.objects.filter(token=self).annotate(events=models.Sum('count')).aggregate(models.Sum('events')).get('events__sum', 0)
        
    def trendline(self, *args, **kwargs):
        # Get list of dates
        qs = Pulse.objects.annotate(
            ts=TruncHour('created')
        ).values('ts').distinct().annotate(
            num_events=Coalesce(models.Sum('count', filter=Q(token=self)), 0), num_bytes=Coalesce(models.Sum('bytes', filter=Q(token=self)), 0)
        ).values('ts', 'host', 'num_events', 'num_bytes').order_by('ts')
        
        data = [x['num_events'] for x in qs]
        if len(data) < 30:
            data = [0 for x in range(30-len(data))] + data
        return ','.join([str(x) for x in data])

class User(AbstractUser, AbstractBaseModel):
    
    email = models.EmailField(unique=True)
    
    @property
    def tokens(self):
        return Token.objects.filter(user=self)
        
    
class Host(object):
    
    def __init__(self, ip, *args, **kwargs):
        self.ip = ip
        
    def counts_by_day(self):
        # Get list of dates
        return Pulse.objects.annotate(
            ts=TruncDay('created')
        ).values('ts').distinct().annotate(
            num_events=Coalesce(models.Sum('count', filter=Q(host=self.ip)), 0), num_bytes=Coalesce(models.Sum('bytes', filter=Q(host=self.ip)), 0)
        ).values('ts', 'host', 'num_events', 'num_bytes').order_by('ts')
        
    def counts_by_hour(self):
        # Get list of dates
        return Pulse.objects.annotate(
            ts=TruncHour('created')
        ).values('ts').distinct().annotate(
            num_events=Coalesce(models.Sum('count', filter=Q(host=self.ip)), 0), num_bytes=Coalesce(models.Sum('bytes', filter=Q(host=self.ip)), 0)
        ).values('ts', 'host', 'num_events', 'num_bytes').order_by('ts')
    
    def trendline(self):
        data = [x['num_events'] for x in self.counts_by_hour()]
        if len(data) < 30:
            data = [0 for x in range(30-len(data))] + data
        return data