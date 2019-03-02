#!/usr/bin/python3
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

# Paragun logic
def get_parsers():
    """
    Get all valid parsers and precompile the regexes.
    
    """
    logger = logging.getLogger(__name__)
    parse_tree = {}
    
    try:
        with open('/var/log/paragun/lookups/parsers.json', 'r') as f:
            parse_tree = json.load(f)
            
            for service in parse_tree.keys():
                for field in parse_tree[service].keys():
                    parse_tree[service][field] = [re.compile(x) for x in parse_tree[service][field]]
                    
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
            # Get applicable parsers
            for field, parsers in parser_tree.get(process, {}).items():
                # Try each parser; keep first hit
                for parser in parsers:
                    try: value = parser.search(message).group(1)
                    except Exception as e: 
                        logger.debug(e)
                        value = ''
                    
                    if value:
                        data[field] = value
                        break
    
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
    else: # an empty line means stdin has been closed
        keepRunning = 0
onExit()
sys.stdout.flush() # very important, Python buffers far too much!