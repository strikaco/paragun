from common.models import *
from common.views import *
from django.test import TestCase
from django.urls import reverse

# Create your tests here.
class PulseUpdateViewTest(TestCase):
  
    def setUp(self):
        Token.objects.create(value='3f125cd7-fd46-4e37-a88e-610db52c1562')
    
    def test_post(self):
        "Receive and ingest a metrics update parcel."
        data = {
            'data': """
3f125cd7-fd46-4e37-a88e-610db52c1562    cron    7       723
3f125cd7-fd46-4e37-a88e-610db52c1562    sshd    3       351
"""
        }
        
        response = self.client.post(reverse('pulse-update'), data)
        self.assertTrue(response.ok, 'Posting update should have yielded a 200 (returned %s).' % response.status_code)