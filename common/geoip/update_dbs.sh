#!/bin/bash

# Requires pyasn and geoip2
#pip install -U geoip2 pyasn

echo "_____/ Downloading ASN CIDR DB... (1/3) \__________"
pyasn_util_download.py --latest
pyasn_util_convert.py --single rib.* pyasn.dat
echo
echo "_____/ Downloading MaxMind GeoIP City database...(2/3) \__________"
wget http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.tar.gz
tar -zxf ./GeoLite2-City.tar.gz --no-anchored GeoLite2-City.mmdb --transform='s/.*\///'

echo "_____/ Downloading MaxMind GeoIP ASN database...(3/3) \__________"
wget http://geolite.maxmind.com/download/geoip/database/GeoLite2-ASN.tar.gz
tar -zxf ./GeoLite2-ASN.tar.gz --no-anchored GeoLite2-ASN.mmdb --transform='s/.*\///'

echo "_____/ Cleaning up downloaded files... \__________"
rm GeoLite2-*.tar.gz
rm rib.*

echo "_____/ Done! \__________"