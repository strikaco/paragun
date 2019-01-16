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
    """
    Displays the generic sales pitch page.
    
    """
    template_name = 'common/index.html'
    
    
class RegisterView(FormView):
    """
    Displays the account registration page.
    
    """
    form_class = RegisterForm
    success_url = reverse_lazy('login')
    template_name = 'registration/register.html'
    
    def form_valid(self, form):
        """
        Most of this could likely be handled by stock Django but it won't emit
        messages confirming success or denial, hence this extension.
        
        Args:
            form (Form): Django form object.
            
        Returns:
            HttpResponse
        
        """
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
    """
    Displays a summary of the current authenticated user's tokens.
    
    """
    model = Token
    page_title = "Dashboard"
    template_name = 'common/dashboard.html'
    paginate_by = 25
    
    def get_queryset(self, **kwargs):
        """
        Restricts tokens available for access to only those owned by user.
        
        Returns:
            tokens (QuerySet): Tokens owned by current user.
            
        """
        return self.request.user.tokens.order_by('-created')
        

class TokenCreateView(LoginRequiredMixin, CreateView):
    """
    Displays the form to allow creation of new tokens.
    
    """
    model = Token
    fields = ['retain', 'notes', 'tags', 'backup_email']
    page_title = "Create Token"
    template_name = 'common/generic_form.html'
    
    def form_valid(self, form):
        """
        Creates token if all fields are valid.
        
        Args:
            form (Form)
            
        Returns:
            HttpResponse
        
        """
        form.instance.user = self.request.user
        
        # Figure out where to redirect user
        self.success_url = self.request.POST.get('next', '')
        if not self.success_url: self.success_url = reverse('dashboard')
        
        super().form_valid(form)
        
        # TODO: Better backend logging re: reasons for failure
        if self.object:
            messages.success(self.request, "Your new token has been created.")
        else:
            messages.error(self.request, "Your token could not be created.")
            
        return HttpResponseRedirect(self.success_url)
    
    
class TokenUpdateView(LoginRequiredMixin, UpdateView):
    """
    Displays form for user to modify or update a token they own.
    
    """
    model = Token
    fields = ['retain', 'notes', 'tags', 'backup_email']
    page_title = "Update Token"
    template_name = 'common/generic_form.html'
    
    def get_queryset(self, **kwargs):
        """
        Restricts tokens available for access to only those owned by user.
        
        Returns:
            tokens (QuerySet): Tokens owned by current user.
            
        """
        return self.request.user.tokens
        
    def form_valid(self, form):
        """
        Updates the current token with new information.
        
        Args:
            form (Form)
            
        Returns:
            HttpResponse
            
        """
        # Figure out where to redirect user
        self.success_url = self.request.POST.get('next', reverse('dashboard'))
        
        super().form_valid(form)
        
        # Reset expiration timer on every update
        self.object.renew()
        
        messages.success(self.request, "Your access token expiration and details have been refreshed.")
        return HttpResponseRedirect(self.success_url)
        
        
class TokenDetailView(LoginRequiredMixin, DetailView):
    """
    Displays detailed information about a particular token.
    
    """
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

        except Exception as e:
            logger.error("Error extracting tokens from payload:")
            logger.error(e, exc_info=True)
            return HttpResponse(e if settings.DEBUG else 'Server Error', status=500)
            
        # Convert them to token objects
        try:
            valid_tokens = tuple(x for x in Token.objects.filter(id__in=reported_tokens) if not x.expired)
            if not valid_tokens:
                logger.debug("No valid tokens reported in metrics update.")
                return HttpResponseBadRequest()
                
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
                        token_str, host, app, count, bytes = row
                    except ValueError as e:
                        logger.error(e, exc_info=True)
                        return HttpResponse(e if settings.DEBUG else 'Server Error', status=500)
                    
                    # Check if token is valid/enabled
                    token = next((x for x in valid_tokens if str(x.id) == token_str), None)
                    if not token:
                        logger.debug('No current/valid token found for %s.' % token_str)
                        continue
                    
                    # Create new pulse
                    Pulse.objects.create(token=token, host=host, app=app, count=count, bytes=bytes)
                    
        except Exception as e:
            logger.error(e, exc_info=True)
            return HttpResponse(e if settings.DEBUG else 'Server Error', status=500)
                
        return HttpResponse('Update Acknowledged', status=200)