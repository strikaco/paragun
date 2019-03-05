#!/usr/bin/python3
from time import time

import json
import logging
import os
import re
import sys

logging.basicConfig(
    filename='/var/log/paragun/rsysparse.log', 
    format='%(asctime)s [%(levelname)-8s] %(filename)s:%(lineno)d %(message)s', 
    filemode='a', 
    level=logging.DEBUG
)

parsers = {}

# How often to reload the parser tree, in minutes
REFRESH_INTERVAL = 5
start_time = time()

# Paragun logic
def get_parsers():
    """
    Get all valid parsers and precompile the regexes.
    
    """
    logger = logging.getLogger(__name__)
    logger.info("Reloading parser tree...")
    parse_tree = {}
    
    try:
        with open('/var/log/paragun/lookups/parsers.json', 'r') as f:
            parse_tree = json.load(f)
            
            for service in parse_tree.keys():
                for field in parse_tree[service].keys():
                    validator, parsers = parse_tree[service][field]
                    parse_tree[service][field] = (re.compile('^%s$' % validator), tuple(re.compile(x) for x in parsers))
                    
    except Exception as e:
        logger.error(e, exc_info=True)
        
    return parse_tree


# Rsyslog logic
def onInit():
    """ 
    Do everything that is needed to initialize processing (e.g.
    open files, create handles, connect to systems...)
      
    """
    logger = logging.getLogger(__name__)
    global parser_tree
    parser_tree = get_parsers()
    
    global punct
    punct = re.compile('([^a-zA-Z0-9])')
    
    if not parser_tree:
        logger.warn("No parsers loaded.")
        
    
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
        
        # Get the process that produced the log
        process = rsysjson.get('$!', {}).get('programname_clean', '')
        logger.debug('Process: %s' % process)
        
        # Get the cleaned-up message
        message = rsysjson.get('$!', {}).get('msg_short', '')
        logger.debug('Message: %s' % message)
        
        if process and message:
            # Calculate punct string
            data['punct'] = re.sub(' ', '_', ''.join(re.findall(punct, message)[:30]))
            
            # Get applicable parsers
            for field in parser_tree.get(process, {}).keys():
                blob = parser_tree[process][field]
                
                validator = blob[0]
                parsers = blob[1]
                
                value = ''
                
                # Try each parser and retain first match
                for parser in parsers:
                    try: 
                        match = parser.search(message)
                        if match:
                            value = match.group(1)
                            logger.debug('Found %s: %s (%s).' % (field, value, parser))
                        else:
                            continue
                        
                    except Exception as e:
                        logger.error(e, exc_info=True)
                        
                    # Match found
                    if value:
                        # Validate the extracted value
                        match = validator.search(value)
                        if match:
                            data[field] = value
                            logger.debug('Validated %s: %s (%s).' % (field, value, validator))
                            break
                        else:
                            logger.debug('Failed %s: %s.' % (field, value))
                            
    
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
    pass


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
onInit()
keepRunning = 1
while keepRunning == 1:
    msg = sys.stdin.readline()
    if msg:
        msg = msg[:len(msg)-1] # remove LF
        onReceive(msg)
        sys.stdout.flush() # very important, Python buffers far too much!
        
        # Check if we need to reload parser tree
        now = time()
        if now - start_time > REFRESH_INTERVAL * 60:
            start_time = now
            onInit()
        
    else: # an empty line means stdin has been closed
        keepRunning = 0
        
onExit()
sys.stdout.flush() # very important, Python buffers far too much!