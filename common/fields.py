from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from netaddr import EUI

class ActionField(forms.ChoiceField):
    def __init__(self, *args, **kwargs):
        
        kwargs['max_length'] = kwargs.pop('max_length', 16)
        kwargs['help_text'] = kwargs.pop('help_text', "Action taken by the reporting device.")

        if not kwargs.get('choices'):
            kwargs['choices'] = (
                ('acl_modified', 'acl_modified'),
                ('accepted', 'accepted'), 
                ('added', 'added'), 
                ('blocked', 'blocked'),
                ('cleared', 'cleared'), 
                ('created', 'created'),
                ('deferred', 'deferred'),
                ('deleted', 'deleted'), 
                ('denied', 'denied'), 
                ('delivered', 'delivered'),
                ('failure', 'failure'),
                ('modified', 'modified'), 
                ('read', 'read'), 
                ('rejected', 'rejected'), 
                ('stopped', 'stopped'),
                ('success', 'success')
                ('teardown', 'teardown'),
                ('updated', 'updated'),
            )
            
        super().__init__(*args, **kwargs)
        
class ApplicationField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.pop('max_length', 16)
        kwargs['help_text'] = kwargs.pop('help_text', "The application involved in the event.")
        
        super().__init__(*args, **kwargs)
        
class BusinessUnitField(forms.ChoiceField):
    def __init__(self, *args, **kwargs):

        kwargs['help_text'] = kwargs.pop('help_text', "Business unit associated with the event or an artifact thereof.")

        if not kwargs.get('choices'):
            kwargs['choices'] = (
                ('corporate', 'corporate'),
                ('commercial', 'commercial'), 
                ('government', 'government'),
            )
            
        super().__init__(*args, **kwargs)
        
