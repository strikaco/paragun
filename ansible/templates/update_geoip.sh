#!/bin/bash

# Download new databases
wget -P /tmp/ http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.tar.gz
tar -zxf /tmp/GeoLite2-City.tar.gz --directory /tmp/ --no-anchored GeoLite2-City.mmdb --transform='s/.*\///'

wget -P /tmp/ http://geolite.maxmind.com/download/geoip/database/GeoLite2-ASN.tar.gz
tar -zxf /tmp/GeoLite2-ASN.tar.gz --directory /tmp/ --no-anchored GeoLite2-ASN.mmdb --transform='s/.*\///'

cd /tmp/ && /opt/paragun/ENV/bin/pyasn_util_download.py --latestv46
# Compile BGP table
/opt/paragun/ENV/bin/pyasn_util_convert.py --single rib.* /tmp/pyasn.mmdb

# Copy downloaded databases to /usr/share/GeoIP
cp -f /tmp/GeoLite2-City.mmdb /usr/share/GeoIP/GeoLite2-City.mmdb
cp -f /tmp/GeoLite2-ASN.mmdb /usr/share/GeoIP/GeoLite2-ASN.mmdb
cp -f /tmp/pyasn.mmdb /usr/share/GeoIP/pyasn.mmdb

# Update symlink to point to latest db for each type
ln -sf /usr/share/GeoIP/GeoLite2-City.mmdb /usr/share/GeoIP/latest-city
ln -sf /usr/share/GeoIP/GeoLite2-ASN.mmdb /usr/share/GeoIP/latest-isp
ln -sf /usr/share/GeoIP/pyasn.mmdb /usr/share/GeoIP/latest-asn

# Reload rsyslog (SIGHUP)
/usr/sbin/invoke-rc.d rsyslog rotate > /dev/null

# Clean up temp files
rm /tmp/GeoLite2-*.tar.gz
rm /tmp/*.mmdb
rm /tmp/rib.*