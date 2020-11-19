#!/bin/sh

/bin/sh /root/samp-packet-proxy/setup_iptables_live.sh
/usr/bin/python3 pack-scan.py