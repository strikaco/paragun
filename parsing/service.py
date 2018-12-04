from django.conf import settings
import eventlet
import logging
import re


class Service(object):
    
    interface = settings.LISTEN_INTERFACE
    port = settings.LISTEN_PORT
    
    def __init__(self, **kwargs):
        """
        Constructor for Service class.
        
        Kwargs:
            interface (str): IP address of interface to listen to.
            port (str): TCP port to listen on.
            
        """
        logger = logging.getLogger(__name__)
        
        # Get interface
        interface = kwargs.get('interface', self.interface)
        
        # Get port
        port = kwargs.get('port', self.port)
        
        logger.info("Starting service; listening to %s:%s..." % (self.interface, self.port))
        
        self._server = eventlet.listen((self.interface, self.port))
        self._pool = eventlet.GreenPool()
        self.outbox = eventlet.queue.LightQueue()
        
        logger.info("...service started.")
        
        
    def listen(self):
        """
        Event loop that listens for incoming events and takes action 
        (via `handle()`) upon receipt.
        
        """
        logger = logging.getLogger(__name__)
        logger.info("Waiting for messages... (%s:%s)" % (self.interface, self.port))
        
        # Start event loop
        while True:
            try:
                # Get raw socket data and sender address
                new_sock, address = self._server.accept()
                
                # Handle the socket data
                self._pool.spawn_n(self.handle, new_sock.makefile('r'))
                
            except (SystemExit, KeyboardInterrupt):
                break
            
        logger.info("Listener for %s:%s stopped." % (self.interface, self.port))
        
        
    def handle(self, fd):
        """
        Where the magic happens. Performs actions on incoming messages.
        
        """
        logger = logging.getLogger(__name__)
        
        while True:
            # Get non-EOF line
            # What does this do on multiline?
            msg = fd.readline().strip()
            if not msg:
                break
            
            # Parse the message
            #obj = self.parse(msg)
            obj = {
                'msg': msg,
                'pattern': ''.join(re.findall('([^a-zA-Z0-9\s]+)', msg))
            }
            
            # Add it to queue
            self.outbox.put(obj)
            
            logger.info(obj)