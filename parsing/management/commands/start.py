from django.conf import settings
from django.utils import timezone
from django.core.management import BaseCommand

from parsing.service import Service

import logging

#The class must be named Command, and subclass BaseCommand
class Command(BaseCommand):
    # Show this when the user types help
    help = "Starts log ingestion service."

    # A command must define handle()
    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        
        self.service = Service()
        self.service.listen()