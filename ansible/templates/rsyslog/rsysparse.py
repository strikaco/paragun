#!/opt/paragun/ENV/bin/pypy3
from maxminddb.const import MODE_AUTO, MODE_MMAP, MODE_MMAP_EXT, MODE_FILE, MODE_MEMORY, MODE_FD
from netaddr import IPAddress, IPNetwork, ipv6_verbose, ipv6_compact
from time import time

import ast
import geoip2.database
import json
import logging
import os
import pyasn
import re
import sys
import unittest

logging.basicConfig(
    filename='/var/log/paragun/rsysparse.log', 
    format='%(asctime)s [%(levelname)-8s] %(filename)s.%(funcName)s:%(lineno)d %(message)s', 
    filemode='a+', 
    level=logging.INFO
)

start_time = time()

# How often to reload the parser tree, in minutes
refresh_interval = 15

mm_isp_db = geoip2.database.Reader('/usr/share/GeoIP/latest-isp')
mm_city_db = geoip2.database.Reader('/usr/share/GeoIP/latest-city')
asn_db = pyasn.pyasn('/usr/share/GeoIP/latest-asn')

class Parser(object):
    
    def __init__(self, *args, **kwargs):
        self.field = kwargs.pop('field')
        self.cast = kwargs.pop('cast')
        self.type = kwargs.pop('type')
        
        self.parsers = tuple(re.compile(x) for x in kwargs['parsers'])
        
        validator_regex = kwargs.pop('validator')
        self.validator = re.compile('^%s$' % validator_regex)
    
    def parse(self, message, *args, **kwargs):
        logger = logging.getLogger(__name__)
        value = {}

        for parser in self.parsers:
            try:
                match = parser.search(message)
                if not match: continue
            
                # Match found. Proceed with validation
                raw_value = match.group(1)
                
                # Try casting
                value = self.typecast(raw_value)
                if not value: continue
                
                # Try validating
                validated = self.validate(str(value))
                if not validated: continue
                
                return {self.field: value}
                
            except Exception as e:
                logger.error(e, exc_info=True)
                
        return value
    
    def typecast(self, value):
        logger = logging.getLogger(__name__)
        casted = ''
        
        try:
            casted = self.cast(value)
        except Exception as e:
            logger.error("%s failed casting to %s." % (value, self.type))
            logger.error(e)
            
        return casted
    
    def validate(self, value, *args, **kwargs):
        logger = logging.getLogger(__name__)
        
        # Validate the extracted value
        try:
            match = self.validator.search(value)
            if match:
                logger.debug('Validated %s %s (%s).' % (self.field, value, self.validator))
                return True
            else:
                logger.debug('Failed %s validation: %s.' % (self.field, value,))
                return False
                
        except Exception as e:
            logger.error(e, exc_info=True)
            return False
            
            
class IPParser(Parser):
    
    @classmethod
    def geoip(cls, ip, *args, **kwargs):
        logger = logging.getLogger(__name__)
        logger.debug("Geolocating %s..." % ip)
        geo = {}
        
        # Get ASN info
        try:
            # should return: (15169, '8.8.8.0/24'), the origin AS, and the BGP prefix it matches
            asn, bgp = asn_db.lookup(ip)
            network = IPNetwork(bgp)
            
            # Get normalized BGP prefix
            geo['bgp'] = str(network)
            
            # Upscale to ipv6 and get first and last address
            network = network.ipv6()
            geo['v6_bgp_beg'] = str(IPAddress(network.first).format(dialect=ipv6_verbose))
            geo['v6_bgp_end'] = str(IPAddress(network.last).format(dialect=ipv6_verbose))
            
        except Exception as e:
            logger.error(e)
        
        # Get ISP info
        try: response = mm_isp_db.asn(ip)
        except Exception as e: 
            logger.error(e)
            response = None
        
        if response:
            try: geo['asn'] = response.autonomous_system_number
            except: pass
            try: geo['org'] = response.autonomous_system_organization
            except: pass
            
        # Get City info
        try: response = mm_city_db.city(ip)
        except Exception as e: 
            logger.error(e)
            response = None
        
        if response:
            try: geo['iso'] = response.country.iso_code
            except: pass
        
            try: 
                loc = response.subdivisions.most_specific.iso_code
                assert loc
            except: loc = '??'
            try: geo['iso_local'] = '%s-%s' % (response.country.iso_code, loc)
            except: pass
        
            try: 
                geo['lat'] = response.location.latitude
                geo['lon'] = response.location.longitude
            except: pass
        
        return geo
    
    def parse(self, message, *args, **kwargs):
        logger = logging.getLogger(__name__)

        value = super().parse(message, *args, **kwargs)
        if not value: return value
        
        # Do some additional IP-specific enhancement
        ip = value[self.field]
        
        # Store IP as IPv4 if possible
        try: value['%s_v4' % self.field] = str(ip.ipv4())
        except: pass
    
        # Upsize to IPv6 if possible
        value['%s_v6' % self.field] = ip.ipv6().format(dialect=ipv6_verbose)
        
        # Is it a private address?
        is_private = value['%s_private' % self.field] = ip.is_private()
        
        # Cast IP as string
        value[self.field] = str(ip)
        
        # If not private, do geoip lookup
        if not is_private:
            geo = self.geoip(str(ip))
            value.update({'%s_%s' % (self.field, k): v for k,v in geo.items()})
        
        return value
    

