from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import View

from parsing.models import Service

# Create your views here.
class ParserDumpView(View):
    
    def get(self, request, *args, **kwargs):
        """
        Returns:
            table (JSON): Regex parsing tree.
        
        """
        # TODO: Check for API key
        
        # Return it
        return JsonResponse(Service.get_parser_map())