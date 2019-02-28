from django.test import TestCase
from parsing.models import *

# Create your tests here.
class ParsingTest(TestCase):
    
    def setUp(self):
        # Create a service
        self.service = Service.objects.create(key='ssh')
        
        # Create some samples and assertions
        samples = (
            {'raw': 'Aug  1 18:27:46 knight sshd[20325]: Failed password for illegal user test from 218.49.183.17 port 48849 ssh2', 'user': 'test', 'src_ip': '218.49.183.17'},
        )
        
        for sample in samples:
            obj = Sample.objects.create(service=self.service, value=sample.pop('raw'))
            for k,v in sample.items():
                field = Field.objects.get_or_create(key=k)[0]
                obj.assertions.create(key=field, value=v)
        
        # Create some parsers
        parsers = (
            {'key': 'src_ip', 'value': 'from ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})'},
            {'key': 'user', 'value': 'user ([a-zA-Z0-9\.\-]+) from'},
        )
        
        for parser in parsers:
            field = Field.objects.get_or_create(key=parser['key'])[0]
            Parser.objects.create(service=self.service, enabled=True, field=field, value=parser['value'])
            
    def test_service_validation(self):
        self.service.test()