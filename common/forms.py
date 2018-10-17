from django import forms
from django.forms import formset_factory
from django.utils import timezone
from django.utils.text import slugify
from netaddr import IPAddress
from common import fields
from common.geoip import GeoIP
from common.utilities import ldap_query
from urllib.parse import urlparse
import calendar
import re

# Constants
DEFAULT_ACTION_LENGTH = 16
DEFAULT_APP_LENGTH = 64
DEFAULT_CHAR_LENGTH = 32
DEFAULT_HOSTNAME_LENGTH = 253
DEFAULT_PATH_LENGTH = 1024
DEFAULT_SUBJECT_LENGTH = 1024
DEFAULT_USERNAME_LENGTH = 64

GEOIP = GeoIP()

class BaseForm(forms.Form):
    
    host_dns = forms.CharField(required=False, max_length=DEFAULT_HOSTNAME_LENGTH, help_text="The host name of the network device that generated an event.")
    host_ip = forms.GenericIPAddressField(required=False, help_text="The IP address of the network device that generated an event.")
    
    index = forms.CharField(required=False, max_length=DEFAULT_CHAR_LENGTH, help_text="The storage index for the event.")
    raw = forms.CharField(required=False, help_text="Contains the original raw data of an event.")
    linecount = forms.IntegerField(required=False, help_text="Number of lines comprising the event.")
    punct = forms.CharField(required=False, max_length=30, help_text="A pattern of the first N characters of the first line of an event with which it is associated.")
    
    source = forms.CharField(required=False, max_length=1024, help_text="Contains the name of the file, stream, or other input from which the event originates.")
    source_type = forms.CharField(required=False, max_length=DEFAULT_CHAR_LENGTH, help_text="Identifies the data structure of an event. Determines how ClownStrike Enterprise formats the data during indexing.")
    
    timestamp_in = forms.DateTimeField(required=False, help_text="Contains the timestamp value from the time of processing.")
    timestamp = forms.DateTimeField(required=False, help_text="Contains an event's timestamp value.")
    
    date_hour = forms.IntegerField(required=False, help_text="Contains the value of the hour in which an event occurred (range: 0-23).")
    date_mday = forms.IntegerField(required=False, help_text="Contains the value of the day of the month on which an event occurred (range: 1-31).")
    date_minute = forms.IntegerField(required=False, help_text="Contains the value of the minute in which an event occurred (range: 0-59).")
    date_month = forms.IntegerField(required=False, help_text="Contains the value of the month in which an event occurred (range: 1-12).")
    date_second = forms.IntegerField(required=False, help_text="Contains the value of the second in which an event occurred (range: 0-59).")
    date_wday = forms.CharField(required=False, max_length=DEFAULT_CHAR_LENGTH, help_text="Contains the day of week in which an event occurred.")
    date_year = forms.IntegerField(required=False, help_text="Contains the year in which an event occurred.")
    
    app = fields.ApplicationField(required=False, help_text="The app recording the data, such as IIS, Squid, or Bluecoat.")
    category = fields.CategoryField(required=False)
    tag = forms.CharField(required=False, help_text="This automatically generated field is used to access tags from within data models. Do not define extractions for this field when writing add-ons.")
    
    def clean(self):
        cleaned = {k:v.strip() for k,v in super().clean().items() if v not in ('', None)}
        
        # Make sure timestamp was recorded
        cleaned['timestamp_in'] = timezone.now()
        if not cleaned.get('timestamp'): cleaned['timestamp'] = cleaned['timestamp_in']
        
        # Dissect timestamp
        self.dissect_timestamp(cleaned)
        
        # Generate index name if not provided
        if not cleaned.get('index'):
            date = timezone.now().strftime('%Y-%m-%d')
            cleaned['index'] = 'logs_%s' % date
            
        # Calculate linecount and punctstring
        lines = cleaned['raw'].splitlines()
        
        # Set linecount
        cleaned['linecount'] = len(lines)
        
        # Set punct string
        cleaned['punct'] = ''.join(re.findall('([^a-zA-Z0-9\s]+)', lines[0]))
        
        return {k:str(v) for k,v in cleaned.items() if v or v == 0}
        
    def dissect_timestamp(self, data):
        # Dissect the timestamp into its component parts
        ts = data['timestamp']
        data['date_hour'] = ts.hour
        data['date_mday'] = ts.day
        data['date_minute'] = ts.minute
        data['date_month'] = ts.month
        data['date_second'] = ts.second
        data['date_wday'] = calendar.day_name[ts.weekday()]
        data['date_year'] = ts.year
    
    def get_atlassian(self, uid, *args, **kwargs):
        # Get email address from Atlassian user ID
        pass
    
    def get_ipam(self, ip, *args, **kwargs):
        # Do ipam lookup for the given IP
        pass
    
