from random import choice
from time import sleep
import socket
import sys

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = ('localhost', 514)
messages = """
Oct 21 03:17:01 ip-172-31-18-199 CRON[17350]: pam_unix(cron:session): session opened for user root by (uid=0)
Oct 21 03:17:01 ip-172-31-18-199 CRON[17350]: pam_unix(cron:session): session closed for user root
Oct 21 04:17:01 ip-172-31-18-199 CRON[17668]: pam_unix(cron:session): session opened for user root by (uid=0)
Oct 21 04:17:01 ip-172-31-18-199 CRON[17668]: pam_unix(cron:session): session closed for user root
Oct 21 05:17:01 ip-172-31-18-199 CRON[17719]: pam_unix(cron:session): session opened for user root by (uid=0)
Oct 21 05:17:01 ip-172-31-18-199 CRON[17719]: pam_unix(cron:session): session closed for user root
Oct 21 06:17:01 ip-172-31-18-199 CRON[17882]: pam_unix(cron:session): session opened for user root by (uid=0)
Oct 21 06:17:01 ip-172-31-18-199 CRON[17882]: pam_unix(cron:session): session closed for user root
Oct 21 06:25:01 ip-172-31-18-199 CRON[17901]: pam_unix(cron:session): session opened for user root by (uid=0)   
"""
messages = [x for x in messages.split('\n') if x]

try:

    while True:
        # Send data
        msg = choice(messages) + ' f47ac10b-58cc-4372-a567-0e02b2c3d479@P4R4GN'
        sent = sock.sendto(msg.encode(), server_address)
        print(msg)
        sleep(1)
        
except Exception as e:
    print(e)

finally:
    print('closing socket')
    sock.close()