class ParsingEngine(object):
    
    def __init__(self, *args, **kwargs):
        self.type_map = {
            'str': str,
            'bool': bool,
            'int': int,
            'float': float,
            'ip': IPAddress,
            'list': list,
            'dict': dict,
        }
        
        self._punct = re.compile('([^a-zA-Z0-9])')
        
    def parse(self, service, message, *args, **kwargs):
        logger = logging.getLogger(__name__)
        logger.info("Parsing new message...")
        
        data = {}
        
        for field, parser in self.parse_tree.get(service, {}).items():
            logger.debug("Parsing %s..." % field)
            parsed = parser.parse(message)
            if parsed: data.update(parsed)
                
        # Calculate punct string
        data['punct'] = re.sub(' ', '_', ''.join(re.findall(self._punct, message)[:30]))
        
        # Calculate line count
        data['linecount'] = len(message.splitlines())
        
        return data
        
    def load_parsers(self, parse_tree, *args, **kwargs):
        """
        Precompile the regexes for all valid parsers and get associated
        attributes.
        
        """
        logger = logging.getLogger(__name__)
        logger.info("Building parsing tree...")
        
        self.parse_tree = {}
        for service in parse_tree.keys():
            self.parse_tree[service] = {}
            for field in parse_tree[service].keys():
                data = parse_tree[service][field]
                data['cast'] = self.type_map[data['type']]
                data['field'] = field
                
                logger.debug('%s: %s' % (service, field))
                
                Model = Parser
                if data['type'] == 'ip':
                    Model = IPParser
                
                self.parse_tree[service][field] = Model(**data)
                
        logger.info("Done building parsing tree.")
        logger.debug(self.parse_tree)
    
    def read_parser_file(self, *args, **kwargs):
        """
        Reads parse tree structure from file and closes it as quickly as possible.
        
        """
        logger = logging.getLogger(__name__)
        logger.info("Reading parsers from file...")
        
        path = kwargs.get('path', '/var/log/paragun/lookups/parsers.json')
        
        try:
            parse_tree = {}
            with open(path, 'r') as f:
                parse_tree = json.load(f)
        except Exception as e:
            logger.error(e, exc_info=True)
            
        logger.info("Done reading parsers from file.")
        return parse_tree


# Rsyslog logic
def onInit():
    """ 
    Do everything that is needed to initialize processing (e.g.
    open files, create handles, connect to systems...)
      
    """
    logger = logging.getLogger(__name__)
    
    global mm_isp_db
    mm_isp_db = geoip2.database.Reader('/usr/share/GeoIP/latest-isp')
    
    global mm_city_db
    mm_city_db = geoip2.database.Reader('/usr/share/GeoIP/latest-city')
    
    global asn_db
    asn_db = pyasn.pyasn('/usr/share/GeoIP/latest-asn')
    
    global engine
    engine = ParsingEngine()
    data = engine.read_parser_file()
    engine.load_parsers(data)
    
