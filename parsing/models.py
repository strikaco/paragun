from django.db import models

# Create your models here.


        
class Application(models.Model):
    """
    Logical parent of multiple child parsers; identifies a string and applies
    the appropriate Parser to it.
    
    """
    class Meta:
        abstract = True
        
    def __init__(self, parsers=[], *args, **kwargs):
        super(Application, self).__init__(*args, **kwargs)
        # Get the list of parsers that comprise this application
        self.parsers = parsers
        
    def identify(self, msg, *args, **kwargs):
        pass
        
    def parse(self, msg, *args, **kwargs):
        """
        Identify the message and apply the appropriate parser.
        
        If the message cannot be identified, try all parsers for this application.
        
        Args:
            msg (str): The log message to be parsed.
            
        """
        parsed = None
        
        # Try identifying the string and using the appropriate parser
        parser = self.identify(msg, *args, **kwargs)
        if parser:
            parsed = parser.parse(msg, *args, **kwargs)
        
        if not parser or not parsed:
            # Try all parsers
            for parser in self.parsers:
                try:
                    parsed = parser.at_parse(msg, *args, **kwargs)
                    if parsed: break
                except Exception as e:
                    logger.error(e)
        
        return parsed

class BaseParser(models.Model):
    """
    Base class for Parser objects.
    
    """
    class Meta:
        abstract = True
        
    def at_parse(self, msg, *args, **kwargs):
        """
        Base functionality for Parsers; all must implement `parse()`.
        
        """
        # Perform parsing workflow
        parsed = self.at_parse(msg, *args, **kwargs)
        translated = self.translate(parsed, *args, **kwargs)
        enhanced = self.enhance(translated, *args, **kwargs)
        
        # Get final output
        final = enhanced
        
        return final
        
    def parse(self, msg, *args, **kwargs):
        """
        Extend this to implement your own parsing logic.
        
        """
        raise Exception("Method not implemented!")
        return {}
        
    def translate(self, parsed, *args, **kwargs):
        """
        Renames parsed terms according to a prespecified template.
        
        """
        return parsed
        
    def enhance(self, msg, *args, **kwargs):
        """
        Any additional post-parsing steps that need performing (i.e. geoip, 
        lookups, etc.).

        """
        pass
    
class JSONParser(BaseParser):
    class Meta:
        abstract = True
        
class KeyValueParser(BaseParser):
    class Meta:
        abstract = True
    
class RegexParser(BaseParser):
    class Meta:
        abstract = True