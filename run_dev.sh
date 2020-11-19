#!/bin/sh

/bin/sh /root/samp-packet-proxy/setup_iptables_dev.sh
/usr/bin/python3 pack-scan.py