from common.models import *
from common.views import *
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

# Create your tests here.
class PulseUpdateViewTest(TestCase):
  
    def setUp(self):
        self.user1 = get_user_model().objects.create_user('Chevy Chase', 'chevy@chase.com', 'chevyspassword')
        self.token = Token.objects.create(id='3f125cd7-fd46-4e37-a88e-610db52c1562', user=self.user1)
        
    def test_post(self):
        "Receive and ingest a metrics update parcel."
        data = {
            'aggs': """
3f125cd7-fd46-4e37-a88e-610db52c1562    cron    7       723
3f125cd7-fd46-4e37-a88e-610db52c1562    sshd    3       351
"""
        }
        
        data = data['aggs']
        
        response = self.client.post(reverse('pulse-update'), data, content_type="application/octet-stream")
        self.assertTrue(response.status_code == 200, 'Posting update should have yielded a 200 (returned %s).' % response.status_code)
        self.assertEqual(Pulse.objects.all().count(), 2)