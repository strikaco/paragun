from django.test import TestCase
from common.forms import *
from mock import MagicMock

# Create your tests here.

class TemplateTests(TestCase):
    """
    This should test to make sure models are mapping terms properly, doing
    appropriate lookups and fields/validation are working correctly.
    """
    def test_base(self):
        "Make sure BaseEvent functions properly."
        data = dict(
            index = 'stuff_2018-01-01',
            host_ip = '192.168.1.1',
            raw = '[Wed Oct 11 14:32:52 2000] [error] [client 127.0.0.1] client denied by server configuration: /export/home/live/ap/htdocs/test',
        )
        event = BaseForm(data)
        self.assertTrue(event.is_valid())
        
        data = event.cleaned_data
        
        # Make sure host IP was moved correctly
        self.assertTrue(data['host_ip'])
        
        # Make sure timestamp populated
        self.assertTrue(data['timestamp'])
        
        # Make sure timestamp was dissected
        fields = (
            'date_hour',
            'date_mday',
            'date_minute',
            'date_month',
            'date_second',
            'date_wday',
            'date_year',
        )
        for field in fields:
            self.assertTrue(data[field])
            
        # Make sure linecount and punct were calculated
        self.assertTrue(data['punct'])
        self.assertTrue(data['linecount'])
        
    def test_bytes_form(self):
        event = BytesForm(dict(
            bytes_in = 10,
            bytes_out = 10
        ))
        
        self.assertTrue(event.is_valid())
        
        data = event.cleaned_data
        self.assertEqual(data['bytes'], 20)
        
    def test_file_form(self):
        event = FileForm(dict(
            file_path = '/var/log/xyz/10032008.log'    
        ))
        self.assertTrue(event.is_valid())
        data = event.cleaned_data
        
        self.assertTrue(data['file_name'])
        
    def test_network_form(self):
        event = NetworkForm(dict(
            ip='173.199.120.251'
        ))
        import pudb;pudb.set_trace()
        self.assertTrue(event.is_valid(), event.errors)
        print(event.cleaned_data)
        
    def test_severity_form(self):
        event = SeverityForm(dict(
            severity = 'informational',
            severity_id = 10,
        ))
        self.assertTrue(event.is_valid())
        
        event = SeverityForm(dict(
            severity = 'nothing',
            severity_id = 9000,
        ))
        self.assertFalse(event.is_valid())
        
    def test_url_form(self):
        event = URLForm(dict(
            url = 'http://www.cwi.nl:80/%7Eguido/Python.html'
        ))
        self.assertTrue(event.is_valid())
        cleaned = {k:v for k,v in event.cleaned_data.items() if v}
        self.assertEqual(len(cleaned.keys()), 7)
        
    def test_user_form(self):
        event = UserForm(dict(
            user = 'hsimpson'    
        ))
        event.get_ldap = MagicMock()
        event.get_ldap.return_value = {'loginShell': [b'/bin/bash'], 'uid': [b'hsimpson'], 'employeeType': [b'Unknown'], 'objectClass': [], 'mail': [b'homer.simpson@example.com'], 'uidNumber': [b'4444444444'], 'orgSponsorDn': [b'o=example,ou=Organizations,dc=example,dc=com'], 'homeDirectory': [b'/home/hsimpson'], 'cn': [b'Homer Simpson'], 'gidNumber': [b'666'], 'sn': [b'Simpson'], 'givenName': [b'Homer']}
        
        self.assertTrue(event.is_valid())
        self.assertTrue(event['user'])
        self.assertTrue(event['user_email'])