class CategoryField(forms.ChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = kwargs.pop('choices', [[]])
        kwargs['help_text'] = kwargs.pop('help_text', "Generic categorical classification for the event.")
        super().__init__(*args, **kwargs)
        
class DescriptionField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.pop('max_length', 160)
        kwargs['help_text'] = kwargs.pop('help_text', "Generic description of the event.")
        super().__init__(*args, **kwargs)
        
class DeviceField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.pop('max_length', 64)
        kwargs['help_text'] = kwargs.pop('help_text', "Name of a device associated with an event or artifact.")
        super().__init__(*args, **kwargs)
        
class DirectionField(forms.ChoiceField):
    def __init__(self, *args, **kwargs):
        
        kwargs['max_length'] = kwargs.pop('max_length', 16)
        kwargs['help_text'] = kwargs.pop('help_text', "A direction of travel.")

        if not kwargs.get('choices'):
            kwargs['choices'] = (
                ('inbound', 'inbound'),
                ('outbound', 'outbound'),
            )
            
        super().__init__(*args, **kwargs)
        
class DomainField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.pop('max_length', 255)
        kwargs['help_text'] = kwargs.pop('help_text', "Active Directory domain associated with an event.")
        super().__init__(*args, **kwargs)
        
class HashField(forms.RegexField):
    def __init__(self, *args, **kwargs):
        kwargs['regex'] = kwargs.pop('regex', '([a-fA-F0-9]+)')
        super().__init__(*args, **kwargs)
        
class HostnameField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.pop('max_length', 63)
        kwargs['help_text'] = kwargs.pop('help_text', "Hostname of the source or destination of the event.")
        super().__init__(*args, **kwargs)
        
class HttpMethodField(forms.ChoiceField):
    def __init__(self, *args, **kwargs):
        
        kwargs['max_length'] = kwargs.pop('max_length', 8)
        kwargs['help_text'] = kwargs.pop('help_text', "The HTTP method used in the request.")

        kwargs['choices'] = kwargs.pop('choices', (
            ('GET', 'GET'), 
            ('PUT', 'PUT'), 
            ('POST', 'POST'), 
            ('DELETE', 'DELETE'), 
            ('HEAD', 'HEAD'), 
            ('OPTIONS', 'OPTIONS'), 
            ('CONNECT', 'CONNECT'), 
            ('TRACE', 'TRACE')
        ))
            
        super().__init__(*args, **kwargs)
        
class HttpStatusField(forms.IntegerField):
    def __init__(self, *args, **kwargs):
        kwargs['help_text'] = kwargs.pop('help_text', "HTTP status code.")
        kwargs['validators'] = kwargs.pop('validators', [
            MinValueValidator(100),
            MaxValueValidator(600)
        ])
        super().__init__(*args, **kwargs)

class MacAddressField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.pop('max_length', 16)
        kwargs['help_text'] = kwargs.pop('help_text', "A MAC (media access control) address associated with the resource, such as 06:10:9f:eb:8f:14. Note: Always force lower case on this field. Note: Always use colons instead of dashes, spaces, or no separator.")
        super().__init__(*args, **kwargs)
        
    def clean(self, *args, **kwargs):
        data = super().clean(*args, **kwargs)
        
        try:
            # Make sure it's valid MAC
            mac = EUI(data).strip()
            # Replace hyphens with colons; force lowercase
            mac = str(mac).replace('-', ':').lower()
            return mac
            
        except:
            return ''
        
class PathField(forms.RegexField):
    def __init__(self, *args, **kwargs):
        kwargs['regex'] = kwargs.pop('regex', '((?:[^/]*/)*)(.*)')
        kwargs['help_text'] = kwargs.pop('help_text', "Filesystem path to a resource.")
        super().__init__(*args, **kwargs)
        
class PortField(forms.IntegerField):
    def __init__(self, *args, **kwargs):
        kwargs['help_text'] = kwargs.pop('help_text', "TCP or UDP port associated with a connection.")
        kwargs['validators'] = kwargs.pop('validators', [
            MinValueValidator(1),
            MaxValueValidator(65535)
        ])
        super().__init__(*args, **kwargs)
        
class PriorityField(forms.IntegerField):
    def __init__(self, *args, **kwargs):
        kwargs['initial'] = kwargs.pop('initial', 50)
        kwargs['help_text'] = kwargs.pop('help_text', "Priority of a given artifact or event.")
        kwargs['validators'] = kwargs.pop('validators', [
            MinValueValidator(0),
            MaxValueValidator(100)
        ])
        super().__init__(*args, **kwargs)
        
class ProtocolField(forms.CharField):
    def __init__(self, *args, **kwargs):
        
        kwargs['max_length'] = kwargs.pop('max_length', 8)
        kwargs['help_text'] = kwargs.pop('help_text', "Protocol of a given transmission.")

        super().__init__(*args, **kwargs)
        
class SeverityField(forms.ChoiceField):
    def __init__(self, *args, **kwargs):
        
        kwargs['max_length'] = kwargs.pop('max_length', 16)
        kwargs['help_text'] = kwargs.pop('help_text', "The severity associated with an artifact or event.")

        kwargs['choices'] = kwargs.pop('choices', (
            ('critical', 'critical'), 
            ('high', 'high'), 
            ('medium', 'medium'), 
            ('low', 'low'),
            ('info', 'info'),
            ('debug', 'debug')
        ))
            
        super().__init__(*args, **kwargs)
        
class StatusField(forms.ChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.pop('max_length', 16)
        kwargs['help_text'] = kwargs.pop('help_text', "The status associated with an artifact or event.")

        kwargs['choices'] = kwargs.pop('choices', (
            ('available', 'available'), ('installed', 'installed'), ('invalid', 'invalid'), ("'restart required'", "'restart required'"),
            ('critical', 'critical'), ('started', 'started'), ('stopped', 'stopped'), ('warning', 'warning'),
            ('success', 'success'), ('failure', 'failure')
        ))
            
        super().__init__(*args, **kwargs)
        
class TransportField(forms.ChoiceField):
    def __init__(self, *args, **kwargs):
        
        kwargs['max_length'] = kwargs.pop('max_length', 8)
        kwargs['help_text'] = kwargs.pop('help_text', "The transport protocol used by the network resolution event.")

        kwargs['choices'] = kwargs.pop('choices', (
            ('tcp', 'tcp'), 
            ('udp', 'udp'), 
            ('icmp', 'icmp')
        ))
            
        super().__init__(*args, **kwargs)