def onReceive(blob):
    """
    This is the entry point where actual work needs to be done. It receives
    the messge from rsyslog and now needs to examine it, do any processing
    necessary. The to-be-modified properties (one or many) need to be pushed
    back to stdout, in JSON format, with no interim line breaks and a line
    break at the end of the JSON. If no field is to be modified, empty 
    json ("{}") needs to be emitted.
    
    Note that no batching takes place (contrary to the output module skeleton)
    and so each message needs to be fully processed (rsyslog will wait for the
    reply before the next message is pushed to this module).
    
    """
    logger = logging.getLogger(__name__)
    data = {}
    
    try:
        # Deserialize JSON string
        rsysjson = json.loads(blob)
        
        # Get the service that produced the log
        service = rsysjson.get('$!', {}).get('programname_clean', '')
        logger.debug('Service: %s' % service)
        
        # Get the cleaned-up message
        message = rsysjson.get('$!', {}).get('msg_short', '')
        logger.debug('Message: %s' % message)
        
        if service and message:
            data = engine.parse(service, message)
    
    except Exception as e:
        logger.error(e, exc_info=True)

    # Return only the parsed data
    print(json.dumps({'$!':{'data':data}}, separators=(',', ':')))
    
    
def onExit():
    """ 
    Do everything that is needed to finish processing (e.g.
    close files, handles, disconnect from systems...). This is
    being called immediately before exiting.
    
    """
    mm_isp_db.close()
    mm_city_db.close()


"""
-------------------------------------------------------
This is plumbing that DOES NOT need to be CHANGED
-------------------------------------------------------
Implementor's note: Python seems to very agressively
buffer stdouot. The end result was that rsyslog does not
receive the script's messages in a timely manner (sometimes
even never, probably due to races). To prevent this, we
flush stdout after we have done processing. This is especially
important once we get to the point where the plugin does
two-way conversations with rsyslog. Do NOT change this!
See also: https://github.com/rsyslog/rsyslog/issues/22
"""
if __name__ == '__main__':
    onInit()
    keepRunning = 1
    max_minutes = refresh_interval * 60
    while keepRunning == 1:
        msg = sys.stdin.readline()
        if msg:
            msg = msg[:len(msg)-1] # remove LF
            onReceive(msg)
            sys.stdout.flush() # very important, Python buffers far too much!
            
            # Check if we need to reload parser tree
            now = time()
            if now - start_time > max_minutes:
                start_time = now
                onInit()
            
        else: # an empty line means stdin has been closed
            keepRunning = 0
            
    onExit()
    sys.stdout.flush() # very important, Python buffers far too much!

"""
For testing

python -m unittest rsysparse.py

"""
class RsysparseTest(unittest.TestCase):
    
    def setUp(self):
        serialized = '{"sshd": {"src_ip": {"validator": "(.*)", "type": "ip", "parsers": ["from ([0-9]{1,3}\\\.[0-9]{1,3}\\\.[0-9]{1,3}\\\.[0-9]{1,3})"]}, "user": {"validator": "(.*)", "type": "str", "parsers": ["user ([a-zA-Z0-9\\\.\\\-]+) from", "username ([a-zA-Z0-9\\\.\\\-]+)", "user is ([a-zA-Z0-9\\\.\\\-]+)"]}}, "ufw": {"dst_ip": {"validator": "(.*)", "type": "str", "parsers": ["to ([0-9]{1,3}\\\.[0-9]{1,3}\\\.[0-9]{1,3}\\\.[0-9]{1,3})"]}, "src_ip": {"validator": "(.*)", "type": "str", "parsers": ["from ([0-9]{1,3}\\\.[0-9]{1,3}\\\.[0-9]{1,3}\\\.[0-9]{1,3})"]}}}'
        data = json.loads(serialized)
        
        self.engine = ParsingEngine()
        self.engine.load_parsers(data)
    
    def test_stuff(self):
        msg = 'Aug  1 18:27:46 knight sshd[20325]: Failed password for illegal user test from 218.49.183.17 port 48849 ssh2'
        print(self.engine.parse('sshd', msg))
