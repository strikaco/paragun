from django.db import models

# Create your models here.
class BaseEvent(models.Model):
    """
    Base class for Events.
    
    """
    class Meta:
        abstract = True
        
    tags = models.ChoiceField(choices=[[]])
        
    def save(self, *args, **kwargs):
        # Do not allow saving of Event objects
        return None
        
class Alert(BaseEvent):
    class Meta:
        abstract = True
        
class ApplicationState(BaseEvent):
    class Meta:
        abstract = True
        
class Authentication(BaseEvent):
    """
    Authentication events.
    
    """
    class Meta:
        abstract = True
        
    TAG_CHOICES = (
        ('authentication', 'Authentication'),
        ('default', 'Default'),
        ('insecure', 'Cleartext/Insecure'),
        ('privileged', 'Privileged')
    )
        
class Certificate(BaseEvent):
    class Meta:
        abstract = True
        
class ChangeAnalysis(BaseEvent):
    class Meta:
        abstract = True
        
class Database(BaseEvent):
    class Meta:
        abstract = True
        
class DataLossPrevention(BaseEvent):
    class Meta:
        abstract = True
        
class Email(BaseEvent):
    class Meta:
        abstract = True
        
class InterprocessMessage(BaseEvent):
    class Meta:
        abstract = True
        
class IntrusionDetection(BaseEvent):
    class Meta:
        abstract = True
        
class Inventory(BaseEvent):
    class Meta:
        abstract = True
        
class JavaVirtualMachine(BaseEvent):
    class Meta:
        abstract = True
        
class Malware(BaseEvent):
    class Meta:
        abstract = True
        
class NetworkResolution(BaseEvent):
    class Meta:
        abstract = True
        
class NetworkSession(BaseEvent):
    class Meta:
        abstract = True
        
class NetworkTraffic(BaseEvent):
    class Meta:
        abstract = True
        
class Performance(BaseEvent):
    class Meta:
        abstract = True
        
class TicketManagement(BaseEvent):
    class Meta:
        abstract = True
        
class Update(BaseEvent):
    class Meta:
        abstract = True
        
class Vulnerability(BaseEvent):
    class Meta:
        abstract = True
        
class Web(BaseEvent):
    class Meta:
        abstract = True