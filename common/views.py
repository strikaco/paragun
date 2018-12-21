from common.forms import *
from common.models import *
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, ListView, FormView, View
from django.views.generic.edit import CreateView, UpdateView
import logging

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
    fields = ['notes', 'tags']
    page_title = "Create Token"
    success_url = reverse_lazy('dashboard')
    template_name = 'common/generic_form.html'
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        
        super().form_valid(form)
        
        if self.object:
            messages.success(self.request, "Your new token has been created.")
        else:
            messages.error(self.request, "Your token could not be created.")
            
        return HttpResponseRedirect(self.success_url)
    
class TokenUpdateView(LoginRequiredMixin, UpdateView):
    model = Token
    fields = ['notes', 'tags']
    page_title = "Update Token"
    success_url = reverse_lazy('dashboard')
    template_name = 'common/generic_form.html'
    
    def get_queryset(self, **kwargs):
        # Get only those tokens that the current user owns
        return self.request.user.tokens
        
    def form_valid(self, form):
        super().form_valid(form)
        messages.success(self.request, "Your access token expiration and details have been refreshed.")
        return HttpResponseRedirect(self.success_url)
    
        
@method_decorator(csrf_exempt, name='dispatch')
class PulseUpdateView(View):
    
    def post(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        
        # TODO: Check for API key
        
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