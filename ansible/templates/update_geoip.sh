#!/bin/bash

# Download new databases
if [ ! -f /tmp/GeoLite2-City.tar.gz ]; then
    wget -P /tmp/ http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.tar.gz
fi

if [ ! -f /tmp/GeoLite2-ASN.tar.gz ]; then
    wget -P /tmp/ http://geolite.maxmind.com/download/geoip/database/GeoLite2-ASN.tar.gz
fi

# Extract gzips
tar -zxf /tmp/GeoLite2-City.tar.gz --directory /tmp/ --no-anchored GeoLite2-City.mmdb --transform='s/.*\///'
tar -zxf /tmp/GeoLite2-ASN.tar.gz --directory /tmp/ --no-anchored GeoLite2-ASN.mmdb --transform='s/.*\///'

# Copy downloaded databases to /usr/share/GeoIP
cp /tmp/GeoLite2-City.mmdb /usr/share/GeoIP/
cp /tmp/GeoLite2-ASN.mmdb /usr/share/GeoIP/