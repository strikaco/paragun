"""paragun URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from common.views import *
from parsing.views import *
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # HTML views
    path('dashboard/', DashboardView.as_view(), name="dashboard"),
    
    path('tokens/create/', TokenCreateView.as_view(), name="token-create"),
    path('tokens/update/<str:pk>/', TokenUpdateView.as_view(), name="token-update"),
    path('tokens/detail/<str:pk>/', TokenDetailView.as_view(), name="token-detail"),
    path('tokens/delete/<str:pk>/', TokenDeleteView.as_view(), name="token-delete"),
    
    # API views
    path('api/metrics/update/', PulseUpdateView.as_view(), name="pulse-update"),
    path('api/tokens/valid/', TokenDumpView.as_view(), name="token-dump"),
    path('api/tokens/retention/', TokenRetentionView.as_view(), name="token-retention"),
    path('api/parsers/', ParserDumpView.as_view(), name="parser-dump"),
    path('', IndexView.as_view(), name="index"),
]
