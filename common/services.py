import eventlet
import logging

class Service(object):
    
    interface = '0.0.0.0'
    port = 10514
    
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
        
        logger.info("Starting service; listening to port %s on interface %s..." % (self.port, self.interface))
        
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
                new_sock, address = self.server.accept()
                
                # Handle the socket data
                self.pool.spawn_n(self.handle, new_sock.makefile('r'))
                
            except (SystemExit, KeyboardInterrupt):
                break
        
    def handle(self, fd):
        logger = logging.getLogger(__name__)
        
        while True:
            # Get non-EOF line
            msg = fd.readline()
            if not msg:
                break
            
            # Parse the message
            #obj = self.parse(msg)
            obj = {'msg': msg.strip()}
            
            # Add it to queue
            self.outbox.put(obj)
            
            logger.info(obj)
            
        print("client disconnected")