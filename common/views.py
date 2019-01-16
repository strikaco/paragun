from common.forms import *
from common.models import *
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, ListView, DetailView, FormView, View
from django.views.generic.edit import CreateView, UpdateView

from time import time
import json
import logging
import re

# Create your views here.
class IndexView(TemplateView):
    template_name = 'common/index.html'
    
    
class RegisterView(FormView):
    form_class = RegisterForm
    success_url = reverse_lazy('login')
    template_name = 'registration/register.html'
    
    def form_valid(self, form):
        logger = logging.getLogger(__name__)
        
        # Get values provided
        username = form.cleaned_data['username']
        password = form.cleaned_data['password1']
        email = form.cleaned_data.get('email', '')
        
        # Create account
        account = User.objects.create_user(username=username, email=email, password=password)
        
        # If unsuccessful, display error message to user
        if not account:
            messages.error(self.request, "Your account could not be created due to a server error.")
            logger.error('Account for %s was not created successfully.' % username)
            
            # Call the Django "form failure" hook
            return self.form_invalid(form)
            
        # Inform user of success
        messages.success(self.request, "Your account was successfully created! Please log in now.")
        
        # Redirect the user to the login page
        return super().form_valid(form)
        
    
class DashboardView(LoginRequiredMixin, ListView):
    model = Token
    page_title = "Dashboard"
    template_name = 'common/dashboard.html'
    paginate_by = 25
    
    def get_queryset(self, **kwargs):
        # Get tokens that belong to this user
        qs = Token.objects.filter(user=self.request.user).order_by('-created')
        return qs
        

class TokenCreateView(LoginRequiredMixin, CreateView):
    model = Token
    fields = ['retain', 'notes', 'tags']
    page_title = "Create Token"
    #success_url = reverse_lazy('dashboard')
    template_name = 'common/generic_form.html'
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        self.success_url = self.request.POST.get('next', '')
        if not self.success_url: self.success_url = reverse('dashboard')
        
        super().form_valid(form)
        
        if self.object:
            messages.success(self.request, "Your new token has been created.")
        else:
            messages.error(self.request, "Your token could not be created.")
            
        return HttpResponseRedirect(self.success_url)
    
class TokenUpdateView(LoginRequiredMixin, UpdateView):
    model = Token
    fields = ['retain', 'notes', 'tags']
    page_title = "Update Token"
    template_name = 'common/generic_form.html'
    
    def get_queryset(self, **kwargs):
        # Get only those tokens that the current user owns
        return self.request.user.tokens
        
    def form_valid(self, form):
        self.success_url = self.request.POST.get('next', reverse('dashboard'))
        
        super().form_valid(form)
        self.object.renew()
        messages.success(self.request, "Your access token expiration and details have been refreshed.")
        return HttpResponseRedirect(self.success_url)
        
class TokenDetailView(LoginRequiredMixin, DetailView):
    model = Token
    page_title = "Token Detail"
    template_name = 'common/token_detail.html'


class TokenDumpView(View):
    
    def get(self, request, *args, **kwargs):
        """
        Return a list of valid tokens in rsyslog lookup table format (JSON).
        
        Returns:
            table (JSON): Token validity lookup table.
        
        """
        # TODO: Check for API key
        
        # Get all valid tokens
        tokens = Token.objects.filter(expires__gt=timezone.now()).order_by('id').iterator()
        
        # Build the lookup table
        table = { 
            "version" : 1,
            "nomatch" : "0",
            "type" : "string",
            "table" : [{"index" : str(token.id).lower(), "value" : "1"} for token in tokens]
        }
        
        # Return it
        return JsonResponse(table)
        
        
class TokenRetentionView(View):
    
    def get(self, request, *args, **kwargs):
        """
        Returns a lookup table of the retention period (in seconds, as int) for 
        all logs by token.
        
        Returns:
            table (JSON): Log retention lookup table.
        
        """
        # TODO: Check for API key
        
        # Get all valid tokens
        tokens = Token.objects.filter(expires__gt=timezone.now()).order_by('id').iterator()
        
        # Build the lookup table
        table = { "version" : 1,
            "nomatch" : 365,
            "type" : "string",
            "table" : [{"index" : token.id, "value" : token.retain * 86400 } for token in tokens]
        }
        
        # Return it
        return JsonResponse(table)
        
        
@method_decorator(csrf_exempt, name='dispatch')
class PulseUpdateView(View):
    
    def post(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        
        # TODO: Check for API key
        
        # Get payload
        try:
            data = (x.strip() for x in request.body.decode('utf-8').splitlines() if x.strip() != '')
            # Split on any whitespace
            rows = [re.split('\t+|\s{2,}', x) for x in data]
        except Exception as e:
            logger.error("Error getting payload:")
            logger.error(e, exc_info=True)
            return HttpResponse(e if settings.DEBUG else 'Server Error', status=500)
        
        # Get a list of reported tokens from this parcel
        try:
            reported_tokens = set()
            for row in rows:
                reported_tokens.add(row[0].strip())
            logger.info("Found: %s" % reported_tokens)
        except Exception as e:
            logger.error("Error extracting tokens from payload:")
            logger.error(e, exc_info=True)
            return HttpResponse(e if settings.DEBUG else 'Server Error', status=500)
            
        # Convert them to token objects
        try:
            valid_tokens = tuple(x for x in Token.objects.filter(id__in=reported_tokens) if not x.expired)
            if not valid_tokens:
                return HttpResponseBadRequest("No valid tokens were found in the metrics payload.\n%s" % reported_tokens)
        except Exception as e:
            logger.error("Error converting token strings to Token objects:")
            logger.error(e, exc_info=True)
            return HttpResponse(e if settings.DEBUG else 'Server Error', status=500)
        
        # Update metrics for each token
        try:
            with transaction.atomic():
                for row in rows:
                    row = [x.strip() for x in row]
                    
                    try:
                        token_str, app, count, bytes = row
                    except ValueError as e:
                        logger.error(e, exc_info=True)
                        return HttpResponse(e if settings.DEBUG else 'Server Error', status=500)
                    
                    # Check if token is valid/enabled
                    token = next((x for x in valid_tokens if str(x.id) == token_str), None)
                    if not token:
                        logger.debug('No current/valid token found for %s.' % token_str)
                        continue
                    
                    # Create new pulse
                    Pulse.objects.create(token=token, app=app, count=count, bytes=bytes)
                    
        except Exception as e:
            logger.error(e, exc_info=True)
            return HttpResponse(e if settings.DEBUG else 'Server Error', status=500)
                
        return HttpResponse('Update Acknowledged', status=200)