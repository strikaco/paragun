from common.models import *
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import TemplateView, ListView

# Create your views here.
class IndexView(TemplateView):
    template_name = 'common/index.html'
    
class RegisterView(TemplateView):
    template_name = 'common/base.html'
    
class DashboardView(LoginRequiredMixin, TemplateView):
    page_title = "Dashboard"
    template_name = 'common/dashboard.html'
    
class TokenListView(LoginRequiredMixin, ListView):
    model = Token
    page_title = "Tokens"
    template_name = 'common/token_list.html'
    
    def get_queryset(self, **kwargs):
        return self.request.user.tokens