from random import choice
from time import sleep
import uuid
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
Aug  1 18:27:59 knight sshd[20334]: Failed password for illegal user user from 218.49.183.17 port 49680 ssh2
Aug  1 18:30:12 knight sshd[20449]: Failed password for illegal user user from 218.49.183.17 port 53230 ssh2
2006-08-13 00:00:35 10.3.4.2 GET /iisstart.htm - 80 - 10.3.0.5 check_http/1.7+(nagios-plugins+) 200 0 0
4872: Dec 11 08:02:53.887 pst: %SEC-6-IPACCESSLOGP: list 100 denied udp 200.174.153.126(1028) -> 66.81.85.65(137), 1 packet 4873: Dec 11 08:03:09.583 pst: %SEC-6-IPACCESSLOGP: list 100 denied udp 195.23.72.148(1026) -> 66.81.85.65(137), 1 packet
"""
messages = [x for x in messages.split('\n') if x]

uids = [uuid.uuid4() for x in range(15)]

try:

    while True:
        # Send data
        msg = choice(messages) + ' %s@P4R4GN' % choice(uids)
        sent = sock.sendto(msg.encode(), server_address)
        print(msg)
        sleep(1)
        
except Exception as e:
    print(e)
finally:
    print('closing socket...')
    sock.close()