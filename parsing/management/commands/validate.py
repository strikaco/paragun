from django.core.management import BaseCommand

from parsing.models import Service

import logging

#The class must be named Command, and subclass BaseCommand
class Command(BaseCommand):
    # Show this when the user types help
    help = "Performs validation on all service parsers."

    # A command must define handle()
    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        
        services = Service.objects.enabled()
        for service in services:
            logger.info("Validating %s..." % service)
            service.test()