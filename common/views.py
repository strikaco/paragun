from common.models import *
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView, ListView, View
import logging

# Create your views here.
class IndexView(TemplateView):
    template_name = 'common/index.html'
    
class RegisterView(TemplateView):
    template_name = 'common/base.html'
    
class DashboardView(LoginRequiredMixin, ListView):
    model = Token
    page_title = "Dashboard"
    template_name = 'common/dashboard.html'
    
    def get_queryset(self, **kwargs):
        return self.request.user.tokens
        
class PulseUpdateView(View):
    
    def post(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        
        # TODO: Check for API key
        import pudb;pudb.set_trace()
        
        # Get payload
        data = [x.strip() for x in request.POST.get('data', '').strip().split('\n') if x.strip() != '']
        rows = [x.split('    ') for x in data]
        
        # Get a list of reported tokens from this parcel
        reported_tokens = set()
        for row in rows:
            reported_tokens.add(row[0])
            
        # Convert them to token objects
        valid_tokens = tuple(x for x in Token.objects.enabled().filter(value__in=reported_tokens) if not x.expired)
        
        # Update metrics for each token
        with transaction.atomic():
            for row in rows:
                row = [x.strip() for x in row]
                
                try:
                    token_str, app, count, bytes = row
                except ValueError as e:
                    logger.error(e, exc_info=True)
                    return HttpResponse(e if settings.DEBUG else 'Server Error', status=500)
                
                # Check if token is valid/enabled
                token = next((x for x in valid_tokens if x.value == token_str), None)
                if not token:
                    logger.debug('No current/valid token found for %s.' % token_str)
                    continue
                
                # Create new pulse
                Pulse.objects.create(token=token, app=app, count=count, bytes=bytes)
                
        return HttpResponse(status=200)