class BytesForm(forms.Form):
        
    bytes = forms.IntegerField(required=False, help_text="The total number of bytes transferred (bytes_in + bytes_out).")
    bytes_in = forms.IntegerField(required=False, help_text="The number of inbound bytes transferred.")
    bytes_out = forms.IntegerField(required=False, help_text="The number of outbound bytes transferred.")
    
    def clean(self):
        """
        Calculate total if one wasn't provided.
        """
        cleaned = super().clean()
        if (cleaned.get('bytes_in') or cleaned.get('bytes_out')) and not cleaned.get('bytes'):
            cleaned['bytes'] = cleaned.get('bytes_in', 0) + cleaned.get('bytes_out', 0)
            
        return cleaned
        
class FileForm(forms.Form):
        
    file_path = fields.PathField(required=False, help_text="The full file path of the file.")
    file_hash = fields.HashField(required=False, help_text="The hash for the file, if available.")
    file_name = forms.CharField(max_length=2048, required=False, help_text="The name of the file, if available.")
    file_size = forms.IntegerField(required=False, help_text="The size of the file, in bytes.")
    
    def clean(self):
        """
        Get filename if not specified.
        """
        cleaned = super().clean()
        if cleaned.get('file_path') and not cleaned.get('file_name'):
            # Get filename
            filename = cleaned['file_path'].split('/')[-1].strip().lower()
            if '.' in filename:
                cleaned['file_name'] = filename
            
        return cleaned
        
class NetworkForm(forms.Form):
    
    mac = fields.MacAddressField(required=False, help_text="The source TCP/IP layer 2 Media Access Control (MAC) address of a packet's source, such as 06:10:9f:eb:8f:14. Note: Always force lower case on this field. Note: Always use colons instead of dashes, spaces, or no separator.")
    ip = forms.GenericIPAddressField(required=False, help_text="The ip address of the device.")
    port = fields.PortField(required=False, help_text="Network port communicated to by the process, such as 53.")
    ip_private = forms.BooleanField(required=False, help_text="Is this a private network address?")
    dns = fields.DomainField(required=False, help_text="The domain name system address of a network session event.")
    
    cidr = forms.CharField(required=False, help_text="The CIDR block of the device.")
    isp = forms.CharField(required=False, help_text="The ISP address of the device.")
    iso = forms.CharField(required=False, help_text="The ISO country code of the device's location.")
    lat = forms.DecimalField(required=False, max_digits=9, decimal_places=6)
    lon = forms.DecimalField(required=False, max_digits=9, decimal_places=6)
    
    bunit = fields.BusinessUnitField(required=False, help_text="The business unit associated with the source. This field is automatically provided by asset and identity correlation features of applications like ClownStrike Enterprise Security. Do not define extractions for this field when writing add-ons.")
    category = fields.CategoryField(required=False, help_text="The category of the source. This field is automatically provided by asset and identity correlation features of applications like ClownStrike Enterprise Security. Do not define extractions for this field when writing add-ons.")
    priority = fields.PriorityField(required=False, help_text="The priority of the source. This field is automatically provided by asset and identity correlation features of applications like ClownStrike Enterprise Security. Do not define extractions for this field when writing add-ons.")
    nt_domain = fields.DomainField(required=False, help_text="The name of the Active Directory used by the authentication target, if applicable.")
    nt_host = fields.HostnameField(required=False, help_text="The NetBIOS name of the client initializing a network session.")
    interface = forms.CharField(max_length=64, required=False, help_text="The interface that is listening remotely or receiving packets locally. Can also be referred to as the 'egress interface.'")
    translated_ip = forms.GenericIPAddressField(required=False, help_text="The NATed IPv4 or IPv6 address to which a packet has been sent.")
    translated_port = fields.PortField(required=False, help_text="The NATed port to which a packet has been sent. Note: Do not translate the values of this field to strings (tcp/80 is 80, not http).")
    zone = forms.CharField(max_length=64, required=False, help_text="The network zone of the source.")
    
    def clean(self):
        """
        Do lookups for IP metrics.
        """
        cleaned = super().clean()
        ip = IPAddress(cleaned['ip'])
        ip_str = str(ip)
        
        # Is it private?
        private = ip.is_private()
        loopback = ip.is_loopback()
        multicast = ip.is_multicast()
        if private or loopback or multicast:
            cleaned['ip_private'] = True
            
            # Do DHCP lookup
            timestamp = cleaned.get('timestamp', timezone.now())
            cleaned['nt_host'] = self.get_dhcp(ip_str, timestamp)
            
            # Do DNS lookup
            cleaned['dns'] = self.get_dns(ip_str)
            
        else:
            cleaned['ip_private'] = False
            
            # Do GeoIP lookup
            geo = self.get_geoip(ip_str)
            cleaned['lat'] = geo.get('latitude')
            cleaned['lon'] = geo.get('longitude')
            cleaned['isp'] = geo.get('isp')
            cleaned['cidr'] = geo.get('cidr')
            cleaned['iso'] = geo.get('country')
            if geo.get('country') and geo.get('region'):
                cleaned['iso_local'] = '%s-%s' % (geo.get('country'), geo.get('region'))
            
        return cleaned
    
    def get_geoip(self, ip, *args, **kwargs):
        # Get geoip data for the given IP
        result = GEOIP.city(ip)
        result.update(GEOIP.isp(ip))
        return result
    
    def get_dns(self, ip, *args, **kwargs):
        # Do reverse dns lookup for the given IP (if internal)
        return ''
    
    def get_dhcp(self, ip, timestamp, *args, **kwargs):
        # Do reverse dhcp lookup for the given IP (if internal)
        return ''
    
