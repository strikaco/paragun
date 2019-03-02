from django.test import TestCase
from parsing.models import *

# Create your tests here.
class ParsingTest(TestCase):
    
    def setUp(self):
        # Create a service
        self.service = Service.objects.create(key='ssh')
        self.service2 = Service.objects.create(key='ufw')
        
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
            # ssh
            {'key': 'src_ip', 'value': 'from ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})', 'service': self.service},
            {'key': 'user', 'value': 'user ([a-zA-Z0-9\.\-]+) from', 'service': self.service},
            {'key': 'user', 'value': 'username ([a-zA-Z0-9\.\-]+)', 'priority': 75, 'service': self.service},
            {'key': 'user', 'value': 'user is ([a-zA-Z0-9\.\-]+)', 'priority': 100, 'service': self.service},
            
            # ufw
            {'key': 'src_ip', 'value': 'from ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})', 'service': self.service2},
            {'key': 'dst_ip', 'value': 'to ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})', 'service': self.service2},
        )
        
        for parser in parsers:
            parser['field'] = Field.objects.get_or_create(key=parser.pop('key'))[0]
            Parser.objects.create(enabled=True, **parser)
            
    def test_service_validation(self):
        "All demo samples should pass validation."
        test_result = self.service.test()
        
        bucket = []
        if not test_result:
            # Find which samples and assertions failed
            failed_samples = Sample.objects.enabled().filter(status=False)
            for failure in failed_samples:
                report = {'log': failure.value}
                failed_assertions = failure.assertions.enabled().filter(status=False)
                for assertion in failed_assertions:
                    report[assertion.key.key] = assertion.value
                bucket.append(report)
                
        self.assertTrue(test_result, bucket)
        
    def test_get_parser_map(self):
        from pprint import PrettyPrinter
        pp = PrettyPrinter(indent=4)
        pp.pprint(Service.get_parser_map())