class SeverityForm(forms.Form):
        
    severity = forms.ChoiceField(required=False, choices=(('critical', 'critical'), ('high', 'high'), ('medium', 'medium'), ('low', 'low'), ('informational', 'informational')), help_text="The severity of a message.Note: This field is a string. Please use a severity_id field for severity ID fields that are integer data types. Specific values are required. Please use vendor_severity for the vendor's own human-readable strings (such as Good, Bad, Really Bad, and so on).")
    severity_id = forms.IntegerField(required=False, help_text="A numeric severity indicator for a message.")
    
class TransportForm(forms.Form):
        
    transport = forms.SlugField(max_length=8, required=False, help_text="The network ports listened to by the application process, such as tcp, udp, etc.")
    
class URLForm(forms.Form):
        
    url = forms.URLField(required=False, help_text="The URL of the requested HTTP resource.")
    url_length = forms.IntegerField(required=False, help_text="The length of the URL.")
    url_scheme = forms.SlugField(max_length=16, required=False, help_text="URL scheme specifier.")
    url_domain = forms.CharField(max_length=254, required=False)
    url_netloc = forms.CharField(required=False, help_text="Network location.")
    url_path = fields.PathField(required=False, help_text="Hierarchical path.")
    url_params = forms.CharField(max_length=254, required=False)
    url_query = forms.CharField(max_length=254, required=False)
    url_fragment = forms.CharField(max_length=254, required=False)
    url_username = forms.CharField(max_length=254, required=False)
    url_password = forms.CharField(max_length=254, required=False)
    url_hostname = forms.CharField(max_length=254, required=False)
    url_port = forms.IntegerField(required=False)
    
    def clean(self):
        cleaned = super().clean()
        url = cleaned['url'] = cleaned.pop('url', '').strip().lower()
        if not url: return cleaned
        
        # Get length of URL
        cleaned['url_length'] = len(url)
        
        # Parse out features
        parsed = urlparse(url)
        cleaned['url_netloc'] = parsed.netloc
        cleaned['url_path'] = parsed.path
        cleaned['url_params'] = parsed.params
        cleaned['url_query'] = parsed.query
        cleaned['url_fragment'] = parsed.fragment
        cleaned['url_username'] = parsed.username
        cleaned['url_password'] = parsed.password
        cleaned['url_hostname'] = parsed.hostname
        cleaned['url_domain'] = '.'.join(parsed.hostname.split('.')[-2:])
        cleaned['url_post'] = parsed.port
        
        return cleaned
        
class UserForm(forms.Form):
        
    user_id = forms.IntegerField(required=False, help_text="The user identification for a locally defined account.")
    user = forms.CharField(required=False, help_text="The user account in question.")
    user_nt_domain = fields.DomainField(required=False, help_text="The NT domain the username belongs to.")
    user_email = forms.EmailField(required=False, help_text="The email address associated with the user account.")
    user_bunit = fields.BusinessUnitField(required=False, help_text="These fields are automatically provided by asset and identity correlation features of applications like ClownStrike Enterprise Security. Do not define extractions for these fields when writing add-ons.")
    user_category = fields.CategoryField(required=False, help_text="Description not available.")
    user_priority = fields.PriorityField(required=False, help_text="Description not available.")
    
    def clean(self):
        cleaned = super().clean()
        
        if not cleaned.get('user') and cleaned.get('user_email'):
            ldap = self.get_ldap('mail', cleaned.get('user_email'))
            cleaned['user'] = ldap.get('uid', [''])[0]
        elif cleaned.get('user') and not cleaned.get('user_email'):
            ldap = self.get_ldap('uid', cleaned.get('user'))
            cleaned['user_email'] = ldap.get('mail', [''])[0]
        
        return cleaned
        
    def get_ldap(self, key, value):
        # Do ldap query for the given artifact
        return ldap_query(key, value)
        
class VendorForm(forms.Form):
    
    vendor_product = forms.CharField(required=False, help_text="The vendor and product or service that detected the change. This field can be automatically populated by vendor and product fields in your data.")
    product_version = forms.CharField(required=False, help_text="The product version of the product.")
    
# --- Composite Forms ---
class AlertForm(SeverityForm, BaseForm):
    
    body = forms.CharField(required=False, help_text="The body of a message.")
    subject = forms.CharField(required=False, help_text="The message subject.")
    type = forms.ChoiceField(choices=(('alarm', 'alarm'), ('alert', 'alert'), ('event', 'event'), ('task', 'task')), help_text="The message type